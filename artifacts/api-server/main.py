import os
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from routers import health, admin, threats, notifications, hellmode, godmode

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(threats.auto_update_loop())
    asyncio.create_task(_health_monitor())
    asyncio.create_task(_timebomb_watcher())
    await notifications.alert_server_start()
    yield


async def _health_monitor():
    import psutil
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            if cpu > 85:
                await notifications.alert_high_cpu(cpu)
            if mem > 90:
                await notifications.alert_high_memory(mem)
        except Exception:
            pass
        await asyncio.sleep(60)


async def _timebomb_watcher():
    """Check every second if a timebomb should trigger."""
    while True:
        action = godmode.check_timebomb()
        if action == "hell_mode":
            hellmode.activate_hell_mode()
            await notifications.send_discord("💣 TIMEBOMB TRIGGERED", "HELL MODE auto-activated by God Mode timebomb!", 0xff0000, "timebomb")
        elif action == "nuclear":
            godmode.activate_nuclear()
        elif action == "lockdown":
            godmode.set_kill_switch(True)
        await asyncio.sleep(1)


app = FastAPI(
    title="HELL 52",
    version="3.0.0",
    description="**Made by HELL 52** — GOD MODE EDITION",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def supreme_middleware(request: Request, call_next):
    start = time.time()
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown").split(",")[0].strip()
    path = request.url.path
    method = request.method

    # ── GOD BYPASS — skips ALL security ──────────────────────────────────────
    god_token = request.headers.get("X-God-Token", "")
    if godmode.is_god_bypass(god_token):
        response = await call_next(request)
        admin.log_request(ip, method, path, response.status_code, (time.time() - start) * 1000)
        return response

    # ── KILL SWITCH — block everything except static/panel ───────────────────
    if godmode.is_kill_switch() and path not in ("/api/admin/panel", "/api/status", "/api/healthz"):
        admin.log_request(ip, method, path, 503, 0)
        return JSONResponse(status_code=503, content={"detail": "Server in emergency lockdown", "brand": "HELL 52 ⚡"})

    # ── CUSTOM RESPONSE INJECTOR — God can control what specific IPs see ─────
    custom = godmode.get_custom_response(ip)
    if custom:
        admin.log_request(ip, method, path, 200, 0)
        return JSONResponse(content=custom)

    # ── NUCLEAR OPTION — block all non-whitelisted ────────────────────────────
    if godmode.is_nuclear() and not godmode.is_whitelisted(ip):
        admin.log_request(ip, method, path, 403, 0)
        return JSONResponse(status_code=403, content={"detail": "Nuclear lockdown active", "brand": "HELL 52 ⚡"})

    # ── IP WHITELIST — always passes through ─────────────────────────────────
    if godmode.is_whitelisted(ip):
        response = await call_next(request)
        admin.log_request(ip, method, path, response.status_code, (time.time() - start) * 1000)
        return response

    # ── COUNTRY BLACKLIST ─────────────────────────────────────────────────────
    ip_data = hellmode._ip_behavior.get(ip)
    if ip_data and ip_data.get("countryCode"):
        if godmode.is_country_blocked(ip_data["countryCode"]):
            admin.log_request(ip, method, path, 403, 0)
            return JSONResponse(status_code=403, content={"detail": f"Access denied from your region", "brand": "HELL 52 ⚡"})

    # ── ADMIN IP BLOCK ────────────────────────────────────────────────────────
    if admin.is_blocked(ip):
        hellmode.track_request(ip, path, 403)
        admin.log_request(ip, method, path, 403, 0)
        return FileResponse(os.path.join(STATIC_DIR, "404.html"), status_code=403)

    # ── HELL MODE AUTO-BLOCK ──────────────────────────────────────────────────
    if hellmode.should_auto_block(ip):
        admin.block_ip_direct(ip)
        hellmode.increment_auto_block()
        asyncio.create_task(notifications.alert_ip_blocked(ip))
        admin.log_request(ip, method, path, 403, 0)
        return JSONResponse(status_code=403, content={"detail": "Blocked by HELL MODE AI", "brand": "HELL 52 ⚡"})

    # ── RATE LIMITING ─────────────────────────────────────────────────────────
    limit = hellmode.get_rate_limit()
    if not admin.check_rate(ip, limit=limit):
        hellmode.track_request(ip, path, 429)
        admin.log_request(ip, method, path, 429, 0)
        asyncio.create_task(notifications.alert_rate_limited(ip, path))
        return JSONResponse(status_code=429, content={"detail": f"Rate limit exceeded ({limit}/min)", "brand": "HELL 52 ⚡"})

    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    hellmode.track_request(ip, path, response.status_code)
    asyncio.create_task(hellmode.enrich_ip(ip))
    admin.log_request(ip, method, path, response.status_code, duration_ms)
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api")
app.include_router(admin.router, prefix="/api/admin")
app.include_router(threats.router, prefix="/api")
app.include_router(notifications.router, prefix="/api/notifications")
app.include_router(hellmode.router, prefix="/api/hellmode")
app.include_router(godmode.router, prefix="/api/godmode")

if os.path.isdir(STATIC_DIR):
    app.mount("/api/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── Helpers ───────────────────────────────────────────────────────────────────
BADGE_HIDE = """<style>
iframe[src*="replit"],[class*="replit-badge"],[id*="replit-badge"],[class*="replitBadge"],[id*="replitBadge"],
a[href*="replit.com/@"],div[style*="z-index: 9999"] iframe,div[style*="z-index:9999"] iframe
{display:none!important;visibility:hidden!important;opacity:0!important;pointer-events:none!important;width:0!important;height:0!important;}
</style>"""

DOCS_CSS = """<style>
body{margin:0;background:#0a0a0a;}
.swagger-ui .topbar{background:#111!important;}
.swagger-ui .topbar .download-url-wrapper,.swagger-ui .topbar-wrapper img{display:none;}
.swagger-ui .topbar-wrapper::before{content:"⚡ HELL 52 API";color:#ff3333;font-size:22px;font-weight:900;letter-spacing:2px;padding-left:20px;}
.swagger-ui .info .title{color:#ff3333!important;}
.swagger-ui .info,.swagger-ui .scheme-container{background:#111!important;}
footer,.swagger-ui .footer{display:none!important;}
</style>"""


# ── Static pages ──────────────────────────────────────────────────────────────
@app.get("/api/admin/panel", include_in_schema=False)
async def admin_panel():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

@app.get("/api/status", include_in_schema=False)
async def status_page():
    return FileResponse(os.path.join(STATIC_DIR, "status.html"))

# ── Hell Mode controls ────────────────────────────────────────────────────────
@app.get("/api/admin/hell-stats", include_in_schema=False)
async def hell_stats_endpoint():
    return hellmode.get_hell_stats()

@app.post("/api/admin/hell-mode/activate", include_in_schema=False)
async def activate_hell(request: Request):
    if request.headers.get("X-Admin-Token", "") != admin.ADMIN_TOKEN:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    hellmode.activate_hell_mode()
    await notifications.send_discord("🔥 HELL MODE ACTIVATED", "Rate limit: **10/min** | Auto-block: **ON**", 0xff0000, "hell_activate")
    return {"status": "HELL MODE ACTIVATED", "rate_limit": 10}

@app.post("/api/admin/hell-mode/deactivate", include_in_schema=False)
async def deactivate_hell(request: Request):
    if request.headers.get("X-Admin-Token", "") != admin.ADMIN_TOKEN:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    hellmode.deactivate_hell_mode()
    return {"status": "HELL MODE DEACTIVATED", "rate_limit": 100}

# ── GOD MODE controls ─────────────────────────────────────────────────────────
@app.post("/api/god/verify", include_in_schema=False)
async def god_verify(request: Request):
    body = await request.json()
    if godmode.activate_god(body.get("key", "")):
        return {"status": "GOD MODE ACTIVATED", "bypass_token": godmode.GOD_BYPASS_TOKEN}
    return JSONResponse(status_code=403, content={"detail": "Wrong key, mortal."})

@app.get("/api/god/stats", include_in_schema=False)
async def god_stats(request: Request):
    if not _check_god(request):
        return JSONResponse(status_code=403, content={"detail": "God access required"})
    return godmode.get_god_stats()

@app.post("/api/god/nuclear/on", include_in_schema=False)
async def god_nuclear_on(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    godmode.activate_nuclear()
    await notifications.send_discord("☢️ NUCLEAR OPTION", "ALL non-whitelisted IPs are now blocked!", 0xff0000, "nuclear")
    return {"status": "Nuclear active"}

@app.post("/api/god/nuclear/off", include_in_schema=False)
async def god_nuclear_off(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    godmode.deactivate_nuclear()
    return {"status": "Nuclear deactivated"}

@app.post("/api/god/killswitch/on", include_in_schema=False)
async def god_kill_on(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    godmode.set_kill_switch(True)
    await notifications.send_discord("🔴 KILL SWITCH ON", "Server in emergency lockdown!", 0xff0000, "killswitch")
    return {"status": "Kill switch ON — emergency lockdown"}

@app.post("/api/god/killswitch/off", include_in_schema=False)
async def god_kill_off(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    godmode.set_kill_switch(False)
    return {"status": "Kill switch OFF"}

@app.post("/api/god/country/block", include_in_schema=False)
async def god_country_block(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    body = await request.json()
    godmode.blacklist_country(body.get("code", ""))
    return {"blocked": body.get("code", "").upper()}

@app.post("/api/god/country/unblock", include_in_schema=False)
async def god_country_unblock(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    body = await request.json()
    godmode.unblacklist_country(body.get("code", ""))
    return {"unblocked": body.get("code", "").upper()}

@app.post("/api/god/whitelist/add", include_in_schema=False)
async def god_whitelist_add(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    body = await request.json()
    godmode.whitelist_ip(body.get("ip", ""))
    return {"whitelisted": body.get("ip", "")}

@app.post("/api/god/whitelist/remove", include_in_schema=False)
async def god_whitelist_remove(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    body = await request.json()
    godmode.unwhitelist_ip(body.get("ip", ""))
    return {"removed": body.get("ip", "")}

@app.post("/api/god/inject", include_in_schema=False)
async def god_inject(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    body = await request.json()
    godmode.set_custom_response(body.get("ip", ""), body.get("response", {}))
    return {"injected": body.get("ip", "")}

@app.delete("/api/god/inject/{ip}", include_in_schema=False)
async def god_inject_clear(ip: str, request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    godmode.clear_custom_response(ip)
    return {"cleared": ip}

@app.post("/api/god/timebomb", include_in_schema=False)
async def god_timebomb(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    body = await request.json()
    godmode.set_timebomb(int(body.get("seconds", 60)), body.get("action", "hell_mode"))
    return {"timebomb": "SET", "seconds": body.get("seconds"), "action": body.get("action")}

@app.delete("/api/god/timebomb", include_in_schema=False)
async def god_timebomb_cancel(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    godmode.cancel_timebomb()
    return {"timebomb": "CANCELLED"}

@app.post("/api/god/resurrection", include_in_schema=False)
async def god_resurrection(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    godmode.resurrection()
    await notifications.send_discord("🌅 RESURRECTION", "All blocks cleared by God Mode!", 0xffcc00, "resurrection")
    return {"status": "All blocks cleared. Server reborn."}

@app.post("/api/god/deactivate", include_in_schema=False)
async def god_deactivate(request: Request):
    if not _check_god(request): return JSONResponse(status_code=403, content={"detail": "God access required"})
    godmode.deactivate_god()
    return {"status": "God Mode deactivated"}


def _check_god(request: Request) -> bool:
    return (
        godmode.is_god_active() and
        request.headers.get("X-God-Token", "") == godmode.GOD_BYPASS_TOKEN
    )


# ── Docs ──────────────────────────────────────────────────────────────────────
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui():
    html = get_swagger_ui_html(openapi_url="/api/openapi.json", title="HELL 52 — API Docs")
    body = html.body.decode("utf-8").replace("</head>", f"{DOCS_CSS}{BADGE_HIDE}</head>")
    return HTMLResponse(content=body)

@app.get("/api/redoc", include_in_schema=False)
async def custom_redoc():
    html = get_redoc_html(openapi_url="/api/openapi.json", title="HELL 52 — ReDoc")
    body = html.body.decode("utf-8").replace("</head>", f"{DOCS_CSS}{BADGE_HIDE}</head>")
    return HTMLResponse(content=body)

@app.get("/api", include_in_schema=False)
async def api_root():
    return RedirectResponse(url="/api/admin/panel")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=404, content={"detail": "Not found", "brand": "HELL 52 ⚡"})
    return FileResponse(os.path.join(STATIC_DIR, "404.html"), status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "brand": "HELL 52 ⚡"})
