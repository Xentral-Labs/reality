# Implementation Plan: Service refusals speak the user's language

**Branch**: `286-localized-service-errors` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

A refusal gains an optional stable `code` and named `values`. When a code is given, the
English sentence is rendered from one catalog (`config/service_refusals.json`), so the
sentence clients see today stays word for word the same. The web API, the chat stream, the
chat tool result, MCP and failed proposal receipts carry `code`, `template` and `values`
next to the unchanged English `detail`. The web translates the template in one place
(`api.ts` `request()` and the chat stream), so every form shows the refusal in the account
language without touching each card.

A static gate lands first. It lists every refusal in the in-scope modules that still lacks a
code in a ratchet file. The area tasks then convert module group by module group and shrink
the ratchet. At the end only entries marked `later` (out-of-scope areas) remain.

## Inventory (2026-09-27, `scripts/refusal_reach.py`)

This static reachability starts from the in-scope forms' routes and the handlers of their 32
tools (the 25 delivery tools, the 6 master-data tools and `cost.change`). The dispatchers are
pruned to those tools.

| Scope | Raise sites | Distinct sentences | f-strings | `str(error)` re-raises |
|---|---|---|---|---|
| Reachable from the in-scope forms | **584** | 428 | 46 | 10 |
| All sites in the 39 modules holding them | 845 | — | — | — |
| Chat send path (`core.send_chat_message`, US3) | 31 | 25 | 2 | 0 |
| All of `services/` and `tools/` | 1,509 | 1,095 | 113 | 34 |

- **Chat send path:** 31 sites in 9 modules (`tenant_policy` 11, `core` 6,
  `supply_assignments` 4, `free_playground`, `security.secrets`, `agent.settings`,
  `delivery_reads`, `exceptions`, `business_locks`). Some overlap with the forms, so the total
  is about 610 sites.
- **Expected catalog:** about 500 codes (71 sentences repeat across sites, and some
  repeats mean different things).
- **Largest modules:** `core` 213, `costing` 48, `inventory_costing` 44,
  `reference_workspace` 28, `item_imports` 23, `tools.application` 21, `supply_assignments`
  20, `delivery_actions` 20, `tenant_policy` 19, `credit_actions` 17, `shipment_actions` 17.
- **Tests:** 812 `pytest.raises(match=)`; 375 of them match a reachable sentence. They stay
  valid because the English sentences do not change.
- **Limits:** the analysis does not resolve `obj.method()` calls, `getattr` or registries
  other than `TOOLS`, and it folds nested functions into their parent. Only 2 refusal raises
  in the package sit inside methods. The ratchet makes the result explicit and reviewable
  instead of recomputing reachability in CI.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript (React/Vite)
**Storage**: PostgreSQL, no migration. Failed proposal receipts keep their JSON `output`
column and gain keys inside it.
**Testing**:
- pytest: catalog, render, transport and the gate, with positive controls;
- `node --test`: the localization contract and the web contract;
- a Playwright fixture browser test in de/nl/es;
- a live check on an isolated stack.

**Constraints**:
- the English sentence stays word for word;
- values are JSON strings;
- no Accept-Language, and the server stays language-neutral;
- no new dependency.

