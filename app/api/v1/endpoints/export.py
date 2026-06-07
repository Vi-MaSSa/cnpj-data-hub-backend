from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.export import ExportRequest, ExportResponse
from app.services.export_service import create_export_job_request, get_export_job_status

router = APIRouter()


@router.post("/export", response_model=ExportResponse)
def create_export_endpoint(
	request: ExportRequest,
	db: Session = Depends(get_db),
) -> ExportResponse:
	return create_export_job_request(db, request=request)


@router.get("/export/{job_id}/download")
def download_export_file(job_id: str, db: Session = Depends(get_db)) -> FileResponse:
	job = get_export_job_status(db, job_id)
	if job is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

	if job.status != "ready":
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Export is not ready for download yet.",
		)

	if not job.file_path:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found")

	file_path = Path(job.file_path)
	if not file_path.exists():
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found")

	return FileResponse(
		path=file_path,
		media_type="text/csv",
		filename=f"{job_id}.csv",
	)
