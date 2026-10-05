# ERP und Datenquellen anbinden

Beginne mit
[Ein Beispiel-ERP schrittweise anbinden](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/integrations/example-erp.md):
erst Zusagen, dann echte Lieferungen, danach die für deine Frage benötigten Daten. Das Kapitel zeigt
je Stufe die fachliche Ausgabe, bevor diese Anleitung die Implementierung erklärt.

## Das lernst du

Du kannst Transport und Interpretation trennen und einen ERP-Auftrag verlustfrei bis zur operativen
Verpflichtung verfolgen.

## Wann du diesen Baustein brauchst

Eine Integration besteht aus zwei unabhängigen Teilen: Der Connector transportiert und speichert den
externen Payload; der Interpreter leitet daraus Evidence- und Reality-Datensätze ab. So kann ein
unbekanntes Objekt verlustfrei erhalten bleiben, ohne eine nicht verstandene Bedeutung
vorzutäuschen.

## Bevor du beginnst

Ein Original-Payload, Quellidentität und Versionsvertrag müssen vorhanden sein. Arbeite in einer
Testfirma; bewahre Zugangsdaten außerhalb der Fixtures. Lies zuerst den
[Von Quelldaten zu Reality](/de/integrations/connector-contract).

| Art                          | Hier erweitern                               | Beispiel                            |
| ---------------------------- | -------------------------------------------- | ----------------------------------- |
| Benanntes ERP-Objekt         | `services/core.py` und `SOURCE_INTERPRETERS` | `("shopify", "order")`              |
| CSV-, JSON- oder JSONL-Datei | `services/file_interpreters.py`              | `sales_order`, `inventory_snapshot` |
| Auswählbarer Connector       | `config/connector_catalog.yaml`              | Odoo, Xentral, weclapp              |
| Quellenfähigkeit             | `SourceCapability` über Service/API          | Quelltyp → Zieltyp                  |

`connector_catalog.yaml` beschreibt nur eine zugangsdatenfreie Hülle und mögliche Fähigkeiten. Dort
stehen weder Anmeldung noch Transport oder Feldzuordnung. Eine installierte Hülle bedeutet auch
nicht, dass bereits ein Interpreter existiert.

## Durchgearbeitetes Beispiel

`services/core.py::_shopify_interpretation` liest den unveränderlichen `SourceRecord.payload`,
ordnet oder erzeugt für Erstversionen Evidence und Reality, erhält die Herkunft über Evidence und
die kürzesten Reality-Beziehungen und erzeugt Ereignisse. Unterstützte
Mengenreduzierungen/Stornierungen laufen über den gemeinsamen Änderungsservice; andere Änderungen
benötigen Prüfung. Bestehende Evidence wird nicht ersetzt. Die Registrierung erfolgt ausdrücklich:

```python
SOURCE_INTERPRETERS = {
    ("shopify", "order"): _shopify_interpretation,
}
```

`process_import_job` wählt nach `(source_system, source_type)`. Fehlt der Interpreter, erhält der
Job den Status `unmapped` und das Ergebnis `interpreter_unavailable`. Bei unklarer fachlicher
Bedeutung soll der Interpreter `InterpretationNeedsReview` auslösen und nicht raten.

## Schritt für Schritt

1. Speichere den Hersteller-Payload unverändert als versionierten `SourceRecord`. Anmeldung und
   Abruf bleiben im Adapter; dieser ruft den gemeinsamen Ingest-Service auf.
2. Ergänze Quelltyp und vorgesehenes Ziel in der Connector-Hülle, wenn sie auswählbar sein sollen.
3. Implementiere einen mandantenbezogenen Interpreter. Verwende Services wie `create_document`,
   `create_item` oder `record_movement`; der Transportadapter schreibt keine ORM-Zeilen.
