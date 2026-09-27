from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_reports_configured_app(client: TestClient) -> None:
    """Proves the dependency chain works end to end: the route received the
    Settings object that the fixture injected, not a hard-coded string."""
    body = client.get("/api/v1/health").json()

    assert body["app"] == "WorkOS API Test"
    assert body["environment"] == "test"
    assert "version" in body


def test_unknown_path_returns_404(client: TestClient) -> None:
    """A missing route must be a 404, never a 200. A permissive fallback route
    is a classic way to accidentally expose something."""
    assert client.get("/api/v1/does-not-exist").status_code == 404


def test_openapi_schema_is_generated(client: TestClient) -> None:
    """The schema is what generates /docs and what a frontend could generate
    types from, so it must exist from day one."""
    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "WorkOS API Test"
    assert "/api/v1/health" in schema["paths"]
