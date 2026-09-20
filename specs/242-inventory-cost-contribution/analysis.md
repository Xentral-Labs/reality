
### Historical contribution graph review

Spec/plan/tasks analysis for T145–T148: no unresolved critical findings. Fixed
aggregate source vocabulary prevents arbitrary expressions; exact context admission
and standalone grain prevent fanout. Filters precede both coverage and arithmetic.
Rate unit is explicitly percent with currency partition, not a count. Cutoff bucketing
is refused. Required regression tests precede implementation. Existing unresolved
release gates remain open; this step does not claim UI selection or company coverage.

T149 review: discovery remains non-authoritative metadata; execution retains the same
admission boundary. Reuse existing cancellation and saved-question behavior. Distinguish
loaded position count from DB coverage, and never render inventory acquisition wording
for contribution results. No unresolved critical finding or new financial mutation.

### Selected contribution freshness review

T150–T153: no unresolved critical finding. Existing generation/action membership
admission remains unchanged. Both public reads check the cursor after aggregation
under READ COMMITTED; historical reads have no live-cursor dependency. Pending current
results are withheld even for empty filters. A read never locks intake or approves
new events. Tenant-wide invalidation is conservative and explicit, not a claim of
affected-scope precision. No schema expansion. Full-company publication and fixture J
remain open; UI wording describes unchanged data at the selected cutoff.

### Company population closure review

T154–T157: no unresolved critical finding. Exact identities replace count-only completion
checks; unknown values require explicit evaluated rows. Separate population and monetary
coverage prevent dropping unreviewed subjects or presenting partial totals as complete.
A shared context uses a population watermark and per-subject fingerprints, not one
fictitious item policy. Canonical full-company input discovery remains an explicit
unimplemented integration requirement. The internal helper accepts only trusted builder
facts and is not an API, financial approval or sole publication gate. No schema change.

### Current company census review

T158–T161: no unresolved critical finding. Movement membership uses recorded event
identity and effective time; absent or ambiguous events stay visible. Header events
cannot prove line knowledge history, so current MVCC census is explicitly distinguished
from a historical manifest. Sales lines without matched economic dates remain candidates
rather than being excluded by invoice date. Source gaps are not invented sales rows.
Bounds refuse combined overflow. Background discovery may scan its bounded tenant input;
no ordinary report read is routed through it. No new schema or financial approval.

### Manifest-bound company publication review

T162–T165: no unresolved critical finding in the domain extension. FR-007/012/014/018
map to explicit membership/context/hash/count refusal tests and unchanged publication
integrity gates. The typed company basis avoids a fabricated common policy/profile.
Expected fingerprints bind resolved financial inputs, not raw census record fingerprints.
Hashing is order-independent but not an authority or replacement for retained members.
Current discovery remains incompatible with historical PopulationBasis until a trusted
input resolver establishes supported historical admission. No schema or product-scope
expansion, runtime service exposure or automatic confirmation is introduced. Existing
selected-scope publication remains separately typed. Storage and reference-scale gates
remain open rather than being inferred from successful pure validation.

### Retained census design review (proposal only)

The existing sealed receipt manifest cannot truthfully store unassessed current discovery:
its historical knowledge and admitted financial membership semantics differ. Dedicated
current-observation storage avoids that conflict and makes mutable values reconstructable.
Typed family membership is preferred over a generic object registry or single JSON blob.
The proposal explicitly does not capture all financial input families or assert historical
knowledge. Same-capture line/header links, immutable SQL guards, rollback, replay and
byte/record bounds have test requirements. A separate five-table family was not explicit
in the prior approved model; owner schema approval remains a blocking design gate. No
implementation can begin while T167 is open. No existing release task is closed.

Retained census approval gate resolved on 2026-09-19 by explicit owner approval.
All Constitution rows now PASS for the reviewed five-table slice. Tests precede schema
and service implementation; no critical design finding remains. Shared release findings
and historical financial resolver/publication work remain open.


### Retained census final implementation review

The approved five-table shape is implemented with same-tenant/capture FKs, stable opaque
UUIDs, explicit version-1 field allowlists, SQL immutability and populated downgrade refusal.
Records are collected by the same snapshot queries used for discovery. Idempotent replay
verifies the prior capture, and savepoint rollback protects a caller that catches a failure
and commits. A line-removal guard provides domain guidance without freezing permitted
manual edits. An explicit scoped outer-join check refuses malformed legacy parent links
instead of losing their lines through the sales-header join. No foreign header is read.

Byte bounds limit retained canonical output; they are not a peak-memory or fixture-J proof.
The new capture is not a financial manifest, supplies no invented knowledge cutoff and
cannot be passed directly to the company publication guard. No current company valuation,
public write tool, scheduling registration or activation is implied. Shared global lint
and full release gates remain open; there is no critical finding in this bounded slice.

### Retained review resolution review

