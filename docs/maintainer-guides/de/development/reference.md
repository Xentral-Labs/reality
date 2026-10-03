# Gemeinsame Entwicklungsregeln

Nutze diese Referenz während der Umsetzung. Der Lernweg beginnt in der [Übersicht](./index.md).

Das gemeinsame Konzept für Datenanbindungen erklärt
[Von Quelldaten zu Reality](../integrations/connector-contract.md): erst die Idee Source → Evidence →
Reality, dann die Regeln für Originaldaten, Identitäten, Versionen und Fehler.

## Landkarte des Repositorys

| Aufgabe                | Hauptort                                                 | Vorhandenes Beispiel                               |
| ---------------------- | -------------------------------------------------------- | -------------------------------------------------- |
| Domain-Datensätze      | `packages/reality-core/src/reality/db/core.py`           | `Commitment`, `Reservation`, `Movement`            |
| Geschäftsverhalten     | `packages/reality-core/src/reality/services/`            | `core.py::reserve`                                 |
| Application Tools      | `packages/reality-core/src/reality/tools/application.py` | `_reserve` und `TOOLS["reserve"]`                  |
| Ausführbares Vokabular | `packages/reality-core/config/*.yaml`                    | `command_catalog.yaml`, `projection_catalog.yaml`  |
| HTTP-Adapter           | `packages/reality-core/src/reality/web/api.py`           | mandantenbezogene Routen, die Services aufrufen    |
| Agenten-Adapter        | `packages/reality-core/src/reality/mcp/catalog.py`       | Eingabeschemas und Proposal-Tools                  |
| Web-Client             | `apps/web/src/`                                          | API-Client und operative Seiten                    |
| Nachweise              | `packages/reality-core/tests/`                           | Service-, Katalog-, HTTP- und Business-Story-Tests |

Weitere Adapter-Orte: `packages/reality-core/src/reality/web/read_models.py` komponiert
Read-Ausgaben, `apps/web/src/api.ts` enthält den typisierten Client und `apps/web/src/unified/` die
aktiven Workspace-Abläufe. Für CLI nutze `packages/reality-core/src/reality/cli/app.py`.

## Vor einer Änderung

1. Suche die ähnlichste vorhandene Business Story und verfolge sie durch alle Schichten.
2. Aktualisiere bei beobachtbarem Verhalten die Feature-Spezifikation. Eine reine Erklärung in der
   Dokumentation hat `Spec impact: none`.
3. Schreibe den Service-Test nach Möglichkeit zuerst.
4. Halte Source → Evidence → Reality nachvollziehbar und jede Abfrage mandantenbezogen.
5. Verwende undurchsichtige IDs. Belegnummer, SKU oder ERP-Nummer sind Referenzen, keine Identität.

Ein externes Feld bleibt im verlustfreien `SourceRecord.payload`, solange die Kernlogik es nicht
wiederholt berechnet, filtert, verknüpft, einschränkt, vorhersagt oder für Aktionen benötigt.
Adapter schreiben nie direkt über das ORM und duplizieren keine Geschäftsregeln.

## Sinnvoller Einstieg in den Code

Verfolge eine Bestandsreservierung: `reserve` in `services/core.py`, `_reserve` und den
`TOOLS`-Eintrag in `tools/application.py`, `reserve` in `command_catalog.yaml`, `reserve_stock` in
`workspace_catalog.yaml` sowie die Tests in `test_inventory_and_fulfillment.py` und
`test_application_tools.py`. Genau diese vollständige Form sollte eine neue geregelte Aktion haben.

Prüfe vor einer Erweiterung die generierte [Tool-Referenz](https://docs.runreality.ai/de/tool-usage/). Dort stehen alle
vorhandenen Geschäftsaktionen, Business Events, Projections, Exceptions, MCP-Tools und
Workspace-Aktionen.

## Gemeinsamer Ablauf für jede Erweiterung

Nutze den Repository-Vertrag in `docs/SPEC_DRIVEN_WORKFLOW.md`: specify → clarify/review → plan →
tasks → analyze → implement → verify → review. Die Spezifikation beschreibt zuerst den fachlichen
Nutzen, die kleinste benötigte Änderung und die Akzeptanzgeschichte. Implementiere erst, wenn offene
Fragen geklärt und Constitution-/Analyse-Gates erfüllt sind.

Wähle dann die ähnlichste Vorlage aus dem passenden Kapitel. Lies den echten Service und seine
Tests, statt einen verkürzten Ausschnitt als vollständiges Modul zu kopieren. Baue die Änderung
domain → services → tools → adapters; reine neue Zugänge lassen vorhandene Domain-/Service-Logik
unverändert. Prüfe Schnittstellen, Rechte, Mandantengrenzen, Wiederholung und Herkunft. Neue
Katalogeinträge brauchen Ressourcen-Zuordnung, deutsche Labels und `make docs-generate`.
