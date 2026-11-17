# SW Engineering CSC648/848 — Milestone 4: Testing (DRAFT)

**Project:** Projectory
**Section:** 06 — **Team:** 03
**Date:** November 22, 2026
**Final filename (required):** `CSC648-848 Section 06 Milestone4 Team03.PDF`
**Email subject (required):** `CSC648-848 Milestone4 Section 06 Team 03`

**Team members and roles:**
- Rohit — Team lead, integration, 3D functionality
- Nuradil — Backend and integration
- Ian — Frontend design and development
- Obaidullah — AI functionality
- Ali — QA and security
- Fanta — Academic resources and UX

> This draft contains real, re-runable test evidence only. Anything still
> marked TODO needs a human action (final PDF layout, GitHub Issues
> publication, optional browser screenshots) before submission.

---

## 1) QA Testing

### 1.1 Finalized P1 features (from M3 Appendix I, submitted to the instructor)

The M3 Appendix I committed seven P1 feature categories for M5 delivery:

| # | P1 category | M5 acceptance target (as committed) |
|---|---|---|
| P1-1 | Account authentication and authorization | Register, log in/out, validate input and restrict modifications to the authenticated owner |
| P1-2 | Student profile and education history | Create, view and edit biography, interests, education, skills and experience, with saved changes displayed in the portfolio |
| P1-3 | Portfolio and project management | Create, edit, view and discover projects; publish/unpublish portfolios and enforce authorized project access |
| P1-4 | Focused AI academic guidance | Profile- and project-informed recommendations with source-backed suggestions, transparent reasoning, clear provider/error states |
| P1-5 | Recommendation results | Display strengths, development areas, and concrete next steps, distinguishing retrieved source facts from generated suggestions |
| P1-6 | Basic collaborative project feedback | Authenticated likes/comments on projects, displayed to viewers |
| P1-7 | Project/model revision history | Upload and display multiple versions with timestamps and student-written change summaries |

### 1.2 Requirements traceability matrix

| P1 | Implementation files | Unit tests | Integration case | Acceptance evidence |
|---|---|---|---|---|
| P1-1 | `app/routers/auth.py`, `app/security.py`, `app/deps.py`, `app/models.py` (User) | `test_signup_validation`, `test_login_logout`, `test_ownership` (test_api.py) | IT-01 | 5/5 steps PASS (run 2026-11-16) |
| P1-2 | `app/routers/education.py`, `skills.py`, `experience.py`, `certificates.py`, `job_preferences.py`, `portfolio.py` | `test_sections_crud`, `test_certificates_and_job_preferences`, `test_personal_info` | IT-02 | 7/7 steps PASS |
| P1-3 | `app/routers/projects.py`, `portfolio.py` (share), `public.py`, `storage.py` | `test_projects_media_and_models`, `test_sharing`, `test_visibility_discovery_and_owner_isolation`, `test_search_projects`, `test_update_three_fields_persists` | IT-03 | 8/8 steps PASS |
| P1-4 | `app/routers/career_chat.py`, `model_compare.py`, `app/ai.py`, `app/academic_catalog.py` | `tests/test_career_chat.py` (12), `tests/test_career_research.py` (28), `tests/test_resource_links.py` (9), `tests/test_model_compare.py` (30 incl. new provider tests) | IT-04 | 6/6 steps PASS |
| P1-5 | `app/routers/guidance.py`, `app/ai.py` | `test_guidance_mock`, `test_guidance_failure_keeps_previous`, `test_payload_excludes_private_fields`, `test_ai_payload_includes_certificates_not_salary`, `test_ai.py` mock-provider cases | IT-05 | 2/2 steps PASS |
| P1-6 | `app/routers/projects.py` (engagement/like/comment endpoints), `app/models.py` (ProjectLike, ProjectComment) | `tests/test_collaboration.py` like/comment cases (7) | IT-06 | 7/7 steps PASS |
| P1-7 | `app/routers/projects.py` (attach_model, list_model_revisions), `app/models.py` (ProjectModelRevision), `app/storage.py` | `tests/test_collaboration.py` revision cases (6), `tests/test_storage.py` format/validation cases | IT-07 | 5/5 steps PASS |

### 1.3 Ten P1 features selected for unit testing

Ten distinct, testable functionalities within the seven committed categories
(no new product commitments). Each functionality maps to exactly one parent
P1 category:

