from reality.services import product_advisor
from reality.services.product_advisor import (
    answer_product_question,
    classify_product_question,
    is_product_advisor_question,
    plan_product_concerns,
    research_evidence,
    retrieve_evidence,
)


def test_provider_prompt_constrains_workflow_roles(monkeypatch) -> None:
    captured = {}
    call_count = 0

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "submit_product_advice",
                        "input": {
                            "text": "Reality keeps the remainder open.",
                            "claims": [],
                        },
                    }
                ]
            }

    def post(url, *, headers, json, timeout):
        nonlocal call_count
        call_count += 1
        captured.update(json)
        return Response()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(product_advisor.httpx, "post", post)

    provider = product_advisor.product_advisor_provider()
    assert provider is not None
    provider({"question": "What happens with a partial delivery?", "evidence": []})

    assert call_count == 2

    system = captured["system"]
    schema = captured["tools"][0]["input_schema"]
    role_enum = schema["properties"]["claims"]["items"]["properties"][
        "workflow_role"
    ]["enum"]
    assert schema["properties"]["claims"]["minItems"] == 1
    assert "Do not use 'automatic'" in system
    for role in (
        "native",
        "agent_proposal",
        "confirmed_execution",
        "manual",
        "workaround",
        "gap",
    ):
        assert role in system
        assert role in role_enum


def test_under_delivery_retrieves_exact_supplier_journey() -> None:
    evidence = retrieve_evidence("What if a supplier delivers too little?")

    assert any(item.id == "evidence_journey_h02" for item in evidence)


def test_german_supplier_invoice_question_retrieves_invoice_evidence() -> None:
    evidence = retrieve_evidence(
        "Wie erfasse ich eine Lieferantenrechnung und welche Abweichungen erkennt Reality?"
    )

    assert any(item.id.startswith("evidence_journey_i") for item in evidence)


def test_german_supplier_partial_delivery_phrase_retrieves_under_delivery() -> None:
    evidence = retrieve_evidence(
        "Was passiert, wenn ein Lieferant nur einen Teil einer Bestellung liefert?"
    )

    assert any(item.id == "evidence_journey_h02" for item in evidence)


def test_ambiguous_partial_delivery_asks_which_trading_side_is_meant() -> None:
    provider_calls = []

    def provider(envelope):
        provider_calls.append(envelope)
        raise AssertionError("Ambiguity must be resolved before provider research.")

    answer = answer_product_question(
        "What happens with a partial delivery?", provider=provider
    )

    assert answer["outcome"] == "clarification"
    assert answer["citations"] == []
    assert answer["claims"] == []
    assert answer["clarification"].count("?") == 1
    assert "customer" in answer["clarification"].casefold()
    assert "supplier" in answer["clarification"].casefold()
    assert answer["text"] == answer["clarification"]
    assert provider_calls == []


def test_b2b_history_does_not_silently_resolve_partial_delivery_ambiguity() -> None:
    answer = answer_product_question(
        "What happens with a partial delivery?",
        history=(
            {"role": "user", "content": "How do I run a B2B order?"},
            {"role": "assistant", "content": "A B2B order follows order to cash."},
        ),
    )

    assert answer["outcome"] == "clarification"
    assert "customer" in answer["text"].casefold()
    assert "supplier" in answer["text"].casefold()


def test_explicit_supplier_partial_delivery_remains_answerable() -> None:
    answer = answer_product_question(
        "What happens when a supplier makes a partial delivery?"
    )

    assert answer["outcome"] != "clarification"
    assert "H02" in answer["citations"]


def test_customer_partial_delivery_retrieval_does_not_inherit_supplier_aliases() -> None:
    evidence = retrieve_evidence(
        "What remains open when a customer order quantity increases after a partial delivery?"
    )
    evidence_ids = [item.id for item in evidence]

    assert "evidence_journey_a04" in evidence_ids
    assert "evidence_journey_h02" not in evidence_ids


def test_partial_delivery_fallbacks_contain_concrete_erp_outcomes() -> None:
    supplier = answer_product_question(
        "What happens when a supplier makes a partial delivery?"
    )
    customer = answer_product_question(
        "What remains open when a customer order quantity increases after a partial delivery?"
    )

    assert "3 of 8" in supplier["text"]
    assert "5" in supplier["text"]
    assert "10" in customer["text"]
    assert "4" in customer["text"]
    assert "12" in customer["text"]
    assert "8" in customer["text"]


def test_broad_and_technical_questions_are_distinguished() -> None:
    assert classify_product_question("How would we run B2B with Reality?") == "solution_advice"
    assert (
        classify_product_question(
            "How does Reality handle B2B orders with customer credit limits?"
        )
        == "solution_advice"
    )
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


def test_invalid_provider_draft_gets_one_grounded_revision() -> None:
    calls = []

    def provider(envelope):
        calls.append(envelope)
        under_delivery = next(
            item for item in envelope["evidence"] if item["id"] == "evidence_journey_h02"
        )
        if len(calls) == 1:
            return {
                "text": "Reality supports complete automatic supplier fulfillment.",
                "claims": [
                    {
                        "id": "claim_overstatement",
                        "subject": "supplier fulfillment",
                        "statement": "Reality supports complete automatic supplier fulfillment.",
                        "support": "proven",
                        "evidence_ids": [under_delivery["id"]],
                        "limitations": [],
                        "workflow_role": "native",
                        "tool_names": [],
                    }
                ],
            }
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

    assert len(calls) == 2
    assert calls[1]["validation_feedback"]
    assert answer["outcome"] == "researched"
    assert "keeps the remainder open" in answer["text"]


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
