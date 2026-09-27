from fastapi import APIRouter, Depends

from app import __version__
from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(settings: Settings = Depends(get_settings)) -> dict:
    """Liveness probe: the process is up and the app is correctly wired.

    Intentionally does no I/O. A health check that hits the database turns a
    slow database into a false "app is down", which is how orchestrators end up
    restarting healthy containers during someone else's incident.

    Readiness (can we actually serve requests?) is a separate endpoint added in
    iteration 02, once there is a database to check.
    """
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
    }
