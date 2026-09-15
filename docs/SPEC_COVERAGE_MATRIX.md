# Specification Coverage Matrix

**Language**: English
**Reviewed**: 2026-08-31
**Final verification**: 2026-09-02
**Authority**: [`specs/001-baseline-spec-coverage/spec.md`](../specs/001-baseline-spec-coverage/spec.md)

This is the discovery index for existing Business Reality behavior. It assigns each
included source family to one primary baseline or a named cross-cutting authority. It
does not replace feature specifications, the Constitution, Architecture, or ADRs.

## Capability Summary

Learning Playground storage foundation (`096-learning-playground`, implementation in
progress): `playground_run` and `playground_step` are tenant-scoped orchestration metadata,
not new operational records. Evidence: `packages/reality-core/tests/test_playground_runs.py`
and `packages/reality-core/tests/test_migrations.py` cover defaults, immutable purpose,
same-tenant links, uniqueness, bounded observations and disposable migration round-trip.
This does not certify the pending service policy, lesson, chat or UI release gates.

Storyline mode (`182-storyline-mode`, implementation in progress): `storyline_trace_entry`
is a bounded, tenant-scoped call trace of a Storyline run and `storyline_package` is an
account-owned imported package; neither is a business record. Evidence:
`packages/reality-core/tests/test_storyline_trace.py`,
`packages/reality-core/tests/test_storyline_package.py`,
`packages/reality-core/tests/test_storyline_delta.py`,
`packages/reality-core/tests/test_storyline_runs.py`,
`packages/reality-core/tests/test_storyline_library_api.py`,
`packages/reality-core/tests/test_storyline_export.py`,
`packages/reality-core/tests/scenarios/test_storyline_first_round.py`,
`packages/reality-core/tests/scenarios/test_storyline_order_to_close.py`,
`packages/reality-core/tests/scenarios/test_storyline_purchase_to_pay.py` and the storyline migration test in
`packages/reality-core/tests/test_migrations.py`.

| Baseline                                                              | Status   | Primary capability                               | Verified requirement groups | Documented gaps | Reviewed   |
| --------------------------------------------------------------------- | -------- | ------------------------------------------------ | --------------------------: | --------------: | ---------- |
| [`003-tenant-access`](../specs/003-tenant-access/spec.md)             | Reviewed | Identity, access, tenancy, lifecycle, isolation  |                          13 |               0 | 2026-08-31 |
| [`004-master-data`](../specs/004-master-data/spec.md)                 | Reviewed | Parties, items, locations, commercial references |                          16 |               0 | 2026-09-02 |
| [`005-source-ingestion`](../specs/005-source-ingestion/spec.md)       | Reviewed | Immutable sources, artifacts, imports, Shopify   |                          15 |               0 | 2026-08-31 |
| [`006-documents-evidence`](../specs/006-documents-evidence/spec.md)   | Reviewed | Documents, lines, evidence, corrections          |                          12 |               1 | 2026-08-31 |
| [`008-commitments-holds`](../specs/008-commitments-holds/spec.md)     | Reviewed | Directional promises and execution holds         |                          14 |               0 | 2026-08-31 |
| [`009-inventory-execution`](../specs/009-inventory-execution/spec.md) | Reviewed | Reservations, movements, inventory, tracking     |                          15 |               1 | 2026-08-31 |
| [`010-order-to-cash`](../specs/010-order-to-cash/spec.md)             | Reviewed | Customer source-to-delivery-to-cash story        |                          10 |               0 | 2026-08-31 |
| [`011-procure-to-pay`](../specs/011-procure-to-pay/spec.md)           | Reviewed | Supplier promise-to-receipt-to-payment story     |                          10 |               0 | 2026-08-31 |
| [`012-ledger-finance`](../specs/012-ledger-finance/spec.md)           | Reviewed | Postings, payments, allocations, open items      |                          12 |               0 | 2026-09-01 |
| [`013-explain-projections`](../specs/013-explain-projections/spec.md) | Reviewed | Explain, events, exceptions, projections         |                          11 |               0 | 2026-08-31 |
| [`014-agent-interaction`](../specs/014-agent-interaction/spec.md)     | Reviewed | Chat, tools, confirmation, AI, MCP               |                          13 |               0 | 2026-08-31 |
| [`015-demo-scenarios`](../specs/015-demo-scenarios/spec.md)           | Reviewed | Guided demo and deterministic stories            |                          10 |               0 | 2026-09-02 |
| [`016-web-product`](../specs/016-web-product/spec.md)                 | Reviewed | Operations Cockpit and Reality Inspector         |                          16 |               0 | 2026-09-02 |

`007-core-catalogs` is an independently reviewed change specification, not one of the
thirteen as-is capability baselines. It owns the executable vocabulary catalogs and is
referenced as a cross-cutting authority where applicable.

## Accepted Documented Gaps

No accepted documented gaps remain. Spec 033 closes `016/FR-015` with an
repeatable 10,000-orders/day register proof, subject to product-owner final acceptance.

No contract/implementation contradiction was found that violates the Constitution.
Previously accepted uncertainties were closed by focused change specifications.
`003/FR-012` is no longer listed:
Spec 019 added a deterministic catalog for 166 public operations across six isolation
classes, named executable family evidence, registry drift detection, and populated
two-tenant PostgreSQL proofs. `016/FR-013` is also no longer listed:
Spec 017 verified complete `en`, `de`, `nl`, and `es` coverage, safe fallback, public/auth
language continuity, protected original content, and representative visual states.
`013/FR-005` is also no longer listed: Spec 020 added the closed class/cause taxonomy,
one tenant-scoped derivation/explanation service, focused PostgreSQL proof for every class
and cause, shared-consumer parity, and deterministic registry/evidence drift validation.
Spec 068 extended that taxonomy to seven classes by adding the two outgoing-promise
coverage conditions, allowed one business reason to be named by more than one class
without loosening drift detection, and made the overdue class supersede the at-risk class
so one commitment still produces at most one entry. Spec 069 added the eighth class,
overdue receivables, and consolidated the due-date rule that had been duplicated between
the service layer and the read model with no caller in either place, so no transport
computes when money is due. Spec 071 made the business meaning, the operational owner and
the clearing path required fields of every class, so an operator can read what a condition
means from the generated catalog and no class can ship without saying it. Spec 072 added the
ninth class, a source that has stopped delivering, judged against the delivery rhythm that
source has shown itself rather than against any configured interval. Spec 074 added the
tenth, an unpaid supplier invoice, by parameterising the open-item rule rather than copying
it, and recorded three further conditions the model prevents or cannot express. Spec 076
added the eleventh, twelfth and thirteenth by giving an invoice line the one edge it lacked
— a reference to the order line it bills — and deriving from it what was shipped and never
billed, what was billed and never received, and where a billed price differs from the
agreed one. It is the first schema change in this line of work, and the three classes are
what justify the column. Spec 078 added the fourteenth and fifteenth without any schema at
all, by reading a Party field that had been carried, validated and audited since the
master-data baseline without ever being read, and by grouping supplier invoices on the number
their supplier put on them — the first class carried by a Party rather than by a transaction.
Spec 079 closed return-to-resolution, also without schema, by letting a return name the
customer delivery it reverses and a credit note line name the order line it credits — two
links that already existed and were refused to returns. It added the sixteenth and
seventeenth classes, corrected `shipped_not_billed` to stop billing goods that came back, and
put the operational exception queue and the service layer on one correction-aware movement
quantity, which they had not shared. Spec 080 gave the learned-expectation rule of Spec 072
two more users and its own statistic: a median of this tenant's most recent finished cases
rather than a longest pause, because a fulfilment lag has no upper bound. It added the
eighteenth and nineteenth classes — an undated order standing far longer than this company
normally takes, which every date-anchored class was blind to, and a receipt no supplier has
invoiced past the point where that stops being ordinary. Spec 082 closed the last gap the
trading survey found with the second schema change of the series: one nullable column letting a
movement say which return it settles, and the twentieth class over it. Spec 085 added the
first way _out_ of the queue rather than another way in: an imported history leaves thousands
of promises nobody is going to keep, and until now nothing could close them from inside. It is
the only operation in the product that closes many records at once, and everything that makes
it safe — a preview that writes nothing, a confirmed count, a required reason, one transaction,
and a refusal to touch anything with movement or a hold against it — is a requirement rather
than an implementation choice. Spec 086 added the twenty-third class by correcting an
assumption rather than by building a cost model: a purchase price list is a received value, so
comparing an agreed sales price with the standing purchase price computes nothing. It is not
accounting margin and says so in its own guidance. Spec 087 added the twenty-fourth by making
a refusal audible. Six classes had quietly declined to compare any pair recorded in different
units — the right answer every time and silent every time, so that a line nobody needs to look
at and a line the rules refused to look at were indistinguishable. Whether two quantities are
comparable is now one decision in one place, and it uses a relation the company had already
stated and nobody read: an item's purchase unit and conversion factor. Converting a stated
quantity by a stated factor at read time, storing nothing, is an observation and not a second
authority; prices are excluded by rule, because dividing one produces money nobody agreed. What
still cannot be compared is reported per item, saying which of two things went wrong.
Spec 088 is the first in the series to fix a defect rather than add a capability. A `PaymentTerm`
carried only `due_days`, so every early-payment discount a company had negotiated was invisible
— and a customer taking the discount it was offered left a residue that `overdue_receivable`
reported as a debt for ever, one false entry per invoice on any business that grants one. Two
nullable columns, one shared rule placing the discount deadline beside the due date, the
twenty-fifth class for a discount still there to take, and a cause that lets an overdue entry
say why its remainder is not a debt. No discount amount is ever computed: both sides of the
comparison are multiplied out so that nothing divides and no reported figure depends on a
rounding decision. Spec 089 mirrored spec 084 onto the buying side: a supplier credit note that
posts as the reverse of a supplier invoice, nets against a payable or is refunded, and the
twenty-sixth and twenty-seventh classes for a supplier credit nobody booked and one nobody
claimed. Four settleable documents became six and nothing else had to change, because the
settlement relation already links any two control entries on opposite sides of one account. The
two sides share the learned rule for "never booked" and deliberately share no history. It is
half a feature by design: a return to a supplier cannot be recorded at all, so a credit for
returned goods carries no evidence of the goods, and that mirror of specs 079 and 082 is the
remaining gap from the trading survey — until spec 090 closed it. A `supplier_delivery`
commitment accepted receipts and nothing else, so goods going back to a supplier could not be
recorded at all: stock stayed wrong, the company kept accruing an invoice for things it no longer
had, and the resolution spec 082 had already named — sending a customer's faulty item on to the
supplier — was the one the model could not express. One movement kind with the direction it
actually has, bounded by what arrived rather than by what the promise has open, closed all three
and cost no schema. The twenty-eighth and twenty-ninth classes compare what went back against
what the supplier credited, from the same body the selling side has always used. **Every gap the
2026-09-05 trading survey found is now closed**, across seven specifications and four schema
changes. Spec 091 then answered a different question and found something the class surveys had
missed entirely. Every survey until then had asked what the operational queue could not see; this
one asked what a person could not do, and the first answer was that nobody outside the demo could
book an invoice. `post_sales_invoice` and `post_supplier_invoice` had no endpoint, no agent tool
and no command, so on any real tenant the aging register was empty by construction and five
conditions — `overdue_receivable`, `overdue_payable`, `credit_limit_exceeded`,
`purchase_discount_available` and the early-payment discount reason — could never fire. They had
been specified, tested and shipped against a posted invoice no surface could produce, and the
tests passed because the tests post invoices themselves. The fix is entirely declaration and
transport, and the credit note is its yardstick throughout so the two cannot drift apart again.
Spec 092 then built the class 084 had argued for and never written: its own catalog text said
recording and booking are two acts "exactly as they are for an invoice", and the invoice case had
sat unwritten through 084, 089 and the whole trading survey. It could not have come earlier —
until 091 nothing outside the demo could book an invoice, so no tenant could have a booking
rhythm and a class learning one would have been silent everywhere or wrong everywhere. Two
classes rather than one, split by owner as the credit pair is, from the body 089 had already
generalised. Writing the four document types down together also showed that
`supplier_credit_unposted` had been asking a different account from its own posting operation
since 089 — equivalent in practice, corrected so the two cannot drift. Spec 093 closed the third item from that audit and is the first schema change in the series that
exists to _prevent_ an overwrite rather than to record a new kind of fact. A `Commitment` carried
one `due_at`, written at creation, and nothing anywhere updated it — so a supplier acknowledging a
different date could not be recorded at all. A `confirmed_due_at` column would have been smaller
and would have let the second statement erase the first, and a date somebody stated is a received
value. So: one append-only table, one shared rule for the date in force, and one cause so that a
revision cannot buy silence — a promise late against a date its own counterparty chose says that
it was moved and names the day it was originally due. Spec 094 closed the structural item spec 091 named. The tenant isolation catalog is complete by
discovery; the command catalog was written by hand and nothing checked it, so an operation could
be built, made tenant-safe, wired to a surface and never declared. The gate composes the two —
mutating according to the isolation catalog, reachable according to the surfaces — and its first
run named fourteen. Eight were business operations that should always have been declared,
including releasing a reservation, which had an agent tool and no catalog entry for its whole
life; six are recorded as deliberately not commands with a reason each. It fails in both
directions, because a stale exemption hides the next real one. Spec 095 is the shortest entry in this list and the only one that built nothing. A restocking fee
was on the remaining-work list as a suspected false positive; measuring it first showed the model
already expresses one correctly — credit the goods, charge for what is kept — and that the entry
appears only when a company records the fee as a smaller credit, which is a true statement about
its own document. So the delivery is two pinned recordings and a paragraph of guidance, and the
more important test is the one asserting the partial credit still reports, because that behaviour
is correct and looks exactly like the bug. Spec 097 reversed one of spec 093's own non-goals, openly. That specification said a different
quantity is a different promise, which was right for a specification about dates and wrong as a
permanent answer: in trade the two arrive in the same sentence, and a supplier confirming eighty
of the hundred was unrecordable — `Commitment.quantity` was never assigned anywhere and
`create_commitment` is reachable from no surface. So one nullable column on the record 093 built,
a second rule beside its first, and four call sites that stop reading the promise directly.
Writing the second rule exposed a bug in the first: `commitment_due_at` took the latest revision
unconditionally, so a quantity-only statement returned its empty date and silenced every
date-judged class. A test caught it before the feature shipped. Spec 098 built the payment run the
early-payment-discount class had already named as its owner's job, and the most useful thing to
say about it is what it refuses to do. An ERP payment run is mechanically a discount calculator:
it walks the open payables and pays gross minus a rate, which is the largest source of money
nobody agreed to in an ERP, because 2% of 1,234.56 is 24.6912 and the rounded figure becomes what
a supplier is told they were paid. So the run states no amount. What it contributes is the three
things genuinely missing: a read that assembles what is worth paying, a transaction so a Friday
cannot half-happen, and one event recording that forty payments were one decision. It refuses to
pay an invoice reported as a duplicate, which is the one place this queue refuses on a derived
condition rather than reporting it, and it leaves without a durable per-invoice block — holding
one back means leaving it out, and it reappears in the next preview. No schema. Spec 099 closed the last of the four, and its interesting decision is the one that
looks wrong at first glance: an announced return is a directional promise, a Commitment is the
product's word for a directional promise, and the specification does not use one. The reason is a
measurement rather than a preference — `customer_delivery` is read in thirty-two places across
eight modules, seventeen of them a two-way branch whose `else` silently means supplier delivery,
so a third type would make all seventeen wrong while most kept passing their tests. That is the
shape of bug this work has been bitten by twice already. So the announcement is its own record,
the honest cost is one more entity in a model that prides itself on having few, and the plan says
that if the commitment vocabulary is ever widened deliberately this is the first table to fold
into it. Spec 100 turned the largest recorded risk into a gate, and measuring it first changed
every number in it. The risk said absence was load bearing in three classes; there are four
references, sixteen classes read one and eleven reason from one. It said the classes would go
"quietly wrong", which is half the story and the less important half: six pairs conclude from
absence and therefore cry wolf, reporting work that was done, while thirteen start from the
reference and therefore go blind — and `billed_not_received` going blind means a company pays for
goods that never arrived and nothing notices. Four gates now compose a declaration with facts
discovered from the mapper, the source and the command catalog, and on their first run they found
that the MCP schema never named the reference nine classes read and that the web app had no box
for it. The honest limit is stated rather than implied: a gate can prove every path is able to
carry a reference and cannot make anybody type one. The cheaper
version
needing no schema was specified and abandoned, because stock is fungible and reading what is
left in a returns location would have produced a condition that is right only sometimes.
Spec 084 closed the money half of the same chain. A credit note recorded a quantity and posted
nothing, the amount-and-invoice credit path was reachable from no surface the product has, and
crediting an invoice the customer had already paid — the ordinary consumer return — could not
be expressed at all. Settlement now knows four settleable documents rather than two, a credit
note posts as the reverse of an invoice and is netted or refunded, and two classes report a
credit promised and never booked and one booked and never given back.
`009/FR-009` is also no longer listed: Spec 023 added append-only Movement void and
replacement, exact compensation, shared preview/confirmation, audit-chain explanation,
tenant isolation, and correction-aware operational derivation.
`012/FR-008` is also no longer listed: Spec 024 added complete posting-group reversal
through an immutable exact inverse, durable correction Evidence, shared confirmation,
reversal-aware settlement derivation, tenant isolation, and Inspector traversal.
`004/FR-016` is also no longer listed: Spec 026 proves all 36 Party, Item, and Location
create/update/deactivate/reactivate cells across CLI, JSON API, and Product Web through
shared services and equivalent authoritative state.
`015/FR-010` is also no longer listed: Spec 027 proves complete guided-demo state
equivalence across interactive CLI, CLI auto mode, and confirmed Product Web onboarding,
including cancellation, rerun, failure, and tenant-isolation boundaries.
`016/FR-006` is also no longer listed: Spec 030 freezes the complete Product Web
topology in `ux-matrix-v1`, adds the tenant-scoped Journal control surface, enforces
shared state/responsive/trace contracts, and records owner-approved visual and final
review evidence.
`016/FR-015` is also no longer listed: Spec 033 supplies a deterministic full PostgreSQL
dataset with 10,000 same-day orders and 19,999 lines/commitments, two semantically
identical runs across all nine register families, structural SQL-boundary evidence, and
bounded Payment enrichment.

