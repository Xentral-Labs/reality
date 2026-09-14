from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from reality.services.projections import FULFILLMENT_QUEUE, OPEN_FINANCIAL_ITEMS
from reality.web.read_models import (
    commitment_page,
    document_page,
    inventory_page,
    journal_page,
    movement_page,
    payment_page,
    projection_page,
    projection_totals,
    reservation_page,
)

from .dataset import SENTINEL, DatasetHandle
from .query_evidence import capture_queries, summarize_queries

REQUIRED_FAMILIES = (
    "Orders",
    "Commitments",
    "Inventory",
    "Reservations",
    "Movements",
    "Open items",
    "Payments",
    "Journal",
    "Documents",
)


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    family: str
    requirements: tuple[str, ...]


@dataclass(frozen=True)
class CaseObservation:
    case_id: str
    register_family: str
    duration_ms: float
    outcome: str
    requirements: tuple[str, ...]
    observations: dict[str, Any]
    query_evidence: list[dict[str, object]]


def build_case_catalog() -> tuple[BenchmarkCase, ...]:
    requirements = (
        "FR-003",
        "FR-004",
        "FR-005",
        "FR-006",
        "FR-008",
        "FR-009",
        "DR-003",
    )
    return tuple(
        BenchmarkCase(
            f"register-{index:02d}-{family.lower().replace(' ', '-')}",
            family,
            requirements,
        )
        for index, family in enumerate(REQUIRED_FAMILIES, start=1)
    )


def _ids(family: str, rows: list[Any]) -> list[str]:
    if family in {"Orders", "Open items"}:
        return [str(row.get("order_key") or row.get("document_id")) for row in rows]
    if family == "Commitments":
        return [row[0].id for row in rows]
    if family == "Inventory":
        return [row["item"].id for row in rows]
    if family == "Reservations":
        return [row["reservation"].id for row in rows]
    if family == "Movements":
        return [row["movement"].id for row in rows]
    if family == "Payments":
        return [row["cash_entry"].id for row in rows]
    if family == "Journal":
        return [row.id for row in rows]
    if family == "Documents":
        return [row[0].id for row in rows]
    raise AssertionError(f"Unknown register family: {family}")


def _assert_tenant(family: str, rows: list[Any], tenant_id: str) -> None:
    for row in rows:
        values = (
            row.values()
            if isinstance(row, dict)
            else row
            if isinstance(row, tuple)
            else (row,)
        )
        for value in values:
            tenant = getattr(value, "tenant_id", tenant_id)
            if tenant is not None:
                assert tenant == tenant_id, f"{family} returned another tenant"
    assert SENTINEL not in json.dumps(_ids(family, rows))


def _callable(
    family: str, session: Session, dataset: DatasetHandle
) -> tuple[Callable[..., Any], dict[str, Any]]:
    last = dataset.profile.order_count - 1
    if family == "Orders":
        return projection_page, {
            "session": session,
            "tenant_id": dataset.tenant_id,
            "projection_name": FULFILLMENT_QUEUE,
            "query": f"ORDER-{last:06d}",
        }
    if family == "Commitments":
        return commitment_page, {
            "session": session,
            "tenant_id": dataset.tenant_id,
            "status": "open",
            "query": "Benchmark Item 0119",
        }
    if family == "Inventory":
        return inventory_page, {
            "session": session,
            "tenant_id": dataset.tenant_id,
            "query": "SKU-0149",
        }
    if family == "Reservations":
        return reservation_page, {
            "session": session,
            "tenant_id": dataset.tenant_id,
            "query": dataset.commitment_ids[min(119, len(dataset.commitment_ids) - 1)],
        }
    if family == "Movements":
        return movement_page, {
            "session": session,
            "tenant_id": dataset.tenant_id,
            "query": dataset.item_ids[-1],
        }
    if family == "Open items":
        return projection_page, {
            "session": session,
            "tenant_id": dataset.tenant_id,
            "projection_name": OPEN_FINANCIAL_ITEMS,
            "query": "INV-00119",
        }
    if family == "Payments":
        return payment_page, {
            "session": session,
            "tenant_id": dataset.tenant_id,
            "query": "payment-119",
        }
    if family == "Journal":
        return journal_page, {
            "session": session,
            "tenant_id": dataset.tenant_id,
            "account": "cash",
        }
    if family == "Documents":
        return document_page, {
            "session": session,
            "tenant_id": dataset.tenant_id,
            "query": f"ORDER-{last:06d}",
        }
    raise AssertionError(f"Unknown register family: {family}")


def _unpack(family: str, result: Any) -> tuple[list[Any], Any, Any]:
    if family == "Journal":
        rows, pager, totals = result
        return (
            rows,
            pager,
            [(currency, str(debit), str(credit)) for currency, debit, credit in totals],
        )
    rows, pager = result
    return rows, pager, None


