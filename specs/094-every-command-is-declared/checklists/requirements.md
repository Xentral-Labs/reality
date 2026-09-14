# Specification Quality Checklist: An Operation Nobody Declared

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-06
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] Every functional requirement has an acceptance scenario or a named edge case
- [x] The population the gate governs is defined, and the alternatives are measured rather than
      described
- [x] The gate is required to fail in both directions
- [x] The exemption list's failure mode is named, with what limits it
- [x] The operations the measurement found are declared rather than only counted

## Author Notes

This is the structural item Spec 091 named when it fixed a defect: the tenant isolation catalog
is complete by discovery and the command catalog is written by hand, so an operation can be
built, made tenant-safe, wired to a surface and never declared.

Three candidate populations were measured before one was chosen, and the numbers are in the plan
rather than an assurance that the choice was careful. Gating every mutation would have produced
28 entries, most of them exemptions reading "this is internal". Gating every service a surface
touches adds fourteen saying "this is a read". Gating only HTTP misses the agent tools — where
the most telling omission lives: **releasing a reservation has had an agent tool and no catalog
entry for its whole life.** An agent could do it and the catalog said the product could not.

The honest weakness is the exemption list, and it is the same weakness every allow-list has:
nothing stops somebody writing "not a command" and moving on. Two things limit it — a reason is
required, and a stale entry fails the build — and neither is a guarantee. What changes is that
the decision becomes a line in a reviewed file instead of an absence nobody can see, which is
exactly the difference between this and the situation that produced 091.

Six of the fourteen are judgement calls rather than facts: chat session handling and the import
worker mutate and are reachable, and calling them not-commands is a claim. Each is one line, on
purpose, so it can be argued with.
