"""Kits: a stocked item made of components, assembled where it is packed (spec 333).

A kit is a stocked item with a stated bill of materials: the components, how
many of each one kit takes in the component's stock unit, and optionally the
share of the kit's price each component carries. The components are stated
once, through a reviewed definition; a different set is a different kit item.

Kit units come only from an assembly: one reviewed statement at a location
that consumes every component (``assembly_input``) and produces the kits
(``assembly_output``), all or nothing. Packing a kit order assembles it, and
assembling ahead of demand is the same action; the kit then ships, returns
and is invoiced as itself, so every promise, reservation and invoice keeps
reading goods on its own item.

What a location can build and how a kit line splits are read each time from
the components, stock, reservations and blocks, and the line's stated
amounts; nothing about either is stored.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal
from decimal import InvalidOperation as DecimalError
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    DocumentLine,
    Item,
    KitComponent,
    Location,
    Movement,
    now,
    uid,
)
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _require_business_mutation,
    _tenant_record,
    active_reserved,
    blocked_quantity,
    emit_business_event,
    get_tenant,
    record_movement,
    stock_at,
    store_source_record,
)

ZERO = Decimal(0)
ONE = Decimal(1)
CENT = Decimal("0.01")
LIMIT = Decimal(10) ** 14
MAX_COMPONENTS = 50
#: A clock a little ahead of ours is not a future statement (spec 312 rule).
CLOCK_TOLERANCE = timedelta(minutes=5)
DEFINITION_SYSTEM = "internal_kit"
ASSEMBLY_SYSTEM = "internal_kit_assembly"
KIT_TOOLS = {"kit_define", "kit_assemble"}


def _plain(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(Decimal(value).normalize(), "f") if value else "0"


def _decimal(value: Any, code: str, *, places: int) -> Decimal:
    try:
        amount = Decimal(str(value).strip())
    except (DecimalError, ValueError):
        raise InvalidOperation(code=code) from None
    if not amount.is_finite() or amount >= LIMIT:
        raise InvalidOperation(code=code)
    if amount != amount.quantize(Decimal(1).scaleb(-places)):
        # The column keeps four (quantity) or six (share) places; a finer value
        # would be rounded on the way in and disagree with its statement.
        raise InvalidOperation(code=code)
    return amount


def kit_components(
    session: Session, tenant_id: str, kit_item_id: str
) -> list[KitComponent]:
    return list(
        session.scalars(
            select(KitComponent)
            .where(
                KitComponent.tenant_id == tenant_id,
                KitComponent.kit_item_id == kit_item_id,
            )
            .order_by(KitComponent.position, KitComponent.id)
        )
    )


def _is_component(session: Session, tenant_id: str, item_id: str) -> bool:
    return bool(
        session.scalar(
            select(KitComponent.id)
            .where(
                KitComponent.tenant_id == tenant_id,
                KitComponent.component_item_id == item_id,
            )
            .limit(1)
        )
    )


def _held(item: Item) -> bool:
    """Whether an item is goods the company holds, as a kit and its parts are."""
    if item.tracking_type != "none" and item.is_active and item.item_type == "stocked":
        # Kits and parts are untracked: an assembly names no lot or serial.
        raise InvalidOperation(code="kit_item_tracked", values={"sku": item.sku})
    return item.is_active and item.item_type == "stocked"


def validate_kit_definition(
    session: Session,
    tenant_id: str,
    kit_item_id: str,
    components: Any,
) -> tuple[Item, list[tuple[Item, Decimal, Decimal | None]]]:
    """
    The checks a definition makes, also run by its review so both refuse alike.

    BUSINESS PURPOSE:
    The checks a definition makes, also run by its review so both refuse alike.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-9:
    IF the kit is not an active stocked item:
        Refuse with kit_item_not_stocked.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-11:
    IF the kit already has a component definition:
        Refuse with kit_already_defined.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-13:
    IF the proposed kit already serves as a component of another kit:
        Refuse with kit_component_is_kit.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-16:
    IF components are not supplied as a nonempty list of component records:
        Refuse with kit_components_required.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-18:
    IF the component count exceeds MAX_COMPONENTS:
        Refuse with kit_components_too_many.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-58:
    IF any component share was supplied, but another share is missing or the shares do not sum to one:
        Refuse with kit_shares_invalid.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-23:
    IF components are not supplied as a nonempty list of component records:
        Refuse with kit_components_required.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-28:
    IF a component is the kit itself:
        Refuse with kit_component_is_kit.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-30:
    IF the same component item appears more than once:
        Refuse with kit_component_repeated.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-35:
    IF a component is not an active stocked item:
        Refuse with kit_component_not_stocked.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-39:
    IF a proposed component is itself a defined kit:
        Refuse with kit_component_is_kit.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-46:
    IF the stated component quantity is zero or negative:
        Refuse with kit_component_quantity_invalid.

    BUSINESS RULE services.kits.validate_kit_definition.refusal-54:
    IF a component share was supplied and lies outside the inclusive range zero to one:
        Refuse with kit_shares_invalid.

    BUSINESS RULE services.kits.validate_kit_definition.result:
    Return kit, rows, as prepared by the preceding checks and service calls.
    """
    get_tenant(session, tenant_id)
    kit = _tenant_record(session, Item, tenant_id, str(kit_item_id or ""))
    # reality-rule: services.kits.validate_kit_definition.refusal-9
    if not _held(kit):
        raise InvalidOperation(code="kit_item_not_stocked", values={"sku": kit.sku})
    # reality-rule: services.kits.validate_kit_definition.refusal-11
    if kit_components(session, tenant_id, kit.id):
        raise InvalidOperation(code="kit_already_defined", values={"sku": kit.sku})
    # reality-rule: services.kits.validate_kit_definition.refusal-13
    if _is_component(session, tenant_id, kit.id):
        # One level only: a kit inside a kit would need its own assembly first.
        raise InvalidOperation(code="kit_component_is_kit", values={"sku": kit.sku})
    # reality-rule: services.kits.validate_kit_definition.refusal-16
    if not isinstance(components, list) or not components:
        raise InvalidOperation(code="kit_components_required")
    # reality-rule: services.kits.validate_kit_definition.refusal-18
    if len(components) > MAX_COMPONENTS:
        raise InvalidOperation(code="kit_components_too_many")
    rows: list[tuple[Item, Decimal, Decimal | None]] = []
    seen: set[str] = set()
    for entry in components:
        # reality-rule: services.kits.validate_kit_definition.refusal-23
        if not isinstance(entry, dict):
            raise InvalidOperation(code="kit_components_required")
        component = _tenant_record(
            session, Item, tenant_id, str(entry.get("item_id") or "")
        )
        # reality-rule: services.kits.validate_kit_definition.refusal-28
        if component.id == kit.id:
            raise InvalidOperation(code="kit_component_is_kit", values={"sku": kit.sku})
        # reality-rule: services.kits.validate_kit_definition.refusal-30
        if component.id in seen:
            raise InvalidOperation(
                code="kit_component_repeated", values={"sku": component.sku}
            )
        seen.add(component.id)
        # reality-rule: services.kits.validate_kit_definition.refusal-35
        if not _held(component):
            raise InvalidOperation(
                code="kit_component_not_stocked", values={"sku": component.sku}
            )
        # reality-rule: services.kits.validate_kit_definition.refusal-39
        if kit_components(session, tenant_id, component.id):
            raise InvalidOperation(
                code="kit_component_is_kit", values={"sku": component.sku}
            )
        quantity = _decimal(
            entry.get("quantity"), "kit_component_quantity_invalid", places=4
        )
        # reality-rule: services.kits.validate_kit_definition.refusal-46
        if quantity <= ZERO:
            raise InvalidOperation(code="kit_component_quantity_invalid")
        raw_share = entry.get("share")
        share = (
            None
            if raw_share in (None, "")
            else _decimal(raw_share, "kit_shares_invalid", places=6)
        )
        # reality-rule: services.kits.validate_kit_definition.refusal-54
        if share is not None and not ZERO <= share <= ONE:
            raise InvalidOperation(code="kit_shares_invalid")
        rows.append((component, quantity, share))
    shares = [share for _, _, share in rows]
    # reality-rule: services.kits.validate_kit_definition.refusal-58
    if any(share is not None for share in shares) and (
        any(share is None for share in shares) or sum(shares) != ONE  # type: ignore[arg-type]
    ):
        # A split must give the whole line away, no more and no less.
        raise InvalidOperation(code="kit_shares_invalid")
    # reality-rule: services.kits.validate_kit_definition.result
    return kit, rows


def define_kit(
    session: Session,
    tenant_id: str,
    kit_item_id: str,
    components: list[dict[str, Any]],
    *,
    action_id: str | None = None,
    _commit: bool = True,
) -> list[KitComponent]:
    """
    State the components of a kit, once.

    BUSINESS PURPOSE:
    State the components of a kit, once.

    BUSINESS RULE services.kits.define_kit.step-10:
    Require the business permission for 'define_kit' before changing company records.

    BUSINESS RULE services.kits.define_kit.step-12:
    Run the shared validate kit definition check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.kits.define_kit.step-21:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.kits.define_kit.step-48:
    Record the kit.defined audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.kits.define_kit.result:
    Return created, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.kits.define_kit.step-10
    _require_business_mutation(session, tenant_id, "define_kit")
    lock_delivery_state(session, tenant_id)
    # reality-rule: services.kits.define_kit.step-12
    kit, rows = validate_kit_definition(session, tenant_id, kit_item_id, components)
    stated = [
        {
            "item_id": component.id,
            "quantity": _plain(quantity),
            "share": _plain(share),
        }
        for component, quantity, share in rows
    ]
    # reality-rule: services.kits.define_kit.step-21
    source, _, _ = store_source_record(
        session,
        tenant_id,
        DEFINITION_SYSTEM,
        "kit",
        kit.id,
        {
            "kit_item_id": kit.id,
            "components": stated,
            "statement_id": action_id or uid("stm"),
        },
    )
    created = [
        KitComponent(
            id=uid("kco"),
            tenant_id=tenant_id,
            kit_item_id=kit.id,
            component_item_id=component.id,
            quantity=quantity,
            share=share,
            position=position,
            source_record_id=source.id,
        )
        for position, (component, quantity, share) in enumerate(rows)
    ]
    session.add_all(created)
    session.flush()
    # reality-rule: services.kits.define_kit.step-48
    emit_business_event(
        session,
        tenant_id,
        "kit.defined",
        "item",
        kit.id,
        {"kit_item_id": kit.id, "components": stated},
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.kits.define_kit.result
    return created


def _free(session: Session, tenant_id: str, item_id: str, location_id: str) -> Decimal:
    """Physical less reserved less blocked, the one availability rule (spec 304)."""
    return max(
        ZERO,
        stock_at(session, tenant_id, item_id, location_id)
        - active_reserved(session, tenant_id, item_id, location_id)
        - blocked_quantity(session, tenant_id, item_id, location_id),
    )


def _stock_locations(
    session: Session, tenant_id: str, item_ids: list[str]
) -> list[Location]:
    """Locations where the kit or one of its components has ever been held."""
    held = select(Movement.to_location_id).where(
        Movement.tenant_id == tenant_id,
        Movement.item_id.in_(item_ids),
        Movement.to_location_id.is_not(None),
    )
    return list(
        session.scalars(
            select(Location)
            .where(
                Location.tenant_id == tenant_id,
                Location.id.in_(held),
                Location.allows_stock.is_(True),
            )
            .order_by(Location.name, Location.id)
        )
    )


def _availability_at(
    session: Session,
    tenant_id: str,
    kit: Item,
    components: list[KitComponent],
    items: dict[str, Item],
    location: Location,
) -> dict[str, Any]:
    parts = []
    buildable: Decimal | None = None
    for row in components:
        free = _free(session, tenant_id, row.component_item_id, location.id)
        builds = (free / row.quantity).to_integral_value(rounding=ROUND_DOWN)
        buildable = builds if buildable is None else min(buildable, builds)
        component = items[row.component_item_id]
        parts.append(
            {
                "item_id": component.id,
                "sku": component.sku,
                "name": component.name,
                "unit": component.unit,
                "quantity_per_kit": _plain(row.quantity),
                "free": _plain(free),
                "builds": _plain(builds),
            }
        )
    buildable = buildable or ZERO
    limiting = [part for part in parts if Decimal(part["builds"]) == buildable]
    on_hand = _free(session, tenant_id, kit.id, location.id)
    return {
        "location_id": location.id,
        "location": location.name,
        "kits_on_hand": _plain(on_hand),
        "buildable": _plain(buildable),
        "available": _plain(on_hand + buildable),
        "limited_by": [part["sku"] for part in limiting],
        "components": parts,
    }


def _items(session: Session, tenant_id: str, ids: set[str]) -> dict[str, Item]:
    return {
        item.id: item
        for item in session.scalars(
            select(Item).where(Item.tenant_id == tenant_id, Item.id.in_(ids))
        )
    }


def kit_availability(
    session: Session,
    tenant_id: str,
    kit_item_id: str,
    location_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Per location: free kits on hand, what free components build, the limit.

    BUSINESS PURPOSE:
    Per location: free kits on hand, what free components build, the limit.

    BUSINESS RULE services.kits.kit_availability.refusal-9:
    IF the selected item has no kit component definition:
        Refuse with kit_not_defined.

    BUSINESS RULE services.kits.kit_availability.result:
    Return the selected records in the displayed response structure; preserve the source identifiers and stated values used by this comprehension.
    """
    kit = _tenant_record(session, Item, tenant_id, kit_item_id)
    components = kit_components(session, tenant_id, kit.id)
    # reality-rule: services.kits.kit_availability.refusal-9
    if not components:
        raise NotFound(code="kit_not_defined", values={"sku": kit.sku})
    items = _items(session, tenant_id, {row.component_item_id for row in components})
    locations = (
        [_tenant_record(session, Location, tenant_id, location_id)]
        if location_id
        else _stock_locations(
            session, tenant_id, [kit.id, *(row.component_item_id for row in components)]
        )
    )
    # reality-rule: services.kits.kit_availability.result
    return [
        _availability_at(session, tenant_id, kit, components, items, location)
        for location in locations
    ]


def buildable_kits(
    session: Session, tenant_id: str, item_ids: set[str]
) -> dict[str, Decimal]:
    """Whole kits the free components build, over every location, per kit item.

    The *Oversold* class counts these as stock of the kit: a kit order the
    components can serve is not sold beyond what exists (spec 333).
    """
    rows = list(
        session.scalars(
            select(KitComponent).where(
                KitComponent.tenant_id == tenant_id,
                KitComponent.kit_item_id.in_(item_ids),
            )
        )
    )
    by_kit: dict[str, list[KitComponent]] = {}
    for row in rows:
        by_kit.setdefault(row.kit_item_id, []).append(row)
    result: dict[str, Decimal] = {}
    for kit_id, components in by_kit.items():
        kit = _tenant_record(session, Item, tenant_id, kit_id)
        items = _items(
            session, tenant_id, {row.component_item_id for row in components}
        )
        total = ZERO
        for location in _stock_locations(
            session, tenant_id, [kit.id, *(row.component_item_id for row in components)]
        ):
            total += Decimal(
                _availability_at(session, tenant_id, kit, components, items, location)[
                    "buildable"
                ]
            )
        result[kit_id] = total
    return result


def _definition(
    session: Session, tenant_id: str, kit: Item, components: list[KitComponent]
) -> dict[str, Any]:
    items = _items(session, tenant_id, {row.component_item_id for row in components})
    return {
        "kit_item_id": kit.id,
        "sku": kit.sku,
        "name": kit.name,
        "unit": kit.unit,
        "source_record_id": components[0].source_record_id,
        "has_shares": components[0].share is not None,
        "components": [
            {
                "id": row.id,
                "item_id": row.component_item_id,
                "sku": items[row.component_item_id].sku,
                "name": items[row.component_item_id].name,
                "unit": items[row.component_item_id].unit,
                "quantity": _plain(row.quantity),
                "share": _plain(row.share),
            }
            for row in components
        ],
    }


def kits(
    session: Session, tenant_id: str, *, item_id: str | None = None
) -> list[dict[str, Any]]:
    """
    Every kit of the company, or the one an item is or is part of, with availability.

    BUSINESS PURPOSE:
    Every kit of the company, or the one an item is or is part of, with availability.

    BUSINESS RULE services.kits.kits.result:
    Return result, as prepared by the preceding checks and service calls.
    """
    get_tenant(session, tenant_id)
    query = select(KitComponent.kit_item_id).where(KitComponent.tenant_id == tenant_id)
    if item_id:
        _tenant_record(session, Item, tenant_id, item_id)
        query = query.where(
            (KitComponent.kit_item_id == item_id)
            | (KitComponent.component_item_id == item_id)
        )
    kit_ids = set(session.scalars(query.distinct()))
    result = []
    for kit in sorted(
        _items(session, tenant_id, kit_ids).values(), key=lambda kit: (kit.sku, kit.id)
    ):
        components = kit_components(session, tenant_id, kit.id)
        result.append(
            {
                **_definition(session, tenant_id, kit, components),
                "availability": kit_availability(session, tenant_id, kit.id),
            }
        )
    # reality-rule: services.kits.kits.result
    return result


def _whole(value: Any) -> Decimal:
    quantity = _decimal(value, "kit_assembly_quantity_invalid", places=4)
    if quantity <= ZERO or quantity != quantity.to_integral_value():
        # A kit is whole or it does not exist; half a set is two loose parts.
        raise InvalidOperation(code="kit_assembly_quantity_invalid")
    return quantity


def _moment(value: Any) -> datetime:
    current = now()
    if value in (None, ""):
        return current
    if isinstance(value, datetime):
        moment = value
    else:
        try:
            moment = datetime.fromisoformat(str(value))
        except ValueError:
            raise InvalidOperation(code="kit_assembly_time_invalid") from None
    if moment.tzinfo is None:
        raise InvalidOperation(code="kit_assembly_time_invalid")
    moment = moment.astimezone(UTC)
    if moment > current + CLOCK_TOLERANCE:
        raise InvalidOperation(code="kit_assembly_time_future")
    return moment


def validate_kit_assembly(
    session: Session,
    tenant_id: str,
    kit_item_id: str,
    location_id: str,
    quantity: Any,
    occurred_at: Any = None,
) -> dict[str, Any]:
    """
    What an assembly consumes and produces, refused whole when a part is short.

    The review runs the same checks, so what it shows is what the
    confirmation does, and a component that runs short in between refuses the
    confirmation the same way.

    BUSINESS PURPOSE:
    What an assembly consumes and produces, refused whole when a part is short.

    BUSINESS RULE services.kits.validate_kit_assembly.refusal-17:
    IF the selected item has no kit component definition:
        Refuse with kit_not_defined.

    BUSINESS RULE services.kits.validate_kit_assembly.refusal-19:
    IF the kit is not an active stocked item:
        Refuse with kit_item_not_stocked.

    BUSINESS RULE services.kits.validate_kit_assembly.refusal-22:
    IF the assembly location is inactive or does not allow stock:
        Refuse with kit_assembly_location_not_stock.

    BUSINESS RULE services.kits.validate_kit_assembly.refusal-32:
    IF available component stock is less than the quantity needed for the requested assembly:
        Refuse with kit_component_short.

    BUSINESS RULE services.kits.validate_kit_assembly.result:
    Return the current result with kit_item_id, sku, name, unit, location_id, location, quantity, occurred_at, consumes.
    """
    get_tenant(session, tenant_id)
    kit = _tenant_record(session, Item, tenant_id, str(kit_item_id or ""))
    components = kit_components(session, tenant_id, kit.id)
    # reality-rule: services.kits.validate_kit_assembly.refusal-17
    if not components:
        raise InvalidOperation(code="kit_not_defined", values={"sku": kit.sku})
    # reality-rule: services.kits.validate_kit_assembly.refusal-19
    if not _held(kit):
        raise InvalidOperation(code="kit_item_not_stocked", values={"sku": kit.sku})
    location = _tenant_record(session, Location, tenant_id, str(location_id or ""))
    # reality-rule: services.kits.validate_kit_assembly.refusal-22
    if not location.is_active or not location.allows_stock:
        raise InvalidOperation(code="kit_assembly_location_not_stock")
    kits_wanted = _whole(quantity)
    moment = _moment(occurred_at)
    items = _items(session, tenant_id, {row.component_item_id for row in components})
    consumption = []
    for row in components:
        component = items[row.component_item_id]
        needed = row.quantity * kits_wanted
        free = _free(session, tenant_id, component.id, location.id)
        # reality-rule: services.kits.validate_kit_assembly.refusal-32
        if free < needed:
            raise InvalidOperation(
                code="kit_component_short",
                values={
                    "sku": component.sku,
                    "needed": _plain(needed),
                    "free": _plain(free),
                    "unit": component.unit,
                },
            )
        consumption.append(
            {
                "item_id": component.id,
                "sku": component.sku,
                "name": component.name,
                "unit": component.unit,
                "quantity": _plain(needed),
                "free": _plain(free),
            }
        )
    # reality-rule: services.kits.validate_kit_assembly.result
    return {
        "kit_item_id": kit.id,
        "sku": kit.sku,
        "name": kit.name,
        "unit": kit.unit,
        "location_id": location.id,
        "location": location.name,
        "quantity": _plain(kits_wanted),
        "occurred_at": moment.isoformat(),
        "consumes": consumption,
    }


def assemble_kit(
    session: Session,
    tenant_id: str,
    kit_item_id: str,
    location_id: str,
    quantity: Any,
    *,
    occurred_at: Any = None,
    note: str | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """
    Consume the components and produce the kits at one location, all or nothing.

    BUSINESS PURPOSE:
    Consume the components and produce the kits at one location, all or nothing.

    BUSINESS RULE services.kits.assemble_kit.step-13:
    Require the business permission for 'assemble_kit' before changing company records.

    BUSINESS RULE services.kits.assemble_kit.step-15:
    Run the shared validate kit assembly check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.kits.assemble_kit.step-19:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.kits.assemble_kit.step-81:
    Record the kit.assembled audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.kits.assemble_kit.result:
    Return the retained assembly source identity, checked component-consumption plan and recorded input/output warehouse movements.
    """
    # reality-rule: services.kits.assemble_kit.step-13
    _require_business_mutation(session, tenant_id, "assemble_kit")
    lock_delivery_state(session, tenant_id)
    # reality-rule: services.kits.assemble_kit.step-15
    plan = validate_kit_assembly(
        session, tenant_id, kit_item_id, location_id, quantity, occurred_at
    )
    statement = action_id or uid("stm")
    # reality-rule: services.kits.assemble_kit.step-19
    source, inserted, _ = store_source_record(
        session,
        tenant_id,
        ASSEMBLY_SYSTEM,
        "kit_assembly",
        statement,
        {
            "kit_item_id": plan["kit_item_id"],
            "location_id": plan["location_id"],
            "quantity": plan["quantity"],
            "occurred_at": plan["occurred_at"],
            "consumes": [
                {"item_id": part["item_id"], "quantity": part["quantity"]}
                for part in plan["consumes"]
            ],
            "note": (note or "").strip(),
            "statement_id": statement,
        },
    )
    if not inserted:
        # The same confirmation again: it already assembled these.
        movements = list(
            session.scalars(
                select(Movement)
                .where(
                    Movement.tenant_id == tenant_id,
                    Movement.source_record_id == source.id,
                )
                .order_by(Movement.id)
            )
        )
        return _assembly_result(source.id, plan, movements)
    moment = datetime.fromisoformat(plan["occurred_at"])
    movements = [
        record_movement(
            session,
            tenant_id,
            "assembly_input",
            part["item_id"],
            part["quantity"],
            from_location_id=plan["location_id"],
            source_record_id=source.id,
            occurred_at=moment,
            action_id=action_id,
            _commit=False,
        )
        for part in plan["consumes"]
    ]
    movements.append(
        record_movement(
            session,
            tenant_id,
            "assembly_output",
            plan["kit_item_id"],
            plan["quantity"],
            to_location_id=plan["location_id"],
            source_record_id=source.id,
            occurred_at=moment,
            action_id=action_id,
            _commit=False,
        )
    )
    # reality-rule: services.kits.assemble_kit.step-81
    emit_business_event(
        session,
        tenant_id,
        "kit.assembled",
        "item",
        plan["kit_item_id"],
        {
            "kit_item_id": plan["kit_item_id"],
            "location_id": plan["location_id"],
            "quantity": plan["quantity"],
            "movement_ids": [movement.id for movement in movements],
        },
        source_record_id=source.id,
        occurred_at=moment,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.kits.assemble_kit.result
    return _assembly_result(source.id, plan, movements)


def _assembly_result(
    source_record_id: str, plan: dict[str, Any], movements: list[Movement]
) -> dict[str, Any]:
    return {
        "source_record_id": source_record_id,
        "kit_item_id": plan["kit_item_id"],
        "location_id": plan["location_id"],
        "quantity": plan["quantity"],
        "movement_ids": [movement.id for movement in movements],
    }


def _stated_parts(line: DocumentLine) -> dict[str, Decimal]:
    """The amounts the line states: gross always, net and tax where stated (spec 284)."""
    stated = {"gross": Decimal(line.gross_amount)}
    try:
        finance = (json.loads(line.payload or "{}") or {}).get(
            "reality_finance_v1"
        ) or {}
    except ValueError:
        finance = {}
    for key in ("net", "tax"):
        if finance.get(key) not in (None, ""):
            stated[key] = Decimal(str(finance[key]))
    return stated


def _apportion(total: Decimal, shares: list[Decimal]) -> list[Decimal]:
    """Cents by share, the remainder on the largest share, adding up exactly."""
    parts = [
        (total * share).quantize(CENT, rounding=ROUND_HALF_EVEN) for share in shares
    ]
    largest = max(range(len(shares)), key=lambda index: (shares[index], -index))
    parts[largest] += total - sum(parts)
    return parts


def kit_split(
    session: Session, tenant_id: str, document_line_id: str
) -> dict[str, Any]:
    """
    How an order or invoice line of a kit splits across its components.

    Read at read time from the line's stated amounts and the kit's stated
    shares; nothing is recomputed from a rate and nothing is stored. A kit
    without stated shares has no split, and the read says so.

    BUSINESS PURPOSE:
    How an order or invoice line of a kit splits across its components.

    BUSINESS RULE services.kits.kit_split.refusal-10:
    IF the order line has no item or its item has no kit component definition:
        Refuse with kit_split_line_not_kit.

    BUSINESS RULE services.kits.kit_split.refusal-14:
    IF the order line has no item or its item has no kit component definition:
        Refuse with kit_split_line_not_kit.

    BUSINESS RULE services.kits.kit_split.result:
    Return the current result with stated, split.
    """
    line = _tenant_record(session, DocumentLine, tenant_id, document_line_id)
    # reality-rule: services.kits.kit_split.refusal-10
    if not line.item_id:
        raise InvalidOperation(code="kit_split_line_not_kit")
    kit = _tenant_record(session, Item, tenant_id, line.item_id)
    components = kit_components(session, tenant_id, kit.id)
    # reality-rule: services.kits.kit_split.refusal-14
    if not components:
        raise InvalidOperation(code="kit_split_line_not_kit")
    base = {
        "document_line_id": line.id,
        "document_id": line.document_id,
        "kit_item_id": kit.id,
        "sku": kit.sku,
        "line_quantity": _plain(line.quantity),
        "source_record_id": components[0].source_record_id,
    }
    stated = _stated_parts(line)
    if components[0].share is None:
        return {
            **base,
            "split": None,
            "stated": {k: _plain(v) for k, v in stated.items()},
        }
    shares = [Decimal(row.share) for row in components]  # type: ignore[arg-type]
    apportioned = {key: _apportion(total, shares) for key, total in stated.items()}
    items = _items(session, tenant_id, {row.component_item_id for row in components})
    parts = []
    for index, row in enumerate(components):
        pieces = Decimal(line.quantity) * row.quantity
        gross = apportioned["gross"][index]
        parts.append(
            {
                "item_id": row.component_item_id,
                "sku": items[row.component_item_id].sku,
                "name": items[row.component_item_id].name,
                "unit": items[row.component_item_id].unit,
                "share": _plain(row.share),
                "quantity": _plain(pieces),
                **{key: _plain(values[index]) for key, values in apportioned.items()},
                "gross_per_piece": _plain(
                    (gross / pieces).quantize(CENT, rounding=ROUND_HALF_EVEN)
                )
                if pieces
                else None,
            }
        )
    # reality-rule: services.kits.kit_split.result
    return {
        **base,
        "stated": {key: _plain(value) for key, value in stated.items()},
        "split": parts,
    }


def review_kit(
    session: Session, tenant_id: str, tool_name: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    The arguments a confirmation executes and what the person is shown.

    BUSINESS PURPOSE:
    The arguments a confirmation executes and what the person is shown.

    BUSINESS RULE services.kits.review_kit.refusal-4:
    IF the requested operation is not registered for this review service:
        Refuse with proposal_tool_not_found.

    BUSINESS RULE services.kits.review_kit.step-48:
    Run the shared validate kit assembly check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.kits.review_kit.result:
    Return normalized, {'operation': 'assemble', **plan}, as prepared by the preceding checks and service calls.

    BUSINESS RULE services.kits.review_kit.effect-23:
    IF the requested operation defines a kit:
        Run the shared validate kit definition check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.
    """
    # reality-rule: services.kits.review_kit.refusal-4
    if tool_name not in KIT_TOOLS:
        raise InvalidOperation(code="proposal_tool_not_found")
    if tool_name == "kit_define":
        # reality-rule: services.kits.review_kit.effect-23
        kit, rows = validate_kit_definition(
            session,
            tenant_id,
            arguments.get("kit_item_id"),
            arguments.get("components"),
        )
        components = [
            {
                "item_id": component.id,
                "sku": component.sku,
                "name": component.name,
                "unit": component.unit,
                "quantity": _plain(quantity),
                "share": _plain(share),
            }
            for component, quantity, share in rows
        ]
        return (
            {
                "kit_item_id": kit.id,
                "components": [
                    {
                        "item_id": part["item_id"],
                        "quantity": part["quantity"],
                        **(
                            {"share": part["share"]}
                            if part["share"] is not None
                            else {}
                        ),
                    }
                    for part in components
                ],
            },
            {
                "operation": "define",
                "kit_item_id": kit.id,
                "sku": kit.sku,
                "name": kit.name,
                "components": components,
            },
        )
    # reality-rule: services.kits.review_kit.step-48
    plan = validate_kit_assembly(
        session,
        tenant_id,
        arguments.get("kit_item_id"),
        arguments.get("location_id"),
        arguments.get("quantity"),
        arguments.get("occurred_at"),
    )
    normalized = {
        "kit_item_id": plan["kit_item_id"],
        "location_id": plan["location_id"],
        "quantity": plan["quantity"],
        # The time is fixed at review, so the confirmation states what was seen.
        "occurred_at": plan["occurred_at"],
    }
    note = str(arguments.get("note") or "").strip()
    if note:
        normalized["note"] = note
    # reality-rule: services.kits.review_kit.result
    return normalized, {"operation": "assemble", **plan}
