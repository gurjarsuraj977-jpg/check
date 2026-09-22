from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import AuditEvent, User
from app.auth.routes import current_user

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("")
async def list_audit(limit: int = Query(100, ge=1, le=500), user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit))
    return [{"id": e.id, "event_type": e.event_type, "user_id": e.user_id, "batch_id": e.batch_id, "key_reference": e.key_reference, "metadata": e.metadata_json, "created_at": e.created_at} for e in result.scalars()]
