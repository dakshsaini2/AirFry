# APIx Production Data Requirements

## Supported Data Modes
1. **fixture**: Static testing data for development only.
2. **synthetic**: Programmatically generated data for pipeline and stress testing only.
3. **external**: Clearly marked external data that lacks official provenance.
4. **official**: Authoritative, validated, independently sourced data (e.g. MoSPI, DGCA).
5. **live**: Permitted production web scraping data for real-time aggregation.

## Official Data Requirements
Official data MUST NOT be generated, bypassed, or synthetically repaired. It must have:
- `data_mode` = "official" or "live"
- A verifiable `source_reference`
- A verified `dataset_version`

## DGCA Ingestion
The authoritative DGCA parser handles DGCA historical traffic share data.
- **Validation**: Requires verifying `month`, `sector`, and `average fare`.
- **Rejection**: Missing provenance or invalid schema fails the entire dataset ingestion.

## Airfare Ingestion
The production adapters are located in `backend/scrapers/adapters.py` (e.g., `IndiGoAdapter`, `MMTAdapter`).
- **Authorization**: Uses Playwright Headless Web Scrapers.
- **Normalization**: Responses must be normalized into the APIx canonical schema (`origin`, `destination`, `carrier`, `flight_no`, `base_fare`, `taxes`, etc.) without storing personally identifiable information.

## Provenance and Dataset Versioning
Traceability must be strictly maintained for every observation:
`Index -> Fare Observation -> Raw Quote -> Source -> Dataset Version`

Dataset snapshots are tagged with:
- `airfare_dataset_version`
- `dgca_dataset_version`
- `weight_version`
- `methodology_version`

## Validation Gate & Contamination Protection
The system executes a central validation gate before generating official backtests.
- **Protection**: `synthetic` + `official` or `fixture` + `official` produces a `contaminated_dataset` error. The official datasets must be independent.
- **30-Day Requirement**: There must be >= 30 *eligible* overlapping days between the airfare data and the DGCA reference to perform the Phase 15 validation.

## Security Requirements
- API Key Authentication is mandatory (`/api/v1/scrape`).
- Strict CORS, HSTS, and Rate Limiting must be enforced.
- Database (`PostgreSQL`) must be isolated with no public exposure. SQLite is rejected in production environments.

## Production Environment Variables
Required variables for production (see `.env.production.example`):
- `APP_ENV=production`
- `DATABASE_URL=postgresql://...`
- `API_KEY=...`
- `FRONTEND_URL=...`
- `PLAYWRIGHT_BROWSERS_PATH=...`
