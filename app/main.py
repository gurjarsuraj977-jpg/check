from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Private Security Lab", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "private-security-lab"}

@app.get("/", response_class=HTMLResponse)
async def index():
    return """<!doctype html><html><head><meta charset='utf-8'><title>Security Lab</title></head><body><h1>Private Security Lab</h1><p>Foundation is running.</p></body></html>"""
