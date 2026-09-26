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
| `004-master-data`, extended by Spec 258        | `party`, `party_role`, `party_email_address`, `payment_term`, `item`, `location`, `price_list`, `price_list_entry`, `party_price_list`, `party_group`, `party_group_member`, `party_group_price_list`       |
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
| Master/commercial services        | master data, payment terms, pricing in `services/core.py`      | `004`, `259`                                  | operational fields, pricing, payment-term tests; authoritative MCP price quote                                |
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
| Public Site                       | landing presentation under `provider-site/src/`                | `022`, localization by `034`                  | site contract tests, site localization tests, four-language `i18n:audit`, build, independent image smoke test |
| React product                     | auth and routed pages under `apps/web/src/`                    | `016`, boundary refined by `022`              | build, i18n audit, product-boundary and API contract tests                                                    |
| Generated reference               | Web catalog/data-model/CLI reference modules                   | `007`, `016`                                  | application-catalog and HTTP-boundary tests                                                                   |

Private helpers within these modules are implementation detail. They are covered through
their public family and are not separate capabilities.

## Executable Proof Ownership

| Test family                                                                                           | Primary baseline or authority                                                                    | Coverage note                                                                                                                                                                                                                                                                                                               |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `packages/reality-core/tests/test_user_access.py`                                                     | `003`                                                                                            | Active auth/access proof                                                                                                                                                                                                                                                                                                    |
| `packages/reality-core/tests/test_tenant_lifecycle.py`                                                | `003`                                                                                            | Archive/restore/delete proof                                                                                                                                                                                                                                                                                                |
| `packages/reality-core/tests/test_tenancy.py`                                                         | `003`                                                                                            | Cross-tenant domain proof                                                                                                                                                                                                                                                                                                   |
| `packages/reality-core/tests/tenant_isolation/test_families.py`                                       | `003/FR-012`, Spec 019                                                                           | Two-tenant proof for every catalogued isolation class and registry drift                                                                                                                                                                                                                                                    |
| `packages/reality-core/tests/test_cli_context.py`                                                     | `003`                                                                                            | Tenant context/ambiguity proof                                                                                                                                                                                                                                                                                              |
| `packages/reality-core/tests/test_email_delivery.py`                                                  | `003`                                                                                            | Account-mail provider boundary                                                                                                                                                                                                                                                                                              |
| `packages/reality-core/tests/test_verification_email_return.py`                                       | `190`                                                                                            | Verification email return URL and explicit-code boundary                                                                                                                                                                                                                                                                    |
| `packages/reality-core/tests/test_payment_terms.py`                                                   | `004`                                                                                            | Payment-term lifecycle/validation                                                                                                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_payment_term_prepayment_migration.py`                               | Spec 275                                                                                         | Additive explicit-prepayment migration, false compatibility default, and downgrade preservation                                                                                                                                                                                                                             |
| `packages/reality-core/tests/test_fulfillment_readiness.py`                                          | Spec 275                                                                                         | Explicit prepayment policy, stated/allocated amounts, blocker evidence, and net-term control                                                                                                                                                                                                                                |
| `packages/reality-core/tests/test_master_data_parity.py`                                              | `004/FR-016`, Spec 026                                                                           | Master-data adapter matrix, canonical-state, and drift proof                                                                                                                                                                                                                                                                |
| `packages/reality-core/tests/test_pricing.py`                                                         | `004`                                                                                            | Deterministic pricing; history gap retained                                                                                                                                                                                                                                                                                 |
| `packages/reality-core/tests/test_price_quote_mcp.py`                                                 | `259`                                                                                            | Canonical MCP price result, provenance, explicit no-match, and tenant isolation                                                                                                                                                                                                                                             |
| `packages/reality-core/tests/test_operational_fields.py`                                              | `004`                                                                                            | Proven typed fields/constraints                                                                                                                                                                                                                                                                                             |
| `packages/reality-core/tests/test_source_ingestion.py`                                                | `005`                                                                                            | Generic/artifact/file ingestion                                                                                                                                                                                                                                                                                             |
| `packages/reality-core/tests/test_interpretation_coverage.py`                                         | Spec 045                                                                                         | Immutable attempt outcomes, produced-record identities, classification, retry, MCP, and tenant proof                                                                                                                                                                                                                        |
| `packages/reality-core/tests/test_integrations.py`                                                    | `005`                                                                                            | Source registry/intake UI API                                                                                                                                                                                                                                                                                               |
| `packages/reality-core/tests/test_import_demo_files.py`                                               | `005`                                                                                            | Explicit file-profile story                                                                                                                                                                                                                                                                                                 |
| `packages/reality-core/tests/test_shopify_and_explain.py`                                             | `005`, `013`                                                                                     | Shopify plus source explanation                                                                                                                                                                                                                                                                                             |
| `packages/reality-core/tests/test_shopify_update_guard.py`                                            | Spec 081                                                                                         | Shopify update preservation, explicit review, retry, batch and HTTP behavior                                                                                                                                                                                                                                                |
| `packages/reality-core/tests/test_document_corrections.py`                                            | `006`                                                                                            | Header/source correction; line gap retained                                                                                                                                                                                                                                                                                 |
| `packages/reality-core/tests/test_documents.py`                                                       | `077`                                                                                            | Stated amounts recorded, never calculated                                                                                                                                                                                                                                                                                   |
| `packages/reality-core/tests/test_returns.py`                                                         | `079`, `250`                                                                                     | Goods coming back name the delivery they reverse; tracked return dispositions preserve the exact arrived stock identity                                                                                                                                                                                                      |
| `packages/reality-core/tests/test_credit_notes.py`                                                    | `084`                                                                                            | Credit notes post, net and refund                                                                                                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_commitment_revisions.py`                                            | `093`, `097`, `250`                                                                              | A counterparty's new date is recorded without erasing the old one; quantity revisions also keep active reservations within the revised open quantity                                                                                                                                                                         |
| `packages/reality-core/tests/test_commitment_actions.py`                                              | `250`                                                                                            | Reviewed commitment cancellation, exact reservation and hold release, stable receipt, and authoritative event verification                                                                                                                                                                                                  |
| `packages/reality-core/tests/test_chat.py`                                                            | `250`                                                                                            | Chat provider discovery of reviewed commitment revision/cancellation proposals and canonical application-tool parity                                                                                                                                                                                                         |
| `packages/reality-core/tests/test_stale_promises.py`                                                  | `085`                                                                                            | Previewing and closing promises an import left behind                                                                                                                                                                                                                                                                       |
| `packages/reality-core/tests/test_payment_runs.py`                                                    | `098`                                                                                            | What is worth paying now, and paying it all at once or not at all                                                                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_return_announcements.py`                                            | `099`                                                                                            | A customer's announced return, and the parcel that names it                                                                                                                                                                                                                                                                 |
| `packages/reality-core/tests/test_return_announcement_adapters.py`                                    | `099`                                                                                            | The announcement and the resolution references reach MCP, web and CLI (099 amendment)                                                                                                                                                                                                                                       |
| `packages/reality-core/tests/test_reference_integrity.py`                                             | `100`                                                                                            | The references the queue leans on, and the paths and surfaces that can set them                                                                                                                                                                                                                                             |
| `packages/reality-core/tests/operational_exceptions/test_derivation.py`                               | `107`                                                                                            | A hold nobody lifted, on a promise or on a whole counterparty                                                                                                                                                                                                                                                               |
| `packages/reality-core/tests/test_commitment_holds.py`                                                | `008`, `108`                                                                                     | Promise/document convenience holds, and a hold never outliving its promise                                                                                                                                                                                                                                                  |
| `packages/reality-core/tests/test_inventory_tracking_reservations.py`                                 | `009`, `109`, `110`                                                                              | Lot/serial allocations and tools, the best-before date a lot carries, and correcting a misread one                                                                                                                                                                                                                          |
| `packages/reality-core/tests/test_party_delivery_holds.py`                                            | `008`                                                                                            | Customer delivery hold scope                                                                                                                                                                                                                                                                                                |
| `packages/reality-core/tests/test_inventory_and_fulfillment.py`                                       | `008`, `009`                                                                                     | Fulfilment/inventory core story                                                                                                                                                                                                                                                                                             |
| `packages/reality-core/tests/test_movement_corrections.py`                                            | Spec 023                                                                                         | Append-only Movement void/replacement, retry, audit, and tenant proof                                                                                                                                                                                                                                                       |
| `packages/reality-core/tests/test_handling_units.py`                                                  | `009`                                                                                            | Optional pallet/NVE behavior                                                                                                                                                                                                                                                                                                |
| `packages/reality-core/tests/scenarios/test_order_to_cash.py`                                         | `010`                                                                                            | Customer end-to-end story                                                                                                                                                                                                                                                                                                   |
| `packages/reality-core/tests/scenarios/test_fulfillment_safety_parity.py`                             | Spec 275                                                                                         | Two-order net/prepayment story, zero-effect refusal, application/MCP parity, partial/full payment, and final stock/open-item reconciliation                                                                                                                                                                                   |
| `packages/reality-core/tests/scenarios/test_procure_to_pay.py`                                        | `011`                                                                                            | Supplier end-to-end story                                                                                                                                                                                                                                                                                                   |
| `packages/reality-core/tests/scenarios/test_b2b_operational_integrity.py`                             | `250`                                                                                            | Exact tracked-return, reviewed revision/cancellation and historical no-silent-repair business proof                                                                                                                                                                                                                           |
| `packages/reality-core/tests/scenarios/test_external_agent_audit_closure.py`                          | `257`                                                                                            | Fresh-tenant F1–F13 harness, terminal-result completeness and secret-redaction evidence contract                                                                                                                                                                                                                              |
| `packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py` | `009`, `010`, `119`, `173` | Scenario catalog A13, A20, D03, L09, O04: per-line promised dates, one shipment for two orders, several commitments in one package, a zero-price promotion line, a delisted item still served |
| `packages/reality-core/tests/scenarios/test_catalog_purchasing.py` | `011`, `089`, `248/FR-009` | Scenario catalog G14, H10, H11, H12, I05: two suppliers protect one demand, one package for several purchases, early receipt, receipt linked to a later purchase, one supplier invoice over two purchases |
| `packages/reality-core/tests/scenarios/test_catalog_finance.py` | `012`, `121`, `125`, `126` | Scenario catalog C06, E09, E10, F13: payment after cancellation becomes credit and is refunded, bill-to vs ship-to, lossless e-invoice artifact, credit booked in the next month |
| `packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py` | `009`, `099`, `262` | Scenario catalog B04, F03, J08, L01: re-reservation between customers, a foreign item cannot fulfil a return announcement, consignment and external fulfilment locations |
| `packages/reality-core/tests/test_ledger.py`                                                          | `012`                                                                                            | Balanced postings/settlement/registers                                                                                                                                                                                                                                                                                      |
| `packages/reality-core/tests/test_finance_payment_atomicity.py`                                       | `096 FR-017`                                                                                     | Durable customer-payment rollback and confirmed-action event attribution                                                                                                                                                                                                                                                    |
| `packages/reality-core/tests/test_free_supplier_invoice.py`                                           | Spec 257                                                                                         | Source-backed free supplier-invoice evidence, stated totals, ordinary-human authority, atomic rollback, replay, tenant scope, and no invented stock or commitment effects                                                                                                                                                   |
| `packages/reality-core/tests/test_ledger_reversals.py`                                                | Spec 024                                                                                         | Whole-group exact inverse, immutable allocation history, retry, audit, and tenant proof                                                                                                                                                                                                                                     |
| `packages/reality-core/tests/test_business_events.py`                                                 | `013`                                                                                            | Transactional ordered events                                                                                                                                                                                                                                                                                                |
| `packages/reality-core/tests/test_materialized_projections.py`                                        | `013`                                                                                            | Refresh/checkpoint/stale rows                                                                                                                                                                                                                                                                                               |
| `packages/reality-core/tests/test_application_tools.py`                                               | `013`, `014`                                                                                     | Read tools and confirmed mutations                                                                                                                                                                                                                                                                                          |
| `packages/reality-core/tests/operational_exceptions/test_coverage.py`                                 | `013/FR-005`, Spec 020, Specs 068 and 071                                                        | Closed class/cause taxonomy, shared-cause vocabulary, operator-guidance completeness, and registry/order drift proof                                                                                                                                                                                                        |
| `packages/reality-core/tests/operational_exceptions/test_derivation.py`                               | `013/FR-005`, Spec 020, Specs 068, 069 and 072                                                   | Tenant-scoped derivation, ordering, single-entry, learned-rhythm and clearing proof for every class                                                                                                                                                                                                                         |
| `packages/reality-core/tests/operational_exceptions/test_explanation.py`                              | `013/FR-005`, Spec 020, Spec 068                                                                 | Shared-consumer explanation parity and class-transition identity proof                                                                                                                                                                                                                                                      |
| `packages/reality-core/tests/test_chat_confirmation.py`                                               | `014`, `015`                                                                                     | Chat proposals and shared demos                                                                                                                                                                                                                                                                                             |
| `packages/reality-core/tests/test_desktop_http.py`                                                    | `239`                                                                                            | Exact loopback origin, authenticated desktop transport and hosted-boundary preservation                                                                                                                                                                                                                                    |
| `packages/reality-core/tests/test_desktop_identity.py`                                                | `239`                                                                                            | Installation-bound local owner identity, hosted denial and shared session lifecycle                                                                                                                                                                                                                                        |
| `packages/reality-core/tests/test_desktop_identity_migration.py`                                      | `239`                                                                                            | Desktop identity schema upgrade and guarded downgrade                                                                                                                                                                                                                                                                       |
| `packages/reality-core/tests/test_key_provider.py`                                                    | `240 FR-006`                                                                                     | Installation-bound, single-assignment desktop master-key handoff with fail-closed desktop mode and unchanged hosted configuration                                                                                                                                                                                           |
| `packages/reality-core/tests/test_chat_master_data.py`                                                | `014`, Spec 038                                                                                  | Confirmed Party, Item, and Location proposal, batch, provenance, and tenant proof                                                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_chat_master_data_updates.py`                                        | Spec 041                                                                                         | Confirmed Party, Item, and Location update previews, stale guards, atomicity, and proposal-event linkage                                                                                                                                                                                                                    |
| `packages/reality-core/tests/test_master_data_update_audit.py`                                        | Spec 041                                                                                         | Exact normalized before/after diffs, no-op behavior, rollback, lifecycle, and immutable source-version proof                                                                                                                                                                                                                |
| `packages/reality-core/tests/test_party_email_lookup.py`                                               | Spec 258                                                                                         | Party email normalization, exact discovery, ambiguity, replacement and tenant isolation                                                                                                                                                                                                                                     |
| `packages/reality-core/tests/test_ai_mcp.py`                                                          | `014`                                                                                            | Secrets/tokens/MCP permission boundary                                                                                                                                                                                                                                                                                      |
| `packages/reality-core/tests/test_agent_command_parity.py`                                            | Spec 042                                                                                         | Canonical command classification, strict schema, and Chat/MCP registry parity                                                                                                                                                                                                                                               |
| `packages/reality-core/tests/test_mcp_read_contract.py`                                               | Spec 145                                                                                         | Currency separation, ledger direction, units, locations, closed orders, scoped traversal and no-write diagnostics                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_agent_discovery.py`                                                 | Spec 042                                                                                         | Bounded tenant-scoped discovery and opaque identity proof                                                                                                                                                                                                                                                                   |
| `packages/reality-core/tests/test_capability_guidance.py`                                             | Specs 044, 047, 048                                                                              | Complete public proposal/read guidance, shared lookup, verification boundaries, and registry drift proof                                                                                                                                                                                                                    |
| `packages/reality-core/tests/test_chat_mcp_business_commands.py`                                      | Spec 042                                                                                         | Proposal/approval stories across warehouse, pricing, finance, source, and membership command families                                                                                                                                                                                                                       |
| `packages/reality-core/tests/test_chat_mcp_orders.py`                                                 | Spec 042                                                                                         | Sales/purchase order Source-to-Evidence-to-Commitment proposal stories                                                                                                                                                                                                                                                      |
| `packages/reality-core/tests/test_mcp_chat.py`                                                        | `014`, Spec 038                                                                                  | Copilot prompt and provider-derived master-data tool-schema proof                                                                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_fact_observation.py`                                                | Spec 043                                                                                         | Source-required, cataloged, idempotent, tenant-scoped Fact observation and atomic event proof                                                                                                                                                                                                                               |
| `packages/reality-core/tests/test_mcp_fact_observation.py`                                            | Spec 043                                                                                         | Confirmed MCP/Chat Fact proposal and shared application-tool proof                                                                                                                                                                                                                                                          |
| `packages/reality-core/tests/test_reality_gaps.py`                                                    | Spec 067                                                                                         | Tenant-scoped capture, investigation, safe Fact-rule simulation, activation, replay, and provenance proof                                                                                                                                                                                                                   |
| `packages/reality-core/tests/test_reality_gap_tools.py`                                               | Spec 067                                                                                         | Shared application-tool and complete MCP proposal/read surface proof                                                                                                                                                                                                                                                        |
| `packages/reality-core/tests/test_reality_gap_rules.py`                                               | Spec 067                                                                                         | Closed conditional evaluation, output modes, effective time, line resolution, conflicts, and resumable replay proof                                                                                                                                                                                                         |
| `packages/reality-core/tests/test_chat_scope_security.py`                                             | `197`                                                                                            | Shared scope policy, forged history roles, hostile tool data and model confirmation denial                                                                                                                                                                                                                                  |
| `packages/reality-core/tests/test_anthropic_copilot.py`                                               | `037`                                                                                            | Managed Anthropic Messages API and canonical tool-use boundary                                                                                                                                                                                                                                                              |
| `packages/reality-core/tests/test_mcp_http_runtime.py`                                                | `018`                                                                                            | Separate authenticated HTTP-only MCP runtime, health/readiness, and tool parity                                                                                                                                                                                                                                             |
| `packages/reality-core/tests/test_mcp_oauth_http.py`                                                  | Spec 265                                                                                         | OAuth/MCP discovery, PKCE, exact resource/client/redirect, consent, transport challenges and revocation contract                                                                                                                                                                                                            |
| `packages/reality-core/tests/test_mcp_oauth_migration.py`                                             | Spec 265                                                                                         | Interactive MCP authorization schema parity, tenant keys, lifecycle constraints and guarded rollback                                                                                                                                                                                                                       |
| `packages/reality-core/tests/test_mcp_oauth_service.py`                                               | Spec 265                                                                                         | Grant, credential, rotation/reuse, effective authority, retention and bounded CIMD security proof                                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_mcp_error_codes.py`                                                 | `214`                                                                                            | Stable `code`, `message` and `tool` in MCP tool refusals from service errors; plain text kept for non-business failures                                                                                                                                                                                                     |
| `packages/reality-core/tests/scenarios/test_normal_month.py`                                          | `015`                                                                                            | Deterministic/idempotent scenario                                                                                                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_bootstrap.py`                                                       | `015`                                                                                            | Explicit configured bootstrap                                                                                                                                                                                                                                                                                               |
| `packages/reality-core/tests/test_demo_entrypoint_parity.py`                                          | `015/FR-010`, Spec 027                                                                           | Guided-demo real-entrypoint manifest, safety, and drift proof                                                                                                                                                                                                                                                               |
| `packages/reality-core/tests/test_cli.py`                                                             | Owning baselines + `016`                                                                         | CLI adapter equivalence evidence                                                                                                                                                                                                                                                                                            |
| `packages/reality-core/tests/test_master_data_api.py`                                                 | `004`, `006`, `013`, `014`, `016`                                                                | Public API/React contract evidence                                                                                                                                                                                                                                                                                          |
| `packages/reality-core/tests/test_web_ux_reads.py`                                                    | `016/FR-006`, Spec 030                                                                           | Tenant-scoped Journal totals, filters, inspection, and foreign-boundary proof                                                                                                                                                                                                                                               |
| `packages/reality-core/tests/test_large_tenant_register_contract.py`                                  | `016/FR-015`, Spec 033                                                                           | Reduced/full profile contract, nine-family bounded reads, stable paging, tenant sentinels, and result-schema proof                                                                                                                                                                                                          |
| `packages/reality-core/tests/test_inspector_presentation.py`                                          | Spec 138 FR-028                                                                                  | Typed numeric presentation, raw values and identifiers, currency, historical precision and foreign record isolation                                                                                                                                                                                                         |
| `packages/reality-core/tests/test_inspector_register.py`                                              | Spec 138 FR-027                                                                                  | Full record-family paging, search, summary bounds, tenant isolation and HTTP validation                                                                                                                                                                                                                                     |
| `packages/reality-core/tests/test_http_boundary.py`                                                   | `007`, `016`                                                                                     | API boundary and generated-catalog evidence                                                                                                                                                                                                                                                                                 |
| `packages/reality-core/tests/test_application_catalog.py`                                             | `007`                                                                                            | Executable vocabulary drift proof                                                                                                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_data_model.py`                                                      | Data Model, Spec 035                                                                             | Access model/catalog parity and shortest-link proof                                                                                                                                                                                                                                                                         |
| `packages/reality-core/tests/test_playground_runs.py`                                                 | `096/FR-001`, `096/FR-002`, `096/FR-003`, `096/FR-011`, `096/DR-003`, `096/DR-004`               | Storage constraints; owner-locked atomic reference setup, concurrent/idempotent start, failure recovery, archive safety and run quotas; no public entry yet                                                                                                                                                                 |
| `packages/reality-core/tests/test_playground_security.py`                                             | `096/FR-003`                                                                                     | Owner resolver, catalogued core writes, generic proposals/lifecycle, rule/upload and egress boundaries, CLI/MCP/HTTP denial; complete entrypoint audit remains pending                                                                                                                                                      |
| `packages/reality-core/tests/test_playground_api.py`                                                  | `096/FR-001`, `096/FR-002`, `096/FR-003`, `096/FR-011`                                           | Authenticated start/replay and setup failure, bounded private history, strict confirmation, quotas, session/membership checks, generic inspection and production separation                                                                                                                                                 |
| `packages/reality-core/tests/test_playground_chat.py`                                                 | `106/FR-003`, `106/FR-004`                                                                       | Owner-scoped read-only companion, bounded input, managed provider failure and mutation dispatch rejection                                                                                                                                                                                                                   |
| `packages/reality-core/tests/test_playground_steps.py`                                                | `096/FR-005`                                                                                     | Confirmed V1 action attribution, shipment consumption/remainder/fulfilment, repeat confirmation, transaction rollback and foreign action rejection                                                                                                                                                                          |
| `packages/reality-core/tests/test_storyline_package.py`                                               | `182/FR-002`, `182/FR-017`, `182/FR-019`, `182/SC-004`, `182/SC-008`                             | Storyline package contract: shape, catalog names, symbolic references, dominator rule for chapter references, bounds, collected errors, built-in validation, catalog labels                                                                                                                                                 |
| `packages/reality-core/tests/test_storyline_trace.py`                                                 | `182/FR-004`                                                                                     | Storyline call trace: dispatcher wrappers for reads and proposals, markers on confirmation, chapter scope, entry and run bounds, view middleware, tenant scope                                                                                                                                                              |
| `packages/reality-core/tests/test_storyline_delta.py`                                                 | `182/FR-005`                                                                                     | Delta primitives: forward timeline read after a marker, cursor exclusivity, Fact recording order independent of business time                                                                                                                                                                                               |
| `packages/reality-core/tests/test_storyline_runs.py`                                                  | `182/FR-001`, `182/FR-003`, `182/FR-005`, `182/FR-009`, `182/FR-010`, `182/FR-011`, `182/FR-012` | Storyline runs: seeded practice company, atomic seed failure, chapters through the ordinary proposal path, refused preparation as outcome, derived chapter state, branches, reject and retry, restart, library, tool reference, free play with its own marker and delta, blocked chapter names the missing finding          |
| `packages/reality-core/tests/test_storyline_library_api.py`                                           | `182/FR-001`, `182/FR-003`, `182/FR-004`, `182/FR-005`, `182/FR-007`, `182/FR-018`               | Storyline HTTP surface: library and start, chapter prepare and confirm, trace, delta, tool reference, owner privacy and cookie requirement, error mapping                                                                                                                                                                   |
| `packages/reality-core/tests/scenarios/test_storyline_first_round.py`                                 | `182/FR-009`, `182/FR-014`, `182/SC-002`                                                         | First round, the short introduction, played end to end: a rule raises a finding no command wrote, the same rule clears it once the remainder is reserved, a refused dispatch writes nothing, the read chapter writes nothing, the story ends on one open finding, every event after the seed in exactly one chapter's delta |
| `packages/reality-core/tests/scenarios/test_storyline_order_to_close.py`                              | `182/FR-009`, `182/FR-010`, `182/FR-014`, `182/SC-002`                                           | Order to close played end to end through the service: default path and both alternative paths, expected against observed findings, refused dispatch, read chapters, every event after the seed in exactly one chapter's delta                                                                                               |
| `packages/reality-core/tests/scenarios/test_storyline_purchase_to_pay.py`                             | `182/FR-009`, `182/FR-010`, `182/FR-014`, `182/SC-002`                                           | Purchase to pay played end to end: short delivery, invoice over quantity and price, duplicate invoice booked and reversed, discount taken on the record; credit branch pays less and keeps the quantity finding; every event after the seed in exactly one chapter's delta                                                  |
| `packages/reality-core/tests/test_storyline_export.py`                                                | `182/FR-021`, `182/SC-009`                                                                       | Run exported as a storyline draft: seed identities as `$ref`, created records as `$chapter`, dates as offsets, texts marked missing, story chapters keep their texts, unsupported commands in place, the filled draft imports and plays, draft route                                                                        |
| `packages/reality-core/tests/test_playground_practice_companies.py`                                   | `104/FR-001`, `104/FR-002`, `104/FR-003`, `104/FR-004`, `104/DR-001`, `104/DR-002`               | Named isolated setup, retry validation, persistent lifecycle and temporary replacement                                                                                                                                                                                                                                      |
| `packages/reality-core/tests/test_playground_free_operations.py`                                      | `103/FR-003`, `103/FR-004`, `103/FR-005`, `103/DR-002`                                           | Selected target response, remaining-quantity freshness and interleaved sales/purchase/partial fulfillment in one sandbox                                                                                                                                                                                                    |
| `packages/reality-core/tests/test_playground_release.py`                                              | `103/FR-012`                                                                                     | Reviewed exact reservation release, rejection, stale and missing target refusal, repeat confirmation and unchanged stock/obligation                                                                                                                                                                                         |
| `packages/reality-core/tests/test_playground_master_data.py`                                          | `103/FR-013`                                                                                     | Shared Party/Item/Location creation and editing, rejection, stale/foreign/extra input refusal, exact execution scope and repeated confirmation                                                                                                                                                                              |
| `packages/reality-core/tests/test_playground_shipment_recovery.py`                                    | `103/FR-008`, `103/FR-005`                                                                       | Pre-claim overdelivery rejection, proven unapplied legacy discard and refusal of uncertain execution                                                                                                                                                                                                                        |
| `packages/reality-core/tests/test_master_data_api.py`, `apps/web/scripts/playground-free-browser.mjs` | `103/FR-007`                                                                                     | Outstanding financial filter retains partial amounts, removes paid items, and supports separate central registers with inspection                                                                                                                                                                                           |
| `packages/reality-core/tests/test_membership_invitations.py`                                          | Spec 035                                                                                         | Owner authorization, invitation lifecycle, explicit acceptance, and membership reactivation proof                                                                                                                                                                                                                           |
| `packages/reality-core/tests/test_platform_admin_overview.py`                                         | `003`, Spec 036                                                                                  | Platform-admin authorization, platform metadata content, secret-presence disclosure limit, and migration-drift proof                                                                                                                                                                                                        |
| `packages/reality-core/tests/test_migrations.py`                                                      | Data Model/ADRs                                                                                  | Schema construction/backfill proof                                                                                                                                                                                                                                                                                          |
| `packages/reality-core/tests/test_postgresql_integration.py`                                          | PostgreSQL ADR                                                                                   | Integration proof; environment-dependent skip is not sole feature proof                                                                                                                                                                                                                                                     |
| `packages/reality-core/tests/test_database_config.py`                                                 | PostgreSQL ADR                                                                                   | PostgreSQL-only configuration proof                                                                                                                                                                                                                                                                                         |
| `packages/reality-core/tests/test_spec_policy.py`                                                     | `001-baseline-spec-coverage`                                                                     | Baseline structure and deterministic coverage regression proof                                                                                                                                                                                                                                                              |
| `packages/reality-core/tests/test_repository_layout.py`                                               | `021-deployable-app-layout`, `022-public-site`                                                   | Deployable-root, shared-core, Site/Web split, Compose, CI and command-path regression proof                                                                                                                                                                                                                                 |

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
| Browser builds           | PASS                      | `make web-build`                                                                                                                                                                     |
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

| Test family                                                 | Spec  | Coverage                                                                 |
| ----------------------------------------------------------- | ----- | ------------------------------------------------------------------------ |
| `packages/reality-core/tests/test_unified_workspace_api.py` | `221` | Legacy overview GET retirement; composable analytics retained            |
| `packages/reality-core/tests/test_reference_workspace.py`   | `140` | Reference roles, preservation, stale edits and canonical proposal replay |
| `packages/reality-core/tests/test_unified_workspace_api.py` | `140` | Scoped Analytics and Master data HTTP contracts                          |

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

| Artifact                                                                                   | Specification  | Proof                                                                                                    |
| ------------------------------------------------------------------------------------------ | -------------- | -------------------------------------------------------------------------------------------------------- |
| `docs/features/company-setup-demo.md`                                                      | Specs 146, 147 | Shared services and local integration contract                                                           |
| `docs/features/demo-data-catalog.md`                                                       | Spec 246       | Stable business-facing inventory of canonical demo journeys and expected outcomes                        |
| `docs/features/scheduled-jobs.md`                                                          | Specs 146, 147 | Shared services and local integration contract                                                           |
| `docs/features/payment_matching.md`                                                        | Spec 168       | Payment intake and matching contract; customer side implemented                                          |
| `packages/reality-core/tests/test_demo_data_settlement_plan.py`                            | Spec 168       | Settlement planner: weights, delays, stated amounts, payloads, normalisers                               |
| `packages/reality-core/tests/test_payment_intake.py`                                       | Spec 168       | Shared invoice/payment core, reference resolution, candidates, guard rails                               |
| `packages/reality-core/tests/scenarios/test_demo_order_to_cash.py`                         | Spec 168       | Order → invoice → payment story across all outcomes through public reads                                 |
| `packages/reality-core/tests/operational_exceptions/test_payment_differences_from_demo.py` | Spec 168       | Existing exception classes surface synthetic differences                                                 |
| `packages/reality-core/tests/test_company_setup.py`                                        | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_company_setup_api.py`                                    | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_company_setup_migration.py`                              | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_company_setup_unified.py`                                | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_data.py`                                            | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_data_api.py`                                        | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_data_compatibility.py`                              | Spec 256      | Live-source reference compatibility and stall state                                                      |
| `packages/reality-core/tests/test_live_source_recovery.py`                                 | Spec 256      | Schedule suspension, recovery and owner control                                                          |
| `packages/reality-core/tests/test_demo_data_generator.py`                                  | Spec 146       | Reproducible synthetic order plan: Poisson burst size on the hourly demand curve, weighted customer pool |
| `packages/reality-core/tests/test_demo_data_intake.py`                                     | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_data_security.py`                                   | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_execution_profile.py`                               | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_demo_profile_history.py`                                 | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_invitation_cleanup.py`                         | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_job_migration.py`                              | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_job_recovery.py`                               | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_job_registry.py`                               | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_job_timing.py`                                 | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_jobs.py`                                       | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_worker.py`                                     | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/test_scheduled_worker_deployment.py`                          | Specs 146, 147 | Company/source/scheduling service, adapter or migration regression                                       |
| `packages/reality-core/tests/scenarios/test_international_demo.py`                         | Spec 146       | Canonical operations and source lineage                                                                  |

