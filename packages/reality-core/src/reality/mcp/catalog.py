from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy.orm import Session

from reality.services.core import InvalidOperation, NotFound
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)

ToolAccess = Literal["read", "propose", "confirm"]
ToolHandler = Callable[[Session, str, dict[str, Any]], Any]


@dataclass(frozen=True)
class MCPToolDefinition:
    name: str
    label: str
    description: str
    access: ToolAccess
    group: str
    input_schema: dict[str, Any]
    handler: ToolHandler

    @property
    def mutating(self) -> bool:
        return self.access == "confirm"

    def model_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def public_metadata(self) -> dict[str, Any]:
        """Return the serializable catalog representation exposed by settings APIs."""
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "access": self.access,
            "group": self.group,
            "input_schema": self.input_schema,
            "mutating": self.mutating,
        }


def _object_schema(
    properties: dict[str, dict[str, Any]] | None = None,
    *,
    required: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties or {},
        "required": list(required),
        "additionalProperties": False,
    }


def _read(application_name: str) -> ToolHandler:
    def handler(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
        if application_name in {
            "business_discover",
            "inventory",
            "commitments",
            "fulfillment_queue",
            "fulfillment_blockers",
            "item_supply_demand",
        }:
            arguments = {"response_format": "page", **arguments}
        return run_read_tool(session, tenant_id, application_name, arguments)

    return handler


def _propose(application_name: str) -> ToolHandler:
    def handler(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
        normalized = {
            key: value for key, value in arguments.items() if value is not None
        }
        if application_name == "source_ingest":
            normalized.setdefault("source_system", "manual_upload")
            normalized.setdefault("source_type", "data_drop")
            normalized.setdefault("expected_target", "data_drop")
        proposal = create_change_proposal(
            session, tenant_id, application_name, normalized
        )
        return {
            "proposal_id": proposal.id,
            "status": proposal.status,
            "requires_human_confirmation": True,
            "arguments": normalized,
            "preview": json.loads(proposal.output),
        }

    return handler


def _approve_proposal(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    if arguments.get("approved") is not True:
        raise ValueError("Set approved=true only after explicit human approval.")
    from reality.services.delivery_actions import get_delivery_proposal, review_existing

    try:
        candidate = get_delivery_proposal(session, tenant_id, arguments["proposal_id"])
    except (InvalidOperation, NotFound):
        candidate = None
    if (
        candidate
        and "_delivery_review" not in json.loads(candidate.input)
        and candidate.status == "proposed"
    ):
        reviewed = review_existing(session, tenant_id, candidate.id)
        return {
            "proposal_id": reviewed.id,
            "status": reviewed.status,
            "preview": json.loads(reviewed.output),
            "requires_human_confirmation": True,
        }
    proposal = approve_and_execute_proposal(
        session,
        tenant_id,
        arguments["proposal_id"],
        review_token=arguments.get("review_token"),
        confirmed=True,
        confirming_principal=_analytics_caller(),
    )
    receipt = json.loads(proposal.output)
    return {
        "proposal_id": proposal.id,
        "status": proposal.status,
        "tool": proposal.type.removeprefix("tool:"),
        "output": receipt,
        "receipt": receipt,
    }


STRING = {"type": "string"}
OPTIONAL_STRING = {"type": ["string", "null"]}
SOURCE_PAYLOAD = {"type": ["object", "null"], "additionalProperties": True}


def _records_schema(record_schema: dict[str, Any]) -> dict[str, Any]:
    return _object_schema(
        {
            "records": {
                "type": "array",
                "minItems": 1,
                "items": record_schema,
            }
        },
        required=("records",),
    )


PARTY_CREATE_RECORD = _object_schema(
    {
        "name": STRING,
        "roles": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "enum": ["company", "customer", "supplier"]},
        },
        "type": {
            "type": ["string", "null"],
            "enum": ["company", "customer", "supplier", None],
        },
        "accounting_code": {"type": "string", "default": ""},
        "payment_term_code": {"type": "string", "default": ""},
        "default_currency": {"type": "string", "default": "EUR"},
        "credit_limit": {"type": "string", "default": "0"},
        "tax_identifier": {"type": "string", "default": ""},
        "source_system": OPTIONAL_STRING,
        "external_id": OPTIONAL_STRING,
        "source_payload": SOURCE_PAYLOAD,
    },
    required=("name", "roles"),
)

ITEM_CREATE_RECORD = _object_schema(
    {
        "sku": STRING,
        "name": STRING,
        "unit": {"type": "string", "default": "pcs"},
        "item_type": {
            "type": "string",
            "enum": ["stocked", "service", "charge"],
            "default": "stocked",
        },
        "tracking_type": {
            "type": "string",
            "enum": ["none", "lot", "serial"],
            "default": "none",
        },
        "default_location_id": OPTIONAL_STRING,
        "purchase_unit": OPTIONAL_STRING,
        "conversion_factor": {"type": "string", "default": "1"},
        "lead_time_days": {"type": "integer", "minimum": 0, "default": 0},
        "source_system": OPTIONAL_STRING,
        "external_id": OPTIONAL_STRING,
        "source_payload": SOURCE_PAYLOAD,
    },
    required=("sku", "name"),
)

LOCATION_CREATE_RECORD = _object_schema(
    {
        "ref": {
            "type": ["string", "null"],
            "description": "Optional local reference used by later records in the same batch.",
        },
        "name": STRING,
        "type": {"type": "string", "default": "warehouse"},
        "parent_ref": {
            "type": ["string", "null"],
            "description": "Local ref of an earlier Location in the same batch. Use this for newly created hierarchies.",
        },
        "parent_location_id": {
            "type": ["string", "null"],
            "description": "Opaque ID of an existing Location. Never pass a name here.",
        },
        "allows_stock": {"type": "boolean", "default": True},
        "source_system": OPTIONAL_STRING,
        "external_id": OPTIONAL_STRING,
        "source_payload": SOURCE_PAYLOAD,
    },
    required=("name",),
)


def _update_properties(record_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        name: {key: value for key, value in property_schema.items() if key != "default"}
        for name, property_schema in record_schema["properties"].items()
    }


PARTY_UPDATE_RECORD = _object_schema(
    {
        "id": {"type": "string", "description": "Opaque Party ID."},
        **_update_properties(PARTY_CREATE_RECORD),
        "type": {
            "type": "string",
            "enum": ["company", "customer", "supplier"],
        },
    },
    required=("id", "name", "type", "roles"),
)

ITEM_UPDATE_RECORD = _object_schema(
    {
        "id": {"type": "string", "description": "Opaque Item ID."},
        **_update_properties(ITEM_CREATE_RECORD),
    },
    required=("id", "sku", "name", "unit"),
)

LOCATION_UPDATE_RECORD = _object_schema(
    {
        "id": {"type": "string", "description": "Opaque Location ID."},
        **_update_properties(LOCATION_CREATE_RECORD),
    },
    required=("id", "name", "type"),
)

PAGE_PROPERTIES = {
    "response_format": {
        "type": "string",
        "enum": ["page", "legacy"],
        "default": "page",
        "description": "Page returns records, continuation and metadata; legacy preserves the old list shape.",
    },
    "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 25,
        "description": "Maximum records per page; legacy operational lists retain their full-list behavior.",
    },
    "cursor": {
        "type": ["string", "null"],
        "default": None,
        "description": "Continuation for the same tenant, read and filters. Live pages are not a snapshot.",
    },
}

