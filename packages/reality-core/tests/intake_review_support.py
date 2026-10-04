"""Explicit real reviewer fixtures for stories requiring accepted source evidence.

These helpers submit exact retained decisions; they do not change any service,
permission check or runtime approval context. Refusal/preparation tests call the
real entrypoints directly.
"""

import json

from sqlalchemy import select

from reality.db.core import (
    AppUser,
    Commitment,
    Document,
    DocumentLine,
    ImportJob,
    SourceRecord,
    TenantMembership,
)
from reality.services import core, intake_batches
from reality.services.intake import apply_prepared_intake, review_intake
from reality.services.memberships import Principal


def explicit_owner(session, tenant_id):
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.role == "owner",
            TenantMembership.status == "active",
        )
    )
    if membership:
        return Principal(membership.user_id)
    owner = AppUser(
        id=core.uid("usr"),
        email=f"{core.uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=core.now(),
    )
    session.add(owner)
    session.flush()
    session.add(
        TenantMembership(
            id=core.uid("tmb"),
            tenant_id=tenant_id,
            user_id=owner.id,
            role="owner",
            status="active",
        )
    )
    session.flush()
    return Principal(owner.id)


def accept_import_job(session, tenant_id, job_id):
    """Review and confirm one exact retained source, then return accepted evidence."""
    try:
        proposal = core.process_import_job(session, tenant_id, job_id)
    except core.InterpretationNeedsReview:
        return None
    if proposal is None:
        return None
    owner = explicit_owner(session, tenant_id)
    job = core._tenant_record_read(session, ImportJob, tenant_id, job_id)
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, job.source_record_id
    )
    if proposal.type == "tool:intake_batch_apply":
        intake_batches.approve_batch(
            session,
            tenant_id,
            proposal.id,
            json.loads(proposal.input)["digest"],
            confirmed=True,
            principal=owner,
        )
        while proposal.status != "executed":
            intake_batches.settle_chunk(
                session,
                tenant_id,
                proposal.id,
                continuation_id=json.loads(proposal.output)["continuation_id"],
            )
            session.commit()
        status = intake_batches.batch_status(session, tenant_id, proposal.id)
        receipts = []
        for row in status["results"]:
            if row["disposition"] in {"applied", "replayed"}:
                receipts.append(row["receipt"])
                continue
            # Related orders change the customer's reviewed exposure. The fixture
            # asks its real owner for a separate fresh review, never reuses bulk consent.
            assert (
                row["disposition"] == "review_required"
                and row["reason_code"] == "intake_review_stale"
            ), status
            from reality.db.core import ChangeProposal
            from reality.services.intake import renew_prepared_intake

            previous = core._tenant_record_read(
                session, ChangeProposal, tenant_id, row["proposal_id"]
            )
            child_job_id = json.loads(previous.input)["plan"]["import_job_id"]
            renewed = renew_prepared_intake(
                session,
                tenant_id,
                child_job_id,
                previous_proposal_id=previous.id,
                request_id=core.uid("fixture_review"),
            )
            fresh = review_intake(session, tenant_id, renewed.id)
            receipt = apply_prepared_intake(
                session,
                tenant_id,
                renewed.id,
                fresh["digest"],
                confirmed=True,
                principal=owner,
            )
            receipts.append(json.loads(receipt.output))
        target = json.loads(job.input).get("expected_target")
        ids = [
            record["id"]
            for receipt in receipts
            for record in receipt["records"]
            if record["type"]
            == {
                "sales_order": "document",
                "bank_statement": "document",
                "inventory_snapshot": "movement",
                "external_stock": "external_stock_statement",
            }.get(target, target)
        ]
        return {"target": target, "rows": len(ids), "created_ids": ids}
    held = review_intake(session, tenant_id, proposal.id)
    applied = apply_prepared_intake(
        session, tenant_id, proposal.id, held["digest"], confirmed=True, principal=owner
    )
    target = json.loads(job.input).get("expected_target")
    if target:
        records = json.loads(applied.output)["records"]
        kind = {
            "sales_order": "document",
            "bank_statement": "document",
            "inventory_snapshot": "movement",
            "external_stock": "external_stock_statement",
        }.get(target, target)
        ids = [row["id"] for row in records if row["type"] == kind]
        return {"target": target, "rows": len(ids), "created_ids": ids}
    if source.source_type == "order":
        from reality.services.shop_order_changes import order_for_source

        document = order_for_source(session, tenant_id, source)
    else:
        document = session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id, Document.source_record_id == source.id
            )
        )
    assert applied.status == "executed"
    if document is None:
        return applied
    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import JSONB

    from reality.db.core import ChangeProposal

    original = applied
    if document.source_record_id != source.id:
        original = session.scalar(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.type == "tool:intake_apply",
                ChangeProposal.status == "executed",
                cast(ChangeProposal.output, JSONB)["source_record_id"].astext
                == document.source_record_id,
            )
        )
    records = json.loads(original.output)["records"]
    lines = [
        core._tenant_record_read(session, DocumentLine, tenant_id, record["id"])
        for record in records
        if record["type"] == "document_line"
    ]
    commitments = [
        core._tenant_record_read(session, Commitment, tenant_id, record["id"])
        for record in records
        if record["type"] == "commitment"
    ]
    return source, document, lines, commitments