Spec 146 FR-026–028: `test_company_setup_unified.py`, `test_playground_api.py`, `test_demo_data_intake.py`, `test_demo_data_api.py`; browser acceptance `apps/web/scripts/demo-live-browser.mjs` and `company-setup-unified-browser.mjs` cover compact Sandbox labeling, real-time import snapshots, preserved choices and safe controls.

| `packages/reality-core/tests/test_home_readiness.py` | Spec 149 | Volatile health freshness, private probes and scoped Home readiness |
| `docs/features/home-live-status.md` | Spec 149 | Home activity, volatile process readiness and portable deployment contract |
| `docs/features/engine-room.md` | Spec 266 | Live, value-free interactions per channel, owner-only reads, retention by the recording work |

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
| `packages/reality-core/tests/finance/test_payment_reads.py` | Spec 257 FR-026 | Strict incoming/outgoing payment filtering and rejection of legacy or unsupported filters |
| `packages/reality-core/tests/finance/test_party_balances.py` | Spec 170 | Party balances: open, overdue, credit and balance per party and currency, tool equals view, tenant-scoped |

| Feature                                               | Specification                                       | Verification                                                                                                                                        | Coverage                                                                        |
| ----------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Guided Fact rules (159)                               | `specs/159-guided-fact-rules/spec.md`               | `apps/web/scripts/guided-rule-draft.test.mjs`; `apps/web/scripts/guided-rules-browser.mjs`; `packages/reality-core/tests/test_reality_gap_rules.py` | Typed form preservation, source evidence, reviewed version lifecycle and replay |
| `packages/reality-core/tests/finance/test_opening.py` | `148-accounting-journal-cost-centers`               | FR-044–FR-048: four opening-position directions, coverage identity and normal settlement                                                            |
| `packages/reality-core/tests/finance/test_owner_handoff.py` | Spec 257 FR-007/FR-008 | Agent preparation, shared owner review descriptor, authenticated owner confirmation, proposal reconciliation and tenant isolation |
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

