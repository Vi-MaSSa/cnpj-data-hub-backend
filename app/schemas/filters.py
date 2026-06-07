from pydantic import BaseModel


class UFResponse(BaseModel):
    ufs: list[str]


class MunicipioResponse(BaseModel):
    uf: str
    municipios: list[str]


class CNAEResponse(BaseModel):
    cnaes: list[str]


class SituacaoResponse(BaseModel):
    situacoes: list[str]