# Data model

No schema change. SecurityAuditEvent event_type=playground.ai_allowance_granted uses
user_id for recipient, actor_user_id for actor, tenant_id for authorization context,
subject_type=ai_allowance and subject_id=recipient. detail version 1 contains mode,
questions, reason, expires_at and request_key. occurred_at is grant timestamp.
AppUser row lock serializes all grants and dispatch reservations per recipient.
