# Governance Trace Contract

The governance trace is a generated developer/reviewer contract, not a new public business API or
runtime permission surface.

## Required trace row

Each catalogued ERP command and public ERP read produces exactly one governed row:

```text
identity and kind
business resources[] and process steps[]
authoritative owner { application name, source path, function, semantic question }
supporting services[] and public entry points[]
data basis { reads[], writes[], events[] }
verification { reads[], proves[], does-not-prove[], executable evidence[] }
critical calculation { family, grain, consumers[] } | absent
exclusion { reason } | absent
```

Rows and nested identity lists are deterministic. Tenant data, source payloads, credentials and
stack traces never appear.

## Validation contract

Construction fails before readiness when an identity/owner/entry point is missing or duplicated; a
referenced callable, classification, verification read or test does not resolve; a mutation has
zero/multiple owners; an exclusion is unexplained; a critical consumer lacks shared evidence; or
fragment composition changes identity/order. Failure names the governed identity, rule and expected
owner/boundary and emits no partial trace.

## Compatibility contract

Existing command/tool names, labels, descriptions, schemas, access classes, confirmation policy,
outputs, events, ordering and stable facade exports remain unchanged. Generated Tool Usage adds
governance detail but invents no capability.

## Architecture exception contract

An exception identifies exactly one rule, file and function and includes rationale plus executable
evidence. Whole-directory/wildcard exceptions are invalid. An exception that no longer matches a
finding is stale and fails.