def accept_shopify_order(
    session, tenant_id, payload, company_party_id, customer_party_id, location_id
):
    _, job = core.enqueue_shopify_order(
        session, tenant_id, payload, company_party_id, customer_party_id, location_id
    )
    return accept_import_job(session, tenant_id, job.id)


def accept_pending_import_jobs(session, tenant_id):
    ids = list(
        session.scalars(
            select(ImportJob.id).where(
                ImportJob.tenant_id == tenant_id, ImportJob.status == "pending"
            )
        )
    )
    accepted = failed = 0
    for job_id in ids:
        try:
            result = accept_import_job(session, tenant_id, job_id)
        except core.RealityError:
            failed += 1
        else:
            accepted += int(result is not None)
    return accepted, failed


def accept_fixed_setup(session, tenant_id, tool):
    """Confirm the retained closed setup definition with a real company owner."""
    from reality.db.core import ChangeProposal
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    proposal = session.scalar(
        select(ChangeProposal)
        .where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == f"tool:{tool}",
            ChangeProposal.status == "executed",
        )
        .order_by(ChangeProposal.created_at)
        .limit(1)
    )
    if proposal is None:
        proposal = create_change_proposal(session, tenant_id, tool, {})
    return approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        confirmed=True,
        confirming_principal=explicit_owner(session, tenant_id),
    )


def accept_demo_setup(session, tenant):
    return accept_fixed_setup(session, tenant.id, "demo_seed")


def accept_normal_month(session, tenant_id):
    from decimal import Decimal

    proposal = accept_fixed_setup(session, tenant_id, "normal_month")
    output = json.loads(proposal.output)
    return {
        key: Decimal(value) if key in {"physical", "reserved", "receivable"} else value
        for key, value in output.items()
    }


def _accept_financial_fixture(session, tenant_id, source, stated, profile):
    """Retain fully stated fixture evidence, then ask its real owner for an exact decision."""
    from reality.services.intake import prepare_intake

    commit = not session.in_nested_transaction()
    if (
        "party_id" in json.loads(source.payload)
        or json.loads(source.payload).get("schema_version") == 1
    ):
        job = session.scalar(
            select(ImportJob).where(
                ImportJob.tenant_id == tenant_id,
                ImportJob.source_record_id == source.id,
            )
        )
    else:
        body = stated.model_dump(mode="json")
        source, job = core.enqueue_source(
            session,
            tenant_id,
            source.source_system,
            source.source_type,
            source.external_id,
            body,
            context={"profile": profile},
            _commit=commit,
        )
    proposal = prepare_intake(session, tenant_id, job.id, _commit=commit)
    digest = review_intake(session, tenant_id, proposal.id)["digest"]
    proposal = apply_prepared_intake(
        session,
        tenant_id,
        proposal.id,
        digest,
        confirmed=True,
        principal=explicit_owner(session, tenant_id),
        _commit=commit,
    )
    assert proposal.status == "executed"
    records = json.loads(proposal.output)["records"]
    document = next(
        core._tenant_record_read(session, Document, tenant_id, row["id"])
        for row in records
        if row["type"] == "document"
    )
    return source, document, records