## Durable Contract Ownership

| Source                                                      | Primary baseline or authority                                                                    | Coverage                                                                                        |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| `AGENTS.md`                                                 | Constitution                                                                                     | Cross-cutting runtime contract                                                                  |
| `.specify/memory/constitution.md`                           | Constitution                                                                                     | Cross-cutting highest authority                                                                 |
| `docs/ARCHITECTURE.md`                                      | Constitution + all baselines                                                                     | Cross-cutting architecture                                                                      |
| `docs/CLI_SPEC.md`                                          | `003`, `014`, `015`, `016`                                                                       | Cross-cutting adapter contract                                                                  |
| `docs/DATA_MODEL.md`                                        | Constitution + `003–016`                                                                         | Cross-cutting model summary                                                                     |
| `docs/DEMO_SPEC.md`                                         | `015-demo-scenarios`                                                                             | Covered                                                                                         |
| `docs/ERP_MONTH.md`                                         | `015-demo-scenarios`                                                                             | Covered                                                                                         |
| `docs/SPEC_DRIVEN_WORKFLOW.md`                              | `001-baseline-spec-coverage`                                                                     | Cross-cutting workflow                                                                          |
| `docs/TAILADMIN_UI_AUDIT.md`                                | `016-web-product`                                                                                | Covered; backlog distinguished                                                                  |
| `docs/TEST_STRATEGY.md`                                     | Constitution + `001`                                                                             | Cross-cutting test authority                                                                    |
| `docs/THIRD_PARTY_NOTICES.md`                               | Repository governance                                                                            | Excluded: licensing inventory, not product behavior                                             |
| `docs/V0_CHECKLIST.md`                                      | All capability baselines                                                                         | Cross-cutting completion contract                                                               |
| `docs/WEB_SPEC.md`                                          | `016-web-product`                                                                                | Covered; component rules delegated to domain baselines                                          |
| `docs/WEB_UX_MATRIX.md`                                     | `016-web-product`                                                                                | Covered; incomplete targets are gaps                                                            |
| `docs/agreements/atlas_reality_o2c_test.md`                 | Repository governance                                                                            | Excluded: external integration test agreement, not product behavior                             |
| `docs/decisions/0001-postgresql-only.md`                    | Constitution                                                                                     | Cross-cutting storage decision                                                                  |
| `docs/decisions/0002-source-evidence-reality.md`            | Constitution                                                                                     | Cross-cutting domain decision                                                                   |
| `docs/decisions/0003-shortest-true-link.md`                 | Constitution                                                                                     | Cross-cutting relationship decision                                                             |
| `docs/decisions/0004-production-storage-and-projections.md` | `013-explain-projections`                                                                        | Cross-cutting projection/storage decision                                                       |
| `docs/decisions/0005-frontend-backend-object-storage.md`    | `005`, `016`                                                                                     | Cross-cutting deployment/storage decision                                                       |
| `docs/features/tenancy.md`                                  | `003-tenant-access`                                                                              | Covered                                                                                         |
| `docs/features/master_data.md`                              | `004-master-data`                                                                                | Covered                                                                                         |
| `docs/features/operational_fields.md`                       | `004-master-data`                                                                                | Covered; referenced by Evidence/Reality baselines                                               |
| `docs/features/source_ingestion.md`                         | `005-source-ingestion`                                                                           | Covered                                                                                         |
| `docs/features/shopify_ingestion.md`                        | `005-source-ingestion`                                                                           | Covered                                                                                         |
| `docs/features/commitments.md`                              | `008-commitments-holds`                                                                          | Covered                                                                                         |
| `docs/features/commitment_holds.md`                         | `008-commitments-holds`                                                                          | Covered                                                                                         |
| `docs/features/party_delivery_holds.md`                     | `008-commitments-holds`                                                                          | Covered                                                                                         |
| `docs/features/reservations.md`                             | `009-inventory-execution`                                                                        | Covered                                                                                         |
| `docs/features/inventory.md`                                | `009-inventory-execution`                                                                        | Covered                                                                                         |
| `docs/features/movements.md`                                | `009-inventory-execution`                                                                        | Covered                                                                                         |
| `docs/features/order_to_cash.md`                            | `010-order-to-cash`                                                                              | Covered                                                                                         |
| `docs/features/procure_to_pay.md`                           | `011-procure-to-pay`                                                                             | Covered                                                                                         |
| `docs/features/ledger.md`                                   | `012-ledger-finance`                                                                             | Covered                                                                                         |
| `docs/features/explain.md`                                  | `013-explain-projections`                                                                        | Covered                                                                                         |
| `docs/features/operational_exceptions.md`                   | `013-explain-projections`, implemented by Spec 020, extended by Specs 068, 069, 071, 072 and 074 | Covered; complete class/cause proof validated                                                   |
| `docs/features/mcp_reads.md`                                | `145-mcp-read-contract`                                                                          | Currency, units, locations, retained evidence, pagination and observation contracts             |
| `docs/features/chat.md`                                     | `014-agent-interaction`                                                                          | Covered                                                                                         |
| `docs/features/chat_sessions.md`                            | `014-agent-interaction`                                                                          | Covered                                                                                         |
| `docs/features/demo.md`                                     | `015-demo-scenarios`                                                                             | Covered                                                                                         |
| `docs/features/web.md`                                      | `016-web-product`                                                                                | Covered                                                                                         |
| `docs/features/reality_gaps.md`                             | `067-reality-gap-workflow`                                                                       | Covered; tenant self-service is limited to safe declarative Fact rules                          |
| `docs/features/learning-playground.md`                      | `096-learning-playground`                                                                        | Storage and business-egress foundation only; interactive product and complete isolation pending |

## Persisted Concept Ownership

The source is `packages/reality-core/config/data_model.yaml`. Every key below has one primary owner;
cross-cutting relationships remain governed by the Constitution and Data Model.

| Primary owner                                  | Catalog tables                                                                                                                                                                                              |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `096-learning-playground` (storage foundation) | `playground_run`, `playground_step`                                                                                                                                                                         |
| `003-tenant-access`, extended by Spec 035      | `tenant`, `app_user`, `email_verification_code`, `user_session`, `access_application`, `access_admission_counter`, `tenant_membership`, `company_invitation`, `invitation_delivery`, `security_audit_event` |
| `004-master-data`                              | `party`, `party_role`, `payment_term`, `item`, `location`, `price_list`, `price_list_entry`, `party_price_list`, `party_group`, `party_group_member`, `party_group_price_list`                              |
| `005-source-ingestion`, extended by Spec 045   | `source_system`, `source_capability`, `source_artifact`, `source_stream`, `source_record`, `import_job`, `interpretation_outcome`, `interpretation_record_reference`                                        |
| `006-documents-evidence`                       | `document`, `document_line`                                                                                                                                                                                 |
| `008-commitments-holds`                        | `commitment`, `commitment_hold`, `party_hold`                                                                                                                                                               |
| `009-inventory-execution`                      | `reservation`, `movement`, `handling_unit`, `lot`, `serial_unit`                                                                                                                                            |
| `012-ledger-finance`                           | `ledger_entry`, `ledger_reversal`, `settlement_allocation`                                                                                                                                                  |
| `013-explain-projections`                      | `fact`, `business_event`, `projection_row`, `projection_checkpoint`                                                                                                                                         |
| `014-agent-interaction`                        | `secret`, `secret_audit_event`, `ai_settings`, `mcp_access_token`, `action`, `chat_session`, `chat_message`                                                                                                 |
| `067-reality-gap-workflow`                     | `reality_gap`, `reality_gap_entry`, `interpretation_rule`, `rule_interpretation_outcome`; adds optional Fact rule provenance                                                                                |

The end-to-end `010`, `011`, and `015` baselines compose these records and deliberately
do not claim duplicate table ownership. `016` presents them through shared services.

## Machine-Readable Catalog Ownership

