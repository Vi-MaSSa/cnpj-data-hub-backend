from datetime import datetime

from pydantic import BaseModel


class JobResponse(BaseModel):
	job_id: str
	status: str
	format: str
	filters: dict
	file_path: str | None
	row_count: int | None
	error_message: str | None
	created_at: datetime | None
	started_at: datetime | None
	finished_at: datetime | None
	expires_at: datetime | None
