# Reality mit Docker betreiben

## Release-Reihenfolge

Baue unveränderliche App-Images, starte PostgreSQL, führe `alembic upgrade head` aus und starte
danach die App. Nimm Verkehr erst an, wenn ihr Health Check erfolgreich ist. Die Migration muss
abgeschlossen sein, bevor API und Hintergrundarbeit die neue Version verwenden.

## PostgreSQL sichern und wiederherstellen

Sichere PostgreSQL nach einem festgelegten Zeitplan und bewahre Backups außerhalb des laufenden
Docker-Hosts auf. Erprobe die Wiederherstellung in einer isolierten Umgebung. Sie ist erst
erfolgreich, wenn Migrationen laufen und sich ein repräsentatives Geschäftsergebnis weiterhin von
Reality über Evidence bis zur SourceRecord zurückverfolgen lässt.

Installationen aus dem [Einzeiler-Setup](./installation) erledigen das mit zwei Befehlen:

```bash
./reality/reality.sh backup                  # schreibt reality-backup-<zeitstempel>.tar
./reality/reality.sh restore <archiv.tar>    # auf einem frischen Host in ein leeres Verzeichnis
```

Das Archiv enthält einen `pg_dump` der Datenbank, das Volume `artifacts` mit hochgeladenen
Quelldateien und `.env` mit `REALITY_MASTER_KEY`. Ohne den Schlüssel kann eine wiederhergestellte
Datenbank ihre verschlüsselten Zugangsdaten nicht lesen; das Archiv ist deshalb so schützenswert wie
der Schlüssel.

## Health und Logs

Nutze `/healthz` der App-API und den Docker-Dienstzustand. Führe Anwendungs- und Datenbanklogs
zentral zusammen, schließe Geheimnisse und sensible Quell-Payloads aus und alarmiere bei
fehlgeschlagenen Migrationen, ungesunden App-Instanzen, Fehlern im Quelleingang und wiederholten
Interpretationsfehlern.

## Upgrade und Rollback

Halte vor einem Upgrade laufendes Image und Datenbank-Migrationsstand fest und erzeuge ein geprüftes
Backup. Wende Migrationen vor dem App-Verkehr an. Das Zurückrollen eines App-Images macht weder eine
festgeschriebene Datenbankmigration noch Geschäftsvorfälle rückgängig. Jedes Release braucht deshalb
eine ausdrückliche Bewertung von Migration und Rollback.

```bash
./reality/reality.sh upgrade                 # neuestes Release
./reality/reality.sh upgrade --version 0.2.0 # ein bestimmtes Release
```

Laufende Version und Commit zeigen `GET /api/v1/system/status` und die
Plattformverwaltungsübersicht. Eine manuelle Compose-Installation aktualisiert über
`REALITY_VERSION` in `.env`, danach `docker compose pull && docker compose up -d`.

## Sicherheitscheckliste

- Beende HTTPS vor der App.
- Bewahre Zugangsdaten für Datenbank, Authentifizierung, E-Mail und Anbieter in Docker Secrets oder
  einer gleichwertig geschützten Umgebung auf.
- Nutze sichere Session-Cookies und exakt erlaubte Origins.
- Stelle PostgreSQL nicht öffentlich bereit.
- Prüfe Mandantentrennung, Backup-Wiederherstellung, Migrationsstand, Health und Logs.

Reality kann später eine verwaltete Infrastruktur anbieten. Diese Seite dokumentiert ausschließlich
den mit Docker betriebenen Contract aus App und PostgreSQL und schreibt keinen Cloud-Anbieter vor.
