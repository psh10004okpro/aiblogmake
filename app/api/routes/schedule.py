"""
Scheduling API routes.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.schemas import ScheduleTaskRequest, ScheduleTaskResponse
from app.models.database import ScheduledTask
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post("/", response_model=ScheduleTaskResponse)
async def schedule_task(
    request: ScheduleTaskRequest,
    db: AsyncSession = Depends(get_db)
):
    """Schedule a new task."""
    logger.info("scheduling_task", task_name=request.task_name)

    try:
        task = ScheduledTask(
            task_name=request.task_name,
            task_type=request.task_type,
            schedule_time=request.schedule_time,
            params=request.params,
            status="pending"
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        return ScheduleTaskResponse.model_validate(task)

    except Exception as e:
        logger.error("task_scheduling_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task scheduling failed: {str(e)}"
        )


@router.get("/", response_model=List[ScheduleTaskResponse])
async def get_scheduled_tasks(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all scheduled tasks."""
    query = select(ScheduledTask).order_by(ScheduledTask.schedule_time.desc())

    if status:
        query = query.where(ScheduledTask.status == status)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return [ScheduleTaskResponse.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=ScheduleTaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific scheduled task."""
    result = await db.execute(
        select(ScheduledTask).where(ScheduledTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )

    return ScheduleTaskResponse.model_validate(task)


@router.delete("/{task_id}")
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a scheduled task."""
    result = await db.execute(
        select(ScheduledTask).where(ScheduledTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )

    task.status = "cancelled"
    await db.commit()

    return {"message": f"Task {task_id} cancelled successfully"}
