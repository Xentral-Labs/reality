import pathlib
from copy import deepcopy

import pytest

from reality import catalogs
from reality.catalogs import (
    load_operational_exception_catalog,
    validate_operational_exception_catalog,
)
from reality.services.exceptions import DERIVATION_REGISTRY


def payload():
    catalog = load_operational_exception_catalog()
    return {"version": catalog.version, "classes": deepcopy(list(catalog.classes))}


def test_production_operational_exception_catalog_has_closed_registry():
    catalog = load_operational_exception_catalog()

    assert [entry["id"] for entry in catalog.classes] == [
        "overdue_outgoing_customer_commitment",
        "outgoing_commitment_at_risk",
        "order_stalled",
        "overdue_incoming_supplier_commitment",
        "shipped_not_billed",
        "billed_not_received",
        "invoice_price_differs",
        "sold_below_purchase_price",
        "returned_not_credited",
        "credited_not_returned",
        "supplier_return_not_credited",
        "supplier_credit_not_returned",
        "return_unresolved",
        "receipt_unbilled",
        "units_not_comparable",
        "reservation_exceeds_stock",
        "silent_source",
        "source_interpretation_failure",
        "unexplained_movement",
        "sales_invoice_unposted",
        "supplier_invoice_unposted",
        "credit_note_unposted",
        "credit_note_unsettled",
        "supplier_credit_unposted",
        "supplier_credit_unclaimed",
        "overdue_receivable",
        "credit_limit_exceeded",
        "overdue_payable",
        "purchase_discount_available",
        "duplicate_supplier_invoice",
        "unmatched_financial_event",
        "announced_return_not_arrived",
        "commitment_hold_unreleased",
        "party_hold_unreleased",
        "stock_expired",
        "missing_acquisition_cost",
        "unassigned_cost_component",
        "stale_cost_review",
        "negative_actual_db1",
    ]
    assert catalog.classes[0]["causes"][0]["id"] == "insufficient_reservation"
    assert {entry["derivation"] for entry in catalog.classes} == set(
        DERIVATION_REGISTRY
    )


