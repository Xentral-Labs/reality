# External target mapping: bounded implementation design

Status: product scope and the concrete Finance-specific three-table schema accepted
by the owner after reviewing the fields and explicitly choosing Finance-only catalogs.
Implemented, verified and deployed locally on schema `0054_target_mappings`; see
[verification-results.md](verification-results.md) for exact evidence.
Requirements: FR-009, FR-021, FR-027, FR-030–FR-034; DR-001–DR-007.

## Outcome and boundary

An owner registers an accounting target, defines its allowed external accounts and
tax codes, and reviews exact mappings. A member can explain the destination of real
received components and operational account legs. Local posting, allocation and
balances remain independent. The result is mapping resolution, not certification of
an accounting entry or export readiness.

The first slice contains no vendor connector, file export, delivery receipt, remote
posting status, profile engine, tax calculation or automatic case determination.
Payment account mapping does not reuse invoice tax coding. Export packages and their
frozen revision manifests follow in the handoff slice.

## Data model

All three tables are tenant-scoped. IDs are generated opaque identifiers. Human
account codes and target namespaces never serve as local identity.

### accounting_target

Fields: id, tenant_id, namespace (unique per tenant, immutable), name, state
(active/blocked), revision (positive), created_at, updated_at.

Purpose: explicit independent accounting destinations. A target is not a connector
installation and activation performs no external effect. Name/state changes use
owner-confirmed proposals and existing audit events. Blocking makes current mapping
resolution unavailable; it does not mutate historical mapping revisions.

Constraints: unique (tenant_id, id), unique (tenant_id, namespace), nonempty bounded
namespace/name, bounded state and positive revision. Target deletion is not offered.

### accounting_target_reference

Fields: id, tenant_id, target_id, kind (account/tax_code), code, name, state
(active/blocked), revision, created_at, updated_at.

Purpose: select only defined references belonging to the chosen target. These are
user-maintained external identifiers, not a local chart or proof that a remote system
accepts them. No balances, account classes, rates or tax algorithms live here.

Constraints: composite FK (tenant_id, target_id) to target; unique
(tenant_id, target_id, kind, code); unique (tenant_id, target_id, id, kind).
Code, target and kind are immutable after creation. Correcting a wrong code creates
a new reference and blocks the old one. Name/state changes increment revision and
retain before/after audit evidence. No cascading deletion.

### finance_target_mapping_revision

Fields: id, tenant_id, target_id, mapping_kind (local_account/case_routing),
local_account_id (nullable), transaction_kind (nullable), case_reference_id
(nullable), group_mode (none/exact, nullable), group_reference_id (nullable),
external_account_id, external_tax_code_id (nullable), revision, replaces_id
(nullable), state (active/blocked), is_current, configuration_snapshot JSONB,
reason, actor_id, action_id, created_at.

Case-routing shape: transaction and case required; group mode required; group ID
required exactly when mode is exact; local account absent. Supported transaction
keys use existing invoice and credit-note operation identifiers; never reuse invoice
keys for credits. Initially preview only customer/supplier invoices and credit notes.
Local-account shape: local account required; transaction/case/group absent; tax code
absent. This maps an operational ledger leg, not a received net/tax component.

Composite tenant FKs protect target, predecessor, local account, case and group.
Case/group FKs include the existing reference-kind discriminator, constrained to the
correct constant. External reference FKs include tenant, target and kind; account
output cannot point to a tax-code reference or another target. Nullable columns use
CHECK constraints for the two complete mapping shapes. Positive revision, nonempty
reason and bounded states are enforced in PostgreSQL.

Each logical scope has one current revision, enforced through separate partial
unique indexes for local-account, no-group case and exact-group case scopes.
Historical scope/revision uniqueness uses the same three shapes, without filtering
out history. The tenant finance lock serializes all activation, replacement, block
and reference-maintenance operations. Under that lock, activation also rejects any
active no-group/exact-group overlap for the same target/transaction/case. There is no
priority or fallback rule. Runtime still refuses multiple matches defensively.