def accept_normalized_invoice(session, tenant_id, source, invoice):
    from reality.db.core import LedgerEntry

    source, document, records = _accept_financial_fixture(
        session, tenant_id, source, invoice, "sales_invoice.v1"
    )
    lines = [
        core._tenant_record_read(session, DocumentLine, tenant_id, row["id"])
        for row in records
        if row["type"] == "document_line"
    ]
    entries = [
        core._tenant_record_read(session, LedgerEntry, tenant_id, row["id"])
        for row in records
        if row["type"] == "ledger_entry"
    ]
    return source, document, lines, entries


def accept_normalized_payment(session, tenant_id, source, payment):
    from reality.db.core import LedgerEntry, SettlementAllocation
    from reality.services.payment_intake import (
        Resolution,
        prepare_customer_payment,
        resolve_references,
    )

    resolution = resolve_references(
        session,
        tenant_id,
        payment.party_id,
        payment.currency,
        payment.references,
        source_system="demo_data"
        if source.source_system == "normalized_fixture"
        else source.source_system,
    )
    details = prepare_customer_payment(session, tenant_id, source, payment)
    resolution = Resolution(resolution.invoices, tuple(details["issues"]))
    source, document, records = _accept_financial_fixture(
        session, tenant_id, source, payment, "customer_payment.v1"
    )
    entries = [
        core._tenant_record_read(session, LedgerEntry, tenant_id, row["id"])
        for row in records
        if row["type"] == "ledger_entry"
    ]
    allocations = [
        core._tenant_record_read(session, SettlementAllocation, tenant_id, row["id"])
        for row in records
        if row["type"] == "settlement_allocation"
    ]
    return (
        source,
        document,
        entries,
        allocations[0] if allocations else None,
        resolution,
    )


def create_reviewed_master(session, tenant_id, family, record):
    """Fixture: confirm a real named Owner proposal rather than bypassing admission."""
    from reality.db.core import Item, Location, Party
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    principal = explicit_owner(session, tenant_id)
    proposal = create_change_proposal(
        session, tenant_id, f"{family}_create", {"records": [record]}
    )
    decided = approve_and_execute_proposal(
        session, tenant_id, proposal.id, confirming_principal=principal, confirmed=True
    )
    identity = json.loads(decided.output)["records"][0]["id"]
    return core._tenant_record_read(
        session,
        {"party": Party, "item": Item, "location": Location}[family],
        tenant_id,
        identity,
    )


def reviewed_create_party(session, tenant_id, name, party_type, **arguments):
    """Fixture: retain and confirm the stated partner through the public catalog."""
    record = {"name": name, "type": party_type, **arguments}
    record["roles"] = record.get("roles") or [party_type]
    record.pop("_commit", None)
    return create_reviewed_master(session, tenant_id, "party", record)


def reviewed_create_item(session, tenant_id, sku, name, unit="pcs", **arguments):
    """Fixture: retain and confirm the stated item through the public catalog."""
    record = {"sku": sku, "name": name, "unit": unit, **arguments}
    record.pop("_commit", None)
    return create_reviewed_master(session, tenant_id, "item", record)


def reviewed_create_location(
    session, tenant_id, name, location_type="warehouse", **arguments
):
    """Fixture: retain and confirm the stated location through the public catalog."""
    record = {"name": name, "type": location_type, **arguments}
    record.pop("_commit", None)
    return create_reviewed_master(session, tenant_id, "location", record)


def reviewed_update_party(session, tenant_id, party_id, name, party_type, **arguments):
    """Fixture: confirm the exact partner update through the public catalog."""
    return _reviewed_master_update(
        session,
        tenant_id,
        "party",
        {
            "id": party_id,
            "name": name,
            "type": party_type,
            "roles": arguments.pop("roles", None) or [party_type],
            **arguments,
        },
    )


def reviewed_update_item(session, tenant_id, item_id, sku, name, unit, **arguments):
    """Fixture: confirm the exact item update through the public catalog."""
    return _reviewed_master_update(
        session,
        tenant_id,
        "item",
        {"id": item_id, "sku": sku, "name": name, "unit": unit, **arguments},
    )


