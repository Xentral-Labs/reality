# Links aus den Docs konfigurieren

Die Links im Kopf der Docs sind Deployment-Konfiguration und keine fest im Produkt verdrahtete
Entscheidung.

| Sichtbares Ziel                | Build-Variable | Produktionsbeispiel          |
| ------------------------------ | -------------- | ---------------------------- |
| **Kommerzielles Angebot**      | `SITE_URL`     | `https://runreality.ai`      |
| **Reality öffnen**             | `APP_URL`      | `https://app.runreality.ai`  |
| Docs selbst und erzeugte Feeds | `DOCS_URL`     | `https://docs.runreality.ai` |

Abschließende Schrägstriche werden vor dem Erzeugen der Links entfernt. Fehlt ein Wert, verwendet
das Image die oben genannten Produktionsbeispiele als Standardwerte.

## Docker Compose

Setze die Origins in der Umgebung von Docker Compose und baue die Docs neu:

```bash
APP_URL=https://app.example.com \
SITE_URL=https://www.example.com \
DOCS_URL=https://docs.example.com \
docker compose build docs

docker compose up -d docs
```

Der `docs`-Service übergibt alle drei Werte als Build-Argumente an `apps/docs/Dockerfile`.

## Railway

Lege `APP_URL`, `SITE_URL` und `DOCS_URL` als **Variablen des Docs-Service** an. Railway stellt
Service-Variablen beim Docker-Build bereit; das Docs-Dockerfile deklariert alle drei im Build-Stage
als `ARG`.

VitePress erzeugt statisches HTML und JavaScript. Deshalb bettet `npm run build` die konfigurierten
Origins fest ein. Erzeuge nach einer Änderung ein neues Deployment mit einem neuen Image-Build. Ein
reiner Neustart des Containers liefert weiterhin die zuvor erzeugten Links aus.

Verwende exakte öffentliche HTTPS-Origins ohne Pfad:

```text
APP_URL=https://app.example.com
SITE_URL=https://www.example.com
DOCS_URL=https://docs.example.com
```

Diese Werte sind öffentliche Browserziele und keine Geheimnisse.

## Das Deployment prüfen

Nach dem Deployment:

1. Öffne die Docs in einem privaten Browserfenster.
2. Folge **Kommerzielles Angebot** und prüfe das Ziel `SITE_URL`.
3. Folge **Reality öffnen** und prüfe das Ziel `APP_URL`.
4. Öffne die erzeugte Feed-Adresse unter `DOCS_URL`.
5. Ist noch ein alter Link sichtbar, prüfe zuerst, ob Railway wirklich neu gebaut hat, und schließe
   danach veraltete Browser- oder CDN-Caches aus.
