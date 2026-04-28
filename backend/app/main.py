"""FastAPI entry point."""
from __future__ import annotations

from collections import defaultdict
from time import time as _now

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from .config import settings
from .routes import chat, manuals

app = FastAPI(
    title="Bike Troubleshooting Bot",
    description="Answers bike troubleshooting questions strictly from the uploaded manual.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Rate limiting — simple in-process sliding window per IP
# ---------------------------------------------------------------------------
_rate_windows: dict[str, list[float]] = defaultdict(list)


async def rate_limit(request: Request) -> None:
    if settings.rate_limit_per_minute <= 0:
        return
    ip = (request.client.host if request.client else None) or "unknown"
    now = _now()
    window = [t for t in _rate_windows[ip] if now - t < 60]
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Too many requests — please wait before trying again.")
    window.append(now)
    _rate_windows[ip] = window


# ---------------------------------------------------------------------------
# Optional API key auth — enabled when API_SECRET is set in .env
# ---------------------------------------------------------------------------
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_auth(api_key: str = Depends(_api_key_header)) -> None:
    if settings.api_secret and api_key != settings.api_secret:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


_shared_deps = [Depends(rate_limit), Depends(require_auth)]

app.include_router(manuals.router, dependencies=_shared_deps)
app.include_router(chat.router, dependencies=_shared_deps)


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "model": settings.anthropic_model,
        "anthropic_key_configured": bool(settings.anthropic_api_key),
        "auth_enabled": bool(settings.api_secret),
        "rate_limit_per_minute": settings.rate_limit_per_minute,
    }


@app.get("/")
async def root() -> dict:
    return {"service": "bike-troubleshooting-bot", "docs": "/docs", "health": "/api/health"}
