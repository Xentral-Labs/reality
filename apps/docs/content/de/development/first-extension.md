# Deine erste Erweiterung

## Ziel und erwartetes Ergebnis

Du ergänzt in einem **lokalen Übungsbranch** einen lesenden Agent Tool namens
`training_inventory_read`. Er zeigt dieselben Bestandszeilen wie `inventory_read`. Du lernst
Registrierung, Schema, Service-Wiederverwendung und Ergebnisprüfung. Es entstehen keine neuen
Tabellen oder Geschäftsregeln. Der Alias ist eine Trainingshilfe, keine zusätzliche Produktfunktion.

## Voraussetzungen

Arbeite im Repository-Hauptverzeichnis mit eingerichteter Python-Umgebung und den Abhängigkeiten aus
der [Installation](../operations/installation). Für den Ergebnistest brauchst du die
PostgreSQL-Testumgebung des Repositorys. Verwende keine Produktionsdatenbank. Lies die
[gemeinsamen Entwicklungsregeln](./reference); auch eigene Produktänderungen durchlaufen Spec,
Review, Plan, Tasks und Tests.

## 1. Die Vorlage verstehen

Öffne `packages/reality-core/src/reality/mcp/catalog.py` und finde `inventory_read` in
`MCP_TOOL_CATALOG`. Name und Label machen den Zugang auffindbar, `read` kennzeichnet den Zugriff,
das Schema beschreibt Eingaben und `_read("inventory")` nutzt den vorhandenen Application Tool. Die
`view`-Option wählt Gesamtbestand oder Bestand pro Lagerort.

## 2. Den Vertrag zuerst testen

Lege `packages/reality-core/tests/test_training_inventory_tool.py` mit diesem Inhalt an. Der erste
Test prüft den Vertrag, der zweite vergleicht tatsächliche Bestandszeilen. `session` und `business`
kommen aus den bestehenden PostgreSQL-Fixtures; die Tests erstellen keine Produktionsdaten.

```python
from decimal import Decimal

from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_tool
from reality.services.core import record_movement


def test_training_inventory_schema():
    original = MCP_TOOL_REGISTRY["inventory_read"]
    training = MCP_TOOL_REGISTRY["training_inventory_read"]
    assert training.access == "read"
    assert training.input_schema == original.input_schema


def test_training_inventory_result(session, business):
    record_movement(
        session, business.tenant.id, "opening_stock", business.item.id, "10",
        to_location_id=business.location.id,
    )
    arguments = {"view": "aggregate", "item_id": business.item.id}
    original = dispatch_tool(session, business.tenant.id, "inventory_read", arguments)
    training = dispatch_tool(
        session, business.tenant.id, "training_inventory_read", arguments
    )
    assert len(original["records"]) == 1
    assert Decimal(original["records"][0]["available"]) == Decimal("10")
    assert training["records"] == original["records"]
```

```bash
.venv/bin/python -m pytest packages/reality-core/tests/test_training_inventory_tool.py -q
```

Vor der Registrierung schlagen die Tests mit dem fehlenden Registry-Schlüssel fehl. Das ist der
erwartete Ausgang.

## 3. Den Zugang ergänzen

Füge den folgenden Eintrag **innerhalb von `MCP_TOOL_CATALOG` direkt nach `inventory_read`** ein.
Übernimm das vollständige Schema; erfinde keine vereinfachten Eingaben. Registry und
Tool-Namensliste werden aus dem Katalog aufgebaut.

```python
    MCPToolDefinition(
        "training_inventory_read",
        "Training: read inventory",
        "Read inventory as cursor pages: labelled item totals or item/location rows with units. Page mode does not write projection caches.",
        "read",
        "Operations",
        _object_schema(
            {
                **PAGE_PROPERTIES,
                "view": {
                    "type": "string",
                    "enum": ["aggregate", "location"],
                    "default": "aggregate",
                },
                "item_id": OPTIONAL_STRING,
                "location_id": OPTIONAL_STRING,
            }
        ),
        _read("inventory"),
    ),
```

## 4. Das Ergebnis prüfen

Führe den Testbefehl erneut aus. Erwartung: **2 Tests bestanden**. Der erste bestätigt lesenden
Zugriff und identisches Schema. Der zweite bestätigt dieselben nichtleeren Bestandszeilen über den
kanonischen Dispatcher. Das ist mehr als ein Syntaxcheck; ohne PostgreSQL lässt sich dieser
Ergebnistest nicht durchführen.

Führe anschließend `make docs-generate` und `make docs-catalog-check` aus. Die Ressourcen-Zuordnung
erfolgt über die vorhandene `inventory`-Zuordnung. Falls die Generierung einen neuen Eintrag ohne
Zuordnung meldet, ergänze `resource_catalog.yaml`; schwäche den Check nicht ab. Prüfe den neuen
Zugang unter Artikel im generierten Katalog. Tool-Discovery und produktive Berechtigungen brauchen
eigene Adaptertests, wenn du aus dieser Übung eine Produktänderung machst.

## 5. Selbst ausprobieren

Erweitere den Ergebnistest mit `view="location"`. Die Zeilen müssen weiterhin mit `inventory_read`
übereinstimmen. Verfolge den Handler bis zum gemeinsamen Bestands-Reader und erkläre, an welcher
Stelle die Berechnung stattfindet.

## Aufräumen und weiterlernen

Entferne den Trainingsalias und seinen Test nach der Übung und regeneriere die Referenz. Für eine
echte neue Fähigkeit definiere zuerst den fachlichen Bedarf. [Agent Tools](./agent-tools) zeigt
lesende und ändernde Zugänge; [Views](./views) erklärt die Anzeige, [Projections](./projections) die
Ableitung und [Commands](./commands) die Operation.
