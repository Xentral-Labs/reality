# Implementation Plan: Additional Fact Rules Label

**Language**: English

## Constitution Check

- No schema, service, API or tool change; labels and one documentation paragraph. PASS
- Web product stays explainable: the label now says what the rules produce. PASS
- Shared language: one UI name for the register and the rules that fill it; technical names
  unchanged, so CLI, API and MCP vocabulary is not forked. PASS

## Steps

1. `inspectorSections.ts`: tab label. `pageIntroduction.ts`: subtitle. `FactRuleWizard.tsx`,
   `RuleEvidence.tsx`: the three sentences.
2. `localization.tsx`: rename the five English keys and translate de, nl, es.
3. Tests: `inspector-navigation.test.mjs` tab labels; `unified-inspector-browser.mjs` tab map
   and tab click.
4. `docs/WEB_SPEC.md`: label rule beside the Additional facts paragraph; the Rules section
   heading path.
5. Gates: prettier, `npm test`, `npm run i18n:audit`, `npm run build`, `make spec-check`.

## Rollback

Revert the commit; labels only.
