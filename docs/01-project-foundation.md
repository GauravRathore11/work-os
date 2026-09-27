# Iteration 01 — Project Foundation

> **Status:** complete
> **Goal:** a running FastAPI service, a clean layered folder structure, config that comes from
> the environment, and a test suite you can run — all in a Git repository with meaningful history.

---

## 1. What are we building?

Today we build almost no *product*. We build the **house the product will live in**.

Concretely, by the end of this iteration you will have:

- A Git repository with a clean history.
- A folder layout that separates HTTP, business logic, and data access.
- A FastAPI application that starts and answers `GET /health`.
- Configuration read from environment variables, not hard-coded.
- One passing test and one linter run.

That sounds small. It is deliberately the smallest thing that is still *real*, because every
later iteration drops code into these folders. If the foundation is wrong, iteration 11
(tenant isolation) becomes dangerous.

---

## 2. Why do we need it?

Three real problems this solves:

**1. "It works on my machine."** If the database URL is written directly in the code, the app
only runs on your laptop. Configuration must come from the *environment* so the same image runs
in dev, staging, and production with different values and no code changes.

**2. The "one giant file" trap.** Many beginner projects end up as a single `main.py` with
800 lines. By the time you discover you need to change how a query is built, you cannot find
it. Separating concerns early is cheaper than untangling later.

**3. No safety net.** Code that cannot be tested is code you are afraid to change. We wire up
pytest and ruff *now*, while there is one test, so adding the second test is trivial.

---

## 3. Concepts

### 3.1 Virtual environment

A virtual environment is an isolated copy of Python's standard library plus the packages *you*
installed, living in a project folder instead of the machine-wide Python.

**Why it matters:** if project A needs `pydantic 1.x` and project B needs `pydantic 2.x`,
installing both into system Python makes one of them break. Virtual environments make each
project's dependencies independent.

We are using **`uv`** to manage this. `uv` replaces three traditional tools:

| Traditional | uv equivalent |
| --- | --- |
| `python -m venv .venv` | `uv venv` (usually automatic) |
| `pip install X` | `uv add X` |
| `pip freeze > requirements.txt` | `uv.lock` (automatic, more precise) |

`uv.lock` records the *exact* resolved version of every package, including transitive
dependencies. `requirements.txt` written by hand usually does not.

### 3.2 `pyproject.toml`

The modern single file that declares: project metadata, the Python version required, and the
dependencies. `requirements.txt` is the older way; `pyproject.toml` also carries tool config
(ruff, pytest), which is why we use it.

### 3.3 Layered architecture

We split the backend into layers. Each layer has **one** job and is only allowed to talk to the
layer directly beneath it.

```
        HTTP request
             │
             ▼
    ┌─────────────────┐
    │  api/  (routes) │   "Translate HTTP to Python and back"
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   services/     │   "Business rules. Knows nothing about HTTP."
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ repositories/   │   "Talk to the database. No business rules here."
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  models/ (ORM)  │   "The shape of the tables."
    └─────────────────┘
```

**Why this matters enormously for this specific project:** tenant isolation (iteration 11) is
enforced *in the repository layer*. Every query that touches tenant data goes through a
repository method that takes `organization_id` as a required argument. By the time iteration 11
arrives, isolation is a property of the architecture rather than something we remember to type.

**The one rule that keeps layers honest:** a route may not import from `repositories/`, and a
repository may not import from `services/`. Dependencies point downward only. We will use
FastAPI's dependency injection to hand a repository *into* a service, which is how we avoid the
layering being violated in practice.

### 3.4 Application factory pattern

`main.py` will not be one global `app = FastAPI()` at import time. Instead it will be a
`create_app()` **function** that builds and returns the app.

**Why:** as the project grows you will need more than one app — the real one, and a test app
with different settings. A factory makes "build an app with these settings" a normal operation
instead of a hack.

### 3.5 Environment variables and twelve-factor config

Config differs per environment: dev uses `localhost`, production uses a real hostname. The
**12-factor app** methodology says config comes from the environment, not from code.

- **`.env`** — your real, local, secret values. **Never committed.** In `.gitignore`.
- **`.env.example`** — the same keys with placeholder values, no secrets. **Committed.** It is
  the documentation of what config exists.
- Environment variables — in production, injected by the platform (Docker, Heroku, K8s).

We read them with **`pydantic-settings`**, which turns env vars into a validated, typed object.
If a required variable is missing, the app **fails at startup** instead of crashing at 2am
during a request.

### 3.6 Health endpoint

