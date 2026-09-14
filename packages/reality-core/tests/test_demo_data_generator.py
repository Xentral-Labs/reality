"""The synthetic order generator: reproducible, varied in count and customer."""

from collections import Counter
from datetime import UTC, datetime

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


def _orders(references, deliveries):
    return [
        order
        for index in range(deliveries)
        for order in synthetic.plan("sch_1", f"run_{index}", "seed", AT, references)
    ]


def test_hourly_demand_averages_the_selected_rate_over_a_day():
    assert len(synthetic.HOURLY_DEMAND) == 24
    assert abs(sum(synthetic.HOURLY_DEMAND) / 24 - 1) < 1e-5
    assert 0.65 <= min(synthetic.HOURLY_DEMAND) and max(synthetic.HOURLY_DEMAND) <= 1.35
    assert (
        synthetic.HOURLY_DEMAND[19]
        > synthetic.HOURLY_DEMAND[9]
        > synthetic.HOURLY_DEMAND[3]
    )


def test_deliveries_carry_a_poisson_number_of_orders_following_the_hour():
    def sizes(hour):
        at = AT.replace(hour=hour)
        return [
            synthetic.burst_size("seed", "sch_1", f"run_{i}", at) for i in range(3000)
        ]

    night, evening = sizes(3), sizes(19)
    assert set(night) | set(evening) <= set(range(synthetic.MAX_BURST + 1))
    assert {0, 1, 2, 3} <= set(evening)
    assert abs(sum(night) / 3000 - synthetic.HOURLY_DEMAND[3]) < 0.06
    assert abs(sum(evening) / 3000 - synthetic.HOURLY_DEMAND[19]) < 0.06
    assert sum(night) < sum(evening)
    assert night == sizes(3)


def test_plans_are_reproducible_and_orders_in_one_delivery_stay_distinct():
    plans = [
        synthetic.plan("sch_1", f"run_{i}", "seed", AT, REFERENCES) for i in range(200)
    ]
    assert plans == [
        synthetic.plan("sch_1", f"run_{i}", "seed", AT, REFERENCES) for i in range(200)
    ]
    first, second = next(plan for plan in plans if len(plan) == 2)
    assert second["number"] == f"{first['number']}-2"
    assert first["delivery_id"] == second["delivery_id"]
    assert (
        first["customer_party_id"],
        first["lines"][0]["item_id"],
    ) != (second["customer_party_id"], second["lines"][0]["item_id"])


def test_demand_spreads_over_the_pool_with_a_few_large_buyers():
    orders = _orders(REFERENCES, 400)
    spread = Counter(order["customer_party_id"] for order in orders)
    assert len(spread) >= 12
    assert spread.most_common(1)[0][1] / len(orders) < 0.5
    assert spread["party_C1"] > spread["party_C20"]


def test_older_runs_only_use_the_customers_they_captured():
    references = {
        **REFERENCES,
        "parties": {"company": "party_company", "C1": "party_C1", "C4": "party_C4"},
    }
    customers = {order["customer_party_id"] for order in _orders(references, 100)}
    assert customers == {"party_C1", "party_C4"}
