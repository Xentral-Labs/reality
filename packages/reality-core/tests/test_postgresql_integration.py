import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from time import monotonic

import pytest
from alembic import command
from alembic.config import Config
from conftest import record_by_id
from sqlalchemy import delete, func, insert, inspect, select
from sqlalchemy.exc import TimeoutError
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    ROOT,
    AppUser,
    BusinessEvent,
    CompanyInvitation,
    FinanceRoleDestination,
    FinanceState,
    ImportJob,
    InterpretationRule,
    InvitationDelivery,
    RealityGap,
    RealityGapEntry,
    Reservation,
    RuleInterpretationOutcome,
    SecurityAuditEvent,
    Session,
    SourceRecord,
    SubledgerAccount,
    Tenant,
    TenantMembership,
    build_engine,
    now,
    resolve_database_pool_settings,
    uid,
)
from reality.services.core import (
    InvalidOperation,
    create_commitment,
    create_item,
    create_location,
    create_party,
    create_tenant,
    enqueue_shopify_order,
    record_movement,
)
from reality.services.memberships import (
    Principal,
    accept_invitation,
    create_invitation,
    remove_member,
    resend_invitation,
    revoke_invitation,
)
from reality.services.notifications import claim_due_delivery, issue_delivery_token
from reality.services.reality_gaps import (
    capture_gap,
    decide_gap,
    list_gaps,
    prepare_implementation,
    replay_rule,
)
from reality.tools.application import confirm_tool, propose_tool

FIXTURE = Path(__file__).parents[1] / "fixtures" / "shopify" / "order_10473.json"


