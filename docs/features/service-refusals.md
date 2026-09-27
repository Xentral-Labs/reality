# Feature: Service refusals

Spec: [`specs/286-localized-service-errors/`](../../specs/286-localized-service-errors/spec.md).

## Contract

When a service refuses a request, it raises `InvalidOperation`, `NotFound` or `Conflict`, or one
of their subclasses (`services/core.py`). A refusal may carry a stable **code** and named
**values**:

```python
raise InvalidOperation(code="manual_line_amount_required", values={"index": index})
```

With a code, the English sentence is rendered from the catalog
`packages/reality-core/config/service_refusals.json`, which holds each code's English template,
its placeholders and the kind of each value (`text`, `term`, `number`, `amount`, `quantity`,
`date`). The code identifies the meaning of a refusal. Its wording may change, but a code is
never reused for another meaning. A refusal without a code behaves exactly as before.

Domain rules raise `DomainRefusal` or one of its subclasses (`CostingRefusal`,
`ShipmentCompatibilityError`), which are `ValueError`s with the same code and values. A service
re-raises one with `InvalidOperation.from_refusal(error)`, which keeps the code.

## What each client receives

| Surface | Payload |
|---|---|
| Web API (`api_error`, 400/404/409, and the 403 Playground denial) | `{"detail": <English>, "code", "template", "values": {name: {"value", "kind"}}}`; an uncoded refusal keeps exactly `{"detail": ...}` |
| Chat stream | `{"type": "error", "message": <English>, "code", "template", "values"}` |
| Chat tool result (the model) | `{"error": <English>, "code", "values"}`; the model reads English and answers in the conversation language |
| MCP | `ToolError` JSON `{"code", "message": <English>, "tool", "values"}`; `code` is the refusal code where one exists, otherwise the class code (`not_found`, `invalid_operation`, ...) |
| Failed proposal receipt | `output.error` = `{"code", "type", "message", "values"}` with the same rule for `code` |

## The web

`apps/web/src/api.ts` builds every `APIError` through `refusalError()` (`apps/web/src/apiError.ts`),
so `error.message` is already the refusal in the account language. Every form shows it without
extra code. The English sentence stays on `error.detail`. `refusals.ts` interpolates the
translated template:
- `term` values are translated too;
- numbers, amounts and quantities are formatted exactly for the language;
- dates use the date format.

When the code is unknown, a value is missing or a translation dropped a placeholder, the English
sentence is shown. Web code never compares refusal text; it branches on `code`.

Translations live in `apps/web/src/localization.tsx`, keyed by the English template.
`service-refusals-localization.test.mjs` requires German, Dutch and Spanish for every template
and term, with all placeholders and protected terms kept.

## Adding a refusal

1. Add the code to `service_refusals.json` (English template, values and their kinds; new
   `term` words go into `terms`).
2. Raise it with `code=` (a string literal) and `values=`.
3. Add the de/nl/es translations to `localization.tsx`.

## The gate and the ratchet

`tests/test_refusal_gate.py` is a static AST pass over the modules listed in
`config/refusal_ratchet.json`. It fails in four cases:
1. a raise in one of those modules has neither a code nor a ratchet entry;
2. a ratchet entry no longer matches a site, so it must be removed;
3. a code is missing from the catalog;
4. a catalog entry is never raised.

The ratchet lists the refusals not coded yet. All remaining entries are marked `later`: they
belong to areas outside spec 286, or to request field validation (Pydantic re-raises), which
stays English like FastAPI's 422. A later area spec codes its entries and removes them; the
ratchet only shrinks.

`scripts/refusal_reach.py` is the advisory planning tool that measures which refusals a set
of entry points can reach. It is not part of CI.

Out of scope for now: analytics (its own codes), authentication and invitations, integrations,
Playground, storyline import, background jobs and the CLI. These keep their English sentences
until their area moves over.
