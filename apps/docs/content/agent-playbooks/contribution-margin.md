# Playbook: Contribution margin (DB1 and DB2)

Use this playbook when an agent must answer a margin question for an exact received sales-invoice
line. It is the short operational route through the model; the
[inventory cost and contribution chapter](../concepts/business-reality-guide/08-inventory-cost-and-contribution)
explains the accounting logic in depth.

## What the agent is tracking

```text
DB1 = received net revenue − reviewed consumed acquisition cost
DB2 = DB1 − reviewed direct selling cost − reviewed allocated selling cost
```

Reality never treats a missing basis as zero. A negative DB2 is a valid reviewed result; **Not
evidenced** means that no honest result exists yet.

## Situation map

| Business situation                      | First read                                          | What it establishes                                                          | Next action when incomplete                                                         |
| --------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Explain DB1/DB2 for one invoice line    | `cost_query_get kind=contribution scope_id=<line>`  | Retained revenue, consumed cost, selling costs, cutoffs and missing basis    | Follow the named missing basis below                                                |
| Check a current candidate before review | `cost_contribution_preview document_line_id=<line>` | Current exact revenue/consumption candidate and candidate hash               | Prepare the required review with `cost_change_propose`                              |
| DB1 is missing                          | `cost_commercial_match_get document_line_id=<line>` | Whether the invoice line has a reviewed match to exact inventory consumption | Review inventory first if necessary, then propose `commercial_match_review`         |
| DB2 is missing                          | `cost_query_get kind=contribution scope_id=<line>`  | Which selling category or assignment is still unknown                        | Propose `selling_assign`, then `contribution_review`; review a true zero explicitly |
| DB2 looks low or negative               | `cost_query_get kind=contribution scope_id=<line>`  | Exact bridge from revenue through DB1 and selling costs to DB2               | Inspect the referenced evidence; do not “correct” a valid negative result           |
| Knowledge arrived later                 | `cost_query_get` with `review_id` or `knowledge_at` | Which answer was knowable at that retained boundary                          | Compare the older and newer review; never overwrite the older explanation           |
| Compare a portfolio                     | `graph_contribution_reviews_list`, then Analytics   | Confirmed review identities, followed by an explicitly captured population   | Pin the intended contribution basis before aggregating                              |

All identifiers are opaque IDs returned by an earlier read. Human invoice numbers help a person find
the line; they are never used as identity.

## Situation: explain one reviewed DB1 and DB2

1. **See** the invoice in **Finance**, expand its line and open the contribution explanation.
2. **Agent** reads `cost_query_get` with `kind=contribution` and that line's opaque ID.
3. **Check** revenue, consumed acquisition cost and DB1 first; then direct and allocated selling
   cost and DB2. Read the valuation and knowledge cutoffs with the amounts.
4. **Report** both the result and its status. A complete answer names the retained review; an
   incomplete answer names `missing_basis` rather than supplying an estimate.

This is a read-only path. It records no new financial authority.

## Situation: DB1 is not evidenced

1. **Agent** reads `cost_contribution_preview`. It should name the missing commercial or inventory
   basis instead of presenting DB1.
2. **Agent** reads `cost_commercial_match_get`. A reviewed commercial match must connect this exact
   invoice line to exact reviewed consumption.
3. **You** verify the source-backed receipt/opening, ownership, issue and acquisition amount.
4. **Agent** prepares `cost_change_propose` for the required `inventory_review` or
   `inventory_batch_review`, followed by `commercial_match_review`.
5. **You** approve the proposals under **Decisions**.
6. **Check** the new `cost_contribution_preview`; DB1 appears only when received net revenue and
   reviewed consumed acquisition cost are both known.

Do not enter a convenient unit cost merely to make DB1 appear. The acquisition amount must come from
received evidence or an explicit reviewed opening.

## Situation: DB1 exists but DB2 does not

1. **Agent** reads `cost_query_get` and lists each missing selling category.
2. **You** distinguish a real cost from a real zero. Freight, marketplace commission, packaging,
   payment fee, sales commission and other selling cost all need evidence or an explicit reviewed
   zero/not-applicable disposition.
3. **Agent** prepares `cost_change_propose operation=selling_assign` for source-backed supplier
   expense shares. Direct shares belong to one sold line; allocated shares state their allocation.
4. **Agent** refreshes `cost_contribution_preview` and prepares
   `cost_change_propose operation=contribution_review` with the exact candidate hash and complete
   category review.
5. **You** approve; **Check** with `cost_query_get`. DB2 must reconcile exactly to DB1 minus direct
   and allocated selling costs.

Zero is not the default. The zero-selling-cost demo case is complete because every category was
reviewed as zero or not applicable.

## Situation: DB2 is unexpectedly low or negative

1. **Agent** reads `cost_query_get`, retaining the review and cutoff identities.
2. **Check** the bridge in this order: received net revenue → consumed acquisition cost → DB1 →
   direct selling cost → allocated selling cost → DB2.
3. **Agent** follows the referenced commercial match, inventory review, assignments and source
   records. It reports which component drives the result.
4. **You** change something only when the underlying evidence or review is wrong. A negative DB2 is
   not an exception by itself; it can truthfully show an unprofitable sale.

## Situation: costs or knowledge arrive later

1. **Agent** reads the old answer with its `review_id` or `knowledge_at`.
2. **Agent** reads the current answer separately.
3. **Report** what was known then and what is known now. A later supplier invoice, return or review
   creates a new knowledge boundary; it does not rewrite the earlier one.
4. **Check** freshness in `cost_query_get`. Never describe a current review as though it existed at
   an earlier cutoff.

## Situation: compare invoices or a whole portfolio

1. **Agent** uses `graph_contribution_reviews_list` to discover confirmed contribution reviews.
2. **You** choose the population and retained cost basis to compare.
3. **Agent** uses Analytics only with that explicit contribution-cost context; it must not silently
   mix independently reviewed generations.
4. **Check** outliers with the single-line `cost_query_get` explanation before acting on a total.

For a quick walkthrough, create a new company with Demo Data and compare the six
`COST-PORTFOLIO-*`/fixture outcomes documented in the
[worked demo portfolio](../concepts/business-reality-guide/08-inventory-cost-and-contribution#compare-the-demo-portfolio).

## What the agent must never claim

- No DB1 while the commercial match or consumed acquisition cost is unreviewed.
- No DB2 while a selling-cost category remains unknown.
- No assumption that missing means zero.
- No use of invoice numbers as record identity.
- No historical claim without the retained valuation and knowledge cutoffs.
- No direct write: every review or assignment is a proposal using the same application service as
  the app, CLI and API.
