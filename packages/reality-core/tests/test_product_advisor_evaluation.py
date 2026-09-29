from pathlib import Path

import yaml

from reality.services.product_advisor import (
    detect_question_language,
    retrieve_evidence,
)

CASES = yaml.safe_load(
    (Path(__file__).parent / "fixtures/product_advisor_buyer_cases.yaml").read_text(
        encoding="utf-8"
    )
)["cases"]
CONVERSATIONS = yaml.safe_load(
    (Path(__file__).parent / "fixtures/product_advisor_conversations.yaml").read_text(
        encoding="utf-8"
    )
)["conversations"]


def _journey_citations(question: str) -> set[str]:
    return {
        reference
        for unit in retrieve_evidence(question)
        for reference in unit.references
        if len(reference) == 3 and reference[0].isalpha() and reference[1:].isdigit()
    }


def test_release_matrix_contains_at_least_75_reviewed_buyer_questions() -> None:
    assert len(CASES) >= 75
    assert len({case["id"] for case in CASES}) == len(CASES)


def test_every_buyer_question_retrieves_required_and_forbids_unsafe_journeys() -> None:
    failures: list[str] = []
    for case in CASES:
        citations = _journey_citations(case["question"])
        missing = set(case["required_citations"]) - citations
        forbidden = set(case["forbidden_citations"]) & citations
        if missing or forbidden:
            failures.append(
                f"{case['id']}: missing={sorted(missing)}, forbidden={sorted(forbidden)}"
            )
    assert not failures, "\n".join(failures)


def test_multilingual_matrix_detects_the_question_language() -> None:
    language_cases = [case for case in CASES if case["id"].startswith("partial-delivery-")]

    assert {case["language"] for case in language_cases} == {
        "en",
        "de",
        "nl",
        "es",
        "fr",
        "pl",
        "tr",
        "ar",
        "ja",
    }
    for case in language_cases:
        assert detect_question_language(case["question"]) == case["language"]


def test_broad_cases_define_concise_workflow_and_forbidden_claim_contracts() -> None:
    broad = [case for case in CASES if case["id"].startswith("broad-")]

    assert len(broad) >= 2
    for case in broad:
        assert len(case["required_concerns"]) >= 4
        assert case["forbidden_claims"]
        assert case["max_default_words"] <= 180


def test_connected_erp_selection_suite_has_five_ten_turn_conversations() -> None:
    assert len(CONVERSATIONS) >= 5
    assert len({item["id"] for item in CONVERSATIONS}) == len(CONVERSATIONS)
    for conversation in CONVERSATIONS:
        assert conversation["persona"]
        assert conversation["locale"] in {"de", "en"}
        assert len(conversation["required_conclusions"]) >= 3
        assert conversation["prohibited_overclaims"]
        assert conversation["final_required_sections"] == [
            "Belegt",
            "Grenzen",
            "Pilot",
        ]
        assert len(conversation["questions"]) == 10
        assert any(
            phrase in conversation["questions"][-1].casefold()
            for phrase in (
                "fit-gap",
                "pilot",
                "entscheidungsempfehlung",
                "gesamtfit",
            )
        )