A replacement appends a row and clears only the predecessor's is_current marker.
Decision fields on old rows remain unchanged. The immutable snapshot records selected
target/reference labels, codes, states and revisions as reviewed. Mutable current
labels must never rewrite historical review displays. The snapshot has no amounts
and is not a second authority for financial evidence.

## Confirmation and lifecycle

Drafts use existing ChangeProposal records, matching the delivered source mapping
workflow. Editing a form or creating a proposal does not activate a rule. Approval
activates/appends the exact reviewed revision through the shared application tools.
A separate persistent draft mapping table has no use case in this slice.

Commands require owner rights, a reason, expected finance revision and the existing
confirmation boundary. Reference and target edits participate in the same finance
revision as mappings. Approval rechecks permissions, locks finance, reloads current
references and validates the complete intent. A stale proposal fails and requires a
new review. Retrying an already completed approval returns its original result.

Changing a mapping key creates a separate scope: explicitly block the old rule before
activating an overlapping replacement mode. Never silently retire unrelated scopes.
Blocked references remain inspectable but cannot be newly selected or resolved.
Blocking an existing mapping must remain possible even if its target/reference has
already been blocked. No-op changes are refused.

## Exact resolution and evidence preview

A shared read accepts target_id and document_id and loads the existing received
component context. It returns two separately labelled collections:

- Received components: transaction kind, exact scope, stated amounts/currency/basis,
  original source codes and source mapping revision, internal assignment revision,
  effective case/group provenance, matching target mapping revision and destinations.
- Operational account legs: existing entry/account identity and exact local-account
  mapping. These are gross subledger legs, never presented as net/tax posting lines.

Case/group resolution reuses current source resolution and assignment services. An
internal assignment can provide a missing declaration; an explicit malformed,
unmapped, blocked or conflicting declaration is not silently replaced. If both valid
source and internal references exist, they must agree. A case is always required for
case routing. Group is required only by exact-group discrimination; a supplied invalid
or conflicting group remains a review issue even for a no-group mapping. Nothing is
inherited from a document summary onto a line.

Results distinguish missing case, missing group, invalid/blocked classification,
source/internal conflict, missing mapping, ambiguous mapping, blocked target and
blocked external destination. A successful result includes the exact selected IDs
and revisions. Received fields absent from the source remain absent; no amounts are
calculated. No mappings does not imply no-tax. No matching document/target in the
tenant returns not-found without disclosing another tenant's data.

An internal assignment is usable only while the evidence hash in its confirmed
action matches the current received component. Changed evidence yields
`stale_assignment`; the old assignment and new received values remain separately
inspectable. This is a derived read result and adds no stored status or schema.

Preview is a read-only consistent snapshot; no source, component, assignment, ledger,
audit event or mapping row is created by it. Unsupported document kinds are refused.
A preview may show missing received net/tax detail separately, but MUST NOT claim
export completeness without the future explicit target profile contract.

## Commands and adapters

Shared commands:

- finance.target.create / finance.target.update
- finance.target_reference.create / finance.target_reference.update
- finance.target_mapping.set

Shared reads:

- finance.targets.list
- finance.target_references.list
- finance.target_mappings.list / finance.target_mappings.history
- finance.target_mappings.preview (target_id, document_id)

All use Pydantic extra-forbid request models. Lists filter before count/pagination,
default limit 50 and maximum 200, stable ID tiebreakers. Pickers are searchable and
must not make references beyond the first 200 unreachable. The API, CLI, MCP and
agent catalog expose the same service/tool contracts. API proposals require company
owner rights; no adapter implements matching or writes ORM records directly.

## Screens

Finance → Settings → Accounts & account mapping retains the existing operational
account editor. A compact in-content selector distinguishes Operational accounts and
External accounting. Keep the four existing settings areas and the mobile area
selector; do not add another global workspace or return to accordions.

