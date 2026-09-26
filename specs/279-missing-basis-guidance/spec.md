# Feature Specification: Guidance for missing basis

**Feature Branch**: `279-missing-basis-guidance`
**Created**: 2026-09-26
**Status**: Draft
**Language**: English
**Input**: "Whenever a value is missing (for example the inventory cost panel showing
'Cost readiness: uninitialized'), it is not clear what one has to do to get it filled.
Where does this happen, and what could be offered at each place so people can help
themselves?"

## Context and Intent

### Problem

Reality correctly refuses to show a number it cannot prove. The pages say *that*
something is missing, but not *what* a person can do about it, *who* may do it, or
*where*. The inventory cost panel is the clearest case. In the German edition a user sees:

- `Kostenbereitschaft: uninitialized`;
- an untranslated English sentence that repeats the translated one above it;
- `Nächste zulässige Aktion: cost_change_propose · inventory_review`;
- `Fehlende Grundlage: inventory_scope_not_reviewed`;
- three values marked "Nicht nachgewiesen".

There is no button, no link and no hint that the action exists only in chat or MCP. The
only mention of who may act is "Authentifizierter Unternehmenseigentümer erforderlich".

A survey of the web app on 2026-09-26 found the same gap in several places:

| Area | Where | What is missing today |
|---|---|---|
| Cost | Warehouse stock row, Finance open items (DB1/DB2 per invoice line), Customer orders (expanded) | Raw stage, tool, operation and basis codes. Nothing tells the user what to do, and there is no web path for `cost_change_propose`. Unit cost can never be filled; the carrying-value cause is hidden. Contribution shows only the last gap, not the upstream blocker. |
| Cost valuation | Analytics > Inventory valuation | Empty generation selector with no explanation; state `unavailable` untranslated. Generation jobs exist only for operators. |
| Operational exceptions | Exceptions page (all 39 classes, cost classes most visibly) | Title, impact and resolution text (`clears_through`) are English only; no path to the resolving action. |
| Stored calculations | Exceptions, Exception rules, Finance open items, Payment invoice picker, report dialog | "Awaiting first calculation" / "could not be updated" with only a re-read button; no link to system status, no cause. |
| Pricing | Reports > Price determination | Needs a business partner and item, but offers no input. |
| Delivery readiness | Dispatch/blockers report | Raw blocker codes (`insufficient_stock`, `prepayment_invoice_missing`, …) with no action link. |
| Other | Storyline step check, Data sources ("No import job"), Finance source mappings | Raw check codes; explanation without a next step. |

Good existing patterns to reuse:

- Chat "AI credentials not configured" links straight to Settings > AI.
- Finance "Set up standard accounts" offers a button that runs the initialization.
- Delivery holds show translated labels with hold and release actions.

### Scope

- One shared **resolution guidance** contract. Every service that reports a missing,
  stale, pending or unavailable basis also returns stable codes for the reason and for
  the ordered steps that resolve it. Each step carries its state, the role that may act,
  and the best existing path to act.
- One shared web presentation of that guidance. It shows a plain-language reason, the
  ordered steps with the first open one highlighted, and one control per step.
- Complete translations in every supported web language (English, German, Dutch,
  Spanish) for every reason, stage, step and blocker code that the web can display, and
  a check that fails when one is missing.
- Applying the pattern to the surfaces in the table above, in priority order: cost first,
  then stored calculations, then exceptions, then the remaining places.
- A chat handoff. When a step can only be carried out through an agent tool, the user
  can open chat with a prepared, unsent request for that scope. The normal chat
  preview and confirmation rules still apply.

### Non-Goals

- New web forms for cost reviews, price lists, payment terms or pricing resolution. They
  are recorded as follow-up candidates; this feature links to what already exists.
- Changing who may perform or confirm a cost action, or any other authorization rule.
- Letting the browser decide which step is next. The shared services decide; the web
  only renders.
- Web triggers for operator-only work (company cost generation jobs, scheduler and worker
  health). The guidance says it is operator work and points to system status.
- Automatic sending of chat requests or any mutation without the existing confirmation.
- Storing guidance. It is derived at read time.
- Data sources "No import job". Found during implementation (2026-09-26): records
  written directly through the API never have an import job, so the label is
  information, not a missing prerequisite, and a "set up the source" step would
  mislead.
