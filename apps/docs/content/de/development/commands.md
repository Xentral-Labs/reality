# Commands entwickeln

## Das lernst du

Du kannst eine gemeinsame Operation mit Service, Application Tool und Katalogeintrag ergänzen. Du
unterscheidest dabei Reads von Änderungen.

## Wann du diesen Baustein brauchst

Ein Command beschreibt eine Anwendungsoperation mit definierten Eingaben und Ergebnissen. Ergänze
ihn, wenn die Operation noch fehlt; ein neuer Zugang zu einer vorhandenen Operation braucht keinen
zweiten Command.

Verfolge `credit_exposure` in `config/command_catalog.yaml`, `_credit_exposure` und
`TOOLS["credit_exposure"]` in `tools/application.py` sowie `credit_exposure` im gleichnamigen
Service-Modul. Anders als `reserve` verwendet dieser Einstieg keine Änderungsfreigabe. Die Abfrage
liest die vorhandenen Datensätze mandantenbezogen; ein Read darf nicht beim Anzeigen fachliche
Datensätze verändern. Übernimm Eingaben und Ergebnis aus dem tatsächlichen Schema, statt den
Reservierungsvertrag für eine Abfrage zu kopieren.

## Bevor du beginnst

Du kennst die beteiligten Reality-Datensätze und den gewünschten fachlichen Ausgang. Nutze eine
PostgreSQL-Testumgebung und vorhandene Fixtures. Spec, Plan und Tests stehen vor der
Implementierung; die
[gemeinsame Referenz](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/reference.md)
beschreibt den Ablauf.

## Durchgearbeitetes Beispiel

1. `packages/reality-core/src/reality/services/core.py::reserve` besitzt die Regeln. Der Service
   lädt das `Commitment` mandantenbezogen, prüft Sperren und Bestandsidentität, berechnet Mengen mit
   `Decimal`, erzeugt die `Reservation` und schreibt das Business Event.
2. `packages/reality-core/src/reality/tools/application.py::_reserve` übersetzt die Argumente in den
   Service-Aufruf. Das Ergebnis enthält stabile IDs sowie `requested`, `applied`, `shortage` und
   `event_id`.
3. Dieselbe Datei registriert `TOOLS["reserve"]` mit `mutating=True`. Dadurch erkennt die Proposal-
   und Freigabelogik die Zustandsänderung.
4. `packages/reality-core/config/command_catalog.yaml` beschreibt Reads, Writes, Wirkung, Parameter
   und Adapter. `workspace_catalog.yaml` platziert die Aktion als `reserve_stock`.
5. HTTP, MCP, CLI und Chat verwenden die gemeinsamen Services und Application Tools. Dort stehen
   keine eigenen Regeln.

Lies den vollständigen Service und Wrapper im Repository. Die Reservierung verwendet den gleichen
Weg für Web, CLI und Agenten; Wrapper sind keine neue Regelinstanz.

## Schritt für Schritt

1. Lege unter `packages/reality-core/tests/` zuerst einen fehlschlagenden Business-Test an. Benenne
   Vorbedingungen, geschriebene Datensätze, Event und maßgebliche Kontrollabfrage.
2. Implementiere den mandantenbezogenen Service in `src/reality/services/`. Verwende keine
   Belegnummer oder SKU, wenn eine undurchsichtige ID erforderlich ist.
3. Ergänze Wrapper und `Tool(...)` in `tools/application.py`. Jede Zustandsänderung erhält
   `mutating=True`.
4. Ergänze `config/command_catalog.yaml`. Kann ein Mensch die Aktion auslösen, kommt in
   `config/workspace_catalog.yaml` eine Aktion mit Voraussetzungen, Bestätigung und Ergebnisart
   hinzu.
5. Ergänze nur benötigte Adapter. Agentenänderungen laufen über `create_change_proposal`: Das
   Proposal speichert Tool, Argumente und Server-Vorschau exakt und läuft erst nach separater
   Freigabe.
6. Teste Service, Application Tool, Katalog und jede verwendete Adaptergrenze.

Gute Vorlagen sind `test_inventory_and_fulfillment.py`, `test_application_tools.py`,
`test_application_catalog.py` und `test_http_boundary.py`.

Ein lesender Command darf eine Berechnung oder Projection zugänglich machen. Die Ableitung bleibt im
gemeinsamen Service; aktuelle Risikozustände gehören zur Ausnahmeableitung und ERP-Transport zum
Connector. Liefer- und Reservierungsstatus gehören nie an ein Document; sie werden aus
Reality-Datensätzen abgeleitet.

## Ergebnis prüfen

Nutze dieselbe fachliche Testgeschichte für Service, Tool und Adapter: ausreichend Bestand,
Fehlmenge, gesperrtes Commitment und fremde Tenant-ID. Überprüfe das Ergebnis durch Reservations und
Movements, nicht durch einen neuen Status am Document. Ergänze Ressourcen-Zuordnung und `labels.de`
in `config/resource_catalog.yaml`, führe `make docs-generate` aus und kontrolliere die Referenz.

Für den nächsten Schritt gibt es konkrete Vorlagen: [Agent Tools](/de/development/agent-tools) und
[Web Actions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/web-actions.md).
Neue Tabellen sind keine Voraussetzung für einen neuen Command; eine Schemaänderung braucht einen
nachgewiesenen Use Case in Spec und Plan.

## Selbst ausprobieren

Verfolge zunächst den lesenden `credit_exposure`-Command. Notiere Service, Eingaben und Ergebnis.
Vergleiche ihn mit `reserve`: Nur die Änderung braucht Mutation-Markierung und Freigabe. Erwartetes
Ergebnis: Du kannst erklären, welche vorhandenen Teile ein zusätzlicher Zugang wiederverwendet.

## Häufige Fehler

Keine Geschäftsregeln im Adapter; keine Belegnummer als ID; kein Fulfillment-Status am Document. Ein
verkürztes Beispiel ersetzt nicht Guards, Idempotenz und Events der vollständigen Implementierung.

## Weiterlesen

[Ausnahmen entwickeln](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/exceptions.md)
erklärt abgeleiteten Handlungsbedarf. Für Zugänge folgen [Agent Tools](/de/development/agent-tools)
und
[Web Actions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/web-actions.md).
