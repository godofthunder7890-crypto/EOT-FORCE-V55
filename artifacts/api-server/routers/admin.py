import os
import time
import platform
import psutil
from collections import deque
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from database import engine

router = APIRouter(tags=["admin"])

START_TIME = time.time()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "hell52secret")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "hell52-token-xK9mP2vQ")

_request_log = deque(maxlen=200)
_blocked_ips = set()
_rate_tracker = {}


def log_request(ip: str, method: str, path: str, status: int, duration_ms: float):
    _request_log.appendleft({
        "ip": ip,
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": round(duration_ms, 1),
        "time": time.strftime("%H:%M:%S"),
        "timestamp": time.time(),
    })


def is_blocked(ip: str) -> bool:
    return ip in _blocked_ips


def block_ip_direct(ip: str):
    _blocked_ips.add(ip)


def check_rate(ip: str, limit: int = 60) -> bool:
    now = time.time()
    window = 60
    if ip not in _rate_tracker:
        _rate_tracker[ip] = []
    _rate_tracker[ip] = [t for t in _rate_tracker[ip] if now - t < window]
    if len(_rate_tracker[ip]) >= limit:
        return False
    _rate_tracker[ip].append(now)
    return True


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
async def admin_login(body: LoginRequest):
    if body.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Wrong password")
    return {"token": ADMIN_TOKEN, "status": "ok"}


@router.post("/verify")
async def verify_token(request: Request):
    token = request.headers.get("X-Admin-Token", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"valid": True}


@router.get("/stats")
async def get_stats():
    uptime_seconds = int(time.time() - START_TIME)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60

    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    db_status = "disconnected"
    db_message = "SUPABASE_DATABASE_URL not set"
    if engine:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "connected"
            db_message = "Supabase PostgreSQL — OK"
        except Exception as e:
            db_status = "error"
            db_message = str(e)[:100]

    from routers.threats import get_cache
    threat_cache = get_cache()

    total_reqs = len(_request_log)
    blocked_reqs = sum(1 for r in _request_log if r["status"] == 429)

    return {
        "server": {
            "name": "HELL 52 API",
            "version": "1.0.0",
            "uptime": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "uptime_seconds": uptime_seconds,
            "python": platform.python_version(),
            "platform": platform.system(),
        },
        "system": {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_mb": round(mem.used / 1024 / 1024, 1),
            "memory_total_mb": round(mem.total / 1024 / 1024, 1),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
        },
        "database": {
            "status": db_status,
            "message": db_message,
            "provider": "Supabase PostgreSQL",
        },
        "security": {
            "threat_db_count": len(threat_cache.get("threats", [])),
            "power_level": threat_cache.get("power_level", 1.0),
            "threat_updates": threat_cache.get("update_count", 0),
            "last_threat_update": int(time.time() - threat_cache.get("last_updated", time.time())),
            "total_requests": total_reqs,
            "blocked_requests": blocked_reqs,
            "blocked_ips": len(_blocked_ips),
        },
        "endpoints": [
            {"method": "GET",  "path": "/api/healthz",         "description": "Health check"},
            {"method": "GET",  "path": "/api/admin/stats",     "description": "Server stats"},
            {"method": "GET",  "path": "/api/admin/logs",      "description": "Request logs"},
            {"method": "GET",  "path": "/api/threats",         "description": "Threat intelligence"},
            {"method": "POST", "path": "/api/threats/refresh", "description": "Force threat DB update"},
            {"method": "GET",  "path": "/api/docs",            "description": "Swagger UI"},
            {"method": "GET",  "path": "/api/admin/panel",     "description": "Admin Dashboard"},
        ],
    }


@router.get("/logs")
async def get_logs(limit: int = 100):
    logs = list(_request_log)[:limit]
    unique_ips = list(set(r["ip"] for r in logs))
    return {
        "total": len(logs),
        "unique_ips": len(unique_ips),
        "blocked_ips": list(_blocked_ips),
        "logs": logs,
    }


class BlockIPRequest(BaseModel):
    ip: str


@router.post("/block-ip")
async def block_ip(body: BlockIPRequest, request: Request):
    token = request.headers.get("X-Admin-Token", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    _blocked_ips.add(body.ip)
    from routers.notifications import alert_ip_blocked
    import asyncio
    asyncio.create_task(alert_ip_blocked(body.ip))
    return {"status": "blocked", "ip": body.ip}


@router.post("/unblock-ip")
async def unblock_ip(body: BlockIPRequest, request: Request):
    token = request.headers.get("X-Admin-Token", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    _blocked_ips.discard(body.ip)
    return {"status": "unblocked", "ip": body.ip}