MCP_TOOL_CATALOG = (
    MCPToolDefinition(
        "capability_describe",
        "Describe an agent capability",
        "Read when one public mutation should or should not be used, its expected refusals, and how to verify its outcome.",
        "read",
        "Discovery",
        _object_schema({"tool_name": STRING}, required=("tool_name",)),
        _read("capability_describe"),
    ),
    MCPToolDefinition(
        "business_records_discover",
        "Discover business records",
        "Read tenant-scoped business records as complete cursor pages with metadata; explicit legacy mode is a bounded lookup.",
        "read",
        "Discovery",
        _object_schema(
            {
                **PAGE_PROPERTIES,
                "family": {
                    "type": "string",
                    "enum": [
                        "party",
                        "item",
                        "location",
                        "document",
                        "commitment",
                        "movement",
                        "reservation",
                        "handling_unit",
                        "lot",
                        "serial_unit",
                        "payment_term",
                        "price_list",
                        "price_list_entry",
                        "party_group",
                        "ledger_entry",
                        "source_system",
                        "source_capability",
                        "source_record",
                    ],
                },
                "query": {"type": "string", "default": ""},
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 25,
                },
                "record_id": OPTIONAL_STRING,
            },
            required=("family",),
        ),
        _read("business_discover"),
    ),
    MCPToolDefinition(
        "inventory_read",
        "Read inventory",
        "Read inventory as cursor pages: labelled item totals or item/location rows with units. Page mode does not write projection caches.",
        "read",
        "Operations",
        _object_schema(
            {
                **PAGE_PROPERTIES,
                "view": {
                    "type": "string",
                    "enum": ["aggregate", "location"],
                    "default": "aggregate",
                },
                "item_id": OPTIONAL_STRING,
                "location_id": OPTIONAL_STRING,
            }
        ),
        _read("inventory"),
    ),
    MCPToolDefinition(
        "commitments_list",
        "List commitments",
        "Customer and supplier obligations with quantity, due date, and status.",
        "read",
        "Operations",
        _object_schema(PAGE_PROPERTIES),
        _read("commitments"),
    ),
    MCPToolDefinition(
        "shipments_list",
        "List physical shipments",
        "List real incoming or outgoing consignments and packages; these are distinct from delivery commitments.",
        "read",
        "Operations",
        _object_schema(
            {
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 50,
                },
                "query": OPTIONAL_STRING,
                "direction": {
                    "type": "string",
                    "enum": ["", "inbound", "outbound"],
                    "default": "",
                },
                "purpose": {
                    "type": "string",
                    "enum": [
                        "",
                        "customer_delivery",
                        "supplier_delivery",
                        "customer_return",
                        "supplier_return",
                    ],
                    "default": "",
                },
                "counterparty_id": OPTIONAL_STRING,
                "carrier": OPTIONAL_STRING,
                "tracking": OPTIONAL_STRING,
                "created_from": OPTIONAL_STRING,
                "created_to": OPTIONAL_STRING,
                "observation": {
                    "type": "string",
                    "enum": [
                        "",
                        "announced",
                        "dispatched",
                        "received",
                        "externally_delivered",
                        "has_exception",
                    ],
                    "default": "",
                },
            }
        ),
        _read("shipments_list"),
    ),
    MCPToolDefinition(
        "shipment_explain",
        "Explain a physical shipment",
        "Explain one consignment through packages, tracking observations, effective Movements, and source links without treating dispatch as delivery.",
        "read",
        "Operations",
        _object_schema({"shipment_id": STRING}, required=("shipment_id",)),
        _read("shipment_explain"),
    ),
    MCPToolDefinition(
        "shipment_notice_record_propose",
        "Propose shipment notice",
        "Prepare a shipment/package notice without moving stock; execution requires explicit confirmation.",
        "propose",
        "Operations",
        _object_schema(
            {
                "direction": {"type": "string", "enum": ["inbound", "outbound"]},
                "purpose": {
                    "type": "string",
                    "enum": [
                        "customer_delivery",
                        "supplier_delivery",
                        "customer_return",
                        "supplier_return",
                    ],
                },
                "counterparty_id": STRING,
                "carrier": OPTIONAL_STRING,
                "tracking_number": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "occurred_at": OPTIONAL_STRING,
                "reporter_type": {
                    "type": "string",
                    "enum": ["company", "counterparty", "carrier", "integration"],
                    "default": "counterparty",
                },
            },
            required=("direction", "purpose", "counterparty_id"),
        ),
        _propose("shipment_notice_record"),
    ),
    MCPToolDefinition(
        "shipment_dispatch_propose",
        "Propose package dispatch",
        "Prepare one outgoing package and its exact physical Movements; execution requires explicit confirmation.",
        "propose",
        "Operations",
        _object_schema(
            {
                "purpose": {
                    "type": "string",
                    "enum": ["customer_delivery", "supplier_return"],
                },
                "counterparty_id": STRING,
                "movements": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "object"},
                },
                "carrier": OPTIONAL_STRING,
                "tracking_number": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "occurred_at": OPTIONAL_STRING,
            },
            required=("purpose", "counterparty_id", "movements"),
        ),
        _propose("shipment_dispatch"),
    ),
    MCPToolDefinition(
        "shipment_receive_propose",
        "Propose package receipt",
        "Prepare one incoming package and its exact physical Movements; execution requires explicit confirmation.",
        "propose",
        "Operations",
        _object_schema(
            {
                "purpose": {
                    "type": "string",
                    "enum": ["supplier_delivery", "customer_return"],
                },
                "counterparty_id": STRING,
                "movements": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "object"},
                },
                "carrier": OPTIONAL_STRING,
                "tracking_number": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "occurred_at": OPTIONAL_STRING,
            },
            required=("purpose", "counterparty_id", "movements"),
        ),
        _propose("shipment_receive"),
    ),
    MCPToolDefinition(
        "shipment_event_record_propose",
        "Propose shipment event",
        "Prepare one attributed logistics observation; execution requires explicit confirmation.",
        "propose",
        "Operations",
        _object_schema(
            {
                "shipment_id": STRING,
                "shipment_package_id": OPTIONAL_STRING,
                "event_type": {
                    "type": "string",
                    "enum": [
                        "announced",
                        "handed_over",
                        "in_transit",
                        "delivered",
                        "delivery_exception",
                        "received",
                    ],
                },
                "reporter_type": {
                    "type": "string",
                    "enum": ["company", "counterparty", "carrier", "integration"],
                },
                "occurred_at": OPTIONAL_STRING,
                "location_text": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "external_event_id": OPTIONAL_STRING,
            },
            required=("shipment_id", "event_type", "reporter_type"),
        ),
        _propose("shipment_event_record"),
    ),
    MCPToolDefinition(
        "shipment_event_supersede_propose",
        "Propose shipment event correction",
        "Prepare an append-only correction or retraction; execution requires explicit confirmation.",
        "propose",
        "Operations",
        _object_schema(
            {
                "event_id": STRING,
                "reason": STRING,
                "replacement_event_id": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
            },
            required=("event_id", "reason"),
        ),
        _propose("shipment_event_supersede"),
    ),
    MCPToolDefinition(
        "fulfillment_queue",
        "Read fulfillment queue",
        "Orders with ship readiness, lines, shortages, holds, and source identity.",
        "read",
        "Operations",
        _object_schema(PAGE_PROPERTIES),
        _read("fulfillment_queue"),
    ),
    MCPToolDefinition(
        "fulfillment_blockers",
        "Read fulfillment blockers",
        "Current order and item blockers with their affected operational records.",
        "read",
        "Operations",
        _object_schema(PAGE_PROPERTIES),
        _read("fulfillment_blockers"),
    ),
    MCPToolDefinition(
        "item_supply_demand",
        "Read item supply and demand",
        "Stock, incoming supply, customer demand, shortages, and blocked orders by item.",
        "read",
        "Operations",
        _object_schema(PAGE_PROPERTIES),
        _read("item_supply_demand"),
    ),
    MCPToolDefinition(
        "order_explain",
        "Explain an order",
        "Explain retained open, fulfilled or cancelled orders by opaque ID with Source, Evidence and Reality links; not a historical snapshot.",
        "read",
        "Operations",
        _object_schema({"order_reference": STRING}, required=("order_reference",)),
        _read("order_explain"),
    ),
    MCPToolDefinition(
        "exceptions_list",
        "List operational exceptions",
        "Current tenant-scoped derived conditions that require attention; these are not tickets.",
        "read",
        "Exceptions & proposals",
        _object_schema(),
        _read("exceptions"),
    ),
    MCPToolDefinition(
        "interpretation_coverage",
        "Read interpretation coverage",
        "List source interpretation outcomes and produced Reality identities without raw payloads.",
        "read",
        "Operations",
        _object_schema({"source_record_id": OPTIONAL_STRING}),
        _read("interpretation_coverage"),
    ),
    MCPToolDefinition(
        "expired_lots",
        "Read expired lots",
        "List the batches whose stated best-before date has passed, oldest first. A lot with "
        "no stated date is absent in both directions. There is deliberately no way to ask what "
        "is about to expire: no horizon is stated anywhere and Reality does not invent one.",
        "read",
        "Operations",
        _object_schema(),
        _read("expired_lots"),
    ),
    MCPToolDefinition(
        "return_announcements",
        "Read announced returns",
        "List the returns customers have announced, in the order they said so, with what each "
        "is still waiting for. An announced return is not supply: nothing here makes the goods "
        "available.",
        "read",
        "Operations",
        _object_schema(
            {
                "commitment_id": OPTIONAL_STRING,
                "status": {
                    "type": ["string", "null"],
                    "enum": ["open", "fulfilled", "withdrawn", None],
                },
            }
        ),
        _read("return_announcements"),
    ),
    MCPToolDefinition(
        "payment_run_preview",
        "Preview a payment run",
        "Show which supplier invoices are worth paying now, what each supplier is owed and "
        "what was withheld, without paying anything. Names an early-payment rate and its "
        "deadline; never states what a discount is worth.",
        "read",
        "Exceptions & proposals",
        _object_schema({"pay_by": STRING}, required=("pay_by",)),
        _read("payment_run_preview"),
    ),
    MCPToolDefinition(
        "stale_closure_preview",
        "Preview a stale promise closure",
        "Show how many promises an import left behind would close, and a sample of them, without changing anything.",
        "read",
        "Exceptions & proposals",
        _object_schema(
            {
                "direction": {"type": "string", "enum": ["sales", "purchase"]},
                "due_before": STRING,
            },
            required=("direction", "due_before"),
        ),
        _read("stale_closure_preview"),
    ),
    MCPToolDefinition(
        "exception_explain",
        "Explain an operational exception",
        "Return one current exception and the Reality context from which it is derived.",
        "read",
        "Exceptions & proposals",
        _object_schema({"exception_id": STRING}, required=("exception_id",)),
        _read("exception_explain"),
    ),
    MCPToolDefinition(
        "proposals_awaiting_approval",
        "List proposals awaiting approval",
        "Auditable changes that have been prepared but not executed.",
        "read",
        "Exceptions & proposals",
        _object_schema(),
        _read("proposals_awaiting_approval"),
    ),
    MCPToolDefinition(
        "proposal_execution_status",
        "Reconcile proposal execution",
        "Read one proposal lifecycle and verify its stored receipt against authoritative Reality records.",
        "read",
        "Exceptions & proposals",
        _object_schema({"proposal_id": STRING}, required=("proposal_id",)),
        _read("proposal_execution_status"),
    ),
    MCPToolDefinition(
        "proposal_approve_and_execute",
        "Approve and execute a proposal",
        "Approve one exact proposal and execute it through the shared application boundary.",
        "confirm",
        "Exceptions & proposals",
        _object_schema(
            {
                "proposal_id": STRING,
                "approved": {"type": "boolean", "default": False},
                "review_token": OPTIONAL_STRING,
            },
            required=("proposal_id",),
        ),
        _approve_proposal,
    ),
    MCPToolDefinition(
        "finance_balances",
        "Read finance balances",
        "Read balances per recorded currency with metadata. Never converts or adds different currencies; returns balances, not legacy EUR fields.",
        "read",
        "Finance",
        _object_schema(),
        _read("finance_balances"),
    ),
    MCPToolDefinition(
        "reservation_propose",
        "Propose reservation",
        "Prepare a stock reservation without allocating before confirmation.",
        "propose",
        "Mutations",
        _object_schema(
            {
                "commitment_id": STRING,
                "quantity": OPTIONAL_STRING,
                "handling_unit_id": OPTIONAL_STRING,
                "lot_id": OPTIONAL_STRING,
                "serial_unit_id": OPTIONAL_STRING,
            },
            required=("commitment_id",),
        ),
        _propose("reserve"),
    ),
    MCPToolDefinition(
        "movement_correction_propose",
        "Propose Movement correction",
        "Preview an exact compensating Movement and optional replacement without executing before human approval.",
        "propose",
        "Mutations",
        _object_schema(
            {
                "movement_id": STRING,
                "reason": STRING,
                "replacement": {
                    "type": ["object", "null"],
                    "additionalProperties": True,
                },
            },
            required=("movement_id", "reason"),
        ),
        _propose("movement_correct"),
    ),
    MCPToolDefinition(
        "ledger_reversal_propose",
        "Propose Ledger reversal",
        "Preview a complete inverse posting group without executing before human approval.",
        "propose",
        "Mutations",
        _object_schema(
            {"posting_group_id": STRING, "reason": STRING},
            required=("posting_group_id", "reason"),
        ),
        _propose("ledger_reverse"),
    ),
    MCPToolDefinition(
        "party_create_propose",
        "Propose Party creation",
        "Prepare manual creation of one or more Parties. Name and roles are required; source provenance is optional. Human confirmation is required.",
        "propose",
        "Mutations",
        _records_schema(PARTY_CREATE_RECORD),
        _propose("party_create"),
    ),
    MCPToolDefinition(
        "item_create_propose",
        "Propose Item creation",
        "Prepare manual creation of one or more Items. SKU and name are required, unit defaults to pcs, and source provenance is optional. Human confirmation is required.",
        "propose",
        "Mutations",
        _records_schema(ITEM_CREATE_RECORD),
        _propose("item_create"),
    ),
    MCPToolDefinition(
        "location_create_propose",
        "Propose Location creation",
        "Prepare manual creation of one or more Locations. Name is required and type defaults to warehouse. For a hierarchy created in this batch, give parents a ref and children a parent_ref; parent_location_id accepts only an existing opaque ID, never a name. Source provenance is optional. Human confirmation is required.",
        "propose",
        "Mutations",
        _records_schema(LOCATION_CREATE_RECORD),
        _propose("location_create"),
    ),
    MCPToolDefinition(
        "party_update_propose",
        "Propose Party update",
        "Prepare updates to existing Parties identified only by opaque ID. Exact changes are previewed and human confirmation is required.",
        "propose",
        "Mutations",
        _records_schema(PARTY_UPDATE_RECORD),
        _propose("party_update"),
    ),
    MCPToolDefinition(
        "item_update_propose",
        "Propose Item update",
        "Prepare updates to existing Items identified only by opaque ID. Exact changes are previewed and human confirmation is required.",
        "propose",
        "Mutations",
        _records_schema(ITEM_UPDATE_RECORD),
        _propose("item_update"),
    ),
    MCPToolDefinition(
        "location_update_propose",
        "Propose Location update",
        "Prepare updates to existing Locations identified only by opaque ID. Parent locations also use opaque IDs. Exact changes are previewed and human confirmation is required.",
        "propose",
        "Mutations",
        _records_schema(LOCATION_UPDATE_RECORD),
        _propose("location_update"),
    ),
    MCPToolDefinition(
        "source_ingest_propose",
        "Propose source ingestion",
        "Attach an uploaded artifact to immutable Source evidence after confirmation.",
        "propose",
        "Mutations",
        _object_schema(
            {
                "artifact_id": STRING,
                "source_system": {"type": "string", "default": "manual_upload"},
                "source_type": {"type": "string", "default": "data_drop"},
                "external_id": OPTIONAL_STRING,
                "expected_target": {"type": "string", "default": "data_drop"},
            },
            required=("artifact_id",),
        ),
        _propose("source_ingest"),
    ),
    MCPToolDefinition(
        "fact_observe_propose",
        "Propose Fact observation",
        "Prepare one source-supported observation about an existing opaque Reality subject. Human confirmation is required and model output alone is not a Fact.",
        "propose",
        "Mutations",
        _object_schema(
            {
                "source_record_id": STRING,
                "subject_type": STRING,
                "subject_id": STRING,
                "predicate": STRING,
                "value": STRING,
                "observed_at": STRING,
                "idempotency_key": STRING,
            },
            required=(
                "source_record_id",
                "subject_type",
                "subject_id",
                "predicate",
                "value",
                "observed_at",
                "idempotency_key",
            ),
        ),
        _propose("fact_observe"),
    ),
    MCPToolDefinition(
        "reality_gaps",
        "List missing information",
        "List the tenant's durable missing-information queue.",
        "read",
        "Missing information",
        _object_schema(
            {
                "status": OPTIONAL_STRING,
                "destination": OPTIONAL_STRING,
                "origin": OPTIONAL_STRING,
            }
        ),
        _read("reality_gaps"),
    ),
    MCPToolDefinition(
        "reality_gap_get",
        "Inspect missing information",
        "Read one gap, its investigation, decision, and implementation history.",
        "read",
        "Missing information",
        _object_schema({"gap_id": STRING}, required=("gap_id",)),
        _read("reality_gap_get"),
    ),
    MCPToolDefinition(
        "reality_gap_simulate",
        "Simulate Fact rule",
        "Dry-run a reviewed declarative rule without changing Reality.",
        "read",
        "Missing information",
        _object_schema(
            {
                "rule_id": STRING,
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 100,
                },
            },
            required=("rule_id",),
        ),
        _read("reality_gap_simulate"),
    ),
    MCPToolDefinition(
        "reality_gap_create_propose",
        "Propose missing information",
        "Capture an unanswered business question after confirmation.",
        "propose",
        "Missing information",
        _object_schema(
            {
                "question": {
                    "type": "string",
                    "maxLength": 100,
                    "description": "Concise 3–7 word queue label; put explanation in intended_use.",
                },
                "intended_use": STRING,
                "origin": {"type": "string", "enum": ["chat", "mcp", "web"]},
                "idempotency_key": STRING,
                "origin_reference": OPTIONAL_STRING,
            },
            required=("question", "intended_use", "origin", "idempotency_key"),
        ),
        _propose("reality_gap_create"),
    ),
    MCPToolDefinition(
        "reality_gap_entry_add_propose",
        "Propose investigation entry",
        "Append a guided answer or bounded evidence after confirmation.",
        "propose",
        "Missing information",
        _object_schema(
            {
                "gap_id": STRING,
                "entry_type": {
                    "type": "string",
                    "enum": ["answer", "context", "evidence", "note"],
                },
                "payload": {"type": "object", "additionalProperties": True},
                "expected_revision": {"type": "integer", "minimum": 1},
            },
            required=("gap_id", "entry_type", "payload", "expected_revision"),
        ),
        _propose("reality_gap_entry_add"),
    ),
    MCPToolDefinition(
        "reality_gap_recommend_propose",
        "Propose modeling recommendation",
        "Prepare an evidence-grounded destination recommendation.",
        "propose",
        "Missing information",
        _object_schema(
            {"gap_id": STRING, "expected_revision": {"type": "integer", "minimum": 1}},
            required=("gap_id", "expected_revision"),
        ),
        _propose("reality_gap_recommend"),
    ),
    MCPToolDefinition(
        "reality_gap_decide_propose",
        "Propose classification decision",
        "Accept, override, or reject a modeling destination.",
        "propose",
        "Missing information",
        _object_schema(
            {
                "gap_id": STRING,
                "destination": {
                    "type": "string",
                    "enum": [
                        "source_only",
                        "fact",
                        "typed_evidence",
                        "typed_reality",
                        "derived_view",
                        "rejected",
                    ],
                },
                "rationale": STRING,
                "expected_revision": {"type": "integer", "minimum": 1},
            },
            required=("gap_id", "destination", "rationale", "expected_revision"),
        ),
        _propose("reality_gap_decide"),
    ),
    MCPToolDefinition(
        "reality_gap_implementation_prepare_propose",
        "Propose gap implementation",
        "Prepare a safe Fact rule or governed developer package.",
        "propose",
        "Missing information",
        _object_schema(
            {
                "gap_id": STRING,
                "draft": {"type": ["object", "null"], "additionalProperties": True},
                "expected_revision": {"type": "integer", "minimum": 1},
            },
            required=("gap_id", "expected_revision"),
        ),
        _propose("reality_gap_implementation_prepare"),
    ),
    MCPToolDefinition(
        "reality_gap_rule_activate_propose",
        "Propose rule activation",
        "Activate one reviewed declarative Fact rule.",
        "propose",
        "Missing information",
        _object_schema({"rule_id": STRING}, required=("rule_id",)),
        _propose("reality_gap_rule_activate"),
    ),
    MCPToolDefinition(
        "reality_gap_rule_disable_propose",
        "Propose rule disablement",
        "Stop one Fact rule for future sources without deleting Facts.",
        "propose",
        "Missing information",
        _object_schema({"rule_id": STRING}, required=("rule_id",)),
        _propose("reality_gap_rule_disable"),
    ),
    MCPToolDefinition(
        "reality_gap_rule_replay_propose",
        "Propose historical replay",
        "Run one reviewed Fact rule over a bounded source scope.",
        "propose",
        "Missing information",
        _object_schema(
            {
                "rule_id": STRING,
                "source_ids": {"type": ["array", "null"], "items": STRING},
                "cursor": OPTIONAL_STRING,
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 500,
                    "default": 500,
                },
            },
            required=("rule_id",),
        ),
        _propose("reality_gap_rule_replay"),
    ),
)