def reviewed_update_location(
    session, tenant_id, location_id, name, location_type, **arguments
):
    """Fixture: confirm the exact location update through the public catalog."""
    return _reviewed_master_update(
        session,
        tenant_id,
        "location",
        {"id": location_id, "name": name, "type": location_type, **arguments},
    )


def _reviewed_master_update(session, tenant_id, family, record):
    from reality.db.core import Item, Location, Party
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    record.pop("_commit", None)
    proposal = create_change_proposal(
        session, tenant_id, f"{family}_update", {"records": [record]}
    )
    decision = approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        confirming_principal=explicit_owner(session, tenant_id),
        confirmed=True,
    )
    identity = json.loads(decision.output)["records"][0]["id"]
    return core._tenant_record_read(
        session,
        {"party": Party, "item": Item, "location": Location}[family],
        tenant_id,
        identity,
    )


def _reviewed_master_batch(session, tenant_id, family, mode, records):
    """Fixture: explicitly confirm one real catalog decision for the complete batch."""
    from reality.db.core import Item, Location, Party
    from reality.tools.application import (
        _json_value,
        approve_and_execute_proposal,
        create_change_proposal,
    )

    proposal = create_change_proposal(
        session, tenant_id, f"{family}_{mode}", {"records": _json_value(records)}
    )
    receipt = approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        confirming_principal=explicit_owner(session, tenant_id),
        confirmed=True,
    )
    model = {"party": Party, "item": Item, "location": Location}[family]
    return [
        core._tenant_record_read(session, model, tenant_id, row["id"])
        for row in json.loads(receipt.output)["records"]
    ]


def reviewed_create_parties(session, tenant_id, records):
    return _reviewed_master_batch(session, tenant_id, "party", "create", records)


def reviewed_create_items(session, tenant_id, records):
    return _reviewed_master_batch(session, tenant_id, "item", "create", records)


def reviewed_create_locations(session, tenant_id, records):
    return _reviewed_master_batch(session, tenant_id, "location", "create", records)


def reviewed_update_parties(session, tenant_id, records):
    return _reviewed_master_batch(session, tenant_id, "party", "update", records)


def reviewed_update_items(session, tenant_id, records):
    return _reviewed_master_batch(session, tenant_id, "item", "update", records)


def reviewed_update_locations(session, tenant_id, records):
    return _reviewed_master_batch(session, tenant_id, "location", "update", records)


def reviewed_finance_account(session, tenant_id, command, values):
    """Fixture: confirm one retained account command with its real named Owner."""
    from reality.services.finance.accounts import list_accounts
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    principal = explicit_owner(session, tenant_id)
    values = dict(values)
    values.pop("_commit", None)
    values.pop("action_id", None)
    if values.get("expected_revision") is None:
        values["expected_revision"] = list_accounts(session, tenant_id)["revision"]
    proposal = create_change_proposal(session, tenant_id, command, values)
    settled = approve_and_execute_proposal(
        session, tenant_id, proposal.id, confirming_principal=principal, confirmed=True
    )
    return json.loads(settled.output)


def reviewed_create_account(session, tenant_id, **values):
    return reviewed_finance_account(
        session, tenant_id, "finance.account.create", values
    )


def reviewed_update_account(session, tenant_id, account_id, **values):
    return reviewed_finance_account(
        session,
        tenant_id,
        "finance.account.update",
        {"account_id": account_id, **values},
    )


def reviewed_set_default_account(session, tenant_id, **values):
    return reviewed_finance_account(
        session, tenant_id, "finance.account.set_default", values
    )


def reviewed_initialize_accounts(session, tenant_id, **values):
    return reviewed_finance_account(
        session, tenant_id, "finance.account.initialize", values
    )


def _document_fixture_json(value):
    from datetime import date, datetime
    from decimal import Decimal
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _document_fixture_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_document_fixture_json(item) for item in value]
    return value


def _confirm_document_fixture(session, tenant_id, tool, arguments):
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )
    principal = explicit_owner(session, tenant_id)
    values = dict(arguments)
    values.pop("_commit", None)
    values.pop("action_id", None)
    proposal = create_change_proposal(session, tenant_id, tool, _document_fixture_json(values))
    from reality.services.delivery_actions import REVIEW_KEY
    review = json.loads(proposal.input).get(REVIEW_KEY)
    receipt = approve_and_execute_proposal(session, tenant_id, proposal.id, confirming_principal=principal, confirmed=True, review_token=review["token"] if review else None)
    return json.loads(receipt.output)


