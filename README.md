# CNPJ Data Hub — Backend

Plataforma backend para consulta, filtragem, processamento e exportação de dados públicos de empresas brasileiras, utilizando **FastAPI**, **PostgreSQL**, **Redis**, **DuckDB**, **Polars**, **Parquet** e **Docker**.

O projeto tem como objetivo transformar os arquivos públicos da Receita Federal em uma base otimizada para busca, análise e exportação, permitindo que usuários consultem informações empresariais sem precisar baixar arquivos grandes, montar pipelines manuais ou depender de scraping frágil.

----------

## Objetivo do Projeto

O **CNPJ Data Hub** é uma plataforma para centralizar, processar e disponibilizar dados públicos de empresas brasileiras de forma estruturada, performática e acessível por API.

O sistema foi pensado para permitir que o usuário consiga:

-   Buscar empresas por filtros como CNAE, UF, município e situação cadastral;
    
-   Visualizar resultados de forma paginada;
    
-   Exportar dados em arquivos CSV e, futuramente, XLSX/Parquet;
    
-   Consultar dados processados localmente;
    
-   Utilizar uma base otimizada para análise;
    
-   Evitar consultas em tempo real à Receita Federal;
    
-   Evitar scraping instável;
    
-   Automatizar o processamento dos arquivos públicos oficiais.
    

----------

## Proposta de Valor

A Receita Federal disponibiliza bases públicas de CNPJ em arquivos grandes e pouco amigáveis para usuários finais, analistas e empresas.

Este projeto resolve esse problema criando uma camada intermediária entre os arquivos públicos e o usuário final.

### Para usuários e clientes

Permite consultar e exportar dados públicos de empresas brasileiras sem precisar:

-   Baixar manualmente grandes arquivos da Receita Federal;
    
-   Abrir arquivos CSV pesados;
    
-   Montar scripts próprios de tratamento;
    
-   Criar pipelines de dados do zero;
    
-   Entender a estrutura original dos arquivos públicos;
    
-   Consultar a Receita em tempo real.
    

### Para empresas e analistas

O projeto pode apoiar casos de uso como:

-   Prospecção B2B;
    
-   Análise de mercado;
    
-   Segmentação por CNAE;
    
-   Estudos regionais por UF e município;
    
-   Geração de bases para times comerciais;
    
-   Enriquecimento de dados internos;
    
-   Criação de dashboards e relatórios.
    

----------

## Visão Geral da Arquitetura

O backend segue uma arquitetura modular, separando responsabilidades entre API, serviços, banco de dados, workers e pipeline de dados.

Fluxo geral previsto:

```text
Arquivos públicos da Receita Federal
        ↓
Camada RAW
        ↓
Processamento com Polars/DuckDB
        ↓
Camadas Bronze/Silver/Gold
        ↓
Arquivos Parquet otimizados
        ↓
API FastAPI
        ↓
Frontend / BI / Exportações

```

----------

## Tecnologias Utilizadas

Tecnologia

Uso no projeto

FastAPI

Construção da API backend

PostgreSQL

Persistência de metadados, jobs e versões de datasets

Redis

Fila/cache para tarefas assíncronas

Workers

Execução de tarefas em segundo plano

DuckDB

Consulta analítica em arquivos locais/Parquet

Polars

Processamento eficiente de dados tabulares

Parquet

Armazenamento otimizado das camadas processadas

Docker

Padronização do ambiente de desenvolvimento

Pytest

Testes automatizados

Loguru

Logs estruturados da aplicação e pipeline

----------

## Funcionalidades Planejadas

### API

-   Health check da aplicação;
    
-   Busca de empresas por filtros;
    
-   Paginação de resultados;
    
-   Exportação de dados;
    
-   Consulta de status de jobs;
    
-   Consulta de versões de datasets;
    
-   Endpoints para filtros disponíveis.
    

### Pipeline de Dados

-   Download dos arquivos públicos da Receita Federal;
    
-   Geração de manifest de arquivos;
    
-   Validação de arquivos `.zip`;
    
-   Organização da camada RAW;
    
-   Processamento para camadas Bronze, Silver e Gold;
    
-   Geração de arquivos Parquet otimizados;
    
-   Controle de versões de datasets.
    

### Workers

-   Processamento de exportações pesadas;
    
-   Execução de jobs assíncronos;
    
-   Atualização de status de tarefas;
    
-   Possível execução de etapas do pipeline no futuro.
    

----------

## Estrutura Inicial do Projeto

