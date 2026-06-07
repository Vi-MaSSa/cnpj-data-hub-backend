from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
	return datetime.now(timezone.utc)


class Base(DeclarativeBase):
	pass


DATASET_STATUS_VALUES = [
	"pending",
	"downloading",
	"downloaded",
	"processing",
	"validated",
	"published",
	"failed",
	"archived",
]

EXPORT_JOB_STATUS_VALUES = [
	"queued",
	"processing",
	"ready",
	"failed",
	"expired",
]


class DatasetVersion(Base):
	__tablename__ = "dataset_versions"

	id: Mapped[str] = mapped_column(
		String(36),
		primary_key=True,
		default=lambda: str(uuid.uuid4()),
	)
	source: Mapped[str] = mapped_column(String(100), default="receita_federal_cnpj")
	version: Mapped[str] = mapped_column(String(100), index=True)
	status: Mapped[str] = mapped_column(String(30), index=True, default="pending")

	raw_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
	bronze_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
	silver_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
	gold_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

	row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
	checksum: Mapped[str | None] = mapped_column(String(255), nullable=True)
	is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

	started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		default=utc_now,
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		default=utc_now,
		onupdate=utc_now,
	)


class ExportJob(Base):
	__tablename__ = "export_jobs"

	id: Mapped[str] = mapped_column(
		String(36),
		primary_key=True,
		default=lambda: str(uuid.uuid4()),
	)
	dataset_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
	status: Mapped[str] = mapped_column(String(30), index=True, default="queued")
	format: Mapped[str] = mapped_column(String(20), default="csv")
	filters_json: Mapped[dict] = mapped_column(JSONB, default=dict)

	file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
	row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
	error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
	started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# TODO: Add User and UsageLog models in future phases.
