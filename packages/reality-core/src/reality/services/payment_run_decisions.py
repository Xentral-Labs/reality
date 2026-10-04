"""Retained current review for the existing explicit-list supplier payment run."""

import json

from reality.domain.intake import canonical_json
from reality.services import core
from reality.services.payment_actions import _review_payment

REVIEW_KEY = "_payment_run_review"
_PUBLIC_FIELDS = {
    "payments",
    "currency",
    "expected_total",
    "reason",
    "effective_at",
    "actor_context",
}


def _reference_state(session, tenant_id, arguments):
    preview = core._preview_payment_run_input(
        session,
        tenant_id,
        payments=arguments["payments"],
        currency=arguments["currency"],
        expected_total=arguments["expected_total"],
        reason=arguments["reason"],
    )
    return [
        _review_payment(
            session,
            tenant_id,
            "supplier_payment_post",
            {
                "invoice_id": invoice_id,
                "amount": amount,
                "payment_number": number,
                "effective_at": arguments.get("effective_at"),
            },
        )
        for invoice_id, amount, number in preview["stated"]
    ]


def prepare_payment_run(session, tenant_id, arguments):
    from reality.services.intake import _INTENT_DEFAULTS

    if set(arguments) - _PUBLIC_FIELDS:
        raise core.InvalidOperation(code="intake_review_invalid")
    if not {"payments", "currency", "expected_total", "reason"} <= arguments.keys():
        raise core.InvalidOperation(
            "A payment run requires the selected payments, currency, total and reason."
        )
    defaults = {
        key: value
        for key, value in _INTENT_DEFAULTS["execute_payment_run"].items()
        if key in _PUBLIC_FIELDS
    }
    normalized = json.loads(canonical_json({**defaults, **arguments}))
    return {**normalized, REVIEW_KEY: _reference_state(session, tenant_id, normalized)}


def require_current_payment_run(session, tenant_id, intent):
    arguments = json.loads(intent)
    if REVIEW_KEY not in arguments:
        raise core.InvalidOperation(code="intake_review_invalid")
    try:
        current = _reference_state(session, tenant_id, arguments)
    except (core.InvalidOperation, core.NotFound) as error:
        raise core.InvalidOperation(code="intake_review_stale") from error
    if arguments[REVIEW_KEY] != current:
        raise core.InvalidOperation(code="intake_review_stale")
