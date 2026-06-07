import argparse
from datetime import datetime
from pathlib import Path

from loguru import logger

from app.database.postgres import SessionLocal
from app.database.repositories.dataset_repository import (
	create_dataset_version,
	get_dataset_version_by_version,
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


def _default_version() -> str:
	return "dev-real-download"


def _merge_manifest_files(manifest: dict, discovered_files: list[dict]) -> dict:
	existing_files = {file_info["name"]: file_info for file_info in manifest.get("files", [])}
	for discovered in discovered_files:
		name = discovered["name"]
		if name in existing_files:
			existing_files[name]["url"] = discovered["url"]
			existing_files[name]["path"] = discovered["path"]
			continue

		existing_files[name] = {
			"name": discovered["name"],
			"url": discovered["url"],
			"path": discovered["path"],
			"size_bytes": None,
			"status": "pending",
			"checksum": None,
			"error_message": None,
			"downloaded_at": None,
		}

	manifest["files"] = list(existing_files.values())
	return manifest


def run(version: str, include_large_files: bool) -> int:
	configure_logger()
	configure_pipeline_logger()

	logger.info(
		"Starting RAW pipeline: version={} include_large_files={}",
		version,
		include_large_files,
	)

	db = SessionLocal()
	manifest_path = get_manifest_path(version)
	raw_path = Path("data") / "raw" / version
	raw_path.mkdir(parents=True, exist_ok=True)

	try:
		dataset = get_dataset_version_by_version(db, version)
		if dataset is None:
			dataset = create_dataset_version(db, version=version)

		update_dataset_status(
			db,
			dataset.id,
			status="downloading",
			raw_path=str(raw_path),
			error_message=None,
		)

		discovered_files = discover_receita_files(
			version=version,
			include_large_files=include_large_files,
		)

		if manifest_path.exists():
			manifest = load_manifest(manifest_path)
			manifest = _merge_manifest_files(manifest, discovered_files)
		else:
			manifest = create_manifest(
				source="receita_federal_cnpj",
				version=version,
				files=discovered_files,
			)

		update_manifest_status(manifest, "downloading")
		save_manifest(manifest, manifest_path)

		manifest = download_files(discovered_files, version=version, manifest=manifest)

		download_failed = any(
			file_info.get("status") == "failed" for file_info in manifest.get("files", [])
		)
		if download_failed:
			update_manifest_status(manifest, "failed")
			save_manifest(manifest, manifest_path)
			update_dataset_status(
				db,
				dataset.id,
				status="failed",
				raw_path=str(raw_path),
				error_message="One or more downloads failed",
			)
			return 1

		update_manifest_status(manifest, "downloaded")
		save_manifest(manifest, manifest_path)

		validation_result = validate_raw_downloads(version=version, manifest=manifest)
		if validation_result["failed"] > 0:
			update_dataset_status(
				db,
				dataset.id,
				status="failed",
				raw_path=str(raw_path),
				error_message="ZIP validation failed",
			)
			return 1

		update_dataset_status(
			db,
			dataset.id,
			status="downloaded",
			raw_path=str(raw_path),
			error_message=None,
		)

		logger.info(
			"RAW pipeline finished successfully: version={} files_validated={} at={}",
			version,
			validation_result["validated"],
			datetime.now().isoformat(),
		)
		return 0

	except Exception as exc:
		logger.exception("RAW pipeline failed: version={}", version)
		dataset = get_dataset_version_by_version(db, version)
		if dataset is not None:
			update_dataset_status(
				db,
				dataset.id,
				status="failed",
				raw_path=str(raw_path),
				error_message=str(exc),
			)
		return 1
	finally:
		db.close()


def main() -> None:
	parser = argparse.ArgumentParser(description="Run RAW Receita Federal download pipeline")
	parser.add_argument("--version", type=str, default=_default_version())
	parser.add_argument("--include-large-files", action="store_true")
	args = parser.parse_args()

	exit_code = run(version=args.version, include_large_files=args.include_large_files)
	raise SystemExit(exit_code)


if __name__ == "__main__":
	main()
