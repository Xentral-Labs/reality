# Research: Learning Playground

Date: 2026-09-06. Evidence: current origin/main, inspected before planning. No runtime writes.
The plan skill's bounded research agents inspected isolation and execution independently.

## Private tenant per run

Decision: reuse Tenant and membership with immutable purpose plus owner-bound run metadata.
Rationale: existing queries already scope by tenant; a run_id on every business row would
duplicate isolation. Tenant currently has no purpose. archived_at only hides it, not guards writes.
Evidence: db/core.py Tenant; services/core.py get_tenant/archive_tenant; web/api.py company creation.
Rejected: separate simulator database, one shared demo company, production clone or name-based flag.

## Verified Playground admission

Decision: narrow verified/pending user lane, not automatic production admission.
Rationale: web/auth.py verifies accounts into active or pending_approval; web/app.py currently
blocks pending users on business APIs. Login alone does not currently mean immediate product access.
Dedicated run endpoints and generic allowed sandbox reads must resolve ownership before bypassing
the production admission gate. Unverified/disabled and auth-disabled anonymous usage stay denied.

## Policy needs service coverage

Decision: fail-closed tenant operation policy, checked at shared services and outbound boundaries.
Evidence: direct HTTP and CLI service calls bypass tool filtering; memberships.py enqueues email;
security/secrets.py resolves credentials; agent/settings.py permits custom providers; mcp/auth.py
issues tokens. UI hiding and prompt restrictions cannot enforce the boundary.
Allow managed LLM and account verification mail explicitly; never sandbox business delivery.

## Existing proposal receipt, not a second execution engine

Decision: reuse tools/application.py approve_and_execute_proposal and proposal_execution_status.
Rationale: existing CAS and executing/unknown semantics are the right no-blind-retry boundary.
Reserve already has correlated event reconciliation. Extend only V1 handlers to that evidence level.
Evidence: _action_id currently reaches only selected handlers; movement creation commits internally.
_consume_reservations changes status/creates remainder without corresponding events; fulfillment
also lacks a lifecycle event. New trace events are necessary before claiming a complete recorder.
Rejected: assuming sequence-range differences prove causality; making a multi-command chat atomic;
adding synthetic Facts for every effect; model-written receipts.

## Guided lesson and custom references

Decision: one versioned trading preset and a stepwise lesson on real tools; deterministic buttons.
Evidence: normal_month requires an empty tenant, fixed September 2026 dates and completion marker;
partial failure can leave nonempty state without completion. It is not a replayable step engine.
Masterdata business_discover, shared suggestions, creation proposals and bulk seed services exist.
Manual reference data need no fabricated SourceRecord. Stock needs a separate Movement action.

## Observation receipts and time

Decision: bounded before/after audit observations with evaluation time and event watermark,
separate from live shared-reader answers. No simulated clock in V1.
Evidence: projections.py refresh uses checkpoints and commits; exceptions.py supports as_of;
the activity view is time-windowed and capped, while a run needs action-based history.
Rejected: universal historical reconstruction, storing calculated values as new Reality authority.

## Existing UI and deployment

Decision: one Product Web workspace with shared Inspector/autocomplete and ordinary locales;
public static preview in Docs plus light Site CTA. No Sites-hosted replacement application.
Evidence: apps/web App.tsx onboarding and suggestions; apps/docs guide; configured surface origins.
Dependencies: managed provider configured by deployment; rollout flag and quotas. Guided mode
remains useful without it. Owner review of schema and security design remains a pre-implementation gate.
