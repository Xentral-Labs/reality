# Railway

Eine kurzlebige, unabhängig gehostete Demonstration von Site, App und MCP auf Railway mit
verwaltetem PostgreSQL. Es ist ein Demo-Profil, nicht die Produktionsarchitektur: Hochgeladene
Quelldateien sind in diesem Profil flüchtig, deshalb nutzt es ausschließlich gebündelte synthetische
Daten.

## Ressourcen

Ein Railway-Projekt mit diesen Diensten, alle aus dem Wurzelverzeichnis des Repositorys gebaut:

| Dienst     | Dockerfile             | Netz                                             |
| ---------- | ---------------------- | ------------------------------------------------ |
| `Postgres` | Railway verwaltet      | nur privat                                       |
| `api`      | `apps/api/Dockerfile`  | nur privat, Port 8000                            |
| `app`      | `apps/web/Dockerfile`  | öffentliche Domain, Port 80                      |
| `mcp`      | `apps/mcp/Dockerfile`  | öffentlicher authentifizierter Origin, Port 8001 |
| `docs`     | `apps/docs/Dockerfile` | öffentliche Domain, Port 80 (optional)           |

Die Web-App erreicht die API über Railways privates DNS: Setze
`API_UPSTREAM=api.railway.internal:8000` am Dienst `app`.

## Ausrollen

Das Repository-Skript rollt die Dienste in Reihenfolge aus und wartet auf ihre Health:

```bash
make railway-deploy
```

Es liest die öffentlichen URLs aus `SITE_URL`, `APP_URL`, `DOCS_URL` und `MCP_URL` und erwartet eine
angemeldete Railway-CLI. Laufzeitgeheimnisse (`REALITY_DATABASE_URL`, `REALITY_MASTER_KEY`, die
Plattform-Admin-Zugangsdaten) gehören in Railway-Variablen, nie in Git oder Build-Argumente.

## Sicherheitsgrenze

Nutze nur synthetische oder anonymisierte Daten, lass die Authentifizierung mit einem starken
Demo-Administratorpasswort aktiv, halte die öffentliche Registrierung geschlossen, solange kein
E-Mail-Anbieter konfiguriert ist, und verbinde keine echten Shop-, E-Mail-, KI-, Zahlungs- oder
Buchhaltungszugänge.

## Getrennte Quellen für Produkt und Marketing

`make railway-deploy` lädt nur die Produktdienste aus diesem Checkout hoch: API, Scheduler, Worker,
MCP, Docs und zuletzt App. Die Marketing-Website wird separat aus einem privaten Checkout
ausgerollt:

```bash
export REALITY_RAILWAY_SITE_ROOT=/absoluter/pfad/zum/marketing-checkout
./scripts/deploy_railway_demo.sh --only site --dry-run
./scripts/deploy_railway_demo.sh --only site
```

`--only all` rollt beide Checkouts koordiniert aus. `--dry-run` zeigt Dienst, Checkout, Commit und
Dockerfile ohne Anmeldung oder Deployment. Alle gewählten Dockerfiles werden vor dem ersten Upload
geprüft. Für Releases geprüfte, saubere Checkouts verwenden: Der Upload enthält auch nicht
ignorierte lokale Änderungen.

`REALITY_RAILWAY_PROJECT_ID` und die öffentlichen URLs müssen exportiert werden.
`REALITY_RAILWAY_ENVIRONMENT` ist standardmäßig `production`. Produktprüfungen brauchen `APP_URL`,
`DOCS_URL` und `MCP_URL`, die Website-Prüfung `SITE_URL`. Die ignorierte Datei aus
`REALITY_RAILWAY_ENV_FILE` wird nur für `RAILWAY_TOKEN` gelesen; alternativ funktioniert die
bestehende CLI-Anmeldung.

Railway baut aus dem jeweiligen Checkout-Wurzelverzeichnis. `RAILWAY_DOCKERFILE_PATH` zeigt pro
Dienst auf `apps/api/Dockerfile`, `apps/scheduler/Dockerfile`, `apps/worker/Dockerfile`,
`apps/mcp/Dockerfile`, `apps/docs/Dockerfile`, `apps/web/Dockerfile` beziehungsweise
`apps/site/Dockerfile.railway`. Eine lokale Git-Remote-Änderung konfiguriert Railway nicht. Dieser
Ablauf nutzt weiterhin CLI-Uploads und aktiviert keine GitHub-Autodeployments.
