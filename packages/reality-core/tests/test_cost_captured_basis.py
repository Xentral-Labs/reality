"""One captured review vector, with honest independent coverage and no publication."""

from copy import deepcopy

import pytest
import test_cost_census_resolution as resolution
import test_cost_census_storage as storage
from test_cost_census import read_session, seed

from reality.services import core, costing

scheduled_database = storage.scheduled_database


def example():
    context = {
        "id": "capture",
        "tenant_id": "tenant",
        "content_hash": "a" * 64,
        "effective_at": "2026-09-18T00:00:00+00:00",
        "observed_at": "2026-09-19T00:00:00+00:00",
        "snapshot_identity": "10:20:",
        "event_sequence": 3,
    }
    stock = {
        "item_id": "item",
        "review_id": "inventory-review",
        "review_content_hash": "b" * 64,
        "state": "available_at_capture",
        "gaps": [],
        "freshness_proof": {"unchanged": True, "checked_review_event_ids": ["event"]},
        "result": {
            "item_id": "item",
            "review_id": "inventory-review",
            "policy_id": "policy",
            "knowledge_at": "2026-09-17T00:00:00+00:00",
            "acquisition_value": "0.0000",
            "carrying_value": None,
            "carrying_value_state": "assessment_not_supported",
        },
    }
    stock["basis_result"] = deepcopy(stock["result"])
    sale = {
        "document_line_id": "line",
        "review_id": "sale-review",
        "review_content_hash": "c" * 64,
        "state": "available_at_capture",
        "gaps": [],
        "result": {
            "document_line_id": "line",
            "review_id": "sale-review",
            "profile_revision_id": "sale-review",
            "profile": "commercial_v1",
            "knowledge_at": "2026-09-18T00:00:00+00:00",
            "db1": "0.0000",
            "db2": None,
            "missing_basis": ["selling_costs_unknown"],
            "trace": {"inventory_review_id": "inventory-review"},
        },
    }
    sale["basis_result"] = deepcopy(sale["result"])
    result = {
        "census_id": "capture",
        "tenant_id": "tenant",
        "event_sequence": 3,
        "effective_at": context["effective_at"],
        "inventory": [stock],
        "contribution": [sale],
        "document_gaps": [],
        "source_gaps": [],
    }
    return context, result


def assemble(context, result, inventory=("item",), contribution=("line",)):
    from reality.domain.cost_captured_basis import assemble_captured_basis

    return assemble_captured_basis(context, result, inventory, contribution)


def test_zero_is_covered_unknown_is_not_and_knowledge_remains_per_review():
    context, result = example()
    basis = assemble(context, result)
    assert basis["coverage"]["acquisition"] == {
        "expected": 1,
        "covered": 1,
        "unknown": 0,
        "state": "complete",
    }
    assert basis["coverage"]["carrying"]["covered"] == 0
    assert basis["coverage"]["db1"]["covered"] == 1
    assert basis["coverage"]["db2"]["unknown"] == 1
    assert (
        basis["inventory"][0]["knowledge_at"]
        != basis["contribution"][0]["knowledge_at"]
    )
    assert "knowledge_at" not in basis["context"]
    assert basis["retained"] is basis["publication_eligible"] is False
    assert "totals" not in basis
    assert basis["coverage_scope"] == "captured_subjects_and_candidates"


@pytest.mark.parametrize(
    "family,key", [("inventory", "item_id"), ("contribution", "document_line_id")]
)
@pytest.mark.parametrize("fault", ["missing", "duplicate", "extra", "substituted"])
def test_exact_membership_required(family, key, fault):
    context, result = example()
    if fault == "missing":
        result[family] = []
    elif fault == "duplicate":
        result[family].append(deepcopy(result[family][0]))
    elif fault == "extra":
        row = deepcopy(result[family][0])
        row[key] = "extra"
        result[family].append(row)
    else:
        result[family][0][key] = "substituted"
    with pytest.raises(ValueError, match="Captured basis"):
        assemble(context, result)


@pytest.mark.parametrize(
    "field,value",
    [
        ("tenant_id", "foreign"),
        ("census_id", "other"),
        ("event_sequence", 4),
        ("effective_at", "2026-09-20T00:00:00+00:00"),
    ],
)
def test_mixed_context_refuses(field, value):
    context, result = example()
    result[field] = value
    with pytest.raises(ValueError, match="Captured basis"):
        assemble(context, result)


