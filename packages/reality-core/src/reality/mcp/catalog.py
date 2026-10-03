from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy.orm import Session

from reality.mcp.principal import (
    MCPPrincipal,
    current_mcp_principal,
    mcp_principal_context,
)
from reality.services.business_journeys import PROCESS_AREAS
from reality.services.core import (
    MANUAL_OPERATIONAL_DOCUMENT_TYPES,
    MAX_INVOICE_POSITIONS,
    InvalidOperation,
    NotFound,
)
from reality.services.delivery_actions import PUBLIC_MOVEMENT_TYPES
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    reject_proposal,
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
        """
        BUSINESS PURPOSE:
        Run the bound read-only application tool for this company. Selected list tools default to the paginated response format.

        BUSINESS RULE mcp.catalog._read.handler.step-10:
        Pass the stated inputs to the shared run read tool service. Its own source describes validation and record changes.
        """
        if application_name in {
            "business_discover",
            "inventory",
            "commitments",
            "fulfillment_queue",
            "fulfillment_blockers",
            "item_supply_demand",
        }:
            arguments = {"response_format": "page", **arguments}
        # reality-rule: mcp.catalog._read.handler.step-10
        return run_read_tool(session, tenant_id, application_name, arguments)

    return handler


def _company_party_record_propose(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """Spec 289: propose the company's own business partner; the server names it."""
    from reality.services.company_party import propose_company_party

    if arguments:
        raise InvalidOperation(code="company_party_arguments_unsupported")
    proposal = propose_company_party(session, tenant_id)
    return {
        "proposal_id": proposal.id,
        "status": proposal.status,
        "name": json.loads(proposal.input)["name"],
    }


_company_party_record_propose.application_name = "company_party_record"  # type: ignore[attr-defined]


def _cost_review_propose(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """Spec 282: propose a drafted cost review without copying its arguments."""
    from pydantic import ValidationError

    from reality.domain.cost_review_draft import CostReviewProposeRequest
    from reality.services.cost_review_draft import DraftChanged
    from reality.services.costing import propose_cost_review

    try:
        request = CostReviewProposeRequest.model_validate(arguments)
    except ValidationError as error:
        raise InvalidOperation(str(error)) from error
    try:
        return propose_cost_review(
            session,
            tenant_id,
            kind=request.kind,
            scope_id=request.scope_id,
            answers=request.answers.model_dump(exclude_none=True)
            if request.answers
            else None,
        )
    except DraftChanged as error:
        return {
            "proposal_id": None,
            "status": "draft_changed",
            "open_inputs": error.draft["open_inputs"],
            "next_step": "Ask the person about the open inputs by their labels, then call again.",
        }


# The proposal it creates is an ordinary cost decision with its existing web review.
_cost_review_propose.application_name = "cost.change"  # type: ignore[attr-defined]


def _propose(application_name: str) -> ToolHandler:
    def handler(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
        """
        BUSINESS PURPOSE:
        Prepare a change proposal for the bound application tool. Normalize absent arguments and expose the review; do not execute the change.

        BUSINESS RULE mcp.catalog._propose.handler.step-8:
        Pass the stated inputs to the shared create change proposal service. Its own source describes validation and record changes.

        BUSINESS RULE mcp.catalog._propose.handler.result:
        Return the prepared proposal identity, status, normalized arguments, review preview and next-step guidance. requires_confirmation is always true; this adapter does not execute the proposed business change.
        """
        normalized = {
            key: value for key, value in arguments.items() if value is not None
        }
        if application_name == "source_ingest":
            normalized.setdefault("source_system", "manual_upload")
            normalized.setdefault("source_type", "data_drop")
            normalized.setdefault("expected_target", "data_drop")
        # reality-rule: mcp.catalog._propose.handler.step-8
        proposal = create_change_proposal(
            session, tenant_id, application_name, normalized
        )
        from reality.services.proposal_reviews import proposal_next_step

        # reality-rule: mcp.catalog._propose.handler.result
        return {
            "proposal_id": proposal.id,
            "status": proposal.status,
            "requires_confirmation": True,
            "arguments": normalized,
            "preview": json.loads(proposal.output),
            "next_step": proposal_next_step(proposal),
        }

    handler.application_name = application_name  # type: ignore[attr-defined]
    return handler


#: The MCP access token of the call being served, set by the MCP runtime for the
#: duration of one tool call. A decision it settles records this token (spec 263).
#: Chat and other callers of `dispatch_tool` leave it unset.
SETTLING_TOKEN: ContextVar[str | None] = ContextVar("mcp_settling_token", default=None)
SETTLING_CHANNEL: ContextVar[str | None] = ContextVar(
    "decision_settling_channel", default=None
)


@contextmanager
def decision_channel(channel: str):
    """Attach a server-observed decision channel to one adapter dispatch."""
    token = SETTLING_CHANNEL.set(channel)
    try:
        yield
    finally:
        SETTLING_CHANNEL.reset(token)


def _approve_proposal(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Settle an explicit authorized approval through the shared proposal service; legacy delivery proposals first return a review requiring confirmation.

    BUSINESS RULE mcp.catalog._approve_proposal.refusal-3:
    IF approved is not explicitly true:
        Refuse: Set approved=true only for an explicit authorized decision.

    BUSINESS RULE mcp.catalog._approve_proposal.step-29:
    Pass the stated inputs to the shared approve and execute proposal service. Its own source describes validation and record changes.

    BUSINESS RULE mcp.catalog._approve_proposal.result:
    Return the settled proposal identity, status, tool, receipt and recorded decision evidence. Successful settlement delegates execution to the common approval service.

    BUSINESS RULE mcp.catalog._approve_proposal.effect-31:
    IF a proposed legacy delivery action was found and has no retained delivery review:
        Run the shared review existing check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.
    """
    # reality-rule: mcp.catalog._approve_proposal.refusal-3
    if arguments.get("approved") is not True:
        raise ValueError("Set approved=true only for an explicit authorized decision.")
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
        # reality-rule: mcp.catalog._approve_proposal.effect-31
        reviewed = review_existing(session, tenant_id, candidate.id)
        return {
            "proposal_id": reviewed.id,
            "status": reviewed.status,
            "preview": json.loads(reviewed.output),
            "requires_confirmation": True,
        }
    mcp_principal = current_mcp_principal()
    confirming_principal = _analytics_caller()
    if mcp_principal is not None and mcp_principal.user_id is not None:
        from reality.services.memberships import Principal

        confirming_principal = Principal(mcp_principal.user_id)
    # reality-rule: mcp.catalog._approve_proposal.step-29
    proposal = approve_and_execute_proposal(
        session,
        tenant_id,
        arguments["proposal_id"],
        review_token=arguments.get("review_token"),
        confirmed=True,
        confirming_principal=confirming_principal,
        settling_token_id=_settling_token(session, tenant_id),
        settling_channel=SETTLING_CHANNEL.get(),
    )
    receipt = json.loads(proposal.output)
    # reality-rule: mcp.catalog._approve_proposal.result
    return {
        "proposal_id": proposal.id,
        "status": proposal.status,
        "tool": proposal.type.removeprefix("tool:"),
        "output": receipt,
        "receipt": receipt,
        "decider": _decider(session, tenant_id, proposal.id),
    }


def _reject_proposal(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Settle an explicit authorized rejection through the shared proposal service without applying a business change.

    BUSINESS RULE mcp.catalog._reject_proposal.refusal-3:
    IF rejected is not explicitly true:
        Refuse: Set rejected=true only for an explicit authorized decision.

    BUSINESS RULE mcp.catalog._reject_proposal.step-11:
    Pass the stated inputs to the shared reject proposal service. Its own source describes validation and record changes.

    BUSINESS RULE mcp.catalog._reject_proposal.result:
    Return the rejected proposal and recorded decider. Report business_effect as none; rejection does not execute the proposed mutation.
    """
    # reality-rule: mcp.catalog._reject_proposal.refusal-3
    if arguments.get("rejected") is not True:
        raise ValueError("Set rejected=true only for an explicit authorized decision.")
    mcp_principal = current_mcp_principal()
    confirming_principal = _analytics_caller()
    if mcp_principal is not None and mcp_principal.user_id is not None:
        from reality.services.memberships import Principal

        confirming_principal = Principal(mcp_principal.user_id)
    # reality-rule: mcp.catalog._reject_proposal.step-11
    proposal = reject_proposal(
        session,
        tenant_id,
        arguments["proposal_id"],
        confirming_principal=confirming_principal,
        settling_token_id=_settling_token(session, tenant_id),
        settling_channel=SETTLING_CHANNEL.get(),
    )
    # reality-rule: mcp.catalog._reject_proposal.result
    return {
        "proposal_id": proposal.id,
        "status": proposal.status,
        "decided_by_user_id": proposal.decided_by_user_id,
        "decider": _decider(session, tenant_id, proposal.id),
        "business_effect": "none",
    }


def _settling_token(session: Session, tenant_id: str) -> str | None:
    """The calling token, when it is one this company issued.

    The runtime only admits stored tokens, but a decision must never fail because
    its attribution cannot be recorded; an unknown token leaves the decider unknown.
    """
    principal = current_mcp_principal()
    token_id = (
        principal.credential_id
        if principal is not None and principal.authentication_kind == "manual"
        else SETTLING_TOKEN.get()
    )
    if token_id is None:
        return None
    from sqlalchemy import select

    from reality.db.core import MCPAccessToken

    return session.scalar(
        select(MCPAccessToken.id).where(
            MCPAccessToken.tenant_id == tenant_id, MCPAccessToken.id == token_id
        )
    )


def _decider(session: Session, tenant_id: str, proposal_id: str) -> dict[str, Any]:
    from reality.services.decision_attribution import UNKNOWN, decision_attributions

    attribution = decision_attributions(session, tenant_id, [proposal_id])
    return attribution.get(proposal_id, {}).get("decider", dict(UNKNOWN))


STRING = {"type": "string"}
OPTIONAL_STRING = {"type": ["string", "null"]}
SOURCE_PAYLOAD = {"type": ["object", "null"], "additionalProperties": True}
PARTY_EMAILS = {
    "type": "array",
    "maxItems": 20,
    "items": _object_schema(
        {
            "email": {"type": "string", "maxLength": 320},
            "label": {"type": "string", "maxLength": 80, "default": ""},
        },
        required=("email",),
    ),
    "default": [],
}
DECIMAL_STRING = {"type": "string", "pattern": "^-?[0-9]+(?:\\.[0-9]+)?$"}
RECEIVED_FINANCE_DETAIL = _object_schema(
    {
        "version": {"type": "integer", "enum": [1]},
        "net": DECIMAL_STRING,
        "tax": DECIMAL_STRING,
        "base": DECIMAL_STRING,
        "gross": DECIMAL_STRING,
        "currency": STRING,
        "codes": {"type": "object", "additionalProperties": True},
    }
)


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


PURCHASE_UNIT = {
    "type": ["string", "null"],
    "description": (
        "Receipts only: the unit the quantity is stated in, the item's stock unit "
        "(default) or its purchase unit. A purchase-unit quantity is recorded in "
        "the stock unit by the item's stated factor, and what was stated is kept."
    ),
}


BEYOND_ORDER = {
    "type": ["boolean", "null"],
    "description": (
        "Receipts against a purchase line only: bring in more than the line still "
        "expects. The surplus is reported until it is kept or sent back."
    ),
}
ADVISED_LINES = {
    "type": ["array", "null"],
    "description": (
        "Inbound supplier notices only: how much the notice brings for each "
        "purchase line of this supplier, as stated."
    ),
    "items": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"commitment_id": STRING, "quantity": DECIMAL_STRING},
        "required": ["commitment_id", "quantity"],
    },
}


def _shipment_execution_schema(purposes: dict[str, str]) -> dict[str, Any]:
    branches = []
    for purpose, movement_type in purposes.items():
        movement = _object_schema(
            {
                "movement_type": {"type": "string", "const": movement_type},
                "item_id": STRING,
                "quantity": DECIMAL_STRING,
                "from_location_id": OPTIONAL_STRING,
                "to_location_id": OPTIONAL_STRING,
                "commitment_id": OPTIONAL_STRING,
                "handling_unit_id": OPTIONAL_STRING,
                "lot_id": OPTIONAL_STRING,
                "serial_unit_id": OPTIONAL_STRING,
                "reason": OPTIONAL_STRING,
                # Spec 338: the line a wrong item was meant for, instead of a
                # commitment it fulfils.
                "meant_for_commitment_id": OPTIONAL_STRING,
                # Spec 301: only a receipt may be stated in the purchase unit.
                **(
                    {
                        # Spec 338: a surplus received on purpose.
                        "beyond_order": BEYOND_ORDER,
                        "unit": PURCHASE_UNIT,
                        "blocked_quantity": DECIMAL_STRING,
                        "block_reason": {
                            "type": "string",
                            "enum": ["quality", "damage", "expiry", "inspection"],
                        },
                    }
                    if movement_type == "receipt"
                    else {}
                ),
            },
            required=("item_id", "quantity"),
        )
        branches.append(
            _object_schema(
                {
                    "purpose": {"type": "string", "const": purpose},
                    "counterparty_id": STRING,
                    "movements": {
                        "type": "array",
                        "minItems": 1,
                        "items": movement,
                    },
                    "carrier": OPTIONAL_STRING,
                    "tracking_number": OPTIONAL_STRING,
                    "source_record_id": OPTIONAL_STRING,
                    "occurred_at": OPTIONAL_STRING,
                    # Spec 312: a customer pickup and who collected.
                    "delivery_mode": OPTIONAL_STRING,
                    "collected_by": OPTIONAL_STRING,
                    # Spec 334: the planned delivery this dispatch executes.
                    **(
                        {"outbound_delivery_id": OPTIONAL_STRING}
                        if purpose == "customer_delivery"
                        else {}
                    ),
                    # Spec 338: receive into the inbound shipment that was announced.
                    **(
                        {"shipment_id": OPTIONAL_STRING}
                        if purpose in {"supplier_delivery", "customer_return"}
                        else {}
                    ),
                },
                required=("purpose", "counterparty_id", "movements"),
            )
        )
    return {"type": "object", "oneOf": branches, "additionalProperties": False}


OUTBOUND_DELIVERY_FIELDS = {
    "recipient_party_id": OPTIONAL_STRING,
    "address": _object_schema(
        {
            "name": OPTIONAL_STRING,
            "street": OPTIONAL_STRING,
            "postal_code": OPTIONAL_STRING,
            "city": OPTIONAL_STRING,
            "country": OPTIONAL_STRING,
            "note": OPTIONAL_STRING,
        }
    ),
    "slot": _object_schema(
        {"from": STRING, "until": STRING}, required=("from", "until")
    ),
    "staging_location_id": OPTIONAL_STRING,
    "note": OPTIONAL_STRING,
    "lines": {
        "type": "array",
        "minItems": 1,
        "maxItems": 500,
        "items": _object_schema(
            {"commitment_id": STRING, "quantity": DECIMAL_STRING},
            required=("commitment_id", "quantity"),
        ),
    },
}


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
        "emails": PARTY_EMAILS,
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
        "business_journey_guide",
        "Ask about Reality capabilities",
        "Answer whether Reality supports a business situation using cited, release-reviewed Business Journey Guide entries.",
        "read",
        "Discovery",
        _object_schema(
            {
                "question": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 1000,
                    "description": "Business situation to check against the published Business Journey Guide.",
                },
                "locale": {
                    "type": "string",
                    "enum": ["en", "de"],
                    "default": "en",
                    "description": "Language for the deterministic capability conclusion.",
                },
            },
            required=("question",),
        ),
        _read("business_journey_guide"),
    ),
    MCPToolDefinition(
        "capability_catalog",
        "Discover business capabilities",
        (
            "Start here. Without arguments it lists the business areas this company's "
            "Reality covers; with one topic it lists that area's capabilities, the "
            "tools behind each, and whether this credential may call them."
        ),
        "read",
        "Discovery",
        _object_schema({"topic": OPTIONAL_STRING}),
        _read("capability_catalog"),
    ),
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
        "price_quote_read",
        "Read authoritative price quote",
        "Resolve the applicable party-aware quantity tier and explain its assignment path; returns an explicit no-match result when no price applies.",
        "read",
        "Master data",
        _object_schema(
            {
                "party_id": STRING,
                "item_id": STRING,
                "quantity": DECIMAL_STRING,
                "direction": {"type": "string", "enum": ["sales", "purchase"]},
                "currency": STRING,
                "unit": STRING,
                "at": OPTIONAL_STRING,
            },
            required=(
                "party_id",
                "item_id",
                "quantity",
                "direction",
                "currency",
                "unit",
            ),
        ),
        _read("price_quote"),
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
                "advised": ADVISED_LINES,
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
        _shipment_execution_schema(
            {"customer_delivery": "shipment", "supplier_return": "supplier_return"}
        ),
        _propose("shipment_dispatch"),
    ),
    MCPToolDefinition(
        "shipment_receive_propose",
        "Propose package receipt",
        "Prepare one incoming package and its exact physical Movements; execution requires explicit confirmation.",
        "propose",
        "Operations",
        _shipment_execution_schema(
            {"supplier_delivery": "receipt", "customer_return": "return"}
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
        "fulfillment_readiness",
        "Read fulfillment readiness",
        "Canonical blockers, payment amounts, and evidence for one delivery commitment.",
        "read",
        "Operations",
        _object_schema({"commitment_id": STRING}, required=("commitment_id",)),
        _read("fulfillment_readiness"),
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
        "Settle one exact proposal by explicit authorized decision and execute it through the shared application boundary.",
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
        "proposal_reject",
        "Reject a proposal",
        "Reject one pending proposal by explicit authorized decision without business effect.",
        "confirm",
        "Exceptions & proposals",
        _object_schema(
            {
                "proposal_id": STRING,
                "rejected": {"type": "boolean", "const": True},
            },
            required=("proposal_id", "rejected"),
        ),
        _reject_proposal,
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
        "Prepare a stock reservation without allocating before confirmation. Without location_id it reserves at the promise's own warehouse; with it, the rest at that active warehouse holding stock (spec 303), for example one the stock_in_another_location finding names.",
        "propose",
        "Mutations",
        _object_schema(
            {
                "commitment_id": STRING,
                "quantity": OPTIONAL_STRING,
                "handling_unit_id": OPTIONAL_STRING,
                "lot_id": OPTIONAL_STRING,
                "serial_unit_id": OPTIONAL_STRING,
                "location_id": OPTIONAL_STRING,
            },
            required=("commitment_id",),
        ),
        _propose("reserve"),
    ),
    MCPToolDefinition(
        "movement_correction_propose",
        "Propose Movement correction",
        "Preview an exact compensating Movement and optional replacement without executing before a separate decision.",
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
        "Preview a complete inverse posting group without executing before a separate decision.",
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
        "Prepare updates to existing Parties identified only by opaque ID. Exact changes are previewed and a separate decision is required.",
        "propose",
        "Mutations",
        _records_schema(PARTY_UPDATE_RECORD),
        _propose("party_update"),
    ),
    MCPToolDefinition(
        "item_update_propose",
        "Propose Item update",
        "Prepare updates to existing Items identified only by opaque ID. Exact changes are previewed and a separate decision is required.",
        "propose",
        "Mutations",
        _records_schema(ITEM_UPDATE_RECORD),
        _propose("item_update"),
    ),
    MCPToolDefinition(
        "location_update_propose",
        "Propose Location update",
        "Prepare updates to existing Locations identified only by opaque ID. Parent locations also use opaque IDs. Exact changes are previewed and a separate decision is required.",
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
        # Spec 308: a sales order line may name the item by the customer's number.
        "customer_item_number": OPTIONAL_STRING,
    },
    required=("quantity", "unit", "unit_price", "gross_amount"),
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
                "movement_type": {
                    "type": "string",
                    "enum": list(PUBLIC_MOVEMENT_TYPES),
                },
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
                "meant_for_commitment_id": OPTIONAL_STRING,
                "beyond_order": BEYOND_ORDER,
                "unit": PURCHASE_UNIT,
                "blocked_quantity": DECIMAL_STRING,
                "block_reason": {
                    "type": "string",
                    "enum": ["quality", "damage", "expiry", "inspection"],
                },
                "opening_cost": {
                    "type": "object",
                    "description": "Opening stock only: the total acquisition value its evidence states, recorded as received for the cost review (spec 282).",
                    "properties": {
                        "amount": {
                            "type": "string",
                            "description": "Total acquisition value exactly as the evidence states it; never a computed unit cost.",
                        },
                        "currency": {
                            "type": "string",
                            "description": "Three-letter currency code of the stated value.",
                        },
                        "evidence_reference": {
                            "type": "string",
                            "description": "Names the document the value comes from, for example an inventory list.",
                        },
                    },
                    "required": ["amount", "currency", "evidence_reference"],
                    "additionalProperties": False,
                },
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
                "requires_prepayment": BOOLEAN,
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
                "requires_prepayment": BOOLEAN,
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
                "document_type": {
                    "type": "string",
                    "enum": list(MANUAL_OPERATIONAL_DOCUMENT_TYPES),
                },
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
                "exchange_rate": OPTIONAL_STRING,
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
                    "maxItems": MAX_INVOICE_POSITIONS,
                    "items": _object_schema(
                        {
                            "order_line_id": STRING,
                            "quantity": DECIMAL_STRING,
                            "gross_amount": DECIMAL_STRING,
                            "reality_finance_v1": RECEIVED_FINANCE_DETAIL,
                        },
                        required=("order_line_id", "quantity", "gross_amount"),
                    ),
                },
                "gross_amount": DECIMAL_STRING,
                "reality_finance_v1": RECEIVED_FINANCE_DETAIL,
                "number": STRING,
                "effective_at": OPTIONAL_STRING,
                "delivery_guard": _object_schema(
                    {
                        "unbilled_quantity": DECIMAL_STRING,
                        "unit": STRING,
                    },
                    required=("unbilled_quantity", "unit"),
                ),
                # Spec 299: paid down payments this final invoice deducts.
                "down_payment_offsets": {
                    "type": "array",
                    "minItems": 1,
                    "items": _object_schema(
                        {
                            "down_payment_document_id": STRING,
                            "amount": DECIMAL_STRING,
                        },
                        required=("down_payment_document_id", "amount"),
                    ),
                },
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
                    "maxItems": MAX_INVOICE_POSITIONS,
                    "items": _object_schema(
                        {
                            "order_line_id": STRING,
                            "quantity": DECIMAL_STRING,
                            "gross_amount": DECIMAL_STRING,
                            "reality_finance_v1": RECEIVED_FINANCE_DETAIL,
                        },
                        required=("order_line_id", "quantity", "gross_amount"),
                    ),
                },
                "gross_amount": DECIMAL_STRING,
                "reality_finance_v1": RECEIVED_FINANCE_DETAIL,
                "number": STRING,
                "effective_at": OPTIONAL_STRING,
                "exchange_rate": OPTIONAL_STRING,
            },
            required=("gross_amount", "number"),
        ),
    ),
    (
        "supply_assign_propose",
        "Assign supplier supply",
        "supply_assign",
        _object_schema(
            {
                "supplier_commitment_id": STRING,
                "customer_commitment_id": OPTIONAL_STRING,
                "purpose": {
                    "type": "string",
                    "enum": ["customer_demand", "stock_replenishment"],
                },
                "quantity": DECIMAL_STRING,
            },
            required=("supplier_commitment_id", "purpose", "quantity"),
        ),
    ),
    (
        "customer_exchange_propose",
        "Exchange returned goods",
        "customer_exchange_record",
        _object_schema(
            {
                "return_movement_id": OPTIONAL_STRING,
                "return_announcement_id": OPTIONAL_STRING,
                "quantity": DECIMAL_STRING,
                "replacement_item_id": STRING,
                "replacement_quantity": DECIMAL_STRING,
                "location_id": OPTIONAL_STRING,
                "due_at": OPTIONAL_STRING,
                "reason": STRING,
            },
            required=(
                "quantity",
                "replacement_item_id",
                "replacement_quantity",
                "reason",
            ),
        ),
    ),
    (
        "shipment_delivery_failure_propose",
        "Record a failed delivery",
        "shipment_delivery_failure",
        _object_schema(
            {
                "shipment_id": STRING,
                "kind": {
                    "type": "string",
                    "enum": ["undeliverable", "refused", "lost"],
                },
                "reason": STRING,
                "occurred_at": OPTIONAL_STRING,
                "claim_party_id": OPTIONAL_STRING,
                "claim_amount": OPTIONAL_STRING,
            },
            required=("shipment_id", "kind", "reason"),
        ),
    ),
    (
        "drop_shipment_record_propose",
        "Record a drop shipment",
        "drop_shipment_record",
        _object_schema(
            {
                "supplier_commitment_id": STRING,
                "customer_commitment_id": OPTIONAL_STRING,
                "quantity": STRING,
                "occurred_at": OPTIONAL_STRING,
                "carrier": OPTIONAL_STRING,
                "tracking_number": OPTIONAL_STRING,
            },
            required=("supplier_commitment_id", "quantity"),
        ),
    ),
    (
        "order_line_item_assign_propose",
        "Assign an item to an order line",
        "order_line_item_assign",
        _object_schema(
            {
                "document_line_id": STRING,
                "item_id": STRING,
                "remember_for_customer": {"type": "boolean"},
            },
            required=("document_line_id", "item_id"),
        ),
    ),
    (
        "down_payment_invoice_record_propose",
        "Record a down-payment invoice",
        "down_payment_invoice_record",
        _object_schema(
            {
                "order_id": STRING,
                "number": STRING,
                "gross_amount": DECIMAL_STRING,
                "currency": OPTIONAL_STRING,
                "effective_at": OPTIONAL_STRING,
                "net_amount": DECIMAL_STRING,
                "tax_amount": DECIMAL_STRING,
            },
            required=("order_id", "number", "gross_amount"),
        ),
    ),
    (
        "proforma_invoice_record_propose",
        "Record a pro-forma invoice",
        "proforma_invoice_record",
        _object_schema(
            {
                "order_id": STRING,
                "number": STRING,
                "gross_amount": DECIMAL_STRING,
                "currency": OPTIONAL_STRING,
                "document_date": OPTIONAL_STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "items": _object_schema(
                        {
                            "description": STRING,
                            "quantity": DECIMAL_STRING,
                            "gross_amount": DECIMAL_STRING,
                            "net_amount": DECIMAL_STRING,
                            "tax_amount": DECIMAL_STRING,
                        },
                        required=("description", "quantity", "gross_amount"),
                    ),
                },
            },
            required=("order_id", "number", "gross_amount"),
        ),
    ),
    (
        "credit_hold_release_propose",
        "Release a credit hold",
        "credit_hold_release",
        _object_schema(
            {"document_id": STRING, "reason": STRING},
            required=("document_id", "reason"),
        ),
    ),
    (
        "return_disposition_propose",
        "Resolve returned goods",
        "return_disposition",
        _object_schema(
            {
                "return_movement_id": STRING,
                "disposition": {
                    "type": "string",
                    "enum": [
                        "restock",
                        "quarantine_repair",
                        "scrap_loss",
                        "return_to_supplier",
                    ],
                },
                "quantity": DECIMAL_STRING,
                "destination_location_id": OPTIONAL_STRING,
                "reason": OPTIONAL_STRING,
            },
            required=("return_movement_id", "disposition", "quantity"),
        ),
    ),
    (
        "sales_credit_record_propose",
        "Record customer credit",
        "sales_credit_record",
        {
            **_object_schema(
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
            "oneOf": [
                {
                    "title": "Invoice-linked financial credit",
                    "required": [
                        "invoice_id",
                        "lines",
                        "reason",
                        "allocation_amount",
                    ],
                    "not": {
                        "anyOf": [
                            {"required": ["order_line_id"]},
                            {"required": ["quantity"]},
                        ]
                    },
                },
                {
                    "title": "Legacy return credit",
                    "required": ["order_line_id", "quantity"],
                    "not": {
                        "anyOf": [
                            {"required": ["invoice_id"]},
                            {"required": ["lines"]},
                            {"required": ["reason"]},
                            {"required": ["allocation_amount"]},
                        ]
                    },
                },
            ],
        },
    ),
    (
        "supplier_invoice_free_record_propose",
        "Record free supplier invoice",
        "supplier_invoice_free_record",
        _object_schema(
            {
                "supplier_id": STRING,
                "number": STRING,
                "currency": STRING,
                "gross_amount": DECIMAL_STRING,
                "document_date": OPTIONAL_STRING,
                "effective_at": OPTIONAL_STRING,
                "exchange_rate": OPTIONAL_STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
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
                        },
                        required=("quantity", "unit_price", "gross_amount"),
                    ),
                },
            },
            required=(
                "supplier_id",
                "number",
                "currency",
                "gross_amount",
                "lines",
            ),
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
                "paid_amount": OPTIONAL_STRING,
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
                # Spec 310: a supplier's confirmed unit price, in the line's unit.
                "unit_price": OPTIONAL_STRING,
                "note": OPTIONAL_STRING,
                "stated_at": OPTIONAL_STRING,
                "source_record_id": OPTIONAL_STRING,
                "retained_allocations": {
                    "type": ["array", "null"],
                    "items": _object_schema(
                        {
                            "reservation_id": STRING,
                            "quantity": DECIMAL_STRING,
                        },
                        required=("reservation_id", "quantity"),
                    ),
                },
            },
            required=("commitment_id",),
        ),
    ),
    (
        "commitment_cancel_propose",
        "Cancel commitment remainder",
        "commitment_cancel",
        _object_schema(
            {
                "commitment_id": STRING,
                "reason": STRING,
                "source_record_id": OPTIONAL_STRING,
            },
            required=("commitment_id", "reason"),
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
    (
        "business_journey_suggest_propose",
        "Suggest a Business Journey",
        "business_journey_proposal_create",
        _object_schema(
            {
                "title": {"type": "string", "minLength": 3, "maxLength": 200},
                "business_question": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 1000,
                },
                "expected_outcome": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 2000,
                },
                "process_area": {
                    "type": "string",
                    "enum": sorted(PROCESS_AREAS),
                },
                "business_context": {
                    "type": "string",
                    "maxLength": 1000,
                    "default": "",
                },
            },
            required=(
                "title",
                "business_question",
                "expected_outcome",
                "process_area",
            ),
        ),
    ),
    (
        "business_journey_vote_propose",
        "Vote for a Business Journey suggestion",
        "business_journey_vote_set",
        _object_schema(
            {
                "proposal_id": STRING,
                "active": {
                    "type": "boolean",
                    "default": True,
                    "description": "True votes; false withdraws the account's vote.",
                },
            },
            required=("proposal_id", "active"),
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

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "supply_coverage",
        "Supply coverage",
        "Read customer-assigned, stock-replenishment, received, open and unassigned supplier quantity.",
        "read",
        "Purchasing",
        _object_schema(
            {
                "supplier_commitment_id": OPTIONAL_STRING,
                "customer_commitment_id": OPTIONAL_STRING,
            }
        ),
        _read("supply_coverage"),
    ),
    MCPToolDefinition(
        "stock_blocks",
        "Stock blocks",
        "Read stock held back where it lies: item, location, lot or pallet, the quantity as blocked, what is still open, reason, who blocked it, and each release or scrap since. Blocked stock is excluded from availability, reservation and shipping until released or scrapped.",
        "read",
        "Warehouse",
        _object_schema(
            {
                "item_id": OPTIONAL_STRING,
                "location_id": OPTIONAL_STRING,
                "status": {
                    "type": "string",
                    "enum": ["active", "resolved", "all"],
                },
            }
        ),
        _read("stock_blocks"),
    ),
    MCPToolDefinition(
        "stock_block_propose",
        "Block stock",
        "Prepare blocking a quantity of an item at a location, optionally its lot, pallet or serial, for quality, damage, expiry or inspection. Nothing moves; the review shows what stays available. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {
                "item_id": STRING,
                "location_id": STRING,
                "quantity": DECIMAL_STRING,
                "reason_code": {
                    "type": "string",
                    "enum": ["quality", "damage", "expiry", "inspection"],
                },
                "note": OPTIONAL_STRING,
                "handling_unit_id": OPTIONAL_STRING,
                "lot_id": OPTIONAL_STRING,
                "serial_unit_id": OPTIONAL_STRING,
            },
            required=("item_id", "location_id", "quantity", "reason_code"),
        ),
        _propose("stock_block"),
    ),
    MCPToolDefinition(
        "stock_block_release_propose",
        "Release blocked stock",
        "Prepare releasing a stock block, wholly or partly (quantity), with a reason, so the goods are available again. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {"block_id": STRING, "quantity": OPTIONAL_STRING, "reason": STRING},
            required=("block_id", "reason"),
        ),
        _propose("stock_block_release"),
    ),
    MCPToolDefinition(
        "stock_block_scrap_propose",
        "Scrap blocked stock",
        "Prepare scrapping blocked stock, wholly or partly, with a reason: one adjustment writes it off its location. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {"block_id": STRING, "quantity": OPTIONAL_STRING, "reason": STRING},
            required=("block_id", "reason"),
        ),
        _propose("stock_block_scrap"),
    ),
    MCPToolDefinition(
        "backorders_serve_propose",
        "Serve backorders",
        "Prepare reserving what is available of an item at a location for the customer orders waiting for it. Serving order: the orders the named purchase (supplier_commitment_id, usually the one just received) is assigned to, in assignment order, then the others by due date. Without lines the available quantity is given out in that order; stated lines set the quantity per order. The review lists every waiting order and those on hold. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {
                "item_id": STRING,
                "location_id": STRING,
                "supplier_commitment_id": OPTIONAL_STRING,
                "lines": {
                    "type": "array",
                    "maxItems": 200,
                    "items": _object_schema(
                        {"commitment_id": STRING, "quantity": DECIMAL_STRING},
                        required=("commitment_id", "quantity"),
                    ),
                },
            },
            required=("item_id", "location_id"),
        ),
        _propose("backorders_serve"),
    ),
    MCPToolDefinition(
        "available_to_promise",
        "Available to promise",
        "Read from when and how much of an item can be promised: free stock now (less reservations, blocks and waiting orders no supply covers), then each open purchase by its stated date with what stays free of it after its customer assignments, as a running total naming the purchase.",
        "read",
        "Warehouse",
        _object_schema({"item_id": STRING}, required=("item_id",)),
        _read("available_to_promise"),
    ),
    MCPToolDefinition(
        "company_currency_set_propose",
        "State the company currency",
        "Prepare stating the company currency the books are kept in (a three-letter code; EUR until stated). Every ledger entry carries its amount in it beside its own. It is refused once the company has posted anything. A person confirms.",
        "propose",
        "Finance",
        _object_schema({"currency": STRING}, required=("currency",)),
        _propose("company_currency_set"),
    ),
    MCPToolDefinition(
        "company_currency",
        "Company currency",
        "Read the company currency and whether the company has posted anything yet.",
        "read",
        "Finance",
        _object_schema({}),
        _read("company_currency"),
    ),
    MCPToolDefinition(
        "company_time_zone_set_propose",
        "State the company time zone",
        "Prepare stating the time zone the company's business days are counted in (an IANA name such as Europe/Berlin; UTC until stated). Instants stay in UTC; due dates, overdue days, documents dated by a posting and day filters use the company's local day. A person confirms.",
        "propose",
        "Finance",
        _object_schema({"time_zone": STRING}, required=("time_zone",)),
        _propose("company_time_zone_set"),
    ),
    MCPToolDefinition(
        "company_time_zone",
        "Company time zone",
        "Read the time zone the company's business days are counted in, and whether it was stated.",
        "read",
        "Finance",
        _object_schema({}),
        _read("company_time_zone"),
    ),
    MCPToolDefinition(
        "supplier_item_terms_set_propose",
        "State supplier item terms",
        "Prepare stating a supplier's minimum order quantity and/or order multiple (pack size) for one item (party_id, item_id), both in the item's purchase unit. Purchase reviews then name an order below the minimum or off the multiple, with the next quantity that meets them; orders are never refused. A person confirms.",
        "propose",
        "Purchasing",
        _object_schema(
            {
                "party_id": STRING,
                "item_id": STRING,
                "minimum_quantity": OPTIONAL_STRING,
                "order_multiple": OPTIONAL_STRING,
            },
            required=("party_id", "item_id"),
        ),
        _propose("supplier_item_terms_set"),
    ),
    MCPToolDefinition(
        "supplier_item_terms_remove_propose",
        "Withdraw supplier item terms",
        "Prepare withdrawing a supplier's minimum order quantity and order multiple for one item. A person confirms.",
        "propose",
        "Purchasing",
        _object_schema(
            {"party_id": STRING, "item_id": STRING}, required=("party_id", "item_id")
        ),
        _propose("supplier_item_terms_remove"),
    ),
    MCPToolDefinition(
        "supplier_item_terms",
        "Supplier item terms",
        "Read suppliers' minimum order quantities and order multiples, of one supplier (party_id) or one item (item_id).",
        "read",
        "Purchasing",
        _object_schema({"party_id": OPTIONAL_STRING, "item_id": OPTIONAL_STRING}),
        _read("supplier_item_terms"),
    ),
    MCPToolDefinition(
        "purchase_match",
        "Three-way match of a purchase order",
        "Read per line of one purchase order (document_id) whether it is matched: the quantity in force (ordered, or confirmed by the supplier) received net of returns and billed net of credits at the price agreed last. Otherwise each difference is named (received_short, received_over, billed_short, billed_over, price_differs, units_not_comparable). A cancelled line expects nothing and shows its cancellation charges.",
        "read",
        "Purchasing",
        _object_schema({"document_id": STRING}, required=("document_id",)),
        _read("purchase_match"),
    ),
    MCPToolDefinition(
        "customer_item_number_set_propose",
        "State a customer item number",
        "Prepare stating which of our items a customer's own article number names (party_id, item_id, customer_item_number), with the customer's name for it. Orders by hand, by chat and by file then resolve lines quoting that number for this customer; case and spaces do not matter. The review shows what the number names now. A person confirms.",
        "propose",
        "Orders",
        _object_schema(
            {
                "party_id": STRING,
                "item_id": STRING,
                "customer_item_number": STRING,
                "customer_item_name": OPTIONAL_STRING,
            },
            required=("party_id", "item_id", "customer_item_number"),
        ),
        _propose("customer_item_number_set"),
    ),
    MCPToolDefinition(
        "customer_item_number_remove_propose",
        "Withdraw a customer item number",
        "Prepare withdrawing a customer's article number; lines already ordered by it keep it as stated. A person confirms.",
        "propose",
        "Orders",
        _object_schema(
            {"party_id": STRING, "customer_item_number": STRING},
            required=("party_id", "customer_item_number"),
        ),
        _propose("customer_item_number_remove"),
    ),
    MCPToolDefinition(
        "customer_item_numbers",
        "Customer item numbers",
        "Read a customer's own article numbers (party_id) or the numbers customers use for one of our items (item_id), with the customer's names for them.",
        "read",
        "Orders",
        _object_schema({"party_id": OPTIONAL_STRING, "item_id": OPTIONAL_STRING}),
        _read("customer_item_numbers"),
    ),
    MCPToolDefinition(
        "outbound_delivery_plan_propose",
        "Plan a delivery",
        "Prepare a planned outbound delivery of one customer's open promises before dispatch: per line the commitment_id and the quantity planned (one promise can be split across deliveries up to what is still open). Optionally a recipient (recipient_party_id, e.g. a store of a retail chain; default the customer), the stated address, a booked slot and the staging location goods are picked into. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {
                **OUTBOUND_DELIVERY_FIELDS,
                "customer_id": STRING,
            },
            required=("customer_id", "lines"),
        ),
        _propose("outbound_delivery_plan"),
    ),
    MCPToolDefinition(
        "outbound_delivery_revise_propose",
        "Revise a planned delivery",
        "Prepare a revision of a planned delivery before it ships: any of recipient, address, slot, staging location, note and the full list of lines. Fields left out stay as stated; every statement is kept. Lines with picked goods cannot be removed or planned below what is picked. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {**OUTBOUND_DELIVERY_FIELDS, "outbound_delivery_id": STRING},
            required=("outbound_delivery_id",),
        ),
        _propose("outbound_delivery_revise"),
    ),
    MCPToolDefinition(
        "outbound_delivery_pick_propose",
        "Pick a planned delivery",
        "Prepare picking for a planned delivery: per line the commitment_id, the quantity and optionally from_location_id (default the one location where the promise is reserved). The goods move to the delivery's staging location and the reservation moves with them. More than planned is refused. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {
                "outbound_delivery_id": STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 500,
                    "items": _object_schema(
                        {
                            "commitment_id": STRING,
                            "quantity": DECIMAL_STRING,
                            "from_location_id": OPTIONAL_STRING,
                        },
                        required=("commitment_id", "quantity"),
                    ),
                },
            },
            required=("outbound_delivery_id", "lines"),
        ),
        _propose("outbound_delivery_pick"),
    ),
    MCPToolDefinition(
        "outbound_delivery_put_back_propose",
        "Put back picked goods",
        "Prepare a put-back from a planned delivery's staging location: per line the commitment_id, the quantity and the to_location_id the goods go back to. While the promise is open its reservation moves back with them; goods of a cancelled promise go back as free stock. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {
                "outbound_delivery_id": STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 500,
                    "items": _object_schema(
                        {
                            "commitment_id": STRING,
                            "quantity": DECIMAL_STRING,
                            "to_location_id": STRING,
                        },
                        required=("commitment_id", "quantity", "to_location_id"),
                    ),
                },
            },
            required=("outbound_delivery_id", "lines"),
        ),
        _propose("outbound_delivery_put_back"),
    ),
    MCPToolDefinition(
        "outbound_deliveries",
        "Planned deliveries",
        "Read the planned outbound deliveries, newest first, of one customer (customer_id) or all, optionally only those not shipped (open_only): recipient, address, slot, state and per line planned, picked, to put back and shipped.",
        "read",
        "Warehouse",
        _object_schema(
            {"customer_id": OPTIONAL_STRING, "open_only": {"type": "boolean"}}
        ),
        _read("outbound_deliveries"),
    ),
    MCPToolDefinition(
        "outbound_delivery_detail",
        "Planned delivery",
        "Read one planned delivery: its lines with their pick and put-back movements, every statement oldest first, its shipment, and `dispatch`, the arguments for shipment_dispatch_propose that ship exactly what it carries.",
        "read",
        "Warehouse",
        _object_schema(
            {"outbound_delivery_id": STRING}, required=("outbound_delivery_id",)
        ),
        _read("outbound_delivery_detail"),
    ),
    MCPToolDefinition(
        "stock_count_propose",
        "Count stock",
        "Prepare a count of one location: per line the item, its lot where the item is lot-tracked, the counted quantity and optionally when it was counted (ISO 8601 with its offset, default now). The review shows the book at each counting time, the difference, how much of a loss comes from blocks, and the reservations left uncovered. Confirming records the count and posts every difference as an adjustment; movements after a counting time carry on. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {
                "location_id": STRING,
                "note": OPTIONAL_STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 500,
                    "items": _object_schema(
                        {
                            "item_id": STRING,
                            "lot_id": OPTIONAL_STRING,
                            "counted_quantity": DECIMAL_STRING,
                            "counted_at": OPTIONAL_STRING,
                        },
                        required=("item_id", "counted_quantity"),
                    ),
                },
            },
            required=("location_id", "lines"),
        ),
        _propose("stock_count"),
    ),
    MCPToolDefinition(
        "external_stock_state_propose",
        "State external stock",
        "Prepare recording stock someone outside states, such as a 3PL's stock report or a shop's stock level: per line the item, the location, the stated quantity and optionally when it was there (ISO 8601 with its offset, default now), plus the business partner that reported it (reporter_party_id) where known. Nothing moves: the review shows what Reality's movements hold there at each stated time and the difference, and a difference becomes the finding External stock differs. To take a difference over, book a stock count at that time. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {
                "reporter_party_id": OPTIONAL_STRING,
                "note": OPTIONAL_STRING,
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 500,
                    "items": _object_schema(
                        {
                            "item_id": STRING,
                            "location_id": STRING,
                            "quantity": DECIMAL_STRING,
                            "stated_at": OPTIONAL_STRING,
                        },
                        required=("item_id", "location_id", "quantity"),
                    ),
                },
            },
            required=("lines",),
        ),
        _propose("external_stock_state"),
    ),
    MCPToolDefinition(
        "external_stock",
        "External stock",
        "Read the latest external stock statement per item and location (optionally one item_id or location_id, or only those that differ with differing_only): the stated quantity and time, who stated it, what Reality's movements held there at that time, and the difference.",
        "read",
        "Warehouse",
        _object_schema(
            {
                "item_id": OPTIONAL_STRING,
                "location_id": OPTIONAL_STRING,
                "differing_only": {"type": ["boolean", "null"]},
            }
        ),
        _read("external_stock"),
    ),
    MCPToolDefinition(
        "stock_counts",
        "Stock counts",
        "Read the counts of a location (location_id) or of the company, newest first, with how many lines each has.",
        "read",
        "Warehouse",
        _object_schema({"location_id": OPTIONAL_STRING}),
        _read("stock_counts"),
    ),
    MCPToolDefinition(
        "stock_count_detail",
        "Stock count",
        "Read one count: each line as counted with its counting time, the book then, the difference, and the adjustments and block scraps that posted it.",
        "read",
        "Warehouse",
        _object_schema({"stock_count_id": STRING}, required=("stock_count_id",)),
        _read("stock_count_detail"),
    ),
    MCPToolDefinition(
        "delivery_rule_set_propose",
        "State a delivery rule",
        "Prepare stating how a customer (party_id) or one order (document_id) is delivered: partial_allowed, ship_complete (the whole order in one shipment) or no_backorders (what does not ship with the first shipment is cancelled, not delivered later), with the reason. An order's rule wins over its customer's; lifting ship complete for one order is stating partial_allowed for it. The review shows the rule now and the open orders it governs. A person confirms.",
        "propose",
        "Orders",
        _object_schema(
            {
                "party_id": OPTIONAL_STRING,
                "document_id": OPTIONAL_STRING,
                "rule": {
                    "type": "string",
                    "enum": ["partial_allowed", "ship_complete", "no_backorders"],
                },
                "reason": STRING,
            },
            required=("rule", "reason"),
        ),
        _propose("delivery_rule_set"),
    ),
    MCPToolDefinition(
        "delivery_rules",
        "Delivery rules",
        "Read the delivery rule in force for a customer (party_id) or an order (document_id): the rule, whether it comes from the order, the customer or the default, its reason, and every earlier statement.",
        "read",
        "Orders",
        _object_schema({"party_id": OPTIONAL_STRING, "document_id": OPTIONAL_STRING}),
        _read("delivery_rules"),
    ),
    MCPToolDefinition(
        "reorder_points",
        "Reorder points",
        "Read the reorder points the company stated: per item and location, the stock level it reorders at and the quantity it then orders, in the item's stock unit. Which are reached is the exception class reorder_point_reached.",
        "read",
        "Purchasing",
        _object_schema({"item_id": OPTIONAL_STRING, "location_id": OPTIONAL_STRING}),
        _read("reorder_points"),
    ),
    MCPToolDefinition(
        "reorder_point_set_propose",
        "Set reorder point",
        "Prepare the reorder point and reorder quantity of an item at a location, in the item's stock unit, for confirmation. The review shows the current values beside the new ones; confirming refuses if the point changed meanwhile.",
        "propose",
        "Purchasing",
        _object_schema(
            {
                "item_id": STRING,
                "location_id": STRING,
                "reorder_point": DECIMAL_STRING,
                "reorder_quantity": DECIMAL_STRING,
            },
            required=("item_id", "location_id", "reorder_point", "reorder_quantity"),
        ),
        _propose("reorder_point_set"),
    ),
    MCPToolDefinition(
        "reorder_point_remove_propose",
        "Remove reorder point",
        "Prepare removing the reorder point of an item at a location for confirmation. The review shows the values being removed.",
        "propose",
        "Purchasing",
        _object_schema(
            {"item_id": STRING, "location_id": STRING},
            required=("item_id", "location_id"),
        ),
        _propose("reorder_point_remove"),
    ),
    MCPToolDefinition(
        "kits",
        "Kits",
        "Read the kits of the company, or the kit an item is or is part of (item_id): the components, how many one kit takes, the stated price shares, and per location the free kits on hand, the whole kits the free components build and the component that limits them.",
        "read",
        "Warehouse",
        _object_schema({"item_id": OPTIONAL_STRING}),
        _read("kits"),
    ),
    MCPToolDefinition(
        "kit_split",
        "Kit split",
        "Read how a kit's order or invoice line (document_line_id) splits its stated gross, and its stated net and tax where the line states them, across the components by the kit's stated shares, with the gross per component piece. A kit without stated shares has no split.",
        "read",
        "Warehouse",
        _object_schema({"document_line_id": STRING}, required=("document_line_id",)),
        _read("kit_split"),
    ),
    MCPToolDefinition(
        "kit_define_propose",
        "Define kit",
        "Prepare the components of a kit for confirmation: per component the item, how many one kit takes in the component's stock unit and optionally its share of the kit's price (shares for all or none, adding up to exactly 1). The kit and its components are stocked, untracked items; a component is never a kit. The components are stated once. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {
                "kit_item_id": STRING,
                "components": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 50,
                    "items": _object_schema(
                        {
                            "item_id": STRING,
                            "quantity": DECIMAL_STRING,
                            "share": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9]+(?:\\.[0-9]+)?$",
                            },
                        },
                        required=("item_id", "quantity"),
                    ),
                },
            },
            required=("kit_item_id", "components"),
        ),
        _propose("kit_define"),
    ),
    MCPToolDefinition(
        "kit_assemble_propose",
        "Assemble kits",
        "Prepare assembling whole kits at a location for confirmation: every component leaves the location by its quantity per kit and the kits enter it, all or nothing, optionally at a stated earlier time (ISO 8601 with its offset). The review shows what each component gives and what is free; a component short of free stock refuses the whole assembly. Packing a kit order assembles it this way before it ships. A person confirms.",
        "propose",
        "Warehouse",
        _object_schema(
            {
                "kit_item_id": STRING,
                "location_id": STRING,
                "quantity": DECIMAL_STRING,
                "occurred_at": OPTIONAL_STRING,
                "note": OPTIONAL_STRING,
            },
            required=("kit_item_id", "location_id", "quantity"),
        ),
        _propose("kit_assemble"),
    ),
    MCPToolDefinition(
        "party_merges",
        "Business partner merges",
        "Read the business partner merges of the company, or those one partner took part in (party_id): the duplicate, the survivor it was merged into, the reason and when. A survivor's detail, balances and credit exposure include the history of every partner merged into it.",
        "read",
        "Master data",
        _object_schema({"party_id": OPTIONAL_STRING}),
        _read("party_merges"),
    ),
    MCPToolDefinition(
        "party_merge_propose",
        "Merge duplicate business partner",
        "Prepare merging a duplicate business partner (duplicate_party_id) into the one that survives (surviving_party_id), with a reason, for confirmation. Nothing stated is rewritten: the duplicate's documents, promises and ledger entries keep naming it and read under the survivor; the duplicate becomes inactive, and new shop orders and imports naming it land on the survivor. The survivor must be active and hold every role of the duplicate; merged partners are never merged again; the company's own partner and a partner with an open delivery hold are refused. A person confirms.",
        "propose",
        "Master data",
        _object_schema(
            {
                "duplicate_party_id": STRING,
                "surviving_party_id": STRING,
                "reason": STRING,
            },
            required=("duplicate_party_id", "surviving_party_id", "reason"),
        ),
        _propose("party_merge"),
    ),
    MCPToolDefinition(
        "commitment_substitute_accept_propose",
        "Accept a substitute item",
        "Prepare accepting another item in place of what a purchase line ordered, for confirmation: a successor or substitute the supplier delivers instead. It must be a stocked item in the ordered item's unit, and a reason is required. Receipts of the substitute then name the line and fulfil it; the line keeps what it ordered. A substitute that already arrived as a wrong item is moved onto the line by correcting that receipt. A person confirms.",
        "propose",
        "Purchasing",
        _object_schema(
            {"commitment_id": STRING, "item_id": STRING, "reason": STRING},
            required=("commitment_id", "item_id", "reason"),
        ),
        _propose("commitment_substitute_accept"),
    ),
)

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "movement_explanation",
        "Movement explanation",
        "Explain why a stock movement exists through its shortest authoritative links.",
        "read",
        "Warehouse",
        _object_schema({"movement_id": STRING}, required=("movement_id",)),
        _read("movement_explanation"),
    ),
    MCPToolDefinition(
        "customer_exchange",
        "Customer exchange",
        "Read what a customer exchange replaced, what it sent and what it still settles.",
        "read",
        "Returns",
        _object_schema(
            {
                "exchange_id": OPTIONAL_STRING,
                "return_movement_id": OPTIONAL_STRING,
                "replacement_commitment_id": OPTIONAL_STRING,
            }
        ),
        _read("customer_exchange"),
    ),
    MCPToolDefinition(
        "drop_shipments",
        "Drop shipping",
        "Read a promise's drop shipping: the purchase assigned to it and what the supplier shipped straight to the customer.",
        "read",
        "Shipping",
        _object_schema({"commitment_id": STRING}, required=("commitment_id",)),
        _read("drop_shipments"),
    ),
    MCPToolDefinition(
        "delivery_failure_summary",
        "Failed delivery",
        "Read a failed delivery: what happened, what it reversed and the carrier claim it opened.",
        "read",
        "Shipping",
        _object_schema(
            {
                "delivery_failure_id": OPTIONAL_STRING,
                "shipment_id": OPTIONAL_STRING,
            }
        ),
        _read("delivery_failure_summary"),
    ),
    MCPToolDefinition(
        "return_disposition_summary",
        "Return disposition summary",
        "Read arrived, resolved and unresolved returned-goods quantity by physical outcome.",
        "read",
        "Returns",
        _object_schema(
            {"return_movement_id": STRING}, required=("return_movement_id",)
        ),
        _read("return_disposition_summary"),
    ),
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
        "invoice_credit_context",
        "Invoice credit context",
        "Read eligible customer-invoice positions, remaining quantities, amount capacity and blockers.",
        "read",
        "finance",
        _object_schema({"invoice_id": STRING}, required=("invoice_id",)),
        _read("invoice_credit_context"),
    ),
    MCPToolDefinition(
        "invoice_billable_positions",
        "Billable order positions",
        "Read one party's delivered or received order positions that are not yet fully billed, grouped by order, for one consolidated invoice.",
        "read",
        "finance",
        _object_schema(
            {
                "direction": {"type": "string", "enum": ["sales", "purchase"]},
                "party_id": STRING,
                "currency": STRING,
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            },
            required=("direction", "party_id", "currency"),
        ),
        _read("invoice_billable_positions"),
    ),
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