DECIMAL_STRING = {"type": "string", "pattern": "^-?[0-9]+(?:\\.[0-9]+)?$"}
BOOLEAN = {"type": "boolean"}
INTEGER = {"type": "integer"}
STRING_ARRAY = {"type": "array", "items": STRING, "minItems": 1, "uniqueItems": True}

ORDER_LINE = _object_schema(
    {
        "item_id": STRING,
        "quantity": DECIMAL_STRING,
        "unit": STRING,
        "unit_price": DECIMAL_STRING,
        "gross_amount": DECIMAL_STRING,
        "description": {"type": "string", "default": ""},
        "promised_at": OPTIONAL_STRING,
        "line_type": {"type": "string", "default": "item"},
        "price_list_entry_id": OPTIONAL_STRING,
    },
    required=("item_id", "quantity", "unit", "unit_price", "gross_amount"),
)

ADDITIONAL_PROPOSAL_TOOLS: tuple[tuple[str, str, str, dict[str, Any]], ...] = (
    (
        "member_invite_propose",
        "Invite company member",
        "member_invite",
        _object_schema(
            {"email": STRING, "locale": {"type": "string", "default": "en"}},
            required=("email",),
        ),
    ),
    (
        "invitation_resend_propose",
        "Resend company invitation",
        "invitation_resend",
        _object_schema({"invitation_id": STRING}, required=("invitation_id",)),
    ),
    (
        "invitation_revoke_propose",
        "Revoke company invitation",
        "invitation_revoke",
        _object_schema({"invitation_id": STRING}, required=("invitation_id",)),
    ),
    (
        "member_remove_propose",
        "Remove company member",
        "member_remove",
        _object_schema({"membership_id": STRING}, required=("membership_id",)),
    ),
    (
        "document_correct_propose",
        "Correct manual document",
        "document_correct",
        _object_schema(
            {
                "document_id": STRING,
                "document_type": STRING,
                "number": STRING,
                "party_id": STRING,
                "amount": DECIMAL_STRING,
                "currency": {"type": "string", "default": "EUR"},
                "document_date": {"type": "string", "default": ""},
                "ordered_at": OPTIONAL_STRING,
                "requested_delivery_at": OPTIONAL_STRING,
                "customer_reference": {"type": "string", "default": ""},
                "sales_channel": {"type": "string", "default": ""},
                "payment_term_code": {"type": "string", "default": ""},
                "ship_to_party_id": OPTIONAL_STRING,
            },
            required=("document_id", "document_type", "number", "party_id", "amount"),
        ),
    ),
    (
        "document_source_correct_propose",
        "Append corrected document source",
        "document_source_correct",
        _object_schema(
            {
                "document_id": STRING,
                "payload": {"type": "object", "additionalProperties": True},
                "source_version_at": OPTIONAL_STRING,
            },
            required=("document_id", "payload"),
        ),
    ),
    (
        "document_lines_correct_propose",
        "Correct manual document lines",
        "document_lines_correct",
        _object_schema(
            {
                "document_id": STRING,
                "expected_revision": STRING,
                "lines": {
                    "type": "array",
                    "items": {"type": "object", "additionalProperties": True},
                },
                "actor_context": {
                    "type": ["object", "null"],
                    "additionalProperties": {"type": "string"},
                },
            },
            required=("document_id", "expected_revision", "lines"),
        ),
    ),
    (
        "source_record_ingest_propose",
        "Ingest arbitrary source record",
        "source_record_ingest",
        _object_schema(
            {
                "source_system": STRING,
                "source_type": STRING,
                "external_id": STRING,
                "payload": {"type": "object", "additionalProperties": True},
                "source_version_at": OPTIONAL_STRING,
                "context": {"type": ["object", "null"], "additionalProperties": True},
                "source_artifact_id": OPTIONAL_STRING,
            },
            required=("source_system", "source_type", "external_id", "payload"),
        ),
    ),
    (
        "order_create_propose",
        "Create order",
        "order_create",
        _object_schema(
            {
                "direction": {"type": "string", "enum": ["sales", "purchase"]},
                "number": STRING,
                "company_party_id": STRING,
                "counterparty_id": STRING,
                "location_id": STRING,
                "lines": {"type": "array", "minItems": 1, "items": ORDER_LINE},
                "gross_amount": STRING,
                "currency": {"type": "string", "default": "EUR"},
                "document_date": {"type": "string", "default": ""},
                "ordered_at": OPTIONAL_STRING,
                "requested_delivery_at": OPTIONAL_STRING,
                "customer_reference": {"type": "string", "default": ""},
                "sales_channel": {"type": "string", "default": ""},
                "payment_term_code": {"type": "string", "default": ""},
                "ship_to_party_id": OPTIONAL_STRING,
            },
            required=(
                "direction",
                "number",
                "company_party_id",
                "counterparty_id",
                "location_id",
                "lines",
                "gross_amount",
            ),
        ),
    ),
    (
        "handling_unit_create_propose",
        "Create handling unit",
        "handling_unit_create",
        _object_schema({"nve": OPTIONAL_STRING, "source_record_id": OPTIONAL_STRING}),
    ),
    (
        "lot_create_propose",
        "Create lot",
        "lot_create",
        _object_schema(
            {
                "item_id": STRING,
                "lot_number": STRING,
                # Stated, never computed. A shelf life multiplied out from a
                # production date would be a date nobody printed.
                "expires_at": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
            },
            required=("item_id", "lot_number"),
        ),
    ),
    (
        "lot_expiry_state_propose",
        "State lot expiry",
        "lot_expiry_state",
        _object_schema(
            {"lot_id": STRING, "expires_at": STRING},
            required=("lot_id", "expires_at"),
        ),
    ),
    (
        "lot_expiry_correct_propose",
        "Correct lot expiry",
        "lot_expiry_correct",
        _object_schema(
            {
                "lot_id": STRING,
                # Absent says the lot has no best-before, which is the honest
                # fix for a date read off the wrong label.
                "expires_at": OPTIONAL_STRING,
                # Absent says none is stated now. The correction is refused
                # unless this still matches, so it cannot be made blind.
                "expected_expires_at": OPTIONAL_STRING,
                "reason": STRING,
            },
            required=("lot_id", "reason"),
        ),
    ),
    (
        "serial_unit_create_propose",
        "Create serial unit",
        "serial_unit_create",
        _object_schema(
            {
                "item_id": STRING,
                "serial_number": STRING,
                "lot_id": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
            },
            required=("item_id", "serial_number"),
        ),
    ),
    (
        "movement_create_propose",
        "Record Movement",
        "movement_create",
        _object_schema(
            {
                "movement_type": STRING,
                "item_id": STRING,
                "quantity": DECIMAL_STRING,
                "from_location_id": OPTIONAL_STRING,
                "to_location_id": OPTIONAL_STRING,
                "commitment_id": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "handling_unit_id": OPTIONAL_STRING,
                "lot_id": OPTIONAL_STRING,
                "serial_unit_id": OPTIONAL_STRING,
                "occurred_at": OPTIONAL_STRING,
                "reason": OPTIONAL_STRING,
                "resolves_movement_id": OPTIONAL_STRING,
                "return_announcement_id": OPTIONAL_STRING,
            },
            required=("movement_type", "item_id", "quantity"),
        ),
    ),
    (
        "reservation_release_propose",
        "Release reservation",
        "reservation_release",
        _object_schema({"reservation_id": STRING}, required=("reservation_id",)),
    ),
    (
        "commitment_hold_propose",
        "Hold commitment",
        "commitment_hold",
        _object_schema(
            {
                "commitment_id": STRING,
                "reason_code": STRING,
                "note": {"type": "string", "default": ""},
            },
            required=("commitment_id", "reason_code"),
        ),
    ),
    (
        "commitment_hold_release_propose",
        "Release commitment hold",
        "commitment_hold_release",
        _object_schema({"commitment_id": STRING}, required=("commitment_id",)),
    ),
    (
        "document_hold_propose",
        "Hold document commitments",
        "document_hold",
        _object_schema(
            {
                "document_id": STRING,
                "reason_code": STRING,
                "note": {"type": "string", "default": ""},
            },
            required=("document_id", "reason_code"),
        ),
    ),
    (
        "document_hold_release_propose",
        "Release document holds",
        "document_hold_release",
        _object_schema({"document_id": STRING}, required=("document_id",)),
    ),
    (
        "party_delivery_hold_propose",
        "Place party delivery hold",
        "party_delivery_hold",
        _object_schema(
            {
                "party_id": STRING,
                "reason_code": STRING,
                "note": {"type": "string", "default": ""},
            },
            required=("party_id", "reason_code"),
        ),
    ),
    (
        "party_delivery_hold_release_propose",
        "Release party delivery hold",
        "party_delivery_hold_release",
        _object_schema({"party_id": STRING}, required=("party_id",)),
    ),
    (
        "master_data_lifecycle_propose",
        "Change master-data lifecycle",
        "master_data_lifecycle",
        _object_schema(
            {
                "model": {
                    "type": "string",
                    "enum": ["party", "item", "location", "payment_term"],
                },
                "record_id": STRING,
                "is_active": BOOLEAN,
            },
            required=("model", "record_id", "is_active"),
        ),
    ),
    (
        "payment_term_create_propose",
        "Create payment term",
        "payment_term_create",
        _object_schema(
            {
                "code": STRING,
                "name": STRING,
                "due_days": {"type": "integer", "minimum": 0},
                "discount_percent": {"type": "string"},
                "discount_days": {"type": "integer", "minimum": 0},
                "source_system": {"type": "string", "default": ""},
                "external_id": {"type": "string", "default": ""},
                "source_payload": SOURCE_PAYLOAD,
            },
            required=("code", "name", "due_days"),
        ),
    ),
    (
        "payment_term_update_propose",
        "Update payment term",
        "payment_term_update",
        _object_schema(
            {
                "payment_term_id": STRING,
                "code": STRING,
                "name": STRING,
                "due_days": {"type": "integer", "minimum": 0},
                "discount_percent": {"type": "string"},
                "discount_days": {"type": "integer", "minimum": 0},
            },
            required=("payment_term_id", "code", "name", "due_days"),
        ),
    ),
    (
        "price_list_create_propose",
        "Create price list",
        "price_list_create",
        _object_schema(
            {
                "code": STRING,
                "name": STRING,
                "direction": {"type": "string", "enum": ["sales", "purchase"]},
                "currency": STRING,
                "valid_from": OPTIONAL_STRING,
                "valid_until": OPTIONAL_STRING,
                "is_default": {"type": "boolean", "default": False},
                "source_system": {"type": "string", "default": ""},
                "external_id": {"type": "string", "default": ""},
                "source_payload": SOURCE_PAYLOAD,
            },
            required=("code", "name", "direction", "currency"),
        ),
    ),
    (
        "price_list_update_propose",
        "Update price list",
        "price_list_update",
        _object_schema(
            {
                "price_list_id": STRING,
                "code": STRING,
                "name": STRING,
                "direction": {"type": "string", "enum": ["sales", "purchase"]},
                "currency": STRING,
                "is_default": {"type": "boolean", "default": False},
            },
            required=("price_list_id", "code", "name", "direction", "currency"),
        ),
    ),
    (
        "price_tier_create_propose",
        "Add price tier",
        "price_tier_create",
        _object_schema(
            {
                "price_list_id": STRING,
                "item_id": STRING,
                "min_quantity": DECIMAL_STRING,
                "unit_price": DECIMAL_STRING,
                "unit": STRING,
                "valid_from": OPTIONAL_STRING,
                "valid_until": OPTIONAL_STRING,
            },
            required=("price_list_id", "item_id", "min_quantity", "unit_price", "unit"),
        ),
    ),
    (
        "party_price_list_assign_propose",
        "Assign party price list",
        "party_price_list_assign",
        _object_schema(
            {
                "party_id": STRING,
                "price_list_id": STRING,
                "priority": {"type": "integer", "default": 100},
            },
            required=("party_id", "price_list_id"),
        ),
    ),
    (
        "party_group_create_propose",
        "Create party group",
        "party_group_create",
        _object_schema({"code": STRING, "name": STRING}, required=("code", "name")),
    ),
    (
        "party_group_update_propose",
        "Update party group",
        "party_group_update",
        _object_schema(
            {"party_group_id": STRING, "code": STRING, "name": STRING},
            required=("party_group_id", "code", "name"),
        ),
    ),
    (
        "party_group_member_add_propose",
        "Add party group member",
        "party_group_member_add",
        _object_schema(
            {"party_group_id": STRING, "party_id": STRING},
            required=("party_group_id", "party_id"),
        ),
    ),
    (
        "group_price_list_assign_propose",
        "Assign group price list",
        "group_price_list_assign",
        _object_schema(
            {
                "party_group_id": STRING,
                "price_list_id": STRING,
                "priority": {"type": "integer", "default": 100},
            },
            required=("party_group_id", "price_list_id"),
        ),
    ),
    (
        "customer_payment_post_propose",
        "Post customer payment",
        "customer_payment_post",
        _object_schema(
            {
                "invoice_id": STRING,
                "amount": DECIMAL_STRING,
                "payment_number": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("invoice_id", "amount"),
        ),
    ),
    (
        "return_announce_propose",
        "Announce customer return",
        "return_announce",
        _object_schema(
            {
                "commitment_id": STRING,
                "quantity": DECIMAL_STRING,
                "reference": OPTIONAL_STRING,
                "reason": OPTIONAL_STRING,
                "expected_by": OPTIONAL_STRING,
            },
            required=("commitment_id", "quantity"),
        ),
    ),
    (
        "return_announcement_withdraw_propose",
        "Withdraw return announcement",
        "return_announcement_withdraw",
        _object_schema(
            {"announcement_id": STRING, "note": OPTIONAL_STRING},
            required=("announcement_id",),
        ),
    ),
    (
        "payment_run_propose",
        "Execute payment run",
        "payment_run",
        _object_schema(
            {
                "payments": {
                    "type": "array",
                    "minItems": 1,
                    "items": _object_schema(
                        {
                            "invoice_id": STRING,
                            "amount": DECIMAL_STRING,
                            "payment_number": OPTIONAL_STRING,
                        },
                        required=("invoice_id", "amount"),
                    ),
                },
                "currency": STRING,
                "expected_total": DECIMAL_STRING,
                "reason": STRING,
            },
            required=("payments", "currency", "expected_total", "reason"),
        ),
    ),
    (
        "stale_closure_propose",
        "Close stale promises",
        "stale_closure",
        _object_schema(
            {
                "direction": {"type": "string", "enum": ["sales", "purchase"]},
                "due_before": STRING,
                "expected_count": {"type": "integer", "minimum": 0},
                "reason": STRING,
            },
            required=("direction", "due_before", "expected_count", "reason"),
        ),
    ),
    (
        "document_create_propose",
        "Record manual document",
        "document_create",
        _object_schema(
            {
                "document_type": STRING,
                "number": STRING,
                "party_id": STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    # Declared rather than left as a free-form object. The
                    # service has always accepted `billed_document_line_id` and
                    # a schema that does not name it is an absence for an agent,
                    # which can only send what it can read. Nine operational
                    # exception classes read that reference.
                    "items": _object_schema(
                        {
                            "item_id": OPTIONAL_STRING,
                            "sku": OPTIONAL_STRING,
                            "description": OPTIONAL_STRING,
                            "quantity": DECIMAL_STRING,
                            "unit": OPTIONAL_STRING,
                            "unit_price": DECIMAL_STRING,
                            "gross_amount": DECIMAL_STRING,
                            "line_type": OPTIONAL_STRING,
                            "promised_at": OPTIONAL_STRING,
                            "price_list_entry_id": OPTIONAL_STRING,
                            "billed_document_line_id": OPTIONAL_STRING,
                        },
                        required=("quantity", "unit_price", "gross_amount"),
                    ),
                },
                "gross_amount": DECIMAL_STRING,
                "currency": OPTIONAL_STRING,
                "document_date": OPTIONAL_STRING,
                "payment_term_code": OPTIONAL_STRING,
            },
            required=("document_type", "number", "party_id", "lines", "gross_amount"),
        ),
    ),
    (
        "sales_invoice_post_propose",
        "Post sales invoice",
        "sales_invoice_post",
        _object_schema(
            {
                "document_id": STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("document_id",),
        ),
    ),
    (
        "supplier_invoice_post_propose",
        "Post supplier invoice",
        "supplier_invoice_post",
        _object_schema(
            {
                "document_id": STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("document_id",),
        ),
    ),
    (
        "sales_invoice_record_propose",
        "Record sales invoice",
        "sales_invoice_record",
        _object_schema(
            {
                "order_line_id": STRING,
                "quantity": DECIMAL_STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "items": _object_schema(
                        {
                            "order_line_id": STRING,
                            "quantity": DECIMAL_STRING,
                            "gross_amount": DECIMAL_STRING,
                        },
                        required=("order_line_id", "quantity", "gross_amount"),
                    ),
                },
                "gross_amount": DECIMAL_STRING,
                "number": STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("gross_amount", "number"),
        ),
    ),
    (
        "supplier_invoice_record_propose",
        "Record supplier invoice",
        "supplier_invoice_record",
        _object_schema(
            {
                "order_line_id": STRING,
                "quantity": DECIMAL_STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "items": _object_schema(
                        {
                            "order_line_id": STRING,
                            "quantity": DECIMAL_STRING,
                            "gross_amount": DECIMAL_STRING,
                        },
                        required=("order_line_id", "quantity", "gross_amount"),
                    ),
                },
                "gross_amount": DECIMAL_STRING,
                "number": STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("gross_amount", "number"),
        ),
    ),
    (
        "sales_credit_record_propose",
        "Record customer credit",
        "sales_credit_record",
        _object_schema(
            {
                "order_line_id": STRING,
                "quantity": DECIMAL_STRING,
                "invoice_id": STRING,
                "reason": STRING,
                "allocation_amount": DECIMAL_STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "items": _object_schema(
                        {
                            "invoice_line_id": STRING,
                            "quantity": DECIMAL_STRING,
                            "gross_amount": DECIMAL_STRING,
                        },
                        required=("invoice_line_id", "quantity", "gross_amount"),
                    ),
                },
                "gross_amount": DECIMAL_STRING,
                "number": STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("gross_amount", "number"),
        ),
    ),
    (
        "credit_note_post_propose",
        "Post credit note",
        "credit_note_post",
        _object_schema(
            {
                "credit_note_id": STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("credit_note_id",),
        ),
    ),
    (
        "credit_note_allocate_propose",
        "Net credit note against invoice",
        "credit_note_allocate",
        _object_schema(
            {
                "credit_note_id": STRING,
                "invoice_id": STRING,
                "amount": DECIMAL_STRING,
            },
            required=("credit_note_id", "invoice_id", "amount"),
        ),
    ),
    (
        "customer_refund_post_propose",
        "Post customer refund",
        "customer_refund_post",
        _object_schema(
            {
                "credit_note_id": STRING,
                "amount": DECIMAL_STRING,
                "refund_number": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("credit_note_id", "amount"),
        ),
    ),
    (
        "supplier_payment_post_propose",
        "Post supplier payment",
        "supplier_payment_post",
        _object_schema(
            {
                "invoice_id": STRING,
                "amount": DECIMAL_STRING,
                "payment_number": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("invoice_id", "amount"),
        ),
    ),
    (
        "supplier_credit_note_post_propose",
        "Post supplier credit note",
        "supplier_credit_note_post",
        _object_schema(
            {
                "credit_note_id": STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("credit_note_id",),
        ),
    ),
    (
        "supplier_credit_note_allocate_propose",
        "Net supplier credit against invoice",
        "supplier_credit_note_allocate",
        _object_schema(
            {
                "credit_note_id": STRING,
                "invoice_id": STRING,
                "amount": DECIMAL_STRING,
            },
            required=("credit_note_id", "invoice_id", "amount"),
        ),
    ),
    (
        "supplier_refund_post_propose",
        "Post supplier refund",
        "supplier_refund_post",
        _object_schema(
            {
                "credit_note_id": STRING,
                "amount": DECIMAL_STRING,
                "refund_number": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "effective_at": OPTIONAL_STRING,
            },
            required=("credit_note_id", "amount"),
        ),
    ),
    (
        "commitment_revise_propose",
        "Revise commitment",
        "commitment_revise",
        _object_schema(
            {
                "commitment_id": STRING,
                "due_at": OPTIONAL_STRING,
                "quantity": DECIMAL_STRING,
                "note": OPTIONAL_STRING,
                "stated_at": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
            },
            required=("commitment_id",),
        ),
    ),
    (
        "connector_install_propose",
        "Install connector shell",
        "connector_install",
        _object_schema(
            {
                "connector_code": STRING,
                "source_types": {"type": ["array", "null"], "items": STRING},
                "system_code": OPTIONAL_STRING,
                "system_name": OPTIONAL_STRING,
            },
            required=("connector_code",),
        ),
    ),
    (
        "source_system_create_propose",
        "Create source system",
        "source_system_create",
        _object_schema(
            {
                "code": STRING,
                "name": STRING,
                "description": {"type": "string", "default": ""},
            },
            required=("code", "name"),
        ),
    ),
    (
        "source_system_lifecycle_propose",
        "Change source system lifecycle",
        "source_system_lifecycle",
        _object_schema(
            {"source_system_id": STRING, "is_active": BOOLEAN},
            required=("source_system_id", "is_active"),
        ),
    ),
    (
        "source_capability_create_propose",
        "Create source capability",
        "source_capability_create",
        _object_schema(
            {"source_system_id": STRING, "source_type": STRING, "target_type": STRING},
            required=("source_system_id", "source_type", "target_type"),
        ),
    ),
    (
        "source_capability_lifecycle_propose",
        "Change source capability lifecycle",
        "source_capability_lifecycle",
        _object_schema(
            {"capability_id": STRING, "is_active": BOOLEAN},
            required=("capability_id", "is_active"),
        ),
    ),
)

MCP_TOOL_CATALOG += tuple(
    MCPToolDefinition(
        name,
        label,
        f"Prepare this business mutation without changing state. {label}. Human confirmation is required.",
        "propose",
        "Mutations",
        schema,
        _propose(application_name),
    )
    for name, label, application_name, schema in ADDITIONAL_PROPOSAL_TOOLS
)

from reality.tools.finance import ACCOUNT_COMMANDS

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_accounts",
        "Operational accounts",
        "Read allowed accounts, roles, defaults and preview revision.",
        "read",
        "finance",
        _object_schema(),
        _read("finance.accounts.list"),
    ),
)
for _command, (_schema, _service) in ACCOUNT_COMMANDS.items():
    MCP_TOOL_CATALOG += (
        MCPToolDefinition(
            "finance_" + _service.__name__ + "_propose",
            "Configure operational accounts",
            "Prepare an owner-confirmed operational account change; never execute it autonomously.",
            "propose",
            "finance",
            _schema.model_json_schema(),
            _propose(_command),
        ),
    )

from reality.tools.finance import AdjustmentRequest, settlement_input_schema

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_adjustment_context",
        "Settlement reduction context",
        "Read the current invoice claim, accounts and review revision.",
        "read",
        "finance",
        _object_schema({"invoice_id": STRING}, required=("invoice_id",)),
        _read("finance.adjustment.context"),
    ),
    MCPToolDefinition(
        "finance_adjustment_propose",
        "Accept a stated settlement reduction",
        "Prepare a noncash reduction with evidence and owner confirmation. Supplier agreement is mandatory. Never calculate a discount or execute autonomously.",
        "propose",
        "finance",
        AdjustmentRequest.model_json_schema(),
        _propose("finance.adjustment.accept"),
    ),
)

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_credits",
        "Available credit",
        "Read customer or supplier credit that is not used yet: overpayments and credit notes with their original, used and available amounts.",
        "read",
        "finance",
        _object_schema(
            {
                "side": {"type": "string", "enum": ["customer", "supplier"]},
                "status": {"type": "string", "enum": ["outstanding", "all"]},
                "query": STRING,
                "limit": INTEGER,
            }
        ),
        _read("finance.credits.list"),
    ),
    MCPToolDefinition(
        "finance_party_balances",
        "Party balances",
        "Read where each customer or supplier stands: open amount, of which overdue, available credit and balance per party and currency, summed from the open items and the credit register at read time.",
        "read",
        "finance",
        _object_schema(
            {
                "side": {"type": "string", "enum": ["customer", "supplier"]},
                "credit_only": BOOLEAN,
                "query": STRING,
                "limit": INTEGER,
            },
            required=("side",),
        ),
        _read("finance.party_balances.list"),
    ),
    MCPToolDefinition(
        "finance_payments",
        "Recorded payments",
        "Read recorded payments with allocated and unallocated amounts, optionally only those with money left to allocate.",
        "read",
        "finance",
        _object_schema(
            {
                "direction": {"type": "string", "enum": ["incoming", "outgoing"]},
                "only_unallocated": BOOLEAN,
                "query": STRING,
                "limit": INTEGER,
            }
        ),
        _read("finance.payments.list"),
    ),
)

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_settlement_context",
        "Payment and credit context",
        "Read an invoice or original credit and matching invoice choices.",
        "read",
        "finance",
        _object_schema(
            {"document_id": STRING, "query": STRING}, required=("document_id",)
        ),
        _read("finance.settlement.context"),
    ),
    MCPToolDefinition(
        "finance_settlement_propose",
        "Record payment or use credit",
        "Prepare actual payment with explicit allocation and optional stated reduction, allocate existing credit, or record an actual refund. Requires owner confirmation; never initiates a bank transfer.",
        "propose",
        "finance",
        settlement_input_schema(),
        _propose("finance.settlement.apply"),
    ),
)

