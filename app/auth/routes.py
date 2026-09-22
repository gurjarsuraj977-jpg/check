from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, AuditEvent
from app.auth.service import hash_password, verify_password, create_session, revoke_session, get_session_user, login_blocked, record_login, verify_csrf
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE = "lab_session"
CSRF_COOKIE = "lab_csrf"

class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)

class BootstrapIn(LoginIn):
    bootstrap_token: str = Field(min_length=1, max_length=256)

@router.post("/bootstrap")
async def bootstrap(data: BootstrapIn, request: Request, db: AsyncSession = Depends(get_db)):
    if settings.environment == "production" and not settings.bootstrap_token:
        raise HTTPException(503, "Bootstrap is not configured")
    if not settings.bootstrap_token or not __import__('hmac').compare_digest(data.bootstrap_token, settings.bootstrap_token):
        raise HTTPException(403, "Invalid bootstrap token")
    result = await db.execute(select(User).limit(1))
    if result.scalar_one_or_none(): raise HTTPException(409, "Admin already initialized")
    user = User(username=data.username, password_hash=hash_password(data.password))
    db.add(user); await db.flush()
    db.add(AuditEvent(user_id=user.id, event_type="ADMIN_INITIALIZED"))
    await db.commit()
    return {"status": "initialized"}

@router.post("/login")
async def login(data: LoginIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if await login_blocked(db, data.username, ip):
        raise HTTPException(429, "Too many failed login attempts")
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        await record_login(db, data.username, ip, False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    await record_login(db, data.username, ip, True)
    token, csrf = await create_session(db, user.id)
    secure = settings.cookie_secure
    response.set_cookie(COOKIE, token, httponly=True, secure=secure, samesite="lax", max_age=43200, path="/")
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, secure=secure, samesite="lax", max_age=43200, path="/")
    db.add(AuditEvent(user_id=user.id, event_type="LOGIN")); await db.commit()
    return {"status": "authenticated", "username": user.username}

async def current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    user = await get_session_user(db, request.cookies.get(COOKIE))
    if not user: raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_csrf(request: Request, db: AsyncSession = Depends(get_db)) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}: return
    ok = await verify_csrf(db, request.cookies.get(COOKIE), request.headers.get("X-CSRF-Token") or request.cookies.get(CSRF_COOKIE))
    if not ok: raise HTTPException(403, "CSRF validation failed")

@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db), user: User = Depends(current_user), _: None = Depends(require_csrf)):
    await revoke_session(db, request.cookies.get(COOKIE))
    db.add(AuditEvent(user_id=user.id, event_type="LOGOUT")); await db.commit()
    response.delete_cookie(COOKIE, path="/"); response.delete_cookie(CSRF_COOKIE, path="/")
    return {"status": "logged_out"}

@router.get("/me")
async def me(user: User = Depends(current_user)):
    return {"id": user.id, "username": user.username}
