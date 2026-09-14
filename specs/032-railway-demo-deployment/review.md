# Repository split verification

The owner requested separate Railway source repositories. The existing CLI upload mechanism is retained; GitHub autodeploy is not introduced. Product mode deploys six services from the script checkout. Site and combined modes require a distinct explicit marketing checkout.

Eight mocked end-to-end script tests pass: product and site source routing, combined ordering, fail-before-upload preflight, no-effect dry runs, invalid mode rejection and mode-specific health URL requirements. The old script failed the routing/preflight tests before implementation. Shell syntax, Ruff, documentation formatting, spec policy and diff whitespace checks pass. A real local dry run validates both checkouts and all seven Dockerfiles without deployment. No backend behavior or schema changed.

Operational configuration is maintained separately from this public patch. Railway Dockerfile paths are updated using skip-deploys and read back per service. Full builds and runtime health after a new deployment are not claimed.
