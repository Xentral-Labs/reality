# Ausnahmen entwickeln

## Das lernst du

Du kannst einen aktuellen Zustand mit Handlungsbedarf ableiten, erklären und sein Verschwinden
testen.

## Wann du diesen Baustein brauchst

Nutze eine Ausnahme, wenn ein deterministischer aktueller Zustand operative Aufmerksamkeit braucht.
Definiere:

- die genaue Bedingung und wann sie nicht mehr gilt,
- Schweregrad und stabile Klassenidentität,
- betroffenen Reality-Datensatz und kürzeste Spur,
- die fachlich zuständige Rolle sowie
- ausführbare Nachweise für Ableitung, Mandantentrennung und Behebung.

Registriere Klasse und Ableitung im Katalog der operativen Ausnahmen. Erzeuge kein manuell
geschlossenes Ticket und kopiere keinen Status auf ein Document. Braucht die Behebung eine Änderung,
verwende einen normalen Command mit seiner Freigabegrenze.

## Bevor du beginnst

Du kennst Bedingung, Gegenfall, betroffenen Datensatz und verantwortliche Rolle. Kläre vorhandene
Ableitungen im [Katalog](https://docs.runreality.ai/de/tool-usage/exceptions). Die Behebung verwendet vorhandene Commands; eine
neue Ausnahme braucht keine neue Tabelle.

## Durchgearbeitetes Beispiel

### Codebeispiel: gefährdetes Commitment

`packages/reality-core/src/reality/services/exceptions.py` enthält `_outgoing_commitment_at_risk`
und registriert ihn in `DERIVATION_REGISTRY`. Der Eintrag in
`config/operational_exception_catalog.yaml` definiert stabile Klassen-ID, Bezeichnung, Schweregrad,
betroffenen Datensatztyp, Zuständigkeit und Evidence. Verschwindet die Bedingung, verschwindet auch
die abgeleitete Exception.

Katalogeintrag und Ableitung werden gemeinsam ergänzt. Teste Entstehung und Verschwinden,
Mandantentrennung, stabile Ursachen-IDs und Erklärungsspur. Vorlagen sind
`operational_exceptions/test_derivation.py`, `test_coverage.py` und `test_explanation.py`.

## Schritt für Schritt

1. Formuliere die Bedingung und den Gegenfall zuerst in der Spezifikation: Wann ist ein offenes
   ausgehendes Commitment gefährdet, wann nicht?
2. Folge `_commitment_exceptions` und `_outgoing_commitment_at_risk` im Service. Die zweite Funktion
   filtert die gemeinsame Ableitung; sie berechnet nicht unabhängig neue Bestandsregeln.
3. Ergänze eine stabile Klasse im Katalog, die tenantbezogene Ableitung und `DERIVATION_REGISTRY`.
   Verwende vorhandene Reality-Beziehungen für Ursachen und Herkunft.
4. Erzeuge im Test ein Commitment mit unzureichender Deckung. Prüfe die abgeleitete Ausnahme und
   ihren Erklärpfad. Stelle die Deckung über den vorhandenen Service her; bei erneuter Ableitung
   muss die Bedingung verschwinden, ohne manuelles Schließen.
5. Ergänze den Gegenfall, relevante Sperren, fehlende Evidence und fremde Tenant-IDs. Kopiere nicht
   die Bedingung in die Web-Oberfläche. Bei anderer Bedeutung nutze eine neue Klasse statt die
   vorhandene zu erweitern.
6. Ergänze Ressourcen-Zuordnung/deutsches Label und führe `make docs-generate` aus. Die neue Klasse
   muss im Katalog auffindbar sein und alle geplanten Tests bestehen.

## Ergebnis prüfen

Nutze die vorhandene Commitment-at-risk-Fixture mit passendem Termin und ohne unabhängige Sperren.
Prüfe Entstehung bei fehlender Deckung, Ursache/Erklärpfad, Verschwinden nach Behebung und
Mandantentrennung. Eine zweite Ableitung darf keine manuellen Statusänderungen benötigen.

## Selbst ausprobieren

Formuliere den Gegenfall des Beispiels: rechtzeitig gedeckt und ohne Sperre. Erwartet: keine
at-risk-Ausnahme. Füge anschließend eine unabhängige Sperre hinzu und prüfe die tatsächlich
registrierte Ursache statt fehlende Deckung zu unterstellen.

## Häufige Fehler

Ausnahmen nicht als manuell schließbare Tickets speichern; keine neue Authority aus einer Ableitung
machen; keine Browser-Regel kopieren. Verschwindet eine Ursache, müssen verbleibende Ursachen
weiterhin erklärt werden.

## Weiterlesen

[Zugänge ergänzen](./application-surfaces.md) zeigt, wie vorhandene Reads und Commands nutzbar werden.
