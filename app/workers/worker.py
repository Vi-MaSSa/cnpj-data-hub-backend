from loguru import logger
from rq import Worker

from app.config import get_settings
from app.utils.logger import configure_logger
from app.workers.queues import export_queue, redis_connection


def main() -> None:
	settings = get_settings()
	configure_logger()
	logger.info("Starting worker for queue: {}", settings.redis_queue_name)
	worker = Worker([export_queue], connection=redis_connection)
	worker.work()


if __name__ == "__main__":
	main()
