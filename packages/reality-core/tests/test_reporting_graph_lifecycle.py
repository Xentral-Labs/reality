"""A saved graph report holds the question, and reopening it asks again.

The number is never stored, because a number stored is a number that stops being
true. What has to survive instead is the question and the meaning that produced
it — so a report records the model version, and a report saved under one meaning
cannot be silently reopened under another.
"""

from __future__ import annotations

import json
from decimal import Decimal
from uuid import uuid4

import pytest
from conftest import record_by_id
from cryptography.fernet import Fernet
from intake_review_support import reviewed_manual_order

from reality.domain.traversal import Traversal
from reality.services.analytics.errors import AnalyticsError
from reality.services.analytics.graph_model import reporting_graph
from reality.services.analytics.reports import (
    change_graph_report,
    get_report,
    list_reports,
)
from reality.services.analytics.traversal import run_traversal
from reality.services.core import NotFound
from reality.services.memberships import Principal

QUESTION = {
    "from": "order",
    "as": "o",
    "measures": ["stated_order_amount"],
    "group_by": [{"field": "o.currency"}],
}


def save(session, tenant_id, principal, **changes):
    arguments = {
        "operation": "create",
        "request_id": str(uuid4()),
        "name": "Umsatz nach Währung",
        "question": QUESTION,
        **changes,
    }
    return change_graph_report(session, tenant_id, principal, arguments)


@pytest.fixture
def author(scheduled_owner):
    return Principal(scheduled_owner.id)


@pytest.fixture
def sales(session, business):
    reviewed_manual_order(
        session,
        business.tenant.id,
        "sales",
        "AN-001",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "sku": business.item.sku,
                "quantity": "1",
                "unit_price": "1",
                "gross_amount": "250",
                "unit": "pcs",
            }
            for _ in range(4)
        ],
        "1000",
        currency="EUR",
        ordered_at="2026-03-10T10:00:00Z",
        document_date="2026-03-10",
    )
    session.flush()


# --- saving the question ---------------------------------------------------------


def test_a_saved_report_holds_the_question_and_its_meaning(session, business, author):
    saved = save(session, business.tenant.id, author)
    assert saved["kind"] == "graph"
    assert saved["model_version"] == reporting_graph().model_version
    assert saved["definition"]["from"] == "order"
    assert saved["definition"]["measures"] == ["stated_order_amount"]


def test_the_stored_question_carries_no_sql_and_no_dialect(session, business, author):
    """What makes a different execution backend a compiler change, not a migration."""
    stored = repr(save(session, business.tenant.id, author)["definition"]).lower()
    for trace in ("select", "join", "document", "postgres", "sql"):
        assert trace not in stored, trace


def test_reopening_asks_the_question_again(session, business, author, sales):
    saved = save(session, business.tenant.id, author)
    reopened = get_report(
        session, business.tenant.id, author, saved["id"], report_kind="graph"
    )
    result = run_traversal(
        session, business.tenant.id, Traversal.model_validate(reopened["definition"])
    )
    assert Decimal(result.rows[0]["stated_order_amount"]) == Decimal(1000)


def test_a_reopened_question_is_the_one_that_was_saved(session, business, author):
    saved = save(session, business.tenant.id, author)
    reopened = get_report(
        session, business.tenant.id, author, saved["id"], report_kind="graph"
    )
    assert Traversal.model_validate(reopened["definition"]) == Traversal.model_validate(
        QUESTION
    )


# --- a lost response must not create two reports ----------------------------------


def test_a_retry_returns_the_same_report(session, business, author):
    arguments = {
        "operation": "create",
        "request_id": str(uuid4()),
        "name": "Umsatz nach Währung",
        "question": QUESTION,
    }
    first = change_graph_report(session, business.tenant.id, author, arguments)
    again = change_graph_report(session, business.tenant.id, author, arguments)
    assert again["id"] == first["id"]
    assert again["replayed"] is True
    listed = list_reports(session, business.tenant.id, author, report_kind="graph")
    assert len(listed["records"]) == 1, "a lost response creates one report, not two"


def test_reusing_a_retry_key_for_a_different_question_is_refused(
    session, business, author
):
    request_id = str(uuid4())
    save(session, business.tenant.id, author, request_id=request_id)
    with pytest.raises(AnalyticsError) as refusal:
        save(
            session,
            business.tenant.id,
            author,
            request_id=request_id,
            name="Etwas anderes",
        )
    assert refusal.value.code == "idempotency_conflict"


