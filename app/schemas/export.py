from enum import Enum

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
	csv = "csv"
	xlsx = "xlsx"
	parquet = "parquet"


class ExportRequest(BaseModel):
	format: ExportFormat = ExportFormat.csv
	filters: dict = Field(default_factory=dict)


class ExportResponse(BaseModel):
	job_id: str
	status: str
