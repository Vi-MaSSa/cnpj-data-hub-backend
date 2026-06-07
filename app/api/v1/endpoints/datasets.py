from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.dataset import CurrentDatasetResponse
from app.services.dataset_service import get_current_dataset

router = APIRouter()


@router.get("/datasets/current", response_model=CurrentDatasetResponse)
def get_current_dataset_endpoint(db: Session = Depends(get_db)) -> CurrentDatasetResponse:
	dataset = get_current_dataset(db)

	if dataset is None:
		return CurrentDatasetResponse(
			active=False,
			message="No active dataset version found",
		)

	return CurrentDatasetResponse(
		active=True,
		id=dataset.id,
		version=dataset.version,
		status=dataset.status,
		gold_path=dataset.gold_path,
		row_count=dataset.row_count,
		published_at=dataset.published_at,
	)
