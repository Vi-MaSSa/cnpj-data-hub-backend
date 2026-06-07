from datetime import date

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
	uf: str | None = None
	municipio: str | None = None
	cnae_principal: str | None = None
	situacao_cadastral: str | None = None
	opcao_simples: bool | None = None
	opcao_mei: bool | None = None
	porte_empresa: str | None = None
	data_inicio_min: date | None = None
	data_inicio_max: date | None = None
	page: int = Field(default=1, ge=1)
	page_size: int = Field(default=10, ge=1, le=100)

	@field_validator("uf")
	@classmethod
	def validate_uf(cls, value: str | None) -> str | None:
		if value is None:
			return None
		normalized = value.strip().upper()
		if len(normalized) != 2:
			raise ValueError("uf must have exactly 2 characters")
		return normalized

	@field_validator("cnae_principal")
	@classmethod
	def validate_cnae(cls, value: str | None) -> str | None:
		if value is None:
			return None
		return value.strip()


class CompanyResult(BaseModel):
    cnpj_completo: str
    razao_social: str
    nome_fantasia: str | None = None
    uf: str
    municipio: str
    cnae_principal: str
    situacao_cadastral: str
    opcao_simples: bool
    opcao_mei: bool
    porte_empresa: str
    data_inicio_atividade: str


class SearchResponse(BaseModel):
    page: int
    page_size: int
    total: int
    data: list[CompanyResult]
