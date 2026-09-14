"""The settlement planner: one reproducible order-to-cash story per synthetic order.

Feature 168. The planner is pure: it turns seed, schedule and order identity into
the invoice, the payments, their delays, their stated amounts and the references the
payer writes. Nothing here touches Reality.
"""

from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from reality.demo.international import DEMO_DATA_CUSTOMERS
from reality.integrations import demo_data as synthetic

REFERENCES = {
    "parties": {
        "company": "party_company",
        **{key: f"party_{key}" for key, _ in DEMO_DATA_CUSTOMERS},
    },
    "locations": {"A": "location_a"},
    "items": {key: f"item_{key}" for key in ("P01", "P02", "P11", "P12")},
}
AT = datetime(2026, 9, 10, 8, 0, tzinfo=UTC)
DIFFERENCES = {
    "short_discount",
    "short_withheld",
    "short_partial",
    "over",
    "unmatched",
    "late",
    "never",
}


def _order(index: int, position: int = 1) -> tuple[str, dict]:
    external_id = f"sch_1:run_{index}" + (f":{position}" if position > 1 else "")
    return external_id, synthetic.produce(
        "sch_1", f"run_{index}", "seed", AT, REFERENCES, position
    )


def _plans(count: int) -> list[synthetic.SettlementPlan]:
    return [
        synthetic.settlement_plan("seed", "sch_1", *_order(index))
        for index in range(count)
    ]


def test_weight_tables_live_in_one_place_and_sum_to_one_hundred():
    assert sum(synthetic.OUTCOME_WEIGHTS.values()) == 100
    assert sum(synthetic.MONEY_PATH_WEIGHTS.values()) == 100
    assert synthetic.OUTCOME_WEIGHTS == {
        "exact": 91,
        "short_discount": 2,
        "short_withheld": 1,
        "short_partial": 1,
        "over": 1,
        "unmatched": 1,
        "late": 2,
        "never": 1,
    }
    assert synthetic.MONEY_PATH_WEIGHTS == {"provider": 60, "bank": 40}


def test_plans_are_reproducible_and_change_with_every_input():
    external_id, order = _order(7)
    first = synthetic.settlement_plan("seed", "sch_1", external_id, order)
    assert first == synthetic.settlement_plan("seed", "sch_1", external_id, order)
    others = {
        synthetic.settlement_plan(
            "seed-2", "sch_1", external_id, order
        ).model_dump_json(),
        synthetic.settlement_plan(
            "seed", "sch_2", external_id, order
        ).model_dump_json(),
        synthetic.settlement_plan(
            "seed", "sch_1", external_id + ":2", order
        ).model_dump_json(),
    }
    assert first.model_dump_json() not in others
    assert len(others) == 3


def test_ten_thousand_orders_follow_the_outcome_and_money_path_tables():
    plans = _plans(10_000)
    outcomes = Counter(plan.outcome for plan in plans)
    paths = Counter(plan.money_path for plan in plans)
    for outcome, weight in synthetic.OUTCOME_WEIGHTS.items():
        assert abs(outcomes[outcome] / 100 - weight) < 1, (outcome, outcomes[outcome])
    for path, weight in synthetic.MONEY_PATH_WEIGHTS.items():
        assert abs(paths[path] / 100 - weight) < 1.5, (path, paths[path])


def test_every_difference_lies_on_the_bank_transfer_path():
    for plan in _plans(3_000):
        if plan.outcome in DIFFERENCES:
            assert plan.money_path == "bank", plan.outcome
        if plan.money_path == "provider":
            assert plan.outcome == "exact"


def test_amounts_are_stated_decimals_shaped_by_the_outcome():
    seen = set()
    for plan, (_, order) in zip(_plans(5_000), (_order(i) for i in range(5_000))):
        gross = Decimal(order["gross_amount"])
        amounts = [payment.amount for payment in plan.payments]
        for amount in amounts:
            assert isinstance(amount, Decimal)
            assert amount == amount.quantize(Decimal("0.01"))
            assert amount > 0
        seen.add(plan.outcome)
        if plan.outcome in {"exact", "late", "unmatched"}:
            assert amounts == [gross]
        elif plan.outcome == "short_discount":
            assert len(amounts) == 1 and gross * Decimal("0.96") < amounts[0] < gross
        elif plan.outcome == "short_withheld":
            assert len(amounts) == 1
            assert Decimal("0.50") <= gross - amounts[0] <= Decimal("6.00")
        elif plan.outcome == "short_partial":
            assert len(amounts) == 2 and sum(amounts) == gross
            assert Decimal("0.35") * gross < amounts[0] < Decimal("0.75") * gross
        elif plan.outcome == "over":
            assert sum(amounts) > gross
            assert amounts in ([gross, gross], [amounts[0]]) or len(amounts) == 1
        elif plan.outcome == "never":
            assert amounts == []
    assert seen == set(synthetic.OUTCOME_WEIGHTS)


