### PhySioLog — Copilot instructions for contributors

Short, actionable guidance to help AI coding agents be immediately productive in this repository.

User-provided project intent (included as entered):

"I want to create a small web page to track health data (see HealthTracker.csv). The user (me) will run a small app (e.g., Danjo or  Flask) to open a webpage that fills that form, and a plot with the average results will be shown (with Plotly). I would love to prepare it for deployment on AWS (in the cloud), probably using a Docker container running the app and connecting to a SQL-like database."


- **Big picture**: This is a single-process Flask web app (app.py) that serves an HTML/JS dashboard and a tiny JSON API. Data is stored locally in SQLite (`physiolog.db`) via SQLAlchemy (`HealthEntry` model in `app.py`). Static UI + charts live under `static/` and templates under `templates/`.

- **Key files**:
  - `app.py` — main Flask app, routes, and `HealthEntry` SQLAlchemy model (date is `unique=True`). API endpoints:
    - `GET /api/entries` — returns all entries (JSON)
    - `POST /api/entries` — create entry (expects JSON with `date` in `YYYY-MM-DD`)
    - `GET /api/stats` — computed averages + counts
  - `scripts/import_data.py` — CSV/TSV import helper; contains `parse_date`, `parse_time`, `parse_number` and a flexible column-mapping heuristic.
  - `static/js/dashboard.js` — UI logic: fetches `/api/entries` and `/api/stats`, calculates 7-day moving averages, and draws Plotly charts.
  - `templates/` — Jinja templates: `overview.html`, `trends.html`, `entry.html`, `coach.html`, `test.html`.

- **How the data-flow works**:
  1. Browser loads HTML from Flask templates.
  2. `static/js/dashboard.js` calls `/api/entries` and `/api/stats` to render charts and stats.
  3. New entries are posted to `/api/entries` which are persisted via SQLAlchemy to `physiolog.db`.
  4. `scripts/import_data.py` can bulk-import CSV/TSV files; it uses the `date` column to detect duplicates and will skip existing rows.

- **Developer workflows / commands** (copyable):
  - Install deps: `uv sync` (creates `.venv` and `uv.lock`).
  - Run app locally: `uv run python app.py` (debug server on port 5000). Note: `app.py` calls `db.create_all()` on import — DB auto-initializes.
  - Import CSV/TSV data: `uv run python scripts/import_data.py data/health_data.csv` (script prints mapped columns and summary). The importer requires a column containing the word `date`.
  - Run tests (if added): `uv run pytest` (pytest config in `pyproject.toml`).
  - Format: `uv run black .` (Black config: 88 chars, py311 target).

- **Project-specific conventions / gotchas**:
  - The SQLite DB file `physiolog.db` is created in the repository root by the app; treat it as local/private data.
  - `HealthEntry.date` is unique — imports and API POSTs will fail if you try to insert a duplicate date. The importer purposely skips existing dates.
  - `scripts/import_data.py` maps columns by simple keyword matching (e.g., if a CSV column name contains `weight` and `kg` it maps to `weight`). When adding tests or fixing imports, prefer adding explicit mapping tests for edge-case column names.
  - Time parsing: `parse_time` expects `h:mm` or `h:mm:ss` and returns hours as float rounded to two decimals. Invalid formats raise ValueError — importer logs and counts these as errors.
  - API POST payload shape example (JSON):

```json
{
  "date": "2026-02-01",
  "weight": 72.5,
  "body_fat": 18.2,
  "calories": 2200,
  "steps": 8500,
  "sleep_total": 7.5,
  "sleep_quality": "good",
  "observations": "felt energetic"
}
```

- **Where to make targeted changes**:
  - Adjust stats or add new API fields: modify `HealthEntry.to_dict()` and update `static/js/dashboard.js` consumers (`/api/entries` parsing and charts).
  - Add server-side validation: extend the POST branch in `app.py` (`/api/entries`) and make importer raise clearer errors.
  - Add tests: place tests under `tests/` (pytest is configured in `pyproject.toml`). Start with import edge cases (`scripts/import_data.py`) and API contract tests (`app.py` endpoints).

- **Linting/formatting and CI hints**:
  - Project uses Black (see `pyproject.toml`). Keep line-length 88. Ruff config exists in `pyproject.toml`.
  - There is no CI config file in the repo; when adding CI, include `uv sync` and `uv run pytest` steps and persist artifacts only when appropriate (do not commit `physiolog.db`).

- **Security & privacy notes**:
  - All user data is local to the repository (`physiolog.db`). Avoid printing or uploading `physiolog.db` or `data/*.csv` to public remotes.

If anything above is unclear or you want more examples (API tests, importer unit tests, or a CI workflow), tell me which section to expand. 