def test_reality_gap_register_is_bounded_at_erp_scale() -> None:
    timestamp = now()
    with Session() as session:
        tenant = create_tenant(session, f"Gap benchmark {uid('run')}")
        # This measures register bounds, not random identifier collision probability.
        try:
            gap_rows = [
                {
                    "id": f"gap_benchmark_{index:05d}",
                    "tenant_id": tenant.id,
                    "question": f"Question {index}",
                    "intended_use": "Bounded register benchmark",
                    "origin": "web",
                    "status": "open",
                    "revision": 1,
                    "request_fingerprint": f"benchmark-{index}",
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
                for index in range(10_000)
            ]
            session.execute(insert(RealityGap), gap_rows)
            for start in range(0, 100_000, 10_000):
                session.execute(
                    insert(RealityGapEntry),
                    [
                        {
                            "id": f"rge_benchmark_{index:06d}",
                            "tenant_id": tenant.id,
                            "gap_id": gap_rows[index % 10_000]["id"],
                            "entry_type": "note",
                            "payload": "{}",
                            "actor_type": "system",
                            "created_at": timestamp,
                        }
                        for index in range(start, start + 10_000)
                    ],
                )
            session.commit()

            started = monotonic()
            result = list_gaps(session, tenant.id, lifecycle="open", page=1, size=25)
            elapsed = monotonic() - started

            assert result["total"] == 10_000
            assert len(result["items"]) == 25
            assert elapsed < 2
        finally:
            session.rollback()
            session.execute(
                delete(RealityGapEntry).where(RealityGapEntry.tenant_id == tenant.id)
            )
            session.execute(delete(RealityGap).where(RealityGap.tenant_id == tenant.id))
            for model in (FinanceRoleDestination, FinanceState, SubledgerAccount):
                session.execute(delete(model).where(model.tenant_id == tenant.id))
            session.execute(delete(Tenant).where(Tenant.id == tenant.id))
            session.commit()


def test_reality_gap_replay_resumes_ten_thousand_sources_without_duplicates() -> None:
    timestamp = now()
    with Session() as session:
        tenant = create_tenant(session, f"Replay benchmark {uid('run')}")
        try:
            gap = capture_gap(
                session,
                tenant.id,
                question="Which benchmark records apply?",
                intended_use="Verify resumable ERP-scale replay",
                origin="web",
                idempotency_key=uid("benchmark"),
            )
            decide_gap(
                session,
                tenant.id,
                gap.id,
                destination="fact",
                rationale="Reviewed benchmark rule",
                expected_revision=gap.revision,
                actor_user_id=None,
            )
            rule = prepare_implementation(
                session,
                tenant.id,
                gap.id,
                {
                    "logical_name": "ERP replay benchmark",
                    "source_system": "benchmark",
                    "source_type": "order",
                    "conditions": [
                        {
                            "path": "eligible",
                            "operator": "equals",
                            "value_type": "boolean",
                            "operand": True,
                        }
                    ],
                    "output_mode": "constant",
                    "constant_value": True,
                    "predicate": "order.benchmark_eligible",
                    "subject_type": "commitment",
                    "subject_resolver": "source_document_commitments",
                    "value_type": "boolean",
                    "observed_at_mode": "source_received_at",
                },
                expected_revision=gap.revision,
            )
            for start in range(0, 10_000, 1_000):
                session.execute(
                    insert(SourceRecord),
                    [
                        {
                            "id": f"src_benchmark_{index:05d}",
                            "tenant_id": tenant.id,
                            "source_system": "benchmark",
                            "source_type": "order",
                            "external_id": f"benchmark-{index}",
                            "payload": '{"eligible":false}',
                            "payload_hash": f"{index:064x}",
                            "version": 1,
                            "received_at": timestamp,
                        }
                        for index in range(start, start + 1_000)
                    ],
                )
            session.commit()

            started = monotonic()
            cursor = None
            pages = 0
            while True:
                result = replay_rule(
                    session, tenant.id, rule.id, limit=500, cursor=cursor
                )
                pages += 1
                cursor = result["next_cursor"]
                if result["complete"]:
                    break
            elapsed = monotonic() - started

            assert pages == 20
            assert result["cumulative"]["not_applicable"] == 10_000
            assert elapsed < 60
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(RuleInterpretationOutcome)
                    .where(
                        RuleInterpretationOutcome.tenant_id == tenant.id,
                        RuleInterpretationOutcome.rule_id == rule.id,
                    )
                )
                == 10_000
            )

            retry = replay_rule(session, tenant.id, rule.id, limit=500)
            assert retry["cumulative"]["not_applicable"] == 10_000
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(RuleInterpretationOutcome)
                    .where(
                        RuleInterpretationOutcome.tenant_id == tenant.id,
                        RuleInterpretationOutcome.rule_id == rule.id,
                    )
                )
                == 10_000
            )
        finally:
            # A failed timing assertion must not leak committed benchmark data.
            session.rollback()
            session.execute(
                delete(RuleInterpretationOutcome).where(
                    RuleInterpretationOutcome.tenant_id == tenant.id
                )
            )
            session.execute(
                delete(SourceRecord).where(SourceRecord.tenant_id == tenant.id)
            )
            session.execute(
                delete(InterpretationRule).where(
                    InterpretationRule.tenant_id == tenant.id
                )
            )
            session.execute(
                delete(RealityGapEntry).where(RealityGapEntry.tenant_id == tenant.id)
            )
            session.execute(delete(RealityGap).where(RealityGap.tenant_id == tenant.id))
            for model in (FinanceRoleDestination, FinanceState, SubledgerAccount):
                session.execute(delete(model).where(model.tenant_id == tenant.id))
            session.execute(delete(Tenant).where(Tenant.id == tenant.id))
            session.commit()