- Translating the per-finding impact sentence on the Exceptions page. Several are
  composed with quantities in the services (for example "3 remain overdue"), and
  localizing them needs structured impact values. That is a follow-up.

### Existing Contracts

- `docs/WEB_SPEC.md` — Product principle, Inspect pattern, AI and MCP boundary, Chat.
- `docs/features/receipt-costing.md` — cost evidence, reviews and owner confirmation.
- `docs/features/operational_exceptions.md` — exception catalog and `clears_through`.
- `docs/features/home-live-status.md` — system readiness (spec 149).
- `docs/features/chat.md` — chat preview and confirmation.
- `docs/features/shared-language.md` — shared vocabulary and German ERP labels.
- Specs 272 (compact chat answer basis) and 276 (human-readable decision review), which
  already removed raw codes from other surfaces.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Missing states read as plain language (Priority: P1)

A warehouse clerk opens a stock row whose cost is not yet proven. Instead of machine
codes, they read one plain sentence in their language, for example "Nobody has confirmed
the acquisition cost for this item yet". Each missing value says why it is missing.

**Why this priority**: It is the smallest change that removes confusion everywhere, and
the step-by-step guidance builds on it.

**Independent Test**: Render every surface in the table above in German and English with
each reason code the services can emit. No raw code is visible, and no sentence appears
twice.

**Acceptance Scenarios**:

1. **Given** an item without a reviewed cost basis, **When** a German-speaking member
   opens its stock row, **Then** the stage, the reason and every missing-basis entry
   appear as German text, and no identifier such as `uninitialized`,
   `cost_change_propose` or `inventory_scope_not_reviewed` is visible outside the
   inspector.
2. **Given** a value that the service cannot provide for this scope (for example
   carrying value without an assessment), **When** it is shown, **Then** its specific
   reason is shown next to it instead of a bare "Not evidenced".
3. **Given** an exception of any catalog class, **When** it is listed in German, **Then**
   its title and resolution text are German.
4. **Given** a new reason code added to a service without a label, **When** the
   translation check runs, **Then** it fails and names the code.

---

### User Story 2 - The cost panel shows the path to a proven value (Priority: P1)

An owner looks at DB1 for an invoice line that shows "Not evidenced". The panel lists the
steps in order: record the supplier invoice, assign the receipt cost, review the item's
inventory cost, review the contribution. Completed steps are ticked, and the real blocker
is the first open step, even when it lies upstream of the contribution.

**Why this priority**: Cost is where users hit the gap most often, and today it is a dead
end.

**Independent Test**: For an inventory scope and a contribution line in each state
(uninitialized, pending, stale, complete), request cost guidance. Verify the ordered
steps, their states and the first open step.

**Acceptance Scenarios**:

1. **Given** a contribution line whose item has no inventory review, **When** its
   explanation is opened, **Then** the first open step is the inventory review, not the
   contribution review.
2. **Given** a stale contribution whose cause is a stale inventory review, **When** it is
   opened, **Then** the guidance names renewing the inventory review as the next step.
3. **Given** an inventory scope, **When** the panel is shown, **Then** it does not show a
   value field that the service never provides for that scope.
4. **Given** a complete, current basis, **When** the panel is shown, **Then** no steps
   are shown and the existing "Inspect cost basis" link remains.

---

### User Story 3 - Every step offers the best available way to act (Priority: P2)

For each open step, the user gets one control. It leads to the matching web form when one
exists, to chat with a prepared request when only an agent tool exists, or to Decisions
when a proposal waits for confirmation. When the step needs a role the user lacks, the
guidance says who must act instead of offering a control that would be refused.

**Why this priority**: It turns explanation into self-help. It depends on US2's steps.

**Independent Test**: For each path type, verify the control's target and that it is
hidden or replaced by a "who must act" note when the viewer lacks the role.

**Acceptance Scenarios**:

1. **Given** an open "record supplier invoice" step, **When** a member follows it,
   **Then** the existing supplier-invoice form opens with the relevant party or item
   preselected where the form supports it.
2. **Given** an open inventory review step, **When** a member chooses "Prepare with
   Reality", **Then** chat opens with an unsent request that names the scope. Nothing is
   proposed until the user sends it, and nothing changes until the proposal is confirmed
   as usual.
3. **Given** a waiting cost proposal, **When** the owner opens the guidance, **Then** the
   step links to that proposal in Decisions.
