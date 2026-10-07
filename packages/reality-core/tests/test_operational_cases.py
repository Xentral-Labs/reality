"""First-slice coordination: current facts, takeover and exact handback."""

import json
from pathlib import Path

import pytest
from reality.db.core import ChangeProposal, now, uid
from reality.db.operational_cases import OperationalCase
from reality.services import core
from reality.services import operational_cases as cases
from reality.services.case_action_guards import automated_execution, guard_operation
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake
from reality.services.memberships import Principal
from sqlalchemy import select

FIXTURE = Path(__file__).parent.parent / "fixtures/shopify/order_10473.json"


def order(session, business):
    payload = json.loads(FIXTURE.read_text())
    _, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        review["digest"],
        confirmed=True,
    )
    return core.commitments(session, business.tenant.id)[0]


def activate(session, business, owner):
    result = cases.adopt(
        session,
        business.tenant.id,
        Principal(owner.id),
        confirmed=True,
        request_key=uid("req"),
    )
    cases.reconcile_events(session, business.tenant.id)
    return result


def test_case_register_keeps_completed_human_work_and_exact_control_attribution(
    session, business, scheduled_owner
):
    # BUSINESS PURPOSE: A human can always find the exact case they removed from automation.
    # BUSINESS RULE: Completion does not erase responsibility; control attribution comes from retained decisions/events.
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    principal = Principal(scheduled_owner.id)
    result = cases.takeover(
        session,
        business.tenant.id,
        case_id,
        principal,
        expected_revision=1,
        request_key="register-take",
        confirmed=True,
        reason="Handle the customer escalation myself",
    )
    assert result["control"]["actor_user_id"] == scheduled_owner.id
    assert result["control"]["reason"] == "Handle the customer escalation myself"
    assert result["control"]["decision_id"] and result["control"]["event_id"]
    repeated = cases.takeover(
        session,
        business.tenant.id,
        case_id,
        principal,
        expected_revision=1,
        request_key="register-take",
        confirmed=True,
        reason="Handle the customer escalation myself",
    )
    assert repeated == result
    for row in cases.explain(session, business.tenant.id, case_id)["work"]:
        core.cancel_commitment(
            session,
            business.tenant.id,
            row["commitment_id"],
            reason="Customer cancelled",
        )
    register = cases.register_cases(session, business.tenant.id, control_mode="human")
    assert register["total"] == 1 and register["items"][0]["goal_state"] == "completed"
    assert register["counts"]["human"] == 1
    assert register["kind_counts"]["order_fulfillment"]["human"] == 1
    assert register["kind_counts"]["order_fulfillment"]["completed"] == 1
    assert register["kind_counts"]["order_fulfillment"]["outstanding"] == 0
    assert register["kind_counts"]["customer_return"]["human"] == 0
    assert (
        cases.register_cases(
            session, business.tenant.id, control_mode="human", outstanding_only=True
        )["total"]
        == 0
    )
    assert commitment.document_id == register["items"][0]["order_document_id"]


