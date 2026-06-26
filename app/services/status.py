from app.schemas.health import HealthResponse
from app.schemas.root import RootResponse


def get_health_status() -> HealthResponse:
    return HealthResponse(status="ok")


def get_root_status() -> RootResponse:
    return RootResponse(app="Barghouth Footy Analytics", status="running")