def test_packaged_runtime_load_does_not_require_development_test_files(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(catalogs, "ROOT", tmp_path)

    catalog = load_operational_exception_catalog()

    assert {entry["derivation"] for entry in catalog.classes} == set(
        DERIVATION_REGISTRY
    )


@pytest.mark.parametrize("field", ["label", "severity", "record_type", "authority"])
def test_catalog_rejects_invalid_metadata(field):
    candidate = payload()
    candidate["classes"][0][field] = ""

    with pytest.raises(ValueError, match=field):
        validate_operational_exception_catalog(
            candidate, registry_keys=tuple(DERIVATION_REGISTRY)
        )


def test_catalog_rejects_duplicate_and_empty_evidence():
    candidate = payload()
    candidate["classes"][1]["id"] = candidate["classes"][0]["id"]
    with pytest.raises(ValueError, match="Duplicate"):
        validate_operational_exception_catalog(
            candidate, registry_keys=tuple(DERIVATION_REGISTRY)
        )

    candidate = payload()
    candidate["classes"][0]["evidence"] = []
    with pytest.raises(ValueError, match="evidence"):
        validate_operational_exception_catalog(
            candidate, registry_keys=tuple(DERIVATION_REGISTRY)
        )


def test_catalog_rejects_registry_drift_deterministically():
    with pytest.raises(
        ValueError,
        match=r"missing=\['future_class'\], stale=\['unmatched_financial_event'\]",
    ):
        validate_operational_exception_catalog(
            payload(),
            registry_keys=tuple(
                key for key in DERIVATION_REGISTRY if key != "unmatched_financial_event"
            )
            + ("future_class",),
        )


def test_catalog_rejects_unordered_classes_and_cause_drift():
    candidate = payload()
    candidate["classes"][0], candidate["classes"][1] = (
        candidate["classes"][1],
        candidate["classes"][0],
    )
    with pytest.raises(ValueError, match="class order mismatch"):
        validate_operational_exception_catalog(
            candidate, registry_keys=tuple(DERIVATION_REGISTRY)
        )

    candidate = payload()
    for entry in candidate["classes"]:
        entry["causes"] = []
    with pytest.raises(ValueError, match="cause drift"):
        validate_operational_exception_catalog(
            candidate, registry_keys=tuple(DERIVATION_REGISTRY)
        )


def test_class_order_constants_agree():
    from reality.services.exceptions import CLASS_ORDER

    # The two constants are duplicated because the exception module cannot import
    # the catalog module at import time without a cycle. Nothing else keeps them
    # in step, so this is the guard.
    assert tuple(CLASS_ORDER) == catalogs.OPERATIONAL_EXCEPTION_CLASS_ORDER
    assert sorted(CLASS_ORDER.values()) == list(range(len(CLASS_ORDER)))


def test_shared_cause_is_declared_on_both_classes():
    catalog = load_operational_exception_catalog()

    declaring = {
        entry["id"]
        for entry in catalog.classes
        for cause in entry.get("causes", [])
        if cause["id"] == "insufficient_reservation"
    }

    # The same business reason appears on the overdue and the at-risk class, and
    # each declaration carries its own executable evidence.
    assert declaring == {
        "overdue_outgoing_customer_commitment",
        "outgoing_commitment_at_risk",
    }
    for entry in catalog.classes:
        for cause in entry.get("causes", []):
            assert cause["evidence"]


def test_catalog_rejects_cause_vocabulary_drift():
    candidate = payload()
    candidate["classes"][0]["causes"] = [
        {
            "id": "invented_reason",
            "label": "Invented reason",
            "authority": "068/FR-003",
            "evidence": ["tests/operational_exceptions/test_derivation.py::test_x"],
        }
    ]

    with pytest.raises(ValueError, match="cause"):
        validate_operational_exception_catalog(
            candidate, registry_keys=tuple(DERIVATION_REGISTRY)
        )

    assert catalogs.OPERATIONAL_EXCEPTION_CAUSE_VOCABULARY == (
        "insufficient_reservation",
        "early_payment_discount_taken",
        "promise_was_revised",
        "reserved_for_delivery",
        "acquisition_cost_unknown",
        "contribution_goods_cost_unknown",
        "cost_component_unassigned",
        "later_relevant_evidence",
        "supported_actual_db1_negative",
    )


def test_catalog_rejects_duplicate_cause_within_one_class():
    candidate = payload()
    causes = candidate["classes"][0]["causes"]
    candidate["classes"][0]["causes"] = [*causes, deepcopy(causes[0])]

    with pytest.raises(ValueError, match="Duplicate"):
        validate_operational_exception_catalog(
            candidate, registry_keys=tuple(DERIVATION_REGISTRY)
        )


GUIDANCE_FIELDS = ("description", "owner", "clears_through")
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GENERATED_PAGES = (
    REPO_ROOT / "apps/docs/content/tool-usage/exceptions.md",
    REPO_ROOT / "apps/docs/content/de/tool-usage/exceptions.md",
)


def test_every_class_carries_operator_guidance():
    catalog = load_operational_exception_catalog()

    for entry in catalog.classes:
        for field in GUIDANCE_FIELDS:
            assert entry[field].strip(), f"{entry['id']} has no {field}"
        # Guidance explains the condition; it does not restate the identifier.
        assert entry["description"].strip() != entry["label"]
        assert entry["id"] not in entry["description"]


@pytest.mark.parametrize("field", GUIDANCE_FIELDS)
@pytest.mark.parametrize("value", ["", "   "])
def test_catalog_rejects_missing_guidance(field, value):
    candidate = payload()
    class_id = candidate["classes"][0]["id"]
    candidate["classes"][0][field] = value

    with pytest.raises(ValueError, match=f"{field}.*{class_id}|{class_id}.*{field}"):
        validate_operational_exception_catalog(
            candidate, registry_keys=tuple(DERIVATION_REGISTRY)
        )

    candidate = payload()
    del candidate["classes"][0][field]
    with pytest.raises(ValueError, match=field):
        validate_operational_exception_catalog(
            candidate, registry_keys=tuple(DERIVATION_REGISTRY)
        )


def test_causes_are_not_required_to_carry_guidance():
    candidate = payload()
    causes = [entry for entry in candidate["classes"] if entry.get("causes")]
    assert causes, "expected at least one class with a cause"
    for entry in causes:
        for cause in entry["causes"]:
            assert not set(GUIDANCE_FIELDS) & set(cause)

    # A reason is read through the class that carries it, so the catalog must
    # keep accepting causes that carry label, authority and evidence only.
    validate_operational_exception_catalog(
        candidate, registry_keys=tuple(DERIVATION_REGISTRY)
    )


def test_generated_reference_carries_guidance():
    catalog = load_operational_exception_catalog()

    for page in GENERATED_PAGES:
        # The pages are formatted after generation, so prose is re-wrapped.
        # What must survive is the text, not the line breaks.
        rendered = " ".join(page.read_text(encoding="utf-8").split())
        for entry in catalog.classes:
            for field in GUIDANCE_FIELDS:
                expected = " ".join(entry[field].split())
                assert expected in rendered, (
                    f"{page.name} is missing the {field} of {entry['id']}"
                )


def test_the_discount_guidance_names_both_endings():
    """FR-009: the class goes quiet whether the discount was taken or lost.

    The guidance gate checks that guidance exists, not what it says, so the one
    thing an operator has to know about this class needs a test of its own. An
    operator who reads silence here as success has been misled by the queue.
    """
    catalog = load_operational_exception_catalog()
    entry = next(
        row for row in catalog.classes if row["id"] == "purchase_discount_available"
    )
    guidance = " ".join(f"{entry['description']} {entry['clears_through']}".split())

    assert "taken or lost" in guidance
    assert "deadline passes" in entry["clears_through"]


def test_the_return_guidance_says_how_to_record_a_fee():
    """FR-004: the guidance gate checks that guidance exists, not what it says.

    An operator who records a restocking fee as a smaller credit gets a true
    statement about their own document and an entry that never clears. Reality
    cannot know what was meant, so the only remedy is saying so before they do
    it.
    """
    catalog = load_operational_exception_catalog()
    entry = next(row for row in catalog.classes if row["id"] == "returned_not_credited")
    guidance = " ".join(entry["description"].split())

    assert "charge line beside a full credit" in guidance
    assert "fewer units than came back" in guidance


def test_catalog_parses_each_evidence_file_once_per_load(monkeypatch):
    parsed = []
    original = catalogs.ast.parse

    def track(source, filename="<unknown>", *args, **kwargs):
        parsed.append(filename)
        return original(source, filename, *args, **kwargs)

    monkeypatch.setattr(catalogs.ast, "parse", track)
    load_operational_exception_catalog()
    assert parsed
    assert len(parsed) == len(set(parsed))
    first = list(parsed)
    parsed.clear()
    load_operational_exception_catalog()
    assert parsed == first  # A later read still validates current evidence.


def test_catalog_rechecks_changed_or_missing_evidence(monkeypatch, tmp_path):
    candidate = payload()
    for entry in candidate["classes"]:
        entry["evidence"] = ["tests/evidence.py::test_evidence"]
        for cause in entry.get("causes", []):
            cause["evidence"] = ["tests/evidence.py::test_evidence"]
    evidence = tmp_path / "tests" / "evidence.py"
    evidence.parent.mkdir()
    evidence.write_text("def test_evidence(): pass\n")
    monkeypatch.setattr(catalogs, "ROOT", tmp_path)
    monkeypatch.setattr(
        catalogs, "config_text", lambda _: catalogs.yaml.safe_dump(candidate)
    )
    load_operational_exception_catalog()
    evidence.write_text("def renamed_test(): pass\n")
    with pytest.raises(ValueError, match="Missing operational exception evidence"):
        load_operational_exception_catalog()
    evidence.unlink()
    with pytest.raises(ValueError, match="Missing operational exception evidence"):
        load_operational_exception_catalog()