def test_case_register_cursor_is_bound_to_company_and_filters(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    order(session, business)
    for arguments in (
        {"limit": True},
        {"kind": "purchase"},
        {"control_mode": "robot"},
        {"outstanding_only": "true"},
        {"after": "not-a-cursor"},
    ):
        with pytest.raises(core.InvalidOperation):
            cases.register_cases(session, business.tenant.id, **arguments)


def test_bounded_case_actions_keep_complete_unresolved_execution_visibility(
    session, business, scheduled_owner
):
    # BUSINESS PURPOSE: A compact explanation must never hide an execution already started.
    # BUSINESS RULE: Display samples are independent of complete unresolved-execution evidence.
    activate(session, business, scheduled_owner)
    order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    for index in range(4):
        action = ChangeProposal(
            id=f"action_{index}",
            tenant_id=business.tenant.id,
            type="tool:commitment_revise",
            input="{}",
            output="{}",
            status="executing" if index == 3 else "executed",
        )
        session.add(action)
        session.flush()
        cases.bind_proposal(session, business.tenant.id, action.id, [case_id])
    compact = cases.explain(session, business.tenant.id, case_id, action_limit=1)
    assert len(compact["actions"]) == 1 and compact["actions_has_more"]
    assert compact["unsettled_action_total"] == 1
    assert compact["unsettled_actions"] == ["action_3"]


def test_staging_does_not_create_case(session, business, scheduled_owner):
    activate(session, business, scheduled_owner)
    payload = json.loads(FIXTURE.read_text())
    _, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    prepare_intake(session, business.tenant.id, job.id)
    assert session.scalar(select(OperationalCase)) is None


def test_acceptance_ensures_case_and_event_replay_is_idempotent(
    session,
    business,
    scheduled_owner,
):
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    initial = cases.list_cases(session, business.tenant.id)
    assert len(initial) == 1
    assert initial[0]["order_document_id"] == commitment.document_id
    cases.reconcile_events(session, business.tenant.id)
    cases.reconcile_events(session, business.tenant.id)
    assert [c["case_id"] for c in cases.list_cases(session, business.tenant.id)] == [
        initial[0]["case_id"]
    ]


def test_legacy_activation_does_not_reset_default_order_case(
    session, business, scheduled_owner
):
    commitment = order(session, business)
    original = cases.object_cases(
        session, business.tenant.id, "commitment", commitment.id
    )
    activate(session, business, scheduled_owner)
    assert len(original) == 1
    assert (
        cases.object_cases(session, business.tenant.id, "commitment", commitment.id)
        == original
    )


def test_takeover_blocks_direct_automation_but_allows_human_repair(
    session,
    business,
    scheduled_owner,
):
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    taken = cases.takeover(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take-1",
        confirmed=True,
    )
    assert taken["control_mode"] == "human"
    with (
        automated_execution(session, business.tenant.id),
        pytest.raises(core.InvalidOperation, match="manually owned"),
    ):
        core.revise_commitment(
            session, business.tenant.id, commitment.id, quantity="20"
        )
    core.revise_commitment(session, business.tenant.id, commitment.id, quantity="20")
    assert core.commitment_quantity(session, business.tenant.id, commitment.id) == 20


def test_handback_is_exact_and_old_action_generation_stays_invalid(
    session,
    business,
    scheduled_owner,
):
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="tool:commitment_revise",
        actor_type="agent",
        status="proposed",
        input="{}",
        created_at=now(),
    )
    session.add(proposal)
    session.flush()
    cases.bind_proposal(session, business.tenant.id, proposal.id, [case_id])
    cases.takeover(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take-2",
        confirmed=True,
    )
    review = cases.handback_preview(session, business.tenant.id, case_id)
    core.revise_commitment(session, business.tenant.id, commitment.id, quantity="20")
    with pytest.raises(core.InvalidOperation, match="case changed"):
        cases.handback(
            session,
            business.tenant.id,
            case_id,
            Principal(scheduled_owner.id),
            review_digest=review["digest"],
            request_key="back-1",
            confirmed=True,
        )
    review = cases.handback_preview(session, business.tenant.id, case_id)
    cases.handback(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        review_digest=review["digest"],
        request_key="back-2",
        confirmed=True,
    )
    with (
        automated_execution(session, business.tenant.id, proposal_id=proposal.id),
        pytest.raises(core.InvalidOperation, match="older case control"),
    ):
        guard_operation(
            session,
            business.tenant.id,
            "revise_commitment",
            {
                "commitment_id": commitment.id,
            },
        )


def test_executing_action_prevents_handback(session, business, scheduled_owner):
    activate(session, business, scheduled_owner)
    order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    action = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="tool:shipment_dispatch",
        status="executing",
        input="{}",
    )
    session.add(action)
    session.flush()
    cases.bind_proposal(session, business.tenant.id, action.id, [case_id])
    cases.takeover(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take-3",
        confirmed=True,
    )
    review = cases.handback_preview(session, business.tenant.id, case_id)
    assert review["unsettled_actions"] == [action.id]
    with pytest.raises(core.InvalidOperation, match="unresolved execution"):
        cases.handback(
            session,
            business.tenant.id,
            case_id,
            Principal(scheduled_owner.id),
            review_digest=review["digest"],
            request_key="back-3",
            confirmed=True,
        )