from reality.tools.finance import OpeningRequest

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_opening_context",
        "Opening positions",
        "Read permitted accounts, parties and revision for opening residual positions.",
        "read",
        "finance",
        _object_schema({"query": STRING}),
        _read("finance.opening.context"),
    ),
    MCPToolDefinition(
        "finance_opening_propose",
        "Import opening positions",
        "Review stated customer/supplier residual debt or credit from a cutover snapshot. No cash or turnover effect. Requires owner confirmation.",
        "propose",
        "finance",
        OpeningRequest.model_json_schema(),
        _propose("finance.opening.import"),
    ),
)

from reality.tools.finance import CreateReference, UpdateReference

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_references",
        "Finance references",
        "Read defined cost centers, case codes and coding groups; no inferred financial meaning.",
        "read",
        "finance",
        _object_schema(
            {
                "kind": {
                    "type": "string",
                    "enum": ["cost_center", "case_code", "coding_group"],
                },
                "state": {"type": "string", "enum": ["active", "blocked"]},
                "query": STRING,
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "offset": {"type": "integer", "minimum": 0},
            }
        ),
        _read("finance.references.list"),
    ),
    MCPToolDefinition(
        "finance_reference_history",
        "Reference history",
        "Read immutable before/after decisions, reason and action for one reference.",
        "read",
        "finance",
        _object_schema(
            {
                "reference_id": STRING,
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "offset": {"type": "integer", "minimum": 0},
            },
            required=["reference_id"],
        ),
        _read("finance.references.history"),
    ),
    MCPToolDefinition(
        "finance_reference_create_propose",
        "Create finance reference",
        "Review a defined cost center, case code or coding group. Requires owner confirmation.",
        "propose",
        "finance",
        CreateReference.model_json_schema(),
        _propose("finance.reference.create"),
    ),
    MCPToolDefinition(
        "finance_reference_update_propose",
        "Update finance reference",
        "Review reference rename, blocking or reactivation with a reason. Requires owner confirmation.",
        "propose",
        "finance",
        UpdateReference.model_json_schema(),
        _propose("finance.reference.update"),
    ),
)

