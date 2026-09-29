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

    assert call_count == 1

    system = captured["system"]
    schema = captured["tools"][0]["input_schema"]
    role_enum = schema["properties"]["claims"]["items"]["properties"]["workflow_role"][
        "enum"
    ]
    tool_names = schema["properties"]["claims"]["items"]["properties"]["tool_names"]
    assert schema["properties"]["claims"]["minItems"] == 0
    assert schema["properties"]["claims"]["maxItems"] == 8
    assert tool_names["maxItems"] == 0
    assert "materially different" in system
    assert "one focused clarification" in system
    assert "Do not use 'automatic'" in system
    assert "requested business object primary" in system
    assert "Tool names and vocabulary-only evidence" in system
    assert "must not be generalized to every manually created" in system
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


def test_provider_research_planner_selects_from_compact_catalog(monkeypatch) -> None:
    captured = {}
    observed_timeout = None

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "select_product_capabilities",
                        "input": {
                            "capability_ids": [
                                "capability_process_payment_and_release"
                            ],
                            "search_terms": ["customer overpayment"],
                        },
                    }
                ]
            }

    def post(url, *, headers, json, timeout):
        nonlocal observed_timeout
        observed_timeout = timeout
        captured.update(json)
        return Response()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(product_advisor.httpx, "post", post)

    provider = product_advisor.product_advisor_provider()
    assert provider is not None
    planner = provider.plan  # type: ignore[attr-defined]
    result = planner(
        {
            "question": "Wie geht Reality mit einer Überzahlung von Kunden um?",
            "detected_language": "de",
        }
    )

    assert result == {
        "capability_ids": ["capability_process_payment_and_release"],
        "search_terms": ["customer overpayment"],
    }
    payload = captured["messages"][0]["content"]
    assert "capability_process_payment_and_release" in payload
    assert "evidence_journey_c03" not in payload
    assert "claim_text" not in payload
    assert "search_text" not in payload
    assert (
        captured["tools"][0]["input_schema"]["properties"]["capability_ids"]["maxItems"]
        == 6
    )
    assert "input_schema" not in payload
    assert observed_timeout == 10.0


def test_provider_answer_stage_is_bounded_below_widget_timeout(monkeypatch) -> None:
    observed_timeout = None

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
                            "text": "Which trading side do you mean?",
                            "clarification": "Which trading side do you mean?",
                            "claims": [],
                        },
                    }
                ]
            }

    def post(url, *, headers, json, timeout):
        nonlocal observed_timeout
        observed_timeout = timeout
        return Response()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(product_advisor.httpx, "post", post)

    provider = product_advisor.product_advisor_provider()
    assert provider is not None
    provider({"question": "What happens with a partial delivery?", "evidence": []})

    assert observed_timeout == 12.0
    assert product_advisor._PLANNER_TIMEOUT_SECONDS + 2 * observed_timeout < 40
    assert 2 * product_advisor._BROAD_ANSWER_TIMEOUT_SECONDS < 40


def test_under_delivery_retrieves_exact_supplier_journey() -> None:
    evidence = retrieve_evidence("What if a supplier delivers too little?")

    assert any(item.id == "evidence_journey_h02" for item in evidence)


def test_german_supplier_invoice_question_retrieves_invoice_evidence() -> None:
    evidence = retrieve_evidence(
        "Wie erfasse ich eine Lieferantenrechnung und welche Abweichungen erkennt Reality?"
    )

    assert any(item.id.startswith("evidence_journey_i") for item in evidence)


def test_product_evaluation_question_retrieves_buyer_overview() -> None:
    evidence = retrieve_evidence(
        "Wo sind die wichtigsten Grenzen bei einer ERP-Bewertung von Reality?"
    )

    assert any(
        item.id.startswith("evidence_document_product_evaluation_") for item in evidence
    )


def test_product_evaluation_provider_failure_keeps_balanced_overview() -> None:
    def unavailable_provider(_envelope):
        raise product_advisor.httpx.ReadTimeout("provider timed out")

    answer = answer_product_question(
        "Wo sind heute die wichtigsten Grenzen, wenn ich Reality als ERP-Berater bewerte?",
        surface_language="de",
        provider=unavailable_provider,
    )

    assert answer["outcome"] == "fallback"
    assert answer["status"] == "partial"
    assert "Stark ist Reality" in answer["text"]
    assert "Wichtige Grenzen" in answer["text"]
    assert "Drei-Wege-Abgleich" in answer["text"]
    assert answer["citations"] == []
    assert answer["sources"][0]["id"] == "source_document_product_evaluation"


def test_mixed_supported_and_limited_claims_are_reported_as_partial() -> None:
    claims = [
        product_advisor.AdvisoryClaim(
            id="claim_supported",
            subject="supported capability",
            statement="A capability is supported.",
            support="proven",
            workflow_role="native",
        ),
        product_advisor.AdvisoryClaim(
            id="claim_gap",
            subject="current gap",
            statement="A different capability is not established.",
            support="not_established",
            workflow_role="gap",
        ),
    ]

    assert product_advisor._aggregate_status(claims) == "partial"


