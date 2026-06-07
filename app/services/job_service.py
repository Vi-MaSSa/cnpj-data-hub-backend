from sqlalchemy.orm import Session

from app.database.repositories.job_repository import get_export_job_by_id


def get_job_by_id(db: Session, job_id: str):
	return get_export_job_by_id(db, job_id)
