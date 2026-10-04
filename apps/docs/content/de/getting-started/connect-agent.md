# Deinen Agenten verbinden

Verbinde deinen Agenten mit dem Unternehmen aus deinem [Einstiegsrezept](./). Reality stellt
externen Agenten dieselben Geschäftswerkzeuge bereit, die auch die eigene App nutzt.

**Vorher:** Erledige Account, E-Mail-Bestätigung und Unternehmensanlage im Browser. Lass das
gewünschte Unternehmen ausgewählt. Diese Anleitung gilt für Demo, Neugründung und Firmenpiloten.

## 1. Kopiere die Verbindungsadresse

Öffne in Reality **Unternehmenseinstellungen → Agenten → MCP Server** und kopiere den angezeigten
Endpunkt. Verwende genau diese Adresse; sie gehört zu deiner Reality-Installation.

## 2. Verbinde den Agenten und gib den Zugriff frei

Füge die Adresse in den MCP-Verbindungseinstellungen deines Agenten hinzu und starte dessen
Anmeldeablauf. Melde dich auf der Reality-Seite im Browser an, wähle dein vorbereitetes Unternehmen
und erlaube die Werkzeuge zum Lesen von Aufträgen, Bestand und ihren Erklärungen.

Dein Client muss **Streamable HTTP und OAuth mit PKCE** unterstützen. Bezeichnungen und
Verfügbarkeit der Verbindungseinstellungen hängen vom Client ab. Die
[MCP-Verbindungsanleitung](/de/api-tools/connect-mcp) beschreibt den vollständigen
Verbindungsvertrag und die Fehlerbehebung.

Beginne mit Lesezugriff. Werkzeuge für Änderungsvorschläge kannst du später bewusst freigeben, wenn
du deine [erste Aktion](./first-action) vorbereiten möchtest. Die Agentenverbindung gilt für das
autorisierte Unternehmen; ein anderer Firmenname im Prompt wechselt den Zugriff nicht.

## 3. Prüfe die Verbindung

Kopiere diesen lesenden Prompt in den verbundenen Agenten:

```text
Prüfe, welches Reality-Unternehmen diese Verbindung autorisiert. Zeige seine Identität
und die verfügbaren Lesefähigkeiten für unsere Einstiegsaufgabe. Verändere keine Daten
und wechsle nicht das Unternehmen. Erkläre fehlende Berechtigungen oder Einrichtung,
statt zu raten.
```

**Das solltest du sehen:** Das autorisierte Unternehmen und die Werkzeuge zum Prüfen seiner
Datensätze. Vergleiche das Unternehmen mit deiner Auswahl in Reality. Ein leeres neues Unternehmen
kann bereits eine funktionierende Agentenverbindung haben; es braucht keinen Demo-Auftrag.

Für das Demo-Rezept lässt du zusätzlich **SO-006** suchen. Im unveränderten Ausgangsdatensatz sind
drei von fünf Stück versendet und zwei offen. Frage nach den aktuellen Datensätzen und ihren
Verweisen.

Bei verweigertem Zugriff prüfst du Verbindung und Werkzeugberechtigungen anhand der
[Verbindungsanleitung](/de/api-tools/connect-mcp).

**Zurück zum Rezept:** [Demo](./demo-company) · [Von null](./start-business) ·
[Bestehende Firma](./existing-business).

## Du möchtest in Reality bleiben?

Nutze den integrierten **Chat**, wenn KI für dein Unternehmen konfiguriert ist. Er verwendet
dieselben Anwendungswerkzeuge; du kannst ohne externe Verbindung mit deinem Rezept weitermachen.

## MCP-Prüfwerkzeuge

Verwende `company_context` für gespeicherte Firmen-ID, Name und Zweck und danach
`capability_catalog` für tatsächliche Toolrechte. `proposal_review` liefert die konkrete
Entscheidungsvorschau; `proposal_execution_status` prüft den Ausführungsnachweis. Browserlinks sind
optional; Leserechte erteilen keine Bestätigungsrechte.
