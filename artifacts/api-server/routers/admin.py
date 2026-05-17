import os
import time
import platform
import psutil
from fastapi import APIRouter
from sqlalchemy import text

from database import engine

router = APIRouter(tags=["admin"])

START_TIME = time.time()
REQUEST_COUNT = {"total": 0}


@router.get("/stats")
async def get_stats():
    uptime_seconds = int(time.time() - START_TIME)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60

    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()

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
            db_message = str(e)[:80]

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
        },
        "database": {
            "status": db_status,
            "message": db_message,
            "provider": "Supabase PostgreSQL",
        },
        "endpoints": [
            {"method": "GET", "path": "/api/healthz", "description": "Health check"},
            {"method": "GET", "path": "/api/admin/stats", "description": "Server stats"},
            {"method": "GET", "path": "/api/docs", "description": "Swagger UI"},
            {"method": "GET", "path": "/api/redoc", "description": "ReDoc"},
        ],
    }
