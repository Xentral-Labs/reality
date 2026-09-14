# ADR 0001: PostgreSQL-only persistence

Status: accepted; supersedes the original local-database decision.

## Decision

Use PostgreSQL through SQLAlchemy 2 and Alembic for local development, automated
tests, demos, and production. `REALITY_DATABASE_URL` is required. Do not maintain
alternate database dialect behavior.

## Why

The product depends on concurrent tenant-scoped writes, row locking, transactional
journals, JSON projection filters, and production-equivalent migration tests. One
dialect keeps these semantics explicit and prevents a lightweight local database
from hiding production failures.
