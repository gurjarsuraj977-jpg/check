from datetime import datetime, timedelta, timezone
import base64, hashlib, hmac, secrets
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, SessionRecord, LoginAttempt
from app.security import hash_token, random_token
from app.config import settings

SESSION_TTL = timedelta(hours=12)
PBKDF2_ROUNDS = 600_000

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt_b64, digest_b64 = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256": return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def _ip_hash(ip: str) -> str:
    return hmac.new(settings.fingerprint_key.encode(), ip.encode(), hashlib.sha256).hexdigest()

async def login_blocked(db: AsyncSession, username: str, ip: str) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.login_window_seconds)
    result = await db.execute(select(func.count(LoginAttempt.id)).where(
        LoginAttempt.username == username,
        LoginAttempt.ip_hash == _ip_hash(ip),
        LoginAttempt.succeeded.is_(False),
        LoginAttempt.created_at >= cutoff,
    ))
    return (result.scalar_one() or 0) >= settings.login_max_failures

async def record_login(db: AsyncSession, username: str, ip: str, succeeded: bool) -> None:
    db.add(LoginAttempt(username=username, ip_hash=_ip_hash(ip), succeeded=succeeded, created_at=datetime.now(timezone.utc)))
    await db.commit()

async def create_session(db: AsyncSession, user_id: int) -> tuple[str, str]:
    raw = random_token()
    csrf = random_token()
    now = datetime.now(timezone.utc)
    db.add(SessionRecord(user_id=user_id, token_hash=hash_token(raw), csrf_hash=hash_token(csrf), expires_at=now + SESSION_TTL))
    await db.commit()
    return raw, csrf

async def get_session(db: AsyncSession, raw_token: str | None) -> SessionRecord | None:
    if not raw_token: return None
    now = datetime.now(timezone.utc)
    result = await db.execute(select(SessionRecord).where(SessionRecord.token_hash == hash_token(raw_token)))
    session = result.scalar_one_or_none()
    if not session or session.expires_at <= now:
        if session:
            await db.delete(session); await db.commit()
        return None
    return session

async def get_session_user(db: AsyncSession, raw_token: str | None) -> User | None:
    session = await get_session(db, raw_token)
    if not session: return None
    result = await db.execute(select(User).where(User.id == session.user_id))
    return result.scalar_one_or_none()

async def verify_csrf(db: AsyncSession, raw_token: str | None, csrf_token: str | None) -> bool:
    session = await get_session(db, raw_token)
    return bool(session and csrf_token and hmac.compare_digest(session.csrf_hash, hash_token(csrf_token)))

async def revoke_session(db: AsyncSession, raw_token: str | None) -> None:
    if not raw_token: return
    await db.execute(delete(SessionRecord).where(SessionRecord.token_hash == hash_token(raw_token)))
    await db.commit()
