"""What an analysis costs, pinned in the one unit a test can trust (spec 234).

Wall-clock is not that unit: the same query measured 13 ms on a company with 98
ledger entries and 764 ms on one with 13,590, and a busy machine moves both. What
is stable is how many statements a question runs and how much the canonical
services are asked to derive. Those are what regressed before, and those are what
these tests hold.
"""

from decimal import Decimal

import pytest

from reality.domain.traversal import Traversal
from reality.services import core
from reality.services.analytics.graph_model import reporting_graph
from reality.services.analytics.traversal import run_traversal


def ask(session, tenant, **query):
    return run_traversal(session, tenant, Traversal.model_validate(query))


@pytest.fixture
def two_customers(session, business):
    """Two customers with an open invoice each, so a filter has something to cut."""
    tenant = business.tenant.id
    other = core.create_party(session, tenant, "Schmidt AG", "customer")
    for party, number in ((business.customer, "INV-A"), (other, "INV-B")):
        document = core.create_document(
            session,
            tenant,
            "sales_invoice",
            number,
            party.id,
            "100",
            document_date="2026-08-01",
        )
        core.post_sales_invoice(session, tenant, document.id)
    return other


def test_an_ordinary_path_still_costs_exactly_one_statement(session, business):
    core.create_document(
        session,
        business.tenant.id,
        "sales_order",
        "ONE",
        business.customer.id,
        "10",
        document_date="2026-08-01",
    )
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "as": "o",
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "o.currency"}],
        },
    )
    assert result.statements == 1


def test_a_derivation_stays_under_the_declared_statement_ceiling(
    session, business, two_customers
):
    """The ceiling is the alarm for a derivation that becomes a read per row."""
    ceiling = reporting_graph().limits.statements_per_derivation
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "customer_balance",
            "as": "b",
            "measures": ["customer_balance_open"],
            "group_by": [{"field": "b.currency"}],
        },
    )
    assert 1 < result.statements <= ceiling


def test_a_filter_reaches_the_derivation_instead_of_only_its_result(
    session, business, two_customers, monkeypatch
):
    """The narrowing arrives before the canonical work, not after it.

    Filtering to one customer used to cost exactly what asking for all of them
    cost: the register was derived for the whole company and the filter was
    applied to what came back.
    """
    seen: list[set[str] | None] = []
    original = core.aging_register

    def recording(session_, tenant_, **kwargs):
        seen.append(kwargs.get("party_ids"))
        return original(session_, tenant_, **kwargs)

    monkeypatch.setattr(core, "aging_register", recording)

    query = {
        "from": "customer_balance",
        "as": "b",
        "measures": ["customer_balance_open"],
        "group_by": [{"field": "b.currency"}],
        "filter": [
            {"field": "b.party_id", "op": "eq", "value": business.customer.id},
        ],
    }
    result = ask(session, business.tenant.id, **query)

    assert seen and seen[-1] == {business.customer.id}
    assert Decimal(result.rows[0]["customer_balance_open"]) == Decimal(100)


def test_the_unfiltered_question_still_reaches_every_party(
    session, business, two_customers
):
    """Push-down narrows what was asked for and never what was not."""
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "customer_balance",
            "as": "b",
            "measures": ["customer_balance_open"],
            "group_by": [{"field": "b.currency"}],
        },
    )
    assert Decimal(result.rows[0]["customer_balance_open"]) == Decimal(200)


def test_both_sides_of_one_request_derive_the_register_once(
    session, business, two_customers
):
    """Customer and supplier balances rest on the same open-item source.

    No declared edge leads from one derived position to another, so a single path
    reaches at most one of them; only an existence test walked backwards can reach
    two. The sharing is therefore narrow, and this test holds it where it is real:
    one request asking both sides derives the source once.
    """
    from reality.services.finance.balances import party_balance_rows

    calls: list[dict] = []
    original = core.aging_register

    def recording(session_, tenant_, **kwargs):
        calls.append(kwargs)
        return original(session_, tenant_, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(core, "aging_register", recording)
    try:
        shared: dict = {}
        moment = core.now()
        customer = party_balance_rows(
            session, business.tenant.id, side="customer", as_of=moment, cache=shared
        )
        supplier = party_balance_rows(
            session, business.tenant.id, side="supplier", as_of=moment, cache=shared
        )
    finally:
        monkeypatch.undo()

    assert len(calls) == 1, "the second side derived the same source again"
    assert sum(row["open"] for row in customer) == Decimal(200)
    assert supplier == []


def test_a_narrower_share_is_never_served_to_a_wider_question(
    session, business, two_customers
):
    """The cache key is the exact question asked of the source."""
    from reality.services.finance.balances import party_balance_rows

    shared: dict = {}
    moment = core.now()
    one = party_balance_rows(
        session,
        business.tenant.id,
        side="customer",
        as_of=moment,
        party_ids={business.customer.id},
        cache=shared,
    )
    everyone = party_balance_rows(
        session, business.tenant.id, side="customer", as_of=moment, cache=shared
    )
    assert sum(row["open"] for row in one) == Decimal(100)
    assert sum(row["open"] for row in everyone) == Decimal(200)
