from pathlib import Path

from loguru import logger


# Future: move to environment variable when pipeline configuration is externalized.
RECEITA_BASE_URL = "https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj"

# Small/auxiliary reference tables.
AUXILIARY_FILE_PREFIXES = [
	"Cnaes",
	"Municipios",
	"Naturezas",
	"Paises",
	"Qualificacoes",
	"Motivos",
]

# Large datasets can consume significant disk, memory and processing time.
LARGE_FILE_PREFIXES = [
	"Empresas",
	"Estabelecimentos",
	"Socios",
	"Simples",
]


def _build_file_descriptor(version: str, prefix: str, index: int = 0) -> dict:
	name = f"{prefix}{index}.zip"
	url = f"{RECEITA_BASE_URL}/{version}/{name}"
	path = str(Path("data") / "raw" / version / name)
	return {
		"name": name,
		"url": url,
		"path": path,
	}


def discover_receita_files(version: str, include_large_files: bool = False) -> list[dict]:
	prefixes = [*AUXILIARY_FILE_PREFIXES]
	if include_large_files:
		prefixes.extend(LARGE_FILE_PREFIXES)

	files = [_build_file_descriptor(version, prefix) for prefix in prefixes]
	logger.info(
		"Discovered Receita files: version={} include_large_files={} count={}",
		version,
		include_large_files,
		len(files),
	)
	return files
