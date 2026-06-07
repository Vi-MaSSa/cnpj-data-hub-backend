from pathlib import Path
import zipfile

from loguru import logger

from pipeline.ingestion.manifest import get_manifest_path, save_manifest, update_file_status


def is_valid_zip(file_path: str | Path) -> bool:
	result = validate_zip_file(file_path)
	return bool(result["valid"])


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
			"error_message": "File is empty",
		}

	if path.suffix.lower() != ".zip":
		return {
			"valid": False,
			"file_path": str(path),
			"size_bytes": size_bytes,
			"error_message": "File extension is not .zip",
		}

	try:
		with zipfile.ZipFile(path, "r") as zip_file:
			invalid_entry = zip_file.testzip()
			if invalid_entry is not None:
				return {
					"valid": False,
					"file_path": str(path),
					"size_bytes": size_bytes,
					"error_message": f"Corrupted zip entry: {invalid_entry}",
				}

			members = zip_file.namelist()
			if len(members) == 0:
				return {
					"valid": False,
					"file_path": str(path),
					"size_bytes": size_bytes,
					"error_message": "Zip file has no members",
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

	total = 0
	validated = 0
	failed = 0
	results: list[dict] = []

	for file_info in manifest.get("files", []):
		status = file_info.get("status")
		if status not in {"downloaded", "skipped", "validated"}:
			continue

		total += 1
		file_path = file_info.get("path")
		if not file_path:
			failed += 1
			update_file_status(
				manifest,
				file_info["name"],
				"failed",
				error_message="Missing file path in manifest",
			)
			continue

		result = validate_zip_file(file_path)
		results.append(result)
		if result["valid"]:
			validated += 1
			update_file_status(
				manifest,
				file_info["name"],
				"validated",
				size_bytes=result["size_bytes"],
				error_message=None,
			)
		else:
			failed += 1
			update_file_status(
				manifest,
				file_info["name"],
				"failed",
				size_bytes=result["size_bytes"],
				error_message=result["error_message"],
			)

	save_manifest(manifest, manifest_path)
	logger.info(
		"ZIP validation summary: version={} total={} validated={} failed={}",
		version,
		total,
		validated,
		failed,
	)
	return {
		"total": total,
		"validated": validated,
		"failed": failed,
		"results": results,
	}
