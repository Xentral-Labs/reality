# Data model and schema review

No new table or business field is proposed. Source, Evidence, Reality, BusinessEvent, ProjectionRow and ProjectionCheckpoint retain their meanings and relationships.

## ScheduledJobRun amendment
`actor_id` remains a foreign key to AppUser but permits NULL for exactly one internal job:

```sql
ALTER TABLE scheduled_job_run ALTER COLUMN actor_id DROP NOT NULL;
ALTER TABLE scheduled_job_run ADD CONSTRAINT ck_scheduled_run_actor
CHECK (
  (job_type = 'projections.refresh' AND actor_id IS NULL AND schedule_id IS NULL)
  OR (job_type <> 'projections.refresh' AND actor_id IS NOT NULL)
);
CREATE UNIQUE INDEX uq_projection_run_unfinished
ON scheduled_job_run (tenant_id, job_type)
WHERE job_type = 'projections.refresh'
  AND status IN ('pending', 'running', 'retry', 'unresolved');
```

Proof: FR-004 requires database-only maintenance without impersonating a human, and FR-003 requires durable coalescing across scheduler replicas. Existing non-null actors cannot truthfully represent this capability. The partial index prevents two replicas enqueuing unfinished runs for one tenant. Existing request IDs, frozen configurations and claims suffice; no redundant event, source or document foreign keys are added.

Service validation restricts internal configuration to a bounded set of known materialized projection names and contract version. The internal enqueue helper is not exposed as a user command/MCP mutation. Ordinary user job types continue to require an authenticated actor. NULL never means general permission.

## Projection progress
Checkpoints mean fully published progress only. A queued job does not advance them. Freshness is derived from the completed checkpoint, relevant committed events, builder version, minute eligibility and existing run state. No second freshness authority is stored. Values and source links in rows are disposable canonical derivations.

## Migration safety
Upgrade preserves existing rows. Downgrade refuses if internal runs exist; operators must keep additive schema during code rollback rather than lose run history. The owner explicitly approved this proposal and implementation on 2026-09-12.
