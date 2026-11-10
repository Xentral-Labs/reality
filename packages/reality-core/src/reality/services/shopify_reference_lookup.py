"""Spec393: canonical current-reference reads, never mapping selection."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from reality.db.core import Item, Location, Party, PartyRole, now
from reality.domain.shopify_buyer_mapping import canonical, digest
from reality.domain.shopify_intake_preflight import PreflightInput
from reality.domain.shopify_reference_lookup import (
    MAX_WIRE_BYTES,
    PURPOSE,
    ReferenceLookupInput,
    ReferenceLookupResult,
)
from reality.integrations.shopify.graphql import project_order
from reality.services import core
from reality.services.shopify_intake_preflight import _basis, _reference_check
from reality.services.shopify_order_proposal import _item_digest


def _unavailable():
    return core.InvalidOperation(code="shopify_reference_lookup_unavailable")


def _candidates(
    session: Session, tenant_id: str, value: ReferenceLookupInput, projection
):
    model = {"company": Party, "location": Location, "item": Item}[value.family]
    statement = select(model).where(
        model.tenant_id == tenant_id, model.is_active.is_(True)
    )
    ships = any(line["requires_shipping"] for line in projection["line_items"])
    if value.family == "company":
        statement = statement.where(
            select(PartyRole.id)
            .where(
                PartyRole.tenant_id == tenant_id,
                PartyRole.party_id == Party.id,
                PartyRole.role == "company",
            )
            .exists()
        )
    elif value.family == "location" and ships:
        statement = statement.where(Location.allows_stock.is_(True))
    elif value.family == "item":
        statement = statement.where(
            Item.item_type.in_(["stocked", "service", "charge"])
        )
    if value.record_id is not None:
        statement = statement.where(model.id == value.record_id)
    elif value.query:
        text = model.name.icontains(value.query, autoescape=True)
        statement = statement.where(
            or_(text, Item.sku.icontains(value.query, autoescape=True))
            if value.family == "item"
            else text
        )
    rows = list(
        session.scalars(
            statement.order_by(model.id)
            .limit(21)
            .execution_options(populate_existing=True)
        )
    )
    records = []
    for record in rows:
        roles = {"kind": "unknown"}
        stock_unit = None
        source_lines = []
        if value.family == "item":
            current_digest = _item_digest(record)
            stock_unit = record.unit or None
            source_lines = [
                line["id"]
                for line in projection["line_items"]
                if line["sku"] and line["sku"] == record.sku
            ]
        else:
            checked = _reference_check(
                session, tenant_id, value.family, record.id, ships=ships
            )
            if checked["status"] != "matched":
                raise _unavailable()
            current_digest = checked["digest"]
            if value.family == "company":
                roles = {
                    "kind": "known",
                    "values": list(
                        session.scalars(
                            select(PartyRole.role)
                            .where(
                                PartyRole.tenant_id == tenant_id,
                                PartyRole.party_id == record.id,
                            )
                            .order_by(PartyRole.role)
                        )
                    ),
                }
        records.append(
            {
                "id": record.id,
                "label": record.name,
                "digest": current_digest,
                "active": True,
                "roles": roles,
                "stockUnit": stock_unit,
                "sourceLineIds": source_lines,
            }
        )
    return {"records": records[:20], "hasMore": len(rows) > 20}, records


def shopify_source_reference_lookup(session: Session, tenant_id: str, **arguments: Any):
    """
    BUSINESS PURPOSE:
    Observe bounded existing company, location or item candidates for one exact held Shopify source without choosing mappings.

    BUSINESS RULE shopify_reference_lookup.current_read:
    Validate the tenant and exact immutable held-source basis, preserve explicit company roles and observed units, recheck bounded canonical reference fingerprints, and never prepare or accept a business effect.
    """
    # reality-rule: shopify_reference_lookup.current_read
    try:
        value = ReferenceLookupInput.model_validate(arguments)
        basis = PreflightInput.model_validate(
            value.model_dump(
                include={
                    "source_record_id",
                    "import_job_id",
                    "source_hash",
                    "source_version",
                }
            )
        )
        with session.no_autoflush:
            binding, raw, context, _ = _basis(session, tenant_id, basis)
            projection = project_order(raw, binding["external_id"])
            if len(projection["line_items"]) > 100:
                raise _unavailable()
            result, fingerprints = _candidates(session, tenant_id, value, projection)
            checked, fresh_fingerprints = _candidates(
                session, tenant_id, value, projection
            )
            fresh_binding, fresh_raw, fresh_context, _ = _basis(
                session, tenant_id, basis
            )
            if (
                digest(fingerprints) != digest(fresh_fingerprints)
                or result != checked
                or digest([binding, raw, context])
                != digest([fresh_binding, fresh_raw, fresh_context])
            ):
                raise _unavailable()
            response = ReferenceLookupResult.model_validate(
                {
                    "purpose": PURPOSE,
                    "source_binding": binding,
                    "observed_at": now().isoformat(),
                    **result,
                }
            ).model_dump()
            if len(canonical(response).encode("utf-8")) > MAX_WIRE_BYTES:
                raise _unavailable()
            return response
    except (ValueError, TypeError, AttributeError, ValidationError) as error:
        raise _unavailable() from error
