from fastapi import FastAPI

from app import __version__
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings

API_V1_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and wire the application.

    A factory instead of a module-level `app = FastAPI()` so that tests (and any
    future second app) can construct an app with different settings. Importing
    this module should not have the side effect of freezing configuration.

    `settings` is a parameter, not an internal call, because app construction and
    request handling read configuration at two different times. Only the second
    one can be swapped via dependency_overrides - anything create_app() needs
    during construction has to arrive as an argument.
    """
    if settings is None:
        settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        # These three only change how /docs renders. Nothing is "hidden" by them -
        # /docs already reflects exactly the routes the server exposes. The real
        # reason to keep them is honest docs, not secrecy.
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    application.include_router(api_router, prefix=API_V1_PREFIX)

    return application


app = create_app()
