from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Batch, User
from app.auth.routes import current_user
from .manager import worker_manager

router = APIRouter(prefix="/api/batches", tags=["workers"])

@router.post("/{batch_id}/start")
async def start_batch(batch_id: int, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    if batch.status in {"completed", "cancelled", "empty"}:
        raise HTTPException(409, f"Batch is {batch.status}")
    started = await worker_manager.start(batch_id)
    return {"started": started, "status": "running" if started else "already_running"}

@router.post("/{batch_id}/stop")
async def stop_batch(batch_id: int, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    if batch.status in {"completed", "cancelled", "empty"}:
        return {"status": batch.status}
    await worker_manager.cancel(batch_id)
    return {"status": "cancellation_requested"}

@router.get("/{batch_id}/progress")
async def batch_progress(batch_id: int, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    return {
        "batch_id": batch.id,
        "reference": batch.batch_reference,
        "total": batch.total,
        "processed": batch.processed,
        "remaining": max(batch.total - batch.processed, 0),
        "status": batch.status,
    }