def test_saving_over_a_stale_revision_is_refused(session, business, author):
    saved = save(session, business.tenant.id, author)
    change_graph_report(
        session,
        business.tenant.id,
        author,
        {
            "operation": "rename",
            "request_id": str(uuid4()),
            "report_id": saved["id"],
            "expected_revision": saved["revision"],
            "name": "Neu benannt",
        },
    )
    with pytest.raises(AnalyticsError) as refusal:
        change_graph_report(
            session,
            business.tenant.id,
            author,
            {
                "operation": "rename",
                "request_id": str(uuid4()),
                "report_id": saved["id"],
                "expected_revision": saved["revision"],
                "name": "Zu spät",
            },
        )
    assert refusal.value.code == "revision_conflict"


# --- what the retired generation left behind ---------------------------------------


def _retired_report(session, tenant_id, owner):
    """A row exactly as the configured generation saved it: no kind, no version.

    They are still in the table. Nothing reads them any more, and the point of
    these tests is that nothing silently writes over them either.
    """
    from reality.db.analytics import AnalyticsReport
    from reality.db.core import uid

    row = AnalyticsReport(
        id=uid("rep"),
        tenant_id=tenant_id,
        owner_user_id=owner.user_id,
        name="Alte Art",
        definition={
            "dataset": "sales_orders",
            "dimensions": ["customer_id"],
            "measures": ["order_count"],
        },
        revision=1,
        create_request_id=str(uuid4()),
        create_payload_hash="retired",
        last_request_id=str(uuid4()),
        last_payload_hash="retired",
    )
    session.add(row)
    session.flush()
    return row


def test_a_retired_report_is_not_listed_among_graph_ones(session, business, author):
    save(session, business.tenant.id, author)
    _retired_report(session, business.tenant.id, author)
    listed = list_reports(session, business.tenant.id, author, report_kind="graph")
    assert [r["name"] for r in listed["records"]] == ["Umsatz nach Währung"]


def test_a_retired_report_cannot_be_opened_as_a_graph_one(session, business, author):
    """Reading it with the wrong meaning is worse than not finding it."""
    row = _retired_report(session, business.tenant.id, author)
    with pytest.raises(NotFound):
        get_report(session, business.tenant.id, author, row.id, report_kind="graph")


def test_a_retired_report_is_not_overwritten_by_a_graph_change(
    session, business, author
):
    """The kind column is NULL on those rows, which is not the same as "any kind"."""
    row = _retired_report(session, business.tenant.id, author)
    with pytest.raises(AnalyticsError) as refusal:
        change_graph_report(
            session,
            business.tenant.id,
            author,
            {
                "operation": "rename",
                "request_id": str(uuid4()),
                "report_id": row.id,
                "expected_revision": row.revision,
                "name": "Falsche Art",
            },
        )
    assert refusal.value.code == "kind_mismatch"


# --- the whole way a chat saves one --------------------------------------------------


def test_the_chat_route_prepares_confirms_and_saves_a_report(session, business, author):
    """The path a copilot actually takes, which nothing exercised end to end.

    Retiring the configured generation left `proposals.py` importing a function
    that no longer existed. Every unit test still passed, because the import sits
    inside the function that prepares a proposal and nothing called it — so the
    first thing that did was a person in the chat.
    """
    from reality.services.analytics.reports import CALLER, caller
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    with caller(author):
        assert CALLER.get() is author
        proposal = create_change_proposal(
            session,
            business.tenant.id,
            "graph.reports.change",
            {
                "operation": "create",
                "request_id": str(uuid4()),
                "name": "Umsatz je Währung",
                "question": QUESTION,
            },
        )
    # The question is sealed: a proposal row is visible to the company, a private
    # report is not.
    assert "Umsatz je Währung" not in proposal.input

    with pytest.raises(AnalyticsError):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=author,
        )
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=author,
        confirmed=True,
    )
    saved = list_reports(session, business.tenant.id, author, report_kind="graph")
    assert [row["name"] for row in saved["records"]] == ["Umsatz je Währung"]
    assert saved["records"][0]["model_version"] == reporting_graph().model_version


