# Views entwickeln

## Das lernst du

Du kannst eine fachliche Anzeige auf einen vorhandenen Reader aufsetzen, ohne Geschäftsregeln zu
kopieren.

## Wann du diesen Baustein brauchst

Eine View ist die fachliche Sicht, in der Benutzer Daten lesen. Nutze ein vorhandenes Register oder
eine Projection; eine neue View benötigt nicht automatisch eine neue Projection. Beschreibe zuerst
die Benutzerfrage, Filter und den Erklärpfad.

Registriere die View in `packages/reality-core/config/workspace_catalog.yaml` mit stabilem
Schlüssel, Route und Datenbasis. Die Web-Oberfläche verwendet vorhandene mandantenbezogene Services
und implementiert keine eigene Berechnung. Teste Mandantengrenze, Filter, leere Ergebnisse und die
Links zu den zugrunde liegenden Reality-Datensätzen. Die Anleitung
[Zugänge ergänzen](./application-surfaces) erklärt die gemeinsame Servicegrenze.

## Bevor du beginnst

Formuliere die Nutzerfrage und prüfe den [View-Katalog](../tool-usage/views). Du brauchst einen
tenant-begrenzten Reader und für die Web-Seite TypeScript/React. Fehlt das Lesemodell, lies zuerst
[Projections](./projections).

## Durchgearbeitetes Beispiel

Verfolge `warehouse_queue` im Workspace-Katalog. Der Eintrag verwendet
`kind: materialized_projection`, `route: warehouse-queue` und `projection: fulfillment_queue`.
`orders` verwendet dieselbe Projection mit einem anderen fachlichen Zweck. Das ist die Vorlage, wenn
eine neue View ein vorhandenes Lesemodell verwendet. Neue Route und Katalogeintrag reichen allein
nicht: Binde den Reader und die Seite in die bestehende API-/Web-Zuordnung ein.

```yaml
- {
    key: warehouse_queue,
    label: Warehouse Queue,
    route: warehouse-queue,
    kind: materialized_projection,
    projection: fulfillment_queue,
    description: Orders prioritized for warehouse execution and shipment readiness,
  }
```

## Schritt für Schritt

1. Schreibe einen Test für Frage, Filter und erwartete Zeilen.
2. Verwende den bestehenden Reader der `fulfillment_queue`; ändere keine Reservierungsregeln.
3. Ergänze den View-Eintrag in `workspace_catalog.yaml` und seine Zuordnung in
   `resource_catalog.yaml`.
4. Verbinde API-Reader, Route und Seite über die vorhandenen Web-Mappings. Verwende
   `warehouse_queue` als Vorlage.
5. Ergänze Labels, Leerzustand, Fehlerzustand und Links zur zugrunde liegenden Zusage.
6. Führe `make docs-generate` aus.

## Ergebnis prüfen

Prüfe dieselben Daten über Reader und Seite: identische Zeilen und Mengen, korrekte Filter, leerer
Zustand und keine fremden Tenant-Daten. Öffne die Erklärung einer Zeile und folge ihr bis zu den
Reality-Records. Ein Katalogeintrag allein besteht diese Prüfung nicht.

## Selbst ausprobieren

Entwirf auf Papier eine zweite Anzeige derselben `fulfillment_queue` für eine andere Rolle. Notiere
Frage, Filter und Spalten. Entscheide, ob ein neuer Reader nötig ist, und begründe dies anhand der
vorhandenen Felder.

## Häufige Fehler

Eine View mit ihrer Projection verwechseln; Mengen im Browser neu berechnen; nur YAML ergänzen und
eine fertige Seite erwarten; technische IDs durch Belegnummern ersetzen.

## Weiterlesen

[Projections](./projections) erklärt ein neues Lesemodell. Für einen Bedienablauf folgt
[Web Actions](./web-actions).
