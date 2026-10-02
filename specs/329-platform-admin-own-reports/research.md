# Research

## Current authority
Decision: authorize private analytics through an active persisted AppUser and either active company membership or current platform administration for a nonarchived business tenant. Do not trust Principal.is_platform_admin or cached ORM flags.
Rationale: API analytics principals omit the admin flag; scalar SQL checks apply current revocation uniformly to services, API and shared tools.
Alternatives rejected: fabricate memberships (changes authority); bypass owner predicates (violates private-per-user scope); adapter-only exception (leaves tools/workers inconsistent).

## Deferred analysis
Decision: requests._member delegates to the shared private-author eligibility guard while retaining its existing nondisclosing errors. Scheduling admission and worker execution already call this guard.
Rationale: interactive and deferred private analytics must have the same current-user eligibility; no new job infrastructure.

## Presentation
Decision: use existing authenticated AuthUser.is_platform_admin explicitly in Shell/SettingsPage, and a shared access-label helper in switcher/company cards. Actual membership roles take precedence.
Rationale: absence of a membership is not evidence of admin access. Bootstrap role remains lossless and truthful; no API schema needed.
Alternatives rejected: infer admin from visible company; set bootstrap role to owner/admin; expose owner administration controls outside this feature.

Research agents: admin_report_research and admin_switcher_research completed read-only investigation under speckit-plan Phase 0. All technical unknowns resolved.
