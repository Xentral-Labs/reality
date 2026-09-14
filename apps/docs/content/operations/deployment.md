# Operate Reality with Docker

## Release sequence

Build immutable App images, start PostgreSQL, run `alembic upgrade head`, then start the App and
accept traffic only after its health check passes. The migration step must complete before the API
and background workers use the new release.

## PostgreSQL backup and recovery

Back up PostgreSQL on a defined schedule and retain backups outside the running Docker host. Test
restoration in an isolated environment. A recovery is successful only after migrations apply and a
representative business result remains traceable from Reality through Evidence to SourceRecord.

Installations created by the [one-line setup](./installation) do this with two commands:

```bash
./reality/reality.sh backup                  # writes reality-backup-<timestamp>.tar
./reality/reality.sh restore <archive.tar>   # on a fresh host, into an empty directory
```

The archive holds a `pg_dump` of the database, the `artifacts` volume with uploaded source binaries,
and `.env` with `REALITY_MASTER_KEY`. Without the key a restored database cannot read its encrypted
credentials, so the archive is as sensitive as the key.

## Health and logs

Use the App API's `/healthz` endpoint and Docker service state. Centralise application and database
logs, exclude secrets and sensitive source payloads, and alert on failed migrations, unhealthy App
instances, failed intake and repeated interpretation errors.

## Upgrade and rollback

Before an upgrade, record the running image and database migration revision and create a verified
backup. Apply migrations before App traffic. An application-image rollback does not reverse a
committed database migration or business event; every release therefore needs an explicit migration
and rollback assessment.

```bash
./reality/reality.sh upgrade                 # latest release
./reality/reality.sh upgrade --version 0.2.0 # a specific release
```

The running version and commit are shown by `GET /api/v1/system/status` and in the platform
administration overview. A manual Compose installation upgrades by changing `REALITY_VERSION` in
`.env`, then `docker compose pull && docker compose up -d`.

## Security checklist

- Terminate HTTPS in front of the App.
- Keep database, authentication, email and provider credentials in Docker secrets or an equivalent
  protected environment.
- Use secure session cookies and exact allowed origins.
- Do not expose PostgreSQL publicly.
- Verify tenant isolation, backup restoration, migration state, health and logs.

Reality may later provide managed infrastructure. This page documents only the Docker-operated App
and PostgreSQL contract and does not prescribe a cloud provider.
