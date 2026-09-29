import pytest
from fastapi.testclient import TestClient
from backend.app import app, get_db
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.models import Base

# Setup isolated test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_overrides():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


def test_unauthenticated_scrape():
    response = client.post("/api/v1/scrape")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

def test_authorized_scrape(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    # For testing, we mock the lock acquisition and run_collection_cycle
    from backend import app as app_module
    
    def mock_run(db):
        pass
    
    monkeypatch.setattr(app_module, "run_collection_cycle", mock_run)
    monkeypatch.setattr(app_module, "ADMIN_API_KEY", "test-key")
    
    response = client.post("/api/v1/scrape", headers={"x-api-key": "test-key"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

def test_rate_limiting(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    from backend import app as app_module
    
    # Mock lock to be already acquired
    class MockLock:
        def acquire(self, blocking=False): return False
        def release(self): pass
    
    monkeypatch.setattr(app_module, "scrape_lock", MockLock())
    monkeypatch.setattr(app_module, "ADMIN_API_KEY", "test-key")
    
    response = client.post("/api/v1/scrape", headers={"x-api-key": "test-key"})
    assert response.status_code == 429
    assert response.json()["detail"] == "A collection cycle is already running."

def test_security_headers():
    response = client.get("/api/v1/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    
def test_methodology():
    response = client.get("/api/v1/methodology")
    assert response.status_code == 200
    assert response.json()["Data mode"] == "synthetic"

def test_backtest_endpoint():
    response = client.get("/api/v1/backtest")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] in ["ready_for_testing", "insufficient_data", "validation_failed", "external_validation", "official_validation"]

def test_db_security_sqlite_prod(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    
    with pytest.raises(Exception):
        import importlib
        import backend.database
        importlib.reload(backend.database)
