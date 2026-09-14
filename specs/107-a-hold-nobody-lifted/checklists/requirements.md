# Specification Quality Checklist: The Hold Nobody Lifted

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-08
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
- [x] Every domain requirement states what may not be stored, released or shared
- [x] The clearing path was verified reachable before the class was designed
- [x] What is deliberately left standing is stated, with why it is a separate specification
- [x] The standing risk the feature adds to is acknowledged rather than omitted

## Author Notes

The gap was found by asking what the queue *reads*, and the answer was blunt: `exceptions.py`
touches `CommitmentHold` and `PartyHold` **zero times**. There is a hold register a person can go
and read, and nothing that ever tells anybody to.

What made it worth doing rather than merely tidy is the second-order effect. `close_stale_promises`
skips held promises on purpose — a sweep must not close something out from under the person dealing
with it — and **that protection has no expiry**. A hold raised for a credit check somebody finished
a year ago goes on shielding its promise from the only operation that could close it, and nothing
reports either the hold or the shielding. A forgotten hold is not untidy, it is permanent.

The first thing done was not design. It was checking that a person can actually lift these holds
from a surface, because Spec 091 found five shipped classes whose clearing path nothing reached.
Both release operations are declared on all five adapters, and that check is recorded in the plan
rather than assumed.

Two things a reviewer should weigh.

**This adds two classes to a threshold nobody has measured.** The Spec 080 helper now serves eight
classes and none of its numbers has been checked against a real business — the largest standing
risk in this queue. This specification makes it slightly larger. The argument for doing it anyway
is that a learned rhythm is better evidence than a configured number, and the alternative here is
no visibility at all.

**A count is a weak figure for a party hold.** "Blocking nine deliveries" says nothing about
whether those nine matter. The alternatives are worse: summing quantities across different items
produces a number that means nothing, which Spec 076 settled, and listing the promises would be a
wall. The count is the honest figure available, and anyone who wants more is asking for a read
model rather than a class.
