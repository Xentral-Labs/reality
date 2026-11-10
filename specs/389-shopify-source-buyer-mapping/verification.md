# Verification and explicit limits

## Current source checks

- Isolated PostgreSQL combined mapping/capture/catalogue/proposal-parity suite:
  87 passed. Includes actual independent DB sessions: second approval waits on
  the first transaction, then refuses rather than remapping.
- Isolated mapping/refusal/business-annotation/tool-catalogue suite: 81 passed.
  Generic approve was explicitly confirmed true and still cannot execute this
  mapping type. Tests include policy/proof expiry after canonical Source wait.
- Web contract tests: 483 passed. Shared refusal vocabulary only; no layout
  changes or visual/user-journey acceptance is claimed.
- Ruff, spec policy, business-annotation audit, generated docs, Web formatting
  and shared i18n audit passed (3070/3070 in all four supported languages).
- Full current backend suite and hosted CI are not claimed green. Parent review
  of source boundaries found no blocker; exact final CI remains pending.

## Version-pinned schema99 compatibility

Exact old image:
sha256:e236510920b35a2d96233ad6350954d87fcef10b57d036f01b66ef913e4c0ae6

The private v3 artifact copies the SAME current pure domain, canonical service
and narrow tools into a guarded old-image overlay. Proof created only a NEW owned
disposable schema from old Base.metadata, without migration or existing company
data. It verified existing active customer recognition, signed human approval
UUID/original proof digest, truthful token versus external-human attribution,
exact replay/status, canonical candidate mapping reader, unchanged original
source/job input, review-required outcome and zero operational business records.

Authenticated actual ASGI tools/list was tested in that old image: disabling MCP
lifespan returns500 because the session manager never starts; normal MCP
lifespan returns200 and advertises all four narrow tools. Only the old API
lifespan is disabled to avoid its migration/bootstrap. MCP startup does not
start global company workers.

Old99 cannot prepare the newer full business intake. A mapped source remains
held. No accepted order, customer creation, payment, fulfillment, stock effect,
provider call, real model test, actual customer selection or human approval was
performed by this implementation lane. Parent owns any separately authorized
actual Main walkthrough and deployment.
