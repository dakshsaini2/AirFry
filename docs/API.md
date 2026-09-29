# APIx Backend Endpoints

APIx exposes a robust set of RESTful JSON endpoints to power the dashboard.

Base URL: `http://localhost:8000`

## Health & Core
- `GET /api/v1/health` - Check database status and last run.
- `GET /api/v1/methodology` - Return index methodology parameters.

## Web Scraping Execution
- `POST /api/v1/scrape` - Triggers the Playwright scraping adapters (requires `X-API-Key` in headers if running in production mode).

## Dashboard Aggregations
- `GET /api/v1/summary?lead=[1,7,15,30,45]&carrier=[carrier]` - High-level KPIs (latest index, DoD, average fare, total valid quotes).
- `GET /api/v1/index?freq=[D|W|M]` - Jevons index time-series calculation.
- `GET /api/v1/elasticity?route=[route]` - T+1 vs T+45 percentage premium analysis.
- `GET /api/v1/heatmap` - Pivot table of Route vs Lead Time average total fares.
- `GET /api/v1/carriers` - Tax, Base, and Convenience fee splits by carrier.

## Data Explorer
- `GET /api/v1/fares?limit=[N]` - The clean, normalized records matching the filters.

## Empirical Validation
- `GET /api/v1/backtest` - Re-runs the empirical DGCA alignment report using current DB data.
- `GET /api/v1/validation_report` - Exposes strict validation state (eligibility, missing sources, Pearson/Spearman alignment stats).
