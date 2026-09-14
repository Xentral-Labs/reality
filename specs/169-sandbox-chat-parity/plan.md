# Implementation Plan: The Copilot works the same in Sandbox companies

**Branch**: `169-sandbox-chat-parity` | **Date**: 2026-09-11 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Add `generic_provider_call` to the reviewed practice operations, so the App copilot's
provider loop is admitted for active practice companies through the existing persisted
eligibility check; its tool access already follows the companion scope (read only inside the
lesson companion, read and propose otherwise), so nothing else changes. Make a policy refusal
in the chat reply explain itself instead of reading like an outage.

## Technical Context

**Language/Version**: Python 3.12+ · **Primary Dependencies**: unchanged · **Storage**: no
schema change · **Testing**: pytest service tests with a stubbed provider client ·
**Scale/Scope**: two code lines, one message, two tests.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The copilot creates records only through proposals and confirmed execution, unchanged. | PASS |
| Reality owns operational state | No state added; eligibility derived from persisted run, owner and membership rows. | PASS |
| Proven schema only | No schema change. | PASS |
| Tenant + shared service boundaries | The provider call passes `require_business_operation`, the same guard as every practice operation. | PASS |
| Spec/test traceability | Two new tests plus the existing companion and security tests. | PASS |
| Explainable web behavior | The refusal reply names the reason. | PASS |
| Received values not recomputed | N/A. | PASS |
| Smallest coherent design | One list entry and one except clause. | PASS |

## Design

- `services/tenant_policy.py`: `_PRACTICE_APP_OPERATIONS` gains `generic_provider_call`.
  `require_business_operation` is untouched: the companion scope still admits the call for
  lesson runs read-only; practice companies are admitted through the persisted eligibility
  query; every other playground tenant is refused.
- `agent/mcp_chat.py`: untouched. Tool access is `("read",)` inside the companion scope and
  `("read", "propose")` otherwise, so a practice company gets the business set.
- `services/core.py::send_chat_message`: catch `PlaygroundOperationDenied` before the generic
  handler and reply "The Copilot is not available for this company: <reason>".
- `docs/features/chat.md`: one section.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-002 | service | `tests/test_playground_chat.py::test_practice_company_copilot_is_admitted` | `PlaygroundOperationDenied` on the provider call |
| FR-003 | service | existing `test_companion_scope_is_read_only`, `test_provider_cannot_dispatch_mutations`, `test_generic_provider_egress_cannot_bypass_settings` | none (must stay green) |
| FR-004 | service | `tests/test_playground_chat.py::test_refused_copilot_explains_itself` | reply says "try again later" |
| DR-001–DR-003 | review | no schema diff; eligibility through `practice_company_runs` | none |

## Rollout and Rollback

Code only; deploy the API image. Rollback: revert the commit.

## Review Risks

- A practice company's copilot may now prepare every proposal a business company may; this is
  the owner's explicit intent and every proposal still needs approval.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
