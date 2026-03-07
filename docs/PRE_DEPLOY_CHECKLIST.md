# PhysioLog Pre-Deploy Checklist (v0.4 -> v1.0)

Use this checklist before first cloud deployment.

## Subversion Roadmap (pre-1.0)

### v0.5 — Runtime baseline

- [ ] Sections `1` and `2` completed.

### v0.6 — Data and infra readiness

- [ ] Section `4` completed in staging with PostgreSQL.

### v0.7 — Security hardening

- [ ] Section `5` completed.
- [ ] Section `6` admin strategy decided and documented.

### v0.8 — Observability and deployment gate

- [ ] Sections `7`, `8`, and `9` completed.
- [ ] Final go/no-go review recorded.

## 1) Release Readiness

- [x] Decide target stack: `AWS EC2` or `AWS ECS/Fargate`.
- [x] Create `staging` environment (same config shape as production).
- [x] Freeze dependency versions (`uv.lock` committed and used in build).
- [ ] Run full test suite in clean environment.

## 2) Runtime and Container

- [ ] Add production `Dockerfile`.
- [ ] Add `.dockerignore`.
- [ ] Run app with Gunicorn in container (`gunicorn app:app ...`).
- [ ] Set container healthcheck endpoint (`GET /health`).
- [x] Verify app starts with `FLASK_DEBUG=False`.

## 3) Configuration and Secrets

- [ ] Remove reliance on dev fallback `SECRET_KEY` in production.
- [ ] Set all runtime config via environment variables.
- [ ] Store secrets in AWS Secrets Manager or SSM Parameter Store.
- [ ] Validate no secrets in git history or repo files.

## 4) Database and Migrations

- [ ] Use PostgreSQL in staging and production.
- [ ] Run migrations against PostgreSQL before first release.
- [ ] Verify indexes/constraints in production schema.
- [ ] Backup/restore procedure documented and tested.
- [ ] Keep SQLite only for local dev.

## 5) Auth and Account Security

- [ ] Enforce secure cookies in production:
  - [ ] `SESSION_COOKIE_SECURE=True`
  - [ ] `SESSION_COOKIE_HTTPONLY=True`
  - [ ] `SESSION_COOKIE_SAMESITE='Lax'` (or stricter if feasible)
- [ ] Add CSRF protection for form-based POST actions.
- [ ] Add basic login brute-force protection (rate limit/lockout).
- [ ] Define password minimum policy (length + validation).
- [ ] Decide registration policy for production:
  - [ ] Public sign-up allowed, or
  - [ ] Invite/admin-only sign-up

## 6) Admin Strategy (recommended before deploy)

- [x] Add `is_admin` role (or confirm single-user deployment scope).
- [x] Add first-admin bootstrap flow (CLI/env-driven).
- [ ] Add admin recovery procedure (lost admin credentials).
- [ ] Confirm `AUTH_BOOTSTRAP_USER*` behavior is safe for production.

## 7) Observability and Operations

- [ ] Structured request logging to stdout.
- [ ] Capture unhandled exceptions (Sentry or equivalent).
- [ ] Add `/health` and optional `/ready` endpoints.
- [ ] Define log retention and access policy.
- [ ] Basic alerting (5xx rate, container restarts, DB connectivity failures).

## 8) API and Frontend Contract Checks

- [ ] Verify auth-protected routes return correct 401/403/redirect behavior.
- [ ] Verify `/api/entries`, `/api/stats`, `/api/user-profile`, `/api/user-settings`.
- [ ] Validate trends calculations for selected window and zoom ranges.
- [ ] Smoke test multi-user data isolation.

## 9) Deployment Gate (Go / No-Go)

- [ ] Staging sign-off completed.
- [x] Rollback plan documented.
- [ ] Initial production admin account created.
- [ ] Domain + TLS ready.
- [ ] Deployment runbook available.

## Suggested First Execution Order

1. PostgreSQL + migrations in staging.
2. Docker + Gunicorn + health endpoint.
3. Cookie/CSRF/security hardening.
4. Admin/bootstrap + registration policy.
5. Logging/monitoring + final staging sign-off.