def test_all_migrations_on_disposable_postgresql(
    postgres_database: str,
    monkeypatch,
) -> None:
    database_url = postgres_database
    monkeypatch.setenv("REALITY_DATABASE_URL", database_url)
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    database_engine = build_engine(database_url)
    migrated = False
    try:
        command.upgrade(config, "head")
        migrated = True
        with database_engine.connect() as connection:
            inspector = inspect(connection)
            assert "source_record" in inspector.get_table_names()
            occurred_at = next(
                column
                for column in inspector.get_columns("movement")
                if column["name"] == "occurred_at"
            )
            assert occurred_at["type"].timezone is True

        factory = sessionmaker(database_engine, expire_on_commit=False)
        with factory() as session:
            tenant = create_tenant(session, "Concurrent Imports GmbH")
            company = create_party(session, tenant.id, "Company", "company")
            customer = create_party(session, tenant.id, "Customer", "customer")
            item = create_item(session, tenant.id, "BIKE-LIGHT", "Bike Light")
            location = create_location(session, tenant.id, "Warehouse")
            ids = (tenant.id, company.id, customer.id, item.id, location.id)
        payload = json.loads(FIXTURE.read_text())

        def enqueue() -> tuple[str, str]:
            tenant_id, company_id, customer_id, _item_id, location_id = ids
            with factory() as session:
                source, job = enqueue_shopify_order(
                    session,
                    tenant_id,
                    payload,
                    company_id,
                    customer_id,
                    location_id,
                )
                return source.id, job.id

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: enqueue(), range(2)))
        assert results[0] == results[1]
        with factory() as session:
            assert session.scalar(select(func.count()).select_from(SourceRecord)) == 1
            assert session.scalar(select(func.count()).select_from(ImportJob)) == 1

            tenant_id, company_id, customer_id, item_id, location_id = ids
            record_movement(
                session,
                tenant_id,
                "opening_stock",
                item_id,
                5,
                to_location_id=location_id,
            )
            commitment = create_commitment(
                session,
                tenant_id,
                "customer_delivery",
                company_id,
                customer_id,
                item_id,
                location_id,
                5,
                "2026-09-04",
            )
            proposal = propose_tool(
                session, tenant_id, "reserve", {"commitment_id": commitment.id}
            )
            proposal_id = proposal.id
            review_token = json.loads(proposal.input)["_delivery_review"]["token"]

        confirmation_barrier = Barrier(2)

        def confirm() -> str:
            confirmation_barrier.wait()
            with factory() as session:
                try:
                    return confirm_tool(
                        session,
                        ids[0],
                        proposal_id,
                        review_token=review_token,
                        confirmed=True,
                    ).output
                except InvalidOperation:
                    return "reconcile"

        with ThreadPoolExecutor(max_workers=2) as executor:
            confirmations = list(executor.map(lambda _: confirm(), range(2)))

        receipts = [value for value in confirmations if value != "reconcile"]
        assert len(receipts) >= 1
        with factory() as session:
            replay = confirm_tool(
                session, ids[0], proposal_id, review_token=review_token, confirmed=True
            )
            assert replay.output == receipts[0]
            reservations = list(
                session.scalars(
                    select(Reservation).where(
                        Reservation.tenant_id == ids[0],
                        Reservation.commitment_id == commitment.id,
                    )
                )
            )
            events = list(
                session.scalars(
                    select(BusinessEvent).where(
                        BusinessEvent.tenant_id == ids[0],
                        BusinessEvent.action_id == proposal_id,
                        BusinessEvent.event_type == "reservation.created",
                    )
                )
            )
            assert len(reservations) == 1
            assert len(events) == 1
            assert events[0].subject_id == reservations[0].id
    finally:
        database_engine.dispose()
        if migrated:
            command.downgrade(config, "base")


def test_postgresql_pool_has_a_bounded_acquisition_timeout(
    postgres_database: str,
) -> None:
    database_engine = build_engine(
        postgres_database,
        pool_settings=resolve_database_pool_settings(
            {
                "REALITY_DB_POOL_SIZE": "1",
                "REALITY_DB_MAX_OVERFLOW": "0",
                "REALITY_DB_POOL_TIMEOUT": "1",
            }
        ),
    )
    try:
        with (
            database_engine.connect(),
            pytest.raises(TimeoutError, match="QueuePool limit"),
        ):
            database_engine.connect()
    finally:
        database_engine.dispose()


