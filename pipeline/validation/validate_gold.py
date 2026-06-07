from pathlib import Path

import duckdb
import polars as pl

from pipeline.schemas.gold_schema import GOLD_COLUMNS


def validate_gold_layer(path: str | Path, min_rows: int = 1) -> dict:
	errors: list[str] = []
	gold_path = Path(path)

	if not gold_path.exists():
		errors.append(f"Gold parquet not found: {gold_path}")
		return {"valid": False, "row_count": 0, "errors": errors}

	frame = pl.read_parquet(gold_path)
	row_count = frame.height

	missing_columns = [column for column in GOLD_COLUMNS if column not in frame.columns]
	if missing_columns:
		errors.append(f"Missing Gold columns: {missing_columns}")

	if row_count < min_rows:
		errors.append(f"Gold row count below minimum ({row_count} < {min_rows})")

	required_fields = ["cnpj_completo", "razao_social", "uf", "municipio", "cnae_principal"]
	for field in required_fields:
		if field not in frame.columns:
			continue
		null_count = int(frame.select(pl.col(field).is_null().sum()).item(0, 0))
		if null_count > 0:
			errors.append(f"Field {field} has {null_count} null values")

	try:
		with duckdb.connect(database=":memory:") as connection:
			count_result = connection.execute(
				"SELECT COUNT(*) AS total FROM read_parquet(?)",
				[str(gold_path)],
			).fetchone()
			if count_result is None:
				errors.append("DuckDB count query returned no result")
	except Exception as exc:
		errors.append(f"DuckDB validation query failed: {exc}")

	return {"valid": len(errors) == 0, "row_count": row_count, "errors": errors}
