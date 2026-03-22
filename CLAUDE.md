# Ricky Rolls - Project Guide

## What This Is

A/B test data collection and analysis web app. Officers log PVP matchup results (with/without hero "Ricky") against a set of defender accounts. The app provides individual and aggregate analysis with Plotly charts and Wilcoxon signed-rank statistical tests.

## Running Locally

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8080
```

Default admin key is `admin` (visit `/admin?key=admin`). SQLite DB auto-creates at `data/data.db` with 8 seed defenders on startup.

## Architecture

- **FastAPI** with sync route handlers (no async,SQLite is synchronous)
- **SQLite** with WAL mode, `row_factory=sqlite3.Row`, foreign keys ON
- **Starlette SessionMiddleware** for auth (signed cookies, 90-day expiry)
- **Pico CSS classless** (CDN) as reset + base, heavily overridden by terminal dark theme in `style.css`
- **Plotly** charts built server-side as Figure objects, serialized to JSON, rendered client-side
- **Vanilla JS** single file (`app.js`) with page routing via `document.body.dataset.page`

## File Layout

```
app/
  main.py              # FastAPI app, lifespan hook, middleware, router includes
  config.py            # pydantic-settings: SECRET_KEY, ADMIN_KEY, DATABASE_PATH
  database.py          # SQLite connection factory, schema init, seed defenders, migrate_db()
  models.py            # Pydantic request models (LoginRequest, MatchupRequest, etc.)
  dependencies.py      # FastAPI Depends: get_db, get_current_officer, require_admin
  routers/
    pages.py           # GET routes serving Jinja2 templates (/, /enter, /results, /aggregate, /admin)
    api.py             # JSON API: /api/login, /api/logout, /api/matchup, /api/officer/meta, /api/defenders
    admin.py           # Admin API: CRUD defenders + CSV export. Has TWO routers (router + export_router)
  services/
    stats.py           # compute_stats(), run_wilcoxon(),both take list of dicts with wins_control/wins_ricky
    charts.py          # build_paired_bar(), build_wr_boxplot(), build_trophy_scatter(), empty_chart_json()
  templates/           # Jinja2: base.html, login.html, enter.html, results.html, aggregate.html, admin.html
  static/
    app.js             # All client JS (~200 lines): auto-save, chart rendering, admin CRUD
    style.css           # Terminal dark theme (full custom theme overriding Pico CSS)
