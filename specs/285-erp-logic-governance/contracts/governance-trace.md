# Governance Trace Contract

The governance trace is a generated developer/reviewer contract, not a new public business API or
runtime permission surface.

## Required trace row

Each catalogued ERP command and read-access tool in the public MCP capability registry produces
exactly one governed row, except catalog self-description tools. Web-, CLI-, projection- and
exception-only reads attach as consumers unless they already have a catalogued command.

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

Runtime construction fails before readiness when an identity/owner/entry point is missing or
duplicated; a referenced runtime callable, classification or verification read does not resolve; a
mutation has zero/multiple owners; an exclusion is unexplained; a critical consumer lacks declared
evidence; or fragment composition changes identity/order. CI/docs validation additionally resolves
each executable test node against repository test files. Production startup never depends on those
files. Failure names the governed identity, rule and expected owner/boundary and emits no partial
trace.

## Compatibility contract

Existing command/tool names, labels, descriptions, schemas, access classes, confirmation policy,
outputs, events, ordering and stable facade exports remain unchanged. Generated Tool Usage adds
governance detail but invents no capability.

## Architecture exception contract

An exception identifies exactly one rule, file and function and includes rationale plus executable
evidence. Whole-directory/wildcard exceptions are invalid. An exception that no longer matches a
finding is stale and fails.