**Scale/Scope**: about 610 raise sites and about 500 codes, each translated into 3 languages,
across 39 modules, plus 6 transport touchpoints and 2 web entry points.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Unaffected. Refusals record nothing, and no business record changes. | PASS |
| Reality owns operational state | No document or status fields. | PASS |
| Proven schema only | No table or column. The catalog is a versioned config file, like `resolution_guidance.json`. | PASS |
| Tenant + shared service boundaries | Codes are added at the existing raise sites in the shared services. Adapters only serialize `code`, `template` and `values`, and no adapter decides a refusal. Values carry only what the English sentence already carried (DR-004). | PASS |
| Spec/test traceability | Every FR and DR maps to tasks; the gate enforces FR-006 and FR-007. | PASS |
| Explainable web behavior | The translated sentence has the same meaning and values as the English one. The English sentence stays available for chat, MCP and receipts. | PASS |
| Received values not recomputed | Unaffected. | PASS |
| Smallest coherent design | Rejected: (1) English sentences as dictionary keys, which break on rewording and cannot handle values (the owner decided against it); (2) server-side translation, which would mix languages in chat, MCP and receipts; (3) a reachability computation inside CI, which over-approximates through the tool dispatchers and changes with unrelated code; (4) editing all 16 cards, which one parse point in `api.ts` replaces. | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/config/service_refusals.json                  # NEW catalog: code → English template, value kinds; terms
packages/reality-core/config/refusal_ratchet.json                   # NEW uncoded sites still allowed in in-scope modules (scope: "286" | "later")
packages/reality-core/src/reality/domain/refusals.py                # NEW catalog load, render(code, values), value serialization; RefusalMixin for domain ValueErrors
packages/reality-core/src/reality/services/core.py                  # RealityError(message=None, *, code=None, values=None); codes at raise sites
packages/reality-core/src/reality/services/*.py, tools/application.py, domain/*.py  # codes at the ~584 in-scope raise sites
packages/reality-core/src/reality/web/api.py                        # api_error → RefusalHTTPException; 422 "Check the action fields." coded
packages/reality-core/src/reality/web/app.py                        # handler rendering {detail, code, template, values}
packages/reality-core/src/reality/web/chat_stream.py                # error event carries code, template, values
packages/reality-core/src/reality/agent/mcp_chat.py                 # tool error carries values (code already)
packages/reality-core/src/reality/mcp/server.py                     # error code: refusal code, else class code; values
packages/reality-core/src/reality/tools/application.py              # failed receipt output.error: refusal code, else class code; values
packages/reality-core/tests/test_service_refusals.py                # NEW catalog, render, RealityError, transport tests
packages/reality-core/tests/test_refusal_gate.py                    # NEW static gate with positive controls
scripts/refusal_reach.py                                             # NEW planning tool (advisory, not in CI) that produced the inventory
apps/web/src/refusals.ts                                             # NEW localizeRefusal(template, values): t(template) + kind formatting
apps/web/src/api.ts                                                  # APIError(code, template, values); request() localizes the message
apps/web/src/unified/chatStream.ts, ChatPage.tsx                    # stream error localized; code instead of text comparison
apps/web/src/localization.tsx                                        # de/nl/es for every template and term
apps/web/scripts/service-refusals-localization.test.mjs              # NEW every template/term has de/nl/es with all placeholders
apps/web/scripts/service-refusals-contract.test.mjs                  # NEW parse, interpolation, formatting, fallback, no text comparison
apps/web/scripts/service-refusals-browser.mjs                        # NEW forms and chat show translated refusals (de/nl/es, 390/1440)
docs/features/service-refusals.md                                    # NEW durable contract
```

## Design

### Catalog (`config/service_refusals.json`)

```json
{
  "version": 1,
  "refusals": {
    "invoice_net_tax_mismatch": {
      "message": "Net plus tax differs from the invoice gross."
    },
    "order_line_amount_missing": {
      "message": "Line {index} requires a stated amount; it is never calculated.",
      "values": {"index": "number"}
    },
    "field_not_negative": {
      "message": "{field} cannot be negative.",
      "values": {"field": "term"}
    }
  },
  "terms": ["Lead time days", "Credit limit", "Credit amount"]
}
```

- **Codes:** snake_case. One code per meaning (DR-001), shared by sites that mean the same
  thing, such as "Company not found.".
- **Value kinds:** `text`, `term`, `number`, `amount`, `quantity` and `date`. A `term` value
  must be listed in `terms`, which are the product words that are translated themselves
  (field names).
- **Placeholders:** the placeholders in `message` equal the declared value names.

### Raising (`RealityError`, `domain/refusals.py`)

- `RealityError.__init__(self, message=None, *, code=None, values=None)`. With a code, the
  message is `render(code, values)`. Passing both a message and a code is a `TypeError`.
  Without a code, behaviour is exactly as today.
- `code` and `values` become attributes. The class attribute `code = None` keeps the
  existing subclasses working: `PlaygroundOperationDenied`, `FindingCleared` and `DraftChanged`
  set a class code, and `AnalyticsError` sets `self.code`. Their instance codes take precedence
  where the conversion assigns one.
- **`render`** fills the template with values that are already strings; `values_json` turns
  `Decimal`, `int`, `date` and `datetime` into exact strings, with no rounding. An unknown code,
  missing or extra values, or a `term` value missing from `terms` raises `ValueError` under
  test (`REALITY_STRICT_REFUSALS=1`, set in the test configuration). In production they fall
  back to the filled English sentence.
- **Domain `ValueError` refusals** use `RefusalMixin` for the same code and values: the
  shipment compatibility error and the costing refusals behind the 10 `str(error)` re-raise
  sites. The service re-raise passes `code=error.code, values=error.values` through.
  Pydantic `ValidationError` re-raises get `request_fields_invalid` with the field names as a
  `text` value.
- **Messages taken from data** (`core.py:5450`, `:8769`) get a code, and the data sentence
  becomes a `text` value.

### Transport

- **Web API:**
  - `api_error(error)` returns a `RefusalHTTPException` (a subclass of `HTTPException`) that
    carries `code`, `template` and `values`.
  - The handler in `app.py` renders `{"detail": <English>, "code", "template", "values"}`,
    where `values` is `{name: {"value", "kind"}}`.
  - `detail` stays a string, so the existing `json()["detail"]` assertions and all clients
    remain valid. Uncoded refusals keep exactly `{"detail": ...}`.
  - Statuses stay as they are (400/404/409). The TypeError 422 ("Check the action fields.")
    becomes the coded `action_fields_invalid`.
  - The `draft_changed` 409 keeps its object `detail` and gains the top-level fields.
  - The `PlaygroundOperationDenied` 403 handler (`web/app.py:79`) renders the same fields; its
    16 reachable sites get instance codes (the web never branches on the shared class code).
  - The direct `HTTPException(404, "ChatSession not found.")` in `web/api.py` becomes
    `raise NotFound(code="chat_session_not_found")` through `api_error`.
- **Chat stream:** `{"type": "error", "message", "code", "template", "values"}`.
- **Chat tool result:** `{"error", "code", "values"}`. The model reads English; the outcome code
  in the interactions log becomes the refusal code.
- **MCP:** `ToolError` JSON gets `code` (the refusal code, else the class code as today) and
  `values`; `message` is unchanged.
- **Failed proposal receipt:** `output.error.code` follows the same rule, and `values` is added.
  No web consumer reads this today; the change is recorded in the contract doc.

### Web

- `refusals.ts` exports `localizeRefusal({detail, template, values})`. It returns `t(template)`
  with each `{name}` replaced by its value, formatted by kind:
  - `term`: `t(value)`;
  - `number` and `quantity`: `formatQuantity` (exact);
  - `amount`: `formatExactDecimal` (the language's separators, with no currency and no rounding);
  - `date`: `formatDate`;
  - `text`: as given.

  If a placeholder is missing from the translation, or the template is absent, it returns
  `detail` (the English sentence).
- `api.ts`: `APIError` gains `template` and `values`, and `request()` sets `message` to
  `localizeRefusal(...)`. The English sentence stays available as `error.detail`. Every card
  already shows `error.message`, so all forms are covered at one point.
- `chatStream.ts`: the error event throws an `APIError`-like error with the localized message.
  `ChatPage.tsx` compares `code === "chat_session_not_found"` instead of the text.
- `localization.tsx`: new `Object.assign` blocks per area for de/nl/es (du/je/tú; protected
  terms untranslated).

### Gate (`tests/test_refusal_gate.py`)

A pure AST pass over the in-scope modules (the 39 from the forms plus the chat send path's
modules not already among them), whose list lives in `refusal_ratchet.json`
beside the entries. It checks four things:

1. Every `raise <refusal class>(...)` has a literal `code=` keyword, or matches a ratchet entry
   keyed by (path, function, sentence source). Otherwise it fails and names the file and line.
2. Every ratchet entry still matches a site. A stale entry fails, so the ratchet only shrinks.
3. Every literal `code=` anywhere in `src/reality` exists in the catalog, and every catalog
   entry is raised somewhere (no orphans).
4. The catalog is well formed: placeholders equal the declared values, the kinds are known,
   and every `term` is listed.

**Positive controls:** synthetic sources with an uncoded raise, a coded raise, a stale ratchet
entry and an unknown code each give the expected result. This keeps the negatives from passing
for the wrong reason.

**Final state:** no ratchet entry has `scope: "286"`. About 261 `later` entries remain for the
out-of-scope areas.

### Data and migration impact

None. Rollback is revert: clients ignore the extra keys, and English is unchanged.

### Failure, security, and tenant behavior

- A render failure never hides a refusal: production falls back to English.
- Values only repeat what the sentence showed; there is no new data and no cross-tenant
  identifier.
- The status codes and the conflict and reload behaviour are unchanged.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_service_refusals.py::test_coded_refusal_carries_code_and_values` | TypeError (no `code` keyword) |
| FR-002 | service | `::test_english_sentence_is_the_filled_template` and one test per converted area comparing rendered English with the former sentence | catalog missing |
| FR-003 | API | `::test_api_sends_code_template_values_per_status` (400/404/409/422); `::test_uncoded_refusal_shape_is_unchanged` | keys absent |
| FR-004 | service/API | `::test_chat_stream_error_carries_code`; `::test_failed_receipt_carries_refusal_code` | keys absent |
| FR-005 | node + browser | `service-refusals-contract.test.mjs` (interpolation, kinds, fallback); `service-refusals-browser.mjs` de/nl/es | English shown |
| FR-006 | gate + node | `test_refusal_gate.py` (no `286` ratchet entries); `service-refusals-localization.test.mjs` | ratchet not empty; translations missing |
| FR-007 | gate | positive and negative controls on synthetic sources | — |
| FR-008 | service | `::test_chat_tool_result_keeps_english_and_adds_values`; `::test_mcp_error_uses_refusal_code` | class code only |
| FR-009 | node | the contract has no `message ===` comparison with refusal text in `apps/web/src` | ChatPage compares text |
| DR-001 | gate | catalog keys unique (JSON object); no code reused for a changed template (reviewed in PR) | — |
| DR-002 | suites | the existing 375 matching tests and the whole suite stay green | — |
| DR-003 | review | no migration in the diff | — |
| DR-004 | service | `::test_values_are_only_template_placeholders` | — |
| SC-001 | live | the German invoice form shows the German contradiction refusal on an isolated stack | English |

## Rollout and Rollback

The change is additive and each area task is independently mergeable in principle. This
feature ships as one PR with one commit per area, so reviewers can follow the ratchet shrinking.
Rollback is revert.

## Analysis (2026-09-27)

`$speckit-analyze` over spec, plan and tasks. There are no CRITICAL findings. Every finding is
resolved in the artifacts:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| A1 | HIGH | US3 promises translated chat stream errors, but the chat send path was not in the inventory, so its refusals would have stayed uncoded and English. The web text comparison "ChatSession not found." comes from a direct `HTTPException` in `web/api.py`, not from a service. | Chat send path measured (31 sites) and added to the scope, the gate modules and task T019a; the `HTTPException` becomes a coded `NotFound` (T009). |
| A2 | MEDIUM | The 403 `PlaygroundOperationDenied` handler and status were missing from FR-003 and the transport. | 403 added to FR-003; the handler is part of T009, with a test in T008. |
| A3 | MEDIUM | SC-002 said out-of-scope surfaces behave exactly as before, but a coded refusal is translated wherever the web shows it. | SC-002 reworded: English and behaviour are unchanged for MCP, the chat model and receipts, and uncoded refusals are unchanged everywhere. |
| A4 | LOW | `output.error.code` of failed proposal receipts changes from the class code to the refusal code. | No consumer in `src/` or `apps/web` (grep, 2026-09-27); recorded in the contract doc (T905). |
| A5 | LOW | The strict render mode needs a test-environment switch. | `REALITY_STRICT_REFUSALS=1` is set in `core/tests/conftest.py` (T005). |
| A6 | LOW | The static gate cannot see refusals reached only through `obj.method()` or `getattr`, so FR-006 holds for what the gate sees. | Only 2 refusal raises sit in methods; the ratchet's `scope` marks are reviewed in the PR, and the browser and live checks cover the main forms. |
| A7 | LOW | Some cards already call `t(error.message)`; with the message localized in `request()` this translates twice. | Harmless: a translated sentence is not a dictionary key. The calls stay, because the same cards also translate their own client-side messages through them. |

## Review Risks

- **Wording drift.** A converted site must render exactly the former sentence. The existing
  matching tests catch most drift; each area task also runs a before/after comparison of the
  rendered English (`refusal_reach.py --json` sentences against the rendered catalog).
- **Code granularity.** Too coarse gives wrong translations; too fine bloats the catalog. The
  rule is one code per meaning, with shared sentences sharing a code only when the meaning is
  the same.
- **Translation volume** of about 1,500 strings. Each area is reviewed in German by the owner
  on a sample; the contract enforces completeness and placeholders, not quality.
- **Chat telemetry.** Interaction outcome codes become finer, and dashboards that group by
  `invalid_operation` would change. None exist in the repo; this is noted in the PR.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
