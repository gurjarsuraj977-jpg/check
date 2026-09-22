# Private Security Lab Foundation

FastAPI + PostgreSQL foundation for an authorized security-testing application.

Included:
- FastAPI backend
- PostgreSQL async database layer
- encrypted credential-storage primitives
- HMAC fingerprints for duplicate detection
- 100-record batch limit
- audit/event model
- Render deployment configuration
- basic tests

The verification layer is intentionally not included. Development should use
authorized sandbox/test fixtures and documented API limits rather than a live-secret
bulk validation mechanism.

## Local start

1. Copy `.env.example` to `.env`.
2. Fill in environment values.
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload`

Health: `/health`
