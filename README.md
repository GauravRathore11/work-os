# WorkOS

A **multi-tenant SaaS project management platform**, built from scratch as a learning project.

Companies (organizations) sign up, create workspaces, invite people, and manage projects.
What each person is allowed to do is controlled by roles and permissions — and enforced on
the **backend**, never in the browser.

> **Status:** Iteration 01 of 24 — project foundation.
> See [`docs/00-roadmap.md`](docs/00-roadmap.md) for the full plan and
> [`docs/01-project-foundation.md`](docs/01-project-foundation.md) for the current iteration.

---

## Why this project exists

Most tutorials give you a finished app to copy. This one is built **one learning unit at a
time**, with the reasoning written down before the code exists. The goal is not to finish the
project. The goal is for you to be able to explain, debug, modify, and extend it yourself.

Three things make this different from a tutorial:

1. **Tenancy is architectural, not decorative.** Isolation between organizations is enforced
   in the repository layer, where every query is scoped by `organization_id`. It is proven by
   cross-tenant tests, not by convention.
2. **Authentication is built, not delegated.** No Auth0, no Clerk, no Firebase Auth. Password
   hashing, JWTs, refresh rotation, and Google OAuth are implemented so the mechanics are
   visible.
3. **Every iteration ends in tests and documentation.** A feature with no test is a feature you
   cannot safely change.

---

## Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | Next.js + TypeScript + Tailwind + shadcn/ui | File-based routing, server components, first-class TS |
| Backend | Python + FastAPI | Dependency injection built in, Pydantic validation shared with the schemas, fast to write and read |
| Validation | Pydantic v2 | One schema definition produces the OpenAPI schema, the docs, and runtime validation |
| ORM | SQLAlchemy 2.0 | Typed queries, explicit transactions, mature |
| Migrations | Alembic | Versioned schema changes — the only safe way to evolve a live database |
| Database | PostgreSQL | Row-level constraints, real transactions, JSONB, proper indexing |
| Cache / broker | Redis | Token denylist, rate limiting, short-lived caching |
| Infra | Docker + Compose | The same Postgres locally and in production |
| Auth | Argon2 + JWT + Google OAuth | Implemented here, not outsourced |
| Tests | pytest + TestClient | In-process, milliseconds, no server needed |

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│  Browser (Next.js)                                               │
│  login · register · dashboard · org switcher · admin · projects │
└──────────────────────────────┬───────────────────────────────────┘
                               │  HTTPS — /api/v1/*
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  FastAPI                                                         │
│                                                                  │
│   api/          routes, validation, HTTP status codes           │
│     └── services/       business rules — no HTTP knowledge      │
│           └── repositories/  ALL queries, ALL tenant scoping    │
│                 └── models/     SQLAlchemy tables               │
│                                                                  │
│   core/         config, security primitives, logging            │
└───────┬──────────────────────────────┬──────────────────────────┘
        │                              │
        ▼                              ▼
┌───────────────┐              ┌──────────────────┐
│  PostgreSQL   │              │  Redis           │
│  source of    │              │  denylist, rate  │
│  truth        │              │  limits, cache   │
└───────────────┘              └──────────────────┘
```

**The rule that matters:** dependencies point downward only. A route never imports a
repository; a repository never imports a service. This is what makes tenant isolation in
iteration 11 a property of the architecture rather than something we have to remember.

---

## Repository layout

```text
work-os/
├── docs/                     # Teaching docs, one file per iteration
│   ├── 00-roadmap.md
│   └── 01-project-foundation.md
├── backend/
│   ├── app/
│   │   ├── main.py           # Application factory
│   │   ├── core/             # Config, security, logging
│   │   └── api/v1/           # Versioned routers
│   ├── tests/
│   ├── pyproject.toml        # Dependencies + tool config
│   └── .env.example
└── frontend/                 # Created in iteration 19
```

`models/`, `schemas/`, `services/`, `repositories/`, and `db/` **do not exist yet.** Each is
created in the iteration that first needs it — empty folders are how projects collect dead code.

---

## Getting started

### Prerequisites

- **Python 3.12+** — managed via [`uv`](https://docs.astral.sh/uv/) (`brew install uv`)
- **Node.js 20+** — needed from iteration 19
- **Docker Desktop** — needed from iteration 02

### Backend

```bash
cd backend
uv python pin 3.13          # create .python-version
uv sync                     # create .venv and install everything
uv run uvicorn app.main:app --reload
```

Then open:

- <http://127.0.0.1:8000/api/v1/health> — the health endpoint
- <http://127.0.0.1:8000/docs> — interactive API documentation

### Tests and linting

```bash
cd backend
uv run pytest                        # run the test suite
uv run ruff check .                  # lint
uv run ruff format .                 # format
uv run ruff format --check .         # verify formatting (used in CI)
```

### Configuration

```bash
cd backend
cp .env.example .env
```

`.env` holds your real values and is **git-ignored**. `.env.example` is committed and contains
only placeholder keys — it is the documentation of which settings exist.

---

## Documentation

Every iteration ships a document at `docs/NN-topic.md` containing: what we are building, why,
the concepts explained before use, an architecture diagram, the request/response flow, the
manual steps you must perform yourself, the implementation, security considerations, the
testing strategy, and a summary of what you learned.

Start with [`docs/00-roadmap.md`](docs/00-roadmap.md).

---

## Security posture

Security is a first-class concern, not a final phase. Threats are named and addressed as we
build, not retrofitted.

- Passwords hashed with **Argon2id**, never stored or logged
- Short-lived **JWT access tokens**; **refresh tokens rotated on use** with reuse detection
- **Tenant isolation enforced in the repository layer** and proven by cross-tenant tests
- **Permission checks on the backend** — the frontend hides buttons, the API enforces rules
- Input validated by Pydantic; output validated by `response_model`
- Secrets from the environment only; `.env` never committed

---

## License

Personal learning project.
