# Reality self-hosted

This directory was created by the Reality installer. It holds your configuration
(`.env`, including the encryption key), the Compose files and a copy of the installer
as `reality.sh`. Keep the directory; back it up.

## Commands

```bash
./reality.sh status                 # containers and health
./reality.sh logs                   # follow logs
./reality.sh stop                   # stop, keep data
./reality.sh start                  # start again
./reality.sh upgrade                # move to the latest release (or: upgrade --version 0.2.0)
./reality.sh backup                 # database + source binaries + .env into one archive
./reality.sh restore <archive.tar>  # rebuild an installation from a backup, on a fresh host
```

## Remove

```bash
./reality.sh stop
docker compose down -v      # inside this directory; deletes database and source binaries
cd .. && rm -rf reality     # deletes .env with the master key; back up first
```

## Install

```bash
curl -fsSL https://get.runreality.ai | sh
```

Flags: `--email <owner email>`, `--domain <host>`, `--port <n>`, `--bind <address>`,
`--mcp-port <n>`, `--version <release>`, `--dir <path>`, `--dry-run`, `--help`.

## What is where

- `.env`: your secrets and mode. `REALITY_MASTER_KEY` encrypts stored credentials; without it
  a restore cannot read them. It is inside every backup archive, so protect the archives.
- `postgres_data` volume: the database. `artifacts` volume: uploaded source binaries.
- `compose.yml` plus `compose.direct.yml` or `compose.proxy.yml`: the stack. Selected by
  `COMPOSE_FILE` in `.env`.
- With a domain: `Caddyfile` serves `https://<domain>` and `https://mcp.<domain>/`.