| Feature                        | Specification                                | Verification                                                                                         | Coverage                                                                                                                                |
| ------------------------------ | -------------------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Timeline recorder raster (162) | `specs/162-timeline-recorder-raster/spec.md` | `apps/web/scripts/flight-recorder-layout.test.mjs`; `apps/web/scripts/unified-inspector-browser.mjs` | Interval choice, per-interval columns, lane stacks and widening, header labels, prepend anchoring and auto-fill of a compact first page |

## Context Graph naming

| Feature                    | Specification                            | Verification                                                                                                               | Coverage                                                                |
| -------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Context Graph naming (163) | `specs/163-context-graph-naming/spec.md` | `apps/web/scripts/inspector-navigation.test.mjs`; `provider-site/scripts/site-contract.test.mjs`; both localization audits | Navigation label, public-site wording, invariant term in four languages |

## One page action bar

| Feature                   | Specification                            | Verification                                                                                                                                            | Coverage                                                                                   |
| ------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| One page action bar (165) | `specs/165-unified-page-actions/spec.md` | `apps/web/scripts/unified-app-contract.test.mjs`; `apps/web/scripts/action-discovery-browser.mjs`; register and page browser suites; localization audit | Primary/secondary/More actions rule, no direct slot writers, family labels, four languages |

## Open items default order

