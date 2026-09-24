# API und Werkzeuge

Reality stellt mehrere Adapter um dieselben Anwendungsdienste bereit. Wähle die Schnittstelle, die
zum Akteur passt – nicht ein anderes Geschäftsverhalten.

| Schnittstelle      | Hauptzweck                                           |
| ------------------ | ---------------------------------------------------- |
| Product Web        | Authentifizierte Arbeit und Prüfung durch Menschen   |
| API                | HTTP-Grenze für Browser und Integrationen            |
| CLI                | Abläufe für Entwicklung und Betrieb                  |
| MCP                | Authentifizierte Werkzeuge für Unternehmensagenten   |
| Chat / Ask Reality | Dialogorientierte Abfragen und bestätigte Vorschläge |

Um diese Funktionen mit einem externen Agenten zu nutzen, folge der Anleitung
[Einen MCP-Client verbinden](./connect-mcp). Sie beschreibt die aktuelle Einrichtung über HTTPS und
OAuth, minimale Berechtigungen, einen ersten Lesezugriff, kontrollierte Änderungen, Verifikation und
Widerruf.

Die aktuelle Einrichtung enthält bewusst einen menschlichen Schritt: Ein Mensch meldet sich im
Browser an, erstellt oder wählt das Unternehmen und bestätigt einen eingeschränkten OAuth-Grant.
Nach dieser Übergabe arbeitet der Agent direkt über MCP und darf Registrierung oder Freigabe des
Menschen nicht automatisieren.

## Authentifizierung und Mandantenkontext

Product Web nutzt eine sichere Browser-Session. API-Aufrufe prüfen die Mitgliedschaft vor jedem
fachlichen Zugriff. MCP nutzt seine konfigurierte authentifizierte HTTP-Grenze. Jede fachliche
Anfrage trägt oder ermittelt einen Mandantenkontext; Lesezugriffe über Mandantengrenzen verhalten
sich wie „nicht gefunden“.

## Maßgebliches OpenAPI

Die laufende API stellt ihr maßgebliches OpenAPI-Dokument unter `/openapi.json` und eine interaktive
Referenz unter `/docs` bereit. Verwende den konfigurierten `API_URL`-Origin. Die öffentliche
Dokumentation kopiert keinen zweiten vollständigen Endpunktkatalog, weil dieser vom ausführbaren
Contract abweichen würde.

## Aufbau einer Anfrage

> **Beispiel:** Mandantenbezogene HTTP-Aufrufe verwenden unterstützte Ressourcenpfade und explizite
> Request-Bodies. Methode, Pfad, Payload, Statuscodes, Filter und Paginierung deiner ausgerollten
> Version stehen genau so im OpenAPI-Schema zur Laufzeit.

## Fehler, Filter und Paginierung

Behandle Authentifizierung, Autorisierung bzw. „nicht gefunden“, Validierung, Konflikt und
Serverfehler als unterschiedliche Ergebnisse. Schließe aus einem Fehler niemals auf die Existenz
eines fremden Mandanten. Nutze nur die Filter und die Paginierung, die der ausgerollte
OpenAPI-Contract beschreibt; die Beispiele hier erläutern, sie sind keine eigenständige Zusage über
die Schnittstelle.

## Verändernde Agentenaktionen

Lesende Werkzeugaufrufe laufen ohne Bestätigung. Änderungen aus Chat oder von einem Agenten erzeugen
einen Vorschlag mit Vorschau und brauchen eine ausdrückliche Bestätigung. Die Bestätigung ruft
denselben Anwendungsdienst auf, den auch ein Mensch oder der CLI-Adapter verwenden würde.
