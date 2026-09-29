import pytest
import pandas as pd
from backend.ingestion.dgca import DGCADataSource
from backend.ingestion.airfare import AmadeusAPIAdapter
from backend.data.validators import HistoricalDataValidator

def test_source_metadata_validation():
    df = pd.DataFrame({
        "month": ["2026-09-01"],
        "sector": ["DEL-BOM"],
        "avg_fare": [5000],
        "source": ["DGCA"],
        "data_mode": ["official"],
        "source_reference": ["dgca_2026_09.csv"],
        "dataset_version": ["1.0"]
    })
    validator = HistoricalDataValidator()
    report = validator.validate_dgca_format(df)
    assert report["eligible"] is True
    assert report["dataset_version"] == "1.0"
    assert report["source_reference"] == "dgca_2026_09.csv"


def test_missing_credentials_amadeus(monkeypatch):
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    monkeypatch.delenv("AMADEUS_CLIENT_SECRET", raising=False)
    adapter = AmadeusAPIAdapter(2, "https://test.api.amadeus.com")
    with pytest.raises(ValueError, match="requires_credentials"):
        adapter.fetch_quotes("DEL", "BOM", "2026-10-01")

def test_official_requires_source_reference():
    df = pd.DataFrame({
        "month": ["2026-09-01"],
        "sector": ["DEL-BOM"],
        "avg_fare": [5000],
        "source": ["DGCA"],
        "data_mode": ["official"],
        "source_reference": [None],
        "dataset_version": ["1.0"]
    })
    validator = HistoricalDataValidator()
    report = validator.validate_dgca_format(df)
    assert report["eligible"] is False
    assert report["reason"] == "missing_source_reference"

def test_official_requires_dataset_version():
    df = pd.DataFrame({
        "month": ["2026-09-01"],
        "sector": ["DEL-BOM"],
        "avg_fare": [5000],
        "source": ["DGCA"],
        "data_mode": ["official"],
        "source_reference": ["dgca_2026_09.csv"],
        "dataset_version": [None]
    })
    validator = HistoricalDataValidator()
    report = validator.validate_dgca_format(df)
    assert report["eligible"] is False
    assert report["reason"] == "missing_dataset_version"

def test_invalid_records_rejected():
    df = pd.DataFrame({
        "month": ["2026-09-01"],
        "sector": ["DEL-BOM"],
        "avg_fare": [-100],  # Invalid fare
        "source": ["DGCA"],
        "data_mode": ["official"],
        "source_reference": ["dgca_2026_09.csv"],
        "dataset_version": ["1.0"]
    })
    validator = HistoricalDataValidator()
    report = validator.validate_dgca_format(df)
    assert report["eligible"] is False
    assert report["invalid_fares"] == 1
    assert "Dataset contains zero or negative fares" in report["reason"]

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from backend.app import app, get_db
from backend.models import Base, Fare, Route, Source, DGCAMonthly

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

def test_contamination_rejection():
    db = TestingSessionLocal()
    dt = datetime.utcnow()
    db.add(Fare(route_id="DEL-BOM", carrier="C", flight_no="1", dep_dt=dt, dep_bucket="morning", lead_days=1, fare_class="Economy", base_fare=4000, total_fare=5000, source_id=1, data_mode="synthetic", source_reference="ref", scraped_at=dt))
    db.add(Fare(route_id="DEL-BOM", carrier="C", flight_no="2", dep_dt=dt, dep_bucket="morning", lead_days=1, fare_class="Economy", base_fare=4000, total_fare=5000, source_id=1, data_mode="official", source_reference="ref", dataset_version="1", scraped_at=dt))
    db.commit()
    res = client.get("/api/v1/validation_report")
    assert res.json()["status"] == "contaminated_dataset"

def test_contamination_fixture_rejection():
    db = TestingSessionLocal()
    dt = datetime.utcnow()
    db.add(Fare(route_id="DEL-BOM", carrier="C", flight_no="1", dep_dt=dt, dep_bucket="morning", lead_days=1, fare_class="Economy", base_fare=4000, total_fare=5000, source_id=1, data_mode="fixture", source_reference="ref", scraped_at=dt))
    db.add(Fare(route_id="DEL-BOM", carrier="C", flight_no="2", dep_dt=dt, dep_bucket="morning", lead_days=1, fare_class="Economy", base_fare=4000, total_fare=5000, source_id=1, data_mode="official", source_reference="ref", dataset_version="1", scraped_at=dt))
    db.commit()
    res = client.get("/api/v1/validation_report")
    assert res.json()["status"] == "contaminated_dataset"

def test_contamination_official_allowed():
    db = TestingSessionLocal()
    dt = datetime.utcnow()
    db.add(Fare(route_id="DEL-BOM", carrier="C", flight_no="1", dep_dt=dt, dep_bucket="morning", lead_days=1, fare_class="Economy", base_fare=4000, total_fare=5000, source_id=1, data_mode="live", source_reference="ref", dataset_version="1", scraped_at=dt))
    db.add(Fare(route_id="DEL-BOM", carrier="C", flight_no="2", dep_dt=dt, dep_bucket="morning", lead_days=1, fare_class="Economy", base_fare=4000, total_fare=5000, source_id=1, data_mode="official", source_reference="ref", dataset_version="1", scraped_at=dt))
    db.commit()
    res = client.get("/api/v1/validation_report")
    assert res.json()["status"] != "contaminated_dataset"

