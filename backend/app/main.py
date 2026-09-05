from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config, db
from .llm import probe_provider
from .routers import analytics, auth, billing, competitors, connections, content, products, settings, social_hub, strategy


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    await probe_provider()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Optinum AI", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")
    for module in (auth, products, connections, strategy, analytics, competitors, billing, settings, content, social_hub):
        app.include_router(module.router, prefix="/api")

    @app.get("/api/health")
    def health():
        return {"ok": True}

    return app


app = create_app()
