import hashlib
import json
from pathlib import Path

from app.database.duckdb import query_parquet
from app.schemas.search import CompanyResult, SearchRequest, SearchResponse
from app.services.cache_service import get_cache, set_cache


PARQUET_PATH = Path("data/gold/dev/empresas_consulta.parquet")


def _build_where_clause(request: SearchRequest) -> tuple[str, list]:
	filters: list[str] = []
	params: list = []

	def add_filter(column: str, value: object) -> None:
		filters.append(f"{column} = ?")
		params.append(value)

	if request.uf:
		add_filter("uf", request.uf)
	if request.municipio:
		add_filter("municipio", request.municipio.upper())
	if request.cnae_principal:
		add_filter("cnae_principal", request.cnae_principal)
	if request.situacao_cadastral:
		add_filter("situacao_cadastral", request.situacao_cadastral)
	if request.opcao_simples is not None:
		add_filter("opcao_simples", request.opcao_simples)
	if request.opcao_mei is not None:
		add_filter("opcao_mei", request.opcao_mei)
	if request.porte_empresa:
		add_filter("porte_empresa", request.porte_empresa)
	if request.data_inicio_min:
		filters.append("data_inicio_atividade >= ?")
		params.append(request.data_inicio_min.isoformat())
	if request.data_inicio_max:
		filters.append("data_inicio_atividade <= ?")
		params.append(request.data_inicio_max.isoformat())

	where_clause = ""
	if filters:
		where_clause = " WHERE " + " AND ".join(filters)
	return where_clause, params


def _search_cache_key(request: SearchRequest) -> str:
	payload = json.dumps(request.model_dump(mode="json"), sort_keys=True)
	digest = hashlib.md5(payload.encode("utf-8")).hexdigest()
	return f"search:{digest}"


def count_search_results(request: SearchRequest) -> int:
	if not PARQUET_PATH.exists():
		return 0

	where_clause, where_params = _build_where_clause(request)
	base_params = [str(PARQUET_PATH), *where_params]
	count_query = f"SELECT COUNT(*) AS total FROM read_parquet(?) {where_clause}"
	count_result = query_parquet(count_query, base_params)
	return int(count_result[0]["total"]) if count_result else 0


def search_companies(request: SearchRequest) -> SearchResponse:
	if not PARQUET_PATH.exists():
		return SearchResponse(page=request.page, page_size=request.page_size, total=0, data=[])

	cache_key = _search_cache_key(request)
	cached = get_cache(cache_key)
	if cached:
		try:
			return SearchResponse.model_validate_json(cached)
		except Exception:
			pass

	where_clause, where_params = _build_where_clause(request)
	base_params = [str(PARQUET_PATH), *where_params]

	total = count_search_results(request)

	offset = (request.page - 1) * request.page_size
	data_query = (
		"SELECT cnpj_completo, razao_social, nome_fantasia, uf, municipio, cnae_principal, "
		"situacao_cadastral, opcao_simples, opcao_mei, porte_empresa, data_inicio_atividade "
		f"FROM read_parquet(?) {where_clause} "
		"ORDER BY razao_social LIMIT ? OFFSET ?"
	)
	data_params = [*base_params, request.page_size, offset]
	rows = query_parquet(data_query, data_params)

	response = SearchResponse(
		page=request.page,
		page_size=request.page_size,
		total=total,
		data=[CompanyResult(**row) for row in rows],
	)
	set_cache(cache_key, response.model_dump_json(), expire_seconds=300)
	return response
