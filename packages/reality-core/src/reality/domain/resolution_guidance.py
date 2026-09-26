"""Stable codes that explain a missing basis and the steps that resolve it (spec 279).

The catalog (`config/resolution_guidance.json`) holds the English wording, each step's
required role and the path through which a person acts. Services emit codes and step
states only; the web translates the wording. Nothing here is stored or authorizes an
action: every path ends in an existing form, the chat preview/confirmation flow, or a
decision review.
"""

from functools import lru_cache
from typing import Any

ROLES = frozenset({"member", "owner", "operator"})
PATHS = frozenset(
    {"web_form", "chat", "decision_review", "system_status", "page", "none"}
)
STATES = frozenset({"done", "open", "blocked"})
PAGES = frozenset({"data-sources", "finance", "decisions", "home"})

#: Every reason and step code a service can put into guidance. A new code needs a
#: catalog entry (and translations) before a service may emit it.
EMITTED_CODES = frozenset(
    {
        # Cost query stages.
        "cost_uninitialized",
        "cost_pending",
        "cost_stale",
        "cost_failed",
        "cost_complete",
        # Inventory and contribution missing basis (services/inventory_costing.py,
        # services/contribution.py, services/contribution_reviews.py,
        # services/selling_costs.py).
        "inventory_scope_not_reviewed",
        "inventory_review_stale",
        "commercial_match_not_reviewed",
        "contribution_profile_not_reviewed",
        "selling_costs_unknown",
        "selling_category",
        "contribution_review_stale",
        "received_net_missing",
        "billed_order_line_missing",
        "consumption_not_reviewed",
        "consumption_after_cutoff",
        "unsupported_revenue_type",
        "unsupported_order_scope",
        "corrected_fulfilment_unsupported",
        "negative_revenue_requires_match",
        "owner_scope_mismatch",
        "currency_scope_mismatch",
        "unit_scope_mismatch",
        "quantity_scope_mismatch",
        "ambiguous_billing",
        "ambiguous_fulfilment",
        "customer_scope_mismatch",
        "item_scope_mismatch",
        "revised_fulfilment_unsupported",
        "unsupported_fulfilment",
        # Commercial matching (services/commercial_matching.py).
        "commercial_goods_cost_unresolved",
        "commercial_inventory_cost_unknown",
        # Receipt cost missing basis (services/costing.py receipt_cost).
        "not_admitted",
        "no_attributed_cost",
        "scope_not_reviewed",
        "review_stale",
        "review_categories_incomplete",
        "category",
        "tax_basis_incomplete",
        "receipt_corrected",
        # Carrying value states (services/carrying_value.py).
        "assessment_missing",
        "assessment_not_supported",
        # Stored projections and their job failure codes.
        "projection_uninitialized",
        "projection_pending",
        "projection_failed",
        "handler_timeout",
        "handler_failed",
        "database_error",
        "child_exited",
        "outcome_unresolved",
        # Steps.
        "receipt_cost_evidence",
        "inventory_review",
        "inventory_review_renew",
        "contribution_review",
        "selling_cost_review",
        "owner_confirmation",
        "source_data_limit",
        "system_status",
    }
)


def catalog_key(code: str) -> str:
    """Map a parameterized code such as `selling_category:freight` to its entry."""
    return code.split(":", 1)[0]


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_action(where: str, entry: dict[str, Any], forms: set[str]) -> None:
    path = entry.get("path")
    if path not in PATHS:
        raise ValueError(f"{where}: unknown path {path!r}")
    if path == "web_form" and entry.get("form") not in forms:
        raise ValueError(f"{where}: unknown form {entry.get('form')!r}")
    if path == "chat" and "{scope}" not in str(entry.get("chat_prompt", "")):
        raise ValueError(f"{where}: a chat prompt must name its {{scope}}")
    if path == "page" and entry.get("page") not in PAGES:
        raise ValueError(f"{where}: unknown page {entry.get('page')!r}")


def validate_resolution_guidance(
    payload: dict[str, Any], *, forms: set[str]
) -> dict[str, Any]:
    """Reject incomplete wording, unknown roles/paths and dangling references."""
    reasons = payload.get("reasons")
    steps = payload.get("steps")
    blockers = payload.get("blockers")
    if not all(isinstance(part, dict) for part in (reasons, steps, blockers)):
        raise TypeError("Resolution guidance needs reasons, steps and blockers")
    for code, reason in reasons.items():
        if not _text(reason.get("label")) or not _text(reason.get("explanation")):
            raise ValueError(f"Reason {code} needs a label and an explanation")
    for code, step in steps.items():
        if not _text(step.get("label")):
            raise ValueError(f"Step {code} needs a label")
        if step.get("role") not in ROLES:
            raise ValueError(f"Step {code}: unknown role {step.get('role')!r}")
        _validate_action(f"Step {code}", step, forms)
        alternative = step.get("alternative")
        if alternative is not None:
            if not _text(alternative.get("label")):
                raise ValueError(f"Step {code}: alternative needs a label")
            _validate_action(f"Step {code} alternative", alternative, forms)
    for code, step in blockers.items():
        if code not in reasons or step not in steps:
            raise ValueError(f"Blocker {code} needs a reason and an existing step")
    return payload


@lru_cache(maxsize=1)
def _steps() -> dict[str, Any]:
    # Import lazily: the catalog loader validates against action discovery.
    from reality.catalogs import load_resolution_guidance

    return load_resolution_guidance()["steps"]


def guidance_step(
    code: str,
    state: str,
    *,
    targets: list[str] | tuple[str, ...] = (),
    target_count: int | None = None,
    proposal_id: str | None = None,
) -> dict[str, Any]:
    """Describe one step; role and path come from the catalog, never the caller."""
    if state not in STATES:
        raise ValueError(f"Unknown step state {state!r}")
    entry = _steps().get(code)
    if entry is None:
        raise ValueError(f"Unknown guidance step {code!r}")
    step: dict[str, Any] = {
        "code": code,
        "state": state,
        "role": entry["role"],
        "path": entry["path"],
        "targets": list(targets),
        "target_count": len(targets) if target_count is None else target_count,
    }
    if proposal_id is not None:
        step["proposal_id"] = proposal_id
    return step
