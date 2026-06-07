from io import BytesIO
from pathlib import Path
import zipfile

from loguru import logger
import polars as pl

from pipeline.schemas.receita_columns import CSV_ENCODING, CSV_HAS_HEADER, CSV_SEPARATOR


SIMPLES_COLUMNS = [
	"cnpj_basico",
	"opcao_simples",
	"data_opcao_simples",
	"data_exclusao_simples",
	"opcao_mei",
	"data_opcao_mei",
	"data_exclusao_mei",
]


def _empty_simples_frame() -> pl.DataFrame:
	return pl.DataFrame(
		schema={
			"cnpj_basico": pl.Utf8,
			"opcao_simples": pl.Boolean,
			"opcao_mei": pl.Boolean,
		}
	)


def process_simples_bronze(version: str) -> Path:
	raw_dir = Path("data") / "raw" / version
	bronze_dir = Path("data") / "bronze" / version
	bronze_dir.mkdir(parents=True, exist_ok=True)
	output_path = bronze_dir / "simples.parquet"

	zip_files = sorted(raw_dir.glob("Simples*.zip"))
	if not zip_files:
		logger.warning("Simples ZIP files not found for version={}; writing empty Bronze", version)
		pl.DataFrame(schema={column: pl.Utf8 for column in SIMPLES_COLUMNS}).write_parquet(output_path)
		return output_path

	frames: list[pl.DataFrame] = []
	for zip_path in zip_files:
		with zipfile.ZipFile(zip_path, "r") as archive:
			for member in archive.namelist():
				if not member.lower().endswith((".csv", ".txt")):
					continue
				with archive.open(member) as member_file:
					data = member_file.read()
				frame = pl.read_csv(
					BytesIO(data),
					has_header=CSV_HAS_HEADER,
					separator=CSV_SEPARATOR,
					encoding=CSV_ENCODING,
					infer_schema_length=0,
					ignore_errors=True,
				)
				if frame.width < len(SIMPLES_COLUMNS):
					for index in range(frame.width, len(SIMPLES_COLUMNS)):
						frame = frame.with_columns(pl.lit(None).alias(f"extra_{index}"))
				rename_map = {
					column: (SIMPLES_COLUMNS[index] if index < len(SIMPLES_COLUMNS) else f"extra_{index}")
					for index, column in enumerate(frame.columns)
				}
				frames.append(frame.rename(rename_map).select(SIMPLES_COLUMNS))

	result = pl.concat(frames, how="vertical_relaxed") if frames else pl.DataFrame(schema={column: pl.Utf8 for column in SIMPLES_COLUMNS})
	result.write_parquet(output_path)
	logger.info("Simples Bronze processed: version={} rows={} path={}", version, result.height, output_path)
	return output_path


def process_simples_silver(version: str) -> Path:
	bronze_path = Path("data") / "bronze" / version / "simples.parquet"
	silver_dir = Path("data") / "silver" / version
	silver_dir.mkdir(parents=True, exist_ok=True)
	output_path = silver_dir / "simples_clean.parquet"

	if not bronze_path.exists():
		logger.warning("Simples Bronze file missing for version={}; writing empty Silver", version)
		_empty_simples_frame().write_parquet(output_path)
		return output_path

	frame = pl.read_parquet(bronze_path)
	if frame.is_empty():
		_empty_simples_frame().write_parquet(output_path)
		return output_path

	true_values = ["S", "1", "SIM", "TRUE", "T"]
	silver = frame.with_columns(
		[
			pl.col("cnpj_basico").cast(pl.Utf8, strict=False).str.zfill(8).alias("cnpj_basico"),
			pl.col("opcao_simples")
			.cast(pl.Utf8, strict=False)
			.str.to_uppercase()
			.is_in(true_values)
			.alias("opcao_simples"),
			pl.col("opcao_mei").cast(pl.Utf8, strict=False).str.to_uppercase().is_in(true_values).alias("opcao_mei"),
		]
	).select(["cnpj_basico", "opcao_simples", "opcao_mei"])

	silver.write_parquet(output_path)
	logger.info("Simples Silver processed: version={} rows={} path={}", version, silver.height, output_path)
	return output_path
