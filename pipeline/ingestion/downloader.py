import time
from datetime import datetime, UTC
from pathlib import Path

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from pipeline.ingestion.manifest import (
	get_manifest_path,
	save_manifest,
	update_file_status,
)


def _utc_now_iso() -> str:
	return datetime.now(UTC).isoformat()


def _get_destination_path(file_info: dict) -> Path:
	if "path" in file_info and file_info["path"]:
		return Path(file_info["path"])
	return Path("data") / "raw" / file_info["version"] / file_info["name"]


def _download_with_retry(url: str, destination_part: Path) -> int:
	settings = get_settings()

	@retry(
		stop=stop_after_attempt(settings.download_max_retries),
		wait=wait_exponential(multiplier=1, min=1, max=8),
		reraise=True,
	)
	def _run() -> int:
		with httpx.stream("GET", url, timeout=settings.download_timeout_seconds) as response:
			response.raise_for_status()
			destination_part.parent.mkdir(parents=True, exist_ok=True)
			size_bytes = 0
			with destination_part.open("wb") as output_file:
				for chunk in response.iter_bytes():
					if not chunk:
						continue
					output_file.write(chunk)
					size_bytes += len(chunk)
			return size_bytes

	return _run()


def download_file(file_info: dict, manifest: dict, version: str) -> dict:
	manifest_path = get_manifest_path(version)
	file_name = file_info["name"]
	url = file_info["url"]
	destination = _get_destination_path(file_info)
	part_path = destination.with_suffix(destination.suffix + ".part")

	file_logger = logger.bind(file_name=file_name, version=version)
	started_at = time.perf_counter()

	if destination.exists() and destination.stat().st_size > 0:
		update_file_status(
			manifest,
			file_name,
			"skipped",
			size_bytes=destination.stat().st_size,
			downloaded_at=_utc_now_iso(),
			error_message=None,
		)
		save_manifest(manifest, manifest_path)
		file_logger.info("Download skipped (file already exists): path={}", destination)
		return manifest

	update_file_status(manifest, file_name, "downloading", error_message=None)
	save_manifest(manifest, manifest_path)

	try:
		size_bytes = _download_with_retry(url, part_path)
		part_path.replace(destination)
		duration = time.perf_counter() - started_at
		update_file_status(
			manifest,
			file_name,
			"downloaded",
			size_bytes=size_bytes,
			downloaded_at=_utc_now_iso(),
			error_message=None,
			path=str(destination),
		)
		save_manifest(manifest, manifest_path)
		file_logger.info(
			"Download finished: url={} path={} size_bytes={} duration_seconds={:.2f}",
			url,
			destination,
			size_bytes,
			duration,
		)
	except Exception as exc:
		duration = time.perf_counter() - started_at
		update_file_status(
			manifest,
			file_name,
			"failed",
			error_message=str(exc),
			path=str(destination),
		)
		save_manifest(manifest, manifest_path)
		file_logger.exception(
			"Download failed: url={} path={} duration_seconds={:.2f}",
			url,
			destination,
			duration,
		)
	return manifest


def download_files(files: list[dict], version: str, manifest: dict) -> dict:
	logger.info("Starting download batch: version={} files={}", version, len(files))
	for file_info in files:
		manifest = download_file(file_info, manifest, version)

	stats = {
		"downloaded": 0,
		"skipped": 0,
		"failed": 0,
	}
	for file_info in manifest.get("files", []):
		status = file_info.get("status")
		if status in stats:
			stats[status] += 1

	logger.info(
		"Download batch finished: version={} downloaded={} skipped={} failed={}",
		version,
		stats["downloaded"],
		stats["skipped"],
		stats["failed"],
	)
	return manifest