def reviewed_manual_document_with_lines(session, tenant_id, document_type, number, party_id, lines, gross_amount, **arguments):
    from reality.db.core import Document, DocumentLine
    result = _confirm_document_fixture(session, tenant_id, "document_create", {
        "document_type": document_type, "number": number, "party_id": party_id,
        "lines": lines, "gross_amount": gross_amount, **arguments,
    })
    return (core._tenant_record_read(session, Document, tenant_id, result["document_id"]),
            [core._tenant_record_read(session, DocumentLine, tenant_id, identity) for identity in result["document_line_ids"]])


def reviewed_manual_order(session, tenant_id, direction, number, company_party_id, counterparty_id, location_id, lines, gross_amount, **arguments):
    from reality.db.core import Commitment, Document, DocumentLine, SourceRecord
    result = _confirm_document_fixture(session, tenant_id, "order_create", {
        "direction": direction, "number": number, "company_party_id": company_party_id,
        "counterparty_id": counterparty_id, "location_id": location_id, "lines": lines,
        "gross_amount": gross_amount, **arguments,
    })
    return (core._tenant_record_read(session, SourceRecord, tenant_id, result["source_record_id"]),
            core._tenant_record_read(session, Document, tenant_id, result["document_id"]),
            [core._tenant_record_read(session, DocumentLine, tenant_id, identity) for identity in result["document_line_ids"]],
            [core._tenant_record_read(session, Commitment, tenant_id, identity) for identity in result["commitment_ids"]])


def _reviewed_invoice_fixture(session, tenant_id, tool, positional, arguments):
    names = ("order_line_id", "quantity", "gross_amount", "number")
    if len(positional) > len(names):
        raise TypeError("Too many invoice fixture arguments")
    values = {**dict(zip(names, positional)), **arguments}
    return _confirm_document_fixture(session, tenant_id, tool, values)


def reviewed_record_sales_invoice(session, tenant_id, *positional, **arguments):
    return _reviewed_invoice_fixture(session, tenant_id, "sales_invoice_record", positional, arguments)


def reviewed_record_supplier_invoice(session, tenant_id, *positional, **arguments):
    return _reviewed_invoice_fixture(session, tenant_id, "supplier_invoice_record", positional, arguments)


def reviewed_record_sales_credit(session, tenant_id, *positional, **arguments):
    return _reviewed_invoice_fixture(session, tenant_id, "sales_credit_record", positional, arguments)


def reviewed_record_free_supplier_invoice(session, tenant_id, **arguments):
    return _confirm_document_fixture(session, tenant_id, "supplier_invoice_free_record", arguments)
def reviewed_commercial_master(session, tenant_id, operation, *positional, **arguments):
    """Create current fixture data through an actual retained human decision."""
    import inspect

    from reality.db import core as records
    from reality.services.tenant_policy import COMMERCIAL_MASTER_OPERATIONS
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    core._tenant_record_read(session, records.Tenant, tenant_id, tenant_id)
    from reality.services.tenant_policy import _profile_authority

    if _profile_authority.get() is not None:
        from reality.services.intake import _invoke

        bound = inspect.signature(getattr(core, operation)).bind(session, tenant_id, *positional, **arguments)
        values = {key: value for key, value in bound.arguments.items() if key not in {"session", "tenant_id"}}
        return _invoke(operation, getattr(core, operation), session, tenant_id, **values)
    bound = inspect.signature(getattr(core, operation)).bind(session, tenant_id, *positional, **arguments)
    values = {key: value for key, value in bound.arguments.items() if key not in {"session", "tenant_id", "_commit"}}
    tool = next(tool for tool, canonical in COMMERCIAL_MASTER_OPERATIONS.items() if canonical == operation)
    owner = explicit_owner(session, tenant_id)
    proposal = create_change_proposal(session, tenant_id, tool, _document_fixture_json(values), actor_type="human")
    receipt = approve_and_execute_proposal(session, tenant_id, proposal.id, confirming_principal=owner, confirmed=True)
    record = json.loads(receipt.output)["records"][0]
    models = {"payment_term": records.PaymentTerm, "price_list": records.PriceList, "price_list_entry": records.PriceListEntry, "party_price_list": records.PartyPriceList, "party_group": records.PartyGroup, "party_group_member": records.PartyGroupMember, "party_group_price_list": records.PartyGroupPriceList}
    return core._tenant_record_read(session, models[record["family"]], tenant_id, record["id"])


