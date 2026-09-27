# Project Context — WorkOS

> **Read this first.** This file is the entry point for any new session. It answers:
> *where are we, what has been decided, what does the next iteration look like, and what
> must the human do manually?*
>
> Written for an AI assistant picking the project up cold, and equally useful to a human
> skimming before a session. **Detailed teaching material lives in `docs/`, not here** — this
> file is orientation, not a tutorial.
>
> Last updated: end of Iteration 01.

---

## 1. What this project is

A **multi-tenant SaaS project management platform** built from scratch as a deliberate
learning project. Companies (organizations) create workspaces, invite users, manage projects,
and control access through roles and permissions.

**The defining constraint:** users in Organization A must never see or touch Organization B's
data, and that guarantee must come from the backend architecture plus tests — never from
frontend checks.

**The defining method:** teaching-first, one learning unit at a time. Explain concepts → design
→ implement a small piece → explain the code → test → document → **stop and wait for `continue`**.

## 2. Current status

| | |
| --- | --- |
| **Iteration** | 01 of 24 — **complete** |
| **Branch** | `main` |
| **Last commit** | `9b918a9 chore: bootstrap project foundation` |
| **Working tree** | clean |
| **Remote** | **none configured** — see §9 |
| **Last verified** | `4 passed`, `ruff check` clean, `ruff format --check` clean, server responds `200` on `/api/v1/health` |

**What exists right now:** a runnable FastAPI service, a layered folder skeleton, typed
settings from the environment, one health endpoint, and 4 tests. **No database yet. No models.
No auth.** Those start in Iteration 02.

## 3. The roadmap (summary — full version in `docs/00-roadmap.md`)

```text
Phase 1  01 Foundation ✅
         02 Database / SQLAlchemy / Alembic      ← NEXT
         03 User model + schemas

Phase 2  04 Password hashing
         05 Registration
         06 Login + JWT
         07 Refresh tokens + rotation
         08 Auth dependencies
         09 Email verification / password reset

Phase 3  10 Organizations + membership
         11 Tenant isolation (IDOR)   ← highest-stakes iteration in the project
         12 Roles & permissions
         13 Permission enforcement + admin APIs
         14 Invitations

Phase 4  15 Google OAuth
         16 Projects & tasks

Phase 5  17 Redis: caching + rate limiting
         18 Security hardening (CORS, headers, log hygiene)
         19-22 Next.js frontend (foundation, auth UI, dashboard, admin/projects)

Phase 6  23 Docker + deployment
         24 CI/CD + observability
```

Each iteration is one learning unit and has explicit prerequisites. **Do not skip or reorder.**

## 4. Architecture and the rules that govern it

```text
Browser (Next.js)
   │  HTTPS /api/v1/*
   ▼
FastAPI
   api/            routes, validation, HTTP status codes
     └─ services/        business rules, zero HTTP knowledge
         └─ repositories/  ALL queries, ALL tenant scoping
             └─ models/     SQLAlchemy tables
   core/           config, security, logging
```

**Invariants — breaking these is a bug, not a style preference:**

1. **Dependencies point downward only.** A route never imports a repository; a repository
   never imports a service. Services receive repositories via dependency injection.
2. **All tenant data access goes through `repositories/`** and every such method takes
   `organization_id` as a required argument. This is what makes Iteration 11 isolation
   structural rather than a thing we remember to type.
3. **Authorization is always backend-side.** The frontend hides buttons; the API enforces rules.
4. **Never expose ORM models directly** — every route declares a Pydantic `response_model`.
   This is the most common real-world path to leaking password hashes.
5. **No secrets in code.** Environment variables only, via `app/core/config.py`.
6. **Every route ends in a deliberate `response_model`,** not a `dict`.

## 5. Decisions made, and why

