"""MoSPI eSankhyiki CPI loader. Official client: pip install -r requirements-mospi.txt
Sync live data:  python -m backend.mospi   -> writes data/mospi_cpi.csv (month,cpi_index) + data/mospi_cpi.live
NOTE: column/filter names come from the live API (esankhyiki.get_metadata("CPI", ...)); adjust FILTERS/heuristics if needed."""
import pandas as pd
from pathlib import Path
D = Path(__file__).parent.parent.parent / "data"
FILTERS = {"base_year": "2024", "level": "Item"}  # verify with esankhyiki.get_metadata("CPI", base_year=..., level=...)

def sync():
    import esankhyiki
    df = esankhyiki.get_data("CPI", FILTERS, format="df"); print(list(df.columns))
    txt = lambda k: [c for c in df.columns if k in c.lower()]
    item, idx, per = txt("item") or txt("subclass") or txt("group"), txt("index"), txt("month") or txt("date") or txt("year")
    d = df[df[item[0]].astype(str).str.contains("air|transport", case=False)]
    out = d.groupby(per[0])[idx[0]].mean().reset_index(); out.columns = ["month", "cpi_index"]
    out.to_csv(D / "mospi_cpi.csv", index=False); (D / "mospi_cpi.live").write_text("ok"); print(out.tail())

def load():
    df = pd.read_csv(D / "mospi_cpi.csv")
    return df, ("MoSPI eSankhyiki (synced)" if (D / "mospi_cpi.live").exists() else "Illustrative placeholder - run python -m backend.mospi")

if __name__ == "__main__": sync()
