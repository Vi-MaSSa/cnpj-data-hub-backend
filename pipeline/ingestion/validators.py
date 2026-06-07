from loguru import logger

from pipeline.ingestion.manifest import get_manifest_path, save_manifest, update_manifest_status
from pipeline.validation.validate_zip import validate_downloaded_zips


def validate_raw_downloads(version: str, manifest: dict) -> dict:
	result = validate_downloaded_zips(version=version, manifest=manifest)

	if result["failed"] > 0:
		update_manifest_status(manifest, "failed")
	elif result["validated"] > 0:
		update_manifest_status(manifest, "validated")
	else:
		update_manifest_status(manifest, "pending")

	save_manifest(manifest, get_manifest_path(version))
	logger.info(
		"RAW validation summary: version={} manifest_status={} validated={} failed={}",
		version,
		manifest["status"],
		result["validated"],
		result["failed"],
	)
	return result
