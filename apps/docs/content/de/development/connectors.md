# Ein ERP-System anbinden

Eine Integration besteht aus zwei unabhängigen Teilen: Der Connector transportiert und speichert den
externen Payload; der Interpreter leitet daraus Evidence- und Reality-Datensätze ab. So kann ein
unbekanntes Objekt verlustfrei erhalten bleiben, ohne eine nicht verstandene Bedeutung
vorzutäuschen.

## Vorhandene Erweiterungswege

| Art                          | Hier erweitern                               | Beispiel                            |
| ---------------------------- | -------------------------------------------- | ----------------------------------- |
| Benanntes ERP-Objekt         | `services/core.py` und `SOURCE_INTERPRETERS` | `("shopify", "order")`              |
| CSV-, JSON- oder JSONL-Datei | `services/file_interpreters.py`              | `sales_order`, `inventory_snapshot` |
| Auswählbarer Connector       | `config/connector_catalog.yaml`              | Odoo, Xentral, weclapp              |
| Quellenfähigkeit             | `SourceCapability` über Service/API          | Quelltyp → Zieltyp                  |

`connector_catalog.yaml` beschreibt nur eine zugangsdatenfreie Hülle und mögliche Fähigkeiten. Dort
stehen weder Anmeldung noch Transport oder Feldzuordnung. Eine installierte Hülle bedeutet auch
nicht, dass bereits ein Interpreter existiert.

## Beispiel: Shopify-Auftrag

`services/core.py::_shopify_interpretation` liest den unveränderlichen `SourceRecord.payload`,
ordnet oder erzeugt für Erstversionen Evidence und Reality, verknüpft sie mit `source_record_id` und
erzeugt Ereignisse. Geänderte Versionen benötigen eine Prüfung, ohne bestehende Geschäftsdatensätze
zu ersetzen. Die Registrierung erfolgt ausdrücklich:

```python
SOURCE_INTERPRETERS = {
    ("shopify", "order"): _shopify_interpretation,
}
```

`process_import_job` wählt nach `(source_system, source_type)`. Fehlt der Interpreter, erhält der
Job den Status `unmapped` und das Ergebnis `interpreter_unavailable`. Bei unklarer fachlicher
Bedeutung soll der Interpreter `InterpretationNeedsReview` auslösen und nicht raten.

## Ein ERP-Objekt ergänzen

1. Speichere den Hersteller-Payload unverändert als versionierten `SourceRecord`. Anmeldung und
   Abruf bleiben im Adapter; dieser ruft den gemeinsamen Ingest-Service auf.
2. Ergänze Quelltyp und vorgesehenes Ziel in der Connector-Hülle, wenn sie auswählbar sein sollen.
3. Implementiere einen mandantenbezogenen Interpreter. Verwende Services wie `create_document`,
   `create_item` oder `record_movement`; der Transportadapter schreibt keine ORM-Zeilen.
4. Erhalte `source_record_id` an Evidence/Reality-Datensätzen und schreibe die normalen Business
   Events.
5. Registriere den genauen Schlüssel `(source_system, source_type)` in `SOURCE_INTERPRETERS`.
6. Teste Erstimport, Wiederholung, externe Korrektur/Ersetzung, mehrdeutige und fehlerhafte Eingaben
   sowie Mandantentrennung. Prüfe die Spur bis zum ursprünglichen Payload.

Bei Dateiimporten ergänzt du ein Ziel in `FILE_INTERPRETER_TARGETS`, definierst Pflicht- und
optionale Spalten in `FILE_MAPPING_PROFILES` und implementierst den Zweig in `interpret_artifact`.
Eine menschliche Nummer darf nicht stillschweigend zugeordnet werden, wenn sie nicht eindeutig ist.

Vor dem Transport die [Connector-Vereinbarung](../integrations/connector-contract) lesen.
