from reality.services.product_advisor import (
    answer_product_question,
    classify_product_question,
    is_product_advisor_question,
    plan_product_concerns,
    research_evidence,
    retrieve_evidence,
)


def test_under_delivery_retrieves_exact_supplier_journey() -> None:
    evidence = retrieve_evidence("What if a supplier delivers too little?")

    assert any(item.id == "evidence_journey_h02" for item in evidence)


def test_broad_and_technical_questions_are_distinguished() -> None:
    assert classify_product_question("How would we run B2B with Reality?") == "solution_advice"
    assert (
        classify_product_question("Which APIs and integrations does Reality expose?")
        == "product_technical"
    )


def test_product_intent_is_not_limited_to_fixed_can_reality_phrases() -> None:
    assert is_product_advisor_question("How do I run B2B?")
    assert is_product_advisor_question(
        "Was passiert, wenn mein Lieferant zu wenig liefert?"
    )
    assert is_product_advisor_question(
        "Comment gérer une migration SAP avec Reality ?"
    )
    assert not is_product_advisor_question("Show my open customer orders")


def test_broad_b2b_research_is_decomposed_across_the_operating_flow() -> None:
    concerns = plan_product_concerns("How would we run B2B with Reality?")
    evidence = research_evidence("How would we run B2B with Reality?")
    subjects = " ".join(item.search_text.casefold() for item in evidence)

    assert len(concerns) == 4
    assert "order" in subjects
    assert "delivery" in subjects
    assert "invoice" in subjects
    assert "payment" in subjects or "return" in subjects


def test_provider_cannot_claim_migration_from_unrelated_evidence() -> None:
    def provider(envelope):
        first = envelope["evidence"][0]
        return {
            "text": "Reality supports complete SAP migration.",
            "claims": [
                {
                    "id": "claim_sap_migration",
                    "subject": "migration",
                    "statement": "Reality supports complete SAP migration.",
                    "support": "proven",
                    "evidence_ids": [first["id"]],
                    "limitations": [],
                    "workflow_role": "native",
                    "tool_names": [],
                }
            ],
        }

    answer = answer_product_question(
        "Can we migrate from SAP to Reality?", provider=provider
    )

    assert answer["outcome"] == "fallback"
    assert "supports complete SAP migration" not in answer["text"]


def test_valid_claim_returns_structured_sources() -> None:
    def provider(envelope):
        under_delivery = next(
            item for item in envelope["evidence"] if item["id"] == "evidence_journey_h02"
        )
        return {
            "text": "Reality records the receipt and keeps the remainder open.",
            "claims": [
                {
                    "id": "claim_supplier_under_delivery",
                    "subject": "supplier under-delivery",
                    "statement": "Reality records the receipt and keeps the remainder open.",
                    "support": "proven",
                    "evidence_ids": [under_delivery["id"]],
                    "limitations": [],
                    "workflow_role": "native",
                    "tool_names": [],
                }
            ],
        }

    answer = answer_product_question(
        "What if a supplier delivers too little?", provider=provider
    )

    assert answer["outcome"] == "researched"
    assert answer["status"] == "supported"
    assert answer["citations"] == ["H02"]
    assert answer["claims"][0]["validation"] == "accepted"


def test_provider_cannot_invent_a_tool_name() -> None:
    def provider(envelope):
        under_delivery = next(
            item for item in envelope["evidence"] if item["id"] == "evidence_journey_h02"
        )
        return {
            "text": "Reality keeps the remainder open. Tool: invent_everything.",
            "claims": [
                {
                    "id": "claim_fake_tool",
                    "subject": "supplier under-delivery",
                    "statement": "Reality keeps the remainder open.",
                    "support": "proven",
                    "evidence_ids": [under_delivery["id"]],
                    "limitations": [],
                    "workflow_role": "native",
                    "tool_names": ["invent_everything"],
                }
            ],
        }

    answer = answer_product_question(
        "What if a supplier delivers too little?", provider=provider
    )

    assert answer["outcome"] == "fallback"
    assert "invent_everything" not in answer["text"]


def test_broad_provider_receives_interpretation_and_at_most_one_clarification() -> None:
    captured = {}

    def provider(envelope):
        captured.update(envelope)
        first = next(item for item in envelope["evidence"] if item["support"] == "proven")
        return {
            "text": "I am using the standard B2B operating flow.",
            "clarification": "Do you sell from stock or make to order?",
            "claims": [
                {
                    "id": "claim_b2b_interpretation",
                    "subject": first["subject"],
                    "statement": first["claim_text"],
                    "support": "proven",
                    "evidence_ids": [first["id"]],
                    "limitations": list(first["limitations"]),
                    "workflow_role": "native",
                    "tool_names": [],
                }
            ],
        }

    answer = answer_product_question("How do I run B2B with Reality?", provider=provider)

    assert captured["interpretation"] == "standard operating flow"
    assert len(captured["concerns"]) == 4
    assert answer["clarification"].count("?") == 1
