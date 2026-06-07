import sys
from pathlib import Path

from loguru import logger

from app.config import get_settings


_pipeline_sink_configured = False


def configure_logger() -> None:
    """
    Configura o Loguru para a aplicação.

    Saídas:
    - Console do Docker
    - Arquivo logs/api.log

    Em desenvolvimento, mostra mais detalhes.
    Em produção, evita expor informações sensíveis.
    """
    settings = get_settings()

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=settings.app_debug,
    )

    logger.add(
        "logs/api.log",
        level=settings.log_level,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=settings.app_debug,
    )


def get_logger():
    """
    Retorna a instância global do logger.

    Útil caso futuramente a gente queira trocar/adaptar
    a forma de obter o logger.
    """
    return logger


def configure_pipeline_logger() -> None:
    """
    Garante que o pipeline tenha um arquivo de log dedicado.

    A função adiciona o sink de arquivo somente uma vez para evitar
    duplicidade de logs em execucoes repetidas no mesmo processo.
    """
    global _pipeline_sink_configured
    if _pipeline_sink_configured:
        return

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        "logs/pipeline.log",
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
    _pipeline_sink_configured = True