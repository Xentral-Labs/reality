# Data Model: Transient Blueprint Evidence

No SQLAlchemy models, business tables or migrations are added.

## ReleaseEvidence

Release label, commit where available, runtime source digest, exact evidence-file digests and provenance state (`matched`, `unavailable`, `mismatch`, `development`). A commit label alone is insufficient. Development mode must still verify loaded code versus inspected source; an uncommitted running version is labeled explicitly.

## Blueprint

Existing public entry kind/key, canonical operation identity, responding release, analysis status (`complete`, `partial`, `missing`, `outdated`), semantic limitations, steps, graph edges, source evidence IDs, requirements, scenario references and related consumers. Completeness means the declared analysis boundary is represented, not formal correctness or passing tests.

## RuleNode

Rule identity, kind (input, guard, calculation, read, effect, refusal, result, opaque), structured expression, business labels, incoming/outgoing edges, exact source span and digest. Stable explicit markers contain identity only. Labels may fall back to exact identifiers; unsupported meaning cannot be guessed.

## SourceEvidence

Server-issued ID, approved relative path, qualified symbol, line span, source digest, safe source text and availability. IDs resolve only within the selected request/release evidence set. No caller path input. Truncated evidence cannot yield a complete analysis claim.

## TestScenario

Qualified executable test/node identity, parameter-set identity when resolvable, setup/helper/fixture references, known input facts, unresolved assumptions, action, assertion-derived expectations/effects, relationship (`candidate`, `assertion_linked`), rule references, test type and release identity. A test name is descriptive context, not proof of its assertions.

## TestRunEvidence

Optional existing CI evidence reference, revision/digests when available, UTC execution time, outcome (`passed`, `failed`, `skipped`, `unknown`, `unavailable`), and revision-match status. Missing results remain unknown. No new persistent run repository is required.

## CaseComparison

Authorized current-record or supplied-input origin, evaluation time, historical/current context label, selected scenario IDs, matching/different/unknown relevant facts, untested aspects and existing shortest provenance links. Decimal facts remain strings with currency/unit metadata. No approximate matching establishes outcome proof.

## Lifecycle

All blueprint graphs and case comparisons are request-time values. Each request resolves one consistent release/source set; source changes during analysis invalidate it. No saved explanation transitions become business state. Test results never alter discovered definitions or source-derived rules.

## BusinessPresentation

Ephemeral generic LLM interpretation of verified evidence, never business authority.
Mode llm/unavailable/outdated, language, model identity, source-cited BusinessOverview,
BusinessSteps retaining original rule/function/source identities and spans, contracted
RuleEdges, BusinessScenarios retaining original test identities, unresolved interpretation
notice and the count of source steps not selected for business presentation. Citation
validation is reference integrity, not semantic proof. No table, saved prose or cache.