def test_concurrent_invite_and_accept_converge_on_one_identity() -> None:
    unique = uid("race")
    with Session() as session:
        tenant = create_tenant(session, f"Concurrent Invitation {unique}")
        owner = AppUser(
            id=uid("usr"),
            email=f"owner-{unique}@example.com",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        recipient = AppUser(
            id=uid("usr"),
            email=f"recipient-{unique}@example.com",
            password_hash="unused",
            status="pending_approval",
            email_verified_at=now(),
        )
        session.add_all([owner, recipient])
        session.flush()
        session.add(
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=owner.id,
                role="owner",
                status="active",
            )
        )
        session.commit()
        ids = tenant.id, owner.id, recipient.id, recipient.email

    def invite() -> str:
        tenant_id, owner_id, _, email = ids
        with Session() as session:
            invitation = create_invitation(
                session, tenant_id, Principal(owner_id), email
            )
            session.commit()
            return invitation.id

    with ThreadPoolExecutor(max_workers=2) as executor:
        invitation_ids = list(executor.map(lambda _: invite(), range(2)))
    assert invitation_ids[0] == invitation_ids[1]

    with Session() as session:
        delivery = session.scalar(
            select(InvitationDelivery).where(
                InvitationDelivery.invitation_id == invitation_ids[0]
            )
        )
        _, _, token = issue_delivery_token(session, ids[0], delivery.id)
        session.commit()

    def accept() -> str:
        with Session() as session:
            membership = accept_invitation(session, token, ids[2])
            session.commit()
            return membership.id

    with ThreadPoolExecutor(max_workers=2) as executor:
        membership_ids = list(executor.map(lambda _: accept(), range(2)))
    assert membership_ids[0] == membership_ids[1]
    with Session() as session:
        assert (
            session.scalar(
                select(func.count(TenantMembership.id)).where(
                    TenantMembership.tenant_id == ids[0],
                    TenantMembership.user_id == ids[2],
                )
            )
            == 1
        )
        invitation_ids_query = select(CompanyInvitation.id).where(
            CompanyInvitation.tenant_id == ids[0]
        )
        session.execute(
            delete(InvitationDelivery).where(
                InvitationDelivery.invitation_id.in_(invitation_ids_query)
            )
        )
        session.execute(
            delete(SecurityAuditEvent).where(SecurityAuditEvent.tenant_id == ids[0])
        )
        session.execute(
            delete(CompanyInvitation).where(CompanyInvitation.tenant_id == ids[0])
        )
        session.execute(
            delete(TenantMembership).where(TenantMembership.tenant_id == ids[0])
        )
        session.execute(delete(AppUser).where(AppUser.id.in_((ids[1], ids[2]))))
        for model in (FinanceRoleDestination, FinanceState, SubledgerAccount):
            session.execute(delete(model).where(model.tenant_id == ids[0]))
        session.execute(delete(Tenant).where(Tenant.id == ids[0]))
        session.commit()


@pytest.mark.parametrize("owner_action", ["resend", "revoke"])
def test_concurrent_accept_and_owner_action_serialize_without_deadlock(
    owner_action: str,
) -> None:
    unique = uid("race")
    with Session() as session:
        tenant = create_tenant(session, f"Concurrent {owner_action} {unique}")
        owner = AppUser(
            id=uid("usr"),
            email=f"owner-{unique}@example.com",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        recipient = AppUser(
            id=uid("usr"),
            email=f"recipient-{unique}@example.com",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        session.add_all([owner, recipient])
        session.flush()
        session.add(
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=owner.id,
                role="owner",
                status="active",
            )
        )
        invitation = create_invitation(
            session, tenant.id, Principal(owner.id), recipient.email
        )
        delivery = session.scalar(
            select(InvitationDelivery).where(
                InvitationDelivery.invitation_id == invitation.id
            )
        )
        delivery.created_at = now() - timedelta(seconds=61)
        _, _, token = issue_delivery_token(session, tenant.id, delivery.id)
        session.commit()
        ids = tenant.id, owner.id, recipient.id, invitation.id

    def accept() -> str:
        try:
            with Session() as session:
                accept_invitation(session, token, ids[2])
                session.commit()
            return "accepted"
        except Exception as error:  # noqa: BLE001 - the losing serialized action is expected
            return type(error).__name__

    def administer() -> str:
        try:
            with Session() as session:
                if owner_action == "resend":
                    resend_invitation(session, ids[0], Principal(ids[1]), ids[3])
                else:
                    revoke_invitation(session, ids[0], Principal(ids[1]), ids[3])
                session.commit()
            return owner_action
        except Exception as error:  # noqa: BLE001 - the losing serialized action is expected
            return type(error).__name__

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(operation) for operation in (accept, administer)]
        results = [future.result(timeout=10) for future in futures]

    assert "OperationalError" not in results
    with Session() as session:
        invitation = record_by_id(session, CompanyInvitation, ids[3])
        assert invitation.status in (
            {"accepted", "pending"}
            if owner_action == "resend"
            else {"accepted", "revoked"}
        )
        assert session.scalar(
            select(func.count(TenantMembership.id)).where(
                TenantMembership.tenant_id == ids[0],
                TenantMembership.user_id == ids[2],
            )
        ) in {0, 1}
        invitation_ids_query = select(CompanyInvitation.id).where(
            CompanyInvitation.tenant_id == ids[0]
        )
        session.execute(
            delete(InvitationDelivery).where(
                InvitationDelivery.invitation_id.in_(invitation_ids_query)
            )
        )
        session.execute(
            delete(SecurityAuditEvent).where(SecurityAuditEvent.tenant_id == ids[0])
        )
        session.execute(
            delete(CompanyInvitation).where(CompanyInvitation.tenant_id == ids[0])
        )
        session.execute(
            delete(TenantMembership).where(TenantMembership.tenant_id == ids[0])
        )
        session.execute(delete(AppUser).where(AppUser.id.in_((ids[1], ids[2]))))
        for model in (FinanceRoleDestination, FinanceState, SubledgerAccount):
            session.execute(delete(model).where(model.tenant_id == ids[0]))
        session.execute(delete(Tenant).where(Tenant.id == ids[0]))
        session.commit()


