# CareerGPS Backend

FastAPI backend for CareerGPS. It covers the M2 functional requirements R1–R17:
accounts, the portfolio (personal info, education, skills, experience, projects),
project media and 3D models, AI career guidance, and public sharing.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy (SQLite for local dev, Postgres/Supabase in deployment via `DATABASE_URL`)
- JWT auth (PyJWT) with bcrypt password hashing
- File storage: local disk (dev) or Supabase Storage (deployment)
- AI: pluggable provider: `mock` (no key needed) or `anthropic` (Claude)

## Setup

```bash
cd app/backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env           # defaults: local SQLite, local uploads, mock AI
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs. Click **Authorize** and enter your email as
  the "username" to try authenticated endpoints.
- Health check: http://localhost:8000/health

## Demo data

```bash
python scripts/seed_demo.py                     # against the local API
python scripts/seed_demo.py --api https://careergps-backend-n1uj.onrender.com
```

Creates 4 demo students (emails `@example.com`) with 12 projects. Safe to re-run.

For the frontend team: see [FRONTEND_HANDOFF.md](FRONTEND_HANDOFF.md) for sample
responses, and [schema.sql](schema.sql) for the database schema.

## Test

```bash
pytest
```

Tests use a throwaway SQLite database. To run them against Postgres, set
`TEST_DATABASE_URL` to a **scratch** database. The tests drop all tables, so never
point it at the shared Supabase database.

## Authentication

`POST /auth/signup` and `POST /auth/login` return `{ access_token, user, message }`.
Send the token on every other request:

```
Authorization: Bearer <access_token>
```

Passwords must be 8+ characters with at least one letter and one number (R1.4).
Logout (R2.4) is client-side: delete the stored token. `POST /auth/logout` exists
so the frontend has an endpoint to call.

## Endpoints

All `/portfolio/me/*`, `/guidance/*`, and `/projects/*` routes (except public
`GET /projects`) require a token and only ever touch the caller's own data. Someone else's record ids return 404 (R2.5).
PATCH bodies are partial: send only the fields you want to change.

| Method | Path | Req. | Description |
|--------|------|------|-------------|
| POST | `/auth/signup` | R1 | Register (name, email, password) |
| POST | `/auth/login` | R2 | Log in (JSON) |
| POST | `/auth/token` | R2 | Log in (form data; used by Swagger "Authorize") |
| POST | `/auth/logout` | R2.4 | Log out |
| GET | `/auth/me` | | Current user |
| GET | `/portfolio/me` | R3.2, R9 | Whole portfolio with all sections and projects |
| PATCH | `/portfolio/me` | R3.1, R3.3, R3.4 | Name, headline, bio, location, photo URL, career interests |
| GET/POST | `/portfolio/me/links` | R3.5 | External profile links |
| PATCH/DELETE | `/portfolio/me/links/{id}` | R3.5 | |
| GET/POST | `/portfolio/me/education` | R4 | Education records (incl. coursework) |
| PATCH/DELETE | `/portfolio/me/education/{id}` | R4.3, R4.4 | |
| GET/POST | `/portfolio/me/skills` | R5 | Skills, with category |
| PATCH/DELETE | `/portfolio/me/skills/{id}` | R5.2, R5.3 | |
| GET/POST | `/portfolio/me/experience` | R6 | Work / internship / volunteer / academic / research / other |
| PATCH/DELETE | `/portfolio/me/experience/{id}` | R6.3, R6.4 | |
| GET | `/projects` | | **Public** browse/search: `?search=`, `?category=`, `?limit=`, `?offset=` |
| GET | `/projects/mine` | R7.5 | My projects |
| POST | `/projects` | R7.1–R7.3 | Create a project |
| GET/PATCH/DELETE | `/projects/{id}` | R7.4 | |
| POST | `/projects/{id}/images` | R8.1 | Upload image (multipart: `file`, optional `label`) |
| POST | `/projects/{id}/images/url` | R8.1 | Attach an image by URL |
| POST | `/projects/{id}/links` | R8.2 | Repo / demo / resource link |
| DELETE | `/projects/{id}/media/{media_id}` | R8.4 | Remove an image or link |
| PUT | `/projects/{id}/model` | R15.1–R15.3, R15.5 | Upload/replace 3D model (multipart: `file`) |
| DELETE | `/projects/{id}/model` | R15.4 | Remove 3D model |
| POST | `/guidance` | R10–R13, R14 | Run a new AI analysis of the saved portfolio |
| GET | `/guidance/latest` | R10.4 | Most recent analysis |
| GET | `/guidance` | | Past analyses, newest first |
| GET | `/portfolio/me/share` | R17.1 | Current share status / link |
| POST | `/portfolio/me/share` | R17.1 | Turn sharing on (`?regenerate=true` for a new link) |
| DELETE | `/portfolio/me/share` | | Turn sharing off |
| GET | `/public/portfolios/{token}` | R17.2–R17.4 | Shared portfolio, no login needed |
| GET | `/public/portfolios/{token}/projects/{id}` | R16.1 | Single shared project |
| GET | `/health` | | Liveness check |

### Response shape notes for the frontend

- **Projects** have `description` (plain text) and `content_blocks` (the
  DescriptionEditor's blocks, stored as-is), plus `project_date` ("Fall 2025"),
  `subject`, `technologies[]`, and separate `images[]`, `links[]` lists, and
  `model_3d` (or `null`).
- **Share links** look like `<FRONTEND_URL>/p/<token>`. The frontend needs a `/p/:token`
  route that calls `GET /public/portfolios/:token`. Public responses never include
  the owner's email.
- **3D models**: `.glb` files, or `.gltf` files with everything embedded. `model_3d.url`
  can be passed straight to a Three.js `GLTFLoader` / React Three Fiber `useGLTF`.
  Rotate, zoom, and reset (R16.2–R16.5) are viewer features on the frontend.
- **Errors** come back as `{ "detail": "..." }`. For 422 validation errors,
  `detail` is a list of `{ loc, msg }`.
- **AI guidance**: `POST /guidance` can take several seconds with Claude, so show
  a loading state (NFR2). Errors: 400 = portfolio is empty, 502/503 = AI failed.
  The previous result stays available from `/guidance/latest` either way (R10.5, R14.4).

## Database

| Table | Holds | Relationship |
|-------|-------|--------------|
| `users` | name, email, password hash | 1 → 1 `portfolios` |
| `portfolios` | headline, bio, location, photo URL, career interests, sharing | 1 → many of each table below |
| `portfolio_links` | external profile links | |
| `education` | school, degree, major, dates, GPA, coursework | |
| `skills` | name, category, proficiency | |
| `experiences` | type, organization, position, dates, description | |
| `projects` | title, description, editor blocks, date, subject, technologies | 1 → many `project_media`, 1 → 0..1 `project_models` |
| `project_media` | images and links (`media_type`) | |
| `project_models` | 3D model URL, format, size | |
| `career_guidance` | summary, career paths, strengths, improvements, next steps | one row per analysis |

Deleting a user cascades to everything they own. List-like fields (career
interests, coursework, technologies, AI results) are JSON (JSONB on Postgres).

Tables are created automatically on startup with `Base.metadata.create_all()`.
That creates **missing tables only** and never changes existing ones. Adding a
new table is fine; changing columns on an existing table needs a migration
(introduce Alembic when that first happens).

## Configuration

See `.env.example` for every setting. For deployment (Render):

- `STORAGE_BACKEND=supabase` plus `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
  The public bucket (`careergps-media`) is created on the first upload if it doesn't
  exist. Don't use `local` on Render: its disk is wiped on every deploy.
- `AI_PROVIDER=anthropic` plus `ANTHROPIC_API_KEY` to use Claude. Leave it as
  `mock` to keep guidance working without a key.
- `FRONTEND_URL` for share links.

### Swapping the AI provider

`app/ai.py` has one function per provider, registered in `PROVIDERS`. To add
another LLM, write a function that takes the portfolio payload dict and returns
`(GuidanceContent, model_name)`, register it, and set `AI_PROVIDER` to its key.
Only the fields in `build_portfolio_payload` are sent to the provider: never the
student's name, email, location, or links (NFR4).
