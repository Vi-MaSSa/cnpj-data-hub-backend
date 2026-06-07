from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.filters import CNAEResponse, MunicipioResponse, SituacaoResponse, UFResponse
from app.services.filter_service import (
	get_cnaes,
	get_municipios_by_uf,
	get_situacoes,
	get_ufs,
)

router = APIRouter()


@router.get("/filters/ufs", response_model=UFResponse)
def get_ufs_endpoint() -> UFResponse:
	try:
		return UFResponse(ufs=get_ufs())
	except FileNotFoundError as exc:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/filters/municipios", response_model=MunicipioResponse)
def get_municipios_endpoint(uf: str = Query(..., min_length=2, max_length=2)) -> MunicipioResponse:
	uf_normalized = uf.upper()
	try:
		return MunicipioResponse(
			uf=uf_normalized,
			municipios=get_municipios_by_uf(uf_normalized),
		)
	except FileNotFoundError as exc:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/filters/cnaes", response_model=CNAEResponse)
def get_cnaes_endpoint() -> CNAEResponse:
	try:
		return CNAEResponse(cnaes=get_cnaes())
	except FileNotFoundError as exc:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/filters/situacoes", response_model=SituacaoResponse)
def get_situacoes_endpoint() -> SituacaoResponse:
	try:
		return SituacaoResponse(situacoes=get_situacoes())
	except FileNotFoundError as exc:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
