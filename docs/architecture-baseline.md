# Architecture baseline — 2026-11-04

## Confirmed stack
- Local Python web application: FastAPI + SQLite; application entry points and API routes are in `app/main.py`.
- Frontend is vanilla JavaScript and static HTML/CSS under `app/static/`; no frontend framework or package/build manifest is present.
- Database defaults to `data/beta_intelligence.sqlite3`; `BPI_DATA_DIR` can point to another location. Do not commit or modify the user database during UI work.
- Background monitoring is implemented in `app/monitoring.py`; source definitions and statuses are in `app/source_catalog.py`; discovery and screening code are in `app/discovery.py` and `app/screening.py`.
- `GET /api/projects` returns project records and now accepts `limit` and `offset`. The frontend loads successive pages until the last partial page, so a single-page cap cannot silently truncate larger registries.
- Tests: Python `unittest` under `tests/`; JavaScript validation can use Node `--check`. There is no configured frontend build step.

## Data snapshot (local DB, read only, 2026-11-04)
- 386 project records, 668 project/source associations, 67 registered source records, 641 events (recent events endpoint is intentionally bounded).
- Review statuses: 361 REJECTED, 19 REVIEW, 6 PENDING. The queue endpoint returns 24; radar is a curated active subset and can include one completed REVIEW record.
- Sources: 3 ACTIVE, 1 enabled ERROR, plus records requiring validation, API credentials/integration, access, manual handling, or disabled status.
- The 291 count is the total from a completed historical analysis run dated 2026-11-02; 26 refers to cards produced by that run. Neither is the current database total. The reported 12 sources was a prior report figure; current registry has 67 rows.
- Rejected/later items are filtered from active lists by the existing frontend `matches()` rules, not deleted. They remain available in archived/rejected and dossier views.
- The originally reported “empty dashboard” was stale/misleading summary terminology and filtered feed context rather than missing DB rows. Labels now distinguish dossiers, review candidates, archived records, source links, active and registered sources. No synthetic counts were inserted.
- A pagination limit remains on each API request, but the frontend consumes all pages. Tests cover multiple pages.

## UI implementation
- Theme tokens and component styles are centralized in `app/static/style.css`.
- Local Inter Variable WOFF2 assets and OFL notice live in `app/static/fonts/`; runtime does not depend on a remote font host.
- Search and filters remain client-side over the loaded real dataset. Existing screen/navigation structure and business filtering/scoring criteria are preserved.

## Data safety evidence
The original database SHA-256 before and after the read-only audit was `AD360E998F75465FA92023519E9F45F489450603B97D8ECBFEA9944798A44C72`. Visual QA uses a separate copied database; no user records or environment configuration were edited.
