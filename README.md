# Ricky Rolls

A/B test data collection and analysis app for comparing win rates with and without hero "Ricky" in PVP idle game matchups.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your values:

```bash
cp .env.example .env
```

- `SECRET_KEY`,random string for session signing
- `ADMIN_KEY`,password for admin access
- `DATABASE_PATH`,optional, defaults to `./data/data.db`

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
