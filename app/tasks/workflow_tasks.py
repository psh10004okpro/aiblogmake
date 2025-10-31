"""
Enhanced workflow tasks with progress tracking and state management.

This module provides one-click automation workflows with real-time progress updates.
"""

from celery import Celery, current_task
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.database import WorkflowRun, Keyword, Post
from app.services.keyword_research import KeywordResearchService
from app.services.content_generator import ContentGeneratorService
from app.services.image_generator import ImageGeneratorService
from app.services.ad_inserter import AdInserterService
from app.services.publisher import WordPressPublisher
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Import celery_app from celery_tasks
from app.tasks.celery_tasks import celery_app, run_async


class WorkflowTracker:
    """Helper class for tracking workflow progress in database."""

    def __init__(self, workflow_run_id: int):
        self.workflow_run_id = workflow_run_id
        self.db: Optional[Session] = None

    def __enter__(self):
        self.db = SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()

    def update_status(
        self,
        status: str = None,
        current_step: str = None,
        progress: int = None,
        **kwargs
    ):
        """Update workflow status."""
        if not self.db:
            return

        workflow = self.db.query(WorkflowRun).filter(
            WorkflowRun.id == self.workflow_run_id
        ).first()

        if not workflow:
            return

        if status:
            workflow.status = status
        if current_step:
            workflow.current_step = current_step
        if progress is not None:
            workflow.progress_percentage = progress

        for key, value in kwargs.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)

        self.db.commit()

    def update_step(
        self,
        step_name: str,
        status: str,
        result: Any = None,
        error: str = None
    ):
        """Update individual step status."""
        if not self.db:
            return

        workflow = self.db.query(WorkflowRun).filter(
            WorkflowRun.id == self.workflow_run_id
        ).first()

        if not workflow:
            return

        steps = workflow.steps or {}

        if step_name not in steps:
            steps[step_name] = {
                "started_at": datetime.utcnow().isoformat()
            }

        steps[step_name]["status"] = status

        if status in ["completed", "failed"]:
            steps[step_name]["completed_at"] = datetime.utcnow().isoformat()

        if result is not None:
            steps[step_name]["result"] = result

        if error:
            steps[step_name]["error"] = error

        workflow.steps = steps
        self.db.commit()

    def increment_counter(self, counter_name: str, amount: int = 1):
        """Increment a counter field."""
        if not self.db:
            return

        workflow = self.db.query(WorkflowRun).filter(
            WorkflowRun.id == self.workflow_run_id
        ).first()

        if not workflow or not hasattr(workflow, counter_name):
            return

        current_value = getattr(workflow, counter_name) or 0
        setattr(workflow, counter_name, current_value + amount)
        self.db.commit()