| Catalog                                                           | Primary authority                                                                   | Coverage                                                                                                                    |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `packages/reality-core/config/data_model.yaml`                    | Data Model + owning baselines above                                                 | Covered and metadata-validated                                                                                              |
| `packages/reality-core/config/connector_catalog.yaml`             | `005-source-ingestion`                                                              | Covered                                                                                                                     |
| `packages/reality-core/config/command_catalog.yaml`               | `007-core-catalogs`, consumed by `014`/`016`                                        | Covered                                                                                                                     |
| `packages/reality-core/config/business_event_catalog.yaml`        | `007-core-catalogs`, consumed by `013`/`016`                                        | Covered                                                                                                                     |
| `packages/reality-core/config/projection_catalog.yaml`            | `007-core-catalogs`, consumed by `013`/`016`                                        | Covered                                                                                                                     |
| `packages/reality-core/config/fact_catalog.yaml`                  | `007-core-catalogs`, consumed by `013`/`016`                                        | Covered; empty stable vocabulary is explicit                                                                                |
| `packages/reality-core/config/tenant_isolation_catalog.yaml`      | `003/FR-012`, implemented by Spec 019                                               | Covered; metadata and operation drift validated                                                                             |
| `packages/reality-core/config/operational_exception_catalog.yaml` | `013/FR-005`, implemented by Spec 020, extended by Specs 068, 069, 071, 072 and 074 | Covered; class, cause, registry, order, shared-cause vocabulary, operator guidance, and executable-evidence drift validated |

## Public Capability Families

| Family                            | Observable boundary                                            | Primary owner                                 | Evidence family                                                                                               |
| --------------------------------- | -------------------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Tenant/access services            | `web/auth.py`, tenant lifecycle in `services/core.py`          | `003`                                         | user access, lifecycle, tenancy tests                                                                         |
| Master/commercial services        | master data, payment terms, pricing in `services/core.py`      | `004`                                         | operational fields, pricing, payment-term tests                                                               |
| Source/artifact/import services   | `services/artifacts.py`, file interpreters, ingestion services | `005`                                         | source, integration, import, Shopify tests                                                                    |
| Evidence services                 | document create/correct/detail services                        | `006`                                         | document correction/API/Inspector tests                                                                       |
| Commitment/hold services          | commitment and party/commitment hold functions                 | `008`                                         | fulfilment and hold tests                                                                                     |
| Inventory execution services      | Reservation, Movement, stock, tracking functions               | `009`                                         | inventory, tracking, handling-unit tests                                                                      |
| Finance services                  | posting, payment, allocation, finance reads                    | `012`                                         | ledger and story tests                                                                                        |
| Event/projection/explain services | event, exception, explain, projection modules                  | `013`                                         | event, projection, application-tool tests                                                                     |
| Agent/application tools           | `tools/application.py`, Chat, secrets, MCP                     | `014`                                         | application-tool, Chat, AI/MCP tests                                                                          |
| Scenario/bootstrap services       | demo, normal month, configured bootstrap                       | `015`                                         | scenario, bootstrap, CLI tests                                                                                |
| CLI adapter                       | `cli/app.py`, `cli/context.py`                                 | Owning capability baseline; `016` equivalence | CLI/context tests                                                                                             |
| HTTP/API adapter                  | `web/api.py`, `web/auth.py`, `web/read_models.py`              | Owning capability baseline; `016` shell       | HTTP, access, API tests                                                                                       |
| MCP adapter                       | `mcp/auth.py`, `mcp/catalog.py`, `mcp/server.py`               | `014`                                         | AI/MCP tests                                                                                                  |
| Public Site                       | landing presentation under `provider-site/src/`                    | `022`, localization by `034`                  | site contract tests, site localization tests, four-language `i18n:audit`, build, independent image smoke test |
| React product                     | auth and routed pages under `apps/web/src/`                    | `016`, boundary refined by `022`              | build, i18n audit, product-boundary and API contract tests                                                    |
| Generated reference               | Web catalog/data-model/CLI reference modules                   | `007`, `016`                                  | application-catalog and HTTP-boundary tests                                                                   |

Private helpers within these modules are implementation detail. They are covered through
their public family and are not separate capabilities.

## Executable Proof Ownership

