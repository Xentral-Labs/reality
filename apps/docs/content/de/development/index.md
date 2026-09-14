# Reality-Core-Entwicklung

Dieser Bereich richtet sich an Mitwirkende, die das gemeinsame Geschäftsverhalten von Reality
ändern. ERP-Berater sollten normalerweise bei
[Was kann angepasst werden?](../integrations/customization) beginnen und nur hierher wechseln, wenn
das benötigte Command, die Projection oder Exception noch nicht existiert.

## Was Core-Entwickler ergänzen können

| Du möchtest …                                                     | Dann erweiterst du …                | Anleitung                                                                    |
| ----------------------------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------- |
| ein weiteres ERP-Objekt verlustfrei übernehmen und interpretieren | Connector-Fähigkeit und Interpreter | [Ein weiteres ERP anbinden](./connectors)                                    |
| einen Vorgang wie eine Bestandsreservierung ausführen             | Service und Geschäftsaktion         | [Geschäftsaktionen ergänzen](./commands)                                     |
| eine wiederverwendbare Position wie verfügbaren Bestand berechnen | Projection                          | [Projections und Ausnahmen ergänzen](./derived-views)                        |
| ein aktuelles Risiko in die operative Arbeitsliste bringen        | Exception-Ableitung                 | [Projections und Ausnahmen ergänzen](./derived-views#eine-ausnahme-ergänzen) |
| eine vorhandene Funktion einem weiteren Client anbieten           | nur den Adapter                     | [Funktionen sicher bereitstellen](./application-surfaces)                    |

Beginne nicht bei einer Seite oder einem API-Endpunkt, sondern bei der fehlenden Geschäftsfrage. Die
Reihenfolge ist immer:

```text
Domain-Datensätze → Application Service → Application Tool → Adapter
```

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

Prüfe vor einer Erweiterung die generierte [Tool-Referenz](../tool-usage/). Dort stehen alle
vorhandenen Geschäftsaktionen, Business Events, Projections, Exceptions, MCP-Tools und
Workspace-Aktionen.
