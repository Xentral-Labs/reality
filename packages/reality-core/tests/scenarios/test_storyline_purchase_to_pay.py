"""Spec 182 business story: Purchase to pay, played end to end through the service.

The mirror of Order to close on the purchasing side. The supplier delivers short,
bills the full quantity at a price nobody agreed, sends the invoice twice, and offers
a discount with a deadline. Every chapter runs through the ordinary proposal path in a
practice company; the test proves that the expected findings are raised and cleared by
the rules (FR-009, FR-014), that both branches end at the same review with exactly the
findings the story says remain, and that every event after the seed is in exactly one
chapter's delta (SC-002).
"""

# ruff: noqa: F811 - the owner fixture is imported and then named as a parameter
from sqlalchemy import select

from reality.db.core import BusinessEvent
from reality.services import storyline
from reality.services.core import activity_signal
from reality.storyline.package import builtin_packages
from reality.tools.application import run_read_tool
from tests.scenarios.test_storyline_order_to_close import play_path
from tests.test_storyline_runs import owner  # noqa: F401

KEY, VERSION = "purchase-to-pay", 1

DEFAULT_PATH = [
    "order",
    "notice",
    "receipt",
    "invoice",
    "post",
    "accounts",
    "review",
    "copy",
    "copy-posted",
    "reverse",
    "rest-receipt",
    "pay-full",
    "discount-full",
    "month-end",
]
CREDIT_PATH = [
    "credit-note",
    "credit-post",
    "credit-allocate",
    "pay-net",
    "discount-net",
    "month-end",
]


def package():
    return next(
        result.package for result in builtin_packages() if result.package.key == KEY
    )


def started(session, owner, request_key="p2p-1"):
    view = storyline.start(
        session,
        owner.id,
        key=KEY,
        version=VERSION,
        request_key=request_key,
        confirmed=True,
    )
    assert view["status"] == "active", view
    return view


def remaining_findings(step):
    return {
        x["class_id"]
        for x in step["receipt"]["results"][0]["result"]
        if isinstance(x, dict)
    }


def open_amount(session, tenant_id, document_id):
    context = run_read_tool(
        session, tenant_id, "finance.settlement.context", {"document_id": document_id}
    )
    return context["open"]


def test_the_default_path_raises_and_clears_every_finding_by_rule(session, owner):
    view = started(session, owner)
    tenant_id = view["tenant_id"]
    seed_sequence = activity_signal(session, tenant_id)["latest_sequence"]
    story = package()

    steps, deltas = play_path(session, owner, tenant_id, DEFAULT_PATH)

    for key in DEFAULT_PATH:
        chapter = story.chapter(key)
        assert steps[key]["status"] == "done", (key, steps[key])
        observed_raised = {x["class_id"] for x in deltas[key]["exceptions"]["raised"]}
        observed_cleared = {x["class_id"] for x in deltas[key]["exceptions"]["cleared"]}
        assert set(chapter.expect.raised) <= observed_raised, (key, observed_raised)
        assert set(chapter.expect.cleared) <= observed_cleared, (key, observed_cleared)
        if chapter.kind == "read":
            assert deltas[key]["events"] == [], key

    # The invoice: recorded, booked, paid inside the window, discount on the record.
    invoice = steps["invoice"]["output"]["document_id"]
    assert (
        steps["reverse"]["output"]["original_posting_group_id"]
        == (steps["copy-posted"]["output"]["posting_group_id"])
    )
    assert open_amount(session, tenant_id, invoice) == "0.0000"
    assert steps["discount-full"]["output"]["amount"] == "8.72"

    # The story ends with exactly the finding that should remain.
    assert remaining_findings(steps["month-end"]) == {"invoice_price_differs"}
    assert storyline.state(session, owner.id, tenant_id)["current_chapter"] is None

    # SC-002: every event after the seed is in exactly one chapter's delta.
    recorded = sorted(
        session.scalars(
            select(BusinessEvent.sequence).where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.sequence > seed_sequence,
            )
        )
    )
    listed = sorted(
        event["sequence"] for delta in deltas.values() for event in delta["events"]
    )
    assert listed == recorded

    # Every chapter call belongs to a chapter of this run; the settlement read this
    # test made itself is the one call outside the story (free play, FR-011).
    trace = storyline.trace(session, owner.id, tenant_id, limit=500)
    chapter_items = [item for item in trace["items"] if item["step_id"]]
    assert all(item["chapter"] in DEFAULT_PATH for item in chapter_items)
    assert {item["kind"] for item in chapter_items} >= {"read", "propose", "confirm"}
    free = storyline.trace(session, owner.id, tenant_id, free=True)["items"]
    assert [item["name"] for item in free] == ["finance.settlement.context"]


def test_the_credit_branch_pays_less_and_keeps_the_quantity_finding(session, owner):
    tenant_id = started(session, owner)["tenant_id"]
    story = package()

    play_path(
        session,
        owner,
        tenant_id,
        DEFAULT_PATH[: DEFAULT_PATH.index("reverse") + 1],
        choices={"reverse": "credit"},
    )
    assert (
        storyline.state(session, owner.id, tenant_id)["current_chapter"]
        == "credit-note"
    )
    steps, deltas = play_path(session, owner, tenant_id, CREDIT_PATH)

    for key in CREDIT_PATH:
        chapter = story.chapter(key)
        assert steps[key]["status"] == "done", (key, steps[key])
        observed_raised = {x["class_id"] for x in deltas[key]["exceptions"]["raised"]}
        observed_cleared = {x["class_id"] for x in deltas[key]["exceptions"]["cleared"]}
        assert set(chapter.expect.raised) <= observed_raised, (key, observed_raised)
        assert set(chapter.expect.cleared) <= observed_cleared, (key, observed_cleared)

    assert steps["discount-net"]["output"]["amount"] == "6.54"
    assert steps["discount-net"]["output"]["remaining"] == "0.0000"
    # A credit changes what is owed, not what was billed against the order line.
    assert remaining_findings(steps["month-end"]) == {
        "billed_not_received",
        "invoice_price_differs",
    }
    state = storyline.state(session, owner.id, tenant_id)
    assert state["branches"] == {"reverse": "credit"}
    assert [entry["key"] for entry in state["chapters"]] == (
        DEFAULT_PATH[: DEFAULT_PATH.index("reverse") + 1] + CREDIT_PATH
    )
