"""Tenant-scoped evidence relations, before any aggregation or pagination."""

from sqlalchemy import String, and_, case, cast, exists, func, literal, select, true
from sqlalchemy.dialects.postgresql import JSONB

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    Item,
    Party,
    SourceRecord,
)


def order_relation(tenant_id: str, definition):
    sales = definition.dataset.startswith("sales")
    lines = definition.dataset.endswith("_lines")
    party_key = "customer_id" if sales else "supplier_id"
    party_label = "customer" if sales else "supplier"
    time = definition.time.timezone if definition.time else "UTC"
    local = func.timezone(time, Document.ordered_at)
    source_payload = cast(SourceRecord.payload, JSONB)
    line_payload = cast(DocumentLine.payload, JSONB)
    raw_lines = (
        func.jsonb_array_elements(
            func.coalesce(source_payload["lines"], cast(literal("[]"), JSONB))
        )
        .table_valued("value", with_ordinality="ordinality")
        .render_derived(name="analytics_source_lines")
    )
    raw_value = cast(raw_lines.c.value, JSONB)
    raw_identity = func.coalesce(
        func.nullif(raw_value["source_line_id"].astext, ""),
        cast(raw_lines.c.ordinality, String),
    )
    manual_lines = (
        select(
            SourceRecord.id.label("source_record_id"),
            raw_identity.label("source_line_id"),
            func.bool_or(raw_value["quantity"].astext.is_not(None)).label(
                "has_quantity"
            ),
            func.bool_or(raw_value["gross_amount"].astext.is_not(None)).label(
                "has_gross_amount"
            ),
            func.bool_or(raw_value["unit_price"].astext.is_not(None)).label(
                "has_unit_price"
            ),
        )
        .select_from(SourceRecord)
        .join(raw_lines, true())
        .where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == "manual",
        )
        .group_by(SourceRecord.id, raw_identity)
        .subquery()
    )

    def manual_has(field):
        return (SourceRecord.source_system == "manual") & manual_lines.c["has_" + field]

    stated_order = case(
        (
            source_payload["gross_amount"].astext.is_not(None)
            | source_payload["total_price"].astext.is_not(None),
            Document.gross_amount,
        ),
        else_=None,
    )  # noqa: W601
    columns = [
        (DocumentLine.id if lines else Document.id).label("record_id"),
        literal("document_line" if lines else "document").label("record_kind"),
        literal(tenant_id).label("analytics_tenant"),
        Document.id.label("order_id"),
        Document.number.label("order"),
        Document.party_id.label(party_key),
        Party.name.label(party_label),
        Document.ordered_at.label("ordered_at"),
        Document.currency.label("currency"),
        Document.sales_channel.label("sales_channel"),
        Document.source_record_id.label("source_record_id"),
        func.to_char(local, "YYYY-MM-DD").label("ordered_day"),
        func.to_char(local, 'IYYY-"W"IW').label("ordered_week"),
        func.to_char(local, "YYYY-MM").label("ordered_month"),
        func.to_char(local, 'YYYY-"Q"Q').label("ordered_quarter"),
        func.to_char(local, "YYYY").label("ordered_year"),
        stated_order.label("stated_order_amount"),
    ]
    if lines:
        columns += [
            DocumentLine.item_id.label("product_id"),
            Item.name.label("product"),
            DocumentLine.unit.label("unit"),
            case(
                (
                    line_payload["quantity"].astext.is_not(None)
                    | manual_has("quantity")
                    | Document.source_record_id.is_(None),
                    DocumentLine.quantity,
                ),
                else_=None,
            ).label("ordered_quantity"),
            case(
                (
                    line_payload["gross_amount"].astext.is_not(None)
                    | manual_has("gross_amount"),
                    DocumentLine.gross_amount,
                ),
                else_=None,
            ).label("stated_line_amount"),  # noqa: W601
            case(
                (
                    line_payload["unit_price"].astext.is_not(None)
                    | line_payload["price"].astext.is_not(None)
                    | manual_has("unit_price"),
                    DocumentLine.unit_price,
                ),
                else_=None,
            ).label("unit_price"),
        ]  # noqa: W601
    statement = (
        select(*columns)
        .select_from(Document)
        .outerjoin(
            Party, and_(Party.id == Document.party_id, Party.tenant_id == tenant_id)
        )
        .outerjoin(
            SourceRecord,
            and_(
                SourceRecord.id == Document.source_record_id,
                SourceRecord.tenant_id == tenant_id,
            ),
        )
    )
    if lines:
        statement = (
            statement.join(
                DocumentLine,
                and_(
                    DocumentLine.document_id == Document.id,
                    DocumentLine.tenant_id == tenant_id,
                ),
            )
            .outerjoin(
                Item, and_(Item.id == DocumentLine.item_id, Item.tenant_id == tenant_id)
            )
            .outerjoin(
                manual_lines,
                and_(
                    manual_lines.c.source_record_id == SourceRecord.id,
                    manual_lines.c.source_line_id == DocumentLine.source_line_id,
                ),
            )
        )
    statement = statement.where(
        Document.tenant_id == tenant_id,
        Document.type == ("sales_order" if sales else "purchase_order"),
    )
    if definition.cancellation == "exclude_fully_cancelled":
        related = and_(
            Commitment.tenant_id == tenant_id, Commitment.document_id == Document.id
        )
        any_commitment = exists(select(Commitment.id).where(related))
        not_cancelled = exists(
            select(Commitment.id).where(related, Commitment.status != "cancelled")
        )
        statement = statement.where(~any_commitment | not_cancelled)
    return statement.subquery()


