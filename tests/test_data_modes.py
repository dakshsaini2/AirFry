import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, date

from backend.app import app, get_db
from backend.models import Base, Fare, Route, Source, DGCAMonthly
from backend.database import engine as _engine

from sqlalchemy.pool import StaticPool

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

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    db.add(Route(id="DEL-BOM", origin="DEL", dest="BOM", dgca_pax_share=1.0))
    db.add(Source(id=1, name="MockSource", type="ota", base_url="http://mock"))
    db.commit()
    db.close()
    
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def generate_fares(db, data_mode, days, source_ref="src_123", dataset_version="v1"):
    base_date = datetime.utcnow() - timedelta(days=days)
    for i in range(days):
        dt = base_date + timedelta(days=i)
        f = Fare(
            route_id="DEL-BOM", carrier="MockCarrier", flight_no="123", 
            dep_dt=dt, dep_bucket="morning", lead_days=1, fare_class="Economy", 
            base_fare=4000, taxes=500, udf=500, conv_fee=0,
            total_fare=5000 + i, source_id=1, is_soldout=False, is_outlier=False,
            data_mode=data_mode, source_reference=source_ref, scraped_at=dt
        )
        setattr(f, "dataset_version", dataset_version)
        db.add(f)
    db.commit()

def generate_dgca(db, data_mode, source_ref="dgca_ref", dataset_version="v1"):
    d = DGCAMonthly(month=datetime.utcnow().strftime("%Y-%m"), sector="all", avg_fare=5000.0, data_mode=data_mode, source_reference=source_ref)
    setattr(d, "dataset_version", dataset_version)
    db.add(d)
    db.commit()


def test_insufficient_data():
    db = TestingSessionLocal()
    generate_fares(db, data_mode="official", days=10)
    
    res = client.get("/api/v1/backtest")
    data = res.json()
    assert data["status"] == "insufficient_data"
    assert data["validation_eligible"] is False

def test_synthetic_35_days():
    db = TestingSessionLocal()
    generate_fares(db, data_mode="synthetic", days=35)
    generate_dgca(db, data_mode="synthetic")
    
    res = client.get("/api/v1/backtest")
    data = res.json()
    assert data["status"] == "ready_for_testing"
    assert data["data_mode"] == "synthetic"
    assert data["validation_eligible"] is False

def test_fixture_data():
    db = TestingSessionLocal()
    generate_fares(db, data_mode="fixture", days=35)
    generate_dgca(db, data_mode="fixture")
    
    res = client.get("/api/v1/backtest")
    data = res.json()
    assert data["status"] == "ready_for_testing"
    assert data["data_mode"] == "fixture"
    assert data["validation_eligible"] is False

def test_external_35_days():
    db = TestingSessionLocal()
    generate_fares(db, data_mode="external", days=35)
    generate_dgca(db, data_mode="external")
    
    res = client.get("/api/v1/backtest")
    data = res.json()
    assert data["status"] == "external_validation"
    assert data["data_mode"] == "external"
    assert data["validation_eligible"] is False # Review required for external

def test_official_validation():
    db = TestingSessionLocal()
    generate_fares(db, data_mode="official", days=35, source_ref="ref1")
    generate_dgca(db, data_mode="official", source_ref="ref2")
    
    res = client.get("/api/v1/backtest")
    data = res.json()
    assert data["status"] == "official_validation"
    assert data["data_mode"] == "official"
    assert data["validation_eligible"] is True

def test_missing_source_reference_reject():
    db = TestingSessionLocal()
    generate_fares(db, data_mode="official", days=35, source_ref=None)
    generate_dgca(db, data_mode="official", source_ref=None)
    
    res = client.get("/api/v1/backtest")
    data = res.json()
    # Assuming app.py enforces this rule, let's see
    assert data["validation_eligible"] is False
    assert data["status"] == "validation_failed"