| Test family                                                                                           | Primary baseline or authority                                                      | Coverage note                                                                                                                                                               |
| ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `packages/reality-core/tests/test_user_access.py`                                                     | `003`                                                                              | Active auth/access proof                                                                                                                                                    |
| `packages/reality-core/tests/test_tenant_lifecycle.py`                                                | `003`                                                                              | Archive/restore/delete proof                                                                                                                                                |
| `packages/reality-core/tests/test_tenancy.py`                                                         | `003`                                                                              | Cross-tenant domain proof                                                                                                                                                   |
| `packages/reality-core/tests/tenant_isolation/test_families.py`                                       | `003/FR-012`, Spec 019                                                             | Two-tenant proof for every catalogued isolation class and registry drift                                                                                                    |
| `packages/reality-core/tests/test_cli_context.py`                                                     | `003`                                                                              | Tenant context/ambiguity proof                                                                                                                                              |
| `packages/reality-core/tests/test_email_delivery.py`                                                  | `003`                                                                              | Account-mail provider boundary                                                                                                                                              |
| `packages/reality-core/tests/test_verification_email_return.py` | `190` | Verification email return URL and explicit-code boundary |
| `packages/reality-core/tests/test_payment_terms.py`                                                   | `004`                                                                              | Payment-term lifecycle/validation                                                                                                                                           |
| `packages/reality-core/tests/test_master_data_parity.py`                                              | `004/FR-016`, Spec 026                                                             | Master-data adapter matrix, canonical-state, and drift proof                                                                                                                |
| `packages/reality-core/tests/test_pricing.py`                                                         | `004`                                                                              | Deterministic pricing; history gap retained                                                                                                                                 |
| `packages/reality-core/tests/test_operational_fields.py`                                              | `004`                                                                              | Proven typed fields/constraints                                                                                                                                             |
| `packages/reality-core/tests/test_source_ingestion.py`                                                | `005`                                                                              | Generic/artifact/file ingestion                                                                                                                                             |
| `packages/reality-core/tests/test_interpretation_coverage.py`                                         | Spec 045                                                                           | Immutable attempt outcomes, produced-record identities, classification, retry, MCP, and tenant proof                                                                        |
| `packages/reality-core/tests/test_integrations.py`                                                    | `005`                                                                              | Source registry/intake UI API                                                                                                                                               |
| `packages/reality-core/tests/test_import_demo_files.py`                                               | `005`                                                                              | Explicit file-profile story                                                                                                                                                 |
| `packages/reality-core/tests/test_shopify_and_explain.py`                                             | `005`, `013`                                                                       | Shopify plus source explanation                                                                                                                                             |
| `packages/reality-core/tests/test_shopify_update_guard.py`                                            | Spec 081                                                                           | Shopify update preservation, explicit review, retry, batch and HTTP behavior                                                                                                |
| `packages/reality-core/tests/test_document_corrections.py`                                            | `006`                                                                              | Header/source correction; line gap retained                                                                                                                                 |
| `packages/reality-core/tests/test_documents.py`                                                       | `077`                                                                              | Stated amounts recorded, never calculated                                                                                                                                   |
| `packages/reality-core/tests/test_returns.py`                                                         | `079`                                                                              | Goods coming back name the delivery they reverse                                                                                                                            |
| `packages/reality-core/tests/test_credit_notes.py`                                                    | `084`                                                                              | Credit notes post, net and refund                                                                                                                                           |
| `packages/reality-core/tests/test_commitment_revisions.py`                                            | `093`, `097`                                                                       | A counterparty's new date is recorded without erasing the old one, and one statement may restate the quantity as well                                                       |
| `packages/reality-core/tests/test_stale_promises.py`                                                  | `085`                                                                              | Previewing and closing promises an import left behind                                                                                                                       |
| `packages/reality-core/tests/test_payment_runs.py`                                                    | `098`                                                                              | What is worth paying now, and paying it all at once or not at all                                                                                                           |
| `packages/reality-core/tests/test_return_announcements.py`                                            | `099`                                                                              | A customer's announced return, and the parcel that names it                                                                                                                 |
| `packages/reality-core/tests/test_return_announcement_adapters.py`                                    | `099`                                                                              | The announcement and the resolution references reach MCP, web and CLI (099 amendment)                                                                                       |
| `packages/reality-core/tests/test_reference_integrity.py`                                             | `100`                                                                              | The references the queue leans on, and the paths and surfaces that can set them                                                                                             |
| `packages/reality-core/tests/operational_exceptions/test_derivation.py`                               | `107`                                                                              | A hold nobody lifted, on a promise or on a whole counterparty                                                                                                               |
| `packages/reality-core/tests/test_commitment_holds.py`                                                | `008`, `108`                                                                       | Promise/document convenience holds, and a hold never outliving its promise                                                                                                  |
| `packages/reality-core/tests/test_inventory_tracking_reservations.py`                                 | `009`, `109`, `110`                                                                | Lot/serial allocations and tools, the best-before date a lot carries, and correcting a misread one                                                                          |
| `packages/reality-core/tests/test_party_delivery_holds.py`                                            | `008`                                                                              | Customer delivery hold scope                                                                                                                                                |
| `packages/reality-core/tests/test_inventory_and_fulfillment.py`                                       | `008`, `009`                                                                       | Fulfilment/inventory core story                                                                                                                                             |
| `packages/reality-core/tests/test_movement_corrections.py`                                            | Spec 023                                                                           | Append-only Movement void/replacement, retry, audit, and tenant proof                                                                                                       |
| `packages/reality-core/tests/test_handling_units.py`                                                  | `009`                                                                              | Optional pallet/NVE behavior                                                                                                                                                |
| `packages/reality-core/tests/scenarios/test_order_to_cash.py`                                         | `010`                                                                              | Customer end-to-end story                                                                                                                                                   |
| `packages/reality-core/tests/scenarios/test_procure_to_pay.py`                                        | `011`                                                                              | Supplier end-to-end story                                                                                                                                                   |
| `packages/reality-core/tests/test_ledger.py`                                                          | `012`                                                                              | Balanced postings/settlement/registers                                                                                                                                      |
| `packages/reality-core/tests/test_finance_payment_atomicity.py`                                       | `096 FR-017`                                                                       | Durable customer-payment rollback and confirmed-action event attribution                                                                                                    |
| `packages/reality-core/tests/test_ledger_reversals.py`                                                | Spec 024                                                                           | Whole-group exact inverse, immutable allocation history, retry, audit, and tenant proof                                                                                     |
| `packages/reality-core/tests/test_business_events.py`                                                 | `013`                                                                              | Transactional ordered events                                                                                                                                                |
| `packages/reality-core/tests/test_materialized_projections.py`                                        | `013`                                                                              | Refresh/checkpoint/stale rows                                                                                                                                               |
| `packages/reality-core/tests/test_application_tools.py`                                               | `013`, `014`                                                                       | Read tools and confirmed mutations                                                                                                                                          |
| `packages/reality-core/tests/operational_exceptions/test_coverage.py`                                 | `013/FR-005`, Spec 020, Specs 068 and 071                                          | Closed class/cause taxonomy, shared-cause vocabulary, operator-guidance completeness, and registry/order drift proof                                                        |
| `packages/reality-core/tests/operational_exceptions/test_derivation.py`                               | `013/FR-005`, Spec 020, Specs 068, 069 and 072                                     | Tenant-scoped derivation, ordering, single-entry, learned-rhythm and clearing proof for every class                                                                         |
| `packages/reality-core/tests/operational_exceptions/test_explanation.py`                              | `013/FR-005`, Spec 020, Spec 068                                                   | Shared-consumer explanation parity and class-transition identity proof                                                                                                      |
| `packages/reality-core/tests/test_chat_confirmation.py`                                               | `014`, `015`                                                                       | Chat proposals and shared demos                                                                                                                                             |
| `packages/reality-core/tests/test_chat_master_data.py`                                                | `014`, Spec 038                                                                    | Confirmed Party, Item, and Location proposal, batch, provenance, and tenant proof                                                                                           |
| `packages/reality-core/tests/test_chat_master_data_updates.py`                                        | Spec 041                                                                           | Confirmed Party, Item, and Location update previews, stale guards, atomicity, and proposal-event linkage                                                                    |
| `packages/reality-core/tests/test_master_data_update_audit.py`                                        | Spec 041                                                                           | Exact normalized before/after diffs, no-op behavior, rollback, lifecycle, and immutable source-version proof                                                                |
| `packages/reality-core/tests/test_ai_mcp.py`                                                          | `014`                                                                              | Secrets/tokens/MCP permission boundary                                                                                                                                      |
| `packages/reality-core/tests/test_agent_command_parity.py`                                            | Spec 042                                                                           | Canonical command classification, strict schema, and Chat/MCP registry parity                                                                                               |
| `packages/reality-core/tests/test_mcp_read_contract.py`                                               | Spec 145                                                                           | Currency separation, ledger direction, units, locations, closed orders, scoped traversal and no-write diagnostics                                                           |
| `packages/reality-core/tests/test_agent_discovery.py`                                                 | Spec 042                                                                           | Bounded tenant-scoped discovery and opaque identity proof                                                                                                                   |
| `packages/reality-core/tests/test_capability_guidance.py`                                             | Specs 044, 047, 048                                                                | Complete public proposal/read guidance, shared lookup, verification boundaries, and registry drift proof                                                                    |
| `packages/reality-core/tests/test_chat_mcp_business_commands.py`                                      | Spec 042                                                                           | Proposal/approval stories across warehouse, pricing, finance, source, and membership command families                                                                       |
| `packages/reality-core/tests/test_chat_mcp_orders.py`                                                 | Spec 042                                                                           | Sales/purchase order Source-to-Evidence-to-Commitment proposal stories                                                                                                      |
| `packages/reality-core/tests/test_mcp_chat.py`                                                        | `014`, Spec 038                                                                    | Copilot prompt and provider-derived master-data tool-schema proof                                                                                                           |
| `packages/reality-core/tests/test_fact_observation.py`                                                | Spec 043                                                                           | Source-required, cataloged, idempotent, tenant-scoped Fact observation and atomic event proof                                                                               |
| `packages/reality-core/tests/test_mcp_fact_observation.py`                                            | Spec 043                                                                           | Confirmed MCP/Chat Fact proposal and shared application-tool proof                                                                                                          |
| `packages/reality-core/tests/test_reality_gaps.py`                                                    | Spec 067                                                                           | Tenant-scoped capture, investigation, safe Fact-rule simulation, activation, replay, and provenance proof                                                                   |
| `packages/reality-core/tests/test_reality_gap_tools.py`                                               | Spec 067                                                                           | Shared application-tool and complete MCP proposal/read surface proof                                                                                                        |
| `packages/reality-core/tests/test_reality_gap_rules.py`                                               | Spec 067                                                                           | Closed conditional evaluation, output modes, effective time, line resolution, conflicts, and resumable replay proof                                                         |
| `packages/reality-core/tests/test_chat_scope_security.py` | `197` | Shared scope policy, forged history roles, hostile tool data and model confirmation denial |
| `packages/reality-core/tests/test_anthropic_copilot.py`                                               | `037`                                                                              | Managed Anthropic Messages API and canonical tool-use boundary                                                                                                              |
| `packages/reality-core/tests/test_mcp_http_runtime.py`                                                | `018`                                                                              | Separate authenticated HTTP-only MCP runtime, health/readiness, and tool parity                                                                                             |
| `packages/reality-core/tests/scenarios/test_normal_month.py`                                          | `015`                                                                              | Deterministic/idempotent scenario                                                                                                                                           |
| `packages/reality-core/tests/test_bootstrap.py`                                                       | `015`                                                                              | Explicit configured bootstrap                                                                                                                                               |
| `packages/reality-core/tests/test_demo_entrypoint_parity.py`                                          | `015/FR-010`, Spec 027                                                             | Guided-demo real-entrypoint manifest, safety, and drift proof                                                                                                               |
| `packages/reality-core/tests/test_cli.py`                                                             | Owning baselines + `016`                                                           | CLI adapter equivalence evidence                                                                                                                                            |
| `packages/reality-core/tests/test_master_data_api.py`                                                 | `004`, `006`, `013`, `014`, `016`                                                  | Public API/React contract evidence                                                                                                                                          |
| `packages/reality-core/tests/test_web_ux_reads.py`                                                    | `016/FR-006`, Spec 030                                                             | Tenant-scoped Journal totals, filters, inspection, and foreign-boundary proof                                                                                               |
| `packages/reality-core/tests/test_large_tenant_register_contract.py`                                  | `016/FR-015`, Spec 033                                                             | Reduced/full profile contract, nine-family bounded reads, stable paging, tenant sentinels, and result-schema proof                                                          |
| `packages/reality-core/tests/test_inspector_presentation.py`                                          | Spec 138 FR-028                                                                    | Typed numeric presentation, raw values and identifiers, currency, historical precision and foreign record isolation                                                         |
| `packages/reality-core/tests/test_inspector_register.py`                                              | Spec 138 FR-027                                                                    | Full record-family paging, search, summary bounds, tenant isolation and HTTP validation                                                                                     |
| `packages/reality-core/tests/test_http_boundary.py`                                                   | `007`, `016`                                                                       | API boundary and generated-catalog evidence                                                                                                                                 |
| `packages/reality-core/tests/test_application_catalog.py`                                             | `007`                                                                              | Executable vocabulary drift proof                                                                                                                                           |
| `packages/reality-core/tests/test_data_model.py`                                                      | Data Model, Spec 035                                                               | Access model/catalog parity and shortest-link proof                                                                                                                         |
| `packages/reality-core/tests/test_playground_runs.py`                                                 | `096/FR-001`, `096/FR-002`, `096/FR-003`, `096/FR-011`, `096/DR-003`, `096/DR-004` | Storage constraints; owner-locked atomic reference setup, concurrent/idempotent start, failure recovery, archive safety and run quotas; no public entry yet                 |
| `packages/reality-core/tests/test_playground_security.py`                                             | `096/FR-003`                                                                       | Owner resolver, catalogued core writes, generic proposals/lifecycle, rule/upload and egress boundaries, CLI/MCP/HTTP denial; complete entrypoint audit remains pending      |
| `packages/reality-core/tests/test_playground_api.py`                                                  | `096/FR-001`, `096/FR-002`, `096/FR-003`, `096/FR-011`                             | Authenticated start/replay and setup failure, bounded private history, strict confirmation, quotas, session/membership checks, generic inspection and production separation |
| `packages/reality-core/tests/test_playground_chat.py`                                                 | `106/FR-003`, `106/FR-004`                                                         | Owner-scoped read-only companion, bounded input, managed provider failure and mutation dispatch rejection                                                                   |
| `packages/reality-core/tests/test_playground_steps.py`                                                | `096/FR-005`                                                                       | Confirmed V1 action attribution, shipment consumption/remainder/fulfilment, repeat confirmation, transaction rollback and foreign action rejection                          |
| `packages/reality-core/tests/test_storyline_package.py`                                              | `182/FR-002`, `182/FR-017`, `182/FR-019`, `182/SC-004`, `182/SC-008`                | Storyline package contract: shape, catalog names, symbolic references, dominator rule for chapter references, bounds, collected errors, built-in validation, catalog labels            |
| `packages/reality-core/tests/test_storyline_trace.py`                                                | `182/FR-004`                                                                       | Storyline call trace: dispatcher wrappers for reads and proposals, markers on confirmation, chapter scope, entry and run bounds, view middleware, tenant scope                          |
| `packages/reality-core/tests/test_storyline_delta.py`                                                | `182/FR-005`                                                                       | Delta primitives: forward timeline read after a marker, cursor exclusivity, Fact recording order independent of business time                                                          |
| `packages/reality-core/tests/test_storyline_runs.py`                                                 | `182/FR-001`, `182/FR-003`, `182/FR-005`, `182/FR-009`, `182/FR-010`, `182/FR-011`, `182/FR-012` | Storyline runs: seeded practice company, atomic seed failure, chapters through the ordinary proposal path, refused preparation as outcome, derived chapter state, branches, reject and retry, restart, library, tool reference, free play with its own marker and delta, blocked chapter names the missing finding |
| `packages/reality-core/tests/test_storyline_library_api.py`                                          | `182/FR-001`, `182/FR-003`, `182/FR-004`, `182/FR-005`, `182/FR-007`, `182/FR-018`  | Storyline HTTP surface: library and start, chapter prepare and confirm, trace, delta, tool reference, owner privacy and cookie requirement, error mapping                              |
| `packages/reality-core/tests/scenarios/test_storyline_first_round.py`                                | `182/FR-009`, `182/FR-014`, `182/SC-002`                                            | First round, the short introduction, played end to end: a rule raises a finding no command wrote, the same rule clears it once the remainder is reserved, a refused dispatch writes nothing, the read chapter writes nothing, the story ends on one open finding, every event after the seed in exactly one chapter's delta |
| `packages/reality-core/tests/scenarios/test_storyline_order_to_close.py`                            | `182/FR-009`, `182/FR-010`, `182/FR-014`, `182/SC-002`                              | Order to close played end to end through the service: default path and both alternative paths, expected against observed findings, refused dispatch, read chapters, every event after the seed in exactly one chapter's delta      |
| `packages/reality-core/tests/scenarios/test_storyline_purchase_to_pay.py`                           | `182/FR-009`, `182/FR-010`, `182/FR-014`, `182/SC-002`                              | Purchase to pay played end to end: short delivery, invoice over quantity and price, duplicate invoice booked and reversed, discount taken on the record; credit branch pays less and keeps the quantity finding; every event after the seed in exactly one chapter's delta |
| `packages/reality-core/tests/test_storyline_export.py`                                               | `182/FR-021`, `182/SC-009`                                                          | Run exported as a storyline draft: seed identities as `$ref`, created records as `$chapter`, dates as offsets, texts marked missing, story chapters keep their texts, unsupported commands in place, the filled draft imports and plays, draft route                     |
| `packages/reality-core/tests/test_playground_practice_companies.py`                                   | `104/FR-001`, `104/FR-002`, `104/FR-003`, `104/FR-004`, `104/DR-001`, `104/DR-002` | Named isolated setup, retry validation, persistent lifecycle and temporary replacement                                                                                      |
| `packages/reality-core/tests/test_playground_free_operations.py`                                      | `103/FR-003`, `103/FR-004`, `103/FR-005`, `103/DR-002`                             | Selected target response, remaining-quantity freshness and interleaved sales/purchase/partial fulfillment in one sandbox                                                    |
| `packages/reality-core/tests/test_playground_release.py`                                              | `103/FR-012`                                                                       | Reviewed exact reservation release, rejection, stale and missing target refusal, repeat confirmation and unchanged stock/obligation                                         |
| `packages/reality-core/tests/test_playground_master_data.py`                                          | `103/FR-013`                                                                       | Shared Party/Item/Location creation and editing, rejection, stale/foreign/extra input refusal, exact execution scope and repeated confirmation                              |
| `packages/reality-core/tests/test_playground_shipment_recovery.py`                                    | `103/FR-008`, `103/FR-005`                                                         | Pre-claim overdelivery rejection, proven unapplied legacy discard and refusal of uncertain execution                                                                        |
| `packages/reality-core/tests/test_master_data_api.py`, `apps/web/scripts/playground-free-browser.mjs` | `103/FR-007`                                                                       | Outstanding financial filter retains partial amounts, removes paid items, and supports separate central registers with inspection                                           |
| `packages/reality-core/tests/test_membership_invitations.py`                                          | Spec 035                                                                           | Owner authorization, invitation lifecycle, explicit acceptance, and membership reactivation proof                                                                           |
| `packages/reality-core/tests/test_platform_admin_overview.py`                                         | `003`, Spec 036                                                                    | Platform-admin authorization, platform metadata content, secret-presence disclosure limit, and migration-drift proof                                                        |
| `packages/reality-core/tests/test_migrations.py`                                                      | Data Model/ADRs                                                                    | Schema construction/backfill proof                                                                                                                                          |
| `packages/reality-core/tests/test_postgresql_integration.py`                                          | PostgreSQL ADR                                                                     | Integration proof; environment-dependent skip is not sole feature proof                                                                                                     |
| `packages/reality-core/tests/test_database_config.py`                                                 | PostgreSQL ADR                                                                     | PostgreSQL-only configuration proof                                                                                                                                         |
| `packages/reality-core/tests/test_spec_policy.py`                                                     | `001-baseline-spec-coverage`                                                       | Baseline structure and deterministic coverage regression proof                                                                                                              |
| `packages/reality-core/tests/test_repository_layout.py`                                               | `021-deployable-app-layout`, `022-public-site`                                     | Deployable-root, shared-core, Site/Web split, Compose, CI and command-path regression proof                                                                                 |

The browser apps have focused Node contract tests but no component-test family. Their
current gates include locked builds, Product Web i18n audit, and
`scripts/visual_audit.py`; corresponding backend localization, UX-matrix, and
large-tenant read proofs are owned by Specs 017, 030, and 032.

## Exclusions

| Source family                                                | Reason                                                                |
| ------------------------------------------------------------ | --------------------------------------------------------------------- |
| Generated bundles, caches, bytecode, `.venv`, `node_modules` | Build/runtime by-products                                             |
| Fixtures without behavior assertions                         | Test data, owned through the test that interprets it                  |
| Private helper functions                                     | Implementation detail exercised through a public family               |
| Deployment-only files and third-party notices                | Operational/legal support, not independent business capability        |
| `007-core-catalogs` from the thirteen baseline count         | Independent reviewed change spec, retained as cross-cutting authority |

## Representative Future-Change Drill

**Change**: Allow an operator to correct an existing manual DocumentLine.

1. Start at this matrix: `document` and `document_line` are owned by
   [`006-documents-evidence`](../specs/006-documents-evidence/spec.md).
2. Locate `006/FR-008`, which records the missing correction path as a Documented gap.
3. Read Constitution principles I–V, `docs/DATA_MODEL.md`, and the Web Document contract.
4. Create a new numbered change spec before code. Decide replacement versus compensating
   Evidence, downstream Reality locking, audit event, tenant scope, and Web confirmation.
5. Plan tests before implementation, including no mutation of immutable SourceRecords,
   no silent rewrite after dependent Reality, and Source → Evidence → Reality explanation.

The governing baseline and cross-cutting contracts are discoverable from this page
without reading implementation first.

## Maintenance Gate

Run:

```bash
make spec-check
cd packages/reality-core && ../../.venv/bin/pytest -q tests/test_spec_policy.py
```

The policy validates the thirteen baseline paths, required sections/status metadata,
feature-contract entries, catalog-table entries, and backend-test-family entries. Update
this matrix whenever any included source is added, removed, renamed, or reassigned.

## Final Verification Record

