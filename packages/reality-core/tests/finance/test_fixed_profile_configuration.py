"""Spec 356 FR-002: fixed setup retains bounded configuration authority."""
import pytest
from conftest import record_by_id

from reality.db.core import PlaygroundRun
from reality.services import company_setup, core
from reality.services.finance import accounts
from reality.services.intake import _invoke
from reality.services.tenant_policy import _profile_scope


@pytest.mark.parametrize("mutation", ["changed", "repeated"])
def test_fixed_profile_account_invocation_is_exact_and_single_use(session, scheduled_owner, mutation):
    setup = company_setup.create_company(session, scheduled_owner.id, "fixed-finance", "Fixed finance", "sandbox", "international_demo", confirmed=True)
    run = record_by_id(session, PlaygroundRun, setup["run_id"])
    tenant = setup["tenant_id"]
    def callback(db, company, **arguments):
        if mutation == "changed":
            arguments["name"] = "Unreviewed account"
        accounts.create_account(db, company, **arguments)
        if mutation == "repeated":
            accounts.create_account(db, company, **arguments)
    with _profile_scope(session, run.id, scheduled_owner.id):
        _invoke("finance_account_create", accounts.create_account, session, tenant, code="customer_reduction", name="Customer reductions", role="customer_reduction", _commit=False)
        with pytest.raises(core.InvalidOperation) as refused:
            _invoke("finance_account_create", callback, session, tenant, code="supplier_reduction", name="Supplier reductions", role="supplier_reduction", _commit=False)
        assert refused.value.code in {"intake_approval_required", "intake_review_invalid"}