`GET /health` answers "is this process alive and is the app wired up?" It is what Docker,
Kubernetes, and a load balancer poll. It should be **fast and dependency-free** — we will add a
database-backed readiness check in iteration 02, and that will be a *different* endpoint.

### 3.7 `uvicorn`

FastAPI is a library; it does not serve HTTP by itself. **Uvicorn** is an ASGI server — the
actual HTTP server that runs the app. You will meet **ASGI** properly in iteration 02, but the
short version: ASGI is the standard Python interface for async web servers, and FastAPI speaks it.

### 3.8 Ruff and pytest

- **Ruff** — a linter and formatter, written in Rust, extremely fast. It catches real bugs
  (unused imports, shadowed builtins) and enforces formatting so we never argue about style.
- **pytest** — the test framework. A test is a function that asserts. We run them with `uv run pytest`.

---

## 4. Architecture

```text
                    ┌──────────────────────────────┐
  HTTP request ────▶│  uvicorn (ASGI server)      │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  app/main.py                 │
                    │  create_app()                │
                    │  · reads Settings            │
                    │  · includes v1 router        │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  app/api/v1/                 │
                    │  router.py ──▶ health.py     │
                    │  (grouping)    (endpoints)   │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  app/core/config.py          │
                    │  Settings(BaseSettings)      │
                    │  reads .env + os.environ     │
                    └──────────────────────────────┘
```

---

## 5. Request/Response flow

```text
GET /health
      │
      ▼
uvicorn receives the raw HTTP bytes
      │
      ▼
create_app()'s app matches the path to app/api/v1/health.py :: health_check()
      │
      ▼
health_check() calls get_settings()      ← dependency injection
      │
      ▼
Settings loaded from environment (cached, not re-read per request)
      │
      ▼
return HealthResponse(name=..., version=..., environment=...)
      │
      ▼
FastAPI validates the response against the Pydantic model  ← response_model
      │
      ▼
uvicorn serialises to JSON → HTTP 200
```

Note line "response validation": FastAPI checks the returned object against the declared
Pydantic model. This catches a bug where a route accidentally returns an internal object with a
secret field. It is a security feature, not just a typing nicety.

---

## 6. Manual steps you must perform

```text
MANUAL ACTION REQUIRED
```

**1. Install Docker Desktop** (needed in iteration 02, not yet, but start now)

1. Go to <https://www.docker.com/products/docker-desktop/>
2. Download for macOS (Apple Silicon) and drag to Applications.
3. Launch it. The menu bar icon must read "Docker Desktop is running".
4. Verify: open a terminal and run `docker info`. It should print a long block of server info.

```bash
docker info
```

**2. Create your first commit identity** (only if you have not already)

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

**3. Nothing else.** No API keys, no cloud accounts, no OAuth credentials are needed yet. Those
arrive in iteration 15 and I will stop and walk you through Google Cloud Console at that moment.

---

## 7. Implementation — the files

| File | Responsibility | Why here |
| --- | --- | --- |
| `.gitignore` | Keeps secrets, venvs, and build output out of Git | Root of repo, applies to both backend and frontend |
| `README.md` | Entry point: what the project is, how to run it | Convention — people land here first |
| `docs/00-roadmap.md` | The full iteration plan | The plan is a document, not a thought |
| `docs/01-project-foundation.md` | This file | Teaching record of the iteration |
| `backend/pyproject.toml` | Dependencies, Python version, ruff + pytest config | Single source of dependency truth |
| `backend/.env.example` | The contract of what env vars exist | Committed documentation of config |
| `backend/app/main.py` | Application factory, assembles the app | One place that knows the whole app |
| `backend/app/core/config.py` | Typed, validated settings | Config logic in one place, testable |
| `backend/app/api/v1/router.py` | Aggregates v1 routers | Lets us mount `/api/v1` as a prefix |
| `backend/app/api/v1/health.py` | The `/health` endpoint | A real, testable endpoint |
| `backend/tests/conftest.py` | Shared pytest fixtures | Test setup reused across all tests |
| `backend/tests/test_health.py` | First API test | Proves the whole chain works |

### Folders deliberately **not** created yet

`app/models/`, `app/schemas/`, `app/services/`, `app/repositories/`, `app/db/`, `alembic/`,
`frontend/` do not exist. Creating empty folders is how projects accumulate dead code. Each gets
created in the iteration that first needs it, and you will see the reason in that doc.

---

## 8. Security considerations

Nothing in this iteration is clever, but four decisions matter:

1. **`.env` is gitignored, `.env.example` is not.** If you commit `.env` with a real secret, that
   secret is in your history forever, even after you delete the file. Rotation is the only real
   fix. Be paranoid: `git add .env` should never be something you have to undo.
