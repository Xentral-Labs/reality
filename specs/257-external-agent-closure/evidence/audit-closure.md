# F1–F13 Closure Matrix

**Qualification**: fresh external CanisPro run on 2026-09-24
**Evidence**: [final qualification](final-qualification-2026-09-24.md)

| Finding | Status | Qualification evidence | Remaining requirement |
|---|---|---|---|
| F1 | Fixed | Proposal previews returned review tokens; owner decisions and MCP reconciliation completed. | Preserve FR-003–FR-004 and FR-007 regressions. |
| F2 | Fixed | A free inbound-freight supplier invoice completed without an order line or generic workaround. | Preserve FR-013 regression. |
| F3 | Fixed | Exact-location reservation reported zero availability plus named descendant stock and required explicit movement. | Preserve FR-005–FR-006 regression. |
| F4 | Fixed | Agent preparation plus authenticated-owner Web decisions completed account, costing and finance cases. | Preserve FR-007–FR-008 authority boundary. |
| F5 | Fixed | Discounts, accepted small remainder and overpayment credit completed and reconciled. | Preserve FR-009–FR-011 regressions. |
| F6 | Open | Lower-level credit-note actions completed, but `sales_credit_record_propose` discarded its arguments and failed during confirmation. | FR-031 and FR-033. |
| F7 | Partially fixed | General capability discovery worked; `cost_change_propose` still published an empty schema and shipment-purpose movement values were incomplete. | FR-036. |
| F8 | Improved | Return refusals and supported dispositions were discoverable; restock did not retain the supplied reason. | Preserve FR-017; track secondary observation separately. |
| F9 | Fixed with observation | All four dispositions completed with tracked identity; the restock reason omission does not change physical disposition. | Preserve FR-018 regression. |
| F10 | Open | Closed vocabulary improved, but an invalid billed relationship passed proposal preparation, failed during confirmation and remained `executing`. | FR-033–FR-034. |
| F11 | Fixed | Owner-confirmed dunning with a stated fee completed. The fee is still absent from party/open-item views. | Preserve FR-012; track read parity separately. |
| F12 | Open | Cost attribution worked, but global review invalidation, transfer valuation and missing stated net revenue blocked inventory value and DB1/DB2. | FR-032, FR-035 and FR-037. |
| F13 | Partially fixed | Read/filter/reservation/capability improvements held; empty schemas and unrecoverable `executing` failures remain. | FR-033–FR-036. |

No finding is marked closed merely because a workaround exists. `Fixed` means the fresh external
client completed the intended public path and independently read the resulting business effect.

## Final qualification follow-up — 2026-09-24

The fresh tenant `ten_e19e802603` was qualified after rebuilding the API, MCP and Web services from
the current worktree. The complete observed result is summarized in
[final qualification follow-up](final-qualification-follow-up-2026-09-24.md).

The follow-up confirmed the intended repairs for customer-credit argument retention, scoped
receipt-review freshness, named related-evidence invalidation, exact missing movement IDs and
order-backed invoice finance evidence. It also proved that the lifecycle repair was narrower than
the public requirement, that deployed schema fidelity remained incomplete, and that additional
cross-process gaps block a fully successful qualification. Those residual findings are specified,
without silently expanding spec 257, in `specs/267-agent-qualification-gaps/spec.md`.
