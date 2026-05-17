# API Server (FastAPI + Supabase)

A Python FastAPI backend connected to Supabase PostgreSQL.

## Run & Operate

- Server auto-starts via workflow on port 8080
- Dev command: `cd artifacts/api-server && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080`
- Health check: `curl http://localhost:80/api/healthz`
- API docs (auto-generated): `http://localhost:80/api/docs`
- Required env: `SUPABASE_DATABASE_URL` — Supabase PostgreSQL connection string

## Stack

- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy (async) + asyncpg
- Pydantic v2
- Supabase (PostgreSQL)

## Where things live

- `artifacts/api-server/main.py` — FastAPI app entry point
- `artifacts/api-server/database.py` — SQLAlchemy + Supabase connection
- `artifacts/api-server/schemas.py` — Pydantic request/response models
- `artifacts/api-server/routers/` — Route handlers
- `artifacts/api-server/requirements.txt` — Python dependencies
- `lib/api-spec/openapi.yaml` — OpenAPI spec (for reference)
- `lib/` — Legacy Node.js libs (unused, can be removed later)

## Architecture decisions

- FastAPI chosen for modern async support, auto-generated OpenAPI docs, and Pydantic v2 integration
- SQLAlchemy async engine with asyncpg driver for non-blocking DB access
- Database connection is lazy — server starts even without SUPABASE_DATABASE_URL
- CORS enabled for all origins (restrict in production as needed)

## Product

REST API server with health check endpoint. Ready to add GitHub integration routes and Supabase-backed data models.

## User preferences

- Python FastAPI preferred over Node.js/TypeScript
- Supabase for database (not Replit's built-in DB)
- GitHub access token and repo stored as secrets

## Gotchas

- `SUPABASE_DATABASE_URL` must start with `postgresql://` or `postgres://` — asyncpg driver is applied automatically
- Run `pip install -r artifacts/api-server/requirements.txt` if packages are missing

## Pointers

- FastAPI auto docs available at `/api/docs` and `/api/redoc`
- Add new routes in `artifacts/api-server/routers/` and register in `main.py`
