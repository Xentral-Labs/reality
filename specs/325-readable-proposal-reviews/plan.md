# Implementation Plan: Readable Proposal Reviews

## Technical Context
Existing Python 3.12 services, PostgreSQL, React/TypeScript and four-language dictionaries.
No new dependency or schema. Read-time privacy projection only.

## Constitution Check
| Principle | Result | Reason |
|---|---|---|
| Source/evidence and operational authority | PASS | No authority or stored values change. |
| Proven schema and storage discipline | PASS | No migration or persistent field. |
| Tenant/service boundaries | PASS | Existing author-scoped reveal/preview; Web passes authenticated principal. |
| Specification and executable evidence | PASS | Approved scope, test-first privacy and browser proofs. |
| Explainable Web | PASS | Structured held values and collapsed sanitized inspection. |
| Received values | PASS | Display held operations/questions without computing business outcomes. |
Post-design check: PASS. No constitutional exception.

## Research and Design
Research delegated read-only under speckit-plan; see research.md.
Extend services/proposal_reviews.py with optional principal and derived private_review.
Use analytics/proposals.preview for reports, add preview_request projection using existing
_revealed_request for requests. Omit encrypted carrier fields recursively in common review.
Hidden/unavailable private review suppresses confirmation in the view only; existing execution
checks and rejection rights remain authoritative. Hide private output from nonauthors too.
Web get_change_proposal_review passes optional_request_principal. No other reads gain private access.

UI: ProposalReviewCard uses private_review for readable operation/name/question or bounded notice,
with a defensive legacy encrypted-field omission. DecisionReview exposes reusable initially closed
TechnicalDetails that strips credentials/sealed carrier keys. ShipmentActions fallback displays
review intent/effect or receipt using BusinessFieldList; raw sanitized data is optional inspection.
Existing special exchange/return presentations and JSON creation input forms remain unchanged.

## Tests Before Implementation
Backend tests author, nonauthor owner/member, absent principal, removed membership, foreign tenant,
unreadable key, graph request, unchanged stored payload, and Web authenticated identity forwarding.
Frontend/browser tests legacy sealed payload suppression, author readable payload, hidden notice,
collapsed sanitized technical inspection and shipment fields/exact review-token confirmation.

## Execution and Verification
Domain contracts → read services → Web adapter → shared components → dialogs → translations.
Run scoped privacy/analytics/proposal/attribution backend suites and complete required backend
suite; Web build (includes contracts/i18n), browser proof, lint/spec/diff and documentation generation.
Full-run resource failures must be documented and retried, never silently called green.

## Rollback and Risks
Revert the additive projection/UI change; original sealed payloads are unchanged.
Do not reveal private answer receipts to other readers, decrypt in browser, or derive execution
rules in React. Keep unavailable content distinct from authorized readable review.