def test_delays_are_ordered_and_compressed():
    for plan, (_, order) in zip(_plans(3_000), (_order(i) for i in range(3_000))):
        ordered_at = datetime.fromisoformat(order["ordered_at"])
        assert (
            timedelta(minutes=2)
            <= plan.invoice_at - ordered_at
            <= timedelta(minutes=10)
        )
        assert plan.due_at == plan.invoice_at + timedelta(days=14)
        previous = plan.invoice_at
        for index, payment in enumerate(plan.payments, 1):
            assert payment.index == index
            gap = payment.at - previous
            if plan.outcome == "late":
                assert plan.due_at < payment.at <= plan.due_at + timedelta(days=7)
            elif index == 1 and plan.money_path == "provider":
                assert timedelta(minutes=1) <= gap <= timedelta(minutes=3)
            elif index == 1:
                assert timedelta(minutes=10) <= gap <= timedelta(minutes=90)
            else:
                assert timedelta(minutes=20) <= gap <= timedelta(minutes=120)
            previous = payment.at


def test_references_name_the_invoice_or_the_shop_order_and_unmatched_cases_do_not():
    plans = _plans(5_000)
    orders = [_order(i)[1] for i in range(5_000)]
    unmatched_kinds = Counter()
    for plan, order in zip(plans, orders):
        for payment in plan.payments:
            types = [reference.type for reference in payment.references]
            values = {(r.type, r.value) for r in payment.references}
            if plan.outcome == "unmatched":
                assert ("invoice_number", plan.invoice_number) not in values
                assert ("shop_id", order["shop_id"]) not in values
                assert ("shop_order_number", order["number"]) not in values
                assert ("customer_reference", order["customer_reference"]) not in values
                unmatched_kinds[tuple(types)] += 1
            elif plan.money_path == "provider":
                assert ("shop_id", order["shop_id"]) in values
            else:
                assert ("invoice_number", plan.invoice_number) in values
            assert isinstance(payment.remittance_text, str)
    assert set(unmatched_kinds) == {
        ("customer_number",),
        ("customer_reference",),
        ("invoice_number",),
    }


def test_order_payload_carries_three_distinct_identifiers():
    _, first = _order(1)
    _, second = _order(1, position=2)
    for order in (first, second):
        assert order["shop_id"] != order["number"] != order["customer_reference"]
        assert order["shop_id"].startswith("demo-shop-")
        assert order["customer_reference"].startswith("PO-")
        synthetic.DemoOrder.model_validate(order)
    assert first["shop_id"] != second["shop_id"]
    legacy = {
        k: v for k, v in first.items() if k not in {"shop_id", "customer_reference"}
    }
    synthetic.DemoOrder.model_validate(legacy)


def test_invoice_payload_states_the_order_its_terms_and_billed_lines():
    external_id, order = _order(3)
    plan = synthetic.settlement_plan("seed", "sch_1", external_id, order)
    invoice = synthetic.produce_invoice(order, external_id, plan)
    assert invoice["schema_version"] == 1 and invoice["synthetic"] is True
    assert invoice["order_external_id"] == external_id
    assert invoice["number"] == plan.invoice_number
    assert invoice["payment_term_code"] == synthetic.PAYMENT_TERM["code"]
    assert datetime.fromisoformat(invoice["issued_at"]) == plan.invoice_at
    assert datetime.fromisoformat(invoice["due_at"]) == plan.due_at
    assert invoice["customer_party_id"] == order["customer_party_id"]
    assert invoice["currency"] == order["currency"]
    assert invoice["gross_amount"] == order["gross_amount"]
    assert [line["order_source_line_id"] for line in invoice["lines"]] == [
        line["source_line_id"] for line in order["lines"]
    ]
    synthetic.DemoInvoice.model_validate(invoice)


