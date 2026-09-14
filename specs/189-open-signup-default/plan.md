# Implementation Plan: Open Signup by Default

**Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)

## Summary and Technical Context

Use one small shared application policy for admission configuration and atomic
counter claims. Python 3.12+, SQLAlchemy 2, PostgreSQL and existing FastAPI/React
adapters. No new dependencies or schema. No domain, business tool or operational
record changes are needed.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Only platform account metadata; no source or business records changed | PASS |
| Reality owns operational state | No document status or operational derivation changed | PASS |
| Proven schema only | Existing admission counter and application reused | PASS |
| Tenant + shared service boundaries | Shared services/access_admission.py; existing membership guards retained | PASS |
| Spec/test traceability | Every FR/DR mapped below; tests first | PASS |
| Explainable web behavior | Unlimited is explicitly represented, never shown as zero capacity | PASS |
| Received values not recomputed | No received business values involved | PASS |
| Smallest coherent design | Optional limit, not a new setting or admission subsystem | PASS |

## Repository Structure and Layer Changes

- `packages/reality-core/src/reality/services/access_admission.py`: parse optional limit and claim an atomic counter increment; no commit.
- `packages/reality-core/src/reality/web/auth.py`: reuse shared policy, preserve verification transaction and invitation handling.
- `packages/reality-core/src/reality/services/platform.py`: report the same optional limit.
- `apps/web/src/Auth.tsx`, `api.ts`, `localization.tsx`: nullable capacity, neutral signup explanation, explicit unlimited administrator display.
- `provider-site/src/PlatformPage.tsx`, `localization.tsx`, `vite.config.ts`, `Dockerfile`: default open admission and matching package copy.
- `.env.example`, `compose.yml`, `compose.dev.yml`, `installer/compose.yml`, `installer/install.sh`, `helm/reality/values.yaml`: blank generic defaults. Keep explicit testing/demo restrictions.
- `docs/WEB_SPEC.md`, `docs/RAILWAY_DEMO.md`, `apps/docs/content/{reference/environment,operations/installation}.md` and existing localized counterparts: document mode semantics and upgrade behavior.

## Design

Missing/blank returns None, serialized as null. Zero or invalid/negative values
return zero; positive values retain their limit. The shared claim updates the
existing automatic counter atomically with a conditional used_slots < limit only
for finite mode. Unlimited claims still increment for later finite-mode accounting.
There is no read-time creation, business mutation, automatic company creation or
retroactive account status update. Existing schema migrations initialize the counter.
The HTTP audit/application review note must describe automatic admission without
asserting a finite early-access limit. Existing verification challenge consumption
and slot increment remain in one transaction.

## Test Strategy and Traceability

| Requirement | Planned proof | Expected initial failure |
|---|---|---|
| FR-001 | test_user_access.py default/blank verification story | Account stays pending |
| FR-002 | test_access_admission.py value matrix, transition and counter tests; existing finite HTTP story | Missing mode absent |
| FR-003 | Unlimited-to-finite counter transition and verification replay | Unlimited claims refused |
| FR-004 | Platform overview optional limit; site rendering/contract tests; installer/default assertions; frontend gates | Wrong defaults/copy |
| FR-005 | Existing access, invitations and company tests, full PostgreSQL suite | Only tests implicitly relying on old default require explicit zero |
| DR-001 | Shared policy assertions and final schema/diff review | Duplicated parsing removed |

## Rollout and Rollback

No migration. Deploy API and web together for nullable capacity, rebuild Site for
its build-time value. Explicit existing limits are retained; remove or blank them
only when choosing open access. Setting zero restores manual review for subsequent
verifications. Existing account statuses are never mass-updated. The hosted Railway
prepared-account profile remains explicitly restricted. No remote rollout in scope.

## Review Risks

Default changes must not be hidden by Compose/installer defaults. Invalid input
must not be interpreted as open. Unlimited admissions must count toward later caps.
Public package configuration is build-time; it must match API configuration.

## Complexity Tracking

No Constitution exception. Product scope authorized by the owner's request.
