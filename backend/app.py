from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from . import pipeline as P, mospi as M

app = FastAPI(title="APIx - Airfare Price Index API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
S = {}

def load(seed=7):
    raw = P.generate(seed=seed); df, rep = P.clean(raw)
    S.update(df=df, rep=rep, seed=seed, ts=datetime.utcnow().isoformat() + "Z", runs=S.get("runs", 0) + 1)
load()
L = lambda v: int(v) if v not in (None, "", "all") else None
C = lambda v: v if v not in (None, "", "all") else None

@app.get("/api/health")
def health(): return {"status": "ok", "last_run": S["ts"]}

@app.post("/api/scrape")
def scrape():
    """Runs one collection cycle. Demo mode = simulated quotes; see backend/scraper.py for live mode."""
    load(seed=S["seed"] + 1); return {"runs": S["runs"], "quality": S["rep"], "ts": S["ts"]}

@app.get("/api/index")
def index(freq: str = "D", lead: str = "all", carrier: str = "all"):
    s = P.apix(S["df"], L(lead), C(carrier), freq)
    return {"dates": [d.strftime("%Y-%m-%d") for d in s.index], "values": s.round(2).tolist()}

@app.get("/api/summary")
def summary(lead: str = "all", carrier: str = "all"):
    s = P.apix(S["df"], L(lead), C(carrier)); df = S["df"]
    return {"latest": round(s.iloc[-1], 2), "dod": round(s.iloc[-1] / s.iloc[-2] * 100 - 100, 2),
            "wow": round(s.iloc[-1] / s.iloc[-8] * 100 - 100, 2), "peak": round(s.max(), 2),
            "avg_fare": round(df.total.mean()), "quotes": len(df), "runs": S["runs"], "last_run": S["ts"]}

@app.get("/api/heatmap")
def heatmap():
    t = S["df"].pivot_table(index="route", columns="lead", values="total", aggfunc="mean").round(0)
    return {"routes": t.index.tolist(), "leads": t.columns.tolist(), "z": t.values.tolist()}

@app.get("/api/elasticity")
def elasticity(route: str = "all"):
    d = S["df"] if route == "all" else S["df"][S["df"].route == route]
    t = d.pivot_table(index="lead", columns="carrier", values="total", aggfunc="mean").round(0)
    return {"leads": t.index.tolist(), "series": {c: t[c].tolist() for c in t.columns},
            "premium_t1_vs_t45_pct": round((d[d.lead == 1].total.mean() / d[d.lead == 45].total.mean() - 1) * 100, 1)}

@app.get("/api/carriers")
def carriers():
    t = S["df"].groupby("carrier")[["base", "taxes", "udf", "convenience"]].mean().round(0)
    return {"carriers": t.index.tolist(), **{c: t[c].tolist() for c in t.columns}}

@app.get("/api/fares")
def fares(route: str = "all", carrier: str = "all", lead: str = "all", limit: int = Query(40, le=500)):
    d = S["df"]
    if route != "all": d = d[d.route == route]
    if C(carrier): d = d[d.carrier == carrier]
    if L(lead): d = d[d.lead == L(lead)]
    d = d.sort_values("date", ascending=False).head(limit).copy(); d["date"] = d.date.dt.strftime("%Y-%m-%d")
    return d[["date", "route", "carrier", "source", "lead", "fare_class", "base", "taxes", "udf", "convenience", "total"]].to_dict("records")

@app.get("/api/backtest")
def backtest(): return {"rows": P.backtest(S["df"]).to_dict("records"), "days_covered": int(S["df"].date.nunique())}

@app.get("/api/mospi")
def mospi_cmp():
    ref, src = M.load(); a = P.apix(S["df"], freq="M"); a.index = a.index.strftime("%Y-%m")
    m = ref.set_index("month").join(a.rename("apix"), how="inner")
    return {"source": src, "months": m.index.tolist(), "cpi": (m.cpi_index / m.cpi_index.iloc[0] * 100).round(2).tolist(),
            "apix": (m.apix / m.apix.iloc[0] * 100).round(2).tolist()}

@app.get("/api/quality")
def quality(): return S["rep"]

@app.get("/api/routes")
def routes(): return {"routes": list(P.ROUTES), "carriers": list(P.CARRIERS), "leads": P.LEADS}

app.mount("/", StaticFiles(directory=Path(__file__).parent.parent / "frontend", html=True), name="ui")
