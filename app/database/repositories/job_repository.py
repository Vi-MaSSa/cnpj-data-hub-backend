from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy.orm import Session

from app.database.models import ExportJob


def create_export_job(
    db: Session,
    filters: dict,
    file_format: str = "csv",
    dataset_version_id: str | None = None,
    expires_hours: int = 24,
) -> ExportJob:
    job = ExportJob(
        dataset_version_id=dataset_version_id,
        status="queued",
        format=file_format,
        filters_json=filters,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info("Export job created: id={} status={}", job.id, job.status)
    return job


def get_export_job_by_id(db: Session, job_id: str) -> ExportJob | None:
    return db.query(ExportJob).filter(ExportJob.id == job_id).first()


def update_export_job_status(
    db: Session,
    job_id: str,
    status: str,
    error_message: str | None = None,
) -> ExportJob | None:
    job = get_export_job_by_id(db, job_id)
    if job is None:
        logger.warning("Export job not found for update: id={}", job_id)
        return None

    job.status = status
    job.error_message = error_message

    if status == "processing" and job.started_at is None:
        job.started_at = datetime.now(timezone.utc)
    if status in {"ready", "failed", "expired"}:
        job.finished_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)
    logger.info("Export job status updated: id={} status={}", job.id, job.status)
    return job


def mark_export_job_ready(
    db: Session,
    job_id: str,
    file_path: str,
    row_count: int | None = None,
) -> ExportJob | None:
    job = get_export_job_by_id(db, job_id)
    if job is None:
        logger.warning("Export job not found for ready state: id={}", job_id)
        return None

    job.status = "ready"
    job.file_path = file_path
    job.row_count = row_count
    job.finished_at = datetime.now(timezone.utc)
    job.error_message = None

    db.commit()
    db.refresh(job)
    logger.info("Export job marked ready: id={} file={}", job.id, file_path)
    return job


def mark_export_job_failed(db: Session, job_id: str, error_message: str) -> ExportJob | None:
    job = get_export_job_by_id(db, job_id)
    if job is None:
        logger.warning("Export job not found for failed state: id={}", job_id)
        return None

    job.status = "failed"
    job.error_message = error_message
    job.finished_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)
    logger.error("Export job marked failed: id={} error={}", job.id, error_message)
    return job


def get_expired_ready_jobs(db: Session, now: datetime) -> list[ExportJob]:
    return (
        db.query(ExportJob)
        .filter(ExportJob.status == "ready")
        .filter(ExportJob.expires_at.is_not(None))
        .filter(ExportJob.expires_at < now)
        .all()
    )