from reality.tools.finance import AssignmentRequest

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_components",
        "Financial detail",
        "Read received invoice/credit detail separately from internal attribution; no inferred net or tax.",
        "read",
        "finance",
        _object_schema(
            {
                "document_id": STRING,
                "reference_query": STRING,
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "offset": {"type": "integer", "minimum": 0},
            },
            required=["document_id"],
        ),
        _read("finance.components.context"),
    ),
    MCPToolDefinition(
        "finance_component_history",
        "Attribution history",
        "Read immutable internal component assignment revisions and their author/action/reason.",
        "read",
        "finance",
        _object_schema(
            {
                "component_id": STRING,
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "offset": {"type": "integer", "minimum": 0},
            },
            required=["component_id"],
        ),
        _read("finance.component.history"),
    ),
    MCPToolDefinition(
        "finance_component_assign_propose",
        "Assign financial component",
        "Review explicit cost-center shares and case/group references against a received basis. Requires owner confirmation; no posting effect.",
        "propose",
        "finance",
        AssignmentRequest.model_json_schema(),
        _propose("finance.component.assign"),
    ),
)

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_matrix",
        "Operational transaction matrix",
        "Read fixed directions, stated amount bases and configured local defaults. Does not authorize a transaction or infer external tax coding.",
        "read",
        "finance",
        _object_schema(),
        _read("finance.matrix.read"),
    ),
)

