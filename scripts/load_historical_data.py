"""
Development / Synthetic Historical Dataset Generator

WARNING: This script generates FAKE, SYNTHETIC data for development and CI purposes.
It does NOT load real historical data. The generated data is explicitly marked with
data_mode="synthetic" and is NOT ELIGIBLE for official validation.
"""

import os
import sys
import pandas as pd
from datetime import datetime
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend.models import Base, Fare, Route, Source, Weight, DGCAMonthly
from scripts import synthetic_generator as P
import scipy.stats as stats

def load_data():
    db = SessionLocal()
    
    # 1. Routes & Sources
    print("Loading routes and sources (SYNTHETIC)...")
    if db.query(Route).count() == 0:
        for r, (share, base) in P.ROUTES.items():
            origin, dest = r.split("-")
            db.add(Route(id=r, origin=origin, dest=dest, dgca_pax_share=share))
        
        sources = ["IndiGo", "MakeMyTrip", "Yatra", "EaseMyTrip", "Cleartrip", "Ixigo", "Goibibo", "Air India", "SpiceJet", "Akasa Air", "Air India Express"]
        for s in sources:
            db.add(Source(name=s, type="ota" if s not in ["IndiGo", "Air India", "SpiceJet", "Akasa Air", "Air India Express"] else "airline", base_url=f"https://www.{s.lower()}.com/"))
        db.commit()

    # 2. Weights
    print("Loading weights (SYNTHETIC)...")
    db.query(Weight).filter(Weight.version == "2026-v1").delete()
    for route_id, (share, _) in P.ROUTES.items():
        w = Weight(
            version="2026-v1",
            data_mode="synthetic",
            source="synthetic_development_fixture",
            methodology="Mock Traffic Share",
            route_id=route_id,
            weight=share
        )
        db.add(w)
    db.commit()

    # 3. DGCA data
    print("Loading DGCA monthly references (SYNTHETIC)...")
    ref_path = os.path.join(os.path.dirname(__file__), "..", "data", "dgca_monthly.csv")
    if os.path.exists(ref_path):
        ref = pd.read_csv(ref_path)
        db.query(DGCAMonthly).delete()
        for _, row in ref.iterrows():
            db.add(DGCAMonthly(
                month=row['month'],
                sector="all", # Mocking sector as 'all' for national average
                avg_fare=row['avg_fare_inr'],
                source="synthetic_mock",
                data_mode="synthetic"
            ))
        db.commit()

    # 4. Generate 35 days of historical fares
    print("Generating 35 days of historical fares (SYNTHETIC)...")
    raw = P.generate(days=35, seed=42)
    df, _ = P.clean(raw)
    
    # Map to Fare records
    print("Mapping to database records...")
    db.query(Fare).delete()
    
    # Get source IDs
    source_map = {s.name: s.id for s in db.query(Source).all()}
    
    fares = []
    for _, row in df.iterrows():
        dt = datetime.combine(row['date'], datetime.min.time())
        f = Fare(
            route_id=row['route'],
            carrier=row['carrier'],
            flight_no="MOCK123",
            dep_dt=dt,
            dep_bucket="morning",
            lead_days=row['lead'],
            fare_class=row['fare_class'],
            base_fare=row['base'],
            taxes=row['taxes'],
            udf=row['udf'],
            conv_fee=row['convenience'],
            total_fare=row['total'],
            source_id=source_map.get(row['source']),
            is_soldout=False,
            is_outlier=False,
            data_mode="synthetic",
            scraped_at=dt
        )
        fares.append(f)
    
    print(f"Bulk inserting {len(fares)} synthetic fares...")
    db.bulk_save_objects(fares)
    db.commit()
    
    print("Synthetic historical data load complete.")

if __name__ == "__main__":
    load_data()
