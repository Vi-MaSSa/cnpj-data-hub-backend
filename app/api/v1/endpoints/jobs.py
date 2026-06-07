from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.job import JobResponse
from app.services.job_service import get_job_by_id

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_endpoint(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
	job = get_job_by_id(db, job_id)
	if job is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

	return JobResponse(
		job_id=job.id,
		status=job.status,
		format=job.format,
		filters=job.filters_json,
		file_path=job.file_path,
		row_count=job.row_count,
		error_message=job.error_message,
		created_at=job.created_at,
		started_at=job.started_at,
		finished_at=job.finished_at,
		expires_at=job.expires_at,
	)
