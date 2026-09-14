# Neue Geschäftsabläufe implementieren

Eine Geschäftsaktion verändert den Zustand. Die vorhandene Bestandsreservierung ist ein
vollständiges Beispiel.

Die generierte [Tool-Referenz](../tool-usage/commands) zeigt den vorhandenen Bestand samt den
genauen öffentlichen Parametern jedes Agenten-Tools.

## `reserve` durch den Code verfolgen

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
5. HTTP, MCP, CLI und Chat rufen dieselbe Application-Funktion auf. Dort stehen keine eigenen
   Regeln.

```python
def reserve(session, tenant_id, commitment_id, quantity=None, *, action_id=None):
    commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
    require_not_held(session, tenant_id, "commitment", commitment.id)
    # prüfen, mit Decimal berechnen, Reservation erzeugen, Event schreiben
    return ReservationResult(...)
```

Der Wrapper liefert ein Anwendungsergebnis und kein ORM-Objekt:

```python
def _reserve(session, tenant_id, arguments):
    result = reserve(session, tenant_id, arguments["commitment_id"], arguments.get("quantity"))
    return {"reservation_id": result.reservation.id,
            "requested": result.requested, "applied": result.reserved,
            "shortage": result.shortage}
```

## Eine neue Aktion Schritt für Schritt

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

Eine reine Berechnung, ein aktueller Risikozustand oder ERP-Transport sind keine Geschäftsaktion,
sondern Projection, Exception oder Connector. Liefer- und Reservierungsstatus gehören nie an ein
Document; sie werden aus Reality-Datensätzen abgeleitet.
