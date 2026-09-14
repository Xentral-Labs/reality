# Specification Quality Checklist: Operational Master Data Baseline

**Purpose**: Validate the as-is master-data baseline before owner review
**Created**: 2026-08-31
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] Specification and evidence are written in English.
- [x] Scope is organized around business capabilities, not tables or endpoints.
- [x] Operational fields are justified by existing decisions and constraints.
- [x] Non-goals prevent unproven schema expansion.

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` marker remains.
- [x] Party, Item, Location, PaymentTerm, and pricing lifecycle are covered.
- [x] User stories are independently testable.
- [x] Edge cases include tenant, hierarchy, lifecycle, source, and pricing boundaries.
- [x] Stored master data and derived Reality state are separated.

## Evidence Quality

- [x] Every requirement has exactly one evidence status.
- [x] Verified requirements link contract, implementation, and green proof.
- [x] Historical price non-rewrite is conservatively recorded as a Documented gap.
- [x] Full Web/CLI/API equivalence is conservatively recorded as a Documented gap.
- [x] Lossless source trace and manual-record behavior are represented.

## Review

- **Specification reviewer**: Product owner, approved 2026-08-31
- **Domain/commercial reviewer**: Product owner, approved 2026-08-31
- **Decision**: Reviewed; documented evidence gaps retained

## Notes

The owner confirmed that advanced discounting, product structures, contacts/addresses,
and complex unit conversion remain outside the current baseline. FR-014 and FR-016
remain visible Documented gaps.