| Gate                     | Result                    | Evidence                                                                                                                                                                             |
| ------------------------ | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Baseline review          | PASS                      | Thirteen capability baselines are `Reviewed` with owner decisions dated 2026-08-31                                                                                                   |
| Coverage policy          | PASS                      | `make spec-check`                                                                                                                                                                    |
| Policy regression        | PASS                      | Included in the complete PostgreSQL suite and `make spec-check`                                                                                                                      |
| Backend lint             | PASS                      | `make lint`                                                                                                                                                                          |
| PostgreSQL suite         | PASS                      | 251 passed, 7 skipped; skipped tests are not sole proof for Verified requirements                                                                                                    |
| Browser builds           | PASS                      | `make web-build`                                                                                                                                               |
| Translation audit        | PASS                      | Product Web audit covers 717/717 strings for `en`, `de`, `nl`, and `es`, with zero missing or invalid entries; 35/35 focused Product Web contract tests pass                         |
| Diff formatting          | PASS                      | `git diff --check`                                                                                                                                                                   |
| Product/schema isolation | PASS for baseline outputs | Outputs remain within the roots recorded in `specs/001-baseline-spec-coverage/baseline-starting-state.md`; pre-existing/concurrent product changes remain outside baseline ownership |

Final inventory: 13 capability baselines, 24 feature contracts, 50 catalog tables,
48 backend test families, 229 Functional Requirements, 79 Domain Requirements,
119 Success Criteria, and no accepted Documented gaps.

## Unified application foundation (139)

| Test family                                                    | Specification | Proof                                                                                       |
| -------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------- |
| `packages/reality-core/tests/test_unified_delivery_reads.py`   | `139`         | Effective delivery quantities, partial/final shipment, tenant isolation and bounded history |
| `packages/reality-core/tests/test_unified_app_api.py`          | `139`         | Shared delivery HTTP contracts and honest dashboard sample scope                            |
| `packages/reality-core/tests/test_unified_delivery_actions.py` | `139`         | Exact reviewed action authority, stale state and idempotent execution                       |

## Unified analytics and references (140)

| Test family                                                 | Spec  | Coverage                                                                  |
| ----------------------------------------------------------- | ----- | ------------------------------------------------------------------------- |
| `packages/reality-core/tests/test_company_insights.py`      | `140` | Defined current metrics, bounded contributors, UTC and corrected activity |
| `packages/reality-core/tests/test_reference_workspace.py`   | `140` | Reference roles, preservation, stale edits and canonical proposal replay  |
| `packages/reality-core/tests/test_unified_workspace_api.py` | `140` | Scoped Analytics and Master data HTTP contracts                           |

## Spec 161 — Complete master data fields

- `packages/reality-core/tests/test_reference_workspace.py`: FR-001, FR-002, FR-003, FR-005; full-field create/update per family, omitted-field preservation, register role guard, invalid values without a proposal, provenance and detail codes.
- `packages/reality-core/tests/test_unified_workspace_api.py`: FR-001, FR-003; typed JSON field values over HTTP and named rejections.
- `unified-app-contract.test.mjs`, `unified-workspaces-browser.mjs`: FR-004; per-family field coverage, tenant-scoped choices, review labels and the widened edit flow.

## Spec 141 — Unified Warehouse and Attention

- `packages/reality-core/tests/test_unified_operations_api.py`: FR-002, FR-003, FR-005, FR-007; shared stock, exact-item pagination, correction history, tenant scope and read-only effects.
- `packages/reality-core/tests/test_attention_reads.py`: FR-004, FR-005, FR-007; canonical derivation/order, filtering, target identity and resolved/foreign findings.
- `unified-app-contract.test.mjs`, `unified-operations-browser.mjs`: FR-001, FR-005, FR-006, FR-007, FR-008; unified routes, traversal, URL recovery, failures, localization and responsive/keyboard behavior.

## Spec 142 — Unified Finance

- `packages/reality-core/tests/test_master_data_api.py`: reused financial API tenant/currency isolation, outstanding filtering before paging and complete controls (FR-002, FR-003, FR-006).
- `packages/reality-core/tests/test_web_ux_reads.py`: reused journal account/tenant filtering, totals and Inspector (FR-004, FR-005).
- `packages/reality-core/tests/test_ledger_reversals.py`: authoritative reversal and settlement semantics retained by Finance (FR-003, FR-005).
- `apps/web/scripts/unified-app-contract.test.mjs`, `apps/web/scripts/unified-finance-browser.mjs`: FR-001–FR-007; routes, paging, controls, filters, Inspector, company reset and localized responsive read-only navigation.

## Spec 111 — Unified Data and Sources

- `packages/reality-core/tests/test_unified_source_api.py`: FR-002–FR-006; tenant-scoped metadata/counts/versions, SQL payload exclusion, exact-source evidence paging and no effects.
- `packages/reality-core/tests/test_source_ingestion.py`, `packages/reality-core/tests/test_interpretation_coverage.py`: existing immutable source and interpretation semantics retained.
- `apps/web/scripts/unified-app-contract.test.mjs`, `apps/web/scripts/unified-sources-browser.mjs`: FR-001, FR-004–FR-007; source-to-evidence traversal, payload safety, URL/company context and localized responsive read-only navigation.

## Spec 112 — Unified Settings

- `apps/web/scripts/unified-app-contract.test.mjs`: FR-001; route/section roundtrip and safe fallback.
- `apps/web/scripts/unified-settings-browser.mjs`: FR-001–FR-007; save payload/reload, immediate language update, independent locale, validation rejection, applied/unapplied unknown outcomes, failed recovery without duplicate PUT, appearance/header/OS synchronization, role isolation, company reset, retry, secret exclusion and48 visual combinations.
- Existing `packages/reality-core/tests/test_user_access.py`: reused account profile validation/persistence, scoped owner access and membership bounds (FR-002, FR-005).
- Existing `packages/reality-core/tests/test_master_data_api.py`: reused managed/company AI configuration contract (FR-006). No backend or schema change.

## Spec 113 — Unified Orders and Deliveries

- `packages/reality-core/tests/test_unified_orders_api.py`: FR-002–FR-004, FR-006; revised incoming quantities/dates, supplier identity and unit, correction-adjusted receipt/open history, exact multi-line/direct order links, tenant isolation, validated direction and evidence type before paging.
- Existing `test_unified_delivery_reads.py`, `test_unified_delivery_actions.py`: FR-002, FR-005; preserved customer cases, effective observations and durable reviewed actions.
- `apps/web/scripts/unified-app-contract.test.mjs`, `unified-orders-browser.mjs`: FR-001, FR-003–FR-007; typed URL state, order/customer/supplier traversal, shared Inspector/keyboard/reload, retry/empty/foreign/company reset and48 localized screenshots without writes.

## Spec 114 — Unified Facts

| Requirements         | Implementation                                                      | Evidence                                                                              |
| -------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| FR-001 FR-003 FR-007 | FactsPage, routing, Shell and localized original-content boundaries | unified-app-contract.test.mjs; unified-facts-browser.mjs                              |
| FR-002 FR-003 FR-006 | fact_reads metadata projection, tenant filters/count/paging         | `packages/reality-core/tests/test_unified_facts_api.py`                               |
| FR-004 FR-005        | Source → observations, related subject and shared fact Inspector    | test_unified_facts_api.py; test_master_data_api.py; browser and authenticated preview |

No schema or command changes. Overall rollout and legacy retirement remain separate.

## Spec 115 — Unified ERP table standard

- `packages/reality-core/tests/test_unified_table_queries.py`: FR-005/006; invalid sorts, global multi-page order,25/50/100 sizes, numeric projection/stock order and preserved totals.
- `apps/web/scripts/unified-table-contract.test.mjs`: FR-004/005; validated layout, user/variant isolation, bounded URL options and company reset.
- `apps/web/scripts/unified-tables-browser.mjs`: FR-001–FR-007;44/36px geometry, sticky header/key, visibility/resize persistence, SQL query parameters, row/keyboard navigation and24 localized responsive images.
- Existing unified workspace, operations, finance, sources, facts and orders browser journeys retain exact detail/action/confirmation and original-value evidence across the migrated views.

## Spec 116 — Unified receipt and reservation release

- `packages/reality-core/tests/test_unified_receipt_release.py`: FR-001–FR-004; partial receipt, full release, unchanged physical/open quantities, stale and foreign rejection, replay, event recovery, conflicting pool and HTTP/tool parity.
- `apps/web/scripts/unified-receipt-release-browser.mjs`: FR-001–FR-006; contextual and launcher entry, exact review, reload, confirmation, empty state and responsive layout.
- Existing delivery/order/warehouse browser journeys and full backend and frontend gates preserve earlier workflows.

## Spec 117 — Unified delivery holds

- `packages/reality-core/tests/test_unified_delivery_holds.py`: FR-001–FR-005; own/party scope, no stock effects, stale replacement, exact plural release, confirmation and actor checks, practice isolation, event recovery and HTTP/tool parity.
- `apps/web/scripts/unified-holds-browser.mjs`: FR-001–FR-006; case/global entry, reason/note, exact review, edit/reload/confirmation, retained party hold and localized responsive layout.

## Spec 118 — Unified movement corrections

- `packages/reality-core/tests/test_unified_movement_corrections.py`: FR-002–FR-006; read-only projected inverse/replacement validation, chains, serial/lot constraints, physical/open/reservation effects, stale and tenant/auth/practice rejection, bidirectional unresolved overlap, exact event recovery and HTTP/tool review.
- `apps/web/scripts/unified-corrections-browser.mjs`: FR-001/004/005/007; Warehouse/launcher/Chat/Decisions entries, preserved replacement references, reverse/quantity form, reload/edit/reject/confirmation and four-language responsive layouts.

## Spec 119 — Unified order entry

- `packages/reality-core/tests/test_unified_order_entry.py`: FR-002–FR-006; inert multi-line sales/purchase preview, source-stated totals, exact trace, stale/foreign/auth/practice, replay and unknown outcomes, same-number distinct agreements, duplicate payloads, directed creation snapshots, raw line metadata and historical proof after fulfillment.
- `apps/web/scripts/unified-order-entry-browser.mjs`: FR-001/003/005/006/007; shared entry points, line editing, reload/reject/confirm, recovery and localized responsive layouts.

## Unified invoice entry — Spec 120

- `packages/reality-core/tests/test_unified_invoice_entry.py`: FR-002–FR-005; inert preview, stated sales/purchase postings, quantity/billing limits, stale/foreign references, explicit confirmation, replay and exact unknown recovery.
- `apps/web/scripts/unified-invoice-entry-browser.mjs`: FR-001/FR-006/FR-007; Finance entry, selection, stated values, common proposal reload, response loss and four-language responsive review.

## Unified payment entry — Spec 121

- `packages/reality-core/tests/test_unified_payment_entry.py`: FR-002–FR-005; inert preview, partial/full customer/supplier settlement, exact financial receipts, source/tenant/type and exact storage-precision guards, stale and competing confirmation, historical reversal and HTTP review.
- `apps/web/scripts/unified-payment-entry-browser.mjs`: FR-001/FR-006/FR-007; invoice selection, exact decimal payment/balance review, four entry points, edit/reject, reload/recovery and localized responsive views.

## Multi-position invoices — Spec 122

- `packages/reality-core/tests/test_multi_position_invoices.py`: FR-002–005; both directions, independent stated values, atomicity, invalid/foreign/billed positions, stale second line, concurrent legacy/multi overlap, exact plural receipt and recovery. Existing `test_unified_invoice_entry.py` retains single-position and HTTP compatibility proofs.
- `apps/web/scripts/unified-invoice-entry-browser.mjs`: FR-001/006; add/remove positions, independent amounts, two-position edit/reload, common entries/recovery and localized responsive review.

## Unified financial reversal — Spec 123

- `packages/reality-core/tests/test_unified_financial_reversal.py`: FR-001–005; scoped choices, customer/supplier invoice/payment effects, active/inactive allocations, exact attribution/recovery, stale counterpart, concurrent payment/reversal, current actor/practice, rollback and malformed proof.
- `apps/web/scripts/unified-financial-reversal-browser.mjs`: FR-001/006; choice/reason form, before/after effects, Finance/Actions/Chat/Decisions, edit/reject/reload/response loss and localized responsive review.

## Partial invoicing and rebilling — Spec 124

- `packages/reality-core/tests/test_partial_invoicing_rebilling.py`: FR-001–004/006; partial/remainder/reversal/rebilling in both directions, historical proof, unposted/multiple groups, payment/credit distinction, excess evidence, exact fractional quantities, stale review with remaining capacity, independent concurrent writers and tenant-scoped Inspector HTTP.
- `apps/web/scripts/unified-invoice-entry-browser.mjs` and `unified-financial-reversal-browser.mjs`: FR-005; available quantities, exhausted choices, remaining review, reversal availability and common localized responsive flows.
- Existing invoice, multi-position and reversal suites retain atomicity, legacy receipt, response-loss and source linkage proofs.

## Invoice-linked customer credits — Spec 125

- `packages/reality-core/tests/test_unified_invoice_credit.py`: FR-001–004; independent invoice capacity, legacy ambiguity/unposted credit, partial multi-position no-return credit, explicit netting/paid invoices, precision/foreign/mixed/excess/stale/concurrent input, atomic failure and exact historical recovery.
- `apps/web/scripts/unified-credit-entry-browser.mjs`: FR-005; invoice selection, position/quantity entry, independent stated amounts, explicit balance review, four entry points, edit/reject/reload/response loss and localized responsive views.
- Existing invoice, reversal, exception and Playground suites retain previous behavior; the application catalog declares the new event and existing command inputs.

