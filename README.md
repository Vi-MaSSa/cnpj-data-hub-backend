# cnpj-data-hub-backend

Backend MVP para consulta e exportacao de dados de CNPJ com FastAPI, PostgreSQL, Redis, RQ, DuckDB e Parquet fake local.

## Stack
- FastAPI
- PostgreSQL
- Redis + RQ (worker)
- SQLAlchemy
- DuckDB
- Polars
- Loguru
- Docker Compose

## Como subir
```bash
docker compose up -d --build
```

## Como gerar dataset fake
```bash
docker compose exec api python -m pipeline.processing.build_fake_gold
```

## Como testar health
```bash
curl http://localhost:8000/api/v1/health
```

## Como testar busca
```bash
curl -X POST http://localhost:8000/api/v1/search \
	-H "Content-Type: application/json" \
	-d '{"uf":"SP","municipio":"MAUA","page":1,"page_size":10}'
```

## Como testar exportacao
```bash
curl -X POST http://localhost:8000/api/v1/export \
	-H "Content-Type: application/json" \
	-d '{"format":"csv","filters":{"uf":"SP"}}'
```

## Como ver logs
```bash
docker compose logs -f api
docker compose logs -f worker
```

## Como rodar testes
```bash
docker compose exec api pytest
```