| # | Functionality | Parent P1 | Units under test | Test file(s) |
|---|---|---|---|---|
| F1 | User registration, login, and token auth (input validation, credential check, 401 on bad login) | P1-1 | `/auth/signup`, `/auth/login`, `get_current_user` | test_api.py |
| F2 | Portfolio section CRUD (education, skills, experience, certificates, job preferences) with owner isolation | P1-2 | `/portfolio/me/*` routers, `get_owned` | test_api.py |
| F3 | Project and portfolio management: create/edit/delete, media/model attachment validation, publish/unpublish, discovery, authorized access | P1-3 | `/projects` router, `/portfolio/me/share`, `_get_viewable_project`, `storage.detect_*` | test_api.py, test_storage.py |
| F4 | Portfolio-completeness gate for the AI advisor (readiness report, missing-item labels, unlock) | P1-4 | `ai.portfolio_readiness`, `/career/readiness` | test_career_chat.py |
| F5 | Source-grounded academic recommendations (web-search domain allowlist, only retrieved URLs kept, blocked domains, link verification) | P1-4 | `career_chat` research pipeline, `resource_links` checker | test_career_research.py, test_resource_links.py |
| F6 | Roadmap proposal lifecycle (draft → approve/reject → per-student isolation → supersede) | P1-4 | `/career/chat`, `/career/proposals/{id}/{decision}`, `/career/roadmap` | test_career_chat.py, test_career_research.py |
| F7 | Two-model comparison with curated-catalog validation (verified/unverified/title mismatch, provider failure reported, never fabricated) | P1-4 | `model_compare.py`, `academic_catalog.py` | test_model_compare.py |
| F8 | Guidance result generation and privacy (summary/paths/strengths/improvements/next_steps; payload excludes private fields) | P1-5 | `ai.generate_guidance`, `ai.build_portfolio_payload`, `ai._mock_guidance`, `/guidance` | test_api.py, test_ai.py |
| F9 | Collaborative project feedback: idempotent likes and comment CRUD with author/owner delete permissions and private-project protection | P1-6 | like/comment endpoints, `ProjectLike`/`ProjectComment` models | test_collaboration.py |
| F10 | Project/model revision history: owner-only uploads, version labels, change notes, current-version tracking, legacy backfill | P1-7 | `attach_model`, `list_model_revisions`, `ProjectModelRevision` model | test_collaboration.py, test_storage.py |

Category coverage of the selection: P1-1 ×1, P1-2 ×1, P1-3 ×1, P1-4 ×4,
P1-5 ×1, P1-6 ×1, P1-7 ×1 — all seven categories are represented and
P1-6/P1-7 are tested as separate functionalities.

**Test directory (GitHub):**
`https://github.com/Nuradil22/SFSU-csc648-06-Fall26-team03/tree/feature/m4-integration/app/backend/tests`
(frontend: `app/frontend/src/lib/stl.test.js`)

### 1.4 Unit-test framework and execution

- Framework: **pytest 9.1.1** (`app/backend`), **node:test** (frontend STL unit)
- Command: `cd app/backend && env -u TEST_DATABASE_URL .venv/bin/python -m pytest -q --cov=app --cov-report=term-missing`
- Test database: disposable SQLite; every test drops/recreates all tables
- Result (latest run, 2026-11-16): **153 passed, 0 failed**
- Frontend: `node --test src/lib/stl.test.js` → 3/3 pass
- Coverage tool: pytest-cov (measured in dev venv)

### 1.5 Coverage analysis

**Statement coverage (measured):** `2184 statements, 130 missed → **94%**`
(rubric target >50%). Per-module table and exact reproduction commands are in
`milestones/m4/COVERAGE_EVIDENCE.md`; the baseline before the M4 test
expansion was 89%. Key modules: `career_chat.py` 92%, `model_compare.py` 97%,
`storage.py` 99%, `projects.py` 94%, `models.py`/`academic_catalog.py` 100%.

**Functional coverage (separate, manual analysis — NOT the measured
statement coverage above):** the fraction of committed P1 acceptance
behaviors exercised by at least one *named, executed* test. Every behavior
below lists its evidence; all tests ran in the 2026-11-16 suite run
(153 passed) and/or the integration transcript.

