from datetime import datetime, UTC

from loguru import logger
from sqlalchemy.orm import Session

from app.database.models import DatasetVersion


def create_dataset_version(
    db: Session,
    version: str,
    source: str = "receita_federal_cnpj",
) -> DatasetVersion:
    dataset = DatasetVersion(
        source=source,
        version=version,
        status="pending",
        is_active=False,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    logger.info("Dataset version created: id={} version={}", dataset.id, dataset.version)
    return dataset


def get_active_dataset_version(db: Session) -> DatasetVersion | None:
    return (
        db.query(DatasetVersion)
        .filter(DatasetVersion.is_active.is_(True))
        .order_by(DatasetVersion.published_at.desc().nullslast(), DatasetVersion.created_at.desc())
        .first()
    )


def get_dataset_version_by_id(db: Session, dataset_id: str) -> DatasetVersion | None:
    return db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()


def get_dataset_version_by_version(db: Session, version: str) -> DatasetVersion | None:
    return db.query(DatasetVersion).filter(DatasetVersion.version == version).first()


def update_dataset_status(
    db: Session,
    dataset_id: str,
    status: str,
    error_message: str | None = None,
    raw_path: str | None = None,
    bronze_path: str | None = None,
    silver_path: str | None = None,
    gold_path: str | None = None,
    row_count: int | None = None,
) -> DatasetVersion | None:
    dataset = get_dataset_version_by_id(db, dataset_id)
    if dataset is None:
        logger.warning("Dataset not found for status update: id={}", dataset_id)
        return None

    dataset.status = status
    dataset.error_message = error_message

    if raw_path is not None:
        dataset.raw_path = raw_path
    if bronze_path is not None:
        dataset.bronze_path = bronze_path
    if silver_path is not None:
        dataset.silver_path = silver_path
    if gold_path is not None:
        dataset.gold_path = gold_path
    if row_count is not None:
        dataset.row_count = row_count

    if status in {"downloading", "processing"} and dataset.started_at is None:
        dataset.started_at = datetime.now(UTC)
    if status in {"failed", "validated", "published", "archived", "downloaded"}:
        dataset.finished_at = datetime.now(UTC)

    db.commit()
    db.refresh(dataset)
    logger.info("Dataset status updated: id={} status={}", dataset.id, dataset.status)
    return dataset


def archive_active_dataset_versions(db: Session) -> int:
    active_datasets = db.query(DatasetVersion).filter(DatasetVersion.is_active.is_(True)).all()
    for dataset in active_datasets:
        dataset.is_active = False
        dataset.status = "archived"
        dataset.finished_at = datetime.now(UTC)
    db.commit()
    if active_datasets:
        logger.info("Archived active dataset versions: count={}", len(active_datasets))
    return len(active_datasets)


def publish_dataset_version(db: Session, dataset_id: str) -> DatasetVersion | None:
    dataset = get_dataset_version_by_id(db, dataset_id)
    if dataset is None:
        logger.warning("Dataset not found for publish: id={}", dataset_id)
        return None

    archive_active_dataset_versions(db)

    dataset.is_active = True
    dataset.status = "published"
    now = datetime.now(UTC)
    dataset.published_at = now
    dataset.finished_at = now

    db.commit()
    db.refresh(dataset)
    logger.info("Dataset version published: id={} version={}", dataset.id, dataset.version)
    return dataset
