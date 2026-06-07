from loguru import logger

from pipeline.ingestion.manifest import (
	get_manifest_path,
	save_manifest,
	update_manifest_status,
)
from pipeline.validation.validate_zip import validate_downloaded_zips


def validate_raw_downloads(version: str, manifest: dict) -> dict:
	validation_result = validate_downloaded_zips(version, manifest)

	if validation_result["failed"] > 0:
		update_manifest_status(manifest, "failed")
	elif validation_result["validated"] > 0:
		update_manifest_status(manifest, "validated")
	else:
		update_manifest_status(manifest, "pending")

	save_manifest(manifest, get_manifest_path(version))
	logger.info(
		"RAW validation completed: version={} manifest_status={} validated={} failed={}",
		version,
		manifest["status"],
		validation_result["validated"],
		validation_result["failed"],
	)
	return validation_result