def test_announced_return_is_distinct_and_not_transferred(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "30",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    announcement = core.announce_customer_return(
        session,
        business.tenant.id,
        commitment.id,
        "1",
    )
    result = cases.list_cases(session, business.tenant.id)
    assert {c["kind"] for c in result} == {"order_fulfillment", "customer_return"}
    ret = next(c for c in result if c["kind"] == "customer_return")
    assert ret["return_announcement_id"] == announcement.id
    register = cases.register_cases(session, business.tenant.id)
    assert register["kind_counts"]["customer_return"]["total"] == 1
    assert register["kind_counts"]["customer_return"]["outstanding"] == 1
    assert register["kind_counts"]["order_fulfillment"]["total"] == 1
    fulfillment = next(c for c in result if c["kind"] == "order_fulfillment")
    cases.takeover(
        session,
        business.tenant.id,
        fulfillment["case_id"],
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take-4",
        confirmed=True,
    )
    assert (
        cases.explain(session, business.tenant.id, ret["case_id"])["control_mode"]
        == "automation"
    )


def test_foreign_case_and_missing_principal_refused(session, business, scheduled_owner):
    activate(session, business, scheduled_owner)
    order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    foreign = core.create_tenant(session, "Other")
    with pytest.raises(core.NotFound):
        cases.explain(session, foreign.id, case_id)
    with pytest.raises(core.NotFound):
        cases.takeover(
            session,
            business.tenant.id,
            case_id,
            None,
            expected_revision=1,
            request_key="take-5",
            confirmed=True,
        )


def test_register_search_is_company_scoped_and_does_not_treat_numbers_as_identity(
    session, business, scheduled_owner
):
    # BUSINESS PURPOSE: An operator can locate a business reference in a complete supported register.
    # BUSINESS RULE: A display-number search only filters exact opaque cases; it grants no control or identity binding.
    activate(session, business, scheduled_owner)
    for number in ("SEARCH-ALPHA", "SEARCH-BETA"):
        core.create_manual_order(
            session,
            business.tenant.id,
            "sales",
            number,
            business.company.id,
            business.customer.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "1",
                    "gross_amount": "1",
                }
            ],
            "1",
        )
    result = cases.register_cases(session, business.tenant.id, query="alpha")
    assert result["total"] == 1
    assert result["items"][0]["business_reference"] == "SEARCH-ALPHA"
    assert result["counts"]["outstanding"] == 2
    assert cases.register_cases(session, business.tenant.id, query="%")["total"] == 0
    case_id = result["items"][0]["case_id"]
    assert (
        cases.register_cases(session, business.tenant.id, query=case_id)["total"] == 1
    )


def test_register_complete_counts_and_all_pages_exceed_two_hundred_cases(
    session, business, scheduled_owner
):
    # BUSINESS PURPOSE: Larger human registers remain discoverable beyond display samples.
    # BUSINESS RULE: Page cursors retain complete counts and every matching case exactly once.
    activate(session, business, scheduled_owner)
    expected = set()
    for index in range(205):
        _, doc, _, _ = core.create_manual_order(
            session,
            business.tenant.id,
            "sales",
            f"PAGE-{index}",
            business.company.id,
            business.customer.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "1",
                    "gross_amount": "1",
                }
            ],
            "1",
            _commit=False,
        )
        expected.add(doc.id)
    session.flush()
    found = []
    cursor = ""
    while True:
        page = cases.register_cases(
            session, business.tenant.id, query="PAGE-", after=cursor, limit=100
        )
        assert page["total"] == 205 and page["counts"]["outstanding"] == 205
        found.extend(row["order_document_id"] for row in page["items"])
        if not page["has_more"]:
            break
        cursor = page["next_after"]
    assert len(found) == 205 and set(found) == expected
    with pytest.raises(core.InvalidOperation):
        cases.register_cases(session, business.tenant.id, query="other", after=cursor)


