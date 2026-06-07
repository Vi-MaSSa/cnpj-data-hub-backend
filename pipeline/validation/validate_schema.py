from pathlib import Path

import polars as pl


def validate_parquet_exists(path: str | Path) -> bool:
	parquet_path = Path(path)
	return parquet_path.exists() and parquet_path.suffix.lower() == ".parquet"


def validate_required_columns(path: str | Path, required_columns: list[str]) -> dict:
	errors: list[str] = []
	parquet_path = Path(path)

	if not validate_parquet_exists(parquet_path):
		errors.append(f"Parquet not found: {parquet_path}")
		return {"valid": False, "errors": errors}

	schema_columns = pl.scan_parquet(parquet_path).collect_schema().names()
	missing_columns = [column for column in required_columns if column not in schema_columns]
	if missing_columns:
		errors.append(f"Missing columns: {missing_columns}")

	return {"valid": len(errors) == 0, "errors": errors}


def validate_min_rows(path: str | Path, min_rows: int = 1) -> dict:
	errors: list[str] = []
	parquet_path = Path(path)

	if not validate_parquet_exists(parquet_path):
		errors.append(f"Parquet not found: {parquet_path}")
		return {"valid": False, "errors": errors}

	row_count = pl.scan_parquet(parquet_path).select(pl.len().alias("rows")).collect().item(0, 0)
	if row_count < min_rows:
		errors.append(f"Row count below minimum ({row_count} < {min_rows})")

	return {"valid": len(errors) == 0, "errors": errors}
