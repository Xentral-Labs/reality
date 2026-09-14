"""Spec 182 business story: Order to close, played end to end through the service.

Every chapter of the built-in package runs through the ordinary proposal path in a
practice company. The story proves FR-009 and FR-014 (chapters build on each other,
refusals are outcomes, read chapters write nothing), SC-002 (every event and Fact the
company recorded after the seed appears in exactly one chapter's delta) and the
branch alternatives (FR-010).
"""

# ruff: noqa: F811 - the owner fixture is imported and then named as a parameter
from sqlalchemy import select

from reality.db.core import BusinessEvent, Fact
from reality.services import storyline
from reality.services.core import activity_signal
from reality.storyline.package import builtin_packages
from tests.test_storyline_runs import KEY, owner, play, started  # noqa: F401

DEFAULT_PATH = [
    "order",
    "reference",
    "receipt",
    "reserve",
    "dispatch",
    "explain-hold",
    "overpayment",
    "release-hold",
    "ship",
    "bill",
    "allocate-credit",
    "supply-check",
    "reorder-40",
    "month-end",
]


def package():
    return next(
        result.package for result in builtin_packages() if result.package.key == KEY
    )


def play_path(session, owner, tenant_id, path, choices=None):
    """Play chapters in order, choosing branches where the path asks for one."""
    steps, deltas = {}, {}
    for key in path:
        step = play(session, owner, tenant_id, key)
        assert step["status"] in {"done", "refused"}, (key, step)
        steps[key] = step
        deltas[key] = storyline.delta(
            session, owner.id, tenant_id, step_id=step["step_id"]
        )
        if choices and key in choices:
            storyline.choose_branch(session, owner.id, tenant_id, key, choices[key])
    return steps, deltas


def test_the_default_path_plays_end_to_end_and_accounts_for_everything(session, owner):
    view = started(session, owner)
    tenant_id = view["tenant_id"]
    seed_sequence = activity_signal(session, tenant_id)["latest_sequence"]
    story = package()

    steps, deltas = play_path(session, owner, tenant_id, DEFAULT_PATH)

    # Chapters build on each other: what the package expects is what was observed.
    for key in DEFAULT_PATH:
        chapter = story.chapter(key)
        observed_raised = {x["class_id"] for x in deltas[key]["exceptions"]["raised"]}
        observed_cleared = {x["class_id"] for x in deltas[key]["exceptions"]["cleared"]}
        assert set(chapter.expect.raised) <= observed_raised, (key, observed_raised)
        assert set(chapter.expect.cleared) <= observed_cleared, (key, observed_cleared)
        if chapter.kind == "read":
            assert deltas[key]["events"] == [], key
            assert steps[key]["receipt"]["kind"] == "read"
            assert [r["tool"] for r in steps[key]["receipt"]["results"]] == [
                read.tool for read in chapter.reads
            ]
    assert steps["dispatch"]["status"] == "refused"
    assert steps["dispatch"]["refused"]["phase"] == "prepare"
    assert [f["predicate"] for f in deltas["reference"]["facts"]] == [
        "order.customer_reference"
    ]
    assert deltas["reference"]["facts"][0]["value"] == "PO-2026-118"
    assert deltas["overpayment"]["records"]
    assert steps["allocate-credit"]["output"]["mode"] == "allocate_credit"

    # The story ends with exactly the findings that remain.
    remaining = {
        x["class_id"]
        for x in steps["month-end"]["receipt"]["results"][0]["result"]
        if isinstance(x, dict)
    }
    assert remaining == {"overdue_incoming_supplier_commitment"}
    assert storyline.state(session, owner.id, tenant_id)["current_chapter"] is None

    # SC-002: every event after the seed is in exactly one chapter's delta, and every
    # Fact recorded after the run started is listed by the chapter that wrote it.
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
    facts = set(session.scalars(select(Fact.id).where(Fact.tenant_id == tenant_id)))
    assert {fact["id"] for delta in deltas.values() for fact in delta["facts"]} == facts

    # Every recorded call belongs to a chapter of this run.
    trace = storyline.trace(session, owner.id, tenant_id, limit=500)
    assert all(item["chapter"] in DEFAULT_PATH for item in trace["items"])
    assert {item["kind"] for item in trace["items"]} >= {
        "read",
        "propose",
        "confirm",
        "error",
    }


