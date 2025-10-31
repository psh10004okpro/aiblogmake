"""
멀티 블로그 관리 서비스
여러 WordPress 사이트를 동시에 관리
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import base64
import requests
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.database import WordPressSite, SitePost, Post
from app.core.database import get_db

logger = logging.getLogger(__name__)


class MultiBlogService:
    """멀티 블로그 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def create_site(
        self,
        name: str,
        url: str,
        username: str,
        app_password: str,
        **kwargs
    ) -> WordPressSite:
        """새 WordPress 사이트 등록"""
        logger.info(f"Creating new WordPress site: {name}")

        # API URL 생성
        api_url = f"{url.rstrip('/')}/wp-json/wp/v2"

        # 사이트 생성
        site = WordPressSite(
            name=name,
            url=url,
            api_url=api_url,
            username=username,
            app_password=app_password,
            is_active=kwargs.get('is_active', True),
            default_category=kwargs.get('default_category', 'Uncategorized'),
            default_tags=kwargs.get('default_tags', []),
            auto_publish=kwargs.get('auto_publish', False),
            publish_delay_minutes=kwargs.get('publish_delay_minutes', 0),
            description=kwargs.get('description'),
            language=kwargs.get('language', 'ko'),
            timezone=kwargs.get('timezone', 'Asia/Seoul')
        )

        self.db.add(site)
        self.db.commit()
        self.db.refresh(site)

        logger.info(f"Created site: {site.id} - {site.name}")
        return site

    def get_site(self, site_id: int) -> Optional[WordPressSite]:
        """사이트 조회"""
        return self.db.query(WordPressSite).filter(WordPressSite.id == site_id).first()

    def list_sites(
        self,
        is_active: Optional[bool] = None,
        limit: int = 100
    ) -> List[WordPressSite]:
        """사이트 목록 조회"""
        query = self.db.query(WordPressSite)

        if is_active is not None:
            query = query.filter(WordPressSite.is_active == is_active)

        return query.order_by(WordPressSite.created_at.desc()).limit(limit).all()

    def update_site(
        self,
        site_id: int,
        **kwargs
    ) -> Optional[WordPressSite]:
        """사이트 정보 업데이트"""
        site = self.get_site(site_id)
        if not site:
            return None

        # 업데이트 가능한 필드
        updateable_fields = [
            'name', 'url', 'api_url', 'username', 'app_password',
            'is_active', 'default_category', 'default_tags',
            'auto_publish', 'publish_delay_minutes', 'description',
            'language', 'timezone'
        ]

        for field in updateable_fields:
            if field in kwargs:
                setattr(site, field, kwargs[field])

        self.db.commit()
        self.db.refresh(site)

        logger.info(f"Updated site: {site.id}")
        return site

    def delete_site(self, site_id: int) -> bool:
        """사이트 삭제"""
        site = self.get_site(site_id)
        if not site:
            return False

        self.db.delete(site)
        self.db.commit()

        logger.info(f"Deleted site: {site_id}")
        return True

    def test_connection(self, site_id: int) -> Dict[str, Any]:
        """WordPress 연결 테스트"""
        site = self.get_site(site_id)
        if not site:
            return {"success": False, "error": "Site not found"}

        try:
            # WordPress REST API에 요청
            auth_header = self._get_auth_header(site)
            response = requests.get(
                f"{site.api_url}/posts",
                headers={"Authorization": auth_header},
                params={"per_page": 1},
                timeout=10
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connection successful",
                    "site_info": {
                        "name": site.name,
                        "url": site.url,
                        "posts_count": response.headers.get('X-WP-Total', 'Unknown')
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            logger.error(f"Connection test failed for site {site_id}: {e}")
            return {"success": False, "error": str(e)}

    def publish_to_site(
        self,
        site_id: int,
        post_id: int,
        schedule_time: Optional[datetime] = None
    ) -> SitePost:
        """특정 사이트에 포스트 발행"""
        logger.info(f"Publishing post {post_id} to site {site_id}")

        site = self.get_site(site_id)
        post = self.db.query(Post).filter(Post.id == post_id).first()

        if not site:
            raise ValueError(f"Site {site_id} not found")
        if not post:
            raise ValueError(f"Post {post_id} not found")

        # SitePost 생성 또는 조회
        site_post = self.db.query(SitePost).filter(
            and_(SitePost.site_id == site_id, SitePost.post_id == post_id)
        ).first()

        if not site_post:
            site_post = SitePost(
                site_id=site_id,
                post_id=post_id,
                status="pending"
            )
            self.db.add(site_post)

        # 스케줄링
        if schedule_time:
            site_post.scheduled_for = schedule_time
            site_post.status = "pending"
        else:
            # 즉시 발행
            result = self._publish_to_wordpress(site, post, site_post)
            if result["success"]:
                site_post.status = "published"
                site_post.wp_post_id = result["wp_post_id"]
                site_post.wp_url = result["wp_url"]
                site_post.wp_status = result["wp_status"]
                site_post.published_at = datetime.utcnow()

                # 사이트 통계 업데이트
                site.total_posts_published += 1
                site.last_published_at = datetime.utcnow()
            else:
                site_post.status = "failed"
                site_post.error_message = result.get("error")

        self.db.commit()
        self.db.refresh(site_post)

        return site_post

    def publish_to_multiple_sites(
        self,
        post_id: int,
        site_ids: List[int],
        schedule_time: Optional[datetime] = None
    ) -> List[SitePost]:
        """여러 사이트에 동시 발행"""
        logger.info(f"Publishing post {post_id} to {len(site_ids)} sites")

        results = []
        for site_id in site_ids:
            try:
                site_post = self.publish_to_site(site_id, post_id, schedule_time)
                results.append(site_post)
            except Exception as e:
                logger.error(f"Failed to publish to site {site_id}: {e}")
                # 실패해도 계속 진행
                continue

        return results

    def publish_to_all_active_sites(
        self,
        post_id: int,
        schedule_time: Optional[datetime] = None
    ) -> List[SitePost]:
        """모든 활성 사이트에 발행"""
        active_sites = self.list_sites(is_active=True)
        site_ids = [site.id for site in active_sites]
        return self.publish_to_multiple_sites(post_id, site_ids, schedule_time)

    def get_site_posts(
        self,
        site_id: Optional[int] = None,
        post_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[SitePost]:
        """사이트별 포스트 목록 조회"""
        query = self.db.query(SitePost)

        if site_id:
            query = query.filter(SitePost.site_id == site_id)
        if post_id:
            query = query.filter(SitePost.post_id == post_id)
        if status:
            query = query.filter(SitePost.status == status)

        return query.order_by(SitePost.created_at.desc()).limit(limit).all()

    def get_site_statistics(self, site_id: int) -> Dict[str, Any]:
        """사이트 통계"""
        site = self.get_site(site_id)
        if not site:
            return {"error": "Site not found"}

        site_posts = self.get_site_posts(site_id=site_id)

        stats = {
            "site_id": site.id,
            "site_name": site.name,
            "total_posts": len(site_posts),
            "published": len([sp for sp in site_posts if sp.status == "published"]),
            "pending": len([sp for sp in site_posts if sp.status == "pending"]),
            "failed": len([sp for sp in site_posts if sp.status == "failed"]),
            "total_views": sum(sp.views for sp in site_posts),
            "total_clicks": sum(sp.clicks for sp in site_posts),
            "total_conversions": sum(sp.conversions for sp in site_posts),
            "last_published": site.last_published_at.isoformat() if site.last_published_at else None
        }

        return stats

    def get_all_sites_statistics(self) -> List[Dict[str, Any]]:
        """전체 사이트 통계"""
        sites = self.list_sites()
        return [self.get_site_statistics(site.id) for site in sites]

    def _get_auth_header(self, site: WordPressSite) -> str:
        """WordPress 인증 헤더 생성"""
        credentials = f"{site.username}:{site.app_password}"
        token = base64.b64encode(credentials.encode()).decode()
        return f"Basic {token}"

    def _publish_to_wordpress(
        self,
        site: WordPressSite,
        post: Post,
        site_post: SitePost
    ) -> Dict[str, Any]:
        """WordPress에 실제 발행"""
        try:
            auth_header = self._get_auth_header(site)

            # WordPress 포스트 데이터
            wp_post_data = {
                "title": post.title,
                "content": post.content,
                "status": "publish",
                "meta_description": post.meta_description,
                "categories": post.categories or [],
                "tags": site.default_tags or post.tags or []
            }

            # WordPress REST API 호출
            response = requests.post(
                f"{site.api_url}/posts",
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                },
                json=wp_post_data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "wp_post_id": data["id"],
                    "wp_url": data["link"],
                    "wp_status": data["status"]
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            logger.error(f"Failed to publish to WordPress: {e}")
            return {"success": False, "error": str(e)}


def get_multi_blog_service(db: Session) -> MultiBlogService:
    """멀티 블로그 서비스 인스턴스 반환"""
    return MultiBlogService(db)
