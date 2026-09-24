"""Record provenance, source addressing and connector association (spec 211)."""

from __future__ import annotations

import json

import pytest

from reality.services.core import connector_shells, install_connector_shell


def shells_containing(session, tenant_id: str, instance_code: str) -> list[str]:
    return [
        shell["code"]
        for shell in connector_shells(session, tenant_id)
        if any(instance.code == instance_code for instance in shell["instances"])
    ]


def test_an_instance_belongs_to_exactly_one_connector_shell(session, business):
    """A prefix-sharing catalog name must not claim another connector's instance.

    `Shopify` and `Shopify Payments` share a prefix, so an instance installed
    from `shopify_payments` satisfies a description-prefix test for both.
    """
    install_connector_shell(
        session,
        business.tenant.id,
        "shopify_payments",
        ["transaction"],
        "shopify_payments_de",
        "Shopify Payments DE",
    )
    assert shells_containing(session, business.tenant.id, "shopify_payments_de") == [
        "shopify_payments"
    ]


def test_each_installed_instance_is_listed_once_across_the_catalog(session, business):
    for connector_code, source_type, instance_code in (
        ("shopify", "order", "shopify_de"),
        ("shopify_payments", "payout", "shopify_payments_de"),
        ("hubspot", "contact", "hubspot_main"),
    ):
        install_connector_shell(
            session,
            business.tenant.id,
            connector_code,
            [source_type],
            instance_code,
            instance_code.replace("_", " ").title(),
        )
    listings = [
        (shell["code"], instance.code)
        for shell in connector_shells(session, business.tenant.id)
        for instance in shell["instances"]
    ]
    assert sorted(listings) == [
        ("hubspot", "hubspot_main"),
        ("shopify", "shopify_de"),
        ("shopify_payments", "shopify_payments_de"),
    ]


def test_a_hand_created_system_is_listed_under_no_connector(session, business):
    from reality.services.core import create_source_system

    create_source_system(
        session, business.tenant.id, "legacy_ftp", "Legacy FTP drop", "Nightly export"
    )
    assert shells_containing(session, business.tenant.id, "legacy_ftp") == []


def test_unknown_upstream_document_label_remains_lossless_source_evidence(
    session, business
):
    from reality.db.core import Document
    from reality.services.core import enqueue_source

    payload = {"type": "delivery_note_probe", "vendor_field": {"raw": "kept"}}
    source, job = enqueue_source(
        session,
        business.tenant.id,
        "external_audit",
        "delivery_note_probe",
        "probe-257",
        payload,
    )

    assert job.status == "unmapped"
    assert source.source_type == "delivery_note_probe"
    assert json.loads(source.payload) == payload
    assert session.query(Document).filter_by(source_record_id=source.id).count() == 0


# --- T004: origin resolution -------------------------------------------------


def imported_party(session, tenant_id, *, system="shopify_de", external_id="cust-1"):
    from reality.services.core import create_party

    return create_party(
        session,
        tenant_id,
        "Imported Customer",
        "customer",
        source_system=system,
        external_id=external_id,
    )


def test_origin_states_the_source_identity_of_an_imported_record(session, business):
    from reality.services.provenance import record_origins

    party = imported_party(session, business.tenant.id)
    install_connector_shell(
        session,
        business.tenant.id,
        "shopify",
        ["customer"],
        "shopify_de",
        "Shopify Germany",
    )
    origin = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert origin["kind"] == "source"
    assert origin["system_code"] == "shopify_de"
    assert origin["system_name"] == "Shopify Germany"
    assert origin["source_type"] == "party"
    assert origin["external_id"] == "cust-1"
    assert origin["source_version"] == 1
    assert origin["received_at"] is not None
    assert origin["source_record_id"] == party.source_record_id


def test_origin_falls_back_to_the_retained_code_without_a_configured_system(
    session, business
):
    from reality.services.provenance import record_origins

    party = imported_party(session, business.tenant.id, system="retired_shop")
    origin = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert origin["kind"] == "source"
    assert origin["system_code"] == "retired_shop"
    assert origin["system_name"] == "retired_shop"
    assert origin.get("url") is None


