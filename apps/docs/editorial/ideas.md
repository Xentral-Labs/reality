# Idea board

Working cadence: one post every two weeks. English is canonical; German ships at the same time.

Statuses: `backlog` → `next` → `drafting` → `published`. Move rows between the sections below; do
not add a status column.

## Drafting

| Slug                | Claim in one sentence                                                         | Target     |
| ------------------- | ----------------------------------------------------------------------------- | ---------- |
| partially-delivered | One status field answers four questions at once and keeps none of the inputs. | 2026-09-18 |

## Next

| Slug                         | Claim in one sentence                                                                                                  | Target     |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------- |
| order-changed-after-shipping | When the customer changes an order that already shipped, an editable document loses the history that decides who pays. | 2026-10-02 |
| stock-is-not-a-number        | A stock balance is a derivation, and storing it as a column is what makes availability unexplainable.                  | 2026-10-16 |

## Backlog

Grouped by the angle they argue from, not by chapter.

### The status-field teardowns

These take one familiar ERP field and show which distinct claims it has silently merged. The launch
post established the pattern; each of these reuses it on a different field.

| Slug                     | Angle                                                                                                |
| ------------------------ | ---------------------------------------------------------------------------------------------------- |
| paid-is-not-a-status     | "Paid" hides partial payments, allocations, credits and reversals behind one boolean.                |
| what-cancel-really-means | Cancellation, return, adjustment and correction are four different events that one button conflates. |
| open-quantity-lies       | An open-quantity column silently picks one of several defensible definitions and hides which.        |
| delivery-date-theatre    | A promised date with no evidence behind it is a guess that the whole company then plans against.     |

### Agent Operations

The category-defining pieces. These are the ones most likely to be cited, so they need the most
care.

| Slug                               | Angle                                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------- |
| the-process-owner                  | A new accountable role: the person who governs what an agent may claim, propose and execute.      |
| approval-queues-are-the-product    | The interesting part of agent safety is not the model, it is who signs and how the queue empties. |
| a-successful-response-is-not-proof | Verification after execution is a separate step from the execution succeeding.                    |
| what-may-be-claimed                | Claim boundaries as a design surface: reads that state what they do not prove.                    |
| mcp-as-the-erp-boundary            | Exposing an ERP to agents over MCP without exposing the ORM.                                      |

### Modelling and integration

For the technical audience. These are the posts to syndicate to dev.to and Lobsters.

| Slug                           | Angle                                                                                            |
| ------------------------------ | ------------------------------------------------------------------------------------------------ |
| never-edit-the-payload         | Lossless ingestion: why the upstream payload is kept verbatim and interpretation is replaceable. |
| shortest-true-links            | Over-linking rots; the shortest true link is a modelling discipline, not a shortcut.             |
| append-only-correction         | Correcting a movement by recording another one, and what that buys the auditor.                  |
| idempotency-is-a-feature       | Re-running an import must be boring. What that requires from the connector contract.             |
| explainability-by-construction | If a number is derived, it can be explained; if it is stored, it can only be defended.           |

### Reader-facing service pieces

Lower effort, high shareability. Good filler between the heavier essays, but never more than one in
a row.

| Slug                        | Angle                                                                                       |
| --------------------------- | ------------------------------------------------------------------------------------------- |
| audit-your-status-fields    | A checklist an ERP team can run against their own system in an afternoon.                   |
| what-open-source-means-here | What is actually open in Reality, what that lets a reader do, and what it does not promise. |
| reading-paths               | Three routes through the guide for warehouse, finance and integration readers.              |

## Published

| Slug                  | Title                 | Date       |
| --------------------- | --------------------- | ---------- |
| why-i-started-reality | Why I started Reality | 2026-09-04 |
| eleven-tables         | Eleven tables         | 2026-09-11 |

## Parked

Ideas that were considered and set aside. Keep the reason — it stops the same idea coming back.

| Slug               | Reason                                                                               |
| ------------------ | ------------------------------------------------------------------------------------ |
| erp-market-history | Interesting, but it argues about the past instead of making a checkable claim today. |
