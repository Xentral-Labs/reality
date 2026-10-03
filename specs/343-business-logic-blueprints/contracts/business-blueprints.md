# Contracts: Shared Live Business Blueprint Reads

## Canonical tools

All tools have `access: read` and use the existing canonical MCP/application registry.

- `business_logic_discover`: optional bounded query and entry-kind filter; cursor/limit. Returns registered entry IDs, labels, linked canonical roots, responding release and conservative explanation availability. Does not deeply analyze every entry just to list it.
- `business_logic_explain`: registered `kind`, `key`, optional supported presentation language. Returns Blueprint, RuleNodes, safe evidence references, actual TestScenarios, optional matching TestRunEvidence and limitations.
- `business_logic_source`: registered entry kind/key and server-issued `evidence_id`. Returns approved version-matched SourceEvidence. No file path or code argument.
- `business_logic_compare`: registered entry kind/key, scenario identities and either supplied bounded facts or an authorized business-record reference. Returns CaseComparison. No operation execution or historical reconstruction.

All input schemas declare nested fields explicitly. Reject extra fields, unknown entry/scenario IDs and arbitrary paths. Discovery defaults to 25 entries, maximum 100. Comparisons allow at most 20 scenarios and 100 facts. Public discovery/explanation/source outputs contain no tenant data.

## HTTP

Public generic routes under `/api/business-logic`:

- `GET /entries` for discovery.
- `GET /entries/{kind}/{key}` for live detail.
- `GET /entries/{kind}/{key}/source/{evidence_id}` for approved source.

Existing tenant-scoped router gains equivalent private detail/source reads and `POST /business-logic/compare` as a read-only structured query. Existing authentication and tenant enforcement apply. Public routes reject company/record/fact inputs, have no database session and cannot call comparison.

Responses identify contract version, exact responding release and source digests. Unknown IDs return 404; source unavailable or inconsistent returns explicit evidence status (503 when no safe useful result exists); limits return partial with omitted nodes and reason. Public endpoints permit only configured docs origins and require deployment-level rate limits. HTTP responses do not expose raw exceptions, local absolute paths or credentials.

## Presentation and Chat

Text and diagram render from identical node/edge data. Render diagram labels as escaped text through a fixed renderer; do not execute model-generated Mermaid/HTML. Provide an accessible text alternative. Source is inert text.

Web detail shows responding release, analysis limitations, business steps/diagram, scenarios, actual assertions, optional run result and source links. Docs fetches from a configured generic live target, visibly names that target and shows loading/retry/unavailable states. Static generated vocabulary is not presented as live explanation content.

Chat retrieves the shared tool response before describing rules. Every decisive answer cites rule/evidence IDs or navigable links and identifies gaps. Historical/current context must survive paraphrasing. MCP receives structured graph/test data rather than prose only. No channel claims a discovered test passed unless matching run evidence exists.

## Compatibility

Existing catalog-code and application-reference contracts remain usable. New tool entries require resource membership and German ERP labels in `resource_catalog.yaml`; regenerate vocabulary docs using `make docs-generate`. No blueprint details are added to generated vocabulary JSON as current explanations.

## Analysis and completeness boundaries

The reference boundary is enumerated before coding in `contracts/reference-boundary.md`, listing exact registered roots, helpers, guards and exclusions with source citations. It must include exposure inputs/exclusions, the strict limit guard, hold creation/replay, readiness blockers and owner-confirmed credit release. Framework internals and generic persistence implementations may be opaque dependencies, but a decision affecting a listed business outcome may not be excluded to make completeness pass. Adding an unresolved business decision changes status to partial and fails the reference gate.

Supported initial expression shapes include constants, named/attribute/subscript values, Decimal literal construction, arithmetic, boolean conjunction/disjunction, comparisons, conditional expressions, assignments, returns, comprehensions and sums. Supported query evidence includes explicit SQLAlchemy where predicates and named joins; inferred database contents are never evaluated. Unsupported runtime dispatch, decorators, dynamic SQL and effect meanings remain opaque until resolved from source. Function names/docstrings are context, not sufficient evidence of their effects.

A rule ID is durable when an explicit identity-only source marker identifies it. Structural IDs for otherwise discovered nodes are revision-local; they must not be advertised as durable shared-rule IDs. Duplicate markers fail validation. Source expression changes alter evidence digests without replacing marker identity. Source provenance checking compiles trusted bounded module text without execution, resolves the matching qualified code object and compares normalized code/constants against the loaded callable; compilation artifacts, defaults/closures and external configuration limitations are separately reported. No caller-supplied code is compiled.

Read-only comparison initially accepts party, order and commitment references resolved through existing tenant-scoped services. Supplied facts use explicit named values with currency/unit/time context; no executable expression is accepted. Match means equal supported relevant conditions, not a branch-execution guarantee. Historical credit-hold event facts retain their recorded version/context; current implementation explanation must not be presented as proof of which historical rule version ran.

Optional test results are read only from trusted, release-bound CI evidence artifacts with recorded UTC time and outcomes; missing artifacts return unknown. They are not caller-supplied proof and no new test execution endpoint is added. Evidence packaging must include a reviewed raw-file allowlist and helper dependencies, reject symlink escapes and flag unresolved fixtures.

Public detail/source admission uses existing ingress rate-limit support where available; otherwise a narrow disposable per-process admission guard is added inside the API adapter. Default budget is 30 requests per minute per validated client address, maximum two concurrent analyses per process, response cap 2 MiB and analysis limits from the plan. Untrusted forwarded headers are not identity. Admission denial returns 429 with retry guidance. Deployment-wide limiting is an operational defense, not a business scheduler or job queue.
