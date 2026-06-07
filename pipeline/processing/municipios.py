from io import BytesIO
from pathlib import Path
import zipfile

from loguru import logger
import polars as pl

from pipeline.schemas.receita_columns import CSV_ENCODING, CSV_HAS_HEADER, CSV_SEPARATOR


MUNICIPIOS_COLUMNS = [
	"codigo_municipio",
	"municipio",
]


def process_municipios_silver(version: str) -> Path:
	raw_dir = Path("data") / "raw" / version
	silver_dir = Path("data") / "silver" / version
	silver_dir.mkdir(parents=True, exist_ok=True)
	output_path = silver_dir / "municipios_clean.parquet"

	zip_files = sorted(raw_dir.glob("Municipios*.zip"))
	if not zip_files:
		logger.warning("Municipios ZIP files not found for version={}; writing empty Silver", version)
		pl.DataFrame(schema={"codigo_municipio": pl.Utf8, "municipio": pl.Utf8, "codigo_ibge": pl.Utf8}).write_parquet(
			output_path
		)
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
				if frame.width < len(MUNICIPIOS_COLUMNS):
					for index in range(frame.width, len(MUNICIPIOS_COLUMNS)):
						frame = frame.with_columns(pl.lit(None).alias(f"extra_{index}"))
				rename_map = {
					column: (MUNICIPIOS_COLUMNS[index] if index < len(MUNICIPIOS_COLUMNS) else f"extra_{index}")
					for index, column in enumerate(frame.columns)
				}
				frames.append(frame.rename(rename_map).select(MUNICIPIOS_COLUMNS))

	merged = pl.concat(frames, how="vertical_relaxed") if frames else pl.DataFrame(schema={"codigo_municipio": pl.Utf8, "municipio": pl.Utf8})
	silver = (
		merged.with_columns(
			[
				pl.col("codigo_municipio").cast(pl.Utf8, strict=False).str.strip_chars(),
				pl.col("municipio").cast(pl.Utf8, strict=False).str.strip_chars().str.to_uppercase(),
				pl.lit(None).cast(pl.Utf8).alias("codigo_ibge"),
			]
		)
		.unique(subset=["codigo_municipio"])
		.sort("codigo_municipio")
	)
	silver.write_parquet(output_path)
	logger.warning("codigo_ibge currently unavailable for raw Municipios source; field kept as null")
	logger.info("Municipios Silver processed: version={} rows={} path={}", version, silver.height, output_path)
	return output_path
