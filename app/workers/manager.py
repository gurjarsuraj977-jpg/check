import asyncio
from datetime import datetime
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Batch, CredentialRecord, AuditEvent
from app.security import decrypt
from .adapter import VerificationAdapter, SandboxFixtureAdapter

TERMINAL_BATCHES = {"completed", "cancelled", "empty"}

class WorkerManager:
    def __init__(self, concurrency: int = 4, adapter: VerificationAdapter | None = None):
        if concurrency < 1 or concurrency > 20:
            raise ValueError("concurrency must be between 1 and 20")
        self.concurrency = concurrency
        self.adapter = adapter or SandboxFixtureAdapter()
        self._tasks: dict[int, asyncio.Task] = {}
        self._cancel: dict[int, asyncio.Event] = {}
        self._lock = asyncio.Lock()

    async def start(self, batch_id: int) -> bool:
        async with self._lock:
            task = self._tasks.get(batch_id)
            if task and not task.done():
                return False
            event = asyncio.Event()
            self._cancel[batch_id] = event
            task = asyncio.create_task(self._run(batch_id, event), name=f"batch-{batch_id}")
            self._tasks[batch_id] = task
            return True

    async def cancel(self, batch_id: int) -> bool:
        event = self._cancel.get(batch_id)
        if event:
            event.set()
            return True
        return False

    async def _run(self, batch_id: int, cancel: asyncio.Event):
        try:
            async with SessionLocal() as db:
                batch = await db.get(Batch, batch_id)
                if not batch or batch.status in TERMINAL_BATCHES:
                    return
                batch.status = "running"
                db.add(AuditEvent(event_type="BATCH_STARTED", batch_id=batch_id))
                await db.commit()

            while True:
                if cancel.is_set():
                    await self._mark_cancelled(batch_id)
                    return
                async with SessionLocal() as db:
                    batch = await db.get(Batch, batch_id)
                    if not batch or batch.status == "cancelled":
                        return
                    result = await db.execute(
                        select(CredentialRecord)
                        .where(CredentialRecord.batch_id == batch_id, CredentialRecord.status == "pending")
                        .order_by(CredentialRecord.id)
                        .limit(self.concurrency)
                    )
                    records = result.scalars().all()
                    if not records:
                        batch.status = "completed"
                        batch.completed_at = datetime.utcnow()
                        db.add(AuditEvent(event_type="BATCH_COMPLETED", batch_id=batch_id))
                        await db.commit()
                        return
                    await db.commit()

                semaphore = asyncio.Semaphore(self.concurrency)
                await asyncio.gather(*(self._process_one(batch_id, r.id, semaphore, cancel) for r in records))
        except asyncio.CancelledError:
            await self._mark_cancelled(batch_id)
            raise
        finally:
            self._tasks.pop(batch_id, None)
            self._cancel.pop(batch_id, None)

    async def _process_one(self, batch_id: int, record_id: int, semaphore: asyncio.Semaphore, cancel: asyncio.Event):
        async with semaphore:
            if cancel.is_set():
                return
            async with SessionLocal() as db:
                record = await db.get(CredentialRecord, record_id)
                if not record or record.status != "pending":
                    return
                try:
                    secret = decrypt(record.encrypted_value)
                    result = await asyncio.wait_for(self.adapter.verify(secret), timeout=10)
                    record.status = result.status
                except asyncio.TimeoutError:
                    record.status = "timeout"
                except Exception:
                    record.status = "worker_error"
                record.tested_at = datetime.utcnow()
                batch = await db.get(Batch, batch_id)
                if batch:
                    batch.processed = batch.processed + 1
                db.add(AuditEvent(event_type="RECORD_PROCESSED", key_reference=record.key_reference, batch_id=batch_id))
                await db.commit()

    async def _mark_cancelled(self, batch_id: int):
        async with SessionLocal() as db:
            batch = await db.get(Batch, batch_id)
            if batch and batch.status not in TERMINAL_BATCHES:
                batch.status = "cancelled"
                db.add(AuditEvent(event_type="BATCH_CANCELLED", batch_id=batch_id))
                await db.commit()

worker_manager = WorkerManager()
