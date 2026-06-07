from datetime import datetime

from pydantic import BaseModel


class CurrentDatasetResponse(BaseModel):
	active: bool
	message: str | None = None
	id: str | None = None
	version: str | None = None
	status: str | None = None
	gold_path: str | None = None
	row_count: int | None = None
	published_at: datetime | None = None
