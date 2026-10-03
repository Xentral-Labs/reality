# Agent Tools ergänzen

## Das lernst du

Du kannst eine vorhandene Operation für einen Agenten aufrufbar machen und ihren
Read-/Proposal-Vertrag prüfen.

## Wann du diesen Baustein brauchst

Ein Agent Tool ist die aufrufbare Schnittstelle für einen Agenten. Es ist nicht der fachliche
Service und nicht die Web Action. Wenn der Command bereits existiert, ergänze nur den Zugang. Ein
lesendes Tool darf sofort lesen; ein änderndes Tool bereitet einen Vorschlag zur getrennten
Bestätigung vor.

## Bevor du beginnst

Der Service und das Application Tool existieren bereits. Für Änderungen kennst du die exakte
Vorschau und den getrennten Freigabeweg; für Reads verwendest du die vorhandene Leseberechtigung.
Beginne gegebenenfalls mit der [ersten Erweiterung](./first-extension.md).

## Durchgearbeitetes Beispiel

Verfolge `reservation_propose` in `packages/reality-core/src/reality/mcp/catalog.py`. Dies ist der
vorhandene Registrierungseintrag im bestehenden Modul; `MCPToolDefinition`, `_object_schema`,
`STRING`, `OPTIONAL_STRING` und `_propose` sind dessen vorhandene Hilfen. Der Ausschnitt ist keine
eigenständige Python-Datei.

```python
MCPToolDefinition(
        "reservation_propose",
        "Propose reservation",
        "Prepare a stock reservation without allocating before confirmation. Without location_id it reserves at the promise's own warehouse; with it, the rest at that active warehouse holding stock (spec 303), for example one the stock_in_another_location finding names.",
        "propose",
        "Mutations",
        _object_schema(
            {
                "commitment_id": STRING,
                "quantity": OPTIONAL_STRING,
                "handling_unit_id": OPTIONAL_STRING,
                "lot_id": OPTIONAL_STRING,
                "serial_unit_id": OPTIONAL_STRING,
                "location_id": OPTIONAL_STRING,
            },
            required=("commitment_id",),
        ),
        _propose("reserve"),
    ),
```

Der Schlüssel `commitment_id` ist Pflicht; Menge und weitere Dimensionen sind optional. Mengen
werden als genaue Dezimalzeichenfolgen übertragen. `_propose("reserve")` ordnet das Tool dem
vorhandenen Application Tool zu. Es reserviert beim Vorschlag noch keinen Bestand.

## Schritt für Schritt

1. Spezifikation und Tests zuerst: benenne Eingaben, Ergebnis, Leseberechtigung und
   Bestätigungsgrenze. Folge dem Spec-Kit-Workflow des Repositorys.
2. Prüfe den vorhandenen Command und `TOOLS` in `tools/application.py`; ergänze dort keine zweite
   Service-Implementierung.
3. Ergänze eine `MCPToolDefinition` mit stabilem Namen, Beschreibung und exaktem Eingabeschema.
   Kopiere nur die Felder, die deine Operation wirklich braucht. Verwende opake IDs und passende
   Pflichtfelder.
4. Verwende für Änderungen den vorhandenen Proposal-Weg. Lies die exakte serverseitige Vorschau; die
   bewusste menschliche Freigabe erfolgt getrennt über `proposal_approve_and_execute`. Übernimm den
   aktuellen Freigabe-/Review-Vertrag dieses Tools, statt `approved=True` automatisch zu setzen.
5. Für reine Reads folge `inventory_read` und `_read` im selben Katalog. Eine Query braucht nicht
   zwingend einen neuen Command oder eine Projection.
6. Prüfe Auffindbarkeit, Schema, Vorschlag ohne Wirkung, Ablehnung, Bestätigung, Wiederholung und
   Mandantentrennung. Vorlagen: `test_mcp_read_contract.py`, `test_chat_mcp_business_commands.py`
   und `test_agent_command_parity.py` unter `packages/reality-core/tests/`.
7. Ordne das Tool über die normalen Katalogbeziehungen einem Geschäftsobjekt zu. Bei neuen
   Commands/Views/Projections ergänze `resource_catalog.yaml` und dessen deutsche Labels. Führe
   `make docs-generate` aus und prüfe die generierte Referenz.

## Ergebnis prüfen

Nutze eine Testfirma mit einem echten Commitment und Bestand. Löse zunächst die opake Commitment-ID
über die vorhandenen Reads auf. Rufe das Vorschlags-Tool mit dieser ID und `quantity: "5"` auf: Es
liefert einen Vorschlag, aber es gibt noch keine neue Reservation. Prüfe die Vorschau und genehmige
diesen konkreten Vorschlag ausdrücklich. Lies danach Reservations und Commitments: Die angewandte
Menge und eventuelle Fehlmenge müssen zum Service-Ergebnis passen. Dieselbe Anfrage in einer anderen
Firma darf den Datensatz nicht offenlegen.

[Web Actions ergänzen](./web-actions.md) zeigt den Zugang für Menschen zu derselben Operation.

## Selbst ausprobieren

Vergleiche `inventory_read` mit `reservation_propose`. Erkläre, warum ein Aufruf sofort lesen darf
und der andere erst einen Vorschlag liefert. Passe danach nur die Beschreibung eines lokalen
Trainings-Tools an; erwartet wird dieselbe Eingabe und dieselbe fachliche Antwort.

## Häufige Fehler

Ein Schema allein macht noch keine sichere Operation. Nicht direkt ORM schreiben, `approved=True`
automatisch setzen oder fremde IDs ungeprüft weiterreichen. Kopiere keine Mutation als Read.

## Weiterlesen

[Web Actions](./web-actions.md) zeigt den menschlichen Zugang; [API und CLI](./api-cli.md) die weiteren
Adapter.
