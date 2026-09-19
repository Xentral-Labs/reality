# Analytics documentation review — 2026-09-19

Spec impact: none. This documentation-only change explains existing behavior from
specs 224 and 228–232, corrects obsolete navigation and order-value terminology,
and adds executable example text. No product behavior, tool schema or catalog changes.

## Review outcome

The previous public guide described the retired step-stack editor, called order
value revenue, and promised that the UI could never construct a refused question.
The English and German guides now describe Analysis / Explore data, Result /
Connections / Cypher, the shared declaration/compiler architecture and the distinction
between Fact records and the broader operational graph. Ordinary SQL execution is
separated from bounded service-backed stock and finance reads. No separate persistent
analytics copy is claimed; external source ingestion remains necessary.

Three usable parameterized paths and one intentionally refused fan-out example are
included in both languages. Runtime budgets and a reproducible load-test plan are
separated from correctness tests; there is no fabricated latency or scale claim.
Existing screenshot work in the private marketing-site repository is unaffected.

## Evidence

- Existing declaration, traversal, surfaces and isolation PostgreSQL suites:
  **132 passed in 24.59s**, using an isolated temporary database. Suite duration is
  test/fixture overhead plus execution, not an Analytics response-time benchmark.
- Extracted all four Cypher blocks from each language and passed them through the
  actual parser and traversal planner: three accepted, final example refused with
  `fan_out`, in both languages. This validates model/syntax, not production volumes.
- Public documentation Node suite: **68 passed**.
- VitePress production build: passed, including page rendering/link checks.
- Changed Markdown formatted with repository Prettier; diff whitespace check passed.
- No Analytics-specific large-volume/concurrent benchmark was run. The public guide
  identifies the missing measurement and describes datasets, concurrency and metrics
  required for a meaningful future run. Existing deferred engine work stays deferred.

Local review: http://localhost:5188/analytics/ and
http://localhost:5188/de/analytics/. Not published.

Owner refinement: removed the automated-test explanation and pytest command from
both public language versions. Verification evidence remains in this internal
record; execution limits and the load-test plan remain in the guide. Spec impact:
none, documentation presentation only.

Owner refinement: simplify both sidebar labels to Analytics and expand the existing
guide with template examples, the chat draft/proposal flow and Data Explorer discovery.
Templates remain unsaved editable questions; chat does not send automatically. Spec
impact: none, documentation navigation wording and explanation of existing behavior.
