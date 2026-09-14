from __future__ import annotations

import json

from sqlalchemy import select

from reality.db.core import Fact
from reality.mcp.catalog import dispatch_tool, model_tool_schemas
from reality.services.core import create_commitment, store_source_record
from reality.tools.application import approve_and_execute_proposal


def test_fact_observation_is_a_typed_confirmation_required_proposal(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        "2026-09-15T10:00:00Z",
    )
    source, _, _ = store_source_record(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "ORDER-42",
        {"id": "ORDER-42", "shipping_priority": "express"},
    )
    session.commit()
    arguments = {
        "source_record_id": source.id,
        "subject_type": "commitment",
        "subject_id": commitment.id,
        "predicate": "order.shipping_priority",
        "value": "express",
        "observed_at": "2026-09-02T14:06:00Z",
        "idempotency_key": "agent-order-42-priority",
    }

    schemas = {
        schema["function"]["name"]: schema["function"]["parameters"]
        for schema in model_tool_schemas(access=("propose",))
    }
    assert set(schemas["fact_observe_propose"]["required"]) == set(arguments)
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "fact_observe_propose",
        arguments,
        allowed_access=("propose",),
    )
    assert session.scalar(select(Fact)) is None
    assert proposal["arguments"]["subject_id"] == commitment.id

    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal["proposal_id"]
    )
    fact = session.scalar(select(Fact))
    assert fact is not None
    assert json.loads(executed.output)["fact_id"] == fact.id
