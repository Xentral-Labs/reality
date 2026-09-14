# Research: Existing-System Specification Baseline

## Decision 1: Use bounded business capabilities

**Decision**: Produce thirteen primary baseline specs. Treat documents, tables,
endpoints, pages, and tests as evidence mapped to them.

**Rationale**: Artifact-level specs would duplicate invariants; one system-wide spec
would be unreviewable. The approved groups follow business ownership and stories.

**Alternatives considered**: One repository spec; one spec per existing feature file;
one spec per table/page/endpoint. All were rejected as too broad or fragmented.

## Decision 2: Classify evidence per requirement

**Decision**: Use exactly `Verified as-is`, `Documented gap`, `Implemented gap`, or
`Intended` on every requirement.

**Rationale**: One feature can contain both proven behavior and future intent. A
feature-level status would hide that distinction.

**Alternatives considered**: Binary implementation status, feature-level status, and
confidence percentages; all lose necessary meaning or imply false precision.

## Decision 3: Require three-source proof

**Decision**: `Verified as-is` requires a durable business contract, an observable
implementation location, and a currently green executable proof.

**Rationale**: Documentation proves intent, implementation proves delivery, and tests
provide repeatable evidence. No one source is sufficient alone.

**Alternatives considered**: Tests alone or documentation plus implementation; both
were rejected as incomplete proof.

## Decision 4: Preserve long-lived authorities

**Decision**: Link Architecture, Data Model, Web Spec, Test Strategy, ADRs, and the
Constitution rather than copying them into every baseline.

**Rationale**: Cross-cutting rules need one durable source. Baselines are discovery and
traceability artifacts, not replacements for architecture contracts.

**Alternatives considered**: Moving all docs under `specs/` or copying invariants into
every spec; both create false history or drift.

## Decision 5: Review in dependency-aware batches

**Decision**: Review foundation before Source/Evidence, then operational Reality,
end-to-end stories, interaction/explanation, and finally Web.

**Rationale**: Later capabilities depend on identity, tenancy, source, and Reality
meaning. This minimizes repeated clarification.

**Alternatives considered**: Alphabetical, UI-first, or all-at-once review; each ignores
dependencies or overloads owner review.

## Decision 6: Do not fix discovered gaps during baselining

**Decision**: Record contradictions and gaps; create future change specs after owner
prioritization.

**Rationale**: Mixing discovery and fixes mutates the measured system and weakens the
review boundary.

**Alternatives considered**: Immediate fixes or silently deferred gaps; both were
rejected because they hide unreviewed choices or incomplete truth.

## Decision 7: Use English for every repository artifact

**Decision**: Specs, plans, tasks, checklists, code, comments, tests, documentation, and
recorded owner decisions are written in English. Owner conversations may remain German.

**Rationale**: One repository language keeps search, review, automation, and future
collaboration consistent while allowing the owner to communicate naturally.

**Alternatives considered**: Bilingual artifacts or German product specs with English
code; both were rejected because they duplicate terminology and create translation
drift.
