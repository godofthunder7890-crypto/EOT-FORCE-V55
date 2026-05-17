import os
import time
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["notifications"])

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
_alert_log = []
_last_alert = {}
_alert_cooldown = 300  # 5 min cooldown per alert type


async def send_discord(title: str, message: str, color: int = 0xff3333, alert_type: str = "general"):
    now = time.time()
    if alert_type in _last_alert and now - _last_alert[alert_type] < _alert_cooldown:
        return False

    _alert_log.append({"type": alert_type, "title": title, "message": message, "time": time.strftime("%H:%M:%S"), "timestamp": now})
    _last_alert[alert_type] = now

    if not DISCORD_WEBHOOK:
        return False

    payload = {
        "embeds": [{
            "title": f"⚡ HELL 52 — {title}",
            "description": message,
            "color": color,
            "footer": {"text": "HELL 52 API Monitor"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }]
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(DISCORD_WEBHOOK, json=payload)
            return r.status_code == 204
    except Exception:
        return False


async def alert_ip_blocked(ip: str):
    await send_discord("🚫 IP Blocked", f"IP **{ip}** has been blocked by admin.", 0xff6600, f"block_{ip}")


async def alert_rate_limited(ip: str, path: str):
    await send_discord("🚦 Rate Limit Hit", f"IP **{ip}** hit rate limit on `{path}`", 0xffcc00, f"rate_{ip}")


async def alert_high_cpu(cpu: float):
    await send_discord("🔥 High CPU Alert", f"CPU usage is at **{cpu}%** — server under load!", 0xff3333, "high_cpu")


async def alert_high_memory(mem: float):
    await send_discord("💾 High Memory Alert", f"Memory usage is at **{mem}%** — watch out!", 0xff9900, "high_mem")


async def alert_db_error(msg: str):
    await send_discord("🗄 Database Error", f"Database connection failed:\n```{msg}```", 0xff0000, "db_error")


async def alert_server_start():
    await send_discord("✅ Server Started", "HELL 52 API server has started successfully!", 0x00ff88, "startup")


def get_alert_log():
    return _alert_log[-50:]


class WebhookUpdate(BaseModel):
    url: str


@router.get("/alerts")
async def get_alerts(request):
    from routers.admin import ADMIN_TOKEN
    token = request.headers.get("X-Admin-Token", "")
    if token != ADMIN_TOKEN:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"alerts": get_alert_log(), "webhook_active": bool(DISCORD_WEBHOOK)}


@router.get("/status")
async def webhook_status():
    return {"webhook_configured": bool(DISCORD_WEBHOOK), "total_alerts": len(_alert_log)}
