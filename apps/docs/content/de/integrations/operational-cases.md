# Einen Vorgang übernehmen

Ein Vorgang klammert die Verantwortung für angenommene Arbeit. In der ersten Version gehören die
Kundenlieferungen eines Auftrags zu einem Vorgang. Jede angekündigte Retoure hat einen eigenen,
verwandten Vorgang. Neue Produkte, Lagerorte und rohe Quellnachrichten legen keinen Vorgang an.

Die Vorgangssteuerung gilt standardmäßig für jede Firma. Neue angenommene Aufträge erhalten sofort
Vorgänge. Offene oder teilweise erledigte Aufträge und angenommene offene Retouren werden durch
begrenzte Update-Jobs erfasst. Abgeschlossene Historie bleibt geschlossen. Prüfe mit
`operational_case_status` die Migration und vollständige Erfassung. Unvollständige Updates oder
Jobfehler erfordern Aufmerksamkeit, keine Aktivierung.

Braucht der Agent Hilfe, öffne den Vorgang und bestätige **Manuell übernehmen / Automatisierung
stoppen**. Neue automatische Aktionen für diesen Vorgang sind sofort gesperrt. Bereits gestartete
Aktionen bleiben sichtbar: Der Stopp storniert keine bereits ausgeführte Sendung oder andere externe
Aktion.

Korrigiere den Auftrag in Shopify. Die unterstützte Quellen- und Belegverarbeitung muss die Änderung
danach annehmen. Eine eingegangene Nachricht allein ist noch keine angenommene Korrektur. Der
Vorgang zeigt aktuelle offene Arbeit, verknüpfte Quellen und ungeklärte Ausführungen oder
Quellenänderungen.

Wähle **Vor Rückgabe an Automatisierung prüfen**. Kläre offene Unsicherheiten, prüfe den aktuellen
Stand und bestätige **An Automatisierung zurückgeben**. Geänderte Daten erfordern eine neue Prüfung.
Alte Pläne laufen nicht wieder an; der Agent muss aktuelle Arbeit neu vorbereiten.

Die Vorgangs-ID bezeichnet die Verantwortungsklammer. Die Proposal-ID bezeichnet eine Entscheidung.
Eine externe Correlation-ID bezeichnet den Verarbeitungskontext des Fremdsystems. Diese Referenzen
sind getrennt und erteilen keine fachlichen Berechtigungen.

Mit `operational_case_object` findest du Vorgänge zu einem bestehenden Auftrag, Commitment, einer
Retoure oder einem Proposal. `operational_case_explain` zeigt denselben Stand wie die Oberfläche.
Lesen legt keine Arbeit an. MCP und Chat können Verantwortungsänderungen vorschlagen; ein
angemeldeter Mensch muss sie bestätigen.

Live-Shopify-Transport und automatische Ausführung von Erstattungsabsichten gehören noch nicht zu
dieser Version. Lieferantenprozesse und weitere Vorgangstypen werden separat geplant. Die
[Werkzeugreferenz](/de/tool-usage/commands) beschreibt die verfügbaren Operationen.

## Standardsteuerung (Spec 377)

Migration 0145 muss vor den passenden Diensten, Scheduler und Workern laufen.
`operational_case_status` zeigt den Versionsursprung, die abgeschlossene Erfassung und Jobfehler.
Manuelle Übernahmen, genaue Rückgabebestätigungen und ausgeführte Belege bleiben erhalten. Alte
Freigaben benötigen eine neue Prüfung. Das Update erteilt keine Berechtigung für Lieferanten-,
Finanz-, Lager-, Erstattungs-, Mail- oder Provideraktionen. Ein Downgrade mit gespeichertem
Rollout-Verlauf wird verweigert.
