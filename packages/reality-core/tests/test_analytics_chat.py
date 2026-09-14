"""Private agent changes need a trusted author and explicit confirmation."""

import json

import pytest
from cryptography.fernet import Fernet
from test_analytics_reports import create_args

from reality.services.analytics.execution import AnalyticsError
from reality.services.analytics.reports import list_reports
from reality.services.memberships import Principal
from reality.tools.analytics import caller
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def test_private_proposal_encrypts_definition_and_rechecks_author(
    session, business, scheduled_owner, monkeypatch
):
    monkeypatch.setenv("REALITY_MASTER_KEY", Fernet.generate_key().decode())
    args = create_args()
    principal = Principal(scheduled_owner.id)
    with caller(principal):
        proposal = create_change_proposal(
            session, business.tenant.id, "analytics.reports.change", args
        )
    from reality.services.analytics.proposals import preview

    shown = preview(session, business.tenant.id, principal, proposal.id)
    assert shown["name"] == args["name"]
    assert shown["operation"] == "create"
    assert list_reports(session, business.tenant.id, principal)["records"] == []
    assert args["name"] not in proposal.input + proposal.output
    assert "sales_orders" not in proposal.input + proposal.output
    with pytest.raises(AnalyticsError):
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirmed=True
        )
    with pytest.raises(AnalyticsError):
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirming_principal=principal
        )
    result = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=principal,
        confirmed=True,
    )
    assert result.status == "executed"
    assert args["name"] not in result.output
    assert len(list_reports(session, business.tenant.id, principal)["records"]) == 1
    assert json.loads(result.output)["private_report_changed"] is True
