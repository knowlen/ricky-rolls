<p align="center">
  <img src="app/static/logo.webp" alt="Ricky Rolls" width="150">
</p>

<h1 align="center">Ricky Rolls</h1>

A/B test data collection and analysis app for comparing win rates with and without hero "Ricky" in PVP idle game matchups.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optionally create a `.env` file to override defaults:

- `SECRET_KEY`: random string for session signing (default: `dev-secret-change-me`)
- `ADMIN_KEY`: password for admin access (default: `admin`)
- `DATABASE_PATH`: SQLite path (default: `./data/data.db`)

## Run

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000

## Admin Access

Visit `/admin?key=YOUR_ADMIN_KEY` to access the admin panel. The key only needs to be provided once per session.

## Deployment (Render)

The included `render.yaml` configures a Render web service.

**Warning:** Render's free tier uses an ephemeral filesystem. The SQLite database resets on each deploy. Options:
- Use the CSV export feature (`/api/export/csv`) for manual backups
- Upgrade to a paid tier with a persistent disk
- Migrate to PostgreSQL for production use
