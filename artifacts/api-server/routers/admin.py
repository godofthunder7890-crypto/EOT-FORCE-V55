import os
import time
import platform
import psutil
from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text

from database import engine

router = APIRouter(tags=["admin"])

START_TIME = time.time()
_request_log = []

ADMIN_KEY = os.environ.get("ADMIN_SECRET_KEY", "hell52-admin-2024")


def require_admin(x_admin_key: str = Header(default="")):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key. Set X-Admin-Key header.")


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
        },
        "endpoints": [
            {"method": "GET",  "path": "/api/healthz",         "description": "Health check"},
            {"method": "GET",  "path": "/api/admin/stats",     "description": "Server stats"},
            {"method": "GET",  "path": "/api/threats",         "description": "Threat intelligence"},
            {"method": "POST", "path": "/api/threats/refresh", "description": "Force threat DB update"},
            {"method": "GET",  "path": "/api/docs",            "description": "Swagger UI"},
            {"method": "GET",  "path": "/api/redoc",           "description": "ReDoc"},
            {"method": "GET",  "path": "/api/admin/panel",     "description": "Admin Dashboard"},
        ],
    }
