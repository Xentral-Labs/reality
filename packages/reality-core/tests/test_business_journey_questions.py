from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from reality.catalogs import config_text
from reality.domain.business_journeys import load_journey_catalog
from reality.services.business_journeys import answer_public_question
from reality.services.core import create_chat_session, send_chat_message
from reality.services.product_advisor import answer_product_question
from reality.tools.application import run_read_tool

QUESTION_FIXTURES = yaml.safe_load(
    (Path(__file__).parent / "fixtures/business_journey_questions.yaml").read_text()
)


def _catalog():
    return load_journey_catalog(
        yaml.safe_load(config_text("business_journey_catalog.yaml"))
    )


def test_supplier_under_delivery_is_grounded_in_catalog_entries() -> None:
    answer = answer_public_question(
        _catalog(), "What happens if a supplier delivers too little?", locale="en"
    )

    assert answer.matches
    assert "H02" in {match.id for match in answer.matches}
    assert answer.citations
    assert set(answer.citations) <= {match.id for match in answer.matches}
    assert answer.status in {"supported", "partial"}


def test_german_supplier_under_delivery_uses_the_same_canonical_entry() -> None:
    answer = answer_public_question(
        _catalog(), "Was passiert, wenn ein Lieferant zu wenig liefert?", locale="de"
    )

    assert "H02" in {match.id for match in answer.matches}
    assert answer.locale == "de"


@pytest.mark.parametrize(
    "case", QUESTION_FIXTURES["public_questions"], ids=lambda case: case["name"]
)
def test_bilingual_and_multi_journey_question_matrix(case) -> None:
    answer = answer_public_question(_catalog(), case["question"], locale=case["locale"])

    assert set(case["expected_ids"]) <= set(answer.citations)
    assert answer.locale == case["locale"]


def test_unknown_question_never_invents_a_capability() -> None:
    answer = answer_public_question(
        _catalog(), "Can Reality teleport a warehouse to the moon?", locale="en"
    )

    assert answer.status == "not_established"
    assert answer.citations == ()
    assert "not established" in answer.text.lower()


def test_provider_can_semantically_ground_a_misspelled_question() -> None:
    def provider(envelope):
        assert envelope["question"] == "can you manage returnsn?"
        assert envelope["allowed_locales"] == ["en", "de", "nl", "es"]
        assert any(entry["id"] == "F02" for entry in envelope["catalog"])
        return {
            "text": "Yes. Reality records a partial return while preserving what the customer kept.",
            "status": "supported",
            "citations": ["F02"],
        }

    answer = answer_public_question(
        _catalog(), "can you manage returnsn?", locale="en", provider=provider
    )

    assert answer.outcome == "provider"
    assert answer.status == "supported"
    assert answer.citations == ("F02",)
    assert [match.id for match in answer.matches] == ["F02"]


def test_provider_receives_bounded_follow_up_context() -> None:
    def provider(envelope):
        assert envelope["history"] == [
            {"role": "user", "content": "Kann ein Lieferant in Teilen liefern?"},
            {"role": "assistant", "content": "Ja, Teillieferungen werden verfolgt."},
        ]
        return {
            "text": "Ja. Mehrere Wareneingänge können der offenen Bestellmenge zugeordnet werden.",
            "status": "supported",
            "citations": ["H02"],
        }

    answer = answer_public_question(
        _catalog(),
        "Und Wareneingang in mehreren Schritten?",
        locale="de",
        history=(
            {"role": "user", "content": "Kann ein Lieferant in Teilen liefern?"},
            {"role": "assistant", "content": "Ja, Teillieferungen werden verfolgt."},
        ),
        provider=provider,
    )

    assert answer.outcome == "provider"
    assert answer.citations == ("H02",)


def test_server_derives_status_from_provider_citations() -> None:
    def provider(_envelope):
        return {
            "text": "Reality supports the standard case, with documented limitations.",
            "status": "supported",
            # A journey that is still partial: the provider's claim must not win.
            "citations": ["A02"],
        }

    answer = answer_public_question(
        _catalog(), "Can one order ship from several warehouses?", provider=provider
    )

    assert answer.outcome == "provider"
    assert answer.status == "partial"