def test_the_alternatives_play_and_end_at_the_same_review(session, owner):
    tenant_id = started(session, owner)["tenant_id"]

    play_path(
        session,
        owner,
        tenant_id,
        ["order", "reference", "receipt", "reserve", "dispatch"],
        choices={"dispatch": "call"},
    )
    assert (
        storyline.state(session, owner.id, tenant_id)["current_chapter"]
        == "call-customer"
    )
    more, _ = play_path(
        session,
        owner,
        tenant_id,
        ["call-customer", "overpayment", "release-hold", "ship", "bill"],
        choices={"bill": "refund"},
    )
    assert (
        storyline.state(session, owner.id, tenant_id)["current_chapter"]
        == "refund-credit"
    )
    last, last_deltas = play_path(
        session,
        owner,
        tenant_id,
        ["refund-credit", "supply-check"],
        choices={"supply-check": "wait"},
    )
    assert (
        storyline.state(session, owner.id, tenant_id)["current_chapter"] == "month-end"
    )
    end, _ = play_path(session, owner, tenant_id, ["month-end"])

    assert more["call-customer"]["receipt"]["kind"] == "read"
    assert last["refund-credit"]["output"]["mode"] == "refund_credit"
    assert [
        x["class_id"] for x in last_deltas["refund-credit"]["exceptions"]["cleared"]
    ] == ["unmatched_financial_event"]
    # The refund is an outgoing cash entry allocated to no invoice, so the same rule
    # that cleared the finding on the incoming payment raises one on the refund.
    assert [
        x["class_id"] for x in last_deltas["refund-credit"]["exceptions"]["raised"]
    ] == ["unmatched_financial_event"]
    remaining = {
        x["class_id"]
        for x in end["month-end"]["receipt"]["results"][0]["result"]
        if isinstance(x, dict)
    }
    assert remaining == {
        "overdue_incoming_supplier_commitment",
        "unmatched_financial_event",
    }
    state = storyline.state(session, owner.id, tenant_id)
    assert state["branches"] == {
        "dispatch": "call",
        "bill": "refund",
        "supply-check": "wait",
    }
    assert [entry["key"] for entry in state["chapters"]] == [
        "order",
        "reference",
        "receipt",
        "reserve",
        "dispatch",
        "call-customer",
        "overpayment",
        "release-hold",
        "ship",
        "bill",
        "refund-credit",
        "supply-check",
        "month-end",
    ]


def test_keeping_the_credit_and_reordering_less_are_valid_paths(session, owner):
    tenant_id = started(session, owner)["tenant_id"]
    play_path(
        session,
        owner,
        tenant_id,
        [
            "order",
            "reference",
            "receipt",
            "reserve",
            "dispatch",
            "explain-hold",
            "overpayment",
        ],
    )
    play_path(
        session,
        owner,
        tenant_id,
        ["release-hold", "ship", "bill"],
        choices={"bill": "keep"},
    )
    kept, kept_deltas = play_path(
        session,
        owner,
        tenant_id,
        ["keep-credit", "supply-check"],
        choices={"supply-check": "twenty"},
    )
    end, _ = play_path(session, owner, tenant_id, ["reorder-20", "month-end"])

    assert kept["keep-credit"]["receipt"]["kind"] == "read"
    assert kept_deltas["keep-credit"]["events"] == []
    assert end["reorder-20"]["status"] == "done"
    remaining = {
        x["class_id"]
        for x in end["month-end"]["receipt"]["results"][0]["result"]
        if isinstance(x, dict)
    }
    assert remaining == {
        "overdue_incoming_supplier_commitment",
        "unmatched_financial_event",
    }


def test_an_exported_and_reimported_package_plays_to_the_same_end_state(session, owner):
    """SC-007: a round trip through the library changes nothing about the story."""
    import yaml

    from reality.db.core import BusinessEvent
    from reality.services.exceptions import operational_exceptions

    body, _content_type, _name = storyline.export_package(
        session, owner.id, KEY, 1, fmt="yaml"
    )
    document = yaml.safe_load(body)
    document["key"] = "my-story"
    imported = storyline.import_package(
        session,
        owner.id,
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True).encode(),
        filename="my-story.storyline.yaml",
    )
    assert imported["chapters"] == 18

    def end_state(tenant_id):
        types = sorted(
            session.scalars(
                select(BusinessEvent.event_type).where(
                    BusinessEvent.tenant_id == tenant_id
                )
            )
        )
        findings = sorted(
            (x.class_id, x.title) for x in operational_exceptions(session, tenant_id)
        )
        facts = sorted(
            session.scalars(select(Fact.predicate).where(Fact.tenant_id == tenant_id))
        )
        return types, findings, facts

    original = started(session, owner)["tenant_id"]
    play_path(session, owner, original, DEFAULT_PATH)
    copy = storyline.start(
        session, owner.id, key="my-story", version=1, request_key="copy", confirmed=True
    )
    assert copy["status"] == "active"
    play_path(session, owner, copy["tenant_id"], DEFAULT_PATH)

    assert end_state(copy["tenant_id"]) == end_state(original)
