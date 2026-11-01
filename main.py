from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.logging import setup_logging
from .db import Base, SessionLocal, engine
from .routers import ALL

settings = get_settings()
log = setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    if settings.seed_demo_data:
        from .seed import seed
        with SessionLocal() as db:
            seed(db)
    log.info("Tawazun API started env=%s config=%s llm=%s", settings.app_env, settings.config_path.name, settings.get("llm.provider"))
    yield


app = FastAPI(
    title=settings.get("app.name", "Tawazun Clinic"),
    version=settings.get("app.version", "0.1.0"),
    lifespan=lifespan,
    docs_url=None if settings.is_prod else "/docs",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get("server.cors_origins", []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"  # medical data must not be cached
    return response


prefix = settings.get("app.api_prefix", "/api")
for module in ALL:
    app.include_router(module.router, prefix=prefix)


@app.get(f"{prefix}/health")
def health():
    return {"status": "ok", "env": settings.app_env, "version": settings.get("app.version")}