def test_origin_of_a_manually_created_record_names_the_deciding_user(
    session, business, scheduled_owner
):
    from reality.db.core import ChangeProposal, now, uid
    from reality.services.core import create_party
    from reality.services.provenance import record_origins

    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="create_party",
        status="executed",
        decided_at=now(),
        decided_by_user_id=scheduled_owner.id,
    )
    session.add(proposal)
    session.flush()
    party = create_party(
        session,
        business.tenant.id,
        "Walk-in Customer",
        "customer",
        action_id=proposal.id,
    )
    assert party.source_record_id is None
    origin = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert origin["kind"] == "application"
    assert origin["actor"] == scheduled_owner.email
    assert "system_code" not in origin


def test_origin_of_a_manual_record_without_a_decision_states_no_actor(
    session, business
):
    from reality.services.core import create_party
    from reality.services.provenance import record_origins

    party = create_party(session, business.tenant.id, "Hand entered", "customer")
    origin = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert origin == {"kind": "application"}


def test_origin_never_crosses_a_tenant_boundary(session, business):
    from reality.services.core import create_tenant
    from reality.services.provenance import record_origins

    party = imported_party(session, business.tenant.id)
    other = create_tenant(session, "Unrelated company")
    origins = record_origins(session, other.id, [party], subject_type="party")
    assert origins[party.id] == {"kind": "application"}


def test_origin_resolution_is_bounded_per_page_not_per_row(session, business):
    from sqlalchemy import event

    from reality.services.provenance import record_origins

    statements: list[str] = []

    def collect(conn, cursor, statement, parameters, context, many):
        # Savepoints belong to the surrounding test transaction, not to the read.
        if (
            not statement.lstrip()
            .upper()
            .startswith(("SAVEPOINT", "RELEASE", "ROLLBACK", "BEGIN", "COMMIT"))
        ):
            statements.append(statement)

    def measured(records):
        statements.clear()
        event.listen(session.get_bind(), "before_cursor_execute", collect)
        try:
            record_origins(session, business.tenant.id, records, subject_type="party")
        finally:
            event.remove(session.get_bind(), "before_cursor_execute", collect)
        return len(statements)

    few = [
        imported_party(session, business.tenant.id, external_id=f"cust-{index}")
        for index in range(2)
    ]
    many = few + [
        imported_party(session, business.tenant.id, external_id=f"cust-{index}")
        for index in range(2, 40)
    ]
    for_two = measured(few)
    for_forty = measured(many)
    assert for_two == for_forty
    assert for_forty <= 6


# --- T008: source addressing -------------------------------------------------


def vendor_sourced_party(session, tenant_id, source_type, external_id):
    """A record whose source record carries the vendor's own source type.

    Master data created with a source annotation records the target family as its
    source type (`party`), which is not a vendor type and therefore addresses
    nothing. A record that arrived through ingestion keeps the vendor's type.
    """
    from reality.services.core import create_party, enqueue_source

    source, _ = enqueue_source(
        session, tenant_id, "shopify_de", source_type, external_id, {"id": external_id}
    )
    return create_party(
        session,
        tenant_id,
        f"From {source_type}",
        "customer",
        source_record_id=source.id,
    )


def shopify_system(session, tenant_id, base_url="https://acme-de.myshopify.com/admin"):
    system = install_connector_shell(
        session, tenant_id, "shopify", ["order", "customer"], "shopify_de", "Shopify DE"
    )
    if base_url:
        from reality.services.core import set_source_system_base_url

        set_source_system_base_url(session, tenant_id, system.id, base_url)
    return system


def test_a_configured_address_links_a_record_to_its_owning_system(session, business):
    from reality.services.provenance import record_origins

    shopify_system(session, business.tenant.id)
    party = vendor_sourced_party(session, business.tenant.id, "customer", "7712/33")
    origin = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert origin["url"] == "https://acme-de.myshopify.com/admin/customers/7712%2F33"


def test_a_trailing_separator_resolves_identically(session, business):
    from reality.services.core import set_source_system_base_url
    from reality.services.provenance import record_origins

    system = shopify_system(session, business.tenant.id)
    party = vendor_sourced_party(session, business.tenant.id, "customer", "99")
    first = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]["url"]
    set_source_system_base_url(
        session, business.tenant.id, system.id, "https://acme-de.myshopify.com/admin/"
    )
    second = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]["url"]
    assert first == second


