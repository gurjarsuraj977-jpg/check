import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import CredentialRecord, AuditEvent, User
from app.auth.routes import current_user, require_csrf

router = APIRouter(prefix="/api/reporting", tags=["reporting"])
ALLOWED = {"not_reported", "report_pending", "reported", "deactivated", "resolved"}

class ReportStatusIn(BaseModel):
    status: str
    note: str = ""

@router.patch("/records/{record_id}")
async def update_report_status(record_id: int, data: ReportStatusIn, user: User = Depends(current_user), _: None = Depends(require_csrf), db: AsyncSession = Depends(get_db)):
    if data.status not in ALLOWED: raise HTTPException(400, "Invalid report status")
    if len(data.note) > 1000: raise HTTPException(400, "Note too long")
    record = await db.get(CredentialRecord, record_id)
    if not record: raise HTTPException(404, "Record not found")
    old = record.report_status
    record.report_status = data.status
    db.add(AuditEvent(user_id=user.id, event_type="REPORT_STATUS_CHANGED", key_reference=record.key_reference, batch_id=record.batch_id, metadata_json=json.dumps({"from": old, "to": data.status, "note": data.note})))
    await db.commit()
    return {"record_id": record.id, "status": record.report_status}