def test_broad_product_question_is_a_valid_advisor_question() -> None:
    def provider(envelope):
        assert envelope["question"] == "Was kann Reality alles?"
        return {
            "text": "Reality verbindet Aufträge, Bestand, Versand, Rechnungen und Zahlungen; einzelne Journeys haben dokumentierte Grenzen.",
            "status": "partial",
            "citations": ["A01", "D01", "E01", "F01"],
        }

    answer = answer_public_question(
        _catalog(), "Was kann Reality alles?", locale="de", provider=provider
    )

    assert answer.outcome == "provider"


def test_advisor_receives_relevant_executable_tools() -> None:
    def provider(envelope):
        tools = envelope["advisor_tools"]
        assert any(
            "supplier_invoice_record_propose" in item["agent_tools"] for item in tools
        )
        return {
            "text": "Create the supplier invoice from its stated evidence. **Tools:** Use supplier_invoice_record_propose and confirm the proposal.",
            "status": "partial",
            "citations": ["I01"],
        }

    answer = answer_public_question(
        _catalog(),
        "Wie kann ich eine Lieferantenrechnung anlegen?",
        locale="de",
        provider=provider,
    )

    assert answer.outcome == "provider"
    assert "supplier_invoice_record_propose" in answer.text
    assert answer.status == "partial"
    assert answer.citations


def test_provider_cannot_upgrade_a_mixed_capability_answer() -> None:
    def provider(_envelope):
        return {
            "text": "Reality supports some return flows, with documented limitations.",
            "status": "partial",
            "citations": ["F02", "F08"],
        }

    answer = answer_public_question(
        _catalog(), "Can Reality manage returns?", locale="en", provider=provider
    )

    assert answer.outcome == "provider"
    assert answer.status == "partial"
    assert answer.citations == ("F02", "F08")


def test_published_ids_named_in_prose_are_added_to_citations() -> None:
    def provider(_envelope):
        return {
            "text": "Partial returns use F02; goodwill refunds use F08.",
            "status": "partial",
            "citations": ["F02"],
        }

    answer = answer_public_question(
        _catalog(), "Can Reality manage returns?", locale="en", provider=provider
    )

    assert answer.outcome == "provider"
    assert answer.status == "partial"
    assert answer.citations == ("F02", "F08")


@pytest.mark.parametrize(
    ("locale", "expected"),
    [
        ("en", "not established"),
        ("de", "nicht belegt"),
        ("nl", "niet aangetoond"),
        ("es", "no está demostrada"),
    ],
)
def test_all_public_languages_have_a_safe_fallback(locale, expected) -> None:
    answer = answer_public_question(
        _catalog(), "Teleport the warehouse to the moon", locale=locale
    )

    assert answer.status == "not_established"
    assert expected in answer.text.lower()


def test_question_is_bounded() -> None:
    try:
        answer_public_question(_catalog(), "x" * 1001, locale="en")
    except ValueError as error:
        assert "1000" in str(error)
    else:  # pragma: no cover - explicit assertion branch
        raise AssertionError("Expected an overlong question to be rejected")


def test_normal_chat_uses_the_same_capability_basis(
    session, business, monkeypatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    chat = create_chat_session(session, business.tenant.id)

    _, reply = send_chat_message(
        session,
        business.tenant.id,
        chat.id,
        "Can Reality handle a supplier delivering too little?",
        language="en",
    )

    assert "3 of 8 ordered units" in reply.content
    assert "open remainder of 5" in reply.content
    assert "H02" in reply.content


def test_registered_read_tool_matches_public_service(session, business) -> None:
    question = "What if a supplier delivers too little?"
    expected = answer_product_question(question)

    actual = run_read_tool(
        session,
        business.tenant.id,
        "business_journey_guide",
        {"question": question, "locale": "en"},
    )

    assert actual["status"] == expected["status"]
    assert actual["citations"] == expected["citations"]
    assert "internal_evidence" not in str(actual)


def test_platform_admin_chat_receives_additive_internal_evidence(
    session, business, scheduled_owner, monkeypatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    scheduled_owner.is_platform_admin = True
    session.flush()
    chat = create_chat_session(session, business.tenant.id)

    _, reply = send_chat_message(
        session,
        business.tenant.id,
        chat.id,
        "Can Reality handle a supplier delivering too little?",
        actor_user_id=scheduled_owner.id,
        language="en",
    )

    assert "3 of 8 ordered units" in reply.content
    assert "open remainder of 5" in reply.content
    assert "Internal evidence:" in reply.content
    assert "tests/scenarios" in reply.content
