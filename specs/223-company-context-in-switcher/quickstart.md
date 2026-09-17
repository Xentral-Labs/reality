# Verification

Run `make lint`, the frontend contract suite, `node scripts/i18n-audit.mjs` and
`tsc -b` in apps/web.

Open the switcher: every company is listed, a company running the simulation shows its
state, and the footer offers Manage companies and New company. Follow New company,
reload, and confirm the creation form is still open at `settings_view=new`.

Open Integrations for a demo or practice company: the Demo data simulation card reports
state, rate and last successful import and opens `/app/demo-data`. Open Integrations for
an ordinary company: no card. Confirm the Company navigation group shows Integrations
and Storyline only.
