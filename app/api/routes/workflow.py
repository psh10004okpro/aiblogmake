"""
API routes for one-click automation workflows.

This module provides endpoints for managing complete blog automation workflows.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.database import WorkflowRun
from app.models.schemas import (
    OneClickPublishRequest,
    OneClickPublishResponse,
    WorkflowStatusResponse,
    WorkflowCancelResponse,
    WorkflowListResponse,
    WorkflowStatistics,
)
from app.tasks.workflow_tasks import (
    one_click_publish_task,
    get_workflow_status,
    cancel_workflow,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/one-click-publish", response_model=OneClickPublishResponse)
async def start_one_click_publish(
    request: OneClickPublishRequest,
    db: Session = Depends(get_db)
):
    """
    Start a one-click publish workflow.

    This endpoint triggers a complete automation workflow:
    1. Research keywords from seed keywords
    2. Select top N keywords by golden score
    3. For each keyword:
       - Generate content using specified LLM
       - Generate images
       - Insert AdSense ads
       - Publish to WordPress

    The workflow runs asynchronously in the background. Use the returned
    workflow_id to check progress with GET /workflow/{workflow_id}/status

    **Example Request:**
    ```json
    {
        "seed_keywords": ["블로그 SEO", "콘텐츠 마케팅"],
        "num_posts": 2,
        "publish_immediately": true,
        "llm_provider": "claude"
    }
    ```

    **Returns:**
    - workflow_id: ID for tracking the workflow
    - celery_task_id: Celery task ID
    - status: Current status (running)
    - message: Success message
    - estimated_duration_minutes: Estimated time to complete
    """
    logger.info(
        "workflow_api_start",
        seed_keywords=request.seed_keywords,
        num_posts=request.num_posts,
        llm_provider=request.llm_provider
    )

    try:
        # Create workflow run record
        workflow_run = WorkflowRun(
            workflow_type="one_click",
            seed_keywords=request.seed_keywords,
            num_posts=request.num_posts,
            publish_immediately=request.publish_immediately,
            llm_provider=request.llm_provider,
            status="pending",
            progress_percentage=0,
            steps={}
        )
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)

        # Start Celery task
        task = one_click_publish_task.delay(
            seed_keywords=request.seed_keywords,
            num_posts=request.num_posts,
            publish_immediately=request.publish_immediately,
            llm_provider=request.llm_provider,
            workflow_run_id=workflow_run.id
        )

        # Update workflow with celery task ID
        workflow_run.celery_task_id = task.id
        db.commit()

        logger.info(
            "workflow_api_started",
            workflow_id=workflow_run.id,
            celery_task_id=task.id
        )

        return OneClickPublishResponse(
            workflow_id=workflow_run.id,
            celery_task_id=task.id,
            status="running",
            message=f"Workflow started successfully. Generating {request.num_posts} post(s) from {len(request.seed_keywords)} seed keyword(s).",
            estimated_duration_minutes=request.num_posts * 5  # Estimate 5 minutes per post
        )

    except Exception as e:
        logger.error("workflow_api_start_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the current status of a workflow.

    Returns detailed information about the workflow including:
    - Current status and progress percentage
    - Current step being executed
    - Detailed step-by-step progress
    - Statistics (keywords researched, posts created, etc.)
    - Results and errors
    - Timing information

    **Example Response:**
    ```json
    {
        "id": 1,
        "workflow_type": "one_click",
        "status": "running",
        "current_step": "post_1_generate_content",
        "progress_percentage": 45,
        "steps": {
            "research_keywords": {"status": "completed", "result": {"count": 20}},
            "post_1_generate_content": {"status": "running"}
        },
        "statistics": {
            "keywords_researched": 20,
            "posts_created": 0,
            "posts_published": 0,
            "errors": 0
        },
        "started_at": "2025-01-01T09:00:00Z",
        "duration_seconds": null
    }
    ```
    """
    logger.info("workflow_api_get_status", workflow_id=workflow_id)

    workflow = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowStatusResponse(
        id=workflow.id,
        workflow_type=workflow.workflow_type,
        status=workflow.status,
        current_step=workflow.current_step,
        progress_percentage=workflow.progress_percentage or 0,
        steps=workflow.steps or {},
        statistics=WorkflowStatistics(
            keywords_researched=workflow.keywords_researched or 0,
            posts_created=workflow.posts_created or 0,
            posts_published=workflow.posts_published or 0,
            errors=workflow.errors_count or 0
        ),
        results=workflow.results,
        errors=workflow.errors,
        started_at=workflow.started_at,
        completed_at=workflow.completed_at,
        duration_seconds=workflow.duration_seconds,
        created_at=workflow.created_at
    )


