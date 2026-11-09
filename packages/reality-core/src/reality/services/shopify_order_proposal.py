"""Spec391: retained exact proposal only; no order application entrypoint."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, Item, Location, Party, SourceRecord
from reality.domain.intake import ReferenceState, canonical_json, content_digest
from reality.domain.shopify_intake_preflight import PreflightInput
from reality.domain.shopify_order_meaning import build_explicit_order_plan
from reality.domain.shopify_order_proposal import (
    ACTION_TYPE,
    MAX_PLAN_BYTES,
    MAX_WIRE_BYTES,
    PURPOSE,
    OrderPrepareInput,
    OrderProposalReview,
    OrderReviewInput,
    StoredOrderProposal,
)
from reality.integrations.shopify.graphql import project_order
from reality.services import core
from reality.services.intake_reference_state import mapped_state
from reality.services.shopify_buyer_mapping import (
    _submitter,
    get_verified_buyer_mapping,
)
from reality.services.shopify_intake_preflight import _basis, _reference_check
from reality.services.shopify_source_reads import accepted_order_exists

_READ_FAILURES = (
    getattr(core, "RealityError", core.InvalidOperation),
    core.InvalidOperation,
    core.NotFound,
    ValueError,
    TypeError,
    ValidationError,
)


def _unavailable():
    if hasattr(core.InvalidOperation, "_init_refusal"):
        return core.InvalidOperation(code="shopify_order_proposal_unavailable")
    return core.InvalidOperation(
        "This exact Shopify order proposal is unavailable or needs changed selections. No business effects are accepted by preparation."
    )


def _item_digest(item):
    return content_digest(
        {
            "purpose": "shopify_intake_reference/1",
            "kind": "item",
            "state": {
                "record_id": item.id,
                "label": item.name,
                "sku": item.sku,
                "is_active": item.is_active,
                "unit": item.unit,
                "item_type": item.item_type,
                "tracking_type": item.tracking_type,
                "source_record_id": item.source_record_id,
            },
        }
    )


def _resolve(
    session: Session, tenant_id: str, request: OrderPrepareInput
) -> StoredOrderProposal:
    binding, raw, _, _ = _basis(
        session,
        tenant_id,
        PreflightInput.model_validate(
            {
                key: getattr(request, key)
                for key in [
                    "source_record_id",
                    "import_job_id",
                    "source_hash",
                    "source_version",
                ]
            }
        ),
    )
    buyer = get_verified_buyer_mapping(
        session, tenant_id, request.source_record_id, request.import_job_id
    )
    if (
        buyer is None
        or not all(buyer["current_basis"].values())
        or buyer["review_id"] != request.buyer_review_id
        or buyer["review_digest"] != request.buyer_review_digest
    ):
        raise _unavailable()
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.id == request.source_record_id,
        )
    )
    if source is None or accepted_order_exists(session, tenant_id, source):
        raise _unavailable()
    received = project_order(raw, binding["external_id"])
    selected = {line.source_line_id: line for line in request.lines}
    if len(received["line_items"]) > 100 or set(selected) != {
        line["id"] for line in received["line_items"]
    }:
        raise _unavailable()
    ships = any(line["requires_shipping"] for line in received["line_items"])
    company = _reference_check(session, tenant_id, "company", request.company_party_id)
    location = _reference_check(
        session, tenant_id, "location", request.location_id, ships=ships
    )
    if company["status"] != "matched" or location["status"] != "matched":
        raise _unavailable()
    if (
        request.expected_company_digest is not None
        and request.expected_company_digest != company["digest"]
        or request.expected_location_digest is not None
        and request.expected_location_digest != location["digest"]
    ):
        raise _unavailable()
    references = {}
    for kind, model, record_id in [
        ("party", Party, request.company_party_id),
        ("party", Party, buyer["customer"]["party_id"]),
        ("location", Location, request.location_id),
    ]:
        record = session.scalar(
            select(model)
            .where(model.tenant_id == tenant_id, model.id == record_id)
            .execution_options(populate_existing=True)
        )
        if record is None:
            raise _unavailable()
        references[(kind, record.id)] = ReferenceState(
            record_type=kind, record_id=record.id, digest=mapped_state(record)
        )
    lines = []
    for line in received["line_items"]:
        choice = selected[line["id"]]
        item = session.scalar(
            select(Item)
            .where(Item.tenant_id == tenant_id, Item.id == choice.item_id)
            .execution_options(populate_existing=True)
        )
        if (
            item is None
            or not item.is_active
            or item.unit != choice.stock_unit
            or item.item_type not in {"stocked", "service", "charge"}
        ):
            raise _unavailable()
        item_digest = _item_digest(item)
        if (
            choice.expected_item_digest is not None
            and choice.expected_item_digest != item_digest
        ):
            raise _unavailable()
        references[("item", item.id)] = ReferenceState(
            record_type="item", record_id=item.id, digest=mapped_state(item)
        )
        lines.append(
            {
                "source_line_id": line["id"],
                "source_sku": line["sku"],
                "item_id": item.id,
                "item_sku": item.sku,
                "item_label": item.name,
                "item_type": item.item_type,
                "item_digest": item_digest,
                "stock_unit": item.unit,
                "quantity_semantics": choice.quantity_semantics,
            }
        )
    bundle = {
        "state": "proposed",
        "customer_id": buyer["customer"]["party_id"],
        "company": company,
        "location": location,
        "lines": lines,
    }
    plan, prices = build_explicit_order_plan(
        binding, raw, bundle, tuple(references[key] for key in sorted(references))
    )
    return StoredOrderProposal(
        purpose=PURPOSE,
        request=request,
        source_binding=binding,
        buyer_mapping=buyer,
        mapping_bundle=bundle,
        plan=plan,
        source_price_evidence=prices,
    )


def _view(proposal_id: str, sealed: StoredOrderProposal, *, stale: bool = False):
    projection = sealed.plan.model_dump(mode="json")
    for effect in projection["effects"]:
        if effect["operation"] == "document":
            effect["arguments"].pop("_source_line_payloads", None)
    result = {
        "purpose": PURPOSE,
        "proposal_id": proposal_id,
        "status": "stale" if stale else "proposed",
        "request_id": sealed.request.request_id,
        "request_digest": content_digest(sealed.request.model_dump()),
        "review_digest": content_digest(sealed.model_dump(mode="json")),
        "source_binding": sealed.source_binding.model_dump(),
        "buyer_mapping": sealed.buyer_mapping.model_dump(),
        "mapping_bundle": sealed.mapping_bundle,
        "plan_digest": sealed.plan.review_digest(),
        "review_projection": projection,
        "projection_scope": "all_business_effect_arguments_excluding_original_line_payloads",
        "source_price_evidence": sealed.source_price_evidence,
        "holds": list(sealed.plan.issues),
        "application_allowed": False,
        "generic_confirmation_allowed": False,
        "business_effects_accepted": False,
        "original_source_unchanged": True,
        "import_job_input_unchanged": True,
    }
    if len(canonical_json(result).encode("utf-8")) > MAX_WIRE_BYTES:
        raise _unavailable()
    return OrderProposalReview.model_validate(result).model_dump(mode="json")


def _retained(session, tenant_id, proposal_id):
    row = session.scalar(
        select(ChangeProposal)
        .where(ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id)
        .execution_options(populate_existing=True)
    )
    if row is None or row.type != ACTION_TYPE or row.status != "proposed":
        raise _unavailable()
    try:
        held = json.loads(row.input)
        sealed = StoredOrderProposal.model_validate(held["proposal"])
        if sealed.source_binding.tenant_id != tenant_id or held[
            "review_digest"
        ] != content_digest(sealed.model_dump(mode="json")):
            raise ValueError("retained_proposal_changed")
    except (ValueError, TypeError, KeyError, ValidationError) as error:
        raise _unavailable() from error
    return row, sealed


def prepare_shopify_order(session: Session, tenant_id: str, **arguments: Any):
    """
    BUSINESS PURPOSE:
    Retain explicit source mapping and prospective order meaning for one exact later review, without acceptance.

    BUSINESS RULE shopify_order_proposal.prepare:
    Require exact current source/buyer/explicit master and quantity selections, freeze fresh references and unknown financial evidence, and idempotently retain only a non-executable proposed Action while original source and job input remain unchanged.
    """
    # reality-rule: shopify_order_proposal.prepare
    try:
        request = OrderPrepareInput.model_validate(arguments)
    except (ValueError, TypeError, ValidationError) as error:
        raise _unavailable() from error
    if (
        session.new
        or session.deleted
        or any(session.is_modified(row) for row in session.dirty)
    ):
        raise _unavailable()
    _submitter(session, tenant_id, "shopify_source_order_prepare")
    proposal_id = (
        "act_sop_"
        + hashlib.sha256((tenant_id + "\0" + request.request_id).encode()).hexdigest()[
            :32
        ]
    )
    with session.no_autoflush:
        existing = session.scalar(
            select(ChangeProposal.id).where(
                ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id
            )
        )
        if existing:
            _, held = _retained(session, tenant_id, proposal_id)
            if held.request != request:
                raise _unavailable()
            result = review_shopify_order(session, tenant_id, proposal_id=proposal_id)
            session.commit()
            return result
        try:
            sealed = _resolve(session, tenant_id, request)
        except (ValueError, TypeError, ValidationError) as error:
            raise _unavailable() from error
        result = _view(proposal_id, sealed)
        if (
            len(canonical_json(sealed.model_dump(mode="json")).encode("utf-8"))
            > MAX_PLAN_BYTES
        ):
            raise _unavailable()
        if _resolve(session, tenant_id, request) != sealed:
            raise _unavailable()
    held = {
        "proposal": sealed.model_dump(mode="json"),
        "review_digest": result["review_digest"],
    }
    try:
        with session.begin_nested():
            session.add(
                ChangeProposal(
                    id=proposal_id,
                    tenant_id=tenant_id,
                    type=ACTION_TYPE,
                    actor_type="agent",
                    status="proposed",
                    input=canonical_json(held),
                    output=canonical_json(result),
                )
            )
            session.flush()
    except IntegrityError:
        _, retained = _retained(session, tenant_id, proposal_id)
        if retained.request != request:
            raise _unavailable()
    session.commit()
    return review_shopify_order(session, tenant_id, proposal_id=proposal_id)


def review_shopify_order(session: Session, tenant_id: str, **arguments: Any):
    """
    BUSINESS PURPOSE:
    Read exact retained proposal and mark changed basis stale without accepting or refreshing it.

    BUSINESS RULE shopify_order_proposal.review:
    Validate tenant, dedicated type and sealed meaning, compare current source/buyer/references without rewriting historical interpretation, and expose all prospective business arguments with original evidence links and no application permission.
    """
    # reality-rule: shopify_order_proposal.review
    try:
        value = OrderReviewInput.model_validate(arguments)
    except (ValueError, TypeError, ValidationError) as error:
        raise _unavailable() from error
    with session.no_autoflush:
        _, sealed = _retained(session, tenant_id, value.proposal_id)
        try:
            current = _resolve(session, tenant_id, sealed.request)
            stale = (
                current != sealed
                or _resolve(session, tenant_id, sealed.request) != current
            )
        except _READ_FAILURES:
            stale = True
        return _view(value.proposal_id, sealed, stale=stale)
