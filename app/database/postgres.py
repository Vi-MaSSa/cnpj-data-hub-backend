from collections.abc import Generator

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.models import Base

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Fornece uma sessao SQLAlchemy por requisicao.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def check_postgres_connection() -> bool:
    """
    Verifica se a API consegue abrir conexao com o PostgreSQL.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.success("PostgreSQL connection successful")
        return True
    except Exception:
        logger.exception("PostgreSQL connection failed")
        return False


def create_database_tables() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/validated")