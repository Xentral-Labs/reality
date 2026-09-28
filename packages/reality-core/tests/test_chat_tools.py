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
