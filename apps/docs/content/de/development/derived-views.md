# Kennzahlen und operative Warnungen entwickeln

Prüfe zuerst die generierten Kataloge für [Projections](../tool-usage/views) und
[Exceptions](../tool-usage/exceptions), damit dieselbe Frage nicht zweimal beantwortet wird.

## Eine Projection ergänzen

Nutze eine Projection, wenn mehrere Verbraucher wiederholt dieselbe abgeleitete Antwort brauchen –
beispielsweise physischen, reservierten und verfügbaren Bestand. Definiere zuerst die Frage, danach
die maßgeblichen Reality-Datensätze und die Formel. Eine Projection ist wiederaufbaubar und wird nie
zu einer weiteren Quelle der Wahrheit.

Registriere Erzeuger, Verbraucher und ungültig machende Business Events. Halte jede Abfrage
mandantenbezogen, definiere für Register eine deterministische Reihenfolge und Paginierung und biete
einen Erklärpfad zu den zugrunde liegenden Datensätzen.

### Codebeispiel: Bestandsposition

Verfolge `inventory_position` in `packages/reality-core/src/reality/services/projections.py`:

- `OPERATIONAL_PROJECTIONS` nennt die unterstützte Projection.
- `_build_operational_rows` ruft `inventory_rows` mandantenbezogen auf und erzeugt pro Artikel einen
  stabilen `record_key` mit physischem, reserviertem, verfügbarem, eingehendem und erwartetem
  Bestand.
- `refresh_operational_projections` baut veraltete Zeilen neu auf; `projection_rows` ist der
  gemeinsame, deterministisch sortierte Leseeinstieg.
- `config/projection_catalog.yaml` beschreibt Datensätze, Berechnung, Ausgaben und Verbraucher.

Implementiere den Row Builder, binde ihn in `_build_operational_rows` ein und ergänze Name und
Katalogeintrag. Ergänze Event-Invalidierung, falls die globale Sequenz nicht genügt. Kopiere
Mandanten-, Rebuild- und Stale-Tests aus `test_materialized_projections.py`; ergänze Katalog- und
HTTP-Test, wenn diese Oberflächen die Projection anbieten.

## Eine Ausnahmeableitung ergänzen

Nutze eine Ausnahme, wenn ein deterministischer aktueller Zustand operative Aufmerksamkeit braucht.
Definiere:

- die genaue Bedingung und wann sie nicht mehr gilt,
- Schweregrad und stabile Klassenidentität,
- betroffenen Reality-Datensatz und kürzeste Spur,
- die fachlich zuständige Rolle sowie
- ausführbare Nachweise für Ableitung, Mandantentrennung und Behebung.

Registriere Klasse und Ableitung im Katalog der operativen Ausnahmen. Erzeuge kein manuell
geschlossenes Ticket und kopiere keinen Status auf ein Document. Braucht die Behebung eine Änderung,
verwende einen normalen Command mit seiner Freigabegrenze.

### Codebeispiel: gefährdetes Commitment

`packages/reality-core/src/reality/services/exceptions.py` enthält `_outgoing_commitment_at_risk`
und registriert ihn in `DERIVATION_REGISTRY`. Der Eintrag in
`config/operational_exception_catalog.yaml` definiert stabile Klassen-ID, Bezeichnung, Schweregrad,
betroffenen Datensatztyp, Zuständigkeit und Evidence. Verschwindet die Bedingung, verschwindet auch
die abgeleitete Exception.

Katalogeintrag und Ableitung werden gemeinsam ergänzt. Teste Entstehung und Verschwinden,
Mandantentrennung, stabile Ursachen-IDs und Erklärungsspur. Vorlagen sind
`operational_exceptions/test_derivation.py`, `test_coverage.py` und `test_explanation.py`.
