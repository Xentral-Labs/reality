# Reality für ERP-Profis

## Vom vertrauten ERP zum neuen Modell

Du kennst Auftragsköpfe und Positionen, Reservierungen, Lagerjournale und offene Posten. Vielleicht
hast du selbst ein ERP mit mehreren hundert Tabellen eingerichtet oder erweitert. Dieses Wissen
hilft dir auch in Reality. Neu ist vor allem, welcher Datensatz für welche geschäftliche Aussage
verantwortlich ist und wie daraus der aktuelle Stand entsteht.

Nach diesem Handbuch kannst du drei Dinge: einen Geschäftsfall in Reality einordnen, eine angezeigte
Menge oder Forderung bis zu ihren Grundlagen erklären und eine vorgeschlagene Agentenaktion fachlich
beurteilen. Dafür musst du weder JSON lesen noch die Datenbanktabellen auswendig kennen.

## Unser roter Faden

Die Acme Bikes GmbH verkauft Fahrradteile. Huber Handel bestellt **30 Fahrradlampen**. Im Lager
Augsburg liegen acht; Acme bestellt 22 weitere bei LightWorks. Die Ware kommt in zwei Teilen an und
geht in zwei Teilen an Huber. Zur Lieferung gehört eine Rechnung über **1.470 EUR**. Huber zahlt 500
EUR; später werden 100 EUR gutgeschrieben und auf diese Rechnung angerechnet.

Wir verwenden diese Beziehungen durchgehend: Auftrag `SO-1001`, Bestellung `PO-2001` und Rechnung
`INV-1001`. Es sind lesbare Beispielnummern, keine technischen Identitäten. Varianten wie eine
Retoure stehen ausdrücklich außerhalb des Grundablaufs. Das Beispiel ist eine Erklärung, keine
vorinstallierte Demo und kein Muster für eine steuerliche Rechnungsstellung.

## Wo Reality arbeitet

Informationen können aus einem angebundenen System oder aus einer unterstützten manuellen Erfassung
kommen. Reality bewahrt die Eingabe auf und übernimmt daraus die geschäftlichen Aussagen, die der
jeweilige Import versteht. Unterstützte Aktionen erfassen anschließend beispielsweise eine
Reservierung, eine Lieferung oder eine Buchung in Reality.

Welche Daten ein konkretes ERP oder ein Shop liefert, hängt von seiner Anbindung ab. Eine Änderung
in Reality ändert nicht automatisch das Vorsystem. Ebenso bewegt eine erfasste Lieferung selbst
keine Ware: Der Lagervorgang und seine Erfassung müssen im Betrieb zusammenpassen. Für einen
parallelen Einstieg neben deinem ERP gibt es den [Pilotleitfaden](../integrations/parallel-test).

## Kapitel

1. [Von ERP-Belegen zur Business Reality](./business-reality-guide/01-from-erp-documents-to-business-reality):
   Welche Fragen beantwortet der Auftrag, welche beantworten Zusage, Reservierung und Bewegung?
2. [Aufträge, Bestand und Lieferungen](./business-reality-guide/02-orders-stock-and-deliveries):
   Verfolge Hubers 30 Lampen und rechne Bestand, Zuordnung und offene Lieferung mit.
3. [Rechnungen und Zahlungen](./business-reality-guide/03-invoices-and-payments): Warum sind
   Rechnungserfassung, Buchung und Zahlungszuordnung getrennte Schritte?
4. [Als Prozessverantwortliche/r arbeiten](./business-reality-guide/04-working-as-process-owner):
   Was prüfst du, wenn ein Agent einen Auftrag erklärt oder eine Änderung vorschlägt?
5. [Ein Auftrag von Anfang bis Ende](./business-reality-guide/05-one-order-end-to-end): Beantworte
   selbst, ob Hubers Auftrag abgeschlossen ist, und vergleiche deine Antwort.
6. [Facts und offene Fragen](./business-reality-guide/06-facts-and-open-questions): Wo gehört eine
   Zusatzinformation hin, für die du im ERP ein Freifeld angelegt hättest?

7. [Zusammenfassung](./business-reality-guide/07-model-at-a-glance): Das gemeinsame Geschäftsjournal
   für Menschen, Agenten und Workflows.

Lies beim ersten Durchgang in dieser Reihenfolge. Aufklappbare technische Vertiefungen kannst du
überspringen. Danach dienen [Tools nutzen](../tool-usage/) und die
[Tabellenübersicht](../reference/table-map) als Nachschlagewerk.

## Autorität und Referenzkern

Das Handbuch erklärt das bestehende Produkt. Maßgeblich bleiben
[Architektur](https://github.com/Xentral-Labs/reality/blob/main/docs/ARCHITECTURE.md),
[Datenmodell](https://github.com/Xentral-Labs/reality/blob/main/docs/DATA_MODEL.md),
[Feature-Contracts](https://github.com/Xentral-Labs/reality/tree/main/docs/features) und die
Spezifikationen unter `specs/`.

Der Referenzkern steht unter der [MIT-Lizenz](/de/reference/license). Du kannst seine Umsetzung
untersuchen und unter den Lizenzbedingungen verwenden und verändern. Copyright-, Lizenz- und
Haftungshinweis müssen bei Kopien oder wesentlichen Teilen erhalten bleiben.

## Felder und Datenstrukturen nachschlagen

Welche Felder hat ein Commitment? Wo stehen spätere Terminänderungen, Reservierungen und
Lieferungen? Im [Datenmodell unter Tools nutzen](/de/tool-usage/#model:commitment) findest du die
zentralen Bausteine mit Beispielen, allen gespeicherten Feldern und passenden Aktionen. Die
Übersicht trennt operative Felder, ergänzende Facts, Originalquellen und berechnete Angaben.

Direkt zu den ERP-Bausteinen: [Geschäftspartner (Party)](/de/tool-usage/#model:party),
[Artikel (Item)](/de/tool-usage/#model:item), [Sendung (Shipment)](/de/tool-usage/#model:shipment),
[Preisliste](/de/tool-usage/#model:price_list) und
[Zahlungszuordnung](/de/tool-usage/#model:settlement_allocation).
