# Verification

## Completed checks

- The measurement that opened the feature: a created demo company reported
  `sales_order: 34 docs -> {'Northstar Outdoor': 34}` and
  `sales_invoice: 24 docs -> {'Northstar Outdoor': 24}`, with the other nineteen pool
  customers holding no document at all. The continuous Demo Data stream was measured in
  the same company over 400 draws and was already spread (largest share 22 %), so only
  the seeded baseline needed changing.
- The new scenario test failed first for the stated reason
  (`AssertionError: Counter({'Northstar Outdoor': 34}) … assert 1 >= 18`).
- Seeding the full pool surfaced three pinned bounds that had to move together with it:
  the profile's own self-check, the manifest contract and the scenario count, all from
  8 parties to 24. The execution fixture keeps its two parties, so both its orders stay
  with the single customer it seeds.
- Final distribution over the 34 seeded orders: 20 distinct buyers, largest 4, three
  customers above two orders, everyone else one or two.
- Scenario suite: 5 passed, including the comparison families, the invoice and credit
  note party, three distinct suppliers and the identical mapping across two companies.
- Focused company setup, demo profile history, execution profile, demo data intake,
  demo data security and free playground suites: 64 passed.
- Lint and format clean; spec coverage policy passed.

## Completion

Full PostgreSQL suite: 2530 passed, 9 skipped in 17:35.

Renumbered from 197 to 200 after `197-chat-scope-hardening` claimed that number on main
first; the branch name is left alone so the pull request survives. Rebased onto the main
that carries feature 198, and the suite was run again on that base.

Existing demo companies are not rewritten; the change only affects companies created
after it. The payload schema, profile version, preset version, source namespaces and
case manifest keys are unchanged, which is what keeps the Demo Data connection preview
matching the profile's customers by name.
