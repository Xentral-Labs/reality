# Zugänge ergänzen

## Welche Oberfläche braucht die vorhandene Fähigkeit?

Zuerst muss die fachliche Abfrage oder Operation existieren. Ein Zugang macht sie erreichbar; er
definiert keine zweite Geschäftsregel. Fehlt die Operation, beginne mit
[Commands](/de/development/commands).

| Zugang     | Wer nutzt ihn?                 | Vorlage                                 | Anleitung                                                                                                             |
| ---------- | ------------------------------ | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Agent Tool | Agent oder Chat                | `inventory_read`, `reservation_propose` | [Agent Tools](/de/development/agent-tools)                                                                            |
| Web Action | Mensch im Workspace            | `reserve_stock`                         | [Web Actions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/web-actions.md) |
| HTTP API   | Unterstützter Client           | `tenant_inventory_control`              | [API und CLI](/de/development/api-cli)                                                                                |
| CLI        | Entwicklung und Administration | `commitment_reserve`                    | [API und CLI](/de/development/api-cli)                                                                                |

Für die reine Anzeige von Daten lies
[Views](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/views.md).
Sie kann ein vorhandenes Lesemodell verwenden und braucht nicht automatisch eine neue Projection.

## Was die Zugänge gemeinsam haben

Alle verwenden die gemeinsamen Services oder Application Tools. Jeder Zugang bewahrt Tenant-Grenze,
typisierte Eingaben und sichere Fehler. Der Reader nach einer Änderung prüft das maßgebliche
Ergebnis.

Lesende Agent Tools können sofort lesen. Ändernde Agent Tools erstellen ein `ChangeProposal` mit
exakter Server-Vorschau. Ausführung benötigt die separate ausdrückliche Freigabe; Leserecht ist
keine Änderungsfreigabe. Web Actions verwenden die vorhandene Bestätigungsoberfläche. Die
vollständigen Vorlagen stehen in den jeweiligen Kapiteln.

## Wo du beginnst

Arbeite zuerst die [erste Erweiterung](/de/development/first-extension) durch oder öffne direkt
deine Anleitung. Die
[gemeinsame Referenz](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/de/development/reference.md)
hält Repository-Orte, Entwicklungsablauf und Prüfregeln fest. Die laufende API beschreibt HTTP über
`/openapi.json`; der MCP-Katalog beschreibt Agent Tools und ihre Eingaben.

[API und Agentenschnittstellen im Überblick](/de/api-tools/) erklärt Zugangswege, Authentifizierung
und die laufende OpenAPI-Referenz.