def test_an_unconfigured_address_still_states_origin_without_a_link(session, business):
    from reality.services.provenance import record_origins

    shopify_system(session, business.tenant.id, base_url="")
    party = imported_party(session, business.tenant.id)
    origin = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert origin["system_name"] == "Shopify DE"
    assert origin["url"] is None


def test_a_source_type_without_a_template_offers_no_link(session, business):
    """Paired with a positive control, so this cannot pass for the wrong reason."""
    from reality.services.provenance import record_origins

    shopify_system(session, business.tenant.id)
    addressed = vendor_sourced_party(session, business.tenant.id, "customer", "c-1")
    # Shopify declares `fulfillment` as a capability but no address for it.
    undeclared = vendor_sourced_party(session, business.tenant.id, "fulfillment", "f-1")
    origins = record_origins(
        session, business.tenant.id, [addressed, undeclared], subject_type="party"
    )
    assert origins[addressed.id]["url"] is not None
    assert origins[undeclared.id]["system_name"] == "Shopify DE"
    assert origins[undeclared.id]["url"] is None


def test_master_data_annotated_with_a_source_records_the_target_family(
    session, business
):
    """A source annotation is not an ingestion, and must not be addressed as one.

    `create_party` stores `party` as the source type, which is the target family
    rather than anything the vendor would answer to, so no template applies.
    """
    from reality.services.provenance import record_origins

    shopify_system(session, business.tenant.id)
    party = imported_party(session, business.tenant.id)
    origin = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert origin["source_type"] == "party"
    assert origin["system_name"] == "Shopify DE"
    assert origin["url"] is None


@pytest.mark.parametrize(
    "rejected",
    [
        "http://acme.example/admin",
        "ftp://acme.example/admin",
        "javascript:alert(1)",
        "https://user:secret@acme.example/admin",
        "/admin",
        "https://acme.example/admin?token=abc",
        "https://" + "a" * 600,
    ],
)
def test_a_base_address_that_is_not_a_plain_https_location_is_rejected(
    session, business, rejected
):
    from reality.services.core import InvalidOperation, set_source_system_base_url

    system = install_connector_shell(
        session, business.tenant.id, "shopify", ["order"], "shopify_de", "Shopify"
    )
    with pytest.raises(InvalidOperation):
        set_source_system_base_url(session, business.tenant.id, system.id, rejected)


def test_a_base_address_can_be_cleared(session, business):
    from reality.services.core import set_source_system_base_url

    system = shopify_system(session, business.tenant.id)
    assert system.base_url
    cleared = set_source_system_base_url(session, business.tenant.id, system.id, "  ")
    assert cleared.base_url is None


def test_a_base_address_is_not_configurable_across_tenants(session, business):
    from reality.services.core import (
        NotFound,
        create_tenant,
        set_source_system_base_url,
    )

    system = install_connector_shell(
        session, business.tenant.id, "shopify", ["order"], "shopify_de", "Shopify"
    )
    other = create_tenant(session, "Unrelated company")
    with pytest.raises(NotFound):
        set_source_system_base_url(
            session, other.id, system.id, "https://other.example/admin"
        )


def test_a_template_may_only_interpolate_the_external_reference():
    from reality.integrations.catalog import connector_catalog

    for connector in connector_catalog()["connectors"]:
        for source_type, template in (connector.get("deep_links") or {}).items():
            assert source_type in connector["capabilities"]
            assert template.count("{") == template.count("{external_id}")
            assert not template.startswith("/")


def test_a_hand_created_system_resolves_no_template(session, business):
    from reality.services.core import (
        create_party,
        create_source_system,
        set_source_system_base_url,
    )
    from reality.services.provenance import record_origins

    system = create_source_system(
        session, business.tenant.id, "legacy_ftp", "Legacy FTP", "Nightly export"
    )
    set_source_system_base_url(
        session, business.tenant.id, system.id, "https://legacy.example/records"
    )
    party = create_party(
        session,
        business.tenant.id,
        "From the old server",
        "customer",
        source_system="legacy_ftp",
        external_id="7",
    )
    origin = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert origin["system_name"] == "Legacy FTP"
    assert origin["url"] is None


