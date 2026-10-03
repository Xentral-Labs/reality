# Reality erweitern

## Was du hier lernst

Du lernst, welche Bausteine Reality verwendet und wie du eine vorhandene Vorlage für eine eigene
Erweiterung nutzt. Am Ende kannst du eine Leseoberfläche, Anwendungsoperation oder Schnittstelle
ergänzen und ihr Ergebnis prüfen.

Du brauchst grundlegende Python-Kenntnisse und ein ausgechecktes Repository. Für Web-Oberflächen
kommen TypeScript/React hinzu. Geschäftsregeln musst du nicht auswendig kennen: Die Kapitel
verfolgen ein gemeinsames Beispiel, **Bestand reservieren und Lieferhindernisse verstehen**.

## Wie die Bausteine zusammenhängen

Eine **View** zeigt Daten. Eine **Projection** liefert bei Bedarf ein abgeleitetes Lesemodell. Ein
**Command** definiert eine gemeinsame Anwendungsoperation; **Agent Tools** und **Web Actions**
machen sie unterschiedlich zugänglich. Eine Ausnahme beschreibt einen aktuellen Zustand mit
Handlungsbedarf.

```text
Lesen:    View oder Agent Tool → gemeinsamer Reader → Reality oder Projection
Handeln:  Web Action oder Agent Tool → Command/Service → Reality
Import:   Connector → SourceRecord → Interpreter → Evidence → Reality
```

Ändernde Agent Tools bereiten einen Vorschlag vor; die Ausführung folgt erst nach ausdrücklicher
Freigabe. Eine View benötigt nicht automatisch eine Projection. Technische Namen bleiben in allen
Sprachen Englisch.

## Die Bausteine im Überblick

| Baustein                | Wofür?                   | Beispiel                 | Anleitung                    |
| ----------------------- | ------------------------ | ------------------------ | ---------------------------- |
| View                    | Daten anzeigen           | Lieferhindernisse        | [Views](./views)             |
| Projection              | Lesemodell ableiten      | Versandvorrat            | [Projections](./projections) |
| Command                 | Operation ausführen      | Bestand reservieren      | [Commands](./commands)       |
| Ausnahme                | Handlungsbedarf erkennen | Gefährdete Zusage        | [Ausnahmen](./exceptions)    |
| Agent Tool              | Agentenzugang anbieten   | Reservierung vorschlagen | [Agent Tools](./agent-tools) |
| Web Action              | Bedienablauf anbieten    | Reservierungsformular    | [Web Actions](./web-actions) |
| Connector / Interpreter | Quelldaten übernehmen    | ERP-Auftrag              | [Datenquellen](./connectors) |

API und CLI sind weitere Zugänge zu denselben Services; die [Adapter-Anleitung](./api-cli) erklärt
ihre Umsetzung.

## So liest du dieses Handbuch

1. Prüfe [Konfiguration oder Entwicklung?](../integrations/customization). Nicht jede Anpassung
   braucht neuen Code.
2. Arbeite die [erste Erweiterung](./first-extension) durch: ein kleiner lesender Agentenzugang ohne
   neue Geschäftsregeln.
3. Wähle danach dein Kapitel. Jedes erklärt Zweck, Voraussetzungen, ein Beispiel, Änderungen,
   Ergebnisprüfung und eine Übung.
4. Nutze die [gemeinsamen Entwicklungsregeln](./reference) für Repository-Orte, Spec-Kit-Workflow
   und Prüfungen.

Wenn du bereits weißt, was du ergänzen möchtest, kannst du direkt beim passenden Baustein beginnen.
Die Kapitel sagen ausdrücklich, welche Teile bereits vorhanden sein müssen.
