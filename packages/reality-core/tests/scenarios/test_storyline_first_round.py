"""Spec 182 business story: First round, the short introduction, played end to end.

Seven chapters on one straight path. The story exists to show three things in five
minutes, so the test asserts exactly those: a rule raises a finding nobody wrote
(FR-009), the same rule takes it back when the evidence changes, and a refused
preparation is an outcome that writes nothing (FR-014). SC-002 holds here too, every
event after the seed belongs to exactly one chapter's delta.
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

KEY, VERSION = "first-round", 1

DEFAULT_PATH = [
    "order",
    "explain",
    "receipt",
    "reserve",
    "dispatch",
    "release-hold",
    "ship",
]


def package():
    return next(
        result.package for result in builtin_packages() if result.package.key == KEY
    )


def started(session, owner, request_key="first-1"):
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


def findings(session, tenant_id):
    return {
        row["class_id"] for row in run_read_tool(session, tenant_id, "exceptions", {})
    }


def test_the_short_path_shows_a_rule_raising_clearing_and_refusing(session, owner):
    view = started(session, owner)
    tenant_id = view["tenant_id"]
    seed_sequence = activity_signal(session, tenant_id)["latest_sequence"]
    story = package()

    steps, deltas = play_path(session, owner, tenant_id, DEFAULT_PATH)

    for key in DEFAULT_PATH:
        chapter = story.chapter(key)
        observed_raised = {x["class_id"] for x in deltas[key]["exceptions"]["raised"]}
        observed_cleared = {x["class_id"] for x in deltas[key]["exceptions"]["cleared"]}
        assert set(chapter.expect.raised) <= observed_raised, (key, observed_raised)
        assert set(chapter.expect.cleared) <= observed_cleared, (key, observed_cleared)

    # The point of the story. A rule raised it, the same rule took it back.
    assert steps["order"]["status"] == "done"
    assert "outgoing_commitment_at_risk" in {
        x["class_id"] for x in deltas["order"]["exceptions"]["raised"]
    }
    assert "outgoing_commitment_at_risk" in {
        x["class_id"] for x in deltas["reserve"]["exceptions"]["cleared"]
    }

    # The read chapter explains and writes nothing.
    assert steps["explain"]["status"] == "done"
    assert deltas["explain"]["events"] == []

    # The refusal is an outcome, not a crash, and it leaves no trace in the data.
    assert steps["dispatch"]["status"] == "refused", steps["dispatch"]
    assert deltas["dispatch"]["events"] == []

    # The same command succeeds once a person lifted the hold.
    assert steps["release-hold"]["status"] == "done"
    assert steps["ship"]["status"] == "done"

    # The story ends on exactly one open finding, the hand-off to Order to close.
    assert findings(session, tenant_id) == {"shipped_not_billed"}

    # The story ends, and it hands the reader on to Order to close.
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

    # Every chapter call belongs to a chapter of this run; the exceptions read this
    # test made itself is the one call outside the story (free play, FR-011).
    trace = storyline.trace(session, owner.id, tenant_id, limit=500)
    chapter_items = [item for item in trace["items"] if item["step_id"]]
    assert all(item["chapter"] in DEFAULT_PATH for item in chapter_items)
    assert {item["kind"] for item in chapter_items} >= {"read", "propose", "confirm"}
    free = storyline.trace(session, owner.id, tenant_id, free=True)["items"]
    assert [item["name"] for item in free] == ["exceptions"]
