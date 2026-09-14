# Research

- Decision: Reuse the existing services and editor controls inside a new wizard.
  Rationale: Existing creation records only a question; subsequent capabilities exist.
  Alternatives: A cosmetic first screen leaves the lifecycle confusing; rewriting the
  legacy workbench risks existing version management. No new library is necessary.
- Decision: Resume from existing evidence, decision and immutable versions.
  Rationale: Saved milestones already contain authoritative progress. Simulation is
  ephemeral and must be rerun after reopening. Reject persisted stage flags.
- Decision: Retain separate reviewed writes within the five stages.
  Rationale: Evidence, recommendation and interpretation are separate existing writes.
  Reject silently batching them or labeling draft creation as activation.
- Decision: Seed only illustrative goal/purpose/characteristic suggestions; source
  mappings come from selected held evidence. Rule subjects remain commitment/line.
  Rationale: Manual Fact catalog predicates do not expand extraction capabilities.
