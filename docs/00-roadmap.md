# Iteration Roadmap

This is the plan for the whole build. It is a **living document** — we will revise it as we
learn things that change the design.

The ordering below is not arbitrary. Later iterations depend on concepts established earlier.
I have written the dependency explicitly for each one so you can see *why* it cannot come sooner.

---

## How to read this

Each iteration is one meaningful learning unit:

1. I explain the concepts (docs/NN-*.md).
2. We implement a small piece.
3. I explain what was written and what to read first.
4. We test it and verify it.
5. Docs get updated.
6. **I stop.** You say `continue` when you are ready.

I will not chain iterations together. If you do not understand iteration 6, iteration 7 will
just be more confusion stacked on top.

---

## Phase 1 — Foundation and the data layer

### Iteration 01 — Project Foundation
*Repo, folder layout, layered architecture, FastAPI app, health endpoint, config from env,
pytest + ruff working.*

Teaches: virtual environments, dependency pinning, application factory pattern, why we split
code into layers, environment variables, `12-factor` config.

**Depends on:** nothing. This is the root.

---

### Iteration 02 — Database, SQLAlchemy, and Migrations
*PostgreSQL in Docker, SQLAlchemy 2.0 engine/session, declarative base, Alembic, first real
migration, health endpoint that actually pings the database.*

Teaches: what an ORM is, engine vs session, connection pooling, transactions, why migrations
exist instead of `create_all()`.

**Depends on:** 01 (needs the app skeleton and config system).

> Docker daemon must be running by now. This is the first iteration that needs it.

---

### Iteration 03 — The User Model and Schemas
*SQLAlchemy `User` model with UUID primary keys and timestamps, Pydantic v2 schemas for
create/read/update, the difference between ORM objects and API shapes.*

Teaches: why we never expose the ORM model directly, field validation, Pydantic v2
`model_config`, UUID vs auto-increment, soft delete and `deleted_at`.

**Depends on:** 02 (a model is meaningless without a database and migrations).

---

## Phase 2 — Authentication

### Iteration 04 — Password Hashing
*Argon2 hashing, salt, pepper, verifying a password, upgrade path for old hashes.*

Teaches: why passwords are never stored directly, what a hash vs encryption is, salting,
key stretching, why `==` on a password is a timing leak.

**Depends on:** 03 (we need a User to store a hash on).

---

### Iteration 05 — Registration API
*`POST /api/v1/auth/register` with the service + repository layers, duplicate email handling,
error mapping.*

Teaches: layering (route → service → repository), why business logic is not in the route
handler, HTTP status code choices, not leaking whether an email exists.

**Depends on:** 03, 04.

---

### Iteration 06 — Login and Access Tokens (JWT)
*`POST /api/v1/auth/login`, JWT structure, signing, claims, `exp`, verifying a token.*

Teaches: what a JWT physically is, header/payload/signature, signing vs encryption, why we
choose short expiry, clock skew, why the access token is stateless.

**Depends on:** 05 (login needs registered users and a password hash to check).

---

### Iteration 07 — Refresh Tokens and Rotation
*Refresh token table, rotation on use, reuse detection, family revocation, logout.*

Teaches: why a stateless access token needs a way to be revoked, token families, what an
attacker gets if they steal a refresh token, the exact attack rotation defeats.

**Depends on:** 06.

---

### Iteration 08 — Auth Dependencies and the Current User
*`get_current_user` FastAPI dependency, OpenAPI security scheme, a protected endpoint that
actually uses the token.*

Teaches: FastAPI dependency injection, why a dependency is better than middleware for auth,
request-scoped state, declaring auth once in the OpenAPI docs.

**Depends on:** 07.

---

### Iteration 09 — Email Verification and Password Reset
*One-time tokens, `POST /verify-email`, `POST /forgot-password`, `POST /reset-password`,
dev-mode token exposure.*

Teaches: one-time vs reusable tokens, token hashing at rest, user enumeration attacks and how
we avoid them, the fact that we log the token in dev because there is no mail provider yet.

**Depends on:** 07 (we already have the refresh-token machinery and revocation ideas).

---

## Phase 3 — Multi-tenancy and authorization

This is the part that makes it a *SaaS* and not a single-user app. We give it the most room.

### Iteration 10 — Organizations and Membership
*`Organization`, `Membership`, `OrganizationRole`. Creating an org, joining it, listing the
orgs a user belongs to.*

Teaches: what a tenant is, why the tenant lives in the database and not just the JWT, the
membership join table, why a user can belong to many orgs.

**Depends on:** 03 (model work), 08 (a user must be authenticated to create an org).

---

### Iteration 11 — Tenant Isolation and IDOR Protection
*Tenant context resolution, every repository scoped by `organization_id`, cross-tenant tests
proving isolation.*

Teaches: **this is the most important iteration in the project.** IDOR, why the frontend
cannot be trusted to hide a URL, how a single missing `WHERE` clause leaks a competitor's
data, writing a test that would fail loudly if isolation breaks.

**Depends on:** 10.

---

### Iteration 12 — Roles and Permissions
*`Role`, `Permission`, role→permission map, permission catalogue with names like
`project:create`.*

Teaches: RBAC vs ABAC, roles are just bundles of permissions, why permissions are data and not
scattered `if` statements.

**Depends on:** 10.

---

