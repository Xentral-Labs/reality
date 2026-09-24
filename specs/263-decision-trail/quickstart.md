# Quickstart: Verify the Decision Trail

1. Start the local stack and apply migrations.
2. As a company owner, open Settings → Agents and issue a new MCP token.
3. With an MCP client using that token, propose and confirm:
   a payment term, a price list with one tier, a customer price-list assignment and an
   item (`proposal_approve_and_execute` with `approved=true`).
4. Open **Decisions → History**: each row shows "confirmed through token ‹name›, issued
   by ‹you›" and the moment of decision.
5. Open **Master data → Items**, then the new item: its origin names the decision and
   links to it; the link opens that decision.
6. Open **Activities** for the price tier: the entry names the decision instead of a raw
   id.
7. Repeat step 3 with a token issued before this feature: rows read "issued by unknown".
8. Measure with SQL:

```sql
select count(*) filter (where decided_via_token_id is not null) * 1.0 / count(*)
from action where tenant_id = :t and status = 'executed' and actor_type = 'agent';

select event_type, count(*), count(action_id)
from business_event where tenant_id = :t and source_record_id is null
group by 1;
```

Both must report full coverage for proposals executed after the migration.