## Customer refunds from open credits — Spec 126

- `packages/reality-core/tests/test_unified_customer_refund.py`: FR-001–005/007, DR-001–003; partial and complete repayment, exact stated precision, original source and inspectable receipt, tenant/type/empty boundaries, credit register search/sort/pagination/totals, stale netting/reversal, both-endpoint capacity, independent concurrent refund/netting, atomic rollback, exact recovery and historical proof after reversal, HTTP prepare/confirm/read.
- `apps/web/scripts/unified-refund-entry-browser.mjs`: FR-002/006/007; selected-credit Finance action, launcher, Chat and Decisions, partial balance review, edit/reject/reload/lost response and four-language responsive light/dark layouts.
- Existing payment, credit, reversal, settlement and Playground suites guard adjacent behavior. No event family, database schema or bank integration is added.

## Complete unified business journey — Spec 127

- `packages/reality-core/tests/test_unified_business_journey.py`: FR-001–004, DR-001/002; linked order/reservation/partial shipment/invoice/payment/credit/partial-or-full refund/reversal through shared reviewed tools; no-effect preparation, replay, source values and shortest links.
- `packages/reality-core/tests/browser/unified_business_journey.py` and `apps/web/scripts/unified-business-journey-browser.mjs`: real migrated disposable PostgreSQL database, dedicated API/Vite processes, ordinary owner login and actual unified forms; persisted receipts, balances and Inspector proof. Invoked explicitly because it requires installed browser tooling.
- FR-005: journey failure artifacts identify bounded defects; repairs and their regression evidence are recorded in Spec 127 quickstart before completion.

## Unified company and member administration — Spec 128

- `apps/web/scripts/unified-company-access-browser.mjs`: FR-001–005; stateful intercepted HTTP covering no-company entry, reviewed empty creation, double-submit prevention, duplicate-name recovery, create rejection and failed post-create bootstrap, invitation review/cancel/resend/revoke/remove, pending versus delivery state, expired resend, member/owner gating, unknown-result and failed-read recovery, context switch, exact invitation acceptance tenant, four languages and responsive dark review.
- `apps/web/scripts/unified-settings-browser.mjs`: existing profile/theme/error/owner-boundary and light/dark responsive regressions.
- `apps/web/scripts/unified-app-contract.test.mjs`: company settings URL round-trip.
- `packages/reality-core/tests/test_membership_invitations.py` and `packages/reality-core/tests/test_user_access.py`: existing PostgreSQL service/HTTP authorization, invitation acceptance, owner protection, expiration, cooldown/limits, duplicates, company creation and membership isolation. Product backend is unchanged; full suite remains required.

## Reviewed new-item CSV import — Spec 129

- `packages/reality-core/tests/test_unified_item_csv_import.py`: FR-001–007; bounded lossless files, explicit mapping/defaults, whole-file validation, stale/duplicate/foreign input, atomic failure, independent concurrent imports and direct creation, exact action receipt/recovery, tenant-scoped HTTP upload/download and legacy item worker replay/retry.
- `packages/reality-core/tests/browser/unified_item_csv_import.py` and `apps/web/scripts/unified-item-import-browser.mjs`: FR-001–006; real ordinary-member login, uploaded BOM/semicolon file, mapping, lost prepare and confirmation responses, bookmarked review/result, byte-exact attachment download, item Inspector, rejected import, foreign access and four-language mobile/desktop dark layouts. Dedicated API/Vite and disposable migrated PostgreSQL; explicit browser invocation.
- Existing source/file suites and source browser retain evidence navigation and other profile behavior. Full backend suite guards the shared item creation serialization and source commit boundary.

## Unified source definition management — Spec 130

- `apps/web/scripts/unified-source-configuration-browser.mjs`: FR-001–006; normalized reviewed registration, cancel, duplicate error, selected source/type flags, current-state uncertainty across reload and failed checks, opaque foreign selection, received-record navigation, 25-type pagination, single-flight submission and company switch during an outstanding write; four-language responsive dark layouts. Stateful intercepted API writes; no shared data changes.
- Existing `packages/reality-core/tests/test_master_data_api.py`, `test_unified_source_api.py`, `test_source_ingestion.py`, `test_user_access.py` and practice security suites retain canonical registry/ingestion and authorization semantics; backend is unchanged.
- `apps/web/scripts/unified-sources-browser.mjs` retains source/evidence navigation; explicit `packages/reality-core/tests/browser/unified_item_csv_import.py` proves actual adjacent file upload/review/confirmation/download against disposable PostgreSQL.

## Unified AI provider and MCP access — Spec 131

- `apps/web/scripts/unified-ai-access-browser.mjs`: FR-001–007; managed/Anthropic review, retain/replace/revoke key effects, error/URL/storage secret exclusion, unsupported stored-provider disclosure and fresh-key requirement, explicit read/propose/confirm scopes, one-time token, clipboard failure, exact-ID revocation, lost provider/create/revoke responses, persisted recovery and failed read, duplicate names, double-click prevention and in-flight company switch. Tool/token pagination, search without implicit permission expansion, empty token state, member gate and 16 localized responsive light/dark layouts. All writes intercepted with synthetic credentials.
- `apps/web/scripts/unified-settings-browser.mjs`: existing preference/theme/recovery, owner boundary, default credential-metadata exclusion and 48 localized settings layouts; fixture expanded to the existing full API shape.
- Existing `packages/reality-core/tests/test_ai_mcp.py`, `test_master_data_api.py`, `test_mcp_chat.py`, `test_mcp_http_runtime.py` and practice-security tests retain encrypted vault, owner/tenant, real runtime dispatch, exact allowlist and revocation evidence. Backend source/tests unchanged; full suite required.

## Reviewed opening stock — Spec 132

- `packages/reality-core/tests/test_unified_opening_stock.py`: FR-002–006; additive/replay/no-preview-effect, exact quantity and field guards, tracked/non-stocked/destination restrictions, stale stock/reference, foreign scope, canonical event/output receipt and recovery after later correction, legacy raw proposal compatibility and explicit Chat review, independent PostgreSQL concurrency, mutual unresolved reservation/correction overlap, unrelated pools, HTTP confirmation/principal/practice checks and rollback before commit.
- `apps/web/scripts/unified-opening-stock-browser.mjs`: FR-001/005–007; Warehouse/launcher/Chat/Decisions, empty bounded search, saved request recovery after lost preparation/reload, exact explicit confirmation, lost confirmation and recorded-result reconciliation without replay, historic reload/Inspector, rejection, company isolation, keyboard focus and 16 localized responsive light/dark reviews. Transport writes are intercepted; actual business effects are independently proved by PostgreSQL tests.
- Existing Warehouse/correction browser and full application/backend suites retain adjacent operations, general movement tool and practice semantics.

## Unified customer-wide delivery holds — Spec 133

- `packages/reality-core/tests/test_unified_customer_holds.py`: FR-002–006; reviewed no-effect placement/release, exact event and output proof, replay/request identity, same-reason release/reapply and customer-reference staleness, future shipment gating with reservations still allowed, individual hold preservation, raw general party compatibility, explicit Chat review, independent concurrent placement, mutual unresolved shipment overlap and correction blocking, multi-hold release recovery/history, rollback, foreign customer, HTTP confirmation and actor/practice boundaries.
- `apps/web/scripts/unified-customer-holds-browser.mjs`: FR-001/005–007; delivery case/master data/launcher/Chat/Decisions, customer paging/empty search, exact review and escaped notes, persisted lost preparation, lost release confirmation and reconciliation without replay, historical placement with different current hold state, reject/company/focus behavior and 32 localized responsive light/dark placement/release reviews. All writes intercepted.
- Existing party/delivery-hold tests, full backend and adjacent holds/opening/delivery browser suites retain reservation permission, current shipment gating and operational review behavior.

## Unified activity drawer — Spec 134

- `apps/web/scripts/unified-activity-browser.mjs`: FR-001..006; global entry from Facts/work, preserved route/input/focus, modal dismissal and nested Inspector, exact event/subject targets, escaped payload, unknown-event fallback, split-correlation pages and ID deduplication, older failure/retry, all occurrence windows, historical attention filter, obsolete-search and company-response rejection, empty/error/retry, GET-only transport, and 16 localized theme/viewport layouts.
- Existing `packages/reality-core/tests/test_business_events.py` and `test_unified_delivery_reads.py`: tenant-scoped event history, business context, recorded sequence cursor and bounded reads. No domain, service, tool, schema or API changes for this increment.
- Existing unified application/delivery browser suites protect adjacent navigation and reviewed actions; frontend contract/localization and complete PostgreSQL suites remain required.

## Compact shell and persistent chat — Spec 135

- `apps/web/scripts/unified-shell-chat-browser.mjs`: FR-001..005; 56px sticky header, compact navigation, Analytics/Reports order, persistent hidden/navigation draft, company remount, one global composer and 48 localized responsive/theme/open/closed layouts.
- Existing unified application/delivery browser proves contextual entry now opens the same dock, provider error retention, shared action review and recovery. Existing activity browser proves header/drawer/focus and tenant behavior.
- Frontend contracts/localization/build/format gates pass; domain, service, schema and API are unchanged. Backend baseline remains Spec 134.

## Reference-style chat composer — Spec 136

- `apps/web/scripts/unified-chat-composer-browser.mjs`: FR-001..005; flat message/table rendering, hidden history and selection/new-chat controls, Shift+Enter and explicit Enter submission, literal text attachment and unsupported/oversized/message-limit rejection, simulated browser dictation and hide teardown, unsupported browser explanation and retained draft on provider failure.
- Existing shell/chat, application/delivery and Activity browser gates protect tenant/draft continuity, contextual proposals, responsive layout and shared confirmation/recovery. Speech is simulated; no live microphone/provider or shared business mutation is used for acceptance.
- Frontend contracts/i18n/build/format and repository spec/lint checks apply. Core services and schema are unchanged; prior full backend baseline remains Spec 134.

## Spec 137 — Register workbench

FR-001..004: shared RegisterTable and five register pages; browser workspace/order/finance/facts/table acceptance, frontend contracts, localization and build. Current-page CSV export is read-only; no new service or schema. See specs/137-register-workbench/quickstart.md.

## Reality Inspector — Spec 138

FR-001..006: unified-inspector-browser.mjs covers route/catalog/record/graph navigation, rule creation and review lifecycle, ambiguity, tenant/member boundaries and 16 localized layouts. Shared shell/table suites, 132 frontend contracts, localization, build, formatting, lint and spec gates supplement acceptance. See specs/138-reality-inspector/quickstart.md for limits and evidence.

Spec 135 FR-008: unified-app-contract.test.mjs covers all audited exit components and replacement boundaries; unified-shell-chat-browser.mjs covers absent sidebar exits and sandbox-to-live recovery. Existing full unified application/delivery fixtures verify supported action/review continuity. See Spec 135 quickstart.

Spec 138 FR-001/007/008: Inspector browser covers four group destinations, context selection and graph/detail synchronization, retained tab routes/catalogs/lifecycle, 16 localized layouts; shell browser verifies group order in 48 layouts. Existing frontend gates remain applicable; see Spec 138 quickstart.

Spec 137 FR-005: unified-tables-browser checks toolbar/filter geometry and table controls; unified-workspaces-browser checks action-menu keyboard dismissal/focus and existing record forms; order/finance/facts fixtures cover tabs/filters/rows/errors and localized layouts. Existing action-entry fixtures now open the register menu. No business-service change.

## Legacy browser retirement

| Executable evidence                                                                                                                                                    | Requirements              | Boundary                                                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------- |
| `apps/web/scripts/entry-routing.test.mjs`, `apps/web/scripts/retirement-browser.mjs`, `apps/web/scripts/product-boundary.test.mjs`                                     | `143/FR-001`–`143/FR-006` | Sole app, known/unknown bookmarks, auth return safety, Playground retirement, no navigation writes |
| `packages/reality-core/tests/test_playground_api.py`, `packages/reality-core/tests/test_playground_security.py`, `packages/reality-core/tests/test_playground_runs.py` | `143/FR-004`              | Retained protected history/services and tenant isolation                                           |

Historical legacy/Playground source-shape and browser presentation tests were removed
with their screens in Spec 143. The historical entries above describe the original
acceptance evidence; current behavior is covered by the retained unified browser
suites and retirement tests. Backend sandbox/history tests remain executable.

### Profile menu follow-up

| Executable evidence                                                                         | Requirements               | Boundary                                                                                                              |
| ------------------------------------------------------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `apps/web/scripts/retirement-browser.mjs`, `apps/web/scripts/unified-app-contract.test.mjs` | `143/FR-007`, `143/FR-008` | Bottom profile menu, configured resources, logout failure/retry, separate personal/company settings and default route |

| Executable evidence                                                                                                                               | Requirements   | Boundary                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------------------------------- |
| retirement-browser company list, role guidance, cross-company management, token/provider separation and reload; unified-app-contract agents route | 143 FR-009/010 | Authorized bootstrap only; owner guard and existing confirmation APIs unchanged |

| retirement-browser focused company dialogs, unchanged workspace URL/current marker, target-scoped API reads and member denial | 143 FR-011 and FR-009 top-action clarification | Management never switches working context; creation modal restores focus |

| unified-orders-browser initial work selection, history length, mobile back, explicit unavailable ID and empty list | 143 FR-012 | Read-only initialization; existing scoped delivery API and explicit selections preserved |

