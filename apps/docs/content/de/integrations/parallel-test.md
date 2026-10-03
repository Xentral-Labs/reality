# Eigene Daten nutzen

Beginne nach der Demo mit einer Geschäftsfrage aus deinem Unternehmen — zum Beispiel, welche
Kundenaufträge noch geliefert werden müssen. Kläre, welche Quelldatensätze dafür benötigt werden.

## 1. Prüfe zuerst die Verbindung

Öffne **Integrationen** in deinem Unternehmen und prüfe die gewünschte Quelle. Ein registriertes
Quellsystem ist noch keine ERP-Verbindung. Authentifizierung, Datentransport und Interpretation
müssen für die Datensatzarten verfügbar sein, die du empfangen möchtest.

Dass Shopify, Xentral oder Odoo in einem Integrationskatalog stehen, bedeutet nicht, dass eine
fertige Verbindung verfügbar ist. Kläre den tatsächlichen Anbindungsumfang mit der Person, die sie
umsetzt, bevor du einen Import planst.

## 2. Beginne mit einem kleinen, getrennten Piloten

Nutze ein separates Unternehmen und wenige Datensätze mit bekannten Ergebnissen. Nimm einen
gewöhnlichen Auftrag, eine Teillieferung und einen schwierigen Fall auf. Lass den ersten Piloten
gegenüber deinem ERP lesend: Empfange seine Daten in Reality und vergleiche die Antworten, ohne das
ERP zu verändern.

## 3. Prüfe eine Antwort bis zur Quelle

Stelle deinem [Agenten](../getting-started/connect-agent) eine konkrete Frage. Vergleiche die
Antwort mit deinem Vorsystem und folge ihren Datensätzen durch **Reality → Evidence → Source**.
Fehlende oder nicht interpretierte Datensätze bleiben erkennbare Lücken; sie beweisen nicht, dass
keine Arbeit offen ist.

Erweitere den Datenumfang erst, wenn das Ergebnis verstanden ist. Kläre Berechtigungen,
Vorschlagsprüfung und Verifizierung getrennt, bevor du Aktionen aktivierst.

Für die technische Umsetzung gibt es das
[Integrationshandbuch im Repository](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/integrations/connector-contract.md).
