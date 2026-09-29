# APIx Repository Structure Report

## 1. Final Architecture

```text
APIx/
├── backend/
│   ├── app.py             # FastAPI entry point, routing, backtest logic
│   ├── config.py          # Environment and application config
│   ├── database.py        # SQLAlchemy setup and session management
│   ├── models.py          # Database models
│   ├── data/
│   │   ├── sources.py     # Base interfaces for external sources
│   │   └── validators.py  # Validation pipelines and schemas
│   ├── index/
│   │   └── engine.py      # Core index formulas (Jevons, aggregation)
│   ├── ingestion/
│   │   ├── airfare.py     # Airfare API implementations (e.g. Duffel)
│   │   ├── dgca.py        # DGCA data ingestion tools
│   │   └── mospi.py       # MoSPI CPI comparison loader
│   ├── scrapers/
│   │   ├── base.py        # Base scraper definitions
│   │   ├── registry.py    # Decorators and adapter registration
│   │   └── adapters.py    # Implementations (IndiGo, MakeMyTrip)
│   └── services/
│       └── cleaning.py    # Data cleaning (MAD, deduplication)
├── frontend/              # Clean React/Vite/Tailwind frontend
├── tests/                 # Unit tests logically grouped
├── scripts/               # Helper and generation scripts
├── data/                  # Local CSVs and reference data
├── docs/                  # Project documentation
├── alembic/               # Database migrations
└── [Root files]           # docker-compose.yml, README, etc.
```

## 2. Refactoring Summary

### Files Deleted (Obsolete / Dead Code)
- `test_api.py` (Root) -> Moved relevant tests to `tests/test_api.py`.
- `backend/scraper.py` -> Unused Playwright skeleton not part of the active pipeline.
- `requirements-mospi.txt`, `requirements-scraper.txt` -> Consolidate/removed obsolete dependencies.
- `frontend-old/` -> Completely removed (superceded by `frontend/`).

### Files Merged
- `backend/index_engine/aggregation.py`, `jevons.py`, `relatives.py`, `service.py` -> Merged into `backend/index/engine.py`. These files were too small and tightly coupled, sharing the core responsibility of calculating the APIx index.
- `backend/scrapers/airlines/indigo.py`, `otas/mmt.py` -> Merged into `backend/scrapers/adapters.py`.

### Files Moved
- `backend/pipeline.py` -> Moved to `scripts/synthetic_generator.py` to ensure synthetic demo logic never accidentally bleeds into production or is mistaken for the active pipeline.
- `backend/cleaning.py` -> Moved to `backend/services/cleaning.py`.
- `backend/data_sources/base.py` -> `backend/data/sources.py`.
- `backend/data_sources/validators.py` -> `backend/data/validators.py`.
- `backend/data_sources/airfare.py`, `dgca.py` -> `backend/ingestion/airfare.py`, `dgca.py`.
- `backend/mospi.py` -> Moved to `backend/ingestion/mospi.py`.

### Test Restructuring
- Split `tests/test_pipeline.py` into `tests/test_synthetic.py` and `tests/test_api.py`.
- Fixed global state leakage with `app.dependency_overrides` by scoping it correctly in test fixtures in `tests/test_data_modes.py` and `tests/test_security.py`.

### Files Intentionally Retained
- `backend/app.py`: It is ~485 lines and cleanly structured with routers, config, and lifecycle events. Splitting it into smaller pieces right now would merely increase file counts without providing architectural clarity.

## 3. Code Quality / Regressions
- All 29 pytest regression tests passed.
- All Phase 11 & Phase 12 security protections and data_mode bounds remain perfectly intact.
- Database models were NOT modified (safe against regressions in alembic).
- Synthetic generation is safely quarantined into `scripts/`.