| Feature                        | Specification                                | Verification                                                                                                | Coverage                                                                                                      |
| ------------------------------ | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
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
- `packages/reality-core/tests/test_mcp_read_optional_arguments.py`: FR-017 and FR-024
  (with spec 267 FR-014); every MCP read tool called with its optional arguments left out
  behaves like its default, and `shipments_list` reads the register instead of failing.
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
- `packages/reality-core/benchmarks/ingest_cost/` and `packages/reality-core/tests/test_ingest_cost_benchmark.py`: FR-006 and the evidence for FR-001 and SC-001. The measurement records what one order, one invoice and one payment cost in queries, SQL time and reads per table, at a series of company sizes, through the real company setup, Demo Data connection, scheduler and worker. The tests hold what a measurement needs to stay trustworthy rather than measuring anything: that it refuses any database not named `reality_benchmark_*` and refuses even that one without `--confirm-disposable`; that cost is divided by the records a sweep produced, because one sweep delivers several orders; that a barren sweep is not divided by zero; that the tables a step read most are named; that the record carries the SC-001 ratio and states what it cannot prove; and that the
slowest statements are separated by span, so a statement of the sweep is never listed as
one of the interpreting — the confusion that made a demo generator's throttle look like a
problem with the intake.

- `packages/reality-core/tests/test_tenant_lifecycle.py::test_the_usage_summary_agrees_with_the_tables_it_summarises`: FR-002. The usage summary asks every table in one statement instead of twenty-four, so each figure is held against a count taken on its own, and the company-by-company call is held against the whole-instance one. Dropping a table from the union, or attributing one to the wrong figure, fails it — the two sabotages that were run, because a wrong total here is a number nobody could see was wrong.
- `packages/reality-core/tests/test_job_history_retention.py`: FR-005's retention, for the one table that grew without any bound. The tests are almost entirely about what is *kept*, because deleting rows is easy and never deleting something a reader can still be shown is the whole value: a failure is never forgotten, since a projection's freshness is read from exactly those; the queue's unfinished run stays, and cannot grow anyway because one unfinished refresh per projection is all the index permits; the most recent runs of each kind survive, counted per projection rather than per job type, so twenty of twelve projections together would not keep twenty of whichever refreshes most often; nothing finished within the last week is taken however many there are; a run an analysis points at is kept, because forgetting it would break a reference rather than free a row; and a run a person asked for keeps its request key, because `create_manual_run` answers a repeat by handing that row back and forgetting it would turn a retry into a second execution. One test holds the wiring itself — a retention rule nobody calls is a function, not a policy.
- `packages/reality-core/migrations/versions/0088_tenant_scoped_keys.py` and `packages/reality-core/tests/test_schema_indexes.py`: FR-005's first clause. Every company-scoped table is keyed by `(tenant_id, id)`, which is what PostgreSQL requires before it will partition one by company, and the 106 references that named `id` alone are composite so that a row cannot name a parent in another company. The migration is derived from the difference between the two schemas rather than written, so it cannot disagree with the models; what pins it is that a migrated database and the models agree on every primary key, foreign key and index. `test_schema_indexes.py` holds the rule against both revisions that own these indexes — 0059 gave every foreign key's first column one, 0088 replaced the narrower ones with composite — because neither owns the set alone, and holds that what a revision creates its downgrade takes away.
- `packages/reality-core/benchmarks/ingest_cost/storage.py` and the storage tests in `packages/reality-core/tests/test_ingest_cost_benchmark.py`: FR-005, which could not be argued about while nobody knew where the bytes were. Every checkpoint records the size of each table that grew, with rows, indexes and out-of-line storage kept apart because they are three different decisions — a table whose indexes outweigh its rows is an indexing question, not a tiering one — and which tenant-scoped tables their keys would let anyone partition. The tests hold the classification rather than any size: a table keyed only by `id` is reported as blocked and the constraint is named, a table whose every key names the company is not, a shared table without a company is never called blocked because it was never a candidate, and a uniqueness promise that must hold across companies (a token hash) appears exactly like a mechanical one so that only the name tells a reader it is a decision. A company with no orders yet is not divided by, and a record written before storage was measured still loads.
- `packages/reality-core/benchmarks/ingest_cost/compare.py` and the comparison tests in `packages/reality-core/tests/test_ingest_cost_benchmark.py`: SC-005 and User Story 5. Two runs are held against each other figure by figure, with counts required to be equal and timings held to a tolerance, because a count is the same arithmetic on any host and a millisecond is not. Every finding names the checkpoint, the step and the figure, so a difference is attributable to an intake step rather than to "the benchmark". Two runs of different commits, or with different numbers of checkpoints, are refused rather than diffed; a checkpoint that drifted by an order is reported and the comparison carries on, because one sweep delivers several orders and the fixture cannot land on 250 exactly. The tests also pin what the first comparison found: that a sweep must deliver exactly one record of any kind, and that no growth ratio is reported when the samples do not hold the same steps.

- `packages/reality-core/tests/test_projection_jobs.py::test_each_projection_behind_gets_its_own_run_and_is_not_queued_twice` and `::test_a_failure_is_recorded_against_one_projection_and_not_its_neighbours`: FR-004's run half. The first holds both directions of the split — a company behind on several projections gets a run each, and a projection whose run is already waiting is not enqueued again. The second is the reason for the split: a run is claimed and failed, and the projection it named is `failed` while its neighbours are not, which the shared run could not say. `test_projection_job_migration.py::test_downgrade_preserves_internal_job_history` now walks both refusals a downgrade meets: the queue cannot be squeezed back into one run per company while several are unfinished, and the internal history cannot be dropped at all.

- `packages/reality-core/tests/test_attention_reads.py::test_two_findings_of_one_class_are_ordered_by_date_and_not_by_record_id`: FR-002's first step for `exceptions`. Two promises of one class are built so that their dates and their record ids disagree, then the stored generation is held against the derivation's order. It fails when the reader's key loses `sort_at` — which is what the stored `position` used to carry, and what a narrowed refresh could never compute.

- `packages/reality-core/tests/operational_exceptions/test_class_clock.py`: FR-002/FR-004 for `exceptions`. Which classes answer differently when only the clock moves, measured by deriving one company twice four hundred days apart — three do. It also pins the twenty-eight classes the fixture does not bring about, so the gap in the measurement is visible rather than implied, and it refuses to pass when the probe moves nothing at all.

- `packages/reality-core/tests/operational_exceptions/test_class_clock.py` (the `next_clock_moment` tests) and `tests/test_projection_jobs.py::test_a_clock_refresh_waits_for_the_moment_something_can_change`: FR-004's cadence. The earliest dated moment inside the window is the answer, a date beyond the window does not delay the daily cap, a revised date is its own candidate, and — the test that stops the saving being bought with a late verdict — a promise falling due in five hours makes the projection pending in five hours rather than in a day. Ignoring the dated candidates and always waiting the full day fails three of them.

- `packages/reality-core/tests/test_incremental_derivation.py` (the exceptions section): FR-002's twelfth builder, which narrows by class. A warehouse event must leave the five money classes untouched and a document must reach all of them; declaring those classes dependent on movements fails both that test and the one that follows. A payment run, which names the company, narrows nothing and says so. And an exception that cleared is removed although nothing produced its row — the reason `covers` is read from the stored keys of the classes evaluated rather than taken from what the refresh produced.

- `packages/reality-core/tests/test_payment_intake.py::test_the_candidate_search_does_not_read_more_as_the_history_settles`: FR-001 in the measure a statement count cannot show. Twenty more settled invoices must not cost the candidate search more rows; the test counts rows read, because the search was already flat in statements while its work grew with the customer's history. It fails against the search that loaded every invoice.

- `packages/reality-core/tests/test_global_search_service.py::test_every_materialized_search_cte_carries_its_own_name`: the search's materialized CTEs must carry their family's name. SQLAlchemy keys anonymous constructs by `id(object)` and renders them `anon_1`, `anon_2`…, so two CTEs built at different moments share a name once the first object has been collected — and several of them meet in one `union_all`. The symptom is `CompileError: Multiple, unrelated CTEs found with the same name`, which appears and disappears with unrelated code; it surfaced in CI while the suite was green locally. Putting the unnamed CTE back fails this test and the canonical-authorities test beside it.

- `packages/reality-core/tests/test_company_purpose_once.py`: FR-001's per-transaction purpose. Four service calls in one transaction read what a company is for twelve times before this and twice after; a savepoint is its own scope and asks again on purpose, because an answer learned inside one must not outlive its rollback. Two rules keep the memory honest and are tested as rules: a company created later in the same transaction is still seen, because absence is never remembered, and a practice company is refused as often as it is asked.

## Composable analytics (185)

Spec 185 owns the analytics service, agent tools, private report configuration and workspace.

- `docs/features/analytics.md` — `specs/185-analytics-workspace/spec.md`, implemented Analytics, agent, privacy, observation, Web and persistence contract.

## Reporting graph (224)

Spec 224 owns the declared property graph over the typed tables, the traversal that is
checked before it becomes a query, and the two surfaces that author one.

- `packages/reality-core/tests/test_reporting_graph_declaration.py` — `specs/224-native-reporting-platform/spec.md`, FR-001–002, FR-005, FR-009, FR-013 and DR-002.
- `packages/reality-core/tests/test_reporting_graph_coverage.py` — `specs/224-native-reporting-platform/spec.md`, FR-001–002, FR-013 and DR-003.
- `packages/reality-core/tests/test_reporting_graph_traversal.py` — `specs/224-native-reporting-platform/spec.md`, FR-003–005, FR-010 and DR-001–002.
- `packages/reality-core/tests/test_reporting_graph_isolation.py` — `specs/224-native-reporting-platform/spec.md`, FR-006, FR-011 and SC-005.
- `packages/reality-core/tests/test_reporting_graph_surfaces.py` — `specs/224-native-reporting-platform/spec.md`, FR-007 and FR-009.
- `packages/reality-core/tests/test_reporting_graph_tools.py` — `specs/224-native-reporting-platform/spec.md`, FR-007, FR-009 and FR-011.
- `packages/reality-core/tests/test_reporting_graph_lifecycle.py` — `specs/224-native-reporting-platform/spec.md`, FR-008 and FR-012.
- `apps/web/scripts/graph-steps.test.mjs` — `specs/224-native-reporting-platform/spec.md`, FR-015, FR-017, FR-019, FR-020; the question the steps compile to, and what a change to one step does to the rest.
- `apps/web/scripts/proposal-cards.test.mjs` — `specs/224-native-reporting-platform/spec.md`, FR-008; a proposal a person cannot dismiss never goes away.
- `packages/reality-core/tests/test_every_module_imports.py` — `specs/224-native-reporting-platform/spec.md`, FR-016; every module imports, so a lazy import cannot hide a removal.
- `apps/web/src/unified/analytics/GraphExplorer.tsx` — `specs/224-native-reporting-platform/spec.md`, FR-007 and FR-010 on the browser surface.

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

- Spec 204: `packages/reality-core/tests/scenarios/test_international_demo.py` proves
  the seeded sales invoices settle in three states with a receivable smaller than what
  was invoiced, six purchase orders across three suppliers cover the whole chain with
  their payables settled, partly settled and untouched, received quantities follow the
  goods receipts, two companies settle identically, and the profile authority gained
  settlement and nothing beyond it.

- Spec 206: `packages/reality-core/tests/test_chat_latency.py` proves bounded history and
  inventory query counts with tenant/value parity; `packages/reality-core/tests/test_chat_streaming.py`
  proves complete provider frames, fragmented tool arguments, caching, redacted logs and HTTP
  stream isolation. `apps/web/scripts/chat-stream.test.mjs` and `chat-stream-browser.mjs`
  prove early text, reset, incomplete-stream failure and final reconciliation.

