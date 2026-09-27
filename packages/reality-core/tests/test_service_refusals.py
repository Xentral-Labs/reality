"""Service refusals carry a code and values next to their English sentence (spec 286)."""

from datetime import date
from decimal import Decimal

import pytest

from reality.domain import refusals
from reality.services.core import Conflict, InvalidOperation, NotFound

CATALOG = {
    "version": 1,
    "refusals": {
        "sample_plain": {"message": "The sample is refused."},
        "sample_line": {
            "message": "Line {index} requires a stated amount; it is never calculated.",
            "values": {"index": "number"},
        },
        "sample_field": {
            "message": "{field} cannot be negative.",
            "values": {"field": "term"},
        },
        "sample_amount": {
            "message": "The amount {amount} is due on {day}.",
            "values": {"amount": "amount", "day": "date"},
        },
    },
    "terms": ["Lead time days"],
}


@pytest.fixture
def catalog(monkeypatch):
    monkeypatch.setattr(refusals, "catalog", lambda: refusals.validate_catalog(CATALOG))


# FR-001 / FR-002 --------------------------------------------------------------------


def test_coded_refusal_carries_code_and_values(catalog):
    error = InvalidOperation(code="sample_line", values={"index": 3})
    assert error.code == "sample_line"
    assert error.values == {"index": "3"}
    assert str(error) == "Line 3 requires a stated amount; it is never calculated."
    assert error.template == (
        "Line {index} requires a stated amount; it is never calculated."
    )
    # Every refusal class takes the same keywords.
    assert NotFound(code="sample_plain").code == "sample_plain"
    assert isinstance(Conflict(code="sample_plain"), InvalidOperation)


def test_english_sentence_is_the_filled_template(catalog):
    error = InvalidOperation(code="sample_field", values={"field": "Lead time days"})
    assert str(error) == "Lead time days cannot be negative."
    assert refusals.payload(error) == {
        "code": "sample_field",
        "template": "{field} cannot be negative.",
        "values": {"field": {"value": "Lead time days", "kind": "term"}},
    }


def test_message_and_code_together_is_a_type_error(catalog):
    with pytest.raises(TypeError):
        InvalidOperation("Some sentence.", code="sample_plain")


def test_values_are_only_template_placeholders(catalog):
    with pytest.raises(ValueError, match="values"):
        InvalidOperation(code="sample_line", values={"index": 1, "tenant": "ten_x"})
    with pytest.raises(ValueError, match="values"):
        InvalidOperation(code="sample_line")


def test_values_are_exact_strings(catalog):
    error = InvalidOperation(
        code="sample_amount",
        values={"amount": Decimal("59.5000"), "day": date(2026, 9, 27)},
    )
    assert error.values == {"amount": "59.5000", "day": "2026-09-27"}
    assert str(error) == "The amount 59.5000 is due on 2026-09-27."


def test_strict_mode_refuses_unknown_code_and_terms(catalog, monkeypatch):
    with pytest.raises(ValueError, match="Unknown refusal code"):
        InvalidOperation(code="sample_unknown")
    with pytest.raises(ValueError, match="term"):
        InvalidOperation(code="sample_field", values={"field": "Not a listed term"})
    # Production never hides a refusal behind a catalog mistake: it falls back to English.
    monkeypatch.setenv("REALITY_STRICT_REFUSALS", "0")
    fallback = InvalidOperation(
        code="sample_field", values={"field": "Not a listed term"}
    )
    assert str(fallback) == "Not a listed term cannot be negative."
    unknown = InvalidOperation(code="sample_unknown")
    assert unknown.code == "sample_unknown" and str(unknown) == "sample_unknown"
    assert refusals.payload(unknown) is None


def test_uncoded_refusal_is_unchanged(catalog):
    error = InvalidOperation("Net plus tax differs from the invoice gross.")
    assert str(error) == "Net plus tax differs from the invoice gross."
    assert error.code is None and error.values == {}
    assert refusals.payload(error) is None


def test_class_codes_of_existing_subclasses_are_kept():
    from reality.services.analytics.errors import AnalyticsError
    from reality.services.cost_review_draft import DraftChanged
    from reality.services.tenant_policy import PlaygroundOperationDenied

    assert AnalyticsError("Refused.", code="query_too_broad").code == "query_too_broad"
    assert DraftChanged({}).code == "draft_changed"
    assert PlaygroundOperationDenied("Denied.").code == "playground_operation_denied"
    # A class code is not a catalog code: no template is sent for it.
    assert refusals.payload(PlaygroundOperationDenied("Denied.")) is None


# The shipped catalog ------------------------------------------------------------------


def test_the_shipped_catalog_is_valid():
    shipped = refusals.catalog()
    assert shipped["version"] == 1
    for code, entry in shipped["refusals"].items():
        assert refusals.CODE.fullmatch(code), code
        assert set(refusals.placeholders(entry["message"])) == set(entry["values"])
