from pathlib import Path

from loguru import logger


RECEITA_BASE_URL = "https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj"

AUXILIARY_PREFIXES = [
	"Cnaes",
	"Municipios",
	"Naturezas",
	"Paises",
	"Qualificacoes",
	"Motivos",
]

# Large files can be very expensive for CPU, disk and memory usage.
LARGE_PREFIXES = [
	"Empresas",
	"Estabelecimentos",
	"Socios",
	"Simples",
]


def discover_receita_files(version: str, include_large_files: bool = False) -> list[dict]:
	prefixes = list(AUXILIARY_PREFIXES)
	if include_large_files:
		prefixes.extend(LARGE_PREFIXES)

	files = []
	for prefix in prefixes:
		name = f"{prefix}0.zip"
		files.append(
			{
				"name": name,
				"url": f"{RECEITA_BASE_URL}/{version}/{name}",
				"path": str(Path("data") / "raw" / version / name),
			}
		)

	logger.info(
		"Discovered Receita files: version={} include_large_files={} count={}",
		version,
		include_large_files,
		len(files),
	)
	return files