- Spec 207: `packages/reality-core/tests/test_scheduled_job_startup.py` covers bounded
  initial timing, frozen inputs, controls and downtime; `packages/reality-core/tests/test_demo_data_startup.py`
  covers normal source intake of the three initial orders, replay and return to stochastic
  demand. `apps/web/scripts/live-simulation-header-browser.mjs` covers visibility,
  current-company navigation, stale responses, responsive placement and reduced motion.

- Telemetry: `packages/reality-core/tests/test_telemetry.py` proves the instrumentation is
  inert without an OTLP endpoint (no SDK import, no middleware, no providers), that the
  resource carries an explicit `service.instance.id` from the pod name rather than a random
  per-process UUID, that HTTP metrics key on the route TEMPLATE so many distinct ids collapse
  to one series, that user-entered query strings never reach a metric attribute, and that
  seconds-valued histograms carry seconds-shaped bucket boundaries rather than the SDK's
  millisecond defaults.

## Operational quick previews (209)

[Spec 209](../specs/209-operational-previews/spec.md) defines business-first inline summaries across Sales, Purchasing, Warehouse and Finance without schema changes. Service and adapter evidence: `packages/reality-core/tests/test_operational_previews.py` and `packages/reality-core/tests/test_reference_workspace.py` (master-data fields, names and unchanged revision identity); responsive/localized browser evidence: `apps/web/scripts/operational-previews-browser.mjs`. Verification: [report](../specs/209-operational-previews/verification.md).

## Record provenance and source addressing (211)

[Spec 211](../specs/211-record-provenance/spec.md) makes record origin visible across the
workspace, extends the source-record inspection with the retained payload and its
interpretation outcome, and adds an optional external address so a record can be opened in
the system that owns it. Service and adapter evidence:
`packages/reality-core/tests/test_provenance.py` (origin batched per page, the manual-origin
fallback, the retained textual code join, address validation and template resolution, the
bounded payload, interpretation outcomes, contributing systems, and that one installed
instance belongs to exactly one connector shell);
`packages/reality-core/tests/test_source_system_addressing_migration.py` (column roundtrip
and the one-time unambiguous `connector_code` backfill). Localized and responsive browser
evidence: `apps/web/scripts/record-provenance-browser.mjs` and
`apps/web/scripts/provenance-labels.test.mjs`. Verification:
[report](../specs/211-record-provenance/verification.md).

## Refresh feedback on the stored-result notice (180, FR-009)

[Spec 180](../specs/180-attention-from-stored-exceptions/spec.md) FR-009 makes the
stored-result notice report what Refresh did: an unavailable control and a busy notice
while the read is in flight, then either a newer generation or an explicit statement that
the stored result is unchanged, plus the backlog where the generation is behind the event
stream. Refresh still only reads. Browser evidence:
`apps/web/scripts/projection-freshness-browser.mjs` (in-flight state, both outcomes, the
backlog and all four languages).

## Unified tool catalog (226)

`specs/226-unified-tool-catalog/spec.md` FR-001–007 are covered by
`packages/reality-core/tests/test_tool_catalog.py`, existing application catalog/MCP tests,
`apps/web/scripts/tool-catalog.test.mjs`, `apps/web/scripts/inspector-navigation.test.mjs`
and `apps/web/scripts/unified-tool-catalog-browser.mjs`.

- `packages/reality-core/tests/test_analysis_builder.py` — `specs/228-guided-analysis-builder/spec.md`, FR-002, FR-004, FR-007, FR-008, FR-009, FR-011, FR-012.

- `apps/web/scripts/analysis-builder-state.test.mjs` and `apps/web/scripts/graph-steps.test.mjs` — `specs/228-guided-analysis-builder/spec.md`, FR-003, FR-004, FR-006, FR-007, FR-008, FR-009, FR-013.


## Business analysis coverage (spec 229)

`packages/reality-core/tests/test_reporting_graph_expansion.py` covers FR-001–006:
typed documents and positions, tenant-scoped parent predicates, reverse same-table
links, received signs, catalog vocabulary, all-node and all-edge query execution.
The analysis declaration includes `shipment`, `shipment_package`, `shipment_event`,
`shipment_event_supersession` and `return_announcement`; their authority remains the
existing shipping/returns domain. It also exposes financial components and opening
evidence without inventing aggregate financial state.

## Finance and calendar analysis (spec 230)

`packages/reality-core/tests/test_analysis_finance_dates.py` covers FR-001–005: canonical aging, reversals, opening debts, currencies, tenant boundaries, derivation limits, signed ledger sums and guarded calendar dates. Web period contracts cover date-only bounds.

## Current stock analysis and templates (spec 231)

`packages/reality-core/tests/test_analysis_warehouse.py` covers FR-001–004: stock parity
with canonical inventory and Warehouse, reservation lifecycle, transfers/corrections,
negative/zero stock, tenant/unit/time/fanout boundaries, bounded inputs, constant read
cost, localized template execution and chat compilation.

## Balances, exact inventory and effective-date analysis (spec 232)

`packages/reality-core/tests/test_analysis_positions_history.py` covers FR-001–006:
unpaged canonical balances, currencies, exact tracking/null buckets, allocation
endpoints, reversals, stock corrections, cutoff and opening boundaries, tenant scope,
fanout, input bounds, chat validation and Cypher round trips. Reporting graph contracts
execute every template. `apps/web/scripts/analysis-snapshot.test.mjs` checks visible
snapshot inputs, replacement of the selected date and preservation of unrelated filters.

## Order journey timeline (spec 233)

`packages/reality-core/tests/test_order_journey.py` covers FR-004–008/011: exact order membership, shared-reference exclusion, typed links, bounded pagination, read-only HTTP and tenant isolation. Frontend `order-journey-layout.test.mjs` and `order-journey-browser.mjs` cover FR-001–010 and SC-001–004. Spec233 supersedes spec162 active Timeline presentation.

## 234 — What an analysis costs

`packages/reality-core/tests/test_analysis_derivation_cost.py` covers FR-001–008: an
ordinary path still compiles to exactly one statement; a derivation stays under the
declared ceiling; a filter reaches the canonical service already narrowed and the
narrowed answer matches the unfiltered one for the same party; an unnarrowed question
still reaches every party; one register asked for twice in a request is derived once.
The cost is pinned in statement counts and derivation inputs rather than wall-clock, so
it means the same on any machine. `packages/reality-core/tests/test_analysis_finance_dates.py`
covers FR-005: an impossible day is refused as a business error and an absent one is
still reported under an explicit unknown group.

## 236 — An analysis you request and collect

`packages/reality-core/tests/test_requested_analysis.py` covers FR-001–007: a question
within the budget is answered in the request and records nothing; a question refused for
its size is accepted for the worker, names the limit that sent it there, and is idempotent
on its request id; every refusal that is a judgement about the question — an unknown node,
an unknown measure, a fan-out — still arrives at request time, and the deferring set is
pinned to exactly the three size codes; the worker answers and the asker collects the rows
with the question, the moment and the model version beside them; a question that still
cannot be answered records why on its row while the run itself succeeds; membership is
checked again when the worker runs, because the minutes between asking and running are
when access changes; a stranger can neither request nor collect; and an uncollected answer
is removed when it expires rather than lingering as a current figure. FR-008: an agent
proposes the request and a person confirms it; the proposal record carries the question
sealed rather than in the open, because a proposal is company-visible and the question is
the asker's; a question the model cannot express is refused when the proposal is prepared,
not minutes later; and the tool refuses direct execution without a confirmation.

## Global command palette (spec 237; implementation in progress)

Feature contract: `docs/features/command-palette.md`.

The following test families provide incremental evidence; they do not certify the
remaining browser, workload and final review acceptance gates.

| Test family | Requirement evidence |
|---|---|
| `packages/reality-core/tests/test_global_search_matching.py` | FR-007/008/021, DR-004: matching corpus, typed bounds and SQL parity |
| `packages/reality-core/tests/test_global_search_migration.py` | DR-005: migration round trip and normalization support |
| `packages/reality-core/tests/test_global_search_service.py` | FR-004/005/009, DR-003/004: exact records, complete pagination and canonical identity |
| `packages/reality-core/tests/test_global_search_access.py` | FR-011/014/017: cross-tenant joins, private reports, lesson scope and cursor sessions |
| `packages/reality-core/tests/test_global_search_web.py` | FR-004/011/012: typed read-only adapter and safe responses |
| `packages/reality-core/tests/test_global_search_worklists.py` | FR-016: canonical overdue filtering before pagination |
| `packages/reality-core/tests/test_global_search_benchmark.py` | SC-003: full-population risk probe and disposable dataset guards, not latency acceptance |


## 241 — Derive by change, not by company

`packages/reality-core/tests/test_incremental_derivation.py` covers FR-001, FR-002 and
FR-006: incremental refresh and full rebuild leave identical stored rows, compared
without the evaluation timestamp an exception carries, because the property is about
what the rows say and not about the second they were derived. A positive control makes
a builder withhold one row — exactly the failure a wrong narrowing produces — and
insists the comparison notices, so the property is known to be guarding something
rather than passing for the wrong reason. A third test refuses to let a projection sit
outside the property by producing no rows for the fixture. The change set is held to
its three refusals: an event type the catalog does not list, a window with more changed
records than are worth visiting one at a time, and a window with no new events. A
refresh reports why each projection narrowed or did not, so a feature whose builders all
decline looks like that rather than like success.

The same file holds one section per narrowed builder, and each one carries the question
that builder's subjects raise. For supply and demand that question is reach rather than
creation: a delivery hold is recorded against a party, so the test insists the articles
that party is waiting for come back blocked, and both halves of that answer — resolving
the party to its articles, and reading the holds at all — were disabled in turn and
watched to fail. A cancelled promise is the second control: the narrowed path reads the
open promises of an article and nothing else, and dropping that predicate is a difference
the comparison catches.

For the fulfillment queue and its blockers the question is disappearance. A shipment that
closes an order's last promise, and a hold that is released, both leave a stored row with
nothing to replace it, so two tests insist the row goes and both fail when the refresh
speaks only for the rows it produced. A third moves a shipment from one order to another
through a movement correction — the replacement is booked against a different promise and
the service settles both — and it fails when the stored correction is not followed. One
more test holds the declared list of blocking reasons against the rules that produce them,
because a reason the list does not name is a blocker that can never be deleted.

The register of promises is tested against the queue it resembles: the order that is over
leaves the queue, the promise that was cancelled stays in the register and says so. Two
tests state what this projection cannot bound — renaming an article reaches every promise
ever made for it, including the fulfilled one, and past the ceiling the same subject makes
the builder decline. Both fail when the article is not resolved to its promises.

The timeline is where a missed record shows as a line of history that is simply absent, so
two tests watch the producers that create records no event names — a movement correction,
which appends a compensating and a replacement movement, and a ledger reversal, whose
counter-entries sit in a new posting group — and both fail when the stored relation is not
followed. A third test renames a party and insists the refresh produces no rows and speaks
for none, because no timeline row prints a party: the one projection that can say nothing
of its own changed, and must not re-read a company's history to say it.

The open items are tested through the two records that move an invoice without naming it:
a settlement allocation, which names two ledger entries, and a payment term, which a party
lends to its documents. Both tests fail when the resolution is removed. A third watches the
row that says `reversed`. The sabotage pass earned its keep negatively here as well — it
showed that following the ledger reversal changed no outcome, because the event names the
original posting group and that group's entries carry the document, so the lookup was
dropped rather than kept for symmetry. The hop that *is* needed came from the suite
instead: `test_finance_partial_refresh_preserves_other_checkpoints_and_tracks_settlement`
reverses a payment and reads the invoice, and a fourth test in
`test_incremental_derivation.py` now states the same thing as a property — an allocation
ties two documents together, so un-settling one gives the other its open amount back.

The payments are tested on the hop that is easy to miss: an allocation names the control
entry of the payment's posting group, not the cash entry the row is keyed by, and a test
that allocates a payment against an invoice fails when the resolution stops at the entry
the event named. A second test reverses a payment and insists nothing is left to allocate,
and a third reverses the *invoice* and insists the payment gets its allocation back — the
group reversed there holds no cash entry, so it is the allocation that carries the change
across, and removing that hop fails the test.

