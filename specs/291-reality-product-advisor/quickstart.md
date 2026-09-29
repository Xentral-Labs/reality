# Quickstart: Validate the Reality Product Advisor

## Pre-implementation analysis

Spec Kit analysis completed on 2026-09-28 after remediation. Result: 36 FR/DR requirements have task coverage, all 55 task rows follow the required format, all Constitution rows pass, and no CRITICAL or HIGH consistency finding remains.

## 1. Generate and validate governed knowledge

```bash
make docs-generate
make docs-catalog-check
```

Expected: deterministic output, valid source references and no private path, test content or internal-only evidence in the public artifact.

## 2. Run claims and buyer evaluations

```bash
cd packages/reality-core
../../.venv/bin/pytest -q \
  tests/test_product_advisor_claims.py \
  tests/test_product_advisor_service.py \
  tests/test_product_advisor_evaluation.py
```

Required regression subjects include under-delivery, automatic three-way matching, blanket orders, credit holds, legacy ERP migration, B2B, procure to pay, integrations/EDI, multi-entity operation and returns end to end.

Expected: no migration claim from item continuity, no automatic credit hold from manual review, no end-to-end claim from partial return evidence, and eligible evidence for every material statement.

## 3. Prove shared surfaces and language detection

```bash
cd packages/reality-core
../../.venv/bin/pytest -q \
  tests/test_business_journey_api.py \
  tests/test_business_journey_tools.py \
  tests/test_chat_tools.py
```

Ask equivalent questions through API, canonical read tool and authenticated Chat in representative languages. Expected: the same public conclusions and sources, with the answer in the question language. Short ambiguous follow-ups use conversation then surface fallback.

## 4. Verify presentation and full gates

```bash
make web-build
make docs-build
make spec-check
make lint
make test
```

Expected: structured claims and sources render safely, old responses remain usable, clients do not derive product status, and all required gates pass.

## Verification record — 2026-09-28

- `make spec-check`: passed.
- `make lint`: passed.
- Focused Product Advisor, security, API, tool, Chat-routing and 75-case evaluation suites: passed.
- Docs reference generation: 233 sources and 353 evidence units; deterministic/stale-output tests passed.
- `make docs-build`: passed, including 107 Docs/widget tests.
- `make web-build`: passed, including 452 Web tests and the en/de/nl/es i18n audit.
- `make test`: 4,708 passed, 10 skipped; the sole initial failure was the new `test_chat_tools.py` family missing from the coverage matrix. After adding that traceability row, `make spec-check` and all 23 `test_spec_policy.py` cases passed.

### Surface smoke matrix

| Surface | Proof | Result |
|---|---|---|
| Website widget | Public endpoint contract, safe structured source rendering, example submission and bounded history in `business-journey-widget.test.mjs` | Passed |
| Docs | Shared public endpoint, cleared composer, formatted answer, titled Journey rows and public source links in `business-journey-guide.test.mjs` | Passed |
| Authenticated Chat | Product-intent routing, canonical read-tool parity, additive platform-admin evidence and unchanged proposal confirmation tests | Passed |

The matrix uses automated surface contracts rather than a deployed production smoke. A deployed Website/Docs/API origin smoke remains a release-environment responsibility.

## General semantic clarification verification — 2026-09-28

- Spec Kit consistency analysis found no new critical, high or medium issue for the FR-013 extension; T060–T062 cover its provider contract, implementation and verification.
- Focused Ruff checks passed.
- Product Advisor service, security, evaluation and Business Journey regression suites passed: 49 tests.

## German overpayment and fallback verification — 2026-09-28

- Provider-assisted semantic catalog planning maps the German customer-overpayment question to C03 without a language-specific retrieval alias or exposing the full evidence text to the planner.
- The C03 public claim states the tested result: the invoice settles and excess cash remains customer credit for reuse or refund.
- Non-English deterministic fallback prose no longer exposes canonical English evidence text.
- Focused Advisor, security, evaluation, generator and Business Journey suites passed: 54 tests.

## Generated Capability Map verification — 2026-09-29

- The governed generator reduced 353 evidence units to 38 semantic Capability Map routes derived from Journey sections, business resources, executable commands and allowlisted public documents.
- The planning provider receives no evidence IDs or claim text. It selects at most six capability identities plus bounded canonical search phrases; the server validates those routes and ranks only their related evidence.
- Public planning has a 10-second timeout and ordinary answer attempts have a 12-second timeout. Recognized broad processes skip redundant provider planning, use their governed concern decomposition directly and receive up to 14 seconds per answer attempt. Both paths keep one validation retry below the widget's 40-second request timeout.
- Generator/staleness, Spec Policy and Ruff checks passed. Focused Advisor, evaluation, security, API, tool and Chat tests passed: 58 tests.
- Complete backend suite passed: 4,742 tests, 10 skipped.

## German ERP-evaluator conversation — 2026-09-29

- A connected ten-question local conversation covered B2B order flow, collective invoicing, customer and supplier partial delivery, invoice settlement, overpayment, returns and credits, supplier-invoice deviations, source provenance and an overall product assessment.
- The initial run exposed stale-history retrieval, an over-broad supplier-invoice synthesis, tool-vocabulary overreach and an unusable single-Journey fallback for the overall assessment.
- Retrieval now scopes self-contained turns independently, supplier-invoice evidence describes the exact proven findings, source-provenance research includes the connector contract, and a reviewed ERP-evaluation overview provides a balanced fallback with strengths and explicit limits.
- The repeated affected live questions returned a bounded supplier-invoice answer with I01/I03, a source-qualified provenance answer, and a balanced partial product assessment instead of claiming that Reality cannot handle the requested topic.
- Focused Advisor, claims, release-evaluation and generator tests passed: 53 tests. Ruff passed.
