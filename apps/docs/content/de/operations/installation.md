# Einzeiler-Setup

Der schnellste Weg zu einem laufenden Reality. Ein Befehl legt ein Verzeichnis `reality/` mit deiner
Konfiguration an, startet die veröffentlichten Images und gibt Adresse und ersten Login aus.

## Voraussetzungen

- Linux oder macOS mit Docker und dem Compose-v2-Plugin (`docker compose`, nicht `docker-compose`).
  Unter Windows WSL 2.
- `curl`.
- 2 vCPU und 4 GB RAM reichen für ein Team; App, PostgreSQL, MCP-Endpunkt und Hintergrund-Worker
  teilen sich den Host.
- Für eine öffentliche Installation: ein Hostname, dessen DNS auf den Host zeigt, plus ein zweiter
  Eintrag für `mcp.<hostname>`. Die Ports 80 und 443 müssen frei sein.

## Installieren

```bash
curl -fsSL https://get.runreality.ai | sh
```

Das Skript prüft Docker, überschreibt keine bestehende Installation, schreibt `reality/.env` mit
generierten Geheimnissen, startet den Stack, wartet auf den Health Check und gibt aus:

- die App-Adresse (`http://localhost:8080` ohne Domain),
- die MCP-Adresse (ohne Domain nur auf Loopback),
- E-Mail und Passwort des ersten Owners, genau einmal.

Gib den Owner direkt mit und für eine öffentliche Installation die Domain:

```bash
curl -fsSL https://get.runreality.ai | sh -s -- --email owner@example.com --domain reality.example.com
```

Mit `--domain` beendet Caddy HTTPS auf den Ports 80 und 443 für `https://reality.example.com` und
`https://mcp.reality.example.com/`, holt und erneuert die Zertifikate selbst, und die App verwendet
sichere Cookies.

### Flags

| Flag                  | Bedeutung                                                                                   |
| --------------------- | ------------------------------------------------------------------------------------------- |
| `--email <adresse>`   | Erster Owner (Plattform-Admin). Standard `owner@reality.local`. Weiteren Owner siehe unten. |
| `--domain <host>`     | Öffentlicher Hostname. Aktiviert HTTPS und bedient MCP unter `mcp.<host>`.                  |
| `--port <n>`          | Host-Port der App ohne Domain. Standard `8080`.                                             |
| `--bind <adresse>`    | Host-Adresse für diesen Port. Standard `0.0.0.0`.                                           |
| `--mcp-port <n>`      | Loopback-Port für MCP ohne Domain. Standard `8001`.                                         |
| `--version <release>` | Zu installierendes Release, etwa `0.1.0`, `edge` (main) oder `sha-a204c14`.                 |
| `--dir <pfad>`        | Installationsverzeichnis. Standard `./reality`.                                             |
| `--dry-run`           | Dateien schreiben, Docker- und Port-Prüfungen überspringen.                                 |
| `--help`              | Hilfetext.                                                                                  |

## Befehle

Der Installer hinterlässt eine Kopie von sich als `reality/reality.sh`:

```bash
./reality/reality.sh status                 # Container und Health
./reality/reality.sh logs                   # Logs verfolgen
./reality/reality.sh stop                   # anhalten, Daten behalten
./reality/reality.sh start                  # wieder starten
./reality/reality.sh upgrade                # auf das neueste Release (oder --version 0.2.0)
./reality/reality.sh backup                 # Datenbank + Quelldateien + .env in einem Archiv
./reality/reality.sh restore <archiv.tar>   # auf einem frischen Host aus einem Backup aufbauen
```

`upgrade` schreibt `REALITY_VERSION` in `.env` neu, zieht die Images und führt die Migration aus,
bevor App, Scheduler, Worker und MCP starten. Scheitert die Migration, starten die neuen Dienste
nicht, und die bisherigen Images bleiben auf dem Host.

## Auf einem Server ohne Domain

Ohne `--domain` bindet die App `0.0.0.0:8080` und ist im eigenen Netz als `http://<server-ip>:8080`
erreichbar. Die Anmeldung funktioniert dort, aber die Links, die Reality in E-Mails schreibt, nutzen
`APP_URL`, also in diesem Modus `http://localhost:8080`, und Cookies laufen unverschlüsselt. Für
alles jenseits von Laptop oder vertrauenswürdigem LAN nutze `--domain`.

