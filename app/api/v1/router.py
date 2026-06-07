from fastapi import APIRouter

from app.api.v1.endpoints import datasets, export, filters, health, jobs, search

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    datasets.router,
    tags=["Datasets"],
)

api_router.include_router(
    jobs.router,
    tags=["Jobs"],
)

api_router.include_router(
    export.router,
    tags=["Export"],
)

api_router.include_router(
    search.router,
    tags=["Search"],
)

api_router.include_router(
    filters.router,
    tags=["Filters"],
)