2. **Config is validated at startup, not at request time.** A missing `DATABASE_URL` should kill
   the process on boot, where your deploy tooling notices, not on the first request a user makes.
3. **CORS is not enabled yet.** We will configure it explicitly in iteration 18. A default of
   `allow_origins=["*"]` with credentials is a real vulnerability, and doing it later means
   doing it deliberately.
4. **`response_model` on every route.** Prevents an internal object (a user row with a password
   hash) from being serialised into a response by accident. This is the single most common way
   password hashes leak in real applications.

**No secrets are in this codebase at all yet.** When we add a JWT signing key, it will come
from the environment and `.env.example` will show a placeholder.

---

## 9. Testing

**What we test:** that `GET /health` returns 200 and the shape we declared.

**Why:** it exercises the entire chain — app factory, router mounting, dependency injection,
response model validation, JSON serialisation. It is a smoke test with real value.

**How:** FastAPI's `TestClient`, which runs the ASGI app in-process. No server, no network, no
port. It runs in milliseconds, which is what makes people actually write tests.

```bash
cd backend
uv run pytest
```

### The rule we will follow from now on

**Every iteration ends with at least one new test.** A feature with no test is a feature we
cannot change safely. The auth iterations will add the security cases you listed — expired
token, revoked refresh token, cross-tenant access, insufficient permissions — because those are
exactly the cases a human forgets to check manually.

---

## 9.1 Debugging log — a real bug this iteration caught

`test_openapi_schema_is_generated` failed on the first run:

```text
AssertionError: assert 'WorkOS API' == 'WorkOS API Test'
```

**1. Understand the error.** The test injected `Settings(app_name="WorkOS API Test")`, but the
OpenAPI title said `WorkOS API`. The injected settings never reached app construction.

**2. Identify the layer.** The app factory, `create_app()`.

**3. Explain the cause.** `app.dependency_overrides` only intercepts dependencies resolved
**during a request**. `create_app()` called `get_settings()` *directly*, at construction time,
to set the app title — a plain function call, not a dependency. The override did not exist yet
and would not have applied anyway.

**4. Smallest appropriate fix.** Change the assertion, or make the factory injectable?

The tempting fix is to weaken the test. That would be wrong. The real problem is that
`create_app()` claimed to be a factory but had **no seam for configuration**, which defeats the
entire reason we introduced a factory in §3.4. So the fix was in the production code:

```python
def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = get_settings()
```

**5. Why the fix works.** Configuration now reaches the app through an explicit argument, so a
test can construct an app with any settings. `dependency_overrides` is still used for
request-time dependency (`get_settings` inside `health_check`) — the two mechanisms cover
different moments, and the test now exercises both.

**The lesson:** a test failing is not an obstacle to route around. Read the failure, ask which
layer is wrong, and prefer fixing the design over loosening the assertion. A test you edit to
pass is a test that will never catch anything again.

---

## 10. What you learned

- A **virtual environment** isolates a project's dependencies; `uv` manages it, venv, and locking.
- **`pyproject.toml`** declares dependencies and tool configuration in one place.
- **Layered architecture** separates HTTP, business rules, and data access. Dependencies point
  downward only. This is what will make tenant isolation reliable in iteration 11.
- The **application factory** (`create_app()`) makes building a testable app a normal operation.
- **Config from the environment** is what lets one build run in many environments. `.env` is
  secret and ignored; `.env.example` is documentation and committed.
- **FastAPI validates responses** against a Pydantic model, which prevents accidental leaks.
- **pytest + ruff** are the feedback loop that lets you refactor without fear.

---

## Questions you should be able to answer

Before moving on, try these. If you cannot, re-read the relevant section above.

1. Why does `pyproject.toml` exist when `pip install` already knows how to install things?
2. What is the difference between a **layer** and a **folder**? (Hint: a folder is a place; a
   layer is a rule about who may import whom.)
3. If a route handler in `api/v1/projects.py` needs to insert a row, should it import the ORM
   model directly, or call a service? Why?
4. Why is `.env` in `.gitignore` but `.env.example` is not?
5. What is `uvicorn`, and what would happen if you ran the FastAPI app without it?
6. You add a field to the `User` model later. Which file has to change, and why can't you just
   edit the table by hand?
7. What does `response_model` protect against that a plain `dict` return does not?
8. In the request flow diagram, which single line would you debug first if `/health` returned
   `500` with a message about `DATABASE_URL`? (There is no database yet — what does that tell
   you about where the error actually came from?)
