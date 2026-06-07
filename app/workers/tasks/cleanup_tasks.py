from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.database.postgres import SessionLocal
from app.database.repositories.job_repository import get_expired_ready_jobs, update_export_job_status


def cleanup_expired_exports() -> None:
	db = SessionLocal()
	try:
		expired_dir = Path("exports/expired")
		expired_dir.mkdir(parents=True, exist_ok=True)

		expired_jobs = get_expired_ready_jobs(db, datetime.now(timezone.utc))
		for job in expired_jobs:
			if job.file_path:
				source = Path(job.file_path)
				if source.exists():
					destination = expired_dir / source.name
					source.replace(destination)
					job.file_path = str(destination)

			update_export_job_status(db, job.id, "expired")
			logger.info("Expired export cleaned: job_id={}", job.id)
	except Exception:
		logger.exception("Cleanup expired exports failed")
	finally:
		db.close()
