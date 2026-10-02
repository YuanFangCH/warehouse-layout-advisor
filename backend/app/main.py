from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import conversations, decisions, evaluations, projects, scenarios
from .errors import register_exception_handlers
from .persistence.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="仓储布局决策参谋 API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(projects.router)
    app.include_router(scenarios.router)
    app.include_router(conversations.router)
    app.include_router(evaluations.router)
    app.include_router(decisions.router)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "service": "warehouse-decision-backend"}

    return app


app = create_app()
