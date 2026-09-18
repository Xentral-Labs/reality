"""Tenant-constrained SQL candidates; matching always precedes keyset pagination."""

import re

from sqlalchemy import (
    String,
    and_,
    case,
    exists,
    func,
    literal,
    select,
    tuple_,
    union_all,
)
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.orm import aliased

from reality.db.analytics import AnalyticsReport
from reality.db.core import (
    Commitment,
    Document,
    Fact,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    Reservation,
    Shipment,
    ShipmentPackage,
    SourceRecord,
)
from reality.domain.search import FAMILIES, SearchRequest, normalize, words

DOCUMENT_FAMILIES = {
    "sales_order": "customer_order",
    "purchase_order": "supplier_order",
    "sales_invoice": "customer_invoice",
    "supplier_invoice": "supplier_invoice",
    "credit_note": "customer_credit",
    "supplier_credit_note": "supplier_credit",
}
FAMILY_ORDER = {
    family: i
    for i, family in enumerate(
        family for group in FAMILIES.values() for family in group
    )
}


def payment_eligibility(tenant_id, cash=LedgerEntry):
    """The canonical payment row needs cash, its held document and a control entry."""
    control = aliased(LedgerEntry)
    document = aliased(Document)
    return and_(
        cash.tenant_id == tenant_id,
        cash.account == "cash",
        exists(
            select(document.id).where(
                document.tenant_id == tenant_id, document.id == cash.document_id
            )
        ),
        exists(
            select(control.id).where(
                control.tenant_id == tenant_id,
                control.posting_group_id == cash.posting_group_id,
                control.account.in_(("accounts_receivable", "accounts_payable")),
            )
        ),
    )


def _word_pattern(token, fuzzy=True):
    literal_word = re.escape(token)
    alternatives = [literal_word + "[[:alnum:]]*"]
    if fuzzy and len(token) >= 5:
        # These alternatives are a complete single-edit superset, never a sampled pool.
        for i in range(len(token)):
            before, after = re.escape(token[:i]), re.escape(token[i + 1 :])
            alternatives.extend([before + after, before + "[[:alnum:]]" + after])
            alternatives.append(
                re.escape(token[:i]) + "[[:alnum:]]" + re.escape(token[i:])
            )
            if i + 1 < len(token):
                alternatives.append(
                    re.escape(token[:i] + token[i + 1] + token[i] + token[i + 2 :])
                )
        alternatives.append(literal_word + "[[:alnum:]]")
    return "(^|[^[:alnum:]])(" + "|".join(alternatives) + ")($|[^[:alnum:]])"


def _possible_match(query, labels, references):
    from sqlalchemy import or_

    folded = normalize(query.strip())
    terms = words(query)
    reference_matches = [
        func.reality_search_normalize_v1(column).startswith(folded, autoescape=True)
        for column in references
    ]
    exact_labels = [
        func.reality_search_normalize_v1(column) == folded for column in labels
    ]
    label_matches = (
        [
            and_(
                *[
                    or_(
                        *[
                            func.reality_search_normalize_v1(column).op("~")(
                                _word_pattern(token)
                            )
                            for column in labels
                        ]
                    )
                    for token in terms
                ]
            )
        ]
        if labels and terms
        else []
    )
    return or_(*reference_matches, *exact_labels, *label_matches)


def _tier_match(query, labels, references, tier):
    from sqlalchemy import false, or_

    raw = or_(false(), *[column == query.strip() for column in references])
    folded = normalize(query.strip())
    exact = or_(
        *[
            func.reality_search_normalize_v1(column) == folded
            for column in [*labels, *references]
        ]
    )
    terms = words(query)

    def name_match(fuzzy):
        return (
            and_(
                *[
                    or_(
                        *[
                            func.reality_search_normalize_v1(column).op("~")(
                                _word_pattern(token, fuzzy)
                            )
                            for column in labels
                        ]
                    )
                    for token in terms
                ]
            )
            if terms and labels
            else false()
        )

    prefix = or_(
        *[
            func.reality_search_normalize_v1(column).startswith(folded, autoescape=True)
            for column in references
        ],
        name_match(False),
    )
    if tier == 0:
        return raw
    if tier == 1:
        return and_(~func.coalesce(raw, False), exact)
    if tier == 2:
        return and_(~func.coalesce(raw, False), ~func.coalesce(exact, False), prefix)
    return and_(
        ~func.coalesce(raw, False),
        ~func.coalesce(exact, False),
        ~func.coalesce(prefix, False),
        name_match(True),
    )


