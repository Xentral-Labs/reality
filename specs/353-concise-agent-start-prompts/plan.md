# Implementation Plan

Replace fenced prompts in the six localized starting guides, then adjust adjacent
instructions where their fixed sample inputs or scheduling claims conflict.

## Constitution Check

PASS: documentation only; no source/evidence changes, schema, tenancy, services,
business rules, dependencies or scheduling infrastructure. Reads remain grounded;
business changes need confirmation. German is intentional localized public content.

## Verification

Run existing docs tests, format check, docs build and spec-check. Inspect all prompts
for identifier removal, length, cadence and confirmation boundaries. No new tests
that merely mirror prose. Rollback is reverting the documentation commit.

## Pre-implementation Analysis

All five requirements map to six documentation files and semantic review. No unresolved
clarification or critical consistency finding. User scope includes the daily cadence.
