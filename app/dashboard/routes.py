from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Batch, CredentialRecord, AuditEvent, User
from app.auth.routes import current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary")
async def summary(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    batches = await db.scalar(select(func.count()).select_from(Batch)) or 0
    records = await db.scalar(select(func.count()).select_from(CredentialRecord)) or 0
    pending = await db.scalar(select(func.count()).select_from(CredentialRecord).where(CredentialRecord.status == "pending")) or 0
    return {"batches": batches, "records": records, "pending": pending}
