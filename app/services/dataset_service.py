from app.database.postgres import SessionLocal
from app.database.repositories.dataset_repository import (
	get_active_dataset_version,
	get_dataset_version_by_version,
	publish_dataset_version as publish_dataset_version_repo,
)


def get_current_dataset(db):
	return get_active_dataset_version(db)


def publish_dataset_version(version: str):
	db = SessionLocal()
	try:
		dataset = get_dataset_version_by_version(db, version)
		if dataset is None:
			return None
		return publish_dataset_version_repo(db, dataset.id)
	finally:
		db.close()


def get_active_dataset_path() -> str | None:
	db = SessionLocal()
	try:
		active_dataset = get_active_dataset_version(db)
		if active_dataset is None:
			return None
		return active_dataset.gold_path
	finally:
		db.close()
