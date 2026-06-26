from fastapi import APIRouter

from app.api.v1.competitions import router as competitions_router
from app.api.v1.health import router as health_router
from app.api.v1.matches import router as matches_router
from app.api.v1.root import router as root_router
from app.api.v1.seasons import router as seasons_router
from app.api.v1.teams import router as teams_router

router = APIRouter(prefix="/api/v1")
router.include_router(root_router)
router.include_router(health_router)
router.include_router(competitions_router)
router.include_router(seasons_router)
router.include_router(teams_router)
router.include_router(matches_router)
