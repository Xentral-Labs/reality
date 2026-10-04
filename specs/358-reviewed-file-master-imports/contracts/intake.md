# Interface contract: Reviewed file, master-data and stock imports

**Status**: Proposed interface contract; not an available-runtime API claim.

## Operations and payloads

file_intake.stage preserves raw artifact and registers its source; file_intake.prepare takes explicit profile/mapping/defaults and returns fixed packages, excluded row issues and source references. Row identities are artifact-relative record ordinals independent of physical newline encoding. A single package contains at most 500 rows and is atomic; large input is bounded to 5,000 rows/20 MiB and settles through an exact batch manifest. Do not split an oversized coherent order; report it as review-required. Paginated review uses stable membership and at most 100 row summaries per page.

## Shared outcomes

Use explicit classifications: raw received, prepared/awaiting decision,
needs_review, stale/conflict, rejected, executed/applied, failed with known no
effect, or unresolved execution. An import queue completion is not proof of business
acceptance. Scoped reads return source/proposal/receipt references and safe reasons;
they do not expose artifact storage paths or credentials.

## Authorization and replay

Tenant and actor come from the server-owned context. Recheck current relevant
authority at confirmation/application. Exact content digests and opaque IDs bind
the offered review; renewing a review invalidates the old digest. Replay returns
retained receipts. Unresolved execution requires reconciliation before redispatch.

## Adapter obligations

Web, CLI and MCP call shared services and retain their existing stronger permission
checks. No transport implements matching, stock correction or posting logic. Every
important displayed effect links to source and decision; all recovery/status reads
are side-effect free. Unknown/legacy attribution is shown truthfully.

## Deterministic byte-bound packaging

The 20 MiB intake limit measures original uploaded bytes, including encoding/BOM.
The existing legacy 2 MiB upload rule remains unchanged for its single-file path.
For new large-file packages, the 2 MiB package limit measures UTF-8 canonical
serialized prepared-unit content: compact JSON, stable key ordering, unescaped
Unicode and canonical decimal/date strings. Hash/digest metadata is excluded from
the content-size bound but included in the full review digest. Store that measured
size in the non-authoritative review so the boundary is explainable.

Scan source record ordinals in order. Append a row only if the complete resulting
package stays within both 500 rows and 2 MiB; otherwise start the next package.
Orders are indivisible and may only be appended as complete groups. A row or order
that exceeds an atomic package bound is explicitly oversized/needs-review and is
excluded before any manifest is approved. Exclusion never occurs during apply.
The controlled 5,000 short-item-row workload has ten packages; variable-width
input may have more. A manifest supports at most 500 packages; larger preparation
results require separate explicit selections, never an approval of future members.

Test exact byte boundaries, multibyte UTF-8, BOM, quoted multiline CSV fields,
cross-package duplicates, a single oversized row/order and a valid 5,000-row input
needing more than ten packages. Structural parsing failures prevent the whole
file's review; row-level semantic issues can be explicitly excluded beforehand.
