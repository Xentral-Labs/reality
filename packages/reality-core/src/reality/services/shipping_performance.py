"""Current source-backed shipping observations; calculations remain in the domain."""

from __future__ import annotations

import base64
import hashlib
import json
from bisect import bisect_right
from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import cast, select
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    Commitment,
    CommitmentRevision,
    Document,
    Location,
    Movement,
    MovementCorrection,
    Shipment,
    ShipmentEvent,
    ShipmentEventSupersession,
    ShipmentPackage,
    ShippingCapacityWindow,
    ShippingDispatchRequirement,
    Tenant,
    TenantEventProgress,
    now,
)
from reality.db.operational_cases import CaseCommitmentLink, CaseProposalLink
from reality.domain.shipping_performance import (
    OBSERVATION_ONLY_GAPS,
    Capacity,
    DispatchWork,
    PhysicalContent,
    aware,
    covered_at,
    evaluate,
)
from reality.services import core, shipping_plans
from reality.services.company_time_zone import company_time_zone_state
from reality.services.fulfillment_readiness import fulfillment_readiness_batch


def _series(times: dict, start: datetime, end: datetime) -> list[dict]:
    if end < start:
        return []
    opening = sum(instant < start for instant in times.values())
    grouped: dict[datetime, int] = defaultdict(int)
    for instant in times.values():
        if start <= instant <= end:
            grouped[instant] += 1
    result = [{"at": start.isoformat(), "count": opening}]
    if len(grouped) > 300:
        ordered = sorted(times.values())
        result.append({"at": start.isoformat(), "count": bisect_right(ordered, start)})
        instant = start
        while instant < end:
            instant = min(instant + timedelta(minutes=5), end)
            result.append(
                {"at": instant.isoformat(), "count": bisect_right(ordered, instant)}
            )
        return result
    count = opening
    for instant, amount in sorted(grouped.items()):
        count += amount
        result.append({"at": instant.isoformat(), "count": count})
    return result


def _basis_preview(basis: dict[str, Any]) -> dict[str, Any]:
    """Disclose a bounded evidence preview while retaining the full fingerprint.

    BUSINESS PURPOSE:
    Keep enterprise live reads small without sampling calculations or authority.

    BUSINESS RULE shipping_performance.basis.preview:
    Preserve full context, statements and capacities. Bound work, source metadata,
    revisions, readiness and physical-content previews to fifty entries, report
    complete sizes and never mutate the full inputs used for the fingerprint.
    """
    # reality-rule: shipping_performance.basis.preview
    limit = 50
    counts = {
        "work": len(basis["work"]),
        "sources": sum(len(rows) for rows in basis["sources"].values()),
        **{
            key: len(basis[key])
            for key in ("quantity_revision_ids", "readiness", "physical_contents")
        },
    }
    preview = {**basis, "work": basis["work"][:limit]}
    remaining = limit
    essential = set(basis.get("planning_source_record_ids", []))
    preview["sources"] = {identity: {} for identity in basis["sources"]}
    # Daily planning and collection confirmation evidence precedes the sample
    # of order sources, including when an earlier site exhausts that sample.
    for planning_first in (True, False):
        for identity, rows in sorted(basis["sources"].items()):
            keys = set(rows) & essential if planning_first else set(rows) - essential
            selected = sorted(keys)[:remaining]
            preview["sources"][identity].update((key, rows[key]) for key in selected)
            remaining -= len(selected)
    for key in ("quantity_revision_ids", "readiness", "physical_contents"):
        preview[key] = dict(sorted(basis[key].items())[:limit])
    preview["disclosure"] = {
        "sample_limit": limit,
        "sampled": any(size > limit for size in counts.values()),
        "complete_counts": counts,
        "scope": "preview_only_full_fingerprint_and_paged_order_evidence",
    }
    return preview


def _watermark(session: Session, tenant_id: str) -> int:
    return (
        session.scalar(
            select(TenantEventProgress.last_event_sequence).where(
                TenantEventProgress.tenant_id == tenant_id
            )
        )
        or 0
    )