| unified-orders-browser register/detail round trip and compatibility; retirement-browser Home/navigation | 143 FR-013 | No duplicate work list; existing scoped actions and filters retained |

## Spec 144 — Integration preparation catalog

| Requirement | Implementation                               | Verification                                                                                              |
| ----------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| FR-001–004  | IntegrationPreparation.tsx, UnifiedApp.tsx   | integrations-catalog-browser.mjs: provider selection, guided session drafts, isolation, errors, no writes |
| FR-005      | DataSourcesPage.tsx                          | unified-sources-browser.mjs: source/evidence navigation and existing register behavior                    |
| FR-006      | IntegrationPreparation.tsx, localization.tsx | Four-language audit, mobile/desktop/theme screenshots and keyboard focus checks                           |

Spec 144 FR-007: `RegisterTable.tsx` reuses the bottom footer for non-selectable registers; `unified-sources-browser.mjs` asserts one footer after the table in Received data and Documents.

Spec 144 FR-008: delivery_evidence source detail and DataSourcesPage navigation; test_unified_delivery_reads proves exact-source links, payload, limits and tenant isolation; unified-sources-browser proves two tabs, in-dialog record navigation, original payload and legacy document URLs.

## Local company setup and scheduling integration

| Artifact                                                           | Specification  | Proof                                                                                                    |
| ------------------------------------------------------------------ | -------------- | -------------------------------------------------------------------------------------------------------- |
| `docs/features/company-setup-demo.md`                              | Specs 146, 147 | Shared services and local integration contract                                                           |
| `docs/features/scheduled-jobs.md`                                  | Specs 146, 147 | Shared services and local integration contract                                                           |
| `docs/features/payment_matching.md`                                | Spec 168       | Payment intake and matching contract; customer side implemented                                          |
| `packages/reality-core/tests/test_demo_data_settlement_plan.py`    | Spec 168       | Settlement planner: weights, delays, stated amounts, payloads, normalisers                               |
| `packages/reality-core/tests/test_payment_intake.py`               | Spec 168       | Shared invoice/payment core, reference resolution, candidates, guard rails                              |
| `packages/reality-core/tests/scenarios/test_demo_order_to_cash.py` | Spec 168       | Order → invoice → payment story across all outcomes through public reads                                 |
| `packages/reality-core/tests/operational_exceptions/test_payment_differences_from_demo.py` | Spec 168 | Existing exception classes surface synthetic differences                              |
| `packages/reality-core/tests/test_company_setup.py`                | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_company_setup_api.py`            | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_company_setup_migration.py`      | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_company_setup_unified.py`        | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_data.py`                    | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_data_api.py`                | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_data_generator.py`          | Spec 146       | Reproducible synthetic order plan: Poisson burst size on the hourly demand curve, weighted customer pool |
| `packages/reality-core/tests/test_demo_data_intake.py`             | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_data_security.py`           | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_execution_profile.py`       | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_profile_history.py`         | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_invitation_cleanup.py` | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_job_migration.py`      | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_job_recovery.py`       | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_job_registry.py`       | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_job_timing.py`         | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_jobs.py`               | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_worker.py`             | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_worker_deployment.py`  | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/scenarios/test_international_demo.py` | Spec 146       | Canonical operations and source lineage                                                                  |

Spec 146 FR-026–028: `test_company_setup_unified.py`, `test_playground_api.py`, `test_company_insights.py`, `test_demo_data_intake.py`, `test_demo_data_api.py`; browser acceptance `apps/web/scripts/demo-live-browser.mjs` and `company-setup-unified-browser.mjs` cover compact Sandbox labeling, real-time import snapshots, preserved choices and safe controls.

| `packages/reality-core/tests/test_home_readiness.py` | Spec 149 | Volatile health freshness, private probes and scoped Home readiness |
| `docs/features/home-live-status.md` | Spec 149 | Home activity, volatile process readiness and portable deployment contract |

Spec146 FR-030: `test_company_setup_unified.py` verifies seeded Sandbox exception
register/detail against canonical findings; `test_playground_api.py` verifies the
same read surface through authorized HTTP. Existing attention and reference-workspace
regressions retain foreign-record isolation and mutation boundaries.

| `packages/reality-core/tests/test_activity_volume.py` | Spec149 FR-008–011 | Recorded-entity counts, duplicate suppression, intervals, coverage and scoped HTTP |

| `apps/web/scripts/unified-app-contract.test.mjs` | Spec 150 | Reload keeps the held answer, one shared read placeholder, register busy marking |

| `apps/web/scripts/unified-app-contract.test.mjs` | Spec 154 | One shared register empty state inside the table frame, no page-level empty branches |

## Operational read performance (spec 153)

| Contract       | Test family                                                        | Status                                                                                               |
| -------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| 153 FR-001–005 | `packages/reality-core/tests/test_operational_read_performance.py` | Verified on the integrated local stack; isolated PR verification is recorded in spec 153 quickstart. |

## Navigation read performance (spec 154)

| Contract       | Test family                                                          | Status                                                                |
| -------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------- |
| 154 FR-003–005 | `packages/reality-core/tests/test_payment_projection_performance.py` | Focused regressions pass; final suite and browser validation pending. |
| 154 FR-001–002 | `apps/web/scripts/localization-contract.test.mjs`                    | Real-catalog parity and bounded-scan regressions pass.                |

## Sandbox read parity (spec 155)

| Contract               | Test family                                               | Status                                                                                                                       |
| ---------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| FR-001–004, DR-001–003 | `packages/reality-core/tests/test_sandbox_read_parity.py` | Verified: 20 new cases, 94 focused passes, complete backend suite and deployed read-only demo probe; see spec155 quickstart. |
| FR-003                 | `packages/reality-core/tests/test_playground_api.py`      | Authenticated route matrix and existing lifecycle tests.                                                                     |

Daily work lists: spec `152-daily-work-lists`; queue ordering/filtering proof in `packages/reality-core/tests/test_daily_work_lists.py` and adapter proofs in `apps/web/scripts/daily-work-lists.test.mjs` and `apps/web/scripts/daily-work-browser.mjs`.

| Artifact                                               | Specification                         | Proof                                                                                                         |
| ------------------------------------------------------ | ------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `subledger_account`                                    | `148-accounting-journal-cost-centers` | Allowed account identity, role and lifecycle                                                                  |
| `finance_role_destination`                             | `148-accounting-journal-cost-centers` | One permitted default per role                                                                                |
| `finance_state`                                        | `148-accounting-journal-cost-centers` | Transaction coordination revision, no monetary authority                                                      |
| `packages/reality-core/tests/finance/test_accounts.py` | `148-accounting-journal-cost-centers` | Clean schema, tenant isolation, confirmation, original-account settlement, inverse and concurrent consumption |

This is the first implementation slice; it does not mark the entire finance specification complete.

| `packages/reality-core/tests/finance/test_active_stack_stories.py` | `148-accounting-journal-cost-centers` | Source-backed customer/supplier cutover stories |

| `packages/reality-core/tests/finance/test_available_credits.py` | Spec 148 FR-039/FR-040/FR-042 | Symmetric available-credit reads, allocation endpoints, refunds/reversals, tenant isolation and HTTP |

| `packages/reality-core/tests/finance/test_adjustments.py` | `148-accounting-journal-cost-centers` FR-036–FR-040/FR-042 | Explicit reduction, evidence, confirmation, atomicity, stale/concurrent execution and reversal |

| `packages/reality-core/tests/test_action_discovery.py` | `158-categorized-action-discovery` | Shared action classification completeness and drift |

| Categorized action discovery (158) | `specs/158-categorized-action-discovery/spec.md` | `packages/reality-core/tests/test_action_discovery.py`; `apps/web/scripts/action-discovery.test.mjs`; `apps/web/scripts/action-discovery-browser.mjs` | Classification, tree search and contextual form coverage |

## Guided Fact rules

| `packages/reality-core/tests/finance/test_settlement_flows.py` | 148 | Guided actual payment, explicit reduction, credit reuse/refund, reversal, authority and atomicity |
| `packages/reality-core/tests/finance/test_credit_reads.py` | Spec 169 | Available credit and payments as tenant-scoped agent reads |
| `packages/reality-core/tests/finance/test_party_balances.py` | Spec 170 | Party balances: open, overdue, credit and balance per party and currency, tool equals view, tenant-scoped |

| Feature                                               | Specification                                       | Verification                                                                                                                                        | Coverage                                                                        |
| ----------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Guided Fact rules (159)                               | `specs/159-guided-fact-rules/spec.md`               | `apps/web/scripts/guided-rule-draft.test.mjs`; `apps/web/scripts/guided-rules-browser.mjs`; `packages/reality-core/tests/test_reality_gap_rules.py` | Typed form preservation, source evidence, reviewed version lifecycle and replay |
| `packages/reality-core/tests/finance/test_opening.py` | `148-accounting-journal-cost-centers`               | FR-044–FR-048: four opening-position directions, coverage identity and normal settlement                                                            |
| `opening_scope`                                       | `148-accounting-journal-cost-centers` FR-044–FR-048 | Immutable source snapshot, party/direction/currency coverage and duplicate prevention                                                               |
| `opening_item_detail`                                 | `148-accounting-journal-cost-centers` FR-044–FR-048 | Stable original residual identity and optional stated due date; no duplicated balance                                                               |

Managed finance-reference catalog: spec 148 FR-008/010/021/030/031; one tenant-scoped
`finance_reference` table, immutable BusinessEvent decisions and shared confirmed
application tools. Regression proof: `packages/reality-core/tests/finance/test_references.py`;
UI journey: `packages/reality-core/tests/browser/unified_business_journey.py` and
`apps/web/scripts/unified-business-journey-browser.mjs`. Broader assignments/mapping
remain planned; see spec 148 delivery task slice R001–R004 for completion evidence.

Received-component attribution: spec 148 bounded D001–D004 covers
`financial_component`, `component_assignment_revision`, `component_assignment_part`.
Received values remain separate from reasoned internal classification and explicit
cost-center amounts. Regression families:
`packages/reality-core/tests/finance/test_components.py` and
`packages/reality-core/tests/finance/test_component_boundaries.py`.
The existing real business journey covers review/reload/confirmation/history/mobile.
Automatic mapping and global cost reports remain deferred.

Operational transaction matrix: spec148 bounded M001–M004; no new schema.
`packages/reality-core/tests/finance/test_matrix.py` compares real postings and
configuration/default changes, tenant scope and read-only HTTP/CLI/MCP parity.
It also restores canonical customer-credit attribution under the existing spec.

## Page title counts

| Requirement         | Proof                                                                                            | Scope                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Spec 160 FR-001–004 | `apps/web/scripts/page-title-counts-browser.mjs`                                                 | Register matrix, total/zero, navigation, nested technical counts and mobile title layout |
| Spec 160 FR-005–006 | `apps/web/scripts/page-introduction-browser.mjs`; `apps/web/scripts/register-footer-browser.mjs` | Page-local tab placement, single heading, mobile navigation and preserved footer layout  |

## Timeline recorder raster

| Feature                        | Specification                                | Verification                                                                                                                                                                                                  | Coverage                                                                                                                                                                                                                                                                                                                          |
| ------------------------------ | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Timeline recorder raster (162) | `specs/162-timeline-recorder-raster/spec.md` | `apps/web/scripts/flight-recorder-layout.test.mjs`; `apps/web/scripts/unified-inspector-browser.mjs` | Interval choice, per-interval columns, lane stacks and widening, header labels, prepend anchoring and auto-fill of a compact first page |

## Context Graph naming

| Feature                    | Specification                            | Verification                                                                                                           | Coverage                                                                |
| -------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Context Graph naming (163) | `specs/163-context-graph-naming/spec.md` | `apps/web/scripts/inspector-navigation.test.mjs`; `provider-site/scripts/site-contract.test.mjs`; both localization audits | Navigation label, public-site wording, invariant term in four languages |

## One page action bar

| Feature | Specification | Verification | Coverage |
|---|---|---|---|
| One page action bar (165) | `specs/165-unified-page-actions/spec.md` | `apps/web/scripts/unified-app-contract.test.mjs`; `apps/web/scripts/action-discovery-browser.mjs`; register and page browser suites; localization audit | Primary/secondary/More actions rule, no direct slot writers, family labels, four languages |
## Open items default order

| Feature | Specification | Verification | Coverage |
|---|---|---|---|
| Open items default order (168) | `specs/167-open-items-default-order/spec.md` | `packages/reality-core/tests/test_unified_table_queries.py`; `apps/web/scripts/unified-finance-browser.mjs` | Newest document first for the open items projection, per-projection default, visible and sortable Date column |

## Source classification mappings (spec 148)

