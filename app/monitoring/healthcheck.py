"""
Advanced health check system.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session_maker
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """Comprehensive health check system."""
    
    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "disk": self._check_disk,
            "memory": self._check_memory,
        }
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for name, check_func in self.checks.items():
            try:
                result = await asyncio.wait_for(check_func(), timeout=5.0)
                results[name] = result
                
                # Update overall status
                if result["status"] == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result["status"] == HealthStatus.DEGRADED and overall_status != HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    
            except asyncio.TimeoutError:
                results[name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "message": "Health check timed out",
                    "latency_ms": 5000
                }
                overall_status = HealthStatus.UNHEALTHY
            except Exception as e:
                logger.error(f"health_check_error service={name} error={str(e)}")
                results[name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"Health check failed: {str(e)}",
                }
                overall_status = HealthStatus.UNHEALTHY
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": results,
            "version": "1.0.0",
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        start_time = datetime.utcnow()
        
        try:
            session_maker = get_session_maker()
            async with session_maker() as session:
                # Simple ping query
                result = await session.execute(text("SELECT 1"))
                result.scalar()
                
                latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if latency > 1000:  # > 1 second
                    status = HealthStatus.DEGRADED
                    message = f"Database responding slowly ({latency:.0f}ms)"
                else:
                    status = HealthStatus.HEALTHY
                    message = "Database is healthy"
                
                return {
                    "status": status,
                    "message": message,
                    "latency_ms": round(latency, 2),
                }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database check failed: {str(e)}",
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        start_time = datetime.utcnow()
        
        try:
            redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            
            # Ping Redis
            await redis_client.ping()
            await redis_client.close()
            
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if latency > 500:  # > 500ms
                status = HealthStatus.DEGRADED
                message = f"Redis responding slowly ({latency:.0f}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis is healthy"
            
            return {
                "status": status,
                "message": message,
                "latency_ms": round(latency, 2),
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Redis check failed: {str(e)}",
            }
    
    async def _check_disk(self) -> Dict[str, Any]:
        """Check disk space."""
        try:
            import shutil
            
            usage = shutil.disk_usage("/")
            percent_used = (usage.used / usage.total) * 100
            
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Disk space critically low ({percent_used:.1f}% used)"
            elif percent_used > 80:
                status = HealthStatus.DEGRADED
                message = f"Disk space is low ({percent_used:.1f}% used)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk space is healthy ({percent_used:.1f}% used)"
            
            return {
                "status": status,
                "message": message,
                "percent_used": round(percent_used, 2),
                "total_gb": round(usage.total / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"Disk check failed: {str(e)}",
            }
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Memory critically high ({percent_used:.1f}% used)"
            elif percent_used > 80:
                status = HealthStatus.DEGRADED
                message = f"Memory usage is high ({percent_used:.1f}% used)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage is healthy ({percent_used:.1f}% used)"
            
            return {
                "status": status,
                "message": message,
                "percent_used": round(percent_used, 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
            }
        except ImportError:
            # psutil not installed
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Memory check skipped (psutil not installed)",
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"Memory check failed: {str(e)}",
            }
