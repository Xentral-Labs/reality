# Live business logic and test evidence

Spec 343 exposes registered commands, agent tools, Web actions, views and projections
through one read-only service, `reality.services.business_blueprints`. Web, public
Tool Usage, Chat and MCP delegate to it. No explanation is persisted as business
authority; no schema, migration or background job is added.

`business_logic_discover` returns the complete catalog denominator, including entries
whose source is missing. `business_logic_explain` reads the actual registered handlers
and approved dependencies on demand. It compares trusted compiled source with loaded
Python code, records file digests and rechecks each captured source before returning.
A changed checkout cannot stand in for an unchanged running process. Raw positional/keyword defaults and safe imported scalar defaults are also checked.
Unsupported default factories are not executed and remain explicit source limitations.
Default/global mismatches are outdated evidence, rejected by comparison. A reload or new
release is necessary when execution code changes. Source-authored business descriptions are English; interface labels may be localized. Technical identifiers and source retain their exact language.

Steps and diagrams use the same graph. Exact comparisons, filters, arithmetic and
refusals come from source. Inert `reality-rule` comments carry stable identity only.
Unmarked nodes have revision-local identities. Unsupported statements and bounded
traversal yield explicit limitations; freshness does not prove semantic completeness.

The release packages only reviewed raw synthetic tests and helpers with a digest
manifest. It does not generate final descriptions. Test setup, actions and assertions
are read without importing or executing test modules. Candidate relationships do not
prove assertions or branches. Branch gaps remain visible. A trusted release manifest
may supply run records containing outcome, commit, timestamp and evidence location;
without these, execution remains unknown. Current-run matching also requires the actual
test-file and business-source digests (`test_digest`, `source_digest`); a commit label
alone cannot prove unchanged mutable evidence. An older run never proves the current code.

## Boundaries

Public reads are limited to `/api/business-logic/entries` and registered descendants.
They accept no company IDs, facts, credentials, paths, module names or arbitrary URLs.
They have no database session and cannot run business operations. Direct-client rate
limits, concurrent-analysis limits, traversal limits and response limits apply.
Responses use `Cache-Control: no-store`. Source IDs are selected from server evidence.
Deployment CORS uses the existing fixed `DOCS_URL` origin configuration. Tool Usage
reads the build-configured `BUSINESS_LOGIC_API_URL` (fallback `API_URL`) with omitted
credentials; its target and responding release are visible. Static catalog vocabulary
continues to be generated with `make docs-generate`.

Private `business_logic_compare` is a read tool. It accepts supplied facts or one
party/order/commitment reference and enforces the existing company boundary. It reads
current exposure/readiness through application services. Matching conditions preserve
Decimal values, currency and units; missing context is unknown. Multiple conflicting
test facts cannot be collapsed into a single answer. Similarity never proves an
operation's outcome. Historical hold events retain their recorded facts; when their
code version is unavailable, historical rule provenance remains unknown. Nothing is
executed, released or saved by comparison.

## Release and rollback

Build API and MCP images with the same `REALITY_COMMIT`; both include raw evidence
under `/opt/blueprint-evidence` and set `REALITY_BLUEPRINT_EVIDENCE`. The manifest commit
must match the responding process. Missing/mixed evidence is shown as unavailable.
Remove the live adapters to roll back the feature; the operational services, database
and generated vocabulary require no data rollback. The source graph is an inspection
aid, not a substitute for execution, human review or a complete formal verification.

## Source-authored business descriptions

The shared service now reads BUSINESS PURPOSE / BUSINESS RULE descriptions from
verified function docstrings and BUSINESS TEST / GIVEN / WHEN / THEN descriptions
from the verified executable test source. It does not call Anthropic or another
provider, even when `interpret=true` or provider credentials are configured. The
compatibility flag includes descriptions; `interpret=false` remains source-only.
The `brief` flag remains accepted and does not discard reviewed authored rules.

BusinessPresentation uses mode `authored` with English commentary and original
rule/source citations. Missing or invalid descriptions are listed in `annotation_gaps`;
source and executable tests remain available. Displayed THEN descriptions are authored
expectations, not measured assertion mappings or passing execution records. Reading
never executes a test. The legacy inference helper remains isolated from public
explanation routing and its unit tests; no fallback invokes it.

See [the authoring contract](../development/business-source-descriptions.md) and run
`make business-annotations-check`. The initial authored reference comprises credit
exposure functions and six direct credit exposure tests. The coverage audit reports
all remaining roots and approved tests; it generates no narrative artifacts.

## Interactive reading latency and layout

Web and Docs initially request `brief=true`: at most six source-cited rules, no generated overview or test summaries, with explicit partial-reading notice. Source and discovered raw tests remain current. The detailed-read button requests the original full interpretation. Existing MCP/full service defaults remain unchanged. Brief provider output has six nullable rule slots; server maps these back into the shared validated steps. No stored answer or company-data transfer is introduced.

Waiting feedback uses an accessible spinner, elapsed duration, reduced-motion support and honest live-work notice. The primary view uses numbered multiline steps; the separate business flow view is superseded by this reading layout. Numbering is presentation identity, not a fabricated continuous sequence. The original technical graph remains in technical evidence.

## Chat discovery and context boundaries

A filtered discovery that finds no entries returns up to ten matching identities from other kinds, with a total count and recovery hint. Filtered entries, counts and pagination keep their meaning. An empty lookup never proves absence of tests. Chat resolves registry kind independently of read/write access and retrieves current explanation before rule/test claims.

Both Chat provider loops project the canonical explain response into at most 120000 UTF-8 bytes, retaining source identities, rule conditions, interpreted business evidence and actual test assertions/run states with total/shown counts. Expanded technical graph paths and raw source/helper bodies are omitted from initial model context. The full MCP response is unchanged; original source remains available through business_logic_source. Omission is disclosed and is never represented as missing tests or a passing run.

Successful Chat blueprint reads also append a localized evidence footer independently of model prose: actual discovered test count (not a claim of passing execution) and up to three source links carrying canonical returned source IDs. This gives the user a stable inspection path even when the model omits citations. It is a request-local projection of live evidence, not stored explanatory prose.

## Focused source and reading hierarchy

Steps, test cases and technical evidence have separate keyboard-accessible tabs. Numbered step cards preserve live multiline business wording. The generic provider instruction uses translated IF/THEN/ELSE labels for supported conditional rules, without inventing absent alternatives or combining independently cited rules. Selecting a test displays one case, keeps execution status separate and offers detailed interpretation when the brief response contains only raw evidence.

Each source disclosure shows original line numbers and highlights ranges from the step's exact rule/source/function identity, with three surrounding context lines. Large compound control nodes highlight their header rather than their entire subtree. Unmatched helper sources remain unmarked. The full-function toggle reuses the already loaded response and scrolls inside the code pane to the first cited line. Local source and tab navigation makes no extra API or model calls. Source highlighting identifies a cited location; it does not certify the interpretation's correctness.

## ERP explorer navigation

Business-object labels follow the current locale's resource catalog labels in cards, headings and return context; technical identifiers stay exact. The navigation prioritizes order, invoice, item, partner, payment and warehouse location, retaining all remaining and future catalog objects in their original relative order. The unselected details panel offers existing read-only catalog entries for order explanation, credit exposure and stock. Missing entries are omitted. These shortcuts open documentation only; they do not execute the tool or trigger live inference. The explorer introduction is one sentence.
