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

## Suggested fix (smallest backward-compatible change)

Phase 1 — gate the local backend:

- Replace the `StaticFiles` mount with an authenticated route
  `GET /uploads/{path:path}` that looks up `storage_path` in
  `ProjectModel`/`ProjectModelRevision`/project image tables, resolves the
  owning project, and serves the file only when the project is public or the
  caller owns it (`FileResponse`, correct `Content-Type` from stored format).
- URL format stays identical — all stored URLs keep working; older revisions
  remain reachable under the same rules as the project.

Phase 2 — production (Supabase) follow-up:

- Make the bucket private and issue short-lived **signed URLs** on read
  (project GET endpoints and revision listings), or proxy through the same
  gated route. This is a separate, larger change — track as its own issue.

No schema changes required for Phase 1; `storage_path` already exists on every
file record.

## M4 rubric note

Filed as a tracked defect for the milestone's bug-tracking requirement. Status:
Open, fix deferred pending team approval; interim mitigation is documenting
that `/uploads` URLs are bearer URLs.
