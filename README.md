# SafeCorridor Backend

FastAPI service for airport status, route patterns, and advisories.

## Local Run

1. Copy env:
   - `cp .env.example .env`
2. Install:
   - `python3 -m venv venv`
   - `source venv/bin/activate`
   - `pip install -r requirements.txt`
3. Seed data:
   - `python -m app.seed`
4. Run API:
   - `uvicorn app.main:app --reload --port 8000`

## Required Environment Variables

- `DATABASE_URL`  
  Example for PostgreSQL: `postgresql+psycopg2://user:password@host:5432/dbname`
- `CORS_ALLOWED_ORIGINS`  
  Comma-separated frontend origins.

## Deploy Targets

- Fly.io: `fly.toml` + `Dockerfile`
- Railway: `railway.toml` + `Dockerfile`
