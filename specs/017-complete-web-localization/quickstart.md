# Validation Quickstart: Complete Web Localization

## Prerequisites

- Node.js 22
- Frontend dependencies installed from the repository lockfile
- Spec 017 implementation and audit tests present

## 1. Run Audit Behavior Tests First

Run the focused audit regression command defined during task generation. It must prove
complete, missing, blank, invariant, discovery, and deterministic fixture behavior from
the [audit contract](contracts/localization-audit.md).

Before implementation, multi-language/discovery cases should fail. After implementation,
all focused tests must pass.

**Recorded evidence (2026-08-31)**: The previous production audit covered only a fixed
German-oriented subset and allowed gaps unless `--strict` was supplied. The new focused
suite passes 9/9 discovery, per-language, missing, blank, invariant, fallback,
preference-independence, original-content boundary, and public authentication language
continuity cases.

## 2. Run the Strict Production Audit

```bash
cd frontend
npm run i18n:audit
```

Expect separate `en`, `de`, `nl`, and `es` results, zero missing/invalid entries, and exit
status zero. Temporarily remove one required entry: the command must fail and identify
its language and source text. Restore it before continuing.

**Starting production evidence**: The first corrected full-source run discovered 781
canonical strings. German had 162 missing and 16 invalid entries; Dutch had 686 missing
and 4 invalid entries; Spanish had 686 missing and 1 invalid entry. Earlier counts of 28
were limited by the former fixed-file/German-only classifier.

**Current production evidence**: PASS — 775/775 canonical strings covered for each of
English, German, Dutch, and Spanish, with zero missing or invalid entries. The inventory
decreased from 781 to 775 after German-only conditional copy and machine path data were
correctly removed from the canonical English inventory.

## 3. Build

```bash
cd frontend
npm run build
```

Expect type checking and the production build to succeed.

**Recorded evidence (2026-08-31)**: PASS. Vite built 1,595 modules successfully. The
existing bundle-size advisory remains non-blocking and outside this feature's scope.

## 4. Verify Runtime Boundaries

Focused tests must show English fallback for unknown lookup, independence of language
from locale/timezone, unchanged Source/Evidence/document/ID/user/diagnostic samples, and
stable approved invariants.

## 5. Review the Four-Language State Matrix

At desktop and mobile widths, review each language across public/auth, one operational
flow, one configuration flow, and loading/empty/error/confirmation states. Record zero
avoidable English fallback, clipped critical actions, unusable navigation, or inaccessible
labels.

**Recorded evidence (2026-08-31)**: PASS for the owner-reviewed public landing state at
desktop width in Spanish. The review found one usability defect: the four-option
segmented language control looked atypical for a modern landing page. It was replaced
in `frontend/src/LandingPage.tsx` and `frontend/src/landing.css` with the conventional
globe/current-code popover pattern. The owner accepted the corrected result. Automated
coverage remains the evidence for the complete source inventory and all four languages;
editorial native-speaker certification remains outside this feature's claim.

## 6. Run Repository Gates

```bash
python3 scripts/check_spec_policy.py
cd frontend && npm run build && npm run i18n:audit
```

Run all remaining checks required by the pull-request template.

**Final recorded evidence (2026-08-31)**:

- Spec policy: PASS.
- Focused policy regression: PASS, 5/5.
- PostgreSQL backend suite: PASS, 137 passed and 7 skipped.
- Feature-scoped Ruff: PASS. The full dirty-worktree scan reports one unrelated import-
  formatting issue in `backend/tests/test_application_catalog.py`; it is not part of
  Spec 017 and was deliberately not folded into this feature.
- Localization contract/audit tests: PASS, 9/9.
- Strict production audit: PASS, 775/775 for every advertised language.
- Frontend production build: PASS; the existing non-blocking bundle-size advisory remains.
- Diff formatting and final Constitution/scope review: PASS.

## 7. Close the Baseline Gap Last

Only after steps 1–6 pass and owner review accepts the evidence, update
`specs/016-web-product/spec.md` and `docs/SPEC_COVERAGE_MATRIX.md` so `016/FR-013` is
Verified as-is. Do not change any unrelated gap status.

**Owner acceptance (2026-08-31)**: PASS. The product owner accepted the corrected landing
state, landing-to-auth language continuity, mobile presentation, and representative
authenticated operational/configuration states in all advertised languages, then
explicitly approved the Spec Kit remediation and baseline closure.