def test_snapshot_register_batches_original_inputs_without_losing_case_evidence(
    session, business, scheduled_owner
):
    # BUSINESS PURPOSE: A large-company live register retains explainable work without per-case query fan-out.
    # BUSINESS RULE: Bounded previews preserve canonical source/control/action results and complete unsettled counts.
    from datetime import timedelta

    from sqlalchemy import event

    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    source_case = cases.object_cases(
        session, business.tenant.id, "document", commitment.document_id
    )[0]
    for index in range(6):
        core.create_manual_order(
            session,
            business.tenant.id,
            "sales",
            f"BATCH-{index}",
            business.company.id,
            business.customer.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "1",
                    "gross_amount": "1",
                }
            ],
            "1",
            _commit=False,
        )
    session.flush()
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "30",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    announcement = core.announce_customer_return(
        session,
        business.tenant.id,
        commitment.id,
        "1",
        reference="Independent return",
    )
    manual = session.scalars(
        select(OperationalCase).where(
            OperationalCase.tenant_id == business.tenant.id,
            OperationalCase.order_document_id != commitment.document_id,
        )
    ).first()
    for row in cases.explain(session, business.tenant.id, manual.id)["work"]:
        core.cancel_commitment(
            session,
            business.tenant.id,
            row["commitment_id"],
            reason="Customer cancellation",
        )
    action_time = now()
    for index in range(52):
        action = ChangeProposal(
            id=f"batch_action_{index:03}",
            tenant_id=business.tenant.id,
            type="tool:commitment_revise",
            input="{}",
            output="{}",
            status="proposed" if index == 0 else "executing",
            created_at=action_time + timedelta(seconds=1)
            if index == 0
            else action_time,
        )
        session.add(action)
        session.flush()
        cases.bind_proposal(session, business.tenant.id, action.id, [source_case])
    cases.takeover(
        session,
        business.tenant.id,
        source_case,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="batch-take",
        confirmed=True,
        reason="Personally resolve the customer escalation",
    )
    payload = json.loads(FIXTURE.read_text())
    payload["note"] = "A newer customer source awaits interpretation"
    core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    session.flush()
    session.expire_all()
    expected = cases.register_cases(session, business.tenant.id, limit=20)
    session.expire_all()
    reads = []

    def observe(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            reads.append(statement)

    bind = session.get_bind()
    event.listen(bind, "before_cursor_execute", observe)
    session.info["operations_snapshot_consistent"] = True
    try:
        actual = cases.register_cases(session, business.tenant.id, limit=20)
    finally:
        session.info.pop("operations_snapshot_consistent", None)
        event.remove(bind, "before_cursor_execute", observe)
    assert actual == expected
    explained = next(row for row in actual["items"] if row["case_id"] == source_case)
    assert (
        explained["control"]["reason"] == "Personally resolve the customer escalation"
    )
    assert explained["control"]["actor_user_id"] == scheduled_owner.id
    assert explained["source_record_ids"]
    assert explained["unsettled_action_total"] == 51
    assert len(explained["unsettled_actions"]) == 50
    assert explained["actions_has_more"]
    assert explained["coverage_gaps"]
    assert explained["actions"][0]["proposal_id"] == "batch_action_000"
    assert explained["actions"][0]["obsolescence_reason"] == "control_revision_changed"
    returned = next(
        row
        for row in actual["items"]
        if row["return_announcement_id"] == announcement.id
    )
    assert returned["control_mode"] == "automation"
    assert source_case in returned["related_case_ids"]
    assert returned["case_id"] in explained["related_case_ids"]
    assert (
        next(row for row in actual["items"] if row["case_id"] == manual.id)[
            "goal_state"
        ]
        == "completed"
    )
    assert len(reads) <= 55, f"A bounded eight-case page issued {len(reads)} reads"


def test_case_explanation_inputs_never_cross_company_or_override_other_read_limits(
    session, business, scheduled_owner
):
    # BUSINESS PURPOSE: Faster live reads retain exact company and explanation scope.
    # BUSINESS RULE: Private original inputs belong to one snapshot/session/company and the bounded register read only.
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    case_id = cases.object_cases(
        session, business.tenant.id, "document", commitment.document_id
    )[0]
    expected = {
        limit: cases.explain(session, business.tenant.id, case_id, action_limit=limit)
        for limit in (None, 1, 50)
    }
    session.info["operations_snapshot_consistent"] = True
    try:
        inputs = cases._explanation_inputs(session, business.tenant.id, [case_id])
        for limit in (None, 1, 50):
            assert (
                cases.explain(
                    session,
                    business.tenant.id,
                    case_id,
                    action_limit=limit,
                    _inputs=inputs,
                )
                == expected[limit]
            )
        with pytest.raises(core.NotFound) as refused:
            cases.explain(
                session, "foreign-company", case_id, action_limit=50, _inputs=inputs
            )
        assert refused.value.code == "case_not_found"
        foreign_inputs = {**inputs, "tenant_id": "foreign-company"}
        assert (
            cases.explain(
                session,
                business.tenant.id,
                case_id,
                action_limit=50,
                _inputs=foreign_inputs,
            )
            == expected[50]
        )
    finally:
        session.info.pop("operations_snapshot_consistent", None)
    assert (
        cases.explain(
            session, business.tenant.id, case_id, action_limit=50, _inputs=inputs
        )
        == expected[50]
    )


def test_register_exposes_default_cases_without_creating_legacy_adoption(
    session, business
):
    # BUSINESS PURPOSE: Control Tower must show current accepted work without owner activation.
    # BUSINESS RULE: Reads preserve platform coordination and do not adopt history or emit events.
    from reality.db.core import BusinessEvent
    from reality.db.operational_cases import CaseAdoption

    commitment = order(session, business)
    before = list(session.scalars(select(BusinessEvent.id)))
    result = cases.register_cases(session, business.tenant.id)
    assert result["adopted"] is True
    assert result["total"] == result["counts"]["outstanding"] == 1
    assert result["items"][0]["order_document_id"] == commitment.document_id
    assert result["coordination"]["rollout_provenance"] == "platform_version"
    assert result["coordination"]["coverage_ready"] is False
    assert session.get(CaseAdoption, business.tenant.id) is None
    assert list(session.scalars(select(BusinessEvent.id))) == before
    cases.reconcile_events(session, business.tenant.id)
    result = cases.register_cases(session, business.tenant.id)
    assert result["coordination"]["coverage_ready"] is True
    assert result["total"] == 1


def test_snapshot_shared_large_actions_preserve_review_without_opaque_input_transfer(
    session, business, scheduled_owner
):
    # BUSINESS PURPOSE: Real enterprise batch actions must not multiply opaque payload transfer on a live register page.
    # BUSINESS RULE: Original action results, per-case review obsolescence and source evidence match scalar reads; unused invocation input stays deferred.
    from sqlalchemy import event

    activate(session, business, scheduled_owner)
    for index in range(2):
        core.create_manual_order(
            session,
            business.tenant.id,
            "sales",
            f"SHARED-BATCH-{index}",
            business.company.id,
            business.customer.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "1",
                    "gross_amount": "1",
                }
            ],
            "1",
            _commit=False,
        )
    session.flush()
    identities = list(
        session.scalars(
            select(OperationalCase.id).where(
                OperationalCase.tenant_id == business.tenant.id
            )
        )
    )
    frozen = {
        identity: cases.business_review(session, business.tenant.id, identity)
        for identity in identities
    }
    for status in ("executed", "proposed"):
        action = ChangeProposal(
            id=f"shared_large_{status}",
            tenant_id=business.tenant.id,
            type="tool:commitment_revise",
            input=json.dumps({"opaque": "x" * 250000}),
            output=json.dumps(
                {"opaque": "y" * 250000, "_case_business_review": frozen}
            ),
            status=status,
        )
        session.add(action)
        session.flush()
        cases.bind_proposal(session, business.tenant.id, action.id, identities)
    first = cases.explain(session, business.tenant.id, identities[0])
    core.cancel_commitment(
        session,
        business.tenant.id,
        first["work"][0]["commitment_id"],
        reason="Customer cancelled",
    )
    session.flush()
    session.expire_all()
    expected = cases.register_cases(session, business.tenant.id, limit=20)
    session.expire_all()
    reads = []

    def observe(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            reads.append(statement)

    bind = session.get_bind()
    event.listen(bind, "before_cursor_execute", observe)
    session.info["operations_snapshot_consistent"] = True
    try:
        actual = cases.register_cases(session, business.tenant.id, limit=20)
    finally:
        session.info.pop("operations_snapshot_consistent", None)
        event.remove(bind, "before_cursor_execute", observe)
    assert actual == expected
    for item in actual["items"]:
        done = next(
            action
            for action in item["actions"]
            if action["proposal_id"] == "shared_large_executed"
        )
        assert done["recorded_result_available"]
        assert done["external_outcome"] == "not_established_by_execution_status"
        proposed = next(
            action
            for action in item["actions"]
            if action["proposal_id"] == "shared_large_proposed"
        )
        assert proposed["obsolete"] is (item["goal_state"] != "outstanding")
    assert not any(
        f"{ChangeProposal.__tablename__}.input" in statement for statement in reads
    ), "Live action metadata transferred unused opaque invocation input"
    assert session.get(
        ChangeProposal, (business.tenant.id, "shared_large_executed")
    ).input == json.dumps({"opaque": "x" * 250000})


def test_register_kind_counts_are_complete_and_independent_of_page_filters(
    session, business, scheduled_owner
):
    # BUSINESS PURPOSE: The company overview distinguishes complete case ownership from current open work.
    # BUSINESS RULE: Canonical per-kind observations partition the original tenant-scoped counts, independently of a filtered preview.
    activate(session, business, scheduled_owner)
    order(session, business)
    whole = cases.register_cases(session, business.tenant.id, limit=1)
    filtered = cases.register_cases(
        session,
        business.tenant.id,
        kind="customer_return",
        query="missing",
        control_mode="human",
    )
    assert filtered["total"] == 0
    assert filtered["kind_counts"] == whole["kind_counts"]
    assert whole["kind_counts"]["order_fulfillment"]["outstanding"] == 1
    assert set(whole["kind_counts"]) == {"order_fulfillment", "customer_return"}
    for key, count in whole["counts"].items():
        assert sum(row[key] for row in whole["kind_counts"].values()) == count
    other = core.create_tenant(session, name="Unrelated case overview")
    assert all(
        not any(row.values())
        for row in cases.register_cases(session, other.id)["kind_counts"].values()
    )
