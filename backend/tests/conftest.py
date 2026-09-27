from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Settings with a known environment, so assertions do not depend on the
    developer's own .env file."""
    return Settings(environment="test", app_name="WorkOS API Test")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """A TestClient driving the ASGI app in-process.

    No server, no socket, no port. The app's lifespan and every middleware run
    exactly as they would in production, which is why this catches real wiring
    bugs that a mocked test would miss.

    get_settings is overridden because it is lru_cached at module level - without
    this, tests would read the developer's real .env and be non-deterministic.
    create_app(settings=...) is needed too, because the app title is baked in at
    construction time, before dependency_overrides can apply.
    """
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
