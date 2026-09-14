from reality.db.core import HandlingUnit, PaymentTerm, SourceSystem
from reality.mcp.catalog import dispatch_tool


def _execute(session, tenant_id, tool, arguments):
    proposal = dispatch_tool(
        session, tenant_id, tool, arguments, allowed_access=("propose",)
    )
    return dispatch_tool(
        session,
        tenant_id,
        "proposal_approve_and_execute",
        {"proposal_id": proposal["proposal_id"], "approved": True},
        allowed_access=("confirm",),
    )["output"]


def test_warehouse_identity_and_payment_term_use_proposal_boundary(session, business):
    handling = _execute(
        session,
        business.tenant.id,
        "handling_unit_create_propose",
        {"nve": "340123450000000001"},
    )
    term = _execute(
        session,
        business.tenant.id,
        "payment_term_create_propose",
        {"code": "NET14", "name": "Net 14", "due_days": 14},
    )
    assert (
        session.get(HandlingUnit, handling["records"][0]["id"]).nve
        == "340123450000000001"
    )
    assert session.get(PaymentTerm, term["records"][0]["id"]).due_days == 14


def test_source_configuration_uses_existing_service(session, business):
    output = _execute(
        session,
        business.tenant.id,
        "source_system_create_propose",
        {"code": "erp", "name": "ERP"},
    )
    source_system = session.get(SourceSystem, output["records"][0]["id"])
    assert source_system.code == "erp"
