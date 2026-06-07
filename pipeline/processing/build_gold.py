from pathlib import Path
import shutil

from loguru import logger
import polars as pl

from pipeline.schemas.gold_schema import GOLD_COLUMNS


def _ensure_optional_columns(frame: pl.DataFrame, required_columns: list[str]) -> pl.DataFrame:
	result = frame
	for column in required_columns:
		if column not in result.columns:
			default_value = False if column in {"opcao_simples", "opcao_mei"} else None
			result = result.with_columns(pl.lit(default_value).alias(column))
	return result


def _sync_active_gold_paths(version: str, files: list[Path]) -> None:
	current_dir = Path("data") / "gold" / "current"
	dev_dir = Path("data") / "gold" / "dev"
	current_dir.mkdir(parents=True, exist_ok=True)
	dev_dir.mkdir(parents=True, exist_ok=True)

	for file_path in files:
		shutil.copy2(file_path, current_dir / file_path.name)
		shutil.copy2(file_path, dev_dir / file_path.name)

	logger.info("Synced Gold outputs to compatibility paths: current and dev (source version={})", version)


def build_gold_layer(version: str) -> Path:
	silver_dir = Path("data") / "silver" / version
	gold_dir = Path("data") / "gold" / version
	gold_dir.mkdir(parents=True, exist_ok=True)

	empresas_path = silver_dir / "empresas_clean.parquet"
	estabelecimentos_path = silver_dir / "estabelecimentos_clean.parquet"
	simples_path = silver_dir / "simples_clean.parquet"
	municipios_path = silver_dir / "municipios_clean.parquet"

	if not empresas_path.exists() or not estabelecimentos_path.exists():
		raise FileNotFoundError("Empresas and Estabelecimentos Silver parquet files are required")

	empresas = pl.read_parquet(empresas_path)
	estabelecimentos = pl.read_parquet(estabelecimentos_path)

	gold = estabelecimentos.join(empresas, on="cnpj_basico", how="left")

	if simples_path.exists():
		simples = pl.read_parquet(simples_path)
		gold = gold.join(simples, on="cnpj_basico", how="left")

	if municipios_path.exists():
		municipios = pl.read_parquet(municipios_path)
		gold = gold.join(municipios, on="codigo_municipio", how="left")

	gold = gold.with_columns(
		[
			pl.col("cnpj_completo").cast(pl.Utf8, strict=False),
			pl.col("razao_social").cast(pl.Utf8, strict=False),
			pl.col("nome_fantasia").cast(pl.Utf8, strict=False),
			pl.col("cnae_principal").cast(pl.Utf8, strict=False),
			pl.col("cnae_secundario").cast(pl.Utf8, strict=False),
			pl.col("uf").cast(pl.Utf8, strict=False),
			pl.when(pl.col("municipio").is_null())
			.then(pl.col("codigo_municipio"))
			.otherwise(pl.col("municipio"))
			.cast(pl.Utf8, strict=False)
			.alias("municipio"),
			pl.col("codigo_municipio").cast(pl.Utf8, strict=False),
			pl.col("codigo_ibge").cast(pl.Utf8, strict=False),
			pl.col("bairro").cast(pl.Utf8, strict=False),
			pl.col("cep").cast(pl.Utf8, strict=False),
			pl.col("ddd_1").cast(pl.Utf8, strict=False),
			pl.col("telefone_1").cast(pl.Utf8, strict=False),
			pl.col("situacao_cadastral").cast(pl.Utf8, strict=False),
			pl.col("data_inicio_atividade").cast(pl.Utf8, strict=False),
			pl.col("porte_empresa").cast(pl.Utf8, strict=False),
			pl.col("natureza_juridica").cast(pl.Utf8, strict=False),
			pl.col("opcao_simples").cast(pl.Boolean, strict=False).fill_null(False),
			pl.col("opcao_mei").cast(pl.Boolean, strict=False).fill_null(False),
			pl.lit(version).alias("dataset_version"),
		]
	)

	gold = _ensure_optional_columns(gold, GOLD_COLUMNS).select(GOLD_COLUMNS)

	empresas_consulta_path = gold_dir / "empresas_consulta.parquet"
	gold.write_parquet(empresas_consulta_path)

	filtros_ufs = gold.select("uf").drop_nulls().unique().sort("uf")
	filtros_municipios = gold.select("uf", "municipio").drop_nulls().unique().sort(["uf", "municipio"])
	filtros_cnaes = gold.select("cnae_principal").drop_nulls().unique().sort("cnae_principal")
	filtros_situacoes = gold.select("situacao_cadastral").drop_nulls().unique().sort("situacao_cadastral")

	filtros_ufs_path = gold_dir / "filtros_ufs.parquet"
	filtros_municipios_path = gold_dir / "filtros_municipios.parquet"
	filtros_cnaes_path = gold_dir / "filtros_cnaes.parquet"
	filtros_situacoes_path = gold_dir / "filtros_situacoes.parquet"

	filtros_ufs.write_parquet(filtros_ufs_path)
	filtros_municipios.write_parquet(filtros_municipios_path)
	filtros_cnaes.write_parquet(filtros_cnaes_path)
	filtros_situacoes.write_parquet(filtros_situacoes_path)

	_sync_active_gold_paths(
		version,
		[
			empresas_consulta_path,
			filtros_ufs_path,
			filtros_municipios_path,
			filtros_cnaes_path,
			filtros_situacoes_path,
		],
	)

	logger.info("Gold layer built: version={} rows={} path={}", version, gold.height, empresas_consulta_path)
	return empresas_consulta_path
