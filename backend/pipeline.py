"""APIx pipeline: data generation (demo) -> cleaning -> index construction -> back-test."""
import itertools, numpy as np, pandas as pd
from datetime import date, timedelta
from pathlib import Path

# route: (weight from DGCA traffic share [approx], base fare INR)
ROUTES = {"DEL-BOM": (.20, 5200), "DEL-BLR": (.15, 6100), "BOM-BLR": (.11, 4300), "DEL-CCU": (.10, 5600),
          "MAA-DEL": (.08, 6300), "DEL-HYD": (.08, 5400), "DEL-PNQ": (.08, 4800), "BLR-HYD": (.07, 2900),
          "BOM-HYD": (.07, 3600), "BOM-GOI": (.06, 3000)}
CARRIERS = {"IndiGo": .97, "Air India": 1.15, "Air India Express": .93, "Akasa Air": .95, "SpiceJet": .92}
SOURCES = {"Airline Website": 0, "MakeMyTrip": 349, "Yatra": 299, "EaseMyTrip": 0, "Cleartrip": 249, "Ixigo": 199, "Goibibo": 349}
LEADS = [1, 7, 15, 30, 45]
LEAD_MULT = {1: 1.9, 7: 1.35, 15: 1.1, 30: .95, 45: .88}
FESTIVALS = [date(2026, 10, 20), date(2026, 11, 8)]  # Dussehra, Diwali
KEY = ["date", "route", "carrier", "source", "lead"]


def generate(days=60, seed=7):
    """Synthetic quotes shaped like real scraper output (demo mode). Includes dirty rows on purpose."""
    rng = np.random.default_rng(seed)
    end = date.today()
    dates = [end - timedelta(days=i) for i in range(days - 1, -1, -1)]
    rows = list(itertools.product(dates, ROUTES, CARRIERS, LEADS))
    df = pd.DataFrame(rows, columns=["date", "route", "carrier", "lead"])
    df["source"] = rng.choice(list(SOURCES), len(df))
    dep = pd.to_datetime(df["date"]) + pd.to_timedelta(df["lead"], unit="D")
    fest = sum(np.exp(-(((dep - pd.Timestamp(f)).dt.days / 6.0) ** 2)) * .5 for f in FESTIVALS)
    demand = 1 + .08 * (dep.dt.dayofweek >= 4) + fest
    trend = 1 + .002 * np.arange(len(df)) / (len(df) / days)
    df["base"] = (df.route.map(lambda r: ROUTES[r][1]) * df.carrier.map(CARRIERS) * df.lead.map(LEAD_MULT)
                  * demand * trend * rng.lognormal(0, .12, len(df))).round(0)
    df["taxes"] = (df.base * .08 + 350).round(0)
    df["udf"] = 300.0
    df["convenience"] = df.source.map(SOURCES).astype(float)
    df["fare_class"] = "Economy"
    df["status"] = np.where(rng.random(len(df)) < .04, "sold_out", "available")
    out = rng.random(len(df)) < .01
    df.loc[out, "base"] *= rng.choice([4, .2], out.sum())
    df.loc[rng.random(len(df)) < .02, "taxes"] = np.nan
    df = pd.concat([df, df.sample(frac=.02, random_state=seed)], ignore_index=True)  # duplicates
    return df


def clean(raw):
    """Dedupe -> drop sold-out -> impute missing taxes -> robust outlier removal -> total fare."""
    rep = {"raw_rows": len(raw)}
    df = raw.drop_duplicates(KEY).copy(); rep["duplicates_removed"] = len(raw) - len(df)
    n = len(df); df = df[df.status == "available"].copy(); rep["sold_out_removed"] = n - len(df)
    miss = int(df.taxes.isna().sum())
    df["taxes"] = df.taxes.fillna(df.groupby(["route", "lead"]).taxes.transform("median")); rep["missing_imputed"] = miss
    df["total"] = df.base + df.taxes + df.udf + df.convenience
    lg = np.log(df.total)
    med = lg.groupby([df.route, df.lead]).transform("median")
    mad = (lg - med).abs().groupby([df.route, df.lead]).transform("median").clip(lower=.02)
    keep = (.6745 * (lg - med).abs() / mad) < 3.5
    rep["outliers_removed"] = int((~keep).sum()); df = df[keep].copy()
    rep["clean_rows"] = len(df)
    df["date"] = pd.to_datetime(df["date"])
    return df.reset_index(drop=True), rep


def apix(df, lead=None, carrier=None, freq="D"):
    """Weighted geometric (Jevons-type) index of route price relatives; base = first 7 days = 100."""
    d = df
    if lead: d = d[d.lead == lead]
    if carrier: d = d[d.carrier == carrier]
    g = d.groupby(["date", "route"]).total.apply(lambda s: np.exp(np.log(s).mean())).unstack()
    rel = np.log(g / g.iloc[:7].mean())
    w = pd.Series({r: ROUTES[r][0] for r in g.columns}); w /= w.sum()
    s = 100 * np.exp((rel.fillna(0) * w).sum(axis=1))
    return s if freq == "D" else s.resample(freq).mean()


def backtest(df, ref_path=None):
    ref = pd.read_csv(ref_path or Path(__file__).parent.parent / "data" / "dgca_monthly.csv")
    m = df.groupby(df.date.dt.strftime("%Y-%m")).total.mean().round(0).rename("apix_avg_fare")
    out = ref.set_index("month").join(m, how="inner")
    out["error_pct"] = ((out.apix_avg_fare - out.avg_fare_inr) / out.avg_fare_inr * 100).round(2)
    return out.reset_index()