@celery_app.task(bind=True, name="workflow.one_click_publish")
def one_click_publish_task(
    self,
    seed_keywords: List[str],
    num_posts: int = 1,
    publish_immediately: bool = True,
    llm_provider: Optional[str] = None,
    workflow_run_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    One-click complete blog automation workflow with progress tracking.

    This is the enhanced version of complete_blog_workflow with:
    - Real-time progress tracking
    - State persistence in database
    - Better error handling and recovery
    - Detailed step-by-step logging

    Steps:
    1. Research keywords from seed keywords
    2. Select top N keywords by golden score
    3. For each keyword:
       a. Generate content using specified LLM
       b. Generate images for the content
       c. Insert AdSense ads
       d. Publish to WordPress
    4. Return complete results

    Args:
        seed_keywords: List of seed keywords to research
        num_posts: Number of posts to create (default: 1)
        publish_immediately: Whether to publish immediately or schedule (default: True)
        llm_provider: LLM provider to use (claude, chatgpt, gemini)
        workflow_run_id: ID of WorkflowRun record for tracking

    Returns:
        Dict with workflow results including created posts, errors, and statistics
    """
    start_time = datetime.utcnow()

    # Create workflow run record if not provided
    if not workflow_run_id:
        db = SessionLocal()
        try:
            workflow_run = WorkflowRun(
                workflow_type="one_click",
                celery_task_id=self.request.id,
                seed_keywords=seed_keywords,
                num_posts=num_posts,
                publish_immediately=publish_immediately,
                llm_provider=llm_provider,
                status="running",
                started_at=start_time,
                steps={}
            )
            db.add(workflow_run)
            db.commit()
            db.refresh(workflow_run)
            workflow_run_id = workflow_run.id
        finally:
            db.close()

    logger.info(
        "workflow_started",
        workflow_id=workflow_run_id,
        task_id=self.request.id,
        seeds=seed_keywords,
        num_posts=num_posts
    )

    results = {
        "workflow_id": workflow_run_id,
        "keywords": [],
        "posts": [],
        "errors": [],
        "statistics": {
            "keywords_researched": 0,
            "posts_created": 0,
            "posts_published": 0,
            "errors": 0
        }
    }

    try:
        with WorkflowTracker(workflow_run_id) as tracker:
            # ===== STEP 1: Research Keywords =====
            tracker.update_status(
                current_step="research_keywords",
                progress=10
            )
            tracker.update_step("research_keywords", "running")

            logger.info("workflow_step", step=1, action="researching_keywords")

            try:
                keyword_service = KeywordResearchService()
                keywords = run_async(
                    keyword_service.research_keywords(
                        seed_keywords=seed_keywords,
                        include_google=True,
                        include_naver=True,
                        include_autocomplete=True
                    )
                )

                results["keywords"] = keywords
                results["statistics"]["keywords_researched"] = len(keywords)

                tracker.update_step(
                    "research_keywords",
                    "completed",
                    result={"count": len(keywords)}
                )
                tracker.increment_counter("keywords_researched", len(keywords))
                tracker.update_status(progress=20)

                logger.info("workflow_step_completed", step=1, keywords_found=len(keywords))

            except Exception as e:
                error_msg = f"Keyword research failed: {str(e)}"
                logger.error("workflow_step_failed", step=1, error=error_msg)
                tracker.update_step("research_keywords", "failed", error=error_msg)
                tracker.increment_counter("errors_count", 1)
                results["errors"].append({"step": "research_keywords", "error": error_msg})
                raise

            # ===== STEP 2: Select Top Keywords =====
            tracker.update_status(
                current_step="select_keywords",
                progress=25
            )

            top_keywords = sorted(
                keywords,
                key=lambda x: x.get("golden_score", 0),
                reverse=True
            )[:num_posts]

            logger.info(
                "workflow_step",
                step=2,
                action="selected_top_keywords",
                count=len(top_keywords)
            )

            # ===== STEP 3-6: Process Each Keyword =====
            total_steps = num_posts * 4  # content, images, ads, publish
            completed_steps = 0

            for i, kw_data in enumerate(top_keywords):
                keyword = kw_data["keyword"]
                post_num = i + 1

                logger.info(
                    "workflow_processing_post",
                    post_number=post_num,
                    total=num_posts,
                    keyword=keyword
                )

                post_result = {
                    "keyword": keyword,
                    "keyword_data": kw_data,
                    "steps": {}
                }

                try:
                    # === 3a. Generate Content ===
                    step_name = f"post_{post_num}_generate_content"
                    tracker.update_status(
                        current_step=step_name,
                        progress=25 + int((completed_steps / total_steps) * 70)
                    )
                    tracker.update_step(step_name, "running")

                    logger.info("workflow_step", step=f"3.{post_num}.a", action="generating_content")

                    content_service = ContentGeneratorService(provider=llm_provider)
                    content_data = run_async(
                        content_service.generate_content(
                            keyword=keyword,
                            target_word_count=settings.target_word_count,
                            tone="professional"
                        )
                    )

                    post_result["steps"]["content"] = {
                        "status": "completed",
                        "title": content_data["title"],
                        "word_count": content_data["word_count"]
                    }
                    tracker.update_step(step_name, "completed", result={"word_count": content_data["word_count"]})
                    completed_steps += 1

                    # === 3b. Generate Images ===
                    step_name = f"post_{post_num}_generate_images"
                    tracker.update_status(
                        current_step=step_name,
                        progress=25 + int((completed_steps / total_steps) * 70)
                    )
                    tracker.update_step(step_name, "running")

                    logger.info("workflow_step", step=f"3.{post_num}.b", action="generating_images")

                    image_service = ImageGeneratorService()
                    images = run_async(
                        image_service.generate_images_for_post(
                            keyword=keyword,
                            content=content_data["content"],
                            num_images=settings.min_images_per_post
                        )
                    )

                    post_result["steps"]["images"] = {
                        "status": "completed",
                        "count": len(images)
                    }
                    tracker.update_step(step_name, "completed", result={"count": len(images)})
                    completed_steps += 1

                    # === 3c. Insert Ads ===
                    step_name = f"post_{post_num}_insert_ads"
                    tracker.update_status(
                        current_step=step_name,
                        progress=25 + int((completed_steps / total_steps) * 70)
                    )
                    tracker.update_step(step_name, "running")

                    logger.info("workflow_step", step=f"3.{post_num}.c", action="inserting_ads")

                    ad_service = AdInserterService()
                    ad_result = ad_service.insert_ads(content_data["content"])
                    final_content = ad_result["content"]

                    post_result["steps"]["ads"] = {
                        "status": "completed",
                        "ads_inserted": ad_result.get("ads_inserted", 0)
                    }
                    tracker.update_step(step_name, "completed")
                    completed_steps += 1

                    # === 3d. Publish to WordPress ===
                    step_name = f"post_{post_num}_publish"
                    tracker.update_status(
                        current_step=step_name,
                        progress=25 + int((completed_steps / total_steps) * 70)
                    )
                    tracker.update_step(step_name, "running")

                    logger.info("workflow_step", step=f"3.{post_num}.d", action="publishing")

                    publisher = WordPressPublisher()
                    wp_result = run_async(
                        publisher.create_post(
                            title=content_data["title"],
                            content=final_content,
                            categories=[],
                            tags=[keyword],
                            status="publish" if publish_immediately else "draft"
                        )
                    )

                    post_result["steps"]["publish"] = {
                        "status": "completed",
                        "wp_post_id": wp_result["id"],
                        "wp_url": wp_result["url"]
                    }
                    post_result["wp_post_id"] = wp_result["id"]
                    post_result["wp_url"] = wp_result["url"]
                    post_result["title"] = content_data["title"]
                    post_result["status"] = "success"

                    tracker.update_step(step_name, "completed", result={"wp_post_id": wp_result["id"]})
                    tracker.increment_counter("posts_created", 1)
                    if publish_immediately:
                        tracker.increment_counter("posts_published", 1)
                    completed_steps += 1

                    results["posts"].append(post_result)
                    results["statistics"]["posts_created"] += 1
                    if publish_immediately:
                        results["statistics"]["posts_published"] += 1

                    logger.info(
                        "workflow_post_completed",
                        post_number=post_num,
                        keyword=keyword,
                        wp_post_id=wp_result["id"]
                    )

                except Exception as e:
                    error_msg = f"Failed to process post for keyword '{keyword}': {str(e)}"
                    logger.error("workflow_post_failed", keyword=keyword, error=error_msg)

                    post_result["status"] = "failed"
                    post_result["error"] = error_msg

                    results["posts"].append(post_result)
                    results["errors"].append({
                        "post_number": post_num,
                        "keyword": keyword,
                        "error": error_msg
                    })
                    results["statistics"]["errors"] += 1

                    tracker.increment_counter("errors_count", 1)

                    # Continue with next post instead of failing entire workflow
                    continue

            # ===== WORKFLOW COMPLETED =====
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            tracker.update_status(
                status="completed",
                current_step="finished",
                progress=100,
                completed_at=end_time,
                duration_seconds=duration,
                results=results
            )

            logger.info(
                "workflow_completed",
                workflow_id=workflow_run_id,
                duration_seconds=duration,
                posts_created=results["statistics"]["posts_created"],
                errors=results["statistics"]["errors"]
            )

            return results

    except Exception as e:
        # Fatal error - workflow failed completely
        error_msg = f"Workflow failed: {str(e)}"
        logger.error("workflow_failed", workflow_id=workflow_run_id, error=error_msg)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        try:
            with WorkflowTracker(workflow_run_id) as tracker:
                tracker.update_status(
                    status="failed",
                    progress=0,
                    completed_at=end_time,
                    duration_seconds=duration,
                    errors=[{"error": error_msg}]
                )
        except:
            pass

        results["errors"].append({"error": error_msg})
        results["statistics"]["errors"] += 1

        raise


@celery_app.task(name="workflow.get_status")
def get_workflow_status(workflow_run_id: int) -> Dict[str, Any]:
    """
    Get the current status of a workflow run.

    Args:
        workflow_run_id: ID of the workflow run

    Returns:
        Dict with workflow status, progress, and results
    """
    db = SessionLocal()
    try:
        workflow = db.query(WorkflowRun).filter(
            WorkflowRun.id == workflow_run_id
        ).first()

        if not workflow:
            return {"error": "Workflow not found"}

        return {
            "id": workflow.id,
            "workflow_type": workflow.workflow_type,
            "status": workflow.status,
            "current_step": workflow.current_step,
            "progress_percentage": workflow.progress_percentage,
            "steps": workflow.steps,
            "statistics": {
                "keywords_researched": workflow.keywords_researched,
                "posts_created": workflow.posts_created,
                "posts_published": workflow.posts_published,
                "errors_count": workflow.errors_count,
            },
            "results": workflow.results,
            "errors": workflow.errors,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "duration_seconds": workflow.duration_seconds,
            "created_at": workflow.created_at.isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name="workflow.cancel")
def cancel_workflow(workflow_run_id: int) -> Dict[str, Any]:
    """
    Cancel a running workflow.

    Args:
        workflow_run_id: ID of the workflow run

    Returns:
        Dict with cancellation result
    """
    db = SessionLocal()
    try:
        workflow = db.query(WorkflowRun).filter(
            WorkflowRun.id == workflow_run_id
        ).first()

        if not workflow:
            return {"error": "Workflow not found"}

        if workflow.status not in ["pending", "running"]:
            return {"error": f"Cannot cancel workflow with status: {workflow.status}"}

        # Update status to cancelled
        workflow.status = "cancelled"
        workflow.completed_at = datetime.utcnow()
        if workflow.started_at:
            workflow.duration_seconds = (workflow.completed_at - workflow.started_at).total_seconds()
        db.commit()

        # Try to revoke the Celery task
        if workflow.celery_task_id:
            celery_app.control.revoke(workflow.celery_task_id, terminate=True)

        logger.info("workflow_cancelled", workflow_id=workflow_run_id)

        return {
            "success": True,
            "workflow_id": workflow_run_id,
            "status": "cancelled"
        }
    finally:
        db.close()
