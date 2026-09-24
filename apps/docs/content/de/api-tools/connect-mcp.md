# Einen MCP-Client verbinden

Reality stellt kompatiblen externen Agenten mandantengebundene Geschäftswerkzeuge über
authentifiziertes Streamable HTTP bereit. Mit dieser Anleitung verbindest du einen Client nur mit
den Funktionen, die er tatsächlich benötigt.

## Einmal durch einen Menschen einrichten, danach arbeitet der Agent

Die empfohlene Verbindung beginnt mit einer kurzen, einmaligen Einrichtung und OAuth-Freigabe durch einen Menschen im Browser.
Der Mensch meldet sich an, erstellt oder wählt das Unternehmen, wählt die genaue Tool-Allowlist und
bestätigt den Client. Der Client tauscht den Authorization Code anschließend gegen mandantengebundene
Access- und Refresh-Tokens. Der Agent verwendet diese Tokens direkt und erhält weder Browser-Session
noch Passwort des Menschen.

```text
Einmal durch einen Menschen im Browser:
Konto → Unternehmen → Tool-Allowlist → OAuth-Freigabe

Danach durch den Agenten:
MCP-Endpunkt + Access-Token → erlaubte Werkzeuge finden und verwenden
```

Ein Agent oder angebundenes System darf Registrierung, E-Mail-Bestätigung oder die menschliche
Freigabe nicht automatisieren. Hat noch kein Mensch autorisiert, öffnet der Client den OAuth-Login
und bittet den Menschen, ihn im Browser abzuschließen.
Dieser Einstieg gilt für jedes externe Agenten- oder Erkenntnissystem.

## Was ein Agent tun kann

Ein berechtigter Agent kann Aufträge und Commitments untersuchen, Bestand lesen,
Fulfillment-Hindernisse finden, Ausnahmen anhand ihrer Evidence erklären und Vorschläge prüfen. Er
kann außerdem kontrollierte Geschäftsänderungen wie eine Reservation oder ein Movement vorbereiten.
Lesezugriffe laufen sofort. Eine Mutation erzeugt zunächst einen Vorschlag und ändert den
Geschäftszustand erst nach ausdrücklicher menschlicher Freigabe. Danach sollte der Agent das
Ergebnis über die vorgesehene Projection oder Statusabfrage verifizieren.

