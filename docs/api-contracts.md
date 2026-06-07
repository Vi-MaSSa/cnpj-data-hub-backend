# API Contracts

## GET /api/v1/health

- Método: GET
- URL: /api/v1/health
- Payload: sem body
- Sucesso (200):

```json
{
  "status": "ok",
  "service": "CNPJ Data Hub API",
  "environment": "development",
  "version": "0.1.0",
  "dependencies": {
    "postgres": "ok",
    "redis": "ok"
  }
}
```

- Status comuns: 200, 503

## GET /api/v1/datasets/current

- Método: GET
- URL: /api/v1/datasets/current
- Payload: sem body
- Sucesso (200):

```json
{
  "active": false,
  "message": "No active dataset version found"
}
```

- Status comuns: 200

## GET /api/v1/filters/ufs

- Método: GET
- URL: /api/v1/filters/ufs
- Payload: sem body
- Sucesso (200):

```json
{
  "ufs": ["MG", "RJ", "SP"]
}
```

- Status comuns: 200, 503

## GET /api/v1/filters/municipios?uf=SP

- Método: GET
- URL: /api/v1/filters/municipios?uf=SP
- Payload: query string `uf`
- Sucesso (200):

```json
{
  "uf": "SP",
  "municipios": ["MAUA", "SAO PAULO"]
}
```

- Status comuns: 200, 422, 503

## GET /api/v1/filters/cnaes

- Método: GET
- URL: /api/v1/filters/cnaes
- Payload: sem body
- Sucesso (200):

```json
{
  "cnaes": ["6201501", "7112000"]
}
```

- Status comuns: 200, 503

## GET /api/v1/filters/situacoes

- Método: GET
- URL: /api/v1/filters/situacoes
- Payload: sem body
- Sucesso (200):

```json
{
  "situacoes": ["ATIVA", "BAIXADA", "SUSPENSA"]
}
```

- Status comuns: 200, 503

## POST /api/v1/search

- Método: POST
- URL: /api/v1/search
- Payload:

```json
{
  "uf": "SP",
  "municipio": "MAUA",
  "page": 1,
  "page_size": 10
}
```

- Sucesso (200):

```json
{
  "page": 1,
  "page_size": 10,
  "total": 1,
  "data": [
    {
      "cnpj_completo": "11111111000101",
      "razao_social": "ALFA COMERCIO LTDA",
      "nome_fantasia": "ALFA",
      "uf": "SP",
      "municipio": "MAUA",
      "cnae_principal": "6201501",
      "situacao_cadastral": "ATIVA",
      "opcao_simples": true,
      "opcao_mei": false
    }
  ]
}
```

- Status comuns: 200, 422

## POST /api/v1/export

- Método: POST
- URL: /api/v1/export
- Payload:

```json
{
  "format": "csv",
  "filters": {
    "uf": "SP"
  }
}
```

- Sucesso (200):

```json
{
  "job_id": "<uuid>",
  "status": "queued"
}
```

- Status comuns: 200, 400, 422

## GET /api/v1/jobs/{job_id}

- Método: GET
- URL: /api/v1/jobs/{job_id}
- Payload: sem body
- Sucesso (200):

```json
{
  "job_id": "<uuid>",
  "status": "ready",
  "format": "csv",
  "filters": {
    "uf": "SP"
  },
  "file_path": "exports/ready/<uuid>.csv",
  "row_count": 1,
  "error_message": null,
  "created_at": "2026-06-01T10:00:00Z",
  "started_at": "2026-06-01T10:00:05Z",
  "finished_at": "2026-06-01T10:00:08Z",
  "expires_at": "2026-06-02T10:00:00Z"
}
```

- Status comuns: 200, 404

## GET /api/v1/export/{job_id}/download

- Método: GET
- URL: /api/v1/export/{job_id}/download
- Payload: sem body
- Sucesso (200): arquivo CSV
- Status comuns: 200, 400, 404
