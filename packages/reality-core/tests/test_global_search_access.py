"""Search authorization applies to aliases, retained versions and owned definitions."""

import pytest

from reality.db.analytics import AnalyticsReport
from reality.db.core import AppUser, PartyRole, SourceRecord, TenantMembership, now
from reality.domain.search import RecordTarget, SearchRequest
from reality.services.core import NotFound, create_document, create_party, create_tenant
from reality.services.global_search import resolve_search_targets, search_company
from reality.services.memberships import Principal


def test_joined_aliases_are_tenant_scoped_and_dual_roles_do_not_duplicate(
    session, business
):
    other = create_tenant(session, "Other")
    secret = create_party(session, other.id, "Never disclose", "customer")
    document = create_document(
        session,
        business.tenant.id,
        "sales_order",
        "LOCAL-ONLY",
        business.customer.id,
        10,
    )
    # Exercise a legacy single-column FK; search must not trust its company scope.
    document.party_id = secret.id
    session.add(
        PartyRole(
            id="dual_search_role",
            tenant_id=business.tenant.id,
            party_id=business.customer.id,
            role="supplier",
        )
    )
    session.flush()
    assert not search_company(
        session,
        business.tenant.id,
        None,
        SearchRequest(provider="orders", query="Never disclose"),
    ).items
    hit = search_company(
        session,
        business.tenant.id,
        None,
        SearchRequest(provider="orders", query="LOCAL-ONLY"),
    ).items[0]
    assert hit.secondary == ""
    partner = search_company(
        session,
        business.tenant.id,
        None,
        SearchRequest(provider="partners", query="Muller"),
    ).items
    assert len(partner) == 1
    assert partner[0].roles == ["customer", "supplier"]


def test_private_reports_exclude_other_owner_deleted_and_legacy(
    session, business, scheduled_owner
):
    other = AppUser(
        id="other_search_owner",
        email="other-search@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(other)
    session.flush()
    session.add(
        TenantMembership(
            id="other_search_member",
            tenant_id=business.tenant.id,
            user_id=other.id,
            role="member",
            status="active",
        )
    )
    session.flush()
    for index, (owner, kind, deleted) in enumerate(
        [
            (scheduled_owner.id, "graph", None),
            (other.id, "graph", None),
            (scheduled_owner.id, None, None),
            (scheduled_owner.id, "graph", now()),
        ]
    ):
        session.add(
            AnalyticsReport(
                id=f"scope_report_{index}",
                tenant_id=business.tenant.id,
                owner_user_id=owner,
                name="Scoped report",
                definition={},
                kind=kind,
                deleted_at=deleted,
                create_request_id=f"req_{index}",
                create_payload_hash="x",
                last_request_id=f"req_{index}",
                last_payload_hash="x",
            )
        )
    session.flush()
    hits = search_company(
        session,
        business.tenant.id,
        Principal(scheduled_owner.id),
        SearchRequest(provider="reports", query="Scoped"),
    ).items
    assert [hit.target.id for hit in hits] == ["scope_report_0"]
    assert not resolve_search_targets(
        session,
        business.tenant.id,
        Principal(scheduled_owner.id),
        [
            RecordTarget(
                kind="saved_report", record_kind="analytics_report", id="scope_report_1"
            )
        ],
    )
    scheduled_owner.status = "disabled"
    session.flush()
    with pytest.raises(NotFound):
        search_company(
            session,
            business.tenant.id,
            Principal(scheduled_owner.id),
            SearchRequest(provider="partners", query="Muller"),
        )


def test_source_versions_remain_distinct_and_cursor_is_bound_to_session(
    session, business
):
    for version in [1, 2]:
        session.add(
            SourceRecord(
                id=f"version_search_{version}",
                tenant_id=business.tenant.id,
                source_system="test",
                source_type="order",
                external_id="VERSION-SAME",
                payload="{}",
                payload_hash=str(version),
                version=version,
            )
        )
    session.flush()
    request = SearchRequest(
        provider="reality", family="source_record", query="VERSION-SAME", limit=1
    )
    first = search_company(
        session, business.tenant.id, None, request, session_scope="one"
    )
    with pytest.raises(ValueError):
        search_company(
            session,
            business.tenant.id,
            None,
            request.model_copy(update={"cursor": first.next_cursor}),
            session_scope="two",
        )
    second = search_company(
        session,
        business.tenant.id,
        None,
        request.model_copy(update={"cursor": first.next_cursor}),
        session_scope="one",
    )
    assert first.items[0].key != second.items[0].key


def test_lesson_search_restricts_evidence_and_private_run_ownership(
    session, scheduled_owner
):
    from reality.services.playground import start_run

    run = start_run(session, scheduled_owner.id, "search_lesson", confirmed=True)
    actor = Principal(scheduled_owner.id)
    sources = search_company(
        session,
        run.tenant_id,
        actor,
        SearchRequest(provider="reality", family="source_record", query="anything"),
    )
    assert not sources.items
    with pytest.raises(NotFound):
        search_company(
            session,
            run.tenant_id,
            Principal("other"),
            SearchRequest(provider="partners", query="anything"),
        )