def test_a_refused_save_releases_the_proposal_instead_of_stranding_it(
    session, business, author
):
    """Found by using it: a reused retry key locked a proposal out permanently.

    Confirmation claims the proposal before it runs, and commits that claim, so a
    crash mid-write leaves an outcome nobody can assume. A refusal is not that: it
    wrote nothing. Leaving the claim would answer every later confirmation with
    "execution is in progress", and the reader would never learn that the copilot
    had reused a retry key.
    """
    from reality.services.analytics.reports import caller
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    shared_key = str(uuid4())
    save(session, business.tenant.id, author, request_id=shared_key)
    with caller(author):
        proposal = create_change_proposal(
            session,
            business.tenant.id,
            "graph.reports.change",
            {
                "operation": "create",
                "request_id": shared_key,
                "name": "Eine andere Frage",
                "question": {**QUESTION, "limit": 5},
            },
        )

    with pytest.raises(AnalyticsError) as refusal:
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=author,
            confirmed=True,
        )
    assert refusal.value.code == "idempotency_conflict"

    session.expire_all()
    assert record_by_id(session, type(proposal), proposal.id).status == "proposed", (
        "a refusal has to leave the proposal confirmable again"
    )
    # And the refusal is the same one the second time, rather than a dead end.
    with pytest.raises(AnalyticsError) as again:
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=author,
            confirmed=True,
        )
    assert again.value.code == "idempotency_conflict"


def test_a_proposal_that_cannot_be_unsealed_says_so_and_can_be_rejected(
    session, business, author
):
    """Found by moving the running stack between two checkouts.

    Each one generates its own key file, so a proposal sealed under one becomes
    unreadable under the other. The route answered "Report proposal not found"
    for that, for a proposal belonging to somebody else, and for one that really
    was missing — three different situations, one sentence, and only one of them
    meant what it said. A reader looked for a proposal that was in front of them
    and pressed Try again forever.
    """
    from reality.services.analytics.proposals import preview
    from reality.services.analytics.reports import caller
    from reality.tools.application import create_change_proposal, reject_proposal

    with caller(author):
        proposal = create_change_proposal(
            session,
            business.tenant.id,
            "graph.reports.change",
            {
                "operation": "create",
                "request_id": str(uuid4()),
                "name": "Unlesbar",
                "question": QUESTION,
            },
        )
    sealed = json.loads(proposal.input)
    sealed["private_report_change"] = (
        Fernet(Fernet.generate_key()).encrypt(b"{}").decode()
    )
    proposal.input = json.dumps(sealed)
    session.flush()

    with pytest.raises(AnalyticsError) as refusal:
        preview(session, business.tenant.id, author, proposal.id)
    assert refusal.value.code == "sealed_unreadable"
    assert "rejected" in str(refusal.value), "say what can still be done about it"

    # Rejecting needs no key, which is what makes the card dismissible.
    reject_proposal(
        session, business.tenant.id, proposal.id, confirming_principal=author
    )
    assert record_by_id(session, type(proposal), proposal.id).status == "rejected"


# --- what a confirmed proposal points at -----------------------------------------
#
# A create proposal carries no report ID, because the report does not exist when
# the proposal is prepared. Once it is confirmed one does, and the surface that
# offered "open this" had no way to name it: it reopened the proposal's question
# as a fresh unsaved draft, so confirming and then opening produced a second
# report. The link was always there — the row records the retry key the change
# was made under — it was simply never returned.


def _propose(session, business, author, **changes):
    from reality.services.analytics.reports import caller
    from reality.tools.application import create_change_proposal

    with caller(author):
        return create_change_proposal(
            session,
            business.tenant.id,
            "graph.reports.change",
            {
                "operation": "create",
                "request_id": str(uuid4()),
                "name": "Umsatz je Währung",
                "question": QUESTION,
                **changes,
            },
        )


def test_an_unconfirmed_create_names_no_report_because_none_was_written(
    session, business, author
):
    from reality.services.analytics.proposals import preview

    proposal = _propose(session, business, author)
    shown = preview(session, business.tenant.id, author, proposal.id)
    assert shown["status"] == "proposed"
    assert shown["report_id"] is None, (
        "nothing is saved yet, so there is nothing to open"
    )


def test_a_confirmed_create_names_the_report_it_wrote(session, business, author):
    from reality.services.analytics.proposals import preview
    from reality.tools.application import approve_and_execute_proposal

    proposal = _propose(session, business, author)
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=author,
        confirmed=True,
    )
    shown = preview(session, business.tenant.id, author, proposal.id)
    saved = list_reports(session, business.tenant.id, author, report_kind="graph")
    assert shown["report_id"] == saved["records"][0]["id"]
    assert len(saved["records"]) == 1, "confirming writes exactly one report"