def test_concurrent_delivery_claim_uses_skip_locked_once() -> None:
    unique = uid("claim")
    with Session() as session:
        tenant = create_tenant(session, f"Concurrent Delivery {unique}")
        owner = AppUser(
            id=uid("usr"),
            email=f"owner-{unique}@example.com",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        session.add(owner)
        session.flush()
        session.add(
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=owner.id,
                role="owner",
                status="active",
            )
        )
        invitation = create_invitation(
            session,
            tenant.id,
            Principal(owner.id),
            f"recipient-{unique}@example.com",
        )
        session.commit()
        ids = tenant.id, owner.id, invitation.id

    claimed = Barrier(2)

    def claim() -> str | None:
        with Session() as session:
            delivery = claim_due_delivery(session)
            claimed.wait(timeout=5)
            return delivery.id if delivery else None

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: claim(), range(2)))

    assert sum(result is not None for result in results) == 1
    with Session() as session:
        invitation_ids_query = select(CompanyInvitation.id).where(
            CompanyInvitation.tenant_id == ids[0]
        )
        session.execute(
            delete(InvitationDelivery).where(
                InvitationDelivery.invitation_id.in_(invitation_ids_query)
            )
        )
        session.execute(
            delete(SecurityAuditEvent).where(SecurityAuditEvent.tenant_id == ids[0])
        )
        session.execute(
            delete(CompanyInvitation).where(CompanyInvitation.tenant_id == ids[0])
        )
        session.execute(
            delete(TenantMembership).where(TenantMembership.tenant_id == ids[0])
        )
        session.execute(delete(AppUser).where(AppUser.id == ids[1]))
        for model in (FinanceRoleDestination, FinanceState, SubledgerAccount):
            session.execute(delete(model).where(model.tenant_id == ids[0]))
        session.execute(delete(Tenant).where(Tenant.id == ids[0]))
        session.commit()


def test_concurrent_remove_and_reinvite_preserve_one_membership_identity() -> None:
    unique = uid("race")
    with Session() as session:
        tenant = create_tenant(session, f"Concurrent Remove Reinvite {unique}")
        owner = AppUser(
            id=uid("usr"),
            email=f"owner-{unique}@example.com",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        member = AppUser(
            id=uid("usr"),
            email=f"member-{unique}@example.com",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        session.add_all([owner, member])
        session.flush()
        membership = TenantMembership(
            id=uid("tmb"),
            tenant_id=tenant.id,
            user_id=member.id,
            role="member",
            status="active",
        )
        session.add_all(
            [
                TenantMembership(
                    id=uid("tmb"),
                    tenant_id=tenant.id,
                    user_id=owner.id,
                    role="owner",
                    status="active",
                ),
                membership,
            ]
        )
        session.commit()
        ids = tenant.id, owner.id, member.id, membership.id, member.email

    def remove() -> str:
        with Session() as session:
            remove_member(session, ids[0], Principal(ids[1]), ids[3])
            session.commit()
        return "removed"

    def reinvite() -> str:
        with Session() as session:
            invitation = create_invitation(session, ids[0], Principal(ids[1]), ids[4])
            session.commit()
        return invitation.id if invitation else "neutral"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda operation: operation(), (remove, reinvite)))

    assert "removed" in results
    with Session() as session:
        membership = record_by_id(session, TenantMembership, ids[3])
        assert membership is not None
        assert membership.status == "removed"
        assert (
            session.scalar(
                select(func.count(TenantMembership.id)).where(
                    TenantMembership.tenant_id == ids[0],
                    TenantMembership.user_id == ids[2],
                )
            )
            == 1
        )
        assert session.scalar(
            select(func.count(CompanyInvitation.id)).where(
                CompanyInvitation.tenant_id == ids[0],
                CompanyInvitation.normalized_email == ids[4],
            )
        ) in {0, 1}
        invitation_ids_query = select(CompanyInvitation.id).where(
            CompanyInvitation.tenant_id == ids[0]
        )
        session.execute(
            delete(InvitationDelivery).where(
                InvitationDelivery.invitation_id.in_(invitation_ids_query)
            )
        )
        session.execute(
            delete(SecurityAuditEvent).where(SecurityAuditEvent.tenant_id == ids[0])
        )
        session.execute(
            delete(CompanyInvitation).where(CompanyInvitation.tenant_id == ids[0])
        )
        session.execute(
            delete(TenantMembership).where(TenantMembership.tenant_id == ids[0])
        )
        session.execute(delete(AppUser).where(AppUser.id.in_((ids[1], ids[2]))))
        for model in (FinanceRoleDestination, FinanceState, SubledgerAccount):
            session.execute(delete(model).where(model.tenant_id == ids[0]))
        session.execute(delete(Tenant).where(Tenant.id == ids[0]))
        session.commit()


