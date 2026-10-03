# Projections entwickeln

## Das lernst du

Du kannst ein wiederverwendbares Lesemodell ableiten und zeigen, dass es aus Reality reproduzierbar
ist.

## Wann du diesen Baustein brauchst

Mehrere Verbraucher brauchen wiederholt dieselbe berechnete Antwort. Eine reine Anzeige gehört zu
[Views](./views). Prüfe zuerst den [Projection-Katalog](../tool-usage/views), ob die Antwort bereits
existiert.

## Bevor du beginnst

Du brauchst eine definierte Frage, ihre autoritativen Records und einen Service-Test mit PostgreSQL.
Entscheide explizit zwischen Berechnung beim Lesen und materialisiertem Cache; das Beispiel hier ist
materialisiert.

## Durchgearbeitetes Beispiel

Nutze eine Projection, wenn mehrere Verbraucher wiederholt dieselbe abgeleitete Antwort brauchen –
beispielsweise physischen, reservierten und verfügbaren Bestand. Definiere zuerst die Frage, danach
die maßgeblichen Reality-Datensätze und die Formel. Eine Projection ist wiederaufbaubar und wird nie
zu einer weiteren Quelle der Wahrheit.

Registriere Erzeuger, Verbraucher und ungültig machende Business Events. Halte jede Abfrage
mandantenbezogen, definiere für Register eine deterministische Reihenfolge und Paginierung und biete
einen Erklärpfad zu den zugrunde liegenden Datensätzen.

### Codebeispiel: Bestandsposition

Verfolge `_inventory_rows` in `packages/reality-core/src/reality/services/projections.py`:

- `OPERATIONAL_PROJECTIONS` nennt die unterstützte Projection.
- `_build_operational_rows` ruft `inventory_rows` mandantenbezogen auf und erzeugt pro Artikel einen
  stabilen `record_key` mit physischem, reserviertem, verfügbarem, eingehendem und erwartetem
  Bestand.
- `refresh_operational_projections` baut veraltete Zeilen neu auf; `projection_rows` ist der
  gemeinsame, deterministisch sortierte Leseeinstieg.
- `config/projection_catalog.yaml` beschreibt Datensätze, Berechnung, Ausgaben und Verbraucher.

Der vollständige Row Builder aus dem bestehenden Modul (seine Imports und Hilfsfunktionen bleiben im
Modul):

```python
def _inventory_rows(
    session: Session, tenant_id: str, item_ids: frozenset[str] | set[str] | None = None
) -> dict[str, dict[str, Any]]:
    """Stock, for the whole company or for named articles alone."""
    from reality.services.core import inventory_rows

    return {
        row["item"].id: {
            "item_id": row["item"].id,
            "item": row["item"].name,
            "sku": row["item"].sku,
            **quantity_unit(row["item"]),
            "aggregation": "item_all_locations",
            "physical": row["physical"],
            "reserved": row["reserved"],
            "blocked": row["blocked"],
            "available": row["available"],
            "incoming": row["incoming"],
            "projected": row["projected"],
            "receipt_ids": [movement.id for movement in row["receipts"]],
            "issue_ids": [movement.id for movement in row["issues"]],
        }
        for row in inventory_rows(
            session, tenant_id, item_ids=set(item_ids) if item_ids is not None else None
        )
    }
```

### Vorher und nachher

Ein Testartikel hat 10 Stück physischen Bestand, keine Sperren und keine Reservierung. Erwartung:
physisch 10, reserviert 0, verfügbar 10. Nach einer Reservierung von 3 Stück: physisch 10,
reserviert 3, verfügbar 7. Nach Aufhebung: wieder 10 / 0 / 10. Die Werte stammen aus vorhandenen
Records; der Rebuild erzeugt keine neue Bewegung.

## Schritt für Schritt

1. Definiere Records, Formel, Erklärung und Aktualitätsvertrag in Spec und Service-Test. Verwende
   den Vorher-/Nachher-Fall oben als Erwartung.
2. Implementiere den Row Builder im gemeinsamen Projection-Service. Verwende die vorhandenen Reader
   und stabile `record_key`-Identitäten.
3. Binde ihn in `_build_operational_rows` ein und ergänze `OPERATIONAL_PROJECTIONS` sowie
   `projection_catalog.yaml` für eine materialisierte Projection.
4. Verbinde Verbraucher und Aktualisierung. Ergänze Event-Invalidierung, falls die globale Sequenz
   nicht genügt. Für Berechnung beim Lesen brauchst du keinen zusätzlichen Cache.
5. Übernimm passende Tenant-, Rebuild- und Stale-Fälle aus `test_materialized_projections.py`.
   Ergänze Katalog- und HTTP-Tests für die tatsächlich angebotenen Oberflächen.
6. Ergänze Ressourcen-Zuordnung, Label und `make docs-generate`.

## Ergebnis prüfen

Baue in einer Testfirma Artikel, Commitment, Reservation und Movement über die vorhandenen
Test-Fixtures und Services auf. Prüfe vor und nach einer Reservierung, dass physischer Bestand
unverändert bleibt und reservierter/verfügbarer Bestand sich korrekt ändern. Ein erneuter Rebuild
muss dieselbe Antwort liefern. Ein zweiter Tenant darf keine Zeilen sehen. Teste neue Events,
veraltete Ergebnisse, deterministische Sortierung und Paginierung. Prüfe die Erklärungsspur von der
Ergebniszeile bis zu den Reality-Datensätzen. Registriere neue Einträge im Ressourcen-Katalog und
generiere die Referenz.

## Selbst ausprobieren

Erweitere zunächst den Testfall um eine zweite Reservierung und deren Aufhebung. Sage physisch,
reserviert und verfügbar vorher voraus und vergleiche sie nach dem Rebuild. Ändere die Formel erst,
wenn ein neuer fachlicher Bedarf spezifiziert ist.

## Häufige Fehler

Eine Ableitung als neue Autorität speichern; alle Projections für Caches halten; veraltete
Ergebnisse ohne Kennzeichnung zeigen; Tenant-Filter oder stabile Sortierung vergessen.

## Weiterlesen

[Views](./views) macht das Ergebnis sichtbar. [Ausnahmen](./exceptions) leitet daraus
Handlungsbedarf ab.