T170–T173 has no critical finding: current census observations remain distinct from
historical financial authority. Event-scoped review selection cannot borrow future approval;
older or different-cutoff results stay separate. Membership and cursor checks are deliberately
conservative and do not promise affected-input precision. Canonical retained readers own all
arithmetic and financial integrity checks. Unknown subjects, unsupported candidate types and
source/header gaps are preserved. Ten-subject refusal bounds this integration candidate;
full-company manifests, chunking and release qualification remain open. No schema approval
is needed because the existing approved retained records and services are reused.


Retained resolution implementation review: event-scoped selectors, same-tenant joins,
strict pre-valuation subject limits and explicit historical reader calls match the plan.
No amount arithmetic or policy inference was added. Canonical readers verify retained
financial hashes; census verification supplies immutable observation members through a
private optional collector. No ordinary inspection path changed. Gaps and historical
basis_result are separate from result, and all header/source gaps remain represented.
The common financial manifest and precise invalidation are still absent and explicitly
prevent company publication. Owned scope tests pass; shared release gates remain open.

### Contribution-only event relevance review

No critical finding for T174–T177. The existing contribution review executor only admits
revenue/review/selling-review membership; it does not change acquisition attribution,
physical movement, inventory policy or ownership. Exact persisted event/action/target
membership is required before exempting the event. Other-line confirmation is disjoint
under the existing whole-line/unique-shipment admission model. Same-line and all unknown
operations remain conservative. No financial approval is fabricated and the narrow
exception does not relax ordinary current readers, source gaps or publication guards.

Implementation review: the exact closed action/event/target proof precedes every
non-invalidating decision. The interval is complete, ordered and bounded; malformed
proof fails closed. The resolver retains canonical readers and existing cutoff/member
checks. All 140 affected regression tests pass, including 17 new proof cases. No critical
finding remains for this slice. Full-company manifest/publication/scale gates remain open.

### Common captured review basis analysis (T178–T181)

FR-007/012/014/019 map to T178–T181 and test_cost_captured_basis.py, with existing
resolution/relevance tests covering canonical financial replay, tenant/isolation/bounds
and SELECT-only behavior. No unmapped task, ambiguity or critical finding in this slice.
Exact expected membership comes from verified census records, not successful reviews.
The digest binds observations and existing authority references; it is deliberately not
the retained financial input fingerprint required by the company publication guard.
Per-review knowledge remains distinct from observed_at. Acquisition/carrying and DB1/DB2
coverage are independent, with financial dependency checks and explicit external gaps.
No schema expansion or change to scope approval was introduced. Reviewer checklist status
remains 40 checked and six unchecked under the previously authorized continuation.

Implementation review: the resolver adds the assembly only after all canonical reads and
gap checks. The helper rejects exact-set/context/identity mismatches, canonicalizes order,
binds result/proof/gap changes and never calculates monetary amounts. Historical basis
results cannot count as available coverage. Existing financial/publication boundaries hold.

Final evidence: 164 affected backend tests and 73 docs tests pass. The malformed-float
refusal now runs before hashing, and all 24 final basis proofs pass. No critical finding
remains for the captured-basis slice; financial retention and company publication remain
separate unfinished work.

### Captured-basis retention proposal review

T182 prepares the next concrete review boundary. The three-table design covers exact
typed membership, unknown subjects, stable retries, SQL immutability and pinned replay.
It rejects receipt-manifest reuse because the knowledge contract differs, and separates
lifecycle flags from digest content rather than flipping v1 hashed flags after retention.
Tests cover these boundaries before implementation. No unresolved technical clarification
or critical inconsistency in the proposed slice; the explicit owner schema approval gate
T183 remains open. Do not implement T184 until that gate is satisfied. This proposal does
not establish full financial population admission or company publication.

### Approved retention implementation review

T183 owner approval closes the schema gate. Migration 0072 is the sole successor to
0071 and implements only the approved three tables. Same-tenant FKs and sealed SQL
guards preserve dependency retention; metadata and replay use trusted service lookups.
The original resolver receives an internal verified pinned selection only during replay;
public resolution retains latest-at-capture selection. Digest mismatch cannot silently
change historical output. Savepoint rollback, caller-owned commit and fresh-transaction
retry preserve the transaction boundary. No private helper is exposed as user approval.
Version 2 separates lifecycle flags, with explicit v1 verification. No critical finding
in this bounded implementation; company context/publication and scale remain separate.

Retention completion review: 189 broader backend tests, 27 final storage/migration checks
and 69 generation/finance compatibility tests pass, alongside docs/reference/scoped lint
and specification checks. Counts overlap. The three new public service entrypoints are
classified and exercised in the tenant catalog (524 total discovered operations).
The remaining 14 global import findings are outside this slice and keep T185 open.

### Captured known-subtotal summary review (T186–T189)

