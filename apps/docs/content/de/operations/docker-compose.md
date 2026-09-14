# Docker Compose

Der manuelle Weg: dieselben Dateien, die das Einzeiler-Setup schreibt, von Hand gefüllt. Wähle ihn,
wenn du jede Variable ausdrücklich setzen willst, Reality in ein bestehendes Compose-Projekt
aufnimmst oder ein Host kein `curl` hat.

## Dateien

Lade sie aus dem Release, das du betreiben willst, etwa
`https://github.com/Xentral-Labs/reality/releases/latest`:

| Datei                | Zweck                                                                                                                       |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `compose.yml`        | Der Stack: PostgreSQL, Migration, API, Web-App, Einladungs-Worker, Scheduler, Worker, MCP. Veröffentlicht keinen Host-Port. |
| `compose.direct.yml` | Ergänzt die App auf einem Host-Port und MCP auf Loopback.                                                                   |
| `compose.proxy.yml`  | Ergänzt Caddy auf den Ports 80 und 443 mit automatischen Zertifikaten für App und `mcp.<domain>`.                           |
| `compose.s3.yml`     | Ersetzt das Artefakt-Volume durch MinIO (S3-API).                                                                           |
| `Caddyfile`          | Die zwei Hostnamen, die Caddy im Domain-Modus bedient.                                                                      |
| `env.example`        | Jede Variable mit ihrer Bedeutung; nach `.env` kopieren (ohne führenden Punkt ausgeliefert).                                |
| `install.sh`         | Optional: der Installer, als `reality.sh` auch für Upgrade, Backup und Restore nutzbar.                                     |

## Images

Alle Dienste nutzen die veröffentlichten Images, festgelegt durch `REALITY_VERSION`:

```text
ghcr.io/xentral-labs/reality-api:<version>
ghcr.io/xentral-labs/reality-web:<version>
ghcr.io/xentral-labs/reality-mcp:<version>
ghcr.io/xentral-labs/reality-scheduler:<version>
ghcr.io/xentral-labs/reality-worker:<version>
```

Release-Tags veröffentlichen `<version>` und `latest`; jeder Commit auf `main` veröffentlicht
`sha-<kurz>` und `edge`. Die Images werden für `linux/amd64` und `linux/arm64` gebaut.

## Modi

`COMPOSE_FILE` in `.env` wählt den Modus. Compose liest `.env` aus dem Verzeichnis, in dem du es
aufrufst.

```text
COMPOSE_FILE=compose.yml:compose.direct.yml     # App auf REALITY_PORT, MCP auf 127.0.0.1:REALITY_MCP_PORT
COMPOSE_FILE=compose.yml:compose.proxy.yml      # Caddy auf 80/443 für REALITY_DOMAIN und mcp.REALITY_DOMAIN
```

Hänge an beide Modi `:compose.s3.yml` an und setze `MINIO_ROOT_USER` und `MINIO_ROOT_PASSWORD`, um
Quelldateien in MinIO statt im Volume `artifacts` zu speichern. Bestehende Installationen behalten
den Speicher, mit dem sie begonnen haben; eine Migration zwischen beiden gibt es nicht.

## Pflichtwerte

Erzeuge sie selbst; die Beispieldatei markiert sie:

- `POSTGRES_PASSWORD`: ein starkes Passwort.
- `REALITY_MASTER_KEY`: ein Fernet-Schlüssel, 32 Zufallsbytes URL-sicher Base64-kodiert, etwa
  `openssl rand -base64 32 | tr '+/' '-_'`. Geht er verloren, sind gespeicherte Zugangsdaten
  unlesbar.
- `REALITY_PLATFORM_ADMIN_EMAIL` und `REALITY_PLATFORM_ADMIN_PASSWORD`: der erste Owner.
- Mit Domain: `REALITY_DOMAIN`, `APP_URL=https://<domain>`, `MCP_URL=https://mcp.<domain>/`,
  `REALITY_COOKIE_SECURE=true`, `REALITY_MCP_ENV=production`. MCP bleibt auf dem Origin-Root; ein
  Pfad in `MCP_URL` wird abgelehnt.

## Starten

```bash
docker compose up -d
docker compose ps
curl --fail http://localhost:8080/healthz
```

Der Dienst `migrate` führt `alembic upgrade head` aus, und jeder Dienst mit Datenbankzugriff wartet
darauf. Für ein Upgrade änderst du `REALITY_VERSION` und führst
`docker compose pull && docker compose up -d` aus. Backups: siehe
[Mit Docker betreiben](./deployment).

## Entwicklerprofil

Die `compose.yml` im Wurzelverzeichnis des Repositorys ist das Entwicklerprofil: Sie baut die Images
aus dem Quellcode und öffnet API- und MCP-Port für lokale Werkzeuge. Diese Anleitung ändert sie
nicht; aus einem Checkout nutzt du `make dev`.