`packages/reality-core/tests/test_working_set.py` covers 181 FR-003: a derivation about
open work must not read the work that is finished. Sixty more cancelled promises are added
to a company and what every derivation reads is compared before and after. Each projection
is either declared to be about open work or carries a written reason for reading what is
finished, so no projection sits outside that decision unnoticed, and a control insists that
*something* grew — otherwise the silence of the others would mean nothing.

`packages/reality-core/tests/test_clock_sensitivity.py` covers FR-004: which projections
answer differently when only the clock moves. The membership of the cadence list is
measured rather than recalled — every projection is derived twice four hundred days
apart with no event in between — and the exceptions projection is the control, because
if the faked clock stopped reaching the derivations this file would approve of anything.
Two projections that were rebuilt every sixty seconds do not read the clock at all and
no longer are; a final test insists that a refresh with no events behind it rebuilds only
the one projection that does.

`packages/reality-core/tests/test_refresh_units.py` covers 181 FR-004 and SC-003: a
company with no change and no due date must cause no work. It asserts both directions —
a quiet company is not offered to the scheduler, and a company that changed, whose
cadence came round, or whose projections were never built, is — because a selection that
returns nothing is cheap and useless. Two statement counts pin the shape rather than the
speed: asking one company what is behind is one read where it used to be twelve, and
discovering what to do across the instance is a fixed number of statements however many
companies exist. A last test holds the company's recorded event progress against the
events themselves, because the selection believes that number.
+## Costing architecture qualification (spec 242, Phase 0 only)

`packages/reality-core/tests/test_costing_spike_contract.py` proves received-cost
composition, signed allocation, FIFO/specific identity, return provenance and cumulative
rounding for FR-002/003/005/007/020/021/022. These are experimental calculations, not
implemented product cost services.

`packages/reality-core/tests/test_costing_spike_postgres.py` proves fixed experimental
cardinalities, tenant isolation, rollback, scoped replacement and deterministic replay
for FR-018 and DR-001–005. Benchmark evidence distinguishes exploratory measurements
from the still-pending full architecture qualification.

Spec 242 continuation extends those same test families with return COGS reversal,
distributed split/partial matching, stale/live responses, failed refresh recovery,
concurrent intake with frozen-revision publication, and sustained mixed-load generation.
These remain experiment proofs, not production adapter or accounting acceptance.

Spec 242 scoped-live continuation adds proofs to the existing PostgreSQL test family:
unrelated-pool currentness, exact bounded direct/projected parity, financial and movement
limit refusal before replay, snapshot consistency, unchanged publication state, and
refusal of unresolved late targets. These do not certify product adapter availability.

`packages/reality-core/tests/test_costing_spike_jobs.py` covers spec 242 FR-018 and
DR-004/005: staged visibility, frozen revisions, indivisible-pool refusal, foreign
scope, shared claim rollback/retry/replay, archived-tenant authorization, unchanged
normal registry, canonical monthly relation parity, real child timeout/retry, and
repeatable-read consistency across atomic publication. This remains an isolated
shared-worker qualification adapter, not production registration.

`packages/reality-core/tests/test_costing_product_qualification.py` proves the integrated
fixture J release decision fails closed for reduced profiles, prototype entrypoints,
missing evidence, tenant leaks, checksum drift and every FR-018 budget.
`packages/reality-core/tests/test_costing_product_workloads.py` proves the timed adapter
uses the shared cost-query, graph, Exceptions and MCP product entrypoints with the exact
tenant scope. These tests qualify the harness contract only; the dedicated full-profile
reference-host run remains required.


## Receipt acquisition costs (spec 242; approved first production slice)

Feature contract: `docs/features/receipt-costing.md`.

| Test family | Requirement evidence |
|---|---|
| `packages/reality-core/tests/test_costing_domain.py` | FR-002/003/020/021/022: signed contribution, source-share conservation, tax buckets and Decimal precision |
| `packages/reality-core/tests/test_cost_allocation.py` | FR-002/003/013/022: signed largest-remainder allocation, stable opaque-ID ties, residual conservation and exact conversion precision boundaries |
| `packages/reality-core/tests/test_cost_allocation_services.py` | FR-002/003/019/020/022: owner-confirmed weighted receipt allocation, explicit driver semantics, exact persisted shares, tax-bucket and tenant refusals |
| `packages/reality-core/tests/test_cost_conversion_migration.py` | FR-002/013/019/022, SC-003: immutable source-backed conversion revisions, exact ratio precision, nullable same-tenant attribution links and protected rollback |
| `packages/reality-core/tests/test_cost_conversion_services.py` | FR-002/013/016/019/022: owner-confirmed source-backed conversion history, preserved original shares, read-time converted acquisition/DB2 observations and refusal to use unit authority as currency authority |
| `packages/reality-core/tests/test_costing_migration.py` | DR-001–005: all composite authority foreign keys, upgrade, empty downgrade and refusal to erase retained history |
| `packages/reality-core/tests/test_costing_services.py` | FR-001–003/007/014–016/019: actual receipt A, explicit category review, tax, late costs, immutable replacement/correction history, transaction rollback and foreign authority refusal |
| `packages/reality-core/tests/test_costing_tools.py` | FR-016/019/027: actual application/MCP dispatch, explicit owner confirmation, replay, demotion and foreign tenant scope |
| `packages/reality-core/tests/test_demo_costing_profile.py` | Spec 146 FR-026/SC-007 and spec 243 FR-001–011/DR-001–005: international-v3 replay/authority, six exact source-backed contribution outcomes with varied selling costs, deliberate missing cost and signed late-cost return |
| `packages/reality-core/tests/test_carrying_value_domain.py` | FR-009/015/022, SC-001/003: explicit write-down/recovery reconciliation, exact predecessor scope, precision and acquisition-cost ceiling |
| `packages/reality-core/tests/test_carrying_value_migration.py` | FR-009/019, SC-003: guarded assessment schema, shortest same-tenant links, immutability and protected rollback |
| `packages/reality-core/tests/test_carrying_value_services.py` | FR-009/015/019, SC-001/003: owner-confirmed preview/execution, source/member scope, staleness, bounded recovery and current/historical acquisition-to-carrying reads |

Retained first-slice tables: `cost_attribution_part`, `cost_attribution_revision`, `cost_component_basis`, `cost_component_replacement`, `cost_correction_basis`, `cost_input_manifest`, `cost_manifest_attribution`, `cost_manifest_component`, `cost_manifest_correction`, `cost_manifest_receipt`, `cost_manifest_replacement`, `cost_receipt_basis`, `cost_scope_review`, `cost_scope_review_category`.

### Spec 242 inventory calculation foundation

`packages/reality-core/tests/test_inventory_costing.py` covers FR-004–007/017/018/022:
explicit FIFO/specific calculation, stock/consumption conservation, return-time order,
exact original receipt provenance, losses/supplier returns, unknown-cost coverage,
late-cost immutable replay, monetary residuals and bounded work. This pure domain
foundation does not establish company policy, economic ownership, admitted movement
history or a public inventory/DB application surface.

### Spec 242 reviewed inventory services

`packages/reality-core/tests/test_inventory_costing_services.py` covers FR-004–008,
FR-014–019/022/027: bounded complete pool admission, explicit FIFO/owner/history policy,
receipt scope reaffirmation, current/stale/frozen reads, conservation, late costs,
corrections, retained units/event ordering, exact membership integrity, owner confirmation,
foreign scope refusal, rollback and actual application/MCP dispatch.
`packages/reality-core/tests/test_inventory_costing_migration.py` covers DR-001–005:
static inventory schema, composite tenant FKs, empty rollback and retained-history
rollback refusal. Tables: `cost_policy_revision`, `cost_movement_basis`,
`cost_ownership_revision`, `cost_opening_basis`, `cost_inventory_review`,
`cost_inventory_ownership_part`, `cost_inventory_member`.

### Spec 242 contribution calculation foundation

`packages/reality-core/tests/test_contribution.py` covers FR-010–014/016/022:
commercial_v1 DB1/DB2 arithmetic, independent actual/review coverage, null-preserving
partial subtotals, aggregate rates, signed shares, stable grouping/unassigned dimensions,
currency/unit/context separation, trace retention, precision, cutoff and bounded work.
This pure kernel does not establish revenue matching or expose company DB reporting.
`packages/reality-core/tests/test_commercial_matching_migration.py` covers the approved
append-only partial commercial matching authority, tenant-composite FK parity, sealed SQL
immutability, empty rollback and populated downgrade refusal for
`cost_commercial_match_revision`, `cost_commercial_inventory_part` and
`cost_commercial_direct_part`.
`packages/reality-core/tests/test_commercial_matching_services.py` covers
FR-002/003/007/010/011/017/019/022: owner-confirmed admission, split/cross-line
capacity conservation, deterministic frozen inventory reads, complete direct service,
shipping, kit and production inputs, signed credit/return matching, free goods,
explicit unresolved WIP, rematch capacity release, historical replay, tenant isolation
and direct service/Application Tool/MCP parity without stored derived cost or margin.

### Spec 242 contribution SQL aggregation

`packages/reality-core/tests/test_contribution_aggregates.py` covers FR-011/012/014/022:
actual PostgreSQL parity with the domain kernel for all 256 input-state combinations,
partial same-slice margins, independent DB1/DB2 coverage, preview/empty scope,
signed shares, weighted aggregate rates and exact half-even ties/large numeric values.
The internal SQL helper does not admit a tenant/report population or publish graph measures.

### Spec 242 current contribution preview

`packages/reality-core/tests/test_contribution_services.py` covers FR-010/011/014/016/019:
exact current invoice/order/commitment/shipment traversal, received net evidence, reviewed
consumption, unknown commercial/selling coverage, tenant/tool/MCP parity, no writes,
ambiguous/stale scope and concurrent-input refusal. No finalized or historical DB claim.

### Spec 242 confirmed single-line contribution

`packages/reality-core/tests/test_contribution_reviews.py` covers FR-007/010–016/019/022:
owner confirmation, exact candidate binding, final DB1/independent DB2 gaps, immutable
historical replay, late-cost reaffirmation, no full-quantity reuse, source protection,
foreign scope, rollback, read-only behavior and actual application/MCP parity.
`packages/reality-core/tests/test_contribution_migration.py` covers DR-001–005:
static migration, composite tenant FKs, empty rollback and retained-history refusal.
Tables: `cost_revenue_match_basis`, `cost_contribution_review`.

### Source-backed selling costs and reviewed DB2 (234 continuation)

Authority: `specs/234-inventory-cost-contribution/contracts/selling-service.md`.
Tables: `cost_selling_attribution_part`, `cost_selling_review_category`, `cost_selling_review_member`.
Tests: `packages/reality-core/tests/test_selling_costs.py`,
`packages/reality-core/tests/test_selling_migration.py`.

### Retained cost record inspection (234 T078)

Authority: `specs/234-inventory-cost-contribution/contracts/record-inspection.md`.
Tests: `packages/reality-core/tests/test_cost_records.py`. Existing cost authority tables
are read through fixed allowlists; no new storage or valuation rule.

Retained query context: `packages/reality-core/tests/test_cost_query.py` (234).

Stored inventory publications, including assessment-bound carrying snapshots and
replay-free historical reads: `packages/reality-core/tests/test_inventory_generations.py`
and `packages/reality-core/tests/test_inventory_generation_migration.py` (234
FR-007/014/016/018/019). Three disposable cache tables and owner-authorized shared jobs;
retained review authority remains unchanged. Tables: `cost_inventory_generation`,
`cost_inventory_snapshot`, `cost_inventory_publication`.

Generation publication guard: `packages/reality-core/tests/test_cost_generation.py`
(242 FR-007/012/014/018, T101–T103). Pure domain decisions only; production
publication transactions, shared workers and canonical relations remain T080.

