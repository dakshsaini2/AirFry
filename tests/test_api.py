from fastapi.testclient import TestClient

def test_api():
    from backend.app import app, get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from backend.models import Base

    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        Base.metadata.create_all(bind=engine)
        c = TestClient(app)
        
        assert c.get("/api/health").json()["status"] == "ok"
        # Endpoints should return 200 OK and valid JSON structures even if empty
        index_res = c.get("/api/v1/index?freq=D").json()
        assert "values" in index_res
        backtest_res = c.get("/api/v1/backtest").json()
        assert "status" in backtest_res
    finally:
        app.dependency_overrides.clear()

def test_mospi_endpoint():
    from backend.app import app
    r = TestClient(app).get("/api/mospi").json(); assert len(r["months"]) >= 1 and "source" in r
