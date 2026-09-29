# APIx - Real-time Airfare Price Index

## What is APIx?
APIx is a real-time airfare price index tracking engine and dashboard designed for the Ministry of Statistics and Programme Implementation (MoSPI). It systematically scrapes, cleans, and aggregates live domestic airfare data into a unified macroeconomic index.

## What problem does it solve?
Currently, official inflation and Consumer Price Index (CPI) metrics for Transport & Communication suffer from a significant lag and lack granular real-time visibility into dynamic airline pricing. APIx provides NSO and RBI economists with high-frequency, daily airfare inflation metrics to better track macroeconomic consumption trends.

## How does it work?
1. **Multi-Source Scraping**: Uses Playwright to ethically scrape live airline portals (e.g., IndiGo) and OTAs (e.g., MakeMyTrip).
2. **Quality Enforcement**: Filters sold-out flights, imputes missing taxes, and removes dynamic pricing anomalies using Median Absolute Deviation (MAD).
3. **Index Computation**: Computes a daily index using a Jevons geometric mean of price relatives.
4. **Validation**: Backtests real-time metrics against historical DGCA national average fares.

## What data does it use?
APIx strictly uses live, web-scraped data from Indian domestic carriers and OTAs across 10 major high-volume routes. It tracks forward-looking lead times (T+1, T+7, T+15, T+30, T+45) to capture both immediate dynamic pricing and long-term base pricing elasticity.

## How is the index calculated?
The index uses a **Jevons Geometric Mean** approach. It calculates the logarithmic price relative of today's fares against a 7-day base period, weighted by the DGCA passenger traffic share of each respective route.

## What is the current validation status?
**OFFICIAL VALIDATION VERIFIED**. The Phase 15 empirical backtest has successfully confirmed that the APIx Jevons index structurally aligns with the historical DGCA monthly average-fare data, satisfying the MoSPI Hackathon Problem Statement 26056 requirements.

## How do I run it?

### Backend (FastAPI + Playwright)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Start the API server
uvicorn backend.app:app --reload
```
Access the API Docs at: `http://localhost:8000/docs`

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Access the Dashboard at: `http://localhost:5173`

### Run Data Collection Pipeline
```bash
python scripts/ingest_live_airfare.py --origin DEL --destination BOM --departure-date 2026-10-15
```

---
*For extensive methodology, see [METHODOLOGY.md](docs/METHODOLOGY.md).*
