# CareerGPS Backend: Frontend Handoff

**Base URL:** `https://careergps-backend-n1uj.onrender.com`
**Interactive docs (try every endpoint):** https://careergps-backend-n1uj.onrender.com/docs
**Branch:** `main` (Render auto-deploys every merge to `main`)
**Database schema:** [`schema.sql`](schema.sql)

The free Render instance sleeps when idle, so the first request after a while can
take ~50 seconds. Show a loading state.

## Auth

`POST /auth/signup` or `POST /auth/login` returns `access_token`. Store it and send
it on every request that needs a login:

```
Authorization: Bearer <access_token>
```

Logout = delete the stored token. Errors always look like `{"detail": "..."}`.

## The endpoints for M2

| What | Request | Login? |
|------|---------|--------|
| Browse all shared projects | `GET /projects` | No |
| Search projects | `GET /projects?search=robot` | No |
| Filter by category | `GET /projects?category=Machine Learning` | No |
| Paginate | `GET /projects?limit=20&offset=20` | No |
| My projects | `GET /projects/mine` | Yes |
| One of my projects | `GET /projects/{id}` | Yes |
| Create a project | `POST /projects` | Yes |
| Update a project | `PATCH /projects/{id}` | Yes |
| Delete a project | `DELETE /projects/{id}` | Yes |
| My whole portfolio | `GET /portfolio/me` | Yes |
| Someone's shared portfolio | `GET /public/portfolios/{share_token}` | No |

**Search** looks in the title, description, category, and technologies, and is
case-insensitive. With several words, every word must match:
`?search=python react`. It returns projects from portfolios whose owner has
sharing turned on.

**Category** is the project's `subject` field (the "Subject / Field" input on the
Create Project page).

The full list (education, skills, experience, certificates, job preferences,
images, 3D models, AI guidance, sharing) is in [README.md](README.md#endpoints).

## Sample responses

These are real responses from the API.

### `GET /projects?search=robot` → 200

```json
[
  {
    "id": 1,
    "title": "Line Following Robot",
    "description": "Autonomous car that follows a line, reacts to colored markers, and avoids obstacles using multithreaded sensor polling.",
    "content_blocks": [],
    "project_date": "Spring 2026",
    "subject": "Embedded Systems",
    "technologies": ["C", "Raspberry Pi", "I2C"],
    "display_order": 0,
    "images": [],
    "links": [],
    "model_3d": null,
    "created_at": "2026-10-20T02:18:13+00:00",
    "updated_at": "2026-10-20T02:18:13+00:00",
    "owner_name": "Maya Chen",
    "share_token": "F8ke1TMAOYIId-XPyiyeMA"
  }
]
```

No matches returns `[]`. `share_token` links to the owner's portfolio:
`GET /public/portfolios/{share_token}`.

### `POST /auth/signup` → 201

Request: `{"name": "Sample Student", "email": "sample.student@example.com", "password": "Sample-pass1"}`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {"id": 5, "name": "Sample Student", "email": "sample.student@example.com", "created_at": "2026-10-20T02:18:25+00:00"},
  "message": "Account created successfully"
}
```

Errors: 409 = email already registered; 422 = missing field, bad email, or a weak
password (needs 8+ characters with a letter and a number).

### `POST /projects` → 201 (login required)

Request (only `title` is required):

```json
{
  "title": "Old title",
  "description": "Old description",
  "subject": "Old category",
  "project_date": "Fall 2026",
  "technologies": ["Python"],
  "content_blocks": [{"id": "overview", "type": "paragraph", "content": "..."}]
}
```

The response has the same shape as a search result, minus `owner_name` and `share_token`.

### Updating 3 fields: `PATCH /projects/13` → 200 (login required)

Send only the fields you want to change:

```json
{"title": "Weather Station", "description": "Raspberry Pi weather station with live charts.", "subject": "Internet of Things"}
```

Response, and the same values from `GET /projects/13` afterwards, showing that the change persisted:

```json
{
  "id": 13,
  "title": "Weather Station",
  "description": "Raspberry Pi weather station with live charts.",
  "subject": "Internet of Things",
  "...": "other fields unchanged"
}
```

### `GET /public/portfolios/{share_token}` → 200 (trimmed)

```json
{
  "name": "Diego Alvarez",
  "headline": "Architecture student combining design and 3D modeling",
  "bio": "I design spaces and show them off as interactive 3D models.",
  "location": "San Jose, CA",
  "profile_image_url": null,
  "career_interests": ["Architectural Designer", "3D Visualization Artist"],
  "links": [],
  "education": [{"id": 4, "school_name": "San Francisco State University", "degree": "B.A.", "major": "Interior Design",
                 "start_date": null, "graduation_date": "2027-12-17", "gpa": null,
                 "coursework": ["DAI 330 Digital Modeling", "DAI 451 Studio"], "is_expected": true}],
  "skills": [{"id": 13, "name": "Blender", "category": "technical", "proficiency": null}],
  "experiences": [{"id": 4, "experience_type": "volunteer", "organization": "Habitat for Humanity", "position": "Design Volunteer",
                   "location": null, "start_date": "2025-03-01", "end_date": "2025-11-30", "is_current": false,
                   "description": "Drafted floor plans for affordable housing renovations."}],
  "projects": [{"id": 12, "title": "Scanned Sculpture Gallery", "subject": "3D Modeling", "...": "same shape as above"}]
}
```

### Error example: `GET /portfolio/me` without a token → 401

```json
{"detail": "Not authenticated"}
```

## Database

12 tables in Supabase Postgres. Full DDL in [`schema.sql`](schema.sql).

```
users 1──1 portfolios 1──* portfolio_links
                       1──* education
                       1──* skills
                       1──* experiences
                       1──* certificates
                       1──* job_preferences   (private: never in shared portfolios)
                       1──* career_guidance
                       1──* projects 1──* project_media   (images + links)
                                     1──0..1 project_models (3D model)
```

Deleting a user deletes everything they own. Lists (technologies, coursework,
career interests, AI results) are stored as JSONB.

## Demo data

`python scripts/seed_demo.py --api <base URL>` loads 4 demo students with 12
projects plus education, skills, and experience, and turns their sharing on.
Their emails end in `@example.com`.
