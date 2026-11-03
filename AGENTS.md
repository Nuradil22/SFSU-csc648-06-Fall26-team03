# Local verification

- Frontend: `cd app/frontend && npm run build`, `npm run lint`, and `node --test src/lib/stl.test.js`.
- Backend: use `app/backend/.venv`; install the pinned `requirements-dev.txt` before running tests. From `app/backend`, run `env -u TEST_DATABASE_URL .venv/bin/python -m pytest -q` to use the disposable test SQLite database. The test suite drops/recreates tables: never point `TEST_DATABASE_URL` at an existing database.
- Local application database: `app/backend/careergps.db`. Preserve existing data.
- Portfolio-wide visibility already uses authenticated GET/POST/DELETE `/portfolio/me/share`; public `/projects` filters `Portfolio.is_public`. Do not introduce independent project visibility state.
- Uploaded models are displayed by the shared `ModelViewer` component. STL export uses the loaded GLTF scene, not the viewer's lights or controls. STL is a unitless triangle mesh, not parametric CAD.
- Local `/uploads` is currently static file serving; hiding a portfolio does not revoke previously known uploaded-file URLs.
