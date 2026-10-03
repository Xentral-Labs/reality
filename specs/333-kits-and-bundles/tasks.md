# Tasks: Kits, Bundles and Light Assembly

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 `tests/test_kits.py`:
  - definition checks;
  - availability with a positive control;
  - assembly all-or-nothing;
  - the paired movements;
  - the correction and costing refusals;
  - the split adds up;
  - *Oversold* counts buildable kits;
  - tenant isolation.
- [x] T002 `tests/test_kit_adapters.py`: MCP strict schemas and reads, the proposal review refusing what execution refuses, the CLI, and the web API.

## Phase 2: Domain and schema

- [x] T003 `KitComponent` model, migration `0123_kit_components`, data model, isolation catalog and FK indexes.
- [x] T004 `assembly_input` and `assembly_output` in `_append_movement`. Refusals in `movement_correct` and in inventory cost preparation.

## Phase 3: Services

- [x] T005 `services/kits.py`: definition, availability, assembly, split and reviews.
- [x] T006 *Oversold* counts buildable kits.

## Phase 4: Tools and adapters

- [x] T007 Application tools, proposal reviews, MCP, CLI and web API.
- [x] T008 Catalogs:
  - events, commands, tools and discovery;
  - resource catalog and German labels;
  - refusals;
  - reference catalog;
  - `catalogs.py`.

## Phase 5: Web

- [x] T009 The Kit section on the item page, with the define and assemble dialogs, i18n and the browser fixture.

## Phase 6: Stories and Guide

- [x] T010 Stories K01, K02, K03, K04 and K06.
- [x] T011 Promote K01, K02, K04 and K06, and set K03 to partial with its finding: catalog, coverage, roadmap and matrix, then `make docs-generate`.

## Phase 7: Verify

- [ ] T012 The full backend suite, web checks, i18n and spec policy, then a green PR.