```text
cnpj-data-hub-backend/
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   │
│   ├── database/
│   │   ├── models.py
│   │   ├── postgres.py
│   │   ├── duckdb.py
│   │   └── repositories/
│   │
│   ├── schemas/
│   ├── services/
│   ├── workers/
│   └── utils/
│
├── pipeline/
│   ├── run_pipeline.py
│   ├── ingestion/
│   ├── processing/
│   ├── schemas/
│   └── validation/
│
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── exports/
│   ├── pending/
│   ├── processing/
│   ├── ready/
│   └── expired/
│
├── logs/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md

```

----------

## Como Executar o Projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/Vi-MaSSa/cnpj-data-hub-backend.git
cd cnpj-data-hub-backend

```

### 2. Criar o arquivo `.env`

Crie um arquivo `.env` com base no `.env.example`:

```bash
cp .env.example .env

```

No Windows PowerShell:

```powershell
copy .env.example .env

```

### 3. Subir os containers

```bash
docker compose up -d --build

```

### 4. Acessar a documentação da API

Após subir a aplicação, acesse:

```text
http://localhost:8000/docs

```

----------

## Comandos Úteis

### Ver logs da API

```bash
docker compose logs -f api

```

### Rodar testes

```bash
docker compose exec api pytest

```

### Rodar o pipeline manualmente

```bash
docker compose exec api python -m pipeline.run_pipeline

```

### Ver containers ativos

```bash
docker compose ps

```

----------

## Status Atual do Projeto

O projeto está em desenvolvimento ativo.

### Já implementado ou em implementação

-   Estrutura inicial da API FastAPI;
    
-   Configuração com Docker;
    
-   Integração com PostgreSQL;
    
-   Integração com Redis;
    
-   Estrutura de workers;
    
-   Health check;
    
-   Models básicos para datasets e jobs;
    
-   Busca inicial em base fake/processada;
    
-   Exportação CSV;
    
-   Testes automatizados iniciais;
    
-   Estrutura inicial do pipeline de dados;
    
-   Manifest RAW;
    
-   Download e validação inicial dos arquivos da Receita Federal.
    

### Próximas etapas

-   Processamento Bronze;
    
-   Processamento Silver;
    
-   Processamento Gold;
    
-   Enriquecimento com municípios e códigos IBGE;
    
-   Otimização das consultas em Parquet;
    
-   Integração completa com frontend;
    
-   Exportação XLSX;
    
-   Controle avançado de versões de dataset;
    
-   Chat com IA para comandos em linguagem natural.
    

----------

## Roadmap Técnico

### Fase 1 — Base da API

-   Estrutura FastAPI;
    
-   Health check;
    
-   Docker;
    
-   PostgreSQL;
    
-   Redis;
    
-   Testes iniciais.
    

### Fase 2 — Busca e Exportação

-   Busca paginada;
    
-   Filtros;
    
-   Exportação CSV;
    
-   Jobs assíncronos;
    
-   Workers.
    

### Fase 3 — Pipeline RAW

-   Descoberta de arquivos da Receita Federal;
    
-   Download versionado;
    
-   Manifest;
    
-   Validação de ZIPs;
    
-   Registro de DatasetVersion.
    

### Fase 4 — Processamento Analítico

-   Bronze;
    
-   Silver;
    
-   Gold;
    
-   Parquet otimizado;
    
-   DuckDB para consultas analíticas.
    

### Fase 5 — Produto e Inteligência

-   Frontend React;
    
-   Dashboard;
    
-   Exportações avançadas;
    
-   Chat com IA para consultas em linguagem natural.
    

----------

## Exemplo de Uso Futuro

Consulta simples por API:

```http
GET /api/v1/search?uf=SP&cnae=6201501

```

Exemplo de resposta esperada:

```json
{
  "page": 1,
  "limit": 50,
  "total": 1200,
  "results": [
    {
      "cnpj_completo": "00000000000100",
      "razao_social": "EMPRESA EXEMPLO LTDA",
      "cnae_principal": "6201501",
      "uf": "SP",
      "municipio": "SAO PAULO",
      "situacao_cadastral": "ATIVA"
    }
  ]
}

```

----------

## Observações

Este projeto utiliza dados públicos disponibilizados pela Receita Federal do Brasil.

A aplicação não realiza scraping em tempo real e não consulta diretamente os sistemas da Receita Federal durante as buscas dos usuários. O objetivo é baixar, processar e disponibilizar os dados públicos em uma estrutura otimizada para consulta e exportação.

----------

## Autor

Desenvolvido por **Vinícius Massagardi**.

GitHub: [@Vi-MaSSa](https://github.com/Vi-MaSSa)