def customer_relation(tenant_id, definition):
    orders = order_relation(
        tenant_id, definition.model_copy(update={"dataset": "sales_orders"})
    )
    return (
        select(
            literal(tenant_id).label("analytics_tenant"),
            orders.c.customer_id,
            func.min(orders.c.customer).label("customer"),
            func.min(orders.c.ordered_at).label("first_order_at"),
            func.max(orders.c.ordered_at).label("last_order_at"),
        )
        .where(orders.c.customer_id.is_not(None))
        .group_by(orders.c.customer_id)
        .subquery()
    )


def pair_relation(session, tenant_id, definition):
    from datetime import UTC, datetime

    from reality.domain.analytics import resolve_window
    from reality.services.analytics.execution import AnalyticsError

    source = order_relation(
        tenant_id, definition.model_copy(update={"dataset": "sales_order_lines"})
    )
    conditions = [source.c.product_id.is_not(None)]
    if definition.time:
        start, end = resolve_window(definition.time, datetime.now(UTC))
        conditions.extend([source.c.ordered_at >= start, source.c.ordered_at < end])
    products = (
        select(
            source.c.order_id,
            source.c.customer_id,
            source.c.product_id,
            source.c.ordered_at,
        )
        .where(*conditions)
        .distinct()
        .subquery()
    )
    sizes = (
        select(func.count().label("n"))
        .select_from(products)
        .group_by(products.c.order_id)
        .subquery()
    )
    maximum, pairs = session.execute(
        select(func.max(sizes.c.n), func.sum(sizes.c.n * (sizes.c.n - 1) / 2))
    ).one()
    if (maximum or 0) > 100 or (pairs or 0) > 1000000:
        raise AnalyticsError(
            "Product pairing exceeds its bound. Narrow the time window.",
            "query_too_broad",
        )
    other = products.alias()
    return (
        select(
            literal(tenant_id).label("analytics_tenant"),
            products.c.order_id,
            products.c.customer_id,
            products.c.product_id,
            other.c.product_id.label("product_b_id"),
            products.c.ordered_at,
        )
        .join(
            other,
            and_(
                other.c.order_id == products.c.order_id,
                products.c.product_id < other.c.product_id,
            ),
        )
        .subquery()
    )


def supplier_history_relation(tenant_id, definition):
    from datetime import UTC, datetime

    from reality.domain.analytics import resolve_window

    source = order_relation(
        tenant_id, definition.model_copy(update={"dataset": "purchase_order_lines"})
    )
    conditions = [source.c.product_id.is_not(None)]
    if definition.time:
        start, end = resolve_window(definition.time, datetime.now(UTC))
        conditions += [source.c.ordered_at >= start, source.c.ordered_at < end]
    count = func.count(func.distinct(source.c.supplier_id))
    return (
        select(
            source.c.product_id,
            func.min(source.c.product).label("product"),
            count.label("observed_supplier_count"),
            case((count == 1, func.min(source.c.supplier_id)), else_=None).label(
                "supplier_id"
            ),
            func.max(source.c.ordered_at).label("ordered_at"),
        )
        .where(*conditions)
        .group_by(source.c.product_id)
        .subquery()
    )


def source_coverage(session, tenant_id):
    """A pending intake version does not erase already interpreted order evidence."""
    from sqlalchemy.orm import aliased

    newer = aliased(SourceRecord)
    has_newer = exists(
        select(newer.id).where(
            newer.tenant_id == tenant_id,
            newer.source_system == SourceRecord.source_system,
            newer.source_type == SourceRecord.source_type,
            newer.external_id == SourceRecord.external_id,
            newer.version > SourceRecord.version,
        )
    )
    count = session.scalar(
        select(func.count(Document.id))
        .join(
            SourceRecord,
            and_(
                SourceRecord.id == Document.source_record_id,
                SourceRecord.tenant_id == tenant_id,
            ),
        )
        .where(
            Document.tenant_id == tenant_id,
            Document.type.in_(["sales_order", "purchase_order"]),
            has_newer,
        )
    )
    return {
        "scope": "all_retained_company_orders",
        "retained_orders_with_newer_sources": count,
        "policy": "interpreted_document_identity; pending_or_reviewed_source_versions_do_not_replace_retained_evidence",
        "price_basis": "as_stated; unknown_tax_basis_is_not_inferred",
    }