def candidate_query(
    tenant_id: str,
    owner_id: str | None,
    request: SearchRequest,
    *,
    allowed_kinds=None,
    identity=None,
    tier_filter=None,
    branch_limit=None,
    branch_after=None,
):
    statements = []
    families = [request.family] if request.family else FAMILIES[request.provider]

    def add(
        model,
        family,
        label,
        labels,
        refs,
        *,
        predicates=(),
        joins=(),
        secondary=None,
        kind=None,
        exact_only=False,
    ):
        kind = kind or model.__tablename__
        if identity is not None and identity[0] != kind:
            return
        if allowed_kinds is not None and kind not in allowed_kinds:
            return
        display = func.coalesce(func.nullif(label, ""), model.id)
        names = array([func.coalesce(value, "") for value in labels], type_=String)
        identifiers = array(
            [model.id, *[func.coalesce(value, "") for value in refs]], type_=String
        )
        tier = (
            case((model.id == request.query.strip(), 0))
            if exact_only
            else func.reality_search_tier_v1(request.query, names, identifiers)
        )
        matching = (
            (
                (model.id == request.query.strip())
                if tier_filter in (None, 0)
                else literal(False)
            )
            if exact_only
            else _tier_match(request.query, labels, [model.id, *refs], tier_filter)
            if tier_filter is not None
            else _possible_match(request.query, labels, [model.id, *refs])
        )
        if tier_filter is not None:
            tier = literal(tier_filter)
        statement = select(
            model.id.label("id"),
            literal(kind).label("kind"),
            literal(family).label("family"),
            display.label("label"),
            func.coalesce(secondary, "").label("secondary"),
            tier.label("tier"),
        ).select_from(model)
        for target, condition in joins:
            statement = statement.outerjoin(target, condition)
        statements.append(
            statement.where(
                model.tenant_id == tenant_id,
                matching,
                *predicates,
                model.id == identity[1] if identity else True,
            )
        )

    for family in families:
        if family == "party":
            add(
                Party,
                family,
                Party.name,
                [Party.name],
                [Party.accounting_code],
                secondary=Party.accounting_code,
            )
        elif family == "item":
            add(Item, family, Item.name, [Item.name], [Item.sku], secondary=Item.sku)
        elif family == "location":
            add(Location, family, Location.name, [Location.name], [])
        elif family in DOCUMENT_FAMILIES.values() or family == "document":
            predicate = (
                Document.type.not_in(DOCUMENT_FAMILIES)
                if family == "document"
                else Document.type
                == next(
                    key for key, value in DOCUMENT_FAMILIES.items() if value == family
                )
            )
            joins = [
                (
                    Party,
                    and_(Party.tenant_id == tenant_id, Party.id == Document.party_id),
                ),
                (
                    SourceRecord,
                    and_(
                        SourceRecord.tenant_id == tenant_id,
                        SourceRecord.id == Document.source_record_id,
                    ),
                ),
            ]
            add(
                Document,
                family,
                Document.number,
                [Party.name] if family != "document" else [],
                [
                    Document.number,
                    Document.customer_reference,
                    SourceRecord.external_id,
                ],
                predicates=[predicate],
                joins=joins,
                secondary=Party.name,
            )
        elif family == "payment":
            add(
                LedgerEntry,
                family,
                Document.number,
                [Party.name],
                [Document.number, Document.customer_reference],
                predicates=[payment_eligibility(tenant_id)],
                joins=[
                    (
                        Document,
                        and_(
                            Document.tenant_id == tenant_id,
                            Document.id == LedgerEntry.document_id,
                        ),
                    ),
                    (
                        Party,
                        and_(
                            Party.tenant_id == tenant_id,
                            Party.id == LedgerEntry.party_id,
                        ),
                    ),
                ],
                secondary=Party.name,
            )
        elif family == "shipment":
            # EXISTS keeps package matches indexed without multiplying shipments.
            from sqlalchemy import or_

            references = [Shipment.id, SourceRecord.external_id]
            labels = [Party.name]
            matches = []
            for level in range(4):
                base_match = _tier_match(request.query, labels, references, level)
                package_match = exists(
                    select(ShipmentPackage.id).where(
                        ShipmentPackage.tenant_id == tenant_id,
                        ShipmentPackage.shipment_id == Shipment.id,
                        _tier_match(
                            request.query, [], [ShipmentPackage.tracking_number], level
                        ),
                    )
                )
                matches.append(func.coalesce(or_(base_match, package_match), False))
            conditions = [
                and_(matches[level], *[~matches[prior] for prior in range(level)])
                for level in range(4)
            ]
            tier = (
                literal(tier_filter)
                if tier_filter is not None
                else case(
                    *[(condition, level) for level, condition in enumerate(conditions)]
                )
            )
            if (allowed_kinds is None or "shipment" in allowed_kinds) and (
                identity is None or identity[0] == "shipment"
            ):
                statements.append(
                    select(
                        Shipment.id.label("id"),
                        literal("shipment").label("kind"),
                        literal(family).label("family"),
                        func.coalesce(SourceRecord.external_id, Shipment.id).label(
                            "label"
                        ),
                        func.coalesce(Party.name, "").label("secondary"),
                        tier.label("tier"),
                    )
                    .outerjoin(
                        Party,
                        and_(
                            Party.tenant_id == tenant_id,
                            Party.id == Shipment.counterparty_id,
                        ),
                    )
                    .outerjoin(
                        SourceRecord,
                        and_(
                            SourceRecord.tenant_id == tenant_id,
                            SourceRecord.id == Shipment.source_record_id,
                        ),
                    )
                    .where(
                        Shipment.tenant_id == tenant_id,
                        Shipment.id == identity[1] if identity else True,
                        conditions[tier_filter] if tier_filter is not None else True,
                    )
                )
        elif family == "source_record":
            add(
                SourceRecord,
                family,
                SourceRecord.external_id,
                [],
                [SourceRecord.external_id],
                secondary=func.concat(
                    SourceRecord.source_system,
                    " · ",
                    SourceRecord.source_type,
                    " · v",
                    SourceRecord.version,
                ),
            )
        elif family == "private_report":
            add(
                AnalyticsReport,
                family,
                AnalyticsReport.name,
                [AnalyticsReport.name],
                [],
                predicates=[
                    AnalyticsReport.owner_user_id == owner_id,
                    AnalyticsReport.kind == "graph",
                    AnalyticsReport.deleted_at.is_(None),
                ],
            )
        else:
            model = {
                "commitment": Commitment,
                "reservation": Reservation,
                "movement": Movement,
                "fact": Fact,
                "ledger_entry": LedgerEntry,
            }[family]
            add(
                model,
                family,
                model.id,
                [],
                [],
                exact_only=True,
                predicates=[~payment_eligibility(tenant_id)]
                if family == "ledger_entry"
                else [],
            )
    if not statements:
        return None
    if tier_filter is not None:
        bounded = []
        for statement in statements:
            family_name = statement.selected_columns.family.element.value
            # Joined evidence benefits from complete predicate materialization. Direct
            # label families can stop on their ordered index without collecting a
            # very broad (potentially 100,000-row) matching set first.
            if family_name not in {"party", "item", "location", "private_report"}:
                matched = statement.cte().prefix_with("MATERIALIZED")
                statement = select(matched)
            columns = statement.selected_columns
            physical_key = columns.kind + literal(":") + columns.id
            context_order = (
                case((physical_key.in_(request.context), 0), else_=1)
                if request.context
                else literal(1)
            )
            recent_order = (
                case((physical_key.in_(request.recent_keys), 0), else_=1)
                if request.recent_keys
                else literal(1)
            )
            statement = statement.where(columns.tier == tier_filter).order_by(
                *([context_order] if request.context else []),
                *([recent_order] if request.recent_keys else []),
                func.reality_search_normalize_v1(columns.label).collate("C"),
                columns.id,
            )
            if branch_after is not None:
                statement = statement.where(
                    tuple_(
                        columns.tier,
                        context_order,
                        recent_order,
                        literal(FAMILY_ORDER[family_name]),
                        func.reality_search_normalize_v1(columns.label).collate("C"),
                        columns.kind,
                        columns.id,
                    )
                    > tuple_(*branch_after)
                )
            if branch_limit is not None:
                statement = statement.limit(branch_limit)
            bounded.append(select(statement.subquery()))
        statements = bounded
    candidates = union_all(*statements).subquery("search_candidates")
    key = candidates.c.kind + literal(":") + candidates.c.id
    ranked = (
        select(
            candidates,
            case((key.in_(request.context), 0), else_=1).label("context_order"),
            case((key.in_(request.recent_keys), 0), else_=1).label("recent_order"),
            case(FAMILY_ORDER, value=candidates.c.family, else_=999).label(
                "family_order"
            ),
            func.reality_search_normalize_v1(candidates.c.label)
            .collate("C")
            .label("normalized_label"),
        )
        .where(candidates.c.tier.is_not(None))
        .subquery("search_ranked")
    )
    return ranked


def page_query(candidates, limit, after=None):
    columns = [
        candidates.c[name]
        for name in (
            "tier",
            "context_order",
            "recent_order",
            "family_order",
            "normalized_label",
            "kind",
            "id",
        )
    ]
    statement = select(candidates)
    if after is not None:
        statement = statement.where(tuple_(*columns) > tuple_(*after))
    return statement.order_by(*columns).limit(limit + 1)