from reality.tools.finance import DunningRequest, DunningReverseRequest

_DUNNING_CONTEXT_SCHEMA = DunningRequest.model_json_schema()
_DUNNING_CONTEXT_SCHEMA["properties"].pop("expected_revision", None)
_DUNNING_CONTEXT_SCHEMA["required"] = [
    name
    for name in _DUNNING_CONTEXT_SCHEMA.get("required", [])
    if name != "expected_revision"
]

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_dunning_context",
        "Dunning context",
        "Preview one manual notice from currently overdue invoices and return the finance revision required for confirmation.",
        "read",
        "finance",
        _DUNNING_CONTEXT_SCHEMA,
        _read("finance.dunning.context"),
    ),
    MCPToolDefinition(
        "finance_dunning_notices",
        "Dunning notices",
        "List recorded manual dunning notices with fee and reversal trace.",
        "read",
        "finance",
        _object_schema(),
        _read("finance.dunning.notices"),
    ),
    MCPToolDefinition(
        "finance_dunning_notice",
        "Dunning notice",
        "Read one recorded manual dunning notice with fee and reversal trace.",
        "read",
        "finance",
        _object_schema({"notice_id": STRING}, required=("notice_id",)),
        _read("finance.dunning.notice"),
    ),
    MCPToolDefinition(
        "finance_dunning_record_propose",
        "Record dunning notice",
        "Prepare a manual dunning notice and optional exact stated fee for owner confirmation.",
        "propose",
        "finance",
        DunningRequest.model_json_schema(),
        _propose("finance.dunning.record"),
    ),
    MCPToolDefinition(
        "finance_dunning_reverse_propose",
        "Reverse dunning notice",
        "Prepare reversal of one manual dunning notice and any posted fee for owner confirmation.",
        "propose",
        "finance",
        DunningReverseRequest.model_json_schema(),
        _propose("finance.dunning.reverse"),
    ),
)

