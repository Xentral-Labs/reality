from reality.services.product_advisor import answer_product_question
from reality.tools import business_journeys
from reality.tools.business_journeys import business_journey_guide, guide_actor_context


def test_read_tool_uses_the_same_public_advisor(session, monkeypatch) -> None:
    monkeypatch.setattr(business_journeys, "product_advisor_provider", lambda: None)
    question = "What happens when a supplier delivers too little?"

    actual = business_journey_guide(
        session, "tenant_example", {"question": question, "locale": "en"}
    )
    expected = answer_product_question(question, surface_language="en")

    assert actual["status"] == expected["status"]
    assert actual["citations"] == expected["citations"]
    assert actual["knowledge_version"] == expected["knowledge_version"]
    assert "internal_evidence" not in actual


def test_internal_read_tool_adds_evidence_without_raising_public_ceiling(
    session, scheduled_owner, monkeypatch
) -> None:
    scheduled_owner.is_platform_admin = True
    session.flush()
    monkeypatch.setattr(business_journeys, "product_advisor_provider", lambda: None)
    arguments = {
        "question": "What happens when a supplier delivers too little?",
        "locale": "en",
    }

    public = business_journey_guide(session, "tenant_example", dict(arguments))
    with guide_actor_context(scheduled_owner.id):
        internal = business_journey_guide(session, "tenant_example", dict(arguments))

    assert internal["status"] == public["status"]
    assert internal["citations"] == public["citations"]
    assert internal["claims"] == public["claims"]
    assert internal["internal_evidence"]
