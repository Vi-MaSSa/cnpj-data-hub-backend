import argparse
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from app.database.postgres import SessionLocal, create_database_tables
from app.database.repositories.dataset_repository import (
	create_dataset_version,
	get_dataset_version_by_version,
	publish_dataset_version,
	update_dataset_status,
)
from app.utils.logger import configure_logger, configure_pipeline_logger
from pipeline.ingestion.discover_files import discover_receita_files
from pipeline.ingestion.downloader import download_files
from pipeline.ingestion.manifest import (
	create_manifest,
	get_manifest_path,
	load_manifest,
	save_manifest,
	update_manifest_status,
)
from pipeline.ingestion.validators import validate_raw_downloads
from pipeline.processing.build_gold import build_gold_layer
from pipeline.processing.empresas import process_empresas_bronze, process_empresas_silver
from pipeline.processing.estabelecimentos import process_estabelecimentos_bronze, process_estabelecimentos_silver
from pipeline.processing.municipios import process_municipios_silver
from pipeline.processing.simples import process_simples_bronze, process_simples_silver
from pipeline.processing.socios import process_socios_bronze, process_socios_silver
from pipeline.schemas.empresas_schema import EMPRESAS_SILVER_COLUMNS
from pipeline.schemas.estabelecimentos_schema import ESTABELECIMENTOS_SILVER_COLUMNS
from pipeline.validation.validate_gold import validate_gold_layer
from pipeline.validation.validate_schema import (
	validate_min_rows,
	validate_parquet_exists,
	validate_required_columns,
)


def _default_version() -> str:
	return datetime.now(UTC).strftime("%Y-%m")


def _prepare_manifest(version: str, include_large_files: bool) -> tuple[dict, list[dict]]:
	manifest_path = get_manifest_path(version)
	files = discover_receita_files(version=version, include_large_files=include_large_files)

	if manifest_path.exists():
		manifest = load_manifest(manifest_path)
		existing_names = {file_info["name"] for file_info in manifest.get("files", [])}
		for file_info in files:
			if file_info["name"] in existing_names:
				continue
			manifest["files"].append(
				{
					"name": file_info["name"],
					"url": file_info["url"],
					"path": file_info["path"],
					"size_bytes": None,
					"status": "pending",
					"checksum": None,
					"error_message": None,
					"downloaded_at": None,
				}
			)
	else:
		manifest = create_manifest(source="receita_federal_cnpj", version=version, files=files)

	save_manifest(manifest, manifest_path)
	return manifest, files


def _validate_bronze_outputs(version: str) -> list[str]:
	errors: list[str] = []
	bronze_dir = Path("data") / "bronze" / version

	empresas_path = bronze_dir / "empresas.parquet"
	estabelecimentos_path = bronze_dir / "estabelecimentos.parquet"

	if not validate_parquet_exists(empresas_path):
		errors.append(f"Missing empresas bronze parquet: {empresas_path}")
	if not validate_parquet_exists(estabelecimentos_path):
		errors.append(f"Missing estabelecimentos bronze parquet: {estabelecimentos_path}")

	empresas_columns_result = validate_required_columns(empresas_path, EMPRESAS_SILVER_COLUMNS)
	estabelecimentos_columns_result = validate_required_columns(
		estabelecimentos_path,
		["cnpj_basico", "cnpj_ordem", "cnpj_dv", "uf", "codigo_municipio", "cnae_principal", "situacao_cadastral"],
	)
	empresas_rows_result = validate_min_rows(empresas_path, min_rows=1)
	estabelecimentos_rows_result = validate_min_rows(estabelecimentos_path, min_rows=1)

	for result in [
		empresas_columns_result,
		estabelecimentos_columns_result,
		empresas_rows_result,
		estabelecimentos_rows_result,
	]:
		if not result["valid"]:
			errors.extend(result["errors"])

	return errors


def _validate_silver_outputs(version: str) -> list[str]:
	errors: list[str] = []
	silver_dir = Path("data") / "silver" / version

	required_files = [
		silver_dir / "empresas_clean.parquet",
		silver_dir / "estabelecimentos_clean.parquet",
		silver_dir / "socios_clean.parquet",
		silver_dir / "simples_clean.parquet",
		silver_dir / "municipios_clean.parquet",
	]
	for file_path in required_files:
		if not validate_parquet_exists(file_path):
			errors.append(f"Missing silver parquet: {file_path}")

	empresas_rows = validate_min_rows(silver_dir / "empresas_clean.parquet", min_rows=1)
	estabelecimentos_rows = validate_min_rows(silver_dir / "estabelecimentos_clean.parquet", min_rows=1)
	if not empresas_rows["valid"]:
		errors.extend(empresas_rows["errors"])
	if not estabelecimentos_rows["valid"]:
		errors.extend(estabelecimentos_rows["errors"])

	return errors


