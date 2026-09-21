from conftest import record_by_id, seed_company

from reality.db.core import PlaygroundRun
from reality.services import company_setup


def test_story_manifest_has_exact_references_results_and_ui_paths(
    session, scheduled_owner
):
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "b2b-catalog",
        "Harbor Supply B2B Catalog",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    seed_company(session, result["tenant_id"])
    run = record_by_id(session, PlaygroundRun, result["run_id"])
    cases = run.initialization_progress["cases"]

    for key in ("b2b_supply_chain", "b2b_return_disposition"):
        case = cases[key]
        assert case["sales_order_number"].startswith("SO-")
        paths = [value for name, value in case.items() if name.endswith("_ui_path")]
        assert paths
        assert all("→" in path for path in paths)
    assert cases["b2b_supply_chain"]["purchase_order_number"] == "PO-010"
    assert cases["b2b_return_disposition"]["unresolved"] == "0"
