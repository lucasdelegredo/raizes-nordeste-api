from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.session import get_db
from app.main import app


def _override_db_sqlite():
    """Usa SQLite em memória para testar o /health sem depender do Postgres."""
    engine = create_engine("sqlite://")
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()


def test_health_ok():
    app.dependency_overrides[get_db] = _override_db_sqlite
    try:
        r = TestClient(app).get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["database"] == "ok"
    finally:
        app.dependency_overrides.clear()


def test_docs_disponivel():
    r = TestClient(app).get("/openapi.json")
    assert r.status_code == 200
    assert "/health" in r.json()["paths"]