| Decision | Reasoning |
| --- | --- |
| `work-os` is its **own** git repo | It sits inside a `~/Desktop` git repo tracking unrelated projects. The user chose isolation. |
| **`uv`** instead of `pip` + `venv` + `pip-tools` | One tool for env, install, and locking. `uv.lock` is committed for reproducible builds. |
| **Python 3.13**, pinned via `backend/.python-version` | The default `python3` on this machine is **3.9.6** (macOS system Python) — too old and causes dependency friction. Never use bare `python3` here. |
| **`create_app()` factory**, not a module-level `app` | So tests can build an app with different settings. This is also why `create_app(settings=...)` takes settings as a *parameter*. |
| **`get_settings()` wrapped in `@lru_cache`** | Parses `.env` once per process, not per request. |
| `environment` typed as `Literal[...]` | `ENVIRONMENT=prod` crashes at startup rather than silently skipping production branches. |
| Versioned routes under `/api/v1` | `/api/v1` is a **code constant, not config** — a path prefix is part of the API contract, and per-environment prefixes would make docs and frontend wrong somewhere. |
| Folders created **only when needed** | `models/`, `schemas/`, `services/`, `repositories/`, `db/`, `alembic/`, `frontend/` do not exist yet. Empty folders accumulate dead code. |
| `docs/NN-topic.md` written at the **start** of each iteration | The user asked for docs-first; writing the concept explanation before code prevents rationalising a design after the fact. |

## 6. Current file map

```text
work-os/
├── README.md                        project + architecture overview
├── PROJECT_CONTEXT.md               this file — session orientation
├── AGENTS.md                        pointer to this file (auto-discovery)
├── .gitignore                       .env, .venv, node_modules, build output
├── docs/
│   ├── 00-roadmap.md                24-iteration plan + dependency graph
│   └── 01-project-foundation.md     Iteration 01 teaching doc
│                                    (§9.1 logs a real bug the tests caught)
└── backend/
    ├── pyproject.toml               deps + ruff/pytest config
    ├── uv.lock                      committed
    ├── .env.example                 config contract, no secrets
    ├── .env                         local only, git-ignored
    ├── app/
    │   ├── __init__.py              __version__ = "0.1.0"
    │   ├── main.py                  create_app() factory, mounts /api/v1
    │   ├── core/config.py           Settings(BaseSettings)
    │   └── api/v1/
    │       ├── router.py            aggregates v1 routers
    │       └── health.py            GET /api/v1/health (liveness only)
    └── tests/
        ├── conftest.py              settings + client fixtures
        └── test_health.py           4 tests
```

## 7. How to run and verify

```bash
cd backend
uv sync                      # create/patch .venv
uv run pytest                # 4 passed
uv run ruff check .          # lint
uv run ruff format --check . # format check
uv run uvicorn app.main:app --reload
```

- <http://127.0.0.1:8000/api/v1/health>
- <http://127.0.0.1:8000/docs> — auto-generated interactive API docs

**End of every iteration, all four must pass:** `pytest`, `ruff check`, `ruff format --check`,
and a real HTTP request against a running server.

## 8. Environment facts (verified — save yourself the discovery)

| Fact | Detail |
| --- | --- |
| `python3` on PATH | **3.9.6 — do not use.** Use `uv run ...` from `backend/`. |
| `uv` | 0.12.19, installed |
| Python pinned for backend | **3.13** (`backend/.python-version`) |
| **Docker** | CLI 29.2.1 installed, **daemon NOT running**. Iteration 02 is the first to need it. |
| Node / npm | v24.13.1 / 11.8.0 |
| `psql` client | 15.17 (no server running; Docker will provide it) |
| Known benign warning | Starlette: `httpx` with `testclient` is deprecated, suggests `httpx2`. Harmless for now; revisit if it breaks. |
| `readme` in `pyproject.toml` | Must be **inside** `backend/`, not `../README.md` — hatchling errors otherwise. Field was removed. |

## 9. Requires manual human action

Nothing is blocked right now. Two things the **human** must do, and an AI must never fake:

1. **Docker Desktop** — install and launch; verify with `docker info`. Needed at Iteration 02.
2. **Git remote** — no `origin` is configured. To push:
   ```bash
   cd /Users/gauravrathore/Desktop/full-stack/work-os
   git remote add origin <url>
   git push -u origin main
   ```
   The user must create the repo on GitHub and supply the URL.

