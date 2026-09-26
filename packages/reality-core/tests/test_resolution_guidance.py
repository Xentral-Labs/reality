"""The resolution guidance catalog names every code a service can show (spec 279)."""

import copy
import json
import re
from pathlib import Path

import pytest

from reality.catalogs import load_application_catalog, load_resolution_guidance
from reality.config import config_text
from reality.domain.resolution_guidance import (
    EMITTED_CODES,
    catalog_key,
    guidance_step,
    validate_resolution_guidance,
)

FORMS = {
    "supplier_invoice_record",
    "sales_invoice_record",
    "receipt",
    "reserve",
    "commitment_hold_release",
    "party_delivery_hold_release",
}


def raw_catalog() -> dict:
    return json.loads(config_text("resolution_guidance.json"))


def test_shipped_catalog_validates_and_covers_every_emitted_code():
    catalog = load_resolution_guidance()
    known = set(catalog["reasons"]) | set(catalog["steps"])
    assert EMITTED_CODES <= known, sorted(EMITTED_CODES - known)


def test_catalog_is_served_with_the_application_catalog():
    served = load_application_catalog()["resolution_guidance"]
    assert served == load_resolution_guidance()
    classes = load_application_catalog()["operational_exception_guidance"]
    assert all(entry["label"] and entry["clears_through"] for entry in classes)
    assert {entry["id"] for entry in classes} >= {"missing_acquisition_cost"}


@pytest.mark.parametrize(
    "break_catalog",
    [
        lambda c: c["steps"]["record_receipt"].update(form="no_such_form"),
        lambda c: c["steps"]["inventory_review"].update(role="admin"),
        lambda c: c["steps"]["inventory_review"].update(path="email"),
        lambda c: c["steps"]["inventory_review"].update(chat_prompt="No scope here."),
        lambda c: c["steps"]["receipt_cost_evidence"]["alternative"].update(
            form="no_such_form"
        ),
        lambda c: c["blockers"].update(insufficient_stock="no_such_step"),
        lambda c: c["reasons"]["cost_stale"].update(label=""),
        lambda c: c["steps"]["review_open_items"].pop("page"),
    ],
)
def test_invalid_catalog_entries_are_rejected(break_catalog):
    # Positive control: the unmodified catalog passes the same validation.
    validate_resolution_guidance(raw_catalog(), forms=FORMS)
    broken = copy.deepcopy(raw_catalog())
    break_catalog(broken)
    with pytest.raises(ValueError):
        validate_resolution_guidance(broken, forms=FORMS)


def test_prefixed_codes_share_one_catalog_entry():
    assert catalog_key("selling_category:outbound_freight") == "selling_category"
    assert catalog_key("category:goods") == "category"
    assert catalog_key("inventory_scope_not_reviewed") == "inventory_scope_not_reviewed"


def test_step_carries_catalog_role_and_path():
    step = guidance_step("owner_confirmation", "open", proposal_id="act_1")
    assert step == {
        "code": "owner_confirmation",
        "state": "open",
        "role": "owner",
        "path": "decision_review",
        "targets": [],
        "target_count": 0,
        "proposal_id": "act_1",
    }
    with pytest.raises(ValueError):
        guidance_step("owner_confirmation", "maybe")
    with pytest.raises(ValueError):
        guidance_step("not_a_step", "open")


def test_every_gap_a_service_emits_is_listed():
    """Found live (2026-09-26): `ambiguous_fulfilment` reached the web uncatalogued.

    Read the codes straight from the services that produce missing-basis gaps, so a new
    gap cannot bypass `EMITTED_CODES` and fall back to the generic sentence unnoticed.
    """
    services = Path(__file__).resolve().parents[1] / "src" / "reality" / "services"
    patterns = {
        "contribution.py": r'gap\("([a-z_]+)"\)',
        "costing.py": r'missing\.add\("([a-z_]+):?"',
        "commercial_matching.py": r'missing\.append\("([a-z_]+)"',
        "selling_costs.py": r'"(selling_costs_unknown|selling_category):?',
        "inventory_costing.py": r'"missing_basis": \["([a-z_]+)"\]',
        "contribution_reviews.py": r'"(contribution_review_stale|commercial_match_not_reviewed)"',
    }
    found = set()
    for name, pattern in patterns.items():
        codes = set(re.findall(pattern, (services / name).read_text()))
        # Positive control: each pattern still matches something in its file.
        assert codes, f"{name}: the pattern no longer finds any gap"
        found |= codes
    assert found - EMITTED_CODES == set(), sorted(found - EMITTED_CODES)
