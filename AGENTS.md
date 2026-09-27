# AGENTS.md

**Read `PROJECT_CONTEXT.md` first.** It contains the current iteration status, architecture
invariants, decisions and their reasoning, environment gotchas, and the manual steps that
require a human. Then read `docs/00-roadmap.md` for the full plan.

Key rules, stated briefly:

- One iteration at a time. **Stop and wait for `continue` after each one.**
- Docs (`docs/NN-*.md`) are written *before* the code, concepts explained before use.
- Every iteration ends with at least one new test, an updated doc, and a meaningful commit.
- Never put secrets in code or fabricate credentials. Environment variables only.
- Never hard-code authorization in the frontend; the backend is the boundary.
- When something breaks, make the *smallest* fix and explain why. Never weaken a test
  assertion to make it pass.