def reviewed_create_payment_term(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "create_payment_term", *args, **kwargs)


def reviewed_update_payment_term(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "update_payment_term", *args, **kwargs)


def reviewed_create_price_list(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "create_price_list", *args, **kwargs)


def reviewed_update_price_list(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "update_price_list", *args, **kwargs)


def reviewed_create_price_list_entry(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "create_price_list_entry", *args, **kwargs)


def reviewed_assign_party_price_list(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "assign_party_price_list", *args, **kwargs)


def reviewed_create_party_group(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "create_party_group", *args, **kwargs)


def reviewed_update_party_group(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "update_party_group", *args, **kwargs)


def reviewed_add_party_group_member(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "add_party_group_member", *args, **kwargs)


def reviewed_assign_group_price_list(session, tenant_id, *args, **kwargs):
    return reviewed_commercial_master(session, tenant_id, "assign_group_price_list", *args, **kwargs)


def reviewed_set_master_data_active(session, tenant_id, model, record_id, is_active, **arguments):
    """Current fixture lifecycle statement through an actual retained decision."""
    from reality.services.core import _tenant_record_read
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    if arguments:
        raise ValueError("Fixture lifecycle accepts only actual public stated input.")
    owner = explicit_owner(session, tenant_id)
    proposal = create_change_proposal(session, tenant_id, "master_data_lifecycle", {"model": model.__tablename__, "record_id": record_id, "is_active": is_active}, actor_type="human")
    approve_and_execute_proposal(session, tenant_id, proposal.id, confirming_principal=owner, confirmed=True)
    return _tenant_record_read(session, model, tenant_id, record_id)


def reviewed_merge_party(session, tenant_id, duplicate_party_id, surviving_party_id, reason):
    """A current merge fixture settles its actual retained reviewed meaning."""
    from reality.db.core import PartyMerge
    from reality.services.core import _tenant_record_read
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    owner = explicit_owner(session, tenant_id)
    proposal = create_change_proposal(session, tenant_id, "party_merge", {"duplicate_party_id": duplicate_party_id, "surviving_party_id": surviving_party_id, "reason": reason}, actor_type="human")
    receipt = approve_and_execute_proposal(session, tenant_id, proposal.id, confirming_principal=owner, confirmed=True)
    return _tenant_record_read(session, PartyMerge, tenant_id, json.loads(receipt.output)["merge_id"])


def _reviewed_document_correction(session, tenant_id, document_id, operation, arguments):
    """Settle a current fixture statement through its real retained decision."""
    from reality.db.core import Document
    from reality.services.core import _tenant_record_read
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    if any(key.startswith("_") for key in arguments):
        raise ValueError("Fixture correction accepts only public stated input.")
    owner = explicit_owner(session, tenant_id)
    proposal = create_change_proposal(session, tenant_id, operation, {"document_id": document_id, **arguments}, actor_type="human")
    receipt = approve_and_execute_proposal(session, tenant_id, proposal.id, confirming_principal=owner, confirmed=True)
    if operation == "document_lines_correct":
        return json.loads(receipt.output)
    return _tenant_record_read(session, Document, tenant_id, document_id)


def reviewed_correct_manual_document(session, tenant_id, document_id, **arguments):
    return _reviewed_document_correction(session, tenant_id, document_id, "document_correct", arguments)


def reviewed_correct_manual_document_lines(session, tenant_id, document_id, **arguments):
    return _reviewed_document_correction(session, tenant_id, document_id, "document_lines_correct", arguments)



