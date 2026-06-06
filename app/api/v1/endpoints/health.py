from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import get_settings
from app.database.postgres import check_postgres_connection
from app.services.cache_service import check_redis_connection

router = APIRouter()


@router.get("/health")
def health_check():
    settings = get_settings()
    logger.info("Health check requested")

    postgres_ok = check_postgres_connection()
    redis_ok = check_redis_connection()

    dependencies = {
        "postgres": "ok" if postgres_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }

    app_is_healthy = postgres_ok and redis_ok

    response = {
        "status": "ok" if app_is_healthy else "partial",
        "service": settings.app_name,
        "environment": settings.app_env,
        "version": "0.1.0",
        "dependencies": dependencies,
    }

    if app_is_healthy:
        return response

    logger.warning("Health check returned partial status: {}", response)

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=response,
    )