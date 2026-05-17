import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse

from routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="HELL 52",
    version="1.0.0",
    description="**Made by HELL 52** — Powered by FastAPI + Supabase",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")


CUSTOM_CSS = """
<style>
  body { margin: 0; background: #0a0a0a; }
  .swagger-ui { font-family: 'Segoe UI', sans-serif; }
  .swagger-ui .topbar { background: #111 !important; padding: 10px 0; }
  .swagger-ui .topbar .download-url-wrapper { display: none; }
  .swagger-ui .topbar-wrapper img { display: none; }
  .swagger-ui .topbar-wrapper::before {
    content: "⚡ HELL 52 API";
    color: #ff3333;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 2px;
    padding-left: 20px;
  }
  .swagger-ui .info .title { color: #ff3333 !important; }
  .swagger-ui .info { background: #111; padding: 20px; border-radius: 8px; }
  .swagger-ui .scheme-container { background: #111 !important; }
  footer, .swagger-ui .footer { display: none !important; }
  #hell52-footer {
    text-align: center;
    padding: 20px;
    color: #ff3333;
    font-family: 'Segoe UI', sans-serif;
    font-weight: bold;
    font-size: 14px;
    letter-spacing: 1px;
    background: #0a0a0a;
  }
</style>
"""

CUSTOM_JS = """
<script>
  window.onload = function() {
    // Remove any injected badges
    setTimeout(() => {
      document.querySelectorAll('[class*="replit"], [id*="replit"], [src*="replit"]').forEach(el => el.remove());
      document.querySelectorAll('a[href*="replit"]').forEach(el => el.closest('div') && el.closest('div').remove());
    }, 1000);
    setTimeout(() => {
      const footer = document.createElement('div');
      footer.id = 'hell52-footer';
      footer.innerHTML = '⚡ Made by HELL 52 ⚡';
      document.body.appendChild(footer);
    }, 1500);
  }
</script>
"""


@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui() -> HTMLResponse:
    html = get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="HELL 52 — API Docs",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )
    body = html.body.decode("utf-8")
    body = body.replace("</head>", f"{CUSTOM_CSS}</head>")
    body = body.replace("</body>", f"{CUSTOM_JS}</body>")
    return HTMLResponse(content=body)


@app.get("/api/redoc", include_in_schema=False)
async def custom_redoc() -> HTMLResponse:
    html = get_redoc_html(
        openapi_url="/api/openapi.json",
        title="HELL 52 — ReDoc",
    )
    body = html.body.decode("utf-8")
    body = body.replace("</head>", f"{CUSTOM_CSS}</head>")
    body = body.replace("</body>", f"{CUSTOM_JS}</body>")
    return HTMLResponse(content=body)