def run_pipeline(version: str, skip_download: bool = False, include_large_files: bool = False) -> int:
	configure_logger()
	configure_pipeline_logger()
	create_database_tables()

	logger.info(
		"Starting pipeline run: version={} skip_download={} include_large_files={}",
		version,
		skip_download,
		include_large_files,
	)

	raw_dir = Path("data") / "raw" / version
	bronze_dir = Path("data") / "bronze" / version
	silver_dir = Path("data") / "silver" / version
	gold_dir = Path("data") / "gold" / version
	raw_dir.mkdir(parents=True, exist_ok=True)
	bronze_dir.mkdir(parents=True, exist_ok=True)
	silver_dir.mkdir(parents=True, exist_ok=True)
	gold_dir.mkdir(parents=True, exist_ok=True)

	db = SessionLocal()
	try:
		dataset = get_dataset_version_by_version(db, version)
		if dataset is None:
			dataset = create_dataset_version(db, version=version)

		update_dataset_status(db, dataset.id, "downloading", raw_path=str(raw_dir), error_message=None)

		manifest, files = _prepare_manifest(version=version, include_large_files=include_large_files)

		if not skip_download:
			update_manifest_status(manifest, "downloading")
			save_manifest(manifest, get_manifest_path(version))
			manifest = download_files(files=files, version=version, manifest=manifest)
			download_failed = any(file_info.get("status") == "failed" for file_info in manifest.get("files", []))
			if download_failed:
				update_manifest_status(manifest, "failed")
				save_manifest(manifest, get_manifest_path(version))
				update_dataset_status(
					db,
					dataset.id,
					"failed",
					raw_path=str(raw_dir),
					error_message="One or more downloads failed",
				)
				return 1

			update_manifest_status(manifest, "downloaded")
			save_manifest(manifest, get_manifest_path(version))

			zip_validation = validate_raw_downloads(version=version, manifest=manifest)
			if zip_validation["failed"] > 0:
				update_dataset_status(
					db,
					dataset.id,
					"failed",
					raw_path=str(raw_dir),
					error_message="ZIP validation failed",
				)
				return 1

			update_dataset_status(db, dataset.id, "downloaded", raw_path=str(raw_dir), error_message=None)
		else:
			logger.warning("Skipping download and ZIP validation by flag")

		update_dataset_status(db, dataset.id, "processing", raw_path=str(raw_dir), bronze_path=str(bronze_dir))

		process_empresas_bronze(version)
		process_estabelecimentos_bronze(version)
		process_socios_bronze(version)
		process_simples_bronze(version)

		bronze_errors = _validate_bronze_outputs(version)
		if bronze_errors:
			update_dataset_status(db, dataset.id, "failed", error_message="; ".join(bronze_errors))
			return 1

		process_empresas_silver(version)
		process_estabelecimentos_silver(version)
		process_socios_silver(version)
		process_simples_silver(version)
		process_municipios_silver(version)

		update_dataset_status(db, dataset.id, "processing", silver_path=str(silver_dir))

		silver_errors = _validate_silver_outputs(version)
		if silver_errors:
			update_dataset_status(db, dataset.id, "failed", error_message="; ".join(silver_errors))
			return 1

		gold_path = build_gold_layer(version)
		gold_validation = validate_gold_layer(gold_path)
		if not gold_validation["valid"]:
			update_dataset_status(db, dataset.id, "failed", error_message="; ".join(gold_validation["errors"]))
			return 1

		update_dataset_status(
			db,
			dataset.id,
			"validated",
			gold_path=str(gold_path),
			row_count=gold_validation["row_count"],
			error_message=None,
		)
		publish_dataset_version(db, dataset.id)

		logger.info(
			"Pipeline finished successfully: version={} row_count={} gold_path={}",
			version,
			gold_validation["row_count"],
			gold_path,
		)
		return 0
	except Exception as exc:
		logger.exception("Pipeline run failed for version={}", version)
		dataset = get_dataset_version_by_version(db, version)
		if dataset is not None:
			update_dataset_status(db, dataset.id, "failed", error_message=str(exc))
		return 1
	finally:
		db.close()


def main() -> None:
	parser = argparse.ArgumentParser(description="Run CNPJ data pipeline")
	parser.add_argument("--version", default=_default_version(), help="Dataset version label")
	parser.add_argument("--skip-download", action="store_true", help="Skip RAW download and ZIP validation")
	parser.add_argument("--include-large-files", action="store_true", help="Include large Receita files")
	args = parser.parse_args()

	exit_code = run_pipeline(
		version=args.version,
		skip_download=args.skip_download,
		include_large_files=args.include_large_files,
	)
	raise SystemExit(exit_code)


if __name__ == "__main__":
	main()