| Feature | Acceptance behaviors → covering test(s) | Covered |
|---|---|---|
| F1 (P1-1) | signup validation → `test_signup_validation`; duplicate email → `test_signup_validation` + IT-01; login → `test_login_logout` + IT-01; bad login → `test_login_logout` + IT-01; unauthenticated → `test_chat_requires_login`/`test_compare_requires_login` + IT-01; owner-only mutation → `test_ownership` + IT-02/IT-03 | 6/6 |
| F2 (P1-2) | section create/read → `test_sections_crud` + IT-02; validation → `test_sections_crud`; certificates/job prefs → `test_certificates_and_job_preferences`; cross-user isolation → `test_ownership` + IT-02; persisted display → IT-02 | 5/5 |
| F3 (P1-3) | project create/edit/delete → `test_projects_media_and_models`, `test_update_three_fields_persists` + IT-03; image-format detection → `test_detect_image_format_*`; model-format detection incl. .gltf edge cases → `test_detect_model_format_*`; size/empty rejection → `test_read_upload_*`; publish → `test_sharing` + IT-03; unpublish → `test_sharing`; discovery → `test_visibility_discovery_and_owner_isolation` + IT-03; private-project 404 → `test_revisions_public_read_and_private_denied` + IT-03; share-token view → `test_sharing` + IT-03 | 13/13 |
| F4 (P1-4) | readiness report → `test_partial_portfolio_lists_only_what_is_missing_then_unlocks`; missing-item labels → same; blocks before any AI call → `test_incomplete_portfolio_blocks_auto_and_chat_without_any_ai_call`; unlock after completion → same test + IT-04 | 4/4 |
| F5 (P1-4) | allowlist sent/enforced → `test_domain_allowlist_is_sent_and_enforced`; only searched URLs kept → `test_only_urls_returned_by_the_search_are_kept`; blocked domains → `test_blocked_domains_are_never_sources` (+configurable variant); unreachable dropped → `test_unreachable_links_are_dropped_and_good_ones_kept`; no-search mode → `test_disabled_search_sends_no_tools_and_shows_no_links`; ordinary chat never searches → `test_ordinary_chat_does_not_search`; provider failure → `test_api_failure_returns_503_and_stores_no_conversation`; conflicting/outdated-source handling → **no dedicated test** | 7/8 |
| F6 (P1-4) | proposal on demand → `test_roadmap_proposal_approve_flow`; auto-draft once → `test_auto_generates_once_and_refresh_returns_the_same_draft`; approve → `test_roadmap_proposal_approve_flow` + IT-04; reject → `test_roadmap_proposal_reject_flow`; supersede → `test_explicit_request_uses_latest_portfolio_and_supersedes_older_drafts`/`keeps_approved_roadmap_until_replacement_is_approved`; per-student isolation → `test_roadmaps_are_separated_by_account` | 6/6 |
| F7 (P1-4) | both providers called → `test_compare_both_models_validated_and_diffed`; catalog verified/unverified/mismatch → `test_validate_*`; agreement diff → `test_compare_recommendations_*`; provider error surfaced not fabricated → `test_compare_provider_failure_is_reported_not_fabricated`; JSON-in-prose recovery → `test_call_anthropic_extracts_json_wrapped_in_prose`; reasoning-flag/model pairing → `test_supports_reasoning_flag`, `test_compare_pair_*` | 7/7 |
| F8 (P1-5) | result sections populated → `test_guidance_mock` + IT-05; private fields excluded → `test_payload_excludes_private_fields`, `test_ai_payload_includes_certificates_not_salary`; provider failure keeps previous → `test_guidance_failure_keeps_previous` | 3/3 |
| F9 (P1-6) | login required → `test_like_requires_login` + IT-06; idempotent like/unlike → `test_like_unlike_counts_and_idempotency` + IT-06; comment CRUD+delete perms → `test_comments_crud_and_permissions`, `test_comment_owner_can_delete_others`, `test_comment_author_cannot_delete_others`; private-project denial → `test_likes_private_project_hidden_from_others`, `test_comment_validation_and_private_project`; input validation → `test_comment_validation_and_private_project` | 5/5 |
| F10 (P1-7) | history order/labels/current → `test_revisions_history_order_notes_and_current` + IT-07; public read/private denied → `test_revisions_public_read_and_private_denied`; owner-only upload → `test_revision_upload_is_owner_only` + IT-07; legacy backfill → `test_legacy_model_is_backfilled_as_v1`, `test_existing_model_gets_implicit_revision_row`; delete removes revisions → `test_delete_model_removes_all_revisions` | 5/5 |

