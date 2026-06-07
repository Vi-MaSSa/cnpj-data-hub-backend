import time
from datetime import datetime, UTC
from pathlib import Path

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from pipeline.ingestion.manifest import get_manifest_path, save_manifest, update_file_status


def _utc_now_iso() -> str:
	return datetime.now(UTC).isoformat()


def _download_stream(url: str, part_path: Path) -> int:
	settings = get_settings()

	@retry(
		stop=stop_after_attempt(settings.download_max_retries),
		wait=wait_exponential(multiplier=1, min=1, max=8),
		reraise=True,
	)
	def _run() -> int:
		total_size = 0
		with httpx.stream("GET", url, timeout=settings.download_timeout_seconds) as response:
			response.raise_for_status()
			with part_path.open("wb") as part_file:
				for chunk in response.iter_bytes():
					if not chunk:
						continue
					part_file.write(chunk)
					total_size += len(chunk)
		return total_size

	return _run()


def download_file(file_info: dict, manifest: dict, version: str) -> dict:
	manifest_path = get_manifest_path(version)
	file_name = file_info["name"]
	destination = Path(file_info["path"])
	url = file_info["url"]
	destination.parent.mkdir(parents=True, exist_ok=True)

	bound_logger = logger.bind(file_name=file_name, version=version)

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
		bound_logger.info("File already exists, skipping download: path={}", destination)
		return manifest

	update_file_status(manifest, file_name, "downloading", error_message=None)
	save_manifest(manifest, manifest_path)

	start_time = time.perf_counter()
	part_path = Path(f"{destination}.part")

	try:
		size_bytes = _download_stream(url, part_path)
		part_path.replace(destination)

		duration = time.perf_counter() - start_time
		update_file_status(
			manifest,
			file_name,
			"downloaded",
			size_bytes=size_bytes,
			downloaded_at=_utc_now_iso(),
			error_message=None,
		)
		save_manifest(manifest, manifest_path)
		bound_logger.info(
			"Download completed: url={} destination={} size_bytes={} duration_seconds={:.2f}",
			url,
			destination,
			size_bytes,
			duration,
		)
		return manifest
	except Exception as exc:
		duration = time.perf_counter() - start_time
		update_file_status(
			manifest,
			file_name,
			"failed",
			error_message=str(exc),
		)
		save_manifest(manifest, manifest_path)
		bound_logger.exception(
			"Download failed: url={} destination={} duration_seconds={:.2f}",
			url,
			destination,
			duration,
		)
		return manifest


def download_files(files: list[dict], version: str, manifest: dict) -> dict:
	logger.info("Starting downloads: version={} total_files={}", version, len(files))
	for file_info in files:
		manifest = download_file(file_info=file_info, manifest=manifest, version=version)

	return manifest
