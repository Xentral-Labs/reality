# Implementation Plan: Dunning Run and Escalation

**Branch**: `295-dunning-run` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

## Summary

Add a company dunning schedule (three levels with waiting days and a fixed fee), a reviewed
dunning run that proposes spec 247 notices for overdue open items at the level their last
non-reversed notice and the schedule allow, and a reviewed collection handover after level 3
that stops further notices and places a party delivery hold with the reason `collection`.
Levels and eligibility are derived at read time. N04 is then promoted in the Business Journey
Guide.

## Technical Context

**Language/Version**: Python 3.12; TypeScript 5.8 / React 19 for the Web dunning area

**Primary Dependencies**: SQLAlchemy 2, Alembic, Pydantic v2, Typer, FastAPI; existing finance
change proposal and spec 247 dunning service

**Storage**: PostgreSQL; three new tables, migration `0102_dunning_run`

**Testing**: pytest on disposable PostgreSQL (service, adapter, isolation, catalog gates,
business story); Node contract tests and i18n audit for Web

**Target Platform**: Reality core service, Web, MCP/Chat, CLI

**Project Type**: Domain capability across the full stack

**Performance Goals**: One run preview reads aging, notice links, reversal events, credits and
handovers once each; no per-invoice query (spec 181, spec 241)

**Constraints**: No document status fields; no stored level; notices stay spec 247 notices;
tenant-scoped everywhere; every mutation confirmed

**Scale/Scope**: 3 tables, 1 service module, 3 commands, 4 reads, 3 adapters, about 15 catalog
files

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Schedule, run and handover are confirmed manual source records; notices, fees and handovers are Reality derived from them. |
| II. Reality is the operational authority | PASS | Level, eligibility and "in collection" come from notices, reversal events and handovers; invoices gain no field (DR-002). |
| III. Proven schema only | PASS | `dunning_schedule_level` decides every item's level and every fee in each run; `collection_handover(_invoice)` is filtered by every run and joined by the handover read and invoice explanation (research R2, R6). |
| IV. Tenant and service boundaries | PASS | Composite tenant FKs; service writes only; commands through the shared finance change proposal on every surface. |
| V. Specification and test evidence | PASS | Approved spec; tests planned before each implementation task. |
| VI. Explainable Web product | PASS | Each proposed notice names its items, previous notice and waiting period; handovers link notices, hold and source (FR-012). |
| VII. Simplicity and storage discipline | PASS | Run notices reuse `record_notice` through one private helper; the hold reuses `hold_party_delivery`'s body. |
| VIII. Received values are recorded, never recomputed | PASS | Waiting days and fees are stated by the company; a notice records the fee as stated at confirmation; no amount is calculated. |

Post-design check: PASS. [data-model.md](data-model.md) adds no column to existing tables and
[contracts/dunning-run.md](contracts/dunning-run.md) reuses the finance change proposal.

## Design

### Flow

```text
schedule (3 levels) ─┐
aging (overdue)  ────┼─ run preview ── review ── confirm ─┬─ notice per customer/currency/level (spec 247)
notices − reversals ─┤   (read)                            └─ skipped items with codes
handovers, credits ──┘
level 3 notice ── collection handover ── party delivery hold "collection"
```

### Service (`services/dunning_runs.py`)

- `schedule(session, tenant_id)` / `set_schedule(..., levels, action_id, actor_id, expected_revision)`.
- `run_context(session, tenant_id, run_date, party_ids)`: the derivation of research R3 plus
  credit (R5) and handovers; returns the contract shape.
- `confirm_run(..., run_date, party_ids, items, action_id, actor_id, expected_revision)`:
  `lock_finance`, revision check, re-derive, group eligible items, call
  `dunning._record_notice` per group with `source_key = f"{action_id}:{n}"`, write the run
  source record and `dunning.run_confirmed`, idempotent on `action_id`.
- `record_handover(...)`, `handover_detail(...)`, `handovers(...)`.
- `invoice_dunning_state(session, tenant_id, invoice_ids)`: the shared per-invoice reader
  (last notice, level, handover) used by the preview, the handover checks and the invoice
  explanation, so all readers agree.

### Changes to existing code

- `services/dunning.py`: extract `_record_notice(..., source_key, run_source_record_id=None)`;
  `record_notice` calls it with `source_key=action_id` (unchanged behaviour).
- `services/core.py`: add `collection` to `HOLD_REASONS`; extract
  `_place_party_delivery_hold(..., _commit)` from `hold_party_delivery`.
- `tools/finance.py`: three request models and routes in `EDGE_COMMANDS` and the executor.
- Invoice explanation / finance invoice read: name the last notice, the derived level and any
  handover.

### Adapters

Web: schedule form, run review with item checkboxes and skip reasons, handover action on
"ready for collection", read endpoints `GET .../finance/dunning/schedule`,
`GET .../finance/dunning/run-context`, `GET .../finance/dunning/collection-handovers[/{id}]`,
sandbox read allowlist, action discovery. MCP: the four reads and three `_propose` tools with
strict schemas. CLI: `finance dunning-schedule`, `dunning-schedule-set`, `dunning-run`,
`dunning-collection`.

### Catalogs and gates

Every file in research R7, with the pinned counts raised in the same commit as their cause.

## Risks

- Two runs for the same date: serialized by `lock_finance`; the second sees the first's notices
  and skips with `level_changed` (test planned).
- The hold helper extraction touches an existing path; the existing hold tests must stay green.
