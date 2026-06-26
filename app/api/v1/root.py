from fastapi import APIRouter

from app.schemas.root import RootResponse
from app.services.status import get_root_status

router = APIRouter()


@router.get("/", response_model=RootResponse, summary="Application root")
async def root() -> RootResponse:
    return get_root_status()
