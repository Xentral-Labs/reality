from reality.services.product_advisor import is_product_advisor_question
from reality.tools.application import TOOLS


def test_product_intent_routes_broad_advice_but_not_tenant_observations() -> None:
    assert is_product_advisor_question("How would we run B2B with Reality?")
    assert is_product_advisor_question("Was passiert bei einer Teillieferung?")
    assert is_product_advisor_question("How do I record a supplier invoice?")
    assert not is_product_advisor_question("Show my open invoices")
    assert not is_product_advisor_question("How do I record my invoice?")


def test_advice_is_read_only_and_proposals_keep_confirmation() -> None:
    assert not TOOLS["business_journey_guide"].mutating
    assert TOOLS["business_journey_proposal_create"].mutating
    assert TOOLS["business_journey_vote_set"].mutating


def test_current_company_mission_with_reality_is_operational():
    assert not is_product_advisor_question(
        "Du bist der operative Agent meiner ausgewählten Reality-Demo-Firma. "
        "Nutze die Reality-Tools und priorisiere offene Aufträge. "
        "Lies zunächst nur; Änderungen brauchen meine Freigabe."
    )
    assert not is_product_advisor_question(
        "Use Reality tools to review my company orders"
    )
    assert is_product_advisor_question(
        "Was passiert, wenn mein Lieferant zu wenig liefert?"
    )


def test_reality_product_advice_may_mention_our_company():
    assert is_product_advisor_question("How can our company use Reality for B2B?")
