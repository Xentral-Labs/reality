# Implementation Plan: Everyday Fact Predicates

**Language**: English

## Constitution Check

- Source → Evidence → Reality: every Fact still requires a retained source record and an existing
  subject; nothing is derived or stored as new authority.
- No schema change: predicates live in the executable catalog; `lot` joins the subject map that
  already resolves tenant-scoped records.
- All adapters reach the same `observe_fact` service; no adapter gains its own rule.

## Steps

1. Register six predicates in `fact_catalog.yaml` with subject types and value contracts.
2. Add `lot` to the subject models `observe_fact` resolves.
3. Update the two catalog-count assertions and add service tests for the happy path and the
   refusals (value contract, subject type).
4. Documentation follows in the handbook chapter on Facts (separate change).
