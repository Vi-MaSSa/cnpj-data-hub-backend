import redis
from loguru import logger
from rq import Queue

from app.config import get_settings

settings = get_settings()

redis_connection = redis.Redis.from_url(settings.redis_url)
export_queue = Queue(settings.redis_queue_name, connection=redis_connection)


def enqueue_export_job(job_id: str) -> str:
	from app.workers.tasks.export_tasks import process_export_task

	job = export_queue.enqueue(process_export_task, job_id)
	logger.info("Export job enqueued: job_id={} rq_job_id={}", job_id, job.id)
	return job.id
