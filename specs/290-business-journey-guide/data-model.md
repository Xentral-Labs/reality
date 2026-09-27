# Data Model: Business Journey Guide

## JourneyEntry (versioned catalog)

- `id`: unique stable label such as `H02`.
- `section`, `title`, `question`: canonical public English vocabulary.
- `translations`: published localized title/question/summary fields.
- `status`: `supported | partial | recognition_only | missing | out_of_scope`.
- `evidence_level`: `executable | reviewed | inferred | none`.
- `summary`, `limitations`, `keywords`, `question_examples`.
- `tools`, `demo_references`, `product_paths`, `related_journeys`: validated public links.
- `internal_evidence`: allowlisted test/spec references, never publicly serialized.

Rules: `supported` requires `executable`; non-supported entries require a limitation; references resolve; public output uses an explicit allowlist.

## JourneyProposal

- opaque `id` primary key and `creator_account_id` FK.
- `title`, `business_question`, `expected_outcome`, `process_area`, optional bounded `business_context`.
- `normalized_fingerprint` for retry/deduplication assistance.
- `status`: `proposed | under_review | planned | in_progress | available | declined | out_of_scope`.
- optional `public_rationale`, required for terminal unavailable states.
- optional `available_journey_id`, required for `available`.
- moderation and UTC audit timestamps.

Transitions: `proposed → under_review → planned → in_progress → available`; a reviewer may decline, mark out of scope or reopen. `available` retains history and votes.

## JourneyProposalVote

- opaque `id`, `proposal_id` and `account_id`.
- `active`, `created_at`, `updated_at`.
- unique `(proposal_id, account_id)`.

Counts derive from active rows. Withdrawal deactivates; a later vote reactivates the same relationship.

## GuideQuestion (ephemeral)

- bounded question, locale and evidence scope.
- ranked journey IDs/scores.
- structured conclusion with status, limitations and citations.
- provider outcome for observability.

Public questions and generated answers are not persisted in v1.
