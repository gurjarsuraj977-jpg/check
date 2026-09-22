from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Batch, CredentialRecord, AuditEvent, User
from app.auth.routes import current_user
from app.batches.service import validate_batch_size
from app.security import fingerprint, encrypt

router = APIRouter(prefix="/api/batches", tags=["batches"])

class BatchCreate(BaseModel):
    records: list[str] = Field(min_length=1, max_length=100)

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_batch(data: BatchCreate, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    try:
        validate_batch_size(data.records)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    batch = Batch(batch_reference=f"B-{uuid4().hex[:12].upper()}", total=len(data.records), status="queued")
    db.add(batch)
    await db.flush()

    seen = set()
    created = 0
    duplicate_count = 0
    for value in data.records:
        value = value.strip()
        if not value:
            continue
        fp = fingerprint(value)
        if fp in seen:
            duplicate_count += 1
            continue
        seen.add(fp)
        exists = await db.execute(select(CredentialRecord.id).where(CredentialRecord.fingerprint == fp).limit(1))
        if exists.scalar_one_or_none() is not None:
            duplicate_count += 1
            continue
        db.add(CredentialRecord(
            batch_id=batch.id,
            key_reference=f"K-{uuid4().hex[:12].upper()}",
            encrypted_value=encrypt(value),
            fingerprint=fp,
            status="pending",
        ))
        created += 1

    batch.total = created
    batch.status = "queued" if created else "empty"
    db.add(AuditEvent(user_id=user.id, event_type="BATCH_CREATED", batch_id=batch.id))
    await db.commit()
    return {"batch_id": batch.id, "batch_reference": batch.batch_reference, "accepted": created, "duplicates": duplicate_count, "status": batch.status}

@router.get("")
async def list_batches(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Batch).order_by(Batch.created_at.desc()).limit(100))
    return [{"id": b.id, "reference": b.batch_reference, "total": b.total, "processed": b.processed, "status": b.status, "created_at": b.created_at} for b in result.scalars()]

@router.get("/{batch_id}")
async def get_batch(batch_id: int, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    result = await db.execute(select(CredentialRecord).where(CredentialRecord.batch_id == batch.id).order_by(CredentialRecord.created_at))
    records = result.scalars().all()
    return {"id": batch.id, "reference": batch.batch_reference, "total": batch.total, "processed": batch.processed, "status": batch.status,
            "records": [{"reference": r.key_reference, "status": r.status, "report_status": r.report_status, "created_at": r.created_at, "tested_at": r.tested_at} for r in records]}

@router.post("/{batch_id}/cancel")
async def cancel_batch(batch_id: int, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status in {"completed", "cancelled", "empty"}:
        return {"status": batch.status}
    batch.status = "cancelled"
    db.add(AuditEvent(user_id=user.id, event_type="BATCH_CANCELLED", batch_id=batch.id))
    await db.commit()
    return {"status": "cancelled"}


@router.delete("/{batch_id}/records/{record_id}")
async def delete_record(batch_id: int, record_id: int, confirmation: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    """Destroy the stored secret while retaining a non-secret audit/evidence record."""
    record = await db.scalar(select(CredentialRecord).where(
        CredentialRecord.id == record_id, CredentialRecord.batch_id == batch_id
    ))
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.deleted_at is not None:
        return {"status": "already_deleted", "reference": record.key_reference}
    if confirmation != record.key_reference:
        raise HTTPException(status_code=400, detail="Confirmation reference does not match")

    # Cryptographic destruction: the plaintext secret is removed from the database.
    # Fingerprint/reference remain so the same secret is still recognized as processed.
    record.encrypted_value = ""
    record.deleted_at = datetime.utcnow()
    record.deleted_by = user.id
    record.status = "deleted"
    db.add(AuditEvent(user_id=user.id, event_type="CREDENTIAL_DESTROYED",
                      key_reference=record.key_reference, batch_id=batch_id))
    await db.commit()
    return {"status": "deleted", "reference": record.key_reference}
