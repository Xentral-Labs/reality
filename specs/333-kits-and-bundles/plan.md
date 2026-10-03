# Implementation Plan: Kits, Bundles and Light Assembly

**Branch**: `333-kits-and-bundles` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

- **Bill of materials:** a kit is a stocked item with a stated bill of materials, the `kit_component` rows, from one reviewed definition.
- **Assembly:** a reviewed assembly writes paired movements under one source record. Each component leaves through an `assembly_input` movement, and the kit enters through an `assembly_output` movement.
- **Availability:** read at read time.
- **Bundle split:** read at read time, from the stated shares.
- **Shipping, returns and invoices:** these work on the kit item, unchanged.
- **Oversold:** *Oversold* counts the kits the free components build.
- **Inventory costing:** cost reviews refuse items with assembly movements.

## Technical Context

**Language/Version**: Python 3.12, TypeScript (web)

**Storage**: one new table, `kit_component` (migration 0123), and two new movement types. No new column on existing tables.

**Testing**:
- service tests with positive controls;
- adapter tests (MCP, CLI, web API, proposal review);
- stories K01, K02, K03, K04 and K06;
- the existing movement, costing, oversold and isolation suites as regression.

**Constraints**:
- tenant-scoped;
- all or nothing;
- derived at read time;
- unchanged results for companies without kits.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The definition and every assembly are source records. The assembly movements name theirs. |
| II. Reality is the operational authority | PASS | No document status. Availability and the split are derived. |
| III. Proven schema only | PASS | `kit_component` is read by availability, assembly, the split, *Oversold* and the definition checks (DR-001 below). |
| IV. Tenant and service boundaries | PASS | Shared application tools. Every query filters the tenant. Isolation catalog entries. |
| V. Specification and test evidence | PASS | Tests planned first, plus stories per journey. |
| VI. Explainable Web product | PASS | The item page shows components, availability and the limiting component. An assembly names its statement. |
| VII. Simplicity and storage discipline | PASS | One table. The kit stays an item, so no second notion of delivered. |
| VIII. Received values are recorded, never recomputed | PASS | Quantities and shares are kept as stated. The split divides the stated line amounts, and the parts add up exactly. |

### DR-001: `kit_component`

| Column | Read by |
|---|---|
| `kit_item_id`, `component_item_id`, `quantity` | Availability, the assembly's consumption and checks, *Oversold*, the read |
| `share` | The split and the K03 credit |
| `source_record_id` | The statement in force (spec 320 pattern), for the trace |

Unique per kit and component. Quantities are checked positive and shares in [0, 1].

### Movement types

`assembly_input` (out of a location) and `assembly_output` (into a location) are internal. They are not public movement types, so `movement_create` cannot write them. Only the assembly service writes them, always with the assembly's source record.

## Design

1. **Domain/schema:**
   - `KitComponent` in `db/core.py` and migration `0123_kit_components`.
   - `_append_movement` accepts the two types with their directions. `assembly_input` takes free stock only (the existing physical and blocked checks).
2. **Service `services/kits.py`:**
   - `validate_kit_definition` and `define_kit` (source system `internal_kit`, stream per kit item, event `kit.defined`).
   - `kit_components` and `kits` (definitions and per-location availability).
   - `kit_availability`.
   - `validate_kit_assembly` and `assemble_kit` (source `kit_assembly`, event `kit.assembled`).
   - `kit_split(document_line_id)`.
   - Reviews `review_kit_definition` and `review_kit_assembly`. Each refuses what its execution refuses, and the assembly review shows consumption and what is free.
3. **Guards:**
   - `movement_correct` refuses assembly movements (`movement_assembly_not_correctable`).
   - Inventory cost preparation refuses an item with assembly movements (`inventory_assembly_not_costed`).
4. ***Oversold*:** for kit items, the stock adds the kits buildable from free components.
5. **Tools:**
   - `kit_define` and `kit_assemble` (reviewed);
   - `kits` and `kit_split` (reads);
   - MCP `_propose` tools and the reads;
   - CLI `kit define|assemble|show|split`;
   - web API `/kits`, `/kits/split` and `/kits/proposals`.
6. **Web:** the item master data page gets a Kit section with components, shares and availability per location, plus "Define kit" and "Assemble" dialogs with server review and confirmation.
7. **Catalogs:**
   - business events;
   - command, tool and action-discovery catalogs;
   - resource catalog and German labels;
   - isolation catalog;
   - data model;
   - reference catalog consumers;
   - service refusals;
   - i18n;
   - `catalogs.py` module loops;
   - `make docs-generate`.
8. **Stories and Guide:** K01, K02, K04 and K06 are promoted, and K03 is set to partial. Then the coverage, roadmap and matrix.

## Rollback

The migration downgrade refuses while kits are stated. Removing the service and tools leaves the movements readable as plain stock movements.
