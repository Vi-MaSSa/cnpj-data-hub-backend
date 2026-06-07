from pathlib import Path
import zipfile

from loguru import logger

from pipeline.ingestion.manifest import get_manifest_path, save_manifest, update_file_status


def is_valid_zip(file_path: str | Path) -> bool:
	return bool(validate_zip_file(file_path)["valid"])


def validate_zip_file(file_path: str | Path) -> dict:
	path = Path(file_path)

	if not path.exists():
		return {
			"valid": False,
			"file_path": str(path),
			"size_bytes": 0,
			"error_message": "File does not exist",
		}

	size_bytes = path.stat().st_size
	if size_bytes <= 0:
		return {
			"valid": False,
			"file_path": str(path),
			"size_bytes": size_bytes,
			"error_message": "File size must be greater than zero",
		}

	if path.suffix.lower() != ".zip":
		return {
			"valid": False,
			"file_path": str(path),
			"size_bytes": size_bytes,
			"error_message": "File extension is not .zip",
		}

	try:
		with zipfile.ZipFile(path, "r") as archive:
			invalid_member = archive.testzip()
			if invalid_member is not None:
				return {
					"valid": False,
					"file_path": str(path),
					"size_bytes": size_bytes,
					"error_message": f"Corrupted zip entry: {invalid_member}",
				}

			members = archive.namelist()
			if len(members) == 0:
				return {
					"valid": False,
					"file_path": str(path),
					"size_bytes": size_bytes,
					"error_message": "Zip has no internal files",
				}
	except Exception as exc:
		return {
			"valid": False,
			"file_path": str(path),
			"size_bytes": size_bytes,
			"error_message": str(exc),
		}

	return {
		"valid": True,
		"file_path": str(path),
		"size_bytes": size_bytes,
		"error_message": None,
	}


def validate_downloaded_zips(version: str, manifest: dict) -> dict:
	manifest_path = get_manifest_path(version)

	validated_count = 0
	failed_count = 0
	total = 0

	for file_info in manifest.get("files", []):
		if file_info.get("status") not in {"downloaded", "skipped", "validated"}:
			continue

		total += 1
		result = validate_zip_file(file_info.get("path", ""))
		if result["valid"]:
			validated_count += 1
			update_file_status(
				manifest,
				file_info["name"],
				"validated",
				size_bytes=result["size_bytes"],
				error_message=None,
			)
		else:
			failed_count += 1
			update_file_status(
				manifest,
				file_info["name"],
				"failed",
				size_bytes=result["size_bytes"],
				error_message=result["error_message"],
			)

	save_manifest(manifest, manifest_path)
	logger.info(
		"ZIP validation finished: version={} total={} validated={} failed={}",
		version,
		total,
		validated_count,
		failed_count,
	)

	return {
		"valid": failed_count == 0,
		"total": total,
		"validated": validated_count,
		"failed": failed_count,
	}
