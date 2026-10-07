"""Consistent read assembly with fresh authority before and after observation."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from collections.abc import Callable
from concurrent.futures import Future
from threading import Lock

from sqlalchemy import func, select, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from reality.db.core import MCPAccessToken, now
from reality.db.mcp_authorization import MCPClientGrant
from reality.services import (
    activity_volume,
    core,
    operating_flows,
    operational_cases,
    shipping_performance,
)
from reality.services.memberships import Principal

_inflight: dict[tuple, Future] = {}
_inflight_lock = Lock()


def _inflight_read[Result](key: tuple, calculate: Callable[[], Result]) -> Result:
    """Join only a currently running exact read, never a completed observation.

    No authorization is shared. The caller validates access independently before
    joining and again after its own detached response copy. Remove the registry
    entry before waking waiters, including on failure; subsequent reads are fresh.
    Limit retained in-flight keys; distinct excess reads calculate independently.
    """
    with _inflight_lock:
        future = _inflight.get(key)
        leader = future is None
        if leader:
            if len(_inflight) >= 64:
                future = None
            else:
                future = Future()
                _inflight[key] = future
    if future is None:
        return calculate()
    if not leader:
        return json.loads(future.result())
    try:
        result = calculate()
        # These registered read responses are JSON DTOs. Encode once, then decode
        # independently for each observer instead of copying every nested node
        # in Python. No original ORM/input object crosses the snapshot boundary.
        encoded = json.dumps(result)
    except BaseException as error:
        with _inflight_lock:
            _inflight.pop(key, None)
        future.set_exception(error)
        raise
    with _inflight_lock:
        _inflight.pop(key, None)
    future.set_result(encoded)
    return json.loads(encoded)


def _observation_key(operation: str, filters: dict) -> tuple[str, str]:
    return operation, json.dumps(filters, sort_keys=True)


def enabled() -> bool:
    return os.environ.get("REALITY_OPERATIONS_COCKPIT_ENABLED", "").lower() in {
        "1",
        "true",
    }


def _viewer(session: Session, tenant_id: str, principal: Principal):
    with session.no_autoflush:
        return operational_cases._member(session, tenant_id, principal, _fresh=True)


def _with_snapshot[Result](
    session: Session,
    tenant_id: str,
    principal: Principal,
    read: Callable[[Session], Result],
    *,
    owner_only: bool = False,
    observation_key: tuple | None = None,
) -> Result:
    """
    BUSINESS PURPOSE:
    Observe a consistent company without retaining authority after access is revoked.

    BUSINESS RULE operations_cockpit.snapshot.access:
    Require a clean caller, current active company member and enabled surface.
    Configuration and a data snapshot grant no membership or business authority.

    BUSINESS RULE operations_cockpit.snapshot.consistency:
    Production Engine-bound observations use a fresh read-only REPEATABLE READ session
    and its own observation time. An explicitly caller-owned Connection keeps its
    transaction and the canonical source/version/watermark drift guards. Never
    commit, change isolation or discard pending work in the caller's transaction.
    Concurrent exact reads may join one currently running observation; every
    caller retains its own before/after authority checks. Completed results are
    never retained. Bind the key to this Engine, company, operation and filters.

    BUSINESS RULE operations_cockpit.snapshot.return:
    Release the observation transaction then recheck the caller's current company
    access. Unrelated business writes do not invalidate a consistent snapshot.
    """
    # reality-rule: operations_cockpit.snapshot.access
    if session.new or session.dirty or session.deleted:
        raise core.InvalidOperation(code="operations_cockpit_read_session_dirty")
    member = _viewer(session, tenant_id, principal)
    if owner_only and member.role != "owner":
        raise core.NotFound(code="company_not_found")
    if not enabled():
        raise core.NotFound(code="operations_cockpit_unavailable")
    # reality-rule: operations_cockpit.snapshot.consistency
    bind = session.get_bind()
    if isinstance(bind, Connection):
        with session.no_autoflush:
            result = read(session)
    else:

        def calculate():
            with Session(
                bind.execution_options(isolation_level="REPEATABLE READ"),
                autoflush=False,
                expire_on_commit=False,
            ) as snapshot:
                snapshot.execute(text("SET TRANSACTION READ ONLY"))
                snapshot.info["operations_snapshot_consistent"] = True
                snapshot.info["operations_snapshot_observed_at"] = snapshot.scalar(
                    select(func.now())
                )
                return read(snapshot)

        result = (
            _inflight_read((bind, tenant_id, owner_only, *observation_key), calculate)
            if observation_key is not None
            else calculate()
        )
    # reality-rule: operations_cockpit.snapshot.return
    member = _viewer(session, tenant_id, principal)
    if owner_only and member.role != "owner":
        raise core.NotFound(code="company_not_found")
    return result


def capabilities(session: Session, tenant_id: str, principal: Principal) -> dict:
    _viewer(session, tenant_id, principal)
    return {"enabled": enabled()}


def operations_cockpit(
    session: Session,
    tenant_id: str,
    principal: Principal,
    *,
    day: str = "today",
    location_id: str | None = None,
) -> dict:
    """
    BUSINESS PURPOSE:
    Assemble canonical shipping and company-wide operating flow observations.

    BUSINESS RULE operations_cockpit.overview.shared:
    Use current authorized snapshot assembly and shared shipping/operating-flow services.
    Case, activity and access panels retain their own canonical readers.
    """

    def read(snapshot):
        shipping, orders, terms = shipping_performance._read_shipping(
            snapshot,
            tenant_id,
            day=day,
            location_id=location_id,
            _deviations_only=True,
        )
        affected = [row for row in orders if row["at_risk"] or row["coverage_gaps"]]
        from reality.db.operational_cases import OperationalCase

        cases_by_order = {
            row.order_document_id: row.id
            for row in snapshot.scalars(
                select(OperationalCase).where(
                    OperationalCase.tenant_id == tenant_id,
                    OperationalCase.kind == "order_fulfillment",
                    OperationalCase.order_document_id.in_(
                        {row["order_id"] for row in affected[:50]}
                    ),
                )
            )
        }
        deviation_inputs = (
            operational_cases._explanation_inputs(
                snapshot, tenant_id, list(cases_by_order.values())
            )
            if cases_by_order and snapshot.info.get("operations_snapshot_consistent")
            else None
        )
        deviations = []
        for row in affected[:50]:
            case_id = cases_by_order.get(row["order_id"])
            explanation = (
                operational_cases.explain(
                    snapshot,
                    tenant_id,
                    case_id,
                    action_limit=50 if deviation_inputs else 6,
                    _terms=terms,
                    _inputs=deviation_inputs,
                )
                if case_id
                else None
            )
            actions = explanation["actions"][:6] if explanation else []
            deviations.append(
                {
                    **shipping_performance._json_value(row),
                    "case_id": case_id,
                    "responsibility": explanation["control_mode"]
                    if explanation
                    else "unsupported_or_unadopted",
                    "recorded_case_actions": actions,
                    "response_state": "recorded_case_actions"
                    if actions
                    else "no_recorded_response",
                    "response_scope": "case_linked_no_causal_assertion",
                    "next_recorded_check": None,
                }
            )
        return {
            "observed_at": shipping["observed_at"],
            "shipping": shipping,
            "deviations": deviations,
            "deviation_total": len(affected)
            if shipping["coverage"]["cohort"] == "complete"
            else None,
            "deviations_has_more": len(affected) > 50,
        }

    # reality-rule: operations_cockpit.overview.shared
    return _with_snapshot(
        session,
        tenant_id,
        principal,
        read,
        observation_key=_observation_key(
            "overview", {"day": day, "location_id": location_id}
        ),
    )


def supporting_orders(
    session: Session, tenant_id: str, principal: Principal, **filters
) -> dict:
    """
    BUSINESS PURPOSE:
    Read the exact current orders behind a shipping measure without changing work.

    BUSINESS RULE operations_cockpit.orders.shared:
    Use the same authorized snapshot and complete shared shipping-order reader.
    """
    # reality-rule: operations_cockpit.orders.shared
    return _with_snapshot(
        session,
        tenant_id,
        principal,
        lambda snapshot: shipping_performance.shipping_supporting_orders(
            snapshot, tenant_id, **filters
        ),
        observation_key=_observation_key("orders", filters),
    )


def case_register(
    session: Session, tenant_id: str, principal: Principal, **filters
) -> dict:
    """
    BUSINESS PURPOSE:
    Observe exact supported case responsibility through the same current snapshot.

    BUSINESS RULE operations_cockpit.case_register.shared:
    Membership and feature discovery never adopt work. Use the canonical complete
    case register and preserve current post-read access checks. Return this read's
    own observation time even when no work is adopted; it is transient metadata.
    """
    # reality-rule: operations_cockpit.case_register.shared
    return _with_snapshot(
        session,
        tenant_id,
        principal,
        lambda snapshot: {
            **operational_cases.register_cases(snapshot, tenant_id, **filters),
            "observed_at": (
                snapshot.info.get("operations_snapshot_observed_at") or now()
            ).isoformat(),
        },
        observation_key=_observation_key("register", filters),
    )


def activity(
    session: Session, tenant_id: str, principal: Principal, *, minutes: int = 15
) -> dict:
    """
    BUSINESS PURPOSE:
    Show the company's recorded business activity alongside daily shipping results.

    BUSINESS RULE operations_cockpit.activity.shared:
    Authorize a fresh read-only snapshot and reuse canonical recorded-entity activity.
    This company-wide window is independent of shipping site or historical day.
    """
    # reality-rule: operations_cockpit.activity.shared
    return _with_snapshot(
        session,
        tenant_id,
        principal,
        lambda snapshot: {
            **activity_volume.rolling(snapshot, tenant_id, minutes=minutes),
            "flows": operating_flows.observe(snapshot, tenant_id),
        },
        observation_key=_observation_key("activity", {"minutes": minutes}),
    )


def _cursor_scope(tenant_id: str, filters: dict) -> str:
    return hashlib.sha256(
        json.dumps({"tenant": tenant_id, **filters}, sort_keys=True).encode()
    ).hexdigest()


def _cursor_read(value: str, scope: str) -> str:
    if not value:
        return ""
    try:
        if not isinstance(value, str) or len(value) > 4096:
            raise ValueError
        decoded = json.loads(base64.b64decode(value, altchars=b"-_", validate=True))
        if (
            set(decoded) != {"scope", "after"}
            or decoded["scope"] != scope
            or not isinstance(decoded["after"], str)
        ):
            raise ValueError
        return decoded["after"]
    except (ValueError, TypeError, KeyError) as error:
        raise core.InvalidOperation(
            code="shipping_observation_cursor_invalid"
        ) from error


def _cursor_write(scope: str, after: str) -> str:
    return base64.urlsafe_b64encode(
        json.dumps({"scope": scope, "after": after}).encode()
    ).decode()


def _access_inventory(
    session: Session, tenant_id: str, *, access_state: str, after: str, limit: int
) -> dict:
    from reality.services import interactions, mcp_authorization
    from reality.services.tenant_policy import (
        PlaygroundOperationDenied,
        require_business_operation,
    )

    if (
        type(limit) is not int
        or not 1 <= limit <= 50
        or access_state not in {"active", "inactive", "revoked", "all"}
    ):
        raise core.InvalidOperation(code="shipping_observation_filter_invalid")
    scope = _cursor_scope(tenant_id, {"access_state": access_state})
    cursor = _cursor_read(after, scope)
    try:
        require_business_operation(session, tenant_id, "mcp_token_use")
    except (core.NotFound, PlaygroundOperationDenied):
        manual_ready = False
    else:
        manual_ready = True
    rows = []
    for token in session.scalars(
        select(MCPAccessToken).where(MCPAccessToken.tenant_id == tenant_id)
    ):
        state = (
            "revoked" if token.revoked_at else "active" if manual_ready else "inactive"
        )
        rows.append(
            {
                "identity": "manual:" + token.id,
                "name": token.name,
                "connection_kind": "manual",
                "access_state": state,
                "access_reason": "revoked"
                if token.revoked_at
                else None
                if manual_ready
                else "company_not_ready",
                "last_used_at": token.last_used_at.isoformat()
                if token.last_used_at
                else None,
                "runtime_state": "unknown",
                "observed_action": None,
                "permitted_tools": json.loads(token.allowed_tools),
            }
        )
    for grant in session.scalars(
        select(MCPClientGrant).where(MCPClientGrant.tenant_id == tenant_id)
    ):
        view = mcp_authorization._grant_view(session, grant, include_user=False)
        rows.append(
            {
                "identity": "oauth:" + grant.id,
                "name": grant.client_name,
                "connection_kind": "oauth",
                "access_state": view["effective_state"],
                "access_reason": view["effective_reason"],
                "last_used_at": view["last_used_at"],
                "runtime_state": "unknown",
                "observed_action": None,
                "permitted_tools": list(grant.allowed_tools),
            }
        )
    matched = sorted(
        (
            row
            for row in rows
            if access_state == "all" or row["access_state"] == access_state
        ),
        key=lambda row: row["identity"],
    )
    selected = [row for row in matched if row["identity"] > cursor][: limit + 1]
    has_more = len(selected) > limit
    selected = selected[:limit]
    manual_ids = [
        row["identity"].removeprefix("manual:")
        for row in selected
        if row["connection_kind"] == "manual"
    ]
    actions = interactions.latest_manual_actions(session, tenant_id, manual_ids)
    for row in selected:
        if row["connection_kind"] == "manual":
            row["observed_action"] = actions.get(
                row["identity"].removeprefix("manual:")
            )
    return {
        "observed_at": (
            session.info.get("operations_snapshot_observed_at") or now()
        ).isoformat(),
        "coverage": {
            "manual": "available",
            "oauth": "available",
            "runtime": "unavailable",
            "oauth_action_attribution": "unavailable",
        },
        "scope": access_state,
        "total": len(matched),
        "items": selected,
        "has_more": has_more,
        "next_after": _cursor_write(scope, selected[-1]["identity"])
        if has_more
        else None,
    }


def agents(
    session: Session,
    tenant_id: str,
    principal: Principal,
    *,
    access_state: str = "active",
    after: str = "",
    limit: int = 6,
) -> dict:
    """
    BUSINESS PURPOSE:
    Explain the named accesses authorized for this company without inventing Agents.

    BUSINESS RULE operations_cockpit.agents.authorization:
    Require current owner access before and after a read-only snapshot. Configuration
    and recent requests never establish connected or working external processes.

    BUSINESS RULE operations_cockpit.agents.evidence:
    Count the full effective-access cohort before bounded paging. Redact credentials
    and personal profiles. Only an exact recorded manual credential establishes
    interaction attribution; user/client names never establish an OAuth grant match.
    """
    # reality-rule: operations_cockpit.agents.evidence
    read = lambda snapshot: _access_inventory(
        snapshot, tenant_id, access_state=access_state, after=after, limit=limit
    )
    # reality-rule: operations_cockpit.agents.authorization
    return _with_snapshot(
        session,
        tenant_id,
        principal,
        read,
        owner_only=True,
        observation_key=_observation_key(
            "agents", {"access_state": access_state, "after": after, "limit": limit}
        ),
    )