@router.post("/{workflow_id}/cancel", response_model=WorkflowCancelResponse)
async def cancel_workflow_endpoint(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a running workflow.

    This will attempt to stop the workflow execution and mark it as cancelled.
    Note that if a step is already in progress, it may complete before cancellation.

    **Returns:**
    - success: Whether cancellation was successful
    - workflow_id: ID of the cancelled workflow
    - status: New status (cancelled)
    - message: Cancellation message
    """
    logger.info("workflow_api_cancel", workflow_id=workflow_id)

    workflow = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel workflow with status: {workflow.status}"
        )

    try:
        # Cancel via task
        result = cancel_workflow(workflow_id)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info("workflow_api_cancelled", workflow_id=workflow_id)

        return WorkflowCancelResponse(
            success=True,
            workflow_id=workflow_id,
            status="cancelled",
            message="Workflow cancelled successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("workflow_api_cancel_failed", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel workflow: {str(e)}"
        )


@router.get("/list", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str = Query(None, description="Filter by status"),
    workflow_type: str = Query(None, description="Filter by workflow type"),
    db: Session = Depends(get_db)
):
    """
    List all workflows with pagination and filtering.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - status: Filter by status (pending, running, completed, failed, cancelled)
    - workflow_type: Filter by type (one_click, scheduled, manual)

    **Example:**
    ```
    GET /workflow/list?page=1&page_size=20&status=completed
    ```

    **Returns:**
    - workflows: List of workflow status responses
    - total: Total number of workflows matching filters
    - page: Current page number
    - page_size: Items per page
    """
    logger.info(
        "workflow_api_list",
        page=page,
        page_size=page_size,
        status=status,
        workflow_type=workflow_type
    )

    # Build query
    query = db.query(WorkflowRun)

    if status:
        query = query.filter(WorkflowRun.status == status)

    if workflow_type:
        query = query.filter(WorkflowRun.workflow_type == workflow_type)

    # Get total count
    total = query.count()

    # Get paginated results
    workflows = query.order_by(desc(WorkflowRun.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # Convert to response models
    workflow_responses = [
        WorkflowStatusResponse(
            id=w.id,
            workflow_type=w.workflow_type,
            status=w.status,
            current_step=w.current_step,
            progress_percentage=w.progress_percentage or 0,
            steps=w.steps or {},
            statistics=WorkflowStatistics(
                keywords_researched=w.keywords_researched or 0,
                posts_created=w.posts_created or 0,
                posts_published=w.posts_published or 0,
                errors=w.errors_count or 0
            ),
            results=w.results,
            errors=w.errors,
            started_at=w.started_at,
            completed_at=w.completed_at,
            duration_seconds=w.duration_seconds,
            created_at=w.created_at
        )
        for w in workflows
    ]

    return WorkflowListResponse(
        workflows=workflow_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a workflow record.

    This will permanently delete the workflow record from the database.
    Can only delete workflows that are completed, failed, or cancelled.

    **Returns:**
    - success: Whether deletion was successful
    - workflow_id: ID of the deleted workflow
    - message: Deletion message
    """
    logger.info("workflow_api_delete", workflow_id=workflow_id)

    workflow = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete workflow that is pending or running. Cancel it first."
        )

    try:
        db.delete(workflow)
        db.commit()

        logger.info("workflow_api_deleted", workflow_id=workflow_id)

        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Workflow deleted successfully"
        }

    except Exception as e:
        logger.error("workflow_api_delete_failed", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete workflow: {str(e)}"
        )
