# Private Security Lab — Final Staging Build

FastAPI + PostgreSQL foundation for an authorized security-testing application.

## Included

- Secure admin authentication and server-side sessions
- CSRF protection for state-changing authenticated requests
- Login throttling backed by PostgreSQL
- Security response headers
- PostgreSQL schema + Alembic migration
- Batch management with a 100-record limit
- HMAC fingerprints for duplicate detection
- Encrypted credential storage primitives
- Explicit destructive deletion workflow
- Async worker manager with bounded concurrency and cancellation
- Synthetic sandbox fixture adapter only
- Audit event history
- Manual reporting-status workflow (no automatic external reporting)
- Render deployment configuration
- Automated unit/security tests

## Important scope boundary

The shipped verification adapter is synthetic and does not call Stripe or any
other external service. It is intentionally limited to `TEST_FIXTURE_VALID:*`
and `TEST_FIXTURE_INVALID:*` fixtures. Any future external integration must be
implemented only against an explicitly authorized sandbox/test environment and
within documented request/concurrency limits.

## Local setup

1. Copy `.env.example` to `.env`.
2. Set PostgreSQL and application secrets.
3. Install: `pip install -r requirements.txt`
4. Run migrations: `alembic upgrade head`
5. Start: `uvicorn app.main:app --reload`

Health endpoint: `/health`

## Staging checklist

- Configure Render environment secrets outside Git.
- Confirm PostgreSQL is attached.
- Confirm `alembic upgrade head` completes.
- Bootstrap the admin once with the bootstrap token.
- Log in and verify CSRF-protected actions.
- Run only synthetic fixtures in staging.
- Review `/api/audit` for secret-free events.
- Confirm deleted records expose no stored secret.
- Verify logs contain no credential values or Authorization headers.
- Keep production external verification disabled until the authorization,
  endpoint, concurrency, retention, and reporting requirements are documented.
