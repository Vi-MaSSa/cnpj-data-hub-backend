import json
from datetime import datetime, UTC
from pathlib import Path

from loguru import logger


MANIFEST_STATUSES = {"pending", "downloading", "downloaded", "failed", "validated"}
FILE_STATUSES = {"pending", "downloading", "downloaded", "failed", "validated", "skipped"}


def _utc_now_iso() -> str:
	return datetime.now(UTC).isoformat()


def get_manifest_path(version: str) -> Path:
	return Path("data") / "raw" / version / "manifest.json"


def create_manifest(source: str, version: str, files: list[dict]) -> dict:
	now = _utc_now_iso()
	normalized_files: list[dict] = []
	for file_info in files:
		normalized_files.append(
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

	manifest = {
		"source": source,
		"version": version,
		"status": "pending",
		"created_at": now,
		"updated_at": now,
		"files": normalized_files,
	}
	logger.info("Manifest created: version={} files={}", version, len(normalized_files))
	return manifest


def load_manifest(path: str | Path) -> dict:
	manifest_path = Path(path)
	with manifest_path.open("r", encoding="utf-8") as file:
		manifest = json.load(file)
	logger.info("Manifest loaded: path={}", manifest_path)
	return manifest


def save_manifest(manifest: dict, path: str | Path) -> None:
	manifest_path = Path(path)
	manifest_path.parent.mkdir(parents=True, exist_ok=True)
	manifest["updated_at"] = _utc_now_iso()
	with manifest_path.open("w", encoding="utf-8") as file:
		json.dump(manifest, file, ensure_ascii=False, indent=2)
	logger.debug("Manifest saved: path={}", manifest_path)


def update_manifest_status(manifest: dict, status: str) -> dict:
	if status not in MANIFEST_STATUSES:
		raise ValueError(f"Invalid manifest status: {status}")
	manifest["status"] = status
	manifest["updated_at"] = _utc_now_iso()
	return manifest


def update_file_status(manifest: dict, file_name: str, status: str, **kwargs) -> dict:
	if status not in FILE_STATUSES:
		raise ValueError(f"Invalid file status: {status}")

	for file_info in manifest.get("files", []):
		if file_info.get("name") == file_name:
			file_info["status"] = status
			for key, value in kwargs.items():
				file_info[key] = value
			manifest["updated_at"] = _utc_now_iso()
			return manifest

	raise ValueError(f"File not found in manifest: {file_name}")
