"""Service refusals carry a code and values next to their English sentence (spec 286)."""

from datetime import date
from decimal import Decimal

import pytest

from reality.domain import refusals
from reality.services.core import Conflict, InvalidOperation, NotFound

CATALOG = {
    "version": 1,
    "refusals": {
        "sample_plain": {"message": "The sample is refused."},
        "sample_line": {
            "message": "Line {index} requires a stated amount; it is never calculated.",
            "values": {"index": "number"},
        },
        "sample_field": {
            "message": "{field} cannot be negative.",
            "values": {"field": "term"},
        },
        "sample_amount": {
            "message": "The amount {amount} is due on {day}.",
            "values": {"amount": "amount", "day": "date"},
        },
    },
    "terms": ["Lead time days"],
}


@pytest.fixture
def catalog(monkeypatch):
    monkeypatch.setattr(refusals, "catalog", lambda: refusals.validate_catalog(CATALOG))


# FR-001 / FR-002 --------------------------------------------------------------------


def test_coded_refusal_carries_code_and_values(catalog):
    error = InvalidOperation(code="sample_line", values={"index": 3})
    assert error.code == "sample_line"
    assert error.values == {"index": "3"}
    assert str(error) == "Line 3 requires a stated amount; it is never calculated."
    assert error.template == (
        "Line {index} requires a stated amount; it is never calculated."
    )
    # Every refusal class takes the same keywords.
    assert NotFound(code="sample_plain").code == "sample_plain"
    assert isinstance(Conflict(code="sample_plain"), InvalidOperation)


def test_english_sentence_is_the_filled_template(catalog):
    error = InvalidOperation(code="sample_field", values={"field": "Lead time days"})
    assert str(error) == "Lead time days cannot be negative."
    assert refusals.payload(error) == {
        "code": "sample_field",
        "template": "{field} cannot be negative.",
        "values": {"field": {"value": "Lead time days", "kind": "term"}},
    }


def test_message_and_code_together_is_a_type_error(catalog):
    with pytest.raises(TypeError):
        InvalidOperation("Some sentence.", code="sample_plain")


def test_values_are_only_template_placeholders(catalog):
    with pytest.raises(ValueError, match="values"):
        InvalidOperation(code="sample_line", values={"index": 1, "tenant": "ten_x"})
    with pytest.raises(ValueError, match="values"):
        InvalidOperation(code="sample_line")


def test_values_are_exact_strings(catalog):
    error = InvalidOperation(
        code="sample_amount",
        values={"amount": Decimal("59.5000"), "day": date(2026, 9, 27)},
    )
    assert error.values == {"amount": "59.5000", "day": "2026-09-27"}
    assert str(error) == "The amount 59.5000 is due on 2026-09-27."


def test_strict_mode_refuses_unknown_code_and_terms(catalog, monkeypatch):
    with pytest.raises(ValueError, match="Unknown refusal code"):
        InvalidOperation(code="sample_unknown")
    with pytest.raises(ValueError, match="term"):
        InvalidOperation(code="sample_field", values={"field": "Not a listed term"})
    # Production never hides a refusal behind a catalog mistake: it falls back to English.
    monkeypatch.setenv("REALITY_STRICT_REFUSALS", "0")
    fallback = InvalidOperation(
        code="sample_field", values={"field": "Not a listed term"}
    )
    assert str(fallback) == "Not a listed term cannot be negative."
    unknown = InvalidOperation(code="sample_unknown")
    assert unknown.code == "sample_unknown" and str(unknown) == "sample_unknown"
    assert refusals.payload(unknown) is None


def test_uncoded_refusal_is_unchanged(catalog):
    error = InvalidOperation("Net plus tax differs from the invoice gross.")
    assert str(error) == "Net plus tax differs from the invoice gross."
    assert error.code is None and error.values == {}
    assert refusals.payload(error) is None


def test_class_codes_of_existing_subclasses_are_kept():
    from reality.services.analytics.errors import AnalyticsError
    from reality.services.cost_review_draft import DraftChanged
    from reality.services.tenant_policy import PlaygroundOperationDenied

    assert AnalyticsError("Refused.", code="query_too_broad").code == "query_too_broad"
    assert DraftChanged({}).code == "draft_changed"
    assert PlaygroundOperationDenied("Denied.").code == "playground_operation_denied"
    # A class code is not a catalog code: no template is sent for it.
    assert refusals.payload(PlaygroundOperationDenied("Denied.")) is None


# The shipped catalog ------------------------------------------------------------------


def test_the_shipped_catalog_is_valid():
    shipped = refusals.catalog()
    assert shipped["version"] == 1
    for code, entry in shipped["refusals"].items():
        assert refusals.CODE.fullmatch(code), code
        assert set(refusals.placeholders(entry["message"])) == set(
            entry.get("values", {})
        )


# FR-003 web API ---------------------------------------------------------------------


@pytest.fixture
def client(session):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(database_session, None)


def _refuse_prepare(monkeypatch, error):
    import reality.services.delivery_actions as delivery

    def refuse(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(delivery, "prepare_delivery_action", refuse)


def _prepare(client, business, **arguments):
    return client.post(
        f"/api/tenants/{business.tenant.id}/delivery-actions/prepare",
        json={"request_id": "refusal-286", "tool": "reserve", "arguments": arguments},
    )


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (400, lambda: InvalidOperation(code="sample_line", values={"index": 3})),
        (404, lambda: NotFound(code="sample_plain")),
        (409, lambda: Conflict(code="sample_plain")),
    ],
)
def test_api_sends_code_template_values_per_status(
    catalog, client, business, monkeypatch, status, error
):
    raised = error()
    _refuse_prepare(monkeypatch, raised)
    response = _prepare(client, business)
    assert response.status_code == status
    assert response.json() == {"detail": str(raised), **refusals.payload(raised)}