def test_payment_payload_uses_bank_statement_names_and_typed_references():
    external_id, order = _order(5)
    plan = synthetic.settlement_plan("seed", "sch_1", external_id, order)
    invoice = synthetic.produce_invoice(order, external_id, plan)
    for planned in plan.payments:
        payment = synthetic.produce_payment(order, invoice, plan, planned.index)
        assert payment["schema_version"] == 1 and payment["synthetic"] is True
        assert payment["order_external_id"] == external_id
        assert payment["payment_index"] == planned.index
        assert payment["money_path"] == plan.money_path
        assert payment["direction"] == "incoming"
        assert Decimal(payment["amount"]) == planned.amount
        assert payment["currency"] == order["currency"]
        assert datetime.fromisoformat(payment["effective_at"]) == planned.at
        assert payment["customer_party_id"] == order["customer_party_id"]
        assert payment["external_id"] and payment["payment_number"]
        assert payment["references"] == [
            reference.model_dump() for reference in planned.references
        ]
        assert payment["remittance_text"] == planned.remittance_text
        synthetic.DemoPayment.model_validate(payment)


def test_identities_derive_from_the_order_external_id():
    external_id, order = _order(9, position=3)
    plan = synthetic.settlement_plan("seed", "sch_1", external_id, order)
    assert synthetic.invoice_external_id(external_id) == f"{external_id}:invoice"
    assert synthetic.payment_external_id(external_id, 2) == f"{external_id}:payment:2"
    assert plan.model_dump()["order_external_id"] == external_id


def test_payload_models_reject_foreign_or_unversioned_records():
    external_id, order = _order(2)
    plan = synthetic.settlement_plan("seed", "sch_1", external_id, order)
    invoice = synthetic.produce_invoice(order, external_id, plan)
    with pytest.raises(ValidationError):
        synthetic.DemoInvoice.model_validate({**invoice, "schema_version": 2})
    with pytest.raises(ValidationError):
        synthetic.DemoInvoice.model_validate({**invoice, "synthetic": False})
    late = _plans(400)
    payment_plan = next((i, p) for i, p in enumerate(late) if p.payments)
    ext, ord_ = _order(payment_plan[0])
    payment = synthetic.produce_payment(
        ord_, synthetic.produce_invoice(ord_, ext, payment_plan[1]), payment_plan[1], 1
    )
    with pytest.raises(ValidationError):
        synthetic.DemoPayment.model_validate({**payment, "amount": "-1"})
    with pytest.raises(ValidationError):
        synthetic.DemoPayment.model_validate({**payment, "direction": "outgoing"})


def test_normalisers_map_payloads_one_to_one_and_reject_foreign_records():
    external_id, order = _order(11)
    plan = next(
        synthetic.settlement_plan("seed", "sch_1", *_order(i))
        for i in range(11, 400)
        if synthetic.settlement_plan("seed", "sch_1", *_order(i)).payments
    )
    external_id, order = _order(
        int(plan.order_external_id.rsplit("_", 1)[1].split(":")[0])
    )
    invoice = synthetic.produce_invoice(order, external_id, plan)
    normalised = synthetic.normalise_invoice(invoice)
    assert normalised.order_external_id == external_id
    assert normalised.number == plan.invoice_number
    assert normalised.party_id == order["customer_party_id"]
    assert normalised.payment_term_code == synthetic.PAYMENT_TERM["code"]
    assert [line.order_source_line_id for line in normalised.lines] == ["1"]
    payment = synthetic.produce_payment(order, invoice, plan, 1)
    shaped = synthetic.normalise_payment(payment)
    assert shaped.party_id == order["customer_party_id"]
    assert shaped.amount == plan.payments[0].amount
    assert shaped.external_payment_id == payment["external_id"]
    assert [(r.type, r.value) for r in shaped.references] == [
        (r.type, r.value) for r in plan.payments[0].references
    ]
    assert shaped.remittance_text == plan.payments[0].remittance_text
    with pytest.raises(ValidationError):
        synthetic.normalise_invoice({**invoice, "schema_version": 2})
    with pytest.raises(ValidationError):
        synthetic.normalise_payment({**payment, "synthetic": False})
