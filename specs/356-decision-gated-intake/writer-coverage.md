# Intake writer coverage baseline

## Approved scope clarification (2026-10-04)

This rollout governs external sources, imports and agent-proposed business effects.
They require an exact retained proposal and an authorized confirmation before acceptance.
A direct action by an authenticated human is itself the decision and uses the existing
application authorization and audit trail; it does not require a second proposal or
confirmation cycle. Derived effects of one operation share its transaction and receipt.

The owner retained PRs #333–#346 and withdrew the later universal canonical-writer
rollout. Internal service calls and every manual UI/CLI operation are not additional
admission projects. Existing tenant, domain, Finance and Chat confirmation rules remain.
A static writer inventory is discovery material, not a mandate to guard every writer.
References below to governed writes mean external intake only; broader earlier planning
and universal-writer tasks are superseded by this clarification.

**Created**: 2026-10-03
**Language**: English
**Status**: Current paths identified; enforcement and test completion are pending.

This matrix documents current gaps and planned ownership. It does not claim every
business writer already requires a Decision. The accompanying writer-inventory.json
is a read-only AST candidate inventory; its method/limitations are explicit. Full
semantic coverage must also inspect catalog registration, wrappers, class/nested
methods, bulk SQL and call chains, then map every governed writer to a refusal
test before spec 361 can complete.

| Current path | Current behavior / gap | Owning spec | Planned enforcement / proof |
| --- | --- | --- | --- |
| services/core.py: store_source_record/enqueue_source | Lossless raw intake; not business-effect acceptance | 356 | Preserve source/queue permission; test no operational authority gained |
| services/artifacts.py: store/materialize artifact | Original bytes; received source lifecycle differs by profile | 358 | Preserve bytes; register original-source reference before business approval |
| services/core.py: process_import_job | Invokes mutating interpreter and commits | 356 | Prepare only; unique phase outcomes; retained replay |
| services/core.py: process_import_job_bound | Demo-only scope with interpreter call/savepoint | 361 | Shared preparation and authorized apply; no live-demo bypass |
| services/core.py: _shopify_interpretation | Creates evidence/commitments; post-hoc action | 357 | Exact first-order proposal before accepted rows |
| services/shop_order_changes.py | Automatically applies supported reductions/cancellations | 357 | Frozen change plan; canonical approved revision/cancellation |
| services/shop_refunds.py | Creates refund evidence and supported return/reduction effects | 357 | Separate refund proposal; no payment authority |
| services/file_interpreters.py: item/party/location | Direct record creation; internal commits on some profiles | 358 | Pure plan; approved atomic package apply |
| services/item_imports.py | Reviewed item package, 500 rows/2 MiB | 358 | Reuse review; large-file validation/packaging path |
| services/file_interpreters.py: sales_order | Direct documents/lines/commitments with internal commits | 358 | One complete order per exact approved unit |
| services/file_interpreters.py: inventory_snapshot | Computes difference and immediately creates adjustment | 358 | Received statement plus separately visible approved correction |
| services/external_stock.py: _record_file_rows | Direct accepted stock assertions | 358 | Prepared assertion; never implicit book-stock correction |
| services/file_interpreters.py: bank_statement | Direct incoming/outgoing payment records | 359 | Shared financial plan, current owner authority |
| services/payment_intake.py: interpret_sales_invoice | Direct accepted invoice/posting | 359 | No-effect prepare; canonical approved evidence/post |
| services/payment_intake.py: interpret_customer_payment | Direct payment and optional automatic allocation | 359 | Exact visible payment/allocation intent, current-state recheck |
| tools/application.py: generic proposal executor | Commits executing claim before handler; handlers may commit | 356 | Dedicated atomic database-only intake branch; do not weaken unrelated external reconciliation |
| tools/application.py: finance branch | Atomic effect/receipt pattern, business → finance → proposal locks | 356, 359 | Reuse transaction/lock pattern; prove mixed-path concurrency |
| services/core.py: create/update master, documents, commitments, movements, finance | Public canonical writers and direct service callers | 356, 361 | Bounded scope for external intake; direct human operations retain existing service validation/audit and need no new proposal |
| services/tenant_policy.py | Practice/tenant-purpose policy, not general business Decision enforcement | 356, 361 | Keep existing practice rules; no universal manual-writer gate |
| services/demo_data.py, integrations/demo_data.py | Continuous synthetic interpretation and settlement | 361 | Same prepared/approved flow; absent reviewer waits visibly |
| services/company_setup.py, demo profiles, lesson scopes | Fixed confirmed initialization | 361 | Narrow explicit bootstrap exception, no authority for later arbitrary effects |
| jobs/registry.py, services/scheduled_jobs.py, job handlers | Database-only transactions, bounded config/result/time | 360, 361 | Small manifest reference config, original reviewer handoff, handler-owned commits |
| services/proposal_decisions.py, domain/proposal_decisions.py | Current authority; autonomous delegation false | 360 | Explicit narrow mandates; ordinary Chat restriction stays |
| web/api.py, mcp/catalog.py, cli/app.py | Several legacy and shared entrypoints | 356–361 | Shared application boundary; transport parity and bypass tests |
| Derived projections, source/queue/audit administration | Not accepted source interpretation | 356, 361 | Explicit classification; never general operational write exception |

## Required completion evidence

Each candidate/call chain is classified as a governed effect, raw/audit/read work,
or an exact fixed setup exception. Add exact refusal/happy-path test references,
source→decision→receipt links and transport coverage. No candidate is considered
covered solely because emit_business_event can attach an action ID. New writer
registration must fail the coverage check when it lacks an owner and proof.

Domain rules remain in services; adapters and agents never write through ORM.
Historical missing approvals stay unknown. Catalogue and generated documentation
updates follow the actual implemented contracts, not this proposed matrix.
