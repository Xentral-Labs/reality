from __future__ import annotations

import copy
import re

import pytest
import yaml

from reality.catalogs import config_text
from reality.domain.business_journeys import (
    JourneyCatalogError,
    load_journey_catalog,
)


def _payload() -> dict[str, object]:
    return yaml.safe_load(config_text("business_journey_catalog.yaml"))


def test_catalog_accounts_for_every_baseline_journey_once() -> None:
    catalog = load_journey_catalog(_payload())

    assert len(catalog.entries) == 228
    assert len({entry.id for entry in catalog.entries}) == 228
    assert catalog.entries[0].id == "A01"
    assert catalog.entries[-1].id == "R08"
    assert {entry.id[0] for entry in catalog.entries} == set("ABCDEFGHIJKLMNOPQR")


def test_supported_entries_require_executable_evidence() -> None:
    payload = _payload()
    changed = copy.deepcopy(payload)
    changed["entries"][0]["status"] = "supported"
    changed["entries"][0]["evidence_level"] = "reviewed"

    with pytest.raises(JourneyCatalogError, match="A01.*executable"):
        load_journey_catalog(changed)


def test_non_supported_entries_explain_their_limit() -> None:
    payload = _payload()
    changed = copy.deepcopy(payload)
    partial = next(row for row in changed["entries"] if row["status"] == "partial")
    partial["limitations"] = []

    with pytest.raises(JourneyCatalogError, match=f"{partial['id']}.*limitation"):
        load_journey_catalog(changed)


def test_related_journeys_must_resolve() -> None:
    payload = _payload()
    changed = copy.deepcopy(payload)
    changed["entries"][0]["related_journeys"] = ["Z99"]

    with pytest.raises(JourneyCatalogError, match="A01.*Z99"):
        load_journey_catalog(changed)


def test_public_serialization_cannot_leak_internal_evidence() -> None:
    catalog = load_journey_catalog(_payload())
    public = catalog.public_payload()
    rendered = yaml.safe_dump(public)

    assert "internal_evidence" not in rendered
    assert "packages/reality-core/tests" not in rendered
    assert len(public["entries"]) == 228

    for entry in catalog.entries:
        for evidence in entry.internal_evidence:
            if "/" in evidence.reference:
                assert evidence.reference not in rendered
            if len(evidence.note) >= 40:
                assert evidence.note not in rendered


def test_confirmed_agent_assisted_revision_is_not_described_as_person_only() -> None:
    catalog = load_journey_catalog(_payload())
    entry = next(item for item in catalog.entries if item.id == "H03")

    assert "confirmed revision" in entry.question
    assert "agent can prepare" in entry.summary
    assert "person with a reason" not in entry.question


def test_non_supported_journeys_state_their_own_limitation() -> None:
    catalog = load_journey_catalog(_payload())
    generic = set(catalog.public_payload()["statuses"].values()) | {
        "Only part of this journey is currently proven.",
        "The current model or services do not support this complete journey.",
        "This journey is deliberately outside the current product scope.",
    }
    limited = [entry for entry in catalog.entries if entry.status != "supported"]

    assert {entry.status for entry in limited} >= {"partial", "missing", "out_of_scope"}
    for entry in limited:
        assert entry.limitations, entry.id
        assert not set(entry.limitations) & generic, entry.id


def test_public_limitations_carry_no_repository_details() -> None:
    catalog = load_journey_catalog(_payload())
    leaks = re.compile(
        r"`|\.py\b|::|\bspecs?\s+\d|#\d|\b[a-z]+_[a-z_]+\b", re.IGNORECASE
    )

    for entry in catalog.entries:
        for limitation in entry.limitations:
            assert not leaks.search(limitation), f"{entry.id}: {limitation}"


PROVEN_BY_STORY = {
    "A04",
    "A06",
    "A07",
    "A19",
    "C04",
    "D16",
    "F01",
    "F05",
    "F07",
    "G07",
    "H03",
    "I06",
    "I07",
    "K05",
    "L06",
    "M08",
    "N01",
    "N02",
    "N04",
    "N06",
    "O01",
    "P04",
    "P07",
}
#: Promoted from spec 294 on; each must be findable by an ordinary question.
FINDABLE_BY_KEYWORD = {
    "F07",
    "D16",
    "G07",
    "H03",
    "I06",
    "I07",
    "K05",
    "L06",
    "N04",
    "O01",
    "P04",
    "P07",
}


def test_story_proven_journeys_cite_their_catalog_story() -> None:
    """Specs 292 and 293: a promotion stands on a named catalog story."""
    entries = {entry.id: entry for entry in load_journey_catalog(_payload()).entries}
    story = "packages/reality-core/tests/scenarios/test_catalog_"

    for journey in PROVEN_BY_STORY:
        entry = entries[journey]
        assert (entry.status, entry.evidence_level) == ("supported", "executable")
        assert entry.internal_evidence[0].reference.startswith(story), journey
        assert not any("not yet proven" in text for text in entry.limitations)

    # Spec 293 turned the exchange from a pinned gap into a proof.
    assert "customer_exchange" in entries["F07"].internal_evidence[0].note


def test_story_proven_journeys_can_be_found_by_ordinary_words() -> None:
    """Spec 294 FR-005: a promotion the Guide cannot find helps nobody."""
    entries = {entry.id: entry for entry in load_journey_catalog(_payload()).entries}
    for journey in FINDABLE_BY_KEYWORD:
        entry = entries[journey]
        assert entry.keywords, journey
        assert len(entry.question_examples) > 2, journey


def test_the_combined_order_story_names_the_prepayment_it_cannot_release() -> None:
    """Spec 294: R01 stays partial, and its limitation says why instead of claiming a release."""
    entry = next(
        item for item in load_journey_catalog(_payload()).entries if item.id == "R01"
    )
    assert entry.status == "partial"
    assert any("no reviewed release" in text for text in entry.limitations)