The specification, plan and tests agree on a ten-subject, read-only diagnostic over
verified pinned replay. There is no schema expansion or unresolved clarification for
this slice. Existing fixed SQL contribution expressions preserve per-row DB support;
all final totals and rates remain absent. Currency/base-unit partitions and additional
inventory method/owner partitions prevent incompatible sums. Available-only group
coverage is explicitly distinct from full captured population coverage. Historical
values cannot enter numeric groups. Member identities and canonical details preserve
the shortest evidence path.

The SQL VALUES input is private, built only after canonical replay and never offered as
a graph relation or user-supplied row-array API. This does not waive financial population
admission, company context, publication or scale requirements. Review found no critical
inconsistency in this bounded slice. PostgreSQL tests exposed all-null numeric VALUES
columns being inferred as text; explicit numeric casts preserve unknowns and fix the
failure. The real joint fixture uses different base units, so its asserted result remains
two groups instead of an invalid combined sum.


Summary completion review: all 179 selected backend tests pass, including nine new
summary checks; docs/reference generation, scoped lint/format and spec policy pass.
No new critical finding remains in this slice. Shared lint findings and full-company
release obligations remain explicitly open and are not waived by T189 completion.


### Approved captured report implementation analysis

### Fixed captured graph context analysis (T194)

No critical cross-artifact conflict remains for the bounded graph integration. A single
generation identity avoids both a mutable publication selector and a false historical
`knowledge_at`. Reusing the two canonical costing derivations preserves the compiler,
graph measures, saved-report validation and adapter path. The new context is exclusive
with both historical contexts; standalone-only planning prevents fan-out multiplication.
Cached rows retain unknown members for coverage while grouping excludes their absent
dimensions. Final commercial totals remain suppressed through the existing unreviewed
contribution aggregate mode. Company-scale, worker and financial-admission gates remain
outside T194.

### Captured discovery/selector analysis (T195–T197)

### Bounded captured worker analysis (T198–T200)

### Bounded captured publication worker analysis (T201–T203)

No critical conflict remains for the separate publication job. Default worker isolation
matches the existing CAS service, while explicit `expected_previous_id` prevents a queued
stale request from overwriting a newer pointer. Reusing the shared publication service
preserves tenant lock ordering and diagnostic-only semantics. The job is not a scheduler,
builder, financial approval or larger-company orchestrator.

No critical conflict remains for a build-only worker. Combining build and publication in
one handler would violate their deliberate REPEATABLE READ versus READ COMMITTED contracts.
A separate job over one retained basis preserves transaction fencing, bounded work and
idempotent generation identity while returning no commercial values. It is not the future
multi-chunk company orchestrator and cannot close scale or financial-admission gates.

No critical conflict remains for metadata discovery. The existing historical review-option
services cannot represent captured unknown members or a sealed report identity, so a
separate read service is the shortest truthful boundary. It reuses the graph tool/HTTP/MCP
transport pattern and returns no cached financial values. UI selection remains mutually
exclusive at the traversal contract. Publication status is descriptive only and selection
always stores `generation_id`, preventing a saved analysis from drifting with the pointer.
Worker orchestration, larger populations and financial admission remain explicit gaps.

The owner acceptance closes T191. Explicit captured kind prevents historical-context
substitution; cache rows reference typed retained members rather than duplicating source
relationships. Exact sets and canonical persisted hashes precede sealing, with SQL
immutability and same-tenant scope/member checks. Publication uses tenant serialization
and compare-and-swap; reads pin generation identity. Tests cover missing costs independently
from completed work. No critical inconsistency remains for T192/T193. Graph/worker/scale
integration and full financial admission remain separate T194 and release obligations.


Captured report completion review: the 179-test regression, additional publication case
and 58 generation/reporting compatibility tests pass, alongside docs/reference/scoped
lint and spec checks. SQL guards, fixed member links, canonical replay only during build,
exact cached-output verification and tenant-serialized CAS satisfy the approved bounded
contract. No critical implementation finding remains for T192/T193. All captured output
remains financially non-final. T194 and shared formatting/lint/release obligations remain
open; this review is not a claim that the complete company report is delivered.

### Canonical costing demo pre-implementation analysis (T258–T262)

FR-026 and SC-007 have a single bounded implementation path after commercial matching:
the versioned canonical baseline, not the ongoing Demo Data stream. The company-setup
worker already provides the required atomic replay boundary and source-control ordering;
the costing services already provide confirmed append-only inventory, commercial and
contribution authority. Reusing both avoids a second queue and avoids direct seed writes
to costing tables.

The missing plan detail and monolithic T083 task were HIGH execution-quality gaps, not
requirement conflicts. The new plan fixes the profile version, three stories, exact
quantity assertions, authority lifetime and replay behavior; T258–T262 enforce tests
before implementation and name the real baseline files. No schema expansion is required.
The narrow fixed-recipe authority must not be callable by adapters or accept arbitrary
cost requests, and the live source retains its default missing-cost disclosure. With
those constraints, no CRITICAL specification, plan, task or Constitution inconsistency
remains before test authoring.
