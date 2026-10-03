# Web Actions ergänzen

## Das lernst du

Du kannst eine vorhandene Operation als bestätigten Bedienablauf bereitstellen und bis zum
Ergebnisregister verfolgen.

## Wann du diesen Baustein brauchst

Eine Web Action ist ein registrierter Bedienablauf: Eingaben sammeln, Wirkung prüfen, Änderungen
bestätigen und das Ergebnis anzeigen. Sie ruft den vorhandenen Command auf. Der Katalogeintrag
allein baut noch kein Formular.

## Bevor du beginnst

Command, Service und eine passende HTTP-Schnittstelle existieren. Du kennst Eingaben, Rechte,
Bestätigungsart und Zielregister. Für neue Geschäftslogik beginne bei [Commands](./commands.md).

## Durchgearbeitetes Beispiel

Der vorhandene Eintrag aus `packages/reality-core/config/workspace_catalog.yaml`, hier für die
Lesbarkeit mehrzeilig dargestellt:

```yaml
key: reserve_stock
label: Reserve stock
command: reserve
target_route: reservations
confirmation: summary
prerequisites: [commitment]
result_kind: reservation
```

`key` identifiziert die Web Action; `command` verweist auf die gemeinsame Operation. `prerequisites`
beschreibt benötigten Kontext, ersetzt aber keine Service-Validierung. `confirmation` beschreibt die
Bestätigungsart. `target_route` führt zum Ergebnisregister. Der Eintrag wird außerdem in den
passenden `workspaces[].actions` referenziert.

## Schritt für Schritt

1. Beschreibe Benutzerrolle, Startkontext, Eingaben, Bestätigung und Ergebnis in der Spezifikation.
   Plane die Tests vor dem Formular.
2. Prüfe Command, Service, vorhandene HTTP-Route und Berechtigung. Erweitere nur fehlende Teile. Der
   Service entscheidet über Bestandsmenge und Sperren.
3. Ergänze den Action-Eintrag und seine Workspace-Mitgliedschaft. Verwende stabile Schlüssel, keine
   Belegnummern als Identität.
4. Verfolge `ActionLauncher.tsx`, `actionDiscovery.ts` und `CommitmentActionCard.tsx` unter
   `apps/web/src/unified/`. Binde den neuen Ablauf ausdrücklich in die unterstützte
   Formular-/Action-Zuordnung ein; ein unbekannter Schlüssel wird nicht automatisch ausführbar.
5. Sammle nur nötige Eingaben, verwende die vorhandene typisierte API und zeige eine konkrete
   Bestätigung. Server-Preview-/Revisions-Verträge müssen unverändert durchgereicht werden; ein
   Button umgeht sie nicht.
6. Zeige Erfolg, Teilwirkung und Fehler anhand des Server-Ergebnisses. Öffne das Zielregister mit
   dem vorhandenen Inspector-Erklärpfad. Berechne Bestandsverfügbarkeit nicht im Browser.
7. Teste Rechte, fremde IDs, Abbruch ohne Wirkung, bestätigte Ausführung, Fehlmenge, Fehler und
   wiederholte Requests. Vorlagen: `test_unified_workspace_api.py`, `test_http_boundary.py` und die
   Action-/Workspace-Tests in `apps/web/scripts/`.
8. Ergänze Ressourcen-Zuordnung und deutsches Label, führe `make docs-generate` aus und prüfe, dass
   Web Action und Command mit ihrer Beziehung auffindbar sind.

## Ergebnis prüfen

Öffne in einer Testfirma ein Commitment mit Bestand. Starte die Action und gib Menge 5 ein.
Abbrechen darf keine Reservation erzeugen. Bei Bestätigung liest du das Ergebnis im
Reservations-Register und prüfst die Commitment-Verknüpfung. Wiederhole mit zu wenig Bestand und
einer fremden Tenant-ID: Das Formular muss den Service-Ausgang korrekt zeigen und darf keinen
fremden Datensatz offenlegen.

API und CLI verwenden dieselbe fachliche Operation. Die gemeinsame Anleitung
[Zugänge ergänzen](./application-surfaces.md) erklärt diese Adapter;
[Agent Tools ergänzen](./agent-tools.md) zeigt den Vorschlags-/Freigabeweg.

## Selbst ausprobieren

Verfolge `reserve_stock` von der Workspace-Mitgliedschaft zum Formular und Zielregister. Ändere in
einer lokalen Übung nur die Platzierung, nicht den Command. Erwartet: dieselbe Operation und
Bestätigung, erreichbar im gewählten Workspace.

## Häufige Fehler

Ein YAML-Eintrag erzeugt kein Formular. Nicht unbekannte Commands generisch ausführbar machen,
Bestätigungen umgehen oder Fehlmengen im Browser berechnen.

## Weiterlesen

[Agent Tools](./agent-tools.md) zeigt Vorschlag und Freigabe; [API und CLI](./api-cli.md) die weiteren
Adapter.
