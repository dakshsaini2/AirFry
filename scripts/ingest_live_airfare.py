
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import Fare
from backend.scrapers.adapters import IndiGoAdapter

def ingest_live_airfare(origin: str, dest: str, departure_date: str, dry_run: bool):
    print(f"Starting web-scraping ingestion for {origin} -> {dest} on {departure_date}")
    
    dep_dt = datetime.strptime(departure_date, "%Y-%m-%d")
    lead_days = (dep_dt.date() - datetime.now(timezone.utc).date()).days
    
    # Initialize Scraper
    try:
        scraper = IndiGoAdapter(source_id=2, base_url="https://www.goindigo.in")
        normalized = scraper.execute(origin, dest, dep_dt, lead_days)
    except Exception as e:
        print(f"Scraper Error: {e}")
        sys.exit(1)
        
    print(f"Scraped and normalized {len(normalized)} APIx fare observations.")
    
    if not normalized:
        print("No valid fares scraped.")
        sys.exit(0)
        
    if dry_run:
        print("DRY RUN MODE. Normalized records:")
        for r in normalized[:5]:
            print(r)
        print("... (not inserted)")
        sys.exit(0)
        
    print("Inserting into database...")
    db = SessionLocal()
    try:
        records = []
        for row in normalized:
            f = Fare(
                route_id=f"{row['origin']}-{row['destination']}",
                carrier=row['carrier'],
                flight_no=row['flight_number'],
                dep_dt=row.get('departure_datetime'),
                dep_bucket=row['departure_bucket'],
                lead_days=row['lead_days'],
                fare_class=row['fare_class'],
                base_fare=row['base_fare'],
                taxes=row['taxes'],
                udf=row['udf'],
                conv_fee=row['convenience_fee'],
                total_fare=row['total_fare'],
                source_id=2,
                is_soldout=row['is_soldout'],
                is_outlier=row['is_outlier'],
                data_mode="live",
                source_reference=f"scraping_{row['carrier']}_{row['flight_number']}",
                scraped_at=datetime.now(timezone.utc)
            )
            setattr(f, "dataset_version", f"SCRAPER-LIVE-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
            records.append(f)
            
        db.bulk_save_objects(records)
        db.commit()
        print(f"Successfully ingested {len(records)} fares.")
    except Exception as e:
        db.rollback()
        print(f"Database error during ingestion: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest live airfare via web scraping.")
    parser.add_argument("--origin", type=str, required=True, help="Origin IATA code")
    parser.add_argument("--destination", type=str, required=True, help="Destination IATA code")
    parser.add_argument("--departure-date", type=str, required=True, help="Departure date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Scrape and normalize, but do not insert")
    
    args = parser.parse_args()
    
    ingest_live_airfare(args.origin, args.destination, args.departure_date, args.dry_run)
