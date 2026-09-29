import pytest
import pandas as pd
from backend.data.validators import HistoricalDataValidator

def test_dgca_validator_valid_dataset():
    df = pd.DataFrame([
        {"month": "2026-01", "sector": "all", "avg_fare": 5000, "source": "DGCA", "data_mode": "official", "source_reference": "file.csv", "dataset_version": "v1"}
    ])
    val = HistoricalDataValidator()
    report = val.validate_dgca_format(df)
    assert report["eligible"] is True
    assert report["valid_rows"] == 1
    assert report["missing_values"] == 0

def test_dgca_validator_missing_provenance():
    df = pd.DataFrame([
        {"month": "2026-01", "sector": "all", "avg_fare": 5000, "source": "DGCA", "data_mode": "official", "source_reference": None, "dataset_version": "v1"}
    ])
    val = HistoricalDataValidator()
    report = val.validate_dgca_format(df)
    assert report["eligible"] is False
    assert report["reason"] == "missing_source_reference"
    
def test_dgca_validator_invalid_fare():
    df = pd.DataFrame([
        {"month": "2026-01", "sector": "all", "avg_fare": -100, "source": "DGCA", "data_mode": "official", "source_reference": "file.csv", "dataset_version": "v1"}
    ])
    val = HistoricalDataValidator()
    report = val.validate_dgca_format(df)
    assert report["eligible"] is False
    assert report["invalid_fares"] == 1
    
def test_dgca_validator_duplicate():
    df = pd.DataFrame([
        {"month": "2026-01", "sector": "all", "avg_fare": 5000, "source": "DGCA", "data_mode": "official", "source_reference": "file.csv", "dataset_version": "v1"},
        {"month": "2026-01", "sector": "all", "avg_fare": 5100, "source": "DGCA", "data_mode": "official", "source_reference": "file.csv", "dataset_version": "v1"}
    ])
    val = HistoricalDataValidator()
    report = val.validate_dgca_format(df)
    assert report["eligible"] is False
    assert report["duplicate_rows"] == 1

def test_dgca_validator_missing_version():
    df = pd.DataFrame([
        {"month": "2026-01", "sector": "all", "avg_fare": 5000, "source": "DGCA", "data_mode": "official", "source_reference": "file.csv", "dataset_version": None}
    ])
    val = HistoricalDataValidator()
    report = val.validate_dgca_format(df)
    assert report["eligible"] is False
    assert report["reason"] == "missing_dataset_version"
