# Funktionen über API und MCP anbieten

Die generierte [Tool-Referenz](../tool-usage/commands) listet Zugriffsklasse, Parameter,
Pflichtfelder und Standardwerte aller aktuell registrierten Tools.

Domänen- und Anwendungsservices besitzen das Verhalten. Web, API, MCP, CLI und Chat sind Adapter
derselben Funktion.

## Oberflächen auswählen

- Ergänze eine Web-Ansicht, wenn eine menschliche Rolle das Ergebnis regelmäßig im Alltag braucht.
- Ergänze eine API-Operation, wenn ein anderer unterstützter Client den Anwendungscontract braucht.
- Ergänze ein MCP-Werkzeug, wenn ein Unternehmensagent die Funktion finden und aufrufen soll.
- Stelle sie im CLI für Entwicklung oder operative Administration bereit.
- Lass Reality fragen das registrierte Anwendungswerkzeug nutzen; erzeuge keinen eigenen
  Chat-Geschäftsweg.

Leseoperationen dürfen sofort laufen. Änderungen aus Chat oder von einem Agenten erzeugen einen
`ChangeProposal(status=proposed)` mit exakter serverseitiger Vorschau und brauchen eine getrennte
menschliche Freigabe. Leseberechtigung bedeutet niemals automatisch Änderungsberechtigung.

Jeder Adapter erhält Mandantengrenze, typisierte Validierung, sichere Fehler und dieselbe
Prüf-Abfrage. Für HTTP ist `/openapi.json` der laufenden API maßgeblich. Für Agentenwerkzeuge sind
MCP-Katalog und Eingabeschemas maßgeblich.

## Wo welche Änderung hingehört

| Oberfläche       | Datei                                                    | Verantwortung                                                  |
| ---------------- | -------------------------------------------------------- | -------------------------------------------------------------- |
| Gemeinsames Tool | `packages/reality-core/src/reality/tools/application.py` | Argumente prüfen, Service aufrufen, Ergebnis formen            |
| HTTP             | `packages/reality-core/src/reality/web/api.py`           | Request/Response-Modell, Authentifizierung und Mandantengrenze |
| HTTP-Lesemodell  | `packages/reality-core/src/reality/web/read_models.py`   | Leseausgabe zusammensetzen, nie ändern                         |
| MCP              | `packages/reality-core/src/reality/mcp/catalog.py`       | auffindbarer Name, JSON-Schema und Tool-Zuordnung              |
| Web-Client       | `apps/web/src/api.ts`                                    | typisierter HTTP-Aufruf                                        |
| Web-Ablauf       | `apps/web/src/App.tsx` und Feature-Komponenten           | Darstellung und Interaktion                                    |

## Beispiel: Eine Änderung für Agenten anbieten

Prüfe zuerst, dass Service und Application `Tool` bereits existieren. Ergänze im MCP-Katalog eine
Proposal-Definition, deren Eingabeschema undurchsichtige IDs verwendet. Ordne sie dem vorhandenen
Application Tool zu, nicht dem ORM oder Service-Interna. Der Aufruf erzeugt ein `ChangeProposal`;
ein eigener Freigabeaufruf erhält `proposal_id` und `approved`. Nach der Ausführung wird das
Ergebnis über das maßgebliche Register kontrolliert.

Für HTTP definierst du Pydantic-Request und -Response sowie eine Route, die mit dem
authentifizierten `tenant_id` denselben Service oder dasselbe Application Tool aufruft. Prüfe
`/openapi.json` und ergänze danach die typisierte Client-Methode. Eine React-Komponente darf
`shortage` darstellen, aber Verfügbarkeit nicht anders als der Service berechnen.

## Tests, bevor die Oberfläche fertig ist

- Application-Tool-Test für genauen Argument- und Ergebnisvertrag;
- HTTP-Grenztest für Auth, Mandantentrennung, Validierung und sichere Fehler;
- MCP-Katalogtest für Schema und Zuordnung einschließlich Proposal-Pflicht bei Änderungen;
- Web-Test für Laden, leeres Ergebnis, Fehler und Erfolg ohne kopierte Geschäftsregeln.
