from collections.abc import Sequence

import duckdb
from loguru import logger


def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
	return duckdb.connect(database=":memory:")


def execute_query(
	query: str,
	parameters: Sequence | None = None,
) -> list[dict]:
	try:
		with get_duckdb_connection() as connection:
			cursor = connection.execute(query, parameters or [])
			rows = cursor.fetchall()
			columns = [col[0] for col in cursor.description]
		return [dict(zip(columns, row)) for row in rows]
	except Exception:
		logger.exception("DuckDB query execution failed")
		return []


def query_parquet(
	query: str,
	parameters: Sequence | None = None,
) -> list[dict]:
	return execute_query(query=query, parameters=parameters)