**Overall functional coverage: 61/62 ≈ 98%** (rubric target ≥90%). The one
uncovered behavior — handling conflicting or outdated retrieved sources — is
documented here as a gap rather than claimed.

### 1.6 Integration testing — test cases and results

Execution method — IMPORTANT SCOPE NOTE: all cases run through FastAPI's
**TestClient** (full HTTP request → routing → auth dependencies → database)
against a local disposable SQLite database. Each case is a real end-to-end
API integration test, not a mocked unit test — but it is **not** a real
browser session and **not** the deployed production (Render/Supabase)
environment. Browser/manual verification is listed separately and is NOT
claimed as executed. Runner: `app/backend/scripts/m4_integration.py`.
Transcript: `milestones/m4/INTEGRATION_RUN.txt`.

**Date executed:** 2026-11-16 (local) / 2026-11-17 UTC — branch
`feature/m4-integration`, disposable SQLite DB, `AI_PROVIDER=mock`.
Frontend/browser steps are listed as manual verification items and are NOT
claimed as executed.

| ID | P1 | Description | Prerequisites | Test data | Steps (abbrev.) | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|---|
| IT-01 | P1-1 | Registration and login enforce validation and credentials | clean DB | sam@sfsu.edu / password123 | signup→201; duplicate→409; login→token; wrong password→401; no token→401 | All statuses as listed | 5/5 matched | **PASS** |
| IT-02 | P1-2 | Portfolio sections save and display to owner only | logged-in owner + peer | education, skill, internship, certificate | POST each section→201; GET /portfolio/me shows all; peer PATCH affects only peer | Owner portfolio shows 4 sections; owner bio unchanged | 7/7 matched | **PASS** |
| IT-03 | P1-3 | Project CRUD, publish, discovery, authorized access | owner+peer accounts | project "Rover Chassis" | create→201; peer GET private→404; share on→token; peer public view→200; browse lists; peer PATCH→404 | Private hidden, public discoverable after publish | 8/8 matched | **PASS** |
| IT-04 | P1-4 | AI advisor gate + chat + roadmap proposal lifecycle | complete portfolio (IT-02 data + job pref + project) | "What should I learn next?", "Make me a roadmap" | incomplete→not ready; chat→reply; roadmap→proposal_id; roadmap null until approve; approve→active | Proposal requires explicit approval; roadmap served after | 6/6 matched | **PASS** |
| IT-05 | P1-5 | Guidance results structure and persistence | ready portfolio | n/a | POST /guidance→201; fields summary/career_paths/strengths/next_steps present; GET latest→200 | All result sections populated | 2/2 matched | **PASS** |
| IT-06 | P1-6 | Likes and comments on shared project | shared project (IT-03); peer account | comment "Nice chassis tolerances!" | peer like→count 1; repeat like→still 1; comment→201; anonymous like→401; owner deletes→204; unlike→0 | Idempotent likes; author/owner delete rights | 7/7 matched | **PASS** |
| IT-07 | P1-7 | Model revision upload, history, and permissions | shared project (IT-03) | two .glb uploads w/ labels + change notes | v1 upload→200; v2 w/ note→200; peer GET revisions→2 rows, {v1,v2}, note, exactly 1 current; peer upload→404; bad file→400 | Chronological history; owner-only writes | 5/5 matched | **PASS** |

**Coverage:** 7/7 P1 categories tested (100% ≥ 85% requirement); 40/40 steps
passed; **0 failed integration cases** at run time → nothing to file as a
bug-tracker defect from this run.

**Bug tracker:** `https://github.com/Nuradil22/SFSU-csc648-06-Fall26-team03/issues`
Two issues are prepared/identified for filing (see §1.7): the `/uploads`
public-access security issue (draft in repo) and the `compare_pair`
whitespace defect (found and fixed during unit-test authoring; fix commit
`0081429`). TODO: publish to GitHub Issues with assignees (Ali suggested for
the security issue) and record status there — required by the rubric, which
also encourages logging/resolving real issues before the deadline.

### 1.7 Known limitations (honest status, not hidden failures)

