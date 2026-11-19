# DRAFT GitHub Issue — do not publish without team approval

**Suggested title:** Uploaded files for private projects are publicly accessible via known `/uploads/...` URLs

**Suggested labels:** `security`, `bug`, `priority: high`
**Suggested severity:** High (confidentiality — unauthenticated access to user files)
**Suggested assignee:** Ali (QA/security) — backend pair with Nuradil

## Summary

Uploaded project files (images and 3D models, including all historical model
revisions) are served without any authorization check. Anyone who learns a
file's URL can download it, even if the owning project and portfolio are
private.

## Affected code

- `app/backend/app/main.py:54` — `app.mount("/uploads", StaticFiles(directory=settings.upload_dir))` serves the whole upload directory with no authentication.
- `app/backend/app/storage.py` — `LocalStorage.save` returns `…/uploads/{path}` URLs; `SupabaseStorage` creates the bucket with `{"public": True}` and returns public object URLs, so the same exposure exists in production storage, not only local dev.
- `app/backend/app/routers/projects.py` — model/image records store `url` and `storage_path`; visibility is enforced at the project/portfolio API layer only, never at the file layer.

## Reproduction steps

1. Create an account, upload a `.glb` model to a project, note the returned
   `url` (e.g. `/uploads/models/<uuid>.glb`).
2. Ensure the portfolio/project is **not** public (do not enable sharing).
3. In an unauthenticated browser session (or `curl` with no Authorization
   header), request the URL from step 1.
4. The full binary file downloads with HTTP 200.

Same result for previous model revisions — every revision URL stays valid.

## Expected behavior

File access should follow the same visibility rules as the project:
unauthenticated or non-owner requests for files belonging to private projects
should return 401/403/404.

## Actual behavior

HTTP 200 with the file contents, regardless of authentication or project
visibility. Only the unguessable `uuid4` filename limits discovery (security
through obscurity — URLs leak via browser history, referer headers, shared
links, and CDN/proxy logs).

## Security impact

- Private project work — including unpublished 3D models — can be exfiltrated
  by anyone holding or guessing a URL.
- Uploaded images (which may contain EXIF metadata) are exposed the same way.
- Deleting a project removes the DB record and attempts file deletion, but any
  previously copied URL remains valid until then; nothing logs or revokes
  access.

## Suggested fix — complete, backward-compatible design

**Constraint:** every stored file URL (`…/uploads/<folder>/<uuid>.<ext>` for
local, `…/object/public/<bucket>/<path>` for Supabase) must keep working for
authorized viewers; nothing already in the DB changes.

### Phase 1 — gate local `/uploads` (single focused change)

1. Remove `app.mount("/uploads", StaticFiles(...))` in `main.py`.
2. Add `GET /uploads/{path:path}` in a small router:
   - Look up `path` in `ProjectModel.storage_path`,
     `ProjectModelRevision.storage_path`, and the project-image table
     (whichever matches; 404 otherwise — also prevents enumeration).
   - Resolve the owning project; serve via `FileResponse` when the project's
     portfolio is public **or** the caller owns it
     (`get_optional_portfolio` — anonymous viewers of public projects keep
     working; logged-in non-owners get 404, matching `_get_viewable_project`
     semantics).
   - `Content-Type` from the stored `file_format`/image content-type;
     `Cache-Control: private` only for owner-only files.
3. No schema changes — `storage_path` exists on every file record.

Result: identical URLs, access now inherits project visibility for both
current models and every retained revision.

### Phase 2 — production storage (Supabase)

The bucket is created `{"public": True}` today, so the same exposure exists
in production. Options, smallest first:

- **2a. Proxy through the Phase-1 route** — the gated endpoint fetches the
  object server-side and streams it. Zero Supabase changes; adds latency and
  server bandwidth.
- **2b. Private bucket + signed URLs (recommended)** — flip the bucket to
  private, keep `storage_path` in the DB, and have `store_file`/read
  endpoints return short-lived `create_signed_url` results instead of public
  URLs. `ModelOut.url`/`ModelRevisionOut.url`/`ImageOut.url` serialization
  points become "URL minted on read." Older revisions keep working because
  paths are unchanged.

Phase 2b is the complete fix for production; Phase 1 alone fully fixes local
dev and is safe to ship independently.

### Implementation cost estimate

Phase 1: ~60 lines (route + lookup helper) + tests for owner/public/stranger/
anonymous matrix. Phase 2b: storage-backend change in `SupabaseStorage` +
response URL minting, no schema migration.

## M4 rubric note

Filed as a tracked defect for the milestone's bug-tracking requirement. Status:
Open, fix deferred pending team approval; interim mitigation is documenting
that `/uploads` URLs are bearer URLs.
