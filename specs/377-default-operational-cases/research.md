# Research decisions

- Keep CaseAdoption immutable. A nullable fabricated decision or chosen owner would
  confuse historical approval with version policy. Separate CaseRollout records
  bounded cursor/provenance without business authority.
- Use the existing tenant delivery lock for ensure, scanning and event allocation;
  scans include closed supported identities, evaluating current eligibility in services.
- Use the projection job's persisted-run authorization pattern for the exact case job,
  while retaining authorization for already queued owner runs. Reject public creation.
- Guard default work synchronously; background readiness is explicit. Do not use
  an enabled boolean or hide only the activation UI.
- Main lacks simulator implementation. Keep its work separate and update only the
  supplied integration documents and acceptance test, recording this dependency.
- Independent research reviewed scheduling, immutable adoption, backfill and stale
  approvals. No unresolved design clarification or constitutional exception remains.