def _read_shipping(
    session: Session,
    tenant_id: str,
    *,
    day: str = "today",
    location_id: str | None = None,
    observed_at: datetime | None = None,
    _deviations_only: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, core.CommitmentTerms]]:
    """
    BUSINESS PURPOSE:
    Explain today's complete planned shipping cohort from accepted statements,
    effective physical contents, attributed handovers and canonical readiness.

    BUSINESS RULE shipping_performance.read.scope:
    Resolve this company's explicit calendar and dispatch scope. Missing plans
    are unknown; cancellation excludes held work without deleting its evidence.

    BUSINESS RULE shipping_performance.read.evidence:
    Read effective contents through Movement, Package and Shipment, excluding
    corrected movements and superseded observations. Bind current quantities,
    exact reviewed versions and source coverage; never use ingestion as handover.

    BUSINESS RULE shipping_performance.read.result:
    Pass full site/order work and confirmed inputs to completion-slot-v1. Return
    complete aggregates, source identities and timed series without storing any
    forecast or creating business effects. Concurrent business changes remove
    completeness claims rather than combine incompatible observations.
    """
    # reality-rule: shipping_performance.read.scope
    core._tenant_record_read(session, Tenant, tenant_id, tenant_id)
    if location_id:
        core._tenant_record_read(session, Location, tenant_id, location_id)
    instant = aware(
        observed_at or session.info.get("operations_snapshot_observed_at") or now()
    )
    zone_name = company_time_zone_state(session, tenant_id)["time_zone"]
    zone = ZoneInfo(zone_name)
    try:
        selected_day = (
            instant.astimezone(zone).date()
            if day == "today"
            else date.fromisoformat(day)
        )
        if day != "today" and selected_day.isoformat() != day:
            raise ValueError("An ISO date must use the full calendar form.")
    except (TypeError, ValueError) as error:
        raise core.InvalidOperation(
            code="shipping_observation_filter_invalid"
        ) from error
    start = datetime.combine(selected_day, time(), zone).astimezone(UTC)
    end = datetime.combine(selected_day + timedelta(days=1), time(), zone).astimezone(
        UTC
    )
    watermark = _watermark(session, tenant_id)
    narrow = bool(session.info.get("operations_snapshot_consistent"))
    statements = shipping_plans.current_statements(
        session,
        tenant_id,
        business_day=selected_day,
        location_id=location_id,
        _metadata_only=narrow,
    )
    active = [
        (statement, source)
        for statement, source in statements
        if statement.statement_kind == "plan"
    ]
    statement_ids = {statement.id for statement, _ in active}
    requirements = list(
        session.execute(
            select(*ShippingDispatchRequirement.__table__.columns).where(
                ShippingDispatchRequirement.tenant_id == tenant_id,
                ShippingDispatchRequirement.statement_id.in_(statement_ids),
            )
        )
    )
    windows = list(
        session.scalars(
            select(ShippingCapacityWindow).where(
                ShippingCapacityWindow.tenant_id == tenant_id,
                ShippingCapacityWindow.statement_id.in_(statement_ids),
            )
        )
    )
    ids = {row.commitment_id for row in requirements}
    commitment_columns = (
        (
            Commitment.id,
            Commitment.tenant_id,
            Commitment.type,
            Commitment.quantity,
            Commitment.due_at,
            Commitment.status,
            Commitment.cancelled_at,
            Commitment.item_id,
            Commitment.document_id,
            Commitment.location_id,
            Commitment.to_party_id,
            Commitment.currency,
        )
        if narrow
        else (
            Commitment.id,
            Commitment.status,
            Commitment.cancelled_at,
            Commitment.item_id,
            Commitment.document_id,
        )
    )
    commitments = {
        row.id: row
        for row in session.execute(
            select(*commitment_columns).where(
                Commitment.tenant_id == tenant_id,
                core._id_cohort(Commitment.id, ids),
            )
        )
    }
    documents = (
        {
            row.id: row
            for row in session.execute(
                select(
                    Document.id,
                    Document.tenant_id,
                    Document.type,
                    Document.party_id,
                    Document.payment_term_id,
                    Document.gross_amount,
                    Document.currency,
                    Document.number,
                    Document.source_record_id,
                ).where(
                    Document.tenant_id == tenant_id,
                    core._id_cohort(
                        Document.id, {row.document_id for row in commitments.values()}
                    ),
                )
            )
        }
        if narrow
        else None
    )
    terms = core.commitment_terms(
        session, tenant_id, ids, _commitments=commitments if narrow else None
    )
    revisions = {}
    revision_sources = {}
    for row in session.execute(
        select(
            CommitmentRevision.id,
            CommitmentRevision.commitment_id,
            CommitmentRevision.source_record_id,
        )
        .where(
            CommitmentRevision.tenant_id == tenant_id,
            core._id_cohort(CommitmentRevision.commitment_id, ids),
            CommitmentRevision.quantity.is_not(None),
        )
        .order_by(CommitmentRevision.stated_at, CommitmentRevision.id)
    ):
        revisions[row.commitment_id] = row.id
        revision_sources[row.commitment_id] = row.source_record_id
    proposal_query = select(
        *(
            ChangeProposal.id,
            cast(ChangeProposal.input, JSON)["reviewed"].label("reviewed"),
        )
        if narrow
        else (ChangeProposal,)
    ).where(
        ChangeProposal.tenant_id == tenant_id,
        ChangeProposal.id.in_(
            {shipping_plans.statement_action_id(source) for _, source in active}
        ),
    )
    proposals = {
        row.id: row
        for row in (
            session.execute(proposal_query)
            if narrow
            else session.scalars(proposal_query)
        )
    }
    locations = {
        row.id: row
        for row in session.scalars(
            select(Location).where(
                Location.tenant_id == tenant_id,
                Location.id.in_(
                    {statement.dispatch_location_id for statement, _ in active}
                ),
            )
        )
    }
    scoped_windows = defaultdict(list)
    for row in windows:
        scoped_windows[row.statement_id].append(row)
    statement_gaps: dict[str, set[str]] = defaultdict(set)
    sources = {}
    exact_sources = {}
    source_requests = {}
    reviewed = {}
    seen_sites = set()
    for statement, source in active:
        if statement.dispatch_location_id in seen_sites:
            for other, _ in active:
                if other.dispatch_location_id == statement.dispatch_location_id:
                    statement_gaps[other.id].add("shipping_plan_scope_conflict")
        seen_sites.add(statement.dispatch_location_id)
        if statement.business_time_zone != zone_name:
            statement_gaps[statement.id].add("shipping_plan_calendar_changed")
        proposal = proposals.get(shipping_plans.statement_action_id(source))
        basis = (
            (
                proposal.reviewed
                if narrow
                else json.loads(proposal.input).get("reviewed")
            )
            if proposal
            else None
        )
        reviewed[statement.id] = basis
        if not basis:
            statement_gaps[statement.id].add("shipping_plan_review_required")
            continue
        exact = {source.id} | {
            window.confirmation_source_record_id
            for window in scoped_windows[statement.id]
            if window.confirmation_source_record_id
        }
        exact_sources[statement.id] = exact
        source_requests[statement.id] = (set(basis["sources"]) | exact, exact)
    source_inputs = (
        shipping_plans._source_basis_inputs(
            session,
            tenant_id,
            set().union(*(required for required, _ in source_requests.values())),
        )
        if narrow and source_requests
        else None
    )
    for statement_id, (required, exact) in source_requests.items():
        try:
            sources[statement_id] = shipping_plans.source_basis(
                session,
                tenant_id,
                required,
                current_required=exact,
                _inputs=source_inputs,
            )
        except (core.NotFound, core.InvalidOperation) as error:
            statement_gaps[statement_id].add(error.code)

    # reality-rule: shipping_performance.read.evidence
    effective = (
        ~select(MovementCorrection.id)
        .where(
            MovementCorrection.tenant_id == tenant_id,
            MovementCorrection.original_movement_id == Movement.id,
        )
        .exists()
    )
    contents = defaultdict(list)
    shipment_ids = set()
    rows = list(
        session.execute(
            select(Movement, ShipmentPackage, Shipment)
            .outerjoin(
                ShipmentPackage,
                (ShipmentPackage.tenant_id == Movement.tenant_id)
                & (ShipmentPackage.id == Movement.shipment_package_id),
            )
            .outerjoin(
                Shipment,
                (Shipment.tenant_id == ShipmentPackage.tenant_id)
                & (Shipment.id == ShipmentPackage.shipment_id),
            )
            .where(
                Movement.tenant_id == tenant_id,
                core._id_cohort(Movement.commitment_id, ids),
                Movement.type == "shipment",
                effective,
            )
        )
    )
    for _, package, shipment in rows:
        if package and shipment:
            shipment_ids.add(shipment.id)
    effective_event = (
        ~select(ShipmentEventSupersession.id)
        .where(
            ShipmentEventSupersession.tenant_id == tenant_id,
            ShipmentEventSupersession.superseded_event_id == ShipmentEvent.id,
        )
        .exists()
    )
    events = defaultdict(list)
    for event in session.execute(
        select(
            ShipmentEvent.id,
            ShipmentEvent.shipment_id,
            ShipmentEvent.shipment_package_id,
            ShipmentEvent.occurred_at,
        ).where(
            ShipmentEvent.tenant_id == tenant_id,
            core._id_cohort(ShipmentEvent.shipment_id, shipment_ids),
            ShipmentEvent.event_type == "handed_over",
            effective_event,
        )
    ):
        events[event.shipment_id].append(event)
    for movement, package, shipment in rows:
        contents[movement.commitment_id].append((movement, package, shipment))
    uncertain = set(
        session.scalars(
            select(CaseCommitmentLink.commitment_id)
            .join(
                CaseProposalLink,
                (CaseProposalLink.tenant_id == CaseCommitmentLink.tenant_id)
                & (CaseProposalLink.case_id == CaseCommitmentLink.case_id),
            )
            .join(
                ChangeProposal,
                (ChangeProposal.tenant_id == CaseProposalLink.tenant_id)
                & (ChangeProposal.id == CaseProposalLink.proposal_id),
            )
            .where(
                CaseCommitmentLink.tenant_id == tenant_id,
                core._id_cohort(CaseCommitmentLink.commitment_id, ids),
                ChangeProposal.status == "executing",
            )
        )
    )
    by_statement = {statement.id: statement for statement, _ in active}
    work = []
    readiness_results = fulfillment_readiness_batch(
        session,
        tenant_id,
        {
            row.commitment_id: by_statement[row.statement_id].dispatch_location_id
            for row in requirements
            if row.commitment_id in commitments
            and commitments[row.commitment_id].status != "cancelled"
        },
        _terms=terms,
        _commitments=commitments if narrow else None,
        _orders=documents,
    )
    readiness_basis = {}
    physical_basis = {}
    gaps = []
    excluded = []
    for row in requirements:
        commitment = commitments[row.commitment_id]
        if commitment.cancelled_at:
            excluded.append({"commitment_id": commitment.id, "reason": "cancelled"})
            continue
        statement = by_statement[row.statement_id]
        problems = set(statement_gaps[statement.id])
        original = (
            (reviewed[statement.id] or {}).get("commitments", {}).get(commitment.id)
        )
        if (
            row.quantity != terms[commitment.id].quantity
            or not original
            or original.get("quantity_revision_id") != revisions.get(commitment.id)
        ):
            problems.add("shipping_plan_quantity_changed")
        if commitment.id in uncertain:
            problems.add("unresolved_execution_outcome")
        physical = []
        for movement, package, shipment in contents[commitment.id]:
            if movement.occurred_at > instant:
                problems.add("unresolved_future_physical_content")
            if (
                movement.from_location_id != statement.dispatch_location_id
                or movement.item_id != commitment.item_id
            ):
                problems.add("incompatible_dispatch_contents")
                continue
            if (
                not package
                or not shipment
                or shipment.direction != "outbound"
                or shipment.purpose != "customer_delivery"
            ):
                problems.add("unresolved_shipment_linkage")
                continue
            handovers = tuple(
                event.occurred_at
                for event in events[shipment.id]
                if event.shipment_package_id in {None, package.id}
            )
            physical.append(
                PhysicalContent(
                    movement.id, movement.quantity, movement.occurred_at, handovers
                )
            )
        handed_over, timing_gaps = covered_at(
            row.quantity, physical, observed_at=instant
        )
        problems.update(timing_gaps)
        exited = sum(
            (
                content.quantity
                for content in physical
                if content.dispatched_at <= instant
            ),
            Decimal(0),
        )
        readiness = readiness_results[commitment.id]
        ready = exited >= row.quantity or readiness.ship_ready
        readiness_basis[commitment.id] = readiness.as_dict(include_interpretation=False)
        physical_basis[commitment.id] = [
            {
                "movement_id": movement.id,
                "source_record_id": movement.source_record_id,
                "package_id": package.id if package else None,
                "shipment_id": shipment.id if shipment else None,
                "handover_event_ids": [
                    event.id
                    for event in events[shipment.id]
                    if event.shipment_package_id in {None, package.id}
                ]
                if package and shipment
                else [],
            }
            for movement, package, shipment in contents[commitment.id]
        ]
        work.append(
            DispatchWork(
                commitment.id,
                commitment.document_id,
                statement.dispatch_location_id,
                row.quantity,
                row.dispatch_due_at,
                row.planned_handover_at,
                handed_over,
                ready,
                tuple(sorted(problems)),
            )
        )
        gaps.extend(
            {"code": code, "commitment_id": commitment.id, "statement_id": statement.id}
            for code in sorted(problems)
        )
    capacities = [
        Capacity(
            by_statement[row.statement_id].dispatch_location_id,
            row.starts_at,
            row.ends_at,
            row.collection_cutoff_at,
            row.completion_slots,
            row.confirmation_state,
        )
        for row in windows
    ]
    # reality-rule: shipping_performance.read.result
    result = evaluate(work, capacities, observed_at=instant)
    sources_changed = False
    for statement_id, original in (
        sources.items()
        if not session.info.get("operations_snapshot_consistent")
        else []
    ):
        try:
            current = shipping_plans.source_basis(
                session,
                tenant_id,
                set(original),
                current_required=exact_sources[statement_id],
            )
            sources_changed |= current != original
        except (core.NotFound, core.InvalidOperation):
            sources_changed = True
    changed = sources_changed or (
        not session.info.get("operations_snapshot_consistent")
        and watermark != _watermark(session, tenant_id)
    )
    available = bool(active)
    if changed:
        gaps.append({"code": "observation_changed_during_read"})
    complete = (
        available
        and not changed
        and not any(row["code"] not in OBSERVATION_ONLY_GAPS for row in gaps)
    )
    totals = {
        "due": len({row.order_id for row in work}) if available else None,
        "handed_over": sum(
            value <= min(instant, end) for value in result["actual_times"].values()
        )
        if available
        else None,
        "forecast": sum(value <= end for value in result["forecast_times"].values())
        if available and result["forecast_complete"] and complete and instant < end
        else None,
        "risk": len(result["risk_order_ids"])
        if available and result["forecast_complete"] and complete
        else None,
    }
    if changed:
        totals = dict.fromkeys(totals)
    basis = {
        "context": {
            "tenant_id": tenant_id,
            "business_day": selected_day.isoformat(),
            "location_id": location_id,
            "time_zone": zone_name,
            "day_start": start.isoformat(),
            "day_end": end.isoformat(),
        },
        "statement_ids": sorted(statement_ids),
        "planning_source_record_ids": sorted(
            {
                identity
                for identities in exact_sources.values()
                for identity in identities
            }
        ),
        "sources": sources,
        "quantity_revision_ids": revisions,
        "policy_version": result["policy_version"],
        "watermark": watermark,
        "observed_at": instant.isoformat(),
        "work": [row.__dict__ for row in work],
        "capacities": [row.__dict__ for row in capacities],
        "readiness": readiness_basis,
        "physical_contents": physical_basis,
    }
    basis_key = hashlib.sha256(
        json.dumps(basis, default=str, sort_keys=True).encode()
    ).hexdigest()
    sites = []
    for statement, _ in active:
        values = result["sites"].get(
            statement.dispatch_location_id,
            {"due": 0, "handed_over": 0, "forecast": 0, "risk": 0},
        )
        sites.append(
            {
                "location_id": statement.dispatch_location_id,
                "name": locations[statement.dispatch_location_id].name,
                "time_zone": statement.site_time_zone,
                **values,
                "cutoffs": [
                    {
                        "at": window.collection_cutoff_at.isoformat(),
                        "confirmation_state": window.confirmation_state,
                        "source_record_id": window.confirmation_source_record_id,
                        "capacity_window_id": window.id,
                    }
                    for window in scoped_windows[statement.id]
                ],
            }
        )
    snapshot = {
        "observed_at": instant.isoformat(),
        "business_day": selected_day.isoformat(),
        "time_zone": zone_name,
        "location_id": location_id,
        "day_start": start.isoformat(),
        "day_end": end.isoformat(),
        "basis_key": basis_key,
        "basis": _basis_preview(basis),
        "coverage": {
            "cohort": "complete"
            if complete
            else "partial"
            if available
            else "unavailable",
            "handover": "partial"
            if gaps
            else "complete"
            if available
            else "unavailable",
            "forecast": "complete" if totals["forecast"] is not None else "unavailable",
        },
        "totals": totals,
        "sites": sites if not changed else [],
        "gaps": gaps,
        "excluded": excluded,
        "opening_baseline": {
            "handover": sum(value < start for value in result["actual_times"].values()),
            "plan": sum(value < start for value in result["planned_times"].values()),
        },
        "forecast_horizon": "future" if instant < end else "selected_day_ended",
        "series": {
            "plan": _series(result["planned_times"], start, end)
            if available and result["plan_complete"] and complete
            else None,
            "handover": _series(result["actual_times"], start, min(instant, end))
            if available and not changed
            else None,
            "forecast": _series(result["forecast_times"], instant, end)
            if totals["forecast"] is not None
            else None,
        },
    }
    snapshot["series_resolution_seconds"] = {
        name: 300
        if snapshot["series"][name] is not None
        and len({value for value in values.values() if first <= value <= last}) > 300
        else 0
        for name, values, first, last in (
            ("plan", result["planned_times"], start, end),
            ("handover", result["actual_times"], start, min(instant, end)),
            ("forecast", result["forecast_times"], instant, end),
        )
    }
    documents = (
        documents
        if narrow
        else {
            row.id: row
            for row in session.execute(
                select(Document.id, Document.number, Document.source_record_id).where(
                    Document.tenant_id == tenant_id,
                    core._id_cohort(Document.id, {row.order_id for row in work}),
                )
            )
        }
    )
    grouped = defaultdict(list)
    risk_by_order = defaultdict(list)
    for row in result["risk_requirements"]:
        risk_by_order[row["order_id"]].append(row)
    for row in work:
        grouped[row.order_id].append(row)
    risk_order_ids = set(result["risk_order_ids"])
    orders = [
        {
            "order_id": identity,
            "number": documents[identity].number,
            "commitment_ids": sorted(row.commitment_id for row in units),
            "source_record_ids": sorted(
                {
                    source
                    for source in (
                        [documents[identity].source_record_id]
                        + [revision_sources.get(row.commitment_id) for row in units]
                        + [
                            content["source_record_id"]
                            for row in units
                            for content in physical_basis[row.commitment_id]
                        ]
                    )
                    if source
                }
            ),
            "readiness": {
                row.commitment_id: readiness_basis[row.commitment_id] for row in units
            },
            "location_ids": sorted({row.location_id for row in units}),
            "due_at": max(row.due_at for row in units).isoformat(),
            "plan_at": result["planned_times"].get(identity),
            "handover_at": result["actual_times"].get(identity),
            "forecast_at": result["forecast_times"].get(identity),
            "at_risk": identity in risk_order_ids,
            "risk_at": min(row["due_at"] for row in risk_by_order[identity])
            if identity in risk_by_order
            else None,
            "risk_requirements": risk_by_order[identity],
            "blockers": {
                row.commitment_id: readiness_basis[row.commitment_id]["blockers"]
                for row in units
            },
            "coverage_gaps": sorted(
                {code for row in units for code in row.coverage_gaps}
            ),
            "physical_contents": {
                row.commitment_id: physical_basis[row.commitment_id] for row in units
            },
        }
        for identity, units in sorted(grouped.items())
        # Projection follows the complete calculation and full fingerprint. The
        # overview never consumes healthy order details; supporting reads do.
        if not (narrow and _deviations_only)
        or identity in risk_order_ids
        or any(row.coverage_gaps for row in units)
    ]
    return _json_value(snapshot), orders, terms


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def shipping_performance(
    session: Session,
    tenant_id: str,
    *,
    day: str = "today",
    location_id: str | None = None,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    """
    BUSINESS PURPOSE:
    Return canonical current shipping performance with exact provenance and coverage.

    BUSINESS RULE shipping_performance.public.shared:
    Use the shared full-cohort observation without storing a forecast or changing business work.
    """
    # reality-rule: shipping_performance.public.shared
    return _read_shipping(
        session, tenant_id, day=day, location_id=location_id, observed_at=observed_at
    )[0]


def _unplanned_orders(
    session: Session, tenant_id: str, business_day: str
) -> list[dict]:
    """Discover accepted open customer work outside the selected day's plan.

    This company-wide discovery has no assigned dispatch site or shipping
    deadline; reservation locations and generic commitment due dates are not
    planning evidence. Fulfillment comes from canonical commitment terms.
    """
    statements = shipping_plans.current_statements(
        session, tenant_id, business_day=date.fromisoformat(business_day)
    )
    active_ids = {
        statement.id
        for statement, _ in statements
        if statement.statement_kind == "plan"
    }
    assigned = select(ShippingDispatchRequirement.commitment_id).where(
        ShippingDispatchRequirement.tenant_id == tenant_id,
        ShippingDispatchRequirement.statement_id.in_(active_ids),
    )
    rows = list(
        session.execute(
            select(Commitment, Document)
            .join(
                Document,
                (Document.tenant_id == Commitment.tenant_id)
                & (Document.id == Commitment.document_id),
            )
            .where(
                Commitment.tenant_id == tenant_id,
                Document.tenant_id == tenant_id,
                Commitment.type == "customer_delivery",
                Commitment.status == "open",
                Document.type == "sales_order",
                ~Commitment.id.in_(assigned),
            )
        )
    )
    terms = core.commitment_terms(session, tenant_id, [row.id for row, _ in rows])
    grouped = {}
    for row, doc in rows:
        if terms[row.id].open <= 0:
            continue
        record = grouped.setdefault(
            doc.id,
            {
                "order_id": doc.id,
                "number": doc.number,
                "commitment_ids": [],
                "location_ids": [],
                "due_at": None,
                "plan_at": None,
                "handover_at": None,
                "forecast_at": None,
                "at_risk": False,
                "risk_at": None,
                "risk_requirements": [],
                "blockers": {},
                "coverage_gaps": ["no_dispatch_plan_assignment"],
                "physical_contents": {},
            },
        )
        record["commitment_ids"].append(row.id)
    return [grouped[identity] for identity in sorted(grouped)]


def shipping_supporting_orders(
    session: Session,
    tenant_id: str,
    *,
    day: str = "today",
    location_id: str | None = None,
    measure: str = "due",
    at: str | datetime | None = None,
    from_at: str | datetime | None = None,
    until: str | datetime | None = None,
    after: str = "",
    limit: int = 50,
    basis_key: str | None = None,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    """
    BUSINESS PURPOSE:
    Explain all orders behind a shipping measure with complete totals before pagination.

    BUSINESS RULE shipping_performance.supporting.filters:
    Admit exact same-company day/site and measure context, either a cumulative
    instant or a half-open interval, and a bounded context-specific opaque cursor.

    BUSINESS RULE shipping_performance.supporting.result:
    Re-evaluate the same canonical observation, preserve its current totals and
    disclose changed basis. Paging never changes the denominator or authorizes work.
    """
    # reality-rule: shipping_performance.supporting.filters
    if (
        type(limit) is not int
        or not 1 <= limit <= 100
        or measure
        not in {
            "due",
            "plan",
            "handover",
            "forecast",
            "risk",
            "unplanned",
        }
        or (
            measure == "unplanned"
            and (
                location_id
                or at is not None
                or from_at is not None
                or until is not None
            )
        )
        or (at is not None and (from_at is not None or until is not None))
        or ((from_at is None) != (until is None))
    ):
        raise core.InvalidOperation(code="shipping_observation_filter_invalid")
    snapshot, orders, _ = _read_shipping(
        session, tenant_id, day=day, location_id=location_id, observed_at=observed_at
    )
    try:
        parse = lambda value: aware(
            datetime.fromisoformat(value) if isinstance(value, str) else value
        )
        point = parse(at) if at is not None else None
        beginning = parse(from_at) if from_at is not None else None
        ending = parse(until) if until is not None else None
        day_start = datetime.fromisoformat(snapshot["day_start"])
        day_end = datetime.fromisoformat(snapshot["day_end"])
        if point is not None and not day_start <= point <= day_end:
            raise ValueError("Cumulative instant is outside the selected day.")
        if beginning is not None and not day_start <= beginning < ending <= day_end:
            raise ValueError("Interval is outside the selected day.")
    except (TypeError, ValueError) as error:
        raise core.InvalidOperation(
            code="shipping_observation_filter_invalid"
        ) from error
    fields = {
        "due": "due_at",
        "plan": "plan_at",
        "handover": "handover_at",
        "forecast": "forecast_at",
    }
    available = snapshot["totals"]["due"] is not None
    if measure in {"plan", "handover", "forecast"}:
        available &= snapshot["series"][measure] is not None
    if measure == "risk":
        available &= snapshot["totals"]["risk"] is not None
    matched = []
    if measure == "unplanned":
        matched = _unplanned_orders(session, tenant_id, snapshot["business_day"])
        available = True
    for row in orders if available and measure != "unplanned" else []:
        if measure == "risk" and not row["at_risk"]:
            continue
        raw = row[fields[measure]] if measure in fields else row["risk_at"]
        if raw is None:
            continue
        value = parse(raw)
        if point is not None and value > point:
            continue
        if beginning is not None and not beginning <= value < ending:
            continue
        matched.append(row)
    scope = hashlib.sha256(
        json.dumps(
            {
                "tenant": tenant_id,
                "day": snapshot["business_day"],
                "location": location_id,
                "measure": measure,
                "at": point,
                "from": beginning,
                "until": ending,
            },
            default=str,
            sort_keys=True,
        ).encode()
    ).hexdigest()
    cursor_id = ""
    if after:
        try:
            if not isinstance(after, str) or len(after) > 4096:
                raise ValueError("Invalid cursor size.")
            cursor = json.loads(base64.b64decode(after, altchars=b"-_", validate=True))
            if (
                set(cursor) != {"scope", "after"}
                or cursor["scope"] != scope
                or not isinstance(cursor["after"], str)
            ):
                raise ValueError("Cursor belongs to another query.")
            cursor_id = cursor["after"]
        except (ValueError, TypeError, KeyError) as error:
            raise core.InvalidOperation(
                code="shipping_observation_cursor_invalid"
            ) from error
    page = [row for row in matched if row["order_id"] > cursor_id][: limit + 1]
    has_more = len(page) > limit
    page = page[:limit]
    next_after = (
        base64.urlsafe_b64encode(
            json.dumps(
                {
                    "scope": scope,
                    "after": page[-1]["order_id"],
                }
            ).encode()
        ).decode()
        if has_more
        else None
    )
    # reality-rule: shipping_performance.supporting.result
    return {
        "items": _json_value(page),
        "scope": "company_unplanned" if measure == "unplanned" else "shipping_cohort",
        "total": len(matched) if available else None,
        "has_more": has_more,
        "next_after": next_after,
        "observed_at": snapshot["observed_at"],
        "basis_key": snapshot["basis_key"],
        "coverage": snapshot["coverage"],
        "totals": snapshot["totals"],
        "re_evaluated": basis_key is not None and basis_key != snapshot["basis_key"],
    }