from reality.tools.finance import (
    CollectionHandoverRequest,
    DunningRunRequest,
    DunningScheduleRequest,
)

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_dunning_schedule",
        "Dunning schedule",
        "Read the company dunning schedule: waiting days and fixed fee for levels 1 to 3, with the finance revision required to change it.",
        "read",
        "finance",
        _object_schema(),
        _read("finance.dunning.schedule"),
    ),
    MCPToolDefinition(
        "finance_dunning_schedule_set_propose",
        "Set dunning schedule",
        "Prepare the company dunning schedule (levels 1, 2 and 3 with waiting days and a fixed fee) for owner confirmation.",
        "propose",
        "finance",
        DunningScheduleRequest.model_json_schema(),
        _propose("finance.dunning.schedule.set"),
    ),
    MCPToolDefinition(
        "finance_dunning_run_context",
        "Dunning run preview",
        "Preview a dunning run for a date over all or selected customers: proposed notices per customer, currency and level with their fee, items ready for collection and items left out with their reason. Records nothing.",
        "read",
        "finance",
        _object_schema(
            {"run_date": STRING, "party_ids": {"type": "array", "items": STRING}},
            required=("run_date",),
        ),
        _read("finance.dunning.run_context"),
    ),
    MCPToolDefinition(
        "finance_dunning_run_propose",
        "Confirm dunning run",
        "Prepare the reviewed dunning run for owner confirmation: the selected items with their proposed level and the schedule the preview used. On confirmation, items paid, reminded or handed over since the review are skipped and named; nothing is sent.",
        "propose",
        "finance",
        DunningRunRequest.model_json_schema(),
        _propose("finance.dunning.run"),
    ),
    MCPToolDefinition(
        "finance_dunning_collection_propose",
        "Hand over to collection",
        "Prepare handing one customer's invoices to collection after a level 3 notice, with a reason, for owner confirmation. The customer gets a delivery hold with the reason collection unless one is active.",
        "propose",
        "finance",
        CollectionHandoverRequest.model_json_schema(),
        _propose("finance.dunning.collection.handover"),
    ),
    MCPToolDefinition(
        "finance_dunning_collection_handovers",
        "Collection handovers",
        "List collection handovers newest first with their invoices and delivery hold.",
        "read",
        "finance",
        _object_schema(),
        _read("finance.dunning.collection_handovers"),
    ),
    MCPToolDefinition(
        "finance_dunning_collection_handover",
        "Collection handover",
        "Read one collection handover with its invoices, the last notice of each and the delivery hold.",
        "read",
        "finance",
        _object_schema({"handover_id": STRING}, required=("handover_id",)),
        _read("finance.dunning.collection_handover"),
    ),
)