4. Evidence verweist auf den SourceRecord; Reality verwendet die kürzeste passende Evidence- oder
   Reality-Beziehung. Dupliziere nicht auf jedem abgeleiteten Datensatz einen
   SourceRecord-Fremdschlüssel. Schreibe die normalen Business Events.
5. Registriere den genauen Schlüssel `(source_system, source_type)` in `SOURCE_INTERPRETERS`.
6. Teste Erstimport, Wiederholung, externe Korrektur/Ersetzung, mehrdeutige und fehlerhafte Eingaben
   sowie Mandantentrennung. Prüfe die Spur bis zum ursprünglichen Payload.

Bei Dateiimporten ergänzt du ein Ziel in `FILE_INTERPRETER_TARGETS`, definierst Pflicht- und
optionale Spalten in `FILE_MAPPING_PROFILES` und implementierst den Zweig in `interpret_artifact`.
Eine menschliche Nummer darf nicht stillschweigend zugeordnet werden, wenn sie nicht eindeutig ist.

Vor dem Transport die [Von Quelldaten zu Reality](/de/integrations/connector-contract) lesen.

## Ergebnis prüfen

Arbeite das
[ERP-Auftragsbeispiel](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/integrations/order-example.md)
zusammen mit dem [Von Quelldaten zu Reality](/de/integrations/connector-contract) durch. Verwende
zuerst ein Original-Payload als Fixture. Ein Import muss SourceRecord → Document/DocumentLine →
Commitment nachvollziehbar erzeugen; ein Replay darf keine zweite operative Verpflichtung erzeugen.
Eine korrigierte Version bleibt ein neuer SourceRecord und darf einen bereits interpretierten
Geschäftsvorgang nicht still überschreiben. Prüfe den unbekannten Objekttyp separat: Der Payload
bleibt erhalten, auch wenn keine Interpretation möglich ist.

Für wiederkehrenden Abruf gilt der gemeinsame Scheduling-Vertrag in
`docs/features/scheduled-jobs.md`: Registry und Services verwenden, keine Browser-Timer oder
API-Prozessschleifen. Eine weitere Anbindung braucht keinen zweiten Scheduler.

## Selbst ausprobieren

Liefere denselben Fixture-Payload zweimal. Erwartet: keine zweite operative Verpflichtung. Ergänze
dann ein unbekanntes externes Feld in einer neuen Version. Erwartet: das Original bleibt erhalten,
ohne automatisch ein neues typisiertes Feld oder einen still überschriebenen Geschäftsvorgang zu
erzeugen.

## Häufige Fehler

Transport schreibt keine Domain-ORM-Zeilen. Menschliche Nummern sind keine Identität. Unbekannte
Bedeutung nicht erraten; keine Source-Fremdschlüssel entlang bereits vorhandener
Evidence-/Reality-Beziehungen duplizieren.

## Weiterlesen

Für vollständige Quellfälle:
[Xentral anbinden](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/integrations/xentral.md),
[Shopify anbinden](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/integrations/shopify.md)
und
[Odoo anbinden](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/integrations/odoo.md).
Die [Abdeckungsmatrix](/de/integrations/connector-contract#vollständigkeit-und-abnahme) definiert,
wann dein vereinbarter Umfang fertig ist.

[Technische Umsetzung eines Auftragsimports](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/integrations/order-example.md)
zeigt den Implementierungsweg; [Von Quelldaten zu Reality](/de/integrations/connector-contract)
erklärt das gemeinsame Konzept und seine Regeln.
[Gemeinsame Regeln](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/reference.md)
enthält Scheduling- und Spec-Hinweise.

Für angenommene Auftragserfüllung und angekündigte Retouren beschreibt
[Einen Vorgang übernehmen](/de/integrations/operational-cases) die manuelle Übernahme und geprüfte
Rückgabe. Der
[Wartungsvertrag](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/integrations/operational-cases.md)
erklärt die gemeinsamen Eingangspunkte und Ausführungsprüfungen.
