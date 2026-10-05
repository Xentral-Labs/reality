# Coordination schema

CaseRollout has tenant_id (PK/FK), version (377), commitment_after and return_after
(nullable strings: NULL indicates completed scan), completed_at and created_at (UTC).
It records platform version coordination and traversal, never fulfillment or approval.
Cursors advance transactionally with bounded case creation. Completed time is written
only once both scans finish and the consumer catches up. Existing adoption, checkpoints,
cases, bindings and Sources are retained. Existing tenant composite FKs remain unchanged.
ScheduledJobRun actor constraint gains one specific internal unscheduled case job;
legacy actorful case runs remain supported. No actorless public schedules permitted.
