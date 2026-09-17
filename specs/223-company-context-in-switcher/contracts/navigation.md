# Navigation contract

The Company navigation group contains Integrations and Storyline only. `/app/settings`
with `settings_view` of `company`, `new`, `personal`, `access`, `ai`, `agents` or `usage`
is accepted; any other value falls back to `company`. `settings_view=new` opens the
company page with the creation form open and creates nothing by itself.

`/app/demo-data?tenant=…` is unchanged and is reached from the header live indicator and
from the Demo data simulation card in Integrations → My integrations. The card is present
for `company_kind` demo or sandbox, for a company with `sandbox_run_id`, and for any
company with a `demo_data_state`; it is absent otherwise.