def test_a_confirmed_create_whose_report_was_deleted_names_nothing(
    session, business, author
):
    from reality.services.analytics.proposals import preview
    from reality.tools.application import approve_and_execute_proposal

    proposal = _propose(session, business, author)
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=author,
        confirmed=True,
    )
    written = list_reports(session, business.tenant.id, author, report_kind="graph")[
        "records"
    ][0]
    change_graph_report(
        session,
        business.tenant.id,
        author,
        {
            "operation": "delete",
            "request_id": str(uuid4()),
            "report_id": written["id"],
            "expected_revision": written["revision"],
        },
    )
    shown = preview(session, business.tenant.id, author, proposal.id)
    assert shown["report_id"] is None, "offering to open a deleted report is a dead end"


def test_a_change_to_an_existing_report_names_that_report(session, business, author):
    from reality.services.analytics.proposals import preview

    written = save(session, business.tenant.id, author)
    proposal = _propose(
        session,
        business,
        author,
        operation="update",
        name=None,
        report_id=written["id"],
        expected_revision=written["revision"],
    )
    shown = preview(session, business.tenant.id, author, proposal.id)
    assert shown["report_id"] == written["id"]


def test_a_confirmed_duplicate_names_the_copy_not_its_source(session, business, author):
    """A duplicate names its source, but confirming produced the copy."""
    from reality.services.analytics.proposals import preview
    from reality.tools.application import approve_and_execute_proposal

    source = save(session, business.tenant.id, author)
    proposal = _propose(
        session,
        business,
        author,
        operation="duplicate",
        name="Zweite Fassung",
        question=None,
        report_id=source["id"],
        expected_revision=source["revision"],
    )
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=author,
        confirmed=True,
    )
    shown = preview(session, business.tenant.id, author, proposal.id)
    copy = next(
        row
        for row in list_reports(
            session, business.tenant.id, author, report_kind="graph"
        )["records"]
        if row["id"] != source["id"]
    )
    assert shown["report_id"] == copy["id"]


@pytest.mark.parametrize("denial", ["missing", "removed", "inactive_user"])
def test_private_library_explains_membership_without_disclosing_reports(
    session, business, author, scheduled_owner, denial
):
    from sqlalchemy import select

    from reality.db.core import TenantMembership

    saved = save(session, business.tenant.id, author)
    if denial == "missing":
        session.delete(
            session.scalar(
                select(TenantMembership).where(
                    TenantMembership.tenant_id == business.tenant.id,
                    TenantMembership.user_id == author.user_id,
                )
            )
        )
    elif denial == "removed":
        session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == business.tenant.id,
                TenantMembership.user_id == author.user_id,
            )
        ).status = "removed"
    else:
        scheduled_owner.status = "inactive"
    session.flush()
    with pytest.raises(AnalyticsError) as failure:
        list_reports(session, business.tenant.id, author, report_kind="graph")
    assert failure.value.code == "company_membership_required"
    for report_id in [saved["id"], "missing-report"]:
        with pytest.raises(NotFound, match="Report not found"):
            get_report(session, business.tenant.id, author, report_id)
    with pytest.raises(NotFound, match="Report not found"):
        change_graph_report(
            session,
            business.tenant.id,
            author,
            {
                "operation": "delete",
                "request_id": str(uuid4()),
                "report_id": saved["id"],
                "expected_revision": saved["revision"],
            },
        )


def _nonmember_admin(session, scheduled_owner):
    from sqlalchemy import delete

    from reality.db.core import TenantMembership

    scheduled_owner.is_platform_admin = True
    session.execute(
        delete(TenantMembership).where(TenantMembership.user_id == scheduled_owner.id)
    )
    session.flush()
    return Principal(scheduled_owner.id, is_platform_admin=False)


def test_platform_admin_owns_reports_without_creating_membership(
    session, business, scheduled_owner
):
    from sqlalchemy import func, select

    from reality.db.core import TenantMembership

    admin = _nonmember_admin(session, scheduled_owner)
    saved = save(session, business.tenant.id, admin)
    assert (
        get_report(session, business.tenant.id, admin, saved["id"])["id"] == saved["id"]
    )
    for operation in ["rename", "duplicate", "delete"]:
        changed = change_graph_report(
            session,
            business.tenant.id,
            admin,
            {
                "operation": operation,
                "request_id": str(uuid4()),
                "report_id": saved["id"],
                "expected_revision": saved["revision"],
                **({"name": "Admin private report"} if operation != "delete" else {}),
            },
        )
        if operation == "rename":
            saved = changed
    records = list_reports(session, business.tenant.id, admin, report_kind="graph")[
        "records"
    ]
    assert len(records) == 1 and records[0]["name"] == "Admin private report"
    assert (
        session.scalar(
            select(func.count())
            .select_from(TenantMembership)
            .where(TenantMembership.user_id == admin.user_id)
        )
        == 0
    )


