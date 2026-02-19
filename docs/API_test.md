# PhySioLog API Testing Guide

This document provides curl commands to test the PhySioLog API endpoints.
A brief description of the current data flow is described below:

1. Dropdown Selection (UI Layer)
   └─> trends.html ```<select id="windowSelect">```
       (user picks "7d", "30d", etc.)

2. Event Listener (dashboard.js)
   └─> ```wireWindowSelect()``` detects change on windowSelect
   └─> Calls onChange callback → ```refreshTrendsWindow()```

3. API Calls + UI Refresh (dashboard.js)
   └─> ```refreshTrendsWindow()``` reads windowSelect.value
   └─> calls ```fetchStatsPayload(windowValue)```
   └─> FETCH → /api/stats?window=7d  ← GET request
   └─> calls ```loadCharts(windowValue)```
   └─> FETCH → /api/entries (frontend then filters by selected window for plots)

4. Backend Route (routes_api.py)
   └─> ```@api_bp.route("/stats")``` catches GET request
   └─> Parses window="7d" query param
   └─> Converts "7d" → 7 days
   └─> Queries database: HealthEntry.query.filter(date >= today-7days)

5. Business Logic (services.py)
   └─> compute_stats(entries) processes the filtered entries
   └─> Calculates: avg_weight, avg_body_fat, avg_calories, etc.
   └─> Returns dict with aggregated statistics

6. Response (routes_api.py)
   └─> Returns JSON: { window, window_days, start_date, end_date, stats: {...} }

7. DOM Update (dashboard.js)
   └─> renderTrendsStats(payload) receives JSON
   └─> Updates each #stat-* element with formatted values
   └─> Updates #windowMeta with date range

The blueprint (api_bp in routes_api.py) is registered in __init__.py so all /api/* routes are automatically wired up when the Flask app starts.

The API layer is agnostic to the frontend and can be tested independently using curl or Postman. The JavaScript code in dashboard.js is responsible for calling the API, and routes_api.py doesn't care whether the request comes from a browser, curl, Postman, mobile app, etc.

So the flow can be shortened to just:

curl → /api/stats?window=7d → routes_api.py → services.py → JSON response

## Prerequisites

1. __Start the Flask app:__

   ```bash
   uv run python app.py
   ```

2. __Ensure you have test data__ (optional, but recommended for testing `/api/stats`):

   ```bash
   uv run python scripts/import_data.py data/health_data.csv
   ```

The app runs on `http://localhost:5000` by default.

---

## API Endpoints

### 1. GET /api/entries

Retrieve all health entries ordered by date (descending).

__Command:__

```bash
curl http://localhost:5000/api/entries
```

__Response (200 OK):__

```json
[
  {
    "id": 1,
    "date": "2026-02-15",
    "weight": 72.5,
    "body_fat": 18.2,
    "calories": 2200,
    "steps": 8500,
    "sleep_total": 7.5,
    "sleep_quality": "good",
    "observations": "felt energetic"
  },
  ...
]
```

---

### 2. POST /api/entries

Create a new health entry.

__Command:__

```bash
curl -X POST http://localhost:5000/api/entries \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-02-15",
    "weight": 72.5,
    "body_fat": 18.2,
    "calories": 2200,
    "steps": 8500,
    "sleep_total": 7.5,
    "sleep_quality": "good",
    "observations": "felt energetic"
  }'
```

__Response (201 Created):__

```json
{
  "success": true,
  "entry": {
    "id": 1,
    "date": "2026-02-15",
    "weight": 72.5,
    ...
  }
}
```

__Error Cases:__

- __400 Bad Request:__ Missing date, invalid JSON, or invalid date format
- __409 Conflict:__ Entry for the provided date already exists

---

### 3. GET /api/stats

Return aggregated statistics for health entries.

#### 3.1 All-time stats

```bash
curl http://localhost:5000/api/stats
```

#### 3.2 Last 7 days (using `window` parameter)

```bash
curl "http://localhost:5000/api/stats?window=7d"
```

#### 3.3 Last 30 days

```bash
curl "http://localhost:5000/api/stats?window=30d"
```

#### 3.4 Last 3 months

```bash
curl "http://localhost:5000/api/stats?window=3m"
```

#### 3.5 Last 1 year

```bash
curl "http://localhost:5000/api/stats?window=1y"
```

#### 3.6 Alternative: Using `days` parameter

```bash
curl "http://localhost:5000/api/stats?days=7"
curl "http://localhost:5000/api/stats?days=30"
```

__Response (200 OK):__

```json
{
  "window": "7d",
  "window_days": 7,
  "start_date": "2026-02-09",
  "end_date": "2026-02-15",
  "stats": {
    "avg_weight": 72.14,
    "avg_body_fat": 18.63,
    "avg_calories": 2132.5,
    "avg_steps": 8045.8,
    "avg_sleep": 7.36,
    "total_entries": 6
  }
}
```

__All-time response note:__

For `GET /api/stats` without `window`/`days`, the response now includes:

- `start_date`: oldest entry date in the dataset
- `end_date`: latest entry date in the dataset
- `window_days`: inclusive day span between `start_date` and `end_date`

__Error Cases:__

- __400 Bad Request:__ Invalid window format or non-positive `days` parameter
- __404 Not Found:__ No data available for the requested window

---

## Window Parameter Formats

The `window` parameter accepts:

- `7d` — last 7 days
- `30d` — last 30 days
- `3m` — last 3 months (90 days)
- `1y` — last 1 year (365 days)
- Omitted — all-time stats

---

## Troubleshooting

### "Connection refused" or "404 Not Found"

- Make sure the Flask app is running: `uv run python app.py`

### "No data available" (404)

- You need to create or import entries first:
  - Use the POST endpoint to create entries, or
  - Run `uv run python scripts/import_data.py data/health_data.csv`

### "Date already exists" (409)

- An entry for that date already exists in the database. Use a different date.