Die [Agentenfunktionen](/de/tool-usage/#choosing-a-tool) erklären Auswahl und Verifikation. Die
generierte [Tool-Referenz](../tool-usage/commands) enthält aktuelle Namen und Parameter.

## Voraussetzungen

- Ein Mensch hat Registrierung und E-Mail-Bestätigung in der Reality-Browseranwendung abgeschlossen.
- Dieser Mensch hat das Unternehmen erstellt oder ausgewählt, das der Agent verwenden soll.
- Ein kompatibler MCP-Client mit OAuth-Authorization-Code-Flow, S256-PKCE und Streamable HTTP.
- Eine registrierte HTTPS-Redirect-URI. Alternativ unterstützt Reality begrenzte HTTPS-
  Client-Metadata-Dokumente (CIMD).

## 1. Endpunkt finden

Öffne **Unternehmenseinstellungen → Agenten → MCP Server** und kopiere den angezeigten Endpunkt. Das
Deployment veröffentlicht diesen Wert als `MCP_URL`. Produktionsendpunkte verwenden HTTPS und den
Origin-Root, zum Beispiel:

```text
https://mcp.example.com/
```

Hänge nicht selbst `/mcp` an. Maßgeblich ist immer die im Produkt angezeigte URL.

## 2. Client autorisieren

Starte den Verbindungsablauf des Clients am angezeigten MCP-Endpunkt. Reality öffnet die Anmeldung
und Zustimmung im Browser. Wähle ein bereites Unternehmen und die kleinste Tool-Allowlist, die die
Aufgabe ermöglicht, und bestätige anschließend.

## 3. Client konfigurieren

Die Oberflächen unterscheiden sich, der Verbindungsvertrag bleibt jedoch gleich:

```text
Transport: Streamable HTTP
URL:       <die angezeigte MCP_URL>
Auth:      OAuth-2.1-Authorization-Code + PKCE
```

Der Client speichert Access- und Refresh-Tokens im sicheren Anmeldedatenspeicher. Lege Tokens weder
in einem Repository noch in einem Prompt, Screenshot, geteilten Dokument oder Quellpayload ab.

## 4. Ersten Lesezugriff prüfen

Beginne mit einer reinen Leseabfrage. Lass den Client `business_records_discover` für eine bekannte
Geschäftsreferenz aufrufen oder `inventory_read` zuerst mit `capability_describe` beschreiben.

Eine erfolgreiche Verbindung belegt, dass Token, Tenant, Endpunkt und ausgewähltes Werkzeug
zusammenarbeiten. Ein leeres Ergebnis beweist nicht, dass kein passender Datensatz oder kein Problem
existiert. Beachte Datengrundlage, Aktualität, Grenzen und nächste Schritte des Werkzeugs.

## 5. Kontrollierte Änderungen verstehen

Mutierende Agentenwerkzeuge sind Proposal-Tools. Der sichere Ablauf lautet:

```text
prüfen → vorschlagen → menschlich freigeben → ausführen → verifizieren
```

Prüfe vor der Freigabe die genaue beabsichtigte Wirkung. Eine Proposal-Berechtigung beweist weder
Freigabe noch Ausführung, Fulfillment, Lieferung oder Zahlung. Nutze anschließend die vorgesehene
Verifikationsabfrage und vertraue nicht allein einer Erfolgsmeldung.

## Fehlerbehebung

- **Nicht autorisiert**: Prüfe den exakten Endpunkt und das Bearer-Token. Erstelle Ersatz, falls das
  vollständige Token verloren ging.
- **Tool nicht erlaubt**: Ergänze das benötigte Werkzeug bewusst oder verwende ein separates Token
  mit passender Tool allowlist.
- **Client verlangt OAuth**: Fahre mit der Browser-Freigabe fort; OAuth ist der unterstützte
  interaktive Verbindungsweg.
- **Leeres Ergebnis**: Prüfe Geschäftsreferenz, Tenant, Quellenabdeckung, Filter und Aktualität.
- **Unbekanntes Ausführungsergebnis**: Prüfe den Proposal-Status und wiederhole nicht blind.

## Zugriff widerrufen

Öffne wieder **Unternehmenseinstellungen → Agenten → MCP Server** und nutze `revoke`, wenn ein
Client nicht mehr eingesetzt wird, ein Gerät verloren geht oder ein Token offengelegt worden sein
könnte. Der Widerruf blockiert weitere Aufrufe. Erstelle ein separates Ersatztoken, statt ein Token
zwischen Clients zu teilen.

## Aktuelle Authentifizierungsgrenze

Reality bietet Authorization-Code-Flow mit S256-PKCE, exakte Prüfung von Resource und Redirect,
Browser-Consent, mandantengebundene Tool-Rechte, Ablauf, Refresh-Token-Rotation und Widerruf. Das
entstehende mandantengebundenes MCP-Zugriffstoken ist der Zugang des Agenten. OAuth ist fester
Bestandteil der MCP-Produktgrenze. Die Client-Registrierung erfolgt explizit über `MCP_OAUTH_CLIENTS` oder ein begrenztes HTTPS-CIMD-
Dokument; einen offenen Registrierungsendpunkt gibt es nicht. Die Unternehmensanlage bleibt eine
menschlich bestätigte Browser-Aktion und wird niemals ohne diese Zustimmung durch einen Agenten
ausgeführt.

Was ein Agent mit diesen Werkzeugen je Geschäftsbereich tun soll und was beim Menschen bleibt, steht
in den [Agenten-Playbooks](../agent-playbooks/).
