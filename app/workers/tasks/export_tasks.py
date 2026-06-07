import csv
from pathlib import Path

from loguru import logger

from app.config import get_settings
from app.database.duckdb import query_parquet
from app.database.postgres import SessionLocal
from app.database.repositories.job_repository import (
	get_export_job_by_id,
	mark_export_job_failed,
	mark_export_job_ready,
	update_export_job_status,
)
from app.schemas.search import SearchRequest
from app.services.search_service import _build_where_clause


def process_export_task(job_id: str) -> None:
	logger.info("Starting export task: job_id={}", job_id)
	settings = get_settings()

	db = SessionLocal()
	try:
		job = update_export_job_status(db, job_id, "processing")
		if job is None:
			return

		loaded_job = get_export_job_by_id(db, job_id)
		if loaded_job is None:
			return

		# SearchRequest enforces page_size<=100, but export row limits are validated separately.
		request = SearchRequest(**loaded_job.filters_json, page=1, page_size=100)
		where_clause, where_params = _build_where_clause(request)

		parquet_path = Path("data/gold/dev/empresas_consulta.parquet")
		if not parquet_path.exists():
			raise FileNotFoundError(
				"Missing empresas_consulta.parquet. Run: python -m pipeline.processing.build_fake_gold"
			)

		count_query = f"SELECT COUNT(*) AS total FROM read_parquet(?) {where_clause}"
		count_result = query_parquet(count_query, [str(parquet_path), *where_params])
		total = int(count_result[0]["total"]) if count_result else 0

		if total > settings.export_max_rows:
			mark_export_job_failed(
				db,
				job_id,
				f"Export exceeded limit of {settings.export_max_rows} rows",
			)
			return

		export_query = (
			"SELECT cnpj_completo, razao_social, nome_fantasia, uf, municipio, cnae_principal, "
			"situacao_cadastral, opcao_simples, opcao_mei, porte_empresa, data_inicio_atividade "
			f"FROM read_parquet(?) {where_clause} ORDER BY razao_social"
		)
		rows = query_parquet(export_query, [str(parquet_path), *where_params])

		ready_dir = Path("exports/ready")
		ready_dir.mkdir(parents=True, exist_ok=True)
		output_file = ready_dir / f"{job_id}.csv"

		fieldnames = [
			"cnpj_completo",
			"razao_social",
			"nome_fantasia",
			"uf",
			"municipio",
			"cnae_principal",
			"situacao_cadastral",
			"opcao_simples",
			"opcao_mei",
			"porte_empresa",
			"data_inicio_atividade",
		]
		with output_file.open("w", newline="", encoding="utf-8") as file:
			writer = csv.DictWriter(file, fieldnames=fieldnames)
			writer.writeheader()
			writer.writerows(rows)

		mark_export_job_ready(db, job_id, str(output_file), row_count=len(rows))
		logger.success("Export task completed: job_id={} file={} rows={}", job_id, output_file, len(rows))
	except Exception as exc:
		logger.exception("Export task failed: job_id={}", job_id)
		mark_export_job_failed(db, job_id, str(exc))
	finally:
		db.close()


def fake_export_task(job_id: str) -> None:
	process_export_task(job_id)