**Later, still manual (flag them when their iteration arrives, never earlier):** Google Cloud
Console OAuth credentials (Iter 15), an email provider (Iter 09+), production database and
hosting credentials (Iter 23), GitHub Actions secrets (Iter 24).

## 10. Working agreements for AI sessions

- **Stop at the end of every iteration.** Never chain iterations. Wait for `continue`.
- **Docs before code** — write `docs/NN-*.md` concept sections first.
- **Explain before implementing**; explain the implementation again after.
- **Never** generate secrets, claim manual steps were done, or put a secret in source.
- **Every iteration ends with at least one new test.** List what to test and why before
  writing it.
- **When something breaks:** understand the error → identify the layer → explain the cause →
  inspect code → **smallest** fix → retest → explain why the fix works. Do not rewrite.
  Never weaken an assertion to make a test pass — fix the design instead.
- **Comments explain *why*, never *what*.** No "# Import FastAPI". No AI-narrating comments.
- **Commits are meaningful**, conventional-commit style: `feat:`, `fix:`, `chore:`, `docs:`.
- Close every iteration with: what to read first, how to test it manually, and a few questions
  the human should be able to answer. **Do not proceed until they can.**

## 11. Next session — start here

1. Read this file, then `docs/00-roadmap.md`.
2. Run `cd backend && uv run pytest && uv run ruff check .` to confirm a clean baseline.
3. Check whether Docker is running (`docker info`) — Iteration 02 needs it.
4. Write `docs/02-database-and-migrations.md` (concept sections first).
5. Implement Iteration 02, test, document, commit, and **stop**.

### Iteration 02 scope reminder

PostgreSQL in Docker, SQLAlchemy 2.0 async engine + session, declarative base, Alembic, the
first real migration, and a **readiness** endpoint (distinct from the existing liveness
`/health`) that actually pings the database.

Concepts to teach before using them: what an ORM is, declarative vs core, engine vs session,
connection pooling, the transaction/session lifecycle, **async** SQLAlchemy and why we chose
it, `create_all()` vs migrations, and why `Alembic` rather than editing tables by hand.

Dependencies to add: `sqlalchemy[asyncio]`, `asyncpg`, `alembic`. Compose file at
`backend/docker-compose.yml` (db only — Redis arrives in Iteration 17).

---

## Progress log

| Iter | Topic | Status | Commit |
| --- | --- | --- | --- |
| 01 | Project foundation | ✅ complete | `9b918a9` |
| 02 | Database, SQLAlchemy, Alembic | ⬜ next | — |
| 03 | User model + schemas | ⬜ | — |
| 04 | Password hashing | ⬜ | — |
| 05 | Registration API | ⬜ | — |
| 06 | Login + JWT access tokens | ⬜ | — |
| 07 | Refresh tokens + rotation | ⬜ | — |
| 08 | Auth dependencies / current user | ⬜ | — |
| 09 | Email verification + password reset | ⬜ | — |
| 10 | Organizations + membership | ⬜ | — |
| 11 | **Tenant isolation / IDOR** | ⬜ | — |
| 12 | Roles & permissions | ⬜ | — |
| 13 | Permission enforcement | ⬜ | — |
| 14 | Invitations | ⬜ | — |
| 15 | Google OAuth | ⬜ | — |
| 16 | Projects & tasks | ⬜ | — |
| 17 | Redis: caching + rate limiting | ⬜ | — |
| 18 | Security hardening | ⬜ | — |
| 19 | Frontend foundation | ⬜ | — |
| 20 | Auth screens + client tokens | ⬜ | — |
| 21 | Dashboard + org switcher | ⬜ | — |
| 22 | Admin UI + projects UI | ⬜ | — |
| 23 | Docker + deployment | ⬜ | — |
| 24 | CI/CD + observability | ⬜ | — |

**Update this file at the end of every iteration** — status row, file map, decisions table,
environment facts, and the "next session" section.
