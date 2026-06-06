from collections.abc import Generator
from typing import Any

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.postgres import get_db as postgres_get_db
from app.services.cache_service import redis_client


def get_app_settings() -> Settings:
    """
    Retorna as configuracoes globais da aplicacao.
    """
    return get_settings()


def get_db() -> Generator[Session, None, None]:
    """
    Fornece uma sessao do PostgreSQL para endpoints/services.
    """
    yield from postgres_get_db()


def get_cache() -> Any:
    """
    Retorna o cliente Redis compartilhado da aplicacao.
    """
    return redis_client


def get_current_user() -> None:
    """
    Placeholder para autenticacao futura.
    """
    raise NotImplementedError("Authentication is not implemented yet.")
