# Research

- Decision: restore behavior from pre-9b8394a App.tsx with current modal and confirmation.
  Rationale: legacy editor and result panels were removed, shared APIs remain.
  Alternative: restore old shell rejected as unnecessary and regressive.
- Decision: retain explicit condition/output scopes and source-line ID mapping.
  Rationale: the old form itself omitted some advanced parameters; restoration must not lose them.
- Decision: recover advanced normalization/value mapping from matching implementation proposal.
  Rationale: current rule DTO omits these fields; no backend change needed.
- Decision: activation gated by successful exact-version simulation; replay only active rule,
  each batch explicitly confirmed. Existing backend semantics remain unchanged.
- Read-only research agent checked existing service validation and API shapes. No unresolved questions.

## Preimplementation analysis

Ten requirements (FR-001–008, DR-001–002) map to three stories and tasks T003–T009;
T010–T011 supply cross-cutting verification/review. No unmapped requirements or tasks,
no ambiguous product decisions, and no critical Constitution findings. Quality checklist:
five reviewed criteria passed, zero unchecked. Existing ignore files already cover build,
virtual environment and dependency outputs; no setup changes required.

FR-011 preimplementation analysis: owner approved the unified example step. Requirement, plan and T015 agree; no unresolved clarification or critical finding. Existing simulation cannot filter by selected evidence, so UI retains explicit bounded-preview wording.