def _boundary_filters(family: str, dataset: DatasetHandle) -> dict[str, Any]:
    business_date = dataset.profile.business_date.isoformat()
    return {
        "Orders": {"source_system": "benchmark-commerce", "date_from": business_date},
        "Commitments": {
            "commitment_type": "customer_delivery",
            "due_from": business_date,
        },
        "Inventory": {"stock_state": "available", "available_min": Decimal(0)},
        "Reservations": {"status": "active", "date_from": business_date},
        "Movements": {"movement_type": "opening_stock", "date_from": business_date},
        "Open items": {"flow": "receivable", "amount_min": Decimal(1)},
        "Payments": {"direction": "incoming", "date_from": business_date},
        "Journal": {"side": "debit", "date_from": business_date},
        "Documents": {
            "document_type": "sales_order",
            "date_from": business_date,
            "amount_min": Decimal(1),
        },
    }[family]


def run_case(
    session: Session, dataset: DatasetHandle, case: BenchmarkCase
) -> CaseObservation:
    function, selective = _callable(case.family, session, dataset)
    common = {
        key: value
        for key, value in selective.items()
        if key not in {"query", "account"}
    }
    started = perf_counter()
    with capture_queries(session) as queries:
        default_rows, default_pager, aggregate = _unpack(
            case.family, function(**common)
        )
        max_rows, max_pager, _ = _unpack(case.family, function(**common, size=999))
        page_two_rows, _, _ = _unpack(case.family, function(**common, page=2, size=50))
        selected_rows, selected_pager, selected_aggregate = _unpack(
            case.family, function(**selective)
        )
        zero_rows, zero_pager, _ = _unpack(
            case.family, function(**common, query="NO-SUCH-BENCHMARK-RECORD")
        )
        minimum_rows, minimum_pager, _ = _unpack(
            case.family, function(**common, size=0)
        )
        negative_rows, negative_pager, _ = _unpack(
            case.family, function(**common, size=-1)
        )
        filtered_rows, filtered_pager, _ = _unpack(
            case.family, function(**common, **_boundary_filters(case.family, dataset))
        )
        if case.family == "Open items":
            aggregate = [
                tuple(str(value) for value in row)
                for row in projection_totals(
                    session,
                    dataset.tenant_id,
                    OPEN_FINANCIAL_ITEMS,
                    ("gross", "settled", "open"),
                )
            ]
        elif case.family == "Payments":
            from reality.services.projections import PAYMENTS

            aggregate = [
                tuple(str(value) for value in row)
                for row in projection_totals(
                    session,
                    dataset.tenant_id,
                    PAYMENTS,
                    ("amount", "allocated", "unallocated"),
                )
            ]
    duration = (perf_counter() - started) * 1000

    assert len(default_rows) == min(50, default_pager.total)
    assert len(max_rows) <= 100 and max_pager.size == 100
    assert not zero_rows and zero_pager.total == 0
    assert len(minimum_rows) <= 1 and minimum_pager.size == 1
    assert len(negative_rows) <= 1 and negative_pager.size == 1
    assert filtered_rows and filtered_pager.total >= len(filtered_rows)
    assert set(_ids(case.family, default_rows)).isdisjoint(
        _ids(case.family, page_two_rows)
    )
    if selective != common:
        assert selected_pager.total >= 1
    if case.family in {"Open items", "Payments", "Journal"}:
        assert aggregate
    for rows in (
        default_rows,
        max_rows,
        page_two_rows,
        selected_rows,
        minimum_rows,
        negative_rows,
        filtered_rows,
    ):
        _assert_tenant(case.family, rows, dataset.tenant_id)
    assert queries and any(row.is_count for row in queries)
    assert any(row.has_limit for row in queries)
    assert all(
        row.has_tenant_scope
        for row in queries
        if " tenant" not in row.statement.lower()
    )
    unbounded = [row.statement for row in queries if not row.is_bounded]
    assert not unbounded, f"{case.family} materialized unbounded queries: {unbounded}"

    return CaseObservation(
        case.case_id,
        case.family,
        round(duration, 3),
        "passed",
        case.requirements,
        {
            "default_count": len(default_rows),
            "default_total": default_pager.total,
            "max_count": len(max_rows),
            "selected_total": selected_pager.total,
            "filtered_total": filtered_pager.total,
            "page_one_ids": _ids(case.family, default_rows),
            "page_two_ids": _ids(case.family, page_two_rows),
            "aggregate": aggregate,
            "selected_aggregate": selected_aggregate,
        },
        summarize_queries(queries),
    )


def run_catalog(session: Session, dataset: DatasetHandle) -> list[CaseObservation]:
    return [run_case(session, dataset, case) for case in build_case_catalog()]
