"""What a chapter added (spec 182, FR-005): a read after a marker, never stored.

Events come from the timeline's forward mode, Facts from their recording order,
records from the first appearance of a subject after the marker, raised and cleared
findings from comparing the snapshot taken before the chapter with the findings now,
and the graph excerpt from the links the events after the marker name. Nothing here
derives a business value; it lists what Reality already recorded.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, Fact
from reality.storyline.references import RAW_ID_PATTERN

EVENT_LIMIT = 250
FACT_LIMIT = 250
NODE_LIMIT = 40

# Keys in event payloads that name another record; the suffix gives the family.
LINK_FAMILIES = {
    "party_id": "party",
    "counterparty_id": "party",
    "company_party_id": "party",
    "to_party_id": "party",
    "from_party_id": "party",
    "item_id": "item",
    "location_id": "location",
    "from_location_id": "location",
    "to_location_id": "location",
    "commitment_id": "commitment",
    "document_id": "document",
    "invoice_id": "document",
    "document_line_id": "document_line",
    "order_line_id": "document_line",
    "reservation_id": "reservation",
    "movement_id": "movement",
    "source_record_id": "source_record",
    "payment_id": "payment",
    "ledger_entry_id": "ledger_entry",
    "control_entry_id": "ledger_entry",
    "posting_group_id": "posting_group",
    "shipment_id": "shipment",
    "party_hold_id": "party_hold",
    "fact_id": "fact",
}


def read_delta(
    session: Session,
    tenant_id: str,
    *,
    after_sequence: int,
    after_at: datetime | None,
    before_exceptions: list[str],
    primary: tuple[str, str] | None = None,
) -> dict[str, Any]:
    from reality.catalogs import (
        load_exception_class_labels,
        load_operational_exception_catalog,
    )
    from reality.services.core import timeline_activity
    from reality.services.exceptions import operational_exceptions

    page = timeline_activity(
        session, tenant_id, after_sequence=after_sequence, hours=0, limit=EVENT_LIMIT
    )
    events = [
        {
            "id": event["id"],
            "sequence": event["sequence"],
            "type": event["type"],
            "subject_type": event["subject_type"],
            "subject_id": event["subject_id"],
            "title": event.get("title") or event["type"],
            "occurred_at": event["occurred_at"],
            "recorded_at": event["recorded_at"],
            "action_id": event.get("action_id"),
            "payload": event.get("payload") or {},
        }
        for event in page["events"]
    ]
    latest = max((event["sequence"] for event in events), default=after_sequence)

    facts: list[dict[str, Any]] = []
    if after_at is not None:
        rows = session.scalars(
            select(Fact)
            .where(Fact.tenant_id == tenant_id, Fact.recorded_at > after_at)
            .order_by(Fact.recorded_at, Fact.id)
            .limit(FACT_LIMIT)
        )
        facts = [
            {
                "id": fact.id,
                "subject_type": fact.subject_type,
                "subject_id": fact.subject_id,
                "predicate": fact.predicate,
                "value": _value(fact.value),
                "observed_at": fact.observed_at,
                "recorded_at": fact.recorded_at,
                "source_record_id": fact.source_record_id,
            }
            for fact in rows
        ]

    subjects: list[tuple[str, str]] = []
    for event in events:
        pair = (event["subject_type"], event["subject_id"])
        if pair not in subjects:
            subjects.append(pair)
    records: list[dict[str, Any]] = []
    for subject_type, subject_id in subjects:
        earlier = session.scalar(
            select(BusinessEvent.id)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.subject_type == subject_type,
                BusinessEvent.subject_id == subject_id,
                BusinessEvent.sequence <= after_sequence,
            )
            .limit(1)
        )
        if earlier is None:
            records.append({"record_type": subject_type, "record_id": subject_id})
    for fact in facts:
        records.append({"record_type": "fact", "record_id": fact["id"]})

    current = {
        exception.id: exception
        for exception in operational_exceptions(session, tenant_id)
    }
    before = set(before_exceptions or [])
    labels = load_exception_class_labels()
    classes = {
        entry["id"]: entry for entry in load_operational_exception_catalog().classes
    }

    def describe(identity: str, exception=None) -> dict[str, Any]:
        class_id = identity.split("__")[1] if identity.count("__") >= 2 else ""
        record_id = identity.split("__", 2)[2] if identity.count("__") >= 2 else ""
        entry = classes.get(class_id, {})
        return {
            "id": identity,
            "class_id": class_id,
            "record_type": exception.record_type
            if exception
            else entry.get("record_type"),
            "record_id": exception.record_id if exception else record_id,
            "label": {"en": entry.get("label", class_id), **labels.get(class_id, {})},
            "title": exception.title if exception else entry.get("label", class_id),
            "impact": exception.impact if exception else None,
            "severity": exception.severity if exception else entry.get("severity"),
            "clears_through": entry.get("clears_through", ""),
        }

    raised = [
        describe(identity, current[identity])
        for identity in sorted(set(current) - before)
    ]
    cleared = [describe(identity) for identity in sorted(before - set(current))]

    return {
        "range": {
            "after_sequence": after_sequence,
            "after_at": after_at,
            "latest_sequence": latest,
            "available": True,
            "has_more": page.get("has_more", False),
        },
        "events": [
            {k: v for k, v in event.items() if k != "payload"} for event in events
        ],
        "facts": facts,
        "records": records,
        "exceptions": {"raised": raised, "cleared": cleared},
        "graph": _graph(events, records, primary),
    }


def _value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return raw


def _graph(
    events: list[dict[str, Any]],
    records: list[dict[str, Any]],
    primary: tuple[str, str] | None,
) -> dict[str, Any]:
    """Nodes and edges the events after the marker make visible; all edges are new."""
    new_ids = {record["record_id"] for record in records}
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    def node(record_type: str, record_id: str) -> str:
        key = f"{record_type}:{record_id}"
        if key not in nodes and len(nodes) < NODE_LIMIT:
            nodes[key] = {
                "record_type": record_type,
                "record_id": record_id,
                "new": record_id in new_ids,
                "primary": primary == (record_type, record_id),
            }
        return key

    if primary is not None:
        node(*primary)
    for event in events:
        source = node(event["subject_type"], event["subject_id"])
        for key, value in (event.get("payload") or {}).items():
            family = LINK_FAMILIES.get(key)
            if (
                family is None
                or not isinstance(value, str)
                or not RAW_ID_PATTERN.match(value)
            ):
                continue
            if value == event["subject_id"]:
                continue
            target = node(family, value)
            edge = {
                "from": source,
                "to": target,
                "relation": key.removesuffix("_id"),
                "new": True,
            }
            if edge not in edges:
                edges.append(edge)
    return {
        "record": {"record_type": primary[0], "record_id": primary[1]}
        if primary
        else None,
        "nodes": list(nodes.values()),
        "edges": [
            edge for edge in edges if edge["from"] in nodes and edge["to"] in nodes
        ],
    }
