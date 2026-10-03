# Mit Reality entwickeln

Reality liefert dir ein operatives Geschäftsmodell und gemeinsame Anwendungsservices zum Erweitern.
Du kannst eine Geschäftsregel ergänzen, Daten aus deinem ERP interpretieren oder eine Fähigkeit für
Agenten und Anwendungen zugänglich machen. Dieselbe Regel dient dann Web, Chat, MCP, API und CLI
über ihre bestehenden Zugänge.

## Drei Dinge, die du entwickeln kannst

| Dein Ziel                   | Ein konkretes Beispiel                                                                                                      | Hier beginnen                                             |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Geschäftslogik erweitern    | Eine unternehmensgebundene Operation ergänzen, die eine Geschäftsbedingung prüft und ihre freigegebene Wirkung erfasst.     | [Geschäftslogik entwickeln](./commands)                   |
| Ein ERP anbinden            | Einen ursprünglichen Auftrags-Payload empfangen, verlustfrei erhalten und seine Positionen und Lieferzusage interpretieren. | [ERP und Datenquellen anbinden](./connectors)             |
| Eine Schnittstelle ergänzen | Einen Agenten oder eine Anwendung Bestand lesen oder über den bestehenden Service eine Reservierung vorbereiten lassen.     | [Agenten- und API-Schnittstellen](./application-surfaces) |

## Beginne mit einem funktionierenden Beispiel

Folge [deiner ersten Erweiterung](./first-extension): Ergänze ein lesendes Agent Tool, das dieselben
Bestandszeilen wie eine bestehende Fähigkeit liefert. Du registrierst sein Eingabeschema, nutzt das
gemeinsame Anwendungswerkzeug und prüfst sein Ergebnis mit den PostgreSQL-Testdaten des Repositorys.

Die Übung ist bewusst klein. Sie zeigt den vollständigen Erweiterungsweg, ohne dass du neue
Geschäftsregeln oder eine Datenbanktabelle erfinden musst.

## Wo Geschäftslogik hingehört

```text
Web / Chat / MCP / API / CLI
             ↓
Gemeinsames Anwendungswerkzeug und Service
             ↓
Unternehmensgebundene Reality-Datensätze
```

Ein Service besitzt die Geschäftsregel. Seine Schnittstellen übersetzen Eingaben und zeigen
Ergebnisse; sie implementieren die Regel nicht erneut. Eine Reservierung prüft zum Beispiel die
Lieferzusage und den verfügbaren Bestand im gemeinsamen Service — unabhängig davon, ob ein Mensch
oder Agent sie angefragt hat.

ERP-Eingang folgt **Source → Evidence → Reality**: den empfangenen Payload erhalten, seine
kaufmännischen Belege interpretieren und die dadurch belegten operativen Datensätze erzeugen. Ein
Connector transportiert Daten; ein Interpreter gibt ihnen geschäftliche Bedeutung. Siehe
[Von Quelldaten zu Reality](/de/integrations/connector-contract).

## Wähle deinen nächsten Schritt

- [Geschäftslogik](./commands): Service, Anwendungsoperation, Katalog und Tests.
- [ERP-Anbindung](./connectors): Quellenidentität, verlustfreier Eingang und Interpretation.
- [Agentenwerkzeuge](./agent-tools): Auffindbarkeit, Schemas, gemeinsame Abfragen und kontrollierte
  Vorschläge.
- [API und CLI](./api-cli): Schlanke Adapter um eine bestehende Fähigkeit.

Änderungen folgen dem Spezifikations- und Testablauf des Repositorys. Ändernde Agentenaufrufe
bereiten einen Vorschlag vor und benötigen menschliche Bestätigung. Jede Abfrage und Änderung bleibt
an ihr Unternehmen gebunden.

Das
[Entwicklungshandbuch im Repository](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/README.md)
enthält vertiefende Anleitungen für Views, Projections, Exception-Ableitungen und
Implementierungsprüfungen.
