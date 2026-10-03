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
