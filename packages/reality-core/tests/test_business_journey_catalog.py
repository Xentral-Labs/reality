from __future__ import annotations

import copy

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