4. **Given** a member who is not an owner and a step that needs owner confirmation,
   **When** the guidance is shown, **Then** it says that a company owner must confirm,
   and it offers no confirm control.
5. **Given** a company in which cost decisions cannot be confirmed (demo and practice
   companies), **When** a step needs one, **Then** the guidance says so and offers no
   write path.

---

### User Story 4 - Stored calculations explain themselves (Priority: P2)

A finance clerk sees "Awaiting first calculation" on open items. The message says whether
background processing is running and links to the system status. When a calculation
failed, it shows the recorded cause instead of only "could not be updated".

**Why this priority**: The state is common after setup and on large companies, and
nothing on the page tells users that this is operator work rather than their own.

**Independent Test**: Render each projection state (uninitialized, pending, failed,
ready) with system readiness confirmed, unverified and unavailable. Verify the message
and link.

**Acceptance Scenarios**:

1. **Given** a projection that was never calculated and background processing that is
   unavailable, **When** the page is shown, **Then** it says the calculation cannot start
   until background processing runs, and it links to the system status.
2. **Given** a failed projection, **When** the page is shown, **Then** it shows the
   recorded failure reason in plain language.

---

### User Story 5 - The remaining surfaces follow the same pattern (Priority: P3)

The following surfaces use the same guidance presentation, with a step to act wherever an
existing path exists:

- cost exception rows on the Exceptions page;
- the Inventory valuation page;
- the Price determination report, which gets an input for partner and item;
- delivery blocker entries;
- Storyline step checks.

**Why this priority**: Each is less frequent. Together they complete "no dead ends".

**Independent Test**: For each listed surface, verify translated reasons and, where an
existing path exists, a working control.

**Acceptance Scenarios**:

1. **Given** a `missing_acquisition_cost` exception, **When** it is listed, **Then** it
   offers the same first open step as the cost panel for that scope.
2. **Given** a delivery blocked by `prepayment_invoice_missing`, **When** the blocker is
   shown, **Then** it opens invoice entry (with the order preselected where the form
   supports it).
3. **Given** the Price determination report without a partner and item, **When** it is
   opened, **Then** the user can pick both, and the report resolves through the existing
   pricing service.

### Edge Cases

- **Several gaps at once**: all are shown in dependency order, and only the first open
  step is highlighted.
- **Unknown code**: a code without a label falls back to a generic "Missing basis"
  sentence. It never shows the raw code to the user, and the translation check fails in
  CI.
- **State changes while the page is open**: after an action, the guidance re-reads from
  the service and never assumes success locally.
- **Tenant boundary**: guidance, steps and prepared chat requests refer only to records of
  the active company. Cross-company identifiers behave as not found.
- **Unreachable branch**: the `failed` cost stage is currently never produced. Its
  guidance is still defined, so it is correct if it ever appears.
- **Viewer without an AI configuration**: the chat step says AI is not configured and
  links to Settings > AI (the existing pattern).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every shared service result that reports a missing, stale, pending, failed
  or unavailable basis to the web MUST include resolution guidance. The guidance is a
  stable reason code plus an ordered list of steps. Each step has a stable code, a state
  (done, open or blocked), the required role (member, owner or operator), and a path
  type (web form, chat handoff, decision review, system status, app page, or none) with its target.
- **FR-002**: Step order and the first open step MUST be determined by the shared
  services, not by the web.
- **FR-003**: Contribution guidance MUST report upstream blockers (inventory review,
  receipt cost, consumption, billed line, selling costs) instead of only the last
  contribution-level gap.
- **FR-004**: Every reason, stage, step and blocker code the web can display MUST have a
  label in every supported web language. The existing localization audit MUST fail when a label is
  missing.
- **FR-005**: The web MUST NOT show raw machine codes, tool names or operation names
  outside the Inspector and developer-oriented views. It MUST NOT show the same reason
  twice.
- **FR-006**: The web MUST present guidance through one shared component: plain reason,
  ordered steps, first open step highlighted, one control per open step.
- **FR-007**: A step whose path is a web form MUST open that existing form, prefilled
  with the scope where the form supports it.
- **FR-008**: A step whose path is a chat handoff MUST open chat with an unsent,
  editable request that names the scope. It MUST NOT send, propose or confirm anything on
  its own.
- **FR-009**: A step that requires a role the viewer lacks MUST show who must act and
  MUST NOT offer a control that the service would refuse. A company in which cost decisions cannot be confirmed MUST show
  no write path.
