# Private Model Protection — Implementation & Migration Plan

Status: **planned, not implemented** (awaiting approval). Prepared for `feature/m4-integration`.

## Problem

1. **Local storage:** `app/main.py` mounts `StaticFiles` at `/uploads` with no authentication. Anyone who learns a file URL can fetch it forever — hiding a portfolio does not revoke known URLs (documented in `UPLOADS_SECURITY_ISSUE.md`).
2. **Supabase storage:** the bucket is created with `"public": True`, so deployed files are publicly fetchable by path as well.
3. **Scope of exposure:** project cover images, 3D model files (`model_path`), and every stored model revision — including files belonging to private portfolios.

## Goals / non-goals

- Protect private project files; keep public sharing working.
- No independent project-visibility state — visibility stays portfolio-wide (`Portfolio.is_public` + share token).
- Backward compatible: existing stored URLs in the DB keep working for authorized viewers.
- No change to STL export behavior: it runs client-side on the loaded GLTF scene, so it only needs the file to load for *authorized* viewers.

## Authorization rule (single source of truth)

A file linked to project `P` is downloadable iff:

- the requester owns `P.portfolio`, OR
- `P.portfolio.is_public` is true, OR
- the request presents a valid share token for `P.portfolio` (covers `/p/{token}` visitors).

Helper: `can_access_project_file(db, project, user, share_token=None) -> bool` in `app/routers/projects.py` (or a small `app/access.py`), reusing the existing share-token validation used by `GET /public/share/{token}`.

## Phase 1 — local `/uploads` gating (URL-compatible)

1. Remove `app.mount("/uploads", StaticFiles(...))` in `main.py`.
2. Add route `GET /uploads/{path:path}` in a new router (e.g. `app/routers/uploads.py`):
   - Look up which project owns the file: `Project.model_path`, `Project.image_path`, and `ModelRevision.file_path` all store `/uploads/...` URLs — resolve `path` against all three columns.
   - If no row references the path → 404 (orphaned/unknown files stay private by default).
   - If the referencing project's portfolio is public → serve via `FileResponse`.
   - If private → require `Authorization` bearer; owner only → 200, else 404 (404 not 403 to avoid existence leaks).
   - Share-token viewers: accept `?token=` query param on the URL when the file's project belongs to a shared public portfolio. (Public portfolios are already served without a token, so this mainly preserves deep links while a portfolio is private→shared.)
3. File lookup must cover **revisions**: `ModelRevision.file_path` URLs are stored values, so gating by path automatically protects historical versions — no per-revision flag needed.
4. Public shared portfolios: `GET /public/share/{token}` returns project JSON containing `/uploads/...` URLs; those files resolve to public projects and are served — no frontend change.
5. STL export: `ModelViewer` fetches the model URL; for a private project the owner is authenticated, but `<GLTFLoader>` fetches are not sent with the bearer header. Handle by minting short-lived signed file URLs instead of relying on cookies — see "signed URL approach" below; Phase 1 can accept `?token=` (the user's JWT as query param is **not** acceptable — tokens in URLs leak via logs/history). **Decision needed:** preferred approach is that the frontend requests `GET /projects/{id}/file-url?path=…` which returns a short-lived single-use `?sig=` URL (HMAC of path+expiry+project, keyed on `SECRET_KEY`), and `ModelViewer` uses that. Same mechanism reused for shared-portfolio viewers.

## Phase 2 — Supabase private bucket + signed URLs

1. Create the bucket with `public: False` (change `app/storage.py` bucket-create options; existing bucket can be flipped via Supabase dashboard or a one-off script — no data move needed since paths stay the same).
2. All reads go through the same authorization rule: backend generates **signed download URLs** (`create_signed_url`, ~15 min TTL) at serialize time — `ProjectOut.model_url`/`image_url`/`revisions[].url` become signed URLs rather than raw public URLs.
3. Signed URLs also solve the Phase-1 viewer problem uniformly: `ModelViewer` just loads whatever URL the API returns.
4. Writes unchanged (service-role key stays server-side).

## Legacy files & deployed links

- URLs stored in DB (`/uploads/xxx`, Supabase public URLs) do not change in Phase 1 — route shape is identical, so existing data needs no migration.
- Supabase public-object URLs embedded in DB rows (`https://<proj>.supabase.co/storage/v1/object/public/<bucket>/<path>`): after flipping the bucket private these 404 publicly; the API must translate stored public URLs → signed URLs when serializing (parse bucket+path, call `create_signed_url`). Add a serializer helper `to_file_url(stored_url, project, db, user)`.
- **Rollback:** Phase 1 is a code-only change — revert restores the static mount. Phase 2: flipping the bucket back to public restores prior behavior instantly; keep a documented dashboard/API toggle in the runbook.

## Test cases (to be added with the implementation)

Local backend (`storage_backend=local`):

1. Owner `GET` own private project file → 200.
2. Anonymous `GET` private project file URL → 404.
3. Authenticated non-owner `GET` private project file → 404.
4. Anonymous `GET` public-project file → 200.
5. Non-owner `GET` public-project file → 200.
6. Toggle portfolio public→private: previously-known URL now returns 404 for non-owner (revocation works).
7. Old revision file of a private project → 404 for non-owner, 200 for owner.
8. Shared-portfolio visitor (valid token, public portfolio) → project file 200; after `DELETE /portfolio/me/share` → 404.
9. Signed file URL (`?sig=`): valid signature 200; tampered/expired → 404; signature for file A cannot fetch file B.
10. Orphan path (no DB row references it) → 404 for everyone.
11. Path traversal (`/uploads/../app/config.py`, URL-encoded variants) → 404/400; `FileResponse` resolved inside `upload_dir` only.
12. STL export unaffected: authenticated owner loads model → export produces same triangles as before (frontend STL test unchanged; manual check).

Supabase path (mocked storage client, as in `tests/test_storage.py` style):

13. `to_file_url` returns a signed URL for an authorized viewer and is not called for unauthorized (404 before signing).
14. Bucket create options assert `public: False`.

## Ordering

1. Phase 1 + tests (local backend; also protects dev/demo).
2. Serializer + signed URLs (works for both backends — prerequisite for private Supabase reads).
3. Phase 2 bucket flip on staging; validate; flip production.
4. Publish `UPLOADS_SECURITY_ISSUE.md` to GitHub Issues once the fix is on a branch.

## Risks

- **Path→project resolution cost** per file request: one indexed query over three columns; acceptable at this scale (could cache later).
- **Orphaned files become unreachable** — intended (fail closed); note in rollout that any file not referenced by a project row is private by default.
- **`?sig=` URLs in shared HTML/logs** — short TTL (≤15 min) limits replay; same exposure class as Supabase signed URLs.
