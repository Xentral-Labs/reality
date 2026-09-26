"""Shapes of a drafted cost review (spec 282).

A draft describes the review that held records support for one scope: complete
`cost.change` arguments, or the open inputs a person still has to decide or state. It is
derived at read time, never stored, and authorizes nothing; the proposal and the owner's
confirmation stay on the existing path.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DraftKind = Literal["inventory", "contribution"]

#: Open inputs a draft may name. Each has catalog wording in resolution_guidance.json.
OPEN_INPUT_CODES = frozenset(
    {
        "valuation_method",
        "company_party_missing",
        "receipt_cost_incomplete",
        "opening_cost_missing",
        "movement_unclassified",
        "ownership_ambiguous",
        "return_portion_undetermined",
        "review_bound_exceeded",
        "upstream_not_ready",
        "currency_ambiguous",
    }
)

#: Proposal reason the draft supplies; the proposer may edit it.
DRAFT_REASON = "Prepared from held evidence through the cost review draft."


class DraftAnswers(BaseModel):
    """What a person decided for the open inputs; nothing else is accepted."""

    model_config = ConfigDict(extra="forbid")
    method: Literal["fifo", "specific"] | None = None
    owner_party_id: str | None = Field(default=None, min_length=1)


class CostReviewDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: DraftKind
    scope_id: str = Field(min_length=1)
    answers: DraftAnswers | None = None


def method_choices(tracking_type: str | None) -> list[str]:
    """FIFO always; specific selection only where items carry a serial or lot identity."""
    return ["fifo", "specific"] if tracking_type in {"serial", "lot"} else ["fifo"]


def open_input(
    code: str,
    *,
    subject: dict[str, str] | None = None,
    reason: str | None = None,
    choices: list[str] | None = None,
    default: str | None = None,
) -> dict[str, Any]:
    """One thing a person must decide or state before the review can be proposed."""
    if code not in OPEN_INPUT_CODES:
        raise ValueError(f"Unknown open input {code!r}")
    entry: dict[str, Any] = {"code": code}
    if subject is not None:
        entry["subject"] = subject
    if reason is not None:
        entry["reason"] = reason
    if choices is not None:
        entry["choices"] = choices
    if default is not None:
        entry["default"] = default
    return entry


def draft(
    *,
    kind: DraftKind,
    scope_id: str,
    event_sequence: int,
    arguments: dict[str, Any] | None,
    open_inputs: list[dict[str, Any]],
    basis: list[dict[str, str]],
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Arguments are complete only when nothing remains open.

    `summary` holds held or previewed business values for people to read; it is never
    part of the proposal.
    """
    return {
        "summary": summary or {},
        "kind": kind,
        "scope_id": scope_id,
        "event_sequence": event_sequence,
        "arguments": None if open_inputs else arguments,
        "partial_arguments": arguments if open_inputs else None,
        "open_inputs": open_inputs,
        "basis": basis,
        "persistence": {"business_writes": False, "projection_writes": False},
    }