from reality.tools.finance import (
    AuthorizationRecordRequest,
    CaptureRecordRequest,
    PaymentReturnRequest,
    PayoutSettleRequest,
)

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "finance_payment_return_propose",
        "Record a returned payment",
        "Prepare a returned direct debit or chargeback of a customer payment for owner confirmation: it reverses the payment so its invoices are open again, keeps the stated reason and reference, and books a stated fee as payment-fee expense or charges it to the customer.",
        "propose",
        "finance",
        PaymentReturnRequest.model_json_schema(),
        _propose("finance.payment.return"),
    ),
    MCPToolDefinition(
        "month_end_billing",
        "Month-end billing",
        "Read the month-end billing lists at one instant: order lines shipped and not invoiced, and order lines invoiced and not shipped, taken from the findings.",
        "read",
        "finance",
        _object_schema({"as_of": OPTIONAL_STRING}, required=()),
        _read("month_end_billing"),
    ),
    MCPToolDefinition(
        "business_logic_discover",
        "Discover live business logic",
        "Find registered business operations, reads and their live source availability. This read inspects deployment vocabulary, not tenant records.",
        "read",
        "catalog",
        _object_schema(
            {
                "query": OPTIONAL_STRING,
                "kind": {
                    "type": "string",
                    "enum": [
                        "command",
                        "tool",
                        "action",
                        "view",
                        "projection",
                        "exception",
                    ],
                },
                "cursor": {"type": "integer", "minimum": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            required=(),
        ),
        _read("business_logic_discover"),
    ),
    MCPToolDefinition(
        "business_logic_explain",
        "Explain live business logic",
        "Read the exact running source as business steps, decision graph and actual test assertions. Cite returned evidence and retain limitations; never infer successful test execution.",
        "read",
        "catalog",
        _object_schema(
            {
                "kind": {
                    "type": "string",
                    "enum": [
                        "command",
                        "tool",
                        "action",
                        "view",
                        "projection",
                        "exception",
                    ],
                },
                "key": STRING,
                "language": OPTIONAL_STRING,
            },
            required=("kind", "key"),
        ),
        _read("business_logic_explain"),
    ),
    MCPToolDefinition(
        "business_logic_source",
        "Inspect live business source",
        "Inspect approved running source using an evidence identity returned by business_logic_explain; arbitrary paths and code execution are unavailable.",
        "read",
        "catalog",
        _object_schema(
            {"kind": STRING, "key": STRING, "evidence_id": STRING},
            required=("kind", "key", "evidence_id"),
        ),
        _read("business_logic_source"),
    ),
    MCPToolDefinition(
        "business_logic_compare",
        "Compare with tested business cases",
        "Compare supplied facts or one authorized party, order or commitment with actual test assumptions. Matching conditions do not prove the outcome; current state and historical evidence remain separate.",
        "read",
        "catalog",
        _object_schema(
            {
                "kind": STRING,
                "key": STRING,
                "scenario_ids": {"type": "array", "maxItems": 20, "items": STRING},
                "facts": {
                    "type": "array",
                    "maxItems": 100,
                    "items": _object_schema(
                        {
                            "name": STRING,
                            "value": {"type": ["string", "boolean", "null"]},
                            "currency": OPTIONAL_STRING,
                            "unit": OPTIONAL_STRING,
                        },
                        required=("name", "value"),
                    ),
                },
                "evidence_digest": OPTIONAL_STRING,
                "record": _object_schema(
                    {
                        "kind": {
                            "type": "string",
                            "enum": ["party", "order", "commitment"],
                        },
                        "id": STRING,
                    },
                    required=("kind", "id"),
                ),
                "language": OPTIONAL_STRING,
            },
            required=("kind", "key"),
        ),
        _read("business_logic_compare"),
    ),
    MCPToolDefinition(
        "credit_exposure",
        "Credit exposure",
        "Read a customer's credit exposure against its limit: open invoices plus open uninvoiced orders minus available credits, with the overdue invoices and payables named.",
        "read",
        "finance",
        _object_schema(
            {"party_id": STRING, "as_of": OPTIONAL_STRING}, required=("party_id",)
        ),
        _read("credit_exposure"),
    ),
    MCPToolDefinition(
        "finance_payment_returns",
        "Returned payments",
        "List returned customer payments (returned direct debits and chargebacks) with reason, fee and the invoices they reopened.",
        "read",
        "finance",
        _object_schema(),
        _read("finance.payment_returns"),
    ),
    MCPToolDefinition(
        "finance_payment_return",
        "Returned payment",
        "Read one returned customer payment with its reason, reference, fee and the invoices it reopened.",
        "read",
        "finance",
        _object_schema({"return_id": STRING}, required=("return_id",)),
        _read("finance.payment_return"),
    ),
    MCPToolDefinition(
        "finance_payout_settle_propose",
        "Settle a payout",
        "Prepare a marketplace, payment-provider or cash-on-delivery payout statement for owner confirmation: every line is booked against the order, invoice or shipment it names on the provider's cash account (payments, refunds against credit notes, chargebacks, fees), the net payout moves to the bank, and lines that lead nowhere stay unbooked and are reported. The lines must add up to the stated net payout.",
        "propose",
        "finance",
        PayoutSettleRequest.model_json_schema(),
        _propose("finance.payout.settle"),
    ),
    MCPToolDefinition(
        "finance_payouts",
        "Payouts",
        "List marketplace and payment-provider payouts with their net amount and the lines nothing booked yet.",
        "read",
        "finance",
        _object_schema(),
        _read("finance.payouts"),
    ),
    MCPToolDefinition(
        "finance_payout",
        "Payout",
        "Read one payout: every stated line with what it booked, the invoices or credit notes it settled, the shipment a tracking number names, or why it stays unbooked.",
        "read",
        "finance",
        _object_schema({"payout_id": STRING}, required=("payout_id",)),
        _read("finance.payout"),
    ),
    MCPToolDefinition(
        "finance_payment_authorization_record_propose",
        "Record a payment authorization",
        "Prepare what a card or wallet provider authorized for one sales order, and until when, for owner confirmation. Captures are recorded against it separately.",
        "propose",
        "finance",
        AuthorizationRecordRequest.model_json_schema(),
        _propose("finance.payment.authorization.record"),
    ),
    MCPToolDefinition(
        "finance_payment_capture_record_propose",
        "Record a payment capture",
        "Prepare an amount captured against a recorded authorization for owner confirmation; never more than is left and not after the authorization lapsed.",
        "propose",
        "finance",
        CaptureRecordRequest.model_json_schema(),
        _propose("finance.payment.capture.record"),
    ),
    MCPToolDefinition(
        "finance_payment_authorizations",
        "Payment authorizations",
        "List payment authorizations, optionally for one order, with what was captured, what is left and whether each is live, expired or captured at the instant.",
        "read",
        "finance",
        _object_schema(
            {"order_document_id": OPTIONAL_STRING, "as_of": OPTIONAL_STRING},
            required=(),
        ),
        _read("finance.payment_authorizations"),
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

from reality.tools.graph import SCHEMAS as GRAPH_SCHEMAS

for _public_name, _application_name, _label in (
    (
        "graph_company_generation_current",
        "graph.company_generation.current",
        "Read current published company cost generation",
    ),
    (
        "graph_captured_reports_list",
        "graph.captured_reports.list",
        "List captured report generations",
    ),
    (
        "graph_contribution_reviews_list",
        "graph.contribution_reviews.list",
        "List confirmed contribution valuations",
    ),
    (
        "graph_inventory_reviews_list",
        "graph.inventory_reviews.list",
        "List confirmed inventory valuations",
    ),
    ("graph_catalog", "graph.catalog", "Discover the business graph"),
    ("graph_templates", "graph.templates", "List report templates"),
    ("graph_ask", "graph.ask", "Ask the business graph"),
    ("graph_format", "graph.format", "Format an analysis query"),
    ("graph_interpret", "graph.interpret", "Interpret an analysis question"),
    ("graph_reports_list", "graph.reports.list", "List my graph reports"),
    ("graph_report_get", "graph.reports.get", "Read my graph report"),
    ("graph_requests_list", "graph.requests.list", "List my requested analyses"),
    ("graph_request_get", "graph.requests.get", "Collect a requested analysis"),
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

from reality.domain.graph_report import GraphReportChange as _GraphReportChange
from reality.tools.graph import (
    GraphRequestedAnalysisRequest as _GraphRequestedAnalysis,
)

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
        "graph_request_propose",
        "Request an analysis",
        "Prepare an analysis question that may be answered by the worker rather than in "
        "this call. Requires trusted authenticated user context; confirm explicitly. "
        "A question the model cannot express is refused here, not minutes later.",
        "propose",
        "analytics",
        _GraphRequestedAnalysis.model_json_schema(),
        _propose("graph.requests.create"),
    ),
)

from reality.domain.cost_query import CostQueryRequest
from reality.domain.cost_records import CostRecordRead
from reality.domain.cost_review_draft import (
    CostReviewDraftRequest,
    CostReviewProposeRequest,
)
from reality.domain.costing import (
    CommercialMatchRead,
    ContributionRead,
    EvidenceRead,
    InventoryRead,
    ReceiptRead,
    ReviewedContributionRead,
)
from reality.tools.costing import change_input_schema

MCP_TOOL_CATALOG += (
    MCPToolDefinition(
        "cost_commercial_match_get",
        "Reviewed partial commercial match",
        "Read one confirmed partial commercial match or exact historical revision from retained revenue and frozen cost evidence.",
        "read",
        "finance",
        CommercialMatchRead.model_json_schema(),
        _read("cost.commercial-match.get"),
    ),
    MCPToolDefinition(
        "cost_review_draft",
        "Draft a cost review",
        "Call this first whenever someone asks to prepare, draft or start a cost review (Kostenprüfung) for an item or an invoice line. Use kind inventory with the item ID, or kind contribution with the invoice line ID. It derives owner, currency, unit, history and every movement from held records and returns the few open inputs to ask the person, by their labels. Never ask the person for IDs or technical fields. Then call cost_review_propose with the same kind and scope_id and the answers.",
        "read",
        "finance",
        CostReviewDraftRequest.model_json_schema(),
        _read("cost.review.draft"),
    ),
    MCPToolDefinition(
        "cost_review_propose",
        "Propose a drafted cost review",
        "Propose the inventory or contribution review cost_review_draft showed, once its open inputs are answered. Pass only kind, scope_id and the answers (for example method fifo); the server drafts again and proposes exactly that, so never copy identifiers or arguments. It only creates a proposal; a company owner confirms it in Decisions.",
        "propose",
        "finance",
        CostReviewProposeRequest.model_json_schema(),
        _cost_review_propose,
    ),
    MCPToolDefinition(
        "company_party_record_propose",
        "Propose the company as its business partner",
        "Propose recording the company itself as a business partner with the role company, named as the company. Use it only when cost_review_draft reports company_party_missing with an action (no choices). It takes no arguments; the server names the partner. It only creates a proposal; a company owner confirms it in Decisions.",
        "propose",
        "finance",
        {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        _company_party_record_propose,
    ),
    MCPToolDefinition(
        "cost_query_get",
        "Read cost query context",
        "Read one admitted cost scope with its exact retained basis and explicit freshness; not a company-wide generation.",
        "read",
        "finance",
        CostQueryRequest.model_json_schema(),
        _read("cost.query.get"),
    ),
    MCPToolDefinition(
        "cost_record_get",
        "Inspect retained cost record",
        "Read exact cost evidence, decision references and bounded retained membership; no current valuation claim.",
        "read",
        "finance",
        CostRecordRead.model_json_schema(),
        _read("cost.record.get"),
    ),
    MCPToolDefinition(
        "cost_contribution_get",
        "Reviewed commercial contribution",
        "Read confirmed DB1 and independently reviewed DB2 for one whole invoice/shipment scope or its exact historical review.",
        "read",
        "finance",
        ReviewedContributionRead.model_json_schema(),
        _read("cost.contribution.get"),
    ),
    MCPToolDefinition(
        "cost_contribution_preview",
        "Current contribution candidate",
        "Read a bounded exact invoice/shipment candidate and known DB1; no confirmed or historical margin.",
        "read",
        "finance",
        ContributionRead.model_json_schema(),
        _read("cost.contribution.preview"),
    ),
    MCPToolDefinition(
        "cost_inventory_get",
        "Reviewed inventory acquisition value",
        "Read bounded confirmed stock and consumption at a retained cutoff; carrying value is unavailable.",
        "read",
        "finance",
        InventoryRead.model_json_schema(),
        _read("cost.inventory.get"),
    ),
    MCPToolDefinition(
        "cost_receipt_get",
        "Receipt acquisition costs",
        "Read known costs, reviewed completeness and an exact retained manifest. Missing costs stay unknown.",
        "read",
        "finance",
        ReceiptRead.model_json_schema(),
        _read("cost.receipt.get"),
    ),
    MCPToolDefinition(
        "cost_evidence_get",
        "Received cost evidence",
        "Read stated supplier invoice or credit amounts and their evidence fingerprint without writing.",
        "read",
        "finance",
        EvidenceRead.model_json_schema(),
        _read("cost.evidence.get"),
    ),
    MCPToolDefinition(
        "cost_change_propose",
        "Review cost and contribution decision",
        "Prepare explicit received-cost attribution, replacement, withdrawal, inventory scope or whole-line contribution review. For inventory_review and contribution_review use cost_review_draft and cost_review_propose instead; they need no identifiers or arguments to be copied. This only creates a proposal; it never executes. A company owner then confirms it in Decisions.",
        "propose",
        "finance",
        change_input_schema(),
        _propose("cost.change"),
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


def proposal_bindings() -> dict[str, str]:
    """Return the public proposal name to canonical application-tool binding."""
    return {
        definition.name: str(definition.handler.application_name)  # type: ignore[attr-defined]
        for definition in tool_definitions(access=("propose",))
    }


def dispatch_tool(
    session: Session,
    tenant_id: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    *,
    allowed_access: Iterable[ToolAccess] | None = None,
    principal: MCPPrincipal | None = None,
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
    if principal is not None:
        if principal.tenant_id != tenant_id:
            raise PermissionError(
                "MCP principal tenant does not match dispatch tenant."
            )
        if not principal.permits(tool_name):
            raise PermissionError(f"MCP principal does not allow tool: {tool_name}")
        with mcp_principal_context(principal):
            return definition.handler(session, tenant_id, arguments or {})
    return definition.handler(session, tenant_id, arguments or {})


def dispatch_mcp_tool(
    session: Session,
    principal: MCPPrincipal,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    """Dispatch one MCP call using only server-verified principal authority."""
    definition = MCP_TOOL_REGISTRY.get(tool_name)
    if definition is None:
        raise ValueError(f"Unknown MCP tool: {tool_name}")
    if not principal.permits(tool_name):
        raise PermissionError(f"MCP principal does not allow tool: {tool_name}")
    required_scope = f"reality:{definition.access}"
    if (
        principal.authentication_kind == "interactive"
        and required_scope not in principal.scopes
    ):
        raise PermissionError(
            f"MCP principal does not allow {definition.access} access."
        )
    return dispatch_tool(
        session,
        principal.tenant_id,
        tool_name,
        arguments,
        allowed_access=(definition.access,),
        principal=principal,
    )


def schema_argument_names(
    tool_name: str, arguments: dict[str, Any] | None
) -> list[str]:
    """The argument names a call used that its tool declares (spec 266 FR-003).

    Only declared names can reach the engine room, so a caller cannot smuggle
    text into it by inventing a key.
    """
    definition = MCP_TOOL_REGISTRY.get(tool_name)
    if definition is None or not arguments:
        return []
    declared = definition.input_schema.get("properties", {})
    # The MCP server fills in every default; only what the caller chose counts.
    return sorted(
        name
        for name, value in arguments.items()
        if name in declared
        and value is not None
        and value != declared[name].get("default")
    )


def schema_choices(tool_name: str, arguments: dict[str, Any] | None) -> dict[str, str]:
    """Arguments whose value is one of the tool's declared enum values (spec 266).

    A choice from a closed list is vocabulary, not content — `family: party` says
    what was asked without carrying anything a caller wrote. Free text never
    qualifies, and neither does a default the server filled in.
    """
    definition = MCP_TOOL_REGISTRY.get(tool_name)
    if definition is None or not arguments:
        return {}
    declared = definition.input_schema.get("properties", {})
    choices: dict[str, str] = {}
    for name, value in sorted(arguments.items()):
        spec = declared.get(name)
        if (
            isinstance(spec, dict)
            and isinstance(value, str)
            and value in (spec.get("enum") or ())
            and value != spec.get("default")
            and len(value) <= 64
        ):
            choices[name] = value
    return dict(list(choices.items())[:8])


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
    from reality.services.analytics.reports import CALLER

    return CALLER.get()
