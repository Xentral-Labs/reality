import { useLayoutEffect, type ReactNode } from "react";

import {
  createCanonicalSourceResolver,
  isOriginalContent,
  resolveTranslation,
} from "./localization-core";

export type Language = "en" | "de" | "nl" | "es";
export type DisplayLocale = "en-GB" | "de-DE" | "nl-NL" | "es-ES";

type Preferences = { language: Language; locale: DisplayLocale; timezone: string };

const dictionaries: Record<Exclude<Language, "en">, Record<string, string>> = {
  de: {
    "Choose company": "Firma auswählen",
    "Open company chat": "Chat in dieser Firma öffnen",
    "Sandbox with sample data": "Sandbox mit Beispieldaten",
    "Open Free Play Sandbox": "Free-Play-Sandbox öffnen",
    "Choose an existing company or create a Sandbox with sample data.":
      "Wähle eine vorhandene Firma oder erstelle eine Sandbox mit Beispieldaten.",
    "You are working with this company's real data. Changes require confirmation.":
      "Du arbeitest mit den echten Daten dieser Firma. Änderungen musst du bestätigen.",

    "Explore Reality": "Reality entdecken",
    "Choose a storyline or Free Play.": "Wähle eine Storyline oder freies Spiel.",
    "Explore freely in your own Sandbox with sample data.":
      "Probiere frei in deiner eigenen Sandbox mit Beispieldaten aus.",
    "Create Sandbox and start": "Sandbox erstellen und starten",
    "Sandbox setup is not ready. Try again.":
      "Die Sandbox ist noch nicht bereit. Versuche es erneut.",
    "This Sandbox is archived. Restore it under Companies.":
      "Diese Sandbox ist archiviert. Stelle sie unter Unternehmen wieder her.",
    "Sandbox chat": "Sandbox-Chat",
    "Calls for this reply": "Aufrufe zu dieser Antwort",
    "No tool calls were recorded for this reply.":
      "Für diese Antwort wurden keine Tool-Aufrufe aufgezeichnet.",
    "Recorded evidence is unavailable for this reply.":
      "Für diese Antwort sind keine aufgezeichneten Nachweise verfügbar.",
    "Some recorded calls are not included in this view.":
      "Ein Teil der aufgezeichneten Aufrufe ist in dieser Ansicht nicht enthalten.",
    "Changes since this call": "Änderungen seit diesem Aufruf",
    "Changes since this call can include later activity in this Sandbox.":
      "Änderungen seit diesem Aufruf können spätere Aktivitäten in dieser Sandbox enthalten.",
    "Live simulation supports empty and standard demo Sandbox setups. Storyline Sandboxes use a different data setup that is not yet supported.":
      "Die Live-Simulation unterstützt leere und Standard-Demo-Sandboxes. Storyline-Sandboxes verwenden einen anderen Datenaufbau, der noch nicht unterstützt wird.",
    "Live simulation is not available in this Sandbox.":
      "Live-Simulation ist in dieser Sandbox nicht verfügbar.",
    "Create an empty Sandbox under Companies → New company, then enable live simulation there. No historical demo data is needed.":
      "Lege unter Unternehmen → Neues Unternehmen eine leere Sandbox an und aktiviere dort die Live-Simulation. Historische Demodaten sind dafür nicht nötig.",

    "Create a separate demo Sandbox for live simulation. Your existing company and Storyline stay unchanged.":
      "Erstelle eine separate Demo-Sandbox für die Live-Simulation. Deine bestehende Firma und Storyline bleiben unverändert.",
    "Create demo Sandbox": "Demo-Sandbox erstellen",

    "Preparing your company": "Deine Firma wird vorbereitet",
    "Continue company setup": "Firmeneinrichtung fortsetzen",
    "Your setup is saved. Continue with the same company.":
      "Deine Einrichtung ist gespeichert. Du setzt mit derselben Firma fort.",
    "Enter the six-digit code from your verification email.":
      "Gib den sechsstelligen Code aus deiner Bestätigungs-E-Mail ein.",
    "If this address needs verification, a new code has been sent.":
      "Falls diese Adresse noch bestätigt werden muss, wurde ein neuer Code gesendet.",
    "Sending code\u2026": "Code wird gesendet…",
    "Send a new code": "Neuen Code senden",

    "Loading your access": "Dein Zugang wird geladen",
    "Please wait. You will continue automatically.":
      "Bitte warte kurz. Es geht automatisch weiter.",
    "Loading your workspace": "Dein Arbeitsbereich wird geladen",
    "Verifying your email": "Deine E-Mail-Adresse wird bestätigt",

    "Try for free": "Kostenlos testen",
    "Your own demo company. No credit card. No automatic paid subscription.":
      "Deine eigene Demo-Firma. Keine Kreditkarte. Kein automatisches kostenpflichtiges Abo.",
    "Try the Playground for free with your own demo company. No credit card. No automatic paid subscription.":
      "Teste den Playground kostenlos mit deiner eigenen Demo-Firma. Keine Kreditkarte. Kein automatisches kostenpflichtiges Abo.",
    "Try Reality for free with your own demo company. No credit card. No automatic paid subscription.":
      "Teste Reality kostenlos mit deiner eigenen Demo-Firma. Keine Kreditkarte. Kein automatisches kostenpflichtiges Abo.",
    "By continuing, you request a demo company with live sample data after email verification.":
      "Mit dem Fortfahren beauftragst du die Erstellung einer Demo-Firma mit laufenden Beispieldaten nach der E-Mail-Bestätigung.",
    "Your demo is not ready yet. Retry to continue with the same company.":
      "Deine Demo ist noch nicht bereit. Versuche es erneut, um mit derselben Firma fortzufahren.",
    "Preparing your demo company": "Deine Demo-Firma wird vorbereitet",
    "Orders, deliveries and invoices are being prepared for you to explore.":
      "Aufträge, Lieferungen und Rechnungen werden zum Erkunden vorbereitet.",
    "Try these three questions": "Starte mit diesen drei Fragen",
    "Explore the records directly. These tasks use no AI questions.":
      "Erkunde die Datensätze direkt. Diese Aufgaben verbrauchen keine KI-Fragen.",
    "Which orders need attention?": "Welche Aufträge brauchen Aufmerksamkeit?",
    "Why is this order not fully delivered?":
      "Warum ist dieser Auftrag nicht vollständig geliefert?",
    "Which invoices remain open?": "Welche Rechnungen sind noch offen?",
    "Was that useful? Support Reality with a star on GitHub.":
      "War das hilfreich? Unterstütze Reality mit einem Stern auf GitHub.",
    "Star on GitHub": "Stern auf GitHub geben",
    "Keep exploring": "Weiter erkunden",
    "Free AI questions remaining": "Verbleibende kostenlose KI-Fragen",
    "Resets at": "Wieder verfügbar ab",
    "Your daily AI allowance is used. Keep exploring the records or return after the reset.":
      "Dein tägliches KI-Kontingent ist aufgebraucht. Erkunde weiter die Datensätze oder stelle nach der Erneuerung weitere Fragen.",

    "No admission limit": "Keine Zugangsbeschränkung",
    "Manual approval required": "Manuelle Freigabe erforderlich",
    "Create your account and verify your email to continue.":
      "Erstelle dein Konto und bestätige deine E-Mail-Adresse, um fortzufahren.",
    "Admission follows your deployment settings. Review pending applications here.":
      "Der Zugang richtet sich nach deinen Deployment-Einstellungen. Prüfe hier ausstehende Anfragen.",
    "Reset filters": "Filter zurücksetzen",
    "No entries yet.": "Noch keine Einträge.",
    "No entries yet. Use the create action to add the first entry.":
      "Noch keine Einträge. Lege über die Anlegen-Aktion den ersten Eintrag an.",
    "Set up the accounts and tax codes used by your external bookkeeping software, then define how Reality assigns them.":
      "Hinterlege die Konten und Steuerschlüssel deiner externen Buchhaltung und lege anschließend fest, wie Reality sie zuordnet.",
    "Selected accounting target": "Ausgewählte externe Buchhaltung",
    "Back to accounting targets": "Zurück zu den externen Buchhaltungen",
    "Open account setup": "Kontenzuordnung einrichten",
    "Add your external bookkeeping system here. Open its account setup to maintain accounts, tax codes and assignment rules.":
      "Lege hier deine externe Buchhaltung an. Öffne anschließend die Kontenzuordnung, um Konten, Steuerschlüssel und Zuordnungsregeln zu verwalten.",
    "Add the account numbers used in this bookkeeping system. Rules can then assign transactions to these accounts.":
      "Hinterlege die Kontonummern dieser Buchhaltung. Über Regeln ordnest du diesen Konten anschließend Geschäftsvorgänge zu.",
    "Add the tax codes used in this bookkeeping system. You can select them when defining assignment rules.":
      "Hinterlege die Steuerschlüssel dieser Buchhaltung. Du kannst sie anschließend in den Zuordnungsregeln auswählen.",
    "Define which external account and tax code a transaction should use. Add the required accounts and tax codes first.":
      "Lege fest, welches externe Konto und welcher Steuerschlüssel für einen Geschäftsvorgang gelten. Hinterlege zuerst die benötigten Konten und Steuerschlüssel.",
    "No accounting targets yet.": "Noch keine externe Buchhaltung angelegt.",
    "No external accounts yet.": "Noch keine externen Konten angelegt.",
    "No tax codes yet.": "Noch keine Steuerschlüssel angelegt.",
    "No assignment rules yet.": "Noch keine Zuordnungsregeln angelegt.",

    "Set up standard accounts": "Standardkonten einrichten",
    "These defaults apply to new transactions. Linked payments and corrections can retain the accounts of the original invoice.":
      "Diese Standardkonten gelten für neue Vorgänge. Zugeordnete Zahlungen und Korrekturen können die Konten der ursprünglichen Rechnung beibehalten.",
    "Add account": "Konto hinzufügen",
    "View account usage": "Kontenverwendung anzeigen",
    "Accounts for business transactions": "Konten für Geschäftsvorgänge",
    "Change default": "Standard ändern",
    "Change default account": "Standardkonto ändern",
    "Back to accounts": "Zurück zu den Konten",
    "Choose the accounts Reality uses for receivables, payables, payments and settlement differences.":
      "Lege fest, welche Konten Reality für Forderungen, Verbindlichkeiten, Zahlungen und Zahlungsdifferenzen verwendet.",
    "Default means Reality selects this account automatically for its role. External ledger numbers are managed under External accounting.":
      "Standard bedeutet: Reality wählt dieses Konto automatisch für seine Kontenrolle. Kontonummern der externen Buchhaltung verwaltest du unter Externe Buchhaltung.",
    "See which operational accounts each transaction uses. Change a role default when future transactions should use a different account.":
      "Hier siehst du, welche operativen Konten die einzelnen Vorgänge verwenden. Ändere das Standardkonto einer Rolle, wenn künftige Vorgänge ein anderes Konto verwenden sollen.",
    "This default applies to every transaction using this account role. Existing postings keep their original accounts.":
      "Dieses Standardkonto gilt für alle Vorgänge mit dieser Kontenrolle. Bestehende Buchungen behalten ihre ursprünglichen Konten.",
    "Add an active account with this role before changing the default.":
      "Füge zuerst ein aktives Konto mit dieser Rolle hinzu, bevor du den Standard änderst.",
    "All fields are required unless marked optional.":
      "Alle Felder sind Pflichtfelder, sofern sie nicht als optional gekennzeichnet sind.",
    "A prepared change is waiting for your confirmation.":
      "Eine vorbereitete Änderung wartet auf deine Bestätigung.",
    "Continue review": "Prüfung fortsetzen",
    "Edit account": "Konto bearbeiten",
    "Review account change": "Kontoänderung prüfen",
    "Create cost center": "Kostenstelle anlegen",
    "Edit cost center": "Kostenstelle bearbeiten",
    "Create case code": "Fallcode anlegen",
    "Edit case code": "Fallcode bearbeiten",
    "Create coding group": "Kontierungsgruppe anlegen",
    "Edit coding group": "Kontierungsgruppe bearbeiten",
    "Create accounting target": "Buchhaltungsziel anlegen",
    "Edit accounting target": "Buchhaltungsziel bearbeiten",
    "Create external account": "Externes Konto anlegen",
    "Edit external account": "Externes Konto bearbeiten",
    "Create tax code": "Steuerschlüssel anlegen",
    "Edit tax code": "Steuerschlüssel bearbeiten",
    "Create mapping rule": "Zuordnungsregel anlegen",
    "Edit mapping rule": "Zuordnungsregel bearbeiten",
    "Search by code or name": "Nach Code oder Name suchen",
    "Target identifier": "Kennung des Buchhaltungsziels",
    "Coding group condition": "Bedingung für die Kontierungsgruppe",
    "No coding group condition": "Ohne Bedingung für die Kontierungsgruppe",
    "Check the proposed values. The change takes effect only after confirmation.":
      "Prüfe die vorgeschlagenen Werte. Die Änderung wird erst nach der Bestätigung wirksam.",
    "The account role determines which operational transactions can use this account. External ledger numbers are configured under External accounting.":
      "Die Kontenrolle legt fest, welche operativen Vorgänge dieses Konto verwenden können. Externe Sachkonten verwaltest du unter Externe Buchhaltung.",
    "The role is fixed after creation. The default account is used when a transaction does not specify another eligible account.":
      "Die Rolle ist nach dem Anlegen fest. Das Standardkonto wird verwendet, wenn im Vorgang kein anderes zulässiges Konto angegeben ist.",
    "Use a short, unique code and a recognizable name. The code cannot be changed after creation.":
      "Verwende einen kurzen, eindeutigen Code und einen verständlichen Namen. Der Code ist nach dem Anlegen unveränderlich.",
    "Identify the department, location or project receiving the cost, for example SALES or BERLIN. Codes remain permanent.":
      "Benenne die Abteilung, den Standort oder das Projekt, dem Kosten zugeordnet werden, zum Beispiel VERTRIEB oder BERLIN. Codes bleiben unveränderlich.",
    "Define a business case such as domestic sales or export. A case code is a declared classification, not an automatic tax calculation.":
      "Definiere einen Geschäftsfall wie Inlandsverkauf oder Export. Ein Fallcode ist eine festgelegte Einordnung und berechnet keine Steuern.",
    "Group products or services that need the same account mapping. A rule can require an exact coding group.":
      "Fasse Produkte oder Leistungen mit gleicher Kontenzuordnung zusammen. Eine Regel kann eine bestimmte Kontierungsgruppe voraussetzen.",
    "Choose the source system and its original code, then the internal case code or coding group it means.":
      "Wähle das Quellsystem und seinen ursprünglichen Code. Ordne anschließend den passenden internen Fallcode oder die Kontierungsgruppe zu.",
    "The source namespace groups codes from the same source, for example a tax-code list. Copy namespace and code exactly as received.":
      "Der Quellnamensraum bündelt Codes derselben Quelle, zum Beispiel eine Steuerschlüsselliste. Übernimm Namensraum und Code exakt aus der Quelle.",
    "Choose when this rule applies and which external account it selects. All conditions must match exactly.":
      "Lege fest, wann diese Regel gilt und welches externe Konto sie auswählt. Alle Bedingungen müssen exakt zutreffen.",
    "Enter the code and name used by your external accounting software.":
      "Trage Code und Namen aus deiner externen Buchhaltungssoftware ein.",
    "Explain why you are adding or changing this entry. This note is retained in its history.":
      "Begründe kurz, warum du diesen Eintrag anlegst oder änderst. Die Begründung bleibt in der Historie erhalten.",
    "Assignment belongs to an earlier evidence version":
      "Zuordnung gehört zu einer früheren Belegversion",
    "Internal assignment": "Interne Zuordnung",
    "Account settings areas": "Bereiche der Konteneinstellungen",
    "Accounting target": "Buchhaltungsziel",
    "Accounting targets": "Buchhaltungsziele",
    "Define permitted external destinations. Local balances remain independent.":
      "Erlaubte externe Ziele definieren. Lokale Salden bleiben unabhängig.",
    "Edit configuration": "Konfiguration bearbeiten",
    "New configuration": "Neue Konfiguration",
    "Exact coding group": "Exakte Kontierungsgruppe",
    "External account": "Externes Konto",
    "External accounts": "Externe Konten",
    "External accounting": "Externe Buchhaltung",
    "External accounting areas": "Bereiche der externen Buchhaltung",
    "Gross operational account references": "Operative Konten mit Bruttobeträgen",
    "Group discrimination": "Unterscheidung nach Gruppe",
    "Mapping history": "Zuordnungshistorie",
    "Mapping preview": "Zuordnungsvorschau",
    "Mapping revision": "Zuordnungsversion",
    "Mapping scope": "Zuordnungsbereich",
    Namespace: "Namensraum",
    "Operational account": "Operatives Konto",
    "Received components": "Übernommene Belegbestandteile",
    "Review configuration": "Konfiguration prüfen",
    "Shows external destinations, not export completeness or external posting.":
      "Zeigt externe Zuordnungen. Exportvollständigkeit und externe Buchung sind damit nicht bestätigt.",
    "Tax code": "Steuerschlüssel",
    "Tax codes": "Steuerschlüssel",
    Transaction: "Vorgang",
    "Without group discrimination": "Ohne Gruppenunterscheidung",
    "Mapping resolved": "Zuordnung gefunden",
    "A declared case is required": "Ein deklarierter Fallcode fehlt",
    "A coding group is required": "Eine Kontierungsgruppe fehlt",
    "No matching target rule": "Keine passende Zielregel vorhanden",
    "Multiple target rules match": "Mehrere Zielregeln treffen zu",
    "Accounting target is blocked": "Buchhaltungsziel ist gesperrt",
    "External destination is blocked": "Externe Referenz ist gesperrt",
    "Operational account is blocked": "Operatives Konto ist gesperrt",
    "Source and internal case conflict":
      "Fallcode aus Quelle und interner Zuordnung widersprechen sich",
    "Source and internal group conflict":
      "Gruppe aus Quelle und interner Zuordnung widersprechen sich",
    "Classification needs review": "Klassifizierung muss geprüft werden",
    "Transaction matrix": "Vorgangsmatrix",
    Configured: "Konfiguriert",
    "Missing default": "Standardkonto fehlt",
    "Incompatible account role": "Unpassende Kontenrolle",
    "Configured default accounts": "Konfigurierte Standardkonten",
    "Original control account when linked": "Bei Zuordnung gilt das ursprüngliche Personenkonto",
    "Original invoice account required": "Ursprüngliches Rechnungskonto erforderlich",
    "These are current defaults. The action preview validates the actual evidence and accounts.":
      "Dies sind die aktuellen Standardkonten. Die Aktionsvorschau prüft die konkreten Belege und Konten.",
    "Reversals retain original accounts and reverse the original group.":
      "Stornierungen verwenden die ursprünglichen Konten und kehren die ursprüngliche Buchungsgruppe um.",
    "Orders, reservations, stock movements and allocations do not add postings here.":
      "Aufträge, Reservierungen, Warenbewegungen und Zahlungszuordnungen erzeugen hier keine zusätzlichen Buchungen.",
    "Configure accounts": "Konten konfigurieren",
    "Amount basis": "Betragsbasis",
    "Stated invoice gross": "Angegebener Rechnungsbruttobetrag",
    "Stated payment amount": "Angegebener Zahlungsbetrag",
    "Stated refund amount": "Angegebener Erstattungsbetrag",
    "Explicitly accepted reduction": "Ausdrücklich anerkannter Minderungsbetrag",
    "Stated opening residual": "Angegebener Eröffnungsrestbetrag",
    "Customer settlement reduction": "Anerkannte Kundenminderung",
    "Supplier settlement reduction": "Anerkannte Lieferantenminderung",
    "Opening customer debt": "Eröffnungsforderung an Kunden",
    "Opening customer credit": "Eröffnungsguthaben des Kunden",
    "Opening supplier debt": "Eröffnungsverbindlichkeit an Lieferanten",
    "Opening supplier credit": "Eröffnungsguthaben beim Lieferanten",
    "Sales invoice": "Kundenrechnung",
    "Customer credit note": "Kundengutschrift",
    "Customer payment": "Kundenzahlung",
    "Customer refund": "Kundenerstattung",
    "Supplier invoice": "Lieferantenrechnung",
    "Supplier credit note": "Lieferantengutschrift",
    "Supplier payment": "Lieferantenzahlung",
    "Supplier refund": "Lieferantenerstattung",
    "Add cost-center share": "Kostenstellenanteil hinzufügen",
    "Assign individual lines. The document summary is not added again.":
      "Ordne einzelne Positionen zu. Die Belegsumme wird nicht zusätzlich berücksichtigt.",
    Assigned: "Zugeordnet",
    "Attribution basis": "Zuordnungsbasis",
    "Attribution history": "Zuordnungshistorie",
    "Attribution saved": "Zuordnung gespeichert",
    "Case code": "Fallcode",
    "Clear internal attribution": "Interne Zuordnung leeren",
    "Coding group": "Kontierungsgruppe",
    Components: "Bestandteile",
    "Confirm attribution": "Zuordnung bestätigen",
    "Cost center": "Kostenstelle",
    "Current attribution": "Aktuelle Zuordnung",
    "Enter explicit shares. Empty shares leave the amount unassigned.":
      "Erfasse die Anteile als Beträge. Ohne Anteile bleibt der Betrag unzugeordnet.",
    "Financial detail": "Finanzdetails",
    "Find classification references": "Zuordnungswerte suchen",
    "Inspect document": "Beleg untersuchen",
    "Inspect line": "Position untersuchen",
    "Internal attribution": "Interne Zuordnung",
    "No internal attribution": "Keine interne Zuordnung",
    "Original source codes": "Ursprüngliche Quellcodes",
    "Received component": "Empfangener Bestandteil",
    "Received document summary": "Empfangene Belegsummen",
    "Refine the reference search to find more entries.":
      "Verfeinere die Suche, um weitere Einträge zu finden.",
    "Remove share": "Anteil entfernen",
    "Review attribution": "Zuordnung prüfen",
    "Select cost center": "Kostenstelle auswählen",
    "Select financial component": "Finanzbestandteil auswählen",
    "Share amount": "Anteilbetrag",
    "This document has no lines. Attribution uses its received amounts.":
      "Dieser Beleg hat keine Positionen. Die Zuordnung verwendet seine empfangenen Beträge.",
    Unassigned: "Nicht zugeordnet",
    "Other received basis": "Andere empfangene Basis",
    "Inspect financial detail": "Finanzdetails untersuchen",
    "See open commitments, exceptions and decisions across your company.":
      "Sieh offene Verpflichtungen, Abweichungen und Entscheidungen deiner Firma.",
    "Track outstanding deliveries to your customers.":
      "Verfolge ausstehende Lieferungen an deine Kunden.",
    "Track outstanding deliveries from your suppliers.":
      "Verfolge ausstehende Lieferungen deiner Lieferanten.",
    "Review issues that need attention and inspect the records behind them.":
      "Prüfe Abweichungen und die zugrunde liegenden Datensätze.",
    "Review proposed actions and decide whether to proceed.":
      "Prüfe vorgeschlagene Aktionen und entscheide über ihre Ausführung.",
    "See physical, reserved and available stock for each item.":
      "Sieh physischen, reservierten und verfügbaren Bestand je Artikel.",
    "See which stock is reserved for each commitment.":
      "Sieh, welcher Bestand für welche Verpflichtung reserviert ist.",
    "Follow recorded stock receipts, shipments and adjustments.":
      "Verfolge erfasste Wareneingänge, Warenausgänge und Bestandskorrekturen.",
    "See outstanding receivables and payables, grouped by currency.":
      "Sieh offene Forderungen und Verbindlichkeiten, getrennt nach Währung.",
    "Review recorded incoming and outgoing payments.":
      "Prüfe erfasste Zahlungseingänge und Zahlungsausgänge.",
    "Inspect recorded ledger entries and their supporting records.":
      "Prüfe Buchungen und die zugehörigen Nachweise.",
    "Follow how sources, documents and business records connect over time.":
      "Verfolge, wie Quellen, Belege und Geschäftsdaten über die Zeit zusammenhängen.",
    "Explore a record and follow its links to related information.":
      "Erkunde einen Datensatz und seine Verknüpfungen zu weiteren Informationen.",
    "Explore your company’s recorded information and trace it to its sources.":
      "Erkunde die erfassten Informationen deiner Firma und verfolge ihre Herkunft.",
    "Explore how existing records are combined into calculated views.":
      "Sieh, wie berechnete Ansichten aus vorhandenen Datensätzen entstehen.",
    "Review the rules that record additional facts from source data on the right business record.":
      "Prüfe die Regeln, die aus Quelldaten zusätzliche Fakten am richtigen Geschäftsdatensatz festhalten.",
    "Explore the conditions that identify issues requiring attention.":
      "Sieh, welche Bedingungen auf Abweichungen hinweisen.",
    "See what was recorded across your company, newest first.":
      "Sieh die erfassten Ereignisse deiner Firma, die neuesten zuerst.",
    "Explore available actions, their inputs and what they do.":
      "Erkunde verfügbare Aktionen, ihre Eingaben und ihre Wirkung.",
    "Explore additional observations, their sources and the records they describe.":
      "Erkunde zusätzliche Beobachtungen, ihre Quellen und die beschriebenen Datensätze.",
    "Track delivery commitments and inspect their reservations and movements.":
      "Verfolge Lieferverpflichtungen und prüfe ihre Reservierungen und Warenbewegungen.",
    "Review customer orders and follow their linked delivery commitments.":
      "Prüfe Kundenaufträge und die zugehörigen Lieferverpflichtungen.",
    "Review purchase orders and follow their linked delivery commitments.":
      "Prüfe Bestellungen und die zugehörigen Lieferverpflichtungen.",
    "Find customers and review their details and commercial defaults.":
      "Finde Kunden und prüfe ihre Stammdaten und Geschäftsbedingungen.",
    "Find suppliers and review their details and commercial defaults.":
      "Finde Lieferanten und prüfe ihre Stammdaten und Geschäftsbedingungen.",
    "Find items and review their reference details.": "Finde Artikel und prüfe ihre Stammdaten.",
    "Find locations and review their reference details.":
      "Finde Standorte und prüfe ihre Stammdaten.",
    "Plan integrations and manage registered data sources.":
      "Plane Integrationen und verwalte registrierte Datenquellen.",
    "Inspect received data, its import status and linked business records.":
      "Prüfe empfangene Daten, ihren Importstatus und verknüpfte Geschäftsdaten.",
    "Inspect recorded documents and trace them to their original sources.":
      "Prüfe erfasste Belege und verfolge ihre ursprünglichen Quellen.",
    "Explore the current delivery position and the recorded activity behind it.":
      "Analysiere den aktuellen Lieferstand und die zugrunde liegenden Ereignisse.",
    "Switch companies or manage their users, agents and AI settings.":
      "Wechsle die Firma oder verwalte ihre Benutzer, Agenten und KI-Einstellungen.",
    "Set your language, number format, timezone and appearance.":
      "Lege Sprache, Zahlenformat, Zeitzone und Darstellung fest.",
    "Control synthetic data arrivals and review recent demo activity.":
      "Steuere den Eingang synthetischer Daten und prüfe die letzten Demo-Ereignisse.",
    "Demo company": "Demofirma",
    "View data": "Ansichtsdaten",
    "Graph starting points": "Graph-Einstiege",
    "Starting point": "Einstieg",
    "No records are available for this starting point yet.":
      "Für diesen Einstieg sind noch keine Datensätze vorhanden.",
    "Choose a starting point or search for a record.":
      "Wähle einen Einstieg oder suche nach einem Datensatz.",
    Order: "Auftrag",
    Fact: "Fakt",
    Columns: "Spalten",
    "Compact rows": "Kompakte Zeilen",
    "Filter records": "Datensätze filtern",
    Observation: "Beobachtung",
    "Reset table": "Tabelle zurücksetzen",
    "Resize column": "Spaltenbreite ändern",
    "Rows per page": "Zeilen pro Seite",
    "Scrollable register": "Scrollbare Tabelle",
    "Sort column": "Spalte sortieren",
    "All subject types": "Alle Bezugstypen",
    "An observation is not a current-state guarantee. Different observations can coexist; this view does not choose a winning value.":
      "Eine Beobachtung garantiert keinen aktuellen Zustand. Unterschiedliche Beobachtungen können nebeneinander bestehen; diese Ansicht wählt keinen maßgeblichen Wert aus.",
    "Clear filters": "Filter entfernen",
    "Exact predicate": "Exaktes Prädikat",
    "Explain observation": "Beobachtung erklären",
    "Explore recorded observations about your business. Each observation keeps its own value, time and origin.":
      "Erkunde erfasste Beobachtungen zu deinem Unternehmen. Jede behält ihren eigenen Wert, Zeitpunkt und Ursprung.",
    "Fact ID": "Fakten-ID",
    "Interpretation rule": "Interpretationsregel",
    "No linked source recorded": "Keine verknüpfte Quelle erfasst",
    "No observations found": "Keine Beobachtungen gefunden",
    "Predicate, value, subject ID or source reference":
      "Prädikat, Wert, Bezugs-ID oder Quellenreferenz",
    "Related observations": "Verwandte Beobachtungen",
    "Search observations": "Beobachtungen suchen",
    "Shipping priority": "Versandpriorität",
    "Source record ID": "Quelldatensatz-ID",
    "Subject ID": "Bezugs-ID",
    "Subject type": "Bezugstyp",
    "The first 100 subject types are listed. Search can find observations of other types.":
      "Die ersten 100 Bezugstypen werden angezeigt. Über die Suche findest du auch Beobachtungen anderer Typen.",
    "Try another search or clear the filters. Facts appear when a source-backed observation is recorded.":
      "Versuche eine andere Suche oder entferne die Filter. Fakten erscheinen, sobald eine Beobachtung mit Quellenbezug erfasst wird.",
    Value: "Wert",
    "View observations": "Beobachtungen ansehen",
    "What was observed, and where it came from.": "Was beobachtet wurde und woher es stammt.",
    "This is a recorded observation, not a current-state guarantee.":
      "Dies ist eine erfasste Beobachtung, keine Garantie für den aktuellen Zustand.",
    "Context and source": "Kontext und Quelle",
    "Remaining quantity": "Restmenge",
    "Advanced order operations": "Erweiterte Auftragsbearbeitung",
    "All delivery history": "Gesamter Lieferverlauf",
    "Clear order filter": "Auftragsfilter entfernen",
    "Customer deliveries": "Kundenlieferungen",
    "Customer delivery actions open in Your work. Supplier details include their linked evidence.":
      "Aktionen für Kundenlieferungen öffnen sich unter Deine Arbeit. Lieferantendetails enthalten die verknüpften Belege.",
    Deliveries: "Lieferungen",
    Shipments: "Sendungen",
    Dispatched: "Versendet",
    Carrier: "Frachtführer",
    Contents: "Inhalt",
    "Tracking number": "Trackingnummer",
    "Observed state": "Beobachteter Stand",
    "Physical contents": "Physischer Inhalt",
    "Tracking observations": "Tracking-Beobachtungen",
    "No stock movement recorded": "Keine Warenbewegung erfasst",
    "Warehouse and carrier observations differ":
      "Lager- und Frachtführerbeobachtungen weichen voneinander ab",
    "Search carrier, tracking number or shipment ID":
      "Frachtführer, Trackingnummer oder Sendungs-ID suchen",
    "Shipment ID": "Sendungs-ID",
    "Package ID (optional)": "Paket-ID (optional)",
    Reporter: "Meldende Stelle",
    "Replacement event ID (optional)": "ID des Ersatzereignisses (optional)",
    "Counterparty ID": "Geschäftspartner-ID",
    "Movement inputs (JSON)": "Movement-Eingaben (JSON)",
    "Movements must be a JSON array": "Movements müssen ein JSON-Array sein",
    "Review exact effect": "Exakte Wirkung prüfen",
    "Prepare the exact shipment change, then review it before confirmation.":
      "Bereite die exakte Sendungsänderung vor und prüfe sie vor der Bestätigung.",
    "Deliveries for the selected order": "Lieferungen zum ausgewählten Auftrag",
    "Delivery direction": "Lieferrichtung",
    "Delivery scope": "Lieferumfang anzeigen",
    "From order to delivery.": "Vom Auftrag zur Lieferung.",
    Lines: "Positionen",
    "No due date": "Ohne Liefertermin",
    "Open deliveries have a remaining quantity and an open commitment. All history includes completed and cancelled commitments.":
      "Offene Lieferungen haben eine Restmenge und eine offene Zusage. Der gesamte Verlauf umfasst auch erfüllte und stornierte Zusagen.",
    "Order document": "Auftragsbeleg",
    "Order documents record the agreement. Delivery progress comes from linked commitments and movements.":
      "Auftragsbelege halten die Vereinbarung fest. Der Lieferfortschritt ergibt sich aus verknüpften Zusagen und Warenbewegungen.",
    "Orders & deliveries": "Aufträge & Lieferungen",
    "Recorded status": "Erfasster Status",
    "Search orders and deliveries": "Aufträge und Lieferungen suchen",
    "Search party, item or delivery ID": "Geschäftspartner, Artikel oder Liefer-ID suchen",
    "See what was agreed, what is still open and the records behind it.":
      "Sieh, was vereinbart wurde, was noch offen ist und welche Daten dahinterstehen.",
    "Supplier deliveries": "Lieferantenzuläufe",
    "Supplier orders": "Lieferantenbestellungen",
    "Unknown item": "Unbekannter Artikel",
    "Unknown location": "Unbekannter Lagerort",
    "View deliveries": "Lieferungen ansehen",
    Failed: "Fehlgeschlagen",
    Unknown: "Unbekannt",
    Expired: "Abgelaufen",
    "Sending invitation": "Einladung wird gesendet",
    "Invitation delivered": "Einladung zugestellt",
    "Delivery retry scheduled": "Erneuter Versand geplant",
    "Invitation delivery": "Einladungsversand",

    "Advanced company settings": "Erweiterte Firmeneinstellungen",
    "AI credentials configured": "KI-Zugang eingerichtet",
    "AI credentials not configured": "KI-Zugang nicht eingerichtet",
    "Appearance is saved in this browser. System follows your device.":
      "Die Darstellung wird in diesem Browser gespeichert. System folgt deiner Geräteeinstellung.",
    "Check saved preferences": "Gespeicherte Einstellungen prüfen",
    "Company access": "Firmenzugriff",
    "Company credentials": "Firmeneigener Zugang",
    "Configuration status does not confirm a live connection to the AI provider.":
      "Der Konfigurationsstatus bestätigt keine aktive Verbindung zum KI-Anbieter.",
    "Credential management": "Zugangsverwaltung",
    Expires: "Gültig bis",
    "Make Reality work for you.": "Reality, passend zu deinem Alltag.",
    "Manage invitations, credentials and company setup in company administration.":
      "Einladungen, Zugangsdaten und Firmeneinrichtung findest du in der Firmenverwaltung.",
    Member: "Mitglied",
    "Not configured": "Nicht eingerichtet",
    "Number and date format": "Zahlen- und Datumsformat",
    "Only company owners can view these settings.":
      "Nur Firmeneigentümer können diese Einstellungen ansehen.",
    Owner: "Eigentümer",
    "Personal preferences": "Persönlich",
    "Preferences saved.": "Einstellungen gespeichert.",
    "Saved preferences differ from your draft. Review it before saving again.":
      "Die gespeicherten Einstellungen unterscheiden sich von deinem Entwurf. Prüfe ihn vor dem erneuten Speichern.",
    "Settings sections": "Einstellungsbereiche",
    "These preferences apply to your account across all companies.":
      "Diese Einstellungen gelten für dein Konto in allen Firmen.",
    "This view shows up to 500 members and 500 invitations.":
      "Diese Ansicht zeigt bis zu 500 Mitglieder und 500 Einladungen.",
    "Time zone": "Zeitzone",
    "Use an IANA time zone, such as Europe/Rome or America/New_York.":
      "Verwende eine IANA-Zeitzone, etwa Europe/Rome oder America/New_York.",
    "Your preferences, company access and AI configuration in one place.":
      "Deine Einstellungen, Firmenzugriff und KI-Konfiguration an einem Ort.",
    "Preferences were not saved. Check your entries and try again.":
      "Die Einstellungen wurden nicht gespeichert. Prüfe deine Eingaben und versuche es erneut.",
    "The save result is unknown. Check saved preferences before trying again.":
      "Das Speicherergebnis ist unklar. Prüfe die gespeicherten Einstellungen vor einem neuen Versuch.",
    "Could not check saved preferences. Try checking again.":
      "Die gespeicherten Einstellungen konnten nicht geprüft werden. Versuche die Prüfung erneut.",
    Queued: "In Warteschlange",
    Sending: "Wird gesendet",
    "Not sent": "Nicht gesendet",
    "Clear source version": "Quellversion zurücksetzen",
    "Document / party": "Beleg / Geschäftspartner",
    "Documents are evidence. Delivery and payment state comes from the linked business records.":
      "Dokumente sind Belege. Liefer- und Zahlungsstand ergeben sich aus den verknüpften Geschäftsdaten.",
    Enabled: "Aktiviert",

    "Exact source version": "Genaue Quellversion",
    "Exact system code": "Genauer Systemcode",
    "External reference / origin": "Externe Referenz / Herkunft",
    "Follow registered origins, received originals and the evidence they produced.":
      "Verfolge registrierte Herkunftssysteme, empfangene Originale und die daraus entstandenen Belege.",
    "Import job": "Import-Auftrag",
    "Job status describes processing, not interpretation success. Open a record to inspect its original.":
      "Der Auftragsstatus beschreibt die Verarbeitung, nicht den Erfolg der Interpretation. Öffne einen Datensatz für das Original.",
    "No import job": "Kein Import-Auftrag",
    "No linked source": "Keine verknüpfte Quelle",
    "Open original": "Original öffnen",
    "Originals preserve what arrived. Documents hold evidence. Reality describes the business state.":
      "Originale bewahren den empfangenen Inhalt. Dokumente halten Belege fest. Reality beschreibt den Geschäftsstand.",
    "Received records": "Empfangene Daten",
    "received versions": "empfangene Versionen",
    "Recorded amount": "Erfasster Betrag",
    "Registered systems are definitions, not proof of a live connection. Counts include every held source version.":
      "Registrierte Systeme sind Definitionen und belegen keine aktive Verbindung. Gezählt werden alle gespeicherten Quellversionen.",
    "Search data": "Daten suchen",
    "Search document number, reference or source": "Belegnummer, Referenz oder Quelle suchen",
    "Search origin, type or external reference": "Herkunft, Typ oder externe Referenz suchen",
    "Search system name or code": "Systemname oder Code suchen",
    "See where your business data comes from.": "Verstehe, woher deine Geschäftsdaten kommen.",
    "Source setup and imports": "Quellen einrichten und importieren",
    Systems: "Herkunftssysteme",
    "Technical Explorer": "Technischer Explorer",
    "View evidence": "Belege ansehen",
    "View received records": "Empfangene Daten ansehen",
    "Account / posting": "Konto / Buchung",
    "Advanced finance operations": "Weitere Finanzaktionen",
    "All filtered records": "Alle gefilterten Datensätze",
    "Amounts follow recorded postings and allocations. Each currency stays separate.":
      "Beträge beruhen auf erfassten Buchungen und Zuordnungen. Jede Währung bleibt getrennt.",
    Balance: "Saldo",
    Credit: "Haben",
    Debit: "Soll",
    "Debits and credits follow the selected account and search. A filtered balance need not be zero.":
      "Soll und Haben beziehen sich auf das gewählte Konto und die Suche. Der gefilterte Saldo muss nicht null sein.",
    "Exact account": "Genaues Konto",
    "Follow outstanding invoices, recorded payments and their financial evidence.":
      "Verfolge offene Rechnungen, erfasste Zahlungen und die zugehörigen Belege.",
    "Invoice / party": "Rechnung / Geschäftspartner",
    "Operational financial records, not statutory accounts.":
      "Operative Finanzdaten, kein handelsrechtlicher Abschluss.",
    Outstanding: "Noch offen",
    "Partially settled": "Teilweise ausgeglichen",
    "Payment / party": "Zahlung / Geschäftspartner",
    "Recorded payment history includes reversals. Amounts are shown per payment.":
      "Die Zahlungshistorie enthält auch Stornierungen. Beträge werden je Zahlung angezeigt.",
    "Reversed original": "Storniertes Original",
    "Reversing entry": "Stornobuchung",
    "Search finance": "Finanzdaten suchen",
    "Search invoice or party": "Rechnung oder Geschäftspartner suchen",
    "Understand what is open, paid and recorded.": "Verstehe, was offen, bezahlt und gebucht ist.",
    Adjustment: "Bestandsanpassung",
    "Advanced warehouse operations": "Weitere Lageraktionen",
    "All severities": "Alle Prioritäten",
    "Available stock": "Verfügbarer Bestand",
    "Check current state": "Aktuellen Stand prüfen",
    "Clear item filter": "Artikelfilter entfernen",
    "Company-wide stock per item. Quantities retain their own units.":
      "Unternehmensweiter Bestand je Artikel. Mengen behalten ihre eigene Einheit.",
    Compensation: "Gegenbuchung",
    Consumed: "Verbraucht",
    Corrected: "Korrigiert",
    Correction: "Korrektur",
    Critical: "Kritisch",
    "Current finding": "Aktueller Klärfall",
    "Current findings, their causes and the records that explain them.":
      "Aktuelle Klärfälle, ihre Ursachen und die zugehörigen Datensätze.",
    "Explain finding": "Klärfall erklären",
    "Findings clear when the underlying records change. They are not manually dismissed tasks.":
      "Klärfälle lösen sich auf, wenn sich die zugrunde liegenden Daten ändern. Sie werden nicht manuell abgehakt.",
    "Findings reflect the records currently available in this company.":
      "Klärfälle beruhen auf den aktuell verfügbaren Daten dieses Unternehmens.",
    High: "Hoch",
    "Know what is available, and why.": "Verstehe, was verfügbar ist – und warum.",
    Low: "Niedrig",
    "No available stock": "Kein verfügbarer Bestand",
    "No current findings": "Keine aktuellen Klärfälle",
    "No matching findings": "Keine passenden Klärfälle",
    Normal: "Regulär",
    "Open a finding to see its cause, supporting records and next step.":
      "Öffne einen Klärfall für Ursache, zugehörige Datensätze und den nächsten Schritt.",
    "Open delivery": "Lieferung öffnen",
    "Open warehouse": "Lager öffnen",
    "Overallocated stock": "Überreservierter Bestand",
    Receipt: "Wareneingang",
    "Recorded causes and references": "Erfasste Ursachen und Referenzen",
    "Recorded history includes corrected originals and compensations.":
      "Die erfasste Historie enthält korrigierte Originale und Gegenbuchungen.",
    Released: "Freigegeben",
    Replacement: "Ersatzbuchung",
    "Reserved stock is linked to its commitment.":
      "Reservierter Bestand ist mit seiner Zusage verbunden.",
    "Resolution guidance": "Hinweis zur Klärung",
    "Search by item name or SKU": "Nach Artikelname oder SKU suchen",
    "Search by reference ID": "Nach Referenz-ID suchen",
    "Search causes or references": "Ursachen oder Referenzen suchen",
    "Search exceptions": "Klärfälle durchsuchen",
    "Search warehouse": "Lager durchsuchen",
    "See what needs a closer look.": "Sieh, was genauer geprüft werden muss.",
    Severity: "Priorität",
    "Start with a finding": "Wähle einen Klärfall",
    Stock: "Bestand",
    "Stock, its reservations and the movements behind it.":
      "Bestand, seine Reservierungen und die Bewegungen dahinter.",
    "Supplier return": "Lieferantenretoure",
    "Supporting record": "Zugehöriger Datensatz",
    Transfer: "Umlagerung",
    "Try another filter or inspect the original records.":
      "Versuche einen anderen Filter oder prüfe die Originaldatensätze.",
    Workspaces: "Arbeitsbereiche",
    Customers: "Kunden",
    Suppliers: "Lieferanten",
    Roles: "Rollen",
    "Date (UTC)": "Datum (UTC)",
    Analytics: "Auswertungen",
    "Needs reservation": "Reservierung fehlt",
    "Overdue deliveries": "Überfällige Lieferungen",
    "Without due date": "Ohne Fälligkeit",
    "Delivery commitments created": "Angelegte Lieferzusagen",
    "Shipment movements": "Versandbewegungen",
    "How your operations are moving": "Wie sich dein Betrieb entwickelt",
    "Open analytics": "Analytics öffnen",
    "Recorded activity over time": "Erfasste Aktivität im Zeitverlauf",
    "Delivery commitments created and shipment movements":
      "Angelegte Lieferzusagen und Versandbewegungen",
    "Understand the flow of your business.": "Verstehe den Fluss deines Geschäfts.",
    "Current delivery position and the activity behind it.":
      "Aktueller Lieferstand und die Aktivität dahinter.",
    "No open deliveries to measure": "Keine offenen Lieferungen zur Auswertung",
    "of open deliveries": "der offenen Lieferungen",
    "Current position · view records": "Aktueller Stand · Datensätze ansehen",
    "Recorded activity": "Erfasste Aktivität",
    "Counts of commitments and movements · UTC days":
      "Anzahl der Zusagen und Bewegungen · UTC-Tage",
    Period: "Zeitraum",
    days: "Tage",
    "These series count different records, not order conversion. Corrections are reflected in shipment counts. External history may be incomplete.":
      "Diese Reihen zählen unterschiedliche Datensätze, keine Auftragskonversion. Korrekturen sind in der Versandanzahl berücksichtigt. Die externe Historie kann unvollständig sein.",
    "Daily values and supporting records": "Tageswerte und zugehörige Datensätze",
    "Supporting records": "Zugrunde liegende Datensätze",
    records: "Datensätze",
    "No matching records": "Keine passenden Datensätze",
    "Observed at": "Beobachtet am",
    "Current position is independent of the selected period.":
      "Der aktuelle Stand ist unabhängig vom gewählten Zeitraum.",
    "Master data action": "Stammdatenaktion",
    "Master data": "Stammdaten",
    "Edit details": "Details bearbeiten",
    "Item type": "Artikeltyp",
    Tracking: "Nachverfolgung",
    "Default location": "Standardlagerort",
    "Purchase unit": "Einkaufseinheit",
    "Conversion factor": "Umrechnungsfaktor",
    "Lead time (days)": "Lieferzeit (Tage)",
    "Parent location": "Übergeordneter Lagerort",
    "Allows physical stock": "Erlaubt physischen Bestand",
    Stocked: "Lagerartikel",
    Service: "Dienstleistung",
    Charge: "Gebühr",
    "No tracking": "Keine Nachverfolgung",
    Serial: "Seriennummer",
    Identity: "Identität",
    "Commercial defaults": "Kaufmännische Vorgaben",
    "Inventory behaviour": "Bestandsverhalten",
    Hierarchy: "Hierarchie",
    "Reviewed revision": "Geprüfte Revision",
    "Choices could not be loaded.": "Auswahlwerte konnten nicht geladen werden.",
    "Create a record": "Datensatz anlegen",
    "Change recorded": "Änderung erfasst",
    "Outcome not yet verified": "Ergebnis noch nicht geprüft",
    "Ready for your confirmation": "Bereit zur Bestätigung",
    "Recorded intent and receipt. Current details may have changed since execution.":
      "Erfasster Auftrag und Ergebnis. Aktuelle Details können sich seit der Ausführung geändert haben.",
    "Check the exact fields below. Confirmation records this change.":
      "Prüfe die genauen Felder unten. Mit der Bestätigung wird die Änderung erfasst.",
    "Field changes": "Feldänderungen",
    "Recorded reference IDs": "Erfasste Referenz-IDs",
    "Open record": "Datensatz öffnen",
    "Prepare a change, review it, then confirm. Nothing is recorded yet.":
      "Änderung vorbereiten, prüfen und bestätigen. Noch wird nichts erfasst.",
    "A prepared request is saved. Check it before starting another change.":
      "Ein vorbereiteter Auftrag ist gespeichert. Prüfe ihn, bevor du eine weitere Änderung startest.",
    "Check prepared request": "Vorbereiteten Auftrag prüfen",
    "Prepare change": "Änderung vorbereiten",
    "Edit request": "Auftrag bearbeiten",
    "The people, products and places behind your operations.":
      "Die Menschen, Produkte und Orte hinter deinen Abläufen.",
    "Resume request": "Auftrag fortsetzen",
    "Search master data": "Stammdaten durchsuchen",
    "Search by name, SKU or ID": "Nach Name, SKU oder ID suchen",
    "Include inactive": "Inaktive einbeziehen",
    "Adjust your search or create the first record.":
      "Passe die Suche an oder lege den ersten Datensatz an.",
    Provenance: "Herkunft",
    "No original source is linked to this record.":
      "Mit diesem Datensatz ist keine Originalquelle verknüpft.",
    "All recorded details": "Alle erfassten Details",
    "Start with a record": "Wähle einen Datensatz",
    "Choose a customer, supplier, item or location to see its details and prepare a change.":
      "Wähle einen Kunden, Lieferanten, Artikel oder Ort, um Details zu sehen und eine Änderung vorzubereiten.",
    "Also available in chat": "Auch im Chat verfügbar",
    "Ask Reality to prepare a change. You review the same fields before confirming.":
      "Bitte Reality, eine Änderung vorzubereiten. Du prüfst dieselben Felder vor der Bestätigung.",
    "Advanced settings": "Erweiterte Einstellungen",
    "Recorded result is not yet verified.": "Das erfasste Ergebnis ist noch nicht verifiziert.",
    "Still open": "Noch offen",
    "Allocate available stock to a delivery.": "Verfügbaren Bestand einer Lieferung zuordnen.",
    "Record goods leaving the warehouse.": "Waren erfassen, die das Lager verlassen.",
    "More records are available in the workspace.":
      "Weitere Datensätze sind im Arbeitsbereich verfügbar.",
    "Open inventory": "Bestand öffnen",
    "Current observation unavailable": "Aktueller Stand nicht verfügbar",
    "Handling unit": "Ladeeinheit",
    Lot: "Charge",
    "Serial unit": "Seriennummer",
    History: "Verlauf",
    "No results": "Keine Ergebnisse",
    Pending: "Ausstehend",
    Delivery: "Lieferung",
    "Check outcome": "Ergebnis prüfen",
    "Choose a delivery": "Lieferung auswählen",
    "Confirm change": "Änderung bestätigen",
    "Execution outcome is being checked. Do not repeat the action.":
      "Das Ausführungsergebnis wird geprüft. Aktion nicht wiederholen.",
    "Preparing a review does not change stock.": "Die Vorbereitung verändert keinen Bestand.",
    "Record shipment": "Versand erfassen",
    "Recorded result is separate from the current observation.":
      "Erfasstes Ergebnis und aktueller Stand werden getrennt angezeigt.",
    Rejected: "Abgelehnt",
    "Review change": "Änderung prüfen",
    "Review the exact change before confirming.": "Prüfe die genaue Änderung vor der Bestätigung.",
    "Selected delivery": "Ausgewählte Lieferung",
    "Tracking references": "Bestandsidentitäten",
    "Not selected": "Nicht ausgewählt",
    "Refine your search to see more matches.": "Grenze die Suche für weitere Treffer ein.",
    "A clear view of what is open.": "Ein klarer Blick auf alles Offene.",
    "Ask about orders, stock and money.": "Frage nach Aufträgen, Bestand und Finanzen.",
    "Ask about your company": "Frage zu deinem Unternehmen",
    "Back to deliveries": "Zurück zu Lieferungen",
    "Choose a delivery to see what is open and why.":
      "Wähle eine Lieferung, um offene Punkte und ihre Gründe zu sehen.",
    "Choose an authorized company or open company settings.":
      "Wähle ein zugängliches Unternehmen oder öffne die Unternehmenseinstellungen.",
    "Company overview": "Unternehmensübersicht",
    "Company unavailable": "Unternehmen nicht verfügbar",
    Conversation: "Unterhaltung",
    "Customer delivery": "Kundenlieferung",
    "Daily work": "Tägliche Arbeit",
    "Data & sources": "Daten & Quellen",
    Decisions: "Entscheidungen",
    open: "offen",
    "Decisions & control": "Entscheidungen & Kontrolle",
    "Discuss with Reality": "Mit Reality besprechen",
    Explain: "Erklären",
    "Inventory at this location": "Bestand an diesem Lagerort",
    "Latest events": "Neueste Ereignisse",
    "More workspaces": "Weitere Arbeitsbereiche",
    Navigation: "Menü",
    "No document evidence": "Keine Belegnachweise",
    "No open commitments": "Keine offenen Zusagen",
    "No open deliveries": "Keine offenen Lieferungen",
    "No pending decisions": "Keine ausstehenden Entscheidungen",
    "Older events": "Ältere Ereignisse",
    "One conversation across your business.": "Ein Gespräch für dein ganzes Unternehmen.",
    "Open a case to understand the position and its supporting records.":
      "Öffne einen Vorgang, um den Stand und seine Nachweise zu verstehen.",
    "Open existing workspace": "Bestehenden Arbeitsbereich öffnen",
    "Open practice company": "Übungsunternehmen öffnen",
    "Original source": "Originalquelle",
    "Pending decisions": "Ausstehende Entscheidungen",
    "Review decisions": "Entscheidungen prüfen",
    "Review commitments": "Commitments prüfen",
    "Review each proposed change before it is recorded.":
      "Prüfe jede vorgeschlagene Änderung, bevor sie erfasst wird.",
    "Review proposed changes": "Vorgeschlagene Änderungen prüfen",
    Sandbox: "Testumgebung",
    "Thinking…": "Wird bearbeitet …",
    "Unknown party": "Unbekannter Geschäftspartner",
    "What would you like to understand or do?": "Was möchtest du verstehen oder tun?",
    "Your business, in focus.": "Dein Unternehmen im Blick.",
    "Your open work": "Deine offenen Aufgaben",
    "Your work": "Deine Arbeit",
    "Live simulation": "Live-Simulation",
    "New orders": "Neue Aufträge",
    "New reservations": "Neue Reservierungen",
    "Stock movements": "Warenbewegungen",
    "Other documents": "Weitere Belege",
    "Recorded business activity": "Erfasste Geschäftsvorgänge",
    "minutes per bar": "Minuten pro Balken",
    "Activity over time": "Aktivität im Zeitverlauf",
    "Recorded activities": "erfasste Vorgänge",
    "Time range": "Zeitraum",
    "Hover or select a bar to explore what happened.":
      "Zeige auf einen Balken oder wähle ihn aus, um die Vorgänge zu sehen.",
    "Hatched areas have no observed data. The latest bar is still filling.":
      "Schraffierte Bereiche haben keine erfassten Daten. Der neueste Balken ist noch unvollständig.",
    "Counts new orders, reservations, stock movements and other documents. Technical processing steps are excluded.":
      "Zählt neue Aufträge, Reservierungen, Warenbewegungen und weitere Belege. Technische Verarbeitungsschritte werden nicht mitgezählt.",
    "Activity in this interval": "Vorgänge in diesem Zeitabschnitt",
    "No recorded activity in this interval.": "Keine erfassten Vorgänge in diesem Zeitabschnitt.",
    "Showing the latest 50 matching events. Use all activity for more history.":
      "Die letzten 50 passenden Ereignisse. Weitere findest du unter allen Aktivitäten.",
    "Your company, in motion": "Deine Firma in Bewegung",
    "Recorded activity · updates every 10 seconds":
      "Erfasste Aktivitäten · Aktualisierung alle 10 Sekunden",
    "View all activity": "Alle Aktivitäten anzeigen",
    "Updates paused. Showing the last available activity.":
      "Aktualisierung unterbrochen. Die zuletzt verfügbaren Aktivitäten bleiben sichtbar.",
    "Activity is currently unavailable. We will retry automatically.":
      "Aktivitäten sind gerade nicht verfügbar. Wir versuchen es automatisch erneut.",
    "No activity yet. New records will appear here.":
      "Noch keine Aktivitäten. Neue Einträge erscheinen hier.",
    "System status": "Betriebsstatus",
    "Everything is ready": "Alles ist bereit",
    "Availability is not fully confirmed": "Verfügbarkeit nicht vollständig bestätigt",
    Connection: "Verbindung",
    "Automatic scheduling": "Zeitsteuerung",
    "Background processing": "Hintergrundverarbeitung",
    "Shows service availability. Individual imports and actions have their own results.":
      "Zeigt die Verfügbarkeit der Dienste. Einzelne Importe und Aktionen haben eigene Ergebnisse.",
    "Not yet verified": "Noch nicht geprüft",
    "Currently unavailable": "Gerade nicht verfügbar",
    "Checking…": "Wird geprüft…",
    "Recent activity": "Letzte Aktivitäten",
    Updated: "Aktualisiert",
    Ready: "Bereit",
    "Company created": "Firma angelegt",
    "Company created. Opening your company…": "Firma angelegt. Deine Firma wird geöffnet…",
    "Retry opening": "Öffnen erneut versuchen",

    "Company name (required)": "Firmenname (Pflichtfeld)",
    "Choose a name for this company or Sandbox so you can find it later.":
      "Gib dieser Firma oder Sandbox einen Namen, damit du sie später wiederfindest.",
    "Enter a company name to continue.": "Bitte gib einen Firmennamen ein, um fortzufahren.",

    "Start your own company": "Eigene Firma starten",
    "Start empty and add your own data or integrations.":
      "Leer beginnen und eigene Daten oder Integrationen hinzufügen.",
    "Create an empty Sandbox": "Leere Sandbox erstellen",
    "Experiment without preset data in a clearly labelled test environment.":
      "Ohne vorgegebene Daten in einer klar gekennzeichneten Testumgebung experimentieren.",
    "Try demo data": "Mit Demodaten ausprobieren",
    "Explore international products, warehouses, customers and twelve weeks of order history in a Sandbox.":
      "Internationale Produkte, Lager, Kunden und zwölf Wochen Auftragshistorie in einer Sandbox erkunden.",
    "How would you like to start?": "Wie möchtest du starten?",
    "Enable live simulation": "Live-Simulation aktivieren",
    "Receive 60 new demo orders per hour. The demo integration is set up automatically. You can pause it anytime.":
      "Pro Stunde 60 neue Demoaufträge erhalten. Die Demo-Integration wird automatisch eingerichtet und kann jederzeit pausiert werden.",

    "Automatically connect Demo Data and start 60 orders per hour when this company is created. You can pause it anytime in Integrations.":
      "Demodaten werden beim Anlegen automatisch verbunden und mit 60 Aufträgen pro Stunde gestartet. Du kannst die Simulation jederzeit unter Integrationen pausieren.",
    "Manage live simulation": "Live-Simulation verwalten",
    "Receive ongoing demo orders": "Laufend Demoaufträge empfangen",
    "Original source and interpretation": "Originalquelle und Interpretation",
    "Receive synthetic orders through the background worker. Connecting does not start arrivals.":
      "Erhalte automatisch synthetische Aufträge. Nach dem Verbinden musst du den Eingang ausdrücklich starten.",
    "Demo profile and practice cases": "Demoprofil und Übungsfälle",
    "Comparison periods": "Vergleichszeiträume",
    "Amounts are booked gross values by currency. Costs and promotions are not provided.":
      "Beträge sind gebuchte Bruttowerte je Währung. Kosten und Promotions sind nicht hinterlegt.",
    "Create a separate company with one reservable unit and a blocked case. No reservation is executed during setup.":
      "Lege eine separate Firma mit einer reservierbaren Einheit und einem gesperrten Fall an. Die Einrichtung führt keine Reservierung aus.",
    "Create reservation practice": "Reservierungsübung anlegen",
    "Starting data": "Startdaten",
    "Empty company": "Leere Firma",
    "Start without products, orders or opening stock.":
      "Ohne Artikel, Aufträge oder Anfangsbestand starten.",
    "International demo company": "Internationale Demofirma",
    "16 products, two warehouses, operational cases and twelve weeks of synthetic history. Created as a Sandbox.":
      "16 Artikel, zwei Lager, operative Fälle und zwölf Wochen synthetische Historie. Wird als Sandbox angelegt.",
    "Company environment": "Firmenumgebung",
    "Ordinary company": "Normale Firma",
    "An empty Sandbox contains no demo records. Its practice environment stays clearly labelled.":
      "Eine leere Sandbox enthält keine Demodaten. Die Testumgebung bleibt klar gekennzeichnet.",
    "Your access request has not created a company. Choose how this company should start.":
      "Deine Zugangsanfrage hat noch keine Firma angelegt. Wähle jetzt, wie diese Firma starten soll.",
    "Choose how this company should start.": "Wähle, wie diese Firma starten soll.",
    "Company details and order volume describe your access request. They do not create a company.":
      "Firmenangaben und Auftragsvolumen beschreiben deine Zugangsanfrage. Dadurch wird noch keine Firma angelegt.",
    "Company setup could not be loaded. Reload to retry.":
      "Die Firmeneinrichtung konnte nicht geladen werden. Lade die Seite erneut.",
    "Creation could not be confirmed. Retry the same request to recover safely.":
      "Die Anlage konnte nicht bestätigt werden. Wiederhole dieselbe Anfrage, um den Stand sicher wiederherzustellen.",
    "Keep this request while setup is pending. Retrying will not create another company.":
      "Behalte diese Anfrage, solange die Einrichtung läuft. Erneutes Versuchen legt keine weitere Firma an.",
    "Retry company setup": "Firmeneinrichtung erneut versuchen",
    "New demo orders arrive automatically.": "Neue Demoaufträge gehen automatisch ein.",
    "New arrivals are paused. Existing orders remain available.":
      "Neue Eingänge sind pausiert. Vorhandene Aufträge bleiben verfügbar.",
    "Explore your business with synthetic orders.":
      "Erkunde dein Unternehmen mit synthetischen Aufträgen.",
    "Live updates are unavailable. Showing the last known information.":
      "Live-Aktualisierungen sind nicht verfügbar. Die zuletzt bekannten Informationen werden angezeigt.",
    "Imported orders": "Importierte Aufträge",
    "Next scheduled arrival": "Nächster geplanter Eingang",
    "Latest 25 demo orders. Updates automatically while this page is visible.":
      "Die letzten 25 Demoaufträge. Wird automatisch aktualisiert, solange diese Seite sichtbar ist.",
    "Last checked": "Zuletzt geprüft",
    "Waiting for the first demo order.": "Warten auf den ersten Demoauftrag.",
    "Demo order imported": "Demoauftrag importiert",
    "Demo import failed": "Demoimport fehlgeschlagen",
    "Demo import pending": "Demoimport ausstehend",
    Apply: "Übernehmen",
    Loading: "Wird geladen",
    "More options": "Weitere Optionen",
    "Demo Data": "Demodaten",
    "Demo Data is available in compatible practice companies.":
      "Demodaten sind in passenden Übungsfirmen verfügbar.",
    "Receive synthetic orders automatically. Connecting does not start arrivals.":
      "Erhalte automatisch synthetische Aufträge. Nach dem Verbinden musst du den Eingang ausdrücklich starten.",
    "Review demo connection": "Demoverbindung prüfen",
    "Only the following missing references will be added. No stock or history is created.":
      "Nur die folgenden fehlenden Stammdaten werden ergänzt. Es entstehen keine Bestände oder historischen Vorgänge.",
    "Confirm connection": "Verbindung bestätigen",
    "Confirm Demo Data change": "Änderung der Demoquelle bestätigen",
    "Confirm import retry": "Import erneut versuchen bestätigen",
    "Generated orders": "Erzeugte Aufträge",
    "Order to cash": "Auftrag bis Zahlung",
    "Invoices issued": "Gestellte Rechnungen",
    "Payments received": "Erhaltene Zahlungen",
    "Payments allocated": "Zugeordnete Zahlungen",
    "Invoices settled": "Ausgeglichene Rechnungen",
    "Open residuals": "Offene Reste",
    "Customer credit created": "Entstandenes Kundenguthaben",
    "Unmatched payments": "Nicht zugeordnete Zahlungen",
    "Settlement failures": "Fehlgeschlagene Buchungen",
    "Next settlement": "Nächste Buchung",
    "Last settlement": "Letzte Buchung",
    "Open payments": "Zahlungen öffnen",
    "Open open items": "Offene Posten öffnen",
    "Open journal": "Journal öffnen",
    "Differences wait for your decision in Payments.":
      "Abweichungen warten in Zahlungen auf deine Entscheidung.",
    "Suggested invoices": "Vorgeschlagene Rechnungen",
    suggested: "vorgeschlagen",
    "Amount equals the open amount": "Betrag entspricht dem offenen Betrag",
    "Invoice number appears in the remittance text": "Rechnungsnummer steht im Verwendungszweck",
    "Stated reference names this invoice among others":
      "Genannter Bezug nennt diese Rechnung neben anderen",
    Imported: "Importiert",
    "Next arrival": "Nächster Eingang",
    "Last successful import": "Letzter erfolgreicher Import",
    "Orders per hour": "Aufträge pro Stunde",
    "Refresh status": "Status aktualisieren",
    "Recent demo imports": "Letzte Demoimporte",
    "Next page": "Nächste Seite",
    "Open order": "Auftrag öffnen",
    "The change could not be confirmed. Refresh the status before retrying.":
      "Die Änderung konnte nicht bestätigt werden. Aktualisiere vor einem erneuten Versuch den Status.",
    "Sandbox — practice environment": "Sandbox — Testumgebung",
    Start: "Starten",
    "Start simulation": "Simulation starten",
    Pause: "Pausieren",
    Resume: "Fortsetzen",
    Stop: "Stoppen",
    Disconnect: "Trennen",
    Reconnect: "Erneut verbinden",
    "Change rate": "Rate ändern",
    Stopped: "Gestoppt",
    Running: "Läuft",
    Paused: "Pausiert",
    Disconnected: "Getrennt",
    "Paused: resolve failed imports": "Pausiert: fehlerhafte Importe klären",
    "Execution needs attention": "Ausführung prüfen",
    "Not connected": "Nicht verbunden",
    completed: "abgeschlossen",
    failed: "fehlgeschlagen",
    pending: "ausstehend",
    Invoices: "Rechnungen",
    Warehouse: "Lager",
    "Customer order recorded": "Kundenauftrag erfasst",
    "Purchase order recorded": "Bestellung erfasst",
    "Customer invoice recorded": "Kundenrechnung erfasst",
    "Supplier invoice recorded": "Lieferantenrechnung erfasst",
    "Customer credit recorded": "Kundengutschrift erfasst",
    "Supplier credit recorded": "Lieferantengutschrift erfasst",
    "Customer return received": "Kundenretoure empfangen",
    "Stock adjusted": "Bestand korrigiert",
    "Delivery promise recorded": "Lieferzusage erfasst",
    "Delivery promise fulfilled": "Lieferzusage erfüllt",
    "Delivery promise updated": "Lieferzusage geändert",
    "Reservation released": "Reservierung freigegeben",
    "Reserved stock used": "Reservierte Ware verwendet",
    "Goods movement recorded": "Warenbewegung erfasst",
    "Business data received": "Geschäftsdaten empfangen",
    "Business data processed": "Geschäftsdaten verarbeitet",
    "Business change recorded": "Geschäftliche Änderung erfasst",
    "Business context": "Geschäftlicher Zusammenhang",
    "Current recorded position": "Aktueller Stand",
    "Business area": "Geschäftsbereich",
    "Customer orders": "Kundenaufträge",
    "Purchase orders": "Bestellungen",
    "Delivery movements": "Lieferbewegungen",
    "What happened?": "Was ist passiert?",
    "Counts of recorded orders, shipment/receipt movements and invoices in this sandbox, independent of filters. Movements are not unique deliveries.":
      "Anzahl erfasster Aufträge, Bestellungen, Warenein-/ausgänge und Rechnungen dieser Sandbox, unabhängig von Filtern. Bewegungen sind nicht gleich einzelne Lieferungen.",
    "Data overview": "Datenübersicht",
    "Business commitments": "Verpflichtungen",
    "Goods movements": "Warenbewegungen",
    "Totals scope": "Umfang der Kennzahlen",
    "Totals for this sandbox, independent of search and filters.":
      "Gesamtzahlen dieser Sandbox, unabhängig von Suche und Filtern.",
    "About transaction groups": "Über die Vorgangsgruppen",
    "Groups contain loaded matching events linked by source or correlation, not necessarily the entire order.":
      "Gruppen zeigen geladene Treffer mit gemeinsamer Quelle oder Korrelation, nicht zwingend den gesamten Auftrag.",
    "Search open items": "Offene Posten suchen …",
    "Search deliveries": "Lieferungen suchen …",
    "Reserve stock for customer orders": "Ware für Kundenaufträge reservieren",
    "Review overdue customer deliveries": "Überfällige Kundenlieferungen prüfen",
    "Follow up supplier deliveries": "Lieferantenlieferungen nachverfolgen",
    "Review invoicing for shipped goods": "Abrechnung versendeter Ware prüfen",
    "Review stock reservations": "Bestandsreservierungen prüfen",
    "Follow up customer payments": "Kundenzahlungen nachverfolgen",
    "Review supplier payments": "Lieferantenzahlungen prüfen",
    "Review credit for returned goods": "Gutschrift für retournierte Ware prüfen",
    "Context unavailable": "Geschäftsdaten nicht verfügbar",
    "Not reserved": "Noch nicht reserviert",
    "Review record": "Datensatz prüfen",
    "Open notices": "Offene Hinweise",
    "Back to cockpit": "Zurück zum Cockpit",
    "Expand chat": "Chat vergrößern",
    Table: "Tabelle",
    "Sandbox companion": "Sandbox-Begleiter",
    "Read only": "Nur lesen",
    "Understand your sandbox, one question at a time.":
      "Verstehe deine Sandbox – eine Frage nach der anderen.",
    "Checking your sandbox…": "Ich prüfe deine Sandbox …",
    "What needs attention in this sandbox?": "Was braucht in dieser Sandbox meine Aufmerksamkeit?",
    "How has my stock changed?": "Wie hat sich mein Bestand verändert?",
    "What do we still need to deliver or receive?": "Was müssen wir noch liefern oder empfangen?",
    "Which invoices are still unpaid?": "Welche Rechnungen sind noch offen?",
    "Which business partners and items are available?":
      "Welche Geschäftspartner und Artikel sind angelegt?",
    "Explain the latest recorded change.": "Erkläre die zuletzt erfasste Änderung.",
    "How do Source, Evidence and Reality connect?":
      "Wie hängen Source, Evidence und Reality zusammen?",
    "More questions": "Weitere Fragen",
    "Show less": "Weniger anzeigen",
    "All exceptions": "Alle Ausnahmen",
    You: "Du",
    "Ask about your sandbox": "Frage zu deiner Sandbox …",
    "Send question": "Frage senden",
    "Uses the managed AI. No bookings or changes.":
      "Mit verwalteter KI. Keine Buchungen oder Änderungen.",
    "The assistant is unavailable. Your question is kept; please try again.":
      "Die KI ist gerade nicht verfügbar. Deine Frage bleibt erhalten – bitte erneut versuchen.",
    "Individual operations": "Einzelne Vorgänge",
    "More operations": "Weitere Vorgänge",
    "Open in App": "In der App öffnen",
    "Guided examples": "Geführte Beispiele",
    "Free operations": "Freie Vorgänge",
    "Open work": "Offene Aufträge",
    "Create customer order only": "Nur Kundenauftrag anlegen",
    "Create supplier order only": "Nur Bestellung anlegen",
    "Create orders now. Reserve, ship or receive them later in Open work.":
      "Lege Aufträge an. Unter Offene Aufträge kannst du sie später reservieren, liefern oder empfangen.",
    "Open work could not be loaded.": "Offene Aufträge konnten nicht geladen werden.",
    "Business partners": "Geschäftspartner",
    "Financial posting recorded": "Finanzbuchung erfasst",
    "Payment allocated": "Zahlung zugeordnet",
    "Record invoice": "Rechnung erfassen",
    "Record and allocate payment": "Zahlung erfassen und zuordnen",
    "Record the invoice total as stated. This creates a receivable, not a payment.":
      "Erfasse den angegebenen Rechnungsbetrag. Daraus entsteht eine Forderung, noch keine Zahlung.",
    "Record the received payment and allocate it to this invoice. The open amount decreases.":
      "Erfasse den Zahlungseingang und ordne ihn dieser Rechnung zu. Der offene Betrag sinkt.",
    "Stated invoice total": "Angegebener Rechnungsbetrag",
    "Payment amount": "Zahlungsbetrag",
    "Payment recorded": "Zahlung erfasst",
    "Start another operation": "Weiteren Vorgang starten",
    "Same sandbox. Existing stock, obligations and history are preserved.":
      "Gleiche Sandbox. Bestand, Verpflichtungen und Verlauf bleiben erhalten.",
    "Another customer order": "Weiterer Kundenauftrag",
    "Record additional opening stock": "Zusätzlichen Anfangsbestand erfassen",
    "Purchasing and returns are not available yet.":
      "Einkauf und Retouren sind noch nicht verfügbar.",
    "Start a fresh sandbox": "Neue Sandbox starten",
    "Choose your next operation": "Nächsten Vorgang auswählen",
    "Business operations": "Vorgänge",
    "Choose what to try. Everything stays in this sandbox.":
      "Was möchtest du ausprobieren? Alles bleibt in dieser Sandbox.",
    "Record opening stock": "Anfangsbestand erfassen",
    "Record existing goods, then choose your next operation.":
      "Vorhandene Ware erfassen. Danach wählst du den nächsten Vorgang.",
    "Sell from stock": "Verkauf aus Bestand",
    "Customer order, reservation and delivery. Use the stock already available.":
      "Kundenauftrag, Reservierung und Lieferung – mit vorhandenem Bestand.",
    "Purchase order and goods receipt, including partial deliveries.":
      "Bestellung und Wareneingang – auch in Teillieferungen.",
    "More scenarios — coming later": "Weitere Szenarien – folgen noch",
    "Choosing an operation changes nothing. Review and confirm each action separately.":
      "Die Auswahl ändert noch nichts. Jede Aktion wird einzeln geprüft und bestätigt.",
    "Supplier order": "Lieferantenbestellung",
    "Receive goods": "Wareneingang erfassen",
    "Record supplier invoice": "Lieferantenrechnung erfassen",
    "Available inside the sandbox": "Innerhalb der Sandbox auswählbar",
    "Customer return": "Kundenretoure",
    "Receive customer return": "Kundenretoure annehmen",
    "Record credit note": "Gutschrift erfassen",
    "Refund customer": "Kundenrückzahlung erfassen",
    "Original shipment": "Ursprüngliche Lieferung",
    "Stated credit total": "Angegebener Gutschriftbetrag",
    "Receive returned goods, record a credit note and refund the customer.":
      "Retoure annehmen, Gutschrift erfassen und dem Kunden Geld zurückzahlen.",
    "A customer return needs a recorded shipment first.":
      "Für eine Kundenretoure muss zuerst eine Lieferung erfasst sein.",
    "Receive goods from a recorded customer shipment. This changes stock, not money.":
      "Nimm Ware einer erfassten Kundenlieferung zurück. Das verändert den Bestand, nicht das Geld.",
    "Record the stated credit total for returned goods. No money moves yet.":
      "Erfasse den angegebenen Gutschriftbetrag für zurückgenommene Ware. Es fließt noch kein Geld.",
    "Record the refund and allocate it to the credit note. The credit balance decreases.":
      "Erfasse die Rückzahlung und ordne sie der Gutschrift zu. Der offene Gutschriftbetrag sinkt.",
    "Record supplier payment": "Lieferantenzahlung erfassen",
    "Purchase order, goods receipt, supplier invoice and payment.":
      "Bestellung, Wareneingang, Lieferantenrechnung und Zahlung.",
    "Record the supplier's stated invoice total. This creates a payable; stock stays unchanged.":
      "Erfasse den Rechnungsbetrag des Lieferanten. Es entsteht eine Verbindlichkeit; der Bestand bleibt unverändert.",
    "Record your payment to the supplier and allocate it to this invoice. The payable decreases.":
      "Erfasse deine Zahlung an den Lieferanten und ordne sie dieser Rechnung zu. Die offene Verbindlichkeit sinkt.",
    "Customer returns are being prepared.": "Kundenretouren werden noch vorbereitet.",
    "Goods received": "Ware eingegangen",
    "Order from a supplier": "Beim Lieferanten bestellen",
    "Order goods from a supplier. This creates an incoming goods obligation, not stock or a payable.":
      "Bestelle Ware beim Lieferanten. Er schuldet dir dann Ware – Bestand und Geldverbindlichkeiten entstehen dadurch noch nicht.",
    "Record goods actually received. Stock increases and the supplier's remaining obligation decreases.":
      "Erfasse die tatsächlich eingegangene Ware. Der Bestand steigt und die offene Lieferverpflichtung sinkt.",
    "Supplier invoices, supplier payments and returns are not available yet.":
      "Lieferantenrechnungen, Lieferantenzahlungen und Retouren folgen noch.",
    "Stock → order → reservation → shipment → invoice → payment":
      "Bestand → Auftrag → Reservierung → Versand → Rechnung → Zahlung",
    Sales: "Verkauf",
    Purchasing: "Einkauf",
    Accounting: "Buchhaltung",
    "Choose a scenario": "Szenario auswählen",
    "New sandbox": "Neue Sandbox",
    "Your sandboxes": "Deine Sandboxes",
    "Saved sandboxes": "Gespeicherte Sandboxes",
    "Start a new sandbox or continue in an existing one.":
      "Starte eine neue Sandbox oder mache in einer bestehenden weiter.",
    "Choose your operations inside the sandbox. All changes stay in one timeline.":
      "Die Vorgänge wählst du in der Sandbox. Alle Änderungen bleiben in einer Timeline.",
    "Show fewer sandboxes": "Weniger Sandboxes anzeigen",
    "Show more sandboxes": "Weitere Sandboxes anzeigen",
    "Back to current run": "Zurück zum aktuellen Versuch",
    "One business story. Your actions on the left, their effect in Reality on the right.":
      "Ein Geschäftsfall. Links handelst du, rechts siehst du die Wirkung in Reality.",
    "Try this scenario": "Jetzt ausprobieren",
    "Not available yet": "Noch nicht verfügbar",
    "Sell, deliver and get paid": "Verkaufen, liefern, bezahlt werden",
    "From a customer promise to goods leaving the warehouse.":
      "Vom Kundenauftrag bis zum Warenausgang.",
    "Available through delivery. Invoice and payment follow later.":
      "Bis zur Lieferung verfügbar. Rechnung und Zahlung folgen später.",
    "Deliver part of an order": "Einen Auftrag teilweise liefern",
    "Promise twelve, ship five. See the remaining goods obligation.":
      "Zwölf zusagen, fünf liefern. Verstehe, welche Ware du noch schuldest.",
    "Opening stock → order → reservation → partial shipment":
      "Anfangsbestand → Auftrag → Reservierung → Teillieferung",
    "A customer returns goods": "Ein Kunde schickt Ware zurück",
    "Receive the return, record a credit note and refund the customer.":
      "Retoure empfangen, Gutschrift erfassen und Geld zurückzahlen.",
    "Buy, receive and pay": "Bestellen, empfangen, bezahlen",
    "Order from a supplier, receive goods and settle the invoice.":
      "Beim Lieferanten bestellen, Ware empfangen und Rechnung bezahlen.",
    "A supplier delivers in parts": "Ein Lieferant liefert in Teilen",
    "Receive part of a purchase and see what the supplier still owes.":
      "Teillieferung empfangen und sehen, was der Lieferant noch schuldet.",
    "Record and pay an expense": "Eine Ausgabe erfassen und bezahlen",
    "Follow a simple expense from the original receipt to payment.":
      "Eine einfache Ausgabe vom Originalbeleg bis zur Zahlung verfolgen.",
    "Correct an incorrect posting": "Eine falsche Buchung korrigieren",
    "Reverse a posting and record its replacement. Preserve the evidence.":
      "Buchung stornieren und neu erfassen. Der Verlauf bleibt nachvollziehbar.",
    "Your current run will be archived and remain readable. A new private example starts only after confirmation.":
      "Dein aktueller Versuch wird archiviert und bleibt lesbar. Erst nach Bestätigung startet ein neues privates Beispiel.",
    "Starting a scenario is currently unavailable. Your saved runs remain readable.":
      "Ein neues Szenario kann gerade nicht gestartet werden. Gespeicherte Versuche bleiben lesbar.",
    "Delivery:": "Zustellung:",
    "Retry delivery": "Zustellung wiederholen",
    "Accept invitation": "Einladung annehmen",
    "Checking invitation…": "Einladung wird geprüft…",
    "Invited as": "Eingeladen als",
    "Join this company": "Diesem Unternehmen beitreten",
    "One moment while we check your invitation link.":
      "Einen Moment, wir prüfen deinen Einladungslink.",
    "This invitation is no longer valid. Ask a company owner to send you a new one.":
      "Diese Einladung ist nicht mehr gültig. Frag eine Inhaberin oder einen Inhaber des Unternehmens nach einer neuen.",
    "Your invitation is bound to this address.": "Deine Einladung ist an diese Adresse gebunden.",
    "Cancel invitation": "Einladung abbrechen",
    "Company invitation": "Unternehmenseinladung",
    "Confirm that you want to join this company.":
      "Bestätige, dass du diesem Unternehmen beitreten möchtest.",
    "Invitation unavailable": "Einladung nicht verfügbar",
    "Sign in or create an account with the invited email. Membership is granted only after you accept.":
      "Melde dich mit der eingeladenen E-Mail-Adresse an oder erstelle ein Konto. Die Mitgliedschaft entsteht erst nach deiner Bestätigung.",
    "Active members": "Aktive Mitglieder",
    Invitations: "Einladungen",
    "Invite a member": "Mitglied einladen",
    "Invite member": "Mitglied einladen",
    "They receive a secure link and join only after explicitly accepting.":
      "Die Person erhält einen sicheren Link und tritt erst nach ausdrücklicher Bestätigung bei.",
    "name@company.com": "name@unternehmen.de",
    "Internal Copilot": "Interner Copilot",
    "Managed by Reality": "Von Reality verwaltet",
    "Reality-managed": "Von Reality verwaltet",
    "Reality-managed is included. Other providers use your own account.":
      "Reality-managed ist enthalten. Andere Anbieter verwenden dein eigenes Konto.",
    "Reality-managed works immediately. You can instead connect a provider account owned by this company.":
      "Reality-managed funktioniert sofort. Alternativ kannst du ein Anbieterkonto dieses Unternehmens verbinden.",
    "Use own Anthropic key": "Eigenen Anthropic-Schlüssel verwenden",
    "Use the included server credential.": "Die enthaltenen Server-Zugangsdaten verwenden.",
    "Usage is billed directly to your Anthropic account.":
      "Die Nutzung wird direkt über dein Anthropic-Konto abgerechnet.",
    "Anthropic API key": "Anthropic-API-Schlüssel",
    "Enter Anthropic API key": "Anthropic-API-Schlüssel eingeben",
    "Anthropic and the economical Claude model are selected centrally. Choose who provides the API credential for this company.":
      "Anthropic und das kostengünstige Claude-Modell sind zentral ausgewählt. Lege fest, wer die API-Zugangsdaten für dieses Unternehmen bereitstellt.",
    "Copilot available": "Copilot verfügbar",
    "Copilot not configured": "Copilot nicht konfiguriert",
    "Reality is preparing an answer": "Reality bereitet eine Antwort vor",
    "The AI provider and model are operated centrally. Company data remains tenant-scoped, and Copilot can only use registered read and proposal tools.":
      "KI-Anbieter und Modell werden zentral betrieben. Unternehmensdaten bleiben mandantenbezogen, und Copilot kann nur registrierte Lese- und Vorschlagswerkzeuge verwenden.",
    "Inviting…": "Einladung wird gesendet…",
    "Loading members…": "Mitglieder werden geladen…",
    "Manage access for this company. Only owners can invite or remove members.":
      "Verwalte den Zugriff auf dieses Unternehmen. Nur Eigentümer können Mitglieder einladen oder entfernen.",
    Members: "Mitglieder",
    "No active members.": "Keine aktiven Mitglieder.",
    "No invitations.": "Keine Einladungen.",
    Remove: "Entfernen",
    Resend: "Erneut senden",
    All: "Alle",
    "Close activity": "Aktivität schließen",
    "Load older activity": "Ältere Aktivitäten laden",
    "New business events will appear here.": "Neue Business Events erscheinen hier.",
    "Open activity": "Aktivität öffnen",
    "Operational core": "Operational Core",
    "Reality activity": "Reality-Aktivität",
    "Tenant-scoped operational and financial events.":
      "Unternehmensbezogene operative und finanzielle Ereignisse.",
    "What happened": "Was ist passiert?",
    "€18,400": "18.400 €",
    "Company Overview": "Unternehmensübersicht",
    "Company-wide control": "Unternehmensweite Steuerung",
    "Order Operations": "Auftragssteuerung",
    "Orders, promises & execution": "Aufträge, Commitments & Ausführung",
    "Warehouse Operations": "Lagersteuerung",
    "Inventory & fulfilment": "Bestand & Fulfilment",
    "Finance Control": "Finanzsteuerung",
    "Position & reconciliation": "Position & Abstimmung",
    "Data Management": "Datenverwaltung",
    "Registers & maintenance": "Register & Pflege",
    "My area": "Mein Bereich",
    Views: "Ansichten",
    "Workspace navigation unavailable": "Bereichsnavigation nicht verfügbar",
    "Review action": "Aktion prüfen",
    "Confirm action": "Aktion bestätigen",
    "Reserve stock": "Bestand reservieren",
    "Record movement": "Bewegung erfassen",
    "Correct movement": "Bewegung korrigieren",
    "Hold or release commitment": "Commitment sperren oder freigeben",
    "Hold or release document commitments": "Dokument-Commitments sperren oder freigeben",
    "Set or release party delivery hold": "Lieferstopp für Partei setzen oder aufheben",
    "More actions": "Mehr Aktionen",
    "All actions": "Alle Aktionen",
    "Search actions": "Aktionen suchen",
    "No actions found": "Keine Aktionen gefunden",
    "More views": "Mehr Ansichten",
    "All views": "Alle Ansichten",
    "Search views": "Ansichten suchen",
    "No views found": "Keine Ansichten gefunden",
    "Warehouse Queue": "Lagerwarteschlange",
    "Supply & demand": "Angebot & Bedarf",
    "Search this view…": "Diese Ansicht durchsuchen…",
    "View unavailable": "Ansicht nicht verfügbar",
    "No projection rows yet": "Noch keine Daten für diese Ansicht",
    "This view will populate when matching business Reality exists.":
      "Diese Ansicht wird gefüllt, sobald passende Business Reality vorliegt.",
    "Change or clear your search.": "Ändere oder lösche deine Suche.",
    "No results found": "Keine Ergebnisse gefunden",
    Pagination: "Seitennavigation",
    Previous: "Zurück",
    Page: "Seite",
    Next: "Weiter",
    results: "Ergebnisse",
    "Order & Warehouse Operations": "Auftrags- & Lagersteuerung",
    "Customer orders with readiness, due dates and execution blockers":
      "Kundenaufträge mit Bereitschaft, Fälligkeit und Ausführungsblockern",
    "Orders prioritized for warehouse execution and shipment readiness":
      "Für Lagerausführung und Versandbereitschaft priorisierte Aufträge",
    "Commitment shortages and active execution holds blocking fulfillment":
      "Fehlmengen und aktive Ausführungssperren, die Fulfilment blockieren",
    "Item-level physical stock, incoming supply and uncovered customer demand":
      "Physischer Bestand, Zugänge und ungedeckter Kundenbedarf je Artikel",
    "Customer orders with readiness, due dates and the blockers that explain execution.":
      "Kundenaufträge mit Bereitschaft, Fälligkeit und erklärenden Ausführungsblockern.",
    "Orders prioritized for warehouse execution with shipment readiness explained.":
      "Für die Lagerausführung priorisierte Aufträge mit erklärter Versandbereitschaft.",
    "Shortages and active execution holds that currently block fulfillment.":
      "Fehlmengen und aktive Ausführungssperren, die Fulfilment derzeit blockieren.",
    "Physical stock, incoming supply and uncovered customer demand by item.":
      "Physischer Bestand, Zugänge und ungedeckter Kundenbedarf je Artikel.",
    "Create manual sales or purchase order": "Verkaufs- oder Einkaufsbestellung manuell anlegen",
    "Observe source-supported fact": "Quellengestützten Fakt erfassen",
    "Post customer payment": "Kundenzahlung buchen",
    "Post supplier payment": "Lieferantenzahlung buchen",
    "Order lines": "Bestellpositionen",
    Line: "Position",
    "Add line": "Position hinzufügen",
    "Remove line": "Position entfernen",
    "Unit price": "Einzelpreis",
    "Promised at": "Zugesagt am",
    "Create handling unit": "Handling Unit anlegen",
    "Create lot": "Charge anlegen",
    "Create serial unit": "Serieneinheit anlegen",
    Hold: "Sperren",
    Release: "Freigeben",
    "Ask Reality": "Reality fragen",
    Home: "Start",
    Exceptions: "Abweichungen",
    "Company-wide": "Unternehmensweit",
    "Order operations": "Auftragssteuerung",
    "Warehouse operations": "Lagersteuerung",
    "Finance control": "Finanzsteuerung",
    "Data management": "Datenverwaltung",
    Inventory: "Bestand",
    Documents: "Belege",
    Activity: "Aktivität",
    "new attention event": "neues Ereignis mit Handlungsbedarf",
    "new attention events": "neue Ereignisse mit Handlungsbedarf",
    "Open Activity to review": "Aktivität zur Prüfung öffnen",
    Payments: "Zahlungen",
    Parties: "Geschäftspartner",
    Items: "Artikel",
    Locations: "Lagerorte",
    Sources: "Quellen",
    "Open items": "Offene Posten",
    "Commercial terms": "Konditionen",
    "Profile & preferences": "Profil & Einstellungen",
    "Account settings": "Kontoeinstellungen",
    "Manage your personal identity and how Reality displays dates, times and numbers.":
      "Verwalte dein Profil und wie Reality Datum, Uhrzeit und Zahlen darstellt.",
    Account: "Konto",
    "Personal settings": "Persönliche Einstellungen",
    "Your profile": "Dein Profil",
    "These preferences apply only to your account, across every company you can access.":
      "Diese Einstellungen gelten nur für dein Konto – in allen Unternehmen, auf die du Zugriff hast.",
    Email: "E-Mail",
    "Your sign-in identity.": "Deine Identität für die Anmeldung.",
    Name: "Name",
    "Shown to other operators in decisions and activity.":
      "Wird anderen Operatoren bei Entscheidungen und Aktivitäten angezeigt.",
    Language: "Sprache",
    "Controls labels and interface text.": "Steuert Beschriftungen und Texte der Oberfläche.",
    "Number & date format": "Zahlen- & Datumsformat",
    "Controls decimals, dates and currency formatting.":
      "Steuert Dezimalzahlen, Datum und Währungsformat.",
    "Display timezone": "Anzeige-Zeitzone",
    "Business events remain stored in UTC and are converted for your interface.":
      "Business Events bleiben in UTC gespeichert und werden für deine Oberfläche umgerechnet.",
    "Preferences saved": "Einstellungen gespeichert",
    "Changes affect your account only.": "Änderungen gelten nur für dein Konto.",
    "Save preferences": "Einstellungen speichern",
    "Saving…": "Speichern…",
    "Backend unavailable": "Backend nicht verfügbar",
    "Needs attention": "Benötigt Aufmerksamkeit",
    Completed: "Abgeschlossen",
    "Technical details": "Technische Details",
    "Event type": "Ereignistyp",
    Subject: "Bezugsobjekt",
    Correlation: "Prozessbezug",
    "No activity yet": "Noch keine Aktivität",
    "1 event": "1 Ereignis",
    "No operational activity yet": "Noch keine operative Aktivität",
    "Last activity": "Letzte Aktivität",
    "Active company": "Aktives Unternehmen",
    Companies: "Unternehmen",
    "Help & documentation": "Hilfe & Dokumentation",
    Appearance: "Darstellung",
    "Applies immediately and is stored on this device.":
      "Wirkt sofort und wird auf diesem Gerät gespeichert.",
    Light: "Hell",
    Dark: "Dunkel",
    Resources: "Ressourcen",
    Documentation: "Dokumentation",
    "Reality website": "Reality-Website",
    "Sign out": "Abmelden",
    Search: "Suchen",
    Inspect: "Prüfen",
    View: "Öffnen",
    Active: "Aktiv",
    Inactive: "Inaktiv",
    Settings: "Einstellungen",
    General: "Allgemein",
    Data: "Daten",
    Agents: "Agenten",
    Company: "Unternehmen",
    "Company settings": "Unternehmenseinstellungen",
    "Company configuration": "Unternehmenskonfiguration",
    "Company & settings": "Unternehmen verwalten",
    Profile: "Profil",
    "New company": "Neues Unternehmen",
    Archive: "Archivieren",
    "Archive company": "Unternehmen archivieren",
    Archived: "Archiviert",
    "In use": "In Verwendung",
    "Current company": "Aktuelles Unternehmen",
    "Open company": "Unternehmen öffnen",
    "Restore company": "Unternehmen wiederherstellen",
    "Create your first company": "Erstes Unternehmen erstellen",
    "Create company": "Unternehmen erstellen",
    "Company name": "Unternehmensname",
    "Sources & intake": "Quellen & Eingang",
    Processing: "Verarbeitung",
    "Reference data": "Referenzdaten",
    Explorer: "Explorer",
    Copilot: "Copilot",
    "MCP server": "MCP-Server",
    "Company details": "Unternehmensdetails",
    "Default currency": "Standardwährung",
    Timezone: "Zeitzone",
    "Company ID": "Unternehmens-ID",
    Status: "Status",
    "Danger zone": "Gefahrenbereich",
    "Data / explorer": "Daten / Explorer",
    "Reality Explorer": "Reality Explorer",
    Collections: "Sammlungen",
    Record: "Datensatz",
    "Select a record": "Datensatz auswählen",
    "Nothing selected": "Nichts ausgewählt",
    "No records": "Keine Datensätze",
    "Sources & evidence": "Quellen & Evidence",
    Evidence: "Evidence",
    Events: "Events",
    Source: "Quelle",
    Type: "Typ",
    Records: "Datensätze",
    State: "Status",
    Received: "Empfangen",
    Version: "Version",
    "External ID": "Externe ID",
    System: "System",
    "Stable code": "Stabiler Code",
    "Source systems": "Quellsysteme",
    "Source capabilities": "Quellfunktionen",
    "Source registry": "Quellenregister",
    "Processing coverage": "Verarbeitungsumfang",
    "Immutable intake": "Unveränderlicher Eingang",
    "Recent source records": "Letzte SourceRecords",
    "Source type": "Quelltyp",
    "Payload value path": "Wertpfad im Payload",
    "Fact predicate": "Fact-Prädikat",
    "Fact value type": "Fact-Werttyp",
    "Allowed values, comma separated": "Zulässige Werte, kommagetrennt",
    String: "Text",
    Enum: "Auswahlliste",
    Boolean: "Ja/Nein",
    Decimal: "Dezimalzahl",
    Integer: "Ganzzahl",
    "Reality target": "Reality-Ziel",
    "Interpreter ready": "Interpreter bereit",
    "Raw only": "Nur Rohdaten",
    Accepted: "Akzeptiert",
    Disabled: "Deaktiviert",
    Activate: "Aktivieren",
    Deactivate: "Deaktivieren",
    "Test intake": "Eingang testen",
    "Add source": "Quelle hinzufügen",
    "Import jobs": "Import-Jobs",
    "Recent runs": "Letzte Läufe",
    Attempts: "Versuche",
    "Last error": "Letzter Fehler",
    "Read models": "Lesemodelle",
    Projections: "Projections",
    Projection: "Projection",
    Purpose: "Zweck",
    Rebuildable: "Wiederaufbaubar",
    "Business reference registers": "Geschäftliche Referenzregister",
    "Payment terms & pricing": "Zahlungsbedingungen & Preise",
    "Payment terms": "Zahlungsbedingungen",
    "Price lists": "Preislisten",
    "Pricing groups": "Preisgruppen",
    Add: "Hinzufügen",
    Edit: "Bearbeiten",
    Code: "Code",
    Due: "Fälligkeit",
    Scope: "Geltungsbereich",
    Default: "Standard",
    Actions: "Aktionen",
    "AI configuration": "KI-Konfiguration",
    Provider: "Anbieter",
    Model: "Modell",
    "API key": "API-Schlüssel",
    "External agents": "Externe Agenten",
    Endpoint: "Endpunkt",
    "Create token": "Token erstellen",
    Revoke: "Widerrufen",
    "No active MCP tokens.": "Keine aktiven MCP-Tokens.",
    "Save settings": "Einstellungen speichern",
    Timeline: "Timeline",
    "Live activity": "Live-Aktivität",
    "Operating machine": "Laufender Betrieb",
    "Activity over 24 hours": "Aktivität der letzten 24 Stunden",
    "Events today": "Events heute",
    "Orders processed": "Verarbeitete Aufträge",
    "Processing latency": "Verarbeitungslatenz",
    "Latest source": "Letzte Quelle",
    "All business areas": "Alle Geschäftsbereiche",
    "All states": "Alle Status",
    Operations: "Operations",
    Finance: "Finanzen",
    "24 hours": "24 Stunden",
    "7 days": "7 Tage",
    "30 days": "30 Tage",
    Now: "Jetzt",
    "Inventory control": "Bestandssteuerung",
    Physical: "Physisch",
    Reserved: "Reserviert",
    Available: "Verfügbar",
    Incoming: "Eingehend",
    Projected: "Prognostiziert",
    Shortage: "Fehlbestand",
    "Fully allocated": "Vollständig reserviert",
    Risk: "Risiko",
    "Due date": "Fälligkeitsdatum",
    Flow: "Richtung",
    Counterparty: "Geschäftspartner",
    Item: "Artikel",
    Promised: "Zugesagt",
    "At risk": "Gefährdet",
    Covered: "Gedeckt",
    Out: "Ausgehend",
    In: "Eingehend",
    Date: "Datum",
    Document: "Beleg",
    Party: "Geschäftspartner",
    "Gross amount": "Bruttobetrag",
    "Reality links": "Reality-Verknüpfungen",
    Invoice: "Rechnung",
    Gross: "Brutto",
    Settled: "Ausgeglichen",
    Open: "Offen",
    Direction: "Richtung",
    Reference: "Referenz",
    Amount: "Betrag",
    Total: "Summe",
    Allocated: "Zugeordnet",
    Unallocated: "Nicht zugeordnet",
    "Posting group": "Buchungsgruppe",
    Review: "Prüfen",
    Cancel: "Abbrechen",
    Confirm: "Bestätigen",
    Close: "Schließen",
    Delete: "Löschen",
    "No records match": "Keine passenden Datensätze",
    "No activity matches": "Keine passende Aktivität",
    "No inventory matches": "Keine passenden Bestände",
    "No commitments match": "Keine passenden Commitments",
    "No evidence matches": "Keine passende Evidence",
    "No open items match": "Keine passenden offenen Posten",
    "No payment events": "Keine Zahlungs-Events",
    "Could not load this view": "Diese Ansicht konnte nicht geladen werden",
    "Use the owning Reality correction workflow for economic line changes.":
      "Nutze für wirtschaftliche Zeilenänderungen den zuständigen Reality-Korrekturprozess.",
    "Opening Reality": "Reality wird geöffnet",
    "Workspace setup": "Arbeitsbereich einrichten",
    "Current operating mode": "Aktueller Betriebsmodus",
    "Reality is observing your business": "Reality beobachtet dein Unternehmen",
    "Read-only understanding is immediate. Business changes wait for an explicit approval until a person confirms them.":
      "Lesendes Verständnis ist sofort verfügbar. Änderungen am Geschäft warten auf eine ausdrückliche Freigabe, bis ein Mensch sie bestätigt.",
    "Start with observation": "Mit Beobachtung starten",
    "Connect one source. Verify what Reality learns.":
      "Verbinde eine Quelle. Prüfe, was Reality lernt.",
    "Your existing systems remain in place. Reality receives only the operational records you explicitly accept.":
      "Deine bestehenden Systeme bleiben bestehen. Reality empfängt nur operative Datensätze, die du ausdrücklich akzeptierst.",
    "Connect your first source": "Erste Quelle verbinden",
    "Connect a source": "Quelle verbinden",
    "Select exactly which upstream records Reality may receive.":
      "Lege exakt fest, welche Upstream-Datensätze Reality empfangen darf.",
    "Review observed facts": "Beobachtete Fakten prüfen",
    "Verify Reality's interpretation against immutable source evidence.":
      "Prüfe Realitys Interpretation anhand unveränderlicher Source Evidence.",
    "Monitor operations": "Betrieb beobachten",
    "Let Reality surface contradictions and explain their business impact.":
      "Lass Reality Widersprüche aufzeigen und ihre Geschäftsauswirkung erklären.",
    "Delegate one capability": "Eine Fähigkeit übergeben",
    "Move from observation to recommendations only when you trust the result.":
      "Wechsle erst von Beobachtung zu Empfehlungen, wenn du dem Ergebnis vertraust.",
    "Help & reference": "Hilfe & Referenz",
    "Run daily operations": "Tagesgeschäft steuern",
    "Trace an answer": "Antwort nachvollziehen",
    "Connect systems": "Systeme verbinden",
    "Open Home": "Start öffnen",
    "Open Explorer": "Explorer öffnen",
    "Open Integrations": "Integrationen öffnen",
    "Search order, source, SKU, party or ID…":
      "Auftrag, Quelle, SKU, Geschäftspartner oder ID suchen…",
    "Search ID, order number, SKU, party or source reference…":
      "ID, Auftragsnummer, SKU, Geschäftspartner oder Quellreferenz suchen…",
    "Search SKU or item…": "SKU oder Artikel suchen…",
    "Search or type a command…": "Suchen oder Befehl eingeben…",
    "A company contains its own sources, operational records and agent configuration.":
      "Ein Unternehmen enthält eigene Quellen, operative Datensätze und Agentenkonfigurationen.",
    "Create companies, inspect their operational footprint, or archive workspaces without losing data.":
      "Unternehmen erstellen, ihre operative Nutzung prüfen oder Arbeitsbereiche ohne Datenverlust archivieren.",
    "Identity and defaults used across this company workspace.":
      "Identität und Standardwerte für diesen Unternehmensbereich.",
    "Shown throughout Reality.": "Wird überall in Reality angezeigt.",
    "Used when a source does not supply one.":
      "Wird verwendet, wenn eine Quelle keine Währung liefert.",
    "Display timezone for operators.": "Anzeige-Zeitzone für Operatoren.",
    "Stable tenant identity for API calls.": "Stabile Tenant-Identität für API-Aufrufe.",
    "Current workspace lifecycle.": "Aktueller Lebenszyklus des Arbeitsbereichs.",
    "Archive before permanently deleting this company and its tenant-scoped records.":
      "Vor dem endgültigen Löschen des Unternehmens und seiner Tenant-Daten zuerst archivieren.",
    "Manage the typed identities and commercial rules Reality repeatedly uses.":
      "Typisierte Identitäten und Geschäftsregeln verwalten, die Reality wiederholt verwendet.",
    "Companies, customers and suppliers": "Unternehmen, Kunden und Lieferanten",
    "Products, services and charges": "Produkte, Leistungen und Gebühren",
    "Warehouses and stock locations": "Lager und Bestandsorte",
    "Due-date rules, price lists and pricing groups":
      "Fälligkeitsregeln, Preislisten und Preisgruppen",
    "Monitor source interpretation and the rebuildable read models used by the product.":
      "Interpretation von Quellen und die wiederaufbaubaren Lesemodelle des Produkts überwachen.",
    "Current tenant-scoped operational view": "Aktuelle operative Ansicht dieses Tenants",
    "No imports yet": "Noch keine Imports",
    "Runs appear after SourceRecords enter through an integration or test intake.":
      "Läufe erscheinen, sobald SourceRecords über eine Integration oder einen Testeingang eintreffen.",
    "Open one focused viewer for records, events or evidence.":
      "Datensätze, Events oder Evidence in einer fokussierten Ansicht öffnen.",
    "Search any ID and follow Source → Evidence → Reality.":
      "Beliebige ID suchen und Quelle → Evidence → Reality verfolgen.",
    "Review Business Events, processing history and exceptions.":
      "Business Events, Verarbeitungshistorie und Ausnahmen prüfen.",
    "Inspect documents and their shortest links into Reality.":
      "Belege und ihre kürzesten Verknüpfungen zu Reality prüfen.",
    "Search records, browse collections and inspect one object without losing context.":
      "Datensätze suchen, Sammlungen durchsuchen und ein Objekt im Kontext prüfen.",
    "Choose a record from the middle column.": "Wähle einen Datensatz in der mittleren Spalte.",
    "This collection has no matching records.":
      "Diese Sammlung enthält keine passenden Datensätze.",
    "Search a different business identity or clear the query.":
      "Suche nach einer anderen Geschäftsidentität oder leere die Suche.",
    "Connect external origins and test the same immutable intake used by integrations.":
      "Externe Quellen verbinden und denselben unveränderlichen Eingang testen, den Integrationen verwenden.",
    "Each shop, PIM, CRM or payment account is a separate origin.":
      "Jeder Shop sowie jedes PIM-, CRM- oder Zahlungskonto ist eine eigene Quelle.",
    "Upstream vocabulary remains distinct from operational Reality.":
      "Die Begriffe der Quellsysteme bleiben von der operativen Reality getrennt.",
    "External operating system": "Externes operatives System",
    "No source systems": "Keine Quellsysteme",
    "Add the first origin before accepting external records.":
      "Füge zuerst eine Quelle hinzu, bevor externe Datensätze angenommen werden.",
    "No accepted record types": "Keine akzeptierten Datensatztypen",
    "Define which source types this workspace may receive.":
      "Lege fest, welche Quelltypen dieser Arbeitsbereich empfangen darf.",
    "No source records yet": "Noch keine SourceRecords",
    "Use Test intake or connect a source to record the first immutable payload.":
      "Nutze den Testeingang oder verbinde eine Quelle, um den ersten unveränderlichen Payload aufzuzeichnen.",
    "Explain physical, reserved, available and projected stock without storing a presentation balance.":
      "Physische, reservierte, verfügbare und prognostizierte Bestände erklären, ohne einen Präsentationssaldo zu speichern.",
    "Change the filters or add an active item.":
      "Ändere die Filter oder füge einen aktiven Artikel hinzu.",
    "Change the filters or ingest new promise evidence.":
      "Ändere die Filter oder importiere neue Evidence für Commitments.",
    "Change the filters or import source evidence.":
      "Ändere die Filter oder importiere Evidence aus einer Quelle.",
    "Change the filters or ingest invoice evidence.":
      "Ändere die Filter oder importiere Rechnungs-Evidence.",
    "Import a bank statement or change the filters.":
      "Importiere einen Kontoauszug oder ändere die Filter.",
    "Monitor the operating machine, isolate exceptions and trace each change to its source.":
      "Überwache den laufenden Betrieb, grenze Ausnahmen ein und verfolge jede Änderung bis zu ihrer Quelle.",
    "Use a wider time range or remove a filter.":
      "Wähle einen größeren Zeitraum oder entferne einen Filter.",
    "Start with the operational view. Use traceability only when you need the complete explanation.":
      "Beginne mit der operativen Ansicht. Nutze die Nachvollziehbarkeit, wenn du die vollständige Erklärung brauchst.",
    "Review exceptions, commitments and current inventory.":
      "Ausnahmen, Commitments und aktuellen Bestand prüfen.",
    "Follow Reality through Evidence to its original SourceRecord.":
      "Reality über Evidence bis zum ursprünglichen SourceRecord zurückverfolgen.",
    "Configure sources and inspect recently received records.":
      "Quellen konfigurieren und kürzlich empfangene Datensätze prüfen.",
    "Configure the model used by this company and issue tenant-scoped HTTPS MCP credentials.":
      "Das Modell dieses Unternehmens konfigurieren und Tenant-begrenzte HTTPS-MCP-Zugangsdaten ausstellen.",
    "Connect external agents over HTTPS and control exactly which Reality tools each company token may use.":
      "Externe Agenten über HTTPS verbinden und genau steuern, welche Reality-Tools jedes Unternehmenstoken verwenden darf.",
    "No API key stored": "Kein API-Schlüssel gespeichert",
    "API key stored encrypted": "API-Schlüssel verschlüsselt gespeichert",
    "Copy this token now": "Token jetzt kopieren",
    "It will not be shown again.": "Er wird nicht erneut angezeigt.",
    "Token name, e.g. Claude": "Tokenname, z. B. Claude",
    "Model identifier": "Modellkennung",
    "Enter API key": "API-Schlüssel eingeben",
    "OpenAI-compatible base URL": "OpenAI-kompatible Basis-URL",
    "Available application tools": "Verfügbare Anwendungstools",
    "Tool catalog": "Toolkatalog",
    Tool: "Tool",
    Area: "Bereich",
    Access: "Zugriff",
    Description: "Beschreibung",
    Read: "Lesen",
    Write: "Schreiben",
    "Ask operational questions, inspect the facts behind an answer and control every proposed action.":
      "Operative Fragen stellen, die Fakten hinter einer Antwort prüfen und jede vorgeschlagene Aktion kontrollieren.",
    Chats: "Chats",
    "New conversation": "Neuer Chat",
    "Ask Reality…": "Reality fragen…",
    "Companies, customers and suppliers referenced by operational and financial Reality.":
      "Unternehmen, Kunden und Lieferanten, die in der operativen und finanziellen Reality verwendet werden.",
    "New party": "Neuer Geschäftspartner",
    "Search parties…": "Geschäftspartner suchen…",
    Role: "Rolle",
    "Source / identity": "Quelle / Identität",
    "Manual / internal": "Manuell / intern",
    Supplier: "Lieferant",
    Customer: "Kunde",
    "No parties match": "Keine passenden Geschäftspartner",
    "No parties yet": "Noch keine Geschäftspartner",
    "New item": "Neuer Artikel",
    "New location": "Neuer Lagerort",
    "Search locations…": "Lagerorte suchen…",
    "Search name or type…": "Name oder Typ suchen…",
    "Search code or name…": "Code oder Name suchen…",
    "Active parties": "Aktive Geschäftspartner",
    "Active items": "Aktive Artikel",
    "Active locations": "Aktive Lagerorte",
    "Source / Identity": "Quelle / Identität",
    "Operational state": "Operativer Status",
    "Trace ID": "Trace-ID",
    "Base unit": "Basiseinheit",
    SKU: "SKU",
    Address: "Adresse",
    Country: "Land",
    City: "Ort",
    "Autonomous commerce core": "Kern für autonomen Handel",
    "Live operations · calculated now": "Live Operations · jetzt berechnet",
    "Live operations · Calculated now": "Live Operations · jetzt berechnet",
    "Control exceptions, promises and inventory from one operational truth.":
      "Ausnahmen, Commitments und Bestand aus einer operativen Wahrheit steuern.",
    "Inspect reality": "Reality prüfen",
    "Open commitments": "Offene Commitments",
    "Open exceptions": "Offene Ausnahmen",
    "Stocked items": "Artikel mit Bestand",
    "Current positions": "Aktuelle Bestände",
    Traceability: "Nachvollziehbarkeit",
    "Decision queue": "Entscheidungswarteschlange",
    "What needs action": "Was eine Entscheidung benötigt",
    "Open work queue": "Arbeitsliste öffnen",
    "Reality Copilot": "Reality Copilot",
    "Operational briefing": "Operatives Briefing",
    "Ask for the cause behind a risk, the stock calculation, or its source evidence.":
      "Frage nach der Ursache eines Risikos, der Bestandsberechnung oder der zugrunde liegenden Evidence.",
    "Brief me on today’s risks": "Briefing zu den heutigen Risiken",
    "Explain inventory coverage": "Bestandsdeckung erklären",
    "Show open commitments": "Offene Commitments anzeigen",
    "Start a conversation": "Chat starten",
    "Current position": "Aktuelle Lage",
    "Full inventory": "Gesamten Bestand öffnen",
    "Customer commitment insufficiently reserved":
      "Customer Commitment nicht ausreichend reserviert",
    HIGH: "HOCH",
    MEDIUM: "MITTEL",
    LOW: "NIEDRIG",
    "Incoming and outgoing": "Eingehend und ausgehend",
    "Source → Reality": "Quelle → Reality",
    "Fully reserved": "Vollständig reserviert",
    "Fully Reserved": "Vollständig reserviert",
  },
  nl: {
    "Choose company": "Bedrijf kiezen",
    "Open company chat": "Bedrijfschat openen",
    "Sandbox with sample data": "Sandbox met voorbeeldgegevens",
    "Open Free Play Sandbox": "Free Play Sandbox openen",
    "Choose an existing company or create a Sandbox with sample data.":
      "Kies een bestaand bedrijf of maak een Sandbox met voorbeeldgegevens.",
    "You are working with this company's real data. Changes require confirmation.":
      "Je werkt met de echte gegevens van dit bedrijf. Wijzigingen vereisen bevestiging.",

    "Explore Reality": "Ontdek Reality",
    "Choose a storyline or Free Play.": "Kies een verhaallijn of vrij spelen.",
    "Explore freely in your own Sandbox with sample data.":
      "Experimenteer vrij in je eigen Sandbox met voorbeeldgegevens.",
    "Create Sandbox and start": "Sandbox maken en starten",
    "Sandbox setup is not ready. Try again.": "De Sandbox is nog niet klaar. Probeer het opnieuw.",
    "This Sandbox is archived. Restore it under Companies.":
      "Deze Sandbox is gearchiveerd. Herstel deze onder Bedrijven.",
    "Sandbox chat": "Sandbox-chat",
    "Calls for this reply": "Aanroepen voor dit antwoord",
    "No tool calls were recorded for this reply.":
      "Er zijn geen toolaanroepen voor dit antwoord vastgelegd.",
    "Recorded evidence is unavailable for this reply.":
      "Voor dit antwoord zijn geen vastgelegde gegevens beschikbaar.",
    "Some recorded calls are not included in this view.":
      "Sommige vastgelegde aanroepen zijn niet opgenomen in deze weergave.",
    "Changes since this call": "Wijzigingen sinds deze aanroep",
    "Changes since this call can include later activity in this Sandbox.":
      "Wijzigingen sinds deze aanroep kunnen latere activiteiten in deze Sandbox bevatten.",
    "Live simulation supports empty and standard demo Sandbox setups. Storyline Sandboxes use a different data setup that is not yet supported.":
      "Livesimulatie ondersteunt lege en standaard demo-Sandboxes. Storyline-Sandboxes gebruiken een andere gegevensstructuur die nog niet wordt ondersteund.",
    "Live simulation is not available in this Sandbox.":
      "Livesimulatie is niet beschikbaar in deze Sandbox.",
    "Create an empty Sandbox under Companies → New company, then enable live simulation there. No historical demo data is needed.":
      "Maak via Bedrijven → Nieuw bedrijf een lege Sandbox en schakel daar livesimulatie in. Historische demogegevens zijn niet nodig.",

    "Create a separate demo Sandbox for live simulation. Your existing company and Storyline stay unchanged.":
      "Maak een aparte demo-Sandbox voor livesimulatie. Je bestaande bedrijf en Storyline blijven ongewijzigd.",
    "Create demo Sandbox": "Demo-Sandbox maken",

    "Preparing your company": "Je bedrijf wordt voorbereid",
    "Continue company setup": "Bedrijfsinrichting voortzetten",
    "Your setup is saved. Continue with the same company.":
      "Je inrichting is opgeslagen. Ga verder met hetzelfde bedrijf.",
    "Enter the six-digit code from your verification email.":
      "Voer de zescijferige code uit je bevestigingsmail in.",
    "If this address needs verification, a new code has been sent.":
      "Als dit adres nog moet worden bevestigd, is er een nieuwe code verstuurd.",
    "Sending code\u2026": "Code wordt verstuurd…",
    "Send a new code": "Nieuwe code versturen",

    "Loading your access": "Je toegang wordt geladen",
    "Please wait. You will continue automatically.": "Even geduld. Je gaat automatisch verder.",
    "Loading your workspace": "Je werkruimte wordt geladen",
    "Verifying your email": "Je e-mailadres wordt bevestigd",

    "Try for free": "Gratis proberen",
    "Your own demo company. No credit card. No automatic paid subscription.":
      "Je eigen demobedrijf. Geen creditcard. Geen automatisch betaald abonnement.",
    "Try the Playground for free with your own demo company. No credit card. No automatic paid subscription.":
      "Probeer de Playground gratis met je eigen demobedrijf. Geen creditcard. Geen automatisch betaald abonnement.",
    "Try Reality for free with your own demo company. No credit card. No automatic paid subscription.":
      "Probeer Reality gratis met je eigen demobedrijf. Geen creditcard. Geen automatisch betaald abonnement.",
    "By continuing, you request a demo company with live sample data after email verification.":
      "Door verder te gaan vraag je na e-mailverificatie een demobedrijf met doorlopende voorbeeldgegevens aan.",
    "Your demo is not ready yet. Retry to continue with the same company.":
      "Je demo is nog niet klaar. Probeer opnieuw om met hetzelfde bedrijf verder te gaan.",
    "Preparing your demo company": "Je demobedrijf wordt voorbereid",
    "Orders, deliveries and invoices are being prepared for you to explore.":
      "Orders, leveringen en facturen worden klaargezet om te verkennen.",
    "Try these three questions": "Begin met deze drie vragen",
    "Explore the records directly. These tasks use no AI questions.":
      "Verken de gegevens direct. Deze taken gebruiken geen AI-vragen.",
    "Which orders need attention?": "Welke orders vragen aandacht?",
    "Why is this order not fully delivered?": "Waarom is deze order niet volledig geleverd?",
    "Which invoices remain open?": "Welke facturen staan nog open?",
    "Was that useful? Support Reality with a star on GitHub.":
      "Was dit nuttig? Steun Reality met een ster op GitHub.",
    "Star on GitHub": "Ster geven op GitHub",
    "Keep exploring": "Verder verkennen",
    "Free AI questions remaining": "Resterende gratis AI-vragen",
    "Resets at": "Opnieuw beschikbaar op",
    "Your daily AI allowance is used. Keep exploring the records or return after the reset.":
      "Je dagelijkse AI-tegoed is opgebruikt. Verken de gegevens verder of kom terug na de vernieuwing.",

    "No admission limit": "Geen toelatingslimiet",
    "Manual approval required": "Handmatige goedkeuring vereist",
    "Create your account and verify your email to continue.":
      "Maak je account aan en bevestig je e-mailadres om door te gaan.",
    "Admission follows your deployment settings. Review pending applications here.":
      "Toegang volgt je implementatie-instellingen. Beoordeel hier openstaande aanvragen.",
    "Reset filters": "Filters wissen",
    "No entries yet.": "Nog geen items.",
    "No entries yet. Use the create action to add the first entry.":
      "Nog geen items. Gebruik de aanmaakknop om het eerste item toe te voegen.",
    "Set up the accounts and tax codes used by your external bookkeeping software, then define how Reality assigns them.":
      "Stel de rekeningen en belastingcodes van je externe boekhoudsoftware in en bepaal daarna hoe Reality ze toewijst.",
    "Selected accounting target": "Geselecteerde externe boekhouding",
    "Back to accounting targets": "Terug naar boekhoudsystemen",
    "Open account setup": "Rekeninginstellingen openen",
    "Add your external bookkeeping system here. Open its account setup to maintain accounts, tax codes and assignment rules.":
      "Voeg hier je externe boekhoudsysteem toe. Open vervolgens de rekeninginstellingen om rekeningen, belastingcodes en toewijzingsregels te beheren.",
    "Add the account numbers used in this bookkeeping system. Rules can then assign transactions to these accounts.":
      "Voeg de rekeningnummers van dit boekhoudsysteem toe. Met regels kun je daarna transacties aan deze rekeningen toewijzen.",
    "Add the tax codes used in this bookkeeping system. You can select them when defining assignment rules.":
      "Voeg de belastingcodes van dit boekhoudsysteem toe. Je kunt ze daarna selecteren bij het instellen van toewijzingsregels.",
    "Define which external account and tax code a transaction should use. Add the required accounts and tax codes first.":
      "Bepaal welke externe rekening en belastingcode een transactie moet gebruiken. Voeg eerst de benodigde rekeningen en belastingcodes toe.",
    "No accounting targets yet.": "Nog geen boekhoudsystemen toegevoegd.",
    "No external accounts yet.": "Nog geen externe rekeningen toegevoegd.",
    "No tax codes yet.": "Nog geen belastingcodes toegevoegd.",
    "No assignment rules yet.": "Nog geen toewijzingsregels toegevoegd.",

    "Set up standard accounts": "Standaardrekeningen instellen",
    "These defaults apply to new transactions. Linked payments and corrections can retain the accounts of the original invoice.":
      "Deze standaardrekeningen gelden voor nieuwe transacties. Gekoppelde betalingen en correcties kunnen de rekeningen van de oorspronkelijke factuur behouden.",
    "Add account": "Rekening toevoegen",
    "View account usage": "Rekeninggebruik bekijken",
    "Accounts for business transactions": "Rekeningen voor bedrijfsactiviteiten",
    "Change default": "Standaard wijzigen",
    "Change default account": "Standaardrekening wijzigen",
    "Back to accounts": "Terug naar rekeningen",
    "Choose the accounts Reality uses for receivables, payables, payments and settlement differences.":
      "Kies welke rekeningen Reality gebruikt voor vorderingen, schulden, betalingen en betalingsverschillen.",
    "Default means Reality selects this account automatically for its role. External ledger numbers are managed under External accounting.":
      "Standaard betekent dat Reality deze rekening automatisch kiest voor haar rol. Externe grootboeknummers beheer je onder Externe boekhouding.",
    "See which operational accounts each transaction uses. Change a role default when future transactions should use a different account.":
      "Bekijk welke operationele rekeningen elke activiteit gebruikt. Wijzig de standaardrekening van een rol als toekomstige transacties een andere rekening moeten gebruiken.",
    "This default applies to every transaction using this account role. Existing postings keep their original accounts.":
      "Deze standaard geldt voor alle transacties met deze rekeningrol. Bestaande boekingen behouden hun oorspronkelijke rekeningen.",
    "Add an active account with this role before changing the default.":
      "Voeg eerst een actieve rekening met deze rol toe voordat je de standaard wijzigt.",
    "All fields are required unless marked optional.":
      "Alle velden zijn verplicht, tenzij als optioneel gemarkeerd.",
    "A prepared change is waiting for your confirmation.":
      "Een voorbereide wijziging wacht op je bevestiging.",
    "Continue review": "Controle hervatten",
    "Edit account": "Rekening bewerken",
    "Review account change": "Rekeningwijziging controleren",
    "Create cost center": "Kostenplaats aanmaken",
    "Edit cost center": "Kostenplaats bewerken",
    "Create case code": "Situatiecode aanmaken",
    "Edit case code": "Situatiecode bewerken",
    "Create coding group": "Boekingsgroep aanmaken",
    "Edit coding group": "Boekingsgroep bewerken",
    "Create accounting target": "Boekhouddoel aanmaken",
    "Edit accounting target": "Boekhouddoel bewerken",
    "Create external account": "Externe rekening aanmaken",
    "Edit external account": "Externe rekening bewerken",
    "Create tax code": "Belastingcode aanmaken",
    "Edit tax code": "Belastingcode bewerken",
    "Create mapping rule": "Toewijzingsregel aanmaken",
    "Edit mapping rule": "Toewijzingsregel bewerken",
    "Search by code or name": "Zoeken op code of naam",
    "Target identifier": "Identificatie boekhouddoel",
    "Coding group condition": "Voorwaarde voor boekingsgroep",
    "No coding group condition": "Geen voorwaarde voor boekingsgroep",
    "Check the proposed values. The change takes effect only after confirmation.":
      "Controleer de voorgestelde waarden. De wijziging wordt pas na bevestiging toegepast.",
    "The account role determines which operational transactions can use this account. External ledger numbers are configured under External accounting.":
      "De rekeningrol bepaalt welke operationele transacties deze rekening kunnen gebruiken. Externe grootboeknummers beheer je onder Externe boekhouding.",
    "The role is fixed after creation. The default account is used when a transaction does not specify another eligible account.":
      "De rol staat na aanmaak vast. De standaardrekening wordt gebruikt als de transactie geen andere toegestane rekening opgeeft.",
    "Use a short, unique code and a recognizable name. The code cannot be changed after creation.":
      "Gebruik een korte, unieke code en een herkenbare naam. De code kan na aanmaak niet worden gewijzigd.",
    "Identify the department, location or project receiving the cost, for example SALES or BERLIN. Codes remain permanent.":
      "Benoem de afdeling, locatie of het project waaraan kosten worden toegewezen, bijvoorbeeld SALES of BERLIN. Codes blijven permanent.",
    "Define a business case such as domestic sales or export. A case code is a declared classification, not an automatic tax calculation.":
      "Definieer een situatie zoals binnenlandse verkoop of export. Een situatiecode is een vastgelegde classificatie en berekent geen belasting.",
    "Group products or services that need the same account mapping. A rule can require an exact coding group.":
      "Groepeer producten of diensten met dezelfde rekeningtoewijzing. Een regel kan een specifieke boekingsgroep vereisen.",
    "Choose the source system and its original code, then the internal case code or coding group it means.":
      "Kies het bronsysteem en de oorspronkelijke code en wijs de bijbehorende interne situatiecode of boekingsgroep toe.",
    "The source namespace groups codes from the same source, for example a tax-code list. Copy namespace and code exactly as received.":
      "De bronnaamruimte groepeert codes uit dezelfde bron, bijvoorbeeld een belastingcodelijst. Neem naamruimte en code exact over.",
    "Choose when this rule applies and which external account it selects. All conditions must match exactly.":
      "Bepaal wanneer deze regel geldt en welke externe rekening wordt gekozen. Alle voorwaarden moeten exact overeenkomen.",
    "Enter the code and name used by your external accounting software.":
      "Vul de code en naam uit je externe boekhoudsoftware in.",
    "Explain why you are adding or changing this entry. This note is retained in its history.":
      "Leg kort uit waarom je deze invoer aanmaakt of wijzigt. Deze toelichting blijft in de historie bewaard.",
    "Assignment belongs to an earlier evidence version":
      "Toewijzing hoort bij een eerdere documentversie",
    "Internal assignment": "Interne toewijzing",
    "Account settings areas": "Onderdelen van rekeninginstellingen",
    "Accounting target": "Boekhoudbestemming",
    "Accounting targets": "Boekhoudbestemmingen",
    "Define permitted external destinations. Local balances remain independent.":
      "Definieer toegestane externe bestemmingen. Lokale saldi blijven onafhankelijk.",
    "Edit configuration": "Configuratie bewerken",
    "New configuration": "Nieuwe configuratie",
    "Exact coding group": "Exacte coderingsgroep",
    "External account": "Externe rekening",
    "External accounts": "Externe rekeningen",
    "External accounting": "Externe boekhouding",
    "External accounting areas": "Onderdelen van externe boekhouding",
    "Gross operational account references": "Operationele rekeningreferenties voor brutobedragen",
    "Group discrimination": "Onderscheid per groep",
    "Mapping history": "Toewijzingshistorie",
    "Mapping preview": "Toewijzingsvoorbeeld",
    "Mapping revision": "Toewijzingsversie",
    "Mapping scope": "Toewijzingsbereik",
    Namespace: "Naamruimte",
    "Operational account": "Operationele rekening",
    "Received components": "Ontvangen documentonderdelen",
    "Review configuration": "Configuratie beoordelen",
    "Shows external destinations, not export completeness or external posting.":
      "Toont externe bestemmingen. Exportvolledigheid en externe boeking zijn hiermee niet bevestigd.",
    "Tax code": "Belastingcode",
    "Tax codes": "Belastingcodes",
    Transaction: "Transactie",
    "Without group discrimination": "Zonder groepsonderscheid",
    "Mapping resolved": "Toewijzing gevonden",
    "A declared case is required": "Een aangegeven gevalscode ontbreekt",
    "A coding group is required": "Een coderingsgroep ontbreekt",
    "No matching target rule": "Geen passende bestemmingsregel",
    "Multiple target rules match": "Meerdere bestemmingsregels komen overeen",
    "Accounting target is blocked": "Boekhoudbestemming is geblokkeerd",
    "External destination is blocked": "Externe bestemming is geblokkeerd",
    "Operational account is blocked": "Operationele rekening is geblokkeerd",
    "Source and internal case conflict": "Gevalscode uit bron en interne toewijzing conflicteren",
    "Source and internal group conflict": "Groep uit bron en interne toewijzing conflicteren",
    "Classification needs review": "Classificatie moet worden beoordeeld",
    "Transaction matrix": "Transactiematrix",
    Configured: "Ingesteld",
    "Missing default": "Standaardrekening ontbreekt",
    "Incompatible account role": "Onverenigbare rekeningrol",
    "Configured default accounts": "Ingestelde standaardrekeningen",
    "Original control account when linked":
      "Bij koppeling geldt de oorspronkelijke controlerekening",
    "Original invoice account required": "Oorspronkelijke factuurrekening vereist",
    "These are current defaults. The action preview validates the actual evidence and accounts.":
      "Dit zijn de huidige standaardrekeningen. Het actievoorbeeld controleert de daadwerkelijke documenten en rekeningen.",
    "Reversals retain original accounts and reverse the original group.":
      "Storneringen gebruiken de oorspronkelijke rekeningen en keren de oorspronkelijke boekingsgroep om.",
    "Orders, reservations, stock movements and allocations do not add postings here.":
      "Orders, reserveringen, voorraadmutaties en toewijzingen voegen hier geen boekingen toe.",
    "Configure accounts": "Rekeningen instellen",
    "Amount basis": "Bedragsbasis",
    "Stated invoice gross": "Vermeld bruto factuurbedrag",
    "Stated payment amount": "Vermeld betalingsbedrag",
    "Stated refund amount": "Vermeld terugbetalingsbedrag",
    "Explicitly accepted reduction": "Uitdrukkelijk aanvaarde vermindering",
    "Stated opening residual": "Vermeld resterend openingsbedrag",
    "Customer settlement reduction": "Aanvaarde klantvermindering",
    "Supplier settlement reduction": "Aanvaarde leveranciersvermindering",
    "Opening customer debt": "Openingsvordering op klant",
    "Opening customer credit": "Openingstegoed van klant",
    "Opening supplier debt": "Openingsschuld aan leverancier",
    "Opening supplier credit": "Openingstegoed bij leverancier",
    "Sales invoice": "Verkoopfactuur",
    "Customer credit note": "Creditnota voor klant",
    "Customer payment": "Klantbetaling",
    "Customer refund": "Terugbetaling aan klant",
    "Supplier invoice": "Leveranciersfactuur",
    "Supplier credit note": "Creditnota van leverancier",
    "Supplier payment": "Leveranciersbetaling",
    "Supplier refund": "Terugbetaling van leverancier",
    "Add cost-center share": "Kostenplaatsaandeel toevoegen",
    "Assign individual lines. The document summary is not added again.":
      "Wijs afzonderlijke regels toe. Het documenttotaal wordt niet nogmaals meegenomen.",
    Assigned: "Toegewezen",
    "Attribution basis": "Toewijzingsbasis",
    "Attribution history": "Toewijzingsgeschiedenis",
    "Attribution saved": "Toewijzing opgeslagen",
    "Case code": "Situatiecode",
    "Clear internal attribution": "Interne toewijzing wissen",
    "Coding group": "Boekingsgroep",
    Components: "Componenten",
    "Confirm attribution": "Toewijzing bevestigen",
    "Cost center": "Kostenplaats",
    "Current attribution": "Huidige toewijzing",
    "Enter explicit shares. Empty shares leave the amount unassigned.":
      "Voer de aandelen als bedragen in. Zonder aandelen blijft het bedrag niet toegewezen.",
    "Financial detail": "Financiële details",
    "Find classification references": "Classificatiewaarden zoeken",
    "Inspect document": "Document inspecteren",
    "Inspect line": "Regel inspecteren",
    "Internal attribution": "Interne toewijzing",
    "No internal attribution": "Geen interne toewijzing",
    "Original source codes": "Oorspronkelijke broncodes",
    "Received component": "Ontvangen component",
    "Received document summary": "Ontvangen documenttotalen",
    "Refine the reference search to find more entries.":
      "Verfijn de zoekopdracht om meer vermeldingen te vinden.",
    "Remove share": "Aandeel verwijderen",
    "Review attribution": "Toewijzing controleren",
    "Select cost center": "Kostenplaats selecteren",
    "Select financial component": "Financiële component selecteren",
    "Share amount": "Aandeelbedrag",
    "This document has no lines. Attribution uses its received amounts.":
      "Dit document heeft geen regels. De toewijzing gebruikt de ontvangen bedragen.",
    Unassigned: "Niet toegewezen",
    "Other received basis": "Andere ontvangen basis",
    "Inspect financial detail": "Financiële details inspecteren",
    "See open commitments, exceptions and decisions across your company.":
      "Bekijk open verplichtingen, afwijkingen en beslissingen binnen je bedrijf.",
    "Track outstanding deliveries to your customers.":
      "Volg openstaande leveringen aan je klanten.",
    "Track outstanding deliveries from your suppliers.":
      "Volg openstaande leveringen van je leveranciers.",
    "Review issues that need attention and inspect the records behind them.":
      "Bekijk afwijkingen en onderzoek de onderliggende gegevens.",
    "Review proposed actions and decide whether to proceed.":
      "Beoordeel voorgestelde acties en beslis of ze uitgevoerd mogen worden.",
    "See physical, reserved and available stock for each item.":
      "Bekijk de fysieke, gereserveerde en beschikbare voorraad per artikel.",
    "See which stock is reserved for each commitment.":
      "Bekijk welke voorraad voor elke verplichting is gereserveerd.",
    "Follow recorded stock receipts, shipments and adjustments.":
      "Volg geregistreerde ontvangsten, verzendingen en voorraadcorrecties.",
    "See outstanding receivables and payables, grouped by currency.":
      "Bekijk openstaande vorderingen en schulden per valuta.",
    "Review recorded incoming and outgoing payments.":
      "Bekijk geregistreerde inkomende en uitgaande betalingen.",
    "Inspect recorded ledger entries and their supporting records.":
      "Bekijk boekingen en de bijbehorende bewijsstukken.",
    "Follow how sources, documents and business records connect over time.":
      "Volg hoe bronnen, documenten en bedrijfsgegevens door de tijd samenhangen.",
    "Explore a record and follow its links to related information.":
      "Verken een record en volg de koppelingen naar gerelateerde informatie.",
    "Explore your company’s recorded information and trace it to its sources.":
      "Verken de geregistreerde informatie van je bedrijf en volg deze naar de bronnen.",
    "Explore how existing records are combined into calculated views.":
      "Ontdek hoe bestaande records worden gecombineerd in berekende weergaven.",
    "Review the rules that record additional facts from source data on the right business record.":
      "Bekijk de regels die uit brondata aanvullende feiten bij het juiste bedrijfsrecord vastleggen.",
    "Explore the conditions that identify issues requiring attention.":
      "Bekijk welke voorwaarden afwijkingen signaleren.",
    "See what was recorded across your company, newest first.":
      "Bekijk wat binnen je bedrijf is geregistreerd, met het nieuwste eerst.",
    "Explore available actions, their inputs and what they do.":
      "Verken beschikbare acties, hun invoer en hun werking.",
    "Explore additional observations, their sources and the records they describe.":
      "Verken aanvullende waarnemingen, hun bronnen en de records die ze beschrijven.",
    "Track delivery commitments and inspect their reservations and movements.":
      "Volg leveringsverplichtingen en bekijk hun reserveringen en bewegingen.",
    "Review customer orders and follow their linked delivery commitments.":
      "Bekijk klantorders en volg de bijbehorende leveringsverplichtingen.",
    "Review purchase orders and follow their linked delivery commitments.":
      "Bekijk inkooporders en volg de bijbehorende leveringsverplichtingen.",
    "Find customers and review their details and commercial defaults.":
      "Zoek klanten en bekijk hun gegevens en commerciële standaardinstellingen.",
    "Find suppliers and review their details and commercial defaults.":
      "Zoek leveranciers en bekijk hun gegevens en commerciële standaardinstellingen.",
    "Find items and review their reference details.": "Zoek artikelen en bekijk hun stamgegevens.",
    "Find locations and review their reference details.":
      "Zoek locaties en bekijk hun stamgegevens.",
    "Plan integrations and manage registered data sources.":
      "Plan integraties en beheer geregistreerde gegevensbronnen.",
    "Inspect received data, its import status and linked business records.":
      "Bekijk ontvangen gegevens, hun importstatus en gekoppelde bedrijfsrecords.",
    "Inspect recorded documents and trace them to their original sources.":
      "Bekijk geregistreerde documenten en volg ze naar hun oorspronkelijke bronnen.",
    "Explore the current delivery position and the recorded activity behind it.":
      "Verken de huidige leveringssituatie en de geregistreerde activiteit erachter.",
    "Switch companies or manage their users, agents and AI settings.":
      "Wissel van bedrijf of beheer gebruikers, agents en AI-instellingen.",
    "Set your language, number format, timezone and appearance.":
      "Stel je taal, getalnotatie, tijdzone en uiterlijk in.",
    "Control synthetic data arrivals and review recent demo activity.":
      "Beheer de instroom van synthetische gegevens en bekijk recente demoactiviteit.",
    "Demo company": "Demobedrijf",
    "View data": "Weergavegegevens",
    "Graph starting points": "Startpunten van de grafiek",
    "Starting point": "Startpunt",
    "No records are available for this starting point yet.":
      "Voor dit startpunt zijn nog geen records beschikbaar.",
    "Choose a starting point or search for a record.": "Kies een startpunt of zoek een record.",
    Order: "Order",
    Fact: "Feit",
    Columns: "Kolommen",
    "Compact rows": "Compacte rijen",
    "Filter records": "Records filteren",
    Observation: "Waarneming",
    "Reset table": "Tabel herstellen",
    "Resize column": "Kolombreedte aanpassen",
    "Rows per page": "Rijen per pagina",
    "Scrollable register": "Schuifbare tabel",
    "Sort column": "Kolom sorteren",
    "All subject types": "Alle onderwerpsoorten",
    "An observation is not a current-state guarantee. Different observations can coexist; this view does not choose a winning value.":
      "Een waarneming garandeert geen actuele toestand. Verschillende waarnemingen kunnen naast elkaar bestaan; deze weergave kiest geen leidende waarde.",
    "Clear filters": "Filters wissen",
    "Exact predicate": "Exact predicaat",
    "Explain observation": "Waarneming verklaren",
    "Explore recorded observations about your business. Each observation keeps its own value, time and origin.":
      "Verken vastgelegde waarnemingen over je bedrijf. Elke waarneming behoudt haar eigen waarde, tijdstip en herkomst.",
    "Fact ID": "Feit-ID",
    "Interpretation rule": "Interpretatieregel",
    "No linked source recorded": "Geen gekoppelde bron vastgelegd",
    "No observations found": "Geen waarnemingen gevonden",
    "Predicate, value, subject ID or source reference":
      "Predicaat, waarde, onderwerp-ID of bronreferentie",
    "Related observations": "Gerelateerde waarnemingen",
    "Search observations": "Waarnemingen zoeken",
    "Shipping priority": "Verzendprioriteit",
    "Source record ID": "Bronrecord-ID",
    "Subject ID": "Onderwerp-ID",
    "Subject type": "Onderwerpsoort",
    "The first 100 subject types are listed. Search can find observations of other types.":
      "De eerste 100 onderwerpsoorten worden getoond. Met zoeken vind je ook waarnemingen van andere soorten.",
    "Try another search or clear the filters. Facts appear when a source-backed observation is recorded.":
      "Probeer een andere zoekopdracht of wis de filters. Feiten verschijnen wanneer een waarneming met bron wordt vastgelegd.",
    Value: "Waarde",
    "View observations": "Waarnemingen bekijken",
    "What was observed, and where it came from.": "Wat is waargenomen en waar het vandaan komt.",
    "This is a recorded observation, not a current-state guarantee.":
      "Dit is een vastgelegde waarneming, geen garantie voor de actuele toestand.",
    "Context and source": "Context en bron",
    "Remaining quantity": "Resterende hoeveelheid",
    "Advanced order operations": "Geavanceerde orderbewerkingen",
    "All delivery history": "Volledige leveringshistorie",
    "Clear order filter": "Orderfilter wissen",
    "Customer deliveries": "Klantleveringen",
    "Customer delivery actions open in Your work. Supplier details include their linked evidence.":
      "Acties voor klantleveringen openen in Jouw werk. Leveranciersdetails bevatten het gekoppelde bewijs.",
    Deliveries: "Leveringen",
    Shipments: "Zendingen",
    Dispatched: "Verzonden",
    Carrier: "Vervoerder",
    Contents: "Inhoud",
    "Tracking number": "Trackingnummer",
    "Observed state": "Waargenomen status",
    "Physical contents": "Fysieke inhoud",
    "Tracking observations": "Trackingwaarnemingen",
    "No stock movement recorded": "Geen voorraadbeweging vastgelegd",
    "Warehouse and carrier observations differ": "Magazijn- en vervoerderswaarnemingen verschillen",
    "Search carrier, tracking number or shipment ID":
      "Zoek vervoerder, trackingnummer of zendings-ID",
    "Shipment ID": "Zendings-ID",
    "Package ID (optional)": "Pakket-ID (optioneel)",
    Reporter: "Melder",
    "Replacement event ID (optional)": "ID vervangende gebeurtenis (optioneel)",
    "Counterparty ID": "Relatie-ID",
    "Movement inputs (JSON)": "Movement-invoer (JSON)",
    "Movements must be a JSON array": "Movements moeten een JSON-array zijn",
    "Review exact effect": "Exact effect controleren",
    "Prepare the exact shipment change, then review it before confirmation.":
      "Bereid de exacte zendingswijziging voor en controleer die vóór bevestiging.",
    "Deliveries for the selected order": "Leveringen voor de geselecteerde order",
    "Delivery direction": "Leveringsrichting",
    "Delivery scope": "Leveringsselectie",
    "From order to delivery.": "Van order tot levering.",
    Lines: "Regels",
    "No due date": "Geen leverdatum",
    "Open deliveries have a remaining quantity and an open commitment. All history includes completed and cancelled commitments.":
      "Open leveringen hebben een resterende hoeveelheid en een open toezegging. De volledige historie bevat ook vervulde en geannuleerde toezeggingen.",
    "Order document": "Orderdocument",
    "Order documents record the agreement. Delivery progress comes from linked commitments and movements.":
      "Orderdocumenten leggen de afspraak vast. De leveringsvoortgang volgt uit gekoppelde toezeggingen en voorraadbewegingen.",
    "Orders & deliveries": "Orders en leveringen",
    "Recorded status": "Vastgelegde status",
    "Search orders and deliveries": "Orders en leveringen zoeken",
    "Search party, item or delivery ID": "Relatie, artikel of leverings-ID zoeken",
    "See what was agreed, what is still open and the records behind it.":
      "Bekijk wat is afgesproken, wat nog openstaat en de onderliggende records.",
    "Supplier deliveries": "Leveranciersleveringen",
    "Supplier orders": "Leveranciersorders",
    "Unknown item": "Onbekend artikel",
    "Unknown location": "Onbekende locatie",
    "View deliveries": "Leveringen bekijken",
    Failed: "Mislukt",
    Unknown: "Onbekend",
    Expired: "Verlopen",
    "Sending invitation": "Uitnodiging wordt verzonden",
    "Invitation delivered": "Uitnodiging bezorgd",
    "Delivery retry scheduled": "Nieuwe verzendpoging gepland",
    "Invitation delivery": "Verzending uitnodiging",

    "Advanced company settings": "Geavanceerde bedrijfsinstellingen",
    "AI credentials configured": "AI-inloggegevens ingesteld",
    "AI credentials not configured": "AI-inloggegevens niet ingesteld",
    "Appearance is saved in this browser. System follows your device.":
      "De weergave wordt in deze browser opgeslagen. Systeem volgt je apparaatinstelling.",
    "Check saved preferences": "Opgeslagen voorkeuren controleren",
    "Company access": "Bedrijfstoegang",
    "Company credentials": "Bedrijfseigen inloggegevens",
    "Configuration status does not confirm a live connection to the AI provider.":
      "De configuratiestatus bevestigt geen actieve verbinding met de AI-aanbieder.",
    "Credential management": "Beheer van inloggegevens",
    Expires: "Verloopt",
    "Make Reality work for you.": "Stel Reality in op jouw manier.",
    "Manage invitations, credentials and company setup in company administration.":
      "Beheer uitnodigingen, inloggegevens en bedrijfsinstellingen in het bedrijfsbeheer.",
    Member: "Lid",
    "Not configured": "Niet ingesteld",
    "Number and date format": "Getal- en datumnotatie",
    "Only company owners can view these settings.":
      "Alleen bedrijfseigenaren kunnen deze instellingen bekijken.",
    Owner: "Eigenaar",
    "Personal preferences": "Persoonlijke voorkeuren",
    "Preferences saved.": "Voorkeuren opgeslagen.",
    "Saved preferences differ from your draft. Review it before saving again.":
      "De opgeslagen voorkeuren wijken af van je concept. Controleer het voordat je opnieuw opslaat.",
    "Settings sections": "Instellingsonderdelen",
    "These preferences apply to your account across all companies.":
      "Deze voorkeuren gelden voor je account in alle bedrijven.",
    "This view shows up to 500 members and 500 invitations.":
      "Deze weergave toont maximaal 500 leden en 500 uitnodigingen.",
    "Time zone": "Tijdzone",
    "Use an IANA time zone, such as Europe/Rome or America/New_York.":
      "Gebruik een IANA-tijdzone, zoals Europe/Rome of America/New_York.",
    "Your preferences, company access and AI configuration in one place.":
      "Je voorkeuren, bedrijfstoegang en AI-configuratie op één plek.",
    "Preferences were not saved. Check your entries and try again.":
      "De voorkeuren zijn niet opgeslagen. Controleer je invoer en probeer het opnieuw.",
    "The save result is unknown. Check saved preferences before trying again.":
      "Het opslagresultaat is onbekend. Controleer de opgeslagen voorkeuren voordat je het opnieuw probeert.",
    "Could not check saved preferences. Try checking again.":
      "De opgeslagen voorkeuren konden niet worden gecontroleerd. Probeer de controle opnieuw.",
    Queued: "In wachtrij",
    Sending: "Wordt verzonden",
    "Not sent": "Niet verzonden",
    "Clear source version": "Bronversie wissen",
    "Document / party": "Document / relatie",
    "Documents are evidence. Delivery and payment state comes from the linked business records.":
      "Documenten zijn bewijsstukken. Leverings- en betalingsstatus volgen uit gekoppelde bedrijfsrecords.",
    Enabled: "Ingeschakeld",

    "Exact source version": "Exacte bronversie",
    "Exact system code": "Exacte systeemcode",
    "External reference / origin": "Externe referentie / herkomst",
    "Follow registered origins, received originals and the evidence they produced.":
      "Volg geregistreerde bronnen, ontvangen originelen en de bijbehorende bewijsstukken.",
    "Import job": "Importtaak",
    "Job status describes processing, not interpretation success. Open a record to inspect its original.":
      "De taakstatus beschrijft verwerking, niet het succes van interpretatie. Open een record om het origineel te bekijken.",
    "No import job": "Geen importtaak",
    "No linked source": "Geen gekoppelde bron",
    "Open original": "Origineel openen",
    "Originals preserve what arrived. Documents hold evidence. Reality describes the business state.":
      "Originelen bewaren wat binnenkwam. Documenten bevatten bewijs. Reality beschrijft de bedrijfsstand.",
    "Received records": "Ontvangen records",
    "received versions": "ontvangen versies",
    "Recorded amount": "Vastgelegd bedrag",
    "Registered systems are definitions, not proof of a live connection. Counts include every held source version.":
      "Geregistreerde systemen zijn definities, geen bewijs van een actieve verbinding. Aantallen omvatten alle bewaarde bronversies.",
    "Search data": "Gegevens zoeken",
    "Search document number, reference or source": "Documentnummer, referentie of bron zoeken",
    "Search origin, type or external reference": "Herkomst, type of externe referentie zoeken",
    "Search system name or code": "Systeemnaam of code zoeken",
    "See where your business data comes from.": "Zie waar je bedrijfsgegevens vandaan komen.",
    "Source setup and imports": "Broninstellingen en import",
    Systems: "Bronsystemen",
    "Technical Explorer": "Technische Explorer",
    "View evidence": "Bewijsstukken bekijken",
    "View received records": "Ontvangen records bekijken",
    "Account / posting": "Rekening / boeking",
    "Advanced finance operations": "Meer financiële acties",
    "All filtered records": "Alle gefilterde records",
    "Amounts follow recorded postings and allocations. Each currency stays separate.":
      "Bedragen volgen vastgelegde boekingen en toewijzingen. Elke valuta blijft apart.",
    Balance: "Saldo",
    Credit: "Credit",
    Debit: "Debet",
    "Debits and credits follow the selected account and search. A filtered balance need not be zero.":
      "Debet en credit volgen de gekozen rekening en zoekopdracht. Het gefilterde saldo hoeft niet nul te zijn.",
    "Exact account": "Exacte rekening",
    "Follow outstanding invoices, recorded payments and their financial evidence.":
      "Volg openstaande facturen, vastgelegde betalingen en hun bewijsstukken.",
    "Invoice / party": "Factuur / relatie",
    "Operational financial records, not statutory accounts.":
      "Operationele financiële gegevens, geen wettelijke jaarrekening.",
    Outstanding: "Nog openstaand",
    "Partially settled": "Gedeeltelijk vereffend",
    "Payment / party": "Betaling / relatie",
    "Recorded payment history includes reversals. Amounts are shown per payment.":
      "De betalingshistorie bevat ook tegenboekingen. Bedragen worden per betaling getoond.",
    "Reversed original": "Tegengeboekt origineel",
    "Reversing entry": "Tegenboeking",
    "Search finance": "Financiële gegevens zoeken",
    "Search invoice or party": "Factuur of relatie zoeken",
    "Understand what is open, paid and recorded.": "Begrijp wat openstaat, betaald en geboekt is.",
    Adjustment: "Voorraadaanpassing",
    "Advanced warehouse operations": "Meer magazijnacties",
    "All severities": "Alle prioriteiten",
    "Available stock": "Beschikbare voorraad",
    "Check current state": "Actuele stand controleren",
    "Clear item filter": "Artikelfilter wissen",
    "Company-wide stock per item. Quantities retain their own units.":
      "Voorraad per artikel voor het hele bedrijf. Hoeveelheden behouden hun eigen eenheid.",
    Compensation: "Tegenboeking",
    Consumed: "Verbruikt",
    Corrected: "Gecorrigeerd",
    Correction: "Correctie",
    Critical: "Kritiek",
    "Current finding": "Actuele bevinding",
    "Current findings, their causes and the records that explain them.":
      "Actuele bevindingen, hun oorzaken en de onderliggende records.",
    "Explain finding": "Bevinding uitleggen",
    "Findings clear when the underlying records change. They are not manually dismissed tasks.":
      "Bevindingen verdwijnen als de onderliggende records veranderen. Ze worden niet handmatig afgevinkt.",
    "Findings reflect the records currently available in this company.":
      "Bevindingen zijn gebaseerd op de huidige records van dit bedrijf.",
    High: "Hoog",
    "Know what is available, and why.": "Weet wat beschikbaar is, en waarom.",
    Low: "Laag",
    "No available stock": "Geen beschikbare voorraad",
    "No current findings": "Geen actuele bevindingen",
    "No matching findings": "Geen overeenkomende bevindingen",
    Normal: "Standaard",
    "Open a finding to see its cause, supporting records and next step.":
      "Open een bevinding voor de oorzaak, onderliggende records en de volgende stap.",
    "Open delivery": "Levering openen",
    "Open warehouse": "Magazijn openen",
    "Overallocated stock": "Te veel gereserveerd",
    Receipt: "Ontvangst",
    "Recorded causes and references": "Vastgelegde oorzaken en referenties",
    "Recorded history includes corrected originals and compensations.":
      "De vastgelegde historie bevat gecorrigeerde originelen en tegenboekingen.",
    Released: "Vrijgegeven",
    Replacement: "Vervangende boeking",
    "Reserved stock is linked to its commitment.":
      "Gereserveerde voorraad is gekoppeld aan de toezegging.",
    "Resolution guidance": "Richtlijn voor oplossing",
    "Search by item name or SKU": "Zoeken op artikelnaam of SKU",
    "Search by reference ID": "Zoeken op referentie-ID",
    "Search causes or references": "Oorzaken of referenties zoeken",
    "Search exceptions": "Bevindingen doorzoeken",
    "Search warehouse": "Magazijn doorzoeken",
    "See what needs a closer look.": "Zie wat nader onderzoek nodig heeft.",
    Severity: "Prioriteit",
    "Start with a finding": "Begin met een bevinding",
    Stock: "Voorraad",
    "Stock, its reservations and the movements behind it.":
      "Voorraad, reserveringen en de onderliggende bewegingen.",
    "Supplier return": "Leveranciersretour",
    "Supporting record": "Onderliggend record",
    Transfer: "Overboeking",
    "Try another filter or inspect the original records.":
      "Probeer een ander filter of bekijk de oorspronkelijke records.",
    Workspaces: "Werkruimtes",
    Customers: "Klanten",
    Suppliers: "Leveranciers",
    Roles: "Rollen",
    "Date (UTC)": "Datum (UTC)",
    Analytics: "Analyses",
    "Fully reserved": "Volledig gereserveerd",
    "Needs reservation": "Reservering nodig",
    "Overdue deliveries": "Achterstallige leveringen",
    "Without due date": "Zonder vervaldatum",
    "Delivery commitments created": "Aangemaakte levertoezeggingen",
    "Shipment movements": "Verzendbewegingen",
    "How your operations are moving": "Hoe je activiteiten verlopen",
    "Open analytics": "Analytics openen",
    "Recorded activity over time": "Vastgelegde activiteit in de tijd",
    "Delivery commitments created and shipment movements":
      "Aangemaakte levertoezeggingen en verzendbewegingen",
    "Understand the flow of your business.": "Begrijp de stroom van je bedrijf.",
    "Current delivery position and the activity behind it.":
      "Actuele leverstatus en de activiteit erachter.",
    "No open deliveries to measure": "Geen open leveringen om te meten",
    "of open deliveries": "van open leveringen",
    "Current position · view records": "Actuele stand · records bekijken",
    "Recorded activity": "Vastgelegde activiteit",
    "Counts of commitments and movements · UTC days":
      "Aantal toezeggingen en bewegingen · UTC-dagen",
    Period: "Periode",
    days: "dagen",
    "These series count different records, not order conversion. Corrections are reflected in shipment counts. External history may be incomplete.":
      "Deze reeksen tellen verschillende records, geen orderconversie. Correcties zijn verwerkt in de verzendaantallen. Externe historie kan onvolledig zijn.",
    "Daily values and supporting records": "Dagwaarden en onderliggende records",
    "Supporting records": "Onderliggende records",
    records: "records",
    "No matching records": "Geen overeenkomende records",
    "Observed at": "Waargenomen op",
    "Current position is independent of the selected period.":
      "De actuele stand is onafhankelijk van de gekozen periode.",
    "Master data action": "Stamgegevensactie",
    "Edit details": "Details bewerken",
    "Item type": "Artikeltype",
    Tracking: "Tracering",
    "Default location": "Standaardlocatie",
    "Purchase unit": "Inkoopeenheid",
    "Conversion factor": "Omrekeningsfactor",
    "Lead time (days)": "Levertijd (dagen)",
    "Parent location": "Bovenliggende locatie",
    "Allows physical stock": "Staat fysieke voorraad toe",
    Stocked: "Voorraadartikel",
    Service: "Dienst",
    Charge: "Toeslag",
    "No tracking": "Geen tracering",
    Serial: "Serienummer",
    Identity: "Identiteit",
    "Commercial defaults": "Commerciële standaardwaarden",
    "Inventory behaviour": "Voorraadgedrag",
    Hierarchy: "Hiërarchie",
    "Reviewed revision": "Beoordeelde revisie",
    "Choices could not be loaded.": "Keuzes konden niet worden geladen.",
    "Create a record": "Record aanmaken",
    "Change recorded": "Wijziging vastgelegd",
    "Outcome not yet verified": "Uitkomst nog niet gecontroleerd",
    "Ready for your confirmation": "Klaar voor je bevestiging",
    "Recorded intent and receipt. Current details may have changed since execution.":
      "Vastgelegde opdracht en resultaat. Actuele gegevens kunnen sinds de uitvoering zijn gewijzigd.",
    "Check the exact fields below. Confirmation records this change.":
      "Controleer de exacte velden hieronder. Bevestiging legt deze wijziging vast.",
    "Field changes": "Veldwijzigingen",
    "Recorded reference IDs": "Vastgelegde referentie-ID’s",
    "Open record": "Record openen",
    "Prepare a change, review it, then confirm. Nothing is recorded yet.":
      "Bereid een wijziging voor, controleer en bevestig. Er wordt nog niets vastgelegd.",
    "A prepared request is saved. Check it before starting another change.":
      "Er is een voorbereide opdracht opgeslagen. Controleer deze voordat je een nieuwe wijziging start.",
    "Check prepared request": "Voorbereide opdracht controleren",
    "Prepare change": "Wijziging voorbereiden",
    "Edit request": "Opdracht bewerken",
    "The people, products and places behind your operations.":
      "De mensen, producten en locaties achter je activiteiten.",
    "Resume request": "Opdracht hervatten",
    "Search master data": "Stamgegevens doorzoeken",
    "Search by name, SKU or ID": "Zoeken op naam, SKU of ID",
    "Include inactive": "Inactieve opnemen",
    "Adjust your search or create the first record.":
      "Pas je zoekopdracht aan of maak het eerste record aan.",
    Provenance: "Herkomst",
    "No original source is linked to this record.":
      "Er is geen oorspronkelijke bron aan dit record gekoppeld.",
    "All recorded details": "Alle vastgelegde gegevens",
    "Start with a record": "Begin met een record",
    "Choose a customer, supplier, item or location to see its details and prepare a change.":
      "Kies een klant, leverancier, artikel of locatie om details te bekijken en een wijziging voor te bereiden.",
    "Also available in chat": "Ook beschikbaar in chat",
    "Ask Reality to prepare a change. You review the same fields before confirming.":
      "Vraag Reality een wijziging voor te bereiden. Je controleert dezelfde velden voordat je bevestigt.",
    "Advanced settings": "Geavanceerde instellingen",
    "Recorded result is not yet verified.": "Het vastgelegde resultaat is nog niet geverifieerd.",
    "Still open": "Nog open",
    "Allocate available stock to a delivery.": "Beschikbare voorraad aan een levering toewijzen.",
    "Record goods leaving the warehouse.": "Goederen vastleggen die het magazijn verlaten.",
    "More records are available in the workspace.":
      "Meer records zijn beschikbaar in de werkruimte.",
    "Open inventory": "Voorraad openen",
    "Current observation unavailable": "Actuele stand niet beschikbaar",
    "Handling unit": "Laadeenheid",
    Lot: "Partij",
    "Serial unit": "Serienummer",
    History: "Geschiedenis",
    "No results": "Geen resultaten",
    Pending: "In afwachting",
    Delivery: "Levering",
    "Check outcome": "Uitkomst controleren",
    "Choose a delivery": "Kies een levering",
    "Confirm change": "Wijziging bevestigen",
    "Execution outcome is being checked. Do not repeat the action.":
      "De uitkomst wordt gecontroleerd. Herhaal de actie niet.",
    "Preparing a review does not change stock.": "De voorbereiding verandert geen voorraad.",
    "Record shipment": "Verzending vastleggen",
    "Recorded result is separate from the current observation.":
      "Het vastgelegde resultaat en de actuele stand worden afzonderlijk getoond.",
    Rejected: "Afgewezen",
    "Review change": "Wijziging beoordelen",
    "Review the exact change before confirming.":
      "Beoordeel de exacte wijziging voordat je bevestigt.",
    "Selected delivery": "Geselecteerde levering",
    "Tracking references": "Voorraadidentiteiten",
    "Not selected": "Niet geselecteerd",
    "Refine your search to see more matches.": "Verfijn je zoekopdracht voor meer resultaten.",
    "A clear view of what is open.": "Een helder overzicht van wat openstaat.",
    "Ask about orders, stock and money.": "Stel vragen over orders, voorraad en geld.",
    "Ask about your company": "Vraag over je bedrijf",
    "Back to deliveries": "Terug naar leveringen",
    "Choose a delivery to see what is open and why.":
      "Kies een levering om te zien wat openstaat en waarom.",
    "Choose an authorized company or open company settings.":
      "Kies een toegankelijk bedrijf of open de bedrijfsinstellingen.",
    "Company overview": "Bedrijfsoverzicht",
    "Company unavailable": "Bedrijf niet beschikbaar",
    Conversation: "Gesprek",
    "Customer delivery": "Klantlevering",
    "Daily work": "Dagelijks werk",
    "Data & sources": "Gegevens en bronnen",
    Decisions: "Beslissingen",
    open: "open",
    Commitments: "Toezeggingen",
    "Decisions & control": "Beslissingen en controle",
    "Discuss with Reality": "Bespreken met Reality",
    Explain: "Uitleggen",
    "Inventory at this location": "Voorraad op deze locatie",
    "Latest events": "Nieuwste gebeurtenissen",
    "More workspaces": "Meer werkruimten",
    Navigation: "Navigatie",
    "No document evidence": "Geen documentbewijs",
    "No open commitments": "Geen open toezeggingen",
    "No open deliveries": "Geen open leveringen",
    "No pending decisions": "Geen open beslissingen",
    "Older events": "Oudere gebeurtenissen",
    "One conversation across your business.": "Eén gesprek voor je hele bedrijf.",
    "Open a case to understand the position and its supporting records.":
      "Open een dossier om de stand en onderliggende gegevens te begrijpen.",
    "Open commitments": "Open toezeggingen",
    "Open existing workspace": "Bestaande werkruimte openen",
    "Open practice company": "Oefenbedrijf openen",
    "Original source": "Oorspronkelijke bron",
    "Pending decisions": "Open beslissingen",
    "Review decisions": "Beslissingen beoordelen",
    "Review commitments": "Toezeggingen beoordelen",
    "Review each proposed change before it is recorded.":
      "Beoordeel elke voorgestelde wijziging voordat deze wordt vastgelegd.",
    "Review proposed changes": "Voorgestelde wijzigingen beoordelen",
    Sandbox: "Testomgeving",
    "Thinking…": "Bezig met nadenken…",
    "Unknown party": "Onbekende relatie",
    "What would you like to understand or do?": "Wat wil je begrijpen of doen?",
    "Your business, in focus.": "Je bedrijf in beeld.",
    "Your open work": "Je open werk",
    "Your work": "Je werk",
    "Live simulation": "Live-simulatie",
    "New orders": "Nieuwe orders",
    "New reservations": "Nieuwe reserveringen",
    "Stock movements": "Voorraadbewegingen",
    "Other documents": "Overige documenten",
    "Recorded business activity": "Vastgelegde bedrijfsactiviteit",
    "minutes per bar": "minuten per balk",
    "Activity over time": "Activiteit in de tijd",
    "Recorded activities": "vastgelegde activiteiten",
    "Time range": "Periode",
    "Hover or select a bar to explore what happened.":
      "Wijs een balk aan of selecteer deze om de activiteit te bekijken.",
    "Hatched areas have no observed data. The latest bar is still filling.":
      "Gearceerde gebieden hebben geen waargenomen gegevens. De nieuwste balk is nog onvolledig.",
    "Counts new orders, reservations, stock movements and other documents. Technical processing steps are excluded.":
      "Telt nieuwe orders, reserveringen, voorraadbewegingen en overige documenten. Technische verwerkingsstappen tellen niet mee.",
    "Activity in this interval": "Activiteit in dit interval",
    "No recorded activity in this interval.": "Geen vastgelegde activiteit in dit interval.",
    "Showing the latest 50 matching events. Use all activity for more history.":
      "De laatste 50 overeenkomende gebeurtenissen. Bekijk alle activiteit voor meer geschiedenis.",
    "Your company, in motion": "Uw bedrijf in beweging",
    "Recorded activity · updates every 10 seconds":
      "Vastgelegde activiteit · elke 10 seconden bijgewerkt",
    "View all activity": "Alle activiteit bekijken",
    "Updates paused. Showing the last available activity.":
      "Updates onderbroken. De laatst beschikbare activiteit blijft zichtbaar.",
    "Activity is currently unavailable. We will retry automatically.":
      "Activiteit is momenteel niet beschikbaar. We proberen het automatisch opnieuw.",
    "No activity yet. New records will appear here.":
      "Nog geen activiteit. Nieuwe gegevens verschijnen hier.",
    "System status": "Systeemstatus",
    "Everything is ready": "Alles is gereed",
    "Availability is not fully confirmed": "Beschikbaarheid niet volledig bevestigd",
    Connection: "Verbinding",
    "Automatic scheduling": "Automatische planning",
    "Background processing": "Achtergrondverwerking",
    "Shows service availability. Individual imports and actions have their own results.":
      "Toont de beschikbaarheid van diensten. Afzonderlijke imports en acties hebben eigen resultaten.",
    "Not yet verified": "Nog niet geverifieerd",
    "Currently unavailable": "Momenteel niet beschikbaar",
    "Checking…": "Controleren…",
    "Recent activity": "Recente activiteit",
    Updated: "Bijgewerkt",
    Ready: "Gereed",
    "Company created": "Bedrijf aangemaakt",
    "Company created. Opening your company…": "Bedrijf aangemaakt. Je bedrijf wordt geopend…",
    "Retry opening": "Opnieuw openen",

    "Company name (required)": "Bedrijfsnaam (verplicht)",
    "Choose a name for this company or Sandbox so you can find it later.":
      "Geef dit bedrijf of deze Sandbox een naam zodat je deze later terugvindt.",
    "Enter a company name to continue.": "Vul een bedrijfsnaam in om door te gaan.",

    "Start your own company": "Start je eigen bedrijf",
    "Start empty and add your own data or integrations.":
      "Begin leeg en voeg je eigen gegevens of integraties toe.",
    "Create an empty Sandbox": "Maak een lege Sandbox",
    "Experiment without preset data in a clearly labelled test environment.":
      "Experimenteer zonder vooraf ingevulde gegevens in een duidelijk gemarkeerde testomgeving.",
    "Try demo data": "Probeer demogegevens",
    "Explore international products, warehouses, customers and twelve weeks of order history in a Sandbox.":
      "Verken internationale producten, magazijnen, klanten en twaalf weken ordergeschiedenis in een Sandbox.",
    "How would you like to start?": "Hoe wil je beginnen?",
    "Enable live simulation": "Live-simulatie inschakelen",
    "Receive 60 new demo orders per hour. The demo integration is set up automatically. You can pause it anytime.":
      "Ontvang 60 nieuwe demo-orders per uur. De demo-integratie wordt automatisch ingesteld. Je kunt deze op elk moment pauzeren.",

    "Automatically connect Demo Data and start 60 orders per hour when this company is created. You can pause it anytime in Integrations.":
      "Demogegevens worden bij het aanmaken automatisch verbonden en gestart met 60 orders per uur. Je kunt de simulatie altijd pauzeren bij Integraties.",
    "Manage live simulation": "Live-simulatie beheren",
    "Receive ongoing demo orders": "Doorlopend demo-orders ontvangen",
    "Original source and interpretation": "Oorspronkelijke bron en interpretatie",
    "Receive synthetic orders through the background worker. Connecting does not start arrivals.":
      "Ontvang automatisch synthetische orders. Na het verbinden moet je de instroom uitdrukkelijk starten.",
    "Demo profile and practice cases": "Demoprofiel en oefencases",
    "Comparison periods": "Vergelijkingsperioden",
    "Amounts are booked gross values by currency. Costs and promotions are not provided.":
      "Bedragen zijn geboekte brutowaarden per valuta. Kosten en promoties zijn niet beschikbaar.",
    "Create a separate company with one reservable unit and a blocked case. No reservation is executed during setup.":
      "Maak een apart bedrijf met één reserveerbare eenheid en een geblokkeerde case. Bij het inrichten wordt niets gereserveerd.",
    "Create reservation practice": "Reserveringsoefening aanmaken",
    "Starting data": "Begingegevens",
    "Empty company": "Leeg bedrijf",
    "Start without products, orders or opening stock.":
      "Begin zonder artikelen, orders of beginvoorraad.",
    "International demo company": "Internationaal demobedrijf",
    "16 products, two warehouses, operational cases and twelve weeks of synthetic history. Created as a Sandbox.":
      "16 artikelen, twee magazijnen, operationele voorbeelden en twaalf weken synthetische historie. Wordt als Sandbox aangemaakt.",
    "Company environment": "Bedrijfsomgeving",
    "Ordinary company": "Regulier bedrijf",
    "An empty Sandbox contains no demo records. Its practice environment stays clearly labelled.":
      "Een lege Sandbox bevat geen demogegevens. De oefenomgeving blijft duidelijk herkenbaar.",
    "Your access request has not created a company. Choose how this company should start.":
      "Je toegangsaanvraag heeft nog geen bedrijf aangemaakt. Kies hoe dit bedrijf moet beginnen.",
    "Choose how this company should start.": "Kies hoe dit bedrijf moet beginnen.",
    "Company details and order volume describe your access request. They do not create a company.":
      "Bedrijfsgegevens en ordervolume beschrijven je toegangsaanvraag. Ze maken nog geen bedrijf aan.",
    "Company setup could not be loaded. Reload to retry.":
      "De bedrijfsinrichting kon niet worden geladen. Laad de pagina opnieuw.",
    "Creation could not be confirmed. Retry the same request to recover safely.":
      "Het aanmaken kon niet worden bevestigd. Herhaal dezelfde aanvraag om de status veilig te herstellen.",
    "Keep this request while setup is pending. Retrying will not create another company.":
      "Bewaar deze aanvraag zolang de inrichting loopt. Opnieuw proberen maakt geen extra bedrijf aan.",
    "Retry company setup": "Bedrijfsinrichting opnieuw proberen",
    "New demo orders arrive automatically.": "Nieuwe demo-orders komen automatisch binnen.",
    "New arrivals are paused. Existing orders remain available.":
      "Nieuwe ontvangsten zijn gepauzeerd. Bestaande orders blijven beschikbaar.",
    "Explore your business with synthetic orders.": "Verken je bedrijf met synthetische orders.",
    "Live updates are unavailable. Showing the last known information.":
      "Live-updates zijn niet beschikbaar. De laatst bekende informatie wordt weergegeven.",
    "Imported orders": "Geïmporteerde orders",
    "Next scheduled arrival": "Volgende geplande ontvangst",
    "Latest 25 demo orders. Updates automatically while this page is visible.":
      "De laatste 25 demo-orders. Wordt automatisch bijgewerkt zolang deze pagina zichtbaar is.",
    "Last checked": "Laatst gecontroleerd",
    "Waiting for the first demo order.": "Wachten op de eerste demo-order.",
    "Demo order imported": "Demo-order geïmporteerd",
    "Demo import failed": "Demo-import mislukt",
    "Demo import pending": "Demo-import in behandeling",
    Apply: "Toepassen",
    Loading: "Laden",
    "More options": "Meer opties",
    "Demo Data": "Demogegevens",
    "Demo Data is available in compatible practice companies.":
      "Demogegevens zijn beschikbaar in geschikte oefenbedrijven.",
    "Receive synthetic orders automatically. Connecting does not start arrivals.":
      "Ontvang automatisch synthetische orders. Na het verbinden moet je de instroom uitdrukkelijk starten.",
    "Review demo connection": "Demoverbinding controleren",
    "Only the following missing references will be added. No stock or history is created.":
      "Alleen de volgende ontbrekende stamgegevens worden toegevoegd. Er wordt geen voorraad of historie aangemaakt.",
    "Confirm connection": "Verbinding bevestigen",
    "Confirm Demo Data change": "Wijziging van demogegevens bevestigen",
    "Confirm import retry": "Opnieuw importeren bevestigen",
    "Generated orders": "Aangemaakte orders",
    "Order to cash": "Order tot betaling",
    "Invoices issued": "Uitgegeven facturen",
    "Payments received": "Ontvangen betalingen",
    "Payments allocated": "Toegewezen betalingen",
    "Invoices settled": "Vereffende facturen",
    "Open residuals": "Openstaande restbedragen",
    "Customer credit created": "Ontstaan klanttegoed",
    "Unmatched payments": "Niet toegewezen betalingen",
    "Settlement failures": "Mislukte boekingen",
    "Next settlement": "Volgende boeking",
    "Last settlement": "Laatste boeking",
    "Open payments": "Betalingen openen",
    "Open open items": "Openstaande posten openen",
    "Open journal": "Journaal openen",
    "Differences wait for your decision in Payments.":
      "Verschillen wachten in Betalingen op je beslissing.",
    "Suggested invoices": "Voorgestelde facturen",
    suggested: "voorgesteld",
    "Amount equals the open amount": "Bedrag is gelijk aan het openstaande bedrag",
    "Invoice number appears in the remittance text": "Factuurnummer staat in de omschrijving",
    "Stated reference names this invoice among others":
      "Opgegeven referentie noemt deze factuur naast andere",
    Imported: "Geïmporteerd",
    "Next arrival": "Volgende ontvangst",
    "Last successful import": "Laatste geslaagde import",
    "Orders per hour": "Orders per uur",
    "Refresh status": "Status vernieuwen",
    "Recent demo imports": "Recente demo-imports",
    "Next page": "Volgende pagina",
    "Open order": "Order openen",
    "The change could not be confirmed. Refresh the status before retrying.":
      "De wijziging kon niet worden bevestigd. Vernieuw de status voordat je het opnieuw probeert.",
    "Sandbox — practice environment": "Sandbox — oefenomgeving",
    Start: "Starten",
    "Start simulation": "Simulatie starten",
    Pause: "Pauzeren",
    Resume: "Hervatten",
    Stop: "Stoppen",
    Disconnect: "Verbinding verbreken",
    Reconnect: "Opnieuw verbinden",
    "Change rate": "Tempo wijzigen",
    Stopped: "Gestopt",
    Running: "Actief",
    Paused: "Gepauzeerd",
    Disconnected: "Niet verbonden",
    "Paused: resolve failed imports": "Gepauzeerd: los mislukte imports op",
    "Execution needs attention": "Uitvoering controleren",
    "Not connected": "Niet verbonden",
    completed: "voltooid",
    failed: "mislukt",
    pending: "in behandeling",
    Invoices: "Facturen",
    Warehouse: "Magazijn",
    "Master data": "Stamgegevens",
    "Customer order recorded": "Klantorder vastgelegd",
    "Purchase order recorded": "Inkooporder vastgelegd",
    "Customer invoice recorded": "Klantfactuur vastgelegd",
    "Supplier invoice recorded": "Leveranciersfactuur vastgelegd",
    "Customer credit recorded": "Klantcreditnota vastgelegd",
    "Supplier credit recorded": "Leverancierscreditnota vastgelegd",
    "Customer return received": "Klantretour ontvangen",
    "Stock adjusted": "Voorraad gecorrigeerd",
    "Delivery promise recorded": "Leverbelofte vastgelegd",
    "Delivery promise fulfilled": "Leverbelofte nagekomen",
    "Delivery promise updated": "Leverbelofte gewijzigd",
    "Reservation released": "Reservering vrijgegeven",
    "Reserved stock used": "Gereserveerde voorraad gebruikt",
    "Goods movement recorded": "Goederenbeweging vastgelegd",
    "Business data received": "Bedrijfsgegevens ontvangen",
    "Business data processed": "Bedrijfsgegevens verwerkt",
    "Business change recorded": "Bedrijfswijziging vastgelegd",
    "Business context": "Bedrijfscontext",
    "Current recorded position": "Huidige vastgelegde stand",
    "Business area": "Bedrijfsgebied",
    "All business areas": "Alle bedrijfsgebieden",
    "Customer orders": "Klantorders",
    "Purchase orders": "Inkooporders",
    "Delivery movements": "Leverbewegingen",
    "What happened?": "Wat is er gebeurd?",
    "Counts of recorded orders, shipment/receipt movements and invoices in this sandbox, independent of filters. Movements are not unique deliveries.":
      "Aantallen vastgelegde orders, ontvangsten/verzendingen en facturen, onafhankelijk van filters. Bewegingen zijn geen unieke leveringen.",
    "Data overview": "Gegevensoverzicht",
    "Business commitments": "Verplichtingen",
    "Goods movements": "Goederenbewegingen",
    "Totals scope": "Bereik van totalen",
    "Totals for this sandbox, independent of search and filters.":
      "Totalen voor deze sandbox, onafhankelijk van zoeken en filters.",
    "About transaction groups": "Over transactiegroepen",
    "Groups contain loaded matching events linked by source or correlation, not necessarily the entire order.":
      "Groepen bevatten geladen resultaten met een gedeelde bron of correlatie, niet noodzakelijk de hele order.",
    "Search open items": "Open posten zoeken …",
    "Search deliveries": "Leveringen zoeken …",
    "Reserve stock for customer orders": "Voorraad voor klantorders reserveren",
    "Review overdue customer deliveries": "Achterstallige klantleveringen controleren",
    "Follow up supplier deliveries": "Leveranciersleveringen opvolgen",
    "Review invoicing for shipped goods": "Facturatie van verzonden goederen controleren",
    "Review stock reservations": "Voorraadreserveringen controleren",
    "Follow up customer payments": "Klantbetalingen opvolgen",
    "Review supplier payments": "Leveranciersbetalingen controleren",
    "Review credit for returned goods": "Creditnota voor retourgoederen controleren",
    "Context unavailable": "Context niet beschikbaar",
    "Not reserved": "Nog niet gereserveerd",
    "Review record": "Record controleren",
    "Open notices": "Open meldingen",
    "Back to cockpit": "Terug naar cockpit",
    "Expand chat": "Chat vergroten",
    Table: "Tabel",
    "Sandbox companion": "Sandbox-assistent",
    "Read only": "Alleen lezen",
    "Understand your sandbox, one question at a time.": "Begrijp je sandbox, één vraag tegelijk.",
    "Checking your sandbox…": "Je sandbox wordt gecontroleerd…",
    "What needs attention in this sandbox?": "Wat vraagt aandacht in deze sandbox?",
    "How has my stock changed?": "Hoe is mijn voorraad veranderd?",
    "What do we still need to deliver or receive?": "Wat moeten we nog leveren of ontvangen?",
    "Which invoices are still unpaid?": "Welke facturen staan nog open?",
    "Which business partners and items are available?":
      "Welke relaties en artikelen zijn aanwezig?",
    "Explain the latest recorded change.": "Leg de laatst vastgelegde wijziging uit.",
    "How do Source, Evidence and Reality connect?": "Hoe hangen Source, Evidence en Reality samen?",
    "More questions": "Meer vragen",
    "Show less": "Minder tonen",
    "All exceptions": "Alle uitzonderingen",
    You: "Jij",
    "Ask about your sandbox": "Vraag over je sandbox…",
    "Send question": "Vraag versturen",
    "Uses the managed AI. No bookings or changes.":
      "Met beheerde AI. Geen boekingen of wijzigingen.",
    "The assistant is unavailable. Your question is kept; please try again.":
      "De assistent is niet beschikbaar. Je vraag blijft bewaard; probeer opnieuw.",
    "Individual operations": "Afzonderlijke handelingen",
    "More operations": "Meer handelingen",
    "Open in App": "Openen in de app",
    "Guided examples": "Begeleide voorbeelden",
    "Free operations": "Vrije handelingen",
    "Open work": "Open orders",
    "Create customer order only": "Alleen verkooporder aanmaken",
    "Create supplier order only": "Alleen inkooporder aanmaken",
    "Create orders now. Reserve, ship or receive them later in Open work.":
      "Maak orders aan. Reserveer, lever of ontvang ze later bij Open orders.",
    "Open work could not be loaded.": "Open orders konden niet worden geladen.",
    "Actions create records. These views show their current business effect.":
      "Acties maken records aan. Deze weergaven tonen hun huidige zakelijke effect.",
    "All events": "Alle gebeurtenissen",
    "Allocate goods to the order. Physical stock stays unchanged.":
      "Reserveer goederen voor de order. De fysieke voorraad blijft gelijk.",
    "Business partners": "Zakenpartners",
    "Choose a saved run. Its recorded history remains intact.":
      "Kies een opgeslagen proef. De vastgelegde geschiedenis blijft behouden.",
    "Current projection": "Huidige projectie",
    "Current Reality": "Huidige Reality",
    "Customer order": "Klantorder",
    "Every recorded change, in order": "Alle vastgelegde wijzigingen op volgorde",
    "Execution is unresolved or this step was rejected. Refresh to inspect the server state; no action will be repeated automatically.":
      "De uitvoering is onduidelijk of deze stap is afgewezen. Vernieuw om de serverstatus te bekijken; geen actie wordt automatisch herhaald.",
    "Flight recorder": "Gebeurtenissenlogboek",
    "Goods obligations": "Goederenverplichtingen",
    "Goods owed to us": "Goederen die we nog tegoed hebben",
    "Goods shipped": "Goederen verzonden",
    "Money positions": "Geldposities",
    "Money positions are unavailable.": "Geldposities zijn niet beschikbaar.",
    "Movement recorded": "Movement vastgelegd",
    "No locations": "Geen locaties",
    "No open exceptions.": "Geen open uitzonderingen.",
    "No open goods commitments.": "Geen open goederenverplichtingen.",
    "No Reality events yet.": "Nog geen Reality-gebeurtenissen.",
    "No recorded money position yet.": "Nog geen geboekte geldpositie.",
    "Obligations and exceptions": "Verplichtingen en uitzonderingen",
    "Obligations are unavailable. Refresh to retry.":
      "Verplichtingen zijn niet beschikbaar. Vernieuw om opnieuw te proberen.",
    "Opening stock": "Beginvoorraad",
    "Opening stock recorded": "Beginvoorraad vastgelegd",
    "Operational position": "Operationele situatie",
    "Private learning run": "Privéleerproef",
    "Promise goods to a customer. Stock stays unchanged until shipment.":
      "Zeg goederen toe aan een klant. De voorraad blijft gelijk tot verzending.",
    "Reality is loading. Refresh if it remains unavailable.":
      "Reality wordt geladen. Vernieuw als het niet beschikbaar blijft.",
    "Reality timeline": "Reality-tijdlijn",
    "Reality views": "Reality-weergaven",
    "Record a full or partial delivery. Reality shows what remains owed.":
      "Leg een volledige of gedeeltelijke levering vast. Reality toont wat nog verschuldigd is.",
    "Record opening stock to see the inventory position here.":
      "Leg de beginvoorraad vast om hier de voorraadpositie te zien.",
    "Record what is physically in your warehouse. This creates a Movement.":
      "Leg vast wat fysiek in je magazijn ligt. Dit maakt een Movement aan.",
    "Recorded data": "Vastgelegde gegevens",
    "Recorded events — oldest first": "Vastgelegde gebeurtenissen — oudste eerst",
    "Review each action before confirming.": "Controleer elke actie voordat je bevestigt.",
    "Review this action before changing Reality.":
      "Controleer deze actie voordat Reality verandert.",
    "Sandbox — sample data only": "Sandbox — alleen voorbeeldgegevens",
    Shipment: "Verzending",
    "SKU / Unit": "SKU / Eenheid",
    "Stock by item": "Voorraad per artikel",
    "The preview changed or was stale. The current server preview is loaded; review it and confirm again.":
      "Het voorbeeld is gewijzigd of verouderd. Het actuele servervoorbeeld is geladen; controleer het en bevestig opnieuw.",
    "We owe goods": "Goederen die we nog moeten leveren",
    "Who owes what?": "Wie is wat verschuldigd?",
    "Your first action will appear here. Select an event to inspect its evidence.":
      "Je eerste actie verschijnt hier. Selecteer een gebeurtenis om het bewijs te bekijken.",
    "Financial posting recorded": "Financiële boeking vastgelegd",
    "Payment allocated": "Betaling toegewezen",
    "Record invoice": "Factuur vastleggen",
    "Record and allocate payment": "Betaling vastleggen en toewijzen",
    "Record the invoice total as stated. This creates a receivable, not a payment.":
      "Leg het opgegeven factuurtotaal vast. Dit creëert een vordering, geen betaling.",
    "Record the received payment and allocate it to this invoice. The open amount decreases.":
      "Leg de ontvangen betaling vast en wijs deze toe aan deze factuur. Het openstaande bedrag daalt.",
    "Stated invoice total": "Opgegeven factuurtotaal",
    "Payment amount": "Betalingsbedrag",
    "Payment recorded": "Betaling vastgelegd",
    "Start another operation": "Nog een proces starten",
    "Same sandbox. Existing stock, obligations and history are preserved.":
      "Dezelfde sandbox. Voorraad, verplichtingen en geschiedenis blijven behouden.",
    "Another customer order": "Nog een klantorder",
    "Record additional opening stock": "Extra beginvoorraad vastleggen",
    "Purchasing and returns are not available yet.":
      "Inkoop en retouren zijn nog niet beschikbaar.",
    "Start a fresh sandbox": "Nieuwe sandbox starten",
    "Choose your next operation": "Volgend proces kiezen",
    "Business operations": "Bedrijfsprocessen",
    "Choose what to try. Everything stays in this sandbox.":
      "Wat wil je proberen? Alles blijft in deze sandbox.",
    "Record opening stock": "Beginvoorraad vastleggen",
    "Record existing goods, then choose your next operation.":
      "Leg aanwezige goederen vast en kies daarna het volgende proces.",
    "Sell from stock": "Verkopen uit voorraad",
    "Customer order, reservation and delivery. Use the stock already available.":
      "Klantorder, reservering en levering met de aanwezige voorraad.",
    "Purchase order and goods receipt, including partial deliveries.":
      "Inkooporder en goederenontvangst, ook in delen.",
    "More scenarios — coming later": "Meer scenario's volgen later",
    "Choosing an operation changes nothing. Review and confirm each action separately.":
      "Kiezen verandert niets. Controleer en bevestig elke actie afzonderlijk.",
    "Supplier order": "Inkooporder",
    "Receive goods": "Goederen ontvangen",
    "Record supplier invoice": "Leveranciersfactuur vastleggen",
    "Available inside the sandbox": "Beschikbaar binnen de sandbox",
    "Customer return": "Klantretour",
    "Receive customer return": "Klantretour ontvangen",
    "Record credit note": "Creditnota vastleggen",
    "Refund customer": "Klant terugbetalen",
    "Original shipment": "Oorspronkelijke levering",
    "Stated credit total": "Vermeld creditbedrag",
    "Receive returned goods, record a credit note and refund the customer.":
      "Ontvang retourgoederen, leg een creditnota vast en betaal de klant terug.",
    "A customer return needs a recorded shipment first.":
      "Een klantretour vereist eerst een vastgelegde levering.",
    "Receive goods from a recorded customer shipment. This changes stock, not money.":
      "Ontvang goederen uit een vastgelegde levering. Dit wijzigt de voorraad, niet het geld.",
    "Record the stated credit total for returned goods. No money moves yet.":
      "Leg het vermelde creditbedrag voor retourgoederen vast. Er beweegt nog geen geld.",
    "Record the refund and allocate it to the credit note. The credit balance decreases.":
      "Leg de terugbetaling vast en wijs deze toe aan de creditnota. Het openstaande creditbedrag daalt.",
    "Record supplier payment": "Leveranciersbetaling vastleggen",
    "Purchase order, goods receipt, supplier invoice and payment.":
      "Inkooporder, goederenontvangst, leveranciersfactuur en betaling.",
    "Record the supplier's stated invoice total. This creates a payable; stock stays unchanged.":
      "Leg het factuurtotaal van de leverancier vast. Dit creëert een schuld; de voorraad blijft gelijk.",
    "Record your payment to the supplier and allocate it to this invoice. The payable decreases.":
      "Leg de betaling aan de leverancier vast en wijs deze toe aan de factuur. De openstaande schuld daalt.",
    "Customer returns are being prepared.": "Klantretouren worden voorbereid.",
    "Goods received": "Goederen ontvangen",
    "Order from a supplier": "Bij een leverancier bestellen",
    "Order goods from a supplier. This creates an incoming goods obligation, not stock or a payable.":
      "Bestel bij een leverancier. Dit creëert een leveringsverplichting, geen voorraad of schuld in geld.",
    "Record goods actually received. Stock increases and the supplier's remaining obligation decreases.":
      "Leg de ontvangen goederen vast. De voorraad stijgt en de resterende leveringsverplichting daalt.",
    "Supplier invoices, supplier payments and returns are not available yet.":
      "Leveranciersfacturen, leveranciersbetalingen en retouren volgen later.",
    "Stock → order → reservation → shipment → invoice → payment":
      "Voorraad → order → reservering → verzending → factuur → betaling",
    Sales: "Verkoop",
    Purchasing: "Inkoop",
    Accounting: "Boekhouding",
    "Choose a scenario": "Kies een scenario",
    "New sandbox": "Nieuwe sandbox",
    "Your sandboxes": "Je sandboxes",
    "Saved sandboxes": "Opgeslagen sandboxes",
    "Start a new sandbox or continue in an existing one.":
      "Start een nieuwe sandbox of ga verder in een bestaande.",
    "Choose your operations inside the sandbox. All changes stay in one timeline.":
      "Kies je handelingen in de sandbox. Alle wijzigingen blijven in één tijdlijn.",
    "Show fewer sandboxes": "Minder sandboxes tonen",
    "Show more sandboxes": "Meer sandboxes tonen",
    "Back to current run": "Terug naar huidige proef",
    "One business story. Your actions on the left, their effect in Reality on the right.":
      "Eén bedrijfsverhaal. Links handel je, rechts zie je het effect in Reality.",
    "Try this scenario": "Nu proberen",
    "Not available yet": "Nog niet beschikbaar",
    "Sell, deliver and get paid": "Verkopen, leveren en betaald worden",
    "From a customer promise to goods leaving the warehouse.":
      "Van klantbelofte tot goederenuitgifte.",
    "Available through delivery. Invoice and payment follow later.":
      "Beschikbaar tot levering. Factuur en betaling volgen later.",
    "Deliver part of an order": "Een order gedeeltelijk leveren",
    "Promise twelve, ship five. See the remaining goods obligation.":
      "Beloof twaalf, lever vijf. Bekijk de resterende verplichting.",
    "Opening stock → order → reservation → partial shipment":
      "Beginvoorraad → order → reservering → deellevering",
    "A customer returns goods": "Een klant retourneert goederen",
    "Receive the return, record a credit note and refund the customer.":
      "Ontvang de retour, boek een creditnota en betaal terug.",
    "Buy, receive and pay": "Bestellen, ontvangen en betalen",
    "Order from a supplier, receive goods and settle the invoice.":
      "Bestel bij een leverancier, ontvang goederen en betaal de factuur.",
    "A supplier delivers in parts": "Een leverancier levert in delen",
    "Receive part of a purchase and see what the supplier still owes.":
      "Ontvang een deellevering en zie wat de leverancier nog verschuldigd is.",
    "Record and pay an expense": "Een uitgave boeken en betalen",
    "Follow a simple expense from the original receipt to payment.":
      "Volg een uitgave van origineel bewijs tot betaling.",
    "Correct an incorrect posting": "Een onjuiste boeking corrigeren",
    "Reverse a posting and record its replacement. Preserve the evidence.":
      "Keer een boeking om en boek de vervanging. Bewaar het bewijs.",
    "Your current run will be archived and remain readable. A new private example starts only after confirmation.":
      "Je huidige proef wordt gearchiveerd en blijft leesbaar. Een nieuw voorbeeld start pas na bevestiging.",
    "Starting a scenario is currently unavailable. Your saved runs remain readable.":
      "Je kunt nu geen scenario starten. Opgeslagen proeven blijven leesbaar.",
    "Delivery:": "Bezorging:",
    "Retry delivery": "Bezorging opnieuw proberen",
    "Accept invitation": "Uitnodiging accepteren",
    "Checking invitation…": "Uitnodiging wordt gecontroleerd…",
    "Invited as": "Uitgenodigd als",
    "Join this company": "Lid worden van dit bedrijf",
    "One moment while we check your invitation link.":
      "Een moment, we controleren je uitnodigingslink.",
    "This invitation is no longer valid. Ask a company owner to send you a new one.":
      "Deze uitnodiging is niet meer geldig. Vraag een eigenaar van het bedrijf om een nieuwe.",
    "Your invitation is bound to this address.": "Je uitnodiging is gekoppeld aan dit adres.",
    "Cancel invitation": "Uitnodiging annuleren",
    "Company invitation": "Bedrijfsuitnodiging",
    "Confirm that you want to join this company.":
      "Bevestig dat je lid wilt worden van dit bedrijf.",
    "Invitation unavailable": "Uitnodiging niet beschikbaar",
    "Sign in or create an account with the invited email. Membership is granted only after you accept.":
      "Meld je aan of maak een account met het uitgenodigde e-mailadres. Het lidmaatschap wordt pas verleend nadat je accepteert.",
    "Active members": "Actieve leden",
    Invitations: "Uitnodigingen",
    "Invite a member": "Een lid uitnodigen",
    "Invite member": "Lid uitnodigen",
    "They receive a secure link and join only after explicitly accepting.":
      "De persoon ontvangt een beveiligde link en wordt pas lid na uitdrukkelijke aanvaarding.",
    "name@company.com": "naam@bedrijf.nl",
    "Internal Copilot": "Interne Copilot",
    "Managed by Reality": "Beheerd door Reality",
    "Reality-managed": "Beheerd door Reality",
    "Reality-managed is included. Other providers use your own account.":
      "Reality-managed is inbegrepen. Andere providers gebruiken uw eigen account.",
    "Reality-managed works immediately. You can instead connect a provider account owned by this company.":
      "Reality-managed werkt direct. U kunt in plaats daarvan een provideraccount van dit bedrijf koppelen.",
    "Use own Anthropic key": "Eigen Anthropic-sleutel gebruiken",
    "Use the included server credential.": "De inbegrepen serverreferenties gebruiken.",
    "Usage is billed directly to your Anthropic account.":
      "Het gebruik wordt rechtstreeks via uw Anthropic-account gefactureerd.",
    "Anthropic API key": "Anthropic API-sleutel",
    "Enter Anthropic API key": "Voer de Anthropic API-sleutel in",
    "Anthropic and the economical Claude model are selected centrally. Choose who provides the API credential for this company.":
      "Anthropic en het voordelige Claude-model zijn centraal geselecteerd. Kies wie de API-referenties voor dit bedrijf verstrekt.",
    "Copilot available": "Copilot beschikbaar",
    "Copilot not configured": "Copilot niet geconfigureerd",
    "Reality is preparing an answer": "Reality bereidt een antwoord voor",
    "The AI provider and model are operated centrally. Company data remains tenant-scoped, and Copilot can only use registered read and proposal tools.":
      "De AI-provider en het model worden centraal beheerd. Bedrijfsgegevens blijven tenantspecifiek en Copilot kan alleen geregistreerde lees- en voorsteltools gebruiken.",
    "Inviting…": "Uitnodiging wordt verstuurd…",
    "Loading members…": "Leden worden geladen…",
    "Manage access for this company. Only owners can invite or remove members.":
      "Beheer de toegang tot dit bedrijf. Alleen eigenaren kunnen leden uitnodigen of verwijderen.",
    Members: "Leden",
    "No active members.": "Geen actieve leden.",
    "No invitations.": "Geen uitnodigingen.",
    Remove: "Verwijderen",
    Resend: "Opnieuw verzenden",
    All: "Alles",
    "Close activity": "Activiteit sluiten",
    "Load older activity": "Oudere activiteit laden",
    "New business events will appear here.": "Nieuwe bedrijfsgebeurtenissen verschijnen hier.",
    "Open activity": "Activiteit openen",
    "Operational core": "Operationele kern",
    "Reality activity": "Reality-activiteit",
    "Tenant-scoped operational and financial events.":
      "Operationele en financiële gebeurtenissen van dit bedrijf.",
    "What happened": "Wat is er gebeurd?",
    "Company Overview": "Bedrijfsoverzicht",
    "Company-wide control": "Bedrijfsbrede besturing",
    "Order Operations": "Orderbeheer",
    "Warehouse Operations": "Magazijnbeheer",
    "Finance Control": "Financiële controle",
    "Data Management": "Gegevensbeheer",
    "My area": "Mijn gebied",
    Views: "Weergaven",
    Actions: "Acties",
    "Workspace navigation unavailable": "Gebiedsnavigatie niet beschikbaar",
    "Review action": "Actie controleren",
    "Confirm action": "Actie bevestigen",
    "Reserve stock": "Voorraad reserveren",
    "Record movement": "Beweging registreren",
    "Correct movement": "Beweging corrigeren",
    "Hold or release commitment": "Verplichting blokkeren of vrijgeven",
    "Hold or release document commitments": "Documentverplichtingen blokkeren of vrijgeven",
    "Set or release party delivery hold": "Leveringsblokkade voor partij instellen of opheffen",
    "More actions": "Meer acties",
    "All actions": "Alle acties",
    "Search actions": "Acties zoeken",
    "No actions found": "Geen acties gevonden",
    "More views": "Meer weergaven",
    "All views": "Alle weergaven",
    "Search views": "Weergaven zoeken",
    "No views found": "Geen weergaven gevonden",
    "Warehouse Queue": "Magazijnwachtrij",
    "Supply & demand": "Aanbod & vraag",
    "Search this view…": "Deze weergave doorzoeken…",
    "View unavailable": "Weergave niet beschikbaar",
    "No projection rows yet": "Nog geen gegevens voor deze weergave",
    "This view will populate when matching business Reality exists.":
      "Deze weergave wordt gevuld zodra passende bedrijfsgegevens in Reality bestaan.",
    "Change or clear your search.": "Wijzig of wis uw zoekopdracht.",
    "No results found": "Geen resultaten gevonden",
    Pagination: "Paginering",
    Previous: "Vorige",
    Page: "Pagina",
    Next: "Volgende",
    results: "resultaten",
    "Order & Warehouse Operations": "Order- en magazijnbeheer",
    "Customer orders with readiness, due dates and execution blockers":
      "Klantorders met gereedheid, vervaldata en uitvoeringsblokkades",
    "Orders prioritized for warehouse execution and shipment readiness":
      "Orders geprioriteerd voor magazijnuitvoering en verzendgereedheid",
    "Commitment shortages and active execution holds blocking fulfillment":
      "Tekorten en actieve uitvoeringsblokkades die fulfillment verhinderen",
    "Item-level physical stock, incoming supply and uncovered customer demand":
      "Fysieke voorraad, inkomend aanbod en ongedekte klantvraag per artikel",
    "Customer orders with readiness, due dates and the blockers that explain execution.":
      "Klantorders met gereedheid, vervaldata en blokkades die de uitvoering verklaren.",
    "Orders prioritized for warehouse execution with shipment readiness explained.":
      "Voor magazijnuitvoering geprioriteerde orders met verklaarde verzendgereedheid.",
    "Shortages and active execution holds that currently block fulfillment.":
      "Tekorten en actieve uitvoeringsblokkades die fulfillment momenteel verhinderen.",
    "Physical stock, incoming supply and uncovered customer demand by item.":
      "Fysieke voorraad, inkomend aanbod en ongedekte klantvraag per artikel.",
    "Create manual sales or purchase order": "Handmatige verkoop- of inkooporder maken",
    "Observe source-supported fact": "Brongestuurd feit vastleggen",
    "Post customer payment": "Klantbetaling boeken",
    "Post supplier payment": "Leveranciersbetaling boeken",
    "Order lines": "Orderregels",
    Line: "Regel",
    "Add line": "Regel toevoegen",
    "Remove line": "Regel verwijderen",
    "Unit price": "Eenheidsprijs",
    "Promised at": "Toegezegd op",
    "Create handling unit": "Logistieke eenheid aanmaken",
    "Create lot": "Partij aanmaken",
    "Create serial unit": "Seriële eenheid aanmaken",
    Hold: "Blokkeren",
    Release: "Vrijgeven",
    "Ask Reality": "Vraag Reality",
    Home: "Start",
    Exceptions: "Uitzonderingen",
    Inventory: "Voorraad",
    Documents: "Documenten",
    Activity: "Activiteit",
    "new attention event": "nieuwe activiteit die aandacht vereist",
    "new attention events": "nieuwe activiteiten die aandacht vereisen",
    "Open Activity to review": "Activiteit openen om te controleren",
    Payments: "Betalingen",
    Parties: "Relaties",
    Items: "Artikelen",
    Locations: "Locaties",
    Sources: "Bronnen",
    "Open items": "Openstaande posten",
    "Profile & preferences": "Profiel & voorkeuren",
    "Account settings": "Accountinstellingen",
    Language: "Taal",
    "Number & date format": "Getal- & datumformaat",
    "Display timezone": "Weergavetijdzone",
    "Save preferences": "Voorkeuren opslaan",
    "Preferences saved": "Voorkeuren opgeslagen",
    "Saving…": "Opslaan…",
    "Needs attention": "Aandacht nodig",
    Completed: "Voltooid",
    "Technical details": "Technische details",
    "Event type": "Gebeurtenistype",
    Subject: "Onderwerp",
    Correlation: "Procesverband",
    Companies: "Bedrijven",
    "Sign out": "Uitloggen",
    Settings: "Instellingen",
    General: "Algemeen",
    Data: "Gegevens",
    Agents: "Agenten",
    Company: "Bedrijf",
    Status: "Status",
    "Company settings": "Bedrijfsinstellingen",
    "New company": "Nieuw bedrijf",
    Archive: "Archiveren",
    "Archive company": "Bedrijf archiveren",
    Archived: "Gearchiveerd",
    "Company & settings": "Bedrijf & instellingen",
    Profile: "Profiel",
    "Sources & intake": "Bronnen & invoer",
    Processing: "Verwerking",
    "Reference data": "Referentiegegevens",
    Explorer: "Verkenner",
    Copilot: "Copilot",
    "MCP server": "MCP-server",
    "Company details": "Bedrijfsgegevens",
    "Default currency": "Standaardvaluta",
    Timeline: "Tijdlijn",
    "Live activity": "Live-activiteit",
    "Events today": "Gebeurtenissen vandaag",
    "Orders processed": "Verwerkte orders",
    Physical: "Fysiek",
    Reserved: "Gereserveerd",
    Available: "Beschikbaar",
    Incoming: "Inkomend",
    Projected: "Verwacht",
    Risk: "Risico",
    "Due date": "Vervaldatum",
    Flow: "Stroom",
    Counterparty: "Tegenpartij",
    Item: "Artikel",
    Review: "Controleren",
    Date: "Datum",
    Document: "Document",
    Party: "Relatie",
    Amount: "Bedrag",
    Total: "Totaal",
    State: "Status",
    Type: "Type",
    Records: "Records",
    Cancel: "Annuleren",
    Confirm: "Bevestigen",
    Close: "Sluiten",
    Edit: "Bewerken",
    Add: "Toevoegen",
    Search: "Zoeken",
    "Use the owning Reality correction workflow for economic line changes.":
      "Gebruik voor economische regelwijzigingen de bijbehorende Reality-correctieworkflow.",
    "New party": "Nieuwe relatie",
    "Search parties…": "Relaties zoeken…",
    Name: "Naam",
    Role: "Rol",
    "Source / identity": "Bron / identiteit",
    "Manual / internal": "Handmatig / intern",
    Supplier: "Leverancier",
    Customer: "Klant",
  },
  es: {
    "Choose company": "Elegir empresa",
    "Open company chat": "Abrir chat de la empresa",
    "Sandbox with sample data": "Sandbox con datos de ejemplo",
    "Open Free Play Sandbox": "Abrir Sandbox de juego libre",
    "Choose an existing company or create a Sandbox with sample data.":
      "Elige una empresa existente o crea una Sandbox con datos de ejemplo.",
    "You are working with this company's real data. Changes require confirmation.":
      "Trabajas con los datos reales de esta empresa. Los cambios requieren confirmación.",

    "Explore Reality": "Explora Reality",
    "Choose a storyline or Free Play.": "Elige una historia o juego libre.",
    "Explore freely in your own Sandbox with sample data.":
      "Explora libremente en tu propio Sandbox con datos de ejemplo.",
    "Create Sandbox and start": "Crear Sandbox y empezar",
    "Sandbox setup is not ready. Try again.": "El Sandbox aún no está listo. Inténtalo de nuevo.",
    "This Sandbox is archived. Restore it under Companies.":
      "Este Sandbox está archivado. Restáuralo en Empresas.",
    "Sandbox chat": "Chat del Sandbox",
    "Calls for this reply": "Llamadas de esta respuesta",
    "No tool calls were recorded for this reply.":
      "No se registraron llamadas a herramientas para esta respuesta.",
    "Recorded evidence is unavailable for this reply.":
      "No hay evidencia registrada disponible para esta respuesta.",
    "Some recorded calls are not included in this view.":
      "Algunas llamadas registradas no se incluyen en esta vista.",
    "Changes since this call": "Cambios desde esta llamada",
    "Changes since this call can include later activity in this Sandbox.":
      "Los cambios desde esta llamada pueden incluir actividad posterior en este Sandbox.",
    "Live simulation supports empty and standard demo Sandbox setups. Storyline Sandboxes use a different data setup that is not yet supported.":
      "La simulación en vivo admite Sandboxes vacíos y de demostración estándar. Los Sandboxes de Storyline usan una estructura de datos diferente que aún no se admite.",
    "Live simulation is not available in this Sandbox.":
      "La simulación en vivo no está disponible en este Sandbox.",
    "Create an empty Sandbox under Companies → New company, then enable live simulation there. No historical demo data is needed.":
      "Crea un Sandbox vacío en Empresas → Nueva empresa y activa allí la simulación en vivo. No se necesitan datos históricos de demostración.",

    "Create a separate demo Sandbox for live simulation. Your existing company and Storyline stay unchanged.":
      "Crea un Sandbox de demostración separado para la simulación en vivo. Tu empresa y Storyline actuales no cambian.",
    "Create demo Sandbox": "Crear Sandbox de demostración",

    "Preparing your company": "Preparando tu empresa",
    "Continue company setup": "Continuar la configuración",
    "Your setup is saved. Continue with the same company.":
      "Tu configuración está guardada. Continúa con la misma empresa.",
    "Enter the six-digit code from your verification email.":
      "Introduce el código de seis dígitos de tu correo de verificación.",
    "If this address needs verification, a new code has been sent.":
      "Si esta dirección necesita verificación, se ha enviado un nuevo código.",
    "Sending code\u2026": "Enviando código…",
    "Send a new code": "Enviar un código nuevo",

    "Loading your access": "Cargando tu acceso",
    "Please wait. You will continue automatically.":
      "Espera un momento. Continuarás automáticamente.",
    "Loading your workspace": "Cargando tu espacio de trabajo",
    "Verifying your email": "Verificando tu correo electrónico",

    "Try for free": "Probar gratis",
    "Your own demo company. No credit card. No automatic paid subscription.":
      "Tu propia empresa de demostración. Sin tarjeta de crédito. Sin suscripción de pago automática.",
    "Try the Playground for free with your own demo company. No credit card. No automatic paid subscription.":
      "Prueba gratis el Playground con tu propia empresa de demostración. Sin tarjeta de crédito. Sin suscripción de pago automática.",
    "Try Reality for free with your own demo company. No credit card. No automatic paid subscription.":
      "Prueba Reality gratis con tu propia empresa de demostración. Sin tarjeta de crédito. Sin suscripción de pago automática.",
    "By continuing, you request a demo company with live sample data after email verification.":
      "Al continuar, solicitas una empresa de demostración con datos de ejemplo continuos tras verificar tu correo.",
    "Your demo is not ready yet. Retry to continue with the same company.":
      "Tu demostración aún no está lista. Reintenta para continuar con la misma empresa.",
    "Preparing your demo company": "Preparando tu empresa de demostración",
    "Orders, deliveries and invoices are being prepared for you to explore.":
      "Se están preparando pedidos, entregas y facturas para que los explores.",
    "Try these three questions": "Empieza con estas tres preguntas",
    "Explore the records directly. These tasks use no AI questions.":
      "Explora los registros directamente. Estas tareas no consumen preguntas de IA.",
    "Which orders need attention?": "¿Qué pedidos necesitan atención?",
    "Why is this order not fully delivered?":
      "¿Por qué este pedido no se ha entregado por completo?",
    "Which invoices remain open?": "¿Qué facturas siguen pendientes?",
    "Was that useful? Support Reality with a star on GitHub.":
      "¿Te resultó útil? Apoya a Reality con una estrella en GitHub.",
    "Star on GitHub": "Dar una estrella en GitHub",
    "Keep exploring": "Seguir explorando",
    "Free AI questions remaining": "Preguntas de IA gratuitas restantes",
    "Resets at": "Se renueva el",
    "Your daily AI allowance is used. Keep exploring the records or return after the reset.":
      "Has agotado tu cupo diario de IA. Sigue explorando los registros o vuelve cuando se renueve.",

    "No admission limit": "Sin límite de admisión",
    "Manual approval required": "Se requiere aprobación manual",
    "Create your account and verify your email to continue.":
      "Crea tu cuenta y verifica tu correo electrónico para continuar.",
    "Admission follows your deployment settings. Review pending applications here.":
      "El acceso sigue la configuración de tu despliegue. Revisa aquí las solicitudes pendientes.",
    "Reset filters": "Restablecer filtros",
    "No entries yet.": "Todavía no hay registros.",
    "No entries yet. Use the create action to add the first entry.":
      "Todavía no hay registros. Usa el botón de creación para añadir el primero.",
    "Set up the accounts and tax codes used by your external bookkeeping software, then define how Reality assigns them.":
      "Configura las cuentas y los códigos fiscales de tu software contable externo y define cómo los asigna Reality.",
    "Selected accounting target": "Contabilidad externa seleccionada",
    "Back to accounting targets": "Volver a los sistemas contables",
    "Open account setup": "Abrir configuración de cuentas",
    "Add your external bookkeeping system here. Open its account setup to maintain accounts, tax codes and assignment rules.":
      "Añade aquí tu sistema contable externo. Abre su configuración para gestionar cuentas, códigos fiscales y reglas de asignación.",
    "Add the account numbers used in this bookkeeping system. Rules can then assign transactions to these accounts.":
      "Añade los números de cuenta de este sistema contable. Después podrás asignar operaciones a estas cuentas mediante reglas.",
    "Add the tax codes used in this bookkeeping system. You can select them when defining assignment rules.":
      "Añade los códigos fiscales de este sistema contable. Podrás seleccionarlos al definir las reglas de asignación.",
    "Define which external account and tax code a transaction should use. Add the required accounts and tax codes first.":
      "Define qué cuenta externa y código fiscal debe usar una operación. Añade primero las cuentas y los códigos fiscales necesarios.",
    "No accounting targets yet.": "Todavía no hay sistemas contables.",
    "No external accounts yet.": "Todavía no hay cuentas externas.",
    "No tax codes yet.": "Todavía no hay códigos fiscales.",
    "No assignment rules yet.": "Todavía no hay reglas de asignación.",

    "Set up standard accounts": "Configurar cuentas predeterminadas",
    "These defaults apply to new transactions. Linked payments and corrections can retain the accounts of the original invoice.":
      "Estas cuentas predeterminadas se aplican a operaciones nuevas. Los pagos y correcciones vinculados pueden conservar las cuentas de la factura original.",
    "Add account": "Añadir cuenta",
    "View account usage": "Ver uso de cuentas",
    "Accounts for business transactions": "Cuentas por operación",
    "Change default": "Cambiar predeterminada",
    "Change default account": "Cambiar cuenta predeterminada",
    "Back to accounts": "Volver a las cuentas",
    "Choose the accounts Reality uses for receivables, payables, payments and settlement differences.":
      "Define las cuentas que Reality usa para cobros, deudas, pagos y diferencias de liquidación.",
    "Default means Reality selects this account automatically for its role. External ledger numbers are managed under External accounting.":
      "Predeterminada significa que Reality elige esta cuenta automáticamente para su función. Los números del libro mayor externo se gestionan en Contabilidad externa.",
    "See which operational accounts each transaction uses. Change a role default when future transactions should use a different account.":
      "Consulta qué cuentas operativas usa cada operación. Cambia la cuenta predeterminada de una función para las operaciones futuras.",
    "This default applies to every transaction using this account role. Existing postings keep their original accounts.":
      "Esta cuenta predeterminada se aplica a todas las operaciones con esta función. Los asientos existentes conservan sus cuentas originales.",
    "Add an active account with this role before changing the default.":
      "Añade primero una cuenta activa con esta función antes de cambiar la predeterminada.",
    "All fields are required unless marked optional.":
      "Todos los campos son obligatorios salvo los marcados como opcionales.",
    "A prepared change is waiting for your confirmation.":
      "Un cambio preparado espera tu confirmación.",
    "Continue review": "Continuar revisión",
    "Edit account": "Editar cuenta",
    "Review account change": "Revisar cambio de cuenta",
    "Create cost center": "Crear centro de costes",
    "Edit cost center": "Editar centro de costes",
    "Create case code": "Crear código de caso",
    "Edit case code": "Editar código de caso",
    "Create coding group": "Crear grupo de contabilización",
    "Edit coding group": "Editar grupo de contabilización",
    "Create accounting target": "Crear destino contable",
    "Edit accounting target": "Editar destino contable",
    "Create external account": "Crear cuenta externa",
    "Edit external account": "Editar cuenta externa",
    "Create tax code": "Crear código fiscal",
    "Edit tax code": "Editar código fiscal",
    "Create mapping rule": "Crear regla de asignación",
    "Edit mapping rule": "Editar regla de asignación",
    "Search by code or name": "Buscar por código o nombre",
    "Target identifier": "Identificador del destino",
    "Coding group condition": "Condición del grupo contable",
    "No coding group condition": "Sin condición de grupo contable",
    "Check the proposed values. The change takes effect only after confirmation.":
      "Revisa los valores propuestos. El cambio solo se aplica tras confirmarlo.",
    "The account role determines which operational transactions can use this account. External ledger numbers are configured under External accounting.":
      "La función determina qué operaciones pueden usar esta cuenta. Los números contables externos se configuran en Contabilidad externa.",
    "The role is fixed after creation. The default account is used when a transaction does not specify another eligible account.":
      "La función queda fija al crear la cuenta. Se usa la cuenta predeterminada si la operación no indica otra cuenta permitida.",
    "Use a short, unique code and a recognizable name. The code cannot be changed after creation.":
      "Usa un código breve y único y un nombre reconocible. El código no se puede cambiar después.",
    "Identify the department, location or project receiving the cost, for example SALES or BERLIN. Codes remain permanent.":
      "Identifica el departamento, lugar o proyecto al que se asignan los costes, por ejemplo VENTAS o BERLIN. Los códigos son permanentes.",
    "Define a business case such as domestic sales or export. A case code is a declared classification, not an automatic tax calculation.":
      "Define un caso como venta nacional o exportación. El código declara una clasificación y no calcula impuestos.",
    "Group products or services that need the same account mapping. A rule can require an exact coding group.":
      "Agrupa productos o servicios con la misma asignación contable. Una regla puede exigir un grupo concreto.",
    "Choose the source system and its original code, then the internal case code or coding group it means.":
      "Elige el sistema de origen y su código original y asigna el código de caso o grupo contable interno correspondiente.",
    "The source namespace groups codes from the same source, for example a tax-code list. Copy namespace and code exactly as received.":
      "El espacio de nombres agrupa códigos del mismo origen, por ejemplo una lista fiscal. Copia el espacio y el código exactamente como se reciben.",
    "Choose when this rule applies and which external account it selects. All conditions must match exactly.":
      "Define cuándo se aplica la regla y qué cuenta externa selecciona. Todas las condiciones deben coincidir exactamente.",
    "Enter the code and name used by your external accounting software.":
      "Introduce el código y el nombre de tu programa de contabilidad externo.",
    "Explain why you are adding or changing this entry. This note is retained in its history.":
      "Explica por qué añades o modificas esta entrada. La nota se conserva en el historial.",
    "Assignment belongs to an earlier evidence version":
      "La asignación corresponde a una versión anterior del documento",
    "Internal assignment": "Asignación interna",
    "Account settings areas": "Secciones de ajustes de cuentas",
    "Accounting target": "Destino contable",
    "Accounting targets": "Destinos contables",
    "Define permitted external destinations. Local balances remain independent.":
      "Define destinos externos permitidos. Los saldos locales permanecen independientes.",
    "Edit configuration": "Editar configuración",
    "New configuration": "Nueva configuración",
    "Exact coding group": "Grupo de imputación exacto",
    "External account": "Cuenta externa",
    "External accounts": "Cuentas externas",
    "External accounting": "Contabilidad externa",
    "External accounting areas": "Secciones de contabilidad externa",
    "Gross operational account references": "Referencias de cuentas operativas con importes brutos",
    "Group discrimination": "Distinción por grupo",
    "Mapping history": "Historial de asignaciones",
    "Mapping preview": "Vista previa de asignaciones",
    "Mapping revision": "Versión de asignación",
    "Mapping scope": "Ámbito de asignación",
    Namespace: "Espacio de nombres",
    "Operational account": "Cuenta operativa",
    "Received components": "Componentes recibidos",
    "Review configuration": "Revisar configuración",
    "Shows external destinations, not export completeness or external posting.":
      "Muestra destinos externos. No confirma la integridad de la exportación ni la contabilización externa.",
    "Tax code": "Código fiscal",
    "Tax codes": "Códigos fiscales",
    Transaction: "Operación",
    "Without group discrimination": "Sin distinción por grupo",
    "Mapping resolved": "Asignación encontrada",
    "A declared case is required": "Falta un código de caso declarado",
    "A coding group is required": "Falta un grupo de imputación",
    "No matching target rule": "No hay una regla de destino coincidente",
    "Multiple target rules match": "Coinciden varias reglas de destino",
    "Accounting target is blocked": "El destino contable está bloqueado",
    "External destination is blocked": "El destino externo está bloqueado",
    "Operational account is blocked": "La cuenta operativa está bloqueada",
    "Source and internal case conflict": "Conflicto entre el caso de origen y el interno",
    "Source and internal group conflict": "Conflicto entre el grupo de origen y el interno",
    "Classification needs review": "La clasificación requiere revisión",
    "Transaction matrix": "Matriz de operaciones",
    Configured: "Configurado",
    "Missing default": "Falta cuenta predeterminada",
    "Incompatible account role": "Función de cuenta incompatible",
    "Configured default accounts": "Cuentas predeterminadas configuradas",
    "Original control account when linked":
      "Al vincular, se conserva la cuenta de control original",
    "Original invoice account required": "Se requiere la cuenta original de la factura",
    "These are current defaults. The action preview validates the actual evidence and accounts.":
      "Estas son las cuentas predeterminadas actuales. La vista previa de la acción valida los documentos y las cuentas concretos.",
    "Reversals retain original accounts and reverse the original group.":
      "Las anulaciones conservan las cuentas originales e invierten el grupo de asientos original.",
    "Orders, reservations, stock movements and allocations do not add postings here.":
      "Los pedidos, las reservas, los movimientos de existencias y las asignaciones no añaden asientos aquí.",
    "Configure accounts": "Configurar cuentas",
    "Amount basis": "Base del importe",
    "Stated invoice gross": "Importe bruto declarado de la factura",
    "Stated payment amount": "Importe declarado del pago",
    "Stated refund amount": "Importe declarado del reembolso",
    "Explicitly accepted reduction": "Reducción aceptada expresamente",
    "Stated opening residual": "Saldo residual inicial declarado",
    "Customer settlement reduction": "Reducción aceptada del cliente",
    "Supplier settlement reduction": "Reducción aceptada del proveedor",
    "Opening customer debt": "Saldo inicial a cobrar del cliente",
    "Opening customer credit": "Saldo inicial a favor del cliente",
    "Opening supplier debt": "Saldo inicial a pagar al proveedor",
    "Opening supplier credit": "Saldo inicial a favor con el proveedor",
    "Sales invoice": "Factura de venta",
    "Customer credit note": "Nota de crédito del cliente",
    "Customer payment": "Pago del cliente",
    "Customer refund": "Reembolso al cliente",
    "Supplier invoice": "Factura del proveedor",
    "Supplier credit note": "Nota de crédito del proveedor",
    "Supplier payment": "Pago al proveedor",
    "Supplier refund": "Reembolso del proveedor",
    "Add cost-center share": "Añadir parte por centro de costes",
    "Assign individual lines. The document summary is not added again.":
      "Asigna líneas individuales. El total del documento no se suma de nuevo.",
    Assigned: "Asignado",
    "Attribution basis": "Base de asignación",
    "Attribution history": "Historial de asignaciones",
    "Attribution saved": "Asignación guardada",
    "Case code": "Código de caso",
    "Clear internal attribution": "Vaciar asignación interna",
    "Coding group": "Grupo de contabilización",
    Components: "Componentes",
    "Confirm attribution": "Confirmar asignación",
    "Cost center": "Centro de costes",
    "Current attribution": "Asignación actual",
    "Enter explicit shares. Empty shares leave the amount unassigned.":
      "Introduce importes explícitos. Sin partes, el importe queda sin asignar.",
    "Financial detail": "Detalle financiero",
    "Find classification references": "Buscar valores de clasificación",
    "Inspect document": "Inspeccionar documento",
    "Inspect line": "Inspeccionar línea",
    "Internal attribution": "Asignación interna",
    "No internal attribution": "Sin asignación interna",
    "Original source codes": "Códigos originales de la fuente",
    "Received component": "Componente recibido",
    "Received document summary": "Totales recibidos del documento",
    "Refine the reference search to find more entries.":
      "Refina la búsqueda para encontrar más entradas.",
    "Remove share": "Eliminar parte",
    "Review attribution": "Revisar asignación",
    "Select cost center": "Seleccionar centro de costes",
    "Select financial component": "Seleccionar componente financiero",
    "Share amount": "Importe de la parte",
    "This document has no lines. Attribution uses its received amounts.":
      "Este documento no tiene líneas. La asignación utiliza sus importes recibidos.",
    Unassigned: "Sin asignar",
    "Other received basis": "Otra base recibida",
    "Inspect financial detail": "Inspeccionar detalle financiero",
    "See open commitments, exceptions and decisions across your company.":
      "Consulta los compromisos, excepciones y decisiones pendientes de tu empresa.",
    "Track outstanding deliveries to your customers.":
      "Sigue las entregas pendientes a tus clientes.",
    "Track outstanding deliveries from your suppliers.":
      "Sigue las entregas pendientes de tus proveedores.",
    "Review issues that need attention and inspect the records behind them.":
      "Revisa las incidencias y consulta los registros que las explican.",
    "Review proposed actions and decide whether to proceed.":
      "Revisa las acciones propuestas y decide si deben ejecutarse.",
    "See physical, reserved and available stock for each item.":
      "Consulta las existencias físicas, reservadas y disponibles por artículo.",
    "See which stock is reserved for each commitment.":
      "Consulta las existencias reservadas para cada compromiso.",
    "Follow recorded stock receipts, shipments and adjustments.":
      "Consulta las entradas, salidas y ajustes de existencias registrados.",
    "See outstanding receivables and payables, grouped by currency.":
      "Consulta las cuentas pendientes de cobro y pago, agrupadas por moneda.",
    "Review recorded incoming and outgoing payments.": "Revisa los cobros y pagos registrados.",
    "Inspect recorded ledger entries and their supporting records.":
      "Consulta los asientos contables y los registros que los respaldan.",
    "Follow how sources, documents and business records connect over time.":
      "Sigue cómo se relacionan las fuentes, los documentos y los registros a lo largo del tiempo.",
    "Explore a record and follow its links to related information.":
      "Explora un registro y sus enlaces a información relacionada.",
    "Explore your company’s recorded information and trace it to its sources.":
      "Explora la información registrada de tu empresa y rastrea sus fuentes.",
    "Explore how existing records are combined into calculated views.":
      "Descubre cómo se combinan los registros existentes en vistas calculadas.",
    "Review the rules that record additional facts from source data on the right business record.":
      "Revisa las reglas que registran hechos adicionales a partir de los datos de origen en el registro de negocio correcto.",
    "Explore the conditions that identify issues requiring attention.":
      "Consulta las condiciones que detectan incidencias que requieren atención.",
    "See what was recorded across your company, newest first.":
      "Consulta lo registrado en tu empresa, de más reciente a más antiguo.",
    "Explore available actions, their inputs and what they do.":
      "Explora las acciones disponibles, sus datos de entrada y sus efectos.",
    "Explore additional observations, their sources and the records they describe.":
      "Explora las observaciones adicionales, sus fuentes y los registros que describen.",
    "Track delivery commitments and inspect their reservations and movements.":
      "Sigue los compromisos de entrega y consulta sus reservas y movimientos.",
    "Review customer orders and follow their linked delivery commitments.":
      "Revisa los pedidos de clientes y sus compromisos de entrega vinculados.",
    "Review purchase orders and follow their linked delivery commitments.":
      "Revisa los pedidos a proveedores y sus compromisos de entrega vinculados.",
    "Find customers and review their details and commercial defaults.":
      "Busca clientes y consulta sus datos y condiciones comerciales predeterminadas.",
    "Find suppliers and review their details and commercial defaults.":
      "Busca proveedores y consulta sus datos y condiciones comerciales predeterminadas.",
    "Find items and review their reference details.":
      "Busca artículos y consulta sus datos maestros.",
    "Find locations and review their reference details.":
      "Busca ubicaciones y consulta sus datos maestros.",
    "Plan integrations and manage registered data sources.":
      "Planifica integraciones y gestiona las fuentes de datos registradas.",
    "Inspect received data, its import status and linked business records.":
      "Consulta los datos recibidos, su estado de importación y los registros vinculados.",
    "Inspect recorded documents and trace them to their original sources.":
      "Consulta los documentos registrados y rastrea sus fuentes originales.",
    "Explore the current delivery position and the recorded activity behind it.":
      "Analiza la situación actual de las entregas y la actividad registrada que la explica.",
    "Switch companies or manage their users, agents and AI settings.":
      "Cambia de empresa o gestiona sus usuarios, agentes y ajustes de IA.",
    "Set your language, number format, timezone and appearance.":
      "Configura el idioma, el formato numérico, la zona horaria y la apariencia.",
    "Control synthetic data arrivals and review recent demo activity.":
      "Controla la llegada de datos sintéticos y consulta la actividad reciente de la demo.",
    "Demo company": "Empresa de demostración",
    "View data": "Datos de la vista",
    "Graph starting points": "Puntos de partida del grafo",
    "Starting point": "Punto de partida",
    "No records are available for this starting point yet.":
      "Todavía no hay registros disponibles para este punto de partida.",
    "Choose a starting point or search for a record.":
      "Elige un punto de partida o busca un registro.",
    Order: "Pedido",
    Fact: "Hecho",
    Columns: "Columnas",
    "Compact rows": "Filas compactas",
    "Filter records": "Filtrar registros",
    Observation: "Observación",
    "Reset table": "Restablecer tabla",
    "Resize column": "Cambiar ancho de columna",
    "Rows per page": "Filas por página",
    "Scrollable register": "Tabla desplazable",
    "Sort column": "Ordenar columna",
    "All subject types": "Todos los tipos de sujeto",
    "An observation is not a current-state guarantee. Different observations can coexist; this view does not choose a winning value.":
      "Una observación no garantiza el estado actual. Pueden coexistir distintas observaciones; esta vista no elige un valor definitivo.",
    "Clear filters": "Borrar filtros",
    "Exact predicate": "Predicado exacto",
    "Explain observation": "Explicar observación",
    "Explore recorded observations about your business. Each observation keeps its own value, time and origin.":
      "Explora las observaciones registradas de tu empresa. Cada una conserva su valor, momento y origen.",
    "Fact ID": "ID de hecho",
    "Interpretation rule": "Regla de interpretación",
    "No linked source recorded": "No hay fuente vinculada registrada",
    "No observations found": "No se encontraron observaciones",
    "Predicate, value, subject ID or source reference":
      "Predicado, valor, ID de sujeto o referencia de fuente",
    "Related observations": "Observaciones relacionadas",
    "Search observations": "Buscar observaciones",
    "Shipping priority": "Prioridad de envío",
    "Source record ID": "ID de registro fuente",
    "Subject ID": "ID de sujeto",
    "Subject type": "Tipo de sujeto",
    "The first 100 subject types are listed. Search can find observations of other types.":
      "Se muestran los primeros 100 tipos de sujeto. La búsqueda permite encontrar observaciones de otros tipos.",
    "Try another search or clear the filters. Facts appear when a source-backed observation is recorded.":
      "Prueba otra búsqueda o borra los filtros. Los hechos aparecen al registrar una observación respaldada por una fuente.",
    Value: "Valor",
    "View observations": "Ver observaciones",
    "What was observed, and where it came from.": "Qué se observó y de dónde procede.",
    "This is a recorded observation, not a current-state guarantee.":
      "Es una observación registrada, no una garantía del estado actual.",
    "Context and source": "Contexto y fuente",
    "Remaining quantity": "Cantidad restante",
    "Advanced order operations": "Operaciones avanzadas de pedidos",
    "All delivery history": "Todo el historial de entregas",
    "Clear order filter": "Quitar filtro de pedido",
    "Customer deliveries": "Entregas a clientes",
    "Customer delivery actions open in Your work. Supplier details include their linked evidence.":
      "Las acciones de entrega a clientes se abren en Tu trabajo. Los detalles del proveedor incluyen la evidencia vinculada.",
    Deliveries: "Entregas",
    Shipments: "Envíos",
    Dispatched: "Enviado",
    Carrier: "Transportista",
    Contents: "Contenido",
    "Tracking number": "Número de seguimiento",
    "Observed state": "Estado observado",
    "Physical contents": "Contenido físico",
    "Tracking observations": "Observaciones de seguimiento",
    "No stock movement recorded": "No se registró ningún movimiento de existencias",
    "Warehouse and carrier observations differ":
      "Las observaciones del almacén y del transportista difieren",
    "Search carrier, tracking number or shipment ID":
      "Buscar transportista, número de seguimiento o ID de envío",
    "Shipment ID": "ID de envío",
    "Package ID (optional)": "ID de paquete (opcional)",
    Reporter: "Informante",
    "Replacement event ID (optional)": "ID de evento sustituto (opcional)",
    "Counterparty ID": "ID de contraparte",
    "Movement inputs (JSON)": "Entradas de Movement (JSON)",
    "Movements must be a JSON array": "Movements debe ser una matriz JSON",
    "Review exact effect": "Revisar el efecto exacto",
    "Prepare the exact shipment change, then review it before confirmation.":
      "Prepara el cambio exacto del envío y revísalo antes de confirmarlo.",
    "Deliveries for the selected order": "Entregas del pedido seleccionado",
    "Delivery direction": "Dirección de entrega",
    "Delivery scope": "Alcance de entregas",
    "From order to delivery.": "Del pedido a la entrega.",
    Lines: "Líneas",
    "No due date": "Sin fecha prevista",
    "Open deliveries have a remaining quantity and an open commitment. All history includes completed and cancelled commitments.":
      "Las entregas abiertas tienen cantidad pendiente y un compromiso abierto. El historial completo incluye compromisos cumplidos y cancelados.",
    "Order document": "Documento de pedido",
    "Order documents record the agreement. Delivery progress comes from linked commitments and movements.":
      "Los documentos de pedido registran lo acordado. El avance de entrega procede de compromisos y movimientos vinculados.",
    "Orders & deliveries": "Pedidos y entregas",
    "Recorded status": "Estado registrado",
    "Search orders and deliveries": "Buscar pedidos y entregas",
    "Search party, item or delivery ID": "Buscar tercero, artículo o ID de entrega",
    "See what was agreed, what is still open and the records behind it.":
      "Consulta lo acordado, lo pendiente y los registros que lo respaldan.",
    "Supplier deliveries": "Entregas de proveedores",
    "Supplier orders": "Pedidos a proveedores",
    "Unknown item": "Artículo desconocido",
    "Unknown location": "Ubicación desconocida",
    "View deliveries": "Ver entregas",
    Failed: "Fallido",
    Unknown: "Desconocido",
    Expired: "Caducada",
    "Sending invitation": "Enviando invitación",
    "Invitation delivered": "Invitación entregada",
    "Delivery retry scheduled": "Reintento de envío programado",
    "Invitation delivery": "Envío de invitación",

    "Advanced company settings": "Configuración avanzada de la empresa",
    "AI credentials configured": "Credenciales de IA configuradas",
    "AI credentials not configured": "Credenciales de IA sin configurar",
    "Appearance is saved in this browser. System follows your device.":
      "La apariencia se guarda en este navegador. Sistema sigue la configuración del dispositivo.",
    "Check saved preferences": "Comprobar preferencias guardadas",
    "Company access": "Acceso a la empresa",
    "Company credentials": "Credenciales de la empresa",
    "Configuration status does not confirm a live connection to the AI provider.":
      "El estado de configuración no confirma una conexión activa con el proveedor de IA.",
    "Credential management": "Gestión de credenciales",
    Expires: "Caduca",
    "Make Reality work for you.": "Configura Reality a tu manera.",
    "Manage invitations, credentials and company setup in company administration.":
      "Gestiona invitaciones, credenciales y ajustes de la empresa en la administración.",
    Member: "Miembro",
    "Not configured": "Sin configurar",
    "Number and date format": "Formato de números y fechas",
    "Only company owners can view these settings.":
      "Solo los propietarios de la empresa pueden ver estos ajustes.",
    Owner: "Propietario",
    "Personal preferences": "Preferencias personales",
    "Preferences saved.": "Preferencias guardadas.",
    "Saved preferences differ from your draft. Review it before saving again.":
      "Las preferencias guardadas difieren de tu borrador. Revísalo antes de volver a guardar.",
    "Settings sections": "Secciones de configuración",
    "These preferences apply to your account across all companies.":
      "Estas preferencias se aplican a tu cuenta en todas las empresas.",
    "This view shows up to 500 members and 500 invitations.":
      "Esta vista muestra hasta 500 miembros y 500 invitaciones.",
    "Time zone": "Zona horaria",
    "Use an IANA time zone, such as Europe/Rome or America/New_York.":
      "Usa una zona horaria IANA, como Europe/Rome o America/New_York.",
    "Your preferences, company access and AI configuration in one place.":
      "Tus preferencias, el acceso a la empresa y la configuración de IA en un solo lugar.",
    "Preferences were not saved. Check your entries and try again.":
      "No se guardaron las preferencias. Revisa los datos e inténtalo de nuevo.",
    "The save result is unknown. Check saved preferences before trying again.":
      "El resultado del guardado es desconocido. Comprueba las preferencias guardadas antes de volver a intentarlo.",
    "Could not check saved preferences. Try checking again.":
      "No se pudieron comprobar las preferencias guardadas. Vuelve a comprobarlas.",
    Queued: "En cola",
    Sending: "Enviando",
    "Not sent": "Sin enviar",
    "Clear source version": "Quitar versión de origen",
    "Document / party": "Documento / contraparte",
    "Documents are evidence. Delivery and payment state comes from the linked business records.":
      "Los documentos son evidencia. El estado de entregas y pagos procede de los registros empresariales vinculados.",
    Enabled: "Habilitado",

    "Exact source version": "Versión exacta de origen",
    "Exact system code": "Código exacto del sistema",
    "External reference / origin": "Referencia externa / origen",
    "Follow registered origins, received originals and the evidence they produced.":
      "Consulta los sistemas registrados, los originales recibidos y la evidencia que produjeron.",
    "Import job": "Tarea de importación",
    "Job status describes processing, not interpretation success. Open a record to inspect its original.":
      "El estado de la tarea describe el procesamiento, no el éxito de la interpretación. Abre un registro para ver el original.",
    "No import job": "Sin tarea de importación",
    "No linked source": "Sin origen vinculado",
    "Open original": "Abrir original",
    "Originals preserve what arrived. Documents hold evidence. Reality describes the business state.":
      "Los originales conservan lo recibido. Los documentos contienen evidencia. Reality describe el estado del negocio.",
    "Received records": "Registros recibidos",
    "received versions": "versiones recibidas",
    "Recorded amount": "Importe registrado",
    "Registered systems are definitions, not proof of a live connection. Counts include every held source version.":
      "Los sistemas registrados son definiciones, no prueban una conexión activa. Los recuentos incluyen todas las versiones de origen conservadas.",
    "Search data": "Buscar datos",
    "Search document number, reference or source":
      "Buscar número de documento, referencia u origen",
    "Search origin, type or external reference": "Buscar origen, tipo o referencia externa",
    "Search system name or code": "Buscar nombre o código de sistema",
    "See where your business data comes from.":
      "Comprende de dónde proceden tus datos empresariales.",
    "Source setup and imports": "Configuración de fuentes e importaciones",
    Systems: "Sistemas",
    "Technical Explorer": "Explorador técnico",
    "View evidence": "Ver evidencia",
    "View received records": "Ver registros recibidos",
    "Account / posting": "Cuenta / asiento",
    "Advanced finance operations": "Operaciones financieras avanzadas",
    "All filtered records": "Todos los registros filtrados",
    "Amounts follow recorded postings and allocations. Each currency stays separate.":
      "Los importes reflejan los asientos y asignaciones registrados. Cada moneda se mantiene separada.",
    Balance: "Saldo",
    Credit: "Haber",
    Debit: "Debe",
    "Debits and credits follow the selected account and search. A filtered balance need not be zero.":
      "El debe y el haber corresponden a la cuenta y búsqueda seleccionadas. El saldo filtrado no tiene por qué ser cero.",
    "Exact account": "Cuenta exacta",
    "Follow outstanding invoices, recorded payments and their financial evidence.":
      "Consulta facturas pendientes, pagos registrados y sus documentos de respaldo.",
    "Invoice / party": "Factura / contraparte",
    "Operational financial records, not statutory accounts.":
      "Registros financieros operativos, no cuentas anuales.",
    Outstanding: "Pendiente",
    "Partially settled": "Liquidado parcialmente",
    "Payment / party": "Pago / contraparte",
    "Recorded payment history includes reversals. Amounts are shown per payment.":
      "El historial de pagos incluye anulaciones. Los importes se muestran por pago.",
    "Reversed original": "Original anulado",
    "Reversing entry": "Asiento de anulación",
    "Search finance": "Buscar datos financieros",
    "Search invoice or party": "Buscar factura o contraparte",
    "Understand what is open, paid and recorded.":
      "Comprende qué está pendiente, pagado y registrado.",
    Adjustment: "Ajuste",
    "Advanced warehouse operations": "Operaciones avanzadas de almacén",
    "All severities": "Todas las prioridades",
    "Available stock": "Existencias disponibles",
    "Check current state": "Comprobar estado actual",
    "Clear item filter": "Quitar filtro de artículo",
    "Company-wide stock per item. Quantities retain their own units.":
      "Existencias por artículo en toda la empresa. Cada cantidad conserva su unidad.",
    Compensation: "Compensación",
    Consumed: "Consumida",
    Corrected: "Corregido",
    Correction: "Corrección",
    Critical: "Crítica",
    "Current finding": "Hallazgo actual",
    "Current findings, their causes and the records that explain them.":
      "Hallazgos actuales, sus causas y los registros que los explican.",
    "Explain finding": "Explicar hallazgo",
    "Findings clear when the underlying records change. They are not manually dismissed tasks.":
      "Los hallazgos desaparecen cuando cambian los registros subyacentes. No se descartan manualmente.",
    "Findings reflect the records currently available in this company.":
      "Los hallazgos reflejan los registros disponibles actualmente en esta empresa.",
    High: "Alta",
    "Know what is available, and why.": "Comprende qué está disponible y por qué.",
    Low: "Baja",
    "No available stock": "Sin existencias disponibles",
    "No current findings": "No hay hallazgos actuales",
    "No matching findings": "No hay hallazgos coincidentes",
    Normal: "Estándar",
    "Open a finding to see its cause, supporting records and next step.":
      "Abre un hallazgo para ver su causa, los registros de respaldo y el siguiente paso.",
    "Open delivery": "Abrir entrega",
    "Open warehouse": "Abrir almacén",
    "Overallocated stock": "Existencias sobreasignadas",
    Receipt: "Recepción",
    "Recorded causes and references": "Causas y referencias registradas",
    "Recorded history includes corrected originals and compensations.":
      "El historial registrado incluye originales corregidos y compensaciones.",
    Released: "Liberada",
    Replacement: "Sustitución",
    "Reserved stock is linked to its commitment.":
      "Las existencias reservadas están vinculadas a su compromiso.",
    "Resolution guidance": "Orientación para resolver",
    "Search by item name or SKU": "Buscar por nombre de artículo o SKU",
    "Search by reference ID": "Buscar por ID de referencia",
    "Search causes or references": "Buscar causas o referencias",
    "Search exceptions": "Buscar hallazgos",
    "Search warehouse": "Buscar en almacén",
    "See what needs a closer look.": "Ve qué necesita una revisión más detallada.",
    Severity: "Prioridad",
    "Start with a finding": "Empieza con un hallazgo",
    Stock: "Existencias",
    "Stock, its reservations and the movements behind it.":
      "Existencias, sus reservas y los movimientos que las explican.",
    "Supplier return": "Devolución a proveedor",
    "Supporting record": "Registro de respaldo",
    Transfer: "Traslado",
    "Try another filter or inspect the original records.":
      "Prueba otro filtro o inspecciona los registros originales.",
    Workspaces: "Áreas de trabajo",
    Customers: "Clientes",
    Suppliers: "Proveedores",
    Roles: "Roles asignados",
    "Date (UTC)": "Fecha (UTC)",
    Analytics: "Analítica",
    "Fully reserved": "Totalmente reservado",
    "Needs reservation": "Necesita reserva",
    "Overdue deliveries": "Entregas vencidas",
    "Without due date": "Sin fecha de vencimiento",
    "Delivery commitments created": "Compromisos de entrega creados",
    "Shipment movements": "Movimientos de envío",
    "How your operations are moving": "Cómo evolucionan tus operaciones",
    "Open analytics": "Abrir analítica",
    "Recorded activity over time": "Actividad registrada en el tiempo",
    "Delivery commitments created and shipment movements":
      "Compromisos de entrega creados y movimientos de envío",
    "Understand the flow of your business.": "Comprende el flujo de tu negocio.",
    "Current delivery position and the activity behind it.":
      "Situación actual de entregas y la actividad que la explica.",
    "No open deliveries to measure": "No hay entregas abiertas que medir",
    "of open deliveries": "de las entregas abiertas",
    "Current position · view records": "Situación actual · ver registros",
    "Recorded activity": "Actividad registrada",
    "Counts of commitments and movements · UTC days":
      "Recuento de compromisos y movimientos · días UTC",
    Period: "Período",
    days: "días",
    "These series count different records, not order conversion. Corrections are reflected in shipment counts. External history may be incomplete.":
      "Estas series cuentan registros distintos, no conversión de pedidos. Los envíos reflejan las correcciones. El historial externo puede estar incompleto.",
    "Daily values and supporting records": "Valores diarios y registros de respaldo",
    "Supporting records": "Registros de respaldo",
    records: "registros",
    "No matching records": "No hay registros coincidentes",
    "Observed at": "Observado el",
    "Current position is independent of the selected period.":
      "La situación actual es independiente del período seleccionado.",
    "Master data action": "Acción de datos maestros",
    "Edit details": "Editar detalles",
    "Item type": "Tipo de artículo",
    Tracking: "Seguimiento",
    "Default location": "Ubicación predeterminada",
    "Purchase unit": "Unidad de compra",
    "Conversion factor": "Factor de conversión",
    "Lead time (days)": "Plazo de entrega (días)",
    "Parent location": "Ubicación superior",
    "Allows physical stock": "Permite stock físico",
    Stocked: "Almacenable",
    Service: "Servicio",
    Charge: "Cargo",
    "No tracking": "Sin seguimiento",
    Serial: "Número de serie",
    Identity: "Identidad",
    "Commercial defaults": "Valores comerciales predeterminados",
    "Inventory behaviour": "Comportamiento de inventario",
    Hierarchy: "Jerarquía",
    "Reviewed revision": "Revisión revisada",
    "Choices could not be loaded.": "No se pudieron cargar las opciones.",
    "Create a record": "Crear registro",
    "Change recorded": "Cambio registrado",
    "Outcome not yet verified": "Resultado aún sin verificar",
    "Ready for your confirmation": "Listo para tu confirmación",
    "Recorded intent and receipt. Current details may have changed since execution.":
      "Intención y resultado registrados. Los datos actuales pueden haber cambiado desde la ejecución.",
    "Check the exact fields below. Confirmation records this change.":
      "Revisa los campos exactos a continuación. La confirmación registra este cambio.",
    "Field changes": "Cambios de campos",
    "Recorded reference IDs": "Identificadores de referencia registrados",
    "Open record": "Abrir registro",
    "Prepare a change, review it, then confirm. Nothing is recorded yet.":
      "Prepara un cambio, revísalo y confirma. Aún no se registra nada.",
    "A prepared request is saved. Check it before starting another change.":
      "Hay una solicitud preparada guardada. Revísala antes de iniciar otro cambio.",
    "Check prepared request": "Comprobar solicitud preparada",
    "Prepare change": "Preparar cambio",
    "Edit request": "Editar solicitud",
    "The people, products and places behind your operations.":
      "Las personas, productos y lugares de tus operaciones.",
    "Resume request": "Retomar solicitud",
    "Search master data": "Buscar datos maestros",
    "Search by name, SKU or ID": "Buscar por nombre, SKU o ID",
    "Include inactive": "Incluir inactivos",
    "Adjust your search or create the first record.":
      "Ajusta la búsqueda o crea el primer registro.",
    Provenance: "Procedencia",
    "No original source is linked to this record.":
      "Este registro no tiene una fuente original vinculada.",
    "All recorded details": "Todos los datos registrados",
    "Start with a record": "Empieza con un registro",
    "Choose a customer, supplier, item or location to see its details and prepare a change.":
      "Elige un cliente, proveedor, artículo o ubicación para ver sus datos y preparar un cambio.",
    "Also available in chat": "También disponible en el chat",
    "Ask Reality to prepare a change. You review the same fields before confirming.":
      "Pide a Reality que prepare un cambio. Revisas los mismos campos antes de confirmar.",
    "Advanced settings": "Configuración avanzada",
    "Recorded result is not yet verified.": "El resultado registrado aún no está verificado.",
    "Still open": "Pendiente",
    "Allocate available stock to a delivery.": "Asignar existencias disponibles a una entrega.",
    "Record goods leaving the warehouse.": "Registrar la salida de mercancías del almacén.",
    "More records are available in the workspace.":
      "Hay más registros disponibles en el área de trabajo.",
    "Open inventory": "Abrir inventario",
    "Current observation unavailable": "Situación actual no disponible",
    "Handling unit": "Unidad de manipulación",
    Lot: "Lote",
    "Serial unit": "Número de serie",
    History: "Historial",
    "No results": "Sin resultados",
    Pending: "Pendiente",
    Delivery: "Entrega",
    "Check outcome": "Comprobar resultado",
    "Choose a delivery": "Selecciona una entrega",
    "Confirm change": "Confirmar cambio",
    "Execution outcome is being checked. Do not repeat the action.":
      "Se está comprobando el resultado. No repitas la acción.",
    "Preparing a review does not change stock.":
      "Preparar una revisión no modifica las existencias.",
    "Record shipment": "Registrar envío",
    "Recorded result is separate from the current observation.":
      "El resultado registrado se muestra separado de la situación actual.",
    Rejected: "Rechazado",
    "Review change": "Revisar cambio",
    "Review the exact change before confirming.": "Revisa el cambio exacto antes de confirmarlo.",
    "Selected delivery": "Entrega seleccionada",
    "Tracking references": "Identificadores de existencias",
    "Not selected": "Sin seleccionar",
    "Refine your search to see more matches.": "Afina la búsqueda para ver más resultados.",
    "A clear view of what is open.": "Una visión clara de lo que está pendiente.",
    "Ask about orders, stock and money.": "Pregunta por pedidos, existencias y dinero.",
    "Ask about your company": "Pregunta sobre tu empresa",
    "Back to deliveries": "Volver a entregas",
    "Choose a delivery to see what is open and why.":
      "Selecciona una entrega para ver qué está pendiente y por qué.",
    "Choose an authorized company or open company settings.":
      "Selecciona una empresa autorizada o abre su configuración.",
    "Company overview": "Resumen de la empresa",
    "Company unavailable": "Empresa no disponible",
    Conversation: "Conversación",
    "Customer delivery": "Entrega al cliente",
    "Daily work": "Trabajo diario",
    "Data & sources": "Datos y fuentes",
    Decisions: "Decisiones",
    open: "pendientes",
    Commitments: "Compromisos",
    "Decisions & control": "Decisiones y control",
    "Discuss with Reality": "Comentar con Reality",
    Explain: "Explicar",
    "Inventory at this location": "Existencias en esta ubicación",
    "Latest events": "Eventos más recientes",
    "More workspaces": "Más áreas de trabajo",
    Navigation: "Navegación",
    "No document evidence": "Sin evidencia documental",
    "No open commitments": "Sin compromisos pendientes",
    "No open deliveries": "Sin entregas pendientes",
    "No pending decisions": "Sin decisiones pendientes",
    "Older events": "Eventos anteriores",
    "One conversation across your business.": "Una conversación para toda tu empresa.",
    "Open a case to understand the position and its supporting records.":
      "Abre un caso para entender la situación y sus registros de respaldo.",
    "Open commitments": "Compromisos pendientes",
    "Open existing workspace": "Abrir área de trabajo existente",
    "Open practice company": "Abrir empresa de práctica",
    "Original source": "Fuente original",
    "Pending decisions": "Decisiones pendientes",
    "Review decisions": "Revisar decisiones",
    "Review commitments": "Revisar compromisos",
    "Review each proposed change before it is recorded.":
      "Revisa cada cambio propuesto antes de registrarlo.",
    "Review proposed changes": "Revisar cambios propuestos",
    Sandbox: "Entorno de pruebas",
    "Thinking…": "Pensando…",
    "Unknown party": "Contraparte desconocida",
    "What would you like to understand or do?": "¿Qué te gustaría entender o hacer?",
    "Your business, in focus.": "Tu empresa, en perspectiva.",
    "Your open work": "Tu trabajo pendiente",
    "Your work": "Tu trabajo",
    "Live simulation": "Simulación en vivo",
    "New orders": "Pedidos nuevos",
    "New reservations": "Reservas nuevas",
    "Stock movements": "Movimientos de existencias",
    "Other documents": "Otros documentos",
    "Recorded business activity": "Actividad empresarial registrada",
    "minutes per bar": "minutos por barra",
    "Activity over time": "Actividad a lo largo del tiempo",
    "Recorded activities": "actividades registradas",
    "Time range": "Período",
    "Hover or select a bar to explore what happened.":
      "Señala o selecciona una barra para ver lo que ocurrió.",
    "Hatched areas have no observed data. The latest bar is still filling.":
      "Las zonas rayadas no tienen datos observados. La última barra aún está incompleta.",
    "Counts new orders, reservations, stock movements and other documents. Technical processing steps are excluded.":
      "Cuenta pedidos, reservas, movimientos de existencias y otros documentos nuevos. Excluye los pasos de procesamiento técnico.",
    "Activity in this interval": "Actividad en este intervalo",
    "No recorded activity in this interval.": "No hay actividad registrada en este intervalo.",
    "Showing the latest 50 matching events. Use all activity for more history.":
      "Se muestran los últimos 50 eventos coincidentes. Consulta toda la actividad para ver más historial.",
    "Your company, in motion": "Tu empresa en movimiento",
    "Recorded activity · updates every 10 seconds":
      "Actividad registrada · se actualiza cada 10 segundos",
    "View all activity": "Ver toda la actividad",
    "Updates paused. Showing the last available activity.":
      "Actualización interrumpida. Se muestra la última actividad disponible.",
    "Activity is currently unavailable. We will retry automatically.":
      "La actividad no está disponible. Se reintentará automáticamente.",
    "No activity yet. New records will appear here.":
      "Todavía no hay actividad. Los nuevos registros aparecerán aquí.",
    "System status": "Estado del sistema",
    "Everything is ready": "Todo está listo",
    "Availability is not fully confirmed": "Disponibilidad no confirmada por completo",
    Connection: "Conexión",
    "Automatic scheduling": "Programación automática",
    "Background processing": "Procesamiento en segundo plano",
    "Shows service availability. Individual imports and actions have their own results.":
      "Muestra la disponibilidad de los servicios. Cada importación y acción tiene su propio resultado.",
    "Not yet verified": "Aún sin verificar",
    "Currently unavailable": "Actualmente no disponible",
    "Checking…": "Comprobando…",
    "Recent activity": "Actividad reciente",
    Updated: "Actualizado",
    Ready: "Listo",
    "Company created": "Empresa creada",
    "Company created. Opening your company…": "Empresa creada. Abriendo tu empresa…",
    "Retry opening": "Reintentar abrir",

    "Company name (required)": "Nombre de la empresa (obligatorio)",
    "Choose a name for this company or Sandbox so you can find it later.":
      "Elige un nombre para esta empresa o Sandbox para encontrarla más adelante.",
    "Enter a company name to continue.": "Introduce un nombre de empresa para continuar.",

    "Start your own company": "Iniciar tu propia empresa",
    "Start empty and add your own data or integrations.":
      "Empieza sin datos y añade tus propios datos o integraciones.",
    "Create an empty Sandbox": "Crear un Sandbox vacío",
    "Experiment without preset data in a clearly labelled test environment.":
      "Experimenta sin datos predefinidos en un entorno de prueba claramente identificado.",
    "Try demo data": "Probar con datos de demostración",
    "Explore international products, warehouses, customers and twelve weeks of order history in a Sandbox.":
      "Explora productos internacionales, almacenes, clientes y doce semanas de historial de pedidos en un Sandbox.",
    "How would you like to start?": "¿Cómo quieres empezar?",
    "Enable live simulation": "Activar simulación en vivo",
    "Receive 60 new demo orders per hour. The demo integration is set up automatically. You can pause it anytime.":
      "Recibe 60 nuevos pedidos de demostración por hora. La integración se configura automáticamente. Puedes pausarla en cualquier momento.",

    "Automatically connect Demo Data and start 60 orders per hour when this company is created. You can pause it anytime in Integrations.":
      "Los datos de demostración se conectan automáticamente al crear la empresa y comienzan con 60 pedidos por hora. Puedes pausar la simulación en Integraciones.",
    "Manage live simulation": "Gestionar simulación en vivo",
    "Receive ongoing demo orders": "Recibir pedidos de demostración continuos",
    "Original source and interpretation": "Fuente original e interpretación",
    "Receive synthetic orders through the background worker. Connecting does not start arrivals.":
      "Recibe pedidos sintéticos automáticamente. Conectar no inicia la recepción de pedidos.",
    "Demo profile and practice cases": "Perfil y casos de demostración",
    "Comparison periods": "Periodos de comparación",
    "Amounts are booked gross values by currency. Costs and promotions are not provided.":
      "Los importes son valores brutos contabilizados por moneda. No se incluyen costes ni promociones.",
    "Create a separate company with one reservable unit and a blocked case. No reservation is executed during setup.":
      "Crea una empresa separada con una unidad reservable y un caso bloqueado. La configuración no ejecuta ninguna reserva.",
    "Create reservation practice": "Crear práctica de reserva",
    "Starting data": "Datos iniciales",
    "Empty company": "Empresa vacía",
    "Start without products, orders or opening stock.":
      "Empieza sin productos, pedidos ni existencias iniciales.",
    "International demo company": "Empresa de demostración internacional",
    "16 products, two warehouses, operational cases and twelve weeks of synthetic history. Created as a Sandbox.":
      "16 productos, dos almacenes, casos operativos y doce semanas de historial sintético. Se crea como Sandbox.",
    "Company environment": "Entorno de la empresa",
    "Ordinary company": "Empresa normal",
    "An empty Sandbox contains no demo records. Its practice environment stays clearly labelled.":
      "Un Sandbox vacío no contiene datos de demostración. El entorno de pruebas permanece claramente identificado.",
    "Your access request has not created a company. Choose how this company should start.":
      "Tu solicitud de acceso no ha creado una empresa. Elige cómo quieres iniciarla.",
    "Choose how this company should start.": "Elige cómo quieres iniciar esta empresa.",
    "Company details and order volume describe your access request. They do not create a company.":
      "Los datos de la empresa y el volumen de pedidos describen tu solicitud de acceso. No crean una empresa.",
    "Company setup could not be loaded. Reload to retry.":
      "No se pudo cargar la configuración. Vuelve a cargar la página.",
    "Creation could not be confirmed. Retry the same request to recover safely.":
      "No se pudo confirmar la creación. Repite la misma solicitud para recuperar el estado de forma segura.",
    "Keep this request while setup is pending. Retrying will not create another company.":
      "Conserva esta solicitud mientras la configuración está pendiente. Reintentar no creará otra empresa.",
    "Retry company setup": "Reintentar la configuración",
    "New demo orders arrive automatically.":
      "Los nuevos pedidos de demostración llegan automáticamente.",
    "New arrivals are paused. Existing orders remain available.":
      "Las nuevas llegadas están pausadas. Los pedidos existentes siguen disponibles.",
    "Explore your business with synthetic orders.": "Explora tu empresa con pedidos sintéticos.",
    "Live updates are unavailable. Showing the last known information.":
      "Las actualizaciones en vivo no están disponibles. Se muestra la última información conocida.",
    "Imported orders": "Pedidos importados",
    "Next scheduled arrival": "Próxima llegada programada",
    "Latest 25 demo orders. Updates automatically while this page is visible.":
      "Últimos 25 pedidos de demostración. Se actualiza automáticamente mientras esta página está visible.",
    "Last checked": "Última comprobación",
    "Waiting for the first demo order.": "Esperando el primer pedido de demostración.",
    "Demo order imported": "Pedido de demostración importado",
    "Demo import failed": "Importación de demostración fallida",
    "Demo import pending": "Importación de demostración pendiente",
    Apply: "Aplicar",
    Loading: "Cargando",
    "More options": "Más opciones",
    "Demo Data": "Datos de demostración",
    "Demo Data is available in compatible practice companies.":
      "Los datos de demostración están disponibles en empresas de práctica compatibles.",
    "Receive synthetic orders automatically. Connecting does not start arrivals.":
      "Recibe pedidos sintéticos automáticamente. Conectar no inicia la recepción de pedidos.",
    "Review demo connection": "Revisar conexión de demostración",
    "Only the following missing references will be added. No stock or history is created.":
      "Solo se añadirán los siguientes datos maestros que faltan. No se crearán existencias ni historial.",
    "Confirm connection": "Confirmar conexión",
    "Confirm Demo Data change": "Confirmar cambio en datos de demostración",
    "Confirm import retry": "Confirmar reintento de importación",
    "Generated orders": "Pedidos generados",
    "Order to cash": "Del pedido al cobro",
    "Invoices issued": "Facturas emitidas",
    "Payments received": "Pagos recibidos",
    "Payments allocated": "Pagos asignados",
    "Invoices settled": "Facturas liquidadas",
    "Open residuals": "Restos abiertos",
    "Customer credit created": "Crédito de cliente generado",
    "Unmatched payments": "Pagos sin asignar",
    "Settlement failures": "Contabilizaciones fallidas",
    "Next settlement": "Próxima contabilización",
    "Last settlement": "Última contabilización",
    "Open payments": "Abrir pagos",
    "Open open items": "Abrir partidas abiertas",
    "Open journal": "Abrir diario",
    "Differences wait for your decision in Payments.":
      "Las diferencias esperan tu decisión en Pagos.",
    "Suggested invoices": "Facturas sugeridas",
    suggested: "sugerida",
    "Amount equals the open amount": "El importe coincide con el importe abierto",
    "Invoice number appears in the remittance text": "El número de factura aparece en el concepto",
    "Stated reference names this invoice among others":
      "La referencia indicada nombra esta factura entre otras",
    Imported: "Importados",
    "Next arrival": "Próxima llegada",
    "Last successful import": "Última importación correcta",
    "Orders per hour": "Pedidos por hora",
    "Refresh status": "Actualizar estado",
    "Recent demo imports": "Importaciones de demostración recientes",
    "Next page": "Página siguiente",
    "Open order": "Abrir pedido",
    "The change could not be confirmed. Refresh the status before retrying.":
      "No se pudo confirmar el cambio. Actualiza el estado antes de reintentar.",
    "Sandbox — practice environment": "Sandbox — entorno de pruebas",
    Start: "Iniciar",
    "Start simulation": "Iniciar simulación",
    Pause: "Pausar",
    Resume: "Reanudar",
    Stop: "Detener",
    Disconnect: "Desconectar",
    Reconnect: "Reconectar",
    "Change rate": "Cambiar frecuencia",
    Stopped: "Detenido",
    Running: "En marcha",
    Paused: "En pausa",
    Disconnected: "Desconectado",
    "Paused: resolve failed imports": "En pausa: resuelve las importaciones fallidas",
    "Execution needs attention": "La ejecución requiere atención",
    "Not connected": "Sin conexión",
    completed: "completado",
    failed: "fallido",
    pending: "pendiente",
    Invoices: "Facturas",
    Warehouse: "Almacén",
    "Master data": "Datos maestros",
    "Customer order recorded": "Pedido de cliente registrado",
    "Purchase order recorded": "Pedido de compra registrado",
    "Customer invoice recorded": "Factura de cliente registrada",
    "Supplier invoice recorded": "Factura de proveedor registrada",
    "Customer credit recorded": "Abono de cliente registrado",
    "Supplier credit recorded": "Abono de proveedor registrado",
    "Customer return received": "Devolución de cliente recibida",
    "Stock adjusted": "Existencias corregidas",
    "Delivery promise recorded": "Compromiso de entrega registrado",
    "Delivery promise fulfilled": "Compromiso de entrega cumplido",
    "Delivery promise updated": "Compromiso de entrega modificado",
    "Reservation released": "Reserva liberada",
    "Reserved stock used": "Existencias reservadas utilizadas",
    "Goods movement recorded": "Movimiento de mercancía registrado",
    "Business data received": "Datos comerciales recibidos",
    "Business data processed": "Datos comerciales procesados",
    "Business change recorded": "Cambio comercial registrado",
    "Business context": "Contexto comercial",
    "Current recorded position": "Situación registrada actual",
    "Business area": "Área de negocio",
    "All business areas": "Todas las áreas",
    "Customer orders": "Pedidos de clientes",
    "Purchase orders": "Pedidos de compra",
    "Delivery movements": "Movimientos de entrega",
    "What happened?": "¿Qué ha ocurrido?",
    "Counts of recorded orders, shipment/receipt movements and invoices in this sandbox, independent of filters. Movements are not unique deliveries.":
      "Cantidades de pedidos, movimientos de recepción/envío y facturas, independientes de los filtros. Los movimientos no son entregas únicas.",
    "Data overview": "Resumen de datos",
    "Business commitments": "Compromisos",
    "Goods movements": "Movimientos de mercancía",
    "Totals scope": "Alcance de los totales",
    "Totals for this sandbox, independent of search and filters.":
      "Totales de esta sandbox, independientes de la búsqueda y los filtros.",
    "About transaction groups": "Sobre los grupos de transacciones",
    "Groups contain loaded matching events linked by source or correlation, not necessarily the entire order.":
      "Los grupos contienen resultados cargados vinculados por origen o correlación, no necesariamente el pedido completo.",
    "Search open items": "Buscar partidas abiertas …",
    "Search deliveries": "Buscar entregas …",
    "Reserve stock for customer orders": "Reservar existencias para pedidos",
    "Review overdue customer deliveries": "Revisar entregas vencidas",
    "Follow up supplier deliveries": "Revisar entregas de proveedores",
    "Review invoicing for shipped goods": "Revisar facturación de mercancía enviada",
    "Review stock reservations": "Revisar reservas de existencias",
    "Follow up customer payments": "Revisar pagos de clientes",
    "Review supplier payments": "Revisar pagos a proveedores",
    "Review credit for returned goods": "Revisar abono de devoluciones",
    "Context unavailable": "Contexto no disponible",
    "Not reserved": "Sin reservar",
    "Review record": "Revisar registro",
    "Open notices": "Avisos pendientes",
    "Back to cockpit": "Volver al panel",
    "Expand chat": "Ampliar chat",
    Table: "Tabla",
    "Sandbox companion": "Asistente del entorno",
    "Read only": "Solo lectura",
    "Understand your sandbox, one question at a time.":
      "Comprende tu entorno, una pregunta a la vez.",
    "Checking your sandbox…": "Consultando tu entorno…",
    "What needs attention in this sandbox?": "¿Qué requiere atención en este entorno?",
    "How has my stock changed?": "¿Cómo ha cambiado mi inventario?",
    "What do we still need to deliver or receive?": "¿Qué debemos entregar o recibir todavía?",
    "Which invoices are still unpaid?": "¿Qué facturas siguen pendientes?",
    "Which business partners and items are available?":
      "¿Qué socios y artículos están registrados?",
    "Explain the latest recorded change.": "Explica el último cambio registrado.",
    "How do Source, Evidence and Reality connect?":
      "¿Cómo se relacionan Source, Evidence y Reality?",
    "More questions": "Más preguntas",
    "Show less": "Mostrar menos",
    "All exceptions": "Todas las excepciones",
    You: "Tú",
    "Ask about your sandbox": "Pregunta sobre tu entorno…",
    "Send question": "Enviar pregunta",
    "Uses the managed AI. No bookings or changes.":
      "Con IA administrada. Sin registros ni cambios.",
    "The assistant is unavailable. Your question is kept; please try again.":
      "El asistente no está disponible. Tu pregunta se conserva; inténtalo de nuevo.",
    "Individual operations": "Operaciones individuales",
    "More operations": "Más operaciones",
    "Open in App": "Abrir en la aplicación",
    "Guided examples": "Ejemplos guiados",
    "Free operations": "Operaciones libres",
    "Open work": "Pedidos abiertos",
    "Create customer order only": "Crear solo pedido de cliente",
    "Create supplier order only": "Crear solo pedido de compra",
    "Create orders now. Reserve, ship or receive them later in Open work.":
      "Crea pedidos. Reserva, envía o recibe después en Pedidos abiertos.",
    "Open work could not be loaded.": "No se pudieron cargar los pedidos abiertos.",
    "Actions create records. These views show their current business effect.":
      "Las acciones crean registros. Estas vistas muestran su efecto actual en el negocio.",
    "All events": "Todos los eventos",
    "Allocate goods to the order. Physical stock stays unchanged.":
      "Reserva mercancía para el pedido. Las existencias físicas no cambian.",
    "Business partners": "Socios comerciales",
    "Choose a saved run. Its recorded history remains intact.":
      "Elige una prueba guardada. Su historial permanece intacto.",
    "Current projection": "Proyección actual",
    "Current Reality": "Reality actual",
    "Customer order": "Pedido de cliente",
    "Every recorded change, in order": "Todos los cambios registrados, en orden",
    "Execution is unresolved or this step was rejected. Refresh to inspect the server state; no action will be repeated automatically.":
      "La ejecución no está resuelta o este paso fue rechazado. Actualiza para consultar el estado del servidor; ninguna acción se repetirá automáticamente.",
    "Flight recorder": "Registro de eventos",
    "Goods obligations": "Obligaciones de mercancía",
    "Goods owed to us": "Mercancía que nos deben",
    "Goods shipped": "Mercancía enviada",
    "Money positions": "Posiciones monetarias",
    "Money positions are unavailable.": "Las posiciones monetarias no están disponibles.",
    "Movement recorded": "Movement registrado",
    "No locations": "Sin ubicaciones",
    "No open exceptions.": "No hay excepciones abiertas.",
    "No open goods commitments.": "No hay obligaciones de mercancía pendientes.",
    "No Reality events yet.": "Aún no hay eventos en Reality.",
    "No recorded money position yet.": "Aún no hay posiciones monetarias registradas.",
    "Obligations and exceptions": "Obligaciones y excepciones",
    "Obligations are unavailable. Refresh to retry.":
      "Las obligaciones no están disponibles. Actualiza para reintentar.",
    "Opening stock": "Existencias iniciales",
    "Opening stock recorded": "Existencias iniciales registradas",
    "Operational position": "Situación operativa",
    "Private learning run": "Prueba de aprendizaje privada",
    "Promise goods to a customer. Stock stays unchanged until shipment.":
      "Compromete mercancía para un cliente. Las existencias no cambian hasta el envío.",
    "Reality is loading. Refresh if it remains unavailable.":
      "Reality se está cargando. Actualiza si sigue sin estar disponible.",
    "Reality timeline": "Cronología de Reality",
    "Reality views": "Vistas de Reality",
    "Record a full or partial delivery. Reality shows what remains owed.":
      "Registra una entrega completa o parcial. Reality muestra lo que queda pendiente.",
    "Record opening stock to see the inventory position here.":
      "Registra las existencias iniciales para ver aquí el inventario.",
    "Record what is physically in your warehouse. This creates a Movement.":
      "Registra lo que hay físicamente en tu almacén. Esto crea un Movement.",
    "Recorded data": "Datos registrados",
    "Recorded events — oldest first": "Eventos registrados — más antiguos primero",
    "Review each action before confirming.": "Revisa cada acción antes de confirmarla.",
    "Review this action before changing Reality.": "Revisa esta acción antes de cambiar Reality.",
    "Sandbox — sample data only": "Sandbox — solo datos de ejemplo",
    Shipment: "Envío",
    "SKU / Unit": "SKU / Unidad",
    "Stock by item": "Existencias por artículo",
    "The preview changed or was stale. The current server preview is loaded; review it and confirm again.":
      "La vista previa cambió o estaba desactualizada. Se ha cargado la vista actual del servidor; revísala y confirma de nuevo.",
    "We owe goods": "Mercancía que debemos",
    "Who owes what?": "¿Quién debe qué?",
    "Your first action will appear here. Select an event to inspect its evidence.":
      "Tu primera acción aparecerá aquí. Selecciona un evento para consultar su evidencia.",
    "Financial posting recorded": "Asiento financiero registrado",
    "Payment allocated": "Pago asignado",
    "Record invoice": "Registrar factura",
    "Record and allocate payment": "Registrar y asignar el pago",
    "Record the invoice total as stated. This creates a receivable, not a payment.":
      "Registra el total indicado en la factura. Esto crea una cuenta por cobrar, no un pago.",
    "Record the received payment and allocate it to this invoice. The open amount decreases.":
      "Registra el pago recibido y asígnalo a esta factura. El importe pendiente disminuye.",
    "Stated invoice total": "Total indicado en la factura",
    "Payment amount": "Importe del pago",
    "Payment recorded": "Pago registrado",
    "Start another operation": "Iniciar otra operación",
    "Same sandbox. Existing stock, obligations and history are preserved.":
      "La misma sandbox. Se conservan las existencias, obligaciones e historial.",
    "Another customer order": "Otro pedido de cliente",
    "Record additional opening stock": "Registrar más existencias iniciales",
    "Purchasing and returns are not available yet.":
      "Las compras y devoluciones aún no están disponibles.",
    "Start a fresh sandbox": "Iniciar una sandbox nueva",
    "Choose your next operation": "Elegir la siguiente operación",
    "Business operations": "Operaciones de negocio",
    "Choose what to try. Everything stays in this sandbox.":
      "¿Qué quieres probar? Todo permanece en esta sandbox.",
    "Record opening stock": "Registrar existencias iniciales",
    "Record existing goods, then choose your next operation.":
      "Registra la mercancía existente y elige la siguiente operación.",
    "Sell from stock": "Vender existencias",
    "Customer order, reservation and delivery. Use the stock already available.":
      "Pedido de cliente, reserva y entrega con existencias disponibles.",
    "Purchase order and goods receipt, including partial deliveries.":
      "Pedido a proveedor y recepción, incluidas entregas parciales.",
    "More scenarios — coming later": "Más escenarios próximamente",
    "Choosing an operation changes nothing. Review and confirm each action separately.":
      "Elegir no cambia nada. Revisa y confirma cada acción por separado.",
    "Supplier order": "Pedido a proveedor",
    "Receive goods": "Registrar recepción",
    "Record supplier invoice": "Registrar factura del proveedor",
    "Available inside the sandbox": "Disponible dentro del entorno de pruebas",
    "Customer return": "Devolución de cliente",
    "Receive customer return": "Recibir devolución del cliente",
    "Record credit note": "Registrar nota de abono",
    "Refund customer": "Registrar reembolso al cliente",
    "Original shipment": "Entrega original",
    "Stated credit total": "Importe de abono indicado",
    "Receive returned goods, record a credit note and refund the customer.":
      "Recibe la devolución, registra el abono y reembolsa al cliente.",
    "A customer return needs a recorded shipment first.":
      "Una devolución requiere una entrega registrada previamente.",
    "Receive goods from a recorded customer shipment. This changes stock, not money.":
      "Recibe mercancía de una entrega registrada. Cambian las existencias, no el dinero.",
    "Record the stated credit total for returned goods. No money moves yet.":
      "Registra el importe de abono indicado para la devolución. Aún no se mueve dinero.",
    "Record the refund and allocate it to the credit note. The credit balance decreases.":
      "Registra el reembolso y asígnalo al abono. El saldo pendiente disminuye.",
    "Record supplier payment": "Registrar pago al proveedor",
    "Purchase order, goods receipt, supplier invoice and payment.":
      "Pedido de compra, recepción, factura del proveedor y pago.",
    "Record the supplier's stated invoice total. This creates a payable; stock stays unchanged.":
      "Registra el total indicado por el proveedor. Se crea una deuda; las existencias no cambian.",
    "Record your payment to the supplier and allocate it to this invoice. The payable decreases.":
      "Registra el pago al proveedor y asígnalo a esta factura. La deuda pendiente disminuye.",
    "Customer returns are being prepared.": "Las devoluciones de clientes están en preparación.",
    "Goods received": "Mercancía recibida",
    "Order from a supplier": "Comprar a un proveedor",
    "Order goods from a supplier. This creates an incoming goods obligation, not stock or a payable.":
      "Pide mercancía a un proveedor. Se crea una obligación de entrega, no existencias ni deuda monetaria.",
    "Record goods actually received. Stock increases and the supplier's remaining obligation decreases.":
      "Registra la mercancía recibida. Aumentan las existencias y disminuye la obligación pendiente del proveedor.",
    "Supplier invoices, supplier payments and returns are not available yet.":
      "Las facturas y pagos a proveedores y las devoluciones estarán disponibles más adelante.",
    "Stock → order → reservation → shipment → invoice → payment":
      "Existencias → pedido → reserva → envío → factura → pago",
    Sales: "Ventas",
    Purchasing: "Compras",
    Accounting: "Contabilidad",
    "Choose a scenario": "Elegir escenario",
    "New sandbox": "Nueva sandbox",
    "Your sandboxes": "Tus sandboxes",
    "Saved sandboxes": "Sandboxes guardadas",
    "Start a new sandbox or continue in an existing one.":
      "Inicia una nueva sandbox o continúa en una existente.",
    "Choose your operations inside the sandbox. All changes stay in one timeline.":
      "Elige las operaciones dentro de la sandbox. Todos los cambios quedan en una cronología.",
    "Show fewer sandboxes": "Mostrar menos sandboxes",
    "Show more sandboxes": "Mostrar más sandboxes",
    "Back to current run": "Volver al intento actual",
    "One business story. Your actions on the left, their effect in Reality on the right.":
      "Un caso de negocio. Actúa a la izquierda y observa el efecto en Reality a la derecha.",
    "Try this scenario": "Probar ahora",
    "Not available yet": "Aún no disponible",
    "Sell, deliver and get paid": "Vender, entregar y cobrar",
    "From a customer promise to goods leaving the warehouse.":
      "Desde el pedido hasta la salida de mercancías.",
    "Available through delivery. Invoice and payment follow later.":
      "Disponible hasta la entrega. Factura y pago llegarán después.",
    "Deliver part of an order": "Entregar parte de un pedido",
    "Promise twelve, ship five. See the remaining goods obligation.":
      "Promete doce, entrega cinco. Consulta la obligación pendiente.",
    "Opening stock → order → reservation → partial shipment":
      "Stock inicial → pedido → reserva → entrega parcial",
    "A customer returns goods": "Un cliente devuelve mercancías",
    "Receive the return, record a credit note and refund the customer.":
      "Recibe la devolución, registra el abono y reembolsa al cliente.",
    "Buy, receive and pay": "Comprar, recibir y pagar",
    "Order from a supplier, receive goods and settle the invoice.":
      "Pide al proveedor, recibe mercancías y paga la factura.",
    "A supplier delivers in parts": "Un proveedor entrega por partes",
    "Receive part of a purchase and see what the supplier still owes.":
      "Recibe parte de la compra y consulta lo que aún debe el proveedor.",
    "Record and pay an expense": "Registrar y pagar un gasto",
    "Follow a simple expense from the original receipt to payment.":
      "Sigue un gasto desde el comprobante hasta el pago.",
    "Correct an incorrect posting": "Corregir un asiento incorrecto",
    "Reverse a posting and record its replacement. Preserve the evidence.":
      "Revierte un asiento y registra su sustitución. Conserva la evidencia.",
    "Your current run will be archived and remain readable. A new private example starts only after confirmation.":
      "El intento actual se archivará y seguirá visible. El nuevo ejemplo comienza solo tras confirmar.",
    "Starting a scenario is currently unavailable. Your saved runs remain readable.":
      "Ahora no se puede iniciar un escenario. Los intentos guardados siguen visibles.",
    "Delivery:": "Entrega:",
    "Retry delivery": "Reintentar entrega",
    "Accept invitation": "Aceptar invitación",
    "Checking invitation…": "Comprobando la invitación…",
    "Invited as": "Invitado como",
    "Join this company": "Unirse a esta empresa",
    "One moment while we check your invitation link.":
      "Un momento, estamos comprobando tu enlace de invitación.",
    "This invitation is no longer valid. Ask a company owner to send you a new one.":
      "Esta invitación ya no es válida. Pide una nueva a un propietario de la empresa.",
    "Your invitation is bound to this address.": "Tu invitación está vinculada a esta dirección.",
    "Cancel invitation": "Cancelar invitación",
    "Company invitation": "Invitación de empresa",
    "Confirm that you want to join this company.": "Confirma que deseas unirte a esta empresa.",
    "Invitation unavailable": "Invitación no disponible",
    "Sign in or create an account with the invited email. Membership is granted only after you accept.":
      "Inicia sesión o crea una cuenta con el correo invitado. La membresía solo se concede después de aceptar.",
    "Active members": "Miembros activos",
    Invitations: "Invitaciones",
    "Invite a member": "Invitar a un miembro",
    "Invite member": "Invitar miembro",
    "They receive a secure link and join only after explicitly accepting.":
      "La persona recibe un enlace seguro y solo se incorpora después de aceptarlo expresamente.",
    "name@company.com": "nombre@empresa.com",
    "Internal Copilot": "Copilot interno",
    "Managed by Reality": "Gestionado por Reality",
    "Reality-managed": "Gestionado por Reality",
    "Reality-managed is included. Other providers use your own account.":
      "Reality-managed está incluido. Los demás proveedores utilizan su propia cuenta.",
    "Reality-managed works immediately. You can instead connect a provider account owned by this company.":
      "Reality-managed funciona inmediatamente. También puede conectar una cuenta de proveedor propiedad de esta empresa.",
    "Use own Anthropic key": "Usar una clave Anthropic propia",
    "Use the included server credential.": "Usar la credencial de servidor incluida.",
    "Usage is billed directly to your Anthropic account.":
      "El uso se factura directamente a su cuenta de Anthropic.",
    "Anthropic API key": "Clave API de Anthropic",
    "Enter Anthropic API key": "Introduzca la clave API de Anthropic",
    "Anthropic and the economical Claude model are selected centrally. Choose who provides the API credential for this company.":
      "Anthropic y el modelo económico de Claude se seleccionan de forma centralizada. Elija quién proporciona la credencial API para esta empresa.",
    "Copilot available": "Copilot disponible",
    "Copilot not configured": "Copilot no configurado",
    "Reality is preparing an answer": "Reality está preparando una respuesta",
    "The AI provider and model are operated centrally. Company data remains tenant-scoped, and Copilot can only use registered read and proposal tools.":
      "El proveedor y el modelo de IA se administran de forma centralizada. Los datos de la empresa permanecen aislados por tenant y Copilot solo puede usar herramientas registradas de lectura y propuesta.",
    "Inviting…": "Enviando invitación…",
    "Loading members…": "Cargando miembros…",
    "Manage access for this company. Only owners can invite or remove members.":
      "Gestiona el acceso a esta empresa. Solo los propietarios pueden invitar o eliminar miembros.",
    Members: "Miembros",
    "No active members.": "No hay miembros activos.",
    "No invitations.": "No hay invitaciones.",
    Remove: "Eliminar",
    Resend: "Reenviar",
    All: "Todo",
    "Close activity": "Cerrar actividad",
    "Load older activity": "Cargar actividad anterior",
    "New business events will appear here.": "Los nuevos eventos empresariales aparecerán aquí.",
    "Open activity": "Abrir actividad",
    "Operational core": "Núcleo operativo",
    "Reality activity": "Actividad de Reality",
    "Tenant-scoped operational and financial events.":
      "Eventos operativos y financieros de esta empresa.",
    "What happened": "Qué ocurrió",
    "Company Overview": "Resumen de la empresa",
    "Company-wide control": "Control de toda la empresa",
    "Order Operations": "Operaciones de pedidos",
    "Warehouse Operations": "Operaciones de almacén",
    "Finance Control": "Control financiero",
    "Data Management": "Gestión de datos",
    "My area": "Mi área",
    Views: "Vistas",
    Actions: "Acciones",
    "Workspace navigation unavailable": "La navegación del área no está disponible",
    "Review action": "Revisar acción",
    "Confirm action": "Confirmar acción",
    "Reserve stock": "Reservar existencias",
    "Record movement": "Registrar movimiento",
    "Correct movement": "Corregir movimiento",
    "Hold or release commitment": "Bloquear o liberar compromiso",
    "Hold or release document commitments": "Bloquear o liberar compromisos del documento",
    "Set or release party delivery hold": "Establecer o liberar bloqueo de entrega de la parte",
    "More actions": "Más acciones",
    "All actions": "Todas las acciones",
    "Search actions": "Buscar acciones",
    "No actions found": "No se encontraron acciones",
    "More views": "Más vistas",
    "All views": "Todas las vistas",
    "Search views": "Buscar vistas",
    "No views found": "No se encontraron vistas",
    "Warehouse Queue": "Cola de almacén",
    "Supply & demand": "Oferta y demanda",
    "Search this view…": "Buscar en esta vista…",
    "View unavailable": "Vista no disponible",
    "No projection rows yet": "Aún no hay datos para esta vista",
    "This view will populate when matching business Reality exists.":
      "Esta vista se completará cuando existan datos empresariales coincidentes en Reality.",
    "Change or clear your search.": "Cambie o borre la búsqueda.",
    "No results found": "No se encontraron resultados",
    Pagination: "Paginación",
    Previous: "Anterior",
    Page: "Página",
    Next: "Siguiente",
    results: "resultados",
    "Order & Warehouse Operations": "Operaciones de pedidos y almacén",
    "Customer orders with readiness, due dates and execution blockers":
      "Pedidos de clientes con preparación, vencimientos y bloqueos de ejecución",
    "Orders prioritized for warehouse execution and shipment readiness":
      "Pedidos priorizados para ejecución en almacén y preparación de envío",
    "Commitment shortages and active execution holds blocking fulfillment":
      "Faltantes y bloqueos activos que impiden el cumplimiento",
    "Item-level physical stock, incoming supply and uncovered customer demand":
      "Existencias físicas, suministro entrante y demanda no cubierta por artículo",
    "Customer orders with readiness, due dates and the blockers that explain execution.":
      "Pedidos de clientes con preparación, vencimientos y bloqueos que explican la ejecución.",
    "Orders prioritized for warehouse execution with shipment readiness explained.":
      "Pedidos priorizados para almacén con la preparación de envío explicada.",
    "Shortages and active execution holds that currently block fulfillment.":
      "Faltantes y bloqueos activos que actualmente impiden el cumplimiento.",
    "Physical stock, incoming supply and uncovered customer demand by item.":
      "Existencias físicas, suministro entrante y demanda no cubierta por artículo.",
    "Create manual sales or purchase order": "Crear pedido manual de venta o compra",
    "Observe source-supported fact": "Registrar hecho respaldado por una fuente",
    "Post customer payment": "Registrar pago de cliente",
    "Post supplier payment": "Registrar pago a proveedor",
    "Order lines": "Líneas del pedido",
    Line: "Línea",
    "Add line": "Añadir línea",
    "Remove line": "Eliminar línea",
    "Unit price": "Precio unitario",
    "Promised at": "Fecha prometida",
    "Create handling unit": "Crear unidad logística",
    "Create lot": "Crear lote",
    "Create serial unit": "Crear unidad serializada",
    Hold: "Bloquear",
    Release: "Liberar",
    "Ask Reality": "Preguntar a Reality",
    Home: "Inicio",
    Exceptions: "Excepciones",
    Inventory: "Inventario",
    Documents: "Documentos",
    Activity: "Actividad",
    "new attention event": "nuevo evento que requiere atención",
    "new attention events": "nuevos eventos que requieren atención",
    "Open Activity to review": "Abrir Actividad para revisar",
    Payments: "Pagos",
    Parties: "Entidades",
    Items: "Artículos",
    Locations: "Ubicaciones",
    Sources: "Fuentes",
    "Open items": "Partidas abiertas",
    "Profile & preferences": "Perfil y preferencias",
    "Account settings": "Configuración de la cuenta",
    Language: "Idioma",
    "Number & date format": "Formato de números y fechas",
    "Display timezone": "Zona horaria de visualización",
    "Save preferences": "Guardar preferencias",
    "Preferences saved": "Preferencias guardadas",
    "Saving…": "Guardando…",
    "Needs attention": "Requiere atención",
    Completed: "Completado",
    "Technical details": "Detalles técnicos",
    "Event type": "Tipo de evento",
    Subject: "Objeto",
    Correlation: "Correlación",
    Companies: "Empresas",
    "Sign out": "Cerrar sesión",
    Settings: "Configuración",
    General: "General",
    Data: "Datos",
    Agents: "Agentes",
    Company: "Empresa",
    Status: "Estado",
    "Company settings": "Configuración de la empresa",
    "New company": "Nueva empresa",
    Archive: "Archivar",
    "Archive company": "Archivar empresa",
    Archived: "Archivada",
    "Company & settings": "Empresa y configuración",
    Profile: "Perfil",
    "Sources & intake": "Fuentes y entrada",
    Processing: "Procesamiento",
    "Reference data": "Datos de referencia",
    Explorer: "Explorador",
    Copilot: "Copilot",
    "MCP server": "Servidor MCP",
    "Company details": "Datos de la empresa",
    "Default currency": "Moneda predeterminada",
    Timeline: "Cronología",
    "Live activity": "Actividad en vivo",
    "Events today": "Eventos de hoy",
    "Orders processed": "Pedidos procesados",
    Physical: "Físico",
    Reserved: "Reservado",
    Available: "Disponible",
    Incoming: "Entrante",
    Projected: "Proyectado",
    Risk: "Riesgo",
    "Due date": "Fecha de vencimiento",
    Flow: "Flujo",
    Counterparty: "Contraparte",
    Item: "Artículo",
    Review: "Revisar",
    Date: "Fecha",
    Document: "Documento",
    Party: "Entidad",
    Amount: "Importe",
    Total: "Total",
    State: "Estado",
    Type: "Tipo",
    Records: "Registros",
    Cancel: "Cancelar",
    Confirm: "Confirmar",
    Close: "Cerrar",
    Edit: "Editar",
    Add: "Añadir",
    Search: "Buscar",
    "Use the owning Reality correction workflow for economic line changes.":
      "Utilice el flujo de corrección de Reality correspondiente para cambios económicos en líneas.",
    "New party": "Nueva entidad",
    "Search parties…": "Buscar entidades…",
    Name: "Nombre",
    Role: "Rol",
    "Source / identity": "Fuente / identidad",
    "Manual / internal": "Manual / interno",
    Supplier: "Proveedor",
    Customer: "Cliente",
  },
};

// Keep the main catalog readable while covering every product surface. New UI copy
// belongs here (or in the catalog above), never as an unreviewed German-only string.
Object.assign(dictionaries.de, {
  "Activity pulse": "Aktivitätsimpuls",
  "Business record": "Geschäftsdatensatz",
  "records in this interval": "Datensätze in diesem Intervall",
  "Choose a record to trace its connections.":
    "Wähle einen Datensatz, um seine Verbindungen nachzuverfolgen.",
  "Clear pulse": "Impuls schließen",
  "Back to pulse": "Zurück zum Impuls",
  "Relationship trace": "Beziehungspfad",
  "Open a linked record to continue the trace.":
    "Öffne einen verbundenen Datensatz, um den Pfad fortzusetzen.",
  "Evidence and origin": "Evidence und Ursprung",
  "Operational consequences": "Operative Folgen",
  "Records in the same interval combine into one pulse per lane.":
    "Datensätze im selben Intervall werden pro Ebene zu einem Impuls zusammengefasst.",
  "Scroll left for older history. Click a node to follow its connections.":
    "Scrolle nach links für ältere Einträge. Klicke auf einen Knoten, um seine Verbindungen zu verfolgen.",
});
Object.assign(dictionaries.nl, {
  "Activity pulse": "Activiteitspuls",
  "Business record": "Bedrijfsrecord",
  "records in this interval": "records in dit interval",
  "Choose a record to trace its connections.":
    "Kies een record om de verbindingen ervan te volgen.",
  "Clear pulse": "Puls sluiten",
  "Back to pulse": "Terug naar puls",
  "Relationship trace": "Relatiepad",
  "Open a linked record to continue the trace.":
    "Open een gekoppeld record om het pad te vervolgen.",
  "Evidence and origin": "Evidence en oorsprong",
  "Operational consequences": "Operationele gevolgen",
  "Records in the same interval combine into one pulse per lane.":
    "Records in hetzelfde interval worden per baan tot één puls gecombineerd.",
  "Scroll left for older history. Click a node to follow its connections.":
    "Scroll naar links voor oudere geschiedenis. Klik op een knooppunt om de verbindingen te volgen.",
});
Object.assign(dictionaries.es, {
  "Activity pulse": "Pulso de actividad",
  "Business record": "Registro de negocio",
  "records in this interval": "registros en este intervalo",
  "Choose a record to trace its connections.": "Elige un registro para seguir sus conexiones.",
  "Clear pulse": "Cerrar pulso",
  "Back to pulse": "Volver al pulso",
  "Relationship trace": "Ruta de relaciones",
  "Open a linked record to continue the trace.":
    "Abre un registro vinculado para continuar la ruta.",
  "Evidence and origin": "Evidence y origen",
  "Operational consequences": "Consecuencias operativas",
  "Records in the same interval combine into one pulse per lane.":
    "Los registros del mismo intervalo se combinan en un pulso por nivel.",
  "Scroll left for older history. Click a node to follow its connections.":
    "Desplázate a la izquierda para ver el historial anterior. Haz clic en un nodo para seguir sus conexiones.",
});

Object.assign(dictionaries.de, {
  Reset: "Zurücksetzen",
  "Release reservation": "Reservierung freigeben",
  "Edit item": "Artikel bearbeiten",
  Roles: "Rollen",
  "Edit location": "Lagerort bearbeiten",
  "Maintain reference data. This does not move goods or book money.":
    "Stammdaten pflegen. Dabei wird keine Ware bewegt und kein Geld gebucht.",
  "No active reservations.": "Keine aktiven Reservierungen.",
  "Releasing a reservation makes stock available again. The order and physical stock remain unchanged.":
    "Die Freigabe macht die Ware wieder verfügbar. Auftrag und physischer Bestand bleiben unverändert.",
  "Showing the latest 100 active reservations.":
    "Die letzten 100 aktiven Reservierungen werden angezeigt.",
  "Customer payment": "Kundenzahlung",
  "Supplier payment": "Lieferantenzahlung",
  "Document line": "Belegposition",
  "Financial evidence unavailable.": "Finanzbeleg konnte nicht geladen werden.",
  Select: "Bitte auswählen",
  "Select an open order in Open deliveries to continue.":
    "Wähle in Offene Lieferungen einen offenen Auftrag aus, um fortzufahren.",
  "Discard failed shipment": "Fehlgeschlagenen Versand verwerfen",
  "Shipment quantity exceeds the open order quantity.":
    "Die Versandmenge überschreitet die noch offene Auftragsmenge. Bitte korrigiere die Menge.",
  "Open deliveries": "Offene Lieferungen",
  "Customers · We must deliver": "Kunden · Wir müssen liefern",
  "Suppliers · We expect goods": "Lieferanten · Wir erwarten Ware",
  "Customers · Receivables": "Kunden · Forderungen",
  "Suppliers · Payables": "Lieferanten · Verbindlichkeiten",
  "Include settled items": "Ausgeglichene Posten anzeigen",
  "No matching open items.": "Keine passenden Posten.",
  Ready: "Bereit",
  "All statuses": "Alle Status",
  "Lifecycle view": "Lebenszyklusansicht",
  "No items": "Keine Vorgänge",
  "No matching missing information": "Keine passenden fehlenden Informationen",
  "Search questions or intended use": "Fragen oder Verwendungszweck durchsuchen",
  "Try another search or remove a filter.":
    "Versuche eine andere Suche oder entferne einen Filter.",
  Question: "Frage",
  "Current rule version": "Aktuelle Regelversion",
  "New immutable version": "Neue unveränderliche Version",
  "Edit rule as a new version": "Regel als neue Version bearbeiten",
  "Based on version": "Basierend auf Version",
  "New version": "Neue Version",
  Simulation: "Regeltest",
  "Rule activation": "Regelaktivierung",
  "Activate this rule version?": "Diese Regelversion aktivieren?",
  "Future matching sources will create Facts through this exact immutable rule version.":
    "Künftig passende Quellen erzeugen Facts über genau diese unveränderliche Regelversion.",
  "Accepted gaps": "Akzeptierte Lücken",
  "Some checked sources cannot use this rule":
    "Einige geprüfte Quellen können diese Regel nicht verwenden",
  "They will not create a Fact. Activate only if missing historical fields are expected.":
    "Sie erzeugen keinen Fact. Aktiviere nur, wenn fehlende historische Felder erwartet werden.",
  "Created by": "Erstellt durch",
  "Rule versions": "Regelversionen",
  "Test and activate": "Regel testen und aktivieren",
  "Rule active": "Regel aktiv",
  "Edit rule": "Regel bearbeiten",
  "Save as new rule version": "Als neue Regelversion speichern",
  "Accept gaps and activate": "Lücken akzeptieren und aktivieren",
  "Simulation result": "Simulationsergebnis",
  "The rule can be tested further": "Die Regel kann weiter geprüft werden",
  "The rule needs attention": "Die Regel muss korrigiert werden",
  "This preview changes no business data. It shows what would happen with the sources checked.":
    "Diese Vorschau ändert keine Geschäftsdaten. Sie zeigt, was mit den geprüften Quellen passieren würde.",
  "Sources checked": "Quellen geprüft",
  "Facts that would be created": "Facts, die entstehen würden",
  "Sources needing attention": "Quellen mit Klärungsbedarf",
  "Show checked sources": "Geprüfte Quellen anzeigen",
  "Fact would be created": "Fact würde entstehen",
  "Field is missing or has the wrong value": "Feld fehlt oder hat den falschen Wert",
  "Source needs review": "Quelle muss geprüft werden",
  "How the missing information is completed": "So wird die fehlende Information ergänzt",
  "First show the answer in a real case. Reality then proposes how it should be used in the future.":
    "Zeige zuerst an einem echten Vorgang, wo die Information heute steht. Reality schlägt danach vor, wie sie künftig verwendet wird.",
  "Question captured": "Frage erfasst",
  "Now: Show example": "Jetzt: Beispiel zeigen",
  "Example provided": "Beispiel hinzugefügt",
  "Next: Review solution": "Danach: Lösung prüfen",
  "Now: Review solution": "Jetzt: Lösung prüfen",
  "Solution proposed": "Lösung vorgeschlagen",
  "Then: Confirm adoption": "Danach: Übernahme bestätigen",
  "Now: Confirm adoption": "Jetzt: Übernahme bestätigen",
  "Adoption confirmed": "Übernahme bestätigt",
  Details: "Einzelheiten",
  "Missing information captured": "Fehlende Information erfasst",
  "Open Missing information": "Fehlende Informationen öffnen",
  "The question is now in the shared queue. You can open it to add evidence, review the recommendation, and decide what Reality should learn.":
    "Die Frage liegt jetzt in der gemeinsamen Liste. Öffne sie, um Nachweise hinzuzufügen, die Empfehlung zu prüfen und zu entscheiden, was Reality lernen soll.",
  "Start in Ask Reality": "In Ask Reality starten",
  "Found something Reality cannot answer?": "Etwas gefunden, das Reality nicht beantworten kann?",
  "Describe the missing answer in Chat. Reality will ask the necessary follow-up questions and, after your confirmation, add it to this shared queue.":
    "Beschreibe die fehlende Antwort im Chat. Reality stellt die nötigen Rückfragen und nimmt sie nach deiner Bestätigung in diese gemeinsame Liste auf.",
  "Nothing is added or automated until you review and confirm the request in Chat.":
    "Bis du die Anfrage im Chat geprüft und bestätigt hast, wird nichts hinzugefügt oder automatisiert.",
  "Capture in Ask Reality": "In Ask Reality erfassen",
  "I found information that Reality cannot answer yet. Help me describe it and capture it as missing information.":
    "Ich habe eine Information gefunden, die Reality noch nicht beantworten kann. Hilf mir, sie zu beschreiben und als fehlende Information zu erfassen.",
  "Review unanswered business questions captured through Ask Reality and follow them through investigation and implementation.":
    "Prüfe über Ask Reality erfasste unbeantwortete Geschäftsfragen und begleite sie durch Untersuchung und Umsetzung.",
  Step: "Schritt",
  "of 4": "von 4",
  "Tell Reality what is missing": "Sag Reality, was fehlt",
  "Describe a concrete question from your daily work. Reality will save it for review; this does not change orders or automate actions.":
    "Beschreibe eine konkrete Frage aus deinem Arbeitsalltag. Reality speichert sie zur Prüfung; Bestellungen werden dadurch nicht geändert und Aktionen nicht automatisiert.",
  "What question can you not answer right now?": "Welche Frage kannst du gerade nicht beantworten?",
  "For example: Which orders should be shipped first today?":
    "Zum Beispiel: Welche Bestellungen sollen heute zuerst versendet werden?",
  "Which orders should be shipped first today?":
    "Welche Bestellungen sollen heute zuerst versendet werden?",
  "Which orders are gifts?": "Welche Bestellungen sind Geschenke?",
  "Where can I find the requested delivery method?": "Wo finde ich die gewünschte Versandart?",
  "Why is an order not ready to ship?": "Warum ist eine Bestellung noch nicht versandbereit?",
  "How will you use the answer?": "Wofür brauchst du die Antwort?",
  "Show it on a record": "Bei einem Vorgang anzeigen",
  "Search or filter by it": "Danach suchen oder filtern",
  "Prioritize work": "Arbeit priorisieren",
  "Make a decision": "Eine Entscheidung treffen",
  "Trigger an action later": "Später eine Aktion auslösen",
  "How often do you need it?": "Wie oft brauchst du die Information?",
  "For every relevant record": "Bei jedem relevanten Vorgang",
  "Sometimes, for special cases": "Manchmal, bei Sonderfällen",
  "Only for this one case": "Nur für diesen einen Fall",
  "Where do you find the answer today?": "Wo findest du die Antwort heute?",
  "In the Shopify order": "In der Shopify-Bestellung",
  "In another system": "In einem anderen System",
  "In an email or note": "In einer E-Mail oder Notiz",
  "A colleague knows it": "Ein Mitarbeiter kennt sie",
  "I do not know yet": "Ich weiß es noch nicht",
  "What happens next": "Was passiert als Nächstes?",
  "Reality records this question in the shared queue. It will suggest where the answer belongs, but nothing is activated without review and confirmation.":
    "Reality nimmt die Frage in die gemeinsame Liste auf und empfiehlt, wo die Antwort hingehört. Ohne Prüfung und Bestätigung wird nichts aktiviert.",
  Back: "Zurück",
  "Review and capture": "Prüfen und erfassen",
  "Missing information": "Fehlende Informationen",
  "Data management": "Datenverwaltung",
  "Shared queue": "Gemeinsame Liste",
  "No missing information": "Keine fehlenden Informationen",
  "Capture missing information": "Fehlende Information erfassen",
  "Capture the first business question Reality cannot answer.":
    "Erfasse die erste Geschäftsfrage, die Reality noch nicht beantworten kann.",
  "Capture business questions Reality cannot answer yet, review source evidence, and safely teach tenant-specific Facts.":
    "Erfasse unbeantwortete Geschäftsfragen, prüfe Quelldaten und bringe Reality sicher unternehmensspezifische Fakten bei.",
  "What can Reality not answer?": "Was kann Reality nicht beantworten?",
  "What decision, display, filter, or action needs the answer?":
    "Welche Entscheidung, Anzeige, Filterung oder Aktion benötigt die Antwort?",
  "Select missing information": "Fehlende Information auswählen",
  "Open an item to investigate, classify, simulate, and implement it.":
    "Öffne einen Eintrag, um ihn zu untersuchen, einzuordnen, zu simulieren und umzusetzen.",
  "Add a business answer or source observation":
    "Geschäftliche Antwort oder Quellenbeobachtung hinzufügen",
  "Add evidence": "Nachweis hinzufügen",
  "Recommend destination": "Modellziel empfehlen",
  "Model destination": "Modellziel",
  Fact: "Fakt",
  "Source only": "Nur Quelle",
  "Typed Evidence": "Typisierte Evidence",
  "Typed Reality": "Typisierte Reality",
  "Projection or Exception": "Projektion oder Ausnahme",
  "Accept classification": "Einordnung übernehmen",
  "Prepare implementation": "Umsetzung vorbereiten",
  "Simulate rule": "Regel simulieren",
  "Activate rule": "Regel aktivieren",
  "Replay history": "Historie verarbeiten",
  "Disable rule": "Regel deaktivieren",
});

Object.assign(dictionaries.de, {
  "Investigation progress": "Fortschritt der Klärung",
  Request: "Anfrage",
  Examples: "Beispiele",
  Recommendation: "Empfehlung",
  "Next step": "Nächster Schritt",
  "Show Reality where you find the answer today": "Zeige Reality, wo du die Antwort heute findest",
  "Add one real example from Shopify, another system, an email, or current employee knowledge. Do not include passwords or unnecessary personal data.":
    "Füge ein echtes Beispiel aus Shopify, einem anderen System, einer E-Mail oder dem Wissen eines Mitarbeiters hinzu. Keine Passwörter oder unnötigen personenbezogenen Daten eingeben.",
  "Example or observation": "Beispiel oder Beobachtung",
  "For example: In order #1042, the gift-wrap choice appears as gift_wrap = yes.":
    "Zum Beispiel: Bei Bestellung #1042 steht die Geschenkverpackung als gift_wrap = yes.",
  "Save example and continue": "Beispiel speichern und weiter",
  "Ask Reality for a recommendation": "Reality um eine Empfehlung bitten",
  "Reality will assess the business use and saved examples. This creates a recommendation only; it changes no business data.":
    "Reality bewertet den Geschäftszweck und die gespeicherten Beispiele. Dabei entsteht nur eine Empfehlung; Geschäftsdaten werden nicht geändert.",
  "Create recommendation": "Empfehlung erstellen",
  "Reality recommendation": "Empfehlung von Reality",
  "Keep this information as a source-supported business observation":
    "Diese Information als quellenbasierte Geschäftsbeobachtung übernehmen",
  "The saved example describes contextual business meaning rather than a physical event. Reality recommends learning it without changing the order or triggering an action.":
    "Das gespeicherte Beispiel beschreibt eine fachliche Bedeutung und kein physisches Ereignis. Reality empfiehlt, sie zu lernen, ohne die Bestellung zu ändern oder eine Aktion auszulösen.",
  "Accept recommendation": "Empfehlung annehmen",
  "Choose a different outcome": "Anderes Ergebnis wählen",
  "Technical model destination": "Technisches Modellziel",
  "Use different outcome": "Anderes Ergebnis verwenden",
  "Technical implementation": "Technische Umsetzung",
  "Only open this section when a technical owner is ready to map, test, and activate the source rule.":
    "Diesen Bereich nur öffnen, wenn ein technischer Verantwortlicher die Quellregel zuordnen, testen und aktivieren kann.",
  "History and technical details": "Verlauf und technische Details",
  "Greater than": "Größer als",
  "Less than": "Kleiner als",
  "Fact observation time": "Beobachtungszeit des Facts",
  "When Reality received the source": "Als Reality die Quelle empfangen hat",
  "A timestamp in the source": "Ein Zeitstempel in der Quelle",
  "Timestamp field path": "Feldpfad des Zeitstempels",
  "Rule execution summary": "Ausführungsübersicht der Regel",
  "Last evaluated": "Zuletzt ausgewertet",
  "Not evaluated yet": "Noch nicht ausgewertet",
  "Show sources needing attention": "Quellen mit Klärungsbedarf anzeigen",
  "Show generated Facts": "Erzeugte Facts anzeigen",
});

Object.assign(dictionaries.de, {
  "Reality Playground": "Reality Playground",
  "Reality timeline": "Reality-Timeline",
  "Business partner created": "Geschäftspartner angelegt",
  "Item created": "Artikel angelegt",
  "Location created": "Lagerort angelegt",
  "Sandbox — sample data only": "Sandbox · nur Beispieldaten",
  "New run": "Neuer Versuch",
  "Open previous layout": "Vorherige Ansicht öffnen",
  "Previous layout": "Vorherige Ansicht",
  "No locations": "Keine Lagerorte",
  "Private learning run": "Privater Lernversuch",
  ACT: "HANDELN",
  OBSERVE: "BEOBACHTEN",
  UNDERSTAND: "VERSTEHEN",
  Simulation: "Simulation",
  "Opening stock": "Anfangsbestand",
  "Customer order": "Kundenauftrag",
  Reservation: "Reservierung",
  Shipment: "Versand",
  "Review each action before confirming.": "Jede Aktion vor der Bestätigung prüfen.",
  "Operational position": "Operative Lage",
  "Reality views": "Reality-Ansichten",
  "Master data": "Stammdaten",
  "Stock by item": "Bestand je Artikel",
  "Current projection": "Aktuelle Projektion",
  "Reality is loading. Refresh if it remains unavailable.":
    "Reality wird geladen. Bei Bedarf aktualisieren.",
  "Record opening stock to see the inventory position here.":
    "Erfasse Anfangsbestand, um hier die Bestandslage zu sehen.",
  "Actions create records. These views show their current business effect.":
    "Aktionen erzeugen Einträge. Diese Ansichten zeigen ihre aktuelle Wirkung im Geschäft.",
  "SKU / Unit": "SKU / Einheit",
  "Recorded events — oldest first": "Aufgezeichnete Ereignisse · älteste zuerst",
  "Obligations and exceptions": "Verpflichtungen und Ausnahmen",
  "Who owes what?": "Wer schuldet wem was?",
  "Goods obligations": "Warenverpflichtungen",
  "Obligations are unavailable. Refresh to retry.":
    "Verpflichtungen nicht verfügbar. Bitte aktualisieren.",
  "No open goods commitments.": "Keine offenen Warenverpflichtungen.",
  "We owe goods": "Wir schulden Ware",
  "Goods owed to us": "Uns wird Ware geschuldet",
  "Money positions": "Geldpositionen",
  "Money positions are unavailable.": "Geldpositionen nicht verfügbar.",
  "No recorded money position yet.": "Noch keine gebuchte Geldposition.",
  "Needs attention": "Handlungsbedarf",
  "Flight recorder": "Flugschreiber",
  "Every recorded change, in order": "Alle Änderungen in ihrer Reihenfolge",
  "All events": "Alle Ereignisse",
  "Your first action will appear here. Select an event to inspect its evidence.":
    "Deine erste Aktion erscheint hier. Klicke auf ein Ereignis, um den Nachweis zu prüfen.",
  "Choose a saved run. Its recorded history remains intact.":
    "Wähle einen gespeicherten Versuch. Seine Historie bleibt erhalten.",
  "Reality inspector": "Reality-Inspektor",
  "Recorded data": "Aufgezeichnete Daten",
  "Source received": "Quelle empfangen",
  "Document recorded": "Beleg erfasst",
  "Commitment created": "Verpflichtung angelegt",
  "Commitment fulfilled": "Verpflichtung erfüllt",
  "Stock reserved": "Ware reserviert",
  "Reservation consumed": "Reservierung verbraucht",
  "Goods shipped": "Ware versendet",
  "Opening stock recorded": "Anfangsbestand erfasst",
  "Movement recorded": "Movement erfasst",
  "Consumed quantity": "Verbrauchte Menge",
  "From location": "Von Lagerort",
  "To location": "Nach Lagerort",
  "From party": "Von Geschäftspartner",
  "To party": "An Geschäftspartner",
  "Movement type": "Bewegungsart",
  "Occurred at": "Zeitpunkt",
  "Explore your business in a private sandbox": "Entdecke dein Geschäft in einer privaten Sandbox",
  "Start with sample data, record an order and follow every change in Reality.":
    "Starte mit Beispieldaten, erfasse einen Auftrag und verfolge jede Änderung in Reality.",
  "Choose a run": "Versuch auswählen",
  "Review this action before changing Reality.": "Prüfe diese Aktion, bevor sich Reality ändert.",
  "Execution is unresolved or this step was rejected. Refresh to inspect the server state; no action will be repeated automatically.":
    "Die Ausführung ist ungeklärt oder der Schritt wurde abgelehnt. Aktualisiere den Stand; keine Aktion wird automatisch wiederholt.",
  "Archive and start a new run": "Archivieren und neuen Versuch starten",
  "Record what is physically in your warehouse. This creates a Movement.":
    "Erfasse, was physisch im Lager liegt. Dabei entsteht ein Movement.",
  "Promise goods to a customer. Stock stays unchanged until shipment.":
    "Sage einem Kunden Ware zu. Der Bestand bleibt bis zum Versand unverändert.",
  "Allocate goods to the order. Physical stock stays unchanged.":
    "Reserviere Ware für den Auftrag. Der physische Bestand bleibt unverändert.",
  "Record a full or partial delivery. Reality shows what remains owed.":
    "Erfasse eine vollständige oder teilweise Lieferung. Reality zeigt, was noch geschuldet wird.",
  "Review action": "Aktion prüfen",
  "Delivery recorded": "Lieferung erfasst",
  "Inspect the remaining obligations and exceptions. Select an event below to trace the result.":
    "Prüfe offene Verpflichtungen und Ausnahmen. Wähle unten ein Ereignis, um das Ergebnis nachzuvollziehen.",
  "Start a new Playground test": "Neuen Versuch starten",
  "Open new cockpit": "Neues Cockpit öffnen",
  proposed: "Zur Prüfung",
  executing: "In Ausführung",
  executed: "Ausgeführt",
  rejected: "Abgelehnt",
});

Object.assign(dictionaries.nl, {
  Reset: "Resetten",
  "Release reservation": "Reservering vrijgeven",
  "Edit item": "Artikel bewerken",
  Roles: "Rollen",
  "Select a record": "Selecteer een record",
  "Edit location": "Locatie bewerken",
  "Maintain reference data. This does not move goods or book money.":
    "Stamgegevens onderhouden. Dit verplaatst geen goederen en boekt geen geld.",
  "No active reservations.": "Geen actieve reserveringen.",
  "Releasing a reservation makes stock available again. The order and physical stock remain unchanged.":
    "Vrijgeven maakt de voorraad weer beschikbaar. De order en fysieke voorraad blijven ongewijzigd.",
  "Showing the latest 100 active reservations.":
    "De laatste 100 actieve reserveringen worden getoond.",
  "Customer payment": "Klantbetaling",
  "Supplier payment": "Leveranciersbetaling",
  "Document line": "Documentregel",
  "Financial evidence unavailable.": "Financieel document kon niet worden geladen.",
  Select: "Selecteren",
  "Select an open order in Open deliveries to continue.":
    "Selecteer een open order onder Open leveringen om verder te gaan.",
  "Discard failed shipment": "Mislukte verzending verwerpen",
  "Shipment quantity exceeds the open order quantity.":
    "De verzendhoeveelheid overschrijdt de openstaande orderhoeveelheid. Pas de hoeveelheid aan.",
  "Open deliveries": "Open leveringen",
  "Customers · We must deliver": "Klanten · Wij moeten leveren",
  "Suppliers · We expect goods": "Leveranciers · Wij verwachten goederen",
  "Customers · Receivables": "Klanten · Vorderingen",
  "Suppliers · Payables": "Leveranciers · Schulden",
  "Include settled items": "Vereffende posten tonen",
  "No matching open items.": "Geen overeenkomende posten.",
  Ready: "Gereed",
  "Current position": "Huidige positie",
  "All statuses": "Alle statussen",
  "Lifecycle view": "Levenscyclusweergave",
  "No items": "Geen items",
  "No matching missing information": "Geen passende ontbrekende informatie",
  "Search questions or intended use": "Vragen of beoogd gebruik doorzoeken",
  "Try another search or remove a filter.":
    "Probeer een andere zoekopdracht of verwijder een filter.",
  Question: "Vraag",
  "Current rule version": "Huidige regelversie",
  "New immutable version": "Nieuwe onveranderlijke versie",
  "Edit rule as a new version": "Regel als nieuwe versie bewerken",
  "Based on version": "Gebaseerd op versie",
  "New version": "Nieuwe versie",
  Simulation: "Simulatie",
  "Rule activation": "Regelactivering",
  "Activate this rule version?": "Deze regelversie activeren?",
  "Future matching sources will create Facts through this exact immutable rule version.":
    "Toekomstige passende bronnen maken Facts via precies deze onveranderlijke regelversie.",
  "Accepted gaps": "Geaccepteerde hiaten",
  "Some checked sources cannot use this rule":
    "Sommige gecontroleerde bronnen kunnen deze regel niet gebruiken",
  "They will not create a Fact. Activate only if missing historical fields are expected.":
    "Ze maken geen Fact. Activeer alleen als ontbrekende historische velden verwacht zijn.",
  "Created by": "Gemaakt door",
  "Rule versions": "Regelversies",
  "Test and activate": "Regel testen en activeren",
  "Rule active": "Regel actief",
  "Edit rule": "Regel bewerken",
  "Save as new rule version": "Als nieuwe regelversie opslaan",
  "Accept gaps and activate": "Hiaten accepteren en activeren",
  "Simulation result": "Simulatieresultaat",
  "The rule can be tested further": "De regel kan verder worden getest",
  "The rule needs attention": "De regel moet worden aangepast",
  "This preview changes no business data. It shows what would happen with the sources checked.":
    "Deze voorvertoning wijzigt geen bedrijfsgegevens. Ze toont wat er met de gecontroleerde bronnen zou gebeuren.",
  "Sources checked": "Bronnen gecontroleerd",
  "Facts that would be created": "Facts die zouden worden gemaakt",
  "Sources needing attention": "Bronnen die aandacht nodig hebben",
  "Show checked sources": "Gecontroleerde bronnen tonen",
  "Fact would be created": "Fact zou worden gemaakt",
  "Field is missing or has the wrong value": "Veld ontbreekt of heeft de verkeerde waarde",
  "Source needs review": "Bron moet worden beoordeeld",
  "How the missing information is completed": "Zo wordt de ontbrekende informatie aangevuld",
  "First show the answer in a real case. Reality then proposes how it should be used in the future.":
    "Laat eerst in een echte situatie zien waar de informatie nu staat. Reality stelt daarna voor hoe deze voortaan wordt gebruikt.",
  "Question captured": "Vraag vastgelegd",
  "Now: Show example": "Nu: voorbeeld tonen",
  "Example provided": "Voorbeeld toegevoegd",
  "Next: Review solution": "Daarna: oplossing beoordelen",
  "Now: Review solution": "Nu: oplossing beoordelen",
  "Solution proposed": "Oplossing voorgesteld",
  "Then: Confirm adoption": "Daarna: overname bevestigen",
  "Now: Confirm adoption": "Nu: overname bevestigen",
  "Adoption confirmed": "Overname bevestigd",
  "Investigation progress": "Voortgang van het onderzoek",
  Request: "Aanvraag",
  Examples: "Voorbeelden",
  Recommendation: "Aanbeveling",
  "Next step": "Volgende stap",
  "Show Reality where you find the answer today": "Laat Reality zien waar je het antwoord nu vindt",
  "Add one real example from Shopify, another system, an email, or current employee knowledge. Do not include passwords or unnecessary personal data.":
    "Voeg één echt voorbeeld toe uit Shopify, een ander systeem, een e-mail of de huidige kennis van een medewerker. Voeg geen wachtwoorden of onnodige persoonsgegevens toe.",
  "Example or observation": "Voorbeeld of observatie",
  "For example: In order #1042, the gift-wrap choice appears as gift_wrap = yes.":
    "Bijvoorbeeld: In bestelling #1042 staat de cadeauverpakking als gift_wrap = yes.",
  "Save example and continue": "Voorbeeld opslaan en doorgaan",
  "Ask Reality for a recommendation": "Reality om een aanbeveling vragen",
  "Reality will assess the business use and saved examples. This creates a recommendation only; it changes no business data.":
    "Reality beoordeelt het zakelijke gebruik en de opgeslagen voorbeelden. Dit maakt alleen een aanbeveling en wijzigt geen bedrijfsgegevens.",
  "Create recommendation": "Aanbeveling maken",
  "Reality recommendation": "Aanbeveling van Reality",
  "Keep this information as a source-supported business observation":
    "Deze informatie bewaren als een door de bron ondersteunde bedrijfsobservatie",
  "The saved example describes contextual business meaning rather than a physical event. Reality recommends learning it without changing the order or triggering an action.":
    "Het opgeslagen voorbeeld beschrijft zakelijke betekenis en geen fysieke gebeurtenis. Reality adviseert dit te leren zonder de bestelling te wijzigen of een actie te starten.",
  "Accept recommendation": "Aanbeveling accepteren",
  "Choose a different outcome": "Een andere uitkomst kiezen",
  "Technical model destination": "Technische modelbestemming",
  "Use different outcome": "Andere uitkomst gebruiken",
  "Technical implementation": "Technische implementatie",
  "Only open this section when a technical owner is ready to map, test, and activate the source rule.":
    "Open dit onderdeel alleen wanneer een technische eigenaar klaar is om de bronregel toe te wijzen, te testen en te activeren.",
  "History and technical details": "Geschiedenis en technische details",
  "Greater than": "Groter dan",
  "Less than": "Kleiner dan",
  "Fact observation time": "Observatietijd van de Fact",
  "When Reality received the source": "Toen Reality de bron ontving",
  "A timestamp in the source": "Een tijdstip in de bron",
  "Timestamp field path": "Veldpad van het tijdstip",
  "Rule execution summary": "Uitvoeringsoverzicht van de regel",
  "Last evaluated": "Laatst geëvalueerd",
  "Not evaluated yet": "Nog niet geëvalueerd",
  "Show sources needing attention": "Bronnen tonen die aandacht nodig hebben",
  "Show generated Facts": "Gemaakte Facts tonen",
});

Object.assign(dictionaries.es, {
  Reset: "Restablecer",
  "Release reservation": "Liberar reserva",
  "Edit item": "Editar artículo",
  Roles: "Funciones",
  "Select a record": "Seleccionar un registro",
  "Edit location": "Editar ubicación",
  "Maintain reference data. This does not move goods or book money.":
    "Mantener datos maestros. Esto no mueve mercancías ni contabiliza dinero.",
  "No active reservations.": "No hay reservas activas.",
  "Releasing a reservation makes stock available again. The order and physical stock remain unchanged.":
    "Liberar la reserva vuelve a dejar disponible la mercancía. El pedido y las existencias físicas no cambian.",
  "Showing the latest 100 active reservations.": "Se muestran las últimas 100 reservas activas.",
  "Customer payment": "Pago de cliente",
  "Supplier payment": "Pago a proveedor",
  "Document line": "Línea del documento",
  "Financial evidence unavailable.": "No se pudo cargar el documento financiero.",
  Select: "Seleccionar",
  "Select an open order in Open deliveries to continue.":
    "Selecciona un pedido abierto en Entregas pendientes para continuar.",
  "Discard failed shipment": "Descartar envío fallido",
  "Shipment quantity exceeds the open order quantity.":
    "La cantidad del envío supera la cantidad pendiente del pedido. Corrige la cantidad.",
  "Open deliveries": "Entregas pendientes",
  "Customers · We must deliver": "Clientes · Debemos entregar",
  "Suppliers · We expect goods": "Proveedores · Esperamos mercancía",
  "Customers · Receivables": "Clientes · Cuentas por cobrar",
  "Suppliers · Payables": "Proveedores · Cuentas por pagar",
  "Include settled items": "Mostrar partidas liquidadas",
  "No matching open items.": "No hay partidas coincidentes.",
  Ready: "Lista",
  "Current position": "Posición actual",
  "All statuses": "Todos los estados",
  "Lifecycle view": "Vista del ciclo de vida",
  "No items": "No hay elementos",
  "No matching missing information": "No hay información faltante coincidente",
  "Search questions or intended use": "Buscar preguntas o uso previsto",
  "Try another search or remove a filter.": "Prueba otra búsqueda o elimina un filtro.",
  Question: "Pregunta",
  "Current rule version": "Versión actual de la regla",
  "New immutable version": "Nueva versión inmutable",
  "Edit rule as a new version": "Editar regla como nueva versión",
  "Based on version": "Basada en la versión",
  "New version": "Nueva versión",
  Simulation: "Simulación",
  "Rule activation": "Activación de la regla",
  "Activate this rule version?": "¿Activar esta versión de la regla?",
  "Future matching sources will create Facts through this exact immutable rule version.":
    "Las fuentes futuras coincidentes crearán Facts mediante esta versión inmutable exacta de la regla.",
  "Accepted gaps": "Carencias aceptadas",
  "Some checked sources cannot use this rule":
    "Algunas fuentes comprobadas no pueden usar esta regla",
  "They will not create a Fact. Activate only if missing historical fields are expected.":
    "No crearán un Fact. Activa solo si se esperan campos históricos ausentes.",
  "Created by": "Creado por",
  "Rule versions": "Versiones de la regla",
  "Test and activate": "Probar y activar la regla",
  "Rule active": "Regla activa",
  "Edit rule": "Editar regla",
  "Save as new rule version": "Guardar como nueva versión de la regla",
  "Accept gaps and activate": "Aceptar carencias y activar",
  "Simulation result": "Resultado de la simulación",
  "The rule can be tested further": "La regla puede seguir probándose",
  "The rule needs attention": "La regla necesita corrección",
  "This preview changes no business data. It shows what would happen with the sources checked.":
    "Esta vista previa no modifica datos empresariales. Muestra qué ocurriría con las fuentes comprobadas.",
  "Sources checked": "Fuentes comprobadas",
  "Facts that would be created": "Facts que se crearían",
  "Sources needing attention": "Fuentes que requieren atención",
  "Show checked sources": "Mostrar fuentes comprobadas",
  "Fact would be created": "Se crearía el Fact",
  "Field is missing or has the wrong value": "Falta el campo o tiene un valor incorrecto",
  "Source needs review": "La fuente requiere revisión",
  "How the missing information is completed": "Así se completa la información que falta",
  "First show the answer in a real case. Reality then proposes how it should be used in the future.":
    "Primero muestra en un caso real dónde está hoy la información. Después, Reality propone cómo usarla en el futuro.",
  "Question captured": "Pregunta registrada",
  "Now: Show example": "Ahora: mostrar ejemplo",
  "Example provided": "Ejemplo añadido",
  "Next: Review solution": "Después: revisar solución",
  "Now: Review solution": "Ahora: revisar solución",
  "Solution proposed": "Solución propuesta",
  "Then: Confirm adoption": "Después: confirmar adopción",
  "Now: Confirm adoption": "Ahora: confirmar adopción",
  "Adoption confirmed": "Adopción confirmada",
  "Investigation progress": "Progreso de la investigación",
  Request: "Solicitud",
  Examples: "Ejemplos",
  Recommendation: "Recomendación",
  "Next step": "Siguiente paso",
  "Show Reality where you find the answer today":
    "Muestra a Reality dónde encuentras hoy la respuesta",
  "Add one real example from Shopify, another system, an email, or current employee knowledge. Do not include passwords or unnecessary personal data.":
    "Añade un ejemplo real de Shopify, otro sistema, un correo o el conocimiento actual de un empleado. No incluyas contraseñas ni datos personales innecesarios.",
  "Example or observation": "Ejemplo u observación",
  "For example: In order #1042, the gift-wrap choice appears as gift_wrap = yes.":
    "Por ejemplo: En el pedido #1042, la opción de regalo aparece como gift_wrap = yes.",
  "Save example and continue": "Guardar ejemplo y continuar",
  "Ask Reality for a recommendation": "Pedir una recomendación a Reality",
  "Reality will assess the business use and saved examples. This creates a recommendation only; it changes no business data.":
    "Reality evaluará el uso empresarial y los ejemplos guardados. Esto solo crea una recomendación y no modifica datos empresariales.",
  "Create recommendation": "Crear recomendación",
  "Reality recommendation": "Recomendación de Reality",
  "Keep this information as a source-supported business observation":
    "Conservar esta información como observación empresarial respaldada por la fuente",
  "The saved example describes contextual business meaning rather than a physical event. Reality recommends learning it without changing the order or triggering an action.":
    "El ejemplo guardado describe significado empresarial contextual y no un evento físico. Reality recomienda aprenderlo sin modificar el pedido ni activar una acción.",
  "Accept recommendation": "Aceptar recomendación",
  "Choose a different outcome": "Elegir otro resultado",
  "Technical model destination": "Destino técnico del modelo",
  "Use different outcome": "Usar otro resultado",
  "Technical implementation": "Implementación técnica",
  "Only open this section when a technical owner is ready to map, test, and activate the source rule.":
    "Abre esta sección solo cuando un responsable técnico esté listo para mapear, probar y activar la regla de origen.",
  "History and technical details": "Historial y detalles técnicos",
  "Greater than": "Mayor que",
  "Less than": "Menor que",
  "Fact observation time": "Hora de observación del Fact",
  "When Reality received the source": "Cuando Reality recibió la fuente",
  "A timestamp in the source": "Una marca de tiempo en la fuente",
  "Timestamp field path": "Ruta del campo de fecha y hora",
  "Rule execution summary": "Resumen de ejecución de la regla",
  "Last evaluated": "Última evaluación",
  "Not evaluated yet": "Aún no evaluada",
  "Show sources needing attention": "Mostrar fuentes que requieren atención",
  "Show generated Facts": "Mostrar Facts generados",
});

Object.assign(dictionaries.de, {
  "Add opening stock": "Anfangsbestand erfassen",
  "Prepare one real Movement in the sandbox. Nothing changes until you confirm it.":
    "Bereite eine echte Bewegung in der Sandbox vor. Erst durch deine Bestätigung ändert sich die Reality.",
  Item: "Artikel",
  Location: "Lagerort",
  Quantity: "Menge",
  "Review opening stock": "Anfangsbestand prüfen",
  "The server prepared this action from the selected references. Review it before changing Reality.":
    "Der Server hat diese Aktion aus den ausgewählten Stammdaten vorbereitet. Prüfe sie, bevor sich die Reality ändert.",
  Reject: "Ablehnen",
  "This step is recorded in the Reality timeline.":
    "Dieser Schritt ist in der Reality-Timeline aufgezeichnet.",
  "More learning actions are coming": "Weitere Lernaktionen folgen",
  "Reality receipt": "Reality-Nachweis",
  "The server observed the result through the shared Reality executor.":
    "Der Server hat das Ergebnis über den gemeinsamen Reality-Executor beobachtet.",
  Before: "Vorher",
  After: "Nachher",
  "Recorded Movement": "Erfasste Bewegung",
  "Event evidence": "Event-Nachweis",
  "Receipt observation is not available yet.": "Der Nachweis ist noch nicht verfügbar.",
  "Current Reality": "Aktuelle Reality",
  "Shared read models from the sandbox journal — no client-side balance calculation.":
    "Gemeinsame Read Models aus dem Sandbox-Journal — keine Bestandsberechnung im Browser.",
  "Event sequence": "Event-Sequenz",
  "Inventory view": "Bestandsansicht",
  Physical: "Physisch",
  Available: "Verfügbar",
  "No inventory rows yet.": "Noch keine Bestandszeilen.",
  Exceptions: "Abweichungen",
  "No open exceptions.": "Keine offenen Ausnahmen.",
  "Reality journal": "Reality-Journal",
  "No Reality events yet.": "Noch keine Reality-Events.",
});
Object.assign(dictionaries.nl, {
  Details: "Gegevens",
  "Missing information captured": "Ontbrekende informatie vastgelegd",
  "Open Missing information": "Ontbrekende informatie openen",
  "The question is now in the shared queue. You can open it to add evidence, review the recommendation, and decide what Reality should learn.":
    "De vraag staat nu in de gedeelde lijst. Open haar om bewijs toe te voegen, de aanbeveling te beoordelen en te beslissen wat Reality moet leren.",
  "Start in Ask Reality": "Begin met Ask Reality",
  "Found something Reality cannot answer?": "Iets gevonden dat Reality niet kan beantwoorden?",
  "Describe the missing answer in Chat. Reality will ask the necessary follow-up questions and, after your confirmation, add it to this shared queue.":
    "Beschrijf het ontbrekende antwoord in Chat. Reality stelt de nodige vervolgvragen en voegt het na jouw bevestiging toe aan deze gedeelde lijst.",
  "Nothing is added or automated until you review and confirm the request in Chat.":
    "Er wordt niets toegevoegd of geautomatiseerd totdat je het verzoek in Chat beoordeelt en bevestigt.",
  "Capture in Ask Reality": "Vastleggen in Ask Reality",
  "I found information that Reality cannot answer yet. Help me describe it and capture it as missing information.":
    "Ik heb informatie gevonden die Reality nog niet kan beantwoorden. Help me die te beschrijven en als ontbrekende informatie vast te leggen.",
  "Review unanswered business questions captured through Ask Reality and follow them through investigation and implementation.":
    "Beoordeel onbeantwoorde bedrijfsvragen uit Ask Reality en volg ze door onderzoek en implementatie.",
  Step: "Stap",
  "of 4": "van 4",
  "Tell Reality what is missing": "Vertel Reality wat ontbreekt",
  "Describe a concrete question from your daily work. Reality will save it for review; this does not change orders or automate actions.":
    "Beschrijf een concrete vraag uit je dagelijkse werk. Reality bewaart die ter beoordeling; bestellingen veranderen niet en acties worden niet geautomatiseerd.",
  "What question can you not answer right now?": "Welke vraag kun je nu niet beantwoorden?",
  "For example: Which orders should be shipped first today?":
    "Bijvoorbeeld: Welke bestellingen moeten vandaag eerst worden verzonden?",
  "Which orders should be shipped first today?":
    "Welke bestellingen moeten vandaag eerst worden verzonden?",
  "Which orders are gifts?": "Welke bestellingen zijn cadeaus?",
  "Where can I find the requested delivery method?": "Waar vind ik de gewenste bezorgmethode?",
  "Why is an order not ready to ship?": "Waarom is een bestelling nog niet verzendklaar?",
  "How will you use the answer?": "Waarvoor gebruik je het antwoord?",
  "Show it on a record": "Bij een record tonen",
  "Search or filter by it": "Erop zoeken of filteren",
  "Prioritize work": "Werk prioriteren",
  "Make a decision": "Een beslissing nemen",
  "Trigger an action later": "Later een actie starten",
  "How often do you need it?": "Hoe vaak heb je de informatie nodig?",
  "For every relevant record": "Voor elk relevant record",
  "Sometimes, for special cases": "Soms, voor bijzondere gevallen",
  "Only for this one case": "Alleen voor dit ene geval",
  "Where do you find the answer today?": "Waar vind je het antwoord nu?",
  "In the Shopify order": "In de Shopify-bestelling",
  "In another system": "In een ander systeem",
  "In an email or note": "In een e-mail of notitie",
  "A colleague knows it": "Een collega weet het",
  "I do not know yet": "Ik weet het nog niet",
  "What happens next": "Wat gebeurt hierna?",
  "Reality records this question in the shared queue. It will suggest where the answer belongs, but nothing is activated without review and confirmation.":
    "Reality zet deze vraag in de gedeelde lijst en stelt voor waar het antwoord thuishoort. Zonder beoordeling en bevestiging wordt niets geactiveerd.",
  Back: "Terug",
  "Review and capture": "Beoordelen en vastleggen",
  "Missing information": "Ontbrekende informatie",
  "Data management": "Gegevensbeheer",
  "Shared queue": "Gedeelde lijst",
  "No missing information": "Geen ontbrekende informatie",
  "Capture missing information": "Ontbrekende informatie vastleggen",
  "Capture the first business question Reality cannot answer.":
    "Leg de eerste bedrijfsvraag vast die Reality nog niet kan beantwoorden.",
  "Capture business questions Reality cannot answer yet, review source evidence, and safely teach tenant-specific Facts.":
    "Leg onbeantwoorde bedrijfsvragen vast, beoordeel bronbewijs en leer Reality veilig tenantspecifieke feiten.",
  "What can Reality not answer?": "Wat kan Reality niet beantwoorden?",
  "What decision, display, filter, or action needs the answer?":
    "Welke beslissing, weergave, filter of actie heeft het antwoord nodig?",
  "Select missing information": "Selecteer ontbrekende informatie",
  "Open an item to investigate, classify, simulate, and implement it.":
    "Open een item om het te onderzoeken, classificeren, simuleren en implementeren.",
  "Add a business answer or source observation": "Bedrijfsantwoord of bronwaarneming toevoegen",
  "Add evidence": "Bewijs toevoegen",
  "Recommend destination": "Modeldoel aanbevelen",
  "Model destination": "Modeldoel",
  Fact: "Feit",
  "Source only": "Alleen bron",
  "Typed Evidence": "Getypeerde Evidence",
  "Typed Reality": "Getypeerde Reality",
  "Projection or Exception": "Projectie of uitzondering",
  "Accept classification": "Classificatie accepteren",
  "Prepare implementation": "Implementatie voorbereiden",
  "Simulate rule": "Regel simuleren",
  "Activate rule": "Regel activeren",
  "Replay history": "Historie verwerken",
  "Disable rule": "Regel uitschakelen",
});
Object.assign(dictionaries.es, {
  Details: "Detalles",
  "Missing information captured": "Información faltante registrada",
  "Open Missing information": "Abrir información faltante",
  "The question is now in the shared queue. You can open it to add evidence, review the recommendation, and decide what Reality should learn.":
    "La pregunta ya está en la lista compartida. Ábrela para añadir evidencia, revisar la recomendación y decidir qué debe aprender Reality.",
  "Start in Ask Reality": "Empezar en Ask Reality",
  "Found something Reality cannot answer?": "¿Encontraste algo que Reality no puede responder?",
  "Describe the missing answer in Chat. Reality will ask the necessary follow-up questions and, after your confirmation, add it to this shared queue.":
    "Describe la respuesta que falta en el chat. Reality hará las preguntas necesarias y, tras tu confirmación, la añadirá a esta lista compartida.",
  "Nothing is added or automated until you review and confirm the request in Chat.":
    "Nada se añade ni automatiza hasta que revises y confirmes la solicitud en el chat.",
  "Capture in Ask Reality": "Registrar en Ask Reality",
  "I found information that Reality cannot answer yet. Help me describe it and capture it as missing information.":
    "He encontrado información que Reality aún no puede responder. Ayúdame a describirla y registrarla como información faltante.",
  "Review unanswered business questions captured through Ask Reality and follow them through investigation and implementation.":
    "Revisa preguntas empresariales sin respuesta registradas mediante Ask Reality y sigue su investigación e implementación.",
  Step: "Paso",
  "of 4": "de 4",
  "Tell Reality what is missing": "Dile a Reality qué falta",
  "Describe a concrete question from your daily work. Reality will save it for review; this does not change orders or automate actions.":
    "Describe una pregunta concreta de tu trabajo diario. Reality la guardará para revisión; esto no cambia pedidos ni automatiza acciones.",
  "What question can you not answer right now?": "¿Qué pregunta no puedes responder ahora?",
  "For example: Which orders should be shipped first today?":
    "Por ejemplo: ¿Qué pedidos deben enviarse primero hoy?",
  "Which orders should be shipped first today?": "¿Qué pedidos deben enviarse primero hoy?",
  "Which orders are gifts?": "¿Qué pedidos son regalos?",
  "Where can I find the requested delivery method?":
    "¿Dónde encuentro el método de entrega solicitado?",
  "Why is an order not ready to ship?": "¿Por qué un pedido aún no está listo para enviar?",
  "How will you use the answer?": "¿Para qué usarás la respuesta?",
  "Show it on a record": "Mostrarla en un registro",
  "Search or filter by it": "Buscar o filtrar por ella",
  "Prioritize work": "Priorizar el trabajo",
  "Make a decision": "Tomar una decisión",
  "Trigger an action later": "Iniciar una acción más adelante",
  "How often do you need it?": "¿Con qué frecuencia necesitas la información?",
  "For every relevant record": "Para cada registro relevante",
  "Sometimes, for special cases": "A veces, para casos especiales",
  "Only for this one case": "Solo para este caso",
  "Where do you find the answer today?": "¿Dónde encuentras la respuesta actualmente?",
  "In the Shopify order": "En el pedido de Shopify",
  "In another system": "En otro sistema",
  "In an email or note": "En un correo o una nota",
  "A colleague knows it": "Un compañero la conoce",
  "I do not know yet": "Aún no lo sé",
  "What happens next": "¿Qué ocurre después?",
  "Reality records this question in the shared queue. It will suggest where the answer belongs, but nothing is activated without review and confirmation.":
    "Reality registra la pregunta en la lista compartida y sugiere dónde corresponde la respuesta. Nada se activa sin revisión y confirmación.",
  Back: "Atrás",
  "Review and capture": "Revisar y registrar",
  "Missing information": "Información faltante",
  "Data management": "Gestión de datos",
  "Shared queue": "Lista compartida",
  "No missing information": "No hay información faltante",
  "Capture missing information": "Registrar información faltante",
  "Capture the first business question Reality cannot answer.":
    "Registra la primera pregunta empresarial que Reality aún no puede responder.",
  "Capture business questions Reality cannot answer yet, review source evidence, and safely teach tenant-specific Facts.":
    "Registra preguntas sin respuesta, revisa evidencia de origen y enseña Facts específicos a Reality de forma segura.",
  "What can Reality not answer?": "¿Qué no puede responder Reality?",
  "What decision, display, filter, or action needs the answer?":
    "¿Qué decisión, vista, filtro o acción necesita la respuesta?",
  "Select missing information": "Seleccionar información faltante",
  "Open an item to investigate, classify, simulate, and implement it.":
    "Abre un elemento para investigarlo, clasificarlo, simularlo e implementarlo.",
  "Add a business answer or source observation":
    "Añadir respuesta empresarial u observación de origen",
  "Add evidence": "Añadir evidencia",
  "Recommend destination": "Recomendar destino del modelo",
  "Model destination": "Destino del modelo",
  Fact: "Hecho",
  "Source only": "Solo origen",
  "Typed Evidence": "Evidence tipificada",
  "Typed Reality": "Reality tipificada",
  "Projection or Exception": "Proyección o excepción",
  "Accept classification": "Aceptar clasificación",
  "Prepare implementation": "Preparar implementación",
  "Simulate rule": "Simular regla",
  "Activate rule": "Activar regla",
  "Replay history": "Procesar historial",
  "Disable rule": "Desactivar regla",
});
Object.assign(dictionaries.de, {
  "Read product documentation": "Produktdokumentation lesen",
  "Understand concepts, integrations, interfaces and deployment.":
    "Konzepte, Integrationen, Schnittstellen und Deployment verstehen.",
  "Open Docs": "Dokumentation öffnen",
  "Back to Data settings": "Zurück zu den Dateneinstellungen",
  "Switch company": "Unternehmen wechseln",
  "Active companies": "Aktive Unternehmen",
  "Archived companies": "Archivierte Unternehmen",
  "No archived companies.": "Keine archivierten Unternehmen.",
  "Company management": "Unternehmensverwaltung",
  "Open one company to manage its complete configuration.":
    "Öffne ein Unternehmen, um seine vollständige Konfiguration zu verwalten.",
  "All records are retained, but the company is hidden from daily work.":
    "Alle Datensätze bleiben erhalten; das Unternehmen wird im Tagesgeschäft ausgeblendet.",
  Explore: "Daten prüfen",
  "Inspect and trace data": "Daten prüfen und nachvollziehen",
  "Company name": "Unternehmensname",
  "Company ID": "Unternehmens-ID",
  "Business registers": "Geschäftsregister",
  Registers: "Register",
  "Open a register to search, create, inspect or maintain records.":
    "Öffne ein Register, um Datensätze zu suchen, anzulegen, zu prüfen oder zu pflegen.",
  "Minimal customer, supplier and company references":
    "Minimale Referenzen für Kunden, Lieferanten und Unternehmen",
  "Products, services and operational classifications":
    "Produkte, Leistungen und operative Klassifikationen",
  "Warehouses and places used by movements": "Lager und Orte für Bestandsbewegungen",
  "Normalized evidence and its Reality links":
    "Normalisierte Evidence und ihre Reality-Verknüpfungen",
  "Payment terms, pricing and assignments": "Zahlungsbedingungen, Preise und Zuordnungen",
  "External origins, capabilities and intake": "Externe Quellen, Funktionen und Dateneingang",
  "Nothing needs you": "Keine Entscheidung erforderlich",
  "Reality found no current operational exceptions.":
    "Reality hat aktuell keine operativen Ausnahmen gefunden.",
  "Review derived operational risks. They disappear when Reality is corrected.":
    "Prüfe abgeleitete operative Risiken. Sie verschwinden, sobald die zugrunde liegende Reality korrigiert ist.",
  "Search exceptions…": "Ausnahmen suchen…",
  "All priorities": "Alle Prioritäten",
  "No open exceptions": "Keine offenen Ausnahmen",
  "Nothing currently requires review.": "Aktuell ist keine Prüfung erforderlich.",
  "Operations / exceptions": "Operations / Ausnahmen",
  "Operations / commitments": "Operations / Commitments",
  "Promise control": "Commitment-Steuerung",
  "Control incoming and outgoing commitments, reservation coverage and due-date risk.":
    "Steuere eingehende und ausgehende Commitments, Reservierungsdeckung und Terminrisiken.",
  "All flows": "Alle Richtungen",
  "All stock states": "Alle Bestandsstatus",
  Outgoing: "Ausgehend",
  Cancelled: "Storniert",
  Fulfilled: "Erfüllt",
  "Search party, item or ID…": "Geschäftspartner, Artikel oder ID suchen…",
  "Evidence / document register": "Evidence / Belegregister",
  "Normalized business evidence with direct links to Reality and its original source.":
    "Normalisierte geschäftliche Evidence mit direkten Verknüpfungen zu Reality und zur ursprünglichen Quelle.",
  "Import evidence": "Evidence importieren",
  "New document": "Neuer Beleg",
  "Search document, party or source…": "Beleg, Geschäftspartner oder Quelle suchen…",
  "All document types": "Alle Belegtypen",
  "Sales order": "Kundenauftrag",
  "Purchase order": "Bestellung",
  "Sales invoice": "Ausgangsrechnung",
  "Supplier invoice": "Eingangsrechnung",
  Recorded: "Erfasst",
  Posted: "Gebucht",
  "Manual evidence": "Manuelle Evidence",
  "Document register": "Belegregister",
  "Document date": "Belegdatum",
  "Document type": "Belegtyp",
  "Line items": "Positionen",
  "Add line": "Position hinzufügen",
  "Remove line": "Position entfernen",
  Quantity: "Menge",
  "Unit price": "Einzelpreis",
  "Gross amount": "Bruttobetrag",
  "Primary role": "Primäre Rolle",
  "Business roles": "Geschäftsrollen",
  "Operational defaults": "Operative Standardwerte",
  "Accounting code": "Buchhaltungskonto",
  "Credit limit": "Kreditlimit",
  "Tax identifier": "Steuer-ID",
  "External identity": "Externe Identität",
  "Optional origin reference; the complete upstream record remains in its immutable payload.":
    "Optionale Quellreferenz; der vollständige Ursprungsdatensatz bleibt im unveränderlichen Payload erhalten.",
  "Optional. Set together with the upstream External ID.":
    "Optional. Gemeinsam mit der externen ID der Quelle angeben.",
  "Edit party": "Geschäftspartner bearbeiten",
  "Back to parties": "Zurück zu Geschäftspartnern",
  "Party account and connected business evidence.":
    "Geschäftspartnerkonto und verbundene geschäftliche Evidence.",
  "Operational reference": "Operative Referenz",
  "Identity, commercial defaults and source reference.":
    "Identität, kaufmännische Standardwerte und Quellreferenz.",
  "Current position": "Aktuelle Lage",
  "Inventory control": "Bestandssteuerung",
  "Warehouse / inventory": "Lager / Bestand",
  "Warehouse / allocation": "Lager / Reservierungen",
  "Warehouse / physical journal": "Lager / Bestandsjournal",
  Reservations: "Reservierungen",
  Movements: "Bewegungen",
  "Active allocations linked directly to their customer Commitments.":
    "Aktive Reservierungen, die direkt mit ihren Customer Commitments verknüpft sind.",
  "Append-only receipts, transfers, adjustments and shipments.":
    "Unveränderlich ergänzte Wareneingänge, Umlagerungen, Korrekturen und Warenausgänge.",
  "The physical journal starts with the first receipt or opening stock.":
    "Das Bestandsjournal beginnt mit dem ersten Wareneingang oder Anfangsbestand.",
  "No reservations": "Keine Reservierungen",
  "No movements": "Keine Bewegungen",
  "Reserve stock": "Bestand reservieren",
  "Record movement": "Bewegung erfassen",
  "Reserve an open outgoing Commitment when stock becomes available.":
    "Reserviere ein offenes ausgehendes Commitment, sobald Bestand verfügbar ist.",
  "Requested delivery": "Gewünschte Lieferung",
  "Promised date": "Zugesagtes Datum",
  "Bills order line": "Rechnet Auftragsposition ab",
  "Order line id, if this bills one": "Auftragspositions-ID, falls diese Zeile eine abrechnet",
  "Reserved at": "Reserviert am",
  From: "Von",
  To: "Nach",
  Location: "Lagerort",
  Unit: "Einheit",
  Origin: "Ursprung",
  Journal: "Journal",
  "Finance / cash": "Finanzen / Zahlungen",
  "Finance / subledger": "Finanzen / Nebenbuch",
  "Receivables & payables": "Forderungen & Verbindlichkeiten",
  Receivables: "Forderungen",
  Payables: "Verbindlichkeiten",
  "Observed cash postings and their current allocation state.":
    "Erfasste Zahlungsbuchungen und ihr aktueller Zuordnungsstatus.",
  "Receivables and payables derived from postings, credits and settlement allocations.":
    "Aus Buchungen, Gutschriften und Ausgleichszuordnungen abgeleitete Forderungen und Verbindlichkeiten.",
  "Open financial items": "Offene Finanzposten",
  "Search invoice, party or ID…": "Rechnung, Geschäftspartner oder ID suchen…",
  "Search reference, party or posting…": "Referenz, Geschäftspartner oder Buchung suchen…",
  "All directions": "Alle Richtungen",
  "Import statement": "Kontoauszug importieren",
  Statement: "Kontoauszug",
  "Payment term": "Zahlungsbedingung",
  "Price resolution": "Preisermittlung",
  "Reusable rules for calculating invoice due dates.":
    "Wiederverwendbare Regeln zur Berechnung von Rechnungsfälligkeiten.",
  "Commercial prices by direction and currency.": "Kaufmännische Preise nach Richtung und Währung.",
  "Reusable customer or supplier pricing assignments.":
    "Wiederverwendbare Preiszuordnungen für Kunden oder Lieferanten.",
  "Commercial reference": "Kaufmännische Referenz",
  "Add the first rule when the business needs it.":
    "Füge die erste Regel hinzu, sobald sie fachlich benötigt wird.",
  "Import jobs and projections": "Import-Jobs und Projections",
  completed: "abgeschlossen",
  failed: "fehlgeschlagen",
  "total runs": "Läufe insgesamt",
  "Current tenant-scoped operational view": "Aktuelle tenant-begrenzte operative Ansicht",
  "Events & activity": "Events & Aktivität",
  "Activity & timeline": "Aktivität & Timeline",
  "Review business events, processing activity and exceptions over time.":
    "Business Events, Verarbeitung und Ausnahmen im Zeitverlauf prüfen.",
  "Explain the current Reality": "Aktuelle Reality erklären",
  "Start with an operational record, then follow its shortest true links through Evidence to the original SourceRecord.":
    "Beginne mit einem operativen Datensatz und folge den kürzesten echten Verknüpfungen über Evidence zum ursprünglichen SourceRecord.",
  "Search IDs and inspect connected Reality, Evidence and Source records.":
    "IDs suchen und verbundene Reality-, Evidence- und Quelldatensätze prüfen.",
  "Open Timeline": "Timeline öffnen",
  "Open Evidence": "Evidence öffnen",
  "Company settings / agents": "Unternehmenseinstellungen / Agenten",
  "Agents & AI": "Agenten & KI",
  "Copilot provider": "Copilot-Anbieter",
  "HTTPS MCP": "HTTPS MCP",
  "HTTPS endpoint": "HTTPS-Endpunkt",
  "Use this URL in your MCP client.": "Verwende diese URL in deinem MCP-Client.",
  "Tokens are scoped to this company. Reads use shared application tools; mutations still need an approval.":
    "Tokens sind auf dieses Unternehmen begrenzt. Lesezugriffe nutzen gemeinsame Anwendungstools; Änderungen brauchen weiterhin eine Freigabe.",
  "Allow all tools": "Alle Tools erlauben",
  "Includes future tools": "Schließt zukünftige Tools ein",
  "Approval required": "Freigabe erforderlich",
  "Approved, executed and rejected decisions will appear here.":
    "Freigegebene, ausgeführte und abgelehnte Entscheidungen erscheinen hier.",
  "Archive chat": "Chat archivieren",
  "Archive conversation": "Unterhaltung archivieren",
  "Archive this chat?": "Diesen Chat archivieren?",
  "Archived conversations remain available here and can be restored.":
    "Archivierte Unterhaltungen bleiben hier verfügbar und können wiederhergestellt werden.",
  "Archiving…": "Wird archiviert…",
  "Decision history": "Entscheidungsverlauf",
  "leaves the active list. Its complete history is retained and can be restored. Pending approvals remain in the decision queue.":
    "wird aus der aktiven Liste entfernt. Der vollständige Verlauf bleibt erhalten und kann wiederhergestellt werden. Offene Freigaben bleiben in der Entscheidungsübersicht.",
  "No archived chats": "Keine archivierten Chats",
  "No decision history": "Noch kein Entscheidungsverlauf",
  "No pending approvals": "Keine offenen Freigaben",
  "Nothing currently waits for approval.": "Derzeit wartet nichts auf Freigabe.",
  "Pending approvals": "Offene Freigaben",
  "Restore chat": "Chat wiederherstellen",
  "Review operational risks and every business decision that waits for approval.":
    "Prüfe operative Risiken und jede Geschäftsentscheidung, die auf Freigabe wartet.",
  "Human confirmation": "Menschliche Bestätigung",
  "Shared application service": "Gemeinsamer Anwendungsservice",
  "Operational context active": "Operativer Kontext aktiv",
  "How can I help?": "Wie kann ich helfen?",
  "Ask about inventory, commitments, payments or operational risk.":
    "Frage nach Bestand, Commitments, Zahlungen oder operativen Risiken.",
  "Delete chat": "Chat löschen",
  "Delete conversation": "Chat löschen",
  "Delete this chat?": "Diesen Chat löschen?",
  "and its complete conversation history.": "und seinen vollständigen Verlauf.",
  "Copilot prepared an action but has not changed business state.":
    "Der Copilot hat eine Aktion vorbereitet, aber den Geschäftsstatus nicht verändert.",
  Approve: "Freigeben",
  Reject: "Ablehnen",
  Send: "Senden",
  "Events today": "Events heute",
  "Orders processed": "Verarbeitete Aufträge",
  "Processing latency": "Verarbeitungslatenz",
  "Latest source": "Letzte Quelle",
  "Monitor the operating machine, isolate exceptions and trace each change to its source.":
    "Überwache den laufenden Betrieb, grenze Ausnahmen ein und verfolge jede Änderung bis zu ihrer Quelle.",
  "Business activity": "Geschäftsaktivität",
  "Raw event log": "Technisches Eventprotokoll",
  "No activity matches these filters": "Keine Aktivität entspricht diesen Filtern",
  "Source → Evidence → Reality": "Quelle → Evidence → Reality",
  "Search or type a command…": "Suchen oder Befehl eingeben…",
  "Create your first company": "Erstes Unternehmen erstellen",
  "Create empty company": "Leeres Unternehmen erstellen",
  "Try the guided demo": "Geführte Demo ausprobieren",
  "Create a sample company with an explainable order, stock, commitments and shortage.":
    "Erstelle ein Beispielunternehmen mit erklärbarem Auftrag, Bestand, Commitments und Fehlbestand.",
  "Preview demo": "Demo ansehen",
  "This will add sample business records to the new company.":
    "Dadurch werden Beispieldaten im neuen Unternehmen angelegt.",
  "Create demo company": "Demo-Unternehmen erstellen",
  "Each company gets isolated sources, facts, operational records and agent access.":
    "Jedes Unternehmen erhält isolierte Quellen, Fakten, operative Datensätze und Agentenzugriffe.",
  "Creating…": "Wird erstellt…",
  "Close company menu": "Unternehmensmenü schließen",
  "Close inspector": "Inspector schließen",
  "Close navigation": "Navigation schließen",
  "Irreversible deletion": "Unwiderrufliches Löschen",
  "This removes the company and every Source, Evidence, Reality, journal, integration and conversation belonging to it.":
    "Dies löscht das Unternehmen sowie alle zugehörigen Quellen, Evidence-, Reality- und Journaldaten, Integrationen und Chats.",
  "Enter the exact company name": "Gib den exakten Unternehmensnamen ein",
  "Enter DELETE": "Gib DELETE ein",
  "Delete permanently": "Endgültig löschen",
  "Delete company permanently": "Unternehmen endgültig löschen",
  "Deleting…": "Wird gelöscht…",
  "Working…": "Wird verarbeitet…",
  "Restore company": "Unternehmen wiederherstellen",
  "Platform administration": "Plattformverwaltung",
  "Access applications": "Zugangsanfragen",
  "Platform overview": "Plattformübersicht",
  Overview: "Übersicht",
  Deployment: "Bereitstellung",
  People: "Personen",
  "Security trail": "Sicherheitsprotokoll",
  "Loading platform state…": "Plattformstatus wird geladen…",
  Generated: "Erstellt am",
  "No recorded events yet.": "Noch keine Ereignisse aufgezeichnet.",
  "by the system": "durch das System",
  "platform admin": "Plattformadministrator",
  "email unverified": "E-Mail nicht bestätigt",
  "awaiting approval": "wartet auf Freigabe",
  "oldest application": "älteste Anfrage",
  Sessions: "Sitzungen",
  "Last login": "Letzte Anmeldung",
  Created: "Erstellt",
  Owners: "Inhaber",
  "Open invitations": "Offene Einladungen",
  "Business events": "Geschäftsereignisse",
  "imports pending": "offene Importe",
  "imports failed": "fehlgeschlagene Importe",
  "projections not ready": "nicht bereite Projektionen",
  "invitation mail stuck": "hängende Einladungs-E-Mails",
  "delivered invitations": "zugestellte Einladungen",
  "active agent tokens": "aktive Agent-Token",
  "not marked secure": "nicht als sicher markiert",
  "kept private": "bleiben vertraulich",
  "returned by the API": "werden von der API zurückgegeben",
  "missing — encrypted credentials stay unreadable":
    "fehlt – verschlüsselte Zugangsdaten bleiben unlesbar",
  "Approve only the teams you want to admit. Approval unlocks company creation.":
    "Gib nur Teams frei, die du aufnehmen möchtest. Die Freigabe aktiviert das Anlegen von Unternehmen.",
  "Create account": "Konto erstellen",
  "Start with Reality": "Mit Reality starten",
  "Create your account. We review every new workspace personally.":
    "Erstelle dein Konto. Wir prüfen jeden neuen Arbeitsbereich persönlich.",
  "Work email": "Geschäftliche E-Mail",
  Password: "Passwort",
  "At least 10 characters.": "Mindestens 10 Zeichen.",
  "I agree to the Terms and Privacy Policy.":
    "Ich stimme den Nutzungsbedingungen und der Datenschutzerklärung zu.",
  "Already have an account?": "Du hast bereits ein Konto?",
  "Sign in": "Anmelden",
  "Verify email": "E-Mail bestätigen",
  "Check your inbox": "Prüfe deinen Posteingang",
  "Verification code": "Bestätigungscode",
  "Welcome back": "Willkommen zurück",
  "Continue to your Reality workspace.": "Weiter zu deinem Reality-Arbeitsbereich.",
  "New to Reality?": "Neu bei Reality?",
  "Access requested": "Zugang angefragt",
  "You’re on the list": "Du bist auf der Warteliste",
  "Review pending": "Prüfung ausstehend",
  "We will email you when your workspace is unlocked.":
    "Wir senden dir eine E-Mail, sobald dein Arbeitsbereich freigeschaltet ist.",
  "Your name": "Dein Name",
  "Company website": "Unternehmenswebsite",
  "Orders per day": "Aufträge pro Tag",
  "Select volume": "Volumen auswählen",
  "Save details": "Angaben speichern",
  Saved: "Gespeichert",
  Workspace: "Arbeitsbereich",
  "Let agents run the business.": "Lass Agenten das Unternehmen betreiben.",
  "Stay in control.": "Behalte die Kontrolle.",
  "One operational core for facts, decisions and accountable automation.":
    "Ein operativer Kern für Fakten, Entscheidungen und verantwortbare Automatisierung.",
  Action: "Aktion",
  "Add source system": "Quellsystem hinzufügen",
  "Allow physical stock at this location": "Physischen Bestand an diesem Lagerort erlauben",
  "Change the search or create the first record.":
    "Ändere die Suche oder lege den ersten Datensatz an.",
  "Comma-separated: company, customer, supplier": "Kommagetrennt: company, customer, supplier",
  Commitment: "Commitment",
  "Commitment register": "Commitment-Register",
  Commitments: "Verpflichtungen",
  "Company settings / commercial": "Unternehmenseinstellungen / Konditionen",
  "Could not load choices:": "Auswahl konnte nicht geladen werden:",
  "Creates normalized evidence. Operational commitments remain explicit.":
    "Erzeugt normalisierte Evidence. Operative Commitments bleiben explizit.",
  "Credit note": "Gutschrift",
  Currency: "Währung",
  "Currency…": "Währung…",
  "Customer reference": "Kundenreferenz",
  Deutsch: "Deutsch",
  "Deutsch (Deutschland)": "Deutsch (Deutschland)",
  "Drop source data": "Quelldaten einspielen",
  English: "Englisch",
  "English (United Kingdom)": "Englisch (Vereinigtes Königreich)",
  Español: "Spanisch",
  "Español (España)": "Spanisch (Spanien)",
  "Fulfillment blockers": "Fulfilment-Blocker",
  "Fulfillment queue": "Fulfilment-Warteschlange",
  "Immutable source intake": "Unveränderlicher Quelldateneingang",
  Input: "Eingang",
  "Inspect & trace": "Prüfen & nachvollziehen",
  "Inspect normalized documents and their links into operational Reality.":
    "Normalisierte Belege und ihre Verknüpfungen zur operativen Reality prüfen.",
  "Item supply and demand": "Artikelangebot und -bedarf",
  "Loading choices…": "Auswahl wird geladen…",
  "Lossless JSON payload": "Verlustfreier JSON-Payload",
  "Losslessly stored input": "Verlustfrei gespeicherter Eingang",
  "Maintain only the operational references and normalized evidence Reality needs. Complete ERP records remain in their source systems.":
    "Verwalte nur die operativen Referenzen und normalisierte Evidence, die Reality benötigt. Vollständige ERP-Datensätze bleiben in ihren Quellsystemen.",
  "Maintain the small set of commercial rules Reality uses for due dates and price resolution.":
    "Verwalte die wenigen kaufmännischen Regeln, die Reality für Fälligkeiten und Preisermittlung nutzt.",
  Nederlands: "Niederländisch",
  "Nederlands (Nederland)": "Niederländisch (Niederlande)",
  New: "Neu",
  "No linked records.": "Keine verknüpften Datensätze.",
  "No recorded events for this record.": "Für diesen Datensatz wurden keine Events aufgezeichnet.",
  None: "Keine",
  Number: "Nummer",
  Occurred: "Zeitpunkt",
  "Open Items": "Offene Posten",
  "Original source payload": "Ursprünglicher Quell-Payload",
  Paid: "Bezahlt",
  Partial: "Teilweise",
  Reality: "Reality",
  "Reality inspector": "Reality Inspector",
  "Sales channel": "Vertriebskanal",
  "Search currencies…": "Währungen suchen…",
  "Search item or SKU…": "Artikel oder SKU suchen…",
  "Search or enter source system…": "Quellsystem suchen oder eingeben…",
  "Search or enter source type…": "Quelltyp suchen oder eingeben…",
  "Search party…": "Geschäftspartner suchen…",
  "Search payment term…": "Zahlungsbedingung suchen…",
  "Search payment terms…": "Zahlungsbedingungen suchen…",
  "Search ship-to party…": "Lieferempfänger suchen…",
  "Search source systems…": "Quellsysteme suchen…",
  "Search tools…": "Tools suchen…",
  "Ship-to party": "Lieferempfänger",
  "Source record": "SourceRecord",
  "Source system": "Quellsystem",
  "Tell us where you want to use Reality. You’ll receive access after a personal review.":
    "Sag uns, wo du Reality einsetzen möchtest. Nach persönlicher Prüfung erhältst du Zugang.",
  "Tenant usage": "Tenant-Nutzung",
  "This permanently deletes": "Dies löscht endgültig",
  "Traceability / business activity": "Nachvollziehbarkeit / Geschäftsaktivität",
  "Under 1,000": "Unter 1.000",
  "Unit…": "Einheit…",
  "Used when new operational records are created.":
    "Wird beim Anlegen neuer operativer Datensätze verwendet.",
  "Workspace / companies": "Arbeitsbereich / Unternehmen",
  "Act on exceptions": "Ausnahmen bearbeiten",
  "Operational reality": "Operative Realität",
  "Establish your operational truth": "Schaffe deine operative Wahrheit",
  "Connect one source or upload a file. Reality observes your company in parallel, preserves the original and shows what needs attention — without changing existing systems.":
    "Verbinde eine Quelle oder lade eine Datei hoch. Reality beobachtet dein Unternehmen parallel, bewahrt das Original und zeigt, was Aufmerksamkeit benötigt – ohne bestehende Systeme zu verändern.",
  "Current mode": "Aktueller Modus",
  "Observe only": "Nur beobachten",
  "Reality reads, records and explains. It cannot create bookings, reservations or changes in connected systems.":
    "Reality liest, protokolliert und erklärt. Es kann keine Buchungen, Reservierungen oder Änderungen in verbundenen Systemen erzeugen.",
  "No automatic changes": "Keine automatischen Änderungen",
  "Start safely": "Sicher starten",
  "Connect → Observe → Understand → Automate with control":
    "Verbinden → Beobachten → Verstehen → Kontrolliert automatisieren",
  "Reality initially runs alongside your existing systems. Its immutable record lets you verify how it sees your business before you hand over any control.":
    "Reality läuft zunächst parallel zu deinen bestehenden Systemen. Im unveränderlichen Protokoll kannst du prüfen, wie es dein Unternehmen sieht, bevor du Kontrolle übergibst.",
  "Connect first source": "Erste Quelle verbinden",
  "Connect a source": "Quelle verbinden",
  "Connect a shop, ERP, PIM, bank export or upload CSV and JSON files.":
    "Verbinde Shop, ERP, PIM oder Bankexport oder lade CSV- und JSON-Dateien hoch.",
  "Observe in parallel": "Parallel beobachten",
  "Reality builds its operational books without changing the systems that run your company.":
    "Reality baut seine operativen Bücher auf, ohne die Systeme zu verändern, die dein Unternehmen steuern.",
  "Understand facts and exceptions": "Fakten und Ausnahmen verstehen",
  "See commitments, inventory, money and contradictions with a trace to their original source.":
    "Sieh Commitments, Bestand, Geld und Widersprüche mit direkter Spur zur ursprünglichen Quelle.",
  "Automate with control": "Kontrolliert automatisieren",
  "Move from observation to human confirmation and later to explicitly approved automation.":
    "Wechsle vom Beobachten zur menschlichen Bestätigung und später zu ausdrücklich freigegebener Automatisierung.",
  "Add a source": "Quelle hinzufügen",
  "Add a source or upload a file, then review its interpreted operational observations.":
    "Füge eine Quelle hinzu oder lade eine Datei hoch und prüfe anschließend die interpretierten operativen Beobachtungen.",
  "All facts": "Alle Fakten",
  "Ask what to do next": "Nach dem nächsten Schritt fragen",
  "Connect a system or upload CSV, JSON or another source file.":
    "Verbinde ein System oder lade eine CSV-, JSON- oder andere Quelldatei hoch.",
  "Current derived view": "Aktuelle abgeleitete Ansicht",
  "Current exceptions": "Aktuelle Ausnahmen",
  "Explicit, source-supported observations currently retained by Reality. Facts never replace their immutable source.":
    "Explizite, durch Quellen belegte Beobachtungen, die Reality aktuell verwaltet. Fakten ersetzen niemals ihre unveränderliche Quelle.",
  "Facts appear when a source-backed observation is interpreted.":
    "Fakten erscheinen, sobald eine durch Quellen belegte Beobachtung interpretiert wurde.",
  "Inventory position": "Bestandsposition",
  "No explicit facts yet": "Noch keine expliziten Fakten",
  "No facts yet": "Noch keine Fakten",
  "Nothing needs attention": "Keine Aufmerksamkeit erforderlich",
  "Only operationally useful fields become typed Reality.":
    "Nur operativ benötigte Felder werden Teil der typisierten Reality.",
  "Open warehouse view": "Lageransicht öffnen",
  "Operational facts": "Operative Fakten",
  "Operational workspaces appear when orders, stock or finance become available.":
    "Operative Arbeitsbereiche erscheinen, sobald Aufträge, Bestand oder Finanzdaten verfügbar sind.",
  "Read-only answers are immediate. Any change to business Reality waits for an approval until a person confirms it.":
    "Reine Leseantworten erfolgen sofort. Jede Änderung an der geschäftlichen Reality wartet auf eine Freigabe, bis ein Mensch sie bestätigt.",
  "Reality / facts": "Reality / Fakten",
  "Reality found no current operational contradiction or uncovered promise.":
    "Reality hat aktuell keinen operativen Widerspruch und kein ungedecktes Commitment gefunden.",
  "Review all": "Alle prüfen",
  "Review recognized facts": "Erkannte Fakten prüfen",
  "Source → Evidence → Facts → Decisions": "Quelle → Evidence → Fakten → Entscheidungen",
  "Sources & imports": "Quellen & Imports",
  "Start small": "Klein starten",
  "What can be decided": "Was entschieden werden kann",
  "What is true": "Was wahr ist",
  "How Reality may act": "Wie Reality handeln darf",
  Automation: "Automatisierung",
  "Current stage": "Aktuelle Stufe",
  Observe: "Beobachten",
  "Stage 1": "Stufe 1",
  "Let Reality observe first. Check whether its agents understand your business correctly before enabling proposals or execution.":
    "Lass Reality zuerst beobachten. Prüfe, ob die Agenten dein Geschäft richtig verstehen, bevor du Vorschläge oder Ausführungen freigibst.",
  "Check order readiness": "Versandbereitschaft von Aufträgen prüfen",
  "Prepare inventory reservations": "Bestandsreservierungen vorbereiten",
  "Detect execution holds": "Ausführungssperren erkennen",
  "Match incoming payments": "Zahlungseingänge zuordnen",
  "Monitor delivery commitments": "Lieferzusagen überwachen",
  "5 capabilities are being observed": "5 Fähigkeiten werden beobachtet",
  "First verify that Reality understands your business. Nothing is changed automatically.":
    "Prüfe zuerst, ob Reality dein Geschäft versteht. Nichts wird automatisch geändert.",
  "Orders, commitments and holds": "Aufträge, Commitments und Sperren",
  "Inventory and reservations": "Bestand und Reservierungen",
  "Payments and open items": "Zahlungen und offene Posten",
  "Approvals can be enabled later": "Freigaben können später aktiviert werden",
  "Where to begin": "Wo du beginnst",
  "Step 1": "Schritt 1",
  "Reality knows only what a source shows it. Nothing is imported until you accept it.":
    "Reality kennt nur, was eine Quelle zeigt. Nichts wird importiert, bevor du es annimmst.",
  "Connect a system or upload a file": "System verbinden oder Datei hochladen",
  "Accept the records you want interpreted":
    "Die Datensätze annehmen, die interpretiert werden sollen",
  "Verify the facts Reality derives": "Die von Reality abgeleiteten Fakten prüfen",
  "awaiting explicit confirmation": "wartet auf ausdrückliche Bestätigung",
  "Example preview · no live data": "Beispielvorschau · keine Echtdaten",
  "These could be your operational numbers": "So könnten deine operativen Kennzahlen aussehen",
  "Connect a source and Reality observes how reliably orders flow through your company—without changing anything.":
    "Verbinde eine Quelle und Reality beobachtet, wie zuverlässig Aufträge durch dein Unternehmen laufen – ohne etwas zu verändern.",
  "Connect your data": "Daten verbinden",
  "ready to ship today": "heute versandbereit",
  "Ready to ship": "Versandbereit",
  "Waiting for stock": "Wartet auf Bestand",
  Blocked: "Blockiert",
  "Unclear data": "Unklare Daten",
  "orders could ship today": "Aufträge könnten heute rausgehen",
  "orders likely to be late": "Aufträge werden wahrscheinlich verspätet",
  "revenue currently blocked": "Umsatz ist aktuell blockiert",
  "Largest opportunity": "Größter Hebel",
  "Release 5 more orders": "5 weitere Aufträge freigeben",
  "Two inventory transfers could cover the missing reservations.":
    "Zwei Bestandsumbuchungen könnten die fehlenden Reservierungen abdecken.",
  "Example insight generated from operational facts": "Beispielerkenntnis aus operativen Fakten",
  "Observed automation potential": "Beobachtetes Automatisierungspotenzial",
  "of recent decisions were unambiguous. Reality would still only observe at this stage.":
    "der letzten Entscheidungen waren eindeutig. Reality würde in dieser Stufe trotzdem nur beobachten.",
  "Shipping readiness": "Versandbereitschaft",
  today: "heute",
  "+12 pp": "+12 Prozentpunkte",
  "in the example period": "im Beispielzeitraum",
  "Order flow": "Auftragsfluss",
  "can ship today": "können heute rausgehen",
  "3 at risk": "3 gefährdet",
  "need attention": "benötigen Aufmerksamkeit",
  "Blocked revenue": "Blockierter Umsatz",
  "−44%": "−44 %",
  "over 30 days": "in 30 Tagen",
  "Automation potential": "Automatisierungspotenzial",
  unambiguous: "eindeutig",
  "Still observe only": "Weiterhin nur beobachten",
  "Example · last 30 days": "Beispiel · letzte 30 Tage",
  "Operational trend": "Operativer Verlauf",
  "Late orders": "Verspätete Aufträge",
  "Orders received & shipped": "Auftragseingang & Versand",
  "Orders received": "Eingegangen",
  Shipped: "Versendet",
  "Open backlog": "Offener Auftragsbestand",
  Example: "Beispiel",
  days: "Tage",
  "Example orders received and shipped by day":
    "Beispiel für täglich eingegangene und versendete Aufträge",
  "Chart period": "Diagrammzeitraum",
  "Typical operating pattern": "Typischer Betriebsverlauf",
  "Monday clears the weekend backlog": "Montag baut den Wochenendrückstand ab",
  "Orders continue at weekends while shipping follows warehouse cut-off times.":
    "Aufträge gehen auch am Wochenende ein, während der Versand den Cut-off-Zeiten des Lagers folgt.",
  "30 days ago": "Vor 30 Tagen",
  Today: "Heute",
  "Example insights · no live data": "Beispielerkenntnisse · keine Echtdaten",
  "What Reality could reveal next": "Was Reality als Nächstes erkennen könnte",
  "Cross-domain signals connect causes directly to their business impact.":
    "Bereichsübergreifende Signale verbinden Ursachen direkt mit ihrer geschäftlichen Wirkung.",
  "Supplier reliability": "Lieferantentreue",
  "Nordlicht delivers only 78% on time": "Nordlicht liefert nur zu 78 % termingerecht",
  "7 orders": "7 Aufträge",
  "are currently exposed": "sind aktuell gefährdet",
  "Problem item": "Problematischer Artikel",
  "Bike Light causes 43% of delays": "Bike Light verursacht 43 % aller Verzögerungen",
  "Recurring gap before the next receipt": "Wiederkehrende Lücke vor dem nächsten Wareneingang",
  "Tied-up business": "Gebundenes Geschäft",
  "€24,600 waits for stock or approval": "24.600 € warten auf Bestand oder Freigabe",
  "Stock · data quality · execution hold": "Bestand · Datenqualität · Ausführungssperre",
  "Avoidable work": "Vermeidbare Arbeit",
  "12 of 18 decisions were repeatable": "12 von 18 Entscheidungen waren wiederholbar",
  "Observe first, automate when trusted": "Erst beobachten, bei Vertrauen automatisieren",
  "Example trace · no live data": "Beispiel-Trace · keine Echtdaten",
  "How one order became operational reality": "Wie ein Auftrag zur operativen Realität wurde",
  "Shop order received": "Shop-Auftrag eingegangen",
  "Sales order SO-10428": "Kundenauftrag SO-10428",
  "Order quantity confirmed": "Auftragsmenge bestätigt",
  "Shipping commitment": "Versand-Commitment",
  "Inventory reserved": "Bestand reserviert",
  "Shipment posted": "Versand gebucht",
  "Longest wait": "Längste Wartezeit",
  "4 h 19 min until shipment": "4 Std. 19 Min. bis zum Versand",
  "The complete path remains traceable to the immutable shop payload.":
    "Der vollständige Pfad bleibt bis zum unveränderlichen Shop-Payload nachvollziehbar.",
  "The original remains immutable and every number stays traceable.":
    "Das Original bleibt unveränderlich und jede Kennzahl nachvollziehbar.",
  "What needs attention": "Was Aufmerksamkeit benötigt",
  "You do not need a data migration. Connect a source or upload a file; the immutable original remains available at every step.":
    "Du brauchst keine Datenmigration. Verbinde eine Quelle oder lade eine Datei hoch; das unveränderliche Original bleibt bei jedem Schritt verfügbar.",
});

Object.assign(dictionaries.de, {
  "· Manual operational reference": "· Manuelle Betriebsanleitung",
  "4 h 19 min": "4 h 19 min",
  "47 min": "47 min",
  "A paid order is blocked despite available inventory. Reality connects the payment, commitment, reservation and delivery hold — then proposes the exact resolution with its evidence.":
    "Eine bezahlte Bestellung ist trotz verfügbarer Lagerbestände gesperrt. Reality verbindet die Zahlung, den Auftrag, die Reservierung und die Auslieferung – und schlägt die genaue Lösung mit seinen Beweisen vor.",
  "A person confirms the exact business effect.":
    "Eine Person bestätigt den genauen Geschäftseffekt.",
  "A recommendation or controlled action with its reason intact.":
    "Eine Empfehlung oder kontrollierte Aktion mit ihrer Begründung.",
  "Accepted payloads stay lossless and traceable":
    "Akzeptierte Daten bleiben verlustfrei und nachvollziehbar",
  "Agents use the same tenant-scoped application tools as the UI and CLI. Permissions, confirmation and evidence remain part of the operating model.":
    "Agenten verwenden die gleichen tenant-spezifischen Anwendungs-Tools wie die UI und CLI. Berechtigungen, Bestätigungen und Beweise bleiben Teil des Betriebskonzepts.",
  "All tools": "Alle Tools",
  "Already have access? Sign in": "Haben Sie bereits Zugriff? Anmelden",
  AP: "AP",
  "Approve & execute": "Genehmigen & ausführen",
  "Approve and execute this action?": "Möchten Sie diese Aktion genehmigen und ausführen?",
  AR: "AR",
  "Audit Trail": "Audit Trail",
  "Auditable structure": "Auditable Struktur",
  "Auf Deutsch wechseln": "Auf Deutsch wechseln",
  "Ausgewählte Payloads fließen aus bestehenden Systemen in Reality":
    "Ausgewählte Daten fließen aus bestehenden Systemen in Reality",
  "Ausgewählter Payload · verlustfrei bewahrt": "Ausgewählte Daten · verlustfrei gespeichert",
  Automate: "Automatisieren",
  "automatic access slots used": "automatische Zugriffsfenster werden verwendet",
  "AUTONOMOUS COMMERCE CORE": "AUTONOMOUS COMMERCE CORE",
  "Autonomy is granted per capability — never for everything at once.":
    "Autonomie wird pro Fähigkeit gewährt – nie für alles auf einmal.",
  "Autonomy is never a global switch. Every capability advances only after its observations and recommendations have earned trust.":
    "Autonomie ist niemals ein globaler Schalter. Jede Fähigkeit wird erst dann freigeschaltet, wenn ihre Beobachtungen und Empfehlungen Vertrauen erworben haben.",
  "AUTONOMY UNLOCKED": "AUTONOMIE FREIGEBEN",
  "Build an operational picture you can verify before granting any agent permission to act.":
    "Erstellen Sie ein verifizierbares Betriebs-Szenario, bevor Sie einem Agenten die Erlaubnis erteilen, zu handeln.",
  "Choose allowed tools": "Wählen Sie die erlaubten Werkzeuge",
  Classification: "Klassifizierung",
  Commerce: "E-Commerce",
  "Company settings / data": "Firmen-Einstellungen / Daten",
  "Configured — leave empty to keep": "Konfiguriert – leer lassen, um dies beizubehalten",
  Connect: "Verbinden",
  "Connect external origins, upload files and test the same immutable intake used by integrations.":
    "Verbinden Sie externe Quellen, laden Sie Dateien hoch und testen Sie die gleiche unveränderliche Dateneingabe, die von Integrationen verwendet wird.",
  "Connect one source. Start by observing.":
    "Verbinden Sie eine Quelle. Beginnen Sie mit der Beobachtung.",
  "Connect the tools your business already runs on.":
    "Verbinden Sie die Werkzeuge, die Ihr Unternehmen bereits verwendet.",
  "Connect your business": "Verbinden Sie Ihr Unternehmen",
  Continue: "Weiter",
  "Control remains explicit at every level.": "Die Kontrolle bleibt auf jeder Ebene explizit.",
  Copied: "Kopiert",
  "Copy URL": "Kopieren Sie URL",
  "Create document": "Dokument erstellen",
  "Create scoped token": "Erstellen Sie einen begrenzten Token",
  "Create source": "Quelle erstellen",
  "Create your account": "Erstellen Sie Ihr Konto",
  "Creating account…": "Erstellung des Kontos…",
  "Custom source": "Benutzerdefinierte Quelle",
  "Data / immutable intake": "Daten / unveränderliche Dateneingabe",
  "Data received from": "Daten, die von",
  "Data stays in its systems. Reality retains only what operations need — losslessly and traceably.":
    "Daten verbleiben in ihren Systemen. Reality speichert nur das, was für die Abläufe benötigt wird – verlustfrei und nachvollziehbar.",
  DE: "DE",
  Decision: "Entscheidung",
  Delegate: "Delegieren",
  "Delegate step by step": "Delegieren schrittweise",
  DELETE: "LÖSCHEN",
  "Display name": "Anzeigetitel",
  "Document link · Timestamp · Lineage · Change log · Tenant scope · Confirmation":
    "Dokumentverknüpfung · Zeitstempel · Abstammung · Änderungsverlauf · Tenant-Umfang · Bestätigung",
  "Enter a new value": "Geben Sie einen neuen Wert ein",
  "Every answer stays connected to what actually happened.":
    "Jede Antwort bleibt mit dem tatsächlich Geschehen verbunden.",
  "Evidence, permissions and confirmation remain part of every step.":
    "Beweise, Berechtigungen und Bestätigungen bleiben Teil jedes Schritts.",
  "EXAMPLE CAPABILITY": "BEISPIEL-FUNKTIONALITÄT",
  "Execute only the proven capability within explicit rules.":
    "Führen Sie nur die nachgewiesene Funktionalität innerhalb expliziter Regeln aus.",
  EXPLAIN: "ERKLÄREN",
  Facts: "Fakten",
  "Facts · Commitments · Reservations · Movements · Lots · Serials · SSCC":
    "Fakten · Verpflichtungen · Reservierungen · Bewegungen · Chargen · Serien · SSCC",
  "Facts, commitments and movements used by operations.":
    "Fakten, Verpflichtungen und Bewegungen, die von den Abläufen verwendet werden.",
  "Finance Ledger": "Finanzbuch",
  "From original evidence to the ledger. Linked end to end.":
    "Von den ursprünglichen Beweisen bis zum Buch. End-zu-End-Verbindung.",
  "Get started": "Starten",
  "No data yet": "Noch keine Daten",
  "Give agents responsibility one capability at a time.":
    "Übertragen Sie Agenten die Verantwortung für eine Funktionalität nach der anderen.",
  "Here is what Reality knows": "Hier ist, was Reality kennt",
  "https://…/v1": "https://…/v1",
  "Immutable SourceRecords · Versioned payloads · Documents · Document lines":
    "Unveränderliche SourceRecords · Versionierte Payloads · Dokumente · Dokumentzeilen",
  Infrastructure: "Infrastruktur",
  "Instance code": "Instanzcode",
  Invoicing: "Rechnungstellung",
  "LEARNS FROM EVIDENCE": "LERNT AUS BEWEISST",
  "Ledger / Action": "Hauptbuch / Aktion",
  "Ledger entries · Open items · Allocations · Payments · Settlement · Reconciliation":
    "Hauptbuch-Einträge · Offene Posten · Zuordnungen · Zahlungen · Abrechnung · Abgleich",
  "Loading available systems…": "Systeme werden geladen…",
  "Loading…": "Wird geladen…",
  "Main navigation": "Hauptnavigation",
  "Maintain payment terms, price lists and pricing groups used for due dates and price resolution.":
    "Verwalten Sie Zahlungsbedingungen, Preislisten und Preisgruppen, die für Fälligkeitstermine und Preisermittlung verwendet werden.",
  "Monitor import jobs and the rebuildable projections used by the product.":
    "Überwachen Sie Importjobs und die wiederherstellbaren Prognosen, die von der Anwendung verwendet werden.",
  No: "Nein",
  "No business state will be changed. The rejection remains visible in the conversation history.":
    "Kein Geschäftszustand wird geändert. Die Ablehnung ist weiterhin im Gesprächsverlauf sichtbar.",
  "No commitments.": "Keine Verpflichtungen.",
  "No documents.": "Keine Dokumente.",
  "no due date": "kein Fälligkeitstermin",
  "No matching records": "Keine übereinstimmenden Aufzeichnungen",
  "No stock": "Kein Lagerbestand",
  "Nur bei operativem Nutzen typisiert": "Nur bei operativem Nutzen typisiert",
  OBSERVE: "BEWACHEN",
  "Observe what matters": "Beobachten Sie, was wichtig ist",
  "One exception. One explainable resolution.": "Eine Ausnahme. Eine erklärbare Lösung.",
  "One operational core. Your systems remain in place.":
    "Ein operativer Kern. Ihre Systeme bleiben bestehen.",
  "Only operationally useful fields become typed Reality":
    "Nur betrieblich relevante Felder werden typisiert Reality",
  "Open navigation": "Öffne die Navigation",
  "OPERATIONAL CORE": "OPERATIONAL CORE",
  "Operational Reality": "Betriebliche Realität",
  "Operations / decision queue": "Operationen / Entscheidungs-Queue",
  "Operations / promise control": "Operationen / Versprechen-Kontrolle",
  "Orders, stock, payments and promises are observed together. Reality exposes contradictions, business impact and the source evidence behind every conclusion.":
    "Bestellungen, Lagerbestände, Zahlungen und Versprechen werden zusammen betrachtet. Die Realität deckt Widersprüche, Geschäftsauswirkungen und den zugrunde liegenden Beweis für jede Schlussfolgerung auf.",
  "Payload must be valid JSON.": "Der Payload muss ein gültiges JSON sein.",
  "Payment terms, price lists and pricing groups":
    "Zahlungsbedingungen, Preislisten und Preisgruppen",
  "permanently?": "dauerhaft?",
  "PostgreSQL fact journal · Append-only records · S3-compatible object store · Projections · Backups / PITR":
    "PostgreSQL Faktenjournal · Append-only Aufzeichnungen · S3-kompatibler Objektspeicher · Projections · Backups / PITR",
  "Prepare a precise next action and show the evidence.":
    "Bereite eine präzise nächste Aktion vor und zeige den Beweis.",
  "Read, reconcile and explain without changing business state.":
    "Lies, vergleiche und erkläre, ohne den Geschäftszustand zu verändern.",
  "Reality · Autonomous commerce core": "Realität · Autonomer Handelskern",
  "Reality connects operational data into an explainable business reality — a trusted foundation for decisions and step-by-step autonomy.":
    "Realität verbindet betriebliche Daten in eine erklärbare Geschäftswelt – eine vertrauenswürdige Grundlage für Entscheidungen und schrittweise Autonomie.",
  "Reality home": "Realität Home",
  "Reality is not another ERP. It receives selected operational events, preserves their source evidence and types only what is repeatedly needed to understand, decide and act.":
    "Realität ist kein ERP. Es empfängt ausgewählte betriebliche Ereignisse, bewahrt ihre Quelle und Arten, nur was wiederholt benötigt wird, um zu verstehen, zu entscheiden und zu handeln.",
  "Reality separates original data, evidence, operational truth and the ledger — while keeping their lineage verifiable through the shortest true links.":
    "Realität trennt Originaldaten, Beweise, betriebliche Wahrheit und das Ledger – während sie ihre Herkunft durch die kürzesten echten Links verifizierbar halten.",
  "Reality stores before it interprets. The shortest true links keep every operational conclusion explainable.":
    "Realität speichert, bevor sie interpretiert. Die kürzesten echten Links halten jede betriebliche Schlussfolgerung erklärbar.",
  "Reality watches before agents touch the business.":
    "Realität beobachtet, bevor Agenten die Geschäftstätigkeit ausführen.",
  "Reality will execute exactly this action through the shared application service and record its result.":
    "Reality führt genau diese Aktion über den gemeinsamen Anwendungsservice aus und protokolliert das Ergebnis.",
  Recommend: "Empfehlen",
  "Record & enqueue": "Aufzeichnen & Einreihen",
  "Recording…": "Aufzeichnen…",
  "Register an external origin and choose exactly which record types Reality may receive.":
    "Registriere eine externe Quelle und wähle genau, welche Aufzeichnungstypen Reality empfangen darf.",
  "Reject this action?": "Diese Aktion ablehnen?",
  "Resolve delivery holds": "Lieferengstelle lösen",
  "Save changes": "Änderungen speichern",
  "See the operating model": "Betriebsmodell einsehen",
  "See what is true, what needs attention and what can be delegated next.":
    "Was ist wahr, was erfordert Aufmerksamkeit und was kann als nächstes delegiert werden?",
  "Select a system…": "System auswählen…",
  "Select only the upstream types this instance is responsible for.":
    "Wählen Sie nur die Upstream-Typen, für die diese Instanz verantwortlich ist.",
  "Selected operational signals only": "Ausgewählte Betriebssignale",
  "Selected payload · retained losslessly": "Ausgewählte Payloads · verlustfrei gespeichert",
  "Selected payloads flow from existing systems into Reality":
    "Ausgewählte Payloads fließen von bestehenden Systemen in Reality",
  "shared application tools. Mutations still require the Reality approval boundary.":
    "gemeinsame Anwendungs-Tools. Mutationen erfordern weiterhin die Reality-Genehmigungsgrenze.",
  "So agents can operate your business with confidence.":
    "Damit können Agenten Ihr Unternehmen selbstbewusst führen.",
  "Source definition": "Quelldefinition",
  "Source systems remain authoritative": "Quellsysteme bleiben autoritativ",
  "Source templates available in Reality today. Transport and credentials remain explicit per connector.":
    "Quellvorlagen sind heute in Reality verfügbar. Transport und Credentials bleiben explizit pro Connector.",
  "Stable within this company, for example shopify_de.":
    "Stabil innerhalb dieses Unternehmens, z.B. shopify_de.",
  "Start in observation mode": "Im Beobachtungsmodus starten",
  "Stock enabled": "Lagerbestand aktiviert",
  "Supports traceable and verifiable ERP processes aligned with GoBD principles. Actual compliance also depends on operations, internal controls, retention and process documentation.":
    "Unterstützt nachvollziehbare und überprüfbare ERP-Prozesse, die mit GoBD-Prinzipien übereinstimmen. Die tatsächliche Einhaltung hängt auch von den Abläufen, internen Kontrollen, der Aufbewahrung und der Prozessdokumentation ab.",
  "System template": "Systemvorlage",
  "Systeme bleiben führend": "Systeme bleiben führend",
  "Systems remain authoritative": "Systeme bleiben autoritativ",
  "The first verified accounts are admitted automatically. After that, applications wait for your decision.":
    "Die ersten verifizierten Konten werden automatisch angenommen. Danach warten die Anwendungen auf Ihre Entscheidung.",
  "The Operations Cockpit turns connected records into a daily control surface — exceptions first, evidence one step away, agent responsibility always visible.":
    "Das Operations Cockpit wandelt verbundene Aufzeichnungen in eine tägliche Steuerungsumgebung um – zuerst Ausnahmen, Beweise einen Schritt entfernt, Verantwortlichkeit der Agenten immer sichtbar.",
  "The selected upstream payload, retained losslessly and versioned.":
    "Die ausgewählte Upstream-Datenmenge, verlustfrei gespeichert und versioniert.",
  "This creates a definition only. It does not connect to the external system or store credentials.":
    "Dies erstellt lediglich eine Definition. Es verbindet sich nicht mit dem externen System oder speichert Anmeldeinformationen.",
  "Thousands of events become a small number of clear exceptions that need attention.":
    "Tausende von Ereignissen werden zu einer kleinen Anzahl klarer Ausnahmen, die Aufmerksamkeit erfordern.",
  "Traceability / timeline": "Nachverfolgung / Zeitleiste",
  "TRUST INCREASES": "VERTRAUEN STEIGT",
  "Typed only when operationally useful": "Nur bei betrieblicher Notwendigkeit typisiert",
  UNDERSTAND: "VERSTEHEN",
  "Use a name operators recognize.": "Verwenden Sie einen Namen, den Betreiber erkennen.",
  "Use source templates for modern commerce systems, immutable API intake, or controlled CSV and JSON imports. Each origin declares exactly which records Reality may receive.":
    "Verwenden Sie Vorlagen für moderne Commerce-Systeme, unveränderliche API-Eingabe oder kontrollierte CSV- und JSON-Importe. Jede Quelle gibt genau an, welche Aufzeichnungen Reality empfangen darf.",
  "Warehouse / stock control": "Lager / Bestandsverwaltung",
  "What an order, invoice, payment or file actually asserted.":
    "Was eine Bestellung, Rechnung, Zahlung oder Datei tatsächlich belegt.",
  "What conflicts?": "Welche Konflikte?",
  "What evidence proves it?": "Welche Beweise belegen dies?",
  "What external origin does this represent?": "Welche externe Quelle repräsentiert dies?",
  "What happened?": "Was ist passiert?",
  Yes: "Ja",
  "Your systems stay in place. Nothing changes automatically.":
    "Ihre Systeme bleiben unverändert. Nichts ändert sich automatisch.",
  Chats: "Chats",
  "Archived chats": "Archivierte Chats",
  "Back to chats": "Zurück zu Chats",
  Code: "Code",
  Deutsch: "Deutsch",
  "Deutsch (Deutschland)": "Deutsch (Deutschland)",
  Events: "Ereignisse",
  Explorer: "Explorer",
  "HTTPS MCP": "HTTPS MCP",
  Name: "Name",
  Operations: "Operationen",
  Projection: "Projektion",
  Projections: "Projektionen",
  "Reality Explorer": "Reality Explorer",
  Status: "Status",
  System: "System",
  Tool: "Werkzeug",
  Version: "Version",
});

Object.assign(dictionaries.nl, {
  "Archived chats": "Gearchiveerde chats",
  "Back to chats": "Terug naar chats",
  "Read product documentation": "Productdocumentatie lezen",
  "Understand concepts, integrations, interfaces and deployment.":
    "Begrijp concepten, integraties, interfaces en implementatie.",
  "Open Docs": "Documentatie openen",
  "· Manual operational reference": "· Handmatige operationele referentie",
  "+12 pp": "+12 eenheden",
  "€24,600 waits for stock or approval": "€24.600 wacht op voorraad of goedkeuring",
  "12 of 18 decisions were repeatable": "12 van 18 beslissingen waren herhaalbaar",
  "24 hours": "24 uur",
  "3 at risk": "3 in risico",
  "30 days": "30 dagen",
  "4 h 19 min": "4 uur 19 minuten",
  "4 h 19 min until shipment": "4 uur 19 minuten tot verzending",
  "47 min": "47 minuten",
  "7 days": "7 dagen",
  "7 orders": "7 bestellingen",
  "A company contains its own sources, operational records and agent configuration.":
    "Een bedrijf bevat zijn eigen bronnen, operationele records en agentconfiguratie.",
  "A paid order is blocked despite available inventory. Reality connects the payment, commitment, reservation and delivery hold — then proposes the exact resolution with its evidence.":
    "Een betaalde bestelling is geblokkeerd ondanks beschikbare voorraad. Reality verbindt de betaling, commitment, reservatie en levering — en stelt het exacte oplossingsvoorstel voor met zijn bewijs.",
  "A person confirms the exact business effect.":
    "Een persoon bevestigt het exacte zakelijke effect.",
  "A recommendation or controlled action with its reason intact.":
    "Een aanbeveling of gecontroleerde actie met zijn reden intact.",
  Accepted: "Geaccepteerd",
  "Accepted payloads stay lossless and traceable":
    "Geaccepteerde payloads blijven lossless en traceerbaar",
  Access: "Toegang",
  "Access applications": "Toegang tot applicaties",
  "Platform overview": "Platformoverzicht",
  Overview: "Overzicht",
  Deployment: "Implementatie",
  People: "Mensen",
  "Security trail": "Beveiligingsspoor",
  "Loading platform state…": "Platformstatus wordt geladen…",
  Generated: "Gegenereerd",
  "No recorded events yet.": "Nog geen gebeurtenissen vastgelegd.",
  "by the system": "door het systeem",
  "platform admin": "platformbeheerder",
  "email unverified": "e-mail niet geverifieerd",
  "awaiting approval": "wacht op goedkeuring",
  "oldest application": "oudste aanvraag",
  Sessions: "Sessies",
  "Last login": "Laatste aanmelding",
  Created: "Aangemaakt",
  Owners: "Eigenaren",
  "Open invitations": "Openstaande uitnodigingen",
  "Business events": "Bedrijfsgebeurtenissen",
  "imports pending": "openstaande imports",
  "imports failed": "mislukte imports",
  "projections not ready": "projecties niet gereed",
  "invitation mail stuck": "vastgelopen uitnodigingsmail",
  "delivered invitations": "bezorgde uitnodigingen",
  "active agent tokens": "actieve agent-tokens",
  "not marked secure": "niet als veilig gemarkeerd",
  "kept private": "blijven privé",
  "returned by the API": "worden door de API geretourneerd",
  "missing — encrypted credentials stay unreadable":
    "ontbreekt – versleutelde inloggegevens blijven onleesbaar",
  "Access requested": "Toegang gevraagd",
  Account: "Rekening",
  "Accounting code": "Rekeningcode",
  Action: "Actie",
  Actions: "Acties",
  Activate: "Activeren",
  Active: "Actief",
  "Active allocations linked directly to their customer Commitments.":
    "Actieve toewijzingen zijn direct gekoppeld aan hun klant-verplichtingen.",
  "Active companies": "Actieve bedrijven",
  "Active company": "Actief bedrijf",
  "Activity & timeline": "Activiteit & tijdlijn",
  "Activity over 24 hours": "Activiteit gedurende 24 uur",
  "Add a source or upload a file, then review its interpreted operational observations.":
    "Voeg een bron of upload een bestand toe, en controleer de geïnterpreteerde operationele observaties.",
  "Add line": "Voeg regel toe",
  "Add source": "Voeg bron toe",
  "Add the first origin before accepting external records.":
    "Voeg de eerste bron toe voordat externe gegevens worden geaccepteerd.",
  "Add the first rule when the business needs it.":
    "Voeg de eerste regel toe wanneer het bedrijf dit nodig heeft.",
  "Agents & AI": "Agents & AI",
  "Agents use the same tenant-scoped application tools as the UI and CLI. Permissions, confirmation and evidence remain part of the operating model.":
    "Agents gebruiken dezelfde tenant-gebaseerde applicatie-tools als de UI en CLI. Toestemmingen, bevestiging en bewijs blijven deel uitmaken van het operationele model.",
  "AI configuration": "AI-configuratie",
  "All business areas": "Alle bedrijfsgebieden",
  "All directions": "Alle richtingen",
  "All document types": "Alle documenttypen",
  "All facts": "Alle feiten",
  "All flows": "Alle processen",
  "All priorities": "Alle prioriteiten",
  "All records are retained, but the company is hidden from daily work.":
    "Alle gegevens worden bewaard, maar het bedrijf is verborgen voor dagelijkse werkzaamheden.",
  "All states": "Alle staten",
  "All stock states": "Alle voorraadstatus",
  "All tools": "Alle gereedschap",
  Allocated: "Toegekend",
  "Allow all tools": "Laat alle gereedschap toe",
  "Allow physical stock at this location": "Laat fysieke voorraad toe op deze locatie",
  "Already have access? Sign in": "Heb je al toegang? Log in",
  "Already have an account?": "Heb je al een account?",
  "and its complete conversation history.": "en zijn volledige gespreksgeschiedenis.",
  AP: "AP",
  "API key": "API-sleutel",
  "API key stored encrypted": "API-sleutel opgeslagen versleuteld",
  "Append-only receipts, transfers, adjustments and shipments.":
    "Alleen toevoegen van ontvangstbewijzen, overdrachten, aanpassingen en verzendingen.",
  "Approval required": "Goedkeuring vereist",
  "Approved, executed and rejected decisions will appear here.":
    "Goedgekeurde, uitgevoerde en afgewezen beslissingen verschijnen hier.",
  "Archive chat": "Chat archiveren",
  "Archive conversation": "Gesprek archiveren",
  "Archive this chat?": "Deze chat archiveren?",
  "Archived conversations remain available here and can be restored.":
    "Gearchiveerde gesprekken blijven hier beschikbaar en kunnen worden hersteld.",
  "Archiving…": "Archiveren…",
  "Decision history": "Beslissingsgeschiedenis",
  "leaves the active list. Its complete history is retained and can be restored. Pending approvals remain in the decision queue.":
    "verdwijnt uit de actieve lijst. De volledige geschiedenis blijft behouden en kan worden hersteld. Openstaande goedkeuringen blijven in de beslissingswachtrij.",
  "No archived chats": "Geen gearchiveerde chats",
  "No decision history": "Geen beslissingsgeschiedenis",
  "No pending approvals": "Geen openstaande goedkeuringen",
  "Nothing currently waits for approval.": "Op dit moment wacht niets op goedkeuring.",
  "Pending approvals": "Openstaande goedkeuringen",
  "Restore chat": "Chat herstellen",
  "Review operational risks and every business decision that waits for approval.":
    "Beoordeel operationele risico's en elke bedrijfsbeslissing die op goedkeuring wacht.",
  Approve: "Goedkeuren",
  "Approve & execute": "Goedkeuren en uitvoeren",
  "Approve and execute this action?": "Goedkeuren en uitvoeren van deze actie?",
  AR: "AR",
  "Archive before permanently deleting this company and its tenant-scoped records.":
    "Archiveren voordat dit bedrijf en zijn tenant-gerelateerde records permanent worden verwijderd.",
  "Archived companies": "Archiverende bedrijven",
  "are currently exposed": "zijn momenteel beschikbaar",
  Area: "Gebied",
  "Ask about inventory, commitments, payments or operational risk.":
    "Vraag naar voorraad, verplichtingen, betalingen of operationeel risico.",
  "Ask Reality…": "Vraag aan Reality…",
  "Ask what to do next": "Wat moet ik nu doen?",
  "At least 10 characters.": "Minimaal 10 tekens.",
  "At risk": "In gevaar",
  Attempts: "Pogingen",
  "Audit Trail": "Audit Trail",
  "Auditable structure": "Auditabele structuur",
  "Auf Deutsch wechseln": "Naar Duits",
  "Ausgewählte Payloads fließen aus bestehenden Systemen in Reality":
    "Geselecteerde payloads komen uit bestaande systemen in Reality",
  "Ausgewählter Payload · verlustfrei bewahrt": "Geselecteerde payload · onverliesmatig bewaard",
  Automate: "Automatiseren",
  "automatic access slots used": "Automatische toegangsslots worden gebruikt",
  Automation: "Automatisering",
  "Automation potential": "Automatiseringspotentieel",
  "Autonomous commerce core": "Autonome commerciële kern",
  "AUTONOMOUS COMMERCE CORE": "AUTONOME COMMERCIËLE KERN",
  "Autonomy is granted per capability — never for everything at once.":
    "Autonomie wordt verleend per capaciteit — nooit voor alles tegelijk.",
  "Autonomy is never a global switch. Every capability advances only after its observations and recommendations have earned trust.":
    "Autonomie is nooit een wereldwijde schakelaar. Elke capaciteit wordt pas geactiveerd nadat de observaties en aanbevelingen vertrouwen hebben gewekt.",
  "AUTONOMY UNLOCKED": "AUTONOMIE ONTROLLED",
  "Available application tools": "Beschikbare applicatietools",
  "Avoidable work": "Vermijdbaar werk",
  "awaiting explicit confirmation": "wacht op expliciete bevestiging",
  "Back to Data settings": "Terug naar Data-instellingen",
  "Back to parties": "Terug naar partijen",
  "Backend unavailable": "Backend niet beschikbaar",
  "Bike Light causes 43% of delays": "Fietsverlichting veroorzaakt 43% van de vertragingen",
  "Blocked revenue": "Geblokkeerde inkomsten",
  "Build an operational picture you can verify before granting any agent permission to act.":
    "Creëer een operationeel overzicht dat u kunt verifiëren voordat u een agent toestemming verleent om te handelen.",
  "Business events remain stored in UTC and are converted for your interface.":
    "Bedrijfsgebeurtenissen worden opgeslagen in UTC en worden omgezet voor uw interface.",
  "Business roles": "Bedrijfsrollen",
  "can ship today": "kunnen vandaag verzonden worden",
  Cancelled: "Geannuleerd",
  "Change the filters or add an active item.": "Pas de filters aan of voeg een actief item toe.",
  "Change the filters or import source evidence.": "Pas de filters aan of importeer bronbewijs.",
  "Change the filters or ingest invoice evidence.":
    "Pas de filters aan of importeer factuurbewijs.",
  "Change the filters or ingest new promise evidence.":
    "Pas de filters aan of importeer nieuw bewijs.",
  "Change the search or create the first record.":
    "Pas de zoekopdracht aan of creëer het eerste record.",
  "Changes affect your account only.": "Wijzigingen hebben alleen invloed op uw account.",
  "Chart period": "Periode",
  Chats: "Gesprekken",
  "Check your inbox": "Controleer uw inbox",
  "Choose a record from the middle column.": "Kies een record uit de middelste kolom.",
  "Choose allowed tools": "Kies toegestane tools",
  Classification: "Classificatie",
  "Close company menu": "Sluit het bedrijfsmenu",
  "Close inspector": "Sluit de inspectie",
  "Close navigation": "Sluit de navigatie",
  Code: "Code",
  Collections: "Collecties",
  "Comma-separated: company, customer, supplier": "Komma-gescheiden: bedrijf, klant, leverancier",
  Commerce: "Commerce",
  "Commercial prices by direction and currency.": "Commerciële prijzen per richting en valuta.",
  "Commercial reference": "Commerciële referentie",
  "Commercial terms": "Commerciële voorwaarden",
  "Companies, customers and suppliers": "Bedrijven, klanten en leveranciers",
  "Company configuration": "Bedrijfconfiguratie",
  "Company ID": "Bedrijf ID",
  "Company management": "Bedrijfbeheer",
  "Company name": "Bedrijfsnaam",
  "Company settings / agents": "Bedrijfsinstellingen / vertegenwoordigers",
  "Company settings / commercial": "Bedrijfsinstellingen / commercieel",
  "Company settings / data": "Bedrijfsinstellingen / data",
  "Company website": "Bedrijfswebsite",
  "Configure sources and inspect recently received records.":
    "Configureer bronnen en controleer recent ontvangen records.",
  "Configure the model used by this company and issue tenant-scoped HTTPS MCP credentials.":
    "Configureer het model dat door dit bedrijf wordt gebruikt en geef tenant-specifieke HTTPS MCP-credentials.",
  "Configured — leave empty to keep": "Geconfigureerd — laat leeg om te behouden",
  Connect: "Verbind",
  "Connect a source": "Verbind een bron",
  "Connect a source and Reality observes how reliably orders flow through your company—without changing anything.":
    "Verbind een bron en Reality observeert hoe betrouwbaar orders door uw bedrijf lopen—zonder iets te veranderen.",
  "Connect external origins, upload files and test the same immutable intake used by integrations.":
    "Verbind externe bronnen, upload bestanden en test de dezelfde onveranderlijke intake die door integraties wordt gebruikt.",
  "Connect one source. Start by observing.": "Verbind één bron. Begin met observeren.",
  "Connect one source. Verify what Reality learns.":
    "Verbind één bron. Controleer wat Reality leert.",
  "Connect systems": "Verbind systemen",
  "Connect the tools your business already runs on.":
    "Verbind de tools die uw bedrijf al gebruikt.",
  "Connect your business": "Verbind uw bedrijf",
  "Connect your first source": "Verbind uw eerste bron",
  Continue: "Ga verder",
  "Continue to your Reality workspace.": "Ga verder naar uw Reality-werkruimte.",
  "Control incoming and outgoing commitments, reservation coverage and due-date risk.":
    "Beheer inkomende en uitgaande overeenkomsten, reserveringsdekking en risico op vervaldatum.",
  "Control remains explicit at every level.": "Beheer blijft expliciet op elk niveau.",
  "Controls decimals, dates and currency formatting.":
    "Beheert decimale getallen, datums en valutaformaten.",
  "Controls labels and interface text.": "Beheert labels en tekst in de interface.",
  Copied: "Gekopieerd",
  "Copilot prepared an action but has not changed business state.":
    "Copilot heeft een actie voorbereid, maar heeft de bedrijfsstatus niet gewijzigd.",
  "Copilot provider": "Copilot-aanbieder",
  "Copy this token now": "Kopieer dit token nu",
  "Copy URL": "Kopieer URL",
  "Could not load choices:": "Kon geen keuzes laden:",
  "Could not load this view": "Kon deze weergave niet laden",
  Covered: "Gedekt",
  "Create account": "Maak een account",
  "Create companies, inspect their operational footprint, or archive workspaces without losing data.":
    "Maak bedrijven, inspecteer hun operationele voetafdruk, of archiveren werkruimten zonder data te verliezen.",
  "Create company": "Maak bedrijf",
  "Create document": "Maak document",
  "Create scoped token": "Maak geschoold token",
  "Create source": "Maak bron",
  "Create token": "Maak token",
  "Create your account": "Maak uw account",
  "Create your account. We review every new workspace personally.":
    "Maak uw account aan. Wij beoordelen elk nieuw werkruimte persoonlijk.",
  "Create your first company": "Maak uw eerste bedrijf",
  "Create empty company": "Leeg bedrijf aanmaken",
  "Try the guided demo": "Probeer de rondleiding",
  "Create a sample company with an explainable order, stock, commitments and shortage.":
    "Maak een voorbeeldbedrijf met een uitlegbare order, voorraad, toezeggingen en tekort.",
  "Preview demo": "Demo bekijken",
  "This will add sample business records to the new company.":
    "Hiermee worden voorbeeldrecords aan het nieuwe bedrijf toegevoegd.",
  "Create demo company": "Demobedrijf aanmaken",
  "Creates normalized evidence. Operational commitments remain explicit.":
    "Genereert geormaliseerde bewijzen. Operationele verplichtingen blijven expliciet.",
  "Creating account…": "Account aanmaken…",
  "Creating…": "Aanmaken…",
  "Credit limit": "Kredietlimiet",
  "Credit note": "Kredietnota",
  "Cross-domain signals connect causes directly to their business impact.":
    "Cross-domein signalen verbinden oorzaken direct met hun zakelijke impact.",
  Currency: "Valuta",
  "Currency…": "Valuta…",
  "Current company": "Huidig bedrijf",
  "Current derived view": "Huidige afgeleide weergave",
  "Current exceptions": "Huidige uitzonderingen",
  "Current operating mode": "Huidige bedrijfsmodus",
  "Current workspace lifecycle.": "Huidige levenscyclus van de werkruimte.",
  "Custom source": "Aangepaste bron",
  "Customer reference": "Referentie",
  "Danger zone": "Gevaarzone",
  "Data / explorer": "Data / explorer",
  "Data / immutable intake": "Data / immutable intake",
  "Data received from": "Data ontvangen van",
  "Data stays in its systems. Reality retains only what operations need — losslessly and traceably.":
    "Data blijft in zijn systemen. Reality behoudt alleen wat de operaties nodig hebben — zonder verlies en traceerbaar.",
  DE: "DE",
  Deactivate: "Deactiveer",
  Decision: "Beslissing",
  Default: "Standaard",
  "Define which source types this workspace may receive.":
    "Definieer welke bronnen dit werkruimte kan ontvangen.",
  Delegate: "Toewijzen",
  "Delegate one capability": "Toewijzen van een capaciteit",
  "Delegate step by step": "Toewijzen stap voor stap",
  Delete: "Verwijderen",
  DELETE: "VERWIJDEREN",
  "Delete chat": "Chat verwijderen",
  "Delete company permanently": "Bedrijf permanent verwijderen",
  "Delete conversation": "Gesprek verwijderen",
  "Delete permanently": "Permanent verwijderen",
  "Delete this chat?": "Verwijder deze chat?",
  "Deleting…": "Verwijderen…",
  Description: "Beschrijving",
  Deutsch: "Duits",
  "Deutsch (Deutschland)": "Duits (Duitsland)",
  Direction: "Richting",
  Disabled: "Uitgeschakeld",
  "Display name": "Weergavenaam",
  "Display timezone for operators.": "Weergave tijdzone voor operators.",
  "Document date": "Documentdatum",
  "Document link · Timestamp · Lineage · Change log · Tenant scope · Confirmation":
    "Documentlink · Tijdstempel · Afstamming · Wijzigingslog · Tenant scope · Bevestiging",
  "Document type": "Documenttype",
  "Drop source data": "Brongegevens verwijderen",
  Due: "Van",
  "Each company gets isolated sources, facts, operational records and agent access.":
    "Elke bedrijf krijgt geïsoleerde bronnen, feiten, operationele gegevens en toegang tot agenten.",
  "Each shop, PIM, CRM or payment account is a separate origin.":
    "Elke winkel, PIM, CRM of betaalrekening is een afzonderlijke bron.",
  "Edit party": "Partij bewerken",
  Email: "E-mail",
  Endpoint: "Eindpunt",
  English: "Engels",
  "English (United Kingdom)": "Engels (Verenigd Koninkrijk)",
  "Enter a new value": "Voer een nieuwe waarde in",
  "Enter API key": "Voer API-sleutel in",
  "Enter DELETE": "Voer DELETE in",
  "Enter the exact company name": "Voer de exacte bedrijfsnaam in",
  Español: "Spaans",
  "Español (España)": "Spaans (Spanje)",
  Events: "Gebeurtenissen",
  "Events & activity": "Gebeurtenissen & activiteit",
  "Every answer stays connected to what actually happened.":
    "Elke antwoord blijft verbonden aan wat er daadwerkelijk is gebeurd.",
  "Evidence / document register": "Bewijs / documentregister",
  "Evidence, permissions and confirmation remain part of every step.":
    "Bewijs, rechten en bevestiging blijven onderdeel van elke stap.",
  Example: "Voorbeeld",
  "EXAMPLE CAPABILITY": "VOORBEELD FUNCTIE",
  "Example insights · no live data": "Voorbeeld inzichten · geen live gegevens",
  "Example orders received and shipped by day":
    "Voorbeeld bestellingen ontvangen en verzonden per dag",
  "Example preview · no live data": "Voorbeeldweergave · geen live data",
  "Example trace · no live data": "Voorbeeldtrace · geen live data",
  "Execute only the proven capability within explicit rules.":
    "Voer alleen de bewezen functionaliteit uit binnen expliciete regels.",
  EXPLAIN: "VERKLAR",
  "Explain physical, reserved, available and projected stock without storing a presentation balance.":
    "Leg fysieke, gereserveerde, beschikbare en voorspelde voorraad uit zonder een presentatiebalans op te slaan.",
  "Explain the current Reality": "Leg de huidige Realiteit uit",
  "Explicit, source-supported observations currently retained by Reality. Facts never replace their immutable source.":
    "Expliciete, bronondersteunde observaties die momenteel door de Realiteit worden bewaard. Feiten vervangen nooit hun onveranderlijke bron.",
  Explore: "Verken",
  "External agents": "Externe agenten",
  "External ID": "Externe ID",
  "External identity": "Externe identiteit",
  Facts: "Feiten",
  "Facts · Commitments · Reservations · Movements · Lots · Serials · SSCC":
    "Feiten · Verplichtingen · Reserveringen · Bewegingen · Partijen · Serienummers · SSCC",
  "Facts appear when a source-backed observation is interpreted.":
    "Feiten verschijnen wanneer een bronondersteunde observatie wordt geïnterpreteerd.",
  "Facts, commitments and movements used by operations.":
    "Feiten, verplichtingen en bewegingen worden door de operaties gebruikt.",
  Finance: "Financiën",
  "Finance / cash": "Financiën / contanten",
  "Finance / subledger": "Financiën / subledger",
  "Finance Ledger": "Financiële administratie",
  "First verify that Reality understands your business. Nothing is changed automatically.":
    "Controleer eerst of de Realiteit uw bedrijf begrijpt. Niets wordt automatisch gewijzigd.",
  "Follow Reality through Evidence to its original SourceRecord.":
    "Volg de Realiteit via Bewijs naar de oorspronkelijke SourceRecord.",
  From: "Van",
  "From original evidence to the ledger. Linked end to end.":
    "Van oorspronkelijk bewijs naar de administratie. Van eind tot eind gelinkt.",
  Fulfilled: "Uitgevoerd",
  "Fully allocated": "Volledig toegewezen",
  "Get started": "Beginnen",
  "No data yet": "Nog geen gegevens",
  "Give agents responsibility one capability at a time.":
    "Geef agenten één verantwoordelijkheid tegelijk.",
  Gross: "Bruto",
  "Gross amount": "Bruto bedrag",
  "Help & documentation": "Hulp & documentatie",
  Appearance: "Weergave",
  "Applies immediately and is stored on this device.":
    "Werkt direct en wordt op dit apparaat opgeslagen.",
  Light: "Licht",
  Dark: "Donker",
  Resources: "Bronnen",
  Documentation: "Documentatie",
  "Reality website": "Reality-website",
  "Help & reference": "Hulp & referentie",
  "Here is what Reality knows": "Hier is wat Reality kent",
  "How can I help?": "Hoe kan ik helpen?",
  "How one order became operational reality": "Hoe één bestelling operationeel wordt",
  "How Reality may act": "Hoe Reality kan handelen",
  "HTTPS endpoint": "HTTPS endpoint",
  "HTTPS MCP": "HTTPS MCP",
  "https://…/v1": "https://…/v1",
  "Human confirmation": "Menselijke bevestiging",
  "I agree to the Terms and Privacy Policy.":
    "Ik ga akkoord met de Algemene voorwaarden en Privacybeleid.",
  "Identity and defaults used across this company workspace.":
    "Identiteit en standaardinstellingen gebruikt in dit bedrijfsomgeving.",
  "Identity, commercial defaults and source reference.":
    "Identiteit, commerciële standaardinstellingen en bronverwijzing.",
  "Immutable intake": "Onveranderlijke intake",
  "Immutable source intake": "Onveranderlijke bron-intake",
  "Immutable SourceRecords · Versioned payloads · Documents · Document lines":
    "Onveranderlijke SourceRecords · Versieerde payloads · Documenten · Documentregels",
  "Import a bank statement or change the filters.":
    "Importeer een bankafschrift of wijzig de filters.",
  "Import evidence": "Importeer bewijs",
  "Import jobs": "Importeer taken",
  "Import statement": "Importeer statement",
  In: "In",
  "in the example period": "in het voorbeeldperiode",
  "In use": "In gebruik",
  Inactive: "Inactief",
  "Includes future tools": "Bevat toekomstige tools",
  Infrastructure: "Infrastructuur",
  Input: "Input",
  Inspect: "Inspecteren",
  "Inspect & trace": "Inspecteren en traceren",
  "Inspect and trace data": "Inspecteer en traceer data",
  "Inspect documents and their shortest links into Reality.":
    "Inspecteer documenten en hun kortste links naar Reality.",
  "Inspect normalized documents and their links into operational Reality.":
    "Inspecteer genormaliseerde documenten en hun links naar de operationele Reality.",
  "Instance code": "Instantie code",
  "Interpreter ready": "Interpreter klaar",
  "Inventory and reservations": "Inventaris en reserveringen",
  "Inventory position": "Inventarispositie",
  Invoice: "Factuur",
  Invoicing: "Facturering",
  "Irreversible deletion": "Onomkeerbare verwijdering",
  "It will not be shown again.": "Dit zal niet meer worden getoond.",
  "Last activity": "Laatste activiteit",
  "Last error": "Laatste fout",
  "LEARNS FROM EVIDENCE": "LEERT VAN EVIDENTIE",
  "Ledger / Action": "Boekhouding / Actie",
  "Ledger entries · Open items · Allocations · Payments · Settlement · Reconciliation":
    "Boekhoudingsgegevens · Openstaande items · Allocaties · Betalingen · Afrekening · Afstemming",
  "Let agents run the business.": "Laat agenten het bedrijf runnen.",
  "Let Reality surface contradictions and explain their business impact.":
    "Laat Reality tegenstrijdigheden blootleggen en hun zakelijke impact uitleggen.",
  "Line items": "Rekeningstappen",
  "Loading available systems…": "Systemen worden geladen…",
  "Loading choices…": "Keuzes worden geladen…",
  "Loading…": "Geladen…",
  Location: "Locatie",
  "Longest wait": "Langste wachttijd",
  "Lossless JSON payload": "Verliesloze JSON payload",
  "Losslessly stored input": "Verliesloos opgeslagen invoer",
  "Main navigation": "Hoofdnavigatie",
  "Maintain only the operational references and normalized evidence Reality needs. Complete ERP records remain in their source systems.":
    "Behoud alleen de operationele referenties en geënormeerde bewijzen die Reality nodig heeft. Volledige ERP-records blijven in hun bronsystemen.",
  "Maintain payment terms, price lists and pricing groups used for due dates and price resolution.":
    "Behoud betalingstermijnen, prijslijsten en prijsgroepen die gebruikt worden voor de afhandeling van betalingen en prijzen.",
  "Manage the typed identities and commercial rules Reality repeatedly uses.":
    "Beheer de getypeerde identiteiten en commerciële regels die Reality herhaaldelijk gebruikt.",
  "Manage your personal identity and how Reality displays dates, times and numbers.":
    "Beheer uw persoonlijke identiteit en hoe Reality datums, tijden en getallen weergeeft.",
  "Manual evidence": "Bewijs (handmatig)",
  Model: "Model",
  "Model identifier": "Model-ID",
  "Monday clears the weekend backlog": "Maandag maakt het weekendachterstand weg",
  "Monitor import jobs and the rebuildable projections used by the product.":
    "Monitor importtaken en de herbouwbare projecties die door het product worden gebruikt.",
  "Monitor operations": "Monitor operaties",
  "Monitor the operating machine, isolate exceptions and trace each change to its source.":
    "Monitor de werkende machine, isoleer uitzonderingen en traceer elke verandering terug naar de bron.",
  "Move from observation to recommendations only when you trust the result.":
    "Verplaats van observaties naar aanbevelingen alleen wanneer u het resultaat vertrouwt.",
  Nederlands: "Nederlands",
  "Nederlands (Nederland)": "Nederlands (Nederland)",
  "need attention": "vereist aandacht",
  New: "Nieuw",
  "New conversation": "Nieuwe gesprek",
  "New document": "Nieuw document",
  "New to Reality?": "Nieuw in Reality?",
  No: "Nee",
  "No accepted record types": "Geen geaccepteerde recordtypes",
  "No active MCP tokens.": "Geen actieve MCP-tokens.",
  "No activity matches": "Geen activiteit komt overeen",
  "No activity yet": "Geen activiteit nog",
  "1 event": "1 gebeurtenis",
  "No API key stored": "Geen API-sleutel opgeslagen",
  "No archived companies.": "Geen archiverende bedrijven.",
  "No business state will be changed. The rejection remains visible in the conversation history.":
    "Geen bedrijfsstatus wordt gewijzigd. De afwijzing blijft zichtbaar in de gespreksgeschiedenis.",
  "No commitments match": "Geen overeenkomsten",
  "No commitments.": "Geen overeenkomsten.",
  "No documents.": "Geen documenten.",
  "no due date": "geen vervaldatum",
  "No evidence matches": "Geen bewijs komt overeen",
  "No explicit facts yet": "Geen expliciete feiten nog",
  "No facts yet": "Geen feiten nog",
  "No imports yet": "Geen importen nog",
  "No inventory matches": "Geen voorraad komt overeen",
  "No linked records.": "Geen gerelateerde records",
  "No matching records": "Geen overeenkomende records",
  "No movements": "Geen bewegingen",
  "No open exceptions": "Geen openstaande uitzonderingen",
  "No open items match": "Geen openstaande items komen overeen",
  "No operational activity yet": "Geen operationele activiteit nog",
  "No payment events": "Geen betalingsgebeurtenissen",
  "No recorded events for this record.": "Geen geregistreerde gebeurtenissen voor dit record.",
  "No records": "Geen records",
  "No records match": "Geen records komen overeen",
  "No reservations": "Geen reserveringen",
  "No source records yet": "Geen bronrecords nog",
  "No source systems": "Geen bronsystemen",
  "No stock": "Geen voorraad",
  None: "Geen",
  "Nordlicht delivers only 78% on time": "Nordlicht levert slechts 78% op tijd",
  "Normalized business evidence with direct links to Reality and its original source.":
    "Geormaliseerde zakelijke bewijzen met directe links naar Reality en de oorspronkelijke bron.",
  "Nothing currently requires review.": "Op dit moment is er niets dat beoordeeld moet worden.",
  "Nothing needs attention": "Er is niets dat aandacht vereist",
  "Nothing selected": "Geen geselecteerd",
  Now: "Nu",
  Number: "Aantal",
  "Nur bei operativem Nutzen typisiert": "Alleen bij operationele toepassing gedefinieerd",
  Observe: "Observeren",
  OBSERVE: "OBSERVEN",
  "Observe first, automate when trusted": "Observeren eerst, automatiseren wanneer vertrouwd",
  "Observe only": "Alleen observeren",
  "Observe what matters": "Wat belangrijk is observeren",
  "Observed cash postings and their current allocation state.":
    "Gezette contante transacties en hun huidige status",
  Occurred: "Gebeurd",
  "One exception. One explainable resolution.": "Eén uitzondering. Eén uitlegbare oplossing.",
  "One operational core for facts, decisions and accountable automation.":
    "Een operationeel kern voor feiten, beslissingen en verantwoorde automatisering.",
  "One operational core. Your systems remain in place.":
    "Een operationele kern. Uw systemen blijven bestaan.",
  "Only operationally useful fields become typed Reality":
    "Alleen operationeel relevante velden worden getypeerd Reality",
  Open: "Open",
  "Open a register to search, create, inspect or maintain records.":
    "Een register openen om te zoeken, te creëren, te inspecteren of te onderhouden.",
  "Open backlog": "Open backlog",
  "Open company": "Open bedrijf",
  "Open Evidence": "Open Bewijs",
  "Open Explorer": "Open Explorer",
  "Open Home": "Open Home",
  "Open Integrations": "Open Integraties",
  "Open Items": "Open Items",
  "Open navigation": "Open navigatie",
  "Open one company to manage its complete configuration.":
    "Een bedrijf openen om zijn volledige configuratie te beheren.",
  "Open one focused viewer for records, events or evidence.":
    "Een gefocuste weergave openen voor records, gebeurtenissen of bewijs.",
  "Open Timeline": "Open Tijdlijn",
  "Open warehouse view": "Opslagweergave openen",
  "OpenAI-compatible base URL": "OpenAI-compatibele basis-URL",
  "Opening Reality": "Realiteit openen",
  "Operating machine": "Machine bedienen",
  "Operational context active": "Operationele context actief",
  "OPERATIONAL CORE": "OPERATIONELE KERN",
  "Operational defaults": "Operationele standaard",
  "Operational facts": "Operationele feiten",
  "Operational reality": "Operationele realiteit",
  "Operational Reality": "Operationele referentie",
  "Operational reference": "Operationele gegevens",
  Operations: "Operationele processen",
  "Operations / decision queue": "Operationen / beslissingsrij",
  "Operations / promise control": "Operationen / beloftebeheer",
  "Optional origin reference; the complete upstream record remains in its immutable payload.":
    "Optionele bronverwijzing; het volledige upstream-record blijft in zijn onveranderlijke payload.",
  "Optional. Set together with the upstream External ID.":
    "Optioneel. Stel samen met de upstream External ID.",
  "Order flow": "Bestelproces",
  "Orders continue at weekends while shipping follows warehouse cut-off times.":
    "Bestellingen verlopen ook in het weekend, terwijl de verzending zich houdt aan de magazijn-uren.",
  "Orders per day": "Bestellingen per dag",
  "Orders received": "Ontvangenen bestellingen",
  "Orders received & shipped": "Ontvangen en verzonden bestellingen",
  "Orders, commitments and holds": "Bestellingen, beloftes en reserveringen",
  "Orders, stock, payments and promises are observed together. Reality exposes contradictions, business impact and the source evidence behind every conclusion.":
    "Bestellingen, voorraad, betalingen en beloftes worden samen bekeken. Reality onthult tegenstrijdigheden, zakelijke impact en de bron-bewijzen achter elke conclusie.",
  Origin: "Bron",
  "Original source payload": "Originele payload",
  Out: "Uit",
  Outgoing: "Uitgaande",
  "over 30 days": "meer dan 30 dagen",
  Paid: "Betaald",
  Partial: "Gedeeltelijk",
  "Party account and connected business evidence.": "Partijrekening en bijbehorende bewijsstukken.",
  Password: "Wachtwoord",
  Payables: "Betalingen",
  "Payload must be valid JSON.": "De payload moet een geldige JSON zijn.",
  "Payment term": "Betalingstermijn",
  "Payment terms": "Betalingstermijnen",
  "Payment terms, price lists and pricing groups":
    "Betalingsvoorwaarden, prijslijsten en prijsgroepen",
  "Payments and open items": "Betalingen en openstaande facturen",
  "permanently?": "permanent?",
  "Personal settings": "Persoonlijke instellingen",
  "Platform administration": "Platformbeheer",
  Posted: "Geplaatst",
  "PostgreSQL fact journal · Append-only records · S3-compatible object store · Projections · Backups / PITR":
    "PostgreSQL fact journal · Append-only records · S3-compatible object store · Projections · Backups / PITR",
  "Posting group": "Prijsgroep",
  "Prepare a precise next action and show the evidence.":
    "Bereid een nauwkeurige volgende actie voor en toon het bewijs.",
  "Price lists": "Prijslijsten",
  "Pricing groups": "Prijsgroepen",
  "Primary role": "Primaire rol",
  "Problem item": "Probleemitem",
  "Processing coverage": "Verwerkingsdekking",
  "Processing latency": "Verwerkingslatentie",
  "Products, services and charges": "Producten, diensten en kosten",
  Projection: "Projectie",
  Projections: "Projecties",
  Promised: "Gegarandeerd",
  "Promised date": "Gegarandeerde datum",
  "Bills order line": "Factureert orderregel",
  "Order line id, if this bills one": "Orderregel-id, als deze regel er een factureert",
  "Approvals can be enabled later": "Goedkeuringen kunnen later worden ingeschakeld",
  "Where to begin": "Waar te beginnen",
  "Step 1": "Stap 1",
  "Reality knows only what a source shows it. Nothing is imported until you accept it.":
    "Reality kent alleen wat een bron laat zien. Er wordt niets geïmporteerd totdat je het accepteert.",
  "Connect a system or upload a file": "Verbind een systeem of upload een bestand",
  "Accept the records you want interpreted":
    "Accepteer de records die je geïnterpreteerd wilt hebben",
  "Verify the facts Reality derives": "Controleer de feiten die Reality afleidt",
  Provider: "Leverancier",
  "Purchase order": "Bestelovereenkomst",
  Purpose: "Doel",
  Quantity: "Hoeveelheid",
  "Raw only": "Alleen ruwe gegevens",
  "Read models": "Leesmodellen",
  "Read-only answers are immediate. Any change to business Reality waits for an approval until a person confirms it.":
    "Alleen-lezen antwoorden zijn onmiddellijk. Elke wijziging aan de zakelijke Reality wacht op een goedkeuring totdat iemand het bevestigt.",
  "Read-only understanding is immediate. Business changes wait for an explicit approval until a person confirms them.":
    "Alleen-lezen begrip is onmiddellijk. Bedrijfswijzigingen wachten op een expliciete goedkeuring totdat iemand ze bevestigt.",
  "Read, reconcile and explain without changing business state.":
    "Lees, vergelijk en leg uit zonder de bedrijfsstatus te wijzigen.",
  "Reality · Autonomous commerce core": "Realiteit · Kern van autonome commerce",
  "Reality connects operational data into an explainable business reality — a trusted foundation for decisions and step-by-step autonomy.":
    "Realiteit verbindt operationele gegevens met een begrijpelijke bedrijfsrealiteit — een betrouwbare basis voor beslissingen en stapsgewijze autonomie.",
  "Reality Explorer": "Realiteit Explorer",
  "Reality found no current operational contradiction or uncovered promise.":
    "Realiteit vond geen huidige operationele tegenstrijdigheid of onontworpen belofte.",
  "Reality home": "Realiteit home",
  "Reality inspector": "Inspecteur van de realiteit",
  "Reality is not another ERP. It receives selected operational events, preserves their source evidence and types only what is repeatedly needed to understand, decide and act.":
    "Reality is geen ander ERP-systeem. Het ontvangt geselecteerde operationele gebeurtenissen, bewaart hun bronbewijs en alleen de informatie die herhaaldelijk nodig is om te begrijpen, te beslissen en te handelen.",
  "Reality is observing your business": "Reality observeert uw bedrijf",
  "Reality links": "Reality links",
  "Reality separates original data, evidence, operational truth and the ledger — while keeping their lineage verifiable through the shortest true links.":
    "Reality scheidt originele data, bewijs, operationele waarheid en het grootboek — terwijl het hun afkomst verifieerbaar maakt via de kortste, correcte links.",
  "Reality stores before it interprets. The shortest true links keep every operational conclusion explainable.":
    "Reality slaat op voordat het interpreteert. De kortste, correcte links zorgen ervoor dat elke operationele conclusie uitlegbaar is.",
  "Reality target": "Doel van Reality",
  "Reality watches before agents touch the business.":
    "Reality observeert uw bedrijf voordat agenten daarin ingrijpen.",
  "Reality will execute exactly this action through the shared application service and record its result.":
    "Reality voert precies deze actie uit via de gedeelde applicatieservice en registreert het resultaat.",
  Rebuildable: "Herstelbaar",
  Receivables: "Debiteuren",
  "Receivables & payables": "Debiteuren en crediteuren",
  "Receivables and payables derived from postings, credits and settlement allocations.":
    "Debiteuren en crediteuren afgeleid van boekingen, credits en betalingen.",
  Received: "Ontvangen",
  "Recent runs": "Recente runs",
  "Recent source records": "Recente bronregistraties",
  Recommend: "Aanbevelen",
  "Record & enqueue": "Registreer en verwerk",
  "Record movement": "Registreer beweging",
  Recorded: "Geregistreerd",
  "Recording…": "Registreren…",
  "Recurring gap before the next receipt":
    "Herhaaldelijk ontbrekende periode voor de volgende ontvangst",
  Reference: "Referentie",
  "Register an external origin and choose exactly which record types Reality may receive.":
    "Registreer een externe bron en kies precies welke registratievormen Reality kan ontvangen.",
  Registers: "Registreren",
  Reject: "Afwijzen",
  "Reject this action?": "Deze actie afwijzen?",
  "Remove line": "Verwijder regel",
  "Requested delivery": "Gewenste levering",
  "Reserve an open outgoing Commitment when stock becomes available.":
    "Reserveer een open uitgaande Commitment wanneer voorraad beschikbaar is.",
  "Reserve stock": "Reserveer voorraad",
  "Reserved at": "Gereserveerd bij",
  "Resolve delivery holds": "Los leveringsproblemen op",
  "Restore company": "Herstel bedrijf",
  "Reusable customer or supplier pricing assignments.":
    "Herbruikbare prijsopdrachten voor klanten of leveranciers.",
  "Reusable rules for calculating invoice due dates.":
    "Herbruikbare regels voor het berekenen van de factuurdatum.",
  "Review all": "Beoordelen",
  "Review business events, processing activity and exceptions over time.":
    "Beoordeel zakelijke gebeurtenissen, verwerking en uitzonderingen over de tijd.",
  "Review Business Events, processing history and exceptions.":
    "Beoordeel zakelijke gebeurtenissen, verwerking en uitzonderingen.",
  "Review derived operational risks. They disappear when Reality is corrected.":
    "Beoordeel afgeleide operationele risico's. Deze verdwijnen wanneer de Realiteit wordt gecorrigeerd.",
  "Review exceptions, commitments and current inventory.":
    "Beoordeel uitzonderingen, commitments en huidige voorraad.",
  "Review observed facts": "Beoordeel waargenomen feiten",
  "Review pending": "Beoordeel",
  Revoke: "Intrekken",
  "Run daily operations": "Voer dagelijkse operaties uit",
  "Runs appear after SourceRecords enter through an integration or test intake.":
    "Data verschijnen nadat SourceRecords via een integratie of testintake zijn binnengekomen.",
  "Sales channel": "Verkoopkanaal",
  "Sales invoice": "Factuur",
  "Sales order": "Bestelbon",
  "Save changes": "Wijzigingen opslaan",
  "Save details": "Details opslaan",
  "Save settings": "Instellingen opslaan",
  Saved: "Opgeslagen",
  Scope: "Scope",
  "Search a different business identity or clear the query.":
    "Zoek een andere bedrijfsidentiteit of reset de query.",
  "Search any ID and follow Source → Evidence → Reality.":
    "Zoek naar een ID en volg Source → Evidence → Reality.",
  "Search currencies…": "Zoek naar valuta…",
  "Search document, party or source…": "Zoek naar document, partij of bron…",
  "Search exceptions…": "Zoek naar uitzonderingen…",
  "Search ID, order number, SKU, party or source reference…":
    "Zoek naar ID, bestelnummer, SKU, partij of bronverwijzing…",
  "Search IDs and inspect connected Reality, Evidence and Source records.":
    "Zoek naar ID's en inspecteer verbonden Reality, Evidence en Source records.",
  "Search invoice, party or ID…": "Zoek naar factuur, partij of ID…",
  "Search item or SKU…": "Zoek naar artikel of SKU…",
  "Search or enter source system…": "Zoek of voer het bron systeem in…",
  "Search or enter source type…": "Zoek of voer het bron type in…",
  "Search order, source, SKU, party or ID…": "Zoek naar bestelling, bron, SKU, partij of ID…",
  "Search party, item or ID…": "Zoek naar partij, artikel of ID…",
  "Search party…": "Zoek naar partij…",
  "Search payment term…": "Zoek naar betalingsterm…",
  "Search payment terms…": "Zoek naar betalingstermen…",
  "Search records, browse collections and inspect one object without losing context.":
    "Zoek naar records, blader door collecties en inspecteer een object zonder context te verliezen.",
  "Search reference, party or posting…": "Zoek naar referentie, partij of posting…",
  "Search ship-to party…": "Zoek naar afleveradres…",
  "Search SKU or item…": "Zoek naar SKU of artikel…",
  "Search source systems…": "Zoek naar bronsystemen…",
  "Search tools…": "Zoek naar tools…",
  "See the operating model": "Bekijk het operationele model",
  "See what is true, what needs attention and what can be delegated next.":
    "Bekijk wat waar is, wat aandacht vereist en wat de volgende keer kan worden uitbesteed.",
  "Select a system…": "Selecteer een systeem…",
  "Select exactly which upstream records Reality may receive.":
    "Selecteer precies welke upstream records Reality kan ontvangen.",
  "Select only the upstream types this instance is responsible for.":
    "Selecteer alleen de upstream types waar deze instantie verantwoordelijk voor is.",
  "Select volume": "Selecteer volume",
  "Selected operational signals only": "Selecteer alleen de relevante operationele signalen",
  "Selected payload · retained losslessly": "Geselecteerde payload · behouden zonder verlies",
  "Selected payloads flow from existing systems into Reality":
    "Geselecteerde payloads stromen van bestaande systemen naar Reality",
  Send: "Verstuur",
  Settled: "Afgehandeld",
  "Shared application service": "Gedeelde applicatieservice",
  "shared application tools. Mutations still require the Reality approval boundary.":
    "Gedeelde applicatie-tools. Mutaties vereisen nog steeds de Reality-goedkeuringsgrens.",
  "Ship-to party": "Verzendpartij",
  Shipped: "Verzonden",
  "Shipping readiness": "Verzendklaar",
  Shortage: "Tekort",
  "Shown throughout Reality.": "Getoond in Reality.",
  "Shown to other operators in decisions and activity.":
    "Getoond aan andere operators in beslissingen en activiteiten.",
  "Sign in": "Inloggen",
  "So agents can operate your business with confidence.":
    "Zodat agenten uw bedrijf met vertrouwen kunnen beheren.",
  Source: "Bron",
  "Source → Evidence → Reality": "Bron → Bewijs → Realiteit",
  "Source capabilities": "Functionaliteit van de bron",
  "Source definition": "Definitie van de bron",
  "Source record": "Bronrecord",
  "Source registry": "Bronregister",
  "Source system": "Bron systeem",
  "Source systems": "Bron systemen",
  "Source systems remain authoritative": "Bron systemen blijven autoritair",
  "Source templates available in Reality today. Transport and credentials remain explicit per connector.":
    "Bron templates beschikbaar in Realiteit. Transport en credentials blijven expliciet per connector.",
  "Source type": "Type bron",
  "Payload value path": "Waardepad in payload",
  "Fact predicate": "Fact-predicaat",
  "Fact value type": "Fact-waardetype",
  "Allowed values, comma separated": "Toegestane waarden, kommagescheiden",
  String: "Tekst",
  Enum: "Keuzelijst",
  Boolean: "Ja/nee",
  Decimal: "Decimaal getal",
  Integer: "Geheel getal",
  "Sources & evidence": "Bronnen & bewijs",
  "Sources & imports": "Bronnen & import",
  "Stable code": "Stabiele code",
  "Stable tenant identity for API calls.": "Stabiele tenant identiteit voor API calls.",
  "Stable within this company, for example shopify_de.":
    "Stabiel binnen dit bedrijf, bijvoorbeeld shopify_de.",
  "Stage 1": "Fase 1",
  "Start in observation mode": "Begin in observatiemodus",
  "Start with an operational record, then follow its shortest true links through Evidence to the original SourceRecord.":
    "Begin met een operationeel record, en volg vervolgens de kortste, correcte links door Bewijs naar het originele Bronrecord.",
  "Start with observation": "Begin met observatie",
  "Start with Reality": "Begin met Realiteit",
  "Start with the operational view. Use traceability only when you need the complete explanation.":
    "Begin met het operationele overzicht. Gebruik traceerbaarheid alleen wanneer u een volledige uitleg nodig heeft.",
  "Stay in control.": "Blijf in controle.",
  "Still observe only": "Blijf alleen observeren",
  "Stock · data quality · execution hold": "Voorraad · datakwaliteit · uitvoering houden",
  "Stock enabled": "Voorraad ingeschakeld",
  "Supplier invoice": "Leveranciersfactuur",
  "Supplier reliability": "Leveranciersbetrouwbaarheid",
  "Supports traceable and verifiable ERP processes aligned with GoBD principles. Actual compliance also depends on operations, internal controls, retention and process documentation.":
    "Ondersteunt traceerbare en verifieerbare ERP-processen die zijn afgestemd op de GoBD-principes. Echte naleving hangt ook af van de operaties, interne controles, opslag en procesdocumentatie.",
  "Switch company": "Bedrijf overstappen",
  System: "Systeem",
  "System template": "Systeemtemplate",
  "Systeme bleiben führend": "Systemen blijven leidend",
  "Systems remain authoritative": "Systemen blijven autoritair",
  "Tax identifier": "Belastingidentificatienummer",
  "Tell us where you want to use Reality. You’ll receive access after a personal review.":
    "Vertel ons waar u Reality wilt gebruiken. U ontvangt toegang na een persoonlijke beoordeling.",
  "Test intake": "Testintake",
  "The complete path remains traceable to the immutable shop payload.":
    "De volledige route blijft traceerbaar naar de onveranderlijke winkelpayload.",
  "The first verified accounts are admitted automatically. After that, applications wait for your decision.":
    "De eerste geverifieerde accounts worden automatisch geaccepteerd. Daarna wachten de aanvragen op uw beslissing.",
  "The Operations Cockpit turns connected records into a daily control surface — exceptions first, evidence one step away, agent responsibility always visible.":
    "Het Operations Cockpit zet verbonden records om in een dagelijks controlesysteem — eerst uitzonderingen, bewijs op één stap afstand, verantwoordelijkheid van de agent altijd zichtbaar.",
  "The physical journal starts with the first receipt or opening stock.":
    "Het fysieke journaal begint met de eerste ontvangst of voorraad.",
  "The selected upstream payload, retained losslessly and versioned.":
    "De geselecteerde upstream payload, onverliesig bewaard en versie-gecontroleerd.",
  "These could be your operational numbers": "Dit kunnen uw operationele cijfers zijn",
  "These preferences apply only to your account, across every company you can access.":
    "Deze voorkeuren gelden alleen voor uw account, voor elk bedrijf dat u kunt raadplegen.",
  "This collection has no matching records.": "Deze collectie heeft geen overeenkomstige records.",
  "This creates a definition only. It does not connect to the external system or store credentials.":
    "Dit creëert alleen een definitie. Het verbindt zich niet met het externe systeem of slaat wachtwoorden op.",
  "This permanently deletes": "Dit verwijdert permanent",
  "This removes the company and every Source, Evidence, Reality, journal, integration and conversation belonging to it.":
    "Dit verwijdert het bedrijf en alle bijbehorende bronnen, bewijzen, realiteiten, journals, integraties en gesprekken.",
  "Thousands of events become a small number of clear exceptions that need attention.":
    "Duizenden gebeurtenissen worden omgezet in een klein aantal duidelijke uitzonderingen die aandacht vereisen.",
  "Tied-up business": "Vergrendelde bedrijf",
  Timezone: "Tijdszone",
  To: "Om",
  "Token name, e.g. Claude": "Token naam, bijv. Claude",
  "Tokens are scoped to this company. Reads use shared application tools; mutations still need an approval.":
    "Tokens zijn beperkt tot dit bedrijf. Lezen gebeurt met gedeelde applicatie-tools; wijzigingen hebben nog steeds een goedkeuring nodig.",
  Tool: "Tool",
  "Tool catalog": "Tool catalogus",
  "total runs": "totale runs",
  "Trace an answer": "Volg een antwoord",
  "Traceability / timeline": "Volgbaarheid / tijdlijn",
  "TRUST INCREASES": "VERTROUWENS WORDEN VERГОED",
  "Typed only when operationally useful": "Alleen getypt wanneer operationeel nuttig",
  "Typical operating pattern": "Typisch operationeel patroon",
  Unallocated: "Niet toegewezen",
  "Under 1,000": "Minder dan 1.000",
  UNDERSTAND: "BEGRIP",
  Unit: "Eenheid",
  "Unit price": "Eenheidsprijs",
  "Unit…": "Eenheid…",
  "Upstream vocabulary remains distinct from operational Reality.":
    "De upstream terminologie blijft gescheiden van de operationele Realiteit.",
  "Use a name operators recognize.": "Gebruik een naam die operators herkennen.",
  "Use a wider time range or remove a filter.":
    "Gebruik een breder tijdsbereik of verwijder een filter.",
  "Use source templates for modern commerce systems, immutable API intake, or controlled CSV and JSON imports. Each origin declares exactly which records Reality may receive.":
    "Gebruik bron-templates voor moderne commerce-systemen, onveranderlijke API-intake of gecontroleerde CSV- en JSON-importen. Elke bron verklaart precies welke records Reality kan ontvangen.",
  "Use Test intake or connect a source to record the first immutable payload.":
    "Gebruik Test-intake of verbind een bron om het eerste onveranderlijke payload op te nemen.",
  "Use this URL in your MCP client.": "Gebruik deze URL in uw MCP-klant.",
  "Used when a source does not supply one.": "Wordt gebruikt wanneer een bron geen aanbiedt.",
  "Used when new operational records are created.":
    "Wordt gebruikt wanneer nieuwe operationele records worden aangemaakt.",
  "Verification code": "Verificatiecode",
  "Verify email": "Verifieer e-mail",
  "Verify Reality's interpretation against immutable source evidence.":
    "Verifieer de interpretatie van Reality tegen onveranderlijke bron-bewijs.",
  Version: "Versie",
  View: "Bekijken",
  "Warehouse / allocation": "Magazijn / toewijzing",
  "Warehouse / physical journal": "Magazijn / fysiek journaal",
  "Warehouse / stock control": "Magazijn / voorraadbeheer",
  "Warehouses and stock locations": "Magazijnen en voorraadlocaties",
  "We will email you when your workspace is unlocked.":
    "We sturen u een e-mail wanneer uw werkruimte is ontgrendeld.",
  "Welcome back": "Welkom terug",
  "What an order, invoice, payment or file actually asserted.":
    "Wat een bestelling, factuur, betaling of bestand daadwerkelijk stelt.",
  "What can be decided": "Wat kan worden besloten",
  "What conflicts?": "Wat conflicteert?",
  "What evidence proves it?": "Welk bewijs bewijst dit?",
  "What external origin does this represent?": "Welke externe bron vertegenwoordigt dit?",
  "What happened?": "Wat is er gebeurd?",
  "What is true": "Wat is waar",
  "What needs attention": "Wat aandacht behoeft",
  "What Reality could reveal next": "Wat Reality de volgende keer kan onthullen",
  "Work email": "E-mail",
  "Working…": "In werking",
  Workspace: "Werkplek",
  "Workspace / companies": "Werkplek / bedrijven",
  "Workspace setup": "Opzetten van de werkplek",
  Yes: "Ja",
  "You’re on the list": "U staat op de lijst",
  "Your existing systems remain in place. Reality receives only the operational records you explicitly accept.":
    "Uw bestaande systemen blijven actief. Reality ontvangt alleen de operationele gegevens die u expliciet accepteert.",
  "Your name": "Uw naam",
  "Your profile": "Uw profiel",
  "Your sign-in identity.": "Uw inlogidentiteit.",
  "Your systems stay in place. Nothing changes automatically.":
    "Uw systemen blijven actief. Er worden geen wijzigingen automatisch aangebracht.",
  Document: "Document",
  Records: "Records",
  Status: "Status",
  Type: "Type",
});

Object.assign(dictionaries.es, {
  "Read product documentation": "Leer la documentación del producto",
  "Understand concepts, integrations, interfaces and deployment.":
    "Comprenda conceptos, integraciones, interfaces y despliegue.",
  "Open Docs": "Abrir documentación",
  "· Manual operational reference": "· Referencia operativa manual",
  "+12 pp": "+12 unidades",
  "€24,600 waits for stock or approval": "€24.600 pendiente de stock o aprobación",
  "12 of 18 decisions were repeatable": "12 de 18 decisiones eran repetibles",
  "24 hours": "24 horas",
  "3 at risk": "3 en riesgo",
  "30 days": "30 días",
  "4 h 19 min": "4 h 19 min",
  "4 h 19 min until shipment": "4 h 19 min hasta el envío",
  "47 min": "47 min",
  "7 days": "7 días",
  "7 orders": "7 pedidos",
  "A company contains its own sources, operational records and agent configuration.":
    "Una empresa contiene sus propias fuentes, registros operativos y configuración de agentes.",
  "A paid order is blocked despite available inventory. Reality connects the payment, commitment, reservation and delivery hold — then proposes the exact resolution with its evidence.":
    "Un pedido pagado está bloqueado a pesar de la disponibilidad de inventario. La realidad conecta el pago, el compromiso, la reserva y la espera de entrega — y propone la solución exacta con sus pruebas.",
  "A person confirms the exact business effect.":
    "Una persona confirma el efecto exacto en el negocio.",
  "A recommendation or controlled action with its reason intact.":
    "Una recomendación o acción controlada con su razón intacta.",
  Accepted: "Aceptado",
  "Accepted payloads stay lossless and traceable":
    "Los payloads aceptados permanecen sin pérdida y rastreables",
  Access: "Acceso",
  "Access applications": "Aplicaciones de acceso",
  "Platform overview": "Resumen de la plataforma",
  Overview: "Resumen",
  Deployment: "Despliegue",
  People: "Personas",
  "Security trail": "Registro de seguridad",
  "Loading platform state…": "Cargando el estado de la plataforma…",
  Generated: "Generado",
  "No recorded events yet.": "Aún no hay eventos registrados.",
  "by the system": "por el sistema",
  "platform admin": "administrador de la plataforma",
  "email unverified": "correo sin verificar",
  "awaiting approval": "esperando aprobación",
  "oldest application": "solicitud más antigua",
  Sessions: "Sesiones",
  "Last login": "Último inicio de sesión",
  Created: "Creado",
  Owners: "Propietarios",
  "Open invitations": "Invitaciones abiertas",
  "Business events": "Eventos de negocio",
  "imports pending": "importaciones pendientes",
  "imports failed": "importaciones fallidas",
  "projections not ready": "proyecciones no listas",
  "invitation mail stuck": "correo de invitación atascado",
  "delivered invitations": "invitaciones entregadas",
  "active agent tokens": "tokens de agente activos",
  "not marked secure": "sin marcar como seguras",
  "kept private": "se mantienen privados",
  "returned by the API": "devueltos por la API",
  "missing — encrypted credentials stay unreadable":
    "falta: las credenciales cifradas quedan ilegibles",
  "Access requested": "Acceso solicitado",
  Account: "Cuenta",
  "Accounting code": "Código de contabilidad",
  Action: "Acción",
  Actions: "Acciones",
  Activate: "Activar",
  Active: "Activo",
  "Active allocations linked directly to their customer Commitments.":
    "Asignaciones activas vinculadas directamente a sus compromisos del cliente.",
  "Active companies": "Empresas activas",
  "Active company": "Empresa activa",
  "Activity & timeline": "Actividad y cronograma",
  "Activity over 24 hours": "Actividad de 24 horas",
  "Add a source or upload a file, then review its interpreted operational observations.":
    "Añadir una fuente o subir un archivo, y luego revisar sus observaciones operativas interpretadas.",
  "Add line": "Añadir línea",
  "Add source": "Añadir fuente",
  "Add the first origin before accepting external records.":
    "Añadir la primera fuente antes de aceptar registros externos.",
  "Add the first rule when the business needs it.":
    "Añadir la primera regla cuando lo necesite el negocio.",
  "Agents & AI": "Agentes y IA",
  "Agents use the same tenant-scoped application tools as the UI and CLI. Permissions, confirmation and evidence remain part of the operating model.":
    "Los agentes utilizan las mismas herramientas de aplicación con ámbito de inquilino que la interfaz de usuario y la CLI. Los permisos, la confirmación y la evidencia siguen siendo parte del modelo operativo.",
  "AI configuration": "Configuración de IA",
  "All business areas": "Todas las áreas de negocio",
  "All directions": "Todas las direcciones",
  "All document types": "Todos los tipos de documentos",
  "All facts": "Todos los hechos",
  "All flows": "Todos los flujos",
  "All priorities": "Todas las prioridades",
  "All records are retained, but the company is hidden from daily work.":
    "Todos los registros se conservan, pero la empresa se oculta del trabajo diario.",
  "All states": "Todos los estados",
  "All stock states": "Todos los estados de inventario",
  "All tools": "Todas las herramientas",
  Allocated: "Asignado",
  "Allow all tools": "Permitir todas las herramientas",
  "Allow physical stock at this location": "Permitir inventario físico en esta ubicación",
  "Already have access? Sign in": "¿Ya tiene acceso? Iniciar sesión",
  "Already have an account?": "¿Ya tiene una cuenta?",
  "and its complete conversation history.": "y su historial de conversación completo.",
  AP: "AP",
  "API key": "Clave de API",
  "API key stored encrypted": "Clave de API almacenada encriptada",
  "Append-only receipts, transfers, adjustments and shipments.":
    "Recibos, transferencias, ajustes y envíos de solo lectura.",
  "Approval required": "Se requiere aprobación",
  "Approved, executed and rejected decisions will appear here.":
    "Las decisiones aprobadas, ejecutadas y rechazadas aparecerán aquí.",
  "Archive chat": "Archivar chat",
  "Archive conversation": "Archivar conversación",
  "Archive this chat?": "¿Archivar este chat?",
  "Archived conversations remain available here and can be restored.":
    "Las conversaciones archivadas permanecen disponibles aquí y se pueden restaurar.",
  "Archiving…": "Archivando…",
  "Decision history": "Historial de decisiones",
  "leaves the active list. Its complete history is retained and can be restored. Pending approvals remain in the decision queue.":
    "sale de la lista activa. Su historial completo se conserva y se puede restaurar. Las aprobaciones pendientes permanecen en la cola de decisiones.",
  "No archived chats": "No hay chats archivados",
  "No decision history": "No hay historial de decisiones",
  "No pending approvals": "No hay aprobaciones pendientes",
  "Nothing currently waits for approval.": "Actualmente nada espera aprobación.",
  "Pending approvals": "Aprobaciones pendientes",
  "Restore chat": "Restaurar chat",
  "Review operational risks and every business decision that waits for approval.":
    "Revise los riesgos operativos y cada decisión empresarial que espera aprobación.",
  Approve: "Aprobar",
  "Approve & execute": "Aprobar y ejecutar",
  "Approve and execute this action?": "¿Aprobar y ejecutar esta acción?",
  AR: "AR",
  "Archive before permanently deleting this company and its tenant-scoped records.":
    "Archivar antes de eliminar permanentemente esta empresa y sus registros con ámbito de inquilino.",
  "Archived companies": "Empresas archivadas",
  "are currently exposed": "están actualmente expuestas",
  Area: "Área",
  "Ask about inventory, commitments, payments or operational risk.":
    "Pregunte sobre inventario, compromisos, pagos o riesgos operativos.",
  "Ask Reality…": "Pregunte a Reality…",
  "Ask what to do next": "Pregunte qué hacer a continuación",
  "At least 10 characters.": "Al menos 10 caracteres.",
  "At risk": "En riesgo",
  Attempts: "Intentos",
  "Audit Trail": "Rastreo de auditoría",
  "Auditable structure": "Estructura auditada",
  "Auf Deutsch wechseln": "Cambiar a alemán",
  "Ausgewählte Payloads fließen aus bestehenden Systemen in Reality":
    "Cargas seleccionadas fluyen de sistemas existentes en Reality",
  "Ausgewählter Payload · verlustfrei bewahrt": "Carga seleccionada · preservada sin pérdidas",
  Automate: "Automatizar",
  "automatic access slots used": "Slots de acceso automático utilizados",
  Automation: "Automatización",
  "Automation potential": "Potencial de automatización",
  "Autonomous commerce core": "Núcleo de comercio autónomo",
  "AUTONOMOUS COMMERCE CORE": "NÚCLEO DE COMERCIO AUTÓNOMO",
  "Autonomy is granted per capability — never for everything at once.":
    "La autonomía se otorga por capacidad — nunca para todo a la vez.",
  "Autonomy is never a global switch. Every capability advances only after its observations and recommendations have earned trust.":
    "La autonomía nunca es un interruptor global. Cada capacidad solo avanza después de que sus observaciones y recomendaciones hayan ganado confianza.",
  "AUTONOMY UNLOCKED": "AUTONOMÍA DESBLOQUEADA",
  "Available application tools": "Herramientas de aplicación disponibles",
  "Avoidable work": "Trabajo evitables",
  "awaiting explicit confirmation": "esperando confirmación explícita",
  "Back to Data settings": "Volver a la configuración de datos",
  "Back to parties": "Volver a las partes",
  "Backend unavailable": "Backend no disponible",
  "Bike Light causes 43% of delays": "La luz de bicicleta causa el 43% de los retrasos",
  "Blocked revenue": "Ingresos bloqueados",
  "Build an operational picture you can verify before granting any agent permission to act.":
    "Cree una imagen operativa que pueda verificar antes de otorgar cualquier permiso a un agente.",
  "Business events remain stored in UTC and are converted for your interface.":
    "Los eventos comerciales permanecen almacenados en UTC y se convierten para su interfaz.",
  "Business roles": "Roles comerciales",
  "can ship today": "puede enviar hoy",
  Cancelled: "Cancelado",
  "Change the filters or add an active item.": "Cambie los filtros o agregue un elemento activo.",
  "Change the filters or import source evidence.":
    "Cambie los filtros o importe la evidencia de origen.",
  "Change the filters or ingest invoice evidence.":
    "Cambie los filtros o ingeste la evidencia de factura.",
  "Change the filters or ingest new promise evidence.":
    "Cambie los filtros o ingeste nueva evidencia de promesa.",
  "Change the search or create the first record.": "Cambie la búsqueda o cree el primer registro.",
  "Changes affect your account only.": "Los cambios afectan solo a su cuenta.",
  "Chart period": "Período de gráfico",
  Chats: "Chats",
  "Archived chats": "Chats archivados",
  "Back to chats": "Volver a los chats",
  "Check your inbox": "Verifique su bandeja de entrada",
  "Choose a record from the middle column.": "Elija un registro de la columna central.",
  "Choose allowed tools": "Elija las herramientas permitidas",
  Classification: "Clasificación",
  "Close company menu": "Cierre del menú de la empresa",
  "Close inspector": "Cierre del inspector",
  "Close navigation": "Cierre de la navegación",
  Code: "Código",
  Collections: "Colecciones",
  "Comma-separated: company, customer, supplier": "Separado por comas: empresa, cliente, proveedor",
  Commerce: "Comercio",
  "Commercial prices by direction and currency.": "Precios comerciales por dirección y moneda.",
  "Commercial reference": "Referencia comercial",
  "Commercial terms": "Términos comerciales",
  "Companies, customers and suppliers": "Empresas, clientes y proveedores",
  "Company configuration": "Configuración de la empresa",
  "Company ID": "ID de la empresa",
  "Company management": "Gestión de la empresa",
  "Company name": "Nombre de la empresa",
  "Company settings / agents": "Configuración de la empresa / agentes",
  "Company settings / commercial": "Configuración de la empresa / comercial",
  "Company settings / data": "Configuración de la empresa / datos",
  "Company website": "Sitio web de la empresa",
  "Configure sources and inspect recently received records.":
    "Configure fuentes e inspeccione los registros recibidos recientemente.",
  "Configure the model used by this company and issue tenant-scoped HTTPS MCP credentials.":
    "Configure el modelo utilizado por esta empresa y emita credenciales HTTPS MCP a nivel de inquilino.",
  "Configured — leave empty to keep": "Configurado — dejar en blanco para mantener",
  Connect: "Conectar",
  "Connect a source": "Conectar una fuente",
  "Connect a source and Reality observes how reliably orders flow through your company—without changing anything.":
    "Conectar una fuente y Reality observa con qué fiabilidad fluyen los pedidos a través de su empresa—sin cambiar nada.",
  "Connect external origins, upload files and test the same immutable intake used by integrations.":
    "Conectar orígenes externos, subir archivos y probar la misma entrada inmutable utilizada por las integraciones.",
  "Connect one source. Start by observing.": "Conectar una fuente. Empezar observando.",
  "Connect one source. Verify what Reality learns.":
    "Conectar una fuente. Verifique lo que Reality aprende.",
  "Connect systems": "Conectar sistemas",
  "Connect the tools your business already runs on.":
    "Conectar las herramientas que ya utiliza su negocio.",
  "Connect your business": "Conecte su negocio",
  "Connect your first source": "Conecte su primera fuente",
  Continue: "Continuar",
  "Continue to your Reality workspace.": "Continúe a su espacio de trabajo de Reality.",
  "Control incoming and outgoing commitments, reservation coverage and due-date risk.":
    "Controle las obligaciones, la cobertura de reservas y el riesgo de fechas de vencimiento entrantes y salientes.",
  "Control remains explicit at every level.":
    "El control permanece explícito en todos los niveles.",
  "Controls decimals, dates and currency formatting.":
    "Controla decimales, fechas y formato de moneda.",
  "Controls labels and interface text.": "Controla etiquetas y texto de la interfaz.",
  Copied: "Copiado",
  "Copilot prepared an action but has not changed business state.":
    "Copilot preparó una acción, pero no ha cambiado el estado del negocio.",
  "Copilot provider": "Proveedor de Copilot",
  "Copy this token now": "Copie este token ahora",
  "Copy URL": "Copie la URL",
  "Could not load choices:": "No se pudieron cargar las opciones:",
  "Could not load this view": "No se pudo cargar esta vista",
  Covered: "Cubierto",
  "Create account": "Crear cuenta",
  "Create companies, inspect their operational footprint, or archive workspaces without losing data.":
    "Cree empresas, inspeccione su huella operativa o archive espacios de trabajo sin perder datos.",
  "Create company": "Crear empresa",
  "Create document": "Crear documento",
  "Create scoped token": "Crear token con ámbito",
  "Create source": "Crear fuente",
  "Create token": "Crear token",
  "Create your account": "Cree su cuenta",
  "Create your account. We review every new workspace personally.":
    "Cree su cuenta. Revisamos cada nuevo espacio de trabajo personalmente.",
  "Create your first company": "Cree su primera empresa",
  "Create empty company": "Crear empresa vacía",
  "Try the guided demo": "Probar la demostración guiada",
  "Create a sample company with an explainable order, stock, commitments and shortage.":
    "Cree una empresa de ejemplo con pedido, inventario, compromisos y faltante explicables.",
  "Preview demo": "Ver demostración",
  "This will add sample business records to the new company.":
    "Esto añadirá registros empresariales de ejemplo a la nueva empresa.",
  "Create demo company": "Crear empresa de demostración",
  "Creates normalized evidence. Operational commitments remain explicit.":
    "Crea evidencia normalizada. Los compromisos operativos permanecen explícitos.",
  "Creating account…": "Creando cuenta…",
  "Creating…": "Creando…",
  "Credit limit": "Límite de crédito",
  "Credit note": "Nota de crédito",
  "Cross-domain signals connect causes directly to their business impact.":
    "Señales entre dominios conectan directamente las causas con su impacto empresarial.",
  Currency: "Moneda",
  "Currency…": "Moneda…",
  "Current company": "Empresa actual",
  "Current derived view": "Vista derivada actual",
  "Current exceptions": "Excepciones actuales",
  "Current operating mode": "Modo operativo actual",
  "Current workspace lifecycle.": "Ciclo de vida del espacio de trabajo actual.",
  "Custom source": "Fuente personalizada",
  "Customer reference": "Referencia del cliente",
  "Danger zone": "Zona de peligro",
  "Data / explorer": "Datos / explorador",
  "Data / immutable intake": "Datos / entrada inmutable",
  "Data received from": "Datos recibidos de",
  "Data stays in its systems. Reality retains only what operations need — losslessly and traceably.":
    "Los datos permanecen en sus sistemas. Reality retiene solo lo que las operaciones necesitan — de forma sin pérdida y rastreable.",
  DE: "DE",
  Deactivate: "Desactivar",
  Decision: "Decisión",
  Default: "Predeterminado",
  "Define which source types this workspace may receive.":
    "Defina qué tipos de fuentes puede recibir este espacio de trabajo.",
  Delegate: "Delegar",
  "Delegate one capability": "Delegar una capacidad",
  "Delegate step by step": "Delegar paso a paso",
  Delete: "Eliminar",
  DELETE: "ELIMINAR",
  "Delete chat": "Eliminar chat",
  "Delete company permanently": "Eliminar empresa permanentemente",
  "Delete conversation": "Eliminar conversación",
  "Delete permanently": "Eliminar permanentemente",
  "Delete this chat?": "¿Eliminar este chat?",
  "Deleting…": "Eliminando…",
  Description: "Descripción",
  Deutsch: "Alemán",
  "Deutsch (Deutschland)": "Alemán (Alemania)",
  Direction: "Dirección",
  Disabled: "Deshabilitado",
  "Display name": "Nombre de visualización",
  "Display timezone for operators.": "Mostrar zona horaria para los operadores.",
  "Document date": "Fecha del documento",
  "Document link · Timestamp · Lineage · Change log · Tenant scope · Confirmation":
    "Enlace del documento · Marca de tiempo · Origen · Registro de cambios · Alcance del inquilino · Confirmación",
  "Document type": "Tipo de documento",
  "Drop source data": "Eliminar datos de origen",
  Due: "Debido a",
  "Each company gets isolated sources, facts, operational records and agent access.":
    "Cada empresa obtiene fuentes, datos, registros operativos y acceso al agente de forma aislada.",
  "Each shop, PIM, CRM or payment account is a separate origin.":
    "Cada tienda, PIM, CRM o cuenta de pago es un origen separado.",
  "Edit party": "Editar parte",
  Email: "Correo electrónico",
  Endpoint: "Punto final",
  English: "Inglés",
  "English (United Kingdom)": "Inglés (Reino Unido)",
  "Enter a new value": "Introducir un nuevo valor",
  "Enter API key": "Introducir clave API",
  "Enter DELETE": "Introducir DELETE",
  "Enter the exact company name": "Introducir el nombre exacto de la empresa",
  Español: "Español",
  "Español (España)": "Español (España)",
  Events: "Eventos",
  "Events & activity": "Eventos y actividad",
  "Every answer stays connected to what actually happened.":
    "Cada respuesta permanece conectada con lo que realmente ocurrió.",
  "Evidence / document register": "Registro de evidencia / documento",
  "Evidence, permissions and confirmation remain part of every step.":
    "La evidencia, los permisos y la confirmación permanecen como parte de cada paso.",
  Example: "Ejemplo",
  "EXAMPLE CAPABILITY": "CAPACIDAD DE EJEMPLO",
  "Example insights · no live data": "Ejemplos de información · sin datos en vivo",
  "Example orders received and shipped by day": "Ejemplos de pedidos recibidos y enviados por día",
  "Example preview · no live data": "Vista de ejemplo · sin datos en vivo",
  "Example trace · no live data": "Rastreo de ejemplo · sin datos en vivo",
  "Execute only the proven capability within explicit rules.":
    "Ejecutar solo la capacidad probada dentro de las reglas explícitas.",
  EXPLAIN: "EXPLICAR",
  "Explain physical, reserved, available and projected stock without storing a presentation balance.":
    "Explique el inventario físico, reservado, disponible y proyectado sin almacenar un saldo de presentación.",
  "Explain the current Reality": "Explique la realidad actual",
  "Explicit, source-supported observations currently retained by Reality. Facts never replace their immutable source.":
    "Observaciones de origen soportadas explícitamente actualmente retenidas por la realidad. Los hechos nunca reemplazan su fuente inmutable.",
  Explore: "Explorar",
  "External agents": "Agentes externos",
  "External ID": "ID externo",
  "External identity": "Identidad externa",
  Facts: "Hechos",
  "Facts · Commitments · Reservations · Movements · Lots · Serials · SSCC":
    "Hechos · Compromisos · Reservas · Movimientos · Lotes · Números de serie · SSCC",
  "Facts appear when a source-backed observation is interpreted.":
    "Los hechos aparecen cuando una observación de origen es interpretada.",
  "Facts, commitments and movements used by operations.":
    "Hechos, compromisos y movimientos utilizados por las operaciones.",
  Finance: "Finanzas",
  "Finance / cash": "Finanzas / efectivo",
  "Finance / subledger": "Finanzas / sublibro",
  "Finance Ledger": "Libro de cuentas de finanzas",
  "First verify that Reality understands your business. Nothing is changed automatically.":
    "Verifique primero que la realidad comprende su negocio. Nada se cambia automáticamente.",
  "Follow Reality through Evidence to its original SourceRecord.":
    "Siga a la realidad a través de la evidencia hasta su SourceRecord original.",
  From: "Desde",
  "From original evidence to the ledger. Linked end to end.":
    "Desde la evidencia original hasta el libro de cuentas. Enlazado de extremo a extremo.",
  Fulfilled: "Cumplido",
  "Fully allocated": "Completamente asignado",
  "Get started": "Comenzar",
  "No data yet": "Sin datos todavía",
  "Give agents responsibility one capability at a time.":
    "Asigne a los agentes una capacidad a la vez.",
  Gross: "Bruto",
  "Gross amount": "Monto bruto",
  "Help & documentation": "Ayuda y documentación",
  Appearance: "Apariencia",
  "Applies immediately and is stored on this device.":
    "Se aplica de inmediato y se guarda en este dispositivo.",
  Light: "Claro",
  Dark: "Oscuro",
  Resources: "Recursos",
  Documentation: "Documentación",
  "Reality website": "Sitio web de Reality",
  "Help & reference": "Ayuda y referencia",
  "Here is what Reality knows": "Aquí está lo que Reality sabe",
  "How can I help?": "¿Cómo puedo ayudar?",
  "How one order became operational reality":
    "Cómo un pedido se convierte en la realidad operativa",
  "How Reality may act": "Cómo puede actuar Reality",
  "HTTPS endpoint": "Punto final HTTPS",
  "HTTPS MCP": "HTTPS MCP",
  "https://…/v1": "https://…/v1",
  "Human confirmation": "Confirmación humana",
  "I agree to the Terms and Privacy Policy.":
    "Estoy de acuerdo con los Términos y la Política de Privacidad.",
  "Identity and defaults used across this company workspace.":
    "Identidad y valores predeterminados utilizados en este espacio de trabajo de la empresa.",
  "Identity, commercial defaults and source reference.":
    "Identidad, valores predeterminados comerciales y referencia de origen.",
  "Immutable intake": "Entrada inmutable",
  "Immutable source intake": "Entrada de origen inmutable",
  "Immutable SourceRecords · Versioned payloads · Documents · Document lines":
    "Registros de origen inmutables · Cargas versionadas · Documentos · Líneas de documentos",
  "Import a bank statement or change the filters.":
    "Importe un extracto bancario o cambie los filtros.",
  "Import evidence": "Importe evidencia",
  "Import jobs": "Importe trabajos",
  "Import statement": "Declaración de importación",
  In: "En",
  "in the example period": "en el período de ejemplo",
  "In use": "En uso",
  Inactive: "Inactivo",
  "Includes future tools": "Incluye herramientas futuras",
  Infrastructure: "Infraestructura",
  Input: "Entrada",
  Inspect: "Inspeccionar",
  "Inspect & trace": "Inspeccionar y rastrear",
  "Inspect and trace data": "Inspeccionar y rastrear datos",
  "Inspect documents and their shortest links into Reality.":
    "Inspeccionar documentos y sus enlaces más cortos hacia Reality.",
  "Inspect normalized documents and their links into operational Reality.":
    "Inspeccionar documentos normalizados y sus enlaces hacia la realidad operativa.",
  "Instance code": "Código de instancia",
  "Interpreter ready": "Interpretador listo",
  "Inventory and reservations": "Inventario y reservas",
  "Inventory position": "Posición de inventario",
  Invoice: "Factura",
  Invoicing: "Facturación",
  "Irreversible deletion": "Eliminación irreversible",
  "It will not be shown again.": "No se mostrará nuevamente.",
  "Last activity": "Última actividad",
  "Last error": "Último error",
  "LEARNS FROM EVIDENCE": "APRENDE DE LAS PRUEBAS",
  "Ledger / Action": "Libro mayor / Acción",
  "Ledger entries · Open items · Allocations · Payments · Settlement · Reconciliation":
    "Entradas del libro mayor · Elementos pendientes · Asignaciones · Pagos · Liquidación · Conciliación",
  "Let agents run the business.": "Permitir que los agentes gestionen el negocio.",
  "Let Reality surface contradictions and explain their business impact.":
    "Permitir que la Realidad revele contradicciones y explique su impacto en el negocio.",
  "Line items": "Elementos de la línea",
  "Loading available systems…": "Cargando sistemas disponibles…",
  "Loading choices…": "Cargando opciones…",
  "Loading…": "Cargando…",
  Location: "Ubicación",
  "Longest wait": "Mayor tiempo de espera",
  "Lossless JSON payload": "Carga JSON sin pérdidas",
  "Losslessly stored input": "Entrada almacenada sin pérdidas",
  "Main navigation": "Navegación principal",
  "Maintain only the operational references and normalized evidence Reality needs. Complete ERP records remain in their source systems.":
    "Mantener solo las referencias operativas y la evidencia normalizada que la Realidad necesita. Los registros ERP completos permanecen en sus sistemas de origen.",
  "Maintain payment terms, price lists and pricing groups used for due dates and price resolution.":
    "Mantener los términos de pago, listas de precios y grupos de precios utilizados para la resolución de fechas y precios.",
  "Manage the typed identities and commercial rules Reality repeatedly uses.":
    "Gestionar las identidades y reglas comerciales que la Realidad utiliza repetidamente.",
  "Manage your personal identity and how Reality displays dates, times and numbers.":
    "Gestionar su identidad personal y cómo la Realidad muestra fechas, horas y números.",
  "Manual evidence": "Evidencia manual",
  Model: "Modelo",
  "Model identifier": "Identificador de modelo",
  "Monday clears the weekend backlog": "El lunes elimina el retraso del fin de semana",
  "Monitor import jobs and the rebuildable projections used by the product.":
    "Monitorizar las tareas de importación y las proyecciones reconstruibles utilizadas por el producto.",
  "Monitor operations": "Monitorizar las operaciones",
  "Monitor the operating machine, isolate exceptions and trace each change to its source.":
    "Monitorizar la máquina de operación, aislar excepciones y rastrear cada cambio a su origen.",
  "Move from observation to recommendations only when you trust the result.":
    "Mover de la observación a las recomendaciones solo cuando confíe en el resultado.",
  Nederlands: "Nederlands",
  "Nederlands (Nederland)": "Nederlands (Nederland)",
  "need attention": "necesita atención",
  New: "Nuevo",
  "New conversation": "Nueva conversación",
  "New document": "Nuevo documento",
  "New to Reality?": "¿Nuevo en la Realidad?",
  No: "No",
  "No accepted record types": "Tipos de registros no aceptados",
  "No active MCP tokens.": "No hay tokens MCP activos.",
  "No activity matches": "No hay actividad que coincida",
  "No activity yet": "Sin actividad aún",
  "1 event": "1 evento",
  "No API key stored": "Sin clave de API almacenada",
  "No archived companies.": "Sin empresas archivadas.",
  "No business state will be changed. The rejection remains visible in the conversation history.":
    "Ningún estado de la empresa será cambiado. La cancelación sigue visible en el historial de la conversación.",
  "No commitments match": "Sin compromisos coincidentes",
  "No commitments.": "Sin compromisos.",
  "No documents.": "Sin documentos.",
  "no due date": "Sin fecha de vencimiento",
  "No evidence matches": "Sin evidencia coincidente",
  "No explicit facts yet": "Sin hechos explícitos aún",
  "No facts yet": "Sin hechos aún",
  "No imports yet": "Sin importaciones aún",
  "No inventory matches": "No hay inventario que coincida",
  "No linked records.": "No hay registros vinculados.",
  "No matching records": "No hay registros coincidentes",
  "No movements": "No hay movimientos",
  "No open exceptions": "No hay excepciones abiertas",
  "No open items match": "No hay elementos abiertos que coincidan",
  "No operational activity yet": "No hay actividad operativa aún",
  "No payment events": "No hay eventos de pago",
  "No recorded events for this record.": "No hay eventos registrados para este registro.",
  "No records": "No hay registros",
  "No records match": "No hay registros que coincidan",
  "No reservations": "No hay reservas",
  "No source records yet": "No hay registros de origen aún",
  "No source systems": "No hay sistemas de origen",
  "No stock": "No hay stock",
  None: "Ninguno",
  "Nordlicht delivers only 78% on time": "Nordlicht entrega solo el 78% a tiempo",
  "Normalized business evidence with direct links to Reality and its original source.":
    "Evidencia comercial normalizada con enlaces directos a Reality y su fuente original.",
  "Nothing currently requires review.": "Nada requiere revisión actualmente.",
  "Nothing needs attention": "Nada necesita atención",
  "Nothing selected": "Nada seleccionado",
  Now: "Ahora",
  Number: "Número",
  "Nur bei operativem Nutzen typisiert": "Solo para uso operativo tipificado",
  Observe: "Observar",
  OBSERVE: "OBSERVAR",
  "Observe first, automate when trusted": "Observar primero, automatizar cuando sea de confianza",
  "Observe only": "Observar solo",
  "Observe what matters": "Observar lo que es importante",
  "Observed cash postings and their current allocation state.":
    "Registrar las transacciones de efectivo y su estado actual de asignación.",
  Occurred: "Ocurrió",
  "One exception. One explainable resolution.": "Una excepción. Una solución explicable.",
  "One operational core for facts, decisions and accountable automation.":
    "Un núcleo operativo para hechos, decisiones y automatización responsable.",
  "One operational core. Your systems remain in place.":
    "Un núcleo operativo. Sus sistemas permanecen en su lugar.",
  "Only operationally useful fields become typed Reality":
    "Solo los campos útiles para la operación se tipizan Reality",
  Open: "Abrir",
  "Open a register to search, create, inspect or maintain records.":
    "Abrir un registro para buscar, crear, inspeccionar o mantener registros.",
  "Open backlog": "Abrir la cola de tareas",
  "Open company": "Abrir empresa",
  "Open Evidence": "Abrir Evidencia",
  "Open Explorer": "Abrir Explorador",
  "Open Home": "Abrir Inicio",
  "Open Integrations": "Abrir Integraciones",
  "Open Items": "Abrir Elementos",
  "Open navigation": "Abrir navegación",
  "Open one company to manage its complete configuration.":
    "Abrir una empresa para gestionar su configuración completa.",
  "Open one focused viewer for records, events or evidence.":
    "Abrir un visor enfocado para registros, eventos o evidencia.",
  "Open Timeline": "Abrir Cronología",
  "Open warehouse view": "Abrir vista del almacén",
  "OpenAI-compatible base URL": "URL base compatible con OpenAI",
  "Opening Reality": "Abrir Realidad",
  "Operating machine": "Operar máquina",
  "Operational context active": "Contexto operativo activo",
  "OPERATIONAL CORE": "CORAZÓN OPERATIVO",
  "Operational defaults": "Parámetros operativos",
  "Operational facts": "Hechos operativos",
  "Operational reality": "Realidad operativa",
  "Operational Reality": "Realidad operativa",
  "Operational reference": "Referencia operativa",
  Operations: "Operaciones",
  "Operations / decision queue": "Operaciones / cola de decisiones",
  "Operations / promise control": "Operaciones / control de promesas",
  "Optional origin reference; the complete upstream record remains in its immutable payload.":
    "Referencia de origen opcional; el registro upstream completo permanece en su payload inmutable.",
  "Optional. Set together with the upstream External ID.":
    "Opcional. Establecer junto con el External ID upstream.",
  "Order flow": "Flujo de pedidos",
  "Orders continue at weekends while shipping follows warehouse cut-off times.":
    "Los pedidos continúan los fines de semana mientras que el envío sigue los horarios de corte del almacén.",
  "Orders per day": "Pedidos por día",
  "Orders received": "Pedidos recibidos",
  "Orders received & shipped": "Pedidos recibidos y enviados",
  "Orders, commitments and holds": "Pedidos, compromisos y reservas",
  "Orders, stock, payments and promises are observed together. Reality exposes contradictions, business impact and the source evidence behind every conclusion.":
    "Los pedidos, el inventario, los pagos y las promesas se observan juntos. La realidad expone contradicciones, el impacto empresarial y la evidencia de origen detrás de cada conclusión.",
  Origin: "Origen",
  "Original source payload": "Fuente original",
  Out: "Salir",
  Outgoing: "Saliente",
  "over 30 days": "más de 30 días",
  Paid: "Pagado",
  Partial: "Parcial",
  "Party account and connected business evidence.":
    "Cuenta de cliente y evidencia de la empresa relacionada.",
  Password: "Contraseña",
  Payables: "Pagos",
  "Payload must be valid JSON.": "El payload debe ser un JSON válido.",
  "Payment term": "Plazo de pago",
  "Payment terms": "Términos de pago",
  "Payment terms, price lists and pricing groups":
    "Términos de pago, listas de precios y grupos de precios",
  "Payments and open items": "Pagos y elementos pendientes",
  "permanently?": "¿Permanentemente?",
  "Personal settings": "Configuración personal",
  "Platform administration": "Administración de la plataforma",
  Posted: "Publicado",
  "PostgreSQL fact journal · Append-only records · S3-compatible object store · Projections · Backups / PITR":
    "Base de datos PostgreSQL · Registros de solo lectura · Almacenamiento de objetos compatible con S3 · Proyecciones · Copias de seguridad / Recuperación de desastres",
  "Posting group": "Grupo de registro",
  "Prepare a precise next action and show the evidence.":
    "Preparar la siguiente acción precisa y mostrar la evidencia.",
  "Price lists": "Listas de precios",
  "Pricing groups": "Grupos de precios",
  "Primary role": "Rol principal",
  "Problem item": "Elemento de problema",
  "Processing coverage": "Cobertura de procesamiento",
  "Processing latency": "Latencia de procesamiento",
  "Products, services and charges": "Productos, servicios y cargos",
  Projection: "Proyección",
  Projections: "Proyecciones",
  Promised: "Prometido",
  "Promised date": "Fecha prometida",
  "Bills order line": "Factura la línea de pedido",
  "Order line id, if this bills one": "Identidad de la línea de pedido, si esta línea factura una",
  "Approvals can be enabled later": "Las aprobaciones pueden habilitarse más tarde",
  "Where to begin": "Por dónde empezar",
  "Step 1": "Paso 1",
  "Reality knows only what a source shows it. Nothing is imported until you accept it.":
    "Reality solo conoce lo que una fuente le muestra. No se importa nada hasta que lo aceptas.",
  "Connect a system or upload a file": "Conecta un sistema o sube un archivo",
  "Accept the records you want interpreted": "Acepta los registros que quieres que se interpreten",
  "Verify the facts Reality derives": "Verifica los hechos que Reality deriva",
  Provider: "Proveedor",
  "Purchase order": "Orden de compra",
  Purpose: "Propósito",
  Quantity: "Cantidad",
  "Raw only": "Solo datos brutos",
  "Read models": "Modelos de lectura",
  "Read-only answers are immediate. Any change to business Reality waits for an approval until a person confirms it.":
    "Las respuestas de solo lectura son inmediatas. Cualquier cambio en el Reality del negocio espera una aprobación hasta que una persona lo confirme.",
  "Read-only understanding is immediate. Business changes wait for an explicit approval until a person confirms them.":
    "La comprensión de solo lectura es inmediata. Los cambios en el negocio esperan una aprobación explícita hasta que una persona los confirme.",
  "Read, reconcile and explain without changing business state.":
    "Leer, conciliar y explicar sin cambiar el estado del negocio.",
  "Reality · Autonomous commerce core": "Realidad · Núcleo de comercio autónomo",
  "Reality connects operational data into an explainable business reality — a trusted foundation for decisions and step-by-step autonomy.":
    "La realidad conecta los datos operativos en una realidad empresarial explicable — una base de confianza para las decisiones y la autonomía paso a paso.",
  "Reality Explorer": "Explorador de Realidad",
  "Reality found no current operational contradiction or uncovered promise.":
    "La realidad no encontró ninguna contradicción operativa actual ni promesa.",
  "Reality home": "Inicio de Realidad",
  "Reality inspector": "Inspector de Realidad",
  "Reality is not another ERP. It receives selected operational events, preserves their source evidence and types only what is repeatedly needed to understand, decide and act.":
    "Reality no es otro ERP. Recibe eventos operativos seleccionados, preserva su evidencia de origen y solo lo que se necesita repetidamente para comprender, decidir y actuar.",
  "Reality is observing your business": "Reality está observando su negocio",
  "Reality links": "Realidad vincula",
  "Reality separates original data, evidence, operational truth and the ledger — while keeping their lineage verifiable through the shortest true links.":
    "Reality separa los datos originales, la evidencia, la verdad operativa y el registro — mientras mantiene su genealogía verificable a través de los enlaces más cortos y verdaderos.",
  "Reality stores before it interprets. The shortest true links keep every operational conclusion explainable.":
    "Reality almacena antes de interpretar. Los enlaces más cortos y verdaderos mantienen todas las conclusiones operativas explicables.",
  "Reality target": "Objetivo de Reality",
  "Reality watches before agents touch the business.":
    "Reality observa antes de que los agentes toquen el negocio.",
  "Reality will execute exactly this action through the shared application service and record its result.":
    "Reality ejecutará exactamente esta acción a través del servicio de aplicación compartido y registrará su resultado.",
  Rebuildable: "Reconstruible",
  Receivables: "Cuentas por cobrar",
  "Receivables & payables": "Cuentas por cobrar y cuentas por pagar",
  "Receivables and payables derived from postings, credits and settlement allocations.":
    "Cuentas por cobrar y cuentas por pagar derivadas de las escrituras, créditos y asignaciones de liquidación.",
  Received: "Recibido",
  "Recent runs": "Ejecuciones recientes",
  "Recent source records": "Registros de origen recientes",
  Recommend: "Recomendar",
  "Record & enqueue": "Registrar y encolar",
  "Record movement": "Registrar movimiento",
  Recorded: "Registrado",
  "Recording…": "Grabando…",
  "Recurring gap before the next receipt": "Brecha recurrente antes del próximo recibo",
  Reference: "Referencia",
  "Register an external origin and choose exactly which record types Reality may receive.":
    "Registrar un origen externo y elegir exactamente qué tipos de registros Reality puede recibir.",
  Registers: "Registros",
  Reject: "Rechazar",
  "Reject this action?": "¿Rechazar esta acción?",
  "Remove line": "Eliminar línea",
  "Requested delivery": "Entrega solicitada",
  "Reserve an open outgoing Commitment when stock becomes available.":
    "Reservar un compromiso de salida abierto cuando el stock esté disponible.",
  "Reserve stock": "Reservar stock",
  "Reserved at": "Reservado en",
  "Resolve delivery holds": "Resolver problemas de entrega",
  "Restore company": "Restaurar empresa",
  "Reusable customer or supplier pricing assignments.":
    "Asignaciones de precios reutilizables para clientes o proveedores.",
  "Reusable rules for calculating invoice due dates.":
    "Reglas reutilizables para calcular las fechas de vencimiento de la factura.",
  "Review all": "Revisar todo",
  "Review business events, processing activity and exceptions over time.":
    "Revisar eventos comerciales, actividad de procesamiento y excepciones a lo largo del tiempo.",
  "Review Business Events, processing history and exceptions.":
    "Revisar historial de eventos comerciales, actividad de procesamiento y excepciones.",
  "Review derived operational risks. They disappear when Reality is corrected.":
    "Revisar riesgos operativos derivados. Desaparecen cuando la Realidad se corrige.",
  "Review exceptions, commitments and current inventory.":
    "Revisar excepciones, compromisos e inventario actual.",
  "Review observed facts": "Revisar hechos observados",
  "Review pending": "Revisar pendiente",
  Revoke: "Revocar",
  "Run daily operations": "Ejecutar operaciones diarias",
  "Runs appear after SourceRecords enter through an integration or test intake.":
    "Los registros aparecen después de que los SourceRecords ingresen a través de una integración o admisión de pruebas.",
  "Sales channel": "Canal de ventas",
  "Sales invoice": "Factura de ventas",
  "Sales order": "Pedido de ventas",
  "Save changes": "Guardar cambios",
  "Save details": "Guardar detalles",
  "Save settings": "Guardar configuraciones",
  Saved: "Guardado",
  Scope: "Alcance",
  "Search a different business identity or clear the query.":
    "Busque una identidad comercial diferente o limpie la consulta.",
  "Search any ID and follow Source → Evidence → Reality.":
    "Busque cualquier ID y siga Source → Evidence → Reality.",
  "Search currencies…": "Busque monedas…",
  "Search document, party or source…": "Busque documento, parte o fuente…",
  "Search exceptions…": "Busque excepciones…",
  "Search ID, order number, SKU, party or source reference…":
    "Busque ID, número de pedido, SKU, referencia de parte o fuente…",
  "Search IDs and inspect connected Reality, Evidence and Source records.":
    "Busque IDs e inspeccione los registros de Reality, Evidence y Source conectados.",
  "Search invoice, party or ID…": "Busque factura, parte o ID…",
  "Search item or SKU…": "Busque artículo o SKU…",
  "Search or enter source system…": "Busque o ingrese el sistema de origen…",
  "Search or enter source type…": "Busque o ingrese el tipo de origen…",
  "Search order, source, SKU, party or ID…": "Busque pedido, origen, SKU, parte o ID…",
  "Search party, item or ID…": "Busque parte, artículo o ID…",
  "Search party…": "Busque parte…",
  "Search payment term…": "Busque plazo de pago…",
  "Search payment terms…": "Busque plazos de pago…",
  "Search records, browse collections and inspect one object without losing context.":
    "Busque registros, explore colecciones e inspeccione un objeto sin perder el contexto.",
  "Search reference, party or posting…": "Buscar referencia, parte o publicación…",
  "Search ship-to party…": "Buscar destinatario…",
  "Search SKU or item…": "Buscar SKU o artículo…",
  "Search source systems…": "Buscar sistemas de origen…",
  "Search tools…": "Buscar herramientas…",
  "See the operating model": "Ver el modelo operativo",
  "See what is true, what needs attention and what can be delegated next.":
    "Ver qué es cierto, qué necesita atención y qué se puede delegar.",
  "Select a system…": "Seleccionar un sistema…",
  "Select exactly which upstream records Reality may receive.":
    "Seleccionar exactamente qué registros de upstream puede recibir Reality.",
  "Select only the upstream types this instance is responsible for.":
    "Seleccionar solo los tipos de upstream para los que esta instancia es responsable.",
  "Select volume": "Seleccionar volumen",
  "Selected operational signals only": "Señales operativas seleccionadas únicamente",
  "Selected payload · retained losslessly": "Carga seleccionada · retenida sin pérdida",
  "Selected payloads flow from existing systems into Reality":
    "Las cargas seleccionadas fluyen de los sistemas existentes a Reality",
  Send: "Enviar",
  Settled: "Resuelto",
  "Shared application service": "Servicio de aplicación compartido",
  "shared application tools. Mutations still require the Reality approval boundary.":
    "herramientas de aplicación compartidas. Las mutaciones aún requieren el límite de aprobación de Reality.",
  "Ship-to party": "Destinatario",
  Shipped: "Enviado",
  "Shipping readiness": "Listo para enviar",
  Shortage: "Escasez",
  "Shown throughout Reality.": "Mostrado en Reality.",
  "Shown to other operators in decisions and activity.":
    "Mostrado a otros operadores en decisiones y actividades.",
  "Sign in": "Iniciar sesión",
  "So agents can operate your business with confidence.":
    "Para que los agentes puedan operar su negocio con confianza.",
  Source: "Fuente",
  "Source → Evidence → Reality": "Fuente → Evidencia → Realidad",
  "Source capabilities": "Capacidades de la fuente",
  "Source definition": "Definición de la fuente",
  "Source record": "Registro de la fuente",
  "Source registry": "Registro de fuentes",
  "Source system": "Sistema de fuentes",
  "Source systems": "Sistemas de fuentes",
  "Source systems remain authoritative": "Los sistemas de fuentes siguen siendo autoritarios",
  "Source templates available in Reality today. Transport and credentials remain explicit per connector.":
    "Plantillas de fuentes disponibles en la Realidad hoy en día. El transporte y las credenciales siguen siendo explícitos según el conector.",
  "Source type": "Tipo de fuente",
  "Payload value path": "Ruta del valor en el payload",
  "Fact predicate": "Predicado del Fact",
  "Fact value type": "Tipo de valor del Fact",
  "Allowed values, comma separated": "Valores permitidos, separados por comas",
  String: "Texto",
  Enum: "Lista de opciones",
  Boolean: "Sí/no",
  Decimal: "Número decimal",
  Integer: "Número entero",
  "Sources & evidence": "Fuentes y evidencia",
  "Sources & imports": "Fuentes e importaciones",
  "Stable code": "Código estable",
  "Stable tenant identity for API calls.": "Identidad de inquilino estable para llamadas a la API.",
  "Stable within this company, for example shopify_de.":
    "Estable dentro de esta empresa, por ejemplo shopify_de.",
  "Stage 1": "Fase 1",
  "Start in observation mode": "Comenzar en modo de observación",
  "Start with an operational record, then follow its shortest true links through Evidence to the original SourceRecord.":
    "Comenzar con un registro operativo, luego seguir sus enlaces verdaderos más cortos a través de la Evidencia hasta el registro de Fuente original.",
  "Start with observation": "Comenzar con la observación",
  "Start with Reality": "Comenzar con la Realidad",
  "Start with the operational view. Use traceability only when you need the complete explanation.":
    "Comenzar con la vista operativa. Use la trazabilidad solo cuando necesite la explicación completa.",
  "Stay in control.": "Mantenga el control.",
  "Still observe only": "Sigue observando solo",
  "Stock · data quality · execution hold":
    "Inventario · calidad de los datos · ejecución en espera",
  "Stock enabled": "Inventario habilitado",
  "Supplier invoice": "Factura del proveedor",
  "Supplier reliability": "Fiabilidad del proveedor",
  "Supports traceable and verifiable ERP processes aligned with GoBD principles. Actual compliance also depends on operations, internal controls, retention and process documentation.":
    "Soporta procesos ERP rastreables y verificables alineados con los principios de GoBD. El cumplimiento real también depende de las operaciones, los controles internos, la retención y la documentación de los procesos.",
  "Switch company": "Cambiar empresa",
  System: "Sistema",
  "System template": "Plantilla de sistema",
  "Systeme bleiben führend": "Los sistemas siguen siendo autoritarios",
  "Systems remain authoritative": "Los sistemas siguen siendo autoritarios",
  "Tax identifier": "Identificador fiscal",
  "Tell us where you want to use Reality. You’ll receive access after a personal review.":
    "Díganos dónde desea utilizar Reality. Recibirá acceso después de una revisión personal.",
  "Test intake": "Entrada de prueba",
  "The complete path remains traceable to the immutable shop payload.":
    "La ruta completa sigue siendo rastreable al pago del almacén inmutable.",
  "The first verified accounts are admitted automatically. After that, applications wait for your decision.":
    "Las primeras cuentas verificadas se admiten automáticamente. Después, las solicitudes esperan su decisión.",
  "The Operations Cockpit turns connected records into a daily control surface — exceptions first, evidence one step away, agent responsibility always visible.":
    "El panel de control de operaciones convierte los registros conectados en una superficie de control diaria: primero las excepciones, la evidencia a un paso de distancia, la responsabilidad del agente siempre visible.",
  "The physical journal starts with the first receipt or opening stock.":
    "El registro físico comienza con la primera recepción o inventario inicial.",
  "The selected upstream payload, retained losslessly and versioned.":
    "El conjunto de datos upstream seleccionado, retenido sin pérdida y versionado.",
  "These could be your operational numbers": "Estos podrían ser sus números operativos",
  "These preferences apply only to your account, across every company you can access.":
    "Estas preferencias solo se aplican a su cuenta, en todas las empresas a las que pueda acceder.",
  "This collection has no matching records.":
    "Este conjunto de datos no tiene registros coincidentes.",
  "This creates a definition only. It does not connect to the external system or store credentials.":
    "Esto crea solo una definición. No se conecta al sistema externo ni almacena credenciales.",
  "This permanently deletes": "Esto elimina permanentemente",
  "This removes the company and every Source, Evidence, Reality, journal, integration and conversation belonging to it.":
    "Esto elimina a la empresa y todos los Source, Evidence, Reality, diarios, integraciones y conversaciones que pertenecen a ella.",
  "Thousands of events become a small number of clear exceptions that need attention.":
    "Miles de eventos se convierten en un pequeño número de excepciones claras que necesitan atención.",
  "Tied-up business": "Negocio bloqueado",
  Timezone: "Zona horaria",
  To: "Para",
  "Token name, e.g. Claude": "Nombre de token, p. ej. Claude",
  "Tokens are scoped to this company. Reads use shared application tools; mutations still need an approval.":
    "Los tokens están restringidos a esta empresa. Las lecturas usan herramientas de aplicación compartidas; las mutaciones siguen necesitando una aprobación.",
  Tool: "Herramienta",
  "Tool catalog": "Catálogo de herramientas",
  "total runs": "Ejecuciones totales",
  "Trace an answer": "Rastrear una respuesta",
  "Traceability / timeline": "Rastreo / cronología",
  "TRUST INCREASES": "LA CONFIANZA AUMENTA",
  "Typed only when operationally useful": "Solo se tipifica cuando es útil operativamente",
  "Typical operating pattern": "Patrón operativo típico",
  Unallocated: "No asignado",
  "Under 1,000": "Menos de 1.000",
  UNDERSTAND: "ENTENDER",
  Unit: "Unidad",
  "Unit price": "Precio por unidad",
  "Unit…": "Unidad…",
  "Upstream vocabulary remains distinct from operational Reality.":
    "El vocabulario de upstream permanece distinto de la realidad operativa.",
  "Use a name operators recognize.": "Utilice un nombre que los operadores reconozcan.",
  "Use a wider time range or remove a filter.":
    "Utilice un rango de tiempo más amplio o elimine un filtro.",
  "Use source templates for modern commerce systems, immutable API intake, or controlled CSV and JSON imports. Each origin declares exactly which records Reality may receive.":
    "Utilice plantillas de origen para sistemas de comercio modernos, entrada de API inmutable o importaciones controladas de CSV y JSON. Cada origen declara exactamente qué registros de Reality puede recibir.",
  "Use Test intake or connect a source to record the first immutable payload.":
    "Utilice la entrada de prueba o conecte un origen para registrar el primer payload inmutable.",
  "Use this URL in your MCP client.": "Utilice esta URL en su cliente MCP.",
  "Used when a source does not supply one.": "Se utiliza cuando un origen no proporciona uno.",
  "Used when new operational records are created.":
    "Se utiliza cuando se crean nuevos registros operativos.",
  "Verification code": "Código de verificación",
  "Verify email": "Verificar correo electrónico",
  "Verify Reality's interpretation against immutable source evidence.":
    "Verificar la interpretación de Reality frente a la evidencia de origen inmutable.",
  Version: "Versión",
  View: "Ver",
  "Warehouse / allocation": "Almacén / asignación",
  "Warehouse / physical journal": "Almacén / diario físico",
  "Warehouse / stock control": "Almacén / control de inventario",
  "Warehouses and stock locations": "Almacenes y ubicaciones de inventario",
  "We will email you when your workspace is unlocked.":
    "Le enviaremos un correo electrónico cuando su espacio de trabajo esté desbloqueado.",
  "Welcome back": "Bienvenido de nuevo",
  "What an order, invoice, payment or file actually asserted.":
    "Qué afirma un pedido, factura, pago o archivo.",
  "What can be decided": "Qué se puede decidir",
  "What conflicts?": "¿Qué conflictos?",
  "What evidence proves it?": "¿Qué evidencia lo prueba?",
  "What external origin does this represent?": "¿Qué origen externo representa esto?",
  "What happened?": "¿Qué sucedió?",
  "What is true": "¿Qué es verdad?",
  "What needs attention": "Qué necesita atención",
  "What Reality could reveal next": "Qué podría revelar Reality a continuación",
  "Work email": "Correo electrónico",
  "Working…": "Trabajando…",
  Workspace: "Espacio de trabajo",
  "Workspace / companies": "Espacio de trabajo / empresas",
  "Workspace setup": "Configuración del espacio de trabajo",
  Yes: "Sí",
  "You’re on the list": "Estás en la lista",
  "Your existing systems remain in place. Reality receives only the operational records you explicitly accept.":
    "Tus sistemas existentes permanecen en su lugar. Reality solo recibe los registros operativos que aceptas explícitamente.",
  "Your name": "Tu nombre",
  "Your profile": "Tu perfil",
  "Your sign-in identity.": "Tu identidad de inicio de sesión.",
  "Your systems stay in place. Nothing changes automatically.":
    "Tus sistemas permanecen en su lugar. Nada cambia automáticamente.",
  General: "General",
});

Object.assign(dictionaries.nl, {
  "Agents & AI": "Agenten & AI",
  "Audit Trail": "Audittrail",
  Commerce: "Handel",
  "Data / explorer": "Gegevens / verkenner",
  "Data / immutable intake": "Gegevens / onveranderlijke invoer",
  Input: "Invoer",
  "Open backlog": "Openstaande achterstand",
  "Open Explorer": "Verkenner openen",
  "Open Home": "Start openen",
  "Open Items": "Openstaande posten",
  "PostgreSQL fact journal · Append-only records · S3-compatible object store · Projections · Backups / PITR":
    "PostgreSQL-feitenjournaal · Alleen-toevoegen-records · S3-compatibele objectopslag · Projecties · Back-ups / PITR",
  "Reality links": "Reality-koppelingen",
  Scope: "Bereik",
  Tool: "Hulpmiddel",
});

Object.assign(dictionaries.de, {
  "Evidence, permissions and confirmation remain part of every step.":
    "Evidence, Berechtigungen und Bestätigungen sind Teil jedes Schritts.",
  "Facts · Commitments · Reservations · Movements · Lots · Serials · SSCC":
    "Fakten · Commitments · Reservations · Movements · Mengen · Serien · SSCC",
  "Operational Reality": "Operative Reality",
  "Orders, stock, payments and promises are observed together. Reality exposes contradictions, business impact and the source evidence behind every conclusion.":
    "Bestellungen, Lagerbestände, Zahlungen und Zusagen werden zusammen betrachtet. Reality deckt Widersprüche, Geschäftsauswirkungen und die Quelle der Beweise hinter jeder Schlussfolgerung auf.",
  "Reality · Autonomous commerce core": "Reality · Kern der autonomen E-Commerce",
  "Reality connects operational data into an explainable business reality — a trusted foundation for decisions and step-by-step autonomy.":
    "Reality verbindet operative Daten in eine verständliche Geschäftswirklichkeit – eine vertrauenswürdige Grundlage für Entscheidungen und schrittweise Autonomie.",
  "Reality home": "Reality Startseite",
  "Reality is not another ERP. It receives selected operational events, preserves their source evidence and types only what is repeatedly needed to understand, decide and act.":
    "Reality ist kein weiteres ERP. Es empfängt ausgewählte operative Ereignisse, bewahrt ihre Quelle und speichert nur das, was wiederholt benötigt wird, um zu verstehen, zu entscheiden und zu handeln.",
  "Reality separates original data, evidence, operational truth and the ledger — while keeping their lineage verifiable through the shortest true links.":
    "Reality trennt ursprüngliche Daten, Beweise, operative Wahrheit und das Hauptbuch – während es ihre Herkunft durch die kürzesten, wahren Verbindungen verifizierbar hält.",
  "Reality stores before it interprets. The shortest true links keep every operational conclusion explainable.":
    "Reality speichert, bevor es interpretiert. Die kürzesten, wahren Verbindungen halten jede operative Schlussfolgerung verständlich.",
  "Reality watches before agents touch the business.":
    "Reality beobachtet, bevor Agenten die Geschäftstätigkeit ausführen.",
  "Reality will execute exactly this action through the shared application service and record its result.":
    "Reality führt genau diese Aktion über den gemeinsamen Anwendungsservice aus und protokolliert das Ergebnis.",
});

Object.assign(dictionaries.nl, {
  "Active allocations linked directly to their customer Commitments.":
    "Actieve toewijzingen zijn direct gekoppeld aan hun klant Commitments.",
  "Evidence / document register": "Evidence / document register",
  "Evidence, permissions and confirmation remain part of every step.":
    "Evidence, rechten en bevestiging blijven onderdeel van elke stap.",
  "Explain the current Reality": "Leg de huidige Reality uit",
  "Explicit, source-supported observations currently retained by Reality. Facts never replace their immutable source.":
    "Expliciete, bronondersteunde observaties worden momenteel bewaard door Reality. Feiten vervangen nooit hun onveranderlijke bron.",
  "Facts · Commitments · Reservations · Movements · Lots · Serials · SSCC":
    "Feiten · Commitments · Reservations · Movements · Lots · Serien · SSCC",
  "First verify that Reality understands your business. Nothing is changed automatically.":
    "Verifieer eerst dat Reality uw bedrijf begrijpt. Er worden niets automatisch gewijzigd.",
  "Follow Reality through Evidence to its original SourceRecord.":
    "Volg Reality via Evidence naar zijn oorspronkelijke SourceRecord.",
  "Open Evidence": "Open Evidence",
  "Opening Reality": "Openen van Reality",
  "Operational Reality": "Operationele Reality",
  "Read-only answers are immediate. Any change to business Reality waits for an approval until a person confirms it.":
    "Alleen-lezen antwoorden zijn onmiddellijk. Elke wijziging aan de zakelijke Reality wacht op een goedkeuring totdat iemand het bevestigt.",
  "Reality · Autonomous commerce core": "Reality · Kern van autonome handel",
  "Reality connects operational data into an explainable business reality — a trusted foundation for decisions and step-by-step autonomy.":
    "Reality verbindt operationele gegevens met een begrijpelijke zakelijke realiteit — een betrouwbare basis voor beslissingen en stap voor stap autonomie.",
  "Reality Explorer": "Reality Explorer",
  "Reality found no current operational contradiction or uncovered promise.":
    "Reality vond geen huidige operationele tegenstrijdigheid of onontdekte belofte.",
  "Reality home": "Reality huis",
  "Reality inspector": "Reality inspecteur",
  "Review derived operational risks. They disappear when Reality is corrected.":
    "Beoordeel afgeleide operationele risico's. Ze verdwijnen wanneer Reality wordt gecorrigeerd.",
  "Source → Evidence → Reality": "Bron → Evidence → Reality",
  "Source templates available in Reality today. Transport and credentials remain explicit per connector.":
    "Bron templates beschikbaar in Reality vandaag. Transport en credentials blijven expliciet per connector.",
  "Start with an operational record, then follow its shortest true links through Evidence to the original SourceRecord.":
    "Begin met een operationeel record, en volg vervolgens de kortste, correcte links door Evidence naar de oorspronkelijke SourceRecord.",
  "Start with Reality": "Begin met Reality",
  "This removes the company and every Source, Evidence, Reality, journal, integration and conversation belonging to it.":
    "Dit verwijdert het bedrijf en alle bronnen, Evidence, Reality, dagboek, integratie en gesprek die eraan verbonden zijn.",
  "Upstream vocabulary remains distinct from operational Reality.":
    "De upstream vocabulaire blijft gescheiden van de operationele Reality.",
});

Object.assign(dictionaries.es, {
  "A paid order is blocked despite available inventory. Reality connects the payment, commitment, reservation and delivery hold — then proposes the exact resolution with its evidence.":
    "Un pedido pagado está bloqueado a pesar de la disponibilidad de inventario. Reality conecta el pago, el compromiso, la reserva y la entrega — y luego propone la solución exacta con sus pruebas.",
  "Active allocations linked directly to their customer Commitments.":
    "Asignaciones activas vinculadas directamente a su cliente Commitments.",
  "Evidence / document register": "Evidence / registro de documentos",
  "Evidence, permissions and confirmation remain part of every step.":
    "Evidence, los permisos y la confirmación siguen siendo parte de cada paso.",
  "Explain the current Reality": "Explique el Reality actual",
  "Explicit, source-supported observations currently retained by Reality. Facts never replace their immutable source.":
    "Observaciones explícitas y basadas en la fuente, actualmente retenidas por Reality. Los hechos nunca reemplazan su fuente inmutable.",
  "Facts · Commitments · Reservations · Movements · Lots · Serials · SSCC":
    "Hechos · Commitments · Reservations · Movements · Lotes · Números de serie · SSCC",
  "First verify that Reality understands your business. Nothing is changed automatically.":
    "Primero, verifique que Reality comprenda su negocio. Nada se cambia automáticamente.",
  "Follow Reality through Evidence to its original SourceRecord.":
    "Siga a Reality a través de Evidence hasta su origen SourceRecord.",
  "Immutable SourceRecords · Versioned payloads · Documents · Document lines":
    "SourceRecords inmutable · Cargas versionadas · Documentos · Líneas de documentos",
  "Inspect normalized documents and their links into operational Reality.":
    "Inspeccione los documentos normalizados y sus enlaces a Reality operativo.",
  "Let Reality surface contradictions and explain their business impact.":
    "Permita que Reality revele contradicciones y explique su impacto comercial.",
  "Maintain only the operational references and normalized evidence Reality needs. Complete ERP records remain in their source systems.":
    "Mantenga solo las referencias y la evidencia normalizada que Reality necesita. Los registros ERP completos permanecen en sus sistemas de origen.",
  "Manage the typed identities and commercial rules Reality repeatedly uses.":
    "Administre las identidades y las reglas comerciales que Reality utiliza repetidamente.",
  "Manage your personal identity and how Reality displays dates, times and numbers.":
    "Administre su identidad personal y cómo Reality muestra fechas, horas y números.",
  "New to Reality?": "¿Nuevo en Reality?",
  "Open Evidence": "Abrir Evidence",
  "Opening Reality": "Abrir Reality",
  "Operational Reality": "Operacional Reality",
  "Orders, stock, payments and promises are observed together. Reality exposes contradictions, business impact and the source evidence behind every conclusion.":
    "Los pedidos, el inventario, los pagos y las promesas se observan juntos. Reality expone contradicciones, el impacto empresarial y la evidencia de origen detrás de cada conclusión.",
  "Read-only answers are immediate. Any change to business Reality waits for an approval until a person confirms it.":
    "Las respuestas de solo lectura son inmediatas. Cualquier cambio en el Reality del negocio espera una aprobación hasta que una persona lo confirme.",
  "Reality · Autonomous commerce core": "Reality · Núcleo de comercio autónomo",
  "Reality connects operational data into an explainable business reality — a trusted foundation for decisions and step-by-step autonomy.":
    "Reality conecta los datos operativos en una realidad empresarial explicable — una base de confianza para las decisiones y la autonomía paso a paso.",
  "Reality Explorer": "Explorador Reality",
  "Reality found no current operational contradiction or uncovered promise.":
    "Reality no encontró ninguna contradicción operativa actual ni promesa descubierta.",
  "Reality home": "Inicio de Reality",
  "Reality inspector": "Inspector de Reality",
  "Reality links": "Reality conecta",
  "Reserve an open outgoing Commitment when stock becomes available.":
    "Reserve un Commitment saliente abierto cuando el inventario esté disponible.",
  "Review derived operational risks. They disappear when Reality is corrected.":
    "Revise los riesgos operativos derivados. Desaparecen cuando Reality se corrige.",
  "Source → Evidence → Reality": "Origen → Evidence → Reality",
  "Source templates available in Reality today. Transport and credentials remain explicit per connector.":
    "Plantillas de origen disponibles en Reality hoy. El transporte y las credenciales permanecen explícitos según el conector.",
  "Start with an operational record, then follow its shortest true links through Evidence to the original SourceRecord.":
    "Comience con un registro operativo, luego siga sus enlaces verdaderos más cortos a través de Evidence hasta el SourceRecord original.",
  "Start with Reality": "Comience con Reality",
  "Upstream vocabulary remains distinct from operational Reality.":
    "El vocabulario ascendente permanece distinto del registro operativo Reality.",
});

Object.assign(dictionaries.nl, {
  "Evidence / document register": "Evidence / documentenregister",
  "Open Evidence": "Evidence openen",
  "Reality Explorer": "Reality-verkenner",
});

Object.assign(dictionaries.de, {
  Correct: "Korrigieren",
  "Correct movement": "Bewegung korrigieren",
  "Immutable physical journal": "Unveränderliches physisches Journal",
  "The original stays unchanged. Reality records an exact inverse and an optional replacement.":
    "Das Original bleibt unverändert. Reality erfasst eine exakte Gegenbewegung und optional einen Ersatz.",
  "Correction reason": "Korrekturgrund",
  "Record the intended replacement": "Die beabsichtigte Ersatzbewegung erfassen",
  "From location": "Von Lagerort",
  "To location": "Zu Lagerort",
  "Correction preview": "Korrekturvorschau",
  "Original:": "Ursprung:",
  "Compensation: correction ·": "Gegenbewegung: Korrektur ·",
  "Resulting net quantity:": "Resultierende Nettomenge:",
  "Preview correction": "Korrektur prüfen",
  "Confirm correction": "Korrektur bestätigen",
});

Object.assign(dictionaries.nl, {
  Correct: "Corrigeren",
  "Correct movement": "Beweging corrigeren",
  "Immutable physical journal": "Onveranderlijk fysiek journaal",
  "The original stays unchanged. Reality records an exact inverse and an optional replacement.":
    "Het origineel blijft ongewijzigd. Reality registreert een exacte tegenbeweging en een optionele vervanging.",
  "Correction reason": "Correctiereden",
  "Record the intended replacement": "De bedoelde vervangende beweging registreren",
  "From location": "Van locatie",
  "To location": "Naar locatie",
  "Correction preview": "Correctievoorbeeld",
  "Original:": "Origineel:",
  "Compensation: correction ·": "Tegenbeweging: correctie ·",
  "Resulting net quantity:": "Resulterende nettohoeveelheid:",
  "Preview correction": "Correctie bekijken",
  "Confirm correction": "Correctie bevestigen",
});

Object.assign(dictionaries.es, {
  Correct: "Corregir",
  "Correct movement": "Corregir movimiento",
  "Immutable physical journal": "Diario físico inmutable",
  "The original stays unchanged. Reality records an exact inverse and an optional replacement.":
    "El original permanece sin cambios. Reality registra una contrapartida exacta y un reemplazo opcional.",
  "Correction reason": "Motivo de la corrección",
  "Record the intended replacement": "Registrar el movimiento de reemplazo previsto",
  "From location": "Desde ubicación",
  "To location": "Hacia ubicación",
  "Correction preview": "Vista previa de la corrección",
  "Original:": "Movimiento original:",
  "Compensation: correction ·": "Contrapartida: corrección ·",
  "Resulting net quantity:": "Cantidad neta resultante:",
  "Preview correction": "Previsualizar corrección",
  "Confirm correction": "Confirmar corrección",
});

Object.assign(dictionaries.de, {
  Reverse: "Stornieren",
  "Reverse posting group": "Buchungsgruppe stornieren",
  "Immutable financial journal": "Unveränderliches Finanzjournal",
  "The original remains unchanged. Reality appends one exact inverse group.":
    "Das Original bleibt unverändert. Reality fügt eine exakt inverse Buchungsgruppe hinzu.",
  "Reversal reason": "Stornierungsgrund",
  "Reversal preview": "Stornierungsvorschau",
  "Original entries:": "Ursprüngliche Buchungen:",
  "Inverse entries:": "Inverse Buchungen:",
  "Affected allocations:": "Betroffene Zuordnungen:",
  "Preview reversal": "Stornierung prüfen",
  "Confirm reversal": "Stornierung bestätigen",
});

Object.assign(dictionaries.nl, {
  Reverse: "Terugdraaien",
  "Reverse posting group": "Boekingsgroep terugdraaien",
  "Immutable financial journal": "Onveranderlijk financieel journaal",
  "The original remains unchanged. Reality appends one exact inverse group.":
    "Het origineel blijft ongewijzigd. Reality voegt één exact tegengestelde boekingsgroep toe.",
  "Reversal reason": "Reden voor terugdraaiing",
  "Reversal preview": "Voorbeeld van terugdraaiing",
  "Original entries:": "Oorspronkelijke boekingen:",
  "Inverse entries:": "Tegenboekingen:",
  "Affected allocations:": "Betrokken toewijzingen:",
  "Preview reversal": "Terugdraaiing bekijken",
  "Confirm reversal": "Terugdraaiing bevestigen",
});

Object.assign(dictionaries.es, {
  Reverse: "Revertir",
  "Reverse posting group": "Revertir grupo de asientos",
  "Immutable financial journal": "Diario financiero inmutable",
  "The original remains unchanged. Reality appends one exact inverse group.":
    "El original permanece sin cambios. Reality añade un grupo inverso exacto.",
  "Reversal reason": "Motivo de la reversión",
  "Reversal preview": "Vista previa de la reversión",
  "Original entries:": "Asientos originales:",
  "Inverse entries:": "Asientos inversos:",
  "Affected allocations:": "Asignaciones afectadas:",
  "Preview reversal": "Previsualizar reversión",
  "Confirm reversal": "Confirmar reversión",
});

Object.assign(dictionaries.de, {
  Journal: "Hauptbuch",
  "Finance / ledger": "Finanzen / Hauptbuch",
  "Balanced ledger entries with direct drilldown to their evidence and posting context.":
    "Ausgeglichene Buchungen mit direktem Zugriff auf Evidence und Buchungskontext.",
  "Search account, posting or evidence…": "Konto, Buchung oder Evidence suchen…",
  "From date": "Von Datum",
  "To date": "Bis Datum",
  Side: "Seite",
  "No journal entries match": "Keine passenden Hauptbuchbuchungen",
  "Change the account, date or search filters.": "Konto, Datum oder Suchfilter ändern.",
});

Object.assign(dictionaries.nl, {
  Journal: "Grootboek",
  "Finance / ledger": "Financiën / grootboek",
  "Balanced ledger entries with direct drilldown to their evidence and posting context.":
    "Gebalanceerde boekingen met directe toegang tot bewijs en boekingscontext.",
  "Search account, posting or evidence…": "Rekening, boeking of bewijs zoeken…",
  "From date": "Vanaf datum",
  "To date": "Tot datum",
  Side: "Zijde",
  "No journal entries match": "Geen passende grootboekboekingen",
  "Change the account, date or search filters.": "Wijzig de rekening, datum of zoekfilters.",
});

Object.assign(dictionaries.es, {
  Journal: "Libro mayor",
  "Finance / ledger": "Finanzas / libro mayor",
  "Balanced ledger entries with direct drilldown to their evidence and posting context.":
    "Asientos equilibrados con acceso directo a su evidencia y contexto contable.",
  "Search account, posting or evidence…": "Buscar cuenta, asiento o evidencia…",
  "From date": "Desde la fecha",
  "To date": "Hasta la fecha",
  Side: "Lado",
  "No journal entries match": "No hay asientos coincidentes",
  "Change the account, date or search filters.":
    "Cambie la cuenta, la fecha o los filtros de búsqueda.",
});

Object.assign(dictionaries.de, {
  Requires: "Benötigt",
  "Appends one idempotent source-supported observation about an existing tenant-scoped subject after confirmation without copying typed operational state.":
    "Erfasst nach Bestätigung eine idempotente, quellengestützte Beobachtung zu einem bestehenden unternehmensbezogenen Objekt, ohne typisierten operativen Zustand zu kopieren.",
  "Atomically records lossless manual Source evidence, typed order Evidence, and the derived outgoing or incoming Commitments without storing operational status on the Document.":
    "Erfasst atomar verlustfreie manuelle Quelldaten, typisierte Auftrags-Evidence und die abgeleiteten ausgehenden oder eingehenden Commitments, ohne operativen Status am Dokument zu speichern.",
  "Records payment evidence, posts balanced ledger entries, and allocates the payment to an invoice.":
    "Erfasst einen Zahlungsbeleg, bucht ausgeglichene Hauptbucheinträge und ordnet die Zahlung einer Rechnung zu.",
  "Records an outgoing payment and explicitly settles a supplier invoice entry.":
    "Erfasst eine ausgehende Zahlung und gleicht einen Lieferantenrechnungsposten ausdrücklich aus.",
  "Allocates available stock to one commitment, optionally by pallet, lot, or exact serial unit, and reports any shortage.":
    "Ordnet verfügbaren Bestand einem Commitment zu, optional nach Palette, Charge oder exakter Seriennummer, und meldet eine Fehlmenge.",
  "Records an immutable physical event with the same optional pallet, lot, and serial identity used by reservations.":
    "Erfasst ein unveränderliches physisches Ereignis mit denselben optionalen Paletten-, Chargen- und Serienidentitäten wie Reservierungen.",
  "Preserves an immutable original, appends one exact correction and optional replacement, and derives the auditable net physical effect.":
    "Bewahrt das unveränderliche Original, ergänzt eine exakte Korrektur mit optionalem Ersatz und leitet den prüfbaren physischen Nettoeffekt ab.",
  "Prevents execution without changing or deleting the underlying obligation.":
    "Verhindert die Ausführung, ohne die zugrunde liegende Verpflichtung zu ändern oder zu löschen.",
  "Places individual holds on the open commitments evidenced by a document.":
    "Setzt einzelne Sperren auf die offenen Commitments, die durch ein Dokument belegt sind.",
  "Blocks customer shipment execution while orders and reservations remain possible.":
    "Blockiert die Ausführung von Kundenlieferungen, während Aufträge und Reservierungen weiterhin möglich bleiben.",
  "Records an optional tenant-scoped pallet identity with an optional NVE/SSCC and immutable source evidence.":
    "Erfasst eine optionale unternehmensbezogene Palettenidentität mit optionaler NVE/SSCC und unveränderlicher Quellen-Evidence.",
  "Creates a tenant-scoped batch identity for a lot- or serial-tracked item without storing a stock balance.":
    "Erstellt eine unternehmensbezogene Chargenidentität für einen chargen- oder seriengeführten Artikel, ohne einen Bestandswert zu speichern.",
  "Creates the identity of one serialized unit, optionally linked to its lot, without storing its location or status.":
    "Erstellt die Identität einer serialisierten Einheit, optional mit ihrer Charge verknüpft, ohne Standort oder Status zu speichern.",
});

Object.assign(dictionaries.nl, {
  Requires: "Vereist",
  "Appends one idempotent source-supported observation about an existing tenant-scoped subject after confirmation without copying typed operational state.":
    "Legt na bevestiging één idempotente, bronondersteunde waarneming vast over een bestaand bedrijfsgebonden onderwerp, zonder getypeerde operationele toestand te kopiëren.",
  "Atomically records lossless manual Source evidence, typed order Evidence, and the derived outgoing or incoming Commitments without storing operational status on the Document.":
    "Legt atomair verliesvrije handmatige brongegevens, getypeerd orderbewijs en de afgeleide uitgaande of inkomende Commitments vast zonder operationele status op het document op te slaan.",
  "Records payment evidence, posts balanced ledger entries, and allocates the payment to an invoice.":
    "Legt betalingsbewijs vast, boekt gebalanceerde grootboekregels en wijst de betaling toe aan een factuur.",
  "Records an outgoing payment and explicitly settles a supplier invoice entry.":
    "Legt een uitgaande betaling vast en vereffent expliciet een leveranciersfactuurpost.",
  "Allocates available stock to one commitment, optionally by pallet, lot, or exact serial unit, and reports any shortage.":
    "Wijst beschikbare voorraad toe aan één Commitment, optioneel per pallet, partij of exacte seriële eenheid, en meldt elk tekort.",
  "Records an immutable physical event with the same optional pallet, lot, and serial identity used by reservations.":
    "Legt een onveranderlijke fysieke gebeurtenis vast met dezelfde optionele pallet-, partij- en serienummeridentiteit als reserveringen.",
  "Preserves an immutable original, appends one exact correction and optional replacement, and derives the auditable net physical effect.":
    "Behoudt het onveranderlijke origineel, voegt één exacte correctie en optionele vervanging toe en leidt het controleerbare netto fysieke effect af.",
  "Prevents execution without changing or deleting the underlying obligation.":
    "Voorkomt uitvoering zonder de onderliggende verplichting te wijzigen of te verwijderen.",
  "Places individual holds on the open commitments evidenced by a document.":
    "Plaatst afzonderlijke blokkeringen op de open Commitments die door een document worden aangetoond.",
  "Blocks customer shipment execution while orders and reservations remain possible.":
    "Blokkeert de uitvoering van klantzendingen terwijl orders en reserveringen mogelijk blijven.",
  "Records an optional tenant-scoped pallet identity with an optional NVE/SSCC and immutable source evidence.":
    "Legt een optionele bedrijfsgebonden palletidentiteit vast met een optionele NVE/SSCC en onveranderlijk bronbewijs.",
  "Creates a tenant-scoped batch identity for a lot- or serial-tracked item without storing a stock balance.":
    "Maakt een bedrijfsgebonden partij-identiteit voor een partij- of seriegevolgd artikel zonder een voorraadbalans op te slaan.",
  "Creates the identity of one serialized unit, optionally linked to its lot, without storing its location or status.":
    "Maakt de identiteit van één geserialiseerde eenheid, optioneel gekoppeld aan de partij, zonder locatie of status op te slaan.",
});

Object.assign(dictionaries.es, {
  Requires: "Requiere",
  "Appends one idempotent source-supported observation about an existing tenant-scoped subject after confirmation without copying typed operational state.":
    "Registra tras la confirmación una observación idempotente respaldada por una fuente sobre un objeto existente de la empresa, sin copiar estado operativo tipado.",
  "Atomically records lossless manual Source evidence, typed order Evidence, and the derived outgoing or incoming Commitments without storing operational status on the Document.":
    "Registra atómicamente datos de origen manuales sin pérdida, evidencia tipada del pedido y los Commitments entrantes o salientes derivados, sin guardar estado operativo en el documento.",
  "Records payment evidence, posts balanced ledger entries, and allocates the payment to an invoice.":
    "Registra evidencia del pago, contabiliza asientos equilibrados y asigna el pago a una factura.",
  "Records an outgoing payment and explicitly settles a supplier invoice entry.":
    "Registra un pago saliente y liquida explícitamente una partida de factura de proveedor.",
  "Allocates available stock to one commitment, optionally by pallet, lot, or exact serial unit, and reports any shortage.":
    "Asigna existencias disponibles a un Commitment, opcionalmente por palé, lote o unidad serial exacta, e informa de cualquier falta.",
  "Records an immutable physical event with the same optional pallet, lot, and serial identity used by reservations.":
    "Registra un evento físico inmutable con las mismas identidades opcionales de palé, lote y serie usadas por las reservas.",
  "Preserves an immutable original, appends one exact correction and optional replacement, and derives the auditable net physical effect.":
    "Conserva el original inmutable, añade una corrección exacta y un reemplazo opcional, y deriva el efecto físico neto auditable.",
  "Prevents execution without changing or deleting the underlying obligation.":
    "Impide la ejecución sin modificar ni eliminar la obligación subyacente.",
  "Places individual holds on the open commitments evidenced by a document.":
    "Aplica bloqueos individuales a los Commitments abiertos respaldados por un documento.",
  "Blocks customer shipment execution while orders and reservations remain possible.":
    "Bloquea la ejecución de envíos al cliente mientras los pedidos y las reservas siguen siendo posibles.",
  "Records an optional tenant-scoped pallet identity with an optional NVE/SSCC and immutable source evidence.":
    "Registra una identidad de palé opcional de la empresa con NVE/SSCC opcional y evidencia de origen inmutable.",
  "Creates a tenant-scoped batch identity for a lot- or serial-tracked item without storing a stock balance.":
    "Crea una identidad de lote de la empresa para un artículo controlado por lote o serie sin guardar un saldo de existencias.",
  "Creates the identity of one serialized unit, optionally linked to its lot, without storing its location or status.":
    "Crea la identidad de una unidad serializada, opcionalmente vinculada a su lote, sin guardar su ubicación ni estado.",
});

Object.assign(dictionaries.de, {
  "Another run or request needs your attention. Refresh your saved runs before continuing.":
    "Ein anderer Versuch oder eine Anfrage ist noch offen. Aktualisiere zuerst deine gespeicherten Versuche.",
  "Back to your account": "Zurück zu deinem Konto",
  "Create sandbox": "Sandbox anlegen",
  "Exception catalog": "Ausnahmen-Katalog",
  "Business history": "Geschäftsverlauf",
  "All history": "Gesamter Verlauf",
  "All record types": "Alle Datensatztypen",
  "Counts cover all sandbox records. Groups contain loaded matching events linked by source or correlation, not necessarily the entire order.":
    "Zahlen: alle Datensätze dieser Sandbox. Gruppen zeigen geladene Treffer mit gemeinsamer Quelle oder Korrelation, nicht zwingend den gesamten Auftrag.",
  "History could not be loaded.": "Der Verlauf konnte nicht geladen werden.",
  "Last 24 hours": "Letzte 24 Stunden",
  "Last 7 days": "Letzte 7 Tage",
  "Last 30 days": "Letzte 30 Tage",
  "Ledger entries": "Finanzbuchungen",
  "Load older events": "Ältere Ereignisse laden",
  "No matching events.": "Keine passenden Ereignisse.",
  Period: "Zeitraum",
  "Record type": "Datensatztyp",
  "Recorded sequence": "Aufgezeichneter Ablauf",
  "Records in this sandbox": "Datensätze dieser Sandbox",
  "Related record could not be loaded.": "Der verknüpfte Datensatz konnte nicht geladen werden.",
  "Search business history": "Kunde, Artikel, Beleg oder ID suchen",
  "Select a transaction to explore its events and linked records.":
    "Wähle einen Vorgang, um Ereignisse und verknüpfte Datensätze zu erkunden.",
  Transactions: "Vorgänge",
  Retry: "Erneut versuchen",
  "Possible exception classes from the current Reality catalog, not active findings. Some need data or operations beyond this sandbox. Descriptions use the catalog's original language.":
    "Mögliche Ausnahmeklassen aus dem aktuellen Reality-Katalog, keine aktiven Fälle. Manche benötigen Daten oder Vorgänge außerhalb dieser Sandbox. Die Beschreibungen stehen in der Originalsprache des Katalogs.",
  "Could not load the exception catalog.": "Der Ausnahmen-Katalog konnte nicht geladen werden.",
  "No matching exception classes.": "Keine passenden Ausnahmeklassen.",
  "Responsible area": "Zuständiger Bereich",
  "How it clears": "Wie sich der Fall auflösen lässt",
  "Return to operations": "Zurück zu den Vorgängen",
  "Leave operation": "Vorgang verlassen",
  "Leave this operation?": "Diesen Vorgang verlassen?",
  "Continue operation": "Vorgang fortsetzen",
  "Recorded changes remain. Leaving does not undo stock movements, goods obligations or money postings. Consider whether a return, reversal or compensating operation is needed.":
    "Bereits erfasste Änderungen bleiben bestehen. Beim Verlassen werden keine Warenbewegungen, Lieferverpflichtungen oder Geldbuchungen rückgängig gemacht. Prüfe, ob eine Retoure, Stornierung oder Gegenbuchung nötig ist.",
  "Confirm and create sample data": "Bestätigen und Beispieldaten anlegen",
  "Confirm sample setup": "Beispieldaten bestätigen",
  "Daily limit resets": "Tageslimit wird zurückgesetzt",
  "Explore a private example, one explicit action at a time.":
    "Erkunde ein privates Beispiel – mit jeder Aktion nachvollziehbar einen Schritt weiter.",
  "Learn by doing": "Ausprobieren und verstehen",
  "Learning actions are not available yet": "Lernaktionen sind noch nicht verfügbar",
  "Loading this run…": "Versuch wird geladen…",
  "Loading your Playground…": "Dein Playground wird geladen…",
  "New runs are not enabled on this deployment. Saved runs remain readable.":
    "Neue Versuche sind hier noch nicht freigeschaltet. Gespeicherte Versuche bleiben lesbar.",
  "New runs remaining today": "Neue Versuche heute noch möglich",
  "No saved runs yet.": "Noch keine gespeicherten Versuche.",
  "No stock is created by this setup. Stock needs a separate Movement.":
    "Diese Einrichtung erzeugt keinen Bestand. Dafür braucht es ein eigenes Movement.",
  "One company, two customers, one supplier, one warehouse and three articles. No company setup or model key is needed.":
    "Ein Unternehmen, zwei Kunden, ein Lieferant, ein Lager und drei Artikel. Ohne Firmeneinrichtung oder eigenen KI-Schlüssel.",
  "One prepared example": "Ein vorbereitetes Beispiel",
  "Only you can access these runs. No live shop, payments or external business actions are connected.":
    "Nur du hast Zugriff auf diese Versuche. Kein Live-Shop, keine Zahlungen und keine externen Geschäftsaktionen sind angebunden.",
  "Playground navigation": "Playground-Navigation",
  "Playground overview": "Playground-Übersicht",
  "Preparing sample data…": "Beispieldaten werden vorbereitet…",
  "Preparing sample data": "Beispieldaten werden vorbereitet",
  "Setup needs another attempt": "Einrichtung muss erneut versucht werden",
  "Archived — read only": "Archiviert – nur lesbar",
  "Archive and start a fresh run": "Archivieren und neuen Versuch starten",
  "Execution outcome is unresolved": "Ausführung ungeklärt",
  "This step was rejected": "Dieser Schritt wurde abgelehnt",
  "Keep this run for inspection and start a fresh private run for another test.":
    "Bewahre diesen Versuch zur Prüfung auf und starte für einen weiteren Test einen neuen privaten Versuch.",
  "Preset version": "Beispielsatz-Version",
  "Private history, never reset in place.": "Private Historie, ohne Überschreiben.",
  "Record ID": "Datensatz-ID",
  Refresh: "Aktualisieren",
  "Retained run slots remaining": "Weitere speicherbare Versuche",
  "Retry the original setup request. This does not create a second run.":
    "Die ursprüngliche Einrichtung erneut versuchen. Dabei entsteht kein zweiter Versuch.",
  "Review setup retry": "Erneute Einrichtung prüfen",
  "Run ID": "Versuchs-ID",
  "Sandbox — synthetic data only": "Sandbox – ausschließlich Beispieldaten",
  "Saved runs": "Gespeicherte Versuche",
  "Setup is not ready. Refresh its status or explicitly retry this same run. Partial records cannot be used.":
    "Die Einrichtung ist noch nicht bereit. Aktualisiere den Status oder wiederhole ausdrücklich die Einrichtung dieses Versuchs. Unvollständige Daten sind nicht nutzbar.",
  "Start playground": "Playground starten",
  "The server will not retry this action blindly. Keep this run for inspection and start a fresh private run.":
    "Der Server wiederholt diese Aktion nicht blind. Bewahre diesen Versuch zur Prüfung auf und starte einen neuen privaten Versuch.",
  "Start with a small trading business": "Starte mit einem kleinen Handelsunternehmen",
  "The request could not be verified. Refresh the saved runs or retry the same setup request.":
    "Das Ergebnis der Anfrage konnte nicht geprüft werden. Aktualisiere die gespeicherten Versuche oder wiederhole dieselbe Einrichtungsanfrage.",
  "The preview changed or was stale. The current server preview is loaded; review it and confirm again.":
    "Die Vorschau war veraltet oder hat sich geändert. Die aktuelle Server-Vorschau wurde geladen; prüfe sie und bestätige erneut.",
  "The run limit has been reached. Your saved runs remain available.":
    "Das Limit für neue Versuche ist erreicht. Deine gespeicherten Versuche bleiben verfügbar.",
  "These are real records in this sandbox, not a simulated stock balance.":
    "Das sind echte Datensätze in dieser Sandbox, kein simulierter Bestand.",
  "This creates a private sandbox and eight synthetic reference records. It does not create stock or contact external systems.":
    "Es werden eine private Sandbox und acht Beispiel-Stammdatensätze angelegt. Es entsteht kein Bestand; externe Systeme werden nicht kontaktiert.",
  "This first version prepares your private environment. Guided actions, chat and step-by-step explanations are still being built.":
    "Diese erste Version bereitet deine private Umgebung vor. Geführte Aktionen, Chat und Erklärungen zu jedem Schritt werden noch entwickelt.",
  "This run is read only. Its records are preserved.":
    "Dieser Versuch ist nur lesbar. Seine Datensätze bleiben erhalten.",
  "This run is unavailable. Choose one of your saved runs.":
    "Dieser Versuch ist nicht verfügbar. Wähle einen deiner gespeicherten Versuche.",
  "Trading example": "Handelsbeispiel",
  "You already have a current run. Open it from Saved runs.":
    "Du hast bereits einen laufenden Versuch. Öffne ihn unter Gespeicherte Versuche.",
  "Your prepared references": "Deine vorbereiteten Stammdaten",
  "Your session or Playground access is unavailable. Sign in again or check your account.":
    "Deine Sitzung oder dein Playground-Zugang ist nicht verfügbar. Melde dich erneut an oder prüfe dein Konto.",
});

Object.assign(dictionaries.nl, {
  "Another run or request needs your attention. Refresh your saved runs before continuing.":
    "Een andere proef of aanvraag vraagt aandacht. Vernieuw eerst je opgeslagen proeven.",
  "Back to your account": "Terug naar je account",
  "Create sandbox": "Sandbox aanmaken",
  "Exception catalog": "Uitzonderingencatalogus",
  "Business history": "Bedrijfsverloop",
  "All history": "Volledige geschiedenis",
  "All record types": "Alle recordtypen",
  "Counts cover all sandbox records. Groups contain loaded matching events linked by source or correlation, not necessarily the entire order.":
    "Aantallen omvatten alle sandboxrecords. Groepen tonen geladen resultaten met dezelfde bron of correlatie, niet noodzakelijk de hele order.",
  "History could not be loaded.": "De geschiedenis kon niet worden geladen.",
  "Last 24 hours": "Laatste 24 uur",
  "Last 7 days": "Laatste 7 dagen",
  "Last 30 days": "Laatste 30 dagen",
  "Ledger entries": "Financiële boekingen",
  "Load older events": "Oudere gebeurtenissen laden",
  "No matching events.": "Geen passende gebeurtenissen.",
  Period: "Periode",
  "Record type": "Recordtype",
  "Recorded sequence": "Vastgelegd verloop",
  "Records in this sandbox": "Records in deze sandbox",
  "Related record could not be loaded.": "Het gekoppelde record kon niet worden geladen.",
  "Search business history": "Klant, artikel, document of ID zoeken",
  "Select a transaction to explore its events and linked records.":
    "Kies een handeling om gebeurtenissen en gekoppelde records te verkennen.",
  Transactions: "Handelingen",
  Retry: "Opnieuw proberen",
  "Possible exception classes from the current Reality catalog, not active findings. Some need data or operations beyond this sandbox. Descriptions use the catalog's original language.":
    "Mogelijke uitzonderingsklassen uit de actuele Reality-catalogus, geen actieve gevallen. Sommige vereisen gegevens of handelingen buiten deze sandbox. Beschrijvingen gebruiken de oorspronkelijke catalogustaal.",
  "Could not load the exception catalog.": "De uitzonderingencatalogus kon niet worden geladen.",
  "No matching exception classes.": "Geen passende uitzonderingsklassen.",
  "Responsible area": "Verantwoordelijk team",
  "How it clears": "Hoe het geval wordt opgelost",
  "Return to operations": "Terug naar handelingen",
  "Leave operation": "Handeling verlaten",
  "Leave this operation?": "Deze handeling verlaten?",
  "Continue operation": "Handeling voortzetten",
  "Recorded changes remain. Leaving does not undo stock movements, goods obligations or money postings. Consider whether a return, reversal or compensating operation is needed.":
    "Vastgelegde wijzigingen blijven bestaan. Verlaten maakt voorraadbewegingen, leververplichtingen of geldboekingen niet ongedaan. Ga na of een retour, terugboeking of compenserende handeling nodig is.",
  "Confirm and create sample data": "Bevestigen en voorbeeldgegevens aanmaken",
  "Confirm sample setup": "Voorbeeldgegevens bevestigen",
  "Daily limit resets": "Daglimiet wordt vernieuwd",
  "Explore a private example, one explicit action at a time.":
    "Verken een privévoorbeeld, één expliciete actie tegelijk.",
  "Learn by doing": "Leren door te doen",
  "Learning actions are not available yet": "Leeracties zijn nog niet beschikbaar",
  "Loading this run…": "Proef laden…",
  "Loading your Playground…": "Je Playground laden…",
  "New runs are not enabled on this deployment. Saved runs remain readable.":
    "Nieuwe proeven zijn hier niet ingeschakeld. Opgeslagen proeven blijven leesbaar.",
  "New runs remaining today": "Nieuwe proeven vandaag over",
  "No saved runs yet.": "Nog geen opgeslagen proeven.",
  "No stock is created by this setup. Stock needs a separate Movement.":
    "Deze inrichting maakt geen voorraad aan. Daarvoor is een afzonderlijk Movement nodig.",
  "One company, two customers, one supplier, one warehouse and three articles. No company setup or model key is needed.":
    "Eén bedrijf, twee klanten, één leverancier, één magazijn en drie artikelen. Geen bedrijfsconfiguratie of modelsleutel nodig.",
  "One prepared example": "Eén voorbereid voorbeeld",
  "Only you can access these runs. No live shop, payments or external business actions are connected.":
    "Alleen jij hebt toegang tot deze proeven. Er zijn geen livewinkel, betalingen of externe bedrijfsacties gekoppeld.",
  "Playground navigation": "Navigatie van de Playground",
  "Playground overview": "Overzicht van de Playground",
  "Preparing sample data…": "Voorbeeldgegevens voorbereiden…",
  "Preparing sample data": "Voorbeeldgegevens voorbereiden",
  "Setup needs another attempt": "Inrichting moet opnieuw worden geprobeerd",
  "Archived — read only": "Gearchiveerd — alleen lezen",
  "Preset version": "Versie van de voorbeeldset",
  "Private history, never reset in place.": "Privégeschiedenis, nooit overschreven.",
  "Record ID": "Recordidentificatie",
  Refresh: "Vernieuwen",
  "Retained run slots remaining": "Resterende plaatsen voor opgeslagen proeven",
  "Retry the original setup request. This does not create a second run.":
    "Probeer de oorspronkelijke inrichting opnieuw. Dit maakt geen tweede proef aan.",
  "Review setup retry": "Nieuwe inrichtingspoging controleren",
  "Run ID": "Proefidentificatie",
  "Sandbox — synthetic data only": "Sandbox — alleen voorbeeldgegevens",
  "Saved runs": "Opgeslagen proeven",
  "Setup is not ready. Refresh its status or explicitly retry this same run. Partial records cannot be used.":
    "De inrichting is nog niet klaar. Vernieuw de status of probeer dezelfde proef expliciet opnieuw. Onvolledige records zijn niet bruikbaar.",
  "Start playground": "Playground starten",
  "Start with a small trading business": "Begin met een klein handelsbedrijf",
  "The request could not be verified. Refresh the saved runs or retry the same setup request.":
    "Het resultaat van de aanvraag kon niet worden gecontroleerd. Vernieuw de opgeslagen proeven of herhaal dezelfde inrichtingsaanvraag.",
  "The run limit has been reached. Your saved runs remain available.":
    "De limiet voor proeven is bereikt. Je opgeslagen proeven blijven beschikbaar.",
  "These are real records in this sandbox, not a simulated stock balance.":
    "Dit zijn echte records in deze sandbox, geen gesimuleerde voorraad.",
  "This creates a private sandbox and eight synthetic reference records. It does not create stock or contact external systems.":
    "Dit maakt een privésandbox met acht voorbeeldstamrecords aan. Het creëert geen voorraad en benadert geen externe systemen.",
  "This first version prepares your private environment. Guided actions, chat and step-by-step explanations are still being built.":
    "Deze eerste versie bereidt je privéomgeving voor. Begeleide acties, chat en stapsgewijze uitleg zijn nog in ontwikkeling.",
  "This run is read only. Its records are preserved.":
    "Deze proef is alleen-lezen. De records blijven bewaard.",
  "This run is unavailable. Choose one of your saved runs.":
    "Deze proef is niet beschikbaar. Kies een van je opgeslagen proeven.",
  "Trading example": "Handelsvoorbeeld",
  "You already have a current run. Open it from Saved runs.":
    "Je hebt al een huidige proef. Open deze via Opgeslagen proeven.",
  "Your prepared references": "Je voorbereide stamgegevens",
  "Your session or Playground access is unavailable. Sign in again or check your account.":
    "Je sessie of Playground-toegang is niet beschikbaar. Meld je opnieuw aan of controleer je account.",
});

Object.assign(dictionaries.es, {
  "Another run or request needs your attention. Refresh your saved runs before continuing.":
    "Hay otra prueba o solicitud pendiente. Actualiza tus pruebas guardadas antes de continuar.",
  "Back to your account": "Volver a tu cuenta",
  "Create sandbox": "Crear sandbox",
  "Exception catalog": "Catálogo de excepciones",
  "Business history": "Historial del negocio",
  "All history": "Todo el historial",
  "All record types": "Todos los tipos de registro",
  "Counts cover all sandbox records. Groups contain loaded matching events linked by source or correlation, not necessarily the entire order.":
    "Las cifras abarcan todos los registros del sandbox. Los grupos muestran resultados cargados con la misma fuente o correlación, no necesariamente el pedido completo.",
  "History could not be loaded.": "No se pudo cargar el historial.",
  "Last 24 hours": "Últimas 24 horas",
  "Last 7 days": "Últimos 7 días",
  "Last 30 days": "Últimos 30 días",
  "Ledger entries": "Asientos financieros",
  "Load older events": "Cargar eventos anteriores",
  "No matching events.": "No hay eventos coincidentes.",
  Period: "Período",
  "Record type": "Tipo de registro",
  "Recorded sequence": "Secuencia registrada",
  "Records in this sandbox": "Registros de este sandbox",
  "Related record could not be loaded.": "No se pudo cargar el registro relacionado.",
  "Search business history": "Buscar cliente, artículo, documento o ID",
  "Select a transaction to explore its events and linked records.":
    "Selecciona una operación para explorar sus eventos y registros relacionados.",
  Transactions: "Operaciones",
  Retry: "Reintentar",
  "Possible exception classes from the current Reality catalog, not active findings. Some need data or operations beyond this sandbox. Descriptions use the catalog's original language.":
    "Clases posibles del catálogo actual de Reality, no casos activos. Algunas necesitan datos u operaciones fuera de este sandbox. Las descripciones usan el idioma original del catálogo.",
  "Could not load the exception catalog.": "No se pudo cargar el catálogo de excepciones.",
  "No matching exception classes.": "No hay clases de excepción coincidentes.",
  "Responsible area": "Área responsable",
  "How it clears": "Cómo se resuelve",
  "Return to operations": "Volver a las operaciones",
  "Leave operation": "Salir de la operación",
  "Leave this operation?": "¿Salir de esta operación?",
  "Continue operation": "Continuar operación",
  "Recorded changes remain. Leaving does not undo stock movements, goods obligations or money postings. Consider whether a return, reversal or compensating operation is needed.":
    "Los cambios registrados se conservan. Salir no deshace movimientos de existencias, obligaciones de entrega ni asientos monetarios. Comprueba si hace falta una devolución, reversión u operación compensatoria.",
  "Confirm and create sample data": "Confirmar y crear datos de ejemplo",
  "Confirm sample setup": "Confirmar datos de ejemplo",
  "Daily limit resets": "El límite diario se restablece",
  "Explore a private example, one explicit action at a time.":
    "Explora un ejemplo privado, una acción explícita a la vez.",
  "Learn by doing": "Aprender haciendo",
  "Learning actions are not available yet": "Las acciones de aprendizaje aún no están disponibles",
  "Loading this run…": "Cargando esta prueba…",
  "Loading your Playground…": "Cargando tu Playground…",
  "New runs are not enabled on this deployment. Saved runs remain readable.":
    "Las pruebas nuevas no están habilitadas aquí. Puedes seguir consultando las guardadas.",
  "New runs remaining today": "Pruebas nuevas disponibles hoy",
  "No saved runs yet.": "Aún no hay pruebas guardadas.",
  "No stock is created by this setup. Stock needs a separate Movement.":
    "Esta configuración no crea existencias. Para ello se necesita un Movement independiente.",
  "One company, two customers, one supplier, one warehouse and three articles. No company setup or model key is needed.":
    "Una empresa, dos clientes, un proveedor, un almacén y tres artículos. Sin configurar una empresa ni una clave de modelo.",
  "One prepared example": "Un ejemplo preparado",
  "Only you can access these runs. No live shop, payments or external business actions are connected.":
    "Solo tú puedes acceder a estas pruebas. No hay tiendas en vivo, pagos ni acciones empresariales externas conectadas.",
  "Playground navigation": "Navegación del Playground",
  "Playground overview": "Resumen del Playground",
  "Preparing sample data…": "Preparando datos de ejemplo…",
  "Preparing sample data": "Preparando datos de ejemplo",
  "Setup needs another attempt": "Hay que volver a intentar la configuración",
  "Archived — read only": "Archivada — solo lectura",
  "Preset version": "Versión del conjunto de ejemplo",
  "Private history, never reset in place.": "Historial privado que nunca se sobrescribe.",
  "Record ID": "ID del registro",
  Refresh: "Actualizar",
  "Retained run slots remaining": "Plazas disponibles para guardar pruebas",
  "Retry the original setup request. This does not create a second run.":
    "Reintenta la solicitud de configuración original. No se crea una segunda prueba.",
  "Review setup retry": "Revisar el reintento de configuración",
  "Run ID": "ID de la prueba",
  "Sandbox — synthetic data only": "Entorno de pruebas — solo datos sintéticos",
  "Saved runs": "Pruebas guardadas",
  "Setup is not ready. Refresh its status or explicitly retry this same run. Partial records cannot be used.":
    "La configuración aún no está lista. Actualiza el estado o reintenta explícitamente esta misma prueba. Los registros parciales no se pueden usar.",
  "Start playground": "Iniciar Playground",
  "Start with a small trading business": "Empieza con una pequeña empresa comercial",
  "The request could not be verified. Refresh the saved runs or retry the same setup request.":
    "No se pudo verificar el resultado. Actualiza las pruebas guardadas o reintenta la misma solicitud de configuración.",
  "The run limit has been reached. Your saved runs remain available.":
    "Se ha alcanzado el límite de pruebas. Tus pruebas guardadas siguen disponibles.",
  "These are real records in this sandbox, not a simulated stock balance.":
    "Son registros reales de este entorno de pruebas, no un saldo de existencias simulado.",
  "This creates a private sandbox and eight synthetic reference records. It does not create stock or contact external systems.":
    "Se crea un entorno privado con ocho registros de referencia sintéticos. No se crean existencias ni se contacta con sistemas externos.",
  "This first version prepares your private environment. Guided actions, chat and step-by-step explanations are still being built.":
    "Esta primera versión prepara tu entorno privado. Las acciones guiadas, el chat y las explicaciones paso a paso aún están en desarrollo.",
  "This run is read only. Its records are preserved.":
    "Esta prueba es de solo lectura. Sus registros se conservan.",
  "This run is unavailable. Choose one of your saved runs.":
    "Esta prueba no está disponible. Elige una de tus pruebas guardadas.",
  "Trading example": "Ejemplo comercial",
  "You already have a current run. Open it from Saved runs.":
    "Ya tienes una prueba en curso. Ábrela desde Pruebas guardadas.",
  "Your prepared references": "Tus datos de referencia preparados",
  "Your session or Playground access is unavailable. Sign in again or check your account.":
    "Tu sesión o acceso al Playground no está disponible. Inicia sesión de nuevo o revisa tu cuenta.",
});

let active: Preferences = { language: "en", locale: "en-GB", timezone: "UTC" };

export function LocalizationProvider({
  preferences,
  children,
}: {
  preferences: Preferences;
  children: ReactNode;
}) {
  active = preferences;
  useLayoutEffect(() => {
    document.documentElement.lang = preferences.language;
    translateDocument();
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        mutation.addedNodes.forEach((node) => translateTree(node));
        if (mutation.type === "characterData") translateTree(mutation.target);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    return () => observer.disconnect();
  }, [preferences.language]);
  return <>{children}</>;
}

export function t(source: string): string {
  return resolveTranslation(dictionaries, active.language, source);
}

/** The UI language in effect, for content that arrives already translated from the server. */
export function currentLanguage(): Language {
  return active.language;
}

Object.assign(dictionaries.de, {
  "Decided by": "Entschieden von",
  "Hide details": "Details ausblenden",
  "More approvals are waiting than fit on one page.":
    "Es warten mehr Freigaben, als auf eine Seite passen.",
  Outcome: "Ergebnis",
  Requested: "Angefordert",
  "Requested by": "Angefordert von",
  "Search decisions…": "Entscheidungen durchsuchen…",
  "Show details": "Details anzeigen",
  "Show all records": "Alle Datensätze anzeigen",
  "Show fewer records": "Weniger Datensätze anzeigen",
  "Open work": "Offene Arbeit",
});

Object.assign(dictionaries.nl, {
  "Decided by": "Besloten door",
  "Hide details": "Details verbergen",
  "More approvals are waiting than fit on one page.":
    "Er wachten meer goedkeuringen dan op één pagina passen.",
  Outcome: "Uitkomst",
  Requested: "Aangevraagd",
  "Requested by": "Aangevraagd door",
  "Search decisions…": "Beslissingen zoeken…",
  "Show details": "Details tonen",
  "Show all records": "Alle records tonen",
  "Show fewer records": "Minder records tonen",
  "Open work": "Openstaand werk",
});

Object.assign(dictionaries.es, {
  "Decided by": "Decidido por",
  "Hide details": "Ocultar detalles",
  "More approvals are waiting than fit on one page.":
    "Hay más aprobaciones esperando de las que caben en una página.",
  Outcome: "Resultado",
  Requested: "Solicitado",
  "Requested by": "Solicitado por",
  "Search decisions…": "Buscar decisiones…",
  "Show details": "Mostrar detalles",
  "Show all records": "Mostrar todos los registros",
  "Show fewer records": "Mostrar menos registros",
  "Open work": "Trabajo pendiente",
});

const originalText = new WeakMap<Node, string>();
// What this layer last wrote into a node. React reuses a text node across renders
// and only rewrites its content, so without this the first text a node ever held
// would be restored forever and every later render would be silently discarded.
const appliedText = new WeakMap<Node, string>();
const originalAttributes = new WeakMap<Element, Map<string, string>>();

const canonicalSource = createCanonicalSourceResolver(dictionaries);

function translatedText(source: string): string {
  const direct = t(source);
  if (direct !== source) return direct;
  const patterns: [RegExp, (match: RegExpMatchArray) => string][] = [
    [/^(\d+) shown$/, (m) => `${m[1]} ${t("shown")}`],
    [/^(\d+) records$/, (m) => `${m[1]} ${t("Records").toLowerCase()}`],
    [
      /^(\d+) evidence records$/,
      (m) =>
        `${m[1]} ${active.language === "de" ? "Evidence-Datensätze" : active.language === "nl" ? "bewijsrecords" : active.language === "es" ? "registros de evidencia" : "evidence records"}`,
    ],
    [
      /^(\d+) open exceptions$/,
      (m) =>
        `${m[1]} ${active.language === "de" ? "offene Ausnahmen" : active.language === "nl" ? "open uitzonderingen" : active.language === "es" ? "excepciones abiertas" : "open exceptions"}`,
    ],
    [/^(\d+) commitments$/, (m) => `${m[1]} Commitments`],
    [
      /^(\d+) days$/,
      (m) =>
        `${m[1]} ${active.language === "de" ? "Tage" : active.language === "nl" ? "dagen" : active.language === "es" ? "días" : "days"}`,
    ],
    [
      /^(\d+) lines$/,
      (m) =>
        `${m[1]} ${active.language === "de" ? "Positionen" : active.language === "nl" ? "regels" : active.language === "es" ? "líneas" : "lines"}`,
    ],
    [
      /^(\d+) events$/,
      (m) =>
        `${m[1]} ${active.language === "de" ? "Ereignisse" : active.language === "nl" ? "gebeurtenissen" : active.language === "es" ? "eventos" : "events"}`,
    ],
  ];
  for (const [pattern, render] of patterns) {
    const match = source.match(pattern);
    if (match) return render(match);
  }
  return source;
}

function translateTree(root: Node) {
  const nodes: Node[] = [];
  if (root.nodeType === Node.TEXT_NODE) nodes.push(root);
  else if (root.nodeType === Node.ELEMENT_NODE) {
    const element = root as Element;
    if (!isOriginalContent(element)) {
      const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) nodes.push(walker.currentNode);
    }
    for (const candidate of [
      element,
      ...Array.from(element.querySelectorAll("input, textarea, [aria-label], [title]")),
    ]) {
      const saved = originalAttributes.get(candidate) || new Map<string, string>();
      for (const attribute of ["placeholder", "aria-label", "title"]) {
        const current = candidate.getAttribute(attribute);
        if (!current) continue;
        if (!saved.has(attribute)) saved.set(attribute, canonicalSource(current));
        const next = translatedText(saved.get(attribute)!);
        if (current !== next) candidate.setAttribute(attribute, next);
      }
      originalAttributes.set(candidate, saved);
    }
  }
  for (const node of nodes) {
    if (isOriginalContent(node.parentElement)) continue;
    const current = node.textContent || "";
    if (!originalText.has(node) || appliedText.get(node) !== current) {
      originalText.set(node, canonicalSource(current));
    }
    const source = originalText.get(node)!;
    const trimmed = source.trim();
    if (!trimmed) continue;
    const next = translatedText(trimmed);
    const translated = source.replace(trimmed, next);
    if (node.textContent !== translated) node.textContent = translated;
    appliedText.set(node, translated);
  }
}

function translateDocument() {
  translateTree(document.body);
}

const date = (value: string | Date, options: Intl.DateTimeFormatOptions) =>
  new Intl.DateTimeFormat(active.locale, { ...options, timeZone: active.timezone }).format(
    typeof value === "string" ? new Date(value) : value,
  );

export const formatDate = (value: string | null | undefined) =>
  value ? date(value, { day: "2-digit", month: "short", year: "numeric" }) : "—";
export const formatDateTime = (value: string | null | undefined) =>
  value
    ? date(value, {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";
export const formatTime = (value: string | null | undefined, seconds = false) =>
  value
    ? date(value, { hour: "2-digit", minute: "2-digit", ...(seconds ? { second: "2-digit" } : {}) })
    : "—";
export const formatNumber = (value: string | number, maximumFractionDigits = 4) =>
  new Intl.NumberFormat(active.locale, { maximumFractionDigits }).format(Number(value));
export const formatQuantity = (value: string | number) => formatNumber(value, 4);
export const formatMoney = (
  value: string | number,
  currency: string,
  maximumFractionDigits?: number,
) =>
  new Intl.NumberFormat(active.locale, {
    style: "currency",
    currency,
    ...(maximumFractionDigits === undefined ? {} : { maximumFractionDigits }),
  }).format((maximumFractionDigits === undefined ? Number(value) : value) as number);

Object.assign(dictionaries.de, {
  Completed: "Erledigt",
  "Current step": "Aktueller Schritt",
  Upcoming: "Danach",
  "Show example": "Beispiel zeigen",
  "Review solution": "Lösung prüfen",
  "Confirm adoption": "Übernahme bestätigen",
  "Search for a real order or source record and select the field that answers the question. Reality keeps the exact source link.":
    "Suche einen echten Auftrag oder Quelldatensatz und wähle das Feld aus, das die Frage beantwortet. Reality behält den genauen Quellenverweis.",
  "Find an order or source record": "Auftrag oder Quelldatensatz finden",
  "Order number, Shopify ID, or known value": "Bestellnummer, Shopify-ID oder bekannter Wert",
  "Use this value": "Diesen Wert verwenden",
  "No matching source record found. Try another reference or add a manual observation.":
    "Kein passender Quelldatensatz gefunden. Versuche einen anderen Bezug oder füge eine manuelle Beobachtung hinzu.",
  "I cannot find the answer in Reality": "Ich finde die Antwort nicht in Reality",
  "Add employee knowledge, an email reference, or another external observation.":
    "Füge Mitarbeiterwissen, einen E-Mail-Verweis oder eine andere externe Beobachtung hinzu.",
  "Manual observation": "Manuelle Beobachtung",
  "Describe where the answer is currently found.":
    "Beschreibe, wo die Antwort derzeit zu finden ist.",
  "Save manual observation": "Manuelle Beobachtung speichern",
});

Object.assign(dictionaries.nl, {
  Completed: "Voltooid",
  "Current step": "Huidige stap",
  Upcoming: "Daarna",
  "Show example": "Voorbeeld tonen",
  "Review solution": "Oplossing beoordelen",
  "Confirm adoption": "Overname bevestigen",
  "Search for a real order or source record and select the field that answers the question. Reality keeps the exact source link.":
    "Zoek een echte bestelling of bronrecord en kies het veld dat de vraag beantwoordt. Reality bewaart de exacte bronverwijzing.",
  "Find an order or source record": "Bestelling of bronrecord zoeken",
  "Order number, Shopify ID, or known value": "Bestelnummer, Shopify-ID of bekende waarde",
  "Use this value": "Deze waarde gebruiken",
  "No matching source record found. Try another reference or add a manual observation.":
    "Geen passende bronrecord gevonden. Probeer een andere verwijzing of voeg een handmatige observatie toe.",
  "I cannot find the answer in Reality": "Ik kan het antwoord niet vinden in Reality",
  "Add employee knowledge, an email reference, or another external observation.":
    "Voeg medewerkerskennis, een e-mailverwijzing of een andere externe observatie toe.",
  "Manual observation": "Handmatige observatie",
  "Describe where the answer is currently found.": "Beschrijf waar het antwoord nu wordt gevonden.",
  "Save manual observation": "Handmatige observatie opslaan",
});

Object.assign(dictionaries.es, {
  Completed: "Completado",
  "Current step": "Paso actual",
  Upcoming: "Después",
  "Show example": "Mostrar ejemplo",
  "Review solution": "Revisar solución",
  "Confirm adoption": "Confirmar adopción",
  "Search for a real order or source record and select the field that answers the question. Reality keeps the exact source link.":
    "Busca un pedido real o registro de origen y selecciona el campo que responde la pregunta. Reality conserva el enlace exacto a la fuente.",
  "Find an order or source record": "Buscar pedido o registro de origen",
  "Order number, Shopify ID, or known value": "Número de pedido, ID de Shopify o valor conocido",
  "Use this value": "Usar este valor",
  "No matching source record found. Try another reference or add a manual observation.":
    "No se encontró un registro de origen coincidente. Prueba otra referencia o añade una observación manual.",
  "I cannot find the answer in Reality": "No encuentro la respuesta en Reality",
  "Add employee knowledge, an email reference, or another external observation.":
    "Añade conocimiento de empleados, una referencia de correo u otra observación externa.",
  "Manual observation": "Observación manual",
  "Describe where the answer is currently found.":
    "Describe dónde se encuentra actualmente la respuesta.",
  "Save manual observation": "Guardar observación manual",
});

Object.assign(dictionaries.de, {
  "Back to missing information": "Zurück zu fehlenden Informationen",
  "Completed items": "Abgeschlossene Vorgänge",
  "Resolved missing information": "Erledigte fehlende Informationen",
  "New missing information captured in Ask Reality will appear here.":
    "Neue, in Reality fragen erfasste fehlende Informationen erscheinen hier.",
  Outcome: "Ergebnis",
  Updated: "Aktualisiert",
});

Object.assign(dictionaries.nl, {
  "Back to missing information": "Terug naar ontbrekende informatie",
  "Completed items": "Afgeronde items",
  "Resolved missing information": "Afgeronde ontbrekende informatie",
  "New missing information captured in Ask Reality will appear here.":
    "Nieuwe ontbrekende informatie die in Vraag Reality is vastgelegd, verschijnt hier.",
  Outcome: "Resultaat",
  Updated: "Bijgewerkt",
});

Object.assign(dictionaries.es, {
  "Back to missing information": "Volver a información faltante",
  "Completed items": "Elementos completados",
  "Resolved missing information": "Información faltante resuelta",
  "New missing information captured in Ask Reality will appear here.":
    "La nueva información faltante capturada en Preguntar a Reality aparecerá aquí.",
  Outcome: "Resultado",
  Updated: "Actualizado",
});

Object.assign(dictionaries.de, {
  "Open questions": "Offene Fragen",
  "Open question captured": "Offene Frage erfasst",
  "Capture open question": "Offene Frage erfassen",
  "No matching open questions": "Keine passenden offenen Fragen",
  "Back to open questions": "Zurück zu offenen Fragen",
  "How the open question is completed": "So wird die offene Frage geklärt",
  "New open questions captured in Ask Reality will appear here.":
    "Neue, in Ask Reality erfasste offene Fragen erscheinen hier.",
  "I found a business question Reality cannot answer yet. Help me describe it and capture it as an open question.":
    "Ich habe eine Geschäftsfrage, die Reality noch nicht beantworten kann. Hilf mir, sie zu beschreiben und als offene Frage zu erfassen.",
  "A fixed reviewed value": "Ein festgelegter geprüfter Wert",
  "A source field": "Ein Quellfeld",
  "Add condition": "Bedingung hinzufügen",
  "Add group": "Gruppe hinzufügen",
  "All of these": "Alle davon",
  "Any condition": "Mindestens eine Bedingung",
  "Any of these": "Mindestens eine davon",
  "Condition group mode": "Verknüpfung der Bedingungsgruppe",
  "Create the Fact when this logic matches": "Fact erzeugen, wenn diese Logik zutrifft",
  "Groups are limited to three levels and 20 conditions.":
    "Gruppen sind auf drei Ebenen und 20 Bedingungen begrenzt.",
  "Remove group": "Gruppe entfernen",
  "Apply the Fact to": "Fact anwenden auf",
  "At least": "Mindestens",
  "At most": "Höchstens",
  "Condition comparison value": "Vergleichswert der Bedingung",
  "Condition field path": "Feldpfad der Bedingung",
  "Condition operator": "Operator der Bedingung",
  "Condition value type": "Werttyp der Bedingung",
  Datetime: "Datum und Uhrzeit",
  "Does not equal": "Ist nicht gleich",
  "Does not exist": "Ist nicht vorhanden",
  "Each matching order line": "Jede passende Auftragsposition",
  Equals: "Ist gleich",
  Exists: "Ist vorhanden",
  "Fact value comes from": "Fact-Wert stammt aus",
  "Fact value field path": "Feldpfad des Fact-Werts",
  "Fixed Fact value": "Fester Fact-Wert",
  "Is not one of": "Ist keiner von",
  "Is one of": "Ist einer von",
  "No conditions means every valid source is applicable.":
    "Ohne Bedingungen gilt jede gültige Quelle als zutreffend.",
  "Only create the Fact when all conditions match":
    "Fact nur erzeugen, wenn alle Bedingungen zutreffen",
  "Order line list path": "Pfad zur Liste der Auftragspositionen",
  "paid, authorized": "bezahlt, autorisiert",
  "Select a value": "Wert auswählen",
  "The order commitment": "Das Auftrags-Commitment",
});

Object.assign(dictionaries.nl, {
  "Open questions": "Open vragen",
  "Open question captured": "Open vraag vastgelegd",
  "Capture open question": "Open vraag vastleggen",
  "No matching open questions": "Geen passende open vragen",
  "Back to open questions": "Terug naar open vragen",
  "How the open question is completed": "Zo wordt de open vraag beantwoord",
  "New open questions captured in Ask Reality will appear here.":
    "Nieuwe open vragen die in Ask Reality zijn vastgelegd, verschijnen hier.",
  "I found a business question Reality cannot answer yet. Help me describe it and capture it as an open question.":
    "Ik heb een bedrijfsvraag die Reality nog niet kan beantwoorden. Help me die te beschrijven en als open vraag vast te leggen.",
  "A fixed reviewed value": "Een vaste beoordeelde waarde",
  "A source field": "Een bronveld",
  "Add condition": "Voorwaarde toevoegen",
  "Add group": "Groep toevoegen",
  "All of these": "Al deze",
  "Any condition": "Minstens één voorwaarde",
  "Any of these": "Minstens één hiervan",
  "Condition group mode": "Modus van voorwaardengroep",
  "Create the Fact when this logic matches": "Fact maken wanneer deze logica klopt",
  "Groups are limited to three levels and 20 conditions.":
    "Groepen zijn beperkt tot drie niveaus en 20 voorwaarden.",
  "Remove group": "Groep verwijderen",
  "Apply the Fact to": "Fact toepassen op",
  "At least": "Minstens",
  "At most": "Hoogstens",
  "Condition comparison value": "Vergelijkingswaarde van de voorwaarde",
  "Condition field path": "Veldpad van de voorwaarde",
  "Condition operator": "Operator van de voorwaarde",
  "Condition value type": "Waardetype van de voorwaarde",
  Datetime: "Datum en tijd",
  "Does not equal": "Is niet gelijk aan",
  "Does not exist": "Bestaat niet",
  "Each matching order line": "Elke passende orderregel",
  Equals: "Is gelijk aan",
  Exists: "Bestaat",
  "Fact value comes from": "Fact-waarde komt uit",
  "Fact value field path": "Veldpad van de Fact-waarde",
  "Fixed Fact value": "Vaste Fact-waarde",
  "Is not one of": "Is niet een van",
  "Is one of": "Is een van",
  "No conditions means every valid source is applicable.":
    "Zonder voorwaarden is elke geldige bron van toepassing.",
  "Only create the Fact when all conditions match":
    "Fact alleen maken als alle voorwaarden kloppen",
  "Order line list path": "Pad naar de lijst met orderregels",
  "paid, authorized": "betaald, geautoriseerd",
  "Select a value": "Selecteer een waarde",
  "The order commitment": "Het ordercommitment",
});

Object.assign(dictionaries.es, {
  "Open questions": "Preguntas abiertas",
  "Open question captured": "Pregunta abierta registrada",
  "Capture open question": "Registrar pregunta abierta",
  "No matching open questions": "No hay preguntas abiertas coincidentes",
  "Back to open questions": "Volver a preguntas abiertas",
  "How the open question is completed": "Así se resuelve la pregunta abierta",
  "New open questions captured in Ask Reality will appear here.":
    "Las nuevas preguntas abiertas registradas en Ask Reality aparecerán aquí.",
  "I found a business question Reality cannot answer yet. Help me describe it and capture it as an open question.":
    "Tengo una pregunta de negocio que Reality aún no puede responder. Ayúdame a describirla y registrarla como pregunta abierta.",
  "A fixed reviewed value": "Un valor fijo revisado",
  "A source field": "Un campo de origen",
  "Add condition": "Añadir condición",
  "Add group": "Añadir grupo",
  "All of these": "Todas estas",
  "Any condition": "Al menos una condición",
  "Any of these": "Al menos una de estas",
  "Condition group mode": "Modo del grupo de condiciones",
  "Create the Fact when this logic matches": "Crear el Fact cuando coincida esta lógica",
  "Groups are limited to three levels and 20 conditions.":
    "Los grupos están limitados a tres niveles y 20 condiciones.",
  "Remove group": "Eliminar grupo",
  "Apply the Fact to": "Aplicar el Fact a",
  "At least": "Como mínimo",
  "At most": "Como máximo",
  "Condition comparison value": "Valor de comparación de la condición",
  "Condition field path": "Ruta del campo de la condición",
  "Condition operator": "Operador de la condición",
  "Condition value type": "Tipo de valor de la condición",
  Datetime: "Fecha y hora",
  "Does not equal": "No es igual a",
  "Does not exist": "No existe",
  "Each matching order line": "Cada línea de pedido coincidente",
  Equals: "Es igual a",
  Exists: "Existe",
  "Fact value comes from": "El valor del Fact proviene de",
  "Fact value field path": "Ruta del campo del valor del Fact",
  "Fixed Fact value": "Valor fijo del Fact",
  "Is not one of": "No es uno de",
  "Is one of": "Es uno de",
  "No conditions means every valid source is applicable.":
    "Sin condiciones, cada fuente válida es aplicable.",
  "Only create the Fact when all conditions match":
    "Crear el Fact solo cuando coincidan todas las condiciones",
  "Order line list path": "Ruta de la lista de líneas del pedido",
  "paid, authorized": "pagado, autorizado",
  "Select a value": "Seleccionar un valor",
  "The order commitment": "El compromiso del pedido",
});

Object.assign(dictionaries.de, {
  "Conditions do not apply": "Bedingungen treffen nicht zu",
  "Conflicts with an existing Fact": "Widerspricht einem bestehenden Fact",
  "Continue replay": "Replay fortsetzen",
  "Disable this rule for future sources?": "Diese Regel für künftige Quellen deaktivieren?",
  "Facts created": "Erzeugte Facts",
  "Future sources stop using this version. Existing Facts and their provenance remain unchanged.":
    "Künftige Quellen verwenden diese Version nicht mehr. Bestehende Facts und ihre Herkunft bleiben unverändert.",
  "Historical replay": "Historischer Replay",
  "Historical replay can continue": "Der historische Replay kann fortgesetzt werden",
  "Historical replay is complete": "Der historische Replay ist abgeschlossen",
  "Reality processes one bounded page and shows a continuation when more sources remain. Existing Facts are not duplicated.":
    "Reality verarbeitet eine begrenzte Seite und bietet eine Fortsetzung an, wenn weitere Quellen vorhanden sind. Bestehende Facts werden nicht dupliziert.",
  "Replay result": "Replay-Ergebnis",
  "Replay this rule over historical sources?": "Diese Regel auf historische Quellen anwenden?",
  "Rule status": "Regelstatus",
  "Sources not applicable": "Nicht zutreffende Quellen",
  "Start replay": "Replay starten",
});

Object.assign(dictionaries.nl, {
  "Conditions do not apply": "Voorwaarden zijn niet van toepassing",
  "Conflicts with an existing Fact": "Is in strijd met een bestaande Fact",
  "Continue replay": "Replay voortzetten",
  "Disable this rule for future sources?": "Deze regel uitschakelen voor toekomstige bronnen?",
  "Facts created": "Aangemaakte Facts",
  "Future sources stop using this version. Existing Facts and their provenance remain unchanged.":
    "Toekomstige bronnen gebruiken deze versie niet meer. Bestaande Facts en hun herkomst blijven ongewijzigd.",
  "Historical replay": "Historische replay",
  "Historical replay can continue": "De historische replay kan doorgaan",
  "Historical replay is complete": "De historische replay is voltooid",
  "Reality processes one bounded page and shows a continuation when more sources remain. Existing Facts are not duplicated.":
    "Reality verwerkt één begrensde pagina en toont een vervolg als er meer bronnen zijn. Bestaande Facts worden niet gedupliceerd.",
  "Replay result": "Replayresultaat",
  "Replay this rule over historical sources?":
    "Deze regel opnieuw uitvoeren op historische bronnen?",
  "Rule status": "Regelstatus",
  "Sources not applicable": "Niet-toepasselijke bronnen",
  "Start replay": "Replay starten",
});

Object.assign(dictionaries.es, {
  "Conditions do not apply": "Las condiciones no se aplican",
  "Conflicts with an existing Fact": "Entra en conflicto con un Fact existente",
  "Continue replay": "Continuar repetición",
  "Disable this rule for future sources?": "¿Desactivar esta regla para fuentes futuras?",
  "Facts created": "Facts creados",
  "Future sources stop using this version. Existing Facts and their provenance remain unchanged.":
    "Las fuentes futuras dejan de usar esta versión. Los Facts existentes y su procedencia no cambian.",
  "Historical replay": "Repetición histórica",
  "Historical replay can continue": "La repetición histórica puede continuar",
  "Historical replay is complete": "La repetición histórica ha finalizado",
  "Reality processes one bounded page and shows a continuation when more sources remain. Existing Facts are not duplicated.":
    "Reality procesa una página limitada y muestra una continuación si quedan más fuentes. Los Facts existentes no se duplican.",
  "Replay result": "Resultado de la repetición",
  "Replay this rule over historical sources?": "¿Aplicar de nuevo esta regla a fuentes históricas?",
  "Rule status": "Estado de la regla",
  "Sources not applicable": "Fuentes no aplicables",
  "Start replay": "Iniciar repetición",
});

Object.assign(dictionaries.de, {
  Conditions: "Bedingungen",
  "All conditions": "Alle Bedingungen",
  "Every valid source": "Jede gültige Quelle",
  "Rule implementation": "Regelumsetzung",
  Evaluations: "Auswertungen",
});
Object.assign(dictionaries.nl, {
  Conditions: "Voorwaarden",
  "All conditions": "Alle voorwaarden",
  "Every valid source": "Elke geldige bron",
  "Rule implementation": "Regelimplementatie",
  Evaluations: "Evaluaties",
});
Object.assign(dictionaries.es, {
  Conditions: "Condiciones",
  "All conditions": "Todas las condiciones",
  "Every valid source": "Cada fuente válida",
  "Rule implementation": "Implementación de la regla",
  Evaluations: "Evaluaciones",
});

Object.assign(dictionaries.de, {
  "What this means": "Was das bedeutet",
  "What to review next": "Was als Nächstes zu prüfen ist",
  "Why Reality knows this": "Warum Reality das weiß",
  "IDs, exact fields, activity, and original source data":
    "IDs, exakte Felder, Aktivität und ursprüngliche Quelldaten",
  "Record identity": "Technische Identität",
});
Object.assign(dictionaries.nl, {
  "What this means": "Wat dit betekent",
  "What to review next": "Wat nu gecontroleerd moet worden",
  "Why Reality knows this": "Waarom Reality dit weet",
  "IDs, exact fields, activity, and original source data":
    "ID's, exacte velden, activiteit en oorspronkelijke brongegevens",
  "Record identity": "Technische identiteit",
});
Object.assign(dictionaries.es, {
  "What this means": "Qué significa esto",
  "What to review next": "Qué revisar a continuación",
  "Why Reality knows this": "Por qué Reality lo sabe",
  "IDs, exact fields, activity, and original source data":
    "ID, campos exactos, actividad y datos de origen originales",
  "Record identity": "Identidad técnica",
});

Object.assign(dictionaries.de, {
  "Practice company": "Übungsfirma",
  "Quick experiment": "Kurz ausprobieren",
  "Sandbox type": "Art der Sandbox",
  "Practice company name": "Name der Übungsfirma",
  "This practice company stays available when you start other sandboxes. No production data is linked.":
    "Diese Übungsfirma bleibt verfügbar, auch wenn du andere Sandboxes startest. Es werden keine Produktivdaten verknüpft.",
  "A quick experiment has its own sample data. It is not deleted automatically.":
    "Ein kurzer Versuch hat eigene Beispieldaten. Er wird nicht automatisch gelöscht.",
});
Object.assign(dictionaries.nl, {
  "Practice company": "Oefenbedrijf",
  "Quick experiment": "Even uitproberen",
  "Sandbox type": "Type sandbox",
  "Practice company name": "Naam van het oefenbedrijf",
  "This practice company stays available when you start other sandboxes. No production data is linked.":
    "Dit oefenbedrijf blijft beschikbaar wanneer je andere sandboxes start. Er worden geen productiegegevens gekoppeld.",
  "A quick experiment has its own sample data. It is not deleted automatically.":
    "Een kort experiment heeft eigen voorbeeldgegevens. Het wordt niet automatisch verwijderd.",
});
Object.assign(dictionaries.es, {
  "Practice company": "Empresa de práctica",
  "Quick experiment": "Prueba rápida",
  "Sandbox type": "Tipo de entorno",
  "Practice company name": "Nombre de la empresa de práctica",
  "This practice company stays available when you start other sandboxes. No production data is linked.":
    "Esta empresa de práctica sigue disponible al iniciar otros entornos. No se vinculan datos de producción.",
  "A quick experiment has its own sample data. It is not deleted automatically.":
    "Una prueba rápida tiene sus propios datos de ejemplo. No se elimina automáticamente.",
});

Object.assign(dictionaries.de, {
  "Action was not executed": "Aktion nicht ausgeführt",
  "Status check failed": "Statusprüfung fehlgeschlagen",
  "Action recorded; checking evidence": "Aktion gebucht – Nachweis wird geprüft",
  "Outcome not yet verified": "Ergebnis noch ungeklärt",
  "Checking execution status": "Ausführungsstatus wird geprüft",
  "No shipment was recorded. Close this failed attempt to continue in this sandbox.":
    "Es wurde kein Versand gebucht. Schließe diesen Fehlversuch ab, um in dieser Sandbox weiterzumachen.",
  "The server could not be reached. Check the status again; this does not repeat the action.":
    "Der Status konnte nicht abgerufen werden. Prüfe ihn erneut; die Aktion wird dadurch nicht wiederholt.",
  "The result is checked automatically. No action is repeated. You can continue once the outcome is verified.":
    "Das Ergebnis wird automatisch geprüft. Keine Aktion wird wiederholt. Sobald das Ergebnis feststeht, kannst du weitermachen.",
  "Back to operations": "Zurück zu den Vorgängen",
  "Check status again": "Status erneut prüfen",
});
Object.assign(dictionaries.nl, {
  "Action was not executed": "Actie niet uitgevoerd",
  "Status check failed": "Statuscontrole mislukt",
  "Action recorded; checking evidence": "Actie geboekt – bewijs wordt gecontroleerd",
  "Outcome not yet verified": "Resultaat nog niet bevestigd",
  "Checking execution status": "Uitvoeringsstatus wordt gecontroleerd",
  "No shipment was recorded. Close this failed attempt to continue in this sandbox.":
    "Er is geen verzending geboekt. Sluit deze mislukte poging af om in deze sandbox verder te gaan.",
  "The server could not be reached. Check the status again; this does not repeat the action.":
    "De status kon niet worden opgehaald. Controleer opnieuw; dit herhaalt de actie niet.",
  "The result is checked automatically. No action is repeated. You can continue once the outcome is verified.":
    "Het resultaat wordt automatisch gecontroleerd. Geen actie wordt herhaald. Je kunt doorgaan zodra het resultaat vaststaat.",
  "Back to operations": "Terug naar handelingen",
  "Check status again": "Status opnieuw controleren",
});
Object.assign(dictionaries.es, {
  "Action was not executed": "Acción no ejecutada",
  "Status check failed": "Error al consultar el estado",
  "Action recorded; checking evidence": "Acción registrada – comprobando evidencia",
  "Outcome not yet verified": "Resultado aún sin verificar",
  "Checking execution status": "Consultando el estado de ejecución",
  "No shipment was recorded. Close this failed attempt to continue in this sandbox.":
    "No se registró ningún envío. Cierra este intento fallido para continuar en este entorno de pruebas.",
  "The server could not be reached. Check the status again; this does not repeat the action.":
    "No se pudo consultar el estado. Vuelve a comprobarlo; esto no repite la acción.",
  "The result is checked automatically. No action is repeated. You can continue once the outcome is verified.":
    "El resultado se comprueba automáticamente. No se repite ninguna acción. Puedes continuar cuando se verifique el resultado.",
  "Back to operations": "Volver a las operaciones",
  "Check status again": "Consultar el estado de nuevo",
});

Object.assign(dictionaries.de, {
  "Search reservations": "Reservierungen suchen",
  "Select reservation": "Reservierung auswählen",
  Received: "Eingegangen",
  Released: "Freigegeben",
});

Object.assign(dictionaries.nl, {
  "Search reservations": "Reserveringen zoeken",
  "Select reservation": "Reservering selecteren",
  Received: "Ontvangen",
  Released: "Vrijgegeven",
});

Object.assign(dictionaries.es, {
  "Search reservations": "Buscar reservas",
  "Select reservation": "Seleccionar reserva",
  Received: "Recibido",
  Released: "Liberado",
});

Object.assign(dictionaries.de, {
  "Place delivery hold": "Lieferung sperren",
  "Release delivery hold": "Liefersperre aufheben",
  "Pause this delivery with a reason.": "Diese Lieferung mit einem Grund sperren.",
  "Release this delivery’s own holds. Customer-wide holds still apply.":
    "Nur die Sperren dieser Lieferung aufheben. Kundensperren gelten weiterhin.",
  "Hold reason": "Sperrgrund",
  "Select hold reason": "Sperrgrund auswählen",
  "Hold note (optional)": "Notiz zur Sperre (optional)",
  "Delivery holds to set": "Zu setzende Liefersperren",
  "Delivery holds to release": "Aufzuhebende Liefersperren",
  "Customer-wide hold": "Kundensperre",
  "Delivery hold": "Liefersperre",
  "This customer-wide hold remains when a delivery hold is released.":
    "Diese Kundensperre bleibt beim Aufheben einer Liefersperre bestehen.",
  "Credit check": "Bonitätsprüfung",
  "Customer request": "Kundenwunsch",
  "Address clarification": "Adressklärung",
  "Compliance review": "Compliance-Prüfung",
  "Manual review": "Manuelle Prüfung",
  "Other hold reason": "Sonstiger Sperrgrund",
});

Object.assign(dictionaries.nl, {
  "Place delivery hold": "Levering blokkeren",
  "Release delivery hold": "Leveringsblokkade opheffen",
  "Pause this delivery with a reason.": "Blokkeer deze levering met een reden.",
  "Release this delivery’s own holds. Customer-wide holds still apply.":
    "Hef alleen de blokkades van deze levering op. Klantbrede blokkades blijven gelden.",
  "Hold reason": "Blokkadereden",
  "Select hold reason": "Blokkadereden kiezen",
  "Hold note (optional)": "Notitie bij blokkade (optioneel)",
  "Delivery holds to set": "Te plaatsen leveringsblokkades",
  "Delivery holds to release": "Op te heffen leveringsblokkades",
  "Customer-wide hold": "Klantbrede blokkade",
  "Delivery hold": "Leveringsblokkade",
  "This customer-wide hold remains when a delivery hold is released.":
    "Deze klantbrede blokkade blijft bestaan als een leveringsblokkade wordt opgeheven.",
  "Credit check": "Kredietcontrole",
  "Customer request": "Klantverzoek",
  "Address clarification": "Adrescontrole",
  "Compliance review": "Nalevingscontrole",
  "Manual review": "Handmatige controle",
  "Other hold reason": "Andere blokkadereden",
});

Object.assign(dictionaries.es, {
  "Place delivery hold": "Bloquear entrega",
  "Release delivery hold": "Desbloquear entrega",
  "Pause this delivery with a reason.": "Bloquea esta entrega indicando un motivo.",
  "Release this delivery’s own holds. Customer-wide holds still apply.":
    "Levanta los bloqueos de esta entrega. Los bloqueos del cliente siguen vigentes.",
  "Hold reason": "Motivo del bloqueo",
  "Select hold reason": "Seleccionar motivo del bloqueo",
  "Hold note (optional)": "Nota del bloqueo (opcional)",
  "Delivery holds to set": "Bloqueos de entrega a aplicar",
  "Delivery holds to release": "Bloqueos de entrega a levantar",
  "Customer-wide hold": "Bloqueo del cliente",
  "Delivery hold": "Bloqueo de entrega",
  "This customer-wide hold remains when a delivery hold is released.":
    "Este bloqueo del cliente permanece al desbloquear una entrega.",
  "Credit check": "Verificación de crédito",
  "Customer request": "Solicitud del cliente",
  "Address clarification": "Aclaración de dirección",
  "Compliance review": "Revisión de cumplimiento",
  "Manual review": "Revisión manual",
  "Other hold reason": "Otro motivo de bloqueo",
});

Object.assign(dictionaries.de, {
  "Correct movement": "Bewegung korrigieren",
  "Reverse a mistaken movement or correct its quantity.":
    "Eine fehlerhafte Bewegung rückgängig machen oder ihre Menge korrigieren.",
  "Search movements": "Bewegungen suchen",
  "Select movement": "Bewegung auswählen",
  "Correction type": "Art der Korrektur",
  "Reverse this movement": "Buchung rückgängig machen",
  "Replace with correct quantity": "Durch korrekte Menge ersetzen",
  "Correct quantity": "Korrekte Menge",
  "Correction reason": "Korrekturgrund",
  "This movement cannot be corrected.": "Diese Bewegung kann nicht korrigiert werden.",
  "This movement has return references. Use a dedicated return correction workflow.":
    "Diese Bewegung hat Retourenverknüpfungen. Für eine Ersatzbuchung ist ein eigener Retourenablauf erforderlich.",
  "The original stays in history. Consumed reservations are not restored.":
    "Die ursprüngliche Buchung bleibt erhalten. Verbrauchte Reservierungen werden nicht wiederhergestellt.",
  "Original movement": "Ursprüngliche Buchung",
  "Inverse movement": "Gegenbuchung",
  "Available after correction": "Verfügbar nach Korrektur",
  "Current physical stock": "Aktueller physischer Bestand",
});

Object.assign(dictionaries.nl, {
  "Correct movement": "Beweging corrigeren",
  "Reverse a mistaken movement or correct its quantity.":
    "Draai een onjuiste beweging terug of corrigeer de hoeveelheid.",
  "Search movements": "Bewegingen zoeken",
  "Select movement": "Beweging selecteren",
  "Correction type": "Soort correctie",
  "Reverse this movement": "Deze boeking terugdraaien",
  "Replace with correct quantity": "Vervangen door juiste hoeveelheid",
  "Correct quantity": "Juiste hoeveelheid",
  "Correction reason": "Reden voor correctie",
  "This movement cannot be corrected.": "Deze beweging kan niet worden gecorrigeerd.",
  "This movement has return references. Use a dedicated return correction workflow.":
    "Deze beweging heeft retourkoppelingen. Gebruik een speciale retourcorrectie voor een vervangende boeking.",
  "The original stays in history. Consumed reservations are not restored.":
    "De oorspronkelijke boeking blijft bewaard. Verbruikte reserveringen worden niet hersteld.",
  "Original movement": "Oorspronkelijke beweging",
  "Inverse movement": "Tegenboeking",
  "Available after correction": "Beschikbaar na correctie",
  "Current physical stock": "Huidige fysieke voorraad",
});

Object.assign(dictionaries.es, {
  "Correct movement": "Corregir movimiento",
  "Reverse a mistaken movement or correct its quantity.":
    "Revierte un movimiento erróneo o corrige su cantidad.",
  "Search movements": "Buscar movimientos",
  "Select movement": "Seleccionar movimiento",
  "Correction type": "Tipo de corrección",
  "Reverse this movement": "Revertir este movimiento",
  "Replace with correct quantity": "Sustituir por la cantidad correcta",
  "Correct quantity": "Cantidad correcta",
  "Correction reason": "Motivo de la corrección",
  "This movement cannot be corrected.": "Este movimiento no se puede corregir.",
  "This movement has return references. Use a dedicated return correction workflow.":
    "Este movimiento tiene referencias de devolución. Usa el proceso de corrección de devoluciones para sustituirlo.",
  "The original stays in history. Consumed reservations are not restored.":
    "Se conserva el movimiento original. Las reservas consumidas no se restablecen.",
  "Original movement": "Movimiento original",
  "Inverse movement": "Movimiento inverso",
  "Available after correction": "Disponible tras la corrección",
  "Current physical stock": "Existencias físicas actuales",
});

Object.assign(dictionaries.de, { Movement: "Bewegung", "Physical stock": "Physischer Bestand" });
Object.assign(dictionaries.nl, { Movement: "Beweging", "Physical stock": "Fysieke voorraad" });
Object.assign(dictionaries.es, { Movement: "Movimiento", "Physical stock": "Existencias físicas" });

Object.assign(dictionaries.de, {
  "Company party": "Eigenes Unternehmen",
  "Creates the agreement and its deliveries. Stock and money remain unchanged.":
    "Erfasst die Vereinbarung und ihre Lieferungen. Bestand und Geld bleiben unverändert.",
  "Enter the agreed amounts. Reality does not calculate prices, tax or totals.":
    "Trage die vereinbarten Beträge ein. Reality berechnet keine Preise, Steuern oder Summen.",
  "Line details": "Positionsdetails",
  "New order": "Auftrag anlegen",
  "Open order": "Auftrag öffnen",
  "Order details": "Auftragsdetails",
  "Order direction": "Auftragsart",
  "Record a customer order or supplier order.":
    "Kundenauftrag oder Lieferantenbestellung erfassen.",
  "Requested date": "Wunschdatum",
  "Stated line amount": "Vereinbarter Positionsbetrag",
  "Stated order total": "Vereinbarter Gesamtbetrag",
  "YYYY-MM-DD": "JJJJ-MM-TT",
});
Object.assign(dictionaries.nl, {
  "Company party": "Eigen bedrijf",
  "Creates the agreement and its deliveries. Stock and money remain unchanged.":
    "Legt de afspraak en leveringen vast. Voorraad en geld blijven ongewijzigd.",
  "Enter the agreed amounts. Reality does not calculate prices, tax or totals.":
    "Voer de afgesproken bedragen in. Reality berekent geen prijzen, belasting of totalen.",
  "Line details": "Regeldetails",
  "New order": "Order aanmaken",
  "Open order": "Order openen",
  "Order details": "Orderdetails",
  "Order direction": "Ordersoort",
  "Record a customer order or supplier order.":
    "Leg een klantorder of leveranciersbestelling vast.",
  "Requested date": "Gewenste datum",
  "Stated line amount": "Afgesproken regelbedrag",
  "Stated order total": "Afgesproken totaalbedrag",
  "YYYY-MM-DD": "JJJJ-MM-DD",
});
Object.assign(dictionaries.es, {
  "Company party": "Empresa propia",
  "Creates the agreement and its deliveries. Stock and money remain unchanged.":
    "Registra el acuerdo y sus entregas. Las existencias y el dinero no cambian.",
  "Enter the agreed amounts. Reality does not calculate prices, tax or totals.":
    "Introduce los importes acordados. Reality no calcula precios, impuestos ni totales.",
  "Line details": "Detalles de la línea",
  "New order": "Crear pedido",
  "Open order": "Abrir pedido",
  "Order details": "Detalles del pedido",
  "Order direction": "Tipo de pedido",
  "Record a customer order or supplier order.": "Registra un pedido de cliente o a proveedor.",
  "Requested date": "Fecha solicitada",
  "Stated line amount": "Importe acordado de la línea",
  "Stated order total": "Importe total acordado",
  "YYYY-MM-DD": "AAAA-MM-DD",
});

Object.assign(dictionaries.de, {
  "Order number": "Auftragsnummer",
  "Requested delivery date": "Gewünschter Liefertermin",
  "Order date": "Auftragsdatum",
  "Ship to": "Lieferempfänger",
});
Object.assign(dictionaries.nl, {
  "Order number": "Ordernummer",
  "Requested delivery date": "Gewenste leverdatum",
  "Order date": "Orderdatum",
  "Ship to": "Afleveradres",
});
Object.assign(dictionaries.es, {
  "Order number": "Número de pedido",
  "Requested delivery date": "Fecha de entrega solicitada",
  "Order date": "Fecha del pedido",
  "Ship to": "Destinatario",
});

Object.assign(dictionaries.de, {
  "New invoice": "Rechnung erfassen",
  "Invoice type": "Rechnungsart",
  "Customer invoice": "Kundenrechnung",
  "Supplier invoice": "Lieferantenrechnung",
  "Order line": "Auftragsposition",
  "Stated invoice amount": "Angegebener Rechnungsbetrag",
  "Effective time (UTC ISO, optional)": "Zeitpunkt (UTC ISO, optional)",
  "Effective time": "Buchungszeitpunkt",
  "At confirmation": "Bei Bestätigung",
  "Open invoice": "Rechnung öffnen",
  "One invoice per order line. Further partial invoices for that line are not yet supported.":
    "Eine Rechnung je Auftragsposition. Weitere Teilrechnungen zur selben Position werden noch nicht unterstützt.",
  "Enter the invoice amount as stated. Recording also posts the receivable or payable; it does not record payment or move goods.":
    "Übernimm den angegebenen Rechnungsbetrag. Die Erfassung bucht auch die Forderung oder Verbindlichkeit; sie erfasst keine Zahlung und bewegt keine Ware.",
  "Records the customer receivable and revenue.": "Bucht die Kundenforderung und den Erlös.",
  "Records the supplier payable and financial inventory posting.":
    "Bucht die Lieferantenverbindlichkeit und die finanzielle Bestandsbuchung.",
  "Record a customer or supplier invoice.": "Erfasse eine Kunden- oder Lieferantenrechnung.",
});

Object.assign(dictionaries.nl, {
  "New invoice": "Factuur vastleggen",
  "Invoice type": "Factuurtype",
  "Customer invoice": "Klantfactuur",
  "Supplier invoice": "Leveranciersfactuur",
  "Order line": "Orderregel",
  "Stated invoice amount": "Vermeld factuurbedrag",
  "Effective time (UTC ISO, optional)": "Tijdstip (UTC ISO, optioneel)",
  "Effective time": "Boekingstijdstip",
  "At confirmation": "Bij bevestiging",
  "Open invoice": "Factuur openen",
  "One invoice per order line. Further partial invoices for that line are not yet supported.":
    "Eén factuur per orderregel. Verdere deelfacturen voor die regel worden nog niet ondersteund.",
  "Enter the invoice amount as stated. Recording also posts the receivable or payable; it does not record payment or move goods.":
    "Neem het vermelde factuurbedrag over. Vastleggen boekt ook de vordering of schuld; het registreert geen betaling of goederenbeweging.",
  "Records the customer receivable and revenue.": "Boekt de klantvordering en omzet.",
  "Records the supplier payable and financial inventory posting.":
    "Boekt de leveranciersschuld en de financiële voorraadboeking.",
  "Record a customer or supplier invoice.": "Leg een klant- of leveranciersfactuur vast.",
});

Object.assign(dictionaries.es, {
  "New invoice": "Registrar factura",
  "Invoice type": "Tipo de factura",
  "Customer invoice": "Factura de cliente",
  "Supplier invoice": "Factura de proveedor",
  "Order line": "Línea de pedido",
  "Stated invoice amount": "Importe indicado en la factura",
  "Effective time (UTC ISO, optional)": "Fecha y hora (UTC ISO, opcional)",
  "Effective time": "Fecha y hora de registro",
  "At confirmation": "Al confirmar",
  "Open invoice": "Abrir factura",
  "One invoice per order line. Further partial invoices for that line are not yet supported.":
    "Una factura por línea de pedido. Todavía no se admiten más facturas parciales para esa línea.",
  "Enter the invoice amount as stated. Recording also posts the receivable or payable; it does not record payment or move goods.":
    "Introduce el importe indicado en la factura. El registro también contabiliza la cuenta por cobrar o pagar; no registra pagos ni mueve mercancías.",
  "Records the customer receivable and revenue.":
    "Registra la cuenta por cobrar del cliente y los ingresos.",
  "Records the supplier payable and financial inventory posting.":
    "Registra la cuenta por pagar al proveedor y el asiento financiero de inventario.",
  "Record a customer or supplier invoice.": "Registra una factura de cliente o proveedor.",
});

Object.assign(dictionaries.de, {
  "Invoice number": "Rechnungsnummer",
  Order: "Auftrag",
  "Search orders": "Aufträge suchen",
});

Object.assign(dictionaries.nl, {
  "Invoice number": "Factuurnummer",
  Order: "Bestelling",
  "Search orders": "Orders zoeken",
});

Object.assign(dictionaries.es, {
  "Invoice number": "Número de factura",
  Order: "Pedido",
  "Search orders": "Buscar pedidos",
});

Object.assign(dictionaries.de, {
  "Record payment": "Zahlung erfassen",
  "Payment direction": "Zahlungsrichtung",
  "Customer payment received": "Kundenzahlung erhalten",
  "Supplier payment made": "Lieferantenzahlung geleistet",
  "Search invoices": "Rechnungen suchen",
  Invoice: "Rechnung",
  "Payment amount": "Zahlungsbetrag",
  "Payment reference": "Zahlungsreferenz",
  "No matching open invoices": "Keine passenden offenen Rechnungen",
  "Open before payment": "Offen vor der Zahlung",
  "Open after payment": "Offen nach der Zahlung",
  "Currently open": "Aktuell offen",
  "Assigned at recording": "Wird bei Erfassung vergeben",
  "Open payment": "Zahlung öffnen",
  "No original payment source attached.": "Keine ursprüngliche Zahlungsquelle verknüpft.",
  "Record and allocate a customer or supplier payment.":
    "Erfasse eine Kunden- oder Lieferantenzahlung und ordne sie zu.",
  "Record a payment already made and allocate it to one invoice. Partial payments are supported.":
    "Erfasse eine bereits erfolgte Zahlung und ordne sie einer Rechnung zu. Teilzahlungen sind möglich.",
  "Enter the actual payment amount. This records financial evidence; it does not initiate a bank transfer.":
    "Gib den tatsächlich gezahlten Betrag ein. Dies erfasst den Zahlungsnachweis und löst keine Banküberweisung aus.",
  "This allocation is no longer active. The original payment remains in history.":
    "Diese Zuordnung ist nicht mehr aktiv. Die ursprüngliche Zahlung bleibt in der Historie.",
});

Object.assign(dictionaries.nl, {
  "Record payment": "Betaling vastleggen",
  "Payment direction": "Betalingsrichting",
  "Customer payment received": "Klantbetaling ontvangen",
  "Supplier payment made": "Leveranciersbetaling gedaan",
  "Search invoices": "Facturen zoeken",
  Invoice: "Factuur",
  "Payment amount": "Betalingsbedrag",
  "Payment reference": "Betalingsreferentie",
  "No matching open invoices": "Geen overeenkomende openstaande facturen",
  "Open before payment": "Openstaand vóór betaling",
  "Open after payment": "Openstaand na betaling",
  "Currently open": "Nu openstaand",
  "Assigned at recording": "Toegekend bij vastleggen",
  "Open payment": "Betaling openen",
  "No original payment source attached.": "Geen oorspronkelijke betalingsbron gekoppeld.",
  "Record and allocate a customer or supplier payment.":
    "Leg een klant- of leveranciersbetaling vast en wijs deze toe.",
  "Record a payment already made and allocate it to one invoice. Partial payments are supported.":
    "Leg een reeds gedane betaling vast en wijs deze aan één factuur toe. Deelbetalingen zijn mogelijk.",
  "Enter the actual payment amount. This records financial evidence; it does not initiate a bank transfer.":
    "Voer het werkelijk betaalde bedrag in. Dit legt financieel bewijs vast en start geen bankoverschrijving.",
  "This allocation is no longer active. The original payment remains in history.":
    "Deze toewijzing is niet meer actief. De oorspronkelijke betaling blijft in de historie.",
});

Object.assign(dictionaries.es, {
  "Record payment": "Registrar pago",
  "Payment direction": "Dirección del pago",
  "Customer payment received": "Pago de cliente recibido",
  "Supplier payment made": "Pago a proveedor realizado",
  "Search invoices": "Buscar facturas",
  Invoice: "Factura",
  "Payment amount": "Importe del pago",
  "Payment reference": "Referencia del pago",
  "No matching open invoices": "No hay facturas pendientes coincidentes",
  "Open before payment": "Pendiente antes del pago",
  "Open after payment": "Pendiente después del pago",
  "Currently open": "Pendiente actualmente",
  "Assigned at recording": "Se asigna al registrar",
  "Open payment": "Abrir pago",
  "No original payment source attached.": "No hay una fuente original del pago adjunta.",
  "Record and allocate a customer or supplier payment.":
    "Registra y asigna un pago de cliente o proveedor.",
  "Record a payment already made and allocate it to one invoice. Partial payments are supported.":
    "Registra un pago ya realizado y asígnalo a una factura. Se admiten pagos parciales.",
  "Enter the actual payment amount. This records financial evidence; it does not initiate a bank transfer.":
    "Introduce el importe realmente pagado. Esto registra la evidencia financiera y no inicia una transferencia bancaria.",
  "This allocation is no longer active. The original payment remains in history.":
    "Esta asignación ya no está activa. El pago original permanece en el historial.",
});

Object.assign(dictionaries.de, {
  "Invoice positions": "Rechnungspositionen",
  "Stated line amount": "Angegebener Positionsbetrag",
  "Remove position": "Position entfernen",
  "Add invoice position": "Rechnungsposition hinzufügen",
  "Select one or more positions from this order. Already invoiced positions cannot be invoiced again yet.":
    "Wähle eine oder mehrere Positionen dieses Auftrags. Bereits berechnete Positionen können noch nicht erneut abgerechnet werden.",
});

Object.assign(dictionaries.nl, {
  "Invoice positions": "Factuurregels",
  "Stated line amount": "Opgegeven regelbedrag",
  "Remove position": "Regel verwijderen",
  "Add invoice position": "Factuurregel toevoegen",
  "Select one or more positions from this order. Already invoiced positions cannot be invoiced again yet.":
    "Selecteer één of meer regels van deze order. Reeds gefactureerde regels kunnen nog niet opnieuw worden gefactureerd.",
});

Object.assign(dictionaries.es, {
  "Invoice positions": "Líneas de factura",
  "Stated line amount": "Importe indicado de la línea",
  "Remove position": "Eliminar línea",
  "Add invoice position": "Añadir línea de factura",
  "Select one or more positions from this order. Already invoiced positions cannot be invoiced again yet.":
    "Selecciona una o más líneas de este pedido. Las líneas ya facturadas aún no pueden volver a facturarse.",
});

Object.assign(dictionaries.de, {
  "Reverse posting": "Buchung stornieren",
  "Review and reverse a recorded financial posting.":
    "Eine erfasste Finanzbuchung prüfen und stornieren.",
  "Reverse a recorded invoice or payment. Review the full financial effect before confirming.":
    "Storniere eine erfasste Rechnung oder Zahlung. Prüfe vor der Bestätigung die vollständige finanzielle Auswirkung.",
  "Search postings": "Buchungen suchen",
  Posting: "Buchung",
  "No reversible postings found": "Keine stornierbaren Buchungen gefunden",
  "Reversal reason": "Stornogrund",
  "Full posting reversal": "Vollständige Buchungsstornierung",
  "Financial effect": "Finanzielle Auswirkung",
  "Open invoice amount": "Offener Rechnungsbetrag",
  "Unallocated payment amount": "Nicht zugeordneter Zahlungsbetrag",
  "Allocations becoming inactive": "Zuordnungen, die inaktiv werden",
  "Already inactive allocations": "Bereits inaktive Zuordnungen",
  "Inverse entries": "Gegenbuchungen",
  "Reversal time: at confirmation. Original records remain in history; no bank transfer or stock movement is made.":
    "Stornozeitpunkt: bei Bestätigung. Ursprüngliche Datensätze bleiben in der Historie; es erfolgt keine Überweisung oder Warenbewegung.",
  "Reversing an invoice does not delete it or allow its order positions to be invoiced again.":
    "Ein Rechnungsstorno löscht die Rechnung nicht und gibt ihre Auftragspositionen nicht zur erneuten Abrechnung frei.",
  "Confirm reversal": "Storno bestätigen",
  "Open reversal": "Storno öffnen",
  "Current financial position": "Aktuelle finanzielle Situation",
});

Object.assign(dictionaries.nl, {
  "Reverse posting": "Boeking terugboeken",
  "Review and reverse a recorded financial posting.":
    "Controleer een vastgelegde financiële boeking en boek deze terug.",
  "Reverse a recorded invoice or payment. Review the full financial effect before confirming.":
    "Boek een vastgelegde factuur of betaling terug. Controleer het volledige financiële effect vóór bevestiging.",
  "Search postings": "Boekingen zoeken",
  Posting: "Boeking",
  "No reversible postings found": "Geen terug te boeken boekingen gevonden",
  "Reversal reason": "Reden voor terugboeking",
  "Full posting reversal": "Volledige terugboeking",
  "Financial effect": "Financieel effect",
  "Open invoice amount": "Openstaand factuurbedrag",
  "Unallocated payment amount": "Niet-toegewezen betalingsbedrag",
  "Allocations becoming inactive": "Toewijzingen die inactief worden",
  "Already inactive allocations": "Reeds inactieve toewijzingen",
  "Inverse entries": "Tegenboekingen",
  "Reversal time: at confirmation. Original records remain in history; no bank transfer or stock movement is made.":
    "Tijdstip: bij bevestiging. Oorspronkelijke records blijven in de historie; er vindt geen bankoverschrijving of goederenbeweging plaats.",
  "Reversing an invoice does not delete it or allow its order positions to be invoiced again.":
    "Een terugboeking verwijdert de factuur niet en maakt haar orderregels niet opnieuw factureerbaar.",
  "Confirm reversal": "Terugboeking bevestigen",
  "Open reversal": "Terugboeking openen",
  "Current financial position": "Huidige financiële positie",
});

Object.assign(dictionaries.es, {
  "Reverse posting": "Revertir asiento",
  "Review and reverse a recorded financial posting.":
    "Revisa y revierte un asiento financiero registrado.",
  "Reverse a recorded invoice or payment. Review the full financial effect before confirming.":
    "Revierte una factura o un pago registrado. Revisa el efecto financiero completo antes de confirmar.",
  "Search postings": "Buscar asientos",
  Posting: "Asiento",
  "No reversible postings found": "No se encontraron asientos reversibles",
  "Reversal reason": "Motivo de reversión",
  "Full posting reversal": "Reversión completa del asiento",
  "Financial effect": "Efecto financiero",
  "Open invoice amount": "Importe pendiente de factura",
  "Unallocated payment amount": "Importe de pago sin asignar",
  "Allocations becoming inactive": "Asignaciones que quedarán inactivas",
  "Already inactive allocations": "Asignaciones ya inactivas",
  "Inverse entries": "Contraasientos",
  "Reversal time: at confirmation. Original records remain in history; no bank transfer or stock movement is made.":
    "Momento de reversión: al confirmar. Los registros originales permanecen en el historial; no se realiza ninguna transferencia bancaria ni movimiento de mercancías.",
  "Reversing an invoice does not delete it or allow its order positions to be invoiced again.":
    "Revertir una factura no la elimina ni permite volver a facturar sus líneas de pedido.",
  "Confirm reversal": "Confirmar reversión",
  "Open reversal": "Abrir reversión",
  "Current financial position": "Situación financiera actual",
});

Object.assign(dictionaries.de, {
  "Select positions and enter the quantity to invoice now. You can invoice the remaining quantity later.":
    "Wähle Positionen und die Menge, die du jetzt abrechnen möchtest. Die Restmenge kannst du später berechnen.",
  "Invoice evidence stays in history. Its quantity becomes billable again once all invoice posting groups are reversed.":
    "Die Rechnung bleibt in der Historie. Ihre Menge wird wieder abrechenbar, sobald alle Buchungsgruppen der Rechnung storniert sind.",
  "Billing availability": "Abrechenbare Menge",
  "Ordered quantity": "Bestellt",
  "Already invoiced": "Bereits berechnet",
  "Remaining billable": "Noch abrechenbar",
  "Remaining after this invoice": "Nach dieser Rechnung übrig",
  "Prior invoice evidence": "Bisherige Rechnungen ansehen",
  "Quantity released by reversal": "Menge durch Storno freigegeben",
  "Remaining billable after reversal": "Abrechenbare Menge nach Storno",
});

Object.assign(dictionaries.nl, {
  "Select positions and enter the quantity to invoice now. You can invoice the remaining quantity later.":
    "Selecteer regels en de hoeveelheid die je nu wilt factureren. De resterende hoeveelheid kun je later factureren.",
  "Invoice evidence stays in history. Its quantity becomes billable again once all invoice posting groups are reversed.":
    "De factuur blijft in de historie. De hoeveelheid kan opnieuw worden gefactureerd zodra alle boekingsgroepen van de factuur zijn teruggedraaid.",
  "Billing availability": "Factureerbare hoeveelheid",
  "Ordered quantity": "Bestelde hoeveelheid",
  "Already invoiced": "Al gefactureerd",
  "Remaining billable": "Nog factureerbaar",
  "Remaining after this invoice": "Resterend na deze factuur",
  "Prior invoice evidence": "Eerdere facturen bekijken",
  "Quantity released by reversal": "Hoeveelheid vrijgegeven door terugboeking",
  "Remaining billable after reversal": "Factureerbare hoeveelheid na terugboeking",
});

Object.assign(dictionaries.es, {
  "Select positions and enter the quantity to invoice now. You can invoice the remaining quantity later.":
    "Selecciona las líneas y la cantidad que quieres facturar ahora. Puedes facturar la cantidad restante más adelante.",
  "Invoice evidence stays in history. Its quantity becomes billable again once all invoice posting groups are reversed.":
    "La factura permanece en el historial. Su cantidad se puede volver a facturar cuando se anulan todos sus grupos contables.",
  "Billing availability": "Cantidad facturable",
  "Ordered quantity": "Cantidad pedida",
  "Already invoiced": "Ya facturado",
  "Remaining billable": "Pendiente de facturar",
  "Remaining after this invoice": "Restante tras esta factura",
  "Prior invoice evidence": "Ver facturas anteriores",
  "Quantity released by reversal": "Cantidad liberada por anulación",
  "Remaining billable after reversal": "Cantidad facturable tras la anulación",
});

Object.assign(dictionaries.de, {
  "New credit note": "Gutschrift erfassen",
  "Record a customer credit against an invoice.":
    "Eine Kundengutschrift zu einer Rechnung erfassen.",
  "Correct selected invoice positions. No goods are moved and no refund is sent.":
    "Korrigiere ausgewählte Rechnungspositionen. Es wird keine Ware bewegt und keine Rückzahlung ausgeführt.",
  "Invoice position": "Rechnungsposition",
  "Credit positions": "Gutschriftspositionen",
  "Remaining credit quantity": "Noch gutschreibbare Menge",
  "Already credited": "Bereits gutgeschrieben",
  "Prior credit notes": "Bisherige Gutschriften",
  "Add credit position": "Gutschriftsposition hinzufügen",
  "Some positions have older credits without an invoice reference. Inspect those credits before continuing.":
    "Einige Positionen haben ältere Gutschriften ohne Rechnungszuordnung. Prüfe diese Gutschriften vor dem Fortfahren.",
  "Credit note number": "Gutschriftsnummer",
  "Stated credit amount": "Angegebener Gutschriftbetrag",
  "Amount to offset against this invoice": "Mit dieser Rechnung verrechnen",
  "Credit reason": "Gutschriftgrund",
  "Enter 0 to leave the credit unsettled. Only the entered offset reduces this invoice; a refund is a separate action.":
    "Mit 0 bleibt die Gutschrift offen. Nur der eingegebene Verrechnungsbetrag reduziert diese Rechnung; eine Rückzahlung ist ein eigener Vorgang.",
  "Invoice open after credit": "Rechnung nach Verrechnung offen",
  "Credit remaining to settle": "Gutschrift noch auszugleichen",
  "Remaining credit amount": "Noch gutschreibbarer Betrag",
  "Open credit note": "Gutschrift öffnen",
});

Object.assign(dictionaries.nl, {
  "New credit note": "Creditnota maken",
  "Record a customer credit against an invoice.": "Een klantcreditnota bij een factuur vastleggen.",
  "Correct selected invoice positions. No goods are moved and no refund is sent.":
    "Corrigeer geselecteerde factuurregels. Er worden geen goederen verplaatst en geen terugbetaling verzonden.",
  "Invoice position": "Factuurregel",
  "Credit positions": "Creditregels",
  "Remaining credit quantity": "Nog te crediteren hoeveelheid",
  "Already credited": "Al gecrediteerd",
  "Prior credit notes": "Eerdere creditnota’s",
  "Add credit position": "Creditregel toevoegen",
  "Some positions have older credits without an invoice reference. Inspect those credits before continuing.":
    "Sommige regels hebben oudere creditnota’s zonder factuurverwijzing. Bekijk deze eerst.",
  "Credit note number": "Creditnotanummer",
  "Stated credit amount": "Opgegeven creditbedrag",
  "Amount to offset against this invoice": "Met deze factuur verrekenen",
  "Credit reason": "Reden voor creditnota",
  "Enter 0 to leave the credit unsettled. Only the entered offset reduces this invoice; a refund is a separate action.":
    "Bij 0 blijft de creditnota open. Alleen het ingevoerde verrekenbedrag verlaagt deze factuur; een terugbetaling is een aparte handeling.",
  "Invoice open after credit": "Factuur open na verrekening",
  "Credit remaining to settle": "Creditnota nog te vereffenen",
  "Remaining credit amount": "Nog te crediteren bedrag",
  "Open credit note": "Creditnota openen",
});

Object.assign(dictionaries.es, {
  "New credit note": "Crear abono",
  "Record a customer credit against an invoice.": "Registrar un abono de cliente para una factura.",
  "Correct selected invoice positions. No goods are moved and no refund is sent.":
    "Corrige las líneas seleccionadas. No se mueven mercancías ni se envía un reembolso.",
  "Invoice position": "Línea de factura",
  "Credit positions": "Líneas del abono",
  "Remaining credit quantity": "Cantidad pendiente de abonar",
  "Already credited": "Ya abonado",
  "Prior credit notes": "Abonos anteriores",
  "Add credit position": "Añadir línea de abono",
  "Some positions have older credits without an invoice reference. Inspect those credits before continuing.":
    "Algunas líneas tienen abonos anteriores sin referencia a una factura. Revísalos antes de continuar.",
  "Credit note number": "Número de abono",
  "Stated credit amount": "Importe indicado del abono",
  "Amount to offset against this invoice": "Importe a compensar con esta factura",
  "Credit reason": "Motivo del abono",
  "Enter 0 to leave the credit unsettled. Only the entered offset reduces this invoice; a refund is a separate action.":
    "Con 0, el abono queda pendiente. Solo el importe indicado reduce esta factura; el reembolso es una acción separada.",
  "Invoice open after credit": "Factura pendiente tras el abono",
  "Credit remaining to settle": "Abono pendiente de liquidar",
  "Remaining credit amount": "Importe pendiente de abonar",
  "Open credit note": "Abrir abono",
});

Object.assign(dictionaries.de, {
  "Referenced position": "Bezogene Position",
  "Referenced positions": "Bezogene Positionen",
});

Object.assign(dictionaries.nl, {
  "Referenced position": "Gekoppelde regel",
  "Referenced positions": "Gekoppelde regels",
});

Object.assign(dictionaries.es, {
  "Referenced position": "Línea referenciada",
  "Referenced positions": "Líneas referenciadas",
});

Object.assign(dictionaries.de, {
  "Record refund": "Rückerstattung erfassen",
  "Customer credits": "Kundengutschriften",
  "Credit / party": "Gutschrift / Kunde",
  "Customer refund": "Rückzahlung an Kunden",
  "Search credit notes": "Gutschriften suchen",
  "Refund amount": "Rückerstattungsbetrag",
  "Refund reference": "Zahlungsreferenz",
  "Credit open before refund": "Gutschrift vor Rückerstattung offen",
  "Credit open after refund": "Gutschrift nach Rückerstattung offen",
  "No matching open customer credits": "Keine passenden offenen Kundengutschriften",
  "No original refund source attached.": "Keine ursprüngliche Rückzahlungsquelle verknüpft.",
  "Open refund": "Rückerstattung öffnen",
  "Record a refund against an open customer credit.":
    "Erfasse eine Rückzahlung zu einer offenen Kundengutschrift.",
  "Record a refund already made against one customer credit. Partial refunds are supported.":
    "Erfasse eine bereits erfolgte Rückzahlung zu einer Kundengutschrift. Teilrückzahlungen sind möglich.",
  "Enter the amount actually refunded. This records the refund; it does not initiate a bank transfer.":
    "Gib den tatsächlich zurückgezahlten Betrag ein. Dies erfasst die Rückzahlung und löst keine Banküberweisung aus.",
  "This allocation is no longer active. The original refund remains in history.":
    "Diese Zuordnung ist nicht mehr aktiv. Die ursprüngliche Rückzahlung bleibt im Verlauf erhalten.",
});
Object.assign(dictionaries.nl, {
  "Record refund": "Terugbetaling vastleggen",
  "Customer credits": "Klantcreditnota’s",
  "Credit / party": "Creditnota / klant",
  "Customer refund": "Terugbetaling aan klant",
  "Search credit notes": "Creditnota’s zoeken",
  "Refund amount": "Terugbetaald bedrag",
  "Refund reference": "Betalingsreferentie",
  "Credit open before refund": "Open credit vóór terugbetaling",
  "Credit open after refund": "Open credit na terugbetaling",
  "No matching open customer credits": "Geen passende open klantcreditnota’s",
  "No original refund source attached.": "Geen oorspronkelijke terugbetalingsbron gekoppeld.",
  "Open refund": "Terugbetaling openen",
  "Record a refund against an open customer credit.":
    "Leg een terugbetaling op een open klantcreditnota vast.",
  "Record a refund already made against one customer credit. Partial refunds are supported.":
    "Leg een reeds uitgevoerde terugbetaling op één klantcreditnota vast. Gedeeltelijke terugbetalingen zijn mogelijk.",
  "Enter the amount actually refunded. This records the refund; it does not initiate a bank transfer.":
    "Voer het werkelijk terugbetaalde bedrag in. Dit legt de terugbetaling vast en start geen bankoverschrijving.",
  "This allocation is no longer active. The original refund remains in history.":
    "Deze toewijzing is niet meer actief. De oorspronkelijke terugbetaling blijft in de historie staan.",
});
Object.assign(dictionaries.es, {
  "Record refund": "Registrar reembolso",
  "Customer credits": "Abonos de clientes",
  "Credit / party": "Abono / cliente",
  "Customer refund": "Reembolso al cliente",
  "Search credit notes": "Buscar abonos",
  "Refund amount": "Importe reembolsado",
  "Refund reference": "Referencia del pago",
  "Credit open before refund": "Abono pendiente antes del reembolso",
  "Credit open after refund": "Abono pendiente tras el reembolso",
  "No matching open customer credits": "No hay abonos de clientes pendientes que coincidan",
  "No original refund source attached.": "No hay una fuente original del reembolso vinculada.",
  "Open refund": "Abrir reembolso",
  "Record a refund against an open customer credit.":
    "Registra un reembolso contra un abono de cliente pendiente.",
  "Record a refund already made against one customer credit. Partial refunds are supported.":
    "Registra un reembolso ya realizado contra un abono de cliente. Se permiten reembolsos parciales.",
  "Enter the amount actually refunded. This records the refund; it does not initiate a bank transfer.":
    "Introduce el importe realmente reembolsado. Esto registra el reembolso y no inicia una transferencia bancaria.",
  "This allocation is no longer active. The original refund remains in history.":
    "Esta asignación ya no está activa. El reembolso original permanece en el historial.",
});

Object.assign(dictionaries.de, {
  "Open amount": "Offener Betrag",
  "Reverse a recorded financial posting. Review the full financial effect before confirming.":
    "Storniere eine erfasste Finanzbuchung. Prüfe vor der Bestätigung die vollständigen finanziellen Auswirkungen.",
});
Object.assign(dictionaries.nl, {
  "Open amount": "Openstaand bedrag",
  "Reverse a recorded financial posting. Review the full financial effect before confirming.":
    "Draai een vastgelegde financiële boeking terug. Controleer het volledige financiële effect voordat je bevestigt.",
});
Object.assign(dictionaries.es, {
  "Open amount": "Importe pendiente",
  "Reverse a recorded financial posting. Review the full financial effect before confirming.":
    "Anula un asiento financiero registrado. Revisa todo el efecto financiero antes de confirmar.",
});

Object.assign(dictionaries.de, {
  "Check companies": "Unternehmen prüfen",
  "Check current access": "Aktuelle Zugänge prüfen",
  "Company access updated.": "Unternehmenszugänge aktualisiert.",
  "Create an empty company. You become its owner.":
    "Lege ein leeres Unternehmen an. Du wirst dessen Eigentümer.",
  "Create this company and open its settings?":
    "Dieses Unternehmen anlegen und seine Einstellungen öffnen?",
  "If the company is absent, check again or start a new creation after reviewing this list.":
    "Falls das Unternehmen fehlt, prüfe erneut oder starte nach Prüfung dieser Liste eine neue Anlage.",
  "Invitation request accepted. Check delivery status below.":
    "Einladungsanfrage angenommen. Prüfe unten den Zustellstatus.",
  "Review company": "Unternehmen prüfen",
  "Review invitation": "Einladung prüfen",
  "Start a new creation": "Neue Anlage starten",
  "Your role": "Deine Rolle",
  "Choose the company to open. Names may be identical.":
    "Wähle das Unternehmen zum Öffnen. Namen können identisch sein.",
  "Could not check companies. Try checking again.":
    "Unternehmen konnten nicht geprüft werden. Bitte erneut prüfen.",
  "The creation result needs checking. Check companies before creating another.":
    "Das Ergebnis der Anlage muss geprüft werden. Prüfe die Unternehmen, bevor du ein weiteres anlegst.",
  "Send an invitation to this email address? Access starts only after acceptance.":
    "Einladung an diese E-Mail-Adresse senden? Der Zugang beginnt erst nach Annahme.",
  "Send a new invitation link? The previous link will stop working.":
    "Neuen Einladungslink senden? Der bisherige Link wird ungültig.",
  "Revoke this invitation? Its link will stop working.":
    "Diese Einladung widerrufen? Ihr Link wird ungültig.",
  "Remove this member's access to this company? Their other companies remain accessible.":
    "Diesem Mitglied den Zugang zu diesem Unternehmen entziehen? Andere Unternehmen bleiben zugänglich.",
  "Current access loaded. Review the list before another action.":
    "Aktuelle Zugänge geladen. Prüfe die Liste vor einer weiteren Aktion.",
  "Could not check current access. Try checking again.":
    "Aktuelle Zugänge konnten nicht geprüft werden. Bitte erneut prüfen.",
  "The result needs checking. Check current access before another action.":
    "Das Ergebnis muss geprüft werden. Prüfe die aktuellen Zugänge vor einer weiteren Aktion.",
});

Object.assign(dictionaries.nl, {
  "Check companies": "Bedrijven controleren",
  "Check current access": "Huidige toegang controleren",
  "Company access updated.": "Bedrijfstoegang bijgewerkt.",
  "Create an empty company. You become its owner.":
    "Maak een leeg bedrijf aan. Je wordt de eigenaar.",
  "Create this company and open its settings?": "Dit bedrijf aanmaken en de instellingen openen?",
  "If the company is absent, check again or start a new creation after reviewing this list.":
    "Als het bedrijf ontbreekt, controleer opnieuw of begin na controle van deze lijst een nieuwe aanmaak.",
  "Invitation request accepted. Check delivery status below.":
    "Uitnodigingsverzoek ontvangen. Controleer hieronder de bezorgstatus.",
  "Review company": "Bedrijf controleren",
  "Review invitation": "Uitnodiging controleren",
  "Start a new creation": "Nieuwe aanmaak starten",
  "Your role": "Je rol",
  "Choose the company to open. Names may be identical.":
    "Kies het bedrijf om te openen. Namen kunnen identiek zijn.",
  "Could not check companies. Try checking again.":
    "Bedrijven konden niet worden gecontroleerd. Probeer het opnieuw.",
  "The creation result needs checking. Check companies before creating another.":
    "Het resultaat moet worden gecontroleerd. Controleer de bedrijven voordat je er nog een aanmaakt.",
  "Send an invitation to this email address? Access starts only after acceptance.":
    "Een uitnodiging naar dit e-mailadres sturen? Toegang begint pas na acceptatie.",
  "Send a new invitation link? The previous link will stop working.":
    "Een nieuwe uitnodigingslink sturen? De vorige link werkt dan niet meer.",
  "Revoke this invitation? Its link will stop working.":
    "Deze uitnodiging intrekken? De link werkt dan niet meer.",
  "Remove this member's access to this company? Their other companies remain accessible.":
    "De toegang van dit lid tot dit bedrijf verwijderen? Andere bedrijven blijven toegankelijk.",
  "Current access loaded. Review the list before another action.":
    "Huidige toegang geladen. Controleer de lijst voordat je verdergaat.",
  "Could not check current access. Try checking again.":
    "Huidige toegang kon niet worden gecontroleerd. Probeer het opnieuw.",
  "The result needs checking. Check current access before another action.":
    "Het resultaat moet worden gecontroleerd. Controleer de huidige toegang voordat je verdergaat.",
});

Object.assign(dictionaries.es, {
  "Check companies": "Comprobar empresas",
  "Check current access": "Comprobar acceso actual",
  "Company access updated.": "Acceso a la empresa actualizado.",
  "Create an empty company. You become its owner.": "Crea una empresa vacía. Serás su propietario.",
  "Create this company and open its settings?": "¿Crear esta empresa y abrir su configuración?",
  "If the company is absent, check again or start a new creation after reviewing this list.":
    "Si la empresa no aparece, comprueba de nuevo o crea otra tras revisar esta lista.",
  "Invitation request accepted. Check delivery status below.":
    "Solicitud de invitación aceptada. Comprueba el estado de entrega abajo.",
  "Review company": "Revisar empresa",
  "Review invitation": "Revisar invitación",
  "Start a new creation": "Iniciar otra creación",
  "Your role": "Tu rol",
  "Choose the company to open. Names may be identical.":
    "Elige la empresa que quieres abrir. Los nombres pueden coincidir.",
  "Could not check companies. Try checking again.":
    "No se pudieron comprobar las empresas. Inténtalo de nuevo.",
  "The creation result needs checking. Check companies before creating another.":
    "Hay que comprobar el resultado. Comprueba las empresas antes de crear otra.",
  "Send an invitation to this email address? Access starts only after acceptance.":
    "¿Enviar una invitación a este correo? El acceso comienza tras aceptarla.",
  "Send a new invitation link? The previous link will stop working.":
    "¿Enviar un nuevo enlace de invitación? El anterior dejará de funcionar.",
  "Revoke this invitation? Its link will stop working.":
    "¿Revocar esta invitación? Su enlace dejará de funcionar.",
  "Remove this member's access to this company? Their other companies remain accessible.":
    "¿Retirar el acceso de este miembro a esta empresa? Sus otras empresas seguirán accesibles.",
  "Current access loaded. Review the list before another action.":
    "Acceso actual cargado. Revisa la lista antes de otra acción.",
  "Could not check current access. Try checking again.":
    "No se pudo comprobar el acceso actual. Inténtalo de nuevo.",
  "The result needs checking. Check current access before another action.":
    "Hay que comprobar el resultado. Comprueba el acceso actual antes de otra acción.",
});

Object.assign(dictionaries.de, {
  "Create your first company": "Lege dein erstes Unternehmen an",
  "Choose an authorized company or create another.":
    "Wähle ein Unternehmen mit Zugang oder lege ein weiteres an.",
  "Your company brings orders, stock and finance together.":
    "Dein Unternehmen verbindet Aufträge, Lager und Finanzen.",
  "Manage credentials and advanced setup in company administration.":
    "Verwalte Zugangsdaten und erweiterte Einrichtung in der Unternehmensverwaltung.",
});

Object.assign(dictionaries.nl, {
  "Create your first company": "Maak je eerste bedrijf aan",
  "Choose an authorized company or create another.":
    "Kies een toegankelijk bedrijf of maak een ander aan.",
  "Your company brings orders, stock and finance together.":
    "Je bedrijf brengt orders, voorraad en financiën samen.",
  "Manage credentials and advanced setup in company administration.":
    "Beheer inloggegevens en geavanceerde instellingen in het bedrijfsbeheer.",
});

Object.assign(dictionaries.es, {
  "Create your first company": "Crea tu primera empresa",
  "Choose an authorized company or create another.": "Elige una empresa autorizada o crea otra.",
  "Your company brings orders, stock and finance together.":
    "Tu empresa reúne pedidos, existencias y finanzas.",
  "Manage credentials and advanced setup in company administration.":
    "Gestiona las credenciales y la configuración avanzada en la administración de empresas.",
});

Object.assign(dictionaries.de, {
  "Import items": "Artikel importieren",
  "CSV → Map columns → Review → Confirm": "CSV → Spalten zuordnen → Prüfen → Bestätigen",
  "New items only. Maximum 500 rows and 2 MiB. Existing items are never overwritten.":
    "Nur neue Artikel. Maximal 500 Zeilen und 2 MiB. Bestehende Artikel werden niemals überschrieben.",
  "CSV file": "CSV-Datei",
  "Upload and check": "Hochladen und prüfen",
  "Source code": "Quellencode",
  "Default unit": "Standardeinheit",
  "SKU column": "Spalte für Artikelnummer",
  "Name column": "Spalte für Name",
  "Unit column": "Spalte für Einheit",
  "Select a column": "Spalte auswählen",
  "Use default unit": "Standardeinheit verwenden",
  "The default unit applies when no unit column is selected or a unit cell is empty.":
    "Die Standardeinheit gilt, wenn keine Einheitsspalte gewählt ist oder eine Einheitszelle leer ist.",
  "Review import": "Import prüfen",
  "Import review": "Importprüfung",
  "Items imported": "Artikel importiert",
  "Download original CSV": "Original-CSV herunterladen",
  "Confirm import": "Import bestätigen",
  "Cancel import": "Import abbrechen",
  "Import cancelled. No items were created.":
    "Import abgebrochen. Es wurden keine Artikel angelegt.",
  "All items were recorded. Reopening this result does not import them again.":
    "Alle Artikel wurden angelegt. Erneutes Öffnen dieses Ergebnisses importiert sie nicht nochmals.",
  "Inspect source": "Quelle ansehen",
  "Check import status": "Importstatus prüfen",
  "Check the recorded result before taking another action.":
    "Prüfe das gespeicherte Ergebnis vor einer weiteren Aktion.",
  "Recover recorded result": "Gespeichertes Ergebnis übernehmen",
  "Recover import review": "Importprüfung wiederherstellen",
  "The review result needs checking. Recover the same request before starting another.":
    "Das Ergebnis der Prüfung ist unklar. Stelle dieselbe Anfrage wieder her, bevor du eine neue startest.",
  Rows: "Zeilen",
  "CSV must be at most 2 MiB.": "Die CSV-Datei darf höchstens 2 MiB groß sein.",
  "CSV must contain data and be at most 2 MiB.":
    "Die CSV-Datei muss Daten enthalten und darf höchstens 2 MiB groß sein.",
  "CSV requires 1–50 distinct, nonempty column names.":
    "Die CSV-Datei benötigt 1–50 eindeutige, nicht leere Spaltennamen.",
  "CSV may contain at most 500 item rows.":
    "Die CSV-Datei darf höchstens 500 Artikelzeilen enthalten.",
  "CSV has no item rows.": "Die CSV-Datei enthält keine Artikelzeilen.",
  "Upload a valid UTF-8 CSV file.": "Lade eine gültige UTF-8-CSV-Datei hoch.",
  "Choose existing columns for SKU and name and optionally unit.":
    "Wähle vorhandene Spalten für Artikelnummer und Name sowie optional für die Einheit.",
  "Each mapped field must use a different column.":
    "Jedes zugeordnete Feld muss eine andere Spalte verwenden.",
  "This SKU already exists in this company.":
    "Diese Artikelnummer existiert bereits in diesem Unternehmen.",
  "Duplicate SKU in this file.": "Doppelte Artikelnummer in dieser Datei.",
  "Required field is empty or too long.": "Pflichtfeld ist leer oder zu lang.",
  "Field count differs from the header.":
    "Anzahl der Felder stimmt nicht mit der Kopfzeile überein.",
});

Object.assign(dictionaries.nl, {
  "Import items": "Artikelen importeren",
  "CSV → Map columns → Review → Confirm": "CSV → Kolommen koppelen → Controleren → Bevestigen",
  "New items only. Maximum 500 rows and 2 MiB. Existing items are never overwritten.":
    "Alleen nieuwe artikelen. Maximaal 500 rijen en 2 MiB. Bestaande artikelen worden nooit overschreven.",
  "CSV file": "CSV-bestand",
  "Upload and check": "Uploaden en controleren",
  "Source code": "Broncode",
  "Default unit": "Standaardeenheid",
  "SKU column": "Kolom voor artikelnummer",
  "Name column": "Kolom voor naam",
  "Unit column": "Kolom voor eenheid",
  "Select a column": "Kolom selecteren",
  "Use default unit": "Standaardeenheid gebruiken",
  "The default unit applies when no unit column is selected or a unit cell is empty.":
    "De standaardeenheid geldt als er geen eenheidskolom is geselecteerd of een cel leeg is.",
  "Review import": "Import controleren",
  "Import review": "Importcontrole",
  "Items imported": "Artikelen geïmporteerd",
  "Download original CSV": "Originele CSV downloaden",
  "Confirm import": "Import bevestigen",
  "Cancel import": "Import annuleren",
  "Import cancelled. No items were created.":
    "Import geannuleerd. Er zijn geen artikelen aangemaakt.",
  "All items were recorded. Reopening this result does not import them again.":
    "Alle artikelen zijn vastgelegd. Dit resultaat opnieuw openen importeert ze niet nogmaals.",
  "Inspect source": "Bron bekijken",
  "Check import status": "Importstatus controleren",
  "Check the recorded result before taking another action.":
    "Controleer het vastgelegde resultaat voordat je verdergaat.",
  "Recover recorded result": "Vastgelegd resultaat herstellen",
  "Recover import review": "Importcontrole herstellen",
  "The review result needs checking. Recover the same request before starting another.":
    "Het resultaat van de controle is onduidelijk. Herstel hetzelfde verzoek voordat je een ander start.",
  Rows: "Rijen",
  "CSV must be at most 2 MiB.": "Het CSV-bestand mag maximaal 2 MiB zijn.",
  "CSV must contain data and be at most 2 MiB.":
    "Het CSV-bestand moet gegevens bevatten en mag maximaal 2 MiB zijn.",
  "CSV requires 1–50 distinct, nonempty column names.":
    "Het CSV-bestand vereist 1–50 unieke, niet-lege kolomnamen.",
  "CSV may contain at most 500 item rows.":
    "Het CSV-bestand mag maximaal 500 artikelrijen bevatten.",
  "CSV has no item rows.": "Het CSV-bestand bevat geen artikelrijen.",
  "Upload a valid UTF-8 CSV file.": "Upload een geldig UTF-8 CSV-bestand.",
  "Choose existing columns for SKU and name and optionally unit.":
    "Kies bestaande kolommen voor artikelnummer en naam en eventueel eenheid.",
  "Each mapped field must use a different column.":
    "Elk gekoppeld veld moet een andere kolom gebruiken.",
  "This SKU already exists in this company.": "Dit artikelnummer bestaat al in dit bedrijf.",
  "Duplicate SKU in this file.": "Dubbel artikelnummer in dit bestand.",
  "Required field is empty or too long.": "Verplicht veld is leeg of te lang.",
  "Field count differs from the header.": "Aantal velden wijkt af van de kopregel.",
});

Object.assign(dictionaries.es, {
  "Import items": "Importar artículos",
  "CSV → Map columns → Review → Confirm": "CSV → Asignar columnas → Revisar → Confirmar",
  "New items only. Maximum 500 rows and 2 MiB. Existing items are never overwritten.":
    "Solo artículos nuevos. Máximo 500 filas y 2 MiB. Los artículos existentes nunca se sobrescriben.",
  "CSV file": "Archivo CSV",
  "Upload and check": "Subir y comprobar",
  "Source code": "Código de origen",
  "Default unit": "Unidad predeterminada",
  "SKU column": "Columna de referencia",
  "Name column": "Columna de nombre",
  "Unit column": "Columna de unidad",
  "Select a column": "Seleccionar columna",
  "Use default unit": "Usar unidad predeterminada",
  "The default unit applies when no unit column is selected or a unit cell is empty.":
    "La unidad predeterminada se aplica si no se selecciona una columna de unidad o la celda está vacía.",
  "Review import": "Revisar importación",
  "Import review": "Revisión de importación",
  "Items imported": "Artículos importados",
  "Download original CSV": "Descargar CSV original",
  "Confirm import": "Confirmar importación",
  "Cancel import": "Cancelar importación",
  "Import cancelled. No items were created.": "Importación cancelada. No se crearon artículos.",
  "All items were recorded. Reopening this result does not import them again.":
    "Todos los artículos se registraron. Abrir este resultado de nuevo no vuelve a importarlos.",
  "Inspect source": "Inspeccionar origen",
  "Check import status": "Comprobar estado de importación",
  "Check the recorded result before taking another action.":
    "Comprueba el resultado registrado antes de otra acción.",
  "Recover recorded result": "Recuperar resultado registrado",
  "Recover import review": "Recuperar revisión de importación",
  "The review result needs checking. Recover the same request before starting another.":
    "Hay que comprobar el resultado de la revisión. Recupera la misma solicitud antes de iniciar otra.",
  Rows: "Filas",
  "CSV must be at most 2 MiB.": "El archivo CSV no puede superar 2 MiB.",
  "CSV must contain data and be at most 2 MiB.": "El CSV debe contener datos y no superar 2 MiB.",
  "CSV requires 1–50 distinct, nonempty column names.":
    "El CSV requiere entre 1 y 50 nombres de columna distintos y no vacíos.",
  "CSV may contain at most 500 item rows.":
    "El CSV no puede contener más de 500 filas de artículos.",
  "CSV has no item rows.": "El CSV no contiene filas de artículos.",
  "Upload a valid UTF-8 CSV file.": "Sube un archivo CSV válido en UTF-8.",
  "Choose existing columns for SKU and name and optionally unit.":
    "Elige columnas existentes para referencia y nombre, y opcionalmente unidad.",
  "Each mapped field must use a different column.":
    "Cada campo asignado debe usar una columna diferente.",
  "This SKU already exists in this company.": "Esta referencia ya existe en esta empresa.",
  "Duplicate SKU in this file.": "Referencia duplicada en este archivo.",
  "Required field is empty or too long.": "El campo obligatorio está vacío o es demasiado largo.",
  "Field count differs from the header.": "El número de campos difiere de la cabecera.",
});

Object.assign(dictionaries.de, { Row: "Zeile" });
Object.assign(dictionaries.nl, { Row: "Rij" });
Object.assign(dictionaries.es, { Row: "Fila" });

Object.assign(dictionaries.de, { "Source configuration": "Quelleneinrichtung" });
Object.assign(dictionaries.nl, { "Source configuration": "Bronconfiguratie" });
Object.assign(dictionaries.es, { "Source configuration": "Configuración de origen" });

Object.assign(dictionaries.de, { "Preparing import review…": "Importprüfung wird vorbereitet…" });
Object.assign(dictionaries.nl, { "Preparing import review…": "Importcontrole wordt voorbereid…" });
Object.assign(dictionaries.es, {
  "Preparing import review…": "Preparando revisión de importación…",
});

Object.assign(dictionaries.de, {
  "Register source": "Quelle registrieren",
  "Configure source": "Quelle konfigurieren",
  "Source code": "Quellencode",
  "Source name": "Quellenname",
  "Review source": "Quelle prüfen",
  "Review registry change": "Definitionsänderung prüfen",
  "Registry state": "Definitionsstatus",
  "Source registered.": "Quelle registriert.",
  "Registry state saved.": "Definitionsstatus gespeichert.",
  "Source definitions describe origins. They do not connect an account or synchronize data.":
    "Quellendefinitionen beschreiben die Herkunft von Daten. Sie verbinden kein Konto und synchronisieren keine Daten.",
  "Enabled and disabled are registry states. Changing them does not start or stop imports.":
    "Aktiviert und deaktiviert sind Statuswerte der Definition. Eine Änderung startet oder stoppt keine Importe.",
  "Current configuration loaded. This does not prove which request changed it.":
    "Aktuelle Konfiguration geladen. Daraus geht nicht hervor, welche Anfrage sie geändert hat.",
  "The result is uncertain. Check current configuration before another change.":
    "Das Ergebnis ist unklar. Prüfe vor einer weiteren Änderung die aktuelle Konfiguration.",
  "Check current configuration": "Aktuelle Konfiguration prüfen",
  "Disable source definition": "Quellendefinition deaktivieren",
  "Enable source definition": "Quellendefinition aktivieren",
  "Disable type definition": "Typdefinition deaktivieren",
  "Enable type definition": "Typdefinition aktivieren",
  "Declared data types": "Deklarierte Datentypen",
  "A declared target describes intended interpretation. An available interpreter does not prove a live connection.":
    "Ein deklariertes Ziel beschreibt die vorgesehene Interpretation. Ein verfügbarer Interpreter belegt keine aktive Verbindung.",
  "No declared data types.": "Keine Datentypen deklariert.",
  "Interpreter available": "Interpreter verfügbar",
  "No registered interpreter": "Kein registrierter Interpreter",
  "Source definition not found.": "Quellendefinition nicht gefunden.",
  "Source code already exists.": "Quellencode existiert bereits.",
});

Object.assign(dictionaries.nl, {
  "Register source": "Bron registreren",
  "Configure source": "Bron configureren",
  "Source code": "Broncode",
  "Source name": "Bronnaam",
  "Review source": "Bron controleren",
  "Review registry change": "Registerwijziging controleren",
  "Registry state": "Registerstatus",
  "Source registered.": "Bron geregistreerd.",
  "Registry state saved.": "Registerstatus opgeslagen.",
  "Source definitions describe origins. They do not connect an account or synchronize data.":
    "Brondefinities beschrijven de herkomst van gegevens. Ze verbinden geen account en synchroniseren geen gegevens.",
  "Enabled and disabled are registry states. Changing them does not start or stop imports.":
    "Ingeschakeld en uitgeschakeld zijn registerstatussen. Een wijziging start of stopt geen imports.",
  "Current configuration loaded. This does not prove which request changed it.":
    "Huidige configuratie geladen. Dit bewijst niet welk verzoek deze heeft gewijzigd.",
  "The result is uncertain. Check current configuration before another change.":
    "Het resultaat is onzeker. Controleer de huidige configuratie voordat je iets anders wijzigt.",
  "Check current configuration": "Huidige configuratie controleren",
  "Disable source definition": "Brondefinitie uitschakelen",
  "Enable source definition": "Brondefinitie inschakelen",
  "Disable type definition": "Typedefinitie uitschakelen",
  "Enable type definition": "Typedefinitie inschakelen",
  "Declared data types": "Gedeclareerde gegevenstypen",
  "A declared target describes intended interpretation. An available interpreter does not prove a live connection.":
    "Een gedeclareerd doel beschrijft de bedoelde interpretatie. Een beschikbare interpreter bewijst geen actieve verbinding.",
  "No declared data types.": "Geen gegevenstypen gedeclareerd.",
  "Interpreter available": "Interpreter beschikbaar",
  "No registered interpreter": "Geen geregistreerde interpreter",
  "Source definition not found.": "Brondefinitie niet gevonden.",
  "Source code already exists.": "Broncode bestaat al.",
});

Object.assign(dictionaries.es, {
  "Register source": "Registrar origen",
  "Configure source": "Configurar origen",
  "Source code": "Código de origen",
  "Source name": "Nombre del origen",
  "Review source": "Revisar origen",
  "Review registry change": "Revisar cambio de registro",
  "Registry state": "Estado del registro",
  "Source registered.": "Origen registrado.",
  "Registry state saved.": "Estado del registro guardado.",
  "Source definitions describe origins. They do not connect an account or synchronize data.":
    "Las definiciones describen el origen de los datos. No conectan cuentas ni sincronizan datos.",
  "Enabled and disabled are registry states. Changing them does not start or stop imports.":
    "Activado y desactivado son estados del registro. Cambiarlos no inicia ni detiene importaciones.",
  "Current configuration loaded. This does not prove which request changed it.":
    "Configuración actual cargada. Esto no demuestra qué solicitud la modificó.",
  "The result is uncertain. Check current configuration before another change.":
    "El resultado es incierto. Comprueba la configuración actual antes de otro cambio.",
  "Check current configuration": "Comprobar configuración actual",
  "Disable source definition": "Desactivar definición de origen",
  "Enable source definition": "Activar definición de origen",
  "Disable type definition": "Desactivar definición de tipo",
  "Enable type definition": "Activar definición de tipo",
  "Declared data types": "Tipos de datos declarados",
  "A declared target describes intended interpretation. An available interpreter does not prove a live connection.":
    "Un destino declarado describe la interpretación prevista. Un intérprete disponible no demuestra una conexión activa.",
  "No declared data types.": "No hay tipos de datos declarados.",
  "Interpreter available": "Intérprete disponible",
  "No registered interpreter": "Sin intérprete registrado",
  "Source definition not found.": "No se encontró la definición de origen.",
  "Source code already exists.": "El código de origen ya existe.",
});

Object.assign(dictionaries.de, {
  "A token secret cannot be recovered. Inspect active tokens and revoke an unwanted token before creating a replacement.":
    "Ein Token-Schlüssel lässt sich nicht wiederherstellen. Prüfe aktive Tokens und widerrufe einen unerwünschten Token, bevor du einen Ersatz erstellst.",
  "Active MCP tokens": "Aktive MCP-Tokens",
  "AI credential source": "AI-Zugang",
  "AI settings are unavailable.": "AI-Einstellungen sind nicht verfügbar.",
  "AI setup saved.": "AI-Einrichtung gespeichert.",
  "All current and future tools": "Alle aktuellen und zukünftigen Werkzeuge",
  "Change AI setup": "AI-Einrichtung ändern",
  "Check saved AI settings": "Gespeicherte AI-Einstellungen prüfen",
  "Choose exact tools. No permissions are selected by default.":
    "Wähle die einzelnen Werkzeuge aus. Es sind keine Berechtigungen vorausgewählt.",
  "Clear selection": "Auswahl leeren",
  "Company Anthropic key": "Eigener Anthropic-Schlüssel",
  "Copy failed. Select and copy the value manually.":
    "Kopieren fehlgeschlagen. Markiere und kopiere den Wert manuell.",
  "Copy token": "Token kopieren",
  "Enter a new company API key.": "Gib einen neuen API-Schlüssel für die Firma ein.",
  "External agents · MCP": "Externe Agenten · MCP",
  "Fixed chat model": "Festes Chat-Modell",
  "Hide token secret": "Token-Schlüssel ausblenden",
  "Includes approval and execution": "Einschließlich Freigabe und Ausführung",
  "Keep the stored company key.": "Gespeicherten Firmenschlüssel beibehalten.",
  "Last used": "Zuletzt verwendet",
  "Leave the key empty to keep the stored company key.":
    "Lass das Schlüsselfeld leer, um den gespeicherten Firmenschlüssel beizubehalten.",
  "MCP endpoint": "MCP-Endpunkt",
  "MCP token created.": "MCP-Token erstellt.",
  "MCP token revoked.": "MCP-Token widerrufen.",
  "MCP tokens give external agents access to this company. Permissions apply to the selected tools.":
    "MCP-Tokens geben externen Agenten Zugriff auf diese Firma. Berechtigungen gelten für die ausgewählten Werkzeuge.",
  Never: "Nie",
  "New MCP token": "Neuer MCP-Token",
  "New MCP token secret": "Neuer MCP-Token-Schlüssel",
  "No matching tools.": "Keine passenden Werkzeuge.",
  "Other provider settings are stored, but Ask Reality currently uses managed AI or a company Anthropic key.":
    "Andere Anbieter-Einstellungen sind gespeichert. Ask Reality verwendet derzeit jedoch verwaltete AI oder einen eigenen Anthropic-Schlüssel.",
  "Remove the company key and use deployment-managed AI.":
    "Firmenschlüssel entfernen und die für diese Installation verwaltete AI verwenden.",
  "Replace the company key with the new key.":
    "Firmenschlüssel durch den neuen Schlüssel ersetzen.",
  "Review AI setup": "AI-Einrichtung prüfen",
  "Review token": "Token prüfen",
  "Review token revocation": "Token-Widerruf prüfen",
  "Search tools": "Werkzeuge suchen",
  "Select read tools": "Lesewerkzeuge auswählen",
  "selected tools": "ausgewählte Werkzeuge",
  "The result needs checking. No change will be sent again automatically.":
    "Das Ergebnis muss geprüft werden. Keine Änderung wird automatisch erneut gesendet.",
  "This token may approve and execute changes through its selected tools.":
    "Dieser Token darf über seine ausgewählten Werkzeuge Änderungen freigeben und ausführen.",
  "This token will no longer authorize new MCP requests.":
    "Dieser Token berechtigt nicht mehr zu neuen MCP-Anfragen.",
  "Token name": "Token-Name",
  "Tokens remain active until revoked. Removing an owner's membership does not revoke their company tokens.":
    "Tokens bleiben bis zum Widerruf aktiv. Das Entfernen einer Eigentümer-Mitgliedschaft widerruft deren Firmen-Tokens nicht.",
  "Prepare changes": "Änderungen vorbereiten",
  "Approve and execute": "Freigeben und ausführen",
  "Could not complete the request. Check the current settings before trying again.":
    "Die Anfrage konnte nicht abgeschlossen werden. Prüfe vor einem neuen Versuch die aktuellen Einstellungen.",
  "Current AI settings loaded. This is not a receipt for the previous request.":
    "Aktuelle AI-Einstellungen geladen. Dies ist kein Ausführungsnachweis für die vorherige Anfrage.",
  "The change was rejected. Review the current settings and enter credentials again if needed.":
    "Die Änderung wurde abgelehnt. Prüfe die aktuellen Einstellungen und gib Zugangsdaten bei Bedarf erneut ein.",
});

Object.assign(dictionaries.nl, {
  "A token secret cannot be recovered. Inspect active tokens and revoke an unwanted token before creating a replacement.":
    "Een tokengeheim kan niet worden hersteld. Controleer actieve tokens en trek een ongewenst token in voordat je een vervanging maakt.",
  "Active MCP tokens": "Actieve MCP-tokens",
  "AI credential source": "AI-toegang",
  "AI settings are unavailable.": "AI-instellingen zijn niet beschikbaar.",
  "AI setup saved.": "AI-instellingen opgeslagen.",
  "All current and future tools": "Alle huidige en toekomstige tools",
  "Change AI setup": "AI-instellingen wijzigen",
  "Check saved AI settings": "Opgeslagen AI-instellingen controleren",
  "Choose exact tools. No permissions are selected by default.":
    "Kies afzonderlijke tools. Er zijn standaard geen rechten geselecteerd.",
  "Clear selection": "Selectie wissen",
  "Company Anthropic key": "Eigen Anthropic-sleutel",
  "Copy failed. Select and copy the value manually.":
    "Kopiëren mislukt. Selecteer en kopieer de waarde handmatig.",
  "Copy token": "Token kopiëren",
  "Enter a new company API key.": "Voer een nieuwe API-sleutel voor het bedrijf in.",
  "External agents · MCP": "Externe agents · MCP",
  "Fixed chat model": "Vast chatmodel",
  "Hide token secret": "Tokengeheim verbergen",
  "Includes approval and execution": "Inclusief goedkeuring en uitvoering",
  "Keep the stored company key.": "Opgeslagen bedrijfssleutel behouden.",
  "Last used": "Laatst gebruikt",
  "Leave the key empty to keep the stored company key.":
    "Laat het sleutelveld leeg om de opgeslagen bedrijfssleutel te behouden.",
  "MCP endpoint": "MCP-eindpunt",
  "MCP token created.": "MCP-token aangemaakt.",
  "MCP token revoked.": "MCP-token ingetrokken.",
  "MCP tokens give external agents access to this company. Permissions apply to the selected tools.":
    "MCP-tokens geven externe agents toegang tot dit bedrijf. Rechten gelden voor de geselecteerde tools.",
  Never: "Nooit",
  "New MCP token": "Nieuw MCP-token",
  "New MCP token secret": "Nieuw MCP-tokengeheim",
  "No matching tools.": "Geen overeenkomende tools.",
  "Other provider settings are stored, but Ask Reality currently uses managed AI or a company Anthropic key.":
    "Andere providerinstellingen zijn opgeslagen, maar Ask Reality gebruikt momenteel beheerde AI of een eigen Anthropic-sleutel.",
  "Remove the company key and use deployment-managed AI.":
    "Bedrijfssleutel verwijderen en de voor deze installatie beheerde AI gebruiken.",
  "Replace the company key with the new key.": "Bedrijfssleutel vervangen door de nieuwe sleutel.",
  "Review AI setup": "AI-instellingen controleren",
  "Review token": "Token controleren",
  "Review token revocation": "Intrekking van token controleren",
  "Search tools": "Tools zoeken",
  "Select read tools": "Leestools selecteren",
  "selected tools": "geselecteerde tools",
  "The result needs checking. No change will be sent again automatically.":
    "Het resultaat moet worden gecontroleerd. Geen wijziging wordt automatisch opnieuw verzonden.",
  "This token may approve and execute changes through its selected tools.":
    "Dit token mag via de geselecteerde tools wijzigingen goedkeuren en uitvoeren.",
  "This token will no longer authorize new MCP requests.":
    "Dit token geeft geen toestemming meer voor nieuwe MCP-verzoeken.",
  "Token name": "Tokennaam",
  "Tokens remain active until revoked. Removing an owner's membership does not revoke their company tokens.":
    "Tokens blijven actief tot ze worden ingetrokken. Het verwijderen van het lidmaatschap van een eigenaar trekt diens bedrijfstokens niet in.",
  "Prepare changes": "Wijzigingen voorbereiden",
  "Approve and execute": "Goedkeuren en uitvoeren",
  "Could not complete the request. Check the current settings before trying again.":
    "Het verzoek kon niet worden voltooid. Controleer de huidige instellingen voordat je het opnieuw probeert.",
  "Current AI settings loaded. This is not a receipt for the previous request.":
    "Huidige AI-instellingen geladen. Dit is geen uitvoeringsbewijs voor het vorige verzoek.",
  "The change was rejected. Review the current settings and enter credentials again if needed.":
    "De wijziging is afgewezen. Controleer de huidige instellingen en voer zo nodig de inloggegevens opnieuw in.",
});

Object.assign(dictionaries.es, {
  "A token secret cannot be recovered. Inspect active tokens and revoke an unwanted token before creating a replacement.":
    "El secreto de un token no se puede recuperar. Revisa los tokens activos y revoca el que no necesites antes de crear otro.",
  "Active MCP tokens": "Tokens MCP activos",
  "AI credential source": "Acceso de IA",
  "AI settings are unavailable.": "La configuración de IA no está disponible.",
  "AI setup saved.": "Configuración de IA guardada.",
  "All current and future tools": "Todas las herramientas actuales y futuras",
  "Change AI setup": "Cambiar configuración de IA",
  "Check saved AI settings": "Comprobar configuración de IA guardada",
  "Choose exact tools. No permissions are selected by default.":
    "Selecciona herramientas concretas. No hay permisos seleccionados por defecto.",
  "Clear selection": "Borrar selección",
  "Company Anthropic key": "Clave de Anthropic de la empresa",
  "Copy failed. Select and copy the value manually.":
    "No se pudo copiar. Selecciona y copia el valor manualmente.",
  "Copy token": "Copiar token",
  "Enter a new company API key.": "Introduce una nueva clave API de la empresa.",
  "External agents · MCP": "Agentes externos · MCP",
  "Fixed chat model": "Modelo de chat fijo",
  "Hide token secret": "Ocultar secreto del token",
  "Includes approval and execution": "Incluye aprobación y ejecución",
  "Keep the stored company key.": "Conservar la clave guardada de la empresa.",
  "Last used": "Último uso",
  "Leave the key empty to keep the stored company key.":
    "Deja la clave vacía para conservar la clave guardada de la empresa.",
  "MCP endpoint": "Punto de acceso MCP",
  "MCP token created.": "Token MCP creado.",
  "MCP token revoked.": "Token MCP revocado.",
  "MCP tokens give external agents access to this company. Permissions apply to the selected tools.":
    "Los tokens MCP dan acceso a esta empresa a agentes externos. Los permisos se aplican a las herramientas seleccionadas.",
  Never: "Nunca",
  "New MCP token": "Nuevo token MCP",
  "New MCP token secret": "Secreto del nuevo token MCP",
  "No matching tools.": "No hay herramientas coincidentes.",
  "Other provider settings are stored, but Ask Reality currently uses managed AI or a company Anthropic key.":
    "Hay otros proveedores guardados, pero Ask Reality utiliza actualmente IA gestionada o una clave de Anthropic de la empresa.",
  "Remove the company key and use deployment-managed AI.":
    "Eliminar la clave de la empresa y usar la IA gestionada de esta instalación.",
  "Replace the company key with the new key.":
    "Sustituir la clave de la empresa por la nueva clave.",
  "Review AI setup": "Revisar configuración de IA",
  "Review token": "Revisar token",
  "Review token revocation": "Revisar revocación del token",
  "Search tools": "Buscar herramientas",
  "Select read tools": "Seleccionar herramientas de lectura",
  "selected tools": "herramientas seleccionadas",
  "The result needs checking. No change will be sent again automatically.":
    "Hay que comprobar el resultado. Ningún cambio se volverá a enviar automáticamente.",
  "This token may approve and execute changes through its selected tools.":
    "Este token puede aprobar y ejecutar cambios mediante las herramientas seleccionadas.",
  "This token will no longer authorize new MCP requests.":
    "Este token dejará de autorizar nuevas solicitudes MCP.",
  "Token name": "Nombre del token",
  "Tokens remain active until revoked. Removing an owner's membership does not revoke their company tokens.":
    "Los tokens permanecen activos hasta su revocación. Eliminar la membresía de un propietario no revoca sus tokens de empresa.",
  "Prepare changes": "Preparar cambios",
  "Approve and execute": "Aprobar y ejecutar",
  "Could not complete the request. Check the current settings before trying again.":
    "No se pudo completar la solicitud. Comprueba la configuración actual antes de intentarlo de nuevo.",
  "Current AI settings loaded. This is not a receipt for the previous request.":
    "Configuración actual de IA cargada. Esto no es un comprobante de la solicitud anterior.",
  "The change was rejected. Review the current settings and enter credentials again if needed.":
    "El cambio fue rechazado. Revisa la configuración actual y vuelve a introducir las credenciales si es necesario.",
});

Object.assign(dictionaries.de, {
  "Stored provider details": "Gespeicherte Anbieter-Details",
  Endpoint: "Endpunkt",
});

Object.assign(dictionaries.nl, {
  "Stored provider details": "Opgeslagen providergegevens",
  Endpoint: "Eindpunt",
});

Object.assign(dictionaries.es, {
  "Stored provider details": "Detalles del proveedor guardado",
  Endpoint: "Punto de acceso",
});

Object.assign(dictionaries.de, {
  "Record opening stock": "Anfangsbestand erfassen",
  "Add stock already held when starting.": "Bereits vorhandenen Bestand zum Start erfassen.",
  "Opening stock adds to the recorded stock. It does not set a target balance.":
    "Anfangsbestand wird zum erfassten Bestand addiert. Er setzt keinen Zielbestand.",
  "Quantity to add": "Menge hinzufügen",
  "Occurrence time (optional)": "Zeitpunkt (optional)",
  "Occurrence time": "Zeitpunkt",
  "Time uses this device’s timezone. Leave blank to use the booking time.":
    "Die Zeit gilt in der Zeitzone dieses Geräts. Leer lassen, um den Buchungszeitpunkt zu verwenden.",
  "For stocked items without lot or serial tracking.":
    "Für Lagerartikel ohne Chargen- oder Seriennummern.",
  "Preparation outcome is unknown. Recover the same request before starting another.":
    "Das Ergebnis der Vorbereitung ist unbekannt. Stelle dieselbe Anfrage wieder her, bevor du eine neue startest.",
  "Recover review": "Prüfung wiederherstellen",
  "At confirmation": "Bei Bestätigung",
  "Reviewed stock effect": "Geprüfte Bestandsänderung",
  "Reserved stock stays unchanged": "Reservierter Bestand bleibt unverändert",
  "Confirm opening stock": "Anfangsbestand bestätigen",
  "Discard proposal": "Vorschlag verwerfen",
  "The outcome needs checking. Do not record the stock again.":
    "Das Ergebnis muss geprüft werden. Erfasse den Bestand nicht erneut.",
  "Recover recorded result": "Gebuchtes Ergebnis wiederherstellen",
  "Proposal discarded. No stock was recorded.":
    "Vorschlag verworfen. Es wurde kein Bestand gebucht.",
  "Opening stock recorded": "Anfangsbestand gebucht",
  "Current physical stock": "Aktueller physischer Bestand",
  "This is a manual declaration. Its movement and event provide the audit trail.":
    "Dies ist eine manuelle Erfassung. Warenbewegung und Ereignis dokumentieren die Buchung.",
  "Inspect movement": "Warenbewegung prüfen",
  "Inspect event": "Ereignis prüfen",
  "Refine your search to find more records.":
    "Grenze die Suche ein, um weitere Einträge zu finden.",
  "The stock context changed. Prepare a fresh review.":
    "Der Bestandskontext hat sich geändert. Verwirf den Vorschlag und bereite eine neue Prüfung vor.",
  "An overlapping stock action is unresolved. Check its outcome first.":
    "Eine überschneidende Bestandsaktion ist ungeklärt. Prüfe zuerst ihr Ergebnis.",
  "This opening stock form supports items without lot or serial tracking.":
    "Dieses Formular unterstützt Artikel ohne Chargen- oder Seriennummern.",
  "Opening quantity supports at most 14 integer and 4 decimal places.":
    "Die Menge darf höchstens 14 Vor- und 4 Nachkommastellen haben.",
  "Enter a valid positive quantity.": "Gib eine gültige positive Menge ein.",
});

Object.assign(dictionaries.nl, {
  "Record opening stock": "Beginvoorraad vastleggen",
  "Add stock already held when starting.": "Leg voorraad vast die bij de start al aanwezig is.",
  "Opening stock adds to the recorded stock. It does not set a target balance.":
    "Beginvoorraad wordt bij de vastgelegde voorraad opgeteld. Er wordt geen doelvoorraad ingesteld.",
  "Quantity to add": "Toe te voegen hoeveelheid",
  "Occurrence time (optional)": "Tijdstip (optioneel)",
  "Occurrence time": "Tijdstip",
  "Time uses this device’s timezone. Leave blank to use the booking time.":
    "De tijdzone van dit apparaat wordt gebruikt. Laat leeg voor het boekingstijdstip.",
  "For stocked items without lot or serial tracking.":
    "Voor voorraadartikelen zonder partij- of serienummerregistratie.",
  "Preparation outcome is unknown. Recover the same request before starting another.":
    "Het resultaat van de voorbereiding is onbekend. Herstel hetzelfde verzoek voordat je een nieuw verzoek start.",
  "Recover review": "Controle herstellen",
  "At confirmation": "Bij bevestiging",
  "Reviewed stock effect": "Gecontroleerde voorraadwijziging",
  "Reserved stock stays unchanged": "Gereserveerde voorraad blijft ongewijzigd",
  "Confirm opening stock": "Beginvoorraad bevestigen",
  "Discard proposal": "Voorstel verwerpen",
  "The outcome needs checking. Do not record the stock again.":
    "Het resultaat moet worden gecontroleerd. Leg de voorraad niet opnieuw vast.",
  "Recover recorded result": "Vastgelegd resultaat herstellen",
  "Proposal discarded. No stock was recorded.": "Voorstel verworpen. Er is geen voorraad geboekt.",
  "Opening stock recorded": "Beginvoorraad vastgelegd",
  "Current physical stock": "Huidige fysieke voorraad",
  "This is a manual declaration. Its movement and event provide the audit trail.":
    "Dit is een handmatige opgave. De goederenbeweging en gebeurtenis documenteren de boeking.",
  "Inspect movement": "Goederenbeweging inspecteren",
  "Inspect event": "Gebeurtenis inspecteren",
  "Refine your search to find more records.": "Verfijn je zoekopdracht om meer records te vinden.",
  "The stock context changed. Prepare a fresh review.":
    "De voorraadcontext is gewijzigd. Verwerp het voorstel en bereid een nieuwe controle voor.",
  "An overlapping stock action is unresolved. Check its outcome first.":
    "Een overlappende voorraadactie is nog onduidelijk. Controleer eerst het resultaat.",
  "This opening stock form supports items without lot or serial tracking.":
    "Dit formulier ondersteunt artikelen zonder partij- of serienummerregistratie.",
  "Opening quantity supports at most 14 integer and 4 decimal places.":
    "De hoeveelheid mag maximaal 14 gehele cijfers en 4 decimalen hebben.",
  "Enter a valid positive quantity.": "Voer een geldige positieve hoeveelheid in.",
});

Object.assign(dictionaries.es, {
  "Record opening stock": "Registrar existencias iniciales",
  "Add stock already held when starting.": "Registrar las existencias disponibles al comenzar.",
  "Opening stock adds to the recorded stock. It does not set a target balance.":
    "Las existencias iniciales se suman a las registradas. No establecen un saldo objetivo.",
  "Quantity to add": "Cantidad a añadir",
  "Occurrence time (optional)": "Fecha y hora (opcional)",
  "Occurrence time": "Fecha y hora",
  "Time uses this device’s timezone. Leave blank to use the booking time.":
    "Se utiliza la zona horaria de este dispositivo. Dejar vacío para usar el momento del registro.",
  "For stocked items without lot or serial tracking.":
    "Para artículos de almacén sin seguimiento por lote ni número de serie.",
  "Preparation outcome is unknown. Recover the same request before starting another.":
    "Se desconoce el resultado de la preparación. Recupera la misma solicitud antes de iniciar otra.",
  "Recover review": "Recuperar revisión",
  "At confirmation": "Al confirmar",
  "Reviewed stock effect": "Cambio de existencias revisado",
  "Reserved stock stays unchanged": "Las existencias reservadas no cambian",
  "Confirm opening stock": "Confirmar existencias iniciales",
  "Discard proposal": "Descartar propuesta",
  "The outcome needs checking. Do not record the stock again.":
    "Es necesario comprobar el resultado. No vuelvas a registrar las existencias.",
  "Recover recorded result": "Recuperar resultado registrado",
  "Proposal discarded. No stock was recorded.":
    "Propuesta descartada. No se registraron existencias.",
  "Opening stock recorded": "Existencias iniciales registradas",
  "Current physical stock": "Existencias físicas actuales",
  "This is a manual declaration. Its movement and event provide the audit trail.":
    "Esta es una declaración manual. Su movimiento y evento documentan el registro.",
  "Inspect movement": "Inspeccionar movimiento",
  "Inspect event": "Inspeccionar evento",
  "Refine your search to find more records.": "Afina la búsqueda para encontrar más registros.",
  "The stock context changed. Prepare a fresh review.":
    "El contexto de existencias ha cambiado. Descarta la propuesta y prepara una nueva revisión.",
  "An overlapping stock action is unresolved. Check its outcome first.":
    "Una acción de existencias coincidente está sin resolver. Comprueba primero su resultado.",
  "This opening stock form supports items without lot or serial tracking.":
    "Este formulario admite artículos sin seguimiento por lote ni número de serie.",
  "Opening quantity supports at most 14 integer and 4 decimal places.":
    "La cantidad admite como máximo 14 cifras enteras y 4 decimales.",
  "Enter a valid positive quantity.": "Introduce una cantidad positiva válida.",
});

Object.assign(dictionaries.de, { "Check status": "Status prüfen" });
Object.assign(dictionaries.nl, { "Check status": "Status controleren" });
Object.assign(dictionaries.es, { "Check status": "Comprobar estado" });

Object.assign(dictionaries.de, {
  "Place customer delivery hold": "Kundenlieferungen sperren",
  "Release customer delivery hold": "Kundensperre freigeben",
  "Customer delivery holds": "Kundensperren",
  "Pause shipments for this customer’s current and future deliveries.":
    "Stoppt Versandbuchungen für aktuelle und zukünftige Lieferungen dieses Kunden.",
  "Release this customer’s shipment hold. Individual delivery holds still apply.":
    "Gibt die Versandsperre dieses Kunden frei. Sperren einzelner Lieferungen bleiben bestehen.",
  "Existing reservations stay unchanged; new reservations remain allowed. Stock and money stay unchanged.":
    "Reservierungen bleiben möglich. Bestand, bestehende Reservierungen und Geldbeträge bleiben unverändert.",
  "Search customers": "Kunden suchen",
  "This customer already has a delivery hold.": "Dieser Kunde hat bereits eine Liefersperre.",
  "This customer has no active delivery hold.": "Dieser Kunde hat keine aktive Liefersperre.",
  "Confirm customer hold": "Kundensperre bestätigen",
  "Confirm customer hold release": "Freigabe der Kundensperre bestätigen",
  "The hold action needs checking. Do not repeat it.":
    "Das Ergebnis der Sperraktion muss geprüft werden. Wiederhole sie nicht.",
  "Proposal discarded. The hold was not changed.":
    "Vorschlag verworfen. Die Sperre wurde nicht geändert.",
  "Customer hold recorded": "Kundensperre erfasst",
  "Customer hold released": "Kundensperre freigegeben",
  "Inspect customer": "Kunden prüfen",
  "Current customer holds": "Aktuelle Kundensperren",
  "The recorded result remains in history. Current holds may have changed since then.":
    "Das erfasste Ergebnis bleibt im Verlauf. Aktuelle Sperren können sich seitdem geändert haben.",
  "Check the customer hold fields.": "Prüfe die Angaben zur Kundensperre.",
  "Choose a customer.": "Wähle einen Kunden.",
  "An action affecting this customer’s shipment hold is unresolved. Check its outcome first.":
    "Eine Aktion zur Versandsperre dieses Kunden ist ungeklärt. Prüfe zuerst ihr Ergebnis.",
  "The customer hold changed. Prepare a fresh review.":
    "Die Kundensperre hat sich geändert. Verwirf den Vorschlag und bereite eine neue Prüfung vor.",
});

Object.assign(dictionaries.nl, {
  "Place customer delivery hold": "Klantleveringen blokkeren",
  "Release customer delivery hold": "Klantblokkade vrijgeven",
  "Customer delivery holds": "Klantblokkades",
  "Pause shipments for this customer’s current and future deliveries.":
    "Blokkeert verzendingen voor huidige en toekomstige leveringen van deze klant.",
  "Release this customer’s shipment hold. Individual delivery holds still apply.":
    "Geeft de verzendblokkade van deze klant vrij. Blokkades van afzonderlijke leveringen blijven gelden.",
  "Existing reservations stay unchanged; new reservations remain allowed. Stock and money stay unchanged.":
    "Reserveringen blijven toegestaan. Voorraad, bestaande reserveringen en geldbedragen blijven ongewijzigd.",
  "Search customers": "Klanten zoeken",
  "This customer already has a delivery hold.": "Deze klant heeft al een leveringsblokkade.",
  "This customer has no active delivery hold.": "Deze klant heeft geen actieve leveringsblokkade.",
  "Confirm customer hold": "Klantblokkade bevestigen",
  "Confirm customer hold release": "Vrijgave van klantblokkade bevestigen",
  "The hold action needs checking. Do not repeat it.":
    "Het resultaat van de blokkadeactie moet worden gecontroleerd. Herhaal de actie niet.",
  "Proposal discarded. The hold was not changed.":
    "Voorstel verworpen. De blokkade is niet gewijzigd.",
  "Customer hold recorded": "Klantblokkade vastgelegd",
  "Customer hold released": "Klantblokkade vrijgegeven",
  "Inspect customer": "Klant inspecteren",
  "Current customer holds": "Huidige klantblokkades",
  "The recorded result remains in history. Current holds may have changed since then.":
    "Het vastgelegde resultaat blijft in de historie. Huidige blokkades kunnen sindsdien zijn gewijzigd.",
  "Check the customer hold fields.": "Controleer de velden van de klantblokkade.",
  "Choose a customer.": "Kies een klant.",
  "An action affecting this customer’s shipment hold is unresolved. Check its outcome first.":
    "Een actie rond de verzendblokkade van deze klant is onduidelijk. Controleer eerst het resultaat.",
  "The customer hold changed. Prepare a fresh review.":
    "De klantblokkade is gewijzigd. Verwerp het voorstel en bereid een nieuwe controle voor.",
});

Object.assign(dictionaries.es, {
  "Place customer delivery hold": "Bloquear entregas del cliente",
  "Release customer delivery hold": "Liberar bloqueo del cliente",
  "Customer delivery holds": "Bloqueos del cliente",
  "Pause shipments for this customer’s current and future deliveries.":
    "Bloquea los envíos de las entregas actuales y futuras de este cliente.",
  "Release this customer’s shipment hold. Individual delivery holds still apply.":
    "Libera el bloqueo de envíos de este cliente. Se mantienen los bloqueos de entregas individuales.",
  "Existing reservations stay unchanged; new reservations remain allowed. Stock and money stay unchanged.":
    "Las reservas siguen permitidas. Las existencias, reservas actuales e importes no cambian.",
  "Search customers": "Buscar clientes",
  "This customer already has a delivery hold.": "Este cliente ya tiene un bloqueo de entregas.",
  "This customer has no active delivery hold.":
    "Este cliente no tiene un bloqueo de entregas activo.",
  "Confirm customer hold": "Confirmar bloqueo del cliente",
  "Confirm customer hold release": "Confirmar liberación del bloqueo",
  "The hold action needs checking. Do not repeat it.":
    "Es necesario comprobar la acción de bloqueo. No la repitas.",
  "Proposal discarded. The hold was not changed.": "Propuesta descartada. El bloqueo no cambió.",
  "Customer hold recorded": "Bloqueo del cliente registrado",
  "Customer hold released": "Bloqueo del cliente liberado",
  "Inspect customer": "Inspeccionar cliente",
  "Current customer holds": "Bloqueos actuales del cliente",
  "The recorded result remains in history. Current holds may have changed since then.":
    "El resultado registrado permanece en el historial. Los bloqueos actuales pueden haber cambiado desde entonces.",
  "Check the customer hold fields.": "Comprueba los campos del bloqueo del cliente.",
  "Choose a customer.": "Selecciona un cliente.",
  "An action affecting this customer’s shipment hold is unresolved. Check its outcome first.":
    "Hay una acción pendiente de resolver sobre el bloqueo de envíos de este cliente. Comprueba primero su resultado.",
  "The customer hold changed. Prepare a fresh review.":
    "El bloqueo del cliente ha cambiado. Descarta la propuesta y prepara una nueva revisión.",
});

Object.assign(dictionaries.de, {
  "Action ID": "Aktions-ID",
  "Activity could not be loaded.": "Der Verlauf konnte nicht geladen werden.",
  "All time": "Gesamter Zeitraum",
  "Attention event": "Ereignis mit Prüfbedarf",
  "Attention events only": "Nur Ereignisse mit Prüfbedarf",
  "Business document recorded": "Geschäftsbeleg erfasst",
  "Business partner created": "Geschäftspartner angelegt",
  "Causation ID": "Auslöser-ID",
  "Correlation ID": "Zusammenhangs-ID",
  "Business partner delivery hold placed": "Liefersperre für Geschäftspartner gesetzt",
  "Business partner delivery hold released": "Liefersperre für Geschäftspartner aufgehoben",
  "Customer, item, reference or event": "Kunde, Artikel, Referenz oder Ereignis",
  "Delivery commitment changed": "Lieferverpflichtung geändert",
  "Delivery commitment created": "Lieferverpflichtung angelegt",
  "Delivery commitment fulfilled": "Lieferverpflichtung erfüllt",
  "Delivery hold placed": "Liefersperre gesetzt",
  "Delivery hold released": "Liefersperre aufgehoben",
  "End of matching activity.": "Ende des passenden Verlaufs.",
  "Event ID": "Ereignis-ID",
  "Event time": "Ereigniszeit",
  "Financial posting reversed": "Finanzbuchung storniert",
  "Inventory movement corrected": "Bestandsbewegung korrigiert",
  "Inventory movement recorded": "Bestandsbewegung erfasst",
  "Inventory reservation consumed": "Bestandsreservierung verbraucht",
  "Inventory reservation released": "Bestandsreservierung freigegeben",
  "Inventory reserved": "Bestand reserviert",
  "Item created": "Artikel angelegt",
  "Ledger entry recorded": "Finanzeintrag erfasst",
  "Loading activity…": "Verlauf wird geladen…",
  "Location created": "Lagerort angelegt",
  "Older activity could not be loaded.": "Ältere Ereignisse konnten nicht geladen werden.",
  "Open related record": "Verknüpften Datensatz öffnen",
  "Payment allocation recorded": "Zahlungszuordnung erfasst",
  "Period uses event time. Attention describes the event, not the current case status.":
    "Der Zeitraum gilt für die Ereigniszeit. Prüfbedarf bezieht sich auf das Ereignis, nicht auf den aktuellen Vorgangsstatus.",
  "Recorded at": "Erfasst am",
  "Search activity": "Verlauf durchsuchen",
  "Source needs mapping": "Quelle benötigt Zuordnung",
  "Source processing completed": "Quellenverarbeitung abgeschlossen",
  "Source received": "Quelle empfangen",
  "Source recorded by confirmed action": "Quelle durch bestätigte Aktion erfasst",
  "What was recorded across your business. Newest recordings first.":
    "Was in deinem Unternehmen erfasst wurde. Neueste Einträge zuerst.",
});

Object.assign(dictionaries.nl, {
  "Action ID": "Actie-ID",
  "Activity could not be loaded.": "De activiteit kon niet worden geladen.",
  "All time": "Alle perioden",
  "Attention event": "Gebeurtenis met aandachtspunt",
  "Attention events only": "Alleen gebeurtenissen met aandachtspunten",
  "Business document recorded": "Bedrijfsdocument vastgelegd",
  "Business partner created": "Zakenpartner aangemaakt",
  "Causation ID": "Aanleiding-ID",
  "Correlation ID": "Verband-ID",
  "Business partner delivery hold placed": "Leveringsblokkade voor zakenpartner ingesteld",
  "Business partner delivery hold released": "Leveringsblokkade voor zakenpartner opgeheven",
  "Customer, item, reference or event": "Klant, artikel, referentie of gebeurtenis",
  "Delivery commitment changed": "Leveringsverplichting gewijzigd",
  "Delivery commitment created": "Leveringsverplichting aangemaakt",
  "Delivery commitment fulfilled": "Leveringsverplichting vervuld",
  "Delivery hold placed": "Leveringsblokkade ingesteld",
  "Delivery hold released": "Leveringsblokkade opgeheven",
  "End of matching activity.": "Einde van de overeenkomende activiteit.",
  "Event ID": "Gebeurtenis-ID",
  "Event time": "Tijd van gebeurtenis",
  "Financial posting reversed": "Financiële boeking teruggeboekt",
  "Inventory movement corrected": "Voorraadbeweging gecorrigeerd",
  "Inventory movement recorded": "Voorraadbeweging vastgelegd",
  "Inventory reservation consumed": "Voorraadreservering verbruikt",
  "Inventory reservation released": "Voorraadreservering vrijgegeven",
  "Inventory reserved": "Voorraad gereserveerd",
  "Item created": "Artikel aangemaakt",
  "Ledger entry recorded": "Financiële journaalregel vastgelegd",
  "Loading activity…": "Activiteit laden…",
  "Location created": "Locatie aangemaakt",
  "Older activity could not be loaded.": "Oudere activiteit kon niet worden geladen.",
  "Open related record": "Gekoppeld record openen",
  "Payment allocation recorded": "Betalingstoewijzing vastgelegd",
  "Period uses event time. Attention describes the event, not the current case status.":
    "De periode geldt voor de gebeurtenistijd. Aandacht beschrijft de gebeurtenis, niet de huidige dossierstatus.",
  "Recorded at": "Vastgelegd op",
  "Search activity": "Activiteit doorzoeken",
  "Source needs mapping": "Bron vereist toewijzing",
  "Source processing completed": "Bronverwerking voltooid",
  "Source received": "Bron ontvangen",
  "Source recorded by confirmed action": "Bron vastgelegd door bevestigde actie",
  "What was recorded across your business. Newest recordings first.":
    "Wat in je bedrijf is vastgelegd. Nieuwste registraties eerst.",
});

Object.assign(dictionaries.es, {
  "Action ID": "ID de acción",
  "Activity could not be loaded.": "No se pudo cargar la actividad.",
  "All time": "Todo el período",
  "Attention event": "Evento que requiere atención",
  "Attention events only": "Solo eventos que requieren atención",
  "Business document recorded": "Documento comercial registrado",
  "Business partner created": "Socio comercial creado",
  "Causation ID": "ID del evento causante",
  "Correlation ID": "ID de correlación",
  "Business partner delivery hold placed": "Bloqueo de entrega del socio comercial aplicado",
  "Business partner delivery hold released": "Bloqueo de entrega del socio comercial liberado",
  "Customer, item, reference or event": "Cliente, artículo, referencia o evento",
  "Delivery commitment changed": "Compromiso de entrega modificado",
  "Delivery commitment created": "Compromiso de entrega creado",
  "Delivery commitment fulfilled": "Compromiso de entrega cumplido",
  "Delivery hold placed": "Bloqueo de entrega aplicado",
  "Delivery hold released": "Bloqueo de entrega liberado",
  "End of matching activity.": "Fin de la actividad coincidente.",
  "Event ID": "ID del evento",
  "Event time": "Hora del evento",
  "Financial posting reversed": "Asiento financiero revertido",
  "Inventory movement corrected": "Movimiento de existencias corregido",
  "Inventory movement recorded": "Movimiento de existencias registrado",
  "Inventory reservation consumed": "Reserva de existencias consumida",
  "Inventory reservation released": "Reserva de existencias liberada",
  "Inventory reserved": "Existencias reservadas",
  "Item created": "Artículo creado",
  "Ledger entry recorded": "Apunte contable registrado",
  "Loading activity…": "Cargando actividad…",
  "Location created": "Ubicación creada",
  "Older activity could not be loaded.": "No se pudo cargar la actividad anterior.",
  "Open related record": "Abrir registro relacionado",
  "Payment allocation recorded": "Asignación de pago registrada",
  "Period uses event time. Attention describes the event, not the current case status.":
    "El período se aplica a la hora del evento. La atención describe el evento, no el estado actual del caso.",
  "Recorded at": "Registrado el",
  "Search activity": "Buscar actividad",
  "Source needs mapping": "La fuente necesita asignación",
  "Source processing completed": "Procesamiento de la fuente finalizado",
  "Source received": "Fuente recibida",
  "Source recorded by confirmed action": "Fuente registrada por acción confirmada",
  "What was recorded across your business. Newest recordings first.":
    "Lo que se ha registrado en tu empresa. Registros más recientes primero.",
});

Object.assign(dictionaries.de, {
  "Hide chat": "Chat ausblenden",
  "Show chat": "Chat einblenden",
  Reports: "Auswertungen",
});

Object.assign(dictionaries.nl, {
  "Hide chat": "Chat verbergen",
  "Show chat": "Chat tonen",
  Reports: "Rapporten",
});

Object.assign(dictionaries.es, {
  "Hide chat": "Ocultar chat",
  "Show chat": "Mostrar chat",
  Reports: "Informes",
});

Object.assign(dictionaries.de, {
  "Attach text file": "Textdatei anhängen",
  "Attach a text, Markdown, CSV or JSON file (up to 64 KiB)":
    "Text-, Markdown-, CSV- oder JSON-Datei anhängen (bis 64 KiB)",
  "Choose a text, Markdown, CSV or JSON file up to 64 KiB.":
    "Wähle eine Text-, Markdown-, CSV- oder JSON-Datei bis 64 KiB.",
  "Conversation history": "Chatverlauf",
  Dictate: "Diktieren",
  "Dictate using your browser's speech service": "Mit dem Sprachdienst deines Browsers diktieren",
  "Listening… Your words will appear in the draft.":
    "Ich höre zu… Deine Worte erscheinen im Entwurf.",
  "New chat": "Neuer Chat",
  "Put Reality to work…": "Gib Reality eine Aufgabe…",
  "Reality can make mistakes. Check important information.":
    "Reality kann Fehler machen. Prüfe wichtige Informationen.",
  "Stop dictation": "Diktat beenden",
  "This file could not be read as UTF-8 text.":
    "Diese Datei konnte nicht als UTF-8-Text gelesen werden.",
  "Voice input could not start.": "Die Spracheingabe konnte nicht starten.",
  "Voice input is unavailable in this browser.":
    "Spracheingabe ist in diesem Browser nicht verfügbar.",
  "Voice input stopped. Check microphone access or type your message.":
    "Spracheingabe beendet. Prüfe den Mikrofonzugriff oder tippe deine Nachricht.",
  "No conversations yet.": "Noch keine Gespräche.",
});

Object.assign(dictionaries.nl, {
  "Attach text file": "Tekstbestand bijvoegen",
  "Attach a text, Markdown, CSV or JSON file (up to 64 KiB)":
    "Tekst-, Markdown-, CSV- of JSON-bestand bijvoegen (tot 64 KiB)",
  "Choose a text, Markdown, CSV or JSON file up to 64 KiB.":
    "Kies een tekst-, Markdown-, CSV- of JSON-bestand tot 64 KiB.",
  "Conversation history": "Gespreksgeschiedenis",
  Dictate: "Dicteren",
  "Dictate using your browser's speech service": "Dicteren met de spraakdienst van je browser",
  "Listening… Your words will appear in the draft.":
    "Ik luister… Je woorden verschijnen in het concept.",
  "New chat": "Nieuwe chat",
  "Put Reality to work…": "Geef Reality een opdracht…",
  "Reality can make mistakes. Check important information.":
    "Reality kan fouten maken. Controleer belangrijke informatie.",
  "Stop dictation": "Dicteren stoppen",
  "This file could not be read as UTF-8 text.":
    "Dit bestand kon niet als UTF-8-tekst worden gelezen.",
  "Voice input could not start.": "Spraakinvoer kon niet starten.",
  "Voice input is unavailable in this browser.":
    "Spraakinvoer is niet beschikbaar in deze browser.",
  "Voice input stopped. Check microphone access or type your message.":
    "Spraakinvoer gestopt. Controleer de microfoontoegang of typ je bericht.",
  "No conversations yet.": "Nog geen gesprekken.",
});

Object.assign(dictionaries.es, {
  "Attach text file": "Adjuntar archivo de texto",
  "Attach a text, Markdown, CSV or JSON file (up to 64 KiB)":
    "Adjuntar texto, Markdown, CSV o JSON (hasta 64 KiB)",
  "Choose a text, Markdown, CSV or JSON file up to 64 KiB.":
    "Elige un archivo de texto, Markdown, CSV o JSON de hasta 64 KiB.",
  "Conversation history": "Historial de conversaciones",
  Dictate: "Dictar",
  "Dictate using your browser's speech service": "Dictar con el servicio de voz del navegador",
  "Listening… Your words will appear in the draft.":
    "Escuchando… Tus palabras aparecerán en el borrador.",
  "New chat": "Nuevo chat",
  "Put Reality to work…": "Dale una tarea a Reality…",
  "Reality can make mistakes. Check important information.":
    "Reality puede cometer errores. Comprueba la información importante.",
  "Stop dictation": "Detener dictado",
  "This file could not be read as UTF-8 text.": "No se pudo leer este archivo como texto UTF-8.",
  "Voice input could not start.": "No se pudo iniciar la entrada de voz.",
  "Voice input is unavailable in this browser.":
    "La entrada de voz no está disponible en este navegador.",
  "Voice input stopped. Check microphone access or type your message.":
    "Entrada de voz detenida. Comprueba el acceso al micrófono o escribe tu mensaje.",
  "No conversations yet.": "Aún no hay conversaciones.",
});

Object.assign(dictionaries.de, {
  "Keep the message within 4,000 characters.":
    "Eine Nachricht darf höchstens 4.000 Zeichen enthalten.",
  "This file would exceed the 4,000-character message limit.":
    "Mit dieser Datei wäre die Nachricht länger als 4.000 Zeichen.",
});

Object.assign(dictionaries.nl, {
  "Keep the message within 4,000 characters.": "Houd het bericht binnen 4.000 tekens.",
  "This file would exceed the 4,000-character message limit.":
    "Dit bestand zou de berichtlimiet van 4.000 tekens overschrijden.",
});

Object.assign(dictionaries.es, {
  "Keep the message within 4,000 characters.": "Mantén el mensaje dentro de 4.000 caracteres.",
  "This file would exceed the 4,000-character message limit.":
    "Este archivo superaría el límite de 4.000 caracteres por mensaje.",
});

Object.assign(dictionaries.de, {
  "Select current page": "Aktuelle Seite auswählen",
  "Select row": "Zeile auswählen",
  "Selected on this page": "auf dieser Seite ausgewählt",
  "Export selection": "Auswahl exportieren",
});

Object.assign(dictionaries.nl, {
  "Select current page": "Huidige pagina selecteren",
  "Select row": "Rij selecteren",
  "Selected on this page": "geselecteerd op deze pagina",
  "Export selection": "Selectie exporteren",
});

Object.assign(dictionaries.es, {
  "Select current page": "Seleccionar página actual",
  "Select row": "Seleccionar fila",
  "Selected on this page": "seleccionados en esta página",
  "Export selection": "Exportar selección",
});

Object.assign(dictionaries.de, {
  "How does a finding arise?": "Wie entsteht ein Klärfall?",
  "Reality checks the available records for conditions that need attention, such as an overdue delivery or a missing reservation. A finding clears when its underlying cause is resolved.":
    "Reality prüft die vorhandenen Datensätze auf Situationen, die Aufmerksamkeit brauchen – etwa eine überfällige Lieferung oder eine fehlende Reservierung. Ein Klärfall löst sich auf, sobald seine Ursache behoben ist.",
  "View all possible findings": "Alle möglichen Klärfälle ansehen",
  "These are the possible finding types in Reality, not your company’s active findings. Each type requires matching records. Descriptions use the catalog’s original language.":
    "Hier siehst du die möglichen Klärfallarten in Reality, nicht die aktuellen Fälle deines Unternehmens. Sie entstehen nur bei entsprechenden Datensätzen. Die Beschreibungen sind in der Originalsprache des Katalogs.",
});

Object.assign(dictionaries.nl, {
  "How does a finding arise?": "Hoe ontstaat een bevinding?",
  "Reality checks the available records for conditions that need attention, such as an overdue delivery or a missing reservation. A finding clears when its underlying cause is resolved.":
    "Reality controleert beschikbare gegevens op situaties die aandacht vragen, zoals een te late levering of een ontbrekende reservering. Een bevinding verdwijnt zodra de onderliggende oorzaak is opgelost.",
  "View all possible findings": "Alle mogelijke bevindingen bekijken",
  "These are the possible finding types in Reality, not your company’s active findings. Each type requires matching records. Descriptions use the catalog’s original language.":
    "Dit zijn de mogelijke soorten bevindingen in Reality, niet de actieve bevindingen van je bedrijf. Elk type vereist bijpassende gegevens. Beschrijvingen gebruiken de oorspronkelijke taal van de catalogus.",
});

Object.assign(dictionaries.es, {
  "How does a finding arise?": "¿Cómo surge un hallazgo?",
  "Reality checks the available records for conditions that need attention, such as an overdue delivery or a missing reservation. A finding clears when its underlying cause is resolved.":
    "Reality revisa los registros disponibles para detectar situaciones que requieren atención, como una entrega vencida o una reserva pendiente. El hallazgo desaparece cuando se resuelve su causa.",
  "View all possible findings": "Ver todos los posibles hallazgos",
  "These are the possible finding types in Reality, not your company’s active findings. Each type requires matching records. Descriptions use the catalog’s original language.":
    "Estos son los posibles tipos de hallazgos en Reality, no los hallazgos activos de tu empresa. Cada tipo requiere registros correspondientes. Las descripciones usan el idioma original del catálogo.",
});

Object.assign(dictionaries.de, {
  "Add evidence or context": "Nachweise oder Kontext ergänzen",
  "Business question": "Geschäftliche Frage",
  "Catalog definitions": "Katalogdefinitionen",
  "Choose a record from Facts or Reality records to explore its links.":
    "Wähle einen Eintrag aus Fakten oder Reality-Datensätzen, um seine Verbindungen zu sehen.",
  "Choose Fact interpretation": "Als Fact interpretieren",
  Commands: "Befehle",
  "Commands & actions": "Befehle & Aktionen",
  "Context JSON": "Kontext als JSON",
  "Direct links from the selected record. Open a node to continue.":
    "Direkte Verbindungen des gewählten Datensatzes. Öffne einen Knoten, um weiterzugehen.",
  "Supporting records and history": "Nachweise und Verlauf",
  "Execution history": "Ausführungsverlauf",
  "Fact predicates": "Fact-Prädikate",
  "Additional fact rules": "Regeln für zusätzliche Fakten",
  "Inspect records, follow their origins and review the tools that build Reality.":
    "Prüfe Datensätze, verfolge ihre Herkunft und untersuche die Werkzeuge hinter Reality.",
  "Intended use": "Verwendungszweck",
  "New rule": "Neue Regel",
  "No linked records returned.": "Keine verknüpften Datensätze zurückgegeben.",
  "No Web form is registered here. See the command’s supported adapters.":
    "Hier ist kein Webformular hinterlegt. Die unterstützten Zugänge stehen in der Befehlsdefinition.",
  "Only company owners can change rules.": "Nur Unternehmenseigentümer können Regeln ändern.",
  "Open action form": "Aktionsformular öffnen",
  "Open view data": "Daten der Sicht öffnen",
  "Possible finding types, their causes and how they clear.":
    "Mögliche Klärfallarten, ihre Ursachen und ihre Auflösung.",
  "Projections & views": "Projektionen & Sichten",
  "Reality Inspector": "Reality Inspector",
  "Practice companies are not available in this interface. Choose another company.":
    "Übungsunternehmen sind in dieser Oberfläche nicht verfügbar. Wähle ein anderes Unternehmen.",
  "This proposal cannot be reviewed in this interface yet. No change has been made here.":
    "Dieser Vorschlag kann hier noch nicht geprüft werden. Hier wurde keine Änderung vorgenommen.",
  "Understand context": "Kontext verstehen",
  "Facts & origins": "Fakten & Herkunft",
  "Rules & insights": "Regeln & Erkenntnisse",
  "Actions & history": "Aktionen & Verlauf",
  "Operational records & facts": "Operative Datensätze & Fakten",
  "Derived insights": "Abgeleitete Erkenntnisse",
  "What was received? Original values remain unchanged.":
    "Was wurde empfangen? Originalwerte bleiben unverändert.",
  "What does the evidence state? Documents and lines retain their source references.":
    "Was steht im Beleg? Dokumente und Positionen behalten ihren Bezug zur Quelle.",
  "What is recorded? Business commitments, reservations, movements and facts describe the situation.":
    "Was ist erfasst? Zusagen, Reservierungen, Bewegungen und Fakten beschreiben die Geschäftssituation.",
  "What follows from the records? Rules and views derive observations without becoming a new source of truth.":
    "Was ergibt sich daraus? Regeln und Sichten leiten Beobachtungen ab, ohne selbst zur neuen Quelle zu werden.",
  "What can happen next? Existing tools prepare changes for explicit review.":
    "Was ist der nächste Schritt? Bestehende Werkzeuge bereiten Änderungen zur ausdrücklichen Prüfung vor.",
  "Understand the situation, not just one record.": "Verstehe die Situation im Zusammenhang.",
  "Choose a business record. Follow its connections to see what is known, where it comes from and what it means.":
    "Wähle einen Geschäftsvorgang. Folge seinen Verbindungen: Was wissen wir, woher kommt es und was bedeutet es?",
  "How context is built": "Wie Kontext entsteht",
  "This explains the model. The graph below shows only links actually returned for your record.":
    "Das erklärt das Modell. Der Graph darunter zeigt nur tatsächlich gelieferte Verbindungen deines Datensatzes.",
  "Find a business record": "Geschäftsvorgang oder Datensatz suchen",
  "All records": "Alle Datensätze",
  "Customers & suppliers": "Kunden & Lieferanten",
  "Derived insights belong to rules and views; they are not received source values.":
    "Abgeleitete Erkenntnisse gehören zu Regeln und Sichten; sie sind keine empfangenen Quellwerte.",
  "Select a record above to explore its context.":
    "Wähle oben einen Datensatz, um seinen Kontext zu erkunden.",
  "Row density": "Zeilendichte",
  "Updated at": "Aktualisiert am",
  "Edit rule": "Regel bearbeiten",
  "Rule status": "Regelstatus",
  "Select a rule from the list.": "Wähle eine Regel aus der Liste.",
  Draft: "Entwurf",
  "Rule changes require company owner or platform administrator access.":
    "Regeländerungen erfordern Zugriff als Unternehmenseigentümer oder Plattform-Administrator.",
  "This version is active and is applied to matching data.":
    "Diese Version ist aktiv und wird auf passende Daten angewendet.",
  "This draft is not applied. Simulate it before activation.":
    "Dieser Entwurf wird noch nicht angewendet. Simuliere ihn vor der Aktivierung.",
  "This version is disabled and retained for history.":
    "Diese Version ist deaktiviert und bleibt im Verlauf erhalten.",
  "Technical definition": "Technische Definition",
  "Changes create a new draft version. The active version stays unchanged until activation.":
    "Änderungen erzeugen einen neuen Entwurf. Die aktive Version bleibt bis zur Aktivierung unverändert.",

  "Normal rows": "Normal",
  "Table actions": "Tabellenaktionen",
  "About this view": "Über diese Ansicht",
  "Technology & system": "Technik & System",
  "Reality Inspector sections": "Bereiche des Reality Inspectors",
  "Reality records": "Reality-Datensätze",
  "Record graph": "Datensatz-Graph",
  "Records per collection": "Datensätze je Sammlung",
  Result: "Ergebnis",
  "Review recorded events and their supporting records.":
    "Prüfe aufgezeichnete Ereignisse und die zugehörigen Datensätze.",
  "Rule draft": "Regelentwurf",
  "Rule draft JSON": "Regelentwurf als JSON",
  "Rules follow documented questions, evidence, a draft, simulation and explicit activation.":
    "Regeln entstehen aus dokumentierten Fragen und Nachweisen. Es folgen Entwurf, Simulation und bewusste Aktivierung.",
  "Search inspector": "Inspector durchsuchen",
  "Showing up to 100 returned rows.": "Bis zu 100 zurückgegebene Zeilen werden angezeigt.",
  "Register data sources, configure them and open their received records. Registering a source does not connect or synchronize it.":
    "Registriere und konfiguriere Datenquellen oder öffne ihre empfangenen Datensätze. Die Registrierung stellt noch keine Verbindung oder Synchronisierung her.",
  "Find received data and open the unchanged original or its observations. Import status describes processing, not interpretation success.":
    "Suche empfangene Daten und öffne das unveränderte Original oder seine Beobachtungen. Der Importstatus beschreibt die Verarbeitung, nicht den Erfolg der Interpretation.",
  "Find business documents and trace them to their source. Delivery and payment state comes from linked business records.":
    "Suche Belege und verfolge sie bis zu ihrer Quelle. Liefer- und Zahlungsstatus ergeben sich aus verknüpften Geschäftsdaten.",
  "Python code": "Python-Code",
  "View code": "Code ansehen",
  Function: "Funktion",
  "Python source code": "Python-Quellcode",
  "Code preview truncated to 600 lines or 64 KiB.":
    "Code-Vorschau auf 600 Zeilen oder 64 KiB begrenzt.",
  "This action uses the following Python command. The code is shown for reading, not execution.":
    "Diese Action verwendet den folgenden Python-Command. Du kannst den Code hier lesen, aber nicht ausführen.",
  "This view uses the following projection. These Python functions read and calculate its data.":
    "Diese Ansicht verwendet die folgende Projektion. Diese Python-Funktionen lesen und berechnen ihre Daten.",
  "This view reads a register directly. This is its Python read endpoint, not the screen layout.":
    "Diese Ansicht liest direkt aus einem Register. Hier siehst du den Python-Leseendpunkt, nicht den Code für das Bildschirmlayout.",
  "Python functions from the running application. This view does not execute or change the code.":
    "Python-Funktionen aus der laufenden Anwendung. Diese Ansicht führt den Code nicht aus und ändert ihn nicht.",
  Required: "Erforderlich",
  Optional: "Freiwillig",
  "Calculated overview: this combines existing records to answer a business question.":
    "Berechnete Übersicht: Vorhandene Datensätze werden kombiniert, um eine fachliche Frage zu beantworten.",
  "Application view: this presents records or a calculated overview as a screen you can work with.":
    "Anwendungsansicht: Zeigt Datensätze oder eine berechnete Übersicht auf einer Seite, mit der du arbeiten kannst.",
  "Business task: this guides you through the information and confirmation needed to perform an operation.":
    "Fachliche Aufgabe: Führt dich durch die nötigen Eingaben und die Bestätigung einer Aktion.",
  "Application operation: this defines the inputs, processing and results behind a business task.":
    "Anwendungsoperation: Beschreibt Eingaben, Verarbeitung und Ergebnisse hinter einer fachlichen Aufgabe.",
  "Illustrative example": "Beispiel zur Erklärung",
  "100 units in stock minus 30 reserved gives 70 available. These are example numbers, not your company data.":
    "100 Stück auf Lager minus 30 reservierte Stück ergeben 70 verfügbare Stück. Das sind Beispielzahlen, keine Daten deiner Firma.",
  "You confirm a reservation of 5 units for a delivery commitment. The operation creates the reservation; it does not record a shipment.":
    "Du bestätigst eine Reservierung von 5 Stück für eine Lieferzusage. Die Operation legt die Reservierung an; sie bucht noch keinen Versand.",
  "How it works": "So funktioniert es",
  "Data source": "Datenquelle",
  "Data basis": "Datengrundlage",
  "Calculated projection": "Berechnete Projektion",
  "Stored records": "Gespeicherte Datensätze",
  "Required context": "Benötigte Angaben",
  "Application command": "Anwendungsbefehl",
  Confirmation: "Bestätigung",
  "Review a server-generated preview before confirming.":
    "Vor der Bestätigung wird eine vom Server erstellte Vorschau geprüft.",
  "Review the proposed change before confirming.":
    "Die vorgeschlagene Änderung wird vor der Bestätigung geprüft.",
  "Reads from": "Liest aus",
  "Result fields": "Ergebnisfelder",
  "Writes to": "Schreibt in",
  "Used by": "Verwendet von",
  "Updated after": "Aktualisiert nach",
  Returns: "Rückgabe",
  "View implementation": "Implementierung ansehen",
  "View catalog source": "Katalog-Quelldatei ansehen",
  "Open in application": "In Anwendung \u00f6ffnen",
  "A projection is a calculated overview, like an ERP stock report. Example: 100 units in stock minus 30 reserved gives 70 available. It uses existing records and does not create a new stock posting.":
    "Eine Projektion ist eine berechnete Übersicht, ähnlich einem ERP-Bestandsbericht. Beispiel: 100 Stück auf Lager minus 30 reservierte Stück ergeben 70 verfügbare Stück. Sie nutzt vorhandene Datensätze und erzeugt keine neue Lagerbuchung.",
  "A view is a screen or list you work with in the application, like an ERP stock list. It can show a calculated projection or stored records such as items. Several views can use the same projection.":
    "Ein View ist eine Bildschirmansicht oder Liste, mit der du in der Anwendung arbeitest, etwa eine ERP-Bestandsliste. Er zeigt eine berechnete Projektion oder gespeicherte Datensätze wie Artikel. Mehrere Views können dieselbe Projektion nutzen.",
  "An action is a task you want to carry out in the ERP, such as reserving stock for an order. It guides you through the required inputs and confirmation, then uses a command to perform the task.":
    "Eine Action ist eine Aufgabe, die du im ERP erledigen möchtest, zum Beispiel Bestand für einen Auftrag reservieren. Sie führt dich durch die nötigen Eingaben und die Bestätigung und verwendet dann einen Command zur Ausführung.",
  "A command is the application operation behind a task. Example: after you confirm Reserve stock, the reserve command receives the order commitment and quantity and creates the reservation. This catalog describes the inputs and results; some commands only read data.":
    "Ein Command ist die Anwendungsoperation hinter einer Aufgabe. Beispiel: Nach der Bestätigung von „Bestand reservieren“ erhält der Command „reserve“ die Lieferzusage und Menge und legt die Reservierung an. Hier sind Eingaben und Ergebnisse beschrieben; manche Commands lesen nur Daten.",
  "Actions describe business tasks, including prerequisites and confirmation. An action uses an application command; supported actions can open a form here.":
    "Actions beschreiben fachliche Aufgaben mit Voraussetzungen und Bestätigung. Eine Action nutzt einen Anwendungsbefehl; unterstützte Actions öffnen hier ein Formular.",
  "Commands are callable application operations with defined inputs and results. This catalog documents their interface and whether they read or change data.":
    "Commands sind aufrufbare Anwendungsoperationen mit definierten Eingaben und Ergebnissen. Der Katalog dokumentiert ihre Schnittstelle und ob sie Daten lesen oder ändern.",
  Information: "Erläuterung",
  "Projections derive a read model from existing records, such as available stock. They do not replace the underlying records.":
    "Projektionen leiten eine Datensicht aus vorhandenen Datensätzen ab, etwa den verfügbaren Bestand. Sie ersetzen die zugrunde liegenden Datensätze nicht.",
  "Views are application views of data. They use a projection or read an authoritative register directly; multiple views can use the same projection.":
    "Views sind Datenansichten der Anwendung. Sie nutzen eine Projektion oder lesen direkt aus einem maßgeblichen Register. Mehrere Views können dieselbe Projektion verwenden.",
  "Preview of returned data; up to 100 rows from the first response.":
    "Vorschau der zurückgegebenen Daten: bis zu 100 Zeilen aus der ersten Antwort.",
  "Start with a record, then follow the links to its evidence and original source.":
    "Starte bei einem Datensatz und folge seinen Verbindungen zu Nachweisen und Originalquelle.",
  "The result is uncertain. Reload and inspect the current state before another change.":
    "Das Ergebnis ist unklar. Lade neu und prüfe den aktuellen Stand vor einer weiteren Änderung.",
  "Use as draft": "Als Entwurf übernehmen",
  "Zoom in": "Vergrößern",
  "Zoom out": "Verkleinern",
  Views: "Sichten",
  "Create documented question": "Dokumentierte Frage anlegen",
  "Add context": "Kontext ergänzen",
  "Prepare rule draft": "Regelentwurf vorbereiten",
});

Object.assign(dictionaries.nl, {
  "Add evidence or context": "Bewijs of context toevoegen",
  "Business question": "Bedrijfsvraag",
  "Catalog definitions": "Catalogusdefinities",
  "Choose a record from Facts or Reality records to explore its links.":
    "Kies een feit of Reality-record om de koppelingen te bekijken.",
  "Choose Fact interpretation": "Als feit interpreteren",
  Commands: "Opdrachten",
  "Commands & actions": "Opdrachten en acties",
  "Context JSON": "Context als JSON",
  "Direct links from the selected record. Open a node to continue.":
    "Directe koppelingen van het gekozen record. Open een knooppunt om verder te gaan.",
  "Supporting records and history": "Bewijs en geschiedenis",
  "Execution history": "Uitvoeringsgeschiedenis",
  "Fact predicates": "Feitpredicaten",
  "Additional fact rules": "Regels voor aanvullende feiten",
  "Inspect records, follow their origins and review the tools that build Reality.":
    "Inspecteer records, volg hun oorsprong en bekijk de hulpmiddelen achter Reality.",
  "Intended use": "Beoogd gebruik",
  "New rule": "Nieuwe regel",
  "No linked records returned.": "Geen gekoppelde records gevonden.",
  "No Web form is registered here. See the command’s supported adapters.":
    "Hier is geen webformulier beschikbaar. Bekijk de ondersteunde adapters van de opdracht.",
  "Only company owners can change rules.": "Alleen bedrijfseigenaren kunnen regels wijzigen.",
  "Open action form": "Actieformulier openen",
  "Open view data": "Gegevens van weergave openen",
  "Possible finding types, their causes and how they clear.":
    "Mogelijke bevindingen, hun oorzaken en hoe ze verdwijnen.",
  "Projections & views": "Projecties en weergaven",
  "Reality Inspector": "Reality Inspector",
  "Practice companies are not available in this interface. Choose another company.":
    "Oefenbedrijven zijn niet beschikbaar in deze interface. Kies een ander bedrijf.",
  "This proposal cannot be reviewed in this interface yet. No change has been made here.":
    "Dit voorstel kan nog niet worden beoordeeld in deze interface. Hier is niets gewijzigd.",
  "Understand context": "Context begrijpen",
  "Facts & origins": "Feiten en herkomst",
  "Rules & insights": "Regels en inzichten",
  "Actions & history": "Acties en geschiedenis",
  "Operational records & facts": "Operationele records en feiten",
  "Derived insights": "Afgeleide inzichten",
  "What was received? Original values remain unchanged.":
    "Wat is ontvangen? Oorspronkelijke waarden blijven ongewijzigd.",
  "What does the evidence state? Documents and lines retain their source references.":
    "Wat staat in het bewijs? Documenten en regels behouden hun bronverwijzingen.",
  "What is recorded? Business commitments, reservations, movements and facts describe the situation.":
    "Wat is vastgelegd? Toezeggingen, reserveringen, bewegingen en feiten beschrijven de bedrijfssituatie.",
  "What follows from the records? Rules and views derive observations without becoming a new source of truth.":
    "Wat volgt uit de records? Regels en weergaven leiden observaties af zonder een nieuwe bron van waarheid te worden.",
  "What can happen next? Existing tools prepare changes for explicit review.":
    "Wat kan hierna gebeuren? Bestaande hulpmiddelen bereiden wijzigingen voor ter expliciete beoordeling.",
  "Understand the situation, not just one record.": "Begrijp de situatie in samenhang.",
  "Choose a business record. Follow its connections to see what is known, where it comes from and what it means.":
    "Kies een bedrijfsrecord. Volg de verbindingen: wat weten we, waar komt het vandaan en wat betekent het?",
  "How context is built": "Hoe context ontstaat",
  "This explains the model. The graph below shows only links actually returned for your record.":
    "Dit verklaart het model. De grafiek hieronder toont alleen werkelijk geleverde verbindingen van je record.",
  "Find a business record": "Bedrijfsrecord zoeken",
  "All records": "Alle records",
  "Customers & suppliers": "Klanten en leveranciers",
  "Derived insights belong to rules and views; they are not received source values.":
    "Afgeleide inzichten horen bij regels en weergaven; het zijn geen ontvangen bronwaarden.",
  "Select a record above to explore its context.":
    "Selecteer hierboven een record om de context te verkennen.",
  "Row density": "Rijdichtheid",
  "Updated at": "Bijgewerkt op",
  "Edit rule": "Regel bewerken",
  "Rule status": "Regelstatus",
  "Select a rule from the list.": "Selecteer een regel uit de lijst.",
  Draft: "Concept",
  "Rule changes require company owner or platform administrator access.":
    "Regelwijzigingen vereisen toegang als bedrijfseigenaar of platformbeheerder.",
  "This version is active and is applied to matching data.":
    "Deze versie is actief en wordt op passende gegevens toegepast.",
  "This draft is not applied. Simulate it before activation.":
    "Dit concept wordt nog niet toegepast. Simuleer het vóór activering.",
  "This version is disabled and retained for history.":
    "Deze versie is uitgeschakeld en blijft in de geschiedenis bewaard.",
  "Technical definition": "Technische definitie",
  "Changes create a new draft version. The active version stays unchanged until activation.":
    "Wijzigingen maken een nieuwe conceptversie. De actieve versie blijft ongewijzigd tot activering.",

  "Normal rows": "Normaal",
  "Table actions": "Tabelacties",
  "About this view": "Over deze weergave",
  "Technology & system": "Techniek & systeem",
  "Reality Inspector sections": "Onderdelen van Reality Inspector",
  "Reality records": "Reality-records",
  "Record graph": "Recordgrafiek",
  "Records per collection": "Records per verzameling",
  Result: "Resultaat",
  "Review recorded events and their supporting records.":
    "Bekijk vastgelegde gebeurtenissen en bijbehorende records.",
  "Rule draft": "Regelconcept",
  "Rule draft JSON": "Regelconcept als JSON",
  "Rules follow documented questions, evidence, a draft, simulation and explicit activation.":
    "Regels volgen gedocumenteerde vragen, bewijs, een concept, simulatie en expliciete activering.",
  "Search inspector": "Inspector doorzoeken",
  "Showing up to 100 returned rows.": "Maximaal 100 geretourneerde rijen worden getoond.",
  "Register data sources, configure them and open their received records. Registering a source does not connect or synchronize it.":
    "Registreer en configureer gegevensbronnen of open hun ontvangen records. Registratie maakt nog geen verbinding of synchronisatie.",
  "Find received data and open the unchanged original or its observations. Import status describes processing, not interpretation success.":
    "Zoek ontvangen gegevens en open het ongewijzigde origineel of de observaties. De importstatus beschrijft verwerking, niet het succes van interpretatie.",
  "Find business documents and trace them to their source. Delivery and payment state comes from linked business records.":
    "Zoek documenten en volg ze terug naar hun bron. Leverings- en betaalstatus volgen uit gekoppelde bedrijfsrecords.",
  "Python code": "Python-code",
  "View code": "Code bekijken",
  Function: "Functie",
  "Python source code": "Python-broncode",
  "Code preview truncated to 600 lines or 64 KiB.":
    "Codevoorbeeld beperkt tot 600 regels of 64 KiB.",
  "This action uses the following Python command. The code is shown for reading, not execution.":
    "Deze actie gebruikt de volgende Python-opdracht. Je kunt de code hier lezen, maar niet uitvoeren.",
  "This view uses the following projection. These Python functions read and calculate its data.":
    "Deze weergave gebruikt de volgende projectie. Deze Python-functies lezen en berekenen de gegevens.",
  "This view reads a register directly. This is its Python read endpoint, not the screen layout.":
    "Deze weergave leest rechtstreeks uit een register. Dit is het Python-leeseindpunt, niet de schermindeling.",
  "Python functions from the running application. This view does not execute or change the code.":
    "Python-functies uit de actieve toepassing. Deze weergave voert de code niet uit en wijzigt deze niet.",
  Required: "Verplicht",
  Optional: "Optioneel",
  "Calculated overview: this combines existing records to answer a business question.":
    "Berekend overzicht: combineert bestaande records om een zakelijke vraag te beantwoorden.",
  "Application view: this presents records or a calculated overview as a screen you can work with.":
    "Toepassingsweergave: toont records of een berekend overzicht op een scherm waarmee je kunt werken.",
  "Business task: this guides you through the information and confirmation needed to perform an operation.":
    "Zakelijke taak: begeleidt je bij de benodigde gegevens en bevestiging van een bewerking.",
  "Application operation: this defines the inputs, processing and results behind a business task.":
    "Toepassingsbewerking: beschrijft invoer, verwerking en resultaten achter een zakelijke taak.",
  "Illustrative example": "Voorbeeld ter verduidelijking",
  "100 units in stock minus 30 reserved gives 70 available. These are example numbers, not your company data.":
    "100 stuks op voorraad min 30 gereserveerd geeft 70 beschikbaar. Dit zijn voorbeeldcijfers, geen bedrijfsgegevens.",
  "You confirm a reservation of 5 units for a delivery commitment. The operation creates the reservation; it does not record a shipment.":
    "Je bevestigt een reservering van 5 stuks voor een leverbelofte. De bewerking maakt de reservering; ze boekt nog geen verzending.",
  "How it works": "Zo werkt het",
  "Data source": "Gegevensbron",
  "Data basis": "Gegevensbasis",
  "Calculated projection": "Berekende projectie",
  "Stored records": "Opgeslagen records",
  "Required context": "Benodigde context",
  "Application command": "Toepassingsopdracht",
  Confirmation: "Bevestiging",
  "Review a server-generated preview before confirming.":
    "Controleer vóór bevestiging een door de server gemaakte voorvertoning.",
  "Review the proposed change before confirming.":
    "Controleer de voorgestelde wijziging voordat je bevestigt.",
  "Reads from": "Leest uit",
  "Result fields": "Resultaatvelden",
  "Writes to": "Schrijft naar",
  "Used by": "Gebruikt door",
  "Updated after": "Bijgewerkt na",
  Returns: "Retourneert",
  "View implementation": "Implementatie bekijken",
  "View catalog source": "Catalogusbron bekijken",
  "Open in application": "Openen in toepassing",
  "A projection is a calculated overview, like an ERP stock report. Example: 100 units in stock minus 30 reserved gives 70 available. It uses existing records and does not create a new stock posting.":
    "Een projectie is een berekend overzicht, zoals een ERP-voorraadrapport. Voorbeeld: 100 stuks op voorraad min 30 gereserveerd geeft 70 beschikbaar. Ze gebruikt bestaande records en maakt geen nieuwe voorraadboeking.",
  "A view is a screen or list you work with in the application, like an ERP stock list. It can show a calculated projection or stored records such as items. Several views can use the same projection.":
    "Een view is een scherm of lijst waarmee je in de toepassing werkt, zoals een ERP-voorraadlijst. Hij toont een berekende projectie of opgeslagen records zoals artikelen. Meerdere views kunnen dezelfde projectie gebruiken.",
  "An action is a task you want to carry out in the ERP, such as reserving stock for an order. It guides you through the required inputs and confirmation, then uses a command to perform the task.":
    "Een actie is een taak die je in het ERP wilt uitvoeren, zoals voorraad reserveren voor een order. Ze begeleidt je bij de invoer en bevestiging en gebruikt daarna een opdracht om de taak uit te voeren.",
  "A command is the application operation behind a task. Example: after you confirm Reserve stock, the reserve command receives the order commitment and quantity and creates the reservation. This catalog describes the inputs and results; some commands only read data.":
    "Een opdracht is de toepassingsbewerking achter een taak. Voorbeeld: na bevestiging van Voorraad reserveren ontvangt reserve de leverbelofte en hoeveelheid en maakt de reservering. Deze catalogus beschrijft invoer en resultaten; sommige opdrachten lezen alleen gegevens.",
  "Actions describe business tasks, including prerequisites and confirmation. An action uses an application command; supported actions can open a form here.":
    "Acties beschrijven zakelijke taken met voorwaarden en bevestiging. Een actie gebruikt een toepassingsopdracht; ondersteunde acties openen hier een formulier.",
  "Commands are callable application operations with defined inputs and results. This catalog documents their interface and whether they read or change data.":
    "Opdrachten zijn aanroepbare toepassingsbewerkingen met vastgelegde invoer en resultaten. Deze catalogus beschrijft hun interface en of ze gegevens lezen of wijzigen.",
  Information: "Informatie",
  "Projections derive a read model from existing records, such as available stock. They do not replace the underlying records.":
    "Projecties leiden een gegevensmodel af uit bestaande records, zoals beschikbare voorraad. Ze vervangen de onderliggende records niet.",
  "Views are application views of data. They use a projection or read an authoritative register directly; multiple views can use the same projection.":
    "Views zijn gegevensweergaven in de toepassing. Ze gebruiken een projectie of lezen rechtstreeks uit een gezaghebbend register; meerdere views kunnen dezelfde projectie gebruiken.",
  "Preview of returned data; up to 100 rows from the first response.":
    "Voorbeeld van geretourneerde gegevens: maximaal 100 rijen uit het eerste antwoord.",
  "Start with a record, then follow the links to its evidence and original source.":
    "Begin bij een record en volg de koppelingen naar bewijs en oorspronkelijke bron.",
  "The result is uncertain. Reload and inspect the current state before another change.":
    "Het resultaat is onzeker. Herlaad en controleer de huidige toestand vóór een nieuwe wijziging.",
  "Use as draft": "Als concept gebruiken",
  "Zoom in": "Inzoomen",
  "Zoom out": "Uitzoomen",
  Views: "Weergaven",
  "Create documented question": "Gedocumenteerde vraag maken",
  "Add context": "Context toevoegen",
  "Prepare rule draft": "Regelconcept voorbereiden",
});

Object.assign(dictionaries.es, {
  "Add evidence or context": "Añadir evidencia o contexto",
  "Business question": "Pregunta de negocio",
  "Catalog definitions": "Definiciones del catálogo",
  "Choose a record from Facts or Reality records to explore its links.":
    "Elige un hecho o registro de Reality para explorar sus enlaces.",
  "Choose Fact interpretation": "Interpretar como hecho",
  Commands: "Comandos",
  "Commands & actions": "Comandos y acciones",
  "Context JSON": "Contexto JSON",
  "Direct links from the selected record. Open a node to continue.":
    "Enlaces directos del registro seleccionado. Abre un nodo para continuar.",
  "Supporting records and history": "Evidencia e historial",
  "Execution history": "Historial de ejecución",
  "Fact predicates": "Predicados de hechos",
  "Additional fact rules": "Reglas de hechos adicionales",
  "Inspect records, follow their origins and review the tools that build Reality.":
    "Inspecciona registros, sigue su origen y revisa las herramientas de Reality.",
  "Intended use": "Uso previsto",
  "New rule": "Nueva regla",
  "No linked records returned.": "No se devolvieron registros vinculados.",
  "No Web form is registered here. See the command’s supported adapters.":
    "No hay formulario web registrado. Consulta los adaptadores compatibles del comando.",
  "Only company owners can change rules.": "Solo los propietarios pueden modificar reglas.",
  "Open action form": "Abrir formulario de acción",
  "Open view data": "Abrir datos de la vista",
  "Possible finding types, their causes and how they clear.":
    "Posibles hallazgos, sus causas y cómo se resuelven.",
  "Projections & views": "Proyecciones y vistas",
  "Reality Inspector": "Reality Inspector",
  "Practice companies are not available in this interface. Choose another company.":
    "Las empresas de práctica no están disponibles en esta interfaz. Elige otra empresa.",
  "This proposal cannot be reviewed in this interface yet. No change has been made here.":
    "Esta propuesta aún no se puede revisar en esta interfaz. Aquí no se ha realizado ningún cambio.",
  "Understand context": "Comprender el contexto",
  "Facts & origins": "Hechos y origen",
  "Rules & insights": "Reglas y conclusiones",
  "Actions & history": "Acciones e historial",
  "Operational records & facts": "Registros operativos y hechos",
  "Derived insights": "Conclusiones derivadas",
  "What was received? Original values remain unchanged.":
    "¿Qué se recibió? Los valores originales permanecen intactos.",
  "What does the evidence state? Documents and lines retain their source references.":
    "¿Qué indica la evidencia? Los documentos y sus líneas conservan las referencias a su origen.",
  "What is recorded? Business commitments, reservations, movements and facts describe the situation.":
    "¿Qué está registrado? Los compromisos, reservas, movimientos y hechos describen la situación del negocio.",
  "What follows from the records? Rules and views derive observations without becoming a new source of truth.":
    "¿Qué se deduce de los registros? Las reglas y vistas derivan observaciones sin convertirse en una nueva fuente de verdad.",
  "What can happen next? Existing tools prepare changes for explicit review.":
    "¿Qué puede ocurrir después? Las herramientas existentes preparan cambios para su revisión explícita.",
  "Understand the situation, not just one record.": "Comprende la situación en su contexto.",
  "Choose a business record. Follow its connections to see what is known, where it comes from and what it means.":
    "Elige un registro del negocio. Sigue sus conexiones para ver qué se sabe, de dónde viene y qué significa.",
  "How context is built": "Cómo se construye el contexto",
  "This explains the model. The graph below shows only links actually returned for your record.":
    "Esto explica el modelo. El grafo inferior muestra solo conexiones realmente devueltas para tu registro.",
  "Find a business record": "Buscar un registro del negocio",
  "All records": "Todos los registros",
  "Customers & suppliers": "Clientes y proveedores",
  "Derived insights belong to rules and views; they are not received source values.":
    "Las conclusiones derivadas pertenecen a reglas y vistas; no son valores recibidos de la fuente.",
  "Select a record above to explore its context.":
    "Selecciona un registro arriba para explorar su contexto.",
  "Row density": "Densidad de filas",
  "Updated at": "Actualizado el",
  "Edit rule": "Editar regla",
  "Rule status": "Estado de regla",
  "Select a rule from the list.": "Selecciona una regla de la lista.",
  Draft: "Borrador",
  "Rule changes require company owner or platform administrator access.":
    "Los cambios de reglas requieren acceso como propietario o administrador de la plataforma.",
  "This version is active and is applied to matching data.":
    "Esta versión está activa y se aplica a los datos coincidentes.",
  "This draft is not applied. Simulate it before activation.":
    "Este borrador aún no se aplica. Simúlalo antes de activarlo.",
  "This version is disabled and retained for history.":
    "Esta versión está desactivada y se conserva en el historial.",
  "Technical definition": "Definición técnica",
  "Changes create a new draft version. The active version stays unchanged until activation.":
    "Los cambios crean un nuevo borrador. La versión activa no cambia hasta la activación.",

  "Normal rows": "Normal",
  "Table actions": "Acciones de la tabla",
  "About this view": "Acerca de esta vista",
  "Technology & system": "Tecnología y sistema",
  "Reality Inspector sections": "Secciones de Reality Inspector",
  "Reality records": "Registros de Reality",
  "Record graph": "Grafo de registros",
  "Records per collection": "Registros por colección",
  Result: "Resultado",
  "Review recorded events and their supporting records.":
    "Revisa los eventos registrados y los registros relacionados.",
  "Rule draft": "Borrador de regla",
  "Rule draft JSON": "Borrador de regla JSON",
  "Rules follow documented questions, evidence, a draft, simulation and explicit activation.":
    "Las reglas siguen preguntas documentadas, evidencia, borrador, simulación y activación explícita.",
  "Search inspector": "Buscar en Inspector",
  "Showing up to 100 returned rows.": "Se muestran hasta 100 filas devueltas.",
  "Register data sources, configure them and open their received records. Registering a source does not connect or synchronize it.":
    "Registra y configura fuentes de datos o abre sus registros recibidos. Registrarlas no establece una conexión ni sincronización.",
  "Find received data and open the unchanged original or its observations. Import status describes processing, not interpretation success.":
    "Busca datos recibidos y abre el original sin cambios o sus observaciones. El estado de importación describe el procesamiento, no el éxito de la interpretación.",
  "Find business documents and trace them to their source. Delivery and payment state comes from linked business records.":
    "Busca documentos y sigue su origen. El estado de entrega y pago se obtiene de los registros de negocio vinculados.",
  "Python code": "Código Python",
  "View code": "Ver código",
  Function: "Función",
  "Python source code": "Código fuente Python",
  "Code preview truncated to 600 lines or 64 KiB.":
    "Vista de código limitada a 600 líneas o 64 KiB.",
  "This action uses the following Python command. The code is shown for reading, not execution.":
    "Esta acción usa el siguiente comando Python. El código se muestra para leerlo, no para ejecutarlo.",
  "This view uses the following projection. These Python functions read and calculate its data.":
    "Esta vista usa la siguiente proyección. Estas funciones Python leen y calculan sus datos.",
  "This view reads a register directly. This is its Python read endpoint, not the screen layout.":
    "Esta vista lee un registro directamente. Este es su punto de lectura Python, no el diseño de pantalla.",
  "Python functions from the running application. This view does not execute or change the code.":
    "Funciones Python de la aplicación en ejecución. Esta vista no ejecuta ni modifica el código.",
  Required: "Obligatorio",
  Optional: "Opcional",
  "Calculated overview: this combines existing records to answer a business question.":
    "Resumen calculado: combina registros existentes para responder una pregunta de negocio.",
  "Application view: this presents records or a calculated overview as a screen you can work with.":
    "Vista de la aplicación: muestra registros o un resumen calculado en una pantalla de trabajo.",
  "Business task: this guides you through the information and confirmation needed to perform an operation.":
    "Tarea de negocio: te guía por los datos y la confirmación necesarios para realizar una operación.",
  "Application operation: this defines the inputs, processing and results behind a business task.":
    "Operación de la aplicación: define entradas, procesamiento y resultados de una tarea de negocio.",
  "Illustrative example": "Ejemplo ilustrativo",
  "100 units in stock minus 30 reserved gives 70 available. These are example numbers, not your company data.":
    "100 unidades en stock menos 30 reservadas dan 70 disponibles. Son cifras de ejemplo, no datos de tu empresa.",
  "You confirm a reservation of 5 units for a delivery commitment. The operation creates the reservation; it does not record a shipment.":
    "Confirmas una reserva de 5 unidades para un compromiso de entrega. La operación crea la reserva; no registra un envío.",
  "How it works": "Cómo funciona",
  "Data source": "Fuente de datos",
  "Data basis": "Base de datos utilizada",
  "Calculated projection": "Proyección calculada",
  "Stored records": "Registros guardados",
  "Required context": "Contexto necesario",
  "Application command": "Comando de la aplicación",
  Confirmation: "Confirmación",
  "Review a server-generated preview before confirming.":
    "Revisa la vista previa generada por el servidor antes de confirmar.",
  "Review the proposed change before confirming.": "Revisa el cambio propuesto antes de confirmar.",
  "Reads from": "Lee de",
  "Result fields": "Campos de resultado",
  "Writes to": "Escribe en",
  "Used by": "Utilizado por",
  "Updated after": "Actualizado tras",
  Returns: "Devuelve",
  "View implementation": "Ver implementación",
  "View catalog source": "Ver fuente del catálogo",
  "Open in application": "Abrir en la aplicaci\u00f3n",
  "A projection is a calculated overview, like an ERP stock report. Example: 100 units in stock minus 30 reserved gives 70 available. It uses existing records and does not create a new stock posting.":
    "Una proyección es un resumen calculado, como un informe de stock del ERP. Ejemplo: 100 unidades en stock menos 30 reservadas dan 70 disponibles. Usa registros existentes y no crea un nuevo movimiento de stock.",
  "A view is a screen or list you work with in the application, like an ERP stock list. It can show a calculated projection or stored records such as items. Several views can use the same projection.":
    "Una vista es una pantalla o lista de la aplicación, como una lista de stock del ERP. Puede mostrar una proyección calculada o registros guardados, como artículos. Varias vistas pueden usar la misma proyección.",
  "An action is a task you want to carry out in the ERP, such as reserving stock for an order. It guides you through the required inputs and confirmation, then uses a command to perform the task.":
    "Una acción es una tarea que quieres realizar en el ERP, como reservar stock para un pedido. Te guía por los datos necesarios y la confirmación, y después usa un comando para ejecutar la tarea.",
  "A command is the application operation behind a task. Example: after you confirm Reserve stock, the reserve command receives the order commitment and quantity and creates the reservation. This catalog describes the inputs and results; some commands only read data.":
    "Un comando es la operación de la aplicación detrás de una tarea. Ejemplo: al confirmar Reservar stock, reserve recibe el compromiso de entrega y la cantidad y crea la reserva. Este catálogo describe entradas y resultados; algunos comandos solo leen datos.",
  "Actions describe business tasks, including prerequisites and confirmation. An action uses an application command; supported actions can open a form here.":
    "Las acciones describen tareas de negocio con requisitos y confirmación. Una acción usa un comando de la aplicación; las acciones compatibles abren un formulario aquí.",
  "Commands are callable application operations with defined inputs and results. This catalog documents their interface and whether they read or change data.":
    "Los comandos son operaciones invocables de la aplicación con entradas y resultados definidos. El catálogo documenta su interfaz y si leen o modifican datos.",
  Information: "Información",
  "Projections derive a read model from existing records, such as available stock. They do not replace the underlying records.":
    "Las proyecciones derivan una vista de datos de registros existentes, como el stock disponible. No sustituyen los registros originales.",
  "Views are application views of data. They use a projection or read an authoritative register directly; multiple views can use the same projection.":
    "Las vistas muestran datos en la aplicación. Usan una proyección o leen directamente un registro de referencia; varias vistas pueden usar la misma proyección.",
  "Preview of returned data; up to 100 rows from the first response.":
    "Vista previa de los datos devueltos: hasta 100 filas de la primera respuesta.",
  "Start with a record, then follow the links to its evidence and original source.":
    "Empieza por un registro y sigue sus enlaces hasta la evidencia y la fuente original.",
  "The result is uncertain. Reload and inspect the current state before another change.":
    "El resultado es incierto. Recarga y comprueba el estado actual antes de otro cambio.",
  "Use as draft": "Usar como borrador",
  "Zoom in": "Acercar",
  "Zoom out": "Alejar",
  Views: "Vistas",
  "Create documented question": "Crear pregunta documentada",
  "Add context": "Añadir contexto",
  "Prepare rule draft": "Preparar borrador de regla",
});

Object.assign(dictionaries.de, {
  "Flight recorder": "Flugschreiber",
  "Latest recorded changes first. Scroll down to travel back in time.":
    "Neueste Aufzeichnungen zuerst. Scrolle nach unten, um zurückzugehen.",
  "Recorded events": "Aufgezeichnete Ereignisse",
  "Event history": "Ereignisverlauf",
  "Connections show recorded references, not a reconstruction of past state.":
    "Verbindungen zeigen dokumentierte Bezüge. Der damalige Gesamtzustand wird nicht rekonstruiert.",
  "Event details": "Ereignisdetails",
  "Caused by event": "Auslösendes Ereignis",
  "No recorded events yet.": "Noch keine Ereignisse aufgezeichnet.",
  "Beginning of recorded history": "Anfang der Aufzeichnungen",
  "Load older events": "Ältere Ereignisse laden",
});

Object.assign(dictionaries.nl, {
  "Flight recorder": "Vluchtrecorder",
  "Latest recorded changes first. Scroll down to travel back in time.":
    "Nieuwste registraties eerst. Scrol omlaag om terug te gaan in de tijd.",
  "Recorded events": "Geregistreerde gebeurtenissen",
  "Event history": "Gebeurtenisgeschiedenis",
  "Connections show recorded references, not a reconstruction of past state.":
    "Verbindingen tonen vastgelegde verwijzingen, geen reconstructie van een eerdere toestand.",
  "Event details": "Gebeurtenisdetails",
  "Caused by event": "Veroorzakende gebeurtenis",
  "No recorded events yet.": "Nog geen gebeurtenissen geregistreerd.",
  "Beginning of recorded history": "Begin van de geregistreerde geschiedenis",
  "Load older events": "Oudere gebeurtenissen laden",
});

Object.assign(dictionaries.es, {
  "Flight recorder": "Registrador de eventos",
  "Latest recorded changes first. Scroll down to travel back in time.":
    "Los registros más recientes primero. Desplázate hacia abajo para retroceder en el tiempo.",
  "Recorded events": "Eventos registrados",
  "Event history": "Historial de eventos",
  "Connections show recorded references, not a reconstruction of past state.":
    "Las conexiones muestran referencias registradas, no una reconstrucción del estado pasado.",
  "Event details": "Detalles del evento",
  "Caused by event": "Evento causante",
  "No recorded events yet.": "Aún no hay eventos registrados.",
  "Beginning of recorded history": "Inicio del historial registrado",
  "Load older events": "Cargar eventos anteriores",
});

Object.assign(dictionaries.nl, { "Occurred at": "Gebeurd op" });
Object.assign(dictionaries.es, { "Occurred at": "Ocurrido el" });

Object.assign(dictionaries.de, {
  Integrations: "Integrationen",
  "Received data": "Empfangene Daten",
});
Object.assign(dictionaries.nl, {
  Integrations: "Integraties",
  "Received data": "Ontvangen gegevens",
});
Object.assign(dictionaries.es, {
  Integrations: "Integraciones",
  "Received data": "Datos recibidos",
});

Object.assign(dictionaries.de, {
  "Follow how records build up across the layers. Time runs from left to right.":
    "Sieh, wie sich Datensätze über die Ebenen aufbauen. Die Zeit läuft von links nach rechts.",
  "Records appear at their first observation in the loaded history. Earlier references have no known creation time here.":
    "Datensätze stehen bei ihrer ersten Beobachtung im geladenen Verlauf. Bei älteren Referenzen ist die Entstehungszeit hier unbekannt.",
  "Earlier reference": "Ältere Referenz",
  "Connected records highlighted": "Verbundene Knoten hervorgehoben",
  "Recorded change": "Aufgezeichnete Änderung",
  "Source reference": "Quellenbezug",
  "Recorded reference": "Aufgezeichneter Bezug",
});

Object.assign(dictionaries.nl, {
  "Follow how records build up across the layers. Time runs from left to right.":
    "Zie hoe records zich over de lagen opbouwen. De tijd loopt van links naar rechts.",
  "Records appear at their first observation in the loaded history. Earlier references have no known creation time here.":
    "Records staan bij hun eerste waarneming in de geladen geschiedenis. De aanmaaktijd van eerdere verwijzingen is hier onbekend.",
  "Earlier reference": "Eerdere verwijzing",
  "Connected records highlighted": "Verbonden knooppunten gemarkeerd",
  "Recorded change": "Geregistreerde wijziging",
  "Source reference": "Bronverwijzing",
  "Recorded reference": "Geregistreerde verwijzing",
});

Object.assign(dictionaries.es, {
  "Follow how records build up across the layers. Time runs from left to right.":
    "Observa cómo se forman los registros en las distintas capas. El tiempo avanza de izquierda a derecha.",
  "Records appear at their first observation in the loaded history. Earlier references have no known creation time here.":
    "Los registros aparecen en su primera observación del historial cargado. Aquí se desconoce la fecha de creación de las referencias anteriores.",
  "Earlier reference": "Referencia anterior",
  "Connected records highlighted": "Nodos conectados resaltados",
  "Recorded change": "Cambio registrado",
  "Source reference": "Referencia de origen",
  "Recorded reference": "Referencia registrada",
});

Object.assign(dictionaries.de, {
  "How sources, documents and operational records connect over time.":
    "Wie Quellen, Belege und operative Datensätze über die Zeit zusammenhängen.",
});
Object.assign(dictionaries.nl, {
  "How sources, documents and operational records connect over time.":
    "Hoe bronnen, documenten en operationele records door de tijd heen samenhangen.",
});
Object.assign(dictionaries.es, {
  "How sources, documents and operational records connect over time.":
    "Cómo se relacionan las fuentes, los documentos y los registros operativos a lo largo del tiempo.",
});

Object.assign(dictionaries.de, {
  "Document lines": "Belegpositionen",
  "Source records": "Quelldatensätze",
  Record: "Datensatz",
  "Search records": "Datensätze suchen",
  "Search by name, type, value or ID": "Nach Name, Art, Wert oder ID suchen",
  "Grouped by record type. Open a record to see its details and origin.":
    "Nach Datensatzart gruppiert. Öffne einen Datensatz für Details und Herkunft.",
});

Object.assign(dictionaries.nl, {
  "Document lines": "Documentregels",
  "Source records": "Bronrecords",
  Record: "Gegevensrecord",
  "Search records": "Records zoeken",
  "Search by name, type, value or ID": "Zoeken op naam, type, waarde of ID",
  "Grouped by record type. Open a record to see its details and origin.":
    "Gegroepeerd op recordtype. Open een record voor details en herkomst.",
});

Object.assign(dictionaries.es, {
  "Document lines": "Líneas de documento",
  "Source records": "Registros de origen",
  Record: "Registro",
  "Search records": "Buscar registros",
  "Search by name, type, value or ID": "Buscar por nombre, tipo, valor o ID",
  "Grouped by record type. Open a record to see its details and origin.":
    "Agrupados por tipo de registro. Abre un registro para ver sus detalles y origen.",
});

Object.assign(dictionaries.de, {
  "Commitments to customers or from suppliers. Reservations bind stock; movements record actual execution.":
    "Zusagen an Kunden oder von Lieferanten (Commitments). Reservierungen (Reservations) binden Bestand; Bewegungen (Movements) dokumentieren die Ausführung.",
});

Object.assign(dictionaries.nl, {
  "Commitments to customers or from suppliers. Reservations bind stock; movements record actual execution.":
    "Toezeggingen aan klanten of van leveranciers (Commitments). Reserveringen (Reservations) binden voorraad; bewegingen (Movements) leggen de uitvoering vast.",
});

Object.assign(dictionaries.es, {
  "Commitments to customers or from suppliers. Reservations bind stock; movements record actual execution.":
    "Compromisos con clientes o de proveedores (Commitments). Las reservas (Reservations) asignan existencias; los movimientos (Movements) registran la ejecución.",
});

Object.assign(dictionaries.de, {
  "Playground has been retired": "Der Playground wurde eingestellt",
  "Page unavailable": "Seite nicht verfügbar",
  "Use the Reality app for your work. Existing records have been preserved.":
    "Nutze die Reality-App für deine Arbeit. Vorhandene Datensätze bleiben erhalten.",
  "This address no longer has a workspace. Open the app to continue.":
    "Unter dieser Adresse gibt es keinen Arbeitsbereich mehr. Öffne die App, um fortzufahren.",
  "Open app": "App öffnen",
});

Object.assign(dictionaries.nl, {
  "Playground has been retired": "De Playground is beëindigd",
  "Page unavailable": "Pagina niet beschikbaar",
  "Use the Reality app for your work. Existing records have been preserved.":
    "Gebruik de Reality-app voor je werk. Bestaande records zijn behouden.",
  "This address no longer has a workspace. Open the app to continue.":
    "Dit adres heeft geen werkruimte meer. Open de app om verder te gaan.",
  "Open app": "App openen",
});

Object.assign(dictionaries.es, {
  "Playground has been retired": "El Playground se ha retirado",
  "Page unavailable": "Página no disponible",
  "Use the Reality app for your work. Existing records have been preserved.":
    "Usa la aplicación Reality para tu trabajo. Los registros existentes se han conservado.",
  "This address no longer has a workspace. Open the app to continue.":
    "Esta dirección ya no tiene un espacio de trabajo. Abre la aplicación para continuar.",
  "Open app": "Abrir aplicación",
});

Object.assign(dictionaries.de, {
  "Could not sign out. Please try again.": "Abmelden fehlgeschlagen. Bitte versuche es erneut.",
  "Signing out…": "Abmelden…",
});

Object.assign(dictionaries.nl, {
  "Could not sign out. Please try again.": "Uitloggen mislukt. Probeer het opnieuw.",
  "Signing out…": "Uitloggen…",
});

Object.assign(dictionaries.es, {
  "Could not sign out. Please try again.": "No se pudo cerrar la sesión. Inténtalo de nuevo.",
  "Signing out…": "Cerrando sesión…",
});

Object.assign(dictionaries.de, {
  "Agents & API tokens": "Agenten & API-Token",
  "Manage users": "Benutzer verwalten",
  "You own this company and manage its access.":
    "Du bist Inhaber dieses Unternehmens und verwaltest die Zugänge.",
  "You are a member. Only company owners manage users and agent tokens.":
    "Du bist Mitglied. Nur die Inhaber verwalten Benutzer und Agenten-Token.",
});

Object.assign(dictionaries.nl, {
  "Agents & API tokens": "Agenten & API-tokens",
  "Manage users": "Gebruikers beheren",
  "You own this company and manage its access.":
    "Je bent eigenaar van dit bedrijf en beheert de toegang.",
  "You are a member. Only company owners manage users and agent tokens.":
    "Je bent lid. Alleen bedrijfseigenaren beheren gebruikers en agenttokens.",
});

Object.assign(dictionaries.es, {
  "Agents & API tokens": "Agentes y tokens de API",
  "Manage users": "Gestionar usuarios",
  "You own this company and manage its access.":
    "Eres propietario de esta empresa y gestionas su acceso.",
  "You are a member. Only company owners manage users and agent tokens.":
    "Eres miembro. Solo los propietarios gestionan usuarios y tokens de agentes.",
});

Object.assign(dictionaries.de, { "Manage companies": "Firmen verwalten" });

Object.assign(dictionaries.nl, { "Manage companies": "Bedrijven beheren" });

Object.assign(dictionaries.es, { "Manage companies": "Gestionar empresas" });

Object.assign(dictionaries.de, {
  "Search commitments": "Commitments suchen",
  "Back to commitments": "Zurück zu Commitments",
  "View commitments": "Commitments ansehen",
  "Commitments for the selected order": "Commitments zum ausgewählten Auftrag",
  "Choose a commitment to see what is open and why.":
    "Wähle ein Commitment, um zu sehen, was noch offen ist und warum.",
  "Open delivery commitments to customers.": "Offene Lieferzusagen an Kunden.",
});

Object.assign(dictionaries.nl, {
  "Search commitments": "Toezeggingen zoeken",
  "Back to commitments": "Terug naar toezeggingen",
  "View commitments": "Toezeggingen bekijken",
  "Commitments for the selected order": "Commitments voor de geselecteerde order",
  "Choose a commitment to see what is open and why.":
    "Kies een toezegging om te zien wat nog openstaat en waarom.",
  "Open delivery commitments to customers.": "Open levertoezeggingen aan klanten.",
});

Object.assign(dictionaries.es, {
  "Search commitments": "Buscar compromisos",
  "Back to commitments": "Volver a compromisos",
  "View commitments": "Ver compromisos",
  "Commitments for the selected order": "Commitments del pedido seleccionado",
  "Choose a commitment to see what is open and why.":
    "Selecciona un compromiso para ver qué queda pendiente y por qué.",
  "Open delivery commitments to customers.": "Compromisos de entrega pendientes a clientes.",
});

Object.assign(dictionaries.de, {
  "Open commitment": "Commitment öffnen",
  "Supplier delivery": "Lieferantenzusage",
});

Object.assign(dictionaries.nl, {
  "Open commitment": "Toezegging openen",
  "Supplier delivery": "Leverancierslevering",
});

Object.assign(dictionaries.es, {
  "Open commitment": "Abrir compromiso",
  "Supplier delivery": "Entrega de proveedor",
});

Object.assign(dictionaries.de, {
  "My integrations": "Meine Integrationen",
  "Add integration": "Integration hinzufügen",
  "Registered sources": "Registrierte Quellen",
  "Integration preparation": "Integrationen vorbereiten",
  "Choose your systems and prepare what you want to receive.":
    "Wähle deine Systeme und bereite vor, welche Daten du empfangen möchtest.",
  "Preparation only. Drafts stay in this browser session for you and this company. No system is connected and no data is synchronized.":
    "Nur Vorbereitung. Entwürfe bleiben für dich und diese Firma in dieser Browser-Sitzung. Es ist kein System verbunden und es werden keine Daten synchronisiert.",
  "Saved preparations could not be loaded. You can start a new draft.":
    "Gespeicherte Vorbereitungen konnten nicht geladen werden. Du kannst einen neuen Entwurf beginnen.",
  "Start with your first system": "Beginne mit deinem ersten System",
  "Shop, ERP, payments, CRM or product information: choose a provider to prepare its setup.":
    "Shop, ERP, Zahlungen, CRM oder Produktinformationen: Wähle einen Anbieter und bereite die Einrichtung vor.",
  "Preparation draft": "Einrichtungsentwurf",
  "Open preparation": "Einrichtung öffnen",
  "Remove draft": "Entwurf entfernen",
  "Draft removed.": "Entwurf entfernt.",
  "Draft could not be saved. Browser session storage is unavailable.":
    "Der Entwurf konnte nicht gespeichert werden. Der Sitzungsspeicher des Browsers ist nicht verfügbar.",
  "This session has 100 drafts. Remove a draft before adding another.":
    "Diese Sitzung hat 100 Entwürfe. Entferne einen, bevor du einen weiteren hinzufügst.",
  "Preparation saved. The connection will be implemented separately.":
    "Vorbereitung gespeichert. Die technische Anbindung folgt separat.",
  "Name your connection": "Einrichtung benennen",
  "Choose intended data": "Geplante Daten auswählen",
  "Review preparation": "Vorbereitung prüfen",
  "Choose a provider. All connections below are preparation only.":
    "Wähle einen Anbieter. Alle folgenden Anbindungen dienen zunächst nur der Vorbereitung.",
  "Search providers": "Anbieter suchen",
  "Provider category": "Anbieterkategorie",
  "All categories": "Alle Kategorien",
  Prepare: "Vorbereiten",
  "Prepare setup": "Einrichtung vorbereiten",
  "No providers match your search.": "Keine passenden Anbieter gefunden.",
  "Already have a file? Import items using the existing CSV workflow.":
    "Du hast bereits eine Datei? Importiere Artikel über den bestehenden CSV-Import.",
  "No credentials are needed. This prepares the setup; it does not connect your account.":
    "Keine Zugangsdaten nötig. Du bereitest die Einrichtung vor; dein Konto wird noch nicht verbunden.",
  "Connection name": "Name der Einrichtung",
  "Use a name you recognize, such as DE shop or Main account.":
    "Nutze einen eindeutigen Namen, zum Beispiel DE-Shop oder Hauptkonto.",
  "Related Shopify shop": "Zugehöriger Shopify-Shop",
  "Enter the shop name as planning context. This does not link accounts.":
    "Gib den Shopnamen zur Planung an. Dadurch werden keine Konten verknüpft.",
  "Which data would you like to receive? These are planning choices, not available connector features.":
    "Welche Daten möchtest du empfangen? Das sind Planungswünsche, noch keine verfügbaren Funktionen der Anbindung.",
  Provider: "Anbieter",
  "Intended data": "Geplante Daten",
  "Saved only for you and this company in this browser session. Technical connection follows separately.":
    "Wird nur für dich und diese Firma in dieser Browser-Sitzung gespeichert. Die technische Anbindung folgt separat.",
  "Save draft": "Entwurf speichern",
  "Shop & ERP": "Shops und ERP",
  "Product data / PIM": "Produktdaten / PIM",
  CRM: "CRM",
  "Product data": "Produktdaten",
  "Product media": "Produktmedien",
  "Product categories": "Produktkategorien",
  Payouts: "Auszahlungen",
  Contacts: "Kontakte",
  Deals: "Verkaufschancen",
  "Plan to receive orders, customers and products from your shop.":
    "Bereite den Empfang von Bestellungen, Kunden und Artikeln aus deinem Shop vor.",
  "Plan to receive orders and master data from your ERP.":
    "Bereite den Empfang von Aufträgen und Stammdaten aus deinem ERP vor.",
  "Plan payment data for a related Shopify shop.":
    "Plane Zahlungsdaten für einen zugehörigen Shopify-Shop.",
  "Plan to receive payments, refunds and payouts.":
    "Bereite den Empfang von Zahlungen, Erstattungen und Auszahlungen vor.",
  "Plan to receive payments and refunds.":
    "Bereite den Empfang von Zahlungen und Erstattungen vor.",
  "Plan to receive contacts, companies and sales opportunities.":
    "Bereite den Empfang von Kontakten, Firmen und Verkaufschancen vor.",
  "Plan to receive enriched product information and categories.":
    "Bereite den Empfang von angereicherten Produktinformationen und Kategorien vor.",
});

Object.assign(dictionaries.nl, {
  "My integrations": "Mijn integraties",
  "Add integration": "Integratie toevoegen",
  "Registered sources": "Geregistreerde bronnen",
  "Integration preparation": "Integraties voorbereiden",
  "Choose your systems and prepare what you want to receive.":
    "Kies je systemen en bereid voor welke gegevens je wilt ontvangen.",
  "Preparation only. Drafts stay in this browser session for you and this company. No system is connected and no data is synchronized.":
    "Alleen voorbereiding. Concepten blijven voor jou en dit bedrijf in deze browsersessie. Er is geen systeem verbonden en er worden geen gegevens gesynchroniseerd.",
  "Saved preparations could not be loaded. You can start a new draft.":
    "Opgeslagen voorbereidingen konden niet worden geladen. Je kunt een nieuw concept starten.",
  "Start with your first system": "Begin met je eerste systeem",
  "Shop, ERP, payments, CRM or product information: choose a provider to prepare its setup.":
    "Shop, ERP, betalingen, CRM of productinformatie: kies een aanbieder en bereid de inrichting voor.",
  "Preparation draft": "Inrichtingsconcept",
  "Open preparation": "Voorbereiding openen",
  "Remove draft": "Concept verwijderen",
  "Draft removed.": "Concept verwijderd.",
  "Draft could not be saved. Browser session storage is unavailable.":
    "Het concept kon niet worden opgeslagen. De sessieopslag van de browser is niet beschikbaar.",
  "This session has 100 drafts. Remove a draft before adding another.":
    "Deze sessie heeft 100 concepten. Verwijder er een voordat je een ander toevoegt.",
  "Preparation saved. The connection will be implemented separately.":
    "Voorbereiding opgeslagen. De technische verbinding volgt afzonderlijk.",
  "Name your connection": "Verbinding benoemen",
  "Choose intended data": "Gewenste gegevens kiezen",
  "Review preparation": "Voorbereiding controleren",
  "Choose a provider. All connections below are preparation only.":
    "Kies een aanbieder. Alle onderstaande verbindingen zijn alleen ter voorbereiding.",
  "Search providers": "Aanbieders zoeken",
  "Provider category": "Aanbiederscategorie",
  "All categories": "Alle categorieën",
  Prepare: "Voorbereiden",
  "Prepare setup": "Inrichting voorbereiden",
  "No providers match your search.": "Geen aanbieders gevonden voor je zoekopdracht.",
  "Already have a file? Import items using the existing CSV workflow.":
    "Heb je al een bestand? Importeer artikelen via de bestaande CSV-import.",
  "No credentials are needed. This prepares the setup; it does not connect your account.":
    "Er zijn geen inloggegevens nodig. Je bereidt de inrichting voor; je account wordt nog niet verbonden.",
  "Connection name": "Naam van de verbinding",
  "Use a name you recognize, such as DE shop or Main account.":
    "Gebruik een herkenbare naam, bijvoorbeeld DE-shop of Hoofdaccount.",
  "Related Shopify shop": "Bijbehorende Shopify-shop",
  "Enter the shop name as planning context. This does not link accounts.":
    "Voer de shopnaam in voor de planning. Dit koppelt geen accounts.",
  "Which data would you like to receive? These are planning choices, not available connector features.":
    "Welke gegevens wil je ontvangen? Dit zijn planningskeuzes, nog geen beschikbare verbindingsfuncties.",
  Provider: "Aanbieder",
  "Intended data": "Gewenste gegevens",
  "Saved only for you and this company in this browser session. Technical connection follows separately.":
    "Wordt alleen voor jou en dit bedrijf in deze browsersessie opgeslagen. De technische verbinding volgt afzonderlijk.",
  "Save draft": "Concept opslaan",
  "Shop & ERP": "Webshops en ERP",
  "Product data / PIM": "Productgegevens / PIM",
  CRM: "CRM",
  "Product data": "Productgegevens",
  "Product media": "Productmedia",
  "Product categories": "Productcategorieën",
  Payouts: "Uitbetalingen",
  Contacts: "Contacten",
  Deals: "Verkoopkansen",
  "Plan to receive orders, customers and products from your shop.":
    "Bereid de ontvangst van bestellingen, klanten en producten uit je shop voor.",
  "Plan to receive orders and master data from your ERP.":
    "Bereid de ontvangst van orders en stamgegevens uit je ERP voor.",
  "Plan payment data for a related Shopify shop.":
    "Plan betalingsgegevens voor een bijbehorende Shopify-shop.",
  "Plan to receive payments, refunds and payouts.":
    "Bereid de ontvangst van betalingen, terugbetalingen en uitbetalingen voor.",
  "Plan to receive payments and refunds.":
    "Bereid de ontvangst van betalingen en terugbetalingen voor.",
  "Plan to receive contacts, companies and sales opportunities.":
    "Bereid de ontvangst van contacten, bedrijven en verkoopkansen voor.",
  "Plan to receive enriched product information and categories.":
    "Bereid de ontvangst van verrijkte productinformatie en categorieën voor.",
});

Object.assign(dictionaries.es, {
  "My integrations": "Mis integraciones",
  "Add integration": "Añadir integración",
  "Registered sources": "Fuentes registradas",
  "Integration preparation": "Preparación de integraciones",
  "Choose your systems and prepare what you want to receive.":
    "Elige tus sistemas y prepara los datos que quieres recibir.",
  "Preparation only. Drafts stay in this browser session for you and this company. No system is connected and no data is synchronized.":
    "Solo preparación. Los borradores se guardan para ti y esta empresa en esta sesión del navegador. No se conecta ningún sistema ni se sincronizan datos.",
  "Saved preparations could not be loaded. You can start a new draft.":
    "No se pudieron cargar las preparaciones guardadas. Puedes iniciar un nuevo borrador.",
  "Start with your first system": "Empieza con tu primer sistema",
  "Shop, ERP, payments, CRM or product information: choose a provider to prepare its setup.":
    "Tienda, ERP, pagos, CRM o información de productos: elige un proveedor y prepara su configuración.",
  "Preparation draft": "Borrador de configuración",
  "Open preparation": "Abrir preparación",
  "Remove draft": "Eliminar borrador",
  "Draft removed.": "Borrador eliminado.",
  "Draft could not be saved. Browser session storage is unavailable.":
    "No se pudo guardar el borrador. El almacenamiento de sesión del navegador no está disponible.",
  "This session has 100 drafts. Remove a draft before adding another.":
    "Esta sesión tiene 100 borradores. Elimina uno antes de añadir otro.",
  "Preparation saved. The connection will be implemented separately.":
    "Preparación guardada. La conexión técnica se implementará por separado.",
  "Name your connection": "Nombrar conexión",
  "Choose intended data": "Elegir datos previstos",
  "Review preparation": "Revisar preparación",
  "Choose a provider. All connections below are preparation only.":
    "Elige un proveedor. Todas las conexiones siguientes son solo preparaciones.",
  "Search providers": "Buscar proveedores",
  "Provider category": "Categoría del proveedor",
  "All categories": "Todas las categorías",
  Prepare: "Preparar",
  "Prepare setup": "Preparar configuración",
  "No providers match your search.": "No hay proveedores que coincidan con tu búsqueda.",
  "Already have a file? Import items using the existing CSV workflow.":
    "¿Ya tienes un archivo? Importa artículos mediante el proceso CSV existente.",
  "No credentials are needed. This prepares the setup; it does not connect your account.":
    "No se necesitan credenciales. Esto prepara la configuración; no conecta tu cuenta.",
  "Connection name": "Nombre de la conexión",
  "Use a name you recognize, such as DE shop or Main account.":
    "Usa un nombre reconocible, como Tienda DE o Cuenta principal.",
  "Related Shopify shop": "Tienda Shopify relacionada",
  "Enter the shop name as planning context. This does not link accounts.":
    "Introduce el nombre de la tienda como contexto de planificación. Esto no vincula cuentas.",
  "Which data would you like to receive? These are planning choices, not available connector features.":
    "¿Qué datos quieres recibir? Son opciones de planificación, no funciones disponibles del conector.",
  Provider: "Proveedor",
  "Intended data": "Datos previstos",
  "Saved only for you and this company in this browser session. Technical connection follows separately.":
    "Se guarda solo para ti y esta empresa en esta sesión del navegador. La conexión técnica se realizará por separado.",
  "Save draft": "Guardar borrador",
  "Shop & ERP": "Tienda y ERP",
  "Product data / PIM": "Datos de productos / PIM",
  CRM: "CRM",
  "Product data": "Datos de productos",
  "Product media": "Medios de productos",
  "Product categories": "Categorías de productos",
  Payouts: "Desembolsos",
  Contacts: "Contactos",
  Deals: "Oportunidades",
  "Plan to receive orders, customers and products from your shop.":
    "Prepara la recepción de pedidos, clientes y productos de tu tienda.",
  "Plan to receive orders and master data from your ERP.":
    "Prepara la recepción de pedidos y datos maestros de tu ERP.",
  "Plan payment data for a related Shopify shop.":
    "Planifica datos de pagos para una tienda Shopify relacionada.",
  "Plan to receive payments, refunds and payouts.":
    "Prepara la recepción de pagos, reembolsos y desembolsos.",
  "Plan to receive payments and refunds.": "Prepara la recepción de pagos y reembolsos.",
  "Plan to receive contacts, companies and sales opportunities.":
    "Prepara la recepción de contactos, empresas y oportunidades de venta.",
  "Plan to receive enriched product information and categories.":
    "Prepara la recepción de información enriquecida de productos y categorías.",
});

Object.assign(dictionaries.de, {
  "Open received record": "Empfangenen Datensatz öffnen",
  "Open received data to inspect its original content, processing status and recorded links. Sources can contain orders, payments, contacts or products.":
    "Öffne empfangene Daten, um Originalinhalt, Verarbeitungsstand und gespeicherte Verknüpfungen zu sehen. Quellen können Bestellungen, Zahlungen, Kontakte oder Produkte enthalten.",
  "Linked documents": "Verknüpfte Belege",
  "Linked observations": "Verknüpfte Beobachtungen",
  "Linked ledger entries": "Verknüpfte Buchungen",
  "Recorded events and their subjects": "Erfasste Ereignisse und ihre Bezugsdatensätze",
  "Only the first 100 linked records are shown.":
    "Es werden nur die ersten 100 verknüpften Datensätze angezeigt.",
  "Linked records": "Verknüpfte Datensätze",
  "No supported record links are recorded for this source.":
    "Für diese Quelle sind keine unterstützten Datensatzverknüpfungen erfasst.",
  "Linked parties": "Verknüpfte Geschäftspartner",
  "Linked items": "Verknüpfte Artikel",
  "Linked locations": "Verknüpfte Standorte",
  "Linked movements": "Verknüpfte Bewegungen",
});

Object.assign(dictionaries.nl, {
  "Open received record": "Ontvangen record openen",
  "Open received data to inspect its original content, processing status and recorded links. Sources can contain orders, payments, contacts or products.":
    "Open ontvangen gegevens om de originele inhoud, verwerkingsstatus en vastgelegde koppelingen te bekijken. Bronnen kunnen bestellingen, betalingen, contacten of producten bevatten.",
  "Linked documents": "Gekoppelde documenten",
  "Linked observations": "Gekoppelde waarnemingen",
  "Linked ledger entries": "Gekoppelde boekingen",
  "Recorded events and their subjects": "Vastgelegde gebeurtenissen en hun onderwerpen",
  "Only the first 100 linked records are shown.":
    "Alleen de eerste 100 gekoppelde records worden getoond.",
  "Linked records": "Gekoppelde records",
  "No supported record links are recorded for this source.":
    "Voor deze bron zijn geen ondersteunde recordkoppelingen vastgelegd.",
  "Linked parties": "Gekoppelde zakenpartners",
  "Linked items": "Gekoppelde artikelen",
  "Linked locations": "Gekoppelde locaties",
  "Linked movements": "Gekoppelde bewegingen",
});

Object.assign(dictionaries.es, {
  "Open received record": "Abrir registro recibido",
  "Open received data to inspect its original content, processing status and recorded links. Sources can contain orders, payments, contacts or products.":
    "Abre los datos recibidos para ver el contenido original, el estado de procesamiento y los vínculos registrados. Las fuentes pueden contener pedidos, pagos, contactos o productos.",
  "Linked documents": "Documentos vinculados",
  "Linked observations": "Observaciones vinculadas",
  "Linked ledger entries": "Asientos vinculados",
  "Recorded events and their subjects": "Eventos registrados y sus referencias",
  "Only the first 100 linked records are shown.":
    "Solo se muestran los primeros 100 registros vinculados.",
  "Linked records": "Registros vinculados",
  "No supported record links are recorded for this source.":
    "No hay vínculos de registros compatibles registrados para esta fuente.",
  "Linked parties": "Socios comerciales vinculados",
  "Linked items": "Artículos vinculados",
  "Linked locations": "Ubicaciones vinculadas",
  "Linked movements": "Movimientos vinculados",
});

Object.assign(dictionaries.de, {
  "Nothing is recorded until you approve it.": "Nichts wird erfasst, bevor du zustimmst.",
  "Proposed changes, where they came from and what they would record.":
    "Vorgeschlagene Änderungen, ihre Herkunft und was sie erfassen würden.",
  "Search proposed changes": "Vorgeschlagene Änderungen suchen",
  "Proposed by an agent": "Von einem Agenten vorgeschlagen",
  "Prepared by someone in this company": "Von jemandem in diesem Unternehmen vorbereitet",
  "Prepared outside daily work": "Außerhalb der täglichen Arbeit vorbereitet",
  "Every proposed change has been approved or rejected.":
    "Jede vorgeschlagene Änderung ist angenommen oder abgelehnt.",
  "No decision matches this search.": "Keine Entscheidung passt zu dieser Suche.",
  "Start with a decision": "Mit einer Entscheidung anfangen",
  "Open a pending decision to see the change it would make, the records behind it, and then approve or reject it.":
    "Öffne eine offene Entscheidung, um die Änderung und die zugehörigen Datensätze zu sehen, und nimm sie dann an oder lehne sie ab.",
  "A pending decision has changed nothing yet. Rejecting one leaves your records exactly as they are.":
    "Eine offene Entscheidung hat noch nichts geändert. Wer ablehnt, lässt die Datensätze genau so, wie sie sind.",
  "How does a decision arise?": "Wie entsteht eine Entscheidung?",
  "Reality never writes on its own. Every change is proposed first, and a proposal waits here until a person decides on it.":
    "Reality schreibt nie von selbst. Jede Änderung wird zuerst vorgeschlagen, und ein Vorschlag wartet hier, bis ein Mensch darüber entscheidet.",
  "A connected agent proposes a change but cannot carry it out. An action you start in a workspace is also proposed first, and stays here if you leave before deciding.":
    "Ein verbundener Agent schlägt eine Änderung vor, kann sie aber nicht ausführen. Auch eine Aktion, die du in einem Arbeitsbereich startest, wird zuerst vorgeschlagen und bleibt hier liegen, wenn du sie ohne Entscheidung verlässt.",
});

Object.assign(dictionaries.nl, {
  "Nothing is recorded until you approve it.": "Er wordt niets vastgelegd voordat je akkoord gaat.",
  "Proposed changes, where they came from and what they would record.":
    "Voorgestelde wijzigingen, hun herkomst en wat ze zouden vastleggen.",
  "Search proposed changes": "Voorgestelde wijzigingen zoeken",
  "Proposed by an agent": "Voorgesteld door een agent",
  "Prepared by someone in this company": "Voorbereid door iemand in dit bedrijf",
  "Prepared outside daily work": "Buiten het dagelijkse werk voorbereid",
  "Every proposed change has been approved or rejected.":
    "Elke voorgestelde wijziging is goedgekeurd of afgewezen.",
  "No decision matches this search.": "Geen beslissing past bij deze zoekopdracht.",
  "Start with a decision": "Begin met een beslissing",
  "Open a pending decision to see the change it would make, the records behind it, and then approve or reject it.":
    "Open een openstaande beslissing om de wijziging en de onderliggende records te zien, en keur deze vervolgens goed of wijs deze af.",
  "A pending decision has changed nothing yet. Rejecting one leaves your records exactly as they are.":
    "Een openstaande beslissing heeft nog niets gewijzigd. Afwijzen laat je records precies zoals ze zijn.",
  "How does a decision arise?": "Hoe ontstaat een beslissing?",
  "Reality never writes on its own. Every change is proposed first, and a proposal waits here until a person decides on it.":
    "Reality schrijft nooit op eigen initiatief. Elke wijziging wordt eerst voorgesteld en een voorstel wacht hier tot een persoon erover beslist.",
  "A connected agent proposes a change but cannot carry it out. An action you start in a workspace is also proposed first, and stays here if you leave before deciding.":
    "Een verbonden agent stelt een wijziging voor, maar kan die niet uitvoeren. Ook een actie die je in een werkruimte start, wordt eerst voorgesteld en blijft hier staan als je vertrekt zonder te beslissen.",
});

Object.assign(dictionaries.es, {
  "Nothing is recorded until you approve it.": "No se registra nada hasta que lo apruebes.",
  "Proposed changes, where they came from and what they would record.":
    "Cambios propuestos, de dónde vienen y qué registrarían.",
  "Search proposed changes": "Buscar cambios propuestos",
  "Proposed by an agent": "Propuesto por un agente",
  "Prepared by someone in this company": "Preparado por alguien de esta empresa",
  "Prepared outside daily work": "Preparado fuera del trabajo diario",
  "Every proposed change has been approved or rejected.":
    "Todos los cambios propuestos se han aprobado o rechazado.",
  "No decision matches this search.": "Ninguna decisión coincide con esta búsqueda.",
  "Start with a decision": "Empieza por una decisión",
  "Open a pending decision to see the change it would make, the records behind it, and then approve or reject it.":
    "Abre una decisión pendiente para ver el cambio que haría y los registros que lo respaldan, y luego apruébala o recházala.",
  "A pending decision has changed nothing yet. Rejecting one leaves your records exactly as they are.":
    "Una decisión pendiente todavía no ha cambiado nada. Rechazarla deja tus registros exactamente como están.",
  "How does a decision arise?": "¿Cómo surge una decisión?",
  "Reality never writes on its own. Every change is proposed first, and a proposal waits here until a person decides on it.":
    "Reality nunca escribe por su cuenta. Cada cambio se propone primero y una propuesta espera aquí hasta que una persona decide.",
  "A connected agent proposes a change but cannot carry it out. An action you start in a workspace is also proposed first, and stays here if you leave before deciding.":
    "Un agente conectado propone un cambio, pero no puede ejecutarlo. Una acción que inicias en un espacio de trabajo también se propone primero y permanece aquí si te vas sin decidir.",
});

Object.assign(dictionaries.de, {
  "Customer side": "Kundenseite",
  "Supplier side": "Lieferantenseite",
  "Earliest due first": "Früheste Fälligkeit zuerst",
  "Open only": "Nur offen",
  "Due today": "Heute fällig",
  Upcoming: "Später fällig",
  "No due date": "Ohne Fälligkeit",
  "Oldest first": "Älteste zuerst",
  "Action type": "Aktionsart",
  "All actions": "Alle Aktionen",
  "Load more": "Weitere laden",
  "Hold commitment": "Verpflichtung sperren",
  "Release commitment hold": "Sperre der Verpflichtung aufheben",
  "Update party": "Geschäftspartner aktualisieren",
  "Create party": "Geschäftspartner anlegen",
  "Update item": "Artikel aktualisieren",
  "Update location": "Lagerort aktualisieren",
  "Record sales credit": "Kundengutschrift erfassen",
});

Object.assign(dictionaries.nl, {
  "Customer side": "Klantzijde",
  "Supplier side": "Leverancierszijde",
  "Earliest due first": "Vroegste vervaldatum eerst",
  "Open only": "Alleen open",
  "Due today": "Vandaag verschuldigd",
  Upcoming: "Binnenkort",
  "No due date": "Geen vervaldatum",
  "Oldest first": "Oudste eerst",
  "Action type": "Actietype",
  "All actions": "Alle acties",
  "Load more": "Meer laden",
  "Hold commitment": "Toezegging blokkeren",
  "Release commitment hold": "Blokkering vrijgeven",
  "Update party": "Relatie bijwerken",
  "Create party": "Relatie aanmaken",
  "Update item": "Artikel bijwerken",
  "Update location": "Locatie bijwerken",
  "Record sales credit": "Verkoopcredit registreren",
});

Object.assign(dictionaries.es, {
  "Customer side": "Clientes",
  "Supplier side": "Proveedores",
  "Earliest due first": "Vencimiento más próximo primero",
  "Open only": "Solo pendientes",
  "Due today": "Vence hoy",
  Upcoming: "Próximos",
  "No due date": "Sin vencimiento",
  "Oldest first": "Más antiguas primero",
  "Action type": "Tipo de acción",
  "All actions": "Todas las acciones",
  "Load more": "Cargar más",
  "Hold commitment": "Bloquear compromiso",
  "Release commitment hold": "Liberar bloqueo del compromiso",
  "Update party": "Actualizar tercero",
  "Create party": "Crear tercero",
  "Update item": "Actualizar artículo",
  "Update location": "Actualizar ubicación",
  "Record sales credit": "Registrar abono de cliente",
});

Object.assign(dictionaries.de, { Overdue: "Überfällig" });
Object.assign(dictionaries.nl, { Overdue: "Achterstallig" });
Object.assign(dictionaries.es, { Overdue: "Vencido" });

Object.assign(dictionaries.de, {
  "Direct connections": "Direkte Verbindungen",
  "Connections to the left": "Verbindungen links",
  "Connections to the right": "Verbindungen rechts",
  "Connections above": "Verbindungen oberhalb",
  "Connections below": "Verbindungen unterhalb",
});

Object.assign(dictionaries.nl, {
  "Direct connections": "Directe verbindingen",
  "Connections to the left": "Verbindingen links",
  "Connections to the right": "Verbindingen rechts",
  "Connections above": "Verbindingen erboven",
  "Connections below": "Verbindingen eronder",
});

Object.assign(dictionaries.es, {
  "Direct connections": "Conexiones directas",
  "Connections to the left": "Conexiones a la izquierda",
  "Connections to the right": "Conexiones a la derecha",
  "Connections above": "Conexiones arriba",
  "Connections below": "Conexiones abajo",
});

Object.assign(dictionaries.de, {
  Context: "Zusammenhänge",
  Records: "Datensätze",
  Logic: "Logik",
  Activity: "Aktivitäten",
  Timeline: "Zeitverlauf",
  "Record graph": "Datensatzgraph",
  "All records": "Alle Datensätze",
  "Additional fact rules": "Regeln für zusätzliche Fakten",
  "Exception rules": "Ausnahmeregeln",
  "Calculated views": "Berechnete Sichten",
  "Event history": "Ereignisverlauf",
  "Action catalog": "Aktionskatalog",
  "Technical record overview": "Technische Datensatzübersicht",
});

Object.assign(dictionaries.nl, {
  Context: "Samenhang",
  Records: "Records",
  Logic: "Logica",
  Activity: "Activiteiten",
  Timeline: "Tijdlijn",
  "Record graph": "Recordgrafiek",
  "All records": "Alle records",
  "Additional fact rules": "Regels voor aanvullende feiten",
  "Exception rules": "Uitzonderingsregels",
  "Calculated views": "Berekende weergaven",
  "Event history": "Gebeurtenisgeschiedenis",
  "Action catalog": "Actiecatalogus",
  "Technical record overview": "Technisch recordoverzicht",
});

Object.assign(dictionaries.es, {
  Context: "Contexto",
  Records: "Registros",
  Logic: "Lógica",
  Activity: "Actividad",
  Timeline: "Cronología",
  "Record graph": "Grafo de registros",
  "All records": "Todos los registros",
  "Additional fact rules": "Reglas de hechos adicionales",
  "Exception rules": "Reglas de excepciones",
  "Calculated views": "Vistas calculadas",
  "Event history": "Historial de eventos",
  "Action catalog": "Catálogo de acciones",
  "Technical record overview": "Vista técnica de registros",
});

Object.assign(dictionaries.de, {
  Context: "Kontext",
  Facts: "Fakten",
  Rules: "Regeln",
  Actions: "Aktionen",
  "Additional facts": "Zusätzliche Fakten",
});

Object.assign(dictionaries.nl, {
  Context: "Context",
  Facts: "Feiten",
  Rules: "Regels",
  Actions: "Acties",
  "Additional facts": "Aanvullende feiten",
});

Object.assign(dictionaries.es, {
  Context: "Contexto",
  Facts: "Hechos",
  Rules: "Reglas",
  Actions: "Acciones",
  "Additional facts": "Hechos adicionales",
});

Object.assign(dictionaries.de, {
  "Operational accounts": "Operative Konten",
  "Define permitted accounts and defaults for operational postings.":
    "Erlaubte Konten und Standardkonten für operative Buchungen festlegen.",
  "Create minimal operational accounts": "Grundkonten anlegen",
  "Block account": "Konto sperren",
  "Activate account": "Konto aktivieren",
  "Use as default": "Als Standard verwenden",
  "Create account": "Konto anlegen",
  "Confirm account change": "Kontenänderung bestätigen",
  "Customer receivables": "Kundenforderungen",
  "Supplier payables": "Lieferantenverbindlichkeiten",
  "Cash and bank": "Kasse und Bank",
  "Gross sales counterpart": "Gegenkonto Verkauf brutto",
  "Gross purchase counterpart": "Gegenkonto Einkauf brutto",
});

Object.assign(dictionaries.nl, {
  "Operational accounts": "Operationele rekeningen",
  "Define permitted accounts and defaults for operational postings.":
    "Toegestane rekeningen en standaardrekeningen voor operationele boekingen instellen.",
  "Create minimal operational accounts": "Basisrekeningen aanmaken",
  "Block account": "Rekening blokkeren",
  "Activate account": "Rekening activeren",
  "Use as default": "Als standaard gebruiken",
  "Create account": "Rekening aanmaken",
  "Confirm account change": "Rekeningwijziging bevestigen",
  "Customer receivables": "Klantvorderingen",
  "Supplier payables": "Leveranciersschulden",
  "Cash and bank": "Kas en bank",
  "Gross sales counterpart": "Tegenrekening bruto verkoop",
  "Gross purchase counterpart": "Tegenrekening bruto inkoop",
});

Object.assign(dictionaries.es, {
  "Operational accounts": "Cuentas operativas",
  "Define permitted accounts and defaults for operational postings.":
    "Define las cuentas permitidas y predeterminadas para los asientos operativos.",
  "Create minimal operational accounts": "Crear cuentas básicas",
  "Block account": "Bloquear cuenta",
  "Activate account": "Activar cuenta",
  "Use as default": "Usar como predeterminada",
  "Create account": "Crear cuenta",
  "Confirm account change": "Confirmar cambio de cuenta",
  "Customer receivables": "Cuentas por cobrar",
  "Supplier payables": "Cuentas por pagar",
  "Cash and bank": "Caja y bancos",
  "Gross sales counterpart": "Contrapartida de ventas brutas",
  "Gross purchase counterpart": "Contrapartida de compras brutas",
});

Object.assign(dictionaries.de, {
  Blocked: "Gesperrt",
  Loading: "Wird geladen",
  "Request failed": "Anfrage fehlgeschlagen",
});

Object.assign(dictionaries.nl, {
  Blocked: "Geblokkeerd",
  Loading: "Laden",
  "Request failed": "Verzoek mislukt",
});

Object.assign(dictionaries.es, {
  Blocked: "Bloqueada",
  Loading: "Cargando",
  "Request failed": "La solicitud falló",
});

Object.assign(dictionaries.de, {
  Sales: "Verkauf",
  Purchasing: "Einkauf",
  Deliveries: "Lieferungen",
});
Object.assign(dictionaries.nl, {
  Sales: "Verkoop",
  Purchasing: "Inkoop",
  Deliveries: "Leveringen",
});
Object.assign(dictionaries.es, { Sales: "Ventas", Purchasing: "Compras", Deliveries: "Entregas" });

Object.assign(dictionaries.de, { Orders: "Aufträge & Bestellungen" });
Object.assign(dictionaries.nl, { Orders: "Bestellingen" });
Object.assign(dictionaries.es, { Orders: "Pedidos" });

Object.assign(dictionaries.de, {
  "Available customer credit": "Verfügbares Kundenguthaben",
  "Available supplier credit": "Verfügbares Lieferantenguthaben",
  "Original credit": "Ursprüngliches Guthaben",
  "Used credit": "Verwendetes Guthaben",
  "Available credit": "Verfügbares Guthaben",
  "Credit origin / party": "Guthabenherkunft / Geschäftspartner",
});

Object.assign(dictionaries.nl, {
  "Available customer credit": "Beschikbaar klanttegoed",
  "Available supplier credit": "Beschikbaar leverancierstegoed",
  "Original credit": "Oorspronkelijk tegoed",
  "Used credit": "Gebruikt tegoed",
  "Available credit": "Beschikbaar tegoed",
  "Credit origin / party": "Herkomst tegoed / relatie",
});

Object.assign(dictionaries.es, {
  "Available customer credit": "Saldo disponible del cliente",
  "Available supplier credit": "Saldo disponible del proveedor",
  "Original credit": "Saldo original",
  "Used credit": "Saldo utilizado",
  "Available credit": "Saldo disponible",
  "Credit origin / party": "Origen del saldo / tercero",
});

Object.assign(dictionaries.de, { Payment: "Zahlung" });
Object.assign(dictionaries.nl, { Payment: "Betaling" });
Object.assign(dictionaries.es, { Payment: "Pago" });

Object.assign(dictionaries.de, {
  "Accept settlement reduction": "Skonto / Minderung akzeptieren",
  "Record an agreed reduction separately from actual payment.":
    "Eine vereinbarte Minderung getrennt von der tatsächlichen Zahlung erfassen.",
  "Accepted reduction": "Akzeptierte Minderung",
  "Remaining claim": "Verbleibender Anspruch",
  "Cash change": "Geldbewegung",
  "Confirm reduction": "Minderung bestätigen",
  "Configure an active reduction counterpart in company account settings first.":
    "Zuerst ein aktives Gegenkonto für Minderungen in den Firmen-Kontoeinstellungen einrichten.",
  "Stated reduction amount": "Angegebener Minderungsbetrag",
  "Reduction reason": "Minderungsgrund",
  "Early-payment discount": "Skonto",
  "Agreed deduction": "Vereinbarter Einbehalt",
  "Accepted small remainder": "Akzeptierter Kleinrest",
  "Supplier entitlement or agreement": "Berechtigung oder Vereinbarung mit dem Lieferanten",
  "External evidence (optional)": "Externer Nachweis (optional)",
  "Source effect reference": "Vorgangsreferenz im Nachweis",
  "Review reduction": "Minderung prüfen",
});

Object.assign(dictionaries.nl, {
  "Accept settlement reduction": "Betalingsvermindering accepteren",
  "Record an agreed reduction separately from actual payment.":
    "Leg een overeengekomen vermindering afzonderlijk van de werkelijke betaling vast.",
  "Accepted reduction": "Geaccepteerde vermindering",
  "Remaining claim": "Resterende vordering",
  "Cash change": "Geldbeweging",
  "Confirm reduction": "Vermindering bevestigen",
  "Configure an active reduction counterpart in company account settings first.":
    "Stel eerst een actieve tegenrekening voor verminderingen in bij de bedrijfsrekeningen.",
  "Stated reduction amount": "Opgegeven verminderingsbedrag",
  "Reduction reason": "Reden voor vermindering",
  "Early-payment discount": "Betalingskorting",
  "Agreed deduction": "Overeengekomen inhouding",
  "Accepted small remainder": "Geaccepteerd klein restant",
  "Supplier entitlement or agreement": "Recht of overeenkomst met leverancier",
  "External evidence (optional)": "Extern bewijs (optioneel)",
  "Source effect reference": "Referentie in het bewijs",
  "Review reduction": "Vermindering controleren",
});

Object.assign(dictionaries.es, {
  "Accept settlement reduction": "Aceptar reducción del saldo",
  "Record an agreed reduction separately from actual payment.":
    "Registrar una reducción acordada por separado del pago real.",
  "Accepted reduction": "Reducción aceptada",
  "Remaining claim": "Saldo restante",
  "Cash change": "Movimiento de dinero",
  "Confirm reduction": "Confirmar reducción",
  "Configure an active reduction counterpart in company account settings first.":
    "Configure primero una contracuenta activa para reducciones en las cuentas de la empresa.",
  "Stated reduction amount": "Importe indicado de reducción",
  "Reduction reason": "Motivo de reducción",
  "Early-payment discount": "Descuento por pronto pago",
  "Agreed deduction": "Deducción acordada",
  "Accepted small remainder": "Pequeño saldo aceptado",
  "Supplier entitlement or agreement": "Derecho o acuerdo con el proveedor",
  "External evidence (optional)": "Justificante externo (opcional)",
  "Source effect reference": "Referencia del efecto en el justificante",
  "Review reduction": "Revisar reducción",
});

Object.assign(dictionaries.de, { Explanation: "Begründung", Reload: "Neu laden" });
Object.assign(dictionaries.nl, { Explanation: "Toelichting", Reload: "Opnieuw laden" });
Object.assign(dictionaries.es, { Explanation: "Explicación", Reload: "Recargar" });

// Shared action-discovery navigation and directory labels.
Object.assign(dictionaries.de, {
  "Sales & Purchasing": "Verkauf & Einkauf",
  "Orders and commitments": "Aufträge und Zusagen",
  "Delivery holds": "Liefersperren",
  "Return announcements": "Retourenankündigungen",
  "Tracking and expiry": "Rückverfolgung und Haltbarkeit",
  "Customer invoices and credits": "Kundenrechnungen und Gutschriften",
  "Supplier invoices and credits": "Lieferantenrechnungen und Gutschriften",
  "Payments and refunds": "Zahlungen und Erstattungen",
  "Parties, items and locations": "Geschäftspartner, Artikel und Orte",
  "Sources & Evidence": "Quellen & Belege",
  "Integrations and intake": "Integrationen und Import",
  Observations: "Beobachtungen",
  "Members and access": "Mitglieder und Zugriff",
  Unclassified: "Noch nicht zugeordnet",
  "Search action catalog": "Aktionskatalog durchsuchen",
  "Expand all": "Alle aufklappen",
  "Collapse all": "Alle zuklappen",
  "Clear search": "Suche löschen",
  Action: "Aktion",
  Command: "Befehl",
  Mutation: "Änderung",
  "Read only": "Nur lesen",
  "Read-only command. See the supported adapters.": "Lesender Command. Siehe unterstützte Zugänge.",
  "These forms cover opening stock, receipts and shipments.":
    "Diese Formulare decken Anfangsbestand, Wareneingang und Versand ab.",
  "New customer invoice": "Neue Kundenrechnung",
  "New supplier invoice": "Neue Lieferantenrechnung",
  "Record customer payment": "Kundenzahlung erfassen",
  "Record supplier payment": "Lieferantenzahlung erfassen",
  "Manage customers": "Kunden verwalten",
  "Manage suppliers": "Lieferanten verwalten",
  "Manage items": "Artikel verwalten",
  "Manage locations": "Orte verwalten",
  "Manage integrations": "Integrationen verwalten",
  "Manage companies": "Firmen verwalten",
  "Manage members": "Mitglieder verwalten",
  "Manage operational accounts": "Operative Konten verwalten",
  "Manage Demo Data": "Demo-Daten verwalten",
});
Object.assign(dictionaries.nl, {
  "Sales & Purchasing": "Verkoop & Inkoop",
  "Orders and commitments": "Orders en toezeggingen",
  "Delivery holds": "Leveringsblokkades",
  "Return announcements": "Retourmeldingen",
  "Tracking and expiry": "Traceerbaarheid en houdbaarheid",
  "Customer invoices and credits": "Klantfacturen en creditnota’s",
  "Supplier invoices and credits": "Leveranciersfacturen en creditnota’s",
  "Payments and refunds": "Betalingen en terugbetalingen",
  "Parties, items and locations": "Relaties, artikelen en locaties",
  "Sources & Evidence": "Bronnen & Bewijs",
  "Integrations and intake": "Integraties en import",
  Observations: "Waarnemingen",
  "Members and access": "Leden en toegang",
  Unclassified: "Nog niet ingedeeld",
  "Search action catalog": "Actiecatalogus doorzoeken",
  "Expand all": "Alles uitklappen",
  "Collapse all": "Alles inklappen",
  "Clear search": "Zoekopdracht wissen",
  Action: "Actie",
  Command: "Opdracht",
  Mutation: "Wijziging",
  "Read only": "Alleen lezen",
  "Read-only command. See the supported adapters.":
    "Alleen-lezencommand. Zie de ondersteunde adapters.",
  "These forms cover opening stock, receipts and shipments.":
    "Deze formulieren ondersteunen beginvoorraad, ontvangsten en verzendingen.",
  "New customer invoice": "Nieuwe klantfactuur",
  "New supplier invoice": "Nieuwe leveranciersfactuur",
  "Record customer payment": "Klantbetaling vastleggen",
  "Record supplier payment": "Leveranciersbetaling vastleggen",
  "Manage customers": "Klanten beheren",
  "Manage suppliers": "Leveranciers beheren",
  "Manage items": "Artikelen beheren",
  "Manage locations": "Locaties beheren",
  "Manage integrations": "Integraties beheren",
  "Manage companies": "Bedrijven beheren",
  "Manage members": "Leden beheren",
  "Manage operational accounts": "Operationele rekeningen beheren",
  "Manage Demo Data": "Demogegevens beheren",
});
Object.assign(dictionaries.es, {
  "Sales & Purchasing": "Ventas y compras",
  "Orders and commitments": "Pedidos y compromisos",
  "Delivery holds": "Bloqueos de entrega",
  "Return announcements": "Anuncios de devolución",
  "Tracking and expiry": "Trazabilidad y caducidad",
  "Customer invoices and credits": "Facturas y abonos de clientes",
  "Supplier invoices and credits": "Facturas y abonos de proveedores",
  "Payments and refunds": "Pagos y reembolsos",
  "Parties, items and locations": "Contactos, artículos y ubicaciones",
  "Sources & Evidence": "Fuentes y evidencias",
  "Integrations and intake": "Integraciones e importación",
  Observations: "Observaciones",
  "Members and access": "Miembros y acceso",
  Unclassified: "Sin clasificar",
  "Search action catalog": "Buscar en el catálogo de acciones",
  "Expand all": "Expandir todo",
  "Collapse all": "Contraer todo",
  "Clear search": "Borrar búsqueda",
  Action: "Acción",
  Command: "Comando",
  Mutation: "Modificación",
  "Read only": "Solo lectura",
  "Read-only command. See the supported adapters.":
    "Comando de solo lectura. Consulte los adaptadores compatibles.",
  "These forms cover opening stock, receipts and shipments.":
    "Estos formularios cubren existencias iniciales, recepciones y envíos.",
  "New customer invoice": "Nueva factura de cliente",
  "New supplier invoice": "Nueva factura de proveedor",
  "Record customer payment": "Registrar pago de cliente",
  "Record supplier payment": "Registrar pago a proveedor",
  "Manage customers": "Gestionar clientes",
  "Manage suppliers": "Gestionar proveedores",
  "Manage items": "Gestionar artículos",
  "Manage locations": "Gestionar ubicaciones",
  "Manage integrations": "Gestionar integraciones",
  "Manage companies": "Gestionar empresas",
  "Manage members": "Gestionar miembros",
  "Manage operational accounts": "Gestionar cuentas operativas",
  "Manage Demo Data": "Gestionar datos de demostración",
});

Object.assign(dictionaries.de, {
  "Manage settlement reductions": "Forderungsminderungen verwalten",
});
Object.assign(dictionaries.nl, {
  "Manage settlement reductions": "Betalingsverminderingen beheren",
});
Object.assign(dictionaries.es, {
  "Manage settlement reductions": "Gestionar reducciones del saldo",
});

Object.assign(dictionaries.de, {
  "Record payment and allocation": "Zahlung erfassen und zuordnen",
  "Use available credit": "Guthaben verwenden",
  "Record actual money and explicit allocations. Any unaccepted shortfall stays open.":
    "Tatsächliche Zahlungen und Zuordnungen erfassen. Nicht akzeptierte Minderbeträge bleiben offen.",
  "Settlement recorded": "Ausgleich erfasst",
  "Money received": "Geld erhalten",
  "Money paid": "Geld gezahlt",
  "Remaining available credit": "Verbleibendes Guthaben",
  "Explain invoice": "Rechnung erklären",
  "Explain credit": "Guthaben erklären",
  "Confirm settlement": "Ausgleich bestätigen",
  "Credit action": "Guthabenaktion",
  "Allocate to invoice": "Mit Rechnung verrechnen",
  "Record customer credit refund": "Erstattung an Kunden erfassen",
  "Record supplier credit refund": "Erstattung vom Lieferanten erfassen",
  "Find matching invoice": "Passende Rechnung suchen",
  "Refine the search to find more matching invoices.":
    "Suche eingrenzen, um weitere passende Rechnungen zu finden.",
  "Actual cash amount": "Tatsächlicher Zahlbetrag",
  "Amount allocated to this invoice": "Dieser Rechnung zugeordneter Betrag",
  "Also accept a stated reduction": "Zusätzlich angegebene Minderung akzeptieren",
  "Actual payment reference": "Referenz der tatsächlichen Zahlung",
  "Actual payment time (with timezone)": "Tatsächlicher Zahlungszeitpunkt (mit Zeitzone)",
  "Review settlement": "Ausgleich prüfen",
});

Object.assign(dictionaries.nl, {
  "Record payment and allocation": "Betaling vastleggen en toewijzen",
  "Use available credit": "Beschikbaar tegoed gebruiken",
  "Record actual money and explicit allocations. Any unaccepted shortfall stays open.":
    "Leg werkelijke betalingen en toewijzingen vast. Niet-geaccepteerde tekorten blijven open.",
  "Settlement recorded": "Verrekening vastgelegd",
  "Money received": "Geld ontvangen",
  "Money paid": "Geld betaald",
  "Remaining available credit": "Resterend tegoed",
  "Explain invoice": "Factuur toelichten",
  "Explain credit": "Tegoed toelichten",
  "Confirm settlement": "Verrekening bevestigen",
  "Credit action": "Tegoedactie",
  "Allocate to invoice": "Met factuur verrekenen",
  "Record customer credit refund": "Terugbetaling aan klant vastleggen",
  "Record supplier credit refund": "Terugbetaling van leverancier vastleggen",
  "Find matching invoice": "Passende factuur zoeken",
  "Refine the search to find more matching invoices.":
    "Verfijn de zoekopdracht om meer passende facturen te vinden.",
  "Actual cash amount": "Werkelijk betaald bedrag",
  "Amount allocated to this invoice": "Aan deze factuur toegewezen bedrag",
  "Also accept a stated reduction": "Ook een opgegeven vermindering accepteren",
  "Actual payment reference": "Referentie van werkelijke betaling",
  "Actual payment time (with timezone)": "Werkelijk betalingstijdstip (met tijdzone)",
  "Review settlement": "Verrekening controleren",
});

Object.assign(dictionaries.es, {
  "Record payment and allocation": "Registrar y asignar pago",
  "Use available credit": "Usar saldo disponible",
  "Record actual money and explicit allocations. Any unaccepted shortfall stays open.":
    "Registra pagos reales y asignaciones explícitas. Las diferencias no aceptadas quedan pendientes.",
  "Settlement recorded": "Liquidación registrada",
  "Money received": "Dinero recibido",
  "Money paid": "Dinero pagado",
  "Remaining available credit": "Saldo disponible restante",
  "Explain invoice": "Explicar factura",
  "Explain credit": "Explicar saldo",
  "Confirm settlement": "Confirmar liquidación",
  "Credit action": "Acción sobre el saldo",
  "Allocate to invoice": "Asignar a factura",
  "Record customer credit refund": "Registrar devolución al cliente",
  "Record supplier credit refund": "Registrar devolución del proveedor",
  "Find matching invoice": "Buscar factura compatible",
  "Refine the search to find more matching invoices.":
    "Acota la búsqueda para encontrar más facturas compatibles.",
  "Actual cash amount": "Importe real del pago",
  "Amount allocated to this invoice": "Importe asignado a esta factura",
  "Also accept a stated reduction": "Aceptar también una reducción indicada",
  "Actual payment reference": "Referencia del pago real",
  "Actual payment time (with timezone)": "Fecha y hora del pago real (con zona horaria)",
  "Review settlement": "Revisar liquidación",
});

Object.assign(dictionaries.de, {
  "Allocated amount": "Zugeordneter Betrag",
  Refund: "Erstattung",
  "Select invoice": "Rechnung auswählen",
});

Object.assign(dictionaries.nl, {
  "Allocated amount": "Toegewezen bedrag",
  Refund: "Terugbetaling",
  "Select invoice": "Factuur selecteren",
});

Object.assign(dictionaries.es, {
  "Allocated amount": "Importe asignado",
  Refund: "Devolución",
  "Select invoice": "Seleccionar factura",
});

Object.assign(dictionaries.de, {
  "All sources matching the source type": "Alle Quellen dieses Quelltyps",
  "Allowed values (comma-separated)": "Erlaubte Werte (durch Komma getrennt)",
  "Confirm this change for the selected company and rule.":
    "Diese Änderung für die ausgewählte Firma und Regel bestätigen.",
  "Current line": "Aktuelle Position",
  "Fact output": "Faktausgabe",
  "Fact value": "Faktwert",
  "Field scope": "Feldbezug",
  "Output scope": "Ausgabebezug",
  "Fix the technical definition to reopen the guided editor.":
    "Die technische Definition korrigieren, um den Formular-Editor wieder zu öffnen.",
  "More sources remain": "Weitere Quellen vorhanden",
  "Observation time": "Beobachtungszeitpunkt",
  "Open source": "Quelle öffnen",
  "Prepare implementation package": "Umsetzungspaket vorbereiten",
  "Preview of up to 100 sources. No business data is changed.":
    "Vorschau für bis zu 100 Quellen. Geschäftsdaten werden nicht verändert.",
  "Read a source field": "Ein Quellfeld lesen",
  Reason: "Begründung",
  "Replay complete": "Historische Verarbeitung abgeschlossen",
  "Rule name": "Regelname",
  "Source and subject": "Quelle und Zuordnung",
  "Supporting examples": "Belegende Beispiele",
  "Use a fixed value": "Einen festen Wert verwenden",
  "Value type": "Werttyp",
  "When the source was received": "Beim Eingang der Quelle",
  "Whole source": "Gesamte Quelle",
  "Source line ID path": "Pfad zur Quellpositions-ID",
  "Matching observations in this preview": "Passende Beobachtungen in dieser Vorschau",
  "Invalid values": "Ungültige Werte",
  "Ambiguous subjects": "Mehrdeutige Zuordnungen",
  "Existing facts": "Bereits vorhandene Fakten",
  "Conditions match": "Bedingungen treffen zu",
  "Add evidence": "Beleg hinzufügen",
  "Choose interpretation": "Einordnung wählen",
  "Enter true or false.": "true oder false eingeben.",
  "Enter a whole number within the supported range.":
    "Eine ganze Zahl im unterstützten Bereich eingeben.",
  "Enter a decimal number.": "Eine Dezimalzahl eingeben.",
  "Enter a valid date or date and time.": "Ein gültiges Datum oder Datum mit Uhrzeit eingeben.",
  "Enter at least one comparison value.": "Mindestens einen Vergleichswert eingeben.",
  "Complete the rule name, source and Fact fields.": "Regelname, Quelle und Faktfelder ausfüllen.",
  "Enter a valid source field path.": "Einen gültigen Quellfeldpfad eingeben.",
  "A condition group cannot be empty.": "Eine Bedingungsgruppe darf nicht leer sein.",
  "Use nonempty condition groups within three levels.":
    "Bedingungsgruppen mit Inhalt und höchstens drei Ebenen verwenden.",
  "A rule supports at most 20 conditions.": "Eine Regel unterstützt höchstens 20 Bedingungen.",
  "Choose a supported comparison.": "Einen unterstützten Vergleich wählen.",
});
Object.assign(dictionaries.nl, {
  "All sources matching the source type": "Alle bronnen van dit brontype",
  "Allowed values (comma-separated)": "Toegestane waarden (gescheiden door komma's)",
  "Confirm this change for the selected company and rule.":
    "Bevestig deze wijziging voor het geselecteerde bedrijf en de regel.",
  "Current line": "Huidige regel",
  "Fact output": "Feituitvoer",
  "Fact value": "Feitwaarde",
  "Field scope": "Veldbereik",
  "Output scope": "Uitvoerbereik",
  "Fix the technical definition to reopen the guided editor.":
    "Corrigeer de technische definitie om de formuliereditor opnieuw te openen.",
  "More sources remain": "Er zijn meer bronnen",
  "Observation time": "Waarnemingstijd",
  "Open source": "Bron openen",
  "Prepare implementation package": "Implementatiepakket voorbereiden",
  "Preview of up to 100 sources. No business data is changed.":
    "Voorbeeld van maximaal 100 bronnen. Bedrijfsgegevens worden niet gewijzigd.",
  "Read a source field": "Een bronveld lezen",
  Reason: "Reden",
  "Replay complete": "Historische verwerking voltooid",
  "Rule name": "Regelnaam",
  "Source and subject": "Bron en koppeling",
  "Supporting examples": "Ondersteunende voorbeelden",
  "Use a fixed value": "Een vaste waarde gebruiken",
  "Value type": "Waardetype",
  "When the source was received": "Bij ontvangst van de bron",
  "Whole source": "Gehele bron",
  "Source line ID path": "Pad naar bronregel-ID",
  "Matching observations in this preview": "Overeenkomende waarnemingen in dit voorbeeld",
  "Invalid values": "Ongeldige waarden",
  "Ambiguous subjects": "Onduidelijke koppelingen",
  "Existing facts": "Bestaande feiten",
  "Conditions match": "Voorwaarden komen overeen",
  "Add evidence": "Bewijs toevoegen",
  "Choose interpretation": "Interpretatie kiezen",
  "Enter true or false.": "Voer true of false in.",
  "Enter a whole number within the supported range.":
    "Voer een geheel getal binnen het ondersteunde bereik in.",
  "Enter a decimal number.": "Voer een decimaal getal in.",
  "Enter a valid date or date and time.": "Voer een geldige datum of datum en tijd in.",
  "Enter at least one comparison value.": "Voer minimaal één vergelijkingswaarde in.",
  "Complete the rule name, source and Fact fields.": "Vul de regelnaam, bron en feitvelden in.",
  "Enter a valid source field path.": "Voer een geldig bronveldpad in.",
  "A condition group cannot be empty.": "Een voorwaardengroep mag niet leeg zijn.",
  "Use nonempty condition groups within three levels.":
    "Gebruik gevulde voorwaardengroepen binnen drie niveaus.",
  "A rule supports at most 20 conditions.": "Een regel ondersteunt maximaal 20 voorwaarden.",
  "Choose a supported comparison.": "Kies een ondersteunde vergelijking.",
});
Object.assign(dictionaries.es, {
  "All sources matching the source type": "Todas las fuentes de este tipo",
  "Allowed values (comma-separated)": "Valores permitidos (separados por comas)",
  "Confirm this change for the selected company and rule.":
    "Confirma este cambio para la empresa y regla seleccionadas.",
  "Current line": "Línea actual",
  "Fact output": "Salida del hecho",
  "Fact value": "Valor del hecho",
  "Field scope": "Ámbito del campo",
  "Output scope": "Ámbito de salida",
  "Fix the technical definition to reopen the guided editor.":
    "Corrige la definición técnica para volver a abrir el editor guiado.",
  "More sources remain": "Quedan más fuentes",
  "Observation time": "Momento de observación",
  "Open source": "Abrir fuente",
  "Prepare implementation package": "Preparar paquete de implementación",
  "Preview of up to 100 sources. No business data is changed.":
    "Vista previa de hasta 100 fuentes. No se modifican datos empresariales.",
  "Read a source field": "Leer un campo de origen",
  Reason: "Motivo",
  "Replay complete": "Procesamiento histórico completado",
  "Rule name": "Nombre de la regla",
  "Source and subject": "Fuente y asignación",
  "Supporting examples": "Ejemplos de respaldo",
  "Use a fixed value": "Usar un valor fijo",
  "Value type": "Tipo de valor",
  "When the source was received": "Al recibir la fuente",
  "Whole source": "Fuente completa",
  "Source line ID path": "Ruta del ID de línea de origen",
  "Matching observations in this preview": "Observaciones coincidentes en esta vista previa",
  "Invalid values": "Valores no válidos",
  "Ambiguous subjects": "Asignaciones ambiguas",
  "Existing facts": "Hechos existentes",
  "Conditions match": "Se cumplen las condiciones",
  "Add evidence": "Añadir evidencia",
  "Choose interpretation": "Elegir interpretación",
  "Enter true or false.": "Introduce true o false.",
  "Enter a whole number within the supported range.":
    "Introduce un número entero dentro del rango admitido.",
  "Enter a decimal number.": "Introduce un número decimal.",
  "Enter a valid date or date and time.": "Introduce una fecha o fecha y hora válidas.",
  "Enter at least one comparison value.": "Introduce al menos un valor de comparación.",
  "Complete the rule name, source and Fact fields.":
    "Completa el nombre de la regla, la fuente y los campos del hecho.",
  "Enter a valid source field path.": "Introduce una ruta de campo de origen válida.",
  "A condition group cannot be empty.": "Un grupo de condiciones no puede estar vacío.",
  "Use nonempty condition groups within three levels.":
    "Usa grupos con condiciones dentro de tres niveles.",
  "A rule supports at most 20 conditions.": "Una regla admite un máximo de 20 condiciones.",
  "Choose a supported comparison.": "Elige una comparación admitida.",
});
Object.assign(dictionaries.de, {
  "This processes one batch of historical sources and may create Facts.":
    "Dies verarbeitet einen Stapel historischer Quellen und kann Fakten anlegen.",
});
Object.assign(dictionaries.nl, {
  "This processes one batch of historical sources and may create Facts.":
    "Dit verwerkt één reeks historische bronnen en kan feiten aanmaken.",
});
Object.assign(dictionaries.es, {
  "This processes one batch of historical sources and may create Facts.":
    "Esto procesa un lote de fuentes históricas y puede crear hechos.",
});
Object.assign(dictionaries.de, {
  "Iteration path": "Pfad zur Positionsliste",
  "Source value path": "Pfad zum Quellwert",
  "Constant value": "Fester Wert",
  "Observation time path": "Pfad zum Beobachtungszeitpunkt",
  Conflicts: "Konflikte",
  "Invalid rule definition.": "Ungültige Regeldefinition.",
});
Object.assign(dictionaries.nl, {
  "Iteration path": "Pad naar de regellijst",
  "Source value path": "Pad naar bronwaarde",
  "Constant value": "Vaste waarde",
  "Observation time path": "Pad naar waarnemingstijd",
  Conflicts: "Conflicten",
  "Invalid rule definition.": "Ongeldige regeldefinitie.",
});
Object.assign(dictionaries.es, {
  "Iteration path": "Ruta de la lista de líneas",
  "Source value path": "Ruta del valor de origen",
  "Constant value": "Valor fijo",
  "Observation time path": "Ruta del momento de observación",
  Conflicts: "Conflictos",
  "Invalid rule definition.": "Definición de regla no válida.",
});

Object.assign(dictionaries.de, {
  "Set up rule": "Regel einrichten",
  "The question is recorded. Set up when this observation should be remembered.":
    "Die Frage ist erfasst. Lege jetzt fest, wann diese Beobachtung gemerkt werden soll.",
  "Your rule in words": "Deine Regel in Worten",
  "When does the rule apply?": "Wann gilt die Regel?",
  "What should be remembered?": "Was soll gemerkt werden?",
  "Test with examples": "Mit Beispielen prüfen",
  "Review changes": "Änderungen prüfen",
  "Source examples and evidence": "Quellenbeispiele und Belege",
  "Rule details": "Regeldetails",
  "Tests use a saved version. Review and save your changes before testing them.":
    "Geprüft wird eine gespeicherte Version. Prüfe und speichere deine Änderungen, bevor du sie testest.",
  "Review and save a draft first. Then test it with the sources already in Reality.":
    "Prüfe und speichere zuerst einen Entwurf. Danach kannst du ihn mit vorhandenen Quellen in Reality testen.",
  "Complete the rule below.": "Vervollständige die Regel unten.",
  "Choose a source, a characteristic and a value to complete this rule.":
    "Wähle eine Quelle, ein Merkmal und einen Wert, um die Regel zu vervollständigen.",
  "For {source}, when {conditions}, remember {fact} for {subject}.":
    "Für {source}: Wenn {conditions}, merke dir {fact} für {subject}.",
  "the source matches": "die Quelle passt",
  "the delivery commitment": "die Lieferzusage",
  "each matching order line": "jede passende Auftragsposition",
  "Delivery commitment": "Lieferzusage",
  Characteristic: "Merkmal",
  "Record type": "Art des Datensatzes",
  "Source field": "Quellfeld",
  "Value comes from": "Wert stammt aus",
  "Applies to": "Gilt für",
  "Choose a value": "Wert wählen",
  "Choose a field": "Feld wählen",
  Field: "Feld",
  Comparison: "Vergleich",
  " and ": " und ",
  " or ": " oder ",
});

Object.assign(dictionaries.nl, {
  "Set up rule": "Regel instellen",
  "The question is recorded. Set up when this observation should be remembered.":
    "De vraag is vastgelegd. Stel nu in wanneer deze waarneming moet worden onthouden.",
  "Your rule in words": "Je regel in woorden",
  "When does the rule apply?": "Wanneer geldt de regel?",
  "What should be remembered?": "Wat moet worden onthouden?",
  "Test with examples": "Testen met voorbeelden",
  "Review changes": "Wijzigingen controleren",
  "Source examples and evidence": "Bronvoorbeelden en bewijs",
  "Rule details": "Regeldetails",
  "Tests use a saved version. Review and save your changes before testing them.":
    "Tests gebruiken een opgeslagen versie. Controleer en sla je wijzigingen op voordat je ze test.",
  "Review and save a draft first. Then test it with the sources already in Reality.":
    "Controleer en bewaar eerst een concept. Test het daarna met bestaande bronnen in Reality.",
  "Complete the rule below.": "Vul de regel hieronder aan.",
  "Choose a source, a characteristic and a value to complete this rule.":
    "Kies een bron, een kenmerk en een waarde om de regel te voltooien.",
  "For {source}, when {conditions}, remember {fact} for {subject}.":
    "Voor {source}: als {conditions}, onthoud {fact} voor {subject}.",
  "the source matches": "de bron overeenkomt",
  "the delivery commitment": "de leveringsverplichting",
  "each matching order line": "elke passende orderregel",
  "Delivery commitment": "Leveringsverplichting",
  Characteristic: "Kenmerk",
  "Record type": "Recordtype",
  "Source field": "Bronveld",
  "Value comes from": "Waarde komt uit",
  "Applies to": "Geldt voor",
  "Choose a value": "Waarde kiezen",
  "Choose a field": "Veld kiezen",
  Field: "Veld",
  Comparison: "Vergelijking",
  " and ": " en ",
  " or ": " of ",
});

Object.assign(dictionaries.es, {
  "Set up rule": "Configurar regla",
  "The question is recorded. Set up when this observation should be remembered.":
    "La pregunta está registrada. Define cuándo debe recordarse esta observación.",
  "Your rule in words": "Tu regla en palabras",
  "When does the rule apply?": "¿Cuándo se aplica la regla?",
  "What should be remembered?": "¿Qué debe recordarse?",
  "Test with examples": "Probar con ejemplos",
  "Review changes": "Revisar cambios",
  "Source examples and evidence": "Ejemplos de fuentes y evidencias",
  "Rule details": "Detalles de la regla",
  "Tests use a saved version. Review and save your changes before testing them.":
    "Las pruebas usan una versión guardada. Revisa y guarda tus cambios antes de probarlos.",
  "Review and save a draft first. Then test it with the sources already in Reality.":
    "Primero revisa y guarda un borrador. Después pruébalo con las fuentes existentes en Reality.",
  "Complete the rule below.": "Completa la regla a continuación.",
  "Choose a source, a characteristic and a value to complete this rule.":
    "Elige una fuente, una característica y un valor para completar la regla.",
  "For {source}, when {conditions}, remember {fact} for {subject}.":
    "Para {source}: cuando {conditions}, recuerda {fact} para {subject}.",
  "the source matches": "la fuente coincide",
  "the delivery commitment": "el compromiso de entrega",
  "each matching order line": "cada línea de pedido coincidente",
  "Delivery commitment": "Compromiso de entrega",
  Characteristic: "Característica",
  "Record type": "Tipo de registro",
  "Source field": "Campo de origen",
  "Value comes from": "El valor proviene de",
  "Applies to": "Se aplica a",
  "Choose a value": "Elegir valor",
  "Choose a field": "Elegir campo",
  Field: "Campo",
  Comparison: "Comparación",
  " and ": " y ",
  " or ": " o ",
});

Object.assign(dictionaries.de, {
  "Check with examples": "An Beispielen prüfen",
  "Further details": "Weitere Details",
  "This rule could not be loaded. Close the dialog and try again.":
    "Diese Regel konnte nicht geladen werden. Schließe den Dialog und versuche es erneut.",
});

Object.assign(dictionaries.nl, {
  "Check with examples": "Controleren met voorbeelden",
  "Further details": "Meer details",
  "This rule could not be loaded. Close the dialog and try again.":
    "Deze regel kon niet worden geladen. Sluit het venster en probeer het opnieuw.",
});

Object.assign(dictionaries.es, {
  "Check with examples": "Comprobar con ejemplos",
  "Further details": "Más detalles",
  "This rule could not be loaded. Close the dialog and try again.":
    "No se pudo cargar esta regla. Cierra el diálogo e inténtalo de nuevo.",
});

Object.assign(dictionaries.de, {
  "Import opening positions": "Startbestände übernehmen",
  "Enter outstanding amounts from the previous system. Opening positions create no payment, revenue or tax.":
    "Erfasse offene Beträge aus dem bisherigen System. Startbestände erzeugen keine Zahlung, keinen Umsatz und keine Steuer.",
  "Customer opening debt": "Offene Kundenforderung",
  "Customer opening credit": "Startguthaben des Kunden",
  "Supplier opening debt": "Offene Lieferantenverbindlichkeit",
  "Supplier opening credit": "Startguthaben beim Lieferanten",
  "Opening positions recorded": "Startbestände übernommen",
  "Neutral opening counterpart": "Neutrales Gegenkonto für Startbestände",
  "Neutral opening subledger counterpart": "Neutrales Nebenbuch-Gegenkonto für Startbestände",
  "Unknown due dates": "Unbekannte Fälligkeiten",
  "Confirm opening positions": "Startbestände bestätigen",
  "Configure an active opening counterpart in company account settings first.":
    "Richte zuerst ein aktives Gegenkonto für Startbestände in den Konteneinstellungen der Firma ein.",
  "Previous system": "Bisheriges System",
  "Snapshot reference": "Referenz des Datenstands",
  "Cutover date": "Übernahmestichtag",
  "Opening coverage": "Umfang der Übernahme",
  "Individual positions": "Einzelposten",
  "Summary per party and direction": "Summe je Partner und Richtung",
  "Find party": "Geschäftspartner suchen",
  "Refine the search to find more parties.":
    "Grenze die Suche ein, um weitere Geschäftspartner zu finden.",
  "Opening position": "Startbestand",
  "Opening direction": "Art des Startbestands",
  "Outstanding amount at cutover": "Offener Betrag am Stichtag",
  "Stable original item reference": "Eindeutige Postenreferenz im Altsystem",
  "Document reference": "Belegreferenz",
  "Original evidence (optional)": "Ursprüngliche Nachweise (optional)",
  "Original document date": "Ursprüngliches Belegdatum",
  "Original due date": "Ursprüngliche Fälligkeit",
  "Original total": "Ursprünglicher Gesamtbetrag",
  "Add opening position": "Startbestand hinzufügen",
  "Review opening positions": "Startbestände prüfen",
});

Object.assign(dictionaries.nl, {
  "Import opening positions": "Beginposities overnemen",
  "Enter outstanding amounts from the previous system. Opening positions create no payment, revenue or tax.":
    "Voer openstaande bedragen uit het vorige systeem in. Beginposities maken geen betaling, omzet of belasting aan.",
  "Customer opening debt": "Openstaande klantvordering",
  "Customer opening credit": "Beginsaldo klanttegoed",
  "Supplier opening debt": "Openstaande leveranciersschuld",
  "Supplier opening credit": "Beginsaldo leverancierstegoed",
  "Opening positions recorded": "Beginposities vastgelegd",
  "Neutral opening counterpart": "Neutrale tegenrekening voor beginposities",
  "Neutral opening subledger counterpart":
    "Neutrale subadministratieve tegenrekening voor beginposities",
  "Unknown due dates": "Onbekende vervaldata",
  "Confirm opening positions": "Beginposities bevestigen",
  "Configure an active opening counterpart in company account settings first.":
    "Stel eerst een actieve tegenrekening voor beginposities in bij de bedrijfsrekeningen.",
  "Previous system": "Vorig systeem",
  "Snapshot reference": "Referentie van momentopname",
  "Cutover date": "Overnamedatum",
  "Opening coverage": "Dekking van de overname",
  "Individual positions": "Individuele posten",
  "Summary per party and direction": "Totaal per relatie en richting",
  "Find party": "Relatie zoeken",
  "Refine the search to find more parties.": "Verfijn de zoekopdracht om meer relaties te vinden.",
  "Opening position": "Beginpositie",
  "Opening direction": "Soort beginpositie",
  "Outstanding amount at cutover": "Openstaand bedrag op overnamedatum",
  "Stable original item reference": "Vaste oorspronkelijke postreferentie",
  "Document reference": "Documentreferentie",
  "Original evidence (optional)": "Oorspronkelijk bewijs (optioneel)",
  "Original document date": "Oorspronkelijke documentdatum",
  "Original due date": "Oorspronkelijke vervaldatum",
  "Original total": "Oorspronkelijk totaal",
  "Add opening position": "Beginpositie toevoegen",
  "Review opening positions": "Beginposities controleren",
});

Object.assign(dictionaries.es, {
  "Import opening positions": "Importar saldos iniciales",
  "Enter outstanding amounts from the previous system. Opening positions create no payment, revenue or tax.":
    "Introduce los importes pendientes del sistema anterior. Los saldos iniciales no generan pagos, ingresos ni impuestos.",
  "Customer opening debt": "Deuda inicial del cliente",
  "Customer opening credit": "Crédito inicial del cliente",
  "Supplier opening debt": "Deuda inicial con proveedor",
  "Supplier opening credit": "Crédito inicial con proveedor",
  "Opening positions recorded": "Saldos iniciales registrados",
  "Neutral opening counterpart": "Contrapartida neutral de apertura",
  "Neutral opening subledger counterpart": "Contrapartida neutral de apertura del libro auxiliar",
  "Unknown due dates": "Vencimientos desconocidos",
  "Confirm opening positions": "Confirmar saldos iniciales",
  "Configure an active opening counterpart in company account settings first.":
    "Configura primero una contrapartida de apertura activa en las cuentas de la empresa.",
  "Previous system": "Sistema anterior",
  "Snapshot reference": "Referencia de la instantánea",
  "Cutover date": "Fecha de corte",
  "Opening coverage": "Cobertura de apertura",
  "Individual positions": "Partidas individuales",
  "Summary per party and direction": "Resumen por tercero y sentido",
  "Find party": "Buscar tercero",
  "Refine the search to find more parties.": "Refina la búsqueda para encontrar más terceros.",
  "Opening position": "Saldo inicial",
  "Opening direction": "Tipo de saldo inicial",
  "Outstanding amount at cutover": "Importe pendiente en la fecha de corte",
  "Stable original item reference": "Referencia estable de la partida original",
  "Document reference": "Referencia del documento",
  "Original evidence (optional)": "Evidencia original (opcional)",
  "Original document date": "Fecha del documento original",
  "Original due date": "Vencimiento original",
  "Original total": "Total original",
  "Add opening position": "Añadir saldo inicial",
  "Review opening positions": "Revisar saldos iniciales",
});

Object.assign(dictionaries.de, { "Select party": "Geschäftspartner auswählen" });
Object.assign(dictionaries.nl, { "Select party": "Relatie selecteren" });
Object.assign(dictionaries.es, { "Select party": "Seleccionar tercero" });

Object.assign(dictionaries.de, { "Summary opening position": "Summierter Startbestand" });
Object.assign(dictionaries.nl, { "Summary opening position": "Samengevatte beginpositie" });
Object.assign(dictionaries.es, { "Summary opening position": "Saldo inicial resumido" });

Object.assign(dictionaries.de, {
  "Finance references": "Finanzreferenzen",
  "Manage finance references": "Finanzreferenzen verwalten",
  "Cost centers": "Kostenstellen",
  "Case codes": "Fallcodes",
  "Coding groups": "Kontierungsgruppen",
  "Define cost centers, case codes and coding groups for internal classification.":
    "Kostenstellen, Fallcodes und Kontierungsgruppen für interne Zuordnungen definieren.",
  "Codes are permanent. Block unused references to preserve their history.":
    "Codes bleiben dauerhaft bestehen. Nicht mehr benötigte Referenzen sperren, damit die Historie erhalten bleibt.",
  "Reference type": "Referenztyp",
  "Search references": "Referenzen suchen",
  "Reference status filter": "Referenzen nach Status filtern",
  "Reference status": "Referenzstatus",
  "No matching references": "Keine passenden Referenzen",
  References: "Referenzen",
  "New reference": "Neue Referenz",
  "Review reference change": "Referenzänderung prüfen",
  "Confirm reference change": "Referenzänderung bestätigen",
  "Reference saved": "Referenz gespeichert",
  "Reference history": "Referenzhistorie",
  Revision: "Revision",
  Actor: "Ausgeführt durch",
});

Object.assign(dictionaries.nl, {
  "Finance references": "Financiële referenties",
  "Manage finance references": "Financiële referenties beheren",
  "Cost centers": "Kostenplaatsen",
  "Case codes": "Gevalcodes",
  "Coding groups": "Coderingsgroepen",
  "Define cost centers, case codes and coding groups for internal classification.":
    "Definieer kostenplaatsen, gevalcodes en coderingsgroepen voor interne classificatie.",
  "Codes are permanent. Block unused references to preserve their history.":
    "Codes zijn permanent. Blokkeer ongebruikte referenties om hun historie te behouden.",
  "Reference type": "Referentietype",
  "Search references": "Referenties zoeken",
  "Reference status filter": "Referentiestatusfilter",
  "Reference status": "Referentiestatus",
  "No matching references": "Geen overeenkomende referenties",
  References: "Referenties",
  "New reference": "Nieuwe referentie",
  "Review reference change": "Referentiewijziging controleren",
  "Confirm reference change": "Referentiewijziging bevestigen",
  "Reference saved": "Referentie opgeslagen",
  "Reference history": "Referentiehistorie",
  Revision: "Revisie",
  Actor: "Uitgevoerd door",
});

Object.assign(dictionaries.es, {
  "Finance references": "Referencias financieras",
  "Manage finance references": "Gestionar referencias financieras",
  "Cost centers": "Centros de coste",
  "Case codes": "Códigos de caso",
  "Coding groups": "Grupos de imputación",
  "Define cost centers, case codes and coding groups for internal classification.":
    "Define centros de coste, códigos de caso y grupos de imputación para la clasificación interna.",
  "Codes are permanent. Block unused references to preserve their history.":
    "Los códigos son permanentes. Bloquea las referencias que no uses para conservar su historial.",
  "Reference type": "Tipo de referencia",
  "Search references": "Buscar referencias",
  "Reference status filter": "Filtro de estado de referencias",
  "Reference status": "Estado de referencia",
  "No matching references": "No hay referencias coincidentes",
  References: "Referencias",
  "New reference": "Nueva referencia",
  "Review reference change": "Revisar cambio de referencia",
  "Confirm reference change": "Confirmar cambio de referencia",
  "Reference saved": "Referencia guardada",
  "Reference history": "Historial de referencia",
  Revision: "Revisión",
  Actor: "Ejecutado por",
});

Object.assign(dictionaries.de, { Revision: "Änderungsstand" });
Object.assign(dictionaries.nl, { Before: "Voor", After: "Na" });
Object.assign(dictionaries.es, { Before: "Antes", After: "Después" });

Object.assign(dictionaries.de, {
  "Columns are 15-minute recording intervals.":
    "Spalten sind Aufzeichnungsintervalle von 15 Minuten.",
  "Columns are one-hour recording intervals.":
    "Spalten sind Aufzeichnungsintervalle von einer Stunde.",
  "Columns are one-day recording intervals.": "Spalten sind Aufzeichnungsintervalle von einem Tag.",
  "Records recorded in the same interval stack in their lane.":
    "Datensätze aus demselben Intervall stapeln sich in ihrer Spur.",
  "Columns are five-minute recording intervals.":
    "Spalten sind Aufzeichnungsintervalle von fünf Minuten.",
  "Columns are six-hour recording intervals.":
    "Spalten sind Aufzeichnungsintervalle von sechs Stunden.",
  "Columns are one-week recording intervals.":
    "Spalten sind Aufzeichnungsintervalle von einer Woche.",
});
Object.assign(dictionaries.nl, {
  "Columns are 15-minute recording intervals.":
    "Kolommen zijn registratie-intervallen van 15 minuten.",
  "Columns are one-hour recording intervals.": "Kolommen zijn registratie-intervallen van één uur.",
  "Columns are one-day recording intervals.": "Kolommen zijn registratie-intervallen van één dag.",
  "Records recorded in the same interval stack in their lane.":
    "Records uit hetzelfde interval stapelen zich in hun baan.",
  "Columns are five-minute recording intervals.":
    "Kolommen zijn registratie-intervallen van vijf minuten.",
  "Columns are six-hour recording intervals.": "Kolommen zijn registratie-intervallen van zes uur.",
  "Columns are one-week recording intervals.":
    "Kolommen zijn registratie-intervallen van één week.",
});
Object.assign(dictionaries.es, {
  "Columns are 15-minute recording intervals.":
    "Las columnas son intervalos de registro de 15 minutos.",
  "Columns are one-hour recording intervals.":
    "Las columnas son intervalos de registro de una hora.",
  "Columns are one-day recording intervals.": "Las columnas son intervalos de registro de un día.",
  "Records recorded in the same interval stack in their lane.":
    "Los registros del mismo intervalo se apilan en su carril.",
  "Columns are five-minute recording intervals.":
    "Las columnas son intervalos de registro de cinco minutos.",
  "Columns are six-hour recording intervals.":
    "Las columnas son intervalos de registro de seis horas.",
  "Columns are one-week recording intervals.":
    "Las columnas son intervalos de registro de una semana.",
});

// The Context Graph is a product term and reads the same in every language.
Object.assign(dictionaries.de, { "Context Graph": "Context Graph" });
Object.assign(dictionaries.nl, { "Context Graph": "Context Graph" });
Object.assign(dictionaries.es, { "Context Graph": "Context Graph" });
Object.assign(dictionaries.de, {
  Preview: "Vorschau",
  "Close preview": "Vorschau schließen",
  "Open full explanation": "Vollständige Erklärung öffnen",
});
Object.assign(dictionaries.nl, {
  Preview: "Voorbeeld",
  "Close preview": "Voorbeeld sluiten",
  "Open full explanation": "Volledige uitleg openen",
});
Object.assign(dictionaries.es, {
  Preview: "Vista previa",
  "Close preview": "Cerrar vista previa",
  "Open full explanation": "Abrir explicación completa",
});

// Master data names its primary action after the family it creates (spec 165).
Object.assign(dictionaries.de, {
  "New customer": "Neuer Kunde",
  "New supplier": "Neuer Lieferant",
});
Object.assign(dictionaries.nl, {
  "New customer": "Nieuwe klant",
  "New supplier": "Nieuwe leverancier",
});
Object.assign(dictionaries.es, {
  "New customer": "Nuevo cliente",
  "New supplier": "Nuevo proveedor",
});

Object.assign(dictionaries.de, {
  "Source code mappings": "Quellcode-Zuordnungen",
  "No previous mapping": "Keine bisherige Zuordnung",
  "Translate declared source codes into defined internal references. No amounts or postings change.":
    "Angegebene Quellcodes mit definierten internen Referenzen verbinden. Beträge und Buchungen bleiben unverändert.",
  "Search source mappings": "Quellzuordnungen suchen",
  "Edit source mapping": "Quellzuordnung bearbeiten",
  "New source mapping": "Neue Quellzuordnung",
  "Select source system": "Quellsystem auswählen",
  "Classification kind": "Klassifikationsart",
  "Source namespace": "Quell-Namensraum",
  "Declared source code": "Angegebener Quellcode",
  "Internal reference": "Interne Referenz",
  "Select reference": "Referenz auswählen",
  "Refine the search to find more references.":
    "Suche eingrenzen, um weitere Referenzen zu finden.",
  "Refine the search to find more source systems.":
    "Suche eingrenzen, um weitere Quellsysteme zu finden.",
  "Review source mapping": "Quellzuordnung prüfen",
  "Confirm source mapping": "Quellzuordnung bestätigen",
  "Source mapping history": "Historie der Quellzuordnung",
  "No declared code": "Kein Code angegeben",
  "Invalid source declaration": "Ungültige Quellangabe",
  "Source system not registered": "Quellsystem nicht registriert",
  "Source system blocked": "Quellsystem gesperrt",
  "No source mapping": "Keine Quellzuordnung",
  "Source mapping blocked": "Quellzuordnung gesperrt",
  "Internal reference blocked": "Interne Referenz gesperrt",
  "Conflicts with internal assignment": "Widerspruch zur internen Zuordnung",
  "Source code resolved": "Quellcode zugeordnet",
  "Source classification": "Klassifikation aus der Quelle",
  "Source classification and internal assignments remain separate.":
    "Quellklassifikation und interne Zuordnungen bleiben getrennt.",
  Retired: "Abgelöst",
});

Object.assign(dictionaries.nl, {
  "Source code mappings": "Broncodetoewijzingen",
  "No previous mapping": "Geen eerdere toewijzing",
  "Translate declared source codes into defined internal references. No amounts or postings change.":
    "Koppel vermelde broncodes aan gedefinieerde interne referenties. Bedragen en boekingen blijven ongewijzigd.",
  "Search source mappings": "Brontoewijzingen zoeken",
  "Edit source mapping": "Brontoewijzing bewerken",
  "New source mapping": "Nieuwe brontoewijzing",
  "Select source system": "Bronsysteem selecteren",
  "Classification kind": "Classificatiesoort",
  "Source namespace": "Naamruimte van de bron",
  "Declared source code": "Vermelde broncode",
  "Internal reference": "Interne referentie",
  "Select reference": "Referentie selecteren",
  "Refine the search to find more references.":
    "Verfijn de zoekopdracht om meer referenties te vinden.",
  "Refine the search to find more source systems.":
    "Verfijn de zoekopdracht om meer bronsystemen te vinden.",
  "Review source mapping": "Brontoewijzing controleren",
  "Confirm source mapping": "Brontoewijzing bevestigen",
  "Source mapping history": "Historie van brontoewijzing",
  "No declared code": "Geen code vermeld",
  "Invalid source declaration": "Ongeldige bronvermelding",
  "Source system not registered": "Bronsysteem niet geregistreerd",
  "Source system blocked": "Bronsysteem geblokkeerd",
  "No source mapping": "Geen brontoewijzing",
  "Source mapping blocked": "Brontoewijzing geblokkeerd",
  "Internal reference blocked": "Interne referentie geblokkeerd",
  "Conflicts with internal assignment": "Conflict met interne toewijzing",
  "Source code resolved": "Broncode toegewezen",
  "Source classification": "Classificatie uit de bron",
  "Source classification and internal assignments remain separate.":
    "Bronclassificatie en interne toewijzingen blijven gescheiden.",
  Retired: "Vervangen",
});

Object.assign(dictionaries.es, {
  "Source code mappings": "Asignaciones de códigos de origen",
  "No previous mapping": "Sin asignación anterior",
  "Translate declared source codes into defined internal references. No amounts or postings change.":
    "Vincula los códigos declarados a referencias internas definidas. Los importes y asientos no cambian.",
  "Search source mappings": "Buscar asignaciones de origen",
  "Edit source mapping": "Editar asignación de origen",
  "New source mapping": "Nueva asignación de origen",
  "Select source system": "Seleccionar sistema de origen",
  "Classification kind": "Tipo de clasificación",
  "Source namespace": "Espacio de nombres de origen",
  "Declared source code": "Código de origen declarado",
  "Internal reference": "Referencia interna",
  "Select reference": "Seleccionar referencia",
  "Refine the search to find more references.":
    "Refina la búsqueda para encontrar más referencias.",
  "Refine the search to find more source systems.":
    "Refina la búsqueda para encontrar más sistemas de origen.",
  "Review source mapping": "Revisar asignación de origen",
  "Confirm source mapping": "Confirmar asignación de origen",
  "Source mapping history": "Historial de asignación de origen",
  "No declared code": "Sin código declarado",
  "Invalid source declaration": "Declaración de origen no válida",
  "Source system not registered": "Sistema de origen no registrado",
  "Source system blocked": "Sistema de origen bloqueado",
  "No source mapping": "Sin asignación de origen",
  "Source mapping blocked": "Asignación de origen bloqueada",
  "Internal reference blocked": "Referencia interna bloqueada",
  "Conflicts with internal assignment": "Conflicto con la asignación interna",
  "Source code resolved": "Código de origen asignado",
  "Source classification": "Clasificación del origen",
  "Source classification and internal assignments remain separate.":
    "La clasificación del origen y las asignaciones internas se mantienen separadas.",
  Retired: "Sustituida",
});

Object.assign(dictionaries.de, {
  "Finance settings": "Finanzeinstellungen",
  "Manage accounts, internal classifications and source code mappings for this company.":
    "Konten, interne Klassifizierungen und Quellcode-Zuordnungen für diese Firma verwalten.",
});

Object.assign(dictionaries.nl, {
  "Finance settings": "Financiële instellingen",
  "Manage accounts, internal classifications and source code mappings for this company.":
    "Beheer rekeningen, interne classificaties en broncodetoewijzingen voor dit bedrijf.",
});

Object.assign(dictionaries.es, {
  "Finance settings": "Configuración financiera",
  "Manage accounts, internal classifications and source code mappings for this company.":
    "Gestiona cuentas, clasificaciones internas y asignaciones de códigos de origen de esta empresa.",
});

Object.assign(dictionaries.de, {
  "Accounts & account mapping": "Konten & Kontenzuordnung",
  "Case codes & coding groups": "Fallcodes & Buchungsgruppen",
  "Finance settings areas": "Bereiche der Finanzeinstellungen",
  "Settings area": "Einstellungsbereich",
});

Object.assign(dictionaries.nl, {
  "Accounts & account mapping": "Rekeningen & rekeningtoewijzing",
  "Case codes & coding groups": "Gevalcodes & boekingsgroepen",
  "Finance settings areas": "Onderdelen financiële instellingen",
  "Settings area": "Instellingsonderdeel",
});

Object.assign(dictionaries.es, {
  "Accounts & account mapping": "Cuentas y asignación de cuentas",
  "Case codes & coding groups": "Códigos de caso y grupos contables",
  "Finance settings areas": "Secciones de configuración financiera",
  "Settings area": "Sección de configuración",
});

Object.assign(dictionaries.de, {
  "Define cost centers for internal cost allocation.":
    "Kostenstellen für die interne Kostenverteilung definieren.",
  "Define case codes and coding groups for internal classification.":
    "Fallcodes und Buchungsgruppen für die interne Klassifizierung definieren.",
});

Object.assign(dictionaries.nl, {
  "Define cost centers for internal cost allocation.":
    "Definieer kostenplaatsen voor interne kostenverdeling.",
  "Define case codes and coding groups for internal classification.":
    "Definieer gevalcodes en boekingsgroepen voor interne classificatie.",
});

Object.assign(dictionaries.es, {
  "Define cost centers for internal cost allocation.":
    "Define centros de coste para la distribución interna de costes.",
  "Define case codes and coding groups for internal classification.":
    "Define códigos de caso y grupos contables para la clasificación interna.",
});

Object.assign(dictionaries.de, { "Review cost center": "Kostenstelle prüfen" });

Object.assign(dictionaries.nl, { "Review cost center": "Kostenplaats controleren" });

Object.assign(dictionaries.es, { "Review cost center": "Revisar centro de coste" });

Object.assign(dictionaries.de, {
  "Try it with an external agent": "Mit einem externen Agenten ausprobieren",
  "Connect an MCP client to Reality and let it read the current company.":
    "Verbinde einen MCP-Client mit Reality und erlaube ihm, das aktuelle Unternehmen zu lesen.",
  "Ask it to inspect open commitments, inventory or blockers before suggesting a change.":
    "Bitte ihn, offene Commitments, Bestand oder Blocker zu prüfen, bevor er eine Änderung vorschlägt.",
  "Ask it to prepare, not execute, a proposal. The proposal then appears here for human review.":
    "Bitte ihn, einen Vorschlag vorzubereiten, aber nicht auszuführen. Der Vorschlag erscheint dann hier zur menschlichen Prüfung.",
  "Open the decision, verify its evidence and exact effect, then approve or reject it.":
    "Öffne die Entscheidung, prüfe ihre Evidenz und genaue Wirkung und bestätige oder lehne sie anschließend ab.",
  "Example: understand what is open": "Beispiel: verstehen, was offen ist",
  "Example: prepare a human decision": "Beispiel: eine menschliche Entscheidung vorbereiten",
  "Use Reality MCP in read-only mode. List open customer commitments and fulfillment blockers. Explain what is open and why, using the opaque record IDs and available evidence. Do not propose or execute a change yet.":
    "Verwende Reality MCP im Nur-Lese-Modus. Liste offene Kunden-Commitments und Fulfillment-Blocker auf. Erkläre anhand der opaken Datensatz-IDs und der verfügbaren Evidenz, was offen ist und warum. Schlage noch keine Änderung vor und führe keine aus.",
  "For commitment <opaque commitment ID>, use Reality MCP to prepare a reservation proposal for <quantity>. Do not approve or execute it. Return the proposal ID and explain the expected effect so a person can review it in Decisions.":
    "Bereite für das Commitment <opake Commitment-ID> mit Reality MCP einen Reservierungsvorschlag über <Menge> vor. Bestätige ihn nicht und führe ihn nicht aus. Gib die Vorschlags-ID zurück und erkläre die erwartete Wirkung, damit eine Person ihn unter Decisions prüfen kann.",
  "Under the hood, an agent can use commitments_list or fulfillment_blockers to read, business_records_discover to resolve opaque records, and reservation_propose to prepare this example. Approval remains a separate human step.":
    "Im Hintergrund kann ein Agent commitments_list oder fulfillment_blockers zum Lesen, business_records_discover zum Auflösen opaker Datensätze und reservation_propose zum Vorbereiten dieses Beispiels verwenden. Die Bestätigung bleibt ein separater menschlicher Schritt.",
  "Possible future direction": "Mögliche zukünftige Richtung",
  "Reality may eventually let companies create and configure agents inside the product. That direction is exploratory and is not a committed part of the project; Reality may instead remain the governed business system used by external agents through MCP.":
    "Reality könnte Unternehmen künftig ermöglichen, Agenten direkt im Produkt zu erstellen und zu konfigurieren. Diese Richtung wird nur untersucht und ist kein zugesagter Teil des Projekts; Reality könnte stattdessen das kontrollierte Business-System bleiben, das externe Agenten über MCP verwenden.",
});

Object.assign(dictionaries.nl, {
  "Try it with an external agent": "Probeer het met een externe agent",
  "Connect an MCP client to Reality and let it read the current company.":
    "Verbind een MCP-client met Reality en laat die het huidige bedrijf lezen.",
  "Ask it to inspect open commitments, inventory or blockers before suggesting a change.":
    "Vraag de agent openstaande commitments, voorraad of blokkades te onderzoeken voordat een wijziging wordt voorgesteld.",
  "Ask it to prepare, not execute, a proposal. The proposal then appears here for human review.":
    "Vraag de agent een voorstel voor te bereiden, niet uit te voeren. Het voorstel verschijnt hier vervolgens voor menselijke beoordeling.",
  "Open the decision, verify its evidence and exact effect, then approve or reject it.":
    "Open de beslissing, controleer het bewijs en het exacte effect en keur deze daarna goed of wijs deze af.",
  "Example: understand what is open": "Voorbeeld: begrijpen wat openstaat",
  "Example: prepare a human decision": "Voorbeeld: een menselijke beslissing voorbereiden",
  "Use Reality MCP in read-only mode. List open customer commitments and fulfillment blockers. Explain what is open and why, using the opaque record IDs and available evidence. Do not propose or execute a change yet.":
    "Gebruik Reality MCP in alleen-lezenmodus. Toon openstaande klantcommitments en fulfillmentblokkades. Leg met de opaque record-ID's en beschikbare bewijzen uit wat openstaat en waarom. Stel nog geen wijziging voor en voer niets uit.",
  "For commitment <opaque commitment ID>, use Reality MCP to prepare a reservation proposal for <quantity>. Do not approve or execute it. Return the proposal ID and explain the expected effect so a person can review it in Decisions.":
    "Gebruik Reality MCP om voor commitment <opaque commitment-ID> een reserveringsvoorstel voor <hoeveelheid> voor te bereiden. Keur het niet goed en voer het niet uit. Geef de voorstel-ID en het verwachte effect terug, zodat een persoon het in Decisions kan beoordelen.",
  "Under the hood, an agent can use commitments_list or fulfillment_blockers to read, business_records_discover to resolve opaque records, and reservation_propose to prepare this example. Approval remains a separate human step.":
    "Een agent kan commitments_list of fulfillment_blockers gebruiken om te lezen, business_records_discover om opaque records te vinden en reservation_propose om dit voorbeeld voor te bereiden. Goedkeuring blijft een afzonderlijke menselijke stap.",
  "Possible future direction": "Mogelijke toekomstige richting",
  "Reality may eventually let companies create and configure agents inside the product. That direction is exploratory and is not a committed part of the project; Reality may instead remain the governed business system used by external agents through MCP.":
    "Reality maakt het bedrijven in de toekomst mogelijk misschien agenten in het product te maken en configureren. Die richting is verkennend en geen toegezegd onderdeel van het project; Reality kan ook het beheerste bedrijfssysteem blijven dat externe agenten via MCP gebruiken.",
});

Object.assign(dictionaries.es, {
  "Try it with an external agent": "Pruébalo con un agente externo",
  "Connect an MCP client to Reality and let it read the current company.":
    "Conecta un cliente MCP con Reality y permítele leer la empresa actual.",
  "Ask it to inspect open commitments, inventory or blockers before suggesting a change.":
    "Pídele que examine compromisos abiertos, inventario o bloqueos antes de sugerir un cambio.",
  "Ask it to prepare, not execute, a proposal. The proposal then appears here for human review.":
    "Pídele que prepare una propuesta, sin ejecutarla. La propuesta aparecerá aquí para revisión humana.",
  "Open the decision, verify its evidence and exact effect, then approve or reject it.":
    "Abre la decisión, comprueba su evidencia y efecto exacto, y después apruébala o recházala.",
  "Example: understand what is open": "Ejemplo: entender qué está pendiente",
  "Example: prepare a human decision": "Ejemplo: preparar una decisión humana",
  "Use Reality MCP in read-only mode. List open customer commitments and fulfillment blockers. Explain what is open and why, using the opaque record IDs and available evidence. Do not propose or execute a change yet.":
    "Usa Reality MCP en modo de solo lectura. Enumera los compromisos abiertos de clientes y los bloqueos de cumplimiento. Explica qué está pendiente y por qué usando los ID opacos y la evidencia disponible. No propongas ni ejecutes todavía ningún cambio.",
  "For commitment <opaque commitment ID>, use Reality MCP to prepare a reservation proposal for <quantity>. Do not approve or execute it. Return the proposal ID and explain the expected effect so a person can review it in Decisions.":
    "Para el compromiso <ID opaco del compromiso>, usa Reality MCP para preparar una propuesta de reserva por <cantidad>. No la apruebes ni ejecutes. Devuelve el ID de la propuesta y explica el efecto esperado para que una persona pueda revisarla en Decisions.",
  "Under the hood, an agent can use commitments_list or fulfillment_blockers to read, business_records_discover to resolve opaque records, and reservation_propose to prepare this example. Approval remains a separate human step.":
    "Un agente puede usar commitments_list o fulfillment_blockers para leer, business_records_discover para resolver registros opacos y reservation_propose para preparar este ejemplo. La aprobación sigue siendo un paso humano separado.",
  "Possible future direction": "Posible dirección futura",
  "Reality may eventually let companies create and configure agents inside the product. That direction is exploratory and is not a committed part of the project; Reality may instead remain the governed business system used by external agents through MCP.":
    "Reality podría permitir en el futuro crear y configurar agentes dentro del producto. Es una dirección exploratoria y no una parte comprometida del proyecto; Reality también podría seguir siendo el sistema empresarial gobernado que usan agentes externos mediante MCP.",
});

Object.assign(dictionaries.de, {
  Balances: "Salden",
  "Credit only": "Nur Guthaben",
  "Of which overdue": "Davon überfällig",
  "Oldest due": "Älteste Fälligkeit",
  "Open documents": "Offene Belege",
  "Credit documents": "Guthabenbelege",
  "Party / currency": "Geschäftspartner / Währung",
  "Search party": "Geschäftspartner suchen",
  "Only this party": "Nur dieser Geschäftspartner",
  "All parties": "Alle Geschäftspartner",
  Side: "Seite",
});

Object.assign(dictionaries.nl, {
  Balances: "Saldi",
  "Credit only": "Alleen tegoed",
  "Of which overdue": "Waarvan achterstallig",
  "Oldest due": "Oudste vervaldatum",
  "Open documents": "Open documenten",
  "Credit documents": "Tegoeddocumenten",
  "Party / currency": "Partij / valuta",
  "Search party": "Partij zoeken",
  "Only this party": "Alleen deze partij",
  "All parties": "Alle partijen",
  Side: "Zijde",
});

Object.assign(dictionaries.es, {
  Balances: "Saldos",
  "Credit only": "Solo saldo a favor",
  "Of which overdue": "De los cuales vencidos",
  "Oldest due": "Vencimiento más antiguo",
  "Open documents": "Documentos abiertos",
  "Credit documents": "Documentos de saldo a favor",
  "Party / currency": "Tercero / moneda",
  "Search party": "Buscar tercero",
  "Only this party": "Solo este tercero",
  "All parties": "Todos los terceros",
  Side: "Lado",
});

Object.assign(dictionaries.de, {
  "See where each customer or supplier stands: open, overdue, available credit and balance per currency.":
    "Sieh, wo jeder Kunde oder Lieferant steht: offen, überfällig, verfügbares Guthaben und Saldo je Währung.",
});
Object.assign(dictionaries.nl, {
  "See where each customer or supplier stands: open, overdue, available credit and balance per currency.":
    "Zie waar elke klant of leverancier staat: open, achterstallig, beschikbaar tegoed en saldo per valuta.",
});
Object.assign(dictionaries.es, {
  "See where each customer or supplier stands: open, overdue, available credit and balance per currency.":
    "Vea la posición de cada cliente o proveedor: abierto, vencido, saldo a favor disponible y saldo por moneda.",
});

Object.assign(dictionaries.de, {
  "Choose a goal": "Ziel wählen",
  "Find a real example": "Echtes Beispiel finden",
  "Describe the rule": "Regel beschreiben",
  "Test with existing data": "Mit vorhandenen Daten testen",
  "Review and activate": "Prüfen und aktivieren",
  "Delivery instructions": "Lieferhinweise",
  "Keep the delivery instruction stated on an order.":
    "Den Lieferhinweis aus einem Auftrag festhalten.",
  "What delivery instruction was stated on this order?":
    "Welcher Lieferhinweis wurde zu diesem Auftrag angegeben?",
  "Help the warehouse follow the customer's delivery instructions.":
    "Dem Lager helfen, die Lieferhinweise des Kunden zu beachten.",
  "Priority handling": "Bevorzugte Bearbeitung",
  "Remember a priority flag supplied with an order.":
    "Eine im Auftrag angegebene Priorität festhalten.",
  "Does the source mark this order for priority handling?":
    "Ist dieser Auftrag in der Quelle zur bevorzugten Bearbeitung markiert?",
  "Help the team identify orders marked as a priority.":
    "Dem Team helfen, als dringend markierte Aufträge zu erkennen.",
  "My own rule": "Eigene Regel",
  "Start with a different property stated in your data.":
    "Eine andere Eigenschaft aus deinen Daten festhalten.",
  "Save goal and continue": "Ziel speichern und weiter",
  "Save this example": "Dieses Beispiel speichern",
  "Request recommendation": "Empfehlung anfordern",
  "Confirm interpretation": "Einordnung bestätigen",
  "Save draft and continue": "Entwurf speichern und weiter",
  "Confirm activation": "Aktivierung bestätigen",
  "Confirm implementation package": "Umsetzungspaket bestätigen",
  "Your rule is active": "Deine Regel ist aktiv",
  "Draft saved. It is not active yet.": "Entwurf gespeichert. Die Regel ist noch nicht aktiv.",
  "Goal saved. No rule is active yet.": "Ziel gespeichert. Es ist noch keine Regel aktiv.",
  "Nothing has been saved yet.": "Es wurde noch nichts gespeichert.",
  "Rule setup progress": "Fortschritt der Regeleinrichtung",
  "It will apply to future matching data. Existing records have not been replayed.":
    "Sie gilt für künftig eingehende, passende Daten. Bestehende Datensätze wurden nicht nachträglich verarbeitet.",
  "This saves the reviewed setup step. It does not activate a rule or create Facts.":
    "Damit wird der geprüfte Einrichtungsschritt gespeichert. Es wird keine Regel aktiviert und es werden keine Fakten erzeugt.",
  "An Additional fact rule remembers a property stated in your data, so your team can find it on the right business record.":
    "Eine Regel für zusätzliche Fakten merkt sich eine Eigenschaft aus deinen Daten, damit dein Team sie am richtigen Geschäftsdatensatz findet.",
  "Find an order you know. Choose the field that contains the information you want to remember.":
    "Suche einen Auftrag, den du kennst. Wähle das Feld mit der Information, die du festhalten möchtest.",
  "Describe when the rule applies and what it should remember. Start simple; add conditions only if you need them.":
    "Beschreibe, wann die Regel gilt und was sie festhalten soll. Starte einfach und ergänze Bedingungen nur bei Bedarf.",
  "Test the saved version before activation. This preview does not change business data.":
    "Teste die gespeicherte Version vor der Aktivierung. Diese Vorschau verändert keine Geschäftsdaten.",
  "Check the meaning and the test results. Activation applies to future matching data; historical replay is a separate action.":
    "Prüfe die Bedeutung und die Testergebnisse. Die Aktivierung gilt für künftig eingehende, passende Daten. Historische Daten werden nur auf separate Bestätigung verarbeitet.",
  "This goal is already saved. Continue with your example; going back does not create another question.":
    "Dieses Ziel ist bereits gespeichert. Fahre mit deinem Beispiel fort. Zurückgehen legt keine weitere Frage an.",
  "Examples are starting points. The next step checks the data actually available in your company.":
    "Die Beispiele helfen beim Einstieg. Im nächsten Schritt prüfst du die tatsächlich vorhandenen Daten deines Unternehmens.",
  "What should Reality remember?": "Was soll Reality festhalten?",
  "Describe the information you want to remember.":
    "Beschreibe die Information, die du festhalten möchtest.",
  "For example: What delivery instruction was stated on this order?":
    "Zum Beispiel: Welcher Lieferhinweis wurde zu diesem Auftrag angegeben?",
  "How will this help your team?": "Wie hilft das deinem Team?",
  "Explain what your team will use this information for.":
    "Beschreibe, wofür dein Team diese Information braucht.",
  "For example: Help the warehouse follow the customer's delivery instructions.":
    "Zum Beispiel: Dem Lager helfen, die Lieferhinweise des Kunden zu beachten.",
  "This outcome is not an Additional fact rule. Keep the reviewed result or prepare the existing implementation handoff.":
    "Dieses Ergebnis ist keine Regel für zusätzliche Fakten. Behalte das geprüfte Ergebnis oder bereite die bestehende Übergabe an die Implementierung vor.",
  "The supporting example does not limit the test. Reality checks up to 100 matching sources already held by this company.":
    "Das ausgewählte Beispiel begrenzt den Test nicht. Reality prüft bis zu 100 passende Quellen, die für dieses Unternehmen bereits vorliegen.",
  "Test saved draft": "Gespeicherten Entwurf testen",
  "Save your changes before testing this version.":
    "Speichere deine Änderungen, bevor du diese Version testest.",
  "No matching examples were found. Check the source and conditions before deciding to activate.":
    "Es wurden keine passenden Beispiele gefunden. Prüfe Quelle und Bedingungen, bevor du die Regel aktivierst.",
  "Some sources need attention. Review the problems above or go back and adjust your rule.":
    "Einige Quellen müssen geprüft werden. Sieh dir die Probleme oben an oder gehe zurück und passe deine Regel an.",
  "Run the test to make activation review available.":
    "Führe den Test aus, um die Aktivierung prüfen zu können.",
  "Closing keeps saved steps; unsaved changes will be lost.":
    "Beim Schließen bleiben gespeicherte Schritte erhalten. Ungespeicherte Änderungen gehen verloren.",
  "Back to editing": "Zurück zur Bearbeitung",
  "Find an example": "Beispiel finden",
  "Review goal": "Ziel prüfen",
  "Review draft": "Entwurf prüfen",
  "Review activation": "Aktivierung prüfen",
  "Without conditions, the rule applies to every matching source type. Add a condition to limit it, for example to a stated priority flag.":
    "Ohne Bedingungen gilt die Regel für alle Datensätze des gewählten Quelltyps. Mit einer Bedingung kannst du sie beispielsweise auf eine angegebene Priorität begrenzen.",
  "Give this property a stable name, for example order.delivery_instruction. This labels the observation; it does not change the order.":
    "Gib der Eigenschaft einen eindeutigen Namen, zum Beispiel order.delivery_instruction. Er benennt die Beobachtung und verändert den Auftrag nicht.",
  "The source field and value type come from your example. The rule must link to an existing delivery commitment or order line. Line mapping and other options are under Advanced settings.":
    "Quellfeld und Werttyp stammen aus deinem Beispiel. Die Regel muss sich auf eine bestehende Lieferverpflichtung oder Auftragsposition beziehen. Die Zuordnung von Positionen und weitere Optionen findest du unter Erweiterte Einstellungen.",
  "Search by an order reference, then choose the relevant value. Saving an example only documents your evidence.":
    "Suche nach einer Auftragsreferenz und wähle den passenden Wert. Mit dem Speichern dokumentierst du zunächst nur dein Beispiel.",
  "Example saved. Request a recommendation to check whether this information belongs in an Additional fact rule.":
    "Beispiel gespeichert. Fordere eine Empfehlung an, um zu prüfen, ob diese Information in eine Regel für zusätzliche Fakten gehört.",
  "Review the recommendation and its limitations, then confirm the interpretation you want.":
    "Prüfe die Empfehlung und ihre Grenzen. Bestätige anschließend die gewünschte Einordnung.",
  "Your examples remain linked to their original sources.":
    "Deine Beispiele bleiben mit ihren Originalquellen verknüpft.",
});

Object.assign(dictionaries.nl, {
  "Choose a goal": "Kies een doel",
  "Find a real example": "Zoek een echt voorbeeld",
  "Describe the rule": "Beschrijf de regel",
  "Test with existing data": "Test met bestaande gegevens",
  "Review and activate": "Controleren en activeren",
  "Delivery instructions": "Leverinstructies",
  "Keep the delivery instruction stated on an order.": "Bewaar de leverinstructie op een order.",
  "What delivery instruction was stated on this order?":
    "Welke leverinstructie is bij deze order opgegeven?",
  "Help the warehouse follow the customer's delivery instructions.":
    "Help het magazijn de leverinstructies van de klant te volgen.",
  "Priority handling": "Prioriteitsafhandeling",
  "Remember a priority flag supplied with an order.":
    "Bewaar een prioriteitskenmerk dat bij een order is aangeleverd.",
  "Does the source mark this order for priority handling?":
    "Markeert de bron deze order voor prioriteitsafhandeling?",
  "Help the team identify orders marked as a priority.":
    "Help het team orders met prioriteit te herkennen.",
  "My own rule": "Mijn eigen regel",
  "Start with a different property stated in your data.":
    "Begin met een andere eigenschap uit je gegevens.",
  "Save goal and continue": "Doel opslaan en verder",
  "Save this example": "Dit voorbeeld opslaan",
  "Request recommendation": "Aanbeveling aanvragen",
  "Confirm interpretation": "Interpretatie bevestigen",
  "Save draft and continue": "Concept opslaan en verder",
  "Confirm activation": "Activering bevestigen",
  "Confirm implementation package": "Implementatiepakket bevestigen",
  "Your rule is active": "Je regel is actief",
  "Draft saved. It is not active yet.": "Concept opgeslagen. De regel is nog niet actief.",
  "Goal saved. No rule is active yet.": "Doel opgeslagen. Er is nog geen regel actief.",
  "Nothing has been saved yet.": "Er is nog niets opgeslagen.",
  "Rule setup progress": "Voortgang regelinstelling",
  "It will apply to future matching data. Existing records have not been replayed.":
    "De regel geldt voor toekomstige passende gegevens. Bestaande records zijn niet opnieuw verwerkt.",
  "This saves the reviewed setup step. It does not activate a rule or create Facts.":
    "Dit slaat de gecontroleerde instellingsstap op. Het activeert geen regel en maakt geen feiten aan.",
  "An Additional fact rule remembers a property stated in your data, so your team can find it on the right business record.":
    "Een regel voor aanvullende feiten onthoudt een eigenschap uit je data, zodat je team die bij het juiste bedrijfsrecord terugvindt.",
  "Find an order you know. Choose the field that contains the information you want to remember.":
    "Zoek een order die je kent. Kies het veld met de informatie die je wilt bewaren.",
  "Describe when the rule applies and what it should remember. Start simple; add conditions only if you need them.":
    "Beschrijf wanneer de regel geldt en wat deze moet bewaren. Begin eenvoudig en voeg alleen zo nodig voorwaarden toe.",
  "Test the saved version before activation. This preview does not change business data.":
    "Test de opgeslagen versie vóór activering. Deze preview verandert geen bedrijfsgegevens.",
  "Check the meaning and the test results. Activation applies to future matching data; historical replay is a separate action.":
    "Controleer de betekenis en testresultaten. Activering geldt voor toekomstige passende gegevens; historische verwerking is een aparte actie.",
  "This goal is already saved. Continue with your example; going back does not create another question.":
    "Dit doel is al opgeslagen. Ga verder met je voorbeeld; teruggaan maakt geen nieuwe vraag aan.",
  "Examples are starting points. The next step checks the data actually available in your company.":
    "De voorbeelden zijn startpunten. In de volgende stap controleer je de werkelijk beschikbare bedrijfsgegevens.",
  "What should Reality remember?": "Wat moet Reality bewaren?",
  "Describe the information you want to remember.": "Beschrijf de informatie die je wilt bewaren.",
  "For example: What delivery instruction was stated on this order?":
    "Bijvoorbeeld: Welke leverinstructie is bij deze order opgegeven?",
  "How will this help your team?": "Hoe helpt dit je team?",
  "Explain what your team will use this information for.":
    "Leg uit waarvoor je team deze informatie gaat gebruiken.",
  "For example: Help the warehouse follow the customer's delivery instructions.":
    "Bijvoorbeeld: Help het magazijn de leverinstructies van de klant te volgen.",
  "This outcome is not an Additional fact rule. Keep the reviewed result or prepare the existing implementation handoff.":
    "Deze uitkomst is geen regel voor aanvullende feiten. Behoud het beoordeelde resultaat of bereid de bestaande implementatieoverdracht voor.",
  "The supporting example does not limit the test. Reality checks up to 100 matching sources already held by this company.":
    "Het ondersteunende voorbeeld beperkt de test niet. Reality controleert maximaal 100 passende bronnen die dit bedrijf al heeft.",
  "Test saved draft": "Opgeslagen concept testen",
  "Save your changes before testing this version.":
    "Sla je wijzigingen op voordat je deze versie test.",
  "No matching examples were found. Check the source and conditions before deciding to activate.":
    "Er zijn geen passende voorbeelden gevonden. Controleer de bron en voorwaarden voordat je activeert.",
  "Some sources need attention. Review the problems above or go back and adjust your rule.":
    "Sommige bronnen vragen aandacht. Bekijk de problemen hierboven of ga terug en pas je regel aan.",
  "Run the test to make activation review available.":
    "Voer de test uit om de activering te kunnen beoordelen.",
  "Closing keeps saved steps; unsaved changes will be lost.":
    "Bij sluiten blijven opgeslagen stappen bewaard; niet-opgeslagen wijzigingen gaan verloren.",
  "Back to editing": "Terug naar bewerken",
  "Find an example": "Voorbeeld zoeken",
  "Review goal": "Doel controleren",
  "Review draft": "Concept controleren",
  "Review activation": "Activering controleren",
  "Without conditions, the rule applies to every matching source type. Add a condition to limit it, for example to a stated priority flag.":
    "Zonder voorwaarden geldt de regel voor alle records van het gekozen brontype. Voeg een voorwaarde toe om deze bijvoorbeeld tot een opgegeven prioriteit te beperken.",
  "Give this property a stable name, for example order.delivery_instruction. This labels the observation; it does not change the order.":
    "Geef deze eigenschap een vaste naam, bijvoorbeeld order.delivery_instruction. Dit benoemt de waarneming en verandert de order niet.",
  "The source field and value type come from your example. The rule must link to an existing delivery commitment or order line. Line mapping and other options are under Advanced settings.":
    "Het bronveld en waardetype komen uit je voorbeeld. De regel moet verwijzen naar een bestaande leververplichting of orderregel. Regeltoewijzing en andere opties staan onder Geavanceerde instellingen.",
  "Search by an order reference, then choose the relevant value. Saving an example only documents your evidence.":
    "Zoek op een orderreferentie en kies de relevante waarde. Een voorbeeld opslaan documenteert alleen je bewijs.",
  "Example saved. Request a recommendation to check whether this information belongs in an Additional fact rule.":
    "Voorbeeld opgeslagen. Vraag een aanbeveling aan om te controleren of deze informatie in een regel voor aanvullende feiten hoort.",
  "Review the recommendation and its limitations, then confirm the interpretation you want.":
    "Bekijk de aanbeveling en beperkingen en bevestig vervolgens de gewenste interpretatie.",
  "Your examples remain linked to their original sources.":
    "Je voorbeelden blijven gekoppeld aan hun oorspronkelijke bronnen.",
});

Object.assign(dictionaries.es, {
  "Choose a goal": "Elegir un objetivo",
  "Find a real example": "Buscar un ejemplo real",
  "Describe the rule": "Describir la regla",
  "Test with existing data": "Probar con datos existentes",
  "Review and activate": "Revisar y activar",
  "Delivery instructions": "Instrucciones de entrega",
  "Keep the delivery instruction stated on an order.":
    "Conservar la instrucción de entrega de un pedido.",
  "What delivery instruction was stated on this order?":
    "¿Qué instrucción de entrega se indicó en este pedido?",
  "Help the warehouse follow the customer's delivery instructions.":
    "Ayudar al almacén a seguir las instrucciones de entrega del cliente.",
  "Priority handling": "Tramitación prioritaria",
  "Remember a priority flag supplied with an order.":
    "Conservar la prioridad indicada en un pedido.",
  "Does the source mark this order for priority handling?":
    "¿Marca la fuente este pedido para tramitación prioritaria?",
  "Help the team identify orders marked as a priority.":
    "Ayudar al equipo a identificar pedidos marcados como prioritarios.",
  "My own rule": "Mi propia regla",
  "Start with a different property stated in your data.":
    "Empezar con otra propiedad indicada en tus datos.",
  "Save goal and continue": "Guardar objetivo y continuar",
  "Save this example": "Guardar este ejemplo",
  "Request recommendation": "Solicitar recomendación",
  "Confirm interpretation": "Confirmar interpretación",
  "Save draft and continue": "Guardar borrador y continuar",
  "Confirm activation": "Confirmar activación",
  "Confirm implementation package": "Confirmar paquete de implementación",
  "Your rule is active": "Tu regla está activa",
  "Draft saved. It is not active yet.": "Borrador guardado. La regla aún no está activa.",
  "Goal saved. No rule is active yet.": "Objetivo guardado. Aún no hay ninguna regla activa.",
  "Nothing has been saved yet.": "Aún no se ha guardado nada.",
  "Rule setup progress": "Progreso de configuración de la regla",
  "It will apply to future matching data. Existing records have not been replayed.":
    "Se aplicará a futuros datos coincidentes. Los registros existentes no se han reprocesado.",
  "This saves the reviewed setup step. It does not activate a rule or create Facts.":
    "Esto guarda el paso de configuración revisado. No activa ninguna regla ni crea hechos.",
  "An Additional fact rule remembers a property stated in your data, so your team can find it on the right business record.":
    "Una regla de hechos adicionales recuerda una propiedad indicada en tus datos para que tu equipo la encuentre en el registro de negocio correcto.",
  "Find an order you know. Choose the field that contains the information you want to remember.":
    "Busca un pedido que conozcas. Elige el campo con la información que quieres conservar.",
  "Describe when the rule applies and what it should remember. Start simple; add conditions only if you need them.":
    "Describe cuándo se aplica la regla y qué debe conservar. Empieza por lo sencillo y añade condiciones si las necesitas.",
  "Test the saved version before activation. This preview does not change business data.":
    "Prueba la versión guardada antes de activarla. Esta vista previa no modifica los datos del negocio.",
  "Check the meaning and the test results. Activation applies to future matching data; historical replay is a separate action.":
    "Revisa el significado y los resultados de la prueba. La activación se aplica a futuros datos coincidentes; el reprocesamiento histórico es una acción separada.",
  "This goal is already saved. Continue with your example; going back does not create another question.":
    "Este objetivo ya está guardado. Continúa con tu ejemplo; volver atrás no crea otra pregunta.",
  "Examples are starting points. The next step checks the data actually available in your company.":
    "Los ejemplos son puntos de partida. En el siguiente paso se comprueban los datos realmente disponibles en tu empresa.",
  "What should Reality remember?": "¿Qué debe conservar Reality?",
  "Describe the information you want to remember.":
    "Describe la información que quieres conservar.",
  "For example: What delivery instruction was stated on this order?":
    "Por ejemplo: ¿Qué instrucción de entrega se indicó en este pedido?",
  "How will this help your team?": "¿Cómo ayudará esto a tu equipo?",
  "Explain what your team will use this information for.":
    "Explica para qué usará tu equipo esta información.",
  "For example: Help the warehouse follow the customer's delivery instructions.":
    "Por ejemplo: Ayudar al almacén a seguir las instrucciones de entrega del cliente.",
  "This outcome is not an Additional fact rule. Keep the reviewed result or prepare the existing implementation handoff.":
    "Este resultado no es una regla de hechos adicionales. Conserva el resultado revisado o prepara la entrega de implementación existente.",
  "The supporting example does not limit the test. Reality checks up to 100 matching sources already held by this company.":
    "El ejemplo de apoyo no limita la prueba. Reality comprueba hasta 100 fuentes coincidentes ya disponibles en esta empresa.",
  "Test saved draft": "Probar borrador guardado",
  "Save your changes before testing this version.":
    "Guarda los cambios antes de probar esta versión.",
  "No matching examples were found. Check the source and conditions before deciding to activate.":
    "No se encontraron ejemplos coincidentes. Revisa la fuente y las condiciones antes de decidir si activas la regla.",
  "Some sources need attention. Review the problems above or go back and adjust your rule.":
    "Algunas fuentes requieren atención. Revisa los problemas anteriores o vuelve atrás y ajusta la regla.",
  "Run the test to make activation review available.":
    "Ejecuta la prueba para poder revisar la activación.",
  "Closing keeps saved steps; unsaved changes will be lost.":
    "Al cerrar se conservan los pasos guardados; los cambios sin guardar se perderán.",
  "Back to editing": "Volver a editar",
  "Find an example": "Buscar un ejemplo",
  "Review goal": "Revisar objetivo",
  "Review draft": "Revisar borrador",
  "Review activation": "Revisar activación",
  "Without conditions, the rule applies to every matching source type. Add a condition to limit it, for example to a stated priority flag.":
    "Sin condiciones, la regla se aplica a todos los registros del tipo de fuente elegido. Añade una condición para limitarla, por ejemplo, a una prioridad indicada.",
  "Give this property a stable name, for example order.delivery_instruction. This labels the observation; it does not change the order.":
    "Asigna un nombre estable a esta propiedad, por ejemplo order.delivery_instruction. Identifica la observación y no modifica el pedido.",
  "The source field and value type come from your example. The rule must link to an existing delivery commitment or order line. Line mapping and other options are under Advanced settings.":
    "El campo de origen y el tipo de valor proceden de tu ejemplo. La regla debe vincularse a un compromiso de entrega o línea de pedido existente. La asignación de líneas y otras opciones están en Configuración avanzada.",
  "Search by an order reference, then choose the relevant value. Saving an example only documents your evidence.":
    "Busca por referencia de pedido y elige el valor pertinente. Guardar un ejemplo solo documenta la evidencia.",
  "Example saved. Request a recommendation to check whether this information belongs in an Additional fact rule.":
    "Ejemplo guardado. Solicita una recomendación para comprobar si esta información pertenece a una regla de hechos adicionales.",
  "Review the recommendation and its limitations, then confirm the interpretation you want.":
    "Revisa la recomendación y sus limitaciones y confirma la interpretación deseada.",
  "Your examples remain linked to their original sources.":
    "Tus ejemplos siguen vinculados a sus fuentes originales.",
});

Object.assign(dictionaries.de, { Done: "Fertig" });
Object.assign(dictionaries.nl, { Done: "Klaar" });
Object.assign(dictionaries.es, { Done: "Listo" });

Object.assign(dictionaries.de, {
  "Implementation package prepared": "Umsetzungspaket vorbereitet",
});
Object.assign(dictionaries.nl, {
  "Implementation package prepared": "Implementatiepakket voorbereid",
});
Object.assign(dictionaries.es, {
  "Implementation package prepared": "Paquete de implementación preparado",
});

Object.assign(dictionaries.de, {
  "Finding type": "Art der Abweichung",
  "What it detects": "Was erkannt wird",
  "No open findings of this type right now.": "Aktuell keine offenen Klärfälle dieser Art.",
  "Open in Exceptions": "In Abweichungen öffnen",
});
Object.assign(dictionaries.nl, {
  "Finding type": "Soort bevinding",
  "What it detects": "Wat wordt gesignaleerd",
  "No open findings of this type right now.":
    "Momenteel geen openstaande bevindingen van dit soort.",
  "Open in Exceptions": "Openen in Uitzonderingen",
});
Object.assign(dictionaries.es, {
  "Finding type": "Tipo de hallazgo",
  "What it detects": "Qué detecta",
  "No open findings of this type right now.": "Actualmente no hay hallazgos abiertos de este tipo.",
  "Open in Exceptions": "Abrir en Excepciones",
});
Object.assign(dictionaries.de, {
  "Awaiting first calculation.": "Die erste Berechnung steht noch aus.",
  "Results are being updated. The last completed result is shown.":
    "Die Ergebnisse werden aktualisiert. Angezeigt wird der zuletzt berechnete Stand.",
  "The calculation could not be updated.": "Die Berechnung konnte nicht aktualisiert werden.",
  "Stored result": "Vorberechnetes Ergebnis",
  "Last calculated": "Zuletzt berechnet",
  "Live view": "Live-Ansicht",
  "Calculated for your inputs": "Berechnung für deine Eingaben",
  "Price depends on customer, item, quantity and date.":
    "Der Preis hängt von Kunde, Artikel, Menge und Datum ab.",
});
Object.assign(dictionaries.nl, {
  "Awaiting first calculation.": "De eerste berekening staat nog open.",
  "Results are being updated. The last completed result is shown.":
    "De resultaten worden bijgewerkt. Het laatst berekende resultaat wordt getoond.",
  "The calculation could not be updated.": "De berekening kon niet worden bijgewerkt.",
  "Stored result": "Vooraf berekend resultaat",
  "Last calculated": "Laatst berekend",
  "Live view": "Liveweergave",
  "Calculated for your inputs": "Berekening voor je invoer",
  "Price depends on customer, item, quantity and date.":
    "De prijs hangt af van klant, artikel, hoeveelheid en datum.",
});
Object.assign(dictionaries.es, {
  "Awaiting first calculation.": "Pendiente del primer cálculo.",
  "Results are being updated. The last completed result is shown.":
    "Los resultados se están actualizando. Se muestra el último resultado calculado.",
  "The calculation could not be updated.": "No se pudo actualizar el cálculo.",
  "Stored result": "Resultado precalculado",
  "Last calculated": "Último cálculo",
  "Live view": "Vista en directo",
  "Calculated for your inputs": "Cálculo según tus datos",
  "Price depends on customer, item, quantity and date.":
    "El precio depende del cliente, artículo, cantidad y fecha.",
});

Object.assign(dictionaries.de, {
  "This finding has cleared since the last calculation.":
    "Dieser Klärfall hat sich seit der letzten Berechnung erledigt.",
  "It disappears from the list with the next calculation.":
    "Mit der nächsten Berechnung verschwindet er aus der Liste.",
});
Object.assign(dictionaries.nl, {
  "This finding has cleared since the last calculation.":
    "Deze bevinding is sinds de laatste berekening opgelost.",
  "It disappears from the list with the next calculation.":
    "Bij de volgende berekening verdwijnt ze uit de lijst.",
});
Object.assign(dictionaries.es, {
  "This finding has cleared since the last calculation.":
    "Este hallazgo se ha resuelto desde el último cálculo.",
  "It disappears from the list with the next calculation.":
    "Desaparecerá de la lista con el próximo cálculo.",
});

// Storyline mode (spec 182)
Object.assign(dictionaries.de, {
  "Guided business flows. Each one plays in a sandbox of its own, step by step, with the calls and the recorded changes beside it. Nothing here touches a real company.":
    "Geführte Geschäftsabläufe. Jeder läuft in einer eigenen Sandbox, Schritt für Schritt, mit den Aufrufen und den aufgezeichneten Änderungen daneben. Nichts davon berührt ein echtes Unternehmen.",
  "Calls in this step": "Aufrufe in diesem Schritt",
  "Free play": "Freies Spiel",
  "In progress": "Läuft",
  Import: "Importieren",
  "Played to the end": "Zu Ende gespielt",
  "Opens a sandbox of its own for you.": "Legt eine eigene Sandbox für dich an.",
  "Opens a new sandbox at step 1. The current one stays as it is.":
    "Öffnet eine neue Sandbox bei Schritt 1. Die bisherige bleibt, wie sie ist.",
  Autoplay: "Automatik",
  Library: "Bibliothek",
  "Go to the current step": "Zum aktuellen Schritt",
  entries: "Einträge",
  fields: "Felder",
  "Other storylines": "Andere Storylines",
  "Up next": "Als Nächstes",
  "Take the default branch": "Standardabzweig nehmen",
  "Autoplay stopped at an error.": "Automatik angehalten: Ein Fehler ist aufgetreten.",
  "Runs on its own. Any click stops it.": "Läuft von selbst. Jeder Klick hält an.",
  "For a presentation: plays the steps on its own.":
    "Zum Vorführen: spielt die Schritte von selbst.",
  "Stop autoplay": "Automatik anhalten",
  "Play automatically": "Automatisch abspielen",
  "Export as storyline draft": "Als Storyline-Entwurf exportieren",
  "Everything confirmed in this run, in order, as a storyline file with its texts still to be written.":
    "Alles, was in diesem Durchlauf bestätigt wurde, der Reihe nach als Storyline-Datei, deren Texte noch zu schreiben sind.",
  "The storyline has been played to the end.": "Die Storyline ist zu Ende gespielt.",
  "Autoplay stopped: this step cannot run yet.":
    "Automatik angehalten: Dieser Schritt kann noch nicht laufen.",
  "Autoplay stopped: the outcome of a step is unknown.":
    "Automatik angehalten: Das Ergebnis eines Schritts ist unbekannt.",
  "Autoplay stopped: this step comes later in the storyline.":
    "Automatik angehalten: Dieser Schritt kommt später in der Storyline.",
  "Back to the storyline": "Zurück zur Storyline",
  "Open the company": "Firma öffnen",
  "You are working in the sandbox itself.": "Du arbeitest in der Sandbox selbst.",
  "Every read, proposal and confirmation you make anywhere in this sandbox is still recorded here, with what it added.":
    "Jedes Lesen, jeder Vorschlag und jede Bestätigung irgendwo in dieser Sandbox wird weiter hier aufgezeichnet, samt dem, was sie hinzugefügt hat.",
  "The storyline waits at step": "Die Storyline wartet bei Schritt",
  "Calls outside the storyline": "Aufrufe außerhalb der Storyline",
  "Nothing has been done outside the storyline yet.":
    "Außerhalb der Storyline ist noch nichts passiert.",
  "Pick a confirmed call to see what it added.":
    "Wähle einen bestätigten Aufruf, um zu sehen, was er hinzugefügt hat.",
  "What it added": "Was hinzukam",
  Steps: "Schritte",
  steps: "Schritte",
  calls: "Aufrufe",
  "Current step": "Aktueller Schritt",
  Discard: "Verwerfen",
  Error: "Fehler",
  error: "Fehler",
  "Expected to be cleared": "Erwartet geschlossen",
  "Expected to be raised": "Erwartet gehoben",
  Findings: "Abweichungen",
  "How does it continue?": "Wie geht es weiter?",
  imported: "importiert",
  Input: "Eingabe",
  "new since this step": "neu seit diesem Schritt",
  "Next step": "Nächster Schritt",
  "No rows yet. The view fills as the story goes on.":
    "Noch keine Zeilen. Die Ansicht füllt sich im Lauf der Geschichte.",
  "Nothing has been called for this step yet.": "Für diesen Schritt wurde noch nichts aufgerufen.",
  "Once you confirm, the events, facts, records and findings of this step appear here.":
    "Sobald du bestätigst, erscheinen hier die Ereignisse, Fakten, Datensätze und Abweichungen dieses Schritts.",
  "Open in app": "In der App öffnen",
  "Open in Tool Usage": "In Tool Usage öffnen",
  "Prepare this step": "Diesen Schritt vorbereiten",
  "Preview · nothing has happened yet": "Vorschau · noch ist nichts passiert",
  Read: "Lesen",
  read: "lesen",
  Records: "Datensätze",
  Recorded: "Aufgezeichnet",
  "Refused by the system": "Vom System abgelehnt",
  Result: "Ergebnis",
  "solid lines are new links": "durchgezogene Linien sind neue Verknüpfungen",
  "Start over in a new sandbox": "Von vorn in einer neuen Sandbox",
  Storylines: "Storyline-Bibliothek",
  story: "Story",
  "The outcome of this step is unknown. Inspect the proposal before continuing.":
    "Das Ergebnis dieses Schritts ist unbekannt. Prüfe den Vorschlag, bevor du weitermachst.",
  "The storyline sandbox could not be prepared.":
    "Die Sandbox der Storyline konnte nicht vorbereitet werden.",
  "This step cannot run yet. Missing:": "Dieser Schritt kann noch nicht laufen. Es fehlt:",
  "This step comes later in the storyline.": "Dieser Schritt kommt später in der Storyline.",
  "This step has not been played.": "Dieser Schritt wurde nicht gespielt.",
  "This step opens no view.": "Dieser Schritt öffnet keine Ansicht.",
  View: "Ansicht",
  "What happened": "Was passiert ist",
  "What was added": "Was dazukam",
  "Writes to": "Schreibt in",
  you: "du",
});

Object.assign(dictionaries.nl, {
  "Guided business flows. Each one plays in a sandbox of its own, step by step, with the calls and the recorded changes beside it. Nothing here touches a real company.":
    "Begeleide bedrijfsprocessen. Elk speelt in een eigen sandbox, stap voor stap, met de aanroepen en de vastgelegde wijzigingen ernaast. Niets hiervan raakt een echt bedrijf.",
  "Calls in this step": "Aanroepen in deze stap",
  "Free play": "Vrij spel",
  "In progress": "Bezig",
  Import: "Importeren",
  "Played to the end": "Uitgespeeld",
  "Opens a sandbox of its own for you.": "Opent een eigen sandbox voor je.",
  "Opens a new sandbox at step 1. The current one stays as it is.":
    "Opent een nieuwe sandbox bij stap 1. De huidige blijft zoals hij is.",
  Autoplay: "Automatisch",
  Library: "Bibliotheek",
  "Go to the current step": "Naar de huidige stap",
  entries: "items",
  fields: "velden",
  "Other storylines": "Andere Storylines",
  "Up next": "Hierna",
  "Take the default branch": "Standaardaftakking nemen",
  "Autoplay stopped at an error.": "Automatisch afspelen gestopt: er is een fout opgetreden.",
  "Runs on its own. Any click stops it.": "Loopt vanzelf. Elke klik stopt het.",
  "For a presentation: plays the steps on its own.":
    "Om te presenteren: speelt de stappen vanzelf af.",
  "Stop autoplay": "Automatisch afspelen stoppen",
  "Play automatically": "Automatisch afspelen",
  "Export as storyline draft": "Exporteren als Storyline-concept",
  "Everything confirmed in this run, in order, as a storyline file with its texts still to be written.":
    "Alles wat in deze run is bevestigd, op volgorde, als Storyline-bestand waarvan de teksten nog geschreven moeten worden.",
  "The storyline has been played to the end.": "De Storyline is tot het einde gespeeld.",
  "Autoplay stopped: this step cannot run yet.":
    "Automatisch afspelen gestopt: deze stap kan nog niet lopen.",
  "Autoplay stopped: the outcome of a step is unknown.":
    "Automatisch afspelen gestopt: de uitkomst van een stap is onbekend.",
  "Autoplay stopped: this step comes later in the storyline.":
    "Automatisch afspelen gestopt: deze stap komt later in de Storyline.",
  "Back to the storyline": "Terug naar de Storyline",
  "Open the company": "Bedrijf openen",
  "You are working in the sandbox itself.": "Je werkt in de sandbox zelf.",
  "Every read, proposal and confirmation you make anywhere in this sandbox is still recorded here, with what it added.":
    "Elke leesactie, elk voorstel en elke bevestiging ergens in deze sandbox wordt hier nog steeds vastgelegd, met wat ze toevoegde.",
  "The storyline waits at step": "De Storyline wacht bij stap",
  "Calls outside the storyline": "Aanroepen buiten de Storyline",
  "Nothing has been done outside the storyline yet.": "Buiten de Storyline is nog niets gedaan.",
  "Pick a confirmed call to see what it added.":
    "Kies een bevestigde aanroep om te zien wat die toevoegde.",
  "What it added": "Wat erbij kwam",
  Steps: "Stappen",
  steps: "stappen",
  calls: "aanroepen",
  "Current step": "Huidige stap",
  Discard: "Verwerpen",
  Error: "Fout",
  error: "fout",
  "Expected to be cleared": "Verwacht gesloten",
  "Expected to be raised": "Verwacht gemeld",
  Findings: "Bevindingen",
  "How does it continue?": "Hoe gaat het verder?",
  imported: "geïmporteerd",
  Input: "Invoer",
  "new since this step": "nieuw sinds deze stap",
  "Next step": "Volgende stap",
  "No rows yet. The view fills as the story goes on.":
    "Nog geen rijen. Het overzicht vult zich naarmate het verhaal vordert.",
  "Nothing has been called for this step yet.": "Voor deze stap is nog niets aangeroepen.",
  "Once you confirm, the events, facts, records and findings of this step appear here.":
    "Zodra je bevestigt, verschijnen hier de gebeurtenissen, feiten, records en bevindingen van deze stap.",
  "Open in app": "In de app openen",
  "Open in Tool Usage": "In Tool Usage openen",
  "Prepare this step": "Deze stap voorbereiden",
  "Preview · nothing has happened yet": "Voorbeeld · er is nog niets gebeurd",
  Read: "Lezen",
  read: "lezen",
  Records: "Records",
  Recorded: "Vastgelegd",
  "Refused by the system": "Geweigerd door het systeem",
  Result: "Resultaat",
  "solid lines are new links": "doorgetrokken lijnen zijn nieuwe koppelingen",
  "Start over in a new sandbox": "Opnieuw beginnen in een nieuwe sandbox",
  Storylines: "Storyline-bibliotheek",
  story: "verhaal",
  "The outcome of this step is unknown. Inspect the proposal before continuing.":
    "De uitkomst van deze stap is onbekend. Bekijk het voorstel voordat je verdergaat.",
  "The storyline sandbox could not be prepared.":
    "De sandbox van de Storyline kon niet worden voorbereid.",
  "This step cannot run yet. Missing:": "Deze stap kan nog niet lopen. Er ontbreekt:",
  "This step comes later in the storyline.": "Deze stap komt later in de Storyline.",
  "This step has not been played.": "Deze stap is niet gespeeld.",
  "This step opens no view.": "Deze stap opent geen weergave.",
  View: "Overzicht",
  "What happened": "Wat er gebeurde",
  "What was added": "Wat erbij kwam",
  "Writes to": "Schrijft naar",
  you: "jij",
});

Object.assign(dictionaries.es, {
  "Guided business flows. Each one plays in a sandbox of its own, step by step, with the calls and the recorded changes beside it. Nothing here touches a real company.":
    "Flujos de negocio guiados. Cada uno se juega en una sandbox propia, paso a paso, con las llamadas y los cambios registrados al lado. Nada de esto toca una empresa real.",
  "Calls in this step": "Llamadas en este paso",
  "Free play": "Juego libre",
  "In progress": "En curso",
  Import: "Importar",
  "Played to the end": "Jugada hasta el final",
  "Opens a sandbox of its own for you.": "Abre una sandbox propia para ti.",
  "Opens a new sandbox at step 1. The current one stays as it is.":
    "Abre una sandbox nueva en el paso 1. La actual se queda como está.",
  Autoplay: "Automático",
  Library: "Biblioteca",
  "Go to the current step": "Ir al paso actual",
  entries: "entradas",
  fields: "campos",
  "Other storylines": "Otras Storylines",
  "Up next": "A continuación",
  "Take the default branch": "Tomar la rama predeterminada",
  "Autoplay stopped at an error.": "Reproducción automática detenida: se produjo un error.",
  "Runs on its own. Any click stops it.": "Se ejecuta sola. Cualquier clic la detiene.",
  "For a presentation: plays the steps on its own.":
    "Para presentar: reproduce los pasos por sí sola.",
  "Stop autoplay": "Detener la reproducción automática",
  "Play automatically": "Reproducir automáticamente",
  "Export as storyline draft": "Exportar como borrador de Storyline",
  "Everything confirmed in this run, in order, as a storyline file with its texts still to be written.":
    "Todo lo confirmado en esta ejecución, en orden, como archivo de Storyline con los textos aún por escribir.",
  "The storyline has been played to the end.": "La Storyline se ha jugado hasta el final.",
  "Autoplay stopped: this step cannot run yet.":
    "Reproducción automática detenida: este paso aún no puede ejecutarse.",
  "Autoplay stopped: the outcome of a step is unknown.":
    "Reproducción automática detenida: el resultado de un paso es desconocido.",
  "Autoplay stopped: this step comes later in the storyline.":
    "Reproducción automática detenida: este paso llega más adelante en la Storyline.",
  "Back to the storyline": "Volver a la Storyline",
  "Open the company": "Abrir la empresa",
  "You are working in the sandbox itself.": "Estás trabajando en la propia sandbox.",
  "Every read, proposal and confirmation you make anywhere in this sandbox is still recorded here, with what it added.":
    "Cada lectura, propuesta y confirmación que hagas en cualquier parte de esta sandbox sigue registrándose aquí, con lo que añadió.",
  "The storyline waits at step": "La Storyline espera en el paso",
  "Calls outside the storyline": "Llamadas fuera de la Storyline",
  "Nothing has been done outside the storyline yet.":
    "Todavía no se ha hecho nada fuera de la Storyline.",
  "Pick a confirmed call to see what it added.":
    "Elige una llamada confirmada para ver lo que añadió.",
  "What it added": "Lo que añadió",
  Steps: "Pasos",
  steps: "pasos",
  calls: "llamadas",
  "Current step": "Paso actual",
  Discard: "Descartar",
  Error: "Fallo",
  error: "fallo",
  "Expected to be cleared": "Se esperaba que se cerrara",
  "Expected to be raised": "Se esperaba que se levantara",
  Findings: "Hallazgos",
  "How does it continue?": "¿Cómo continúa?",
  imported: "importada",
  Input: "Entrada",
  "new since this step": "nuevo desde este paso",
  "Next step": "Siguiente paso",
  "No rows yet. The view fills as the story goes on.":
    "Aún no hay filas. La vista se llena a medida que avanza la historia.",
  "Nothing has been called for this step yet.": "Todavía no se ha llamado nada para este paso.",
  "Once you confirm, the events, facts, records and findings of this step appear here.":
    "En cuanto confirmes, aquí aparecerán los eventos, hechos, registros y hallazgos de este paso.",
  "Open in app": "Abrir en la app",
  "Open in Tool Usage": "Abrir en Tool Usage",
  "Prepare this step": "Preparar este paso",
  "Preview · nothing has happened yet": "Vista previa · aún no ha pasado nada",
  Read: "Leer",
  read: "leer",
  Records: "Registros",
  Recorded: "Registrado",
  "Refused by the system": "Rechazado por el sistema",
  Result: "Resultado",
  "solid lines are new links": "las líneas continuas son enlaces nuevos",
  "Start over in a new sandbox": "Empezar de nuevo en una sandbox nueva",
  Storylines: "Biblioteca de storylines",
  story: "historia",
  "The outcome of this step is unknown. Inspect the proposal before continuing.":
    "El resultado de este paso es desconocido. Revisa la propuesta antes de continuar.",
  "The storyline sandbox could not be prepared.": "La sandbox de la Storyline no se pudo preparar.",
  "This step cannot run yet. Missing:": "Este paso aún no puede ejecutarse. Falta:",
  "This step comes later in the storyline.": "Este paso llega más adelante en la Storyline.",
  "This step has not been played.": "Este paso no se ha jugado.",
  "This step opens no view.": "Este paso no abre ninguna vista.",
  View: "Vista",
  "What happened": "Qué pasó",
  "What was added": "Qué se añadió",
  "Writes to": "Escribe en",
  you: "tú",
});

Object.assign(dictionaries.de, {
  "A package file someone sent you. It is checked against the catalogs before anything is stored, and it runs under exactly the rules a built-in storyline runs under.":
    "Eine Paketdatei, die dir jemand geschickt hat. Sie wird gegen die Kataloge geprüft, bevor etwas gespeichert wird, und läuft unter genau den Regeln einer eingebauten Storyline.",
  Download: "Herunterladen",
  "Import a storyline": "Storyline importieren",
  Imported: "Importiert",
  "Package file (YAML or JSON)": "Paketdatei (YAML oder JSON)",
  "Play a storyline": "Eine Storyline spielen",
  "Remove from library": "Aus der Bibliothek entfernen",
  "Replace the same key and version": "Gleichen Schlüssel und gleiche Version ersetzen",
});

Object.assign(dictionaries.nl, {
  "A package file someone sent you. It is checked against the catalogs before anything is stored, and it runs under exactly the rules a built-in storyline runs under.":
    "Een pakketbestand dat iemand je stuurde. Het wordt tegen de catalogi gecontroleerd voordat iets wordt opgeslagen, en het loopt onder precies de regels van een ingebouwde storyline.",
  Download: "Downloaden",
  "Import a storyline": "Een storyline importeren",
  Imported: "Geïmporteerd",
  "Package file (YAML or JSON)": "Pakketbestand (YAML of JSON)",
  "Play a storyline": "Een storyline spelen",
  "Remove from library": "Uit de bibliotheek verwijderen",
  "Replace the same key and version": "Dezelfde sleutel en versie vervangen",
});

Object.assign(dictionaries.es, {
  "A package file someone sent you. It is checked against the catalogs before anything is stored, and it runs under exactly the rules a built-in storyline runs under.":
    "Un archivo de paquete que alguien te envió. Se comprueba contra los catálogos antes de guardar nada y se ejecuta bajo exactamente las reglas de una storyline integrada.",
  Download: "Descargar",
  "Import a storyline": "Importar una storyline",
  Imported: "Importada",
  "Package file (YAML or JSON)": "Archivo de paquete (YAML o JSON)",
  "Play a storyline": "Jugar una storyline",
  "Remove from library": "Quitar de la biblioteca",
  "Replace the same key and version": "Reemplazar la misma clave y versión",
});

// Composable analytics workspace (spec 185).
Object.assign(dictionaries.de, {
  "All recorded history": "Gesamter erfasster Verlauf",
  "Analysis chart": "Auswertungsdiagramm",
  "Analysis results": "Auswertungsergebnisse",
  "Analytics views": "Auswertungsansichten",
  Ascending: "Aufsteigend",
  Descending: "Absteigend",
  "Bar chart": "Balkendiagramm",
  "Show in chart": "Im Diagramm anzeigen",
  "Line chart": "Liniendiagramm",
  "Based on interpreted records held in this company. Upstream history may be incomplete. Pages and exports use fresh observations.":
    "Grundlage sind die interpretierten Datensätze dieses Unternehmens. Der Quellverlauf kann unvollständig sein. Seiten und Exporte werden jeweils neu ausgewertet.",
  "Change report": "Auswertung ändern",
  "Chart shows a limited selection.": "Das Diagramm zeigt eine begrenzte Auswahl.",
  "Choose a perspective, measures and filters, then run your analysis. Select any result to see its supporting records.":
    "Wähle Datenbereich, Kennzahlen und Filter und starte die Auswertung. Klicke auf ein Ergebnis, um die zugehörigen Datensätze zu sehen.",
  "Choose a grouping, such as customer or month, and run the analysis again.":
    "Wähle eine Gruppierung, zum Beispiel Kunde oder Monat, und starte die Auswertung erneut.",
  "Compare with previous period": "Mit Vorperiode vergleichen",
  "Custom dates": "Eigener Zeitraum",
  "Data perspective": "Datenbereich",
  "Date field": "Datumsfeld",
  "Delete this report?": "Diese Auswertung löschen?",
  Duplicate: "Duplizieren",
  "End date (exclusive)": "Enddatum (ausschließlich)",
  "Exact values and supporting records are available in the table.":
    "Genaue Werte und zugehörige Datensätze findest du in der Tabelle.",
  "Explore your business. Trace every answer.":
    "Dein Unternehmen auswerten. Jede Antwort nachvollziehen.",
  "Export created from a fresh observation.": "Export mit neu ausgewerteten Daten erstellt.",
  "Export CSV": "CSV exportieren",
  Filter: "Filterbedingung",
  "Filter field": "Filterfeld",
  "Filter operator": "Filterbedingung",
  "Filter value": "Filterwert",
  Filters: "Filter",
  "First page": "Erste Seite",
  "Fresh observation of the selected value.": "Neue Auswertung des ausgewählten Wertes.",
  "Full population": "Gesamtes Ergebnis",
  Group: "Gruppe",
  "Group by": "Gruppieren nach",
  "ISO week": "ISO-Kalenderwoche",
  "Last complete months": "Letzte vollständige Monate",
  "Last complete weeks": "Letzte vollständige Wochen",
  "Last days": "Letzte Tage",
  "Match conditions": "Bedingungen verknüpfen",
  Measures: "Kennzahlen",
  "Missing values": "Fehlende Werte",
  "More records are available. Narrow the analysis to inspect a smaller group.":
    "Weitere Datensätze verfügbar. Grenze die Auswertung für eine kleinere Gruppe ein.",
  "My reports": "Meine Auswertungen",
  "New analysis": "Neue Auswertung",
  "Number of periods": "Anzahl Zeiträume",
  "Only the definition is saved. Results are refreshed when you run it.":
    "Gespeichert werden die Einstellungen. Ergebnisse werden bei jeder Ausführung neu berechnet.",
  "Previous period": "Vorperiode",
  "Private to you in this company. Each opening runs against current records.":
    "Nur für dich in diesem Unternehmen sichtbar. Die Auswertung verwendet aktuelle Datensätze.",
  "Read-only analysis": "Lesende Auswertung",
  "Refresh first page": "Erste Seite aktualisieren",
  "Remove filter": "Filter entfernen",
  Rename: "Umbenennen",
  "Report name": "Name der Auswertung",
  "Report saved.": "Auswertung gespeichert.",
  "Results show the last executed settings. Run again to apply your edits.":
    "Die Ergebnisse gehören zu den zuletzt ausgeführten Einstellungen. Starte erneut, um deine Änderungen anzuwenden.",
  "Run analysis": "Auswertung starten",
  "Run the comparison period directly to inspect its records.":
    "Führe die Vorperiode direkt aus, um ihre Datensätze zu prüfen.",
  "Running analysis…": "Auswertung läuft …",
  Save: "Speichern",
  "Save an analysis to find it here.": "Speichere eine Auswertung, um sie hier wiederzufinden.",
  "Save report": "Auswertung speichern",
  "Scope and data quality": "Umfang und Datenqualität",
  "Search reports": "Auswertungen suchen",
  "Select record": "Datensatz auswählen",
  "Sort by": "Sortieren nach",
  "Sort direction": "Sortierreihenfolge",
  "Start date": "Startdatum",
  "Start with a business question": "Starte mit einer Geschäftsfrage",
  "This month": "Dieser Monat",
  "This quarter": "Dieses Quartal",
  "This year": "Dieses Jahr",
  "Undated records excluded": "Ausgeschlossene Datensätze ohne Datum",
  Week: "Woche",
  Year: "Jahr",
  groups: "Gruppen",
  "All conditions": "Alle Bedingungen",
  "Any condition": "Mindestens eine Bedingung",
  Equals: "Ist gleich",
  "Does not equal": "Ist nicht gleich",
  "In list": "Ist in Liste",
  "Not in list": "Ist nicht in Liste",
  Contains: "Enthält",
  "At least": "Mindestens",
  "Greater than": "Größer als",
  "At most": "Höchstens",
  "Less than": "Kleiner als",
  "Is missing": "Fehlt",
  "Is present": "Ist vorhanden",
  "Customer purchase history": "Kaufhistorie der Kunden",
  "Products ordered together": "Gemeinsam bestellte Produkte",
  "Recorded payments": "Erfasste Zahlungen",
  "Sales order lines": "Kundenauftragspositionen",
  "Purchase order lines": "Bestellpositionen",
  "Sales orders": "Kundenaufträge",
  "Purchase orders": "Bestellungen",
  "Inventory by location": "Bestand nach Lagerort",
  "Record count": "Anzahl Datensätze",
  "Order count": "Anzahl Aufträge",
  "Customer count": "Anzahl Kunden",
  "Ordered quantity": "Bestellte Menge",
  "Stated line amount": "Übermittelter Positionsbetrag",
  "Stated order amount": "Übermittelter Auftragsbetrag",
  "Minimum agreed price": "Niedrigster vereinbarter Preis",
  "Maximum agreed price": "Höchster vereinbarter Preis",
  "Agreed unit price": "Vereinbarter Stückpreis",
  "Physical stock": "Physischer Bestand",
  "Reserved quantity": "Reservierte Menge",
  "Available quantity": "Verfügbare Menge",
  "Incoming quantity": "Erwartete Menge",
  "Open quantity": "Offene Menge",
  "Fulfilled quantity": "Erfüllte Menge",
  "Allocated amount": "Zugeordneter Betrag",
  "Unallocated amount": "Nicht zugeordneter Betrag",
  "Recorded amount": "Erfasster Betrag",
  "Returned quantity": "Retournierte Menge",
  "Due week": "Fälligkeitswoche",
  "Reversal status": "Stornostatus",
  "Other product": "Weiteres Produkt",
  "First observed order": "Erster erfasster Auftrag",
  "Last observed order": "Letzter erfasster Auftrag",
  "Weekly product demand": "Wöchentliche Produktnachfrage",
  "Orders by customer": "Aufträge nach Kunde",
  "Current inventory": "Aktueller Bestand",
  Month: "Monat",
  Quarter: "Quartal",
  Day: "Tag",
  "Occurrence date": "Ereignisdatum",
  "Effective date": "Wirksamkeitsdatum",
  Side: "Seite",
});
Object.assign(dictionaries.nl, {
  "All recorded history": "Alle vastgelegde historie",
  "Analysis chart": "Analysediagram",
  "Analysis results": "Analyseresultaten",
  "Analytics views": "Analyseweergaven",
  Ascending: "Oplopend",
  Descending: "Aflopend",
  "Bar chart": "Staafdiagram",
  "Show in chart": "Tonen in diagram",
  "Line chart": "Lijndiagram",
  "Based on interpreted records held in this company. Upstream history may be incomplete. Pages and exports use fresh observations.":
    "Gebaseerd op geïnterpreteerde gegevens van dit bedrijf. De bronhistorie kan onvolledig zijn. Pagina’s en exports gebruiken nieuwe waarnemingen.",
  "Change report": "Rapport wijzigen",
  "Chart shows a limited selection.": "Het diagram toont een beperkte selectie.",
  "Choose a perspective, measures and filters, then run your analysis. Select any result to see its supporting records.":
    "Kies een gegevensperspectief, meetwaarden en filters en voer de analyse uit. Selecteer een resultaat om de onderliggende gegevens te zien.",
  "Choose a grouping, such as customer or month, and run the analysis again.":
    "Kies een groepering, bijvoorbeeld klant of maand, en voer de analyse opnieuw uit.",
  "Compare with previous period": "Vergelijken met vorige periode",
  "Custom dates": "Aangepaste datums",
  "Data perspective": "Gegevensperspectief",
  "Date field": "Datumveld",
  "Delete this report?": "Dit rapport verwijderen?",
  Duplicate: "Dupliceren",
  "End date (exclusive)": "Einddatum (exclusief)",
  "Exact values and supporting records are available in the table.":
    "Exacte waarden en onderliggende gegevens staan in de tabel.",
  "Explore your business. Trace every answer.": "Onderzoek je bedrijf. Herleid elk antwoord.",
  "Export created from a fresh observation.": "Export gemaakt op basis van een nieuwe waarneming.",
  "Export CSV": "CSV exporteren",
  Filter: "Filtervoorwaarde",
  "Filter field": "Filterveld",
  "Filter operator": "Filteroperator",
  "Filter value": "Filterwaarde",
  Filters: "Filtervoorwaarden",
  "First page": "Eerste pagina",
  "Fresh observation of the selected value.": "Nieuwe waarneming van de geselecteerde waarde.",
  "Full population": "Volledige populatie",
  Group: "Groep",
  "Group by": "Groeperen op",
  "ISO week": "ISO-week",
  "Last complete months": "Laatste volledige maanden",
  "Last complete weeks": "Laatste volledige weken",
  "Last days": "Laatste dagen",
  "Match conditions": "Voorwaarden combineren",
  Measures: "Meetwaarden",
  "Missing values": "Ontbrekende waarden",
  "More records are available. Narrow the analysis to inspect a smaller group.":
    "Er zijn meer gegevens beschikbaar. Beperk de analyse om een kleinere groep te bekijken.",
  "My reports": "Mijn rapporten",
  "New analysis": "Nieuwe analyse",
  "Number of periods": "Aantal perioden",
  "Only the definition is saved. Results are refreshed when you run it.":
    "Alleen de definitie wordt opgeslagen. Resultaten worden bij elke uitvoering vernieuwd.",
  "Previous period": "Vorige periode",
  "Private to you in this company. Each opening runs against current records.":
    "Alleen voor jou zichtbaar in dit bedrijf. De analyse gebruikt actuele gegevens.",
  "Read-only analysis": "Alleen-lezenanalyse",
  "Refresh first page": "Eerste pagina vernieuwen",
  "Remove filter": "Filter verwijderen",
  Rename: "Hernoemen",
  "Report name": "Rapportnaam",
  "Report saved.": "Rapport opgeslagen.",
  "Results show the last executed settings. Run again to apply your edits.":
    "Resultaten horen bij de laatst uitgevoerde instellingen. Voer opnieuw uit om wijzigingen toe te passen.",
  "Run analysis": "Analyse uitvoeren",
  "Run the comparison period directly to inspect its records.":
    "Voer de vergelijkingsperiode rechtstreeks uit om de gegevens te bekijken.",
  "Running analysis…": "Analyse wordt uitgevoerd…",
  Save: "Opslaan",
  "Save an analysis to find it here.": "Sla een analyse op om deze hier terug te vinden.",
  "Save report": "Rapport opslaan",
  "Scope and data quality": "Bereik en gegevenskwaliteit",
  "Search reports": "Rapporten zoeken",
  "Select record": "Record selecteren",
  "Sort by": "Sorteren op",
  "Sort direction": "Sorteerrichting",
  "Start date": "Begindatum",
  "Start with a business question": "Begin met een bedrijfsvraag",
  "This month": "Deze maand",
  "This quarter": "Dit kwartaal",
  "This year": "Dit jaar",
  "Undated records excluded": "Uitgesloten gegevens zonder datum",
  Week: "Kalenderweek",
  Year: "Jaar",
  groups: "groepen",
  "All conditions": "Alle voorwaarden",
  "Any condition": "Een van de voorwaarden",
  Equals: "Is gelijk aan",
  "Does not equal": "Is niet gelijk aan",
  "In list": "Staat in lijst",
  "Not in list": "Staat niet in lijst",
  Contains: "Bevat",
  "At least": "Minstens",
  "Greater than": "Groter dan",
  "At most": "Hoogstens",
  "Less than": "Kleiner dan",
  "Is missing": "Ontbreekt",
  "Is present": "Is aanwezig",
  "Customer purchase history": "Aankoophistorie van klanten",
  "Products ordered together": "Samen bestelde producten",
  "Recorded payments": "Vastgelegde betalingen",
  "Sales order lines": "Verkooporderregels",
  "Purchase order lines": "Inkooporderregels",
  "Sales orders": "Verkooporders",
  "Purchase orders": "Inkooporders",
  "Inventory by location": "Voorraad per locatie",
  "Record count": "Aantal records",
  "Order count": "Aantal orders",
  "Customer count": "Aantal klanten",
  "Ordered quantity": "Bestelde hoeveelheid",
  "Stated line amount": "Opgegeven regelbedrag",
  "Stated order amount": "Opgegeven orderbedrag",
  "Minimum agreed price": "Laagste overeengekomen prijs",
  "Maximum agreed price": "Hoogste overeengekomen prijs",
  "Agreed unit price": "Overeengekomen eenheidsprijs",
  "Physical stock": "Fysieke voorraad",
  "Reserved quantity": "Gereserveerde hoeveelheid",
  "Available quantity": "Beschikbare hoeveelheid",
  "Incoming quantity": "Inkomende hoeveelheid",
  "Open quantity": "Open hoeveelheid",
  "Fulfilled quantity": "Vervulde hoeveelheid",
  "Allocated amount": "Toegewezen bedrag",
  "Unallocated amount": "Niet-toegewezen bedrag",
  "Recorded amount": "Vastgelegd bedrag",
  "Returned quantity": "Geretourneerde hoeveelheid",
  "Due week": "Vervalweek",
  "Reversal status": "Terugboekingsstatus",
  "Other product": "Ander product",
  "First observed order": "Eerste waargenomen order",
  "Last observed order": "Laatste waargenomen order",
  "Weekly product demand": "Wekelijkse productvraag",
  "Orders by customer": "Orders per klant",
  "Current inventory": "Huidige voorraad",
  Month: "Maand",
  Quarter: "Kwartaal",
  Day: "Dag",
  "Occurrence date": "Gebeurtenisdatum",
  "Effective date": "Ingangsdatum",
  Side: "Zijde",
});
Object.assign(dictionaries.es, {
  "All recorded history": "Todo el historial registrado",
  "Analysis chart": "Gráfico de análisis",
  "Analysis results": "Resultados del análisis",
  "Analytics views": "Vistas de análisis",
  Ascending: "Ascendente",
  Descending: "Descendente",
  "Bar chart": "Gráfico de barras",
  "Show in chart": "Mostrar en el gráfico",
  "Line chart": "Gráfico de líneas",
  "Based on interpreted records held in this company. Upstream history may be incomplete. Pages and exports use fresh observations.":
    "Basado en registros interpretados de esta empresa. El historial de origen puede estar incompleto. Las páginas y exportaciones usan observaciones nuevas.",
  "Change report": "Modificar informe",
  "Chart shows a limited selection.": "El gráfico muestra una selección limitada.",
  "Choose a perspective, measures and filters, then run your analysis. Select any result to see its supporting records.":
    "Elige una perspectiva, medidas y filtros, y ejecuta el análisis. Selecciona un resultado para ver sus registros de respaldo.",
  "Choose a grouping, such as customer or month, and run the analysis again.":
    "Elige una agrupación, como cliente o mes, y vuelve a ejecutar el análisis.",
  "Compare with previous period": "Comparar con el período anterior",
  "Custom dates": "Fechas personalizadas",
  "Data perspective": "Perspectiva de datos",
  "Date field": "Campo de fecha",
  "Delete this report?": "¿Eliminar este informe?",
  Duplicate: "Duplicar",
  "End date (exclusive)": "Fecha final (exclusiva)",
  "Exact values and supporting records are available in the table.":
    "Los valores exactos y los registros de respaldo están en la tabla.",
  "Explore your business. Trace every answer.": "Analiza tu empresa. Comprueba cada respuesta.",
  "Export created from a fresh observation.": "Exportación creada con una observación nueva.",
  "Export CSV": "Exportar CSV",
  Filter: "Filtro",
  "Filter field": "Campo de filtro",
  "Filter operator": "Operador de filtro",
  "Filter value": "Valor del filtro",
  Filters: "Filtros",
  "First page": "Primera página",
  "Fresh observation of the selected value.": "Nueva observación del valor seleccionado.",
  "Full population": "Población completa",
  Group: "Grupo",
  "Group by": "Agrupar por",
  "ISO week": "Semana ISO",
  "Last complete months": "Últimos meses completos",
  "Last complete weeks": "Últimas semanas completas",
  "Last days": "Últimos días",
  "Match conditions": "Combinar condiciones",
  Measures: "Medidas",
  "Missing values": "Valores ausentes",
  "More records are available. Narrow the analysis to inspect a smaller group.":
    "Hay más registros disponibles. Acota el análisis para examinar un grupo menor.",
  "My reports": "Mis informes",
  "New analysis": "Nuevo análisis",
  "Number of periods": "Número de períodos",
  "Only the definition is saved. Results are refreshed when you run it.":
    "Solo se guarda la definición. Los resultados se actualizan al ejecutarla.",
  "Previous period": "Período anterior",
  "Private to you in this company. Each opening runs against current records.":
    "Solo visible para ti en esta empresa. El análisis utiliza registros actuales.",
  "Read-only analysis": "Análisis de solo lectura",
  "Refresh first page": "Actualizar primera página",
  "Remove filter": "Eliminar filtro",
  Rename: "Cambiar nombre",
  "Report name": "Nombre del informe",
  "Report saved.": "Informe guardado.",
  "Results show the last executed settings. Run again to apply your edits.":
    "Los resultados corresponden a la última configuración ejecutada. Ejecuta de nuevo para aplicar los cambios.",
  "Run analysis": "Ejecutar análisis",
  "Run the comparison period directly to inspect its records.":
    "Ejecuta directamente el período de comparación para examinar sus registros.",
  "Running analysis…": "Ejecutando análisis…",
  Save: "Guardar",
  "Save an analysis to find it here.": "Guarda un análisis para encontrarlo aquí.",
  "Save report": "Guardar informe",
  "Scope and data quality": "Alcance y calidad de datos",
  "Search reports": "Buscar informes",
  "Select record": "Seleccionar registro",
  "Sort by": "Ordenar por",
  "Sort direction": "Dirección de orden",
  "Start date": "Fecha inicial",
  "Start with a business question": "Empieza con una pregunta de negocio",
  "This month": "Este mes",
  "This quarter": "Este trimestre",
  "This year": "Este año",
  "Undated records excluded": "Registros sin fecha excluidos",
  Week: "Semana",
  Year: "Año",
  groups: "grupos",
  "All conditions": "Todas las condiciones",
  "Any condition": "Cualquier condición",
  Equals: "Es igual a",
  "Does not equal": "No es igual a",
  "In list": "Está en la lista",
  "Not in list": "No está en la lista",
  Contains: "Contiene",
  "At least": "Como mínimo",
  "Greater than": "Mayor que",
  "At most": "Como máximo",
  "Less than": "Menor que",
  "Is missing": "Falta",
  "Is present": "Está presente",
  "Customer purchase history": "Historial de compras de clientes",
  "Products ordered together": "Productos pedidos juntos",
  "Recorded payments": "Pagos registrados",
  "Sales order lines": "Líneas de pedidos de venta",
  "Purchase order lines": "Líneas de pedidos de compra",
  "Sales orders": "Pedidos de venta",
  "Purchase orders": "Pedidos de compra",
  "Inventory by location": "Existencias por ubicación",
  "Record count": "Número de registros",
  "Order count": "Número de pedidos",
  "Customer count": "Número de clientes",
  "Ordered quantity": "Cantidad pedida",
  "Stated line amount": "Importe declarado de la línea",
  "Stated order amount": "Importe declarado del pedido",
  "Minimum agreed price": "Precio mínimo acordado",
  "Maximum agreed price": "Precio máximo acordado",
  "Agreed unit price": "Precio unitario acordado",
  "Physical stock": "Existencias físicas",
  "Reserved quantity": "Cantidad reservada",
  "Available quantity": "Cantidad disponible",
  "Incoming quantity": "Cantidad entrante",
  "Open quantity": "Cantidad pendiente",
  "Fulfilled quantity": "Cantidad cumplida",
  "Allocated amount": "Importe asignado",
  "Unallocated amount": "Importe sin asignar",
  "Recorded amount": "Importe registrado",
  "Returned quantity": "Cantidad devuelta",
  "Due week": "Semana de vencimiento",
  "Reversal status": "Estado de reversión",
  "Other product": "Otro producto",
  "First observed order": "Primer pedido observado",
  "Last observed order": "Último pedido observado",
  "Weekly product demand": "Demanda semanal de productos",
  "Orders by customer": "Pedidos por cliente",
  "Current inventory": "Existencias actuales",
  Month: "Mes",
  Quarter: "Trimestre",
  Day: "Día",
  "Occurrence date": "Fecha del suceso",
  "Effective date": "Fecha efectiva",
  Side: "Lado",
});

Object.assign(dictionaries.de, {
  "Pivot by selected dimensions": "Pivot nach ausgewählten Gruppierungen",
  "Pivot totals are calculated from the full population.":
    "Pivot-Summen werden aus dem gesamten Ergebnis berechnet.",
});
Object.assign(dictionaries.nl, {
  "Pivot by selected dimensions": "Draaitabel per geselecteerde dimensie",
  "Pivot totals are calculated from the full population.":
    "Draaitabeltotalen worden over de volledige populatie berekend.",
});
Object.assign(dictionaries.es, {
  "Pivot by selected dimensions": "Tabla dinámica por dimensiones seleccionadas",
  "Pivot totals are calculated from the full population.":
    "Los totales se calculan sobre la población completa.",
});

Object.assign(dictionaries.de, {
  "Attached analysis": "Angehängte Auswertung",
  "Open in Reports": "In Auswertungen öffnen",
  "Start new chat about analysis": "Neuen Chat zur Auswertung starten",
  "Wait for the current reply before starting a new chat.":
    "Warte auf die aktuelle Antwort, bevor du einen neuen Chat startest.",
  "Analysis attached. Review the settings and run it.":
    "Auswertung übernommen. Prüfe die Einstellungen und starte sie.",
});
Object.assign(dictionaries.nl, {
  "Attached analysis": "Bijgevoegde analyse",
  "Open in Reports": "Openen in rapporten",
  "Start new chat about analysis": "Nieuwe chat over analyse starten",
  "Wait for the current reply before starting a new chat.":
    "Wacht op het huidige antwoord voordat je een nieuwe chat start.",
  "Analysis attached. Review the settings and run it.":
    "Analyse toegevoegd. Controleer de instellingen en voer deze uit.",
});
Object.assign(dictionaries.es, {
  "Attached analysis": "Análisis adjunto",
  "Open in Reports": "Abrir en informes",
  "Start new chat about analysis": "Iniciar un nuevo chat sobre el análisis",
  "Wait for the current reply before starting a new chat.":
    "Espera la respuesta actual antes de iniciar un nuevo chat.",
  "Analysis attached. Review the settings and run it.":
    "Análisis adjunto. Revisa la configuración y ejecútalo.",
});

Object.assign(dictionaries.de, {
  "Billed quantity": "Fakturierte Menge",
  "Unbilled quantity": "Nicht fakturierte Menge",
  "Reservation gap": "Reservierungsfehlmenge",
  "Physical returns": "Physische Retouren",
  "Order line billing": "Fakturierung der Auftragspositionen",
  "Weekly product orders": "Wöchentliche Produktbestellungen",
});
Object.assign(dictionaries.nl, {
  "Billed quantity": "Gefactureerde hoeveelheid",
  "Unbilled quantity": "Niet-gefactureerde hoeveelheid",
  "Reservation gap": "Reserveringstekort",
  "Physical returns": "Fysieke retouren",
  "Order line billing": "Facturering van orderregels",
  "Weekly product orders": "Wekelijkse productbestellingen",
});
Object.assign(dictionaries.es, {
  "Billed quantity": "Cantidad facturada",
  "Unbilled quantity": "Cantidad sin facturar",
  "Reservation gap": "Déficit de reserva",
  "Physical returns": "Devoluciones físicas",
  "Order line billing": "Facturación de líneas de pedido",
  "Weekly product orders": "Pedidos semanales de productos",
});

/** Format exact decimal text without converting the received value to a float. */
export function formatExactDecimal(value: string | number): string {
  const text = String(value);
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(text);
  if (!match) return text;
  const integer = new Intl.NumberFormat(active.locale, { maximumFractionDigits: 0 }).format(
    BigInt(match[2]),
  );
  const separator =
    new Intl.NumberFormat(active.locale).formatToParts(1.1).find((part) => part.type === "decimal")
      ?.value || ".";
  const fraction = (match[3] || "").replace(/0+$/, "");
  return match[1] + integer + (fraction ? separator + fraction : "");
}

Object.assign(dictionaries.de, {
  Change: "Veränderung",
  "Change (%)": "Veränderung (%)",
  "Inventory and open demand": "Bestand und offener Bedarf",
  "Observed product suppliers": "Beobachtete Produktlieferanten",
  "Effective outbound movements": "Wirksame ausgehende Bewegungen",
  "Open demand": "Offener Bedarf",
  "Stock shortfall": "Bestandsfehlmenge",
  "Observed supplier count": "Anzahl beobachteter Lieferanten",
});

Object.assign(dictionaries.nl, {
  Change: "Verandering",
  "Change (%)": "Verandering (%)",
  "Inventory and open demand": "Voorraad en open vraag",
  "Observed product suppliers": "Waargenomen productleveranciers",
  "Effective outbound movements": "Effectieve uitgaande bewegingen",
  "Open demand": "Open vraag",
  "Stock shortfall": "Voorraadtekort",
  "Observed supplier count": "Aantal waargenomen leveranciers",
});

Object.assign(dictionaries.es, {
  Change: "Cambio",
  "Change (%)": "Cambio (%)",
  "Inventory and open demand": "Existencias y demanda pendiente",
  "Observed product suppliers": "Proveedores de productos observados",
  "Effective outbound movements": "Movimientos de salida efectivos",
  "Open demand": "Demanda pendiente",
  "Stock shortfall": "Déficit de existencias",
  "Observed supplier count": "Número de proveedores observados",
});

Object.assign(dictionaries.de, {
  "Match related records": "Zugehörige Datensätze abgleichen",
  "Has matching records": "Hat passende Datensätze",
  "Has no matching records": "Hat keine passenden Datensätze",
  "Related records": "Zugehörige Datensätze",
  "Outbound movements": "Ausgehende Bewegungen",
  "Stock and promised demand": "Bestand und zugesagter Bedarf",
  "Observed suppliers by product": "Beobachtete Lieferanten je Produkt",
  "Open customer demand": "Offener Kundenbedarf",
  "Moved quantity": "Bewegte Menge",
  "Until (exclusive)": "Bis (ausschließlich)",
});

Object.assign(dictionaries.nl, {
  "Match related records": "Gerelateerde records vergelijken",
  "Has matching records": "Heeft overeenkomende records",
  "Has no matching records": "Heeft geen overeenkomende records",
  "Related records": "Gerelateerde records",
  "Outbound movements": "Uitgaande bewegingen",
  "Stock and promised demand": "Voorraad en toegezegde vraag",
  "Observed suppliers by product": "Waargenomen leveranciers per product",
  "Open customer demand": "Open klantvraag",
  "Moved quantity": "Verplaatste hoeveelheid",
  "Until (exclusive)": "Tot (exclusief)",
});

Object.assign(dictionaries.es, {
  "Match related records": "Comparar registros relacionados",
  "Has matching records": "Tiene registros coincidentes",
  "Has no matching records": "No tiene registros coincidentes",
  "Related records": "Registros relacionados",
  "Outbound movements": "Movimientos de salida",
  "Stock and promised demand": "Existencias y demanda comprometida",
  "Observed suppliers by product": "Proveedores observados por producto",
  "Open customer demand": "Demanda pendiente de clientes",
  "Moved quantity": "Cantidad movida",
  "Until (exclusive)": "Hasta (exclusivo)",
});

Object.assign(dictionaries.de, {
  "Change private report": "Privaten Bericht ändern",
  "Analysis settings": "Auswertungseinstellungen",
});

Object.assign(dictionaries.nl, {
  "Change private report": "Privérapport wijzigen",
  "Analysis settings": "Analyse-instellingen",
});

Object.assign(dictionaries.es, {
  "Change private report": "Cambiar informe privado",
  "Analysis settings": "Configuración del análisis",
});

Object.assign(dictionaries.de, {
  "This analysis is too broad. Narrow the period or filters.":
    "Diese Auswertung ist zu umfangreich. Grenze Zeitraum oder Filter ein.",
  "The analysis took too long. Narrow the period or filters and run again.":
    "Die Auswertung hat zu lange gedauert. Grenze Zeitraum oder Filter ein und starte erneut.",
  "The analysis was cancelled.": "Die Auswertung wurde abgebrochen.",
  "Check the selected fields, filters and time window.":
    "Prüfe die ausgewählten Felder, Filter und den Zeitraum.",
  "This page no longer matches the analysis. Refresh the first page.":
    "Diese Seite passt nicht mehr zur Auswertung. Lade die erste Seite neu.",
  "The report changed. Reload it before saving again.":
    "Der Bericht wurde geändert. Lade ihn vor dem erneuten Speichern neu.",
  "This retry belongs to a different change. Reload the report.":
    "Dieser Wiederholungsversuch gehört zu einer anderen Änderung. Lade den Bericht neu.",
  "Sign in with your own account to use private reports.":
    "Melde dich mit deinem eigenen Konto an, um private Berichte zu nutzen.",
  "The analysis could not be completed.": "Die Auswertung konnte nicht abgeschlossen werden.",
});

Object.assign(dictionaries.nl, {
  "This analysis is too broad. Narrow the period or filters.":
    "Deze analyse is te omvangrijk. Beperk de periode of filters.",
  "The analysis took too long. Narrow the period or filters and run again.":
    "De analyse duurde te lang. Beperk de periode of filters en probeer opnieuw.",
  "The analysis was cancelled.": "De analyse is geannuleerd.",
  "Check the selected fields, filters and time window.":
    "Controleer de gekozen velden, filters en periode.",
  "This page no longer matches the analysis. Refresh the first page.":
    "Deze pagina hoort niet meer bij de analyse. Vernieuw de eerste pagina.",
  "The report changed. Reload it before saving again.":
    "Het rapport is gewijzigd. Laad het opnieuw voordat je opslaat.",
  "This retry belongs to a different change. Reload the report.":
    "Deze herhaling hoort bij een andere wijziging. Laad het rapport opnieuw.",
  "Sign in with your own account to use private reports.":
    "Meld je aan met je eigen account om privérapporten te gebruiken.",
  "The analysis could not be completed.": "De analyse kon niet worden voltooid.",
});

Object.assign(dictionaries.es, {
  "This analysis is too broad. Narrow the period or filters.":
    "Este análisis es demasiado amplio. Limita el período o los filtros.",
  "The analysis took too long. Narrow the period or filters and run again.":
    "El análisis tardó demasiado. Limita el período o los filtros y vuelve a ejecutarlo.",
  "The analysis was cancelled.": "Se canceló el análisis.",
  "Check the selected fields, filters and time window.":
    "Revisa los campos, filtros y período seleccionados.",
  "This page no longer matches the analysis. Refresh the first page.":
    "Esta página ya no corresponde al análisis. Actualiza la primera página.",
  "The report changed. Reload it before saving again.":
    "El informe ha cambiado. Vuelve a cargarlo antes de guardar.",
  "This retry belongs to a different change. Reload the report.":
    "Este reintento corresponde a otro cambio. Vuelve a cargar el informe.",
  "Sign in with your own account to use private reports.":
    "Inicia sesión con tu propia cuenta para usar informes privados.",
  "The analysis could not be completed.": "No se pudo completar el análisis.",
});
// Spec 186: company danger zone.
Object.assign(dictionaries.de, {
  "Archiving hides a company or sandbox from every member. Permanent deletion removes company data and cannot be undone.":
    "Archivieren blendet ein Unternehmen oder eine Testumgebung für alle Mitglieder aus. Endgültiges Löschen entfernt Unternehmensdaten und kann nicht rückgängig gemacht werden.",
  "Archive this company": "Dieses Unternehmen archivieren",
  "The company leaves the company switcher for every member. Nothing is deleted; you can restore it here.":
    "Das Unternehmen verschwindet für alle Mitglieder aus der Unternehmensauswahl. Es wird nichts gelöscht; du kannst es hier wiederherstellen.",
  "Archive this sandbox": "Diese Testumgebung archivieren",
  "The sandbox leaves the company switcher. Its records stay and you can restore it here.":
    "Die Testumgebung verschwindet aus der Unternehmensauswahl. Ihre Datensätze bleiben erhalten; du kannst sie hier wiederherstellen.",
  "Archive sandbox": "Testumgebung archivieren",
  "Archived sandboxes": "Archivierte Testumgebungen",
  "No archived sandboxes.": "Keine archivierten Testumgebungen.",
  "Loading archived sandboxes": "Archivierte Testumgebungen werden geladen",
  "Archived sandboxes could not be loaded.":
    "Archivierte Testumgebungen konnten nicht geladen werden.",
  "Deleting sandbox data is not available yet.":
    "Das Löschen von Testumgebungsdaten ist noch nicht verfügbar.",
  "This sandbox cannot be archived from here.":
    "Diese Testumgebung kann hier nicht archiviert werden.",
  "Only company owners can archive this company.":
    "Nur Inhaber des Unternehmens können es archivieren.",
  "This is your last active company. Create or restore another company first.":
    "Dies ist dein letztes aktives Unternehmen. Lege zuerst ein weiteres Unternehmen an oder stelle eines wieder her.",
  "Loading archived companies": "Archivierte Unternehmen werden geladen",
  "Archived companies could not be loaded.":
    "Archivierte Unternehmen konnten nicht geladen werden.",
  "Archived on": "Archiviert am",
  Restore: "Wiederherstellen",
  "Only company owners can restore or delete this company.":
    "Nur Inhaber des Unternehmens können es wiederherstellen oder löschen.",
  "This removes every record of the company. It cannot be undone.":
    "Dies entfernt alle Datensätze des Unternehmens. Es kann nicht rückgängig gemacht werden.",
  "Evidence documents": "Belege",
  "Type the company name exactly as shown.": "Gib den Unternehmensnamen genau wie angezeigt ein.",
  "Confirmation word": "Bestätigungswort",
  "Type the word shown exactly.": "Gib das angezeigte Wort genau ein.",
});
// Spec 186: company danger zone.
Object.assign(dictionaries.nl, {
  "Archiving hides a company or sandbox from every member. Permanent deletion removes company data and cannot be undone.":
    "Archiveren verbergt een bedrijf of sandbox voor alle leden. Definitief verwijderen wist bedrijfsgegevens en kan niet ongedaan worden gemaakt.",
  "Archive this company": "Dit bedrijf archiveren",
  "The company leaves the company switcher for every member. Nothing is deleted; you can restore it here.":
    "Het bedrijf verdwijnt voor alle leden uit de bedrijfskeuze. Er wordt niets verwijderd; je kunt het hier herstellen.",
  "Archive this sandbox": "Deze sandbox archiveren",
  "The sandbox leaves the company switcher. Its records stay and you can restore it here.":
    "De sandbox verdwijnt uit de bedrijfskeuze. De gegevens blijven bewaard; je kunt hem hier herstellen.",
  "Archive sandbox": "Sandbox archiveren",
  "Archived sandboxes": "Gearchiveerde sandboxes",
  "No archived sandboxes.": "Geen gearchiveerde sandboxes.",
  "Loading archived sandboxes": "Gearchiveerde sandboxes laden",
  "Archived sandboxes could not be loaded.": "Gearchiveerde sandboxes konden niet worden geladen.",
  "Deleting sandbox data is not available yet.":
    "Het verwijderen van sandboxgegevens is nog niet beschikbaar.",
  "This sandbox cannot be archived from here.": "Deze sandbox kan hier niet worden gearchiveerd.",
  "Only company owners can archive this company.":
    "Alleen bedrijfseigenaren kunnen dit bedrijf archiveren.",
  "This is your last active company. Create or restore another company first.":
    "Dit is je laatste actieve bedrijf. Maak eerst een ander bedrijf aan of herstel er een.",
  "Loading archived companies": "Gearchiveerde bedrijven laden",
  "Archived companies could not be loaded.": "Gearchiveerde bedrijven konden niet worden geladen.",
  "Archived on": "Gearchiveerd op",
  Restore: "Herstellen",
  "Only company owners can restore or delete this company.":
    "Alleen bedrijfseigenaren kunnen dit bedrijf herstellen of verwijderen.",
  "This removes every record of the company. It cannot be undone.":
    "Dit verwijdert alle gegevens van het bedrijf. Het kan niet ongedaan worden gemaakt.",
  "Evidence documents": "Bewijsdocumenten",
  "Type the company name exactly as shown.": "Typ de bedrijfsnaam precies zoals weergegeven.",
  "Confirmation word": "Bevestigingswoord",
  "Type the word shown exactly.": "Typ het weergegeven woord precies over.",
});
// Spec 186: company danger zone.
Object.assign(dictionaries.es, {
  "Archiving hides a company or sandbox from every member. Permanent deletion removes company data and cannot be undone.":
    "Archivar oculta una empresa o un sandbox a todos los miembros. La eliminación definitiva borra los datos de la empresa y no se puede deshacer.",
  "Archive this company": "Archivar esta empresa",
  "The company leaves the company switcher for every member. Nothing is deleted; you can restore it here.":
    "La empresa desaparece del selector de empresas para todos los miembros. No se elimina nada; puedes restaurarla aquí.",
  "Archive this sandbox": "Archivar este sandbox",
  "The sandbox leaves the company switcher. Its records stay and you can restore it here.":
    "El sandbox desaparece del selector de empresas. Sus registros se conservan; puedes restaurarlo aquí.",
  "Archive sandbox": "Archivar sandbox",
  "Archived sandboxes": "Sandboxes archivados",
  "No archived sandboxes.": "No hay sandboxes archivados.",
  "Loading archived sandboxes": "Cargando sandboxes archivados",
  "Archived sandboxes could not be loaded.": "No se pudieron cargar los sandboxes archivados.",
  "Deleting sandbox data is not available yet.":
    "La eliminación de datos del sandbox aún no está disponible.",
  "This sandbox cannot be archived from here.": "Este sandbox no se puede archivar desde aquí.",
  "Only company owners can archive this company.":
    "Solo los propietarios de la empresa pueden archivarla.",
  "This is your last active company. Create or restore another company first.":
    "Esta es tu última empresa activa. Crea o restaura otra empresa primero.",
  "Loading archived companies": "Cargando empresas archivadas",
  "Archived companies could not be loaded.": "No se pudieron cargar las empresas archivadas.",
  "Archived on": "Archivada el",
  Restore: "Restaurar",
  "Only company owners can restore or delete this company.":
    "Solo los propietarios de la empresa pueden restaurarla o eliminarla.",
  "This removes every record of the company. It cannot be undone.":
    "Esto elimina todos los registros de la empresa. No se puede deshacer.",
  "Evidence documents": "Documentos de evidencia",
  "Type the company name exactly as shown.":
    "Escribe el nombre de la empresa exactamente como se muestra.",
  "Confirmation word": "Palabra de confirmación",
  "Type the word shown exactly.": "Escribe exactamente la palabra mostrada.",
});
// Spec 192: applicant account deletion in platform administration.
Object.assign(dictionaries.de, {
  "Delete account": "Konto löschen",
  "This removes the account and every company only this person owns, with all records in them. It cannot be undone.":
    "Dies entfernt das Konto und jedes Unternehmen, das nur diese Person besitzt, samt allen Datensätzen darin. Es kann nicht rückgängig gemacht werden.",
  "Counting what this removes…": "Wird ermittelt, was dabei entfernt wird…",
  "No company is affected.": "Kein Unternehmen ist betroffen.",
  "Companies another owner holds are kept:":
    "Unternehmen mit einem weiteren Inhaber bleiben bestehen:",
  "E-mail address": "E-Mail-Adresse",
  "Type the address exactly as shown.": "Gib die Adresse genau wie angezeigt ein.",
});
Object.assign(dictionaries.nl, {
  "Delete account": "Account verwijderen",
  "This removes the account and every company only this person owns, with all records in them. It cannot be undone.":
    "Dit verwijdert het account en elk bedrijf dat alleen deze persoon bezit, met alle gegevens daarin. Dit kan niet ongedaan worden gemaakt.",
  "Counting what this removes…": "Bezig te bepalen wat dit verwijdert…",
  "No company is affected.": "Geen enkel bedrijf wordt geraakt.",
  "Companies another owner holds are kept:": "Bedrijven met een andere eigenaar blijven bestaan:",
  "E-mail address": "E-mailadres",
  "Type the address exactly as shown.": "Typ het adres precies zoals weergegeven.",
});
Object.assign(dictionaries.es, {
  "Delete account": "Eliminar cuenta",
  "This removes the account and every company only this person owns, with all records in them. It cannot be undone.":
    "Esto elimina la cuenta y todas las empresas que solo posee esta persona, con todos sus registros. No se puede deshacer.",
  "Counting what this removes…": "Calculando lo que esto elimina…",
  "No company is affected.": "Ninguna empresa se ve afectada.",
  "Companies another owner holds are kept:": "Las empresas con otro propietario se conservan:",
  "E-mail address": "Dirección de correo electrónico",
  "Type the address exactly as shown.": "Escribe la dirección exactamente como se muestra.",
});
// Spec 182: the storyline narrator reads as a conversation.
Object.assign(dictionaries.de, {
  Send: "Senden",
  Recorded: "Erledigt",
  "Your message": "Deine Nachricht",
  "Suggested by the storyline. You can change it.":
    "Von der Storyline vorgeschlagen. Ändern ist erlaubt.",
  "Your own words. Continue in the sandbox itself.":
    "Eigene Worte. Dann arbeitest du direkt in der Sandbox weiter.",
  "Work in the sandbox": "In der Sandbox arbeiten",
});
Object.assign(dictionaries.nl, {
  Send: "Versturen",
  Recorded: "Vastgelegd",
  "Your message": "Jouw bericht",
  "Suggested by the storyline. You can change it.":
    "Voorgesteld door de storyline. Je mag het wijzigen.",
  "Your own words. Continue in the sandbox itself.":
    "Eigen woorden. Dan werk je verder in de sandbox zelf.",
  "Work in the sandbox": "In de sandbox werken",
});
Object.assign(dictionaries.es, {
  Send: "Enviar",
  Recorded: "Registrado",
  "Your message": "Tu mensaje",
  "Suggested by the storyline. You can change it.": "Sugerido por la storyline. Puedes cambiarlo.",
  "Your own words. Continue in the sandbox itself.":
    "Tus propias palabras. Entonces sigues trabajando en el sandbox.",
  "Work in the sandbox": "Trabajar en el sandbox",
});
// Spec 182: the suggestion sits below the conversation and is taken over from there.
Object.assign(dictionaries.de, {
  "You could say": "Das könntest du jetzt sagen",
  "Use this": "Übernehmen",
  "Write your own message": "Oder schreib selbst etwas…",
});
Object.assign(dictionaries.nl, {
  "You could say": "Dit zou je nu kunnen zeggen",
  "Use this": "Overnemen",
  "Write your own message": "Of schrijf zelf iets…",
});
Object.assign(dictionaries.es, {
  "You could say": "Ahora podrías decir",
  "Use this": "Usar esto",
  "Write your own message": "O escribe tú algo…",
});