```

## Key Patterns & Gotchas

### Two Routers in admin.py

`admin.py` exports both `router` (prefix `/api/admin`) and `export_router` (prefix `/api`). Both must be included in `main.py`. The export router exists separately because `/api/export/csv` doesn't fit under `/api/admin` but still needs the admin guard.

### Chart Data Flow

Charts are Plotly JSON strings embedded in `<script type="application/json" id="X-data">` tags. Client JS finds these by ID suffix `-data`, parses them, and calls `Plotly.newPlot()` on the matching `-container` div. This avoids data-attribute escaping issues with large JSON.

### Service Function Signatures

- `compute_stats(matchups)` and `run_wilcoxon(matchups)`, take list of dicts with `wins_control`, `wins_ricky`, `losses_control`, `losses_ricky` keys
- `build_paired_bar(matchups)`, grouped bar chart of control vs ricky WR per defender. Single officer use. Requires `defender_name` key.
- `build_wr_boxplot(matchups, officer_colors=None)`, box plot of WR diff distribution per officer + pooled. Requires `officer_name` key.
- `build_trophy_scatter(matchups, officer_colors=None)`, scatter of defender trophies vs WR diff with OLS trend line. Requires `defender_name`, `officer_name`, `defender_trophies` keys.
- `empty_chart_json(message)`, requires a message string argument (not optional)

### Trophy Scatter Requires Full Data

The trophy scatter needs `officer_name` for grouping traces and `defender_trophies` for the x-axis. Any query feeding `build_trophy_scatter()` must include both fields. The results page injects `officer_name` from the session and adds `d.trophies AS defender_trophies` to the matchup query.

### Data Entry Auto-Save

Counter values on the enter page live in `<span>` elements with `data-field-display` attributes (e.g. `data-field-display="wins_control"`). JS reads `span.textContent`, not input values. Counter +/- buttons share the same `data-field` attribute; direction is determined by `.increment`/`.decrement` CSS class. The `ricky_replaces` field is a `<select>` dynamically populated from the comma-separated comp input. The officer metadata fields (comp, ricky_replaces) are outside the table and use `data-field`. The meta debounce saves both fields together to `/api/officer/meta`.

### Matchup Upsert with COALESCE

The upsert SQL uses `COALESCE(excluded.col, matchups.col)` so that sending `null` for a field preserves the existing value. This prevents partial auto-saves from nuking complete rows. Pydantic model fields are `Optional` with `None` defaults to support this.

### Officer Auth

`get_current_officer()` reads `officer_id` from the session cookie and returns a minimal dict `{id, name}`,NOT a full DB row. The enter page separately queries the officers table for metadata fields (comp, ricky_replaces) and passes them as `officer_meta`.

### Admin Auth

First visit requires `?key=<ADMIN_KEY>` query param which sets `session["is_admin"] = True`. Subsequent visits only check the session flag. The admin check is via `require_admin` dependency (raises 403) for API routes, and via session check in the `admin_page` route handler.

### "Completed" Matchup Definition

A matchup is "completed" when both conditions have 5+ total fights: `(wins_control + losses_control) >= 5 AND (wins_ricky + losses_ricky) >= 5`. Stats, charts, and the Wilcoxon test all use this threshold. Win rate diff = `wr_ricky - wr_control` where `wr = wins / (wins + losses)`. The `mean_diff` returned by `compute_stats` is a raw float (e.g. 0.15); templates multiply by 100 for percentage display.

### Database Migrations

`migrate_db(conn)` in `database.py` runs idempotent `ALTER TABLE ADD COLUMN` statements using `PRAGMA table_info()` to detect missing columns. Called from `init_db()` after schema creation. Add new migrations here for schema changes to existing columns.

### Template Variable Names

Each page route passes different context. Key differences:
- **enter.html**: `officer`, `officer_meta`, `defenders`, `matchup_map` (dict keyed by defender_id)
- **results.html**: `officer`, `stats`, `wilcoxon`, `matchups` (list), `paired_bar_json`, `trophy_scatter_json`, `n_incomplete`, `last_updated`
- **aggregate.html**: `officer`, `per_officer_stats` (dict), `per_officer_wilcoxon` (dict), `pooled_stats`, `pooled_wilcoxon`, `all_matchups`, `boxplot_json`, `trophy_scatter_json`, `n_incomplete`, `last_updated`, `officer_colors` (dict mapping officer name to hex color)
- **admin.html**: `officer`, `defenders` (list), `matchups` (list with officer_name/defender_name)

### CSS Row Classes

Enter page table rows get classes based on WR diff (only for completed matchups with 5+ fights each): `ricky-better` (green), `control-better` (red), `tied` (gray). Set both server-side in Jinja and client-side in JS after counter clicks. Saved rows get `saved` class (green left border) and a brief `save-flash` animation.

## Database

Three tables: `defenders`, `officers`, `matchups`. Schema in `database.py`. Key constraints:
- `officers.name` has `COLLATE NOCASE`,login lookup is case-insensitive
- `matchups` has `UNIQUE(officer_id, defender_id)`,one matchup per officer-defender pair
- `defenders.id` cascade-deletes related matchups via `ON DELETE CASCADE`
- `defenders.trophies`,optional integer for trophy count display
- `matchups` has `wins_control`, `losses_control`, `wins_ricky`, `losses_ricky`,all integer counters (losses default 0 for backwards compat)
- DB auto-creates and seeds on app startup via lifespan hook; `migrate_db()` adds any missing columns

## Theme System

`STYLE.md` is the authoritative design reference. The terminal dark theme uses pure black backgrounds, JetBrains Mono monospace font, and minimal functional color.

### CSS Variables (`:root` in `style.css`)

- `--black` (#000000): page background, chart interiors
- `--surface` (#1a1a1a): nav, cards, inputs, elevated surfaces (only two bg tiers: black and surface)
- `--border` (#404040): all borders and lines,single color everywhere
- `--muted` (#808080): labels, secondary text, inactive elements
- `--readable` (#b0b0b0): instructional/onboarding body text
- `--primary` (#ffffff): headings, body text, active content
- `--accent` (#e8d5b0): active tab underlines, links, button borders, focus rings, step numbers
- `--positive` (#2ecc71): positive numeric values only (never on prose/labels)
- `--negative` (#c0392b): negative numeric values only (never on prose/labels)
- `--data-1` through `--data-7`: categorical data visualization colors (never used in UI chrome)

### Accent Color Swap

To change the accent color, update TWO places:
1. `--accent` in `:root` in `app/static/style.css`
2. `ACCENT` constant in `app/services/charts.py`

### Chart Theming

Charts are themed via `CHART_LAYOUT` and `DATA_COLORS` in `charts.py`. These use hardcoded hex values (Python can't read CSS variables). `CHART_LAYOUT` sets black backgrounds, white text, `#404040` gridlines, JetBrains Mono font. `DATA_COLORS` matches `--data-1` through `--data-7`. Single-series charts use `ACCENT`; multi-series use `DATA_COLORS`.

### UI Text

All UI text is lowercase (headings, labels, nav, buttons). Semantic colors (positive/negative) appear only on numeric values, never on sentences or labels.

## Dependencies

All in `requirements.txt`: fastapi, uvicorn[standard], jinja2, itsdangerous, python-multipart, plotly, scipy, numpy, pydantic-settings.

## Deployment

Configured for Render via `render.yaml`. Render free tier has ephemeral filesystem,DB resets on deploy. CSV export at `/api/export/csv` provides manual backup.

## Future Plans

- Discord OAuth login (officers table has `provider` and `external_id` columns ready)
- Persistent storage migration (PostgreSQL or Render persistent disk)
