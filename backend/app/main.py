"""FastAPI entry point: creates the app, wires CORS, error handlers, and routers."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.db.session import engine
from app.routers import summary, tickets

settings = get_settings()
setup_logging(settings.log_level)
logger = get_logger("main")


def _database_is_up() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    if _database_is_up():
        logger.info("Startup: database connection OK")
    else:
        logger.error("Startup: database unreachable - check DATABASE_URL and that PostgreSQL is running")
    logger.info("Startup: AI model configured = %s", settings.ollama_model)
    yield
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="REST API for the AI-Powered Employee Helpdesk. AI suggestions are advisory only.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "database": "up" if _database_is_up() else "down"}


# Routers are added in later steps:
# from app.routers import tickets, summary, ai
app.include_router(tickets.router)
app.include_router(summary.router)
# app.include_router(ai.router)