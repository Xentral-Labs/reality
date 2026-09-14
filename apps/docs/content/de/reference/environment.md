# App-Umgebung

Diese öffentliche Referenz gilt für die mit Docker betriebene Reality App und PostgreSQL. Das
`.env.example` des Repositorys ist das exakte Konfigurationsinventar der ausgecheckten Version.

## Datenbank und Verschlüsselung

| Variable                                            | Zweck                                                                                                |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Initialisieren den verpackten PostgreSQL-Dienst                                                      |
| `REALITY_DATABASE_URL`                              | SQLAlchemy-Verbindung für App-Services und Migrationen                                               |
| `REALITY_MASTER_KEY`                                | Produktiv benötigter Schlüssel für verschlüsselte Zugangsdaten; außerhalb von PostgreSQL aufbewahren |

Geht `REALITY_MASTER_KEY` verloren oder wird er ohne Migration gewechselt, sind vorhandene
verschlüsselte Zugangsdaten nicht mehr lesbar. Stelle PostgreSQL nicht außerhalb des privaten
Docker-Netzes bereit.

## Installer-Werte

Das [Einzeiler-Setup](/de/operations/installation) schreibt zusätzlich diese Werte; eine manuelle
Compose-Installation setzt sie von Hand aus der `.env.example` der Release-Dateien.

| Variable                                                          | Zweck                                                                                                     |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `REALITY_VERSION`                                                 | Release, auf das die Images festgelegt sind (`0.1.0`, `edge`, `sha-<kurz>`); `upgrade` schreibt es neu    |
| `REALITY_IMAGE_REGISTRY`                                          | Image-Registry, Standard `ghcr.io/xentral-labs`                                                           |
| `COMPOSE_PROJECT_NAME`, `COMPOSE_FILE`                            | Präfix für Container und Volumes; die Compose-Dateien, die den Modus bilden                               |
| `REALITY_BIND`, `REALITY_PORT`, `REALITY_MCP_PORT`                | Host-Adresse und Ports im Direktmodus; MCP bindet immer Loopback                                          |
| `REALITY_DOMAIN`                                                  | Öffentlicher Hostname im Domain-Modus; Caddy bedient auch `mcp.<domain>`                                  |
| `MCP_URL`                                                         | Öffentlicher MCP-Origin-Root; ein Pfad wird abgelehnt, HTTPS ist bei `REALITY_MCP_ENV=production` Pflicht |
| `REALITY_COOKIE_SECURE`                                           | `true` hinter HTTPS                                                                                       |
| `REALITY_ENV`, `REALITY_MCP_ENV`                                  | `production` macht fehlenden Master-Key und einen MCP-Origin ohne HTTPS zu harten Fehlern                 |
| `REALITY_ARTIFACT_DIR`                                            | Verzeichnis des `file`-Artefaktspeichers in den Containern, hinterlegt im Volume `artifacts`              |
| `REALITY_PLATFORM_ADMIN_EMAIL`, `REALITY_PLATFORM_ADMIN_PASSWORD` | Der erste Owner, bei jedem Start angelegt oder reaktiviert                                                |
| `REALITY_AUTO_APPROVE_LIMIT`                                      | Automatische Freigabe von Registrierungen; `0` lässt jede Anfrage beim Owner offen                        |
| `REALITY_COMMIT`                                                  | In das Image eingebrannter Commit; wird neben der Version angezeigt                                       |

Optionale Gruppen, standardmäßig leer: transaktionale E-Mail (`REALITY_EMAIL_PROVIDER`,
`REALITY_EMAIL_FROM`, `RESEND_API_KEY`, `REALITY_SMTP_*`), der interne Copilot (`ANTHROPIC_API_KEY`,
`ANTHROPIC_WORKSPACE_ID`) und MinIO für die `s3`-Ergänzung (`MINIO_ROOT_USER`,
`MINIO_ROOT_PASSWORD`, `REALITY_S3_BUCKET`, `REALITY_S3_REGION`).

## App-Adresse und Kapazität

| Variable                                                          | Zweck                                                           |
| ----------------------------------------------------------------- | --------------------------------------------------------------- |
| `APP_URL`                                                         | Öffentlicher Origin der Reality App für Browser- und Kontolinks |
| `API_URL`                                                         | Origin der Anwendungs-API für den Web-Client                    |
| `APP_PORT`, `API_PORT`                                            | Optionale lokale Host-Port-Überschreibungen für Docker          |
| `REALITY_BACKEND_DB_POOL_SIZE`, `REALITY_BACKEND_DB_MAX_OVERFLOW` | PostgreSQL-Verbindungslimits der App                            |
| `REALITY_DB_POOL_TIMEOUT`                                         | Maximale Wartezeit auf eine Pool-Verbindung in Sekunden         |

## Optionale App-Funktionen

Authentifizierung, transaktionale E-Mail, automatische Zugangsfreigabe und der interne Copilot haben
weitere serverseitige Werte in `.env.example`. Konfiguriere nur die Funktionen, die du verwendest.
Geheimnisse gehören niemals in Browser-Builds, Screenshots, öffentliche Dokumentation oder
eingecheckte Umgebungsdateien.

Die Konfiguration von Site und Docs des Produktanbieters liegt außerhalb dieses
Installationscontracts. Eine zukünftige verwaltete Reality-Infrastruktur veröffentlicht ihren
eigenen Konfigurationscontract.
