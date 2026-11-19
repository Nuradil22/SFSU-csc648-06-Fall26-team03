# M4 Backend Coverage Evidence — Verification Report

Date: 2026-11-16
Branch: `feature/m4-integration`
Commit: `3644f216de352f184d7f727872216b0706501e9a`
Environment: macOS (Darwin 25.6.0), Python 3.13.0, backend venv `app/backend/.venv`
Tooling: `pytest==9.1.1` (pinned in requirements-dev.txt), `pytest-cov` (installed in dev venv for measurement)
Database: disposable test SQLite DB — `env -u TEST_DATABASE_URL` unsets the env var so tests use the throwaway DB (per AGENTS.md; never point TEST_DATABASE_URL at a real DB)

## Command

    cd app/backend
    env -u TEST_DATABASE_URL .venv/bin/python -m pytest -q --cov=app --cov-report=term-missing

## Result

    104 passed in ~25-27s
    TOTAL statement coverage: 2183 stmts, 243 missed -> 89%

## Per-module coverage

| Module | Stmts | Miss | Cover | Missing lines |
|---|---|---|---|---|
| app/__init__.py | 0 | 0 | 100% | |
| app/academic_catalog.py | 41 | 0 | 100% | |
| app/ai.py | 129 | 56 | 57% | 99-103, 170-211, 230, 232, 268, 281, 290-347, 360 |
| app/config.py | 42 | 0 | 100% | |
| app/database.py | 20 | 0 | 100% | |
| app/deps.py | 56 | 11 | 80% | 29-31, 35, 43-45, 68-70, 73 |
| app/main.py | 24 | 1 | 96% | 59 |
| app/migrations.py | 32 | 1 | 97% | 67 |
| app/models.py | 217 | 0 | 100% | |
| app/routers/__init__.py | 0 | 0 | 100% | |
| app/routers/auth.py | 40 | 1 | 98% | 70 |
| app/routers/career_chat.py | 543 | 44 | 92% | 74-75, 90, 151-152, 208-209, 247-248, 284, 324, 327, 343, 376, 400, 579, 749, 758, 825-826, 829-830, 938-1025 |
| app/routers/certificates.py | 27 | 1 | 96% | 13 |
| app/routers/education.py | 29 | 1 | 97% | 13 |
| app/routers/experience.py | 33 | 7 | 79% | 20, 46-51 |
| app/routers/guidance.py | 29 | 0 | 100% | |
| app/routers/job_preferences.py | 27 | 1 | 96% | 14 |
| app/routers/model_compare.py | 130 | 59 | 55% | 95-102, 113-114, 118-150, 154-187, 191-195, 205 |
| app/routers/portfolio.py | 66 | 8 | 88% | 58, 81-85, 94-95 |
| app/routers/projects.py | 186 | 11 | 94% | 26, 37, 142, 184-191, 346, 479 |
| app/routers/public.py | 22 | 1 | 95% | 46 |
| app/routers/skills.py | 38 | 9 | 76% | 17, 25, 52-58 |
| app/schemas.py | 341 | 1 | 99% | 96 |
| app/security.py | 15 | 0 | 100% | |
| app/storage.py | 96 | 30 | 69% | 47, 49, 56, 72-73, 75, 83, 113-121, 124, 131-142, 145-146, 153, 160-161, 172-173 |
| **TOTAL** | **2183** | **243** | **89%** | |

## Frontend tests

    cd app/frontend && node --test src/lib/stl.test.js
    -> 3/3 passed

## Notes

- Test files: tests/test_api.py (17), test_career_chat.py (12), test_career_research.py (28),
  test_collaboration.py (13), test_migrations.py (3), test_model_compare.py (13),
  test_resource_links.py (9). Parameterized cases bring the executed total to 104.
- Machine-readable coverage also captured to /tmp/m4_coverage.json during measurement.

---

## Post-expansion measurement (same environment and command)

After adding provider-level unit tests (tests/test_ai.py, tests/test_storage.py,
and SDK-fake tests appended to tests/test_model_compare.py) plus a one-line fix in
`compare_pair` (whitespace inside `MODEL_COMPARE_PAIR` entries leaked into the
provider name, which would later fail as "Unknown comparison provider"):

    153 passed in ~30s
    TOTAL statement coverage: 2184 stmts, 130 missed -> 94%

| Module | Before | After |
|---|---|---|
| app/ai.py | 57% | 79% (remaining: SDK exception branches, mock plural edge) |
| app/routers/model_compare.py | 55% | 97% (remaining: anthropic regex-fallback inner branch, dispatch lines) |
| app/storage.py | 69% | 99% (remaining: get_storage supabase branch) |
| **TOTAL** | **89%** | **94%** |

Defect found and fixed during test authoring: `compare_pair` parsed
`" OpenAI : gpt-5.1 "` as provider `"openai "` (unstripped whitespace), which
would surface as `503 Unknown comparison provider` at request time. Fixed by
stripping both sides of the `provider:model` partition.
