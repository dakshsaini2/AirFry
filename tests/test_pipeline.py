from backend import pipeline as P
from fastapi.testclient import TestClient

raw = P.generate(days=40); df, rep = P.clean(raw)

def test_cleaning():
    assert rep["duplicates_removed"] > 0 and rep["sold_out_removed"] > 0
    assert df.taxes.notna().all() and (df.total > 0).all()
    assert df.duplicated(P.KEY).sum() == 0

def test_index_base_and_freq():
    s = P.apix(df); assert 90 < s.iloc[:7].mean() < 110
    assert len(P.apix(df, freq="W")) < len(s)

def test_lead_time_elasticity():
    assert df[df.lead == 1].total.mean() > df[df.lead == 45].total.mean()

def test_backtest_has_error_column(): assert "error_pct" in P.backtest(df).columns

def test_api():
    from backend.app import app
    c = TestClient(app)
    assert c.get("/api/health").json()["status"] == "ok"
    assert len(c.get("/api/index?freq=D").json()["values"]) >= 30
    assert c.get("/api/backtest").json()["days_covered"] >= 30

def test_mospi_endpoint():
    from backend.app import app
    r = TestClient(app).get("/api/mospi").json(); assert len(r["months"]) >= 1 and "source" in r
