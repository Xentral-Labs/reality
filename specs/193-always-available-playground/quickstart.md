# Verification Guide

Use the repository Python environment and disposable PostgreSQL test databases.
Run focused pytest for storyline runs/library, playground runs/API/steps, company
setup and free playground; then `make test`, `make lint`, `make spec-check`,
`make docs-build`, `make web-build` and `make docs-catalog-check`.

The regression parameterization covers absent, true, false, empty and malformed
retired values. HTTP library must report enabled and confirmed start must succeed.
Check existing unauthorized, quota, archive and confirmation tests remain green.
No browser appearance changes or actual production credentials are needed.