def test_the_action_fields_refusal_is_coded(client, business, monkeypatch):
    _refuse_prepare(monkeypatch, TypeError("unexpected keyword argument"))
    response = _prepare(client, business)
    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Check the action fields."
    assert body["code"] == "action_fields_invalid"
    assert body["template"] == "Check the action fields." and body["values"] == {}


def test_uncoded_refusal_shape_is_unchanged(client, business, monkeypatch):
    _refuse_prepare(monkeypatch, InvalidOperation("A plain English refusal."))
    response = _prepare(client, business)
    assert response.status_code == 400
    assert response.json() == {"detail": "A plain English refusal."}


def test_playground_denial_carries_its_refusal_code(
    catalog, client, business, monkeypatch
):
    import asyncio
    import json as jsonlib

    from reality.services.tenant_policy import PlaygroundOperationDenied
    from reality.web.app import playground_operation_denied

    # Inside a route it goes through api_error, with the status it has today (400).
    _refuse_prepare(monkeypatch, PlaygroundOperationDenied(code="sample_plain"))
    response = _prepare(client, business)
    assert response.status_code == 400
    assert response.json()["code"] == "sample_plain"

    # Uncaught, the 403 handler sends the refusal code, or its class code when uncoded.
    def handled(error):
        result = asyncio.run(playground_operation_denied(None, error))
        return result.status_code, jsonlib.loads(result.body)

    assert handled(PlaygroundOperationDenied(code="sample_plain")) == (
        403,
        {
            "detail": "The sample is refused.",
            "code": "sample_plain",
            "template": "The sample is refused.",
            "values": {},
        },
    )
    assert handled(PlaygroundOperationDenied("Denied.")) == (
        403,
        {"detail": "Denied.", "code": "playground_operation_denied"},
    )


def test_chat_session_not_found_is_coded(client, business):
    response = client.get(
        f"/api/tenants/{business.tenant.id}/copilot", params={"session_id": "missing"}
    )
    assert response.status_code == 404
    assert response.json()["code"] == "chat_session_not_found"
    assert response.json()["detail"] == "ChatSession not found."


# FR-004 / FR-008 chat, MCP and receipts ---------------------------------------------


def test_chat_stream_error_carries_code(catalog):
    import asyncio
    import json as jsonlib
    from contextlib import contextmanager

    from reality.web.chat_stream import chat_events

    @contextmanager
    def factory():
        yield object()

    def send(*_args, **_kwargs):
        raise InvalidOperation(code="sample_line", values={"index": 2})

    async def run():
        stream = chat_events(
            factory, send, "tenant", "session", "Question", principal=None, options={}
        )
        return [jsonlib.loads(event) async for event in stream]

    events = asyncio.run(run())
    assert events[-1] == {
        "type": "error",
        "message": "Line 2 requires a stated amount; it is never calculated.",
        "code": "sample_line",
        "template": "Line {index} requires a stated amount; it is never calculated.",
        "values": {"index": {"value": "2", "kind": "number"}},
    }


def test_chat_tool_result_keeps_english_and_adds_values(catalog, monkeypatch):
    from reality.agent import mcp_chat

    def refuse(*_args, **_kwargs):
        raise InvalidOperation(code="sample_line", values={"index": 2})

    monkeypatch.setattr(mcp_chat, "dispatch_tool", refuse)
    result, failed = mcp_chat._dispatch(None, "tenant", "order_create", {}, "read")
    assert failed is True
    assert result == {
        "error": "Line 2 requires a stated amount; it is never calculated.",
        "code": "sample_line",
        "values": {"index": "2"},
    }


def test_mcp_error_uses_refusal_code(catalog):
    from reality.mcp.server import tool_error_payload

    assert tool_error_payload(
        "reserve", NotFound(code="sample_line", values={"index": 2})
    ) == {
        "code": "sample_line",
        "message": "Line 2 requires a stated amount; it is never calculated.",
        "tool": "reserve",
        "values": {"index": "2"},
    }
    # Uncoded refusals keep exactly today's payload with the class code.
    assert tool_error_payload("reserve", NotFound("Gone.")) == {
        "code": "not_found",
        "message": "Gone.",
        "tool": "reserve",
    }


def test_failed_receipt_carries_refusal_code(catalog, session, business, monkeypatch):
    import json as jsonlib

    from test_unified_invoice_entry import confirm, prepare

    from reality.tools.application import TOOLS, Tool

    proposal = prepare(session, business)
    original = TOOLS["sales_invoice_record"]

    def refuse(_session, _tenant_id, _arguments):
        raise InvalidOperation(code="sample_line", values={"index": 2})

    monkeypatch.setitem(
        TOOLS,
        "sales_invoice_record",
        Tool(original.name, original.description, original.mutating, refuse),
    )
    with pytest.raises(InvalidOperation, match="requires a stated amount"):
        confirm(session, business, proposal)
    session.refresh(proposal)
    assert jsonlib.loads(proposal.output)["error"] == {
        "code": "sample_line",
        "message": "Line 2 requires a stated amount; it is never calculated.",
        "type": "InvalidOperation",
        "values": {"index": "2"},
    }
