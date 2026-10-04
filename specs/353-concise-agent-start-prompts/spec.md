# Feature Specification: Concise Agent Start Prompts

**Language**: English

**Status**: Accepted scope from the user's request, 2026-10-04.

## Context and Intent

### Problem

The three starting guides bury the first useful task in long instructions and fixed
demo identifiers. Readers need short, transferable prompts with a concrete cadence.

### Scope

Update every copyable prompt in demo-company, start-business and existing-business,
in English and German. Preserve the surrounding walkthrough and safety boundaries.

### Non-Goals

No runtime, scheduler, schema, permission or integration changes. No deployment or merge.

## User Scenarios & Testing

### US1: Start with any suitable records

A reader copies a prompt without replacing seeded order numbers. The agent selects
a suitable existing case or asks for missing business values rather than inventing them.

### US2: Understand recurring work

A reader sees example times, intervals and a first run now. Scheduling depends on
verified agent-system access; timezone, working days, next run and pausing are explicit.

### Edge Cases

Missing tools, records or scheduling support are reported. Pending proposals and
email drafts are not duplicated. A check time never proves a physical shipment.

## Requirements

- **FR-001**: All prompts use concise task language without fixed record identifiers,
  business names, item codes or API/schema catalogs.
- **FR-002**: Demo sales retains 09:00, 11:00, 12:00, 13:00 and 14:00 checks;
  purchasing and Finance retain 09:00, 12:00 and 15:00, Finance reporting 17:00,
  and support every 30 minutes from 09:00 to 17:00.
- **FR-003**: From-scratch and observation guides offer a first read now and a
  daily 09:00 review. Recurring prompts require verified setup, available tools
  and saved assignment/state, timezone and working days, no duplicate routines,
  next run and pause instructions, and truthful reporting of missing setup.
- **FR-004**: Preserve source-grounded reads, stated amounts, opaque record identity,
  explicit approval for business changes and separate email sending approval.
- **FR-005**: Keep both locales and surrounding instructions consistent. Existing
  business defaults to observation; bounded actions remain optional.

## Success Criteria

Each prompt is at most 160 whitespace-delimited words, carries no seeded identifiers,
and explains its immediate task. Documentation tests, formatting, build and spec
checks pass. Human diff review verifies meaning and approval boundaries.

## Assumptions and Dependencies

The user authorized the three-page rewrite and requested explicit timing. Localized
public documentation is intentionally maintained in its existing language. Reality
provides tools and records; recurrence is configured in the user's agent system.

## Requirement Traceability

FR-001–FR-005: review all six guides; existing docs-contract tests and docs build.
Timing, scheduling prerequisites and business boundaries require semantic diff review;
no runtime tests are appropriate for this documentation-only change.
