import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config.settings import settings
from api.logger import logger, log_request
from api.routes import health, auth, assets, risk, portfolio, market, export

# ── Rate Limiter ───────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production-grade Indian equity market risk analytics platform. "
        "Covers Nifty 50, sectoral indices and F&O stocks with "
        "VaR, CVaR, stress testing and India-specific risk signals."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate Limiting Middleware ───────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS Middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request Logging Middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    log_request(
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    return response

# ── Startup Event ──────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    logger.info("Starting up", extra={
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env
    })

# ── Register All Routers ───────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(risk.router)
app.include_router(portfolio.router)
app.include_router(market.router)
app.include_router(export.router)

# ── Serve React Frontend ───────────────────────────────────────────────────────
FRONTEND_DIST = Path(__file__).parent.parent / "dashboard" / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    def serve_root():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health"
        }