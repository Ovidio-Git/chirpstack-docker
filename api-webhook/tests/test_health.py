from fastapi.testclient import TestClient

from app.main import create_app
from app.routes import get_repository


class AvailableRepository:
    def ping(self) -> bool:
        return True


def test_health_returns_ok_when_database_is_available() -> None:
    application = create_app()
    application.dependency_overrides[get_repository] = AvailableRepository

    response = TestClient(application).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