def test_a_superseded_source_version_is_disclosed(session, business):
    from reality.services.core import enqueue_source
    from reality.services.provenance import record_origins

    first, _ = enqueue_source(
        session, business.tenant.id, "shopify_de", "order", "1001", {"total": "10.00"}
    )
    party = imported_party(session, business.tenant.id)
    party.source_record_id = first.id
    session.flush()
    origin = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert origin["superseded"] is False
    enqueue_source(
        session, business.tenant.id, "shopify_de", "order", "1001", {"total": "12.00"}
    )
    later = record_origins(session, business.tenant.id, [party], subject_type="party")[
        party.id
    ]
    assert later["superseded"] is True
    assert later["source_version"] == 1


# --- T006: the source record inspection --------------------------------------


def evidence(session, tenant_id, source_id):
    from reality.services.delivery_reads import delivery_evidence

    return delivery_evidence(session, tenant_id, "source_record", source_id)


def labels(section) -> list[str]:
    return [row["label"] for row in section["rows"]]


def section_named(data, title):
    return next(
        (section for section in data["sections"] if section["title"] == title), None
    )


def test_the_source_inspection_keeps_its_existing_identity_rows(session, business):
    from reality.services.core import enqueue_source

    source, _ = enqueue_source(
        session, business.tenant.id, "shopify_de", "order", "1001", {"total": "10.00"}
    )
    data = evidence(session, business.tenant.id, source.id)
    recorded = section_named(data, "Recorded values")
    assert {
        "Source system",
        "External reference",
        "Source type",
        "Version",
        "Received",
        "Import job",
    } <= set(labels(recorded))


def test_the_source_inspection_bounds_the_retained_payload(session, business):
    from reality.services.core import enqueue_source
    from reality.services.delivery_reads import MAX_SOURCE_PAYLOAD

    small, _ = enqueue_source(
        session, business.tenant.id, "shopify_de", "order", "small", {"a": "1"}
    )
    shown = evidence(session, business.tenant.id, small.id)
    assert shown["source_payload"] == small.payload
    assert shown["source_payload_truncated"] is False

    large, _ = enqueue_source(
        session,
        business.tenant.id,
        "shopify_de",
        "order",
        "large",
        {"note": "x" * (MAX_SOURCE_PAYLOAD + 500)},
    )
    bounded = evidence(session, business.tenant.id, large.id)
    assert len(bounded["source_payload"]) == MAX_SOURCE_PAYLOAD
    assert bounded["source_payload_truncated"] is True
    assert bounded["source_payload"] == large.payload[:MAX_SOURCE_PAYLOAD]


def test_the_source_inspection_states_a_terminal_interpretation_outcome(
    session, business
):
    from reality.db.core import InterpretationOutcome, uid
    from reality.services.core import enqueue_source

    source, job = enqueue_source(
        session, business.tenant.id, "shopify_de", "order", "2002", {"total": "1.00"}
    )
    session.add(
        InterpretationOutcome(
            id=uid("ico"),
            tenant_id=business.tenant.id,
            source_record_id=source.id,
            import_job_id=job.id,
            attempt=1,
            classification="interpreted",
            interpreter_name="shopify_order",
            interpreter_version="3",
            reason_code="",
            summary="One sales order recorded.",
        )
    )
    session.flush()
    rows = {
        row["label"]: row["value"]
        for row in section_named(
            evidence(session, business.tenant.id, source.id), "Recorded values"
        )["rows"]
    }
    assert rows["Interpretation"] == "interpreted"
    assert rows["Interpreter"] == "shopify_order 3"


def test_a_source_without_outcome_evidence_is_labeled_not_given_an_outcome(
    session, business
):
    """`not_recorded` is a label for missing evidence, never a fabricated result.

    An unregistered `(system, type)` pair is classified `unsupported` at attempt
    zero, which is real evidence; only a historical source that predates outcome
    recording has none at all.
    """
    from sqlalchemy import delete

    from reality.db.core import InterpretationOutcome
    from reality.services.core import enqueue_source

    def interpretation(source_id):
        return {
            row["label"]: row["value"]
            for row in section_named(
                evidence(session, business.tenant.id, source_id), "Recorded values"
            )["rows"]
        }["Interpretation"]

    classified, _ = enqueue_source(
        session, business.tenant.id, "shopify_de", "order", "3003", {"total": "1.00"}
    )
    assert interpretation(classified.id) == "unsupported"

    historical, _ = enqueue_source(
        session, business.tenant.id, "shopify_de", "order", "3004", {"total": "2.00"}
    )
    session.execute(
        delete(InterpretationOutcome).where(
            InterpretationOutcome.tenant_id == business.tenant.id,
            InterpretationOutcome.source_record_id == historical.id,
        )
    )
    session.flush()
    assert interpretation(historical.id) == "not_recorded"