@pytest.mark.parametrize("revocation", ["administrator", "account"])
def test_private_admin_access_uses_current_persisted_authority(
    session, business, scheduled_owner, revocation
):
    from sqlalchemy import update

    from reality.db.core import AppUser

    admin = _nonmember_admin(session, scheduled_owner)
    saved = save(session, business.tenant.id, admin)
    values = (
        {"is_platform_admin": False}
        if revocation == "administrator"
        else {"status": "inactive"}
    )
    session.execute(
        update(AppUser)
        .where(AppUser.id == admin.user_id)
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    with pytest.raises(AnalyticsError):
        list_reports(
            session,
            business.tenant.id,
            Principal(admin.user_id, True),
            report_kind="graph",
        )
    with pytest.raises(NotFound):
        get_report(session, business.tenant.id, admin, saved["id"])


def test_admin_cannot_read_change_or_preview_another_authors_report(
    session, business, author, scheduled_owner
):
    from reality.db.core import AppUser, uid
    from reality.services.analytics.proposals import preview

    foreign = save(session, business.tenant.id, author)
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        is_platform_admin=True,
    )
    session.add(user)
    session.flush()
    admin = Principal(user.id)
    held = _propose(
        session,
        business,
        author,
        operation="rename",
        report_id=foreign["id"],
        expected_revision=foreign["revision"],
        name="Private rename",
        question=None,
    )
    assert (
        list_reports(session, business.tenant.id, admin, report_kind="graph")["records"]
        == []
    )
    with pytest.raises(NotFound):
        get_report(session, business.tenant.id, admin, foreign["id"])
    for operation in ["rename", "duplicate", "delete"]:
        with pytest.raises(NotFound):
            change_graph_report(
                session,
                business.tenant.id,
                admin,
                {
                    "operation": operation,
                    "request_id": str(uuid4()),
                    "report_id": foreign["id"],
                    "expected_revision": foreign["revision"],
                    **({"name": "Forbidden"} if operation != "delete" else {}),
                },
            )
    with pytest.raises((AnalyticsError, NotFound)):
        preview(session, business.tenant.id, admin, held.id)


@pytest.mark.parametrize("tenant_state", ["missing", "archived", "playground"])
def test_admin_fallback_requires_visible_business_company(
    session, business, scheduled_owner, tenant_state
):
    from reality.db.core import now

    admin = _nonmember_admin(session, scheduled_owner)
    tenant_id = business.tenant.id
    if tenant_state == "missing":
        tenant_id = "missing-company"
    elif tenant_state == "archived":
        business.tenant.archived_at = now()
    else:
        from reality.db.core import Tenant, uid

        practice = Tenant(
            id=uid("ten"), name="Other user's practice", purpose="playground"
        )
        session.add(practice)
        tenant_id = practice.id
    session.flush()
    with pytest.raises(AnalyticsError):
        list_reports(session, tenant_id, admin, report_kind="graph")


def test_admin_own_report_stays_scoped_to_selected_company(
    session, business, scheduled_owner
):
    from reality.services.core import create_tenant

    admin = _nonmember_admin(session, scheduled_owner)
    saved = save(session, business.tenant.id, admin)
    other = create_tenant(session, "Another accessible company", _commit=False)
    assert list_reports(session, other.id, admin, report_kind="graph")["records"] == []
    with pytest.raises(NotFound):
        get_report(session, other.id, admin, saved["id"])
    with pytest.raises(NotFound):
        change_graph_report(
            session,
            other.id,
            admin,
            {
                "operation": "delete",
                "request_id": str(uuid4()),
                "report_id": saved["id"],
                "expected_revision": saved["revision"],
            },
        )


def test_nonmember_admin_confirms_only_their_own_private_proposal(
    session, business, scheduled_owner
):
    from reality.services.analytics.proposals import preview
    from reality.tools.application import approve_and_execute_proposal

    admin = _nonmember_admin(session, scheduled_owner)
    held = _propose(session, business, admin)
    assert preview(session, business.tenant.id, admin, held.id)["operation"] == "create"
    executed = approve_and_execute_proposal(
        session, business.tenant.id, held.id, confirming_principal=admin, confirmed=True
    )
    assert executed.status == "executed"
    assert (
        len(
            list_reports(session, business.tenant.id, admin, report_kind="graph")[
                "records"
            ]
        )
        == 1
    )
