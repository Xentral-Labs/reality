# Validation Guide: Operational Finance

**Status**: Implementation-target guide. The commands referring to new tests become runnable after those tests are added. Planning does not claim the feature runs today.

## Prerequisites

Use the reviewed implementation checkout, Python 3.12+ environment and the repository's PostgreSQL test setup from `docs/TEST_STRATEGY.md`. Use an isolated disposable test database; do not apply proposed migrations to the active demo/customer database. Resolve the actual migration head and web-shell integration baseline before implementation. No additional production service is required beyond the existing API, scheduler and worker roles.

## Planning check available now

From the repository root:

```bash
make spec-check
```

Review [plan.md](plan.md), [data-model.md](data-model.md), [contracts/commands.md](contracts/commands.md), [contracts/views.md](contracts/views.md), [test-plan.md](test-plan.md) together. Generate dependency-ordered tasks and complete analysis before implementation. Schema review is not replaced by passing this documentation check.

## Tests after implementation

From the root, with the repository test database configured:

```bash
.venv/bin/pytest packages/reality-core/tests/finance
.venv/bin/pytest packages/reality-core/tests/scenarios/test_operational_finance_trade.py
make lint
make test
make web-build
```

Run existing web contract scripts as required by package.json and the test strategy, plus the new browser finance matrix. Run empty-database migration, minimal-account setup and explicitly targeted disposable reseed checks. No legacy account backfill or compatibility rollback is required.

## End-to-end acceptance fixtures

1. **Accounts and eight ERP directions**: create the minimal account set, record each supported invoice/credit/payment/refund direction, change defaults and inspect historical balances across both old and new accounts. A blocked default refuses new postings while an exact inverse uses its original account. Generate fresh fixtures with valid account IDs. One account may contain EUR and USD; balances and credit use remain separated by currency.
2. **Customer and supplier settlement**: independently fixture invoice 1,000 and cash 980. Without accepted reduction, outstanding is 20. With explicitly authorized 20 reduction, cash remains 980 and outstanding becomes zero. On supplier side retain the agreement evidence. Receipt/payment 1,020 allocated 1,000 leaves 20 available credit; refund or reuse it once, including concurrent attempts.
3. **Opening positions**: import each of the four 100 EUR residual directions into a clean tenant. Debt/credit appears on the correct side; no cash or operational sales/purchase turnover is created. Retry preserves IDs. Summary/detail overlap and changed snapshots require review. Unknown original due date does not create invented aging.
4. **Attribution and handoff**: supplier evidence explicitly states gross 1,190, net 1,000 and tax 190. Assign net 600/400 to two existing centers. Confirm unchanged gross payable. Before configuring a target, resolve an explicitly mapped source code to a local case; verify namespace/kind isolation. Then configure target routing and retain the exact source and target mapping revisions. Prepare neutral JSON; change mappings and verify prior download bytes/hash remain identical. Import accepted-only receipt and ensure external posting remains unknown. Add explicit posted receipt for that exact item/version.
5. **Provider path**: source states capture 100, fee 3, dispatched payout 97, bank receipt 97. Clearing ends zero; in-transit ends zero; bank receives 97; stated fee counterpart holds 3. Replay capture from a statement and match it without another effect. A pending authorization creates no money entry. Direct and two-leg payout representations cannot coexist.
6. **Advances/holds/transfers**: earmark 40 from available payment 100; free availability is 60. Apply 25 to an explicitly linked invoice, leaving 15 earmarked. Race a refund and ensure no double use. Place payable hold after payment preview and refuse new execution; still preserve independently evidenced executed cash. Transfer a credit between two same-role accounts with paired allocations and unchanged role total.
7. **Trade and agents**: fixture partial and consolidated billing with stated links, returns/credits and settlement. Imported missing goods history reads unknown until scoped evidence establishes coverage. Page through credits and compare full totals; a concurrent mutation invalidates continuation. Agent explanation leads to original evidence, distinguishes derived values and never reports external success merely because a file was prepared.

Repeat applicable fixtures with a second tenant using identical human codes, opposite customer/supplier direction, another currency and reversed histories. Expected amounts are authored independently of the calculation implementation.

## Browser evidence

Verify V01–V13 per contracts/views.md and views.md. Record viewport, browser, locale, theme, scenario, screenshot location and observed result in the eventual verification report. Confirm that evidence links work, confirmations show separate cash/noncash effects, totals include off-page rows and narrow layouts do not overlap controls. Do not mark a visual criterion complete from component/build tests alone.

## Currently runnable first slice

Use the root checkout against an explicitly disposable database with the root migration chain. Do not run this chain against the active port-8080 worktree database. Migration 0047 refuses populated ledgers instead of deleting data. New companies created through ordinary services get five reference accounts; an older empty company can use the explicit account initialization proposal.

Open company details → Operational accounts. Create/edit/block an account or select a role default, review the proposal, then confirm. Post invoices/payments through existing actions and inspect the journal's account code/name and required account ID. A changed default affects future postings, while invoice-bound settlement stays on the original control account. Use exact reversal for corrections.