- **FR-010**: The cost panel MUST NOT show a value field that the service never provides
  for that scope kind. It MUST show the specific reason for a missing carrying value.
- **FR-011**: Projection freshness messages MUST state whether background processing is
  available, link to system status when it is not, and show the recorded cause for a
  failed calculation.
- **FR-012**: The Exceptions page MUST show catalog titles and resolution text in the
  viewer's language. It MUST offer the resolving step wherever FR-001 guidance exists
  for the finding's scope.
- **FR-013**: The Price determination report MUST let the user choose a business partner
  and an item, and resolve them through the existing pricing service.
- **FR-014**: Delivery blocker entries and Storyline step checks MUST use the shared
  guidance presentation.

### Domain and Traceability Requirements

- **DR-001**: Guidance is a read-time derivation from held Reality and evidence records.
  It MUST NOT be stored and MUST NOT create or change any Fact, review, proposal or
  source record (Constitution VIII).
- **DR-002**: Guidance steps MUST reference existing records through opaque IDs and the
  shortest true link (for example the waiting ChangeProposal, the receipt, or the item).
  They MUST NOT use human numbers as identity.
- **DR-003**: Guidance MUST be computed by the same shared services that the web, CLI,
  MCP and chat already use for the underlying read. MCP and chat reads MUST return the
  same codes.
- **DR-004**: Every guidance query MUST be tenant-scoped. A prepared chat request MUST
  carry only identifiers from the active company.
- **DR-005**: No new tables or typed fields are introduced. The cost query response and
  the projection metadata response gain a guidance structure only.

### Key Entities

- **Resolution guidance**: a derived description of why a basis is not available and the
  ordered steps that would make it available for one scope. It is not persisted.
- **Guidance step**: one action in that order, with its state, required role and path.

## Success Criteria *(mandatory)*

- **SC-001**: In a German session, none of the surfaces listed in Scope shows a raw
  machine code in any state that the services can produce, verified by an automated
  browser check.
- **SC-002**: For every missing-basis state on the cost panel, the viewer is offered
  either a working control or the name of the role that must act.
- **SC-003**: A member can go from "DB1 not evidenced" to a confirmed contribution review
  using only the web and the chat handoff, without typing a tool name.
- **SC-004**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Proposing a cost change requires an active member of the company
  (`preview_cost_change` → `_tenant_member`); confirming requires an active owner
  (`execute_cost_change` → `_owner`). Verified in `services/costing.py`.
- Chat can already open with a prepared request: the shell listens for the
  `reality:open-chat` window event, and `ChatPage` accepts `initialDraft`. Storyline uses
  this today. The handoff reuses it.
- The system readiness service (spec 149) is the source for background-processing state.
- The operational exception catalog and `resource_catalog.yaml` already hold German
  labels for exception classes; resolution texts need new German labels.
- Cost forms for reviews, price lists and payment terms are follow-up specs, and the
  guidance will point to them once they exist.

## Open Questions

None. Scope decisions made while writing, for the owner to accept or overturn in review:

- Operator-only steps are shown to every member as "operator work" with a system status
  link, not hidden.
- The Price determination input (FR-013) is included because it only wires an existing
  read service to the page. The price list and payment term forms are excluded.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US2 1–4, US3 1–3 | service tests for cost and projection guidance |
| FR-002 | US2 1–2 | service tests on step order |
| FR-003 | US2 1–2 | contribution guidance service tests |
| FR-004 | US1 4 | i18n audit extension, failing on a missing label |
| FR-005 | US1 1, 3 | browser check on German surfaces |
| FR-006 | US2, US3 | web component tests |
| FR-007 | US3 1 | web component test with form route |
| FR-008 | US3 2 | chat handoff test (no send, no proposal) |
| FR-009 | US3 4–5 | role and sandbox tests |
| FR-010 | US1 2, US2 3 | cost panel component test |
| FR-011 | US4 1–2 | projection freshness tests |
| FR-012 | US1 3, US5 1 | exceptions page test in German |
| FR-013 | US5 3 | report input test |
| FR-014 | US5 2 | blocker and storyline rendering tests |
| DR-001 | all | no-write assertion in service tests |
| DR-002 | US3 3 | guidance references by opaque ID |
| DR-003 | US2 | MCP read parity test |
| DR-004 | Edge case tenant | cross-tenant guidance test |
| DR-005 | — | plan schema review: no migration |