| Artifact                                                      | Specification                             | Proof                                                                                                                                                                                                            |
| ------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `source_classification_mapping_revision`                      | 148 FR-030, FR-033                        | Exact source scope, tenant/kind-aware links, immutable decisions and selected current head                                                                                                                       |
| `packages/reality-core/tests/finance/test_source_mappings.py` | 148 FR-030, FR-033, FR-034                | Declaration scope, lifecycle, history, no monetary effect, confirmation, tenant/owner parity, concurrent activation and migration preservation                                                                   |
| `packages/reality-core/tests/finance/test_target_mappings.py` | 148 FR-009, FR-021, FR-027, FR-030–FR-034 | Target/reference boundaries, exact mapping lifecycle, stale review, source provenance, no financial effects and additive migration                                                                               |
| `accounting_target`                                           | 148 FR-009, FR-027                        | Finance-only external destination identity and owner-controlled state                                                                                                                                            |
| `accounting_target_reference`                                 | 148 FR-009, FR-027                        | Permitted same-target external account and tax-code references                                                                                                                                                   |
| `finance_target_mapping_revision`                             | 148 FR-032, FR-033                        | Immutable exact routing decisions, tenant/target constraints and reviewed provenance                                                                                                                             |
| `apps/web/scripts/finance-settings-dialog-browser.mjs`        | 148 FR-059                                | All nine named create dialogs, list-only initial state, prefilled account edit, no-write Escape/Close, focus restoration, inline error visibility, owner/member controls, recovered review and responsive themes |
# Spec 173 — Physical Shipments and Tracking

- `packages/reality-core/tests/test_shipments_domain.py`: FR-002, FR-005, FR-008,
  FR-009 and DR-005/DR-007; exact purpose/direction/Movement compatibility and distinct
  warehouse versus externally reported delivery observations.
- `packages/reality-core/tests/test_shipments_migration.py`: FR-004, FR-027 and DR-003;
  additive nullable Movement linkage, no backfill operation and feature-only downgrade boundary.
- `packages/reality-core/tests/test_shipment_reads.py`: FR-004, FR-007, FR-010,
  FR-012, FR-013, FR-025 and DR-003; tenant-scoped tracking search, zero-content notices,
  event supersession, Package compatibility and foreign-record refusal.
- `packages/reality-core/tests/test_shipment_actions.py`: FR-014–FR-016 and FR-018;
  no-effect preparation, stale-state refusal, confirmation replay and lost-response recovery.
- `packages/reality-core/tests/test_shipment_story.py`: FR-004–FR-008; exact outbound Package
  contents, fulfillment, zero-effect inbound notice and partial supplier receipt.
- `packages/reality-core/tests/test_shipment_api.py`: FR-017 and FR-023; HTTP read, not-found,
  preparation and explicit state-bound confirmation parity.
- `packages/reality-core/tests/test_shipment_cli.py`: FR-017 and FR-022; tenant-scoped CLI list
  filters and Shipment detail parity.
- `packages/reality-core/tests/test_shipment_tools.py`: FR-017, FR-018 and FR-024; direct MCP
  reads plus proposal-only mutation exposure without pre-confirmation effects.
- `packages/reality-core/tests/test_shipment_returns.py`: FR-002, FR-005, FR-006 and DR-009;
  packaged customer/supplier return direction and preservation of original fulfillment.
- `apps/web/scripts/unified-shipments-browser.mjs`: FR-019–FR-021 and FR-028; separate physical
  Shipment register/detail, five reviewed forms, error/keyboard behavior, responsive layouts,
  themes and en/de/nl/es rendering.
- `docs/features/shipments.md`: durable domain and adapter contract for Spec 173.

## Shared browser language

- `docs/features/shared-language.md`: durable language handoff contract (anonymous persistence superseded by spec 188) for `specs/176-shared-language/spec.md`, FR-001–FR-005.
- `provider-site/scripts/shared-language.test.mjs` and `provider-site/scripts/shared-language-browser.mjs`: precedence, cookie scope, storage failure, cross-surface navigation and profile/Docs language choices.

## Background projections (Spec 179)

- `packages/reality-core/tests/test_projection_jobs.py`: FR-003–FR-010; event dependencies, durable coalescing, scoped consistent publication, concurrent writers, rollback, recovery, pure reads and freshness.
- `packages/reality-core/tests/test_projection_job_migration.py`: FR-004 and FR-011; approved internal actor constraint, unfinished-run uniqueness and migration roundtrip.
- `apps/web/scripts/unified-inspector-browser.mjs`: FR-001, FR-002, FR-007 and FR-008; lazy disclosure, full-text search and initial/pending/failed/recovered snapshots.
- `apps/web/scripts/unified-finance-browser.mjs`: FR-007 and FR-008; fresh/pending/failed/uninitialized financial snapshots, preserved totals and no false initial emptiness.
- `apps/web/scripts/unified-payment-entry-browser.mjs`: FR-008 and FR-010; invoice choice, reviewed payment actions, recovery and shared service boundaries.

## Scale foundations (Spec 181)

- `packages/reality-core/tests/test_schema_indexes.py`: FR-001 and FR-005; every foreign key's first column leads an index in the models, migration `0059_foreign_key_indexes` creates exactly the derived set, and a freshly migrated database indexes every foreign key with the downgrade removing exactly those.
- `packages/reality-core/tests/test_payment_intake.py::test_matching_cost_does_not_grow_with_the_customers_settled_history` and `tests/test_operational_read_performance.py::test_projection_builders_read_per_company_not_per_record`: FR-001 and FR-002; payment matching and the projection builders read a bounded number of times regardless of history.

## Composable analytics (185)

Spec 185 owns the analytics service, agent tools, private report configuration and workspace.

- `packages/reality-core/tests/test_analytics_adapters.py` — `specs/185-analytics-workspace/spec.md`, FR-001–019 and DR-001–006.
- `packages/reality-core/tests/test_analytics_chat.py` — `specs/185-analytics-workspace/spec.md`, FR-001–019 and DR-001–006.
- `packages/reality-core/tests/test_analytics_contributors.py` — `specs/185-analytics-workspace/spec.md`, FR-001–019 and DR-001–006.
- `packages/reality-core/tests/test_analytics_definitions.py` — `specs/185-analytics-workspace/spec.md`, FR-001–019 and DR-001–006.
- `packages/reality-core/tests/test_analytics_execution.py` — `specs/185-analytics-workspace/spec.md`, FR-001–019 and DR-001–006.
- `packages/reality-core/tests/test_analytics_exports.py` — `specs/185-analytics-workspace/spec.md`, FR-001–019 and DR-001–006.
- `packages/reality-core/tests/test_analytics_questions.py` — `specs/185-analytics-workspace/spec.md`, FR-001–019 and DR-001–006.
- `packages/reality-core/tests/test_analytics_reports.py` — `specs/185-analytics-workspace/spec.md`, FR-001–019 and DR-001–006.
- `packages/reality-core/tests/test_analytics_performance.py` — `specs/185-analytics-workspace/spec.md`, FR-006, FR-018 and SC-005.
- `docs/features/analytics.md` — `specs/185-analytics-workspace/spec.md`, implemented Analytics, agent, privacy, observation, Web and persistence contract.


## Spec 189 — Open Signup by Default

- `packages/reality-core/tests/test_access_admission.py`: optional setting matrix, cumulative mode transitions, concurrent finite claims and generic deployment defaults (FR-001–004, DR-001).
- `packages/reality-core/tests/test_user_access.py`: default and blank admission after verification, replay, existing manual/finite behavior and tenant access (FR-001–003, FR-005).
- `packages/reality-core/tests/test_platform_admin_overview.py`: unlimited/invalid admission reporting (FR-004).
- `provider-site/scripts/site-contract.test.mjs`: unlimited public entry copy (FR-004).

## Spec 190 — Free Playground Trial

- `packages/reality-core/tests/test_free_playground.py`: consent, read-only entry, canonical retry/pause/archive, explicit disable, cross-company allowance including subsequent ordinary companies, UTC reset, concurrent final slot, own-provider/companion boundary and provider refusal (FR-002–004, FR-007–008).
- `packages/reality-core/tests/test_company_setup_api.py`: authenticated account entry and read-only consent status (FR-002–004).
- `apps/web/scripts/free-playground.test.mjs`: task destinations, cleared filters, current-company successful results and browser preference identity (FR-005–006).
- `provider-site/scripts/site-contract.test.mjs`: free-trial positioning without permanent-free or automatic-subscription promise (FR-001, FR-009).

- `apps/web/scripts/free-playground-browser.mjs`: recoverable confirmed entry, actual rendered result/error/uninitialized gates, persistent dismissal, delivery detail, exhaustion draft and four mobile locales (Spec 190 FR-001–009).

- `apps/web/scripts/entry-progress-browser.mjs`: delayed session/signup/verification/bootstrap/policy/setup feedback, single verification navigation, failure retry and language continuity (Spec 190 FR-010).

- `provider-site/scripts/site-contract.test.mjs` and `site-localization.test.mjs`: current free-only hosted offer, absent paid/capacity terms, unchanged signup and localized trial terms (Spec 190 FR-011).

## Spec 192 — Applicant Account Deletion

- `packages/reality-core/tests/test_account_deletion.py`: preview of owned and shared companies, the purge of the account with its sole-owned business and practice companies, case-insensitive address confirmation, the surviving shared company, both guards, the exact confirmations, the refusal that removes nothing, the tombstone without a user reference, and the schema-driven proof that no reference to the account remains (FR-002, FR-004–FR-010, SC-003).
- `packages/reality-core/tests/test_access_application_deletion_api.py`: the preview and delete routes, platform-administration authorization, the refused confirmation and the unknown application (FR-011).
- `apps/web/scripts/access-deletion.test.mjs`: the two-answer confirmation, the literal confirmation word shared with the company danger zone, address normalization and the withheld control for administrators (FR-001, FR-003).
- `apps/web/scripts/access-deletion-browser.mjs`: the offered and withheld delete controls, the preview of what is lost, the gated confirm button, a server refusal that removes nothing, the confirmed payload, and the German dialog at 390px (FR-001–FR-004, FR-011–FR-013, SC-001, SC-004, SC-006).

## Spec 194 — Signup Adopts the Browser's Presentation Defaults

- `packages/reality-core/tests/test_user_access.py`: the stored zone, language and paired locale for public and invitation signup, the fallback for absent, empty, unknown, malformed and unsupported hints, the refused oversized hint that creates no account, the locale a client cannot claim, and the one vocabulary shared with profile validation (FR-001–FR-003, FR-005, DR-002).
- `apps/web/scripts/signup-preferences.test.mjs`: the explicit page language, the browser's requested language, the omitted unsupported language, the stated zone and the omitted unusable or oversized zone (FR-004).
- `apps/web/scripts/signup-preferences-browser.mjs`: a real browser in `America/Denver`, `Europe/Amsterdam` and `Asia/Tokyo` registering from the German entry page, from a Dutch browser and from an unsupported French one, with the sent request body carrying the zone and language and never a locale (FR-004, SC-001).

## Spec 195 — Storyline Free Play Chat

- `packages/reality-core/tests/test_storyline_chat.py`: exact reply/call association, proposal decisions, context isolation, retention and owner/tenant/message boundaries (FR-003–004, DR-001).
- `apps/web/scripts/storyline-browser.mjs`: own words, explicit send, reply evidence, reload and localized responsive layouts (FR-001–005).

- Spec 195 FR-006: `apps/web/scripts/unified-chat-composer-browser.mjs` proves focus
  after failed Enter and successful button send without stealing another control's
  focus; `storyline-browser.mjs` covers the first-session Free Play remount.

- Spec 195 FR-007: `apps/web/scripts/storyline-browser.mjs` verifies direct library
  Free Play entry into the existing tenant without writes and return to the story.

- Spec 195 FR-007–009: `test_storyline_chat.py` proves standalone confirmed/idempotent
  setup, no Storyline identity, archive and owner-scoped recorded calls;
  `storyline-browser.mjs` proves separate entry/creation/reopen, no card shortcuts,
  no prescribed chapters and responsive localized standalone layouts.

- Spec 196: `packages/reality-core/tests/test_ai_usage.py` proves account-wide
  lifetime cap, idempotent confirmation, actor/recipient attribution, tenant/admin
  authorization, UTC expiration and concurrent grants.

- Spec 198: `packages/reality-core/tests/test_free_playground.py` and
  `test_company_setup_api.py` prove both starts, the recorded receipt, replay, the
  refused conflicting start, the closed adapter literal and a Demo Data connection
  after an empty start; `apps/web/scripts/free-playground-browser.mjs` proves the two
  cards, that nothing is created before a choice, and four languages on a narrow
  viewport.

- Spec 199: `packages/reality-core/tests/test_company_setup_initialization.py` proves the
  deferred receipt, the single enqueued initialization, the handler's effect and its
  no-op re-run, refusal at enqueue and at claim, the in-request retry and the immediate
  empty company; `apps/web/scripts/setup-progress.test.mjs` proves the followed receipt,
  its bound and its retry of failed reads; `product-boundary.test.mjs` proves the stated
  proxy timeouts; `free-playground-browser.mjs` proves a slow seed keeps showing progress
  and opens the company without creating a second one.

- Spec 200: `packages/reality-core/tests/scenarios/test_international_demo.py` proves
  the seeded order book spreads over the customer pool within its concentration bound,
  keeps both windows of a comparison family on one buyer, states that buyer on the
  invoice and the credit note, names three suppliers and stays authored rather than
  drawn across companies.

- Spec 201: `packages/reality-core/tests/test_worker_due_discovery.py` proves the worker
  discovers only tenants with claimable work, includes an expired lease, excludes a run
  whose attempt time has not come, pages within its bound, and that the sweep itself no
  longer asks every tenant; `test_company_setup_initialization.py` proves the receipt
  reports queued, preparing and nothing; `apps/web/scripts/setup-progress.test.mjs`
  proves the immediate first read and that the steps are derived, never estimated;
  `free-playground-browser.mjs` proves the three steps follow the real state.
