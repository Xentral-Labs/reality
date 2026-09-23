# Einen MCP-Client verbinden

Reality stellt kompatiblen externen Agenten mandantengebundene Geschäftswerkzeuge über
authentifiziertes Streamable HTTP bereit. Mit dieser Anleitung verbindest du einen Client nur mit
den Funktionen, die er tatsächlich benötigt.

## Einmal durch einen Menschen einrichten, danach arbeitet der Agent

Die aktuelle Verbindung beginnt mit einer kurzen, einmaligen Einrichtung durch einen Menschen im
Browser. Der Mensch erstellt und bestätigt ein Reality-Konto, erstellt oder wählt das Unternehmen
und erzeugt für den Client ein mandantengebundenes MCP-Zugriffstoken. Nach dieser Übergabe verwendet
der Agent MCP-Endpunkt und Token direkt; er benötigt weder die Browser-Session noch das Passwort des
Menschen.

```text
Einmal durch einen Menschen im Browser:
Konto → E-Mail-Bestätigung → Unternehmen → eingeschränktes MCP-Token

Danach durch den Agenten:
MCP-Endpunkt + Token → erlaubte Werkzeuge finden und verwenden
```

Ein Agent oder angebundenes System darf Registrierung, E-Mail-Bestätigung oder interaktiven Login
nicht automatisieren. Hat noch kein Mensch die Browser-Einrichtung abgeschlossen, muss der Agent
darum bitten und anschließend den angezeigten MCP-Endpunkt und das einmal sichtbare Token erhalten.
Dieser Einstieg gilt für jedes externe Agenten- oder Erkenntnissystem; einen produktspezifischen
Provisionierungsweg gibt es derzeit nicht.

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
- Inhaberzugriff auf **Unternehmenseinstellungen → Agenten → MCP Server** für die Tokenverwaltung.
- Ein kompatibler MCP-Client, der einen entfernten Streamable-HTTP-Endpunkt und einen
  Authorization-Bearer-Header akzeptiert.

Einige MCP-Clients verlangen derzeit eine OAuth-Anmeldung und akzeptieren kein manuell
konfiguriertes Bearer-Token. Diese Clients können Reality über diesen Ablauf noch nicht direkt
verbinden.

## 1. Endpunkt finden

Öffne **Unternehmenseinstellungen → Agenten → MCP Server** und kopiere den angezeigten Endpunkt. Das
Deployment veröffentlicht diesen Wert als `MCP_URL`. Produktionsendpunkte verwenden HTTPS und den
Origin-Root, zum Beispiel:

```text
https://mcp.example.com/
```

Hänge nicht selbst `/mcp` an. Maßgeblich ist immer die im Produkt angezeigte URL.

## 2. Eingeschränktes Token erstellen

Erstelle ein benanntes Token für genau einen Client. Wähle die kleinste Tool allowlist, die dessen
Aufgabe ermöglicht. Ein lesender Analyse-Agent benötigt normalerweise Discovery und passende
Lesewerkzeuge, nicht alle heutigen und zukünftigen Tools.

Reality zeigt das vollständige Token genau einmal. Kopiere es sofort in den Client. Reality
speichert nur den Hash und ein kurzes sichtbares Präfix.

## 3. Client konfigurieren

Die Oberflächen unterscheiden sich, der Verbindungsvertrag bleibt jedoch gleich:

```text
Transport: Streamable HTTP
URL:       <die angezeigte MCP_URL>
Header:    Authorization: Bearer <das einmal angezeigte Token>
```

Nutze den sicheren Anmeldedatenspeicher des Clients. Lege das Token weder in einem Repository noch
in einem Prompt, Screenshot, geteilten Dokument oder Quellpayload ab. Produktspezifische Menünamen
und Konfigurationssyntax gehören zum Client und können sich unabhängig von Reality ändern.

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
- **Client verlangt OAuth**: Der Client unterstützt möglicherweise keine manuell konfigurierte
  Bearer-Authentifizierung.
- **Leeres Ergebnis**: Prüfe Geschäftsreferenz, Tenant, Quellenabdeckung, Filter und Aktualität.
- **Unbekanntes Ausführungsergebnis**: Prüfe den Proposal-Status und wiederhole nicht blind.

## Zugriff widerrufen

Öffne wieder **Unternehmenseinstellungen → Agenten → MCP Server** und nutze `revoke`, wenn ein
Client nicht mehr eingesetzt wird, ein Gerät verloren geht oder ein Token offengelegt worden sein
könnte. Der Widerruf blockiert weitere Aufrufe. Erstelle ein separates Ersatztoken, statt ein Token
zwischen Clients zu teilen.

## Aktuelle Authentifizierungsgrenze

Reality verwendet derzeit manuell erzeugte, mandantengebundene Bearer-Access-Tokens. Reality bietet
aktuell keinen OAuth-2.1-Autorisierungsablauf, PKCE, dynamische Client-Registrierung oder rotierende
Refresh-Tokens. Die Verbindung wird daher konfiguriert und erfolgt nicht per One-Click. Prüfe vor
der Annahme eines clientspezifischen Logins immer die aktuellen Produkteinstellungen und
Dokumentation.

Reality bietet damit derzeit auch keine unbeaufsichtigte Unternehmensbereitstellung für ein externes
System. Die Browser-Einrichtung begründet menschliche Identität, Unternehmensmitgliedschaft und die
bewusste Zugriffsfreigabe; danach ist das MCP-Token der Zugang des Agenten.

Was ein Agent mit diesen Werkzeugen je Geschäftsbereich tun soll und was beim Menschen bleibt, steht
in den [Agenten-Playbooks](../agent-playbooks/).
