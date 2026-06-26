from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Application root")
async def root() -> dict[str, str]:
    return {"app": "Barghouth Footy Analytics", "status": "running"}