### Spec 242 joint contribution confirmation

`packages/reality-core/tests/test_contribution_batch_review.py` covers
FR-007/011/012/014/015/016/019: genuine two-item inventory/revenue confirmation,
shared action/event/knowledge time, independent selling coverage, exact replay and
historical member reads, complete rollback, stale/revoked/foreign refusal, request
bounds and isolated cross-member compatibility/disjoint-shipment guards.
The operation retains selected scope authority; it does not publish a report cache.


### Spec 242 stored joint contribution observations

`packages/reality-core/tests/test_contribution_generations.py` covers
FR-007/011/012/014/016/018/019/022: exact real joint membership, persisted/SQL/domain
parity, independent missing selling coverage, bounded historical reads without replay
or autoflush, stable later knowledge, corruption/foreign refusal, atomic failure,
concurrency and the shared owner-authorized worker.
`packages/reality-core/tests/test_contribution_generation_migration.py` covers the two
disposable tables `cost_contribution_generation` and `cost_contribution_snapshot`: static
migration, tenant foreign keys, populated cache rollback and
unfinished worker downgrade refusal. Public DB graph measures remain deferred.

| Historical contribution graph admission, coverage, saved/HTTP reports | 242 FR-012/014/022 | `packages/reality-core/tests/test_contribution_graph_reporting.py` |
| Tenant-scoped contribution confirmation discovery | 242 FR-012/014/022 | `packages/reality-core/tests/test_contribution_review_options.py` |
| Selected contribution freshness and final read cursor, concurrency, historical independence | 242 FR-007/014/018 | `packages/reality-core/tests/test_contribution_current.py` |
| Exact company-generation population closure and independent financial coverage | 242 FR-007/012/014/018 | `packages/reality-core/tests/test_cost_population.py` |

| Current source-backed company census, unreviewed scope, MVCC, bounds and tenant isolation | 242 FR-007/014/018 | `packages/reality-core/tests/test_cost_census.py` |

| Manifest-bound company publication validation and selected-scope separation | 242 FR-007/012/014/018 | `packages/reality-core/tests/test_company_cost_publication.py` |


Retained company discovery (242 FR-007/014/018/019): `cost_company_census`,
`cost_company_census_movement`, `cost_company_census_document`,
`cost_company_census_line`, `cost_company_census_source`. These retain current observed
values and typed source references, not approved costs or historical financial knowledge.

| Verification family | Specification | Tests |
|---|---|---|
| Atomic capture, frozen values, replay, SQL immutability and scoped member inspection | 242 FR-007/014/018/019 | `packages/reality-core/tests/test_cost_census_storage.py` |
| Typed retention schema, restricted downgrade and migration parity | 242 FR-007/019 | `packages/reality-core/tests/test_cost_census_migration.py` |
| Exact snapshot serialization and byte bounds | 242 FR-007/018/022 | `packages/reality-core/tests/test_cost_census_serialization.py` |

| Captured-time review resolution, cutoff/membership gaps and no future approval | 242 FR-007/012/014/019 | `packages/reality-core/tests/test_cost_census_resolution.py` |

| Proved contribution-only events preserve unrelated captured financial inputs | 242 FR-007/014/019 | `packages/reality-core/tests/test_cost_review_relevance.py` |
| Common captured review vector binds exact subjects, independent coverage and gaps without historical/publication claims | 242 FR-007/012/014/019 | `packages/reality-core/tests/test_cost_captured_basis.py` |
| Retained captured review selection, version integrity, atomicity and pinned replay | 242 FR-007/012/014/019 | `packages/reality-core/tests/test_cost_captured_basis_storage.py` |
| Captured-basis typed migration, tenant constraints and protected downgrade | 242 FR-007/012/014/019 | `packages/reality-core/tests/test_cost_captured_basis_migration.py` |

Retained captured review selection (242 FR-007/012/014/019): `cost_captured_basis`,
`cost_captured_inventory_basis`, `cost_captured_contribution_basis`. Schema/immutability
and scoped retain/read/replay proofs are in test_cost_captured_basis_migration.py and
test_cost_captured_basis_storage.py; retained selection grants no company publication.

| Captured known subtotals preserve partitions, unsupported rows and independent DB coverage | 242 FR-007/011/012/014/019 | `packages/reality-core/tests/test_cost_captured_summary.py` |

| Fixed captured report storage, publication CAS, pagination, tenant boundaries and cache disposal | 242 FR-007/012/014/018/019 | `packages/reality-core/tests/test_captured_report.py` |
| Fixed captured generation graph/tool/HTTP reads and saved-analysis identity retention | 242 FR-012/014/016/018/019/023 | `packages/reality-core/tests/test_captured_report_graph.py` |
| Sealed captured-generation discovery, tenant-safe cursors and Analysis selection | 242 FR-012/014/016/019/023/024 | `packages/reality-core/tests/test_captured_report_options.py`; `apps/web/scripts/analysis-builder-state.test.mjs` |
| Owner-authorized idempotent captured-report worker build without publication | 242 FR-007/014/018/019 | `packages/reality-core/tests/test_captured_report_jobs.py` |
| Owner-authorized captured-report CAS publication worker with stale-request refusal | 242 FR-007/014/018/019 | `packages/reality-core/tests/test_captured_report_jobs.py`; `packages/reality-core/tests/test_captured_report.py` |
| Retained exact financial company manifest and disposable generation schema (`cost_company_manifest`, `cost_company_inventory_input`, `cost_company_contribution_input`, `cost_company_generation`, `cost_company_inventory_result`, `cost_company_contribution_result`, `cost_company_publication`) | 242 FR-007/012/014/018/019 | `packages/reality-core/tests/test_company_generations.py`; `packages/reality-core/tests/test_company_generation_migration.py` |
| Owner-authorized exact company-manifest admission, explicit unknowns, gap binding, replay and atomic refusal | 242 FR-007/012/014/019 | `packages/reality-core/tests/test_company_generation_manifest.py` |
| Deterministic company-generation chunks, explicit unknown completion, cache integrity, scope-keyed CAS publication and owner-authorized shared jobs | 242 FR-007/012/014/018/019 | `packages/reality-core/tests/test_company_generation_jobs.py` |
| Fixed-generation company pages, totals, coverage and SELECT-only reads | 242 FR-012/014/018/019 | `packages/reality-core/tests/test_company_generation_reads.py` |
| Fixed company-generation graph context, grouped values, discovery and saved identity | 242 FR-012/013/014/016/023/024 | `packages/reality-core/tests/test_company_generation_graph.py` |
| Published company-generation identity and ready/pending/unavailable freshness as a protected cost-finding prerequisite, without activating findings | 242 FR-012/014/018/025 | `packages/reality-core/tests/test_company_generation_prerequisites.py` |
| Shared cost-finding derivation: unsold gaps, unassigned components, stale review identity, supported negative DB1, clearing, pending preservation and tenant isolation | 242 FR-014/015/018/025 | `packages/reality-core/tests/test_cost_findings.py` |
| Local product-qualification orchestration, retained-manifest reconstruction, concurrent refresh reads and evidence capture | 242 FR-007/012/014/018/019/022 | `packages/reality-core/tests/test_costing_product_runner.py` |

Captured report cache tables (242 FR-007/012/014/018/019): `cost_generation`,
`cost_inventory_row`, `cost_contribution_row`, `cost_publication`. Migration parity,
immutable sealing, typed membership, publication and retained-input survival are proved
in test_captured_report.py. Cache publication grants no company financial approval.

| Inventory batch generation orchestration and publication | 242 FR-007/014/018/019 | `packages/reality-core/tests/test_inventory_batch_generations.py` |
| Atomic multi-item inventory review confirmation | 242 FR-007/014/018/019 | `packages/reality-core/tests/test_inventory_batch_review.py` |
| Inventory costing reporting-graph relation | 242 FR-012/013/014/016 | `packages/reality-core/tests/test_inventory_costing_relation.py` |
| Stored inventory graph reporting and tenant boundaries | 242 FR-012/014/016/018 | `packages/reality-core/tests/test_inventory_graph_reporting.py` |
| Tenant-scoped inventory review discovery | 242 FR-012/014/022 | `packages/reality-core/tests/test_inventory_review_options.py` |
| Current and historical inventory snapshot selection | 242 FR-007/014/018 | `packages/reality-core/tests/test_inventory_snapshot_selection.py` |

| Isolated job children inherit the interpreter's bytecode policy, so a signed or read-only installation is never written into | 240 FR-010 | `packages/reality-core/tests/test_job_runner_process.py` |
| Process-local desktop master-key admission refuses replacement, invalid keys, missing handoff and cross-installation resolution while retaining hosted configuration | 240 FR-006/SC-005 | `packages/reality-core/tests/test_key_provider.py` |
| Private PostgreSQL generations adopt Increment 1 bytes once, reject escaping pointers, retain active data on staged failure and switch only validated generations atomically | 240 FR-007/SC-002 | `apps/desktop/tests/test_recovery.py` |

### Spec 247 commercial edge workflows

| Verification family | Specification | Tests |
|---|---|---|
| Dunning with a stated fee and reversal, customer/supplier deposits, customer bad debt, and controlled overdelivery | 247 FR-001–011/DR-001–006 | `packages/reality-core/tests/finance/test_commercial_edges.py`; `packages/reality-core/tests/test_commitment_revisions.py` |
| Canonical profile-v9 examples, deterministic settlement and discovery | 247 FR-013–015 | `packages/reality-core/tests/scenarios/test_international_demo.py`; `packages/reality-core/tests/test_demo_costing_profile.py`; `packages/reality-core/tests/test_company_setup_initialization.py` |
| Additive tenant-scoped schema and account-role migration | 247 DR-003–005 | `packages/reality-core/tests/test_migrations.py`; `packages/reality-core/tests/finance/test_adjustments.py` |
| Confirmed web dunning action and localized manual fee entry | 247 FR-001–004/FR-012 | `apps/web/scripts/commercial-edge-workflows.test.mjs`; frontend build and i18n audit |

### Spec 248 explainable B2B operational chain

Feature contract: `docs/features/b2b-operational-chain.md`.

| Verification family | Specification | Tests |
|---|---|---|
| Append-only customer-demand and stock-replenishment supply assignments, exact reconciliation, replay and tenant isolation | 248 FR-007–010/FR-019/DR-003/DR-005/DR-008 | `packages/reality-core/tests/test_supply_assignments.py`; `packages/reality-core/tests/test_migrations.py` |
| Purchasing, sales and inventory supply views reconcile without creating reservations or double-counting receipts | 248 FR-008–010/SC-004 | `packages/reality-core/tests/test_supply_coverage.py`; `packages/reality-core/tests/test_unified_delivery_reads.py` |
| Shared application-tool, MCP, API and CLI contracts expose reviewed supply and return actions consistently | 248 FR-007/FR-010–011/FR-019/DR-006 | `packages/reality-core/tests/test_b2b_operational_chain_contracts.py`; `packages/reality-core/tests/test_return_announcement_adapters.py` |
| Arrived customer returns support partial restock, quarantine, scrap and supplier-return outcomes with correction-aware history | 248 FR-011–012/DR-004/DR-007/SC-005 | `packages/reality-core/tests/test_returns.py` |
| Returned goods and commercial credits remain independent while both mismatch directions retain explanation links | 248 FR-013/SC-003 | `packages/reality-core/tests/test_commercial_matching_services.py`; `packages/reality-core/tests/operational_exceptions/test_derivation.py`; `packages/reality-core/tests/operational_exceptions/test_explanation.py` |
| Shortest-link movement explanation, precedence, provenance, correction and tenant isolation | 248 FR-014–015/DR-001/DR-004 | `packages/reality-core/tests/test_movement_explanations.py` |
| Deterministic dated B2B chain, exact contribution/supply/return reconciliation, explained movements and replay | 248 FR-016–019/SC-002–006/SC-008 | `packages/reality-core/tests/scenarios/test_b2b_operational_chain.py` |
| Exact human references, expected outcomes and UI discovery paths in the profile manifest | 248 FR-018/SC-001/SC-007 | `packages/reality-core/tests/scenarios/test_b2b_operational_chain_catalog.py` |

