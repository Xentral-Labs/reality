# Contract: Decision Attribution

One service, `reality.services.decision_attribution`, answers "which decision, and who
settled it" for a bounded set of proposal ids in a constant number of statements.

```python
def decision_attributions(
    session: Session, tenant_id: str, proposal_ids: Iterable[str]
) -> dict[str, DecisionAttribution]: ...
```

Every surface below embeds the same `decision` object (see `data-model.md`).

## HTTP (web)

| Endpoint | Change |
|---|---|
| `GET /api/tenants/{t}/change-proposals?status=history` | Each item gains `decider`; `decided_by` stays for compatibility. |
| `GET /api/tenants/{t}/change-proposals/{id}/review` | Gains `decided_at` and `decider` for any status. |
| `GET /api/tenants/{t}/timeline` | Each event with an `action_id` gains `decision`. |
| Master-data registers and details (`origin`) | `origin.kind == "application"` gains `decision` when the creating event names one; `origin.actor` stays. |

## MCP / agent tools

| Tool | Change |
|---|---|
| `proposal_approve_and_execute` / `proposal_reject` | The server passes the settling token id to the service; results gain `decider`. |
| `proposal_execution_status` | Gains `decision`. |

The MCP input schemas do not change. Output additions are documented by
`make docs-generate`.

## Browser

- `/app/decisions?decisions_view=history` renders the register;
  `/app/decisions?decisions_view=history&proposal=<id>` opens that decision through the
  existing `ProposalReviewCard`, which reads a proposal of any status.
- `SourceBadge` and `ActivityDrawer` render `decision` as
  "‹action› · confirmed by ‹name›" or "‹action› · confirmed through token ‹name› (issued
  by ‹issuer | unknown›)" with a link to that address, and nothing
  when `decision` is absent.
