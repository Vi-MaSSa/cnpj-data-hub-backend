from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1.router import api_router
from app.config import get_settings
from app.database.postgres import create_database_tables
from app.utils.logger import configure_logger

settings = get_settings()

configure_logger()

logger.info("Starting CNPJ Data Hub API")
logger.info("Environment: {}", settings.app_env)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API para consulta, filtragem e exportacao de dados publicos de CNPJ.",
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup() -> None:
    create_database_tables()
    logger.info("Application startup checks completed")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "CNPJ Data Hub API is running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }