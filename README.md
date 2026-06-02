# cnpj-data-hub
Plataforma web para consulta, filtragem e exportação de dados públicos de empresas brasileiras usando React, FastAPI, Polars, DuckDB, Parquet, PostgreSQL, Redis e Docker.


# Objetivo do projeto

O objetivo é criar um sistema web onde o usuário consiga:

```
buscar empresas por filtros simplesvisualizar resultados em tabelabaixar arquivos CSV/XLSXconsultar dados processados localmenteusar uma interface low-codenão depender de scraping frágilnão consultar a Receita em tempo real
```

O sistema deve baixar arquivos públicos da Receita Federal como arquivos remotos, processar esses dados e disponibilizar uma base otimizada para consulta.

----------

# Proposta de valor

## Para usuários/clientes

```
Permitir consultar e exportar dados públicos de empresas brasileiras sem precisar baixar arquivos grandes, rodar scripts ou montar pipeline manualmente.
```