def test_german_supplier_partial_delivery_phrase_retrieves_under_delivery() -> None:
    evidence = retrieve_evidence(
        "Was passiert, wenn ein Lieferant nur einen Teil einer Bestellung liefert?"
    )

    assert any(item.id == "evidence_journey_h02" for item in evidence)


def test_semantic_plan_routes_german_overpayment_and_keeps_fallback_german() -> None:
    def invalid_provider(_envelope):
        return {"text": "Unsupported answer", "claims": []}

    def plan(envelope):
        assert envelope["detected_language"] == "de"
        return {
            "capability_ids": ["capability_process_payment_and_release"],
            "search_terms": ["customer overpayment"],
        }

    invalid_provider.plan = plan
    answer = answer_product_question(
        "Wie geht Reality mit einer Überzahlung von Kunden um?",
        provider=invalid_provider,
    )

    assert answer["outcome"] == "fallback"
    assert answer["detected_language"] == "de"
    assert answer["citations"] == ["C03"]
    assert "Kundenguthaben" in answer["text"]
    assert "Reality evaluates" not in answer["text"]


def test_ambiguous_partial_delivery_asks_which_trading_side_is_meant() -> None:
    provider_calls = []

    def provider(envelope):
        provider_calls.append(envelope)
        clarification = (
            "Do you mean a partial shipment to a customer or a partial goods receipt "
            "from a supplier?"
        )
        return {"text": clarification, "clarification": clarification, "claims": []}

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
    assert len(provider_calls) == 1


def test_provider_can_clarify_any_materially_ambiguous_business_term() -> None:
    def provider(_envelope):
        clarification = (
            "Do you mean reserving stock for a sales order or ordering missing stock "
            "from a supplier?"
        )
        return {"text": clarification, "clarification": clarification, "claims": []}

    answer = answer_product_question(
        "How does Reality handle allocation?", provider=provider
    )

    assert answer["outcome"] == "clarification"
    assert answer["text"] == answer["clarification"]
    assert answer["claims"] == []
    assert answer["citations"] == []


def test_provider_clarification_must_be_exactly_one_question() -> None:
    def provider(_envelope):
        return {
            "text": "Which allocation? Sales or purchasing?",
            "clarification": "Which allocation? Sales or purchasing?",
            "claims": [],
        }

    answer = answer_product_question(
        "How does Reality handle allocation?", provider=provider
    )

    assert answer["outcome"] == "fallback"
    assert answer["clarification"] is None


