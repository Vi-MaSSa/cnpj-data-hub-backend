from pathlib import Path

import polars as pl


def build_fake_gold() -> None:
    output_dir = Path("data/gold/dev")
    output_dir.mkdir(parents=True, exist_ok=True)

    empresas = pl.DataFrame(
        {
            "cnpj_completo": [
                "11111111000101",
                "11111111000102",
                "11111111000103",
                "11111111000104",
                "11111111000105",
                "11111111000106",
                "11111111000107",
                "11111111000108",
                "11111111000109",
                "11111111000110",
            ],
            "razao_social": [
                "ALFA COMERCIO LTDA",
                "BETA SERVICOS LTDA",
                "GAMA INDUSTRIA SA",
                "DELTA TECNOLOGIA LTDA",
                "EPSILON LOGISTICA LTDA",
                "ZETA ALIMENTOS LTDA",
                "ETA ENGENHARIA LTDA",
                "THETA SAUDE LTDA",
                "IOTA CONSULTORIA LTDA",
                "KAPPA DISTRIBUICAO LTDA",
            ],
            "nome_fantasia": [
                "ALFA",
                "BETA",
                "GAMA",
                "DELTA",
                "EPSILON",
                "ZETA",
                "ETA",
                "THETA",
                "IOTA",
                "KAPPA",
            ],
            "uf": ["SP", "SP", "RJ", "MG", "SP", "BA", "PR", "RS", "SP", "SC"],
            "municipio": [
                "MAUA",
                "SAO PAULO",
                "RIO DE JANEIRO",
                "BELO HORIZONTE",
                "CAMPINAS",
                "SALVADOR",
                "CURITIBA",
                "PORTO ALEGRE",
                "SANTOS",
                "FLORIANOPOLIS",
            ],
            "cnae_principal": [
                "6201501",
                "6201501",
                "4711301",
                "7112000",
                "4930202",
                "1091101",
                "4120400",
                "8610101",
                "7020400",
                "4639701",
            ],
            "situacao_cadastral": [
                "ATIVA",
                "ATIVA",
                "ATIVA",
                "ATIVA",
                "ATIVA",
                "BAIXADA",
                "ATIVA",
                "ATIVA",
                "SUSPENSA",
                "ATIVA",
            ],
            "opcao_simples": [True, True, False, False, True, False, False, False, True, False],
            "opcao_mei": [False, False, False, False, False, False, False, False, False, False],
            "porte_empresa": [
                "ME",
                "EPP",
                "DEMAIS",
                "DEMAIS",
                "EPP",
                "ME",
                "DEMAIS",
                "DEMAIS",
                "ME",
                "EPP",
            ],
            "data_inicio_atividade": [
                "2019-01-10",
                "2018-03-20",
                "2015-05-02",
                "2012-09-15",
                "2020-02-01",
                "2011-07-11",
                "2010-04-30",
                "2016-06-18",
                "2021-10-05",
                "2017-08-22",
            ],
        }
    )

    empresas.write_parquet(output_dir / "empresas_consulta.parquet")

    empresas.select("uf").unique().sort("uf").write_parquet(output_dir / "filtros_ufs.parquet")
    empresas.select("uf", "municipio").unique().sort(["uf", "municipio"]).write_parquet(
        output_dir / "filtros_municipios.parquet"
    )
    empresas.select("cnae_principal").unique().sort("cnae_principal").write_parquet(
        output_dir / "filtros_cnaes.parquet"
    )
    empresas.select("situacao_cadastral").unique().sort("situacao_cadastral").write_parquet(
        output_dir / "filtros_situacoes.parquet"
    )


if __name__ == "__main__":
    build_fake_gold()