For adapters, `reality finance-accounts --tenant-id TENANT_ID` and the MCP `finance_accounts` read expose the same configuration/revision. Typed proposal commands are documented in `docs/CLI_SPEC.md` and `contracts/commands.md`. The broader walkthroughs above describe future slices; [verification-results.md](verification-results.md) is the implementation boundary.

## Received financial detail and cost-center attribution

1. Define active cost centers in Company settings → Finance references.
2. Open Finance → Open items → Financial detail on a customer/supplier invoice or
   credit note. Existing typed gross/currency are available even without optional
   received detail. Net, tax and other basis are unknown unless explicitly supplied.
3. For a line-less invoice with source payload
   `{"reality_finance_v1":{"net":"1000","tax":"190"}}` and typed gross `1190`,
   select Net and enter cost-center shares `600` and `400`. When lines exist, use
   each line's received detail; document totals are displayed separately.
4. Supply a reason, review the shared server result, and confirm as a company owner.
   The result has assigned `1000`, unassigned `0`, and no additional ledger posting.
5. Remove one share and confirm a new reasoned revision to leave the remainder
   unassigned. History preserves the old split and reference names. Clearing all
   shares/classification creates a new decision; it does not delete history.
6. CLI reads: `finance-components DOCUMENT_ID`, then
   `finance-component-history COMPONENT_ID`. `finance-component-propose` accepts
   the documented assignment JSON including current finance revision and evidence
   hash. API and MCP expose the same reads and confirmed proposal boundary.

This slice does not infer tax, map arbitrary source fields, determine posting
accounts, produce global cost reports or send data to an accounting system.


## Inspect current operational account usage

Open Company settings → Operational accounts → Transaction matrix. The 14 operations show debit/credit roles, received amount basis and current configured, missing or blocked defaults. Configure accounts returns to the existing account controls; confirmed account changes refresh the matrix. Linked settlements retain the original control account. This view is not a transaction authorization or an external tax/country mapping engine. The same read is available through GET `/finance/matrix`, `finance-matrix`, and MCP `finance_matrix`.

## Translate declared source classifications

Open Company settings → Source code mappings. Choose an existing source system,
enter its exact namespace and code, and select an active internal case code or
coding group. Supply a reason, review and confirm. Mapping scope includes the
source system and classification kind: the same external code in another source
or namespace does not match automatically. Search fields independently narrow the
mapping list, source systems and internal reference choices.

Received `reality_finance_v1.codes.case` and `.group` declarations use objects with
`namespace` and `code`. Financial detail shows the received declaration separately
from the mapped reference and any explicit internal assignment. Open Source mapping
history there to inspect revisions, reasons, actors and confirmation actions.
Missing, malformed, blocked and conflicting declarations remain visible; mapping
never changes source evidence, amounts, component assignments or ledger entries.
Document summary declarations do not become line declarations.

Owners can block or replace a mapping through the same reviewed workflow. History
preserves each active/blocked decision and its reference snapshot. API
`/finance/source-mappings`, CLI `finance-source-mappings` and MCP
`finance_source_mappings` share the tenant-scoped read. Proposals use
`finance.source_mapping.set`; normal confirmation is required to execute them.
Cost-center code translation, external target-account routing and accounting
handoff remain subsequent work.

### Updated finance configuration location

Use Finance → Settings for operational accounts and transaction matrix, cost-center /
case-code / coding-group references, and source-code mappings. This supersedes the
Company settings navigation in earlier walkthroughs above. Existing forms, reviews
and history are unchanged. Company settings retains company/access administration.
A direct bookmark uses `/app/finance?tenant=YOUR_TENANT&finance_view=settings`.

### Finance settings areas

Finance → Settings opens Accounts & account mapping directly. Use the menu on the
left to select Cost centers, Case codes & coding groups, or Source code mappings.
On mobile use Settings area. Areas can be bookmarked with `finance_settings=accounts`,
`cost-centers`, `classifications`, or `source-mappings`. Cost centers has a fixed
reference kind; classifications only offers case codes and coding groups. Prepared
reference reviews remain recoverable when switching areas and reloading.

## External destination setup

1. Open Finance → Settings → Accounts & account mapping → External accounting.
2. Create an accounting target with a stable code/namespace and name; review and confirm.
3. Select it and define permitted External accounts and, when applicable, Tax codes.
4. In Rules choose Received component, a supported transaction and existing Case code.
   Choose no group discrimination or an exact defined Coding group, then select the
   external account and optional tax code. Review and confirm the exact destinations.
5. For control/cash account references choose Operational account instead; it carries
   no tax code and does not replace a component rule.
6. Open Financial detail on a customer/supplier invoice or credit note and select the
   target under Mapping preview. Follow missing classification/destination reasons;
   do not infer treatment from country or a missing tax amount.
7. Inspect history before replacing or blocking a rule. Changes affect current mapping
   resolution; previous confirmed revision snapshots remain inspectable.

This setup performs no export, remote posting or local monetary adjustment.
