
#  CNPJ Data Hub Backend

  

Backend em FastAPI para ingestao e disponibilizacao de dados publicos de CNPJ, com pipeline em camadas RAW/Bronze/Silver/Gold.

  

Esta branch (`feat/build-real-bronze-silver-gold-layers`) foca na implementacao do pipeline real incremental, com manifest, download resiliente, validacoes e publicacao de versao ativa.

  

##  Stack

  

- Python 3.12

- FastAPI + Uvicorn

- PostgreSQL + SQLAlchemy

- Redis + RQ (fila/worker)

- Polars + DuckDB + Parquet

- httpx + tenacity (download com retry)

- Loguru

  

##  Estrutura Principal

  

```text

app/

api/

database/

services/

workers/

pipeline/

ingestion/

processing/

schemas/

validation/

run_pipeline.py

data/

raw/

bronze/

silver/

gold/

logs/

docker-compose.yml

requirements.txt

```

  

##  O Que Foi Implementado Nesta Branch

  

###  1) Ingestion RAW

  

- Manifest versionado em `data/raw/{version}/manifest.json`.

- Descoberta de arquivos da Receita (auxiliares por padrao, grandes opcionais).

- Download com:

- streaming;

- retry exponencial;

- timeout configuravel;

- arquivo temporario `.part`;

- idempotencia (skip se arquivo ja existe com tamanho > 0).

- Validacao de ZIP:

- existencia;

- tamanho > 0;

- extensao `.zip`;

-  `ZipFile.testzip()`;

- quantidade de arquivos internos > 0.

  

###  2) Bronze

  

- Leitura de ZIPs e CSVs internos da Receita com Polars.

- Geracao de:

-  `data/bronze/{version}/empresas.parquet`

-  `data/bronze/{version}/estabelecimentos.parquet`

-  `data/bronze/{version}/socios.parquet`

-  `data/bronze/{version}/simples.parquet`

- Fallback para vazios em arquivos opcionais (socios/simples) com warning.

  

###  3) Silver

  

- Padronizacao e limpeza de campos principais.

- Geracao de:

-  `data/silver/{version}/empresas_clean.parquet`

-  `data/silver/{version}/estabelecimentos_clean.parquet`

-  `data/silver/{version}/socios_clean.parquet`

-  `data/silver/{version}/simples_clean.parquet`

-  `data/silver/{version}/municipios_clean.parquet`

  

###  4) Gold

  

- Join das tabelas Silver para `empresas_consulta.parquet`.

- Inclusao de `dataset_version`.

- Geracao de filtros auxiliares:

-  `filtros_ufs.parquet`

-  `filtros_municipios.parquet`

-  `filtros_cnaes.parquet`

-  `filtros_situacoes.parquet`

- Sincronizacao para compatibilidade em:

-  `data/gold/current/`

-  `data/gold/dev/`

  

###  5) Validacao e Publicacao

  

- Validacao de schema e linhas minimas em Bronze/Silver.

- Validacao da Gold com:

- schema;

- linhas minimas;

- campos criticos;

- query DuckDB (`COUNT(*)`).

- Atualizacao de `DatasetVersion` durante todo o fluxo:

-  `downloading` -> `downloaded` -> `processing` -> `validated` -> `published`

-  `failed` em caso de erro.

- Publicacao da versao ativa com arquivamento da versao anterior.

  

##  Modelo de Dados

  

Tabelas principais no PostgreSQL:

  

-  `dataset_versions`

-  `export_jobs`

  

As tabelas sao criadas/validadas automaticamente no startup da API e no runner do pipeline.

  

##  API (Estado Atual)

  

-  `GET /` retorna mensagem de status.

-  `GET /api/v1/health` valida PostgreSQL e Redis.

  

Observacao: nesta branch, o foco principal foi o pipeline de dados. Endpoints adicionais podem estar fora do escopo desta etapa.

  

##  Configuracao

  

Use um `.env` na raiz com pelo menos:

  