from reality.tools.finance import SourceMappingRequest

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_source_mappings",
        "Source code mappings",
        "Read exact source classification mappings and existing references. No tax inference.",
        "read",
        "finance",
        _object_schema(
            {
                "query": STRING,
                "source_query": STRING,
                "reference_query": STRING,
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "offset": {"type": "integer", "minimum": 0},
            }
        ),
        _read("finance.source_mappings.list"),
    ),
    MCPToolDefinition(
        "finance_source_mapping_history",
        "Source mapping history",
        "Read source classification revisions and actor/reason/action.",
        "read",
        "finance",
        _object_schema(
            {
                "mapping_id": STRING,
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "offset": {"type": "integer", "minimum": 0},
            },
            required=["mapping_id"],
        ),
        _read("finance.source_mappings.history"),
    ),
    MCPToolDefinition(
        "finance_source_mapping_propose",
        "Review source mapping",
        "Review an exact source-code mapping revision; requires owner confirmation and never alters evidence or postings.",
        "propose",
        "finance",
        SourceMappingRequest.model_json_schema(),
        _propose("finance.source_mapping.set"),
    ),
)

from reality.domain.target_mappings import COMMANDS as TARGET_COMMANDS

_target_reads = {
    "finance_targets": ("finance.targets.list", {}),
    "finance_target_references": (
        "finance.target_references.list",
        {"target_id": STRING, "kind": STRING},
    ),
    "finance_target_mappings": ("finance.target_mappings.list", {"target_id": STRING}),
    "finance_target_mapping_history": (
        "finance.target_mappings.history",
        {"mapping_id": STRING},
    ),
    "finance_target_mapping_preview": (
        "finance.target_mappings.preview",
        {"target_id": STRING, "document_id": STRING},
    ),
}
MCP_TOOL_CATALOG += tuple(
    MCPToolDefinition(
        name,
        name.replace("_", " ").title(),
        "Inspect Finance target references and explicit mapping resolution.",
        "read",
        "finance",
        _object_schema(
            {
                **fields,
                **(
                    {"query": STRING}
                    if name
                    in (
                        "finance_targets",
                        "finance_target_references",
                        "finance_target_mappings",
                    )
                    else {}
                ),
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "offset": {"type": "integer", "minimum": 0},
            },
            required=[k for k in fields if k.endswith("_id")],
        ),
        _read(tool),
    )
    for name, (tool, fields) in _target_reads.items()
)
MCP_TOOL_CATALOG += tuple(
    MCPToolDefinition(
        command.replace(".", "_") + "_propose",
        "Review Finance target configuration",
        "Review a Finance-only target configuration change; owner confirmation required.",
        "propose",
        "finance",
        model.model_json_schema(),
        _propose(command),
    )
    for command, model in TARGET_COMMANDS.items()
)

