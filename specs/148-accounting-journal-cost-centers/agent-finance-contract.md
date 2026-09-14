# Agent Finance Explanation and Action Contract

**Status**: Owner-requested requirements; not a new autonomous execution authorization.  
**Feature**: [148](spec.md)

## Authority boundaries

Agents access the same tenant-scoped services/tools as Web and CLI. They cannot write ORM records, approve their own proposals or manufacture factual authority from inference. The narrow configured automatic source handlers are not blanket agent mutation permission.

| Information | Authoritative owner |
|---|---|
| Source-stated amounts, dates, cases, provider outcomes | Lossless SourceRecord and faithful document/component evidence |
| Financial effect | LedgerEntry group and explicit correction relationships |
| Applied payment/credit | SettlementAllocation and its effective status |
| Accepted reduction, hold, earmark, mapping choice | Explicit evidence/decision with actor and approved scope |
| Current open/free/earmarked amount, trade discrepancy | Shared derived read/projection with inputs and coverage |
| Additional source-supported observation with no existing typed owner | Reviewed Fact predicate and existing observe_fact service |
| Mutation performed and who approved | ChangeProposal/BusinessEvent/action evidence |

Do not create Facts such as invoice.paid, customer.balance or order.unbilled to mirror typed state or derivations. Internal agreements and hypotheses cannot bypass the Fact contract's source requirement. This scope requires no new Fact predicate by default; any genuinely new source observation needs a concrete reviewed use case and catalog definition first.

## Required shared explanations

Provide structured tools/read contracts for financial item, partner financial position, payment/credit usage, provider settlement, advance use, payable eligibility and order trade-finance chain. Reuse common explanations rather than separate agent-only computations. Each answer includes:

- Exact tenant/subject identity and requested scope/filter.
- Measure meaning, amount as exact decimal text, currency, basis and direction; distinguish cash, gross claim, net evidence, adjustment and available credit.
- Evaluation/read cutoff, source event/document dates and source coverage/freshness where held. A current read with old dates is not a reconstruction of every historical state.
- Included source/ledger/allocation/decision IDs and signs sufficient to explain totals, with bounded continuation for larger sets. Return full-scope totals independently of page size and explicit incomplete/unknown state.
- Source versus internal assertion versus derived observation, actor/reason where applicable and shortest-link access to evidence/payload.
- Missing/contradictory inputs and the practical limit they impose on the answer.
- Eligible next actions, current preconditions, known blockers, confirmation requirement and expected affected measures. Eligibility must be revalidated at execution.

The API owns arithmetic/eligibility and supplies explanatory components. Agents may phrase the answer but must not reconstruct authoritative balances by summing only a fetched first page. Continuation binds scope and read cutoff; if a stable snapshot cannot be continued, return an explicit restart requirement rather than mixing versions. Export and UI reuse the same result scope where applicable.

For simultaneous views, declare the snapshot/cutoff contract; the plan must choose a supported consistency mechanism. Do not claim unlimited historical as-of support. Reversal and later source versions must preserve the distinction between current effective position and the original event history.

## Example acceptance answers

- Invoice 1,000 is settled by cash 980 plus explicitly accepted adjustment 20; not Cash received 1,000.
- Customer paid 100 through PSP; provider fee is stated 3; bank has a matched receipt 97. Customer has no fee-induced unpaid remainder.
- Supplier invoice 1,000, actual payment 900, documented agreed reduction 60: payable 40, with separate source and approval trace.
- Supplier credit 50 is available, customer credit 100 exists for the same dual-role party: separate sides, no invented net 50.
- Advance 200 is earmarked to order A: total unallocated credit 200 but free credit 0; unrelated invoice B cannot consume it without release.
- Supplier invoice is held: still owed and aging, unavailable for a new proposed payment. Actual bank evidence during the hold is a recorded occurrence, not hidden.
- Imported outstanding 600 belongs to an original invoice of 1,000: opening claim 600, no reconstructed historic payment 400.
- Goods shipped with unknown legacy invoice coverage: billing cannot be established, not confirmed unbilled revenue.

## Action verification

Capability metadata must cover every new financial action, including when not to use it, exact identity/amount requirements, source or decision authority, retry identity and expected refusal. Proposals contain the concrete effects and stale-data revision. A successful tool call is not by itself proof that a bank paid, a provider settled or external accounting posted.

After a confirmed internal action, return committed result IDs and re-read the named authoritative position/eligibility view. Report applied, refused, unknown outcome and external evidence pending distinctly. Unknown execution is reconciled by request identity before any retry. Confirmation cannot be silently reused for changed amounts, source scope, account selection or refund direction.

## Planned proof

Run a deterministic tool-driven business story through import → invoice → payment → adjustment → credit → refund/correction plus provider, advance, hold and migration branches. Assert exact structured totals, origins, capability refusals and post-action receipts. Test colliding tenant identities, pagination beyond one page, missing coverage, source changes between preview/confirm, permissions revoked, concurrent allocation and unavailable external confirmation. Facts are not written by explanatory reads. Web/CLI/MCP consume the same service outputs and retain current token allowlists.