- `/uploads` static mount and the public Supabase bucket serve file bytes to
  anyone holding a URL — filed as a security issue (see
  `milestones/m4/UPLOADS_SECURITY_ISSUE.md`). Discovery privacy works
  correctly (IT-03/IT-06/IT-07); file-bytes access does not yet inherit it.
- AI runs on the deterministic mock provider in tests; live OpenAI calls were
  verified manually in an earlier session but are not part of the automated
  suite (cost/network determinism).
- Browser/UI verification is a manual checklist, not automated evidence.

---

## 2) Coding practices

### 2.1 Style

- **Backend (Python/FastAPI):** PEP 8 with type hints on public function
  signatures, module docstrings describing requirement coverage, small router
  functions delegating to helpers (e.g. `_get_viewable_project`), Pydantic
  schemas for every request/response contract. Style is closest to the Google
  Python Style for docstrings.
- **Frontend (React/JSX):** one component + one CSS file per unit under
  `src/components/`; function components with hooks; API calls isolated in
  `src/lib/api.js`; no inline styles.

### 2.2 Enforcement tools

- **Ruff 0.17.5** (backend, `app/backend/ruff.toml`) — conservative rule set
  (`E`, `F`, `W`, `I`; `E501` off to match existing line lengths; `E402`
  allowed in tests/scripts where env vars precede imports). First run found
  6 auto-fixable issues (5 import-ordering, 1 unused import); all fixed,
  `ruff check` now passes clean on `app/`, `tests/`, `scripts/`.
- `oxlint` (npm `lint` script) — JS/JSX static checks; `npm run lint`
  currently 0 errors, 4 pre-existing `no-unused-vars` warnings.
- `node --test` and `pytest` act as behavioral gates; the Vite build
  (`npm run build`) enforces import/syntax integrity.

### 2.3 Source files demonstrating style (≥85% of P1 features — 7/7 listed)

| P1 | Representative source files |
|---|---|
| P1-1 | `app/routers/auth.py`, `app/security.py`, `app/deps.py` |
| P1-2 | `app/routers/education.py`, `skills.py`, `experience.py`, `certificates.py`, `job_preferences.py` |
| P1-3 | `app/routers/projects.py`, `portfolio.py`, `public.py`, `app/storage.py` |
| P1-4 | `app/routers/career_chat.py`, `app/routers/model_compare.py`, `app/ai.py`, `app/academic_catalog.py` |
| P1-5 | `app/routers/guidance.py`, `app/schemas.py` (GuidanceContent) |
| P1-6 | `app/routers/projects.py` (engagement endpoints), `src/components/Projects/ProjectEngagement.{jsx,css}` |
| P1-7 | `app/routers/projects.py` (revision endpoints), `src/components/Projects/ModelRevisions.{jsx,css}`, `app/models.py` |

### 2.4 Optional extra credit (implemented in this branch)

- **CI integration (+10):** `.github/workflows/tests.yml` — triggers on
  pull requests and pushes to `main`/`dev`/`feature/**`. Two jobs:
  `backend` (Python 3.13, `pip install -r requirements-dev.txt`, then the
  same coverage command as §1.4 with `--cov-fail-under=85`) and `frontend`
  (Node 20, `npm ci`, `npm run lint`, `npm run build`,
  `node --test src/lib/stl.test.js`). YAML syntax validated locally; not yet
  pushed/activated — activation happens when the branch is merged.
- **HTML docs from comments (+10):** generated with **pdoc 16.0.0**
  (`python -m pdoc -o milestones/m4/api-docs app`) — 26 HTML files covering
  every P1-1..P1-7 backend module (`app/routers/*`, `app/ai.py`,
  `app/academic_catalog.py`, `app/storage.py`, `app/models.py`, etc.).
  pdoc documents public methods/classes only, matching the rubric.
  Limitation: documents backend Python only — the JSX components have no
  doc-generation tool configured. Open `api-docs/index.html` to browse.

---

## Appendix — evidence artifacts in this folder

- `COVERAGE_EVIDENCE.md` — commands, environment, per-module coverage table
- `INTEGRATION_RUN.txt` — dated transcript of all 40 integration steps
- `UPLOADS_SECURITY_ISSUE.md` — draft GitHub Issue + fix proposal
- `scripts/m4_integration.py` (in `app/backend/scripts/`) — reproducible runner
