import pandas as pd
import numpy as np
from typing import Dict, Any, List


def calculate_price_relatives(fares_df: pd.DataFrame, base_fares: Dict[str, float]) -> pd.DataFrame:
    """
    Calculate price relative: r(i,t) = P(i,t) / P(i,base).
    """
    if fares_df.empty:
        return fares_df
        
    df = fares_df.copy()
    
    # We define product 'i' as (route, carrier, lead_time, departure_bucket)
    df['product_id'] = df['route_id'] + '|' + df['carrier'] + '|' + df['lead_days'].astype(str) + '|' + df['dep_bucket']
    
    df['base_price'] = df['product_id'].map(base_fares)
    # If no base price found, we could use the first observed price as base
    missing_base = df['base_price'].isna()
    if missing_base.any():
        first_prices = df[missing_base].groupby('product_id')['total_fare'].transform('first')
        df.loc[missing_base, 'base_price'] = first_prices
        
    df['price_relative'] = df['total_fare'] / df['base_price']
    return df



def calculate_elementary_index(relatives_df: pd.DataFrame) -> pd.DataFrame:
    """
    Elementary index (Jevons): I(cell,t) = (product of r(i,t))^(1/n).
    Cell is defined as (route, carrier, lead time).
    """
    if relatives_df.empty:
        return pd.DataFrame()
        
    df = relatives_df.copy()
    
    # Use log to compute geometric mean safely
    df['log_rel'] = np.log(df['price_relative'])
    
    # Group by cell and date
    # Convert dep_dt to date for index
    df['date'] = pd.to_datetime(df['scraped_at']).dt.date
    
    grouped = df.groupby(['date', 'route_id', 'carrier', 'lead_days'])['log_rel'].mean().reset_index()
    grouped['elementary_index'] = np.exp(grouped['log_rel'])
    
    return grouped



def aggregate_index(elementary_df: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    """
    APIx(t) = 100 * Sum(w_r * Sum(w_c|r * Sum(w_l * I(cell,t))))
    Returns a dataframe with daily APIx values.
    """
    if elementary_df.empty:
        return pd.DataFrame()
        
    df = elementary_df.copy()
    
    # Merge with weights based on available granularity
    merge_cols = [c for c in ['route_id', 'carrier', 'lead_days'] if c in weights.columns and not weights[c].isna().all()]
    if merge_cols:
        # Drop columns from weights that are not used in merge to avoid _x/_y suffixes
        cols_to_drop = [c for c in ['carrier', 'lead_days'] if c in weights.columns and c not in merge_cols]
        weights_clean = weights.drop(columns=cols_to_drop)
        df = df.merge(weights_clean.dropna(subset=merge_cols), on=merge_cols, how='left')
    
    # Fill missing weights with 0 or equal weights (for prototype, if weights are missing we handle it)
    if 'w_r' not in df.columns: df['w_r'] = np.nan
    if 'w_c' not in df.columns: df['w_c'] = np.nan
    if 'w_l' not in df.columns: df['w_l'] = np.nan
    
    df['w_r'] = df['w_r'].fillna(1.0 / df.groupby('date')['route_id'].transform('nunique'))
    df['w_c'] = df['w_c'].fillna(1.0 / df.groupby(['date', 'route_id'])['carrier'].transform('nunique'))
    df['w_l'] = df['w_l'].fillna(1.0 / df.groupby(['date', 'route_id', 'carrier'])['lead_days'].transform('nunique'))
    
    df['weighted_index'] = df['elementary_index'] * df['w_r'] * df['w_c'] * df['w_l']
    
    # Aggregate to daily
    daily_index = df.groupby('date')['weighted_index'].sum().reset_index()
    daily_index['apix'] = daily_index['weighted_index'] * 100.0
    
    return daily_index



class IndexEngineService:
    def __init__(self, db_session):
        self.db = db_session

    def fetch_base_fares(self) -> Dict[str, float]:
        # For prototype, we mock base fares for the first 7 days.
        # Ideally, query the DB for the base period.
        return {}

    def fetch_weights(self) -> pd.DataFrame:
        from ..models import Weight
        weights = self.db.query(Weight).filter(Weight.version == "2026-v1").all()
        if not weights:
            # Fallback to hardcoded DGCA traffic-share weights if none in DB
            ROUTES = {
                "DEL-BOM": (.20, 5200), "DEL-BLR": (.15, 6100), "BOM-BLR": (.11, 4300),
                "DEL-CCU": (.10, 5600), "MAA-DEL": (.08, 6300), "DEL-HYD": (.08, 5400),
                "DEL-PNQ": (.08, 4800), "BLR-HYD": (.07, 2900), "BOM-HYD": (.07, 3600),
                "BOM-GOI": (.06, 3000)
            }
            df = pd.DataFrame([{'route_id': r, 'w_r': w[0]} for r, w in ROUTES.items()])
            df['carrier'] = None
            df['lead_days'] = None
            df['w_c'] = 1.0
            df['w_l'] = 1.0
            return df
            
        data = []
        for w in weights:
            data.append({
                'route_id': w.route_id,
                'carrier': w.carrier,
                'lead_days': w.lead_days,
                'w_r': w.weight,
                'w_c': 1.0, # Not modeled in DB currently, assuming 1.0
                'w_l': 1.0  # Not modeled in DB currently, assuming 1.0
            })
        return pd.DataFrame(data)

    def validate_weights(self, weights: pd.DataFrame) -> None:
        if weights.empty:
            return
        if (weights[['w_r', 'w_c', 'w_l']] < 0).any().any():
            raise ValueError("Invalid weights: Negative weights found")
        route_w = weights.groupby('route_id')['w_r'].first()
        if not np.isclose(route_w.sum(), 1.0, atol=0.01) and not route_w.empty:
            print(f"Warning: Route weights sum to {route_w.sum()}, expected 1.0")

    def compute_daily_index(self, fares_df: pd.DataFrame, variant: str = 'total') -> pd.DataFrame:
        if fares_df.empty:
            return pd.DataFrame()
            
        # Select price column based on variant
        if variant == 'base':
            fares_df['total_fare'] = fares_df['base_fare']
            
        base_fares = self.fetch_base_fares()
        weights = self.fetch_weights()
        self.validate_weights(weights)
        
        relatives = calculate_price_relatives(fares_df, base_fares)
        elementary = calculate_elementary_index(relatives)
        daily_index = aggregate_index(elementary, weights)
        
        return daily_index

    def compute_aggregations(self, daily_index: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        if daily_index.empty:
            return {}
            
        daily_index['date'] = pd.to_datetime(daily_index['date'])
        
        weekly = daily_index.resample('W', on='date')['apix'].mean().reset_index()
        monthly = daily_index.resample('ME', on='date')['apix'].mean().reset_index()
        
        return {
            'daily': daily_index,
            'weekly': weekly,
            'monthly': monthly
        }


