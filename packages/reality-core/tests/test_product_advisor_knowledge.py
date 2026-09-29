import json

import pytest

from reality.domain.product_advisor import ProductAdvisorKnowledge
from reality.services.product_advisor import (
    product_advisor_knowledge,
    product_capability_map,
)


def test_checked_in_capability_map_matches_advisor_knowledge() -> None:
    """The two runtime artifacts must remain usable after independently merged changes."""
    knowledge = product_advisor_knowledge()
    capability_map = product_capability_map()

    assert capability_map.knowledge_version == knowledge.knowledge_version


def test_knowledge_rejects_duplicate_evidence_identity() -> None:
    payload = {
        "schema_version": 1,
        "knowledge_version": "advisor-v1:test",
        "sources": [],
        "evidence": [
            {
                "id": "evidence_duplicate",
                "source_id": "source_missing",
                "subject": "orders",
                "title": "Orders",
                "search_text": "orders",
                "claim_text": "Orders are supported.",
                "support": "proven",
                "fingerprint": "a" * 64,
            },
            {
                "id": "evidence_duplicate",
                "source_id": "source_missing",
                "subject": "orders",
                "title": "Orders again",
                "search_text": "orders",
                "claim_text": "Orders are supported.",
                "support": "proven",
                "fingerprint": "b" * 64,
            },
        ],
    }

    with pytest.raises(ValueError, match="Duplicate evidence id"):
        ProductAdvisorKnowledge.model_validate(payload)


def test_public_knowledge_serialization_contains_no_internal_location() -> None:
    payload = {
        "schema_version": 1,
        "knowledge_version": "advisor-v1:test",
        "sources": [
            {
                "id": "source_docs",
                "kind": "public_document",
                "title": "Integration contract",
                "visibility": "public",
                "authority": "technical_contract",
                "public_url": "https://docs.runreality.ai/integrations/connector-contract",
                "fingerprint": "a" * 64,
            }
        ],
        "evidence": [
            {
                "id": "evidence_docs",
                "source_id": "source_docs",
                "subject": "integration",
                "title": "Integration contract",
                "search_text": "integration connector",
                "claim_text": "Reality exposes a connector contract.",
                "support": "explanatory",
                "fingerprint": "b" * 64,
            }
        ],
    }

    rendered = json.dumps(ProductAdvisorKnowledge.model_validate(payload).public_payload())

    assert "packages/" not in rendered
    assert "specs/" not in rendered
    assert "tests/" not in rendered
