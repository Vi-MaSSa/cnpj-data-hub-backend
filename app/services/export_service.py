from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.repositories.dataset_repository import get_active_dataset_version
from app.database.repositories.job_repository import create_export_job, get_export_job_by_id
from app.schemas.export import ExportRequest, ExportResponse
from app.schemas.search import SearchRequest
from app.services.search_service import count_search_results
from app.workers.queues import enqueue_export_job


SUPPORTED_MVP_FORMAT = "csv"
settings = get_settings()


def create_export_job_request(db: Session, request: ExportRequest) -> ExportResponse:
	if request.format.value != SUPPORTED_MVP_FORMAT:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Only CSV export is supported in this MVP.",
		)

	search_request = SearchRequest(**request.filters)
	total_rows = count_search_results(search_request)
	if total_rows > settings.export_max_rows:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=(
				f"Export exceeded max rows ({settings.export_max_rows}). "
				f"Estimated rows: {total_rows}."
			),
		)

	active_dataset = get_active_dataset_version(db)
	dataset_id = active_dataset.id if active_dataset else None
	job = create_export_job(
		db=db,
		filters=request.filters,
		file_format=request.format.value,
		dataset_version_id=dataset_id,
		expires_hours=settings.export_expires_hours,
	)
	job.expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.export_expires_hours)
	db.commit()
	db.refresh(job)
	enqueue_export_job(job.id)
	return ExportResponse(job_id=job.id, status="queued")


def get_export_job_status(db: Session, job_id: str):
	return get_export_job_by_id(db, job_id)