from reality.tools.analytics import SCHEMAS as ANALYTICS_SCHEMAS

for _public_name, _application_name, _label in (
    ("analytics_catalog", "analytics.catalog", "Discover analytics"),
    ("analytics_query", "analytics.query", "Run an analysis"),
    ("analytics_contributors", "analytics.contributors", "Explain an analytical value"),
    ("analytics_export", "analytics.export", "Export an analysis"),
    ("analytics_reports_list", "analytics.reports.list", "List my reports"),
    ("analytics_report_get", "analytics.reports.get", "Read my report"),
):
    MCP_TOOL_CATALOG += (
        MCPToolDefinition(
            _public_name,
            _label,
            "Discover supported datasets first; use structured definitions, scoped identities and declared units. Private reports require authenticated personal context.",
            "read",
            "Analytics",
            {
                "required": [],
                **ANALYTICS_SCHEMAS[_application_name].model_json_schema(),
            },
            _read(_application_name),
        ),
    )

from reality.tools.graph import SCHEMAS as GRAPH_SCHEMAS

for _public_name, _application_name, _label in (
    ("graph_catalog", "graph.catalog", "Discover the business graph"),
    ("graph_ask", "graph.ask", "Ask the business graph"),
    ("graph_reports_list", "graph.reports.list", "List my graph reports"),
    ("graph_report_get", "graph.reports.get", "Read my graph report"),
):
    MCP_TOOL_CATALOG += (
        MCPToolDefinition(
            _public_name,
            _label,
            "Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that cannot be added, and is more useful than a total that is wrong.",
            "read",
            "Analytics",
            {
                "required": [],
                **GRAPH_SCHEMAS[_application_name].model_json_schema(),
            },
            _read(_application_name),
        ),
    )

