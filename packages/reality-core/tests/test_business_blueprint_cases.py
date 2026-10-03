"""Case similarity remains scoped, dimension-aware and read-only."""
import pytest

from reality.domain.business_blueprints import Blueprint
from reality.domain.business_blueprints import TestFact as Fact
from reality.domain.business_blueprints import TestScenario as Scenario
from reality.services import business_blueprints as service
from reality.services import core


def blueprint():
    return Blueprint(kind="tool", key="credit_exposure", label="Credit", purpose="Inspect", status="partial", release={}, scenarios=(Scenario(id="case",name="same currency",path="test.py",line=1,digest="a",facts=(Fact(name="limit",value="1000.00",origin="test:1",currency="EUR"),Fact(name="quantity",value="2",origin="test:2",unit="piece"))),))


def test_case_dimensions_and_decimal_equivalence(session,business,monkeypatch):
    monkeypatch.setattr(service,"explain",lambda *a,**k:blueprint())
    def compare(facts):
        return service.compare(session,business.tenant.id,{"kind":"tool","key":"credit_exposure","facts":facts})["comparisons"][0]["conditions"]
    assert compare([{"name":"limit","value":"1000","currency":"EUR"}])[0]["status"] == "matching"
    assert compare([{"name":"limit","value":"1000","currency":"USD"}])[0]["status"] == "different"
    assert compare([{"name":"limit","value":"1000"}])[0]["status"] == "unknown"
    assert compare([{"name":"quantity","value":"2","unit":"kg"}])[1]["status"] == "different"
    assert compare([])[0]["status"] == "unknown"


def test_other_company_record_is_not_read(session,business,monkeypatch):
    monkeypatch.setattr(service,"explain",lambda *a,**k:blueprint())
    other=core.create_tenant(session,"Other blueprint company")
    party=core.create_party(session,other.id,"Other customer","customer")
    with pytest.raises(core.NotFound):
        service.compare(session,business.tenant.id,{"kind":"tool","key":"credit_exposure","record":{"kind":"party","id":party.id}})
    from reality.mcp.catalog import MCP_TOOL_CATALOG
    tool = next(item for item in MCP_TOOL_CATALOG if item.name == "business_logic_compare")
    with pytest.raises(core.NotFound):
        tool.handler(session, business.tenant.id, {"kind": "tool", "key": "credit_exposure", "record": {"kind": "party", "id": party.id}})
    with pytest.raises(ValueError,match="either"):
        service.compare(session,business.tenant.id,{"kind":"tool","key":"credit_exposure","record":{"kind":"party","id":party.id},"facts":[{"name":"limit","value":"1"}]})


def test_stale_evidence_and_duplicate_fact_names_are_rejected(session,business,monkeypatch):
    monkeypatch.setattr(service,'explain',lambda *a,**k:blueprint())
    for extra in ({'evidence_digest':'outdated'},{'facts':[{'name':'limit','value':'1'},{'name':'limit','value':'2'}]}):
        with pytest.raises(ValueError):
            service.compare(session,business.tenant.id,{'kind':'tool','key':'credit_exposure',**extra})


def test_authorized_current_read_creates_no_business_authority(session,business,monkeypatch):
    from sqlalchemy import func, select

    from reality.db.core import BusinessEvent, CommitmentHold, LedgerEntry
    monkeypatch.setattr(service,'explain',lambda *a,**k:blueprint())
    def counts():
        return tuple(session.scalar(select(func.count()).select_from(model).where(model.tenant_id==business.tenant.id)) for model in (BusinessEvent,CommitmentHold,LedgerEntry))
    before=counts()
    result=service.compare(session,business.tenant.id,{'kind':'tool','key':'credit_exposure','record':{'kind':'party','id':business.customer.id}})
    assert result['context']=='current_state'
    assert result['historical_rule_version']=='unknown'
    assert any(f['name']=='credit_limit' for f in result['case_facts'])
    assert counts()==before