def _reviewed_payment_fixture(session, tenant_id, operation, *positional, **arguments):
    """Create current settlement fixture data through its actual retained decision."""
    import inspect

    from reality.db.core import LedgerEntry
    from reality.services.intake import _invoke
    from reality.services.tenant_policy import (
        PAYMENT_APPLICATION_OPERATIONS,
        _profile_authority,
    )

    bound = inspect.signature(getattr(core, operation)).bind(session, tenant_id, *positional, **arguments)
    values = {key: value for key, value in bound.arguments.items() if key not in {"session", "tenant_id"}}
    if _profile_authority.get() is not None:
        return _invoke(operation, getattr(core, operation), session, tenant_id, **values)
    tool = next(tool for tool, canonical in PAYMENT_APPLICATION_OPERATIONS.items() if canonical == operation)
    result = _confirm_document_fixture(session, tenant_id, tool, values)
    if tool == "payment_run":
        result["total"] = core.decimal(result["total"])
        for payment in result["payments"]:
            payment["amount"] = core.decimal(payment["amount"])
        return result
    return [core._tenant_record_read(session, LedgerEntry, tenant_id, row["id"]) for row in result["records"] if row["family"] == "ledger_entry"]


def reviewed_post_customer_payment(session, tenant_id, *args, **kwargs):
    return _reviewed_payment_fixture(session, tenant_id, "post_customer_payment", *args, **kwargs)


def reviewed_post_supplier_payment(session, tenant_id, *args, **kwargs):
    return _reviewed_payment_fixture(session, tenant_id, "post_supplier_payment", *args, **kwargs)


def reviewed_post_customer_refund(session, tenant_id, *args, **kwargs):
    return _reviewed_payment_fixture(session, tenant_id, "post_customer_refund", *args, **kwargs)


def reviewed_execute_payment_run(session, tenant_id, *args, **kwargs):
    return _reviewed_payment_fixture(session, tenant_id, "execute_payment_run", *args, **kwargs)



def _reviewed_financial_posting_fixture(session, tenant_id, operation, *positional, **arguments):
    """Create current posting fixture data through its actual retained decision."""
    import inspect

    from reality.db.core import LedgerEntry, SettlementAllocation
    from reality.services.intake import _invoke
    from reality.services.tenant_policy import (
        FINANCIAL_POSTING_OPERATIONS,
        _profile_authority,
    )

    bound = inspect.signature(getattr(core, operation)).bind(session, tenant_id, *positional, **arguments)
    values = {key: value for key, value in bound.arguments.items() if key not in {"session", "tenant_id"}}
    if _profile_authority.get() is not None:
        return _invoke(operation, getattr(core, operation), session, tenant_id, **values)
    tool = next(tool for tool, canonical in FINANCIAL_POSTING_OPERATIONS.items() if canonical == operation)
    result = _confirm_document_fixture(session, tenant_id, tool, values)
    if tool.endswith("allocate"):
        return core._tenant_record_read(session, SettlementAllocation, tenant_id, result["records"][0]["id"])
    return [core._tenant_record_read(session, LedgerEntry, tenant_id, row["id"]) for row in result["records"] if row["family"] == "ledger_entry"]


def reviewed_post_sales_invoice(session, tenant_id, *args, **kwargs):
    return _reviewed_financial_posting_fixture(session, tenant_id, "post_sales_invoice", *args, **kwargs)


def reviewed_post_supplier_invoice(session, tenant_id, *args, **kwargs):
    return _reviewed_financial_posting_fixture(session, tenant_id, "post_supplier_invoice", *args, **kwargs)


def reviewed_post_sales_credit_note(session, tenant_id, *args, **kwargs):
    return _reviewed_financial_posting_fixture(session, tenant_id, "post_sales_credit_note", *args, **kwargs)


def reviewed_post_supplier_credit_note(session, tenant_id, *args, **kwargs):
    return _reviewed_financial_posting_fixture(session, tenant_id, "post_supplier_credit_note", *args, **kwargs)


def reviewed_allocate_credit_note(session, tenant_id, *args, **kwargs):
    return _reviewed_financial_posting_fixture(session, tenant_id, "allocate_credit_note", *args, **kwargs)


def reviewed_allocate_supplier_credit_note(session, tenant_id, *args, **kwargs):
    return _reviewed_financial_posting_fixture(session, tenant_id, "allocate_supplier_credit_note", *args, **kwargs)


