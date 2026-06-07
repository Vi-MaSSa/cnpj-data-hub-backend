from io import BytesIO
from pathlib import Path
import zipfile

from loguru import logger
import polars as pl

from pipeline.schemas.receita_columns import CSV_ENCODING, CSV_HAS_HEADER, CSV_SEPARATOR


SOCIOS_COLUMNS = [
	"cnpj_basico",
	"identificador_socio",
	"nome_socio",
	"cnpj_cpf_socio",
	"qualificacao_socio",
	"data_entrada_sociedade",
	"pais",
	"representante_legal",
	"nome_representante",
	"qualificacao_representante_legal",
	"faixa_etaria",
]


def _empty_socios_frame() -> pl.DataFrame:
	return pl.DataFrame(schema={column: pl.Utf8 for column in SOCIOS_COLUMNS})


def process_socios_bronze(version: str) -> Path:
	raw_dir = Path("data") / "raw" / version
	bronze_dir = Path("data") / "bronze" / version
	bronze_dir.mkdir(parents=True, exist_ok=True)
	output_path = bronze_dir / "socios.parquet"

	zip_files = sorted(raw_dir.glob("Socios*.zip"))
	if not zip_files:
		logger.warning("Socios ZIP files not found for version={}; writing empty Bronze", version)
		_empty_socios_frame().write_parquet(output_path)
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
				if frame.width < len(SOCIOS_COLUMNS):
					for index in range(frame.width, len(SOCIOS_COLUMNS)):
						frame = frame.with_columns(pl.lit(None).alias(f"extra_{index}"))
				rename_map = {
					column: (SOCIOS_COLUMNS[index] if index < len(SOCIOS_COLUMNS) else f"extra_{index}")
					for index, column in enumerate(frame.columns)
				}
				frames.append(frame.rename(rename_map).select(SOCIOS_COLUMNS))

	result = pl.concat(frames, how="vertical_relaxed") if frames else _empty_socios_frame()
	result.write_parquet(output_path)
	logger.info("Socios Bronze processed: version={} rows={} path={}", version, result.height, output_path)
	return output_path


def process_socios_silver(version: str) -> Path:
	bronze_path = Path("data") / "bronze" / version / "socios.parquet"
	silver_dir = Path("data") / "silver" / version
	silver_dir.mkdir(parents=True, exist_ok=True)
	output_path = silver_dir / "socios_clean.parquet"

	if not bronze_path.exists():
		logger.warning("Socios Bronze not found for version={}; writing empty Silver", version)
		_empty_socios_frame().write_parquet(output_path)
		return output_path

	frame = pl.read_parquet(bronze_path)
	silver = frame.with_columns(
		[
			pl.col("cnpj_basico").cast(pl.Utf8, strict=False).str.zfill(8).alias("cnpj_basico"),
			pl.col("nome_socio").cast(pl.Utf8, strict=False).str.strip_chars().str.to_uppercase(),
		]
	)
	silver.write_parquet(output_path)
	logger.info("Socios Silver processed: version={} rows={} path={}", version, silver.height, output_path)
	return output_path
