"""Typed analysis objects preserve evidence boundaries, tenancy and recorded values."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from reality.db.core import Document, DocumentLine
from reality.domain.traversal import Traversal
from reality.services.analytics.graph_model import reporting_catalog
from reality.services.analytics.traversal import run_traversal


def ask(session, tenant, **query):
    return run_traversal(session, tenant, Traversal.model_validate(query))


def document(session, tenant, kind, identity, amount="12"):
    row = Document(
        id=identity,
        tenant_id=tenant,
        source_record_id=None,
        type=kind,
        number="SAME-NUMBER",
        gross_amount=Decimal(amount),
    )
    session.add(row)
    session.flush()
    return row


def position(session, tenant, doc, identity, billed=None):
    row = DocumentLine(
        id=identity,
        tenant_id=tenant,
        document_id=doc.id,
        source_line_id=None,
        item_id=None,
        sku="X",
        quantity=Decimal(2),
        gross_amount=Decimal(7),
        billed_document_line_id=billed,
    )
    session.add(row)
    session.flush()
    return row


def test_line_root_is_scoped_to_parent_type_and_tenant(session, business):
    from reality.services.core import create_tenant

    tenant = business.tenant.id
    other = create_tenant(session, "Neighbor")
    sale = document(session, tenant, "sales_order", "scope-sale")
    purchase = document(session, tenant, "purchase_order", "scope-purchase")
    foreign = document(session, other.id, "sales_order", "scope-foreign")
    position(session, tenant, sale, "sale-line")
    position(session, tenant, purchase, "purchase-line")
    position(session, tenant, foreign, "malformed-cross-tenant-line")
    result = ask(
        session,
        tenant,
        **{"from": "order_line", "as": "o", "group_by": [{"field": "o.id"}]},
    )
    assert [row["o.id"] for row in result.rows] == ["sale-line"]


def test_reverse_billed_line_follows_the_referencing_invoice(session, business):
    tenant = business.tenant.id
    sale = document(session, tenant, "sales_order", "reverse-sale")
    invoice = document(session, tenant, "sales_invoice", "reverse-invoice")
    line = position(session, tenant, sale, "reverse-order-line")
    position(session, tenant, invoice, "reverse-invoice-line", line.id)
    result = ask(
        session,
        tenant,
        **{
            "from": "order_line",
            "as": "o",
            "follow": [{"edge": "bills", "direction": "in", "as": "i"}],
            "group_by": [{"field": "o.id"}, {"field": "i.id"}],
        },
    )
    assert list(result.rows) == [{"o.id": line.id, "i.id": "reverse-invoice-line"}]


def test_observed_vocabulary_is_scoped_to_node_type(session, business):
    tenant = business.tenant.id
    sale = document(session, tenant, "sales_order", "enum-sale")
    sale.status = "sales-only"
    purchase = document(session, tenant, "purchase_order", "enum-purchase")
    purchase.status = "purchase-only"
    session.flush()
    node = reporting_catalog("order", session=session, tenant_id=tenant)["nodes"][0]
    status = next(prop for prop in node["properties"] if prop["key"] == "status")
    assert status["values"] == ["sales-only"]


DOCUMENT_TYPES = {
    "sales_invoice": "sales_invoice",
    "customer_credit_note": "credit_note",
    "purchase_order": "purchase_order",
    "supplier_invoice": "supplier_invoice",
    "supplier_credit_note": "supplier_credit_note",
    "customer_payment": "customer_payment",
    "supplier_payment": "supplier_payment",
    "customer_refund": "customer_refund",
    "supplier_refund": "supplier_refund",
    "customer_settlement_adjustment": "customer_settlement_adjustment",
    "supplier_settlement_adjustment": "supplier_settlement_adjustment",
}


@pytest.mark.parametrize("node,kind", DOCUMENT_TYPES.items())
def test_explicit_document_types_preserve_received_values(
    session, business, node, kind
):
    from reality.services.core import create_tenant

    tenant = business.tenant.id
    other = create_tenant(session, "Other company")
    for index, typ in enumerate(DOCUMENT_TYPES.values()):
        document(
            session, tenant, typ, f"typed-{index}", "-7.25" if typ == kind else "999"
        )
    document(session, other.id, kind, "typed-other-tenant", "999999")
    result = ask(
        session,
        tenant,
        **{
            "from": node,
            "as": "o",
            "group_by": [{"field": "o.currency"}],
            "measures": [node + "_amount", node + "_count"],
        },
    )
    assert len(result.rows) == 1
    assert Decimal(result.rows[0][node + "_amount"]) == Decimal("-7.25")
    assert result.rows[0][node + "_count"] == 1


@pytest.mark.parametrize(
    "node",
    [
        "sales_invoice",
        "customer_credit_note",
        "purchase_order",
        "supplier_invoice",
        "supplier_credit_note",
    ],
)
def test_typed_positions_are_scoped_when_root_or_joined(session, business, node):
    tenant = business.tenant.id
    for index, kind in enumerate(DOCUMENT_TYPES.values()):
        doc = document(session, tenant, kind, f"line-doc-{index}")
        position(session, tenant, doc, f"line-{kind}")
    expected = "line-" + DOCUMENT_TYPES[node]
    root = ask(
        session,
        tenant,
        **{"from": node + "_line", "as": "o", "group_by": [{"field": "o.id"}]},
    )
    assert [row["o.id"] for row in root.rows] == [expected]
    joined = ask(
        session,
        tenant,
        **{
            "from": node,
            "as": "d",
            "follow": [{"edge": node + "_contains", "as": "o"}],
            "group_by": [{"field": "o.id"}],
        },
    )
    assert [row["o.id"] for row in joined.rows] == [expected]


def test_legacy_invoice_still_contains_customer_credits(session, business):
    tenant = business.tenant.id
    for kind in [
        "sales_invoice",
        "credit_note",
        "supplier_invoice",
        "supplier_credit_note",
    ]:
        document(session, tenant, kind, "legacy-" + kind)
    result = ask(
        session,
        tenant,
        **{"from": "invoice", "as": "o", "group_by": [{"field": "o.type"}]},
    )
    assert {row["o.type"] for row in result.rows} == {"sales_invoice", "credit_note"}


def snapshot_inputs(node, alias):
    """Catalog probes explicitly supply required inputs, just like a template adopter."""
    return [
        {
            "field": f"{alias}.{key}",
            "op": "eq",
            "value": datetime.now(UTC).date().isoformat(),
        }
        for key, prop in node.properties.items()
        if getattr(prop, "input", None) == "date"
    ]


def test_all_table_nodes_can_preview_their_declared_fields(session, business):
    from reality.services.analytics.graph_model import reporting_graph

    for name, node in reporting_graph().nodes.items():
        if not node.table:
            continue
        result = ask(
            session,
            business.tenant.id,
            **{
                "from": name,
                "as": "o",
                "filter": snapshot_inputs(node, "o"),
                "group_by": [
                    {"field": "o." + field} for field in [node.key, *node.properties]
                ],
                "limit": 1,
            },
        )
        assert result is not None, name


def test_purchase_parent_amount_is_not_multiplied_by_lines(session, business):
    from reality.services.analytics.traversal import TraversalRefused

    tenant = business.tenant.id
    doc = document(session, tenant, "purchase_order", "fanout-purchase", "100")
    position(session, tenant, doc, "fanout-a")
    position(session, tenant, doc, "fanout-b")
    with pytest.raises(TraversalRefused):
        ask(
            session,
            tenant,
            **{
                "from": "purchase_order",
                "as": "o",
                "follow": [{"edge": "purchase_order_contains", "as": "line"}],
                "measures": ["purchase_order_amount"],
                "group_by": [{"field": "o.currency"}, {"field": "line.id"}],
            },
        )


def test_all_structural_edges_are_executable_in_both_directions(session, business):
    from reality.services.analytics.graph_model import reporting_graph

    graph = reporting_graph()
    for key, edge in graph.edges.items():
        if edge.fact:
            continue
        for direction, root, target in [
            ("out", edge.from_, edge.to),
            ("in", edge.to, edge.from_),
        ]:
            result = ask(
                session,
                business.tenant.id,
                **{
                    "from": root,
                    "as": "o",
                    "filter": snapshot_inputs(graph.nodes[root], "o")
                    + snapshot_inputs(graph.nodes[target], "related"),
                    "follow": [
                        {
                            "edge": key,
                            "direction": direction,
                            "as": "related",
                            **({"depth": [1, 1]} if edge.recursive else {}),
                        }
                    ],
                    "group_by": [
                        {"field": "o." + graph.nodes[root].key},
                        {"field": "related." + graph.nodes[target].key},
                    ],
                    "limit": 1,
                },
            )
            assert result is not None, (key, direction)


def test_reservation_details_follow_commitment_and_item(session, business):
    from sqlalchemy import select

    from reality.db.core import Commitment, Reservation
    from reality.services.core import create_manual_order

    tenant = business.tenant.id
    create_manual_order(
        session,
        tenant,
        "sales",
        "RESERVATION-TEST",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "sku": business.item.sku,
                "quantity": "3",
                "unit": "pcs",
                "gross_amount": "30",
                "unit_price": "10",
            }
        ],
        "30",
    )
    commitment = session.scalars(
        select(Commitment).where(Commitment.tenant_id == tenant)
    ).first()
    session.add(
        Reservation(
            id="analysis-reservation",
            tenant_id=tenant,
            commitment_id=commitment.id,
            item_id=business.item.id,
            location_id=business.location.id,
            quantity=Decimal(2),
            status="active",
        )
    )
    session.flush()
    result = ask(
        session,
        tenant,
        **{
            "from": "reservation",
            "as": "r",
            "follow": [
                {"edge": "reservation_item", "as": "i"},
                {"edge": "reservation_commitment", "from": "r", "as": "c"},
            ],
            "filter": [{"field": "r.status", "op": "eq", "value": "active"}],
            "group_by": [{"field": "i.unit"}, {"field": "c.id"}],
            "measures": ["reservation_quantity"],
        },
    )
    assert Decimal(result.rows[0]["reservation_quantity"]) == Decimal(2)
    assert result.rows[0]["c.id"] == commitment.id


def test_credit_can_follow_the_invoice_line_it_credits(session, business):
    tenant = business.tenant.id
    invoice = document(session, tenant, "sales_invoice", "credited-invoice")
    invoice_line = position(session, tenant, invoice, "credited-invoice-line")
    credit = document(session, tenant, "credit_note", "invoice-credit")
    position(session, tenant, credit, "invoice-credit-line", invoice_line.id)
    result = ask(
        session,
        tenant,
        **{
            "from": "customer_credit_note_line",
            "as": "c",
            "follow": [
                {"edge": "customer_credit_note_line_credits_invoice", "as": "i"}
            ],
            "group_by": [{"field": "c.id"}, {"field": "i.id"}],
        },
    )
    assert list(result.rows) == [
        {"c.id": "invoice-credit-line", "i.id": invoice_line.id}
    ]


def test_purchase_order_and_position_reach_incoming_commitment(session, business):
    from sqlalchemy import select

    from reality.db.core import Commitment
    from reality.services.core import create_manual_order

    tenant = business.tenant.id
    create_manual_order(
        session,
        tenant,
        "purchase",
        "PURCHASE-COMMITMENT",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "sku": business.item.sku,
                "quantity": "3",
                "unit": "pcs",
                "gross_amount": "30",
                "unit_price": "10",
            }
        ],
        "30",
    )
    commitment = session.scalars(
        select(Commitment).where(Commitment.tenant_id == tenant)
    ).first()
    for root in ["purchase_order", "purchase_order_line"]:
        result = ask(
            session,
            tenant,
            **{
                "from": root,
                "as": "p",
                "follow": [{"edge": root + "_promises", "as": "c"}],
                "group_by": [{"field": "c.id"}, {"field": "c.type"}],
            },
        )
        assert list(result.rows) == [
            {"c.id": commitment.id, "c.type": "supplier_delivery"}
        ]


def test_reverse_same_table_relation_filters_the_original_target(session, business):
    from reality.db.core import Movement

    tenant = business.tenant.id
    returned = Movement(
        id="analysis-return",
        tenant_id=tenant,
        type="return",
        item_id=business.item.id,
        from_location_id=None,
        to_location_id=business.location.id,
        quantity=Decimal(1),
        commitment_id=None,
        source_record_id=None,
    )
    session.add(returned)
    session.flush()
    session.add(
        Movement(
            id="analysis-return-resolution",
            tenant_id=tenant,
            type="transfer",
            item_id=business.item.id,
            from_location_id=business.location.id,
            to_location_id=business.location.id,
            quantity=Decimal(1),
            commitment_id=None,
            source_record_id=None,
            resolves_movement_id=returned.id,
        )
    )
    session.flush()
    result = ask(
        session,
        tenant,
        **{
            "from": "movement",
            "as": "o",
            "follow": [{"edge": "resolves", "direction": "in", "as": "r"}],
            "filter": [{"field": "o.id", "op": "eq", "value": returned.id}],
            "group_by": [{"field": "o.id"}, {"field": "r.id"}],
        },
    )
    assert list(result.rows) == [
        {"o.id": returned.id, "r.id": "analysis-return-resolution"}
    ]


@pytest.mark.parametrize("parent", ["missing_parent", "order_line"])
def test_invalid_or_cyclic_parent_declaration_is_refused(parent):
    import yaml

    from reality.config import config_text
    from reality.services.analytics.graph_model import (
        parse_reporting_graph,
    )

    payload = yaml.safe_load(config_text("reporting_graph.yaml"))
    payload["nodes"]["order_line"]["of"] = parent
    with pytest.raises(ValueError, match="parent"):
        parse_reporting_graph(payload)


def test_component_owners_and_source_versions_preserve_identity_and_tenancy(
    session, business
):
    from reality.db.components import FinancialComponent
    from reality.db.core import SourceRecord
    from reality.services.core import create_tenant

    tenant = business.tenant.id
    neighbor = create_tenant(session, "Evidence neighbor")
    for owner, prefix in [(tenant, "own"), (neighbor.id, "foreign")]:
        source = SourceRecord(
            id=prefix + "-source-1",
            tenant_id=owner,
            source_system="fixture",
            source_type="invoice",
            external_id="same",
            payload='{"private":"original"}',
            payload_hash=prefix + "-hash-1",
            version=1,
        )
        session.add(source)
        session.flush()
        session.add(
            SourceRecord(
                id=prefix + "-source-2",
                tenant_id=owner,
                source_system="fixture",
                source_type="invoice",
                external_id="same",
                payload='{"private":"update"}',
                payload_hash=prefix + "-hash-2",
                version=2,
                supersedes_source_record_id=source.id,
            )
        )
        doc = document(session, owner, "supplier_invoice", prefix + "-evidence")
        doc.source_record_id = source.id
        line = position(session, owner, doc, prefix + "-position")
        for suffix, doc_id, line_id in [
            ("header", doc.id, None),
            ("line", None, line.id),
        ]:
            session.add(
                FinancialComponent(
                    id=prefix + "-component-" + suffix,
                    tenant_id=owner,
                    document_id=doc_id,
                    document_line_id=line_id,
                    stated_net=None,
                    stated_tax=None,
                    stated_gross=Decimal("7.01"),
                    stated_base=None,
                    currency="EUR",
                )
            )
    session.flush()
    components = ask(
        session,
        tenant,
        **{
            "from": "financial_component",
            "as": "c",
            "follow": [
                {"edge": "financial_component_document", "as": "d"},
                {"edge": "financial_component_document_line", "from": "c", "as": "l"},
            ],
            "group_by": [
                {"field": "c.id"},
                {"field": "c.stated_gross"},
                {"field": "d.id"},
                {"field": "l.id"},
            ],
        },
    )
    assert len(components.rows) == 2
    rows = {row["c.id"]: row for row in components.rows}
    assert rows["own-component-header"]["d.id"] == "own-evidence"
    assert rows["own-component-header"]["l.id"] is None
    assert rows["own-component-line"]["l.id"] == "own-position"
    assert rows["own-component-line"]["d.id"] is None
    assert all(
        Decimal(row["c.stated_gross"]) == Decimal("7.01") for row in rows.values()
    )
    versions = ask(
        session,
        tenant,
        **{
            "from": "source_record",
            "as": "s",
            "follow": [
                {"edge": "source_record_supersedes_source_record", "as": "previous"}
            ],
            "filter": [{"field": "s.version", "op": "eq", "value": 2}],
            "group_by": [{"field": "s.id"}, {"field": "previous.id"}],
        },
    )
    assert list(versions.rows) == [
        {"s.id": "own-source-2", "previous.id": "own-source-1"}
    ]
    source_node = reporting_catalog("source_record")["nodes"][0]
    assert "payload" not in {field["key"] for field in source_node["properties"]}