def reviewed_post_supplier_refund(session, tenant_id, *args, **kwargs):
    return _reviewed_financial_posting_fixture(session, tenant_id, "post_supplier_refund", *args, **kwargs)


def _reviewed_reservation_fixture(session, tenant_id, operation, *positional, **arguments):
    """Create current reservation fixtures through actual retained confirmation."""
    import inspect

    from reality.db.core import BusinessEvent, Reservation
    from reality.services.intake import _invoke
    from reality.services.tenant_policy import (
        _application_authority,
        _decision_authority,
        _profile_authority,
    )

    bound = inspect.signature(getattr(core, operation)).bind(session, tenant_id, *positional, **arguments)
    values = {key: value for key, value in bound.arguments.items() if key not in {"session", "tenant_id"}}
    authority = _application_authority.get()
    if _profile_authority.get() is not None or _decision_authority.get() is not None or authority is not None:
        return _invoke(operation, getattr(core, operation), session, tenant_id, **values)
    tool = "reserve" if operation == "reserve" else "reservation_release"
    result = _confirm_document_fixture(session, tenant_id, tool, values)
    if operation == "release_reservation":
        return core._tenant_record_read(session, Reservation, tenant_id, result["records"][0]["id"])
    reservation = core._tenant_record_read(session, Reservation, tenant_id, result["reservation_id"]) if result["reservation_id"] else None
    event = core._tenant_record_read(session, BusinessEvent, tenant_id, result["event_id"]) if result["event_id"] else None
    return core.ReservationResult(reservation, core.decimal(result["requested"]), core.decimal(result["reserved"]), core.decimal(result["shortage"]), event)


def reviewed_reserve(session, tenant_id, *args, **kwargs):
    return _reviewed_reservation_fixture(session, tenant_id, "reserve", *args, **kwargs)


def reviewed_release_reservation(session, tenant_id, *args, **kwargs):
    return _reviewed_reservation_fixture(session, tenant_id, "release_reservation", *args, **kwargs)


def reviewed_serve_backorders(session, tenant_id, *positional, **arguments):
    """Confirm the complete original backorder fixture as one actual decision."""
    import inspect

    from reality.services.backorders import serve_backorders

    bound = inspect.signature(serve_backorders).bind(session, tenant_id, *positional, **arguments)
    values = {key: value for key, value in bound.arguments.items() if key not in {"session", "tenant_id"}}
    return _confirm_document_fixture(session, tenant_id, "backorders_serve", values)


def _reviewed_commitment_fixture(session, tenant_id, operation, *positional, **arguments):
    """Use the actual retained decision for current commitment fixture statements."""
    import inspect

    from reality.services.intake import _invoke
    from reality.services.tenant_policy import (
        _application_authority,
        _decision_authority,
        _profile_authority,
    )

    bound = inspect.signature(getattr(core, operation)).bind(session, tenant_id, *positional, **arguments)
    values = {key: value for key, value in bound.arguments.items() if key not in {"session", "tenant_id"}}
    if _application_authority.get() is not None or _decision_authority.get() is not None or _profile_authority.get() is not None:
        return _invoke(operation, getattr(core, operation), session, tenant_id, **values)
    tool = {"revise_commitment": "commitment_revise", "cancel_commitment": "commitment_cancel", "close_stale_promises": "stale_closure"}[operation]
    session.flush()
    session.expire_all()
    result = _confirm_document_fixture(session, tenant_id, tool, values)
    if operation == "close_stale_promises":
        return result
    model = core.CommitmentRevision if operation == "revise_commitment" else core.Commitment
    identity = result["records"][0]["id"] if operation == "revise_commitment" else result["commitment_id"]
    return core._tenant_record_read(session, model, tenant_id, identity)


def reviewed_revise_commitment(session, tenant_id, *args, **kwargs):
    return _reviewed_commitment_fixture(session, tenant_id, "revise_commitment", *args, **kwargs)


def reviewed_cancel_commitment(session, tenant_id, *args, **kwargs):
    return _reviewed_commitment_fixture(session, tenant_id, "cancel_commitment", *args, **kwargs)


def reviewed_close_stale_promises(session, tenant_id, *args, **kwargs):
    return _reviewed_commitment_fixture(session, tenant_id, "close_stale_promises", *args, **kwargs)
