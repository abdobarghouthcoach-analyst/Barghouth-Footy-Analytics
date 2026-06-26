from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.status import get_health_status

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    return get_health_status()
