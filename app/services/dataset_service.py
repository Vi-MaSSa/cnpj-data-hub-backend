from sqlalchemy.orm import Session

from app.database.repositories.dataset_repository import get_active_dataset_version


def get_current_dataset(db: Session):
	return get_active_dataset_version(db)
