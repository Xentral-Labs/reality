# API und CLI ergänzen

## Das lernst du

Du kannst eine vorhandene Operation über HTTP oder CLI zugänglich machen und ihre Grenzen prüfen.

## Wann du diesen Baustein brauchst

Eine unterstützte Anwendung benötigt HTTP, oder Entwicklung und Administration brauchen einen
Terminalzugang. Für Agenten verwende [Agent Tools](/de/development/agent-tools), für Bedienabläufe
[Web Actions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/web-actions.md).

## Bevor du beginnst

Der gemeinsame Service muss bereits existieren und getestet sein. Lies
[Commands](/de/development/commands) und die
[Entwicklungsregeln](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/reference.md).
Nutze PostgreSQL-Testfixtures und die authentifizierte Tenant-Grenze.

## Durchgearbeitetes Beispiel

Folge `tenant_inventory_control` in `packages/reality-core/src/reality/web/api.py`: Die Route
`/inventory-control` ruft das gemeinsame Lesemodell mit Tenant und Seitenparametern auf. Für
Änderungen zeigt `commitment_reserve` in `packages/reality-core/src/reality/cli/app.py` den Ablauf:
`selected_tenant` → `reserve` → Ergebnisanzeige. Der Decorator `@commitment_app.command("reserve")`
registriert den CLI-Unterbefehl. Beide Adapter enthalten keine eigene Bestandsformel.

## Schritt für Schritt

1. Schreibe zuerst einen Adapter-Test für Erfolg, ungültige Eingabe und fremden Tenant.
2. Definiere HTTP-Request/Response mit Pydantic beziehungsweise typisierte Typer-Argumente.
3. Löse den Tenant über den bestehenden Zugang auf und rufe den gemeinsamen Service auf.
4. Übertrage Domain-Fehler über die bestehenden Fehlerkonventionen.
5. Prüfe `/openapi.json` für HTTP oder die CLI-Hilfe für Argumente. Ergänze den typisierten
   Web-Client nur bei Bedarf.

## Ergebnis prüfen

Vergleiche mit demselben Fixture die Adapter-Antwort und den direkten Service-Read. Prüfe
Authentifizierung, Tenant-Isolation, Validierung und sichere Fehler. Bei Änderungen prüfe den
anschließenden autoritativen Read. Agentenfreigaben bleiben Teil des Agentenablaufs; ein HTTP-Zugang
ersetzt sie nicht.

## Selbst ausprobieren

Zeichne die Parameterkette für einen zusätzlichen Bestandsfilter auf: HTTP/CLI → gemeinsamer Reader
→ Ergebnis. Prüfe zuerst, ob der Reader diesen Filter bereits unterstützt; ergänze keine zweite
Berechnung.

## Häufige Fehler

ORM-Schreibzugriffe im Adapter; Tenant aus ungeprüfter Eingabe übernehmen; Domain-Regeln kopieren;
Erfolg melden, bevor das Ergebnis verifiziert ist.

## Weiterlesen

[Agent Tools](/de/development/agent-tools),
[Web Actions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/web-actions.md)
und die
[gemeinsamen Regeln](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/reference.md).
