# Admission Contract

REALITY_AUTO_APPROVE_LIMIT: missing/blank = unlimited; 0 = manual approval;
positive integer = cumulative finite capacity; invalid/negative = manual approval.
GET /api/admin/access-capacity returns {used: integer, limit: integer | null}.
Platform overview deployment.automatic_access_limit follows the same contract.
Signup still requires accepted terms and email verification. Successful verification
uses existing active/pending status response and navigation. No new endpoint or tool.