## Reality entfernen

```bash
./reality/reality.sh stop
cd reality && docker compose down -v && cd ..   # löscht auch Datenbank und Quelldateien
rm -rf reality                                  # löscht .env mit dem Master-Key
```

Mache vorher ein Backup, falls du die Daten noch brauchen könntest.

## Was du aufbewahren musst

`reality/.env` enthält `REALITY_MASTER_KEY`, den Schlüssel für gespeicherte Zugangsdaten. Geht er
verloren, sind diese Zugangsdaten unlesbar; er lässt sich nicht neu erzeugen. Jedes Backup-Archiv
enthält `.env`, schütze die Archive deshalb wie den Schlüssel selbst. Die Datenbank liegt im Volume
`postgres_data`, hochgeladene Quelldateien im Volume `artifacts`.

## Nach der Installation: optionale Einstellungen

Der Installer fragt nichts weiter ab. Alles Folgende ist optional, steht in `reality/.env` und gilt
nach `./reality/reality.sh start` (das die Container mit den neuen Werten neu erstellt).

| Einstellung           | Variablen                                                                                                               | Ohne sie                                                                                                                                                               |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Transaktionale E-Mail | `REALITY_EMAIL_PROVIDER` (`resend` oder `smtp`), `REALITY_EMAIL_FROM`, `RESEND_API_KEY` oder die `REALITY_SMTP_*`-Werte | Einladungen und Registrierungsmails werden nur geloggt, nicht versendet; Kollegen können nicht per Einladung beitreten.                                                |
| Interner Copilot      | `ANTHROPIC_API_KEY`, optional `ANTHROPIC_WORKSPACE_ID`                                                                  | Das Produkt läuft vollständig; der Chat-Assistent ist nicht verfügbar.                                                                                                 |
| Automatische Freigabe | `REALITY_AUTO_APPROVE_LIMIT`                                                                                            | Nicht gesetzt/leer: sofortiger Zugang nach E-Mail-Bestätigung. `0`: manuelle Freigabe. Positiv: Gesamtkontingent.                                                      |
| Weiterer Owner        | `REALITY_PLATFORM_ADMIN_EMAIL` und `REALITY_PLATFORM_ADMIN_PASSWORD`                                                    | Der installierte Owner bleibt; eine neue E-Mail mit neuem Passwort legt beim nächsten Start einen zweiten Plattform-Admin an. Bestehende Konten behalten ihr Passwort. |
| Objektspeicher        | `:compose.s3.yml` an `COMPOSE_FILE` angehängt, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`                                 | Quelldateien bleiben im Volume `artifacts`, was für einen Host ausreicht.                                                                                              |

Die [Umgebungsreferenz](/de/reference/environment) listet jede Variable.

## Erste Schritte

Melde dich mit den ausgegebenen Zugangsdaten an, lege ein Unternehmen an und nutze die geführte Demo
für zusammenhängende Source-, Evidence-, operative und finanzielle Datensätze.
[Verfolge danach dein erstes Ergebnis zurück](/de/getting-started/first-trace). Einladungen an
Kollegen bleiben offen, bis du in `.env` einen E-Mail-Anbieter konfigurierst (siehe
[Umgebungsreferenz](/de/reference/environment)).

Um einen Agenten anzubinden, nutze die MCP-Adresse mit einem Token aus der App: siehe
[Einen MCP-Client verbinden](/de/api-tools/connect-mcp).

## Verfügbarkeit von Storylines und Sandboxes

Storylines, der Playground und die Erstellung von Sandboxes sind reguläre Produktfunktionen. Dafür
ist kein Umgebungsschalter erforderlich. Bestehende Zugangsrechte, Eigentümerschaft, Bestätigungen
und Kapazitätsgrenzen gelten weiter. Alte Playground-Freischaltungen haben nach dem Update keine
Wirkung mehr und können aus der Deployment-Konfiguration entfernt werden. Demo-Datenquellen behalten
ihre ausdrücklichen Aktionen zum Starten, Pausieren und Stoppen.
