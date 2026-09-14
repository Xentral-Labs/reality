# Feature Specification: Additional Fact Rules Label

**Feature Branch**: `191-additional-fact-rules`
**Created**: 2026-09-14
**Status**: Implemented (2026-09-14); scope approved by the owner in conversation
**Language**: English
**Input**: Owner question (German, 2026-09-14): "Facts" is the umbrella for all records and the
typed Fact family is "Additional facts" in the type filter; does the Rules page have to follow,
so that "Fact rules" becomes "Additional fact rules"?

## Context and Intent

### Problem

Spec 138's navigation review fixed the Reality Inspector vocabulary: **Facts** is the broad
entry for recorded business information (the register "All records"), and the typed Fact family
is labelled **Additional facts** in the type filter. The Rules page did not follow. Its first tab
and page title read **Fact rules**, its subtitle says "Review the rules used to interpret source
data into business records", and the wizard and evidence copy speak of "a Fact rule". A reader
who has just learned that Facts means everything reads "Fact rules" as rules for everything,
while these rules create exactly the records the register calls Additional facts.

### Scope

- The first Rules tab and the Rules page title become **Additional fact rules**; German
  "Regeln für zusätzliche Fakten", Dutch "Regels voor aanvullende feiten", Spanish "Reglas de
  hechos adicionales".
- The Rules page subtitle says what these rules do: "Review the rules that record additional
  facts from source data on the right business record."
- The three UI sentences that say "a Fact rule" (wizard explanation, wizard non-rule outcome,
  evidence example saved) say "an Additional fact rule", in all four UI languages.
- `docs/WEB_SPEC.md` records the label rule beside the spec 138 umbrella decision.

### Non-Goals

- No change to the record type, its table, predicates, API, MCP tools, CLI commands or their
  catalog descriptions. "Fact rule" stays the technical name of the rule type
  (`FactRule`, `fact_rule_*` commands, "Simulate Fact rule" tool titles), exactly as
  "Fact" stays the technical name of the record while the UI filter says Additional facts.
- No rename of "Additional facts" itself and no reopening of the spec 138 navigation names.
- No change to the concept documentation under `apps/docs/content`, which explains the model
  in technical terms and already distinguishes supported Facts from Reality records.
- No change to the Exception rules tab.

### Existing Contracts

- [Reality Inspector navigation review](../138-reality-inspector/navigation-review.md): the
  approved names Context, Facts, Rules, Actions and the label Additional facts.
- [First-time Fact rule wizard](../177-fact-rule-wizard/spec.md): the wizard whose copy changes.
- [docs/WEB_SPEC.md](../../docs/WEB_SPEC.md): shared vocabulary of the web product.

## User Scenarios & Testing

### User Story 1 - The register and the rules that fill it share one name (Priority: P1)

A reader opens Facts, sees the type filter entry Additional facts, then opens Rules and finds
the tab Additional fact rules with a subtitle that says these rules record additional facts.

**Why this priority**: It is the only change; without it the vocabulary decision of spec 138 is
half applied.

**Independent Test**: The navigation test asserts the Rules tab labels; the browser proof
opens the tab by its new name; the i18n audit proves every language carries the new strings.

**Acceptance Scenarios**:

1. **Given** the Reality Inspector, **When** Rules opens, **Then** the tabs read
   "Additional fact rules" and "Exception rules", the page title is "Additional fact rules" and
   the subtitle is the new sentence.
2. **Given** German, Dutch or Spanish, **When** the same page opens, **Then** the tab, title and
   subtitle are translated and no English string leaks.
3. **Given** the rule wizard, **When** the explanation, the non-rule outcome or the saved-example
   message renders, **Then** it says "Additional fact rule".

### Edge Cases

- Legacy links that select the `rules` inspector view keep working; only labels change.
- The browser proof's tab-name map and the navigation test are updated together with the label,
  so a stale label fails CI rather than passing silently.

## Requirements

### Functional Requirements

- **FR-001**: The first Rules tab and the Rules page title MUST read "Additional fact rules" in
  English and the agreed translation in German, Dutch and Spanish.
- **FR-002**: The Rules page subtitle MUST describe the rules as recording additional facts from
  source data on the right business record, in all four languages.
- **FR-003**: Every UI sentence that names such a rule MUST say "Additional fact rule"; no UI
  string may say "Fact rule" without the qualifier.
- **FR-004**: Technical names of the rule type, its commands and tool descriptions MUST stay
  unchanged.
- **FR-005**: `docs/WEB_SPEC.md` MUST record the label rule next to the Additional facts decision.

## Success Criteria

- **SC-001**: `apps/web/scripts/inspector-navigation.test.mjs` asserts the new tab labels and the
  web test suite passes.
- **SC-002**: `npm run i18n:audit` reports every language fully covered.
- **SC-003**: `grep` for "Fact rule" in `apps/web/src` outside `localization.tsx` finds only
  strings that read "Additional fact rule".

## Assumptions and Dependencies

- Depends on spec 138 (navigation names) and spec 177 (wizard copy) being merged, which they
  are.
- The owner accepted "Additional fact rules" over alternatives such as "Observation rules"
  because renaming the typed family would reopen spec 138 and touch code, catalogs and four
  languages without a user-facing gain.
- Related open question recorded for the owner, not part of this feature: whether a register of
  all Reality records (Commitments, Reservations, Movements, LedgerEntries) is wanted as its own
  page beside Facts.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001 | `apps/web/src/unified/inspectorSections.ts`, `localization.tsx`; `inspector-navigation.test.mjs`, `unified-inspector-browser.mjs` |
| FR-002 | `apps/web/src/unified/pageIntroduction.ts`, `localization.tsx` |
| FR-003 | `FactRuleWizard.tsx`, `RuleEvidence.tsx`, `localization.tsx`; SC-003 grep |
| FR-004 | no change under `packages/reality-core`; catalogs untouched |
| FR-005 | `docs/WEB_SPEC.md` spec 138 vocabulary paragraph |
