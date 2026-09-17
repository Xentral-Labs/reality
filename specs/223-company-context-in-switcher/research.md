# Research

Decision: move company management into the switcher rather than the profile menu. The
profile menu is user scope (profile, documentation, sign out); the company list, roles,
tokens and danger zone are company scope, and the switcher is already the company
control. Alternative considered: keep both entries and only rename Demo Data. Rejected
because the duplicated company list, not the wording, is what makes the group confusing.

Decision: present the simulation as a source under Integrations. It writes orders into
the company exactly as a connected system would, and Integrations already distinguishes
registered sources from preparation drafts. Alternative considered: surface it only in
the switcher. Rejected because the entry point would then disappear whenever the
simulation is stopped, leaving the page reachable only by address.

Repository reference check: `demo_data_state`, `company_kind` and `sandbox_run_id` are
already part of the bootstrap `Tenant`, so the switcher's state line costs no read. The
header `LiveSimulationIndicator` already links to `/app/demo-data` and stays unchanged.
Spec 146 FR-029 is the statement this supersedes; it is recorded in docs/WEB_SPEC.md.
