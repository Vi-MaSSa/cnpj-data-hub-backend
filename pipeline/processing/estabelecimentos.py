from io import BytesIO
from pathlib import Path
import zipfile

from loguru import logger
import polars as pl

from pipeline.schemas.estabelecimentos_schema import (
	ESTABELECIMENTOS_COLUMNS,
	ESTABELECIMENTOS_SILVER_COLUMNS,
)
from pipeline.schemas.receita_columns import CSV_ENCODING, CSV_HAS_HEADER, CSV_SEPARATOR


def _read_estabelecimentos_raw_frames(version: str) -> list[pl.DataFrame]:
	raw_dir = Path("data") / "raw" / version
	zip_files = sorted(raw_dir.glob("Estabelecimentos*.zip"))
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
				frames.append(frame)

	return frames


def _normalize_columns(frame: pl.DataFrame, expected_columns: list[str]) -> pl.DataFrame:
	current = list(frame.columns)
	if len(current) < len(expected_columns):
		for index in range(len(current), len(expected_columns)):
			frame = frame.with_columns(pl.lit(None).alias(f"extra_{index}"))
		current = list(frame.columns)

	rename_map = {}
	for index, column in enumerate(current):
		if index < len(expected_columns):
			rename_map[column] = expected_columns[index]
		else:
			rename_map[column] = f"extra_{index}"
	return frame.rename(rename_map)


def process_estabelecimentos_bronze(version: str) -> Path:
	bronze_dir = Path("data") / "bronze" / version
	bronze_dir.mkdir(parents=True, exist_ok=True)
	output_path = bronze_dir / "estabelecimentos.parquet"

	frames = _read_estabelecimentos_raw_frames(version)
	if not frames:
		logger.warning("No Estabelecimentos ZIP files found for version={}", version)
		empty = pl.DataFrame(schema={column: pl.Utf8 for column in ESTABELECIMENTOS_COLUMNS})
		empty.write_parquet(output_path)
		return output_path

	normalized = [
		_normalize_columns(frame, ESTABELECIMENTOS_COLUMNS).select(ESTABELECIMENTOS_COLUMNS)
		for frame in frames
	]
	bronze = pl.concat(normalized, how="vertical_relaxed")
	bronze.write_parquet(output_path)
	logger.info(
		"Estabelecimentos Bronze processed: version={} files={} rows={} path={}",
		version,
		len(frames),
		bronze.height,
		output_path,
	)
	return output_path


def process_estabelecimentos_silver(version: str) -> Path:
	bronze_path = Path("data") / "bronze" / version / "estabelecimentos.parquet"
	silver_dir = Path("data") / "silver" / version
	silver_dir.mkdir(parents=True, exist_ok=True)
	output_path = silver_dir / "estabelecimentos_clean.parquet"

	if not bronze_path.exists():
		logger.exception("Estabelecimentos Bronze file not found: {}", bronze_path)
		raise FileNotFoundError(bronze_path)

	frame = pl.read_parquet(bronze_path)

	silver = (
		frame.with_columns(
			[
				pl.col("cnpj_basico").cast(pl.Utf8, strict=False).str.zfill(8).alias("cnpj_basico"),
				pl.col("cnpj_ordem").cast(pl.Utf8, strict=False).str.zfill(4).alias("cnpj_ordem"),
				pl.col("cnpj_dv").cast(pl.Utf8, strict=False).str.zfill(2).alias("cnpj_dv"),
				pl.col("nome_fantasia").cast(pl.Utf8, strict=False).str.strip_chars().str.to_uppercase(),
				pl.col("uf").cast(pl.Utf8, strict=False).str.strip_chars().str.to_uppercase(),
				pl.col("codigo_municipio").cast(pl.Utf8, strict=False).str.strip_chars(),
				pl.col("cnae_principal").cast(pl.Utf8, strict=False).str.strip_chars(),
				pl.col("cnae_secundario").cast(pl.Utf8, strict=False).str.strip_chars(),
				pl.col("situacao_cadastral").cast(pl.Utf8, strict=False).str.strip_chars(),
				pl.col("cep").cast(pl.Utf8, strict=False).str.replace_all(r"\D", "").str.zfill(8),
				pl.col("ddd_1").cast(pl.Utf8, strict=False).str.replace_all(r"\D", ""),
				pl.col("telefone_1").cast(pl.Utf8, strict=False).str.replace_all(r"\D", ""),
				pl.col("bairro").cast(pl.Utf8, strict=False).str.strip_chars().str.to_uppercase(),
				pl.concat_str([pl.col("cnpj_basico"), pl.col("cnpj_ordem"), pl.col("cnpj_dv")]).alias(
					"cnpj_completo"
				),
			]
		)
		.select(ESTABELECIMENTOS_SILVER_COLUMNS)
	)

	silver.write_parquet(output_path)
	logger.info("Estabelecimentos Silver processed: version={} rows={} path={}", version, silver.height, output_path)
	return output_path