def test_b2b_history_does_not_silently_resolve_partial_delivery_ambiguity() -> None:
    def provider(envelope):
        assert envelope["history"][0]["content"] == "How do I run a B2B order?"
        clarification = (
            "Do you mean a partial shipment to a customer or a partial goods receipt "
            "from a supplier?"
        )
        return {"text": clarification, "clarification": clarification, "claims": []}

    answer = answer_product_question(
        "What happens with a partial delivery?",
        history=(
            {"role": "user", "content": "How do I run a B2B order?"},
            {"role": "assistant", "content": "A B2B order follows order to cash."},
        ),
        provider=provider,
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


def test_customer_partial_delivery_retrieval_does_not_inherit_supplier_aliases() -> (
    None
):
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
    assert (
        classify_product_question("How would we run B2B with Reality?")
        == "solution_advice"
    )
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
    assert is_product_advisor_question("Comment gérer une migration SAP avec Reality ?")
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


def test_broad_b2b_provider_failure_keeps_the_complete_operating_flow() -> None:
    def unavailable_provider(_envelope):
        raise product_advisor.httpx.ReadTimeout("provider timed out")

    answer = answer_product_question(
        "Wie bilde ich einen B2B-Auftrag ab?",
        surface_language="de",
        provider=unavailable_provider,
    )

    assert answer["outcome"] == "fallback"
    assert len(answer["citations"]) >= 4
    assert {"A01", "B01", "D01", "E01", "C03", "E06"} & set(answer["citations"])
    assert "B2B-Auftrag" in answer["text"]
    for expected_stage in (
        "Auftrag",
        "Reservierung",
        "Teillieferung",
        "Rechnung",
        "Zahlung",
        "Retoure",
    ):
        assert expected_stage in answer["text"]
    assert answer["citations"] != ["E07"]


def test_german_return_credit_fallback_uses_the_reviewed_localized_claim() -> None:
    def unavailable_provider(_envelope):
        raise product_advisor.httpx.ReadTimeout("provider timed out")

    answer = answer_product_question(
        "Wie bilde ich eine Kundenretoure mit Gutschrift ab?",
        surface_language="de",
        provider=unavailable_provider,
    )

    assert answer["outcome"] == "fallback"
    assert answer["citations"] == ["E06"]
    assert "Warenrückgabe" in answer["text"]
    assert "Auftragszeile" in answer["text"]
    assert "verlinkte Quelle enthält" not in answer["text"]


def test_common_german_erp_questions_remain_concrete_during_provider_outage() -> None:
    def unavailable_provider(_envelope):
        raise product_advisor.httpx.ReadTimeout("provider timed out")

    cases = (
        ("Was passiert bei einer Teillieferung an einen Kunden?", "D01", "Restmenge"),
        (
            "Was passiert, wenn ein Lieferant nur einen Teil der Bestellung liefert?",
            "H02",
            "Wareneingang",
        ),
        (
            "Wie geht Reality mit einer Überzahlung eines Kunden um?",
            "C03",
            "Kundenguthaben",
        ),
        (
            "Wie erkenne ich, dass eine Kundenrechnung vollständig bezahlt ist?",
            "A01",
            "offenen Betrag",
        ),
        (
            "Kann ich mehrere Lieferungen in einer Sammelrechnung abrechnen?",
            "E02",
            "mehreren Lieferungen",
        ),
    )

    for question, citation, expected_text in cases:
        answer = answer_product_question(
            question,
            surface_language="de",
            provider=unavailable_provider,
        )
        assert answer["outcome"] == "fallback"
        assert answer["citations"] == [citation]
        assert expected_text in answer["text"]


def test_self_contained_follow_up_does_not_inherit_stale_b2b_retrieval() -> None:
    def unavailable_provider(_envelope):
        raise product_advisor.httpx.ReadTimeout("provider timed out")

    answer = answer_product_question(
        "Kann ich nur einmal im Monat eine Rechnung stellen lassen für alle Lieferscheine?",
        surface_language="de",
        history=(
            {"role": "user", "content": "Wie bilde ich einen B2B-Auftrag ab?"},
            {
                "role": "assistant",
                "content": "Ein B2B-Auftrag folgt mehreren Schritten.",
            },
        ),
        provider=unavailable_provider,
    )

    assert answer["outcome"] == "fallback"
    assert answer["citations"] == ["E02"]
    assert "mehreren Lieferungen" in answer["text"]
    assert "A10" not in answer["citations"]


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
            item
            for item in envelope["evidence"]
            if item["id"] == "evidence_journey_h02"
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
            item
            for item in envelope["evidence"]
            if item["id"] == "evidence_journey_h02"
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


def test_unqualified_automation_word_is_safely_weakened_before_validation() -> None:
    def provider(envelope):
        under_delivery = next(
            item
            for item in envelope["evidence"]
            if item["id"] == "evidence_journey_h02"
        )
        return {
            "text": "Reality erfasst den Eingang und berechnet den Rest automatisch.",
            "claims": [
                {
                    "id": "claim_supplier_under_delivery",
                    "subject": "supplier under-delivery",
                    "statement": (
                        "Reality erfasst den Eingang und berechnet den Rest automatisch."
                    ),
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
    assert "automatisch" not in answer["text"].casefold()
    assert "automatisch" not in answer["claims"][0]["statement"].casefold()


def test_vocabulary_evidence_support_is_normalized_to_a_narrow_proven_claim() -> None:
    def provider(envelope):
        command = next(
            item
            for item in envelope["evidence"]
            if item["id"] == "evidence_command_record_sales_credit"
        )
        return {
            "text": "record_sales_credit records an invoice-linked customer credit.",
            "claims": [
                {
                    "id": "claim_record_sales_credit",
                    "subject": "sales credit command",
                    "statement": (
                        "record_sales_credit records an invoice-linked customer credit."
                    ),
                    "support": "vocabulary_only",
                    "evidence_ids": [command["id"]],
                    "limitations": [],
                    "workflow_role": "native",
                    "tool_names": ["record_sales_credit"],
                }
            ],
        }

    answer = answer_product_question(
        "Wie hängen Kundenretoure und Gutschrift zusammen?", provider=provider
    )

    assert answer["outcome"] == "researched"
    assert answer["claims"][0]["support"] == "proven"


def test_provider_cannot_invent_a_tool_name() -> None:
    def provider(envelope):
        under_delivery = next(
            item
            for item in envelope["evidence"]
            if item["id"] == "evidence_journey_h02"
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


def test_broad_provider_receives_interpretation_and_returns_only_one_clarification() -> (
    None
):
    captured = {}

    def provider(envelope):
        captured.update(envelope)
        clarification = "Do you sell from stock or make to order?"
        return {
            "text": clarification,
            "clarification": clarification,
            "claims": [],
        }

    answer = answer_product_question(
        "How do I run B2B with Reality?", provider=provider
    )

    assert captured["interpretation"] == "standard operating flow"
    assert len(captured["concerns"]) == 4
    assert answer["clarification"].count("?") == 1
    assert answer["claims"] == []
