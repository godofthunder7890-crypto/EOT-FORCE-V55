import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from routers import health
from routers import admin
from routers import threats


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(threats.auto_update_loop())
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
app.include_router(admin.router, prefix="/api/admin")
app.include_router(threats.router, prefix="/api")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/api/static", StaticFiles(directory=STATIC_DIR), name="static")


BADGE_CSS = """
<style>
  iframe[src*="replit"],[class*="replit-badge"],[id*="replit-badge"],
  [class*="replitBadge"],[id*="replitBadge"],a[href*="replit.com/@"],
  div[style*="z-index: 9999"] iframe,div[style*="z-index:9999"] iframe{
    display:none!important;visibility:hidden!important;opacity:0!important;
    pointer-events:none!important;width:0!important;height:0!important;}
</style>"""

BADGE_JS = """
<script>
  function rmReplit(){
    ['iframe[src*="replit"]','[class*="replit-badge"]','[id*="replit-badge"]',
     '[class*="replitBadge"]','[id*="replitBadge"]','a[href*="replit.com/@"]'
    ].forEach(s=>document.querySelectorAll(s).forEach(e=>e.remove()));
    document.querySelectorAll('iframe').forEach(e=>{if(e.src&&e.src.includes('replit'))e.remove();});
    document.querySelectorAll('a[href*="replit"]').forEach(e=>{
      const p=e.closest('div[style]')||e.parentElement;
      if(p&&p!==document.body)p.remove();
    });
  }
  rmReplit();
  window.addEventListener('load',rmReplit);
  new MutationObserver(rmReplit).observe(document.documentElement,{childList:true,subtree:true});
  let c=0;const iv=setInterval(()=>{rmReplit();if(++c>20)clearInterval(iv);},500);
  window.addEventListener('load',()=>{setTimeout(()=>{
    if(!document.getElementById('h52f')){
      const f=document.createElement('div');
      f.id='h52f';f.style='text-align:center;padding:20px;color:#ff3333;font-weight:bold;font-size:14px;letter-spacing:1px;background:#0a0a0a;';
      f.innerHTML='⚡ Made by HELL 52 ⚡';document.body.appendChild(f);}
  },1000);});
</script>"""

DOCS_CSS = """
<style>
  body{margin:0;background:#0a0a0a;}
  .swagger-ui .topbar{background:#111!important;padding:10px 0;}
  .swagger-ui .topbar .download-url-wrapper{display:none;}
  .swagger-ui .topbar-wrapper img{display:none;}
  .swagger-ui .topbar-wrapper::before{content:"⚡ HELL 52 API";color:#ff3333;font-size:22px;font-weight:900;letter-spacing:2px;padding-left:20px;}
  .swagger-ui .info .title{color:#ff3333!important;}
  .swagger-ui .info{background:#111;padding:20px;border-radius:8px;}
  .swagger-ui .scheme-container{background:#111!important;}
  footer,.swagger-ui .footer{display:none!important;}
</style>"""


@app.get("/api/admin/panel", include_in_schema=False)
async def admin_panel() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))


@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui() -> HTMLResponse:
    html = get_swagger_ui_html(openapi_url="/api/openapi.json", title="HELL 52 — API Docs")
    body = html.body.decode("utf-8")
    body = body.replace("</head>", f"{DOCS_CSS}{BADGE_CSS}</head>")
    body = body.replace("</body>", f"{BADGE_JS}</body>")
    return HTMLResponse(content=body)


@app.get("/api/redoc", include_in_schema=False)
async def custom_redoc() -> HTMLResponse:
    html = get_redoc_html(openapi_url="/api/openapi.json", title="HELL 52 — ReDoc")
    body = html.body.decode("utf-8")
    body = body.replace("</head>", f"{DOCS_CSS}{BADGE_CSS}</head>")
    body = body.replace("</body>", f"{BADGE_JS}</body>")
    return HTMLResponse(content=body)


@app.get("/api", include_in_schema=False)
async def api_root():
    return RedirectResponse(url="/api/admin/panel")