External accounting starts with target selection and a clear empty-state action.
Within a selected target, show Rules, External accounts and Tax codes as compact
subviews. Target create/edit uses the existing reviewed form pattern. Catalog rows
show code, name and state with compact Edit/overflow actions. Rule rows show scope,
transaction, case, group mode/group, destinations, state and revision; history opens
the immutable before/after decisions.

The rule editor switches between Received component and Operational account. It only
shows fields meaningful to that scope. Case/group and destination pickers accept
existing eligible references; absent options link to the matching management area.
No free-text tax rule, country wizard, rate field or accounting instruction is added.
The footer contains a content-width Review mapping action followed by explicit
confirmation with before/after destinations. Draft recovery is tenant and target
scoped; late requests cannot leak another tenant/target's data.

Financial detail offers a target picker and Mapping preview beside the existing
received components. Show specific review reasons and links to the responsible
settings area, plus source/internal/mapping history. Labels distinguish gross local
account references from component destinations. Members can inspect; owners maintain.
Loading, error/retry, empty and blocked states, keyboard dismissal/focus, 390/1024/1440
layouts, coarse-pointer targets and light/dark themes are required. All UI labels
ship in English, German, Dutch and Spanish.

## Implementation and migration

Work only in .claude/worktrees/invoice-lines-research; preserve all concurrent work.
Use domain/target_mappings.py for pure shape/matching rules, db/target_mappings.py
for the three models, services/finance/target_mappings.py for shared lifecycle and
snapshot reads, existing tools/finance.py and tools/application.py for confirmation,
and the current CLI/API/MCP/catalog boundaries. New frontend components are
finance/TargetMappings.tsx and finance/TargetMappingPreview.tsx, composed by
FinanceSettings.tsx and FinancialComponents.tsx.

Resolve the actual Alembic head immediately before adding the migration; the observed
head is 0053_source_classification. Add tables only, with no existing financial-data
rewrite or automatic seeds. Downgrade refuses to discard nonempty target/mapping
history. Rehearse on disposable PostgreSQL before any local rollout; no startup
migration, resets, remote calls or deployment of unrelated changes.

## Constitution review

Design checks: PASS for shortest source/evidence links, no local financial authority
change, proven configuration schema, tenant-scoped composite links, shared service
boundaries, received-value fidelity, explainable UI and no new dependencies. This is
a design assessment; the owner subsequently approved the concrete schema after
reviewing the three tables and rejecting a system-wide registry. No further schema
approval is pending for this bounded design.

## Planned acceptance proof

1. Two targets with the same external code remain isolated; cross-tenant and
   cross-target reference links fail at both service and database boundaries.
2. Two explicitly case-coded components in one invoice resolve independently;
   Goods/Software groups select distinct accounts without changing stated amounts.
3. Country/rate alone never determines a case; unknown does not become no-tax.
4. A no-group rule cannot coexist with exact-group rules for the same scope;
   concurrent competing activations yield at most one valid mode.
5. Missing/blocked/conflicting source/internal references yield precise reasons;
   retired configuration cannot be reused and history keeps original snapshots.
6. Preview and draft creation do not alter ledger, evidence, assignment or active
   configuration; confirmation appends exactly one audited revision and replay is safe.
7. Reference edits invalidate pending approval; confirmed history remains unchanged.
8. Invoice/credit kinds are separate; local cash/account mappings never inherit tax
   codes or produce a second invoice posting.
9. Members cannot mutate through any adapter; owner commands preserve preview,
   confirmation, stale checks and tenant scope.
10. UI supports empty setup, all searchable choices, rule review/history, real evidence
    preview, target/tenant switches, recovery and compact responsive actions.
11. Clean migration, populated-history downgrade refusal, full required backend and
    frontend gates pass before marking this slice delivered.
