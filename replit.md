# HELL 52 — Admin Server (FastAPI + Supabase)

Full-featured admin backend with HELL MODE, GOD MODE, threat intelligence, IP tracking, rate limiting, and real-time monitoring. Made by HELL 52.

## Live URLs

- **Admin Panel:** `https://eot-force-v55-api.onrender.com/api/admin/panel`
- **Status Page:** `https://eot-force-v55-api.onrender.com/api/status`
- **API Docs:** `https://eot-force-v55-api.onrender.com/api/docs`
- **Health Check:** `https://eot-force-v55-api.onrender.com/api/healthz`

## Run & Operate

- Server auto-starts via workflow on port 8080
- Dev command: `cd artifacts/api-server && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080`
- Local health check: `curl http://localhost:80/api/healthz`
- Render service: `srv-d84v2cj7uimc7383hm4g` (eot-force-v55-api)

## Credentials

| What | Value | Override via |
|------|-------|-------------|
| Admin Password | `hell52secret` | `ADMIN_PASSWORD` env var |
| Admin Token | `hell52-token-xK9mP2vQ` | `ADMIN_TOKEN` env var |
| GOD KEY | `HELL52-GOD-ULTRA-9999` | `GOD_MODE_KEY` env var |
| GOD Bypass Token | `GOD52-BYPASS-ALL-9999` | `GOD_BYPASS_TOKEN` env var |

**To activate GOD MODE:** Login → click H52 logo 5 times rapidly → enter GOD KEY

## Stack

- Python 3.11
- FastAPI + Uvicorn (2 workers on Render)
- SQLAlchemy (async) + asyncpg
- Pydantic v2
- Supabase (PostgreSQL)
- httpx (geo-IP + threat intel fetching)
- psutil (system monitoring)

## Where things live

```
artifacts/api-server/
├── main.py              — FastAPI app + full security middleware chain
├── database.py          — SQLAlchemy + Supabase connection
├── schemas.py           — Pydantic request/response models
├── requirements.txt     — Python dependencies
├── routers/
│   ├── health.py        — /api/healthz
│   ├── admin.py         — Stats, logs, IP block/unblock, login
│   ├── threats.py       — Threat intelligence (auto-updates hourly)
│   ├── hellmode.py      — HELL MODE AI behavior scoring + geo-IP
│   ├── godmode.py       — GOD MODE supreme control system
│   └── notifications.py — Discord webhook alerts
└── static/
    ├── admin.html       — Full admin dashboard UI
    ├── status.html      — Public status page
    └── 404.html         — Custom 404 page
```

## Security Middleware Chain (in order)

1. **GOD Bypass Token** — `X-God-Token` header skips everything
2. **Kill Switch** — locks entire server (GOD MODE)
3. **Custom Response Injector** — specific IPs get custom JSON (GOD MODE)
4. **Nuclear Option** — blocks all non-whitelisted IPs (GOD MODE)
5. **IP Whitelist** — whitelisted IPs bypass all security (GOD MODE)
6. **Country Blacklist** — banned countries blocked (GOD MODE)
7. **Admin IP Block** — manually blocked IPs
8. **HELL MODE Auto-Block** — AI score ≥ 70 → auto-block
9. **Rate Limiting** — 100/min normal, 10/min in HELL MODE

## Features

### Admin Dashboard
- Real-time CPU/memory/disk charts (Chart.js)
- System power level (grows with threat DB updates)
- Request logger (last 200 requests, IP + method + path + status + speed)
- IP tracker with manual block/unblock

### HELL MODE
- AI behavior scoring per IP (0-100)
- Geo-IP enrichment via ip-api.com (country, city, ISP, VPN/proxy detection)
- Auto-block IPs with score ≥ 70 when active
- Rate limit drops to 10 req/min
- Live threat leaderboard + attack origin world map

### GOD MODE (owner-only)
- Secret activation: click H52 logo 5x → enter GOD KEY
- Nuclear Option, Kill Switch, IP Whitelist, Country Blacklist
- Custom Response Injector (force specific IPs to get custom JSON)
- Time Bomb (schedule HELL MODE / nuclear / lockdown)
- Resurrection (clear all blocks instantly)
- UI turns gold when active
- God Bypass Token in request header bypasses all middleware

### Threat Intelligence
- Auto-fetches from internet every hour
- Sources: NVD CVE feed, CISA advisories, AlienVault OTX
- Power level increases with each update cycle

### Alerts (Discord Webhook)
- Set `DISCORD_WEBHOOK_URL` on Render to enable
- Alerts on: IP blocked, rate limit hit, high CPU/memory, server start, HELL MODE/GOD MODE activation

## Environment Variables (Render)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_DATABASE_URL` | Yes* | Must start with `postgresql://` |
| `ADMIN_PASSWORD` | No | Default: hell52secret |
| `ADMIN_TOKEN` | No | Default: hell52-token-xK9mP2vQ |
| `GOD_MODE_KEY` | No | Default: HELL52-GOD-ULTRA-9999 |
| `GOD_BYPASS_TOKEN` | No | Default: GOD52-BYPASS-ALL-9999 |
| `DISCORD_WEBHOOK_URL` | No | Discord webhook for alerts |
| `RENDER_API_KEY` | No | For auto-deploy triggers |

*Server starts without DB but shows disconnected status

## Architecture decisions

- FastAPI for async support + auto-generated OpenAPI docs
- SQLAlchemy async engine with asyncpg driver
- Database connection is lazy — server starts even without correct URL
- CORS enabled for all origins (restrict in production if needed)
- All security state is in-memory (resets on restart) — Supabase persistence planned

## Gotchas

- `SUPABASE_DATABASE_URL` must start with `postgresql://` or `postgres://`
- GOD MODE state is in-memory — deactivates on server restart
- Run `pip install -r artifacts/api-server/requirements.txt` if packages are missing

## User preferences

- Python FastAPI preferred over Node.js/TypeScript
- Supabase for database (not Replit's built-in DB)
- GitHub access token and repo stored as secrets
- No Replit branding — "Made by HELL 52" throughout
