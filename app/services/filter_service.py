import json
from pathlib import Path

from app.database.duckdb import query_parquet
from app.services.cache_service import get_cache, set_cache


def _load_cached_list(cache_key: str) -> list[str] | None:
    cached = get_cache(cache_key)
    if not cached:
        return None
    try:
        return json.loads(cached)
    except json.JSONDecodeError:
        return None


def _cache_list(cache_key: str, values: list[str]) -> None:
    set_cache(cache_key, json.dumps(values), expire_seconds=3600)


def _require_parquet(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing parquet file: {path}. Run: python -m pipeline.processing.build_fake_gold"
        )


def get_ufs() -> list[str]:
    cache_key = "filters:ufs"
    cached = _load_cached_list(cache_key)
    if cached is not None:
        return cached

    parquet_path = Path("data/gold/dev/filtros_ufs.parquet")
    _require_parquet(parquet_path)
    rows = query_parquet(
        "SELECT uf FROM read_parquet(?) ORDER BY uf",
        [str(parquet_path)],
    )
    values = [row["uf"] for row in rows]
    _cache_list(cache_key, values)
    return values


def get_municipios_by_uf(uf: str) -> list[str]:
    uf_normalized = uf.strip().upper()
    cache_key = f"filters:municipios:{uf_normalized}"
    cached = _load_cached_list(cache_key)
    if cached is not None:
        return cached

    parquet_path = Path("data/gold/dev/filtros_municipios.parquet")
    _require_parquet(parquet_path)
    rows = query_parquet(
        "SELECT municipio FROM read_parquet(?) WHERE uf = ? ORDER BY municipio",
        [str(parquet_path), uf_normalized],
    )
    values = [row["municipio"] for row in rows]
    _cache_list(cache_key, values)
    return values


def get_cnaes() -> list[str]:
    cache_key = "filters:cnaes"
    cached = _load_cached_list(cache_key)
    if cached is not None:
        return cached

    parquet_path = Path("data/gold/dev/filtros_cnaes.parquet")
    _require_parquet(parquet_path)
    rows = query_parquet(
        "SELECT cnae_principal FROM read_parquet(?) ORDER BY cnae_principal",
        [str(parquet_path)],
    )
    values = [row["cnae_principal"] for row in rows]
    _cache_list(cache_key, values)
    return values


def get_situacoes() -> list[str]:
    cache_key = "filters:situacoes"
    cached = _load_cached_list(cache_key)
    if cached is not None:
        return cached

    parquet_path = Path("data/gold/dev/filtros_situacoes.parquet")
    _require_parquet(parquet_path)
    rows = query_parquet(
        "SELECT situacao_cadastral FROM read_parquet(?) ORDER BY situacao_cadastral",
        [str(parquet_path)],
    )
    values = [row["situacao_cadastral"] for row in rows]
    _cache_list(cache_key, values)
    return values