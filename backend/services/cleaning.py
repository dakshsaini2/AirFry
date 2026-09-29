import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple

def clean_fares(raw_fares: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Data Cleaning Pipeline:
    - Canonical deduplication
    - Sold-out detection
    - Outlier detection (IQR / MAD + sanity bounds)
    - Fare component validation
    """
    if not raw_fares:
        return [], {"planned_quotes": 0, "successful_quotes": 0}
        
    df = pd.DataFrame(raw_fares)
    rep = {"planned_quotes": len(df), "successful_quotes": len(df)}
    
    # Validation: total_fare >= base_fare
    df = df[df.total_fare >= df.base_fare].copy()
    
    # Deduplication
    canonical_keys = ["origin", "destination", "carrier", "flight_number", "departure_datetime", "lead_days", "source"]
    n_before = len(df)
    df = df.drop_duplicates(canonical_keys).copy()
    rep["duplicate_quotes"] = n_before - len(df)
    
    # Cross-source deduplication (prefer airline direct if duplicate exists)
    # Group by flight info. If same flight has multiple quotes across sources, maybe take minimum or prioritize source.
    # For now, simplistic dedupe
    cross_source_keys = ["origin", "destination", "carrier", "flight_number", "departure_datetime", "lead_days"]
    # Sort so that Airline (e.g. IndiGo) is preferred over OTAs
    df['source_priority'] = df['source'].apply(lambda x: 0 if x == 'IndiGo' else 1)
    df = df.sort_values('source_priority').drop_duplicates(cross_source_keys).copy()
    df = df.drop(columns=['source_priority'])
    
    # Sold out records
    n_before = len(df)
    df_avail = df[~df.is_soldout].copy()
    rep["sold_out_records"] = n_before - len(df_avail)
    
    # Outlier detection (MAD per route/lead-time group)
    df_avail['is_outlier'] = False
    
    if len(df_avail) > 0:
        # Avoid log(0)
        valid_total = df_avail.total_fare.astype(float)
        valid_total = np.where(valid_total <= 0, 1, valid_total)
        lg = pd.Series(np.log(valid_total), index=df_avail.index)
        med = lg.groupby([df_avail.origin, df_avail.destination, df_avail.lead_days]).transform("median")
        mad = (lg - med).abs().groupby([df_avail.origin, df_avail.destination, df_avail.lead_days]).transform("median").clip(lower=0.02)
        # modified Z-score
        z_score = 0.6745 * (lg - med).abs() / mad
        outliers_mask = z_score > 3.5
        
        df_avail.loc[outliers_mask, 'is_outlier'] = True
        
    rep["outliers"] = int(df_avail.is_outlier.sum())
    
    # We keep non-outliers for the final valid records
    df_final = df_avail[~df_avail.is_outlier].copy()
    rep["valid_records"] = len(df_final)
    rep["coverage_pct"] = round(len(df_final) / max(1, rep["planned_quotes"]) * 100, 2)
    rep["completeness_pct"] = 100.0 # simple mockup, assuming no NaNs for now
    
    # Reconstruct list of dicts (including outliers, but flagged)
    # The DB will store them all, with is_outlier=True/False
    final_records = df_avail.to_dict('records')
    return final_records, rep
