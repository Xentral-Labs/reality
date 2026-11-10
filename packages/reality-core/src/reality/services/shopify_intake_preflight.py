"""Spec390: exact retained diagnosis through shared reads, with no preparation."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    ImportJob,
    Item,
    Location,
    Party,
    PartyRole,
    SourceRecord,
    SourceStream,
)
from reality.domain.shopify_buyer_mapping import digest
from reality.domain.shopify_intake_preflight import (
    NOT_ASSESSED,
    PURPOSE,
    PreflightInput,
    PreflightReport,
    SourceBinding,
    semantic_digest,
)
from reality.integrations.shopify.graphql import GraphQLOrderNeedsReview, project_order
from reality.services import core
from reality.services.shopify_buyer_mapping import get_verified_buyer_mapping
from reality.services.shopify_source_reads import (
    accepted_order_exists as _accepted_order_exists,
)


def _unavailable():
    if hasattr(core.InvalidOperation, "_init_refusal"):
        return core.InvalidOperation(code="shopify_intake_preflight_unavailable")
    return core.InvalidOperation(
        "This exact retained Shopify source cannot provide a current bounded intake preflight. Read the source and existing mappings again; this read does not prepare or accept business effects."
    )


def _basis(session: Session, tenant_id: str, value: PreflightInput):
    source = session.scalar(
        select(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.id == value.source_record_id,
        )
        .execution_options(populate_existing=True)
    )
    job = session.scalar(
        select(ImportJob)
        .where(ImportJob.tenant_id == tenant_id, ImportJob.id == value.import_job_id)
        .execution_options(populate_existing=True)
    )
    if (
        source is None
        or job is None
        or source.source_system != "shopify"
        or source.source_type != "order_graphql"
        or source.source_artifact_id is not None
        or source.payload_hash != value.source_hash
        or source.version != value.source_version
        or job.source_record_id != source.id
        or job.status != "review_required"
        or len(source.payload.encode("utf-8")) > 1_000_000
    ):
        raise _unavailable()
    stream = session.scalar(
        select(SourceStream)
        .where(
            SourceStream.tenant_id == tenant_id,
            SourceStream.source_system == "shopify",
            SourceStream.source_type == "order_graphql",
            SourceStream.external_id == source.external_id,
        )
        .execution_options(populate_existing=True)
    )
    if stream is None or stream.current_source_record_id != source.id:
        raise _unavailable()
    try:
        raw = json.loads(source.payload)
        context = json.loads(job.input)
        if not isinstance(raw, dict) or not isinstance(context, dict):
            raise TypeError("original_object_required")
        acquisition = context.get("acquisition")
        if not isinstance(acquisition, dict):
            raise TypeError("acquisition_object_required")
        name = raw.get("name")
        binding = SourceBinding.model_validate(
            {
                "tenant_id": tenant_id,
                **value.model_dump(),
                "external_id": source.external_id,
                "order_id": raw.get("id"),
                "order_label": name
                if isinstance(name, str) and name
                else source.external_id,
                "shop": acquisition.get("shop"),
                "query_digest": acquisition.get("query_digest"),
            }
        )
        nodes = raw.get("lineItems", {}).get("nodes")
        if not isinstance(nodes, list) or len(nodes) > 500:
            raise ValueError("bounded_selected_lines_required")
    except (ValueError, TypeError, AttributeError, ValidationError) as error:
        raise _unavailable() from error
    return binding.model_dump(), raw, context, len(nodes)


def _reference_check(
    session: Session, tenant_id: str, kind: str, record_id: Any, *, ships: bool = False
):
    empty = {"status": "missing", "record_id": None, "label": None, "digest": None}
    if record_id is None or record_id == "":
        return empty
    if not isinstance(record_id, str) or len(record_id) > 200:
        raise _unavailable()
    model = Party if kind == "company" else Location
    record = session.scalar(
        select(model)
        .where(model.tenant_id == tenant_id, model.id == record_id)
        .execution_options(populate_existing=True)
    )
    if record is None:
        return {**empty, "status": "not_found", "record_id": record_id}
    state = {
        "record_id": record.id,
        "label": record.name,
        "is_active": record.is_active,
        "source_record_id": record.source_record_id,
    }
    roles = []
    if kind == "company":
        roles = list(
            session.scalars(
                select(PartyRole.role)
                .where(
                    PartyRole.tenant_id == tenant_id, PartyRole.party_id == record.id
                )
                .order_by(PartyRole.role)
            )
        )
        state.update(type=record.type, roles=roles)
    else:
        state.update(
            type=record.type,
            allows_stock=record.allows_stock,
            parent_location_id=record.parent_location_id,
        )
    state = digest(
        {"purpose": "shopify_intake_reference/1", "kind": kind, "state": state}
    )
    status = "matched"
    if not record.is_active:
        status = "inactive"
    elif kind == "company" and "company" not in roles:
        status = "role_mismatch"
    elif kind == "location" and ships and not record.allows_stock:
        status = "stock_not_allowed"
    return {
        "status": status,
        "record_id": record.id,
        "label": record.name,
        "digest": state,
    }


def _item_check(session: Session, tenant_id: str, sku: str):
    empty = {
        "item_status": "missing_sku",
        "item_id": None,
        "item_digest": None,
        "stock_unit": None,
    }
    if not sku:
        return empty
    rows = list(
        session.scalars(
            select(Item)
            .where(
                Item.tenant_id == tenant_id, Item.sku == sku, Item.is_active.is_(True)
            )
            .order_by(Item.id)
            .limit(2)
            .execution_options(populate_existing=True)
        )
    )
    if len(rows) > 1:
        return {**empty, "item_status": "ambiguous"}
    if not rows:
        exists = session.scalar(
            select(Item.id).where(Item.tenant_id == tenant_id, Item.sku == sku).limit(1)
        )
        return {**empty, "item_status": "inactive" if exists else "not_found"}
    item = rows[0]
    return {
        "item_status": "matched",
        "item_id": item.id,
        "item_digest": digest(
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
        ),
        "stock_unit": item.unit,
    }


def shopify_source_intake_preflight(
    session: Session, tenant_id: str, **arguments: Any
) -> dict[str, Any]:
    """
    BUSINESS PURPOSE:
    Explain missing existing mappings and selected interpretation evidence for one exact retained Shopify source without preparation or acceptance.

    BUSINESS RULE shopify_intake_preflight.exact_read:
    Validate current tenant/source/job/hash/version and verified buyer, observe only existing retained references and bounded exact active SKU identities, preserve unknown units and source values, and issue no persistent write or effect.
    """
    # reality-rule: shopify_intake_preflight.exact_read
    try:
        value = PreflightInput.model_validate(arguments)
    except (ValueError, TypeError, ValidationError) as error:
        raise _unavailable() from error
    with session.no_autoflush:
        binding, raw, context, line_count = _basis(session, tenant_id, value)
        mapping = get_verified_buyer_mapping(
            session, tenant_id, value.source_record_id, value.import_job_id
        )
        buyer_status = (
            "missing"
            if mapping is None
            else ("verified" if all(mapping["current_basis"].values()) else "stale")
        )
        try:
            projection = project_order(raw, binding["external_id"])
        except GraphQLOrderNeedsReview:
            projection = None
        source = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == value.source_record_id,
            )
        )
        if source is None:
            raise _unavailable()
        accepted_order = bool(_accepted_order_exists(session, tenant_id, source))
        if accepted_order:
            projection = None
        ships = bool(
            projection
            and any(line["requires_shipping"] for line in projection["line_items"])
        )
        company = _reference_check(
            session, tenant_id, "company", context.get("company_party_id")
        )
        location = _reference_check(
            session, tenant_id, "location", context.get("location_id"), ships=ships
        )
        lines = []
        cached = {}
        if projection is not None:
            for line in projection["line_items"][:100]:
                sku = line["sku"]
                if sku not in cached:
                    cached[sku] = _item_check(session, tenant_id, sku)
                lines.append(
                    {
                        "source_line_id": line["id"],
                        "sku": sku,
                        "quantity": str(line["quantity"]),
                        **cached[sku],
                        "source_unit": None,
                        "unit_status": "not_interpreted",
                    }
                )
        complete = projection is not None and len(lines) == line_count
        blockers = []

        def block(code, count=0):
            blockers.append({"code": code, "affected_line_count": count})

        if projection is None:
            block("source_requires_review")
        if buyer_status != "verified":
            block(
                "buyer_mapping_missing"
                if buyer_status == "missing"
                else "buyer_mapping_stale"
            )
        for kind, reference in [("company", company), ("location", location)]:
            if reference["status"] == "missing":
                block(f"{kind}_mapping_missing")
            elif reference["status"] == "stock_not_allowed":
                block("shipping_location_not_allowed")
            elif reference["status"] != "matched":
                block(f"{kind}_reference_unavailable")
        counts = Counter(line["item_status"] for line in lines)
        for status, code in [
            ("missing_sku", "sku_missing"),
            ("not_found", "item_not_found"),
            ("inactive", "item_inactive"),
            ("ambiguous", "item_ambiguous"),
        ]:
            if counts[status]:
                block(code, counts[status])
        if projection is not None:
            block("unit_mapping_not_proved", line_count)
        if not complete:
            block("line_coverage_incomplete", line_count - len(lines))
        report = {
            "purpose": PURPOSE,
            "source_binding": binding,
            "observed_at": core.now().isoformat(),
            "buyer": {"status": buyer_status, "mapping": mapping},
            "company": company,
            "location": location,
            "source_interpretation": {
                "status": "supported" if projection is not None else "requires_review",
                "reason_codes": []
                if projection is not None
                else ["unsupported_selected_first_order"],
            },
            "coverage": {
                "scope": "retained_selected_entity",
                "line_count": line_count,
                "returned_line_count": len(lines),
                "lines_complete": complete,
            },
            "lines": lines,
            "financial": {
                "currency": projection["currency"] if projection else None,
                "order_total": projection["total_price"] if projection else None,
                "line_totals": "not_interpreted",
                "payment": "not_assessed",
                "credit_exposure": "not_assessed",
                "settlement": "not_assessed",
            },
            "blockers": blockers,
            "review_issues": [
                {
                    "code": "line_totals_not_interpreted",
                    "affected_line_count": line_count,
                },
                {"code": "delivery_date_not_interpreted", "affected_line_count": 0},
            ],
            "not_assessed": list(NOT_ASSESSED),
            "preparation_performed": False,
            "business_effects_accepted": False,
            "original_source_unchanged": True,
            "import_job_input_unchanged": True,
        }
        # Recheck the exact mutable source selection and buyer after the other reads.
        final_binding, _, final_context, _ = _basis(session, tenant_id, value)
        final_mapping = get_verified_buyer_mapping(
            session, tenant_id, value.source_record_id, value.import_job_id
        )
        if (
            final_binding != binding
            or final_context != context
            or final_mapping != mapping
            or bool(_accepted_order_exists(session, tenant_id, source))
            != accepted_order
            or _reference_check(
                session, tenant_id, "company", context.get("company_party_id")
            )
            != company
            or _reference_check(
                session, tenant_id, "location", context.get("location_id"), ships=ships
            )
            != location
            or any(
                _item_check(session, tenant_id, sku) != state
                for sku, state in cached.items()
            )
        ):
            raise _unavailable()
        report["observed_at"] = core.now().isoformat()
        report["output_digest"] = semantic_digest(report)
        try:
            return PreflightReport.model_validate(report).model_dump()
        except (ValueError, TypeError, ValidationError) as error:
            raise _unavailable() from error
