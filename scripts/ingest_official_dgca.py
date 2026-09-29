import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import DGCAMonthly
from backend.ingestion.dgca import DGCADataSource
from backend.data.validators import HistoricalDataValidator

def ingest_dgca(file_path: str, dataset_version: str):
    print(f"Reading DGCA official data from {file_path} (Version: {dataset_version})")
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
        
    ds = DGCADataSource(file_path, dataset_version)
    df = ds.fetch()
    
    # Enforce data_mode = official and inject provenance BEFORE validation
    df["data_mode"] = "official"
    df["dataset_version"] = dataset_version
    df["source_reference"] = os.path.basename(file_path)
    if "source" not in df.columns:
        df["source"] = "DGCA"
        
    validator = HistoricalDataValidator()
    report = validator.validate_dgca_format(df)
    
    print("================ DGCA QUALITY REPORT ================")
    for k, v in report.items():
        print(f"{k.replace('_', ' ').capitalize()}: {v}")
    print("=====================================================")
    
    if not report["eligible"]:
        print("\nERROR: Dataset rejected due to validation failures. Data will not be ingested.")
        sys.exit(1)
        
    db = SessionLocal()
    try:
        # Clear existing official records (or append based on strategy)
        # For this prototype we replace the official records
        deleted = db.query(DGCAMonthly).filter(DGCAMonthly.data_mode == "official").delete()
        print(f"Cleared {deleted} existing official records.")
        
        records = []
        for _, row in df.iterrows():
            records.append(DGCAMonthly(
                month=row['month'],
                sector=row['sector'],
                avg_fare=row['avg_fare'],
                source=row['source'],
                data_mode=row['data_mode'],
                dataset_version=row['dataset_version'],
                source_reference=row['source_reference']
            ))
            
        db.bulk_save_objects(records)
        db.commit()
        print(f"Successfully ingested {len(records)} official DGCA records.")
    except Exception as e:
        db.rollback()
        print(f"Database error during ingestion: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest authoritative DGCA CSV data.")
    parser.add_argument("--file", type=str, required=True, help="Path to the DGCA CSV file")
    parser.add_argument("--version", type=str, required=True, help="Dataset version tag (e.g. 2026.1)")
    args = parser.parse_args()
    
    ingest_dgca(args.file, args.version)
