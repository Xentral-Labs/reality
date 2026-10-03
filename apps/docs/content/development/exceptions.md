# Develop Exceptions

## What you will learn

Derive and explain a current condition requiring attention, then test its clearing.

## When to use it

Use an Exception when a deterministic current condition requires operational attention. Define:

- the exact condition and when it clears;
- severity and stable class identity;
- the affected Reality record and shortest trace;
- the operational role that should investigate; and
- executable evidence for derivation, tenant isolation and clearing.

Register the class and derivator in the operational Exception catalog. Do not create a manually
closed ticket or copy status onto a Document. If resolving the condition needs a mutation, use a
normal Command and its approval boundary.

## Before you start

Identify the condition, opposite case, affected record and responsible role. Inspect the existing
[catalog](../tool-usage/exceptions). Resolution uses existing Commands; a new exception does not
need a new table.

## Worked example

### Code example: commitment at risk

`packages/reality-core/src/reality/services/exceptions.py` contains `_outgoing_commitment_at_risk`
and registers it in `DERIVATION_REGISTRY`. Its entry in `config/operational_exception_catalog.yaml`
defines stable class ID, label, severity, affected record type, authority and evidence. When the
condition disappears, the derived Exception disappears too.

Add catalog entry and derivator together. Test appearance and clearing, tenant isolation, stable
cause IDs and the explanation trace. Use `operational_exceptions/test_derivation.py`,
`test_coverage.py` and `test_explanation.py` as templates.

## Step by step

1. Specify the condition and its opposite first: when is an open outgoing Commitment at risk, and
   when is it not?
2. Follow `_commitment_exceptions` and `_outgoing_commitment_at_risk`. The latter filters shared
   derivation rather than implementing independent stock rules.
3. Add a stable catalog class, tenant-scoped derivation and `DERIVATION_REGISTRY` registration. Use
   existing Reality relationships for causes and provenance.
4. Create an under-covered Commitment in a test. Assert the derived exception and explanation path.
   Restore coverage through the existing service; deriving again must clear the condition without
   manually closing anything.
5. Add the opposite case, relevant holds, missing Evidence and foreign tenant identities. Do not
   duplicate the condition in the browser. Different semantics need a separate class rather than
   expanding the existing one.
6. Add resource membership/German label and run `make docs-generate`. The class must be discoverable
   and all planned tests must pass.

## Check the result

Use the existing commitment-at-risk fixture with a suitable due date and no independent holds. Check
appearance under insufficient coverage, cause/explanation, clearing after resolution and tenant
isolation. Re-derivation must need no manual status changes.

## Try it yourself

Describe the opposite case: covered in time with no hold. Expect no at-risk exception. Add an
independent hold and inspect its registered cause rather than assuming missing coverage.

## Common mistakes

Do not store exceptions as manually closed tickets, turn derivation into a new authority or
duplicate browser rules. Clearing one cause must leave other causes explainable.

## Continue

[Add entrypoints](./application-surfaces) shows how existing reads and Commands become usable.
