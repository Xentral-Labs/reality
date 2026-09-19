# Verification

- Before implementation, generator tests failed on the absent generator module.
- Seven Python reference tests pass, including exact executable-declaration parity,
  deterministic generation and a guard prohibiting database connections.
- 72 documentation Node tests pass. The Vue render test renders every one of the
  64 object details in both languages, checks measure and relationship presence,
  and exercises unknown selections and empty search output.
- VitePress production build passes; modified files pass Prettier, Ruff and whitespace checks.
- Spec policy passes. Generated JSON hash is identical across repeated docs generation.
- Current generated inventory: 64 objects, 189 outgoing relationships, 88 measures,
  21 templates. No business values or live company data are exported.
- Final review confirms existing model/resource/process/technical branches remain,
  analytics hashes validate node names, links preserve the locale, and relationship
  navigation reuses existing pushState/popstate handling. Responsive styles wrap tabs,
  stack detail below the picker on narrow screens, and wrap technical definitions.
- Native browser provider is unavailable. Render tests are not an interactive browser
  or visual mobile review; that portion remains pending under T004.
- Existing unrelated source/catalog/workspace edits were preserved. Catalog regeneration
  includes the working tree's current vocabulary. `docs-catalog-check` uses git diff
  and cannot be clean until the generated working tree changes are committed; generated
  freshness was checked by repeat generation instead.

Local preview: http://localhost:5188/tool-usage/#analytics:order and
http://localhost:5188/de/tool-usage/#analytics:order. No publication performed.

## Canonical English entry names (FR-006)

Owner requested consistent English entry names in non-English views. Resource/process
labels, step names, technical entries, group labels and data-model actions now use
English names; localized descriptions and controls remain. Analytics export uses the
English names for objects, fields, relationships, measures and templates, with original
German names retained as search terms and German meanings retained. Runtime catalog
labels are unchanged.

The new parity test failed before the change. Eight generator tests, 73 Node tests
(including bilingual render coverage), the production build, Ruff, spec policy and
whitespace checks pass. Regenerated through make docs-generate. Visual browser review
remains subject to the already documented unavailable browser provider.

## PR preparation against current main

Changes were transferred to an isolated worktree based on `aa10f4fc`. Only the docs
feature was transferred; ongoing inventory, costing and command-palette edits in the
original workspace were not included. Regenerating against current main changes only
`analyticsModel` at the top level of tool-usage.json; existing catalog sections remain
identical. Eight generator tests, 73 documentation tests, full docs formatting, Ruff
and the production build pass on this checkout. CI now discovers all docs Python tests.

The guide also links the spec234 measurements now present on main, recording dataset
size, sample timings and best-of-three methodology without claiming a p95 guarantee.
The earlier local verification remains historical evidence, not a new benchmark.