def test_empty_and_historical_only_coverage_do_not_invent_zero():
    context, result = example()
    for family in ("inventory", "contribution"):
        result[family][0].update(
            state="unknown_at_capture", result=None, gaps=["changed"]
        )
    basis = assemble(context, result)
    assert all(value["covered"] == 0 for value in basis["coverage"].values())
    assert basis["inventory"][0]["review_id"] == "inventory-review"
    result.update(inventory=[], contribution=[])
    empty = assemble(context, result, (), ())
    assert all(value["state"] == "empty" for value in empty["coverage"].values())


def test_order_independent_digest_binds_context_result_proof_and_gaps():
    context, result = example()
    row = deepcopy(result["inventory"][0])
    row["item_id"] = "second"
    row["result"]["item_id"] = row["basis_result"]["item_id"] = "second"
    result["inventory"].append(row)
    original = assemble(context, result, ("item", "second"))
    result["inventory"].reverse()
    assert assemble(context, result, ("second", "item")) == original
    for mutate in (
        lambda c, r: c.update(content_hash="d" * 64),
        lambda c, r: r["inventory"][0]["result"].update(acquisition_value="1.0000"),
        lambda c, r: r["inventory"][0]["freshness_proof"].update(
            checked_review_event_ids=["different"]
        ),
        lambda c, r: r["source_gaps"].append(
            {"source_record_id": "source", "classification": "unresolved"}
        ),
    ):
        ctx, value = deepcopy(context), deepcopy(result)
        mutate(ctx, value)
        assert assemble(ctx, value, ("item", "second"))["digest"] != original["digest"]


def test_result_identity_and_support_consistency_refuse():
    context, result = example()
    result["inventory"][0]["result"]["review_id"] = "wrong"
    with pytest.raises(ValueError, match="Captured basis"):
        assemble(context, result)
    context, result = example()
    result["contribution"][0]["result"].update(db1=None, db2="1")
    with pytest.raises(ValueError, match="Captured basis"):
        assemble(context, result)


def test_real_goods_basis_stays_stable_after_later_events(scheduled_database):
    factory, business, _, cutoff, _ = resolution.setup_review(
        scheduled_database, contribution=True
    )
    tenant = business.tenant.id
    census = resolution.capture(factory, tenant, cutoff)
    with read_session(factory) as session:
        before = costing.resolve_company_cost_census(session, tenant, census)[
            "captured_basis"
        ]
    assert before["coverage"]["acquisition"]["covered"] == 1
    assert before["coverage"]["db1"]["covered"] == 1
    assert before["coverage"]["db2"]["covered"] == 0
    with factory() as session:
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    later = resolution.capture(factory, tenant, cutoff, "later")
    with read_session(factory) as session:
        assert (
            costing.resolve_company_cost_census(session, tenant, census)[
                "captured_basis"
            ]
            == before
        )
        changed = costing.resolve_company_cost_census(session, tenant, later)[
            "captured_basis"
        ]
    assert changed["digest"] != before["digest"]
    assert all(row["covered"] == 0 for row in changed["coverage"].values())


def test_unreviewed_candidates_and_capture_gaps_are_bound(scheduled_database):
    data = seed(scheduled_database)
    factory, tenant, *_ = data
    census = storage.retain(data)
    with read_session(factory) as session:
        basis = costing.resolve_company_cost_census(session, tenant, census["id"])[
            "captured_basis"
        ]
    assert basis["context"]["census_content_hash"] == census["content_hash"]
    assert basis["gaps"]["documents"] and basis["gaps"]["sources"]
    assert all(
        row["expected"] == row["unknown"] == 1 for row in basis["coverage"].values()
    )


def test_partial_coverage_keeps_unreviewed_members_and_external_gaps():
    context, result = example()
    result["inventory"].append(
        {
            "item_id": "unreviewed",
            "review_id": None,
            "review_content_hash": None,
            "state": "unknown_at_capture",
            "result": None,
            "basis_result": None,
            "gaps": ["inventory_scope_not_reviewed"],
        }
    )
    result["document_gaps"] = [
        {"document_id": "header", "reason": "document_lines_missing"}
    ]
    basis = assemble(context, result, ("item", "unreviewed"))
    assert basis["coverage"]["acquisition"] == {
        "expected": 2,
        "covered": 1,
        "unknown": 1,
        "state": "partial",
    }
    assert basis["coverage"]["db1"]["state"] == "complete"
    assert basis["gaps"]["documents"] == result["document_gaps"]
    assert basis["publication_eligible"] is False
    with pytest.raises(ValueError, match="Captured basis"):
        assemble(context, result, ("item", "unreviewed", "unreviewed"))


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "bad", 0.0, True])
def test_invalid_amount_cannot_count_as_covered(amount):
    context, result = example()
    result["inventory"][0]["result"]["acquisition_value"] = amount
    with pytest.raises(ValueError, match="Captured basis"):
        assemble(context, result)
