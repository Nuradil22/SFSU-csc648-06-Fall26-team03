# CareerGPS Backend

FastAPI backend for CareerGPS. Currently implements just enough to back the
frontend's login/signup forms: account creation, login, and a JWT-protected
`/auth/me` endpoint. Everything else (career path logic, resumes, AI
integration) comes in later milestones.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy (SQLite for local dev, Postgres/Supabase in deployment via `DATABASE_URL`)
- JWT auth (PyJWT) with bcrypt password hashing

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # defaults to a local SQLite file
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

The frontend dev server (Vite, `http://localhost:5173`) is allowed by CORS
out of the box. Update `ALLOWED_ORIGINS` in `.env` if that changes.

## Endpoints

| Method | Path          | Auth       | Description                    |
|--------|---------------|------------|---------------------------------|
| POST   | `/auth/signup`| —          | Create a user, returns a token |
| POST   | `/auth/login` | —          | Log in, returns a token        |
| GET    | `/auth/me`    | Bearer JWT | Current user's profile         |
| GET    | `/health`     | —          | Liveness check                 |

## Database

Tables are created automatically on startup via
`Base.metadata.create_all()` — there's no migration tool yet. Once the
schema needs to evolve carefully (e.g. once this is on shared Postgres),
introduce Alembic instead of relying on this.

## Notes

- `DATABASE_URL` defaults to a local `careergps.db` SQLite file (gitignored).
  Point it at the Supabase Postgres connection string to use the shared
  database, e.g. `postgresql+psycopg://user:password@host:5432/dbname`.
- Set a real `SECRET_KEY` (`openssl rand -hex 32`) outside of local dev.
