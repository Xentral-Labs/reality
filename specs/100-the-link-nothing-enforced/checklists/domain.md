# Domain Checklist: The Link Nothing Enforced

**Purpose**: Validate the map, the three gates, and the honest limits of what a gate can prove  
**Created**: 2026-09-07  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Two Directions

- [ ] CHK001 Are both failure directions named, with the classes in each? [Completeness, Spec §Problem]
- [ ] CHK002 Is it said which direction is dangerous, and why? [Clarity, Spec §Problem]
- [ ] CHK003 Is the direction required per declared dependency rather than per reference? [Completeness, Spec §FR-004]
- [ ] CHK004 Is each direction proven by a recording rather than only declared? [Coverage, Spec §FR-004, Plan §Test Strategy]

## What A Reference Is

- [ ] CHK005 Is the set of references discovered from the mapper rather than listed? [Consistency, Spec §FR-001, §DR-003]
- [ ] CHK006 Is the load-bearing / trace-only split required, with a reason on every trace-only entry? [Completeness, Spec §FR-002]
- [ ] CHK007 Is it explained why trace-only references are not walked, and what that costs? [Clarity, Plan §Discovering the consumers, §Review Risks]
- [ ] CHK008 Is the fourth reference the discovery found named, as evidence the list would have been wrong? [Clarity, Plan §Review Risks]

## Why The References Stay Optional

- [ ] CHK009 Is making them required argued down with a case where the record is legitimately unlinked? [Clarity, Plan §Simpler alternatives]
- [ ] CHK010 Is a class reporting a missing link argued down on the same ground Spec 088 used? [Consistency, Spec §Non-Goals]
- [ ] CHK011 Is guessing the link argued down, including why a wrong link is worse than none? [Clarity, Plan §Simpler alternatives]

## The Gates

- [ ] CHK012 Does each gate compose one discovered fact with one declared fact? [Consistency, Plan §What the gate is composed of]
- [ ] CHK013 Does every gate fail in both directions, with the stale-exemption reason stated? [Coverage, Spec §FR-008]
- [ ] CHK014 Is the writer gate a syntax-tree walk rather than a text search, with the reason? [Clarity, Plan §Discovering the writers]
- [ ] CHK015 Is it stated that passing the keyword is not passing a value? [Clarity, Spec §Assumptions, Plan §Discovering the writers, §Review Risks]
- [ ] CHK016 Is the consumer walk's limit stated — one module, calls by name? [Completeness, Plan §Review Risks]

## Surfaces, And The Agent

- [ ] CHK017 Is a passthrough allowed for a human adapter and refused for MCP, with the argument? [Clarity, Spec §FR-007, Plan §Discovering the surfaces]
- [ ] CHK018 Is the point made that a field a schema does not name will never be sent by an agent? [Clarity, Spec §Clarifications]
- [ ] CHK019 Are both first-run findings written down before the gate exists? [Completeness, Spec §Two things already broken]
- [ ] CHK020 Is the Spec 091 parallel drawn — an operation nothing could reach? [Consistency, Spec §Two things already broken]
- [ ] CHK021 Is the plain identity box acknowledged as poor interaction design, with what was chosen instead of it? [Clarity, Plan §Review Risks]

## What Is Left Alone

- [ ] CHK022 Is it required that no class, derivation, register or projection changes? [Coverage, Spec §FR-011]
- [ ] CHK023 Is existing tenant data explicitly out of scope? [Clarity, Spec §Non-Goals, §Assumptions]
- [ ] CHK024 Is it stated that the gate governs paths rather than rows? [Clarity, Spec §Assumptions]
- [ ] CHK025 Is it confirmed that no migration is added? [Completeness, Spec §DR-001]
- [ ] CHK026 Is the closed exception registry untouched? [Consistency, Spec §DR-004]
- [ ] CHK027 Is the declaration validated by its loader rather than only by a test? [Consistency, Spec §DR-002]