def test_remove_does_not_interrupt_authorized_in_flight_work_but_next_read_denies() -> (
    None
):
    unique = uid("race")
    with Session() as session:
        tenant = create_tenant(session, f"Concurrent In Flight {unique}")
        owner = AppUser(
            id=uid("usr"),
            email=f"owner-{unique}@example.com",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        member = AppUser(
            id=uid("usr"),
            email=f"member-{unique}@example.com",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        session.add_all([owner, member])
        session.flush()
        membership = TenantMembership(
            id=uid("tmb"),
            tenant_id=tenant.id,
            user_id=member.id,
            role="member",
            status="active",
        )
        session.add_all(
            [
                TenantMembership(
                    id=uid("tmb"),
                    tenant_id=tenant.id,
                    user_id=owner.id,
                    role="owner",
                    status="active",
                ),
                membership,
            ]
        )
        session.commit()
        ids = tenant.id, owner.id, member.id, membership.id

    authorized = Barrier(2)
    removed = Barrier(2)

    def in_flight() -> tuple[str, str]:
        with Session() as session:
            first = session.scalar(
                select(TenantMembership.status).where(
                    TenantMembership.id == ids[3],
                    TenantMembership.tenant_id == ids[0],
                    TenantMembership.user_id == ids[2],
                )
            )
            authorized.wait(timeout=5)
            removed.wait(timeout=5)
            session.expire_all()
            second = session.scalar(
                select(TenantMembership.status).where(
                    TenantMembership.id == ids[3],
                    TenantMembership.tenant_id == ids[0],
                    TenantMembership.user_id == ids[2],
                )
            )
            return first, second

    def remove() -> None:
        authorized.wait(timeout=5)
        with Session() as session:
            remove_member(session, ids[0], Principal(ids[1]), ids[3])
            session.commit()
        removed.wait(timeout=5)

    with ThreadPoolExecutor(max_workers=2) as executor:
        access_future = executor.submit(in_flight)
        removal_future = executor.submit(remove)
        removal_future.result(timeout=10)
        observations = access_future.result(timeout=10)

    assert observations == ("active", "removed")
    with Session() as session:
        assert (
            session.scalar(
                select(TenantMembership.id).where(
                    TenantMembership.tenant_id == ids[0],
                    TenantMembership.user_id == ids[2],
                    TenantMembership.status == "active",
                )
            )
            is None
        )
        session.execute(
            delete(SecurityAuditEvent).where(SecurityAuditEvent.tenant_id == ids[0])
        )
        session.execute(
            delete(TenantMembership).where(TenantMembership.tenant_id == ids[0])
        )
        session.execute(delete(AppUser).where(AppUser.id.in_((ids[1], ids[2]))))
        for model in (FinanceRoleDestination, FinanceState, SubledgerAccount):
            session.execute(delete(model).where(model.tenant_id == ids[0]))
        session.execute(delete(Tenant).where(Tenant.id == ids[0]))
        session.commit()