from reality.domain.analytics import ReportChange as _AnalyticsReportChange
from reality.domain.graph_report import GraphReportChange as _GraphReportChange

MCP_TOOL_CATALOG = (
    *MCP_TOOL_CATALOG,
    MCPToolDefinition(
        "graph_report_change_propose",
        "Change private graph report",
        "Prepare a private graph report change. Requires trusted authenticated user context; confirm explicitly before it is saved.",
        "propose",
        "analytics",
        _GraphReportChange.model_json_schema(),
        _propose("graph.reports.change"),
    ),
    MCPToolDefinition(
        "analytics_report_change_propose",
        "Change private report",
        "Prepare a private report change. Requires trusted authenticated user context; confirm explicitly before it is saved.",
        "propose",
        "analytics",
        _AnalyticsReportChange.model_json_schema(),
        _propose("analytics.reports.change"),
    ),
)

MCP_TOOL_REGISTRY = {tool.name: tool for tool in MCP_TOOL_CATALOG}
if len(MCP_TOOL_REGISTRY) != len(MCP_TOOL_CATALOG):
    raise RuntimeError("MCP tool names must be unique.")

MCP_TOOL_NAMES = frozenset(MCP_TOOL_REGISTRY)
LEGACY_TOOL_NAMES = {
    "issues_list": "exceptions_list",
    "issue_explain": "exception_explain",
    "actions_pending": "proposals_awaiting_approval",
    "action_confirm": "proposal_approve_and_execute",
}


def tool_definitions(
    *, access: Iterable[ToolAccess] | None = None
) -> tuple[MCPToolDefinition, ...]:
    if access is None:
        return MCP_TOOL_CATALOG
    allowed = frozenset(access)
    return tuple(tool for tool in MCP_TOOL_CATALOG if tool.access in allowed)


def dispatch_tool(
    session: Session,
    tenant_id: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    *,
    allowed_access: Iterable[ToolAccess] | None = None,
) -> Any:
    """Dispatch through the canonical binding with caller-owned tenant authority."""
    definition = MCP_TOOL_REGISTRY.get(tool_name)
    if definition is None:
        raise ValueError(f"Unknown MCP tool: {tool_name}")
    if allowed_access is not None and definition.access not in frozenset(
        allowed_access
    ):
        raise PermissionError(
            f"Caller does not allow MCP {definition.access} tool: {tool_name}"
        )
    return definition.handler(session, tenant_id, arguments or {})


def model_tool_schemas(
    *, access: Iterable[ToolAccess] = ("read", "propose")
) -> list[dict[str, Any]]:
    return [tool.model_schema() for tool in tool_definitions(access=access)]


def validate_tool_permissions(tool_names: list[str] | tuple[str, ...]) -> list[str]:
    normalized = list(
        dict.fromkeys(
            LEGACY_TOOL_NAMES.get(name.strip(), name.strip())
            for name in tool_names
            if name.strip()
        )
    )
    if "*" in normalized:
        return ["*"]
    unknown = sorted(set(normalized) - MCP_TOOL_NAMES)
    if unknown:
        raise ValueError("Unknown MCP tools: " + ", ".join(unknown))
    if not normalized:
        raise ValueError("Select at least one MCP tool or grant all tools.")
    return normalized


def _analytics_caller():
    from reality.tools.analytics import CALLER

    return CALLER.get()