### Iteration 13 — Permission Enforcement and Admin APIs
*The `require_permission` dependency, member management endpoints, role assignment.*

Teaches: how a check is written once and reused, the danger of forgetting a check, OpenAPI
documentation of security requirements, privilege escalation via self-promotion.

**Depends on:** 12, 11.

---

### Iteration 14 — Organization Invitations
*Invite by email, single-use tokens, accept/revoke, expiry.*

Teaches: the invitation token as a scoped one-time token, what happens when an invited person
already has an account, revoking access after the fact.

**Depends on:** 13, 09 (reuses the one-time-token pattern).

---

## Phase 4 — External auth, and the actual product

### Iteration 15 — Google OAuth
*Authorization code flow, state parameter, PKCE, linking a Google identity to a `User`, new
user auto-provisioning.*

Teaches: OAuth 2.0 flows, why `state` defeats CSRF on the callback, what you must configure in
Google Cloud Console yourself, why we never trust an email from an unverified provider.

**Depends on:** 05 (user creation), 08 (authenticated callback).

### Iteration 16 — Projects and Tasks
*The real product surface: projects, tasks, assignment, status transitions. Every read and
write goes through the tenant-scoped repositories.*

Teaches: this is where iteration 11 pays off — a domain feature that is *automatically*
isolated because the repository enforces it.

**Depends on:** 11, 13.

---

## Phase 5 — Redis, hardening, and the frontend

### Iteration 17 — Redis: Caching and Rate Limiting
*Redis container, token denylist, rate limiting on auth endpoints, caching a permission
lookup.*

Teaches: what Redis is and what it is not, in-memory storage, TTL, caching vs a source of
truth, why rate limiting belongs in front of login, cache invalidation.

**Depends on:** 07 (denylist needs revocation), 05 (login is what we rate limit).

### Iteration 18 — Security Hardening
*CORS, security headers, log hygiene, input size limits, dependency audit.*

Teaches: going through the OWASP Top 10 *for our actual code* rather than in the abstract, and
what a "sanitised" log line looks like.

**Depends on:** 17.

### Iteration 19 — Frontend Foundation
*Next.js App Router, TypeScript, Tailwind, shadcn/ui, API client with typed responses.*

Teaches: why the backend is the source of truth, how to keep a TypeScript client honest
against a Pydantic backend.

**Depends on:** 01 (and it consumes the API contract built so far).

### Iteration 20 — Auth Screens and Client Token Handling
*Login, register, forgot password, OAuth button. Refresh-token handling, in-memory access
token, refresh on 401.*

Teaches: why the access token should not be in `localStorage`, the refresh loop, CSRF when
cookies are involved, XSS and token theft.

**Depends on:** 19, 07.

### Iteration 21 — Dashboard, Org Switcher, Protected Routes
*Middleware-based route protection, org context in the client, member list.*

Teaches: that client-side route protection is UX only, the real protection is the API's 401.

**Depends on:** 20, 11.

### Iteration 22 — Admin UI and Projects UI
*Member management, role assignment, project and task screens.*

Teaches: building UI against a permission system, hiding buttons the user cannot use (and why
that is *not* the security boundary).

**Depends on:** 21, 13, 16.

---

## Phase 6 — Shipping it

### Iteration 23 — Docker, Deployment, HTTPS
*Production Dockerfiles, multi-stage builds, compose for the full stack, deploying backend
and frontend, env config per environment, health checks.*

Teaches: image vs container, multi-stage builds, why `root` in a container is a bad idea,
12-factor config in production.

**Depends on:** everything running locally.

### Iteration 24 — CI/CD and Observability
*GitHub Actions for lint + test, structured logging, error tracking, a real README.*

Teaches: CI as a safety net that catches *your* mistakes before a user does.

**Depends on:** 23.

---

## Dependency graph

```
01 Foundation
 └── 02 Database/Alembic
      └── 03 User Model
           ├── 04 Password Hashing
           │    └── 05 Registration
           │         └── 06 Login + JWT
           │              └── 07 Refresh Tokens
           │                   └── 08 Current-User Dependency
           │                        ├── 09 Verify Email / Reset Password
           │                        └── 10 Organizations
           │                             ├── 11 Tenant Isolation  ← critical
           │                             │    └── 16 Projects/Tasks
           │                             └── 12 Roles/Permissions
           │                                  └── 13 Permission Enforcement
           │                                       └── 14 Invitations
           └── 10 Organizations ──┘
                  15 Google OAuth ──┘
17 Redis ── 18 Hardening ── 19 Frontend ── 20 Auth UI ── 21 Dashboard ── 22 Admin UI
                                              23 Docker/Deploy ── 24 CI/CD
```

---

## Things that could still change

I am recording these so you can see this plan is not set in stone:

- **OAuth library.** Iteration 15 will probably use `authlib`, but I will check whether a
  hand-rolled authorization-code exchange teaches more. The flow is ~80 lines either way.
- **Permission storage.** Iteration 12 starts with roles hard-coded in Python. If
  custom-per-role turns out to be a real requirement, we migrate the map into a table. The
  dependency structure does not change.
- **Task model complexity.** Iteration 16 assumes a flat task list per project. If we want
  subtasks, statuses, or assignments history, that iteration gets one extra increment.
- **Email.** Iteration 09 logs tokens instead of sending email. A real provider (Resend,
  SES, Postmark) gets added when we are ready to actually deploy. Nothing else changes.