```env

DATABASE_URL=postgresql+psycopg://cnpj_user:cnpj_password@postgres:5432/cnpj_data_hub

REDIS_URL=redis://redis:6379/0

LOG_LEVEL=INFO

DOWNLOAD_TIMEOUT_SECONDS=120

DOWNLOAD_MAX_RETRIES=3

```

  

Os nomes exatos seguem o mapeamento em `app/config.py`.

  

##  Como Rodar

  

###  1) Subir infraestrutura

  

```bash

docker  compose  up  -d  --build

```

  

###  2) Rodar pipeline completo (com download)

  

```bash

docker  compose  exec  api  python  -m  pipeline.run_pipeline  --version  2024-12

```

  

###  3) Rodar pipeline sem download

  

```bash

docker  compose  exec  api  python  -m  pipeline.run_pipeline  --version  2024-12  --skip-download

```

  

###  4) Incluir arquivos grandes da Receita

  

```bash

docker  compose  exec  api  python  -m  pipeline.run_pipeline  --version  2024-12  --include-large-files

```

  

##  Como Validar Cada Camada

  

###  RAW

  

- Ver arquivos:

-  `data/raw/{version}`

- Ver manifest:

-  `data/raw/{version}/manifest.json`

  

###  Bronze

  

- Conferir existencia dos parquets em `data/bronze/{version}`.

  

###  Silver

  

- Conferir existencia dos parquets em `data/silver/{version}`.

  

###  Gold

  

- Conferir arquivo principal:

-  `data/gold/{version}/empresas_consulta.parquet`

- Conferir filtros auxiliares:

-  `data/gold/{version}/filtros_*.parquet`

  

Exemplo de contagem:

  

```bash

docker  compose  exec  api  python  -c  "import duckdb; print(duckdb.sql(\"SELECT COUNT(*) FROM read_parquet('data/gold/2024-12/empresas_consulta.parquet')\").fetchall())"

```

  

##  Logs

  

- API: `logs/api.log`

- Pipeline: `logs/pipeline.log`

  

Streaming de logs:

  

```bash

docker  compose  logs  -f  api

```

  

##  Troubleshooting

  

###  1) `--skip-download` falhou

  

Motivo comum: a versao informada nao tem arquivos RAW ja baixados para processar.

  

Solucao:

  

1. rode sem `--skip-download`; ou

2. execute `--skip-download` apenas para uma versao que ja possua arquivos em `data/raw/{version}`.

  

###  2) Download retornou 404

  

Motivo comum: versao inexistente na URL da Receita.

  

Solucao:

  

1. use uma versao real disponivel na Receita (exemplo de mes/ano valido);

2. mantenha `dev-real-download` apenas para testes estruturais e de erro controlado.

  

###  3) Pipeline falha em Bronze por arquivos vazios

  

Motivo comum: sem dados necessarios de empresas/estabelecimentos.

  

Solucao:

  

1. conferir manifest e status por arquivo;

2. validar presenca de `Empresas*.zip` e `Estabelecimentos*.zip` quando usar modo completo.

  

##  Limitações Conhecidas

  

1. Descoberta de arquivos da Receita ainda usa convencao de nomes (sufixo `0.zip`) e nao faz listagem dinamica completa do diretorio remoto.

2.  `codigo_ibge` em municipios esta mantido como `null` (TODO mapeamento oficial).

3. Endpoints alem de health/root nao sao foco desta etapa de branch.

4. O pipeline privilegia robustez incremental; otimizações de performance para volumes muito altos ainda podem ser evoluidas.

  

##  Proximos Passos Recomendados

  

1. Implementar descoberta dinamica real dos arquivos por versao (index remoto).

2. Adicionar checksum/hash por arquivo no manifest.

3. Melhorar normalizacao de codigos auxiliares (natureza juridica, cnaes, municipios/ibge).

4. Reintegrar/expandir endpoints de busca/export usando Gold publicado e current ativo.

  

##  Branch e Commit

  

- Branch: `feat/build-real-bronze-silver-gold-layers`

- Commit sugerido da etapa:

  

```text

feat: build real bronze silver and gold layers

```