def test_the_source_inspection_offers_the_configured_external_link(session, business):
    from reality.services.core import enqueue_source

    shopify_system(session, business.tenant.id)
    source, _ = enqueue_source(
        session, business.tenant.id, "shopify_de", "order", "4004", {"total": "1.00"}
    )
    rows = {
        row["label"]: row
        for row in section_named(
            evidence(session, business.tenant.id, source.id), "Recorded values"
        )["rows"]
    }
    assert (
        rows["Open in source system"]["value"]
        == "https://acme-de.myshopify.com/admin/orders/4004"
    )
    unlinked, _ = enqueue_source(
        session, business.tenant.id, "other_shop", "order", "5005", {"total": "1.00"}
    )
    other = {
        row["label"]
        for row in section_named(
            evidence(session, business.tenant.id, unlinked.id), "Recorded values"
        )["rows"]
    }
    assert "Open in source system" not in other


def test_an_unmapped_source_lists_no_operational_records(session, business):
    from reality.services.core import enqueue_source

    source, _ = enqueue_source(
        session, business.tenant.id, "unknown_shop", "mystery", "9", {"a": "1"}
    )
    data = evidence(session, business.tenant.id, source.id)
    titles = {section["title"] for section in data["sections"]}
    assert not titles & {
        "Linked parties",
        "Linked items",
        "Linked documents",
        "Linked movements",
        "Linked observations",
        "Linked ledger entries",
    }


# --- T014: more than one contributing source ---------------------------------


def sourced_document(session, business):
    from reality.services.core import create_document

    return create_document(
        session,
        business.tenant.id,
        "sales_order",
        "SO-9001",
        business.customer.id,
        "100.00",
    )


def observe_from(session, business, document, system, predicate, value, key):
    from reality.services.core import enqueue_source, observe_fact

    source, _ = enqueue_source(
        session, business.tenant.id, system, "order", key, {"ref": value}
    )
    observe_fact(
        session,
        business.tenant.id,
        source_record_id=source.id,
        subject_type="document",
        subject_id=document.id,
        predicate=predicate,
        value=value,
        observed_at="2026-09-16T10:00:00+00:00",
        idempotency_key=key,
    )
    return source


def test_a_single_contributing_system_is_not_announced_as_several(session, business):
    from reality.services.provenance import contributing_systems

    document = sourced_document(session, business)
    observe_from(
        session, business, document, "shopify_de", "order.customer_reference", "A", "k1"
    )
    assert (
        contributing_systems(session, business.tenant.id, "document", document.id) == []
    )


def test_several_contributing_systems_are_disclosed(session, business):
    from reality.services.provenance import contributing_systems

    document = sourced_document(session, business)
    observe_from(
        session, business, document, "shopify_de", "order.customer_reference", "A", "k1"
    )
    observe_from(
        session,
        business,
        document,
        "hubspot_main",
        "invoice.payment_promise_date",
        "2026-10-01",
        "k2",
    )
    assert contributing_systems(
        session, business.tenant.id, "document", document.id
    ) == [
        "hubspot_main",
        "shopify_de",
    ]


def test_contributing_systems_are_bounded_and_tenant_scoped(session, business):
    from reality.services.core import create_tenant
    from reality.services.provenance import contributing_systems

    document = sourced_document(session, business)
    observe_from(
        session, business, document, "shopify_de", "order.customer_reference", "A", "k1"
    )
    observe_from(
        session,
        business,
        document,
        "hubspot_main",
        "invoice.payment_promise_date",
        "2026-10-01",
        "k2",
    )
    assert (
        len(
            contributing_systems(
                session, business.tenant.id, "document", document.id, limit=1
            )
        )
        == 1
    )
    other = create_tenant(session, "Unrelated company")
    assert contributing_systems(session, other.id, "document", document.id) == []
