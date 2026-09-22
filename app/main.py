from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.auth.routes import router as auth_router
from app.batches.routes import router as batch_router
from app.dashboard.routes import router as dashboard_router
from app.workers.routes import router as worker_router
from app.audit.routes import router as audit_router
from app.reporting.routes import router as reporting_router
from app.security_ext.middleware import SecurityHeadersMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Private Security Lab", version="1.0.0", lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)
app.include_router(auth_router)
app.include_router(batch_router)
app.include_router(dashboard_router)
app.include_router(worker_router)
app.include_router(audit_router)
app.include_router(reporting_router)
app.mount("/static", StaticFiles(directory="public"), name="static")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "private-security-lab", "version": "1.0.0"}

@app.get("/", include_in_schema=False)
async def home():
    return FileResponse("public/index.html")
