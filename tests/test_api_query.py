"""API-тесты без сети: TestClient."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_schema(client: TestClient) -> None:
    resp = client.get("/api/v1/schema")
    assert resp.status_code == 200
    assert set(resp.json()["tables"]) == {"users", "orders", "products"}


def test_translate(client: TestClient) -> None:
    resp = client.post("/api/v1/translate", json={"question": "show users older than 30"})
    assert resp.status_code == 200
    assert resp.json()["sql"] == "SELECT name, age FROM users WHERE age > 30 LIMIT 50"


def test_execute(client: TestClient) -> None:
    resp = client.post("/api/v1/execute", json={"sql": "SELECT name FROM users WHERE age > 30"})
    assert resp.status_code == 200
    assert resp.json()["row_count"] == 2


def test_execute_rejected(client: TestClient) -> None:
    resp = client.post("/api/v1/execute", json={"sql": "DELETE FROM users"})
    assert resp.status_code == 422


@pytest.mark.integration()
def test_translate_execute_roundtrip(client: TestClient) -> None:
    """Интеграционный по маркеру: translate → execute, без сети."""
    sql = client.post("/api/v1/translate", json={"question": "paid orders"}).json()["sql"]
    rows = client.post("/api/v1/execute", json={"sql": sql}).json()["rows"]
    assert len(rows) == 2