### Spec 249 Web and MCP proposal review parity

| Verification family | Specification | Tests |
|---|---|---|
| Complete MCP proposal classification, server-side redaction, tenant scope, rejection and receipt recovery | 249 FR-001/FR-003–010 | `packages/reality-core/tests/test_proposal_review_parity.py` |
| Shared Chat/Decisions routing and specialized-review delegation | 249 FR-002/FR-009–011 | `apps/web/scripts/proposal-review-parity.test.mjs`; frontend build and i18n audit |

### Spec 250 operational integrity

| Verification family | Specification | Tests |
|---|---|---|
| Exact tracked-return disposition and unrelated-location protection | 250 FR-001–004/DR-001–002/SC-001 | `packages/reality-core/tests/test_returns.py` |
| Reservation consistency after commitment quantity revision | 250 FR-005–008/DR-003–004/SC-002 | `packages/reality-core/tests/test_commitment_revisions.py` |
| Reviewed commitment cancellation, released allocations and verified receipt | 250 FR-009–012/FR-018/DR-003–006/SC-003/SC-007 | `packages/reality-core/tests/test_commitment_actions.py` |
| Cross-story tracked stock, revision, cancellation and historical no-silent-repair reconciliation | 250 FR-001–019/DR-001–008/SC-001–003/SC-007 | `packages/reality-core/tests/scenarios/test_b2b_operational_integrity.py` |

### Spec 261 saving an analysis is visible and named

| Verification family | Specification | Tests |
|---|---|---|
| A report proposal names the report its change concerns, for a confirmed create, duplicate, update and a since-deleted report | 261 FR-009 | `packages/reality-core/tests/test_reporting_graph_lifecycle.py` |
| Suggested report names from the catalog's own labels, and whether the question on screen is still the saved one | 261 FR-004/FR-006 | `apps/web/scripts/analytics-report-naming.test.mjs` |
| Visible save controls, carried names, draft and saved states, saving into the address, and a confirmed proposal opening its report | 261 FR-001–FR-003/FR-005/FR-007/FR-008/FR-010–FR-012 | `apps/web/scripts/analytics-save-clarity-browser.mjs`; frontend build and i18n audit |

### Spec 262 stock at a location

| Verification family | Specification | Tests |
|---|---|---|
| One item in one place: quantities equal the shared read contract, zero and negative pairs, an unknown pair, a location that stopped allowing stock, and no roll-up from a child to its parent | 262 FR-002/FR-003/FR-012 | `packages/reality-core/tests/test_stock_at_location.py` |
| A place scope on stock, reservations and movements, combined with the item scope, its state filters, its item set and its query shape | 262 FR-005–FR-007/FR-010 | `packages/reality-core/tests/test_stock_at_location.py` |
| The item preview and the location inspector address the pair, with the quantity named and the unit carried | 262 FR-001/FR-011 | `packages/reality-core/tests/test_stock_at_location.py`; `packages/reality-core/tests/test_operational_previews.py` |
| The click path: a location quantity opens the item there, reaches both scoped registers, states and clears its scope in both editions | 262 FR-004/FR-008/FR-009/FR-014 | `apps/web/scripts/stock-at-location-browser.mjs`; `apps/web/scripts/stock-at-location-contract.test.mjs`; frontend build and i18n audit |

### Spec 268 an Inspector row states one measure

| Verification family | Specification | Tests |
|---|---|---|
| A row carries its measure apart from the qualifier beside it, typed the same way, and a row without a qualifier grows no fields | 268 FR-001–FR-003/FR-008–FR-010 | `packages/reality-core/tests/test_inspector_presentation.py`; `packages/reality-core/tests/test_stock_at_location.py` |
| A clock that carries nothing is stated as a day, and any other instant is carried whole | 268 FR-004 | `packages/reality-core/tests/test_inspector_presentation.py`; `packages/reality-core/tests/test_stock_at_location.py` |
| Measures form one column in the full panel and stack in the narrow preview; the row is the click target and only the measure is marked as the link | 268 FR-005/FR-006 | `apps/web/scripts/inspector-row-shape.test.mjs`; frontend build and i18n audit |
| Where there is room for one string only, measure and qualifier recompose, so no view loses what the panel gained a column for | 268 FR-007 | `apps/web/scripts/inspector-row-shape.test.mjs` |

### Spec 263 decision trail

| Verification family | Specification | Tests |
|---|---|---|
| Token and issuer attribution columns: additive, reversible, no backfill, derived foreign-key index | 263 DR-002/SC-005 | `packages/reality-core/tests/test_decision_trail_migration.py`; `packages/reality-core/tests/test_schema_indexes.py` |
| One tenant-scoped reader names a person, a token with its issuer, or unknown, in a constant number of statements | 263 FR-004/DR-003/DR-004/SC-004 | `packages/reality-core/tests/test_decision_attribution.py` |
| MCP approval and rejection record the calling token, web issuance records the owner, signed-in decisions record the person only, restored proposals forget their token | 263 FR-001–FR-004/DR-005 | `packages/reality-core/tests/test_decision_trail_mcp.py` |
| Every event a confirmed proposal writes references it, on the generic, master-data and finance paths; explicit references win; a structural guard fails for any unscoped execution path | 263 FR-005/FR-006/DR-001/SC-002 | `packages/reality-core/tests/test_decision_trail_events.py` |
| History, single-decision review, agent status read and activities name the same decider; a record's origin names only the decision behind its first event | 263 FR-004/FR-007–FR-011 | `packages/reality-core/tests/test_decision_trail_surfaces.py`; `packages/reality-core/tests/test_provenance.py` |
| Decider sentences, Pending/History tabs; registers and Activities rows carry no decision line | 263 FR-004/FR-007/FR-008/FR-010/FR-012 | `apps/web/scripts/decision-trail.test.mjs`; frontend build and i18n audit |
| Every detail view lists the decisions that created and changed its record, an event's detail names the decision that caused it | 263 FR-013 | `packages/reality-core/tests/test_decision_trail_details.py`; `apps/web/scripts/decision-trail.test.mjs` |

### Spec 266 engine room

`interaction` is operational telemetry: one value-free row per crossing into the application, kept seven days, never a business record.

| Verification family | Specification | Tests |
|---|---|---|
| The interaction table: columns, checks, named indexes, reversible revision, derived foreign-key index rule | 266 DR-003 | `packages/reality-core/tests/test_engine_room_migration.py`; `packages/reality-core/tests/test_schema_indexes.py` |
| One boundary records one row; nesting joins; chat inside a request shares its correlation; committed events only, exact ranges; refusals and failures keep a code; a failing recorder never fails the call; expired rows are tidied by the work that records | 266 FR-002–FR-004/FR-011/FR-012/DR-002 | `packages/reality-core/tests/test_engine_room_recording.py` |
| Web (inside admission), MCP token, chat, CLI and worker child each record at their own boundary; no argument value reaches any row across the read catalog; the engine room's own reads are not recorded; refresh is flagged | 266 FR-001/FR-003/FR-010/DR-004 | `packages/reality-core/tests/test_engine_room_channels.py` |
| Cursor with late commits, every filter, truncation, retention, windows, stages from events and catalog, who-changed-this, linked events, owner-only access | 266 FR-005–FR-008/FR-013/FR-015/DR-003 | `packages/reality-core/tests/test_engine_room_reads.py` |
| Only the engine-room modules import the telemetry table or its reader; business code only annotates through the recorder | 266 DR-001 | `packages/reality-core/tests/test_engine_room_architecture.py` |
| Server processes queue rows to one writer and batch them; a full queue drops a row instead of waiting; the call's own duration is kept | 266 FR-012/SC-003 | `packages/reality-core/tests/test_engine_room_recording.py` |

### Spec 270 capability discovery

`capability_catalog` answers what the company's Reality can do and what the calling credential may
use of it. It transmits the existing capability classification and reads no business record.

| Verification family | Specification | Tests |
|---|---|---|
| Every MCP tool is reachable through exactly the known topics, duplicates counted once; the narrow catalog accessor is isolated and reads one section | 270 FR-003/FR-007/FR-008 | `packages/reality-core/tests/test_capability_catalog.py` |
| The topic index and one topic answer their documented shape within their size bounds; an unknown topic is refused by naming the known ones; two calls reach the dunning tools through the MCP runtime; the server instructions name the entry point | 270 FR-001/FR-002/FR-006/SC-001 | `packages/reality-core/tests/test_capability_catalog.py` |
| Grant state per credential kind: no credential, a manual token, a grant that omits a tool, a grant whose scopes exclude an access class; a tool reported callable is dispatched and not refused; a foreign company's grant is never read | 270 FR-004 | `packages/reality-core/tests/test_capability_catalog.py` |
| A capability carries its German business label or falls back to English; chat inherits the tool and reports no credential limit | 270 FR-005/FR-007 | `packages/reality-core/tests/test_capability_catalog.py` |

### Spec 271 MCP permission ceiling

A permission list is bounded by the catalog it draws from, and both grant paths refuse alike.

| Verification family | Specification | Tests |
|---|---|---|
| Approval accepts every eligible tool for each scope combination, counted from the catalog; a duplicate-laden or alias-bearing list normalizes before it is judged; a wildcard stays refused for an interactive grant | 271 FR-001/FR-002/FR-006/FR-007 | `packages/reality-core/tests/test_mcp_oauth_http.py` |
| An unknown name, an empty selection and tools outside the requested scopes each answer a stated sentence the browser can show, and a refused approval leaves the interaction pending | 271 FR-004/FR-005 | `packages/reality-core/tests/test_mcp_oauth_http.py` |
| Interactive approval and manual token creation accept and refuse the same lists with the same message; the wildcard is the one deliberate difference | 271 FR-003 | `packages/reality-core/tests/test_mcp_permission_parity.py` |
| The resolution guidance catalog validates against action discovery forms, rejects unknown roles, paths, pages, scope-less chat prompts and dangling blocker steps, covers every code a service can emit, and is served with the application catalog | 279 FR-001/FR-004 | `packages/reality-core/tests/test_resolution_guidance.py` |
| Cost guidance derives the ordered steps to a proven inventory or contribution value at read time: receipt cost, item review, contribution review and the owner's confirmation linked to the waiting proposal; it names the upstream blocker, writes nothing, stays tenant-scoped and is identical over MCP | 279 FR-001/FR-002/FR-003/FR-009, DR-001–DR-004 | `packages/reality-core/tests/test_cost_resolution.py` |
| The cost review draft derives contribution arguments from the preview and inventory arguments from held movements, receipts and opening statements; the valuation method is always asked; open inputs name what no source states; the draft writes nothing and is identical over MCP and chat | 282 FR-001–FR-005, FR-009–FR-011, DR-001–DR-004 | `packages/reality-core/tests/test_cost_review_draft.py` |
| Opening stock records the total acquisition value its evidence states as an `opening_cost_statement` SourceRecord linked to the movement, refuses malformed statements, and stays unchanged without cost | 282 FR-008, DR-005 | `packages/reality-core/tests/test_opening_cost.py` |
| The web proposes exactly the server-side draft, refuses a drifted draft or open inputs with 409 `draft_changed`, and returns the same proposal for the same draft | 282 FR-006, FR-007, DR-003 | `packages/reality-core/tests/test_cost_review_proposal_api.py` |

## Consolidated invoices — Spec 283

- `packages/reality-core/tests/test_consolidated_invoices.py`: spec 283 FR-001–003 and FR-010; one invoice over several orders of one party in both directions, refusal of another party, currency or direction, atomicity, per-line billing before, after and after reversal, and the 200-position bound in core and the MCP schema.
