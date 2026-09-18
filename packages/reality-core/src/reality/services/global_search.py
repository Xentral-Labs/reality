"""Read-only company search and reference resolution through shared access policy."""

import base64
import hashlib
import json

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from reality.db.core import PartyRole, PlaygroundRun
from reality.db.search import candidate_query, page_query
from reality.domain.search import (
    RecordTarget,
    SearchHit,
    SearchPage,
    SearchRequest,
)
from reality.services.core import NotFound, get_tenant
from reality.services.delivery_actions import require_delivery_principal
from reality.services.memberships import Principal

SORT_FIELDS = (
    "tier",
    "context_order",
    "recent_order",
    "family_order",
    "normalized_label",
    "kind",
    "id",
)
LESSON_KINDS = {
    "party",
    "item",
    "location",
    "document",
    "commitment",
    "reservation",
    "movement",
    "fact",
    "shipment",
}


def _access(session, tenant_id, principal):
    tenant = get_tenant(session, tenant_id)
    if tenant.purpose != "playground":
        require_delivery_principal(session, tenant_id, principal)
        return None
    from reality.services.tenant_policy import (
        practice_company_runs,
        require_playground_run,
    )

    if principal is None:
        raise NotFound("Company not found.")
    run_id = session.scalar(
        select(PlaygroundRun.id).where(
            PlaygroundRun.tenant_id == tenant_id,
            PlaygroundRun.owner_user_id == principal.user_id,
        )
    )
    if run_id is None:
        raise NotFound("Company not found.")
    run = require_playground_run(session, run_id, principal.user_id)
    if run.status not in {"active", "archived"}:
        raise NotFound("Company not found.")
    return (
        None
        if tenant_id in practice_company_runs(session, principal.user_id)
        else LESSON_KINDS
    )


def _scope(tenant_id, principal, request, session_scope=""):
    values = request.model_dump(exclude={"cursor", "limit"})
    values.update(
        tenant=tenant_id,
        actor=principal.user_id if principal else "trusted-local",
        session_scope=session_scope,
    )
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def _decode(cursor, scope):
    try:
        value = json.loads(base64.urlsafe_b64decode(cursor))
        if value["scope"] != scope or len(value["after"]) != 7:
            raise ValueError
        if any(type(x) is not int for x in value["after"][:4]) or any(
            not isinstance(x, str) for x in value["after"][4:]
        ):
            raise ValueError
        return tuple(value["after"])
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise ValueError("Invalid search continuation.") from exc


def _hits(session, tenant_id, request, rows):
    party_ids = [row["id"] for row in rows if row["kind"] == "party"]
    roles = {}
    if party_ids:
        for party_id, role in session.execute(
            select(PartyRole.party_id, PartyRole.role)
            .where(PartyRole.tenant_id == tenant_id, PartyRole.party_id.in_(party_ids))
            .order_by(PartyRole.role)
        ):
            roles.setdefault(party_id, []).append(role)
    return [
        SearchHit(
            key=f"{row['kind']}:{row['id']}",
            family=row["family"],
            group=request.provider,
            label=row["label"],
            secondary=row["secondary"],
            roles=roles.get(row["id"], []),
            tier=row["tier"],
            sort_key=tuple(row[field] for field in SORT_FIELDS),
            target=RecordTarget(
                kind="saved_report" if row["kind"] == "analytics_report" else "record",
                record_kind="payment" if row["family"] == "payment" else row["kind"],
                id=row["id"],
            ),
        )
        for row in rows
    ]


def search_company(
    session: Session,
    tenant_id: str,
    principal: Principal | None,
    request: SearchRequest,
    *,
    session_scope: str = "",
) -> SearchPage:
    """No flush, writes or truncated candidate pool; private reports need an owner."""
    with session.no_autoflush:
        allowed = _access(session, tenant_id, principal)
        scope = _scope(tenant_id, principal, request, session_scope)
        empty = SearchPage(
            items=[], has_more=False, provider=request.provider, scope=scope
        )
        owner_id = None
        if request.provider == "reports":
            from reality.services.analytics.reports import require_author

            owner_id = require_author(session, tenant_id, principal)
        if not request.query.strip():
            return empty
        candidates = candidate_query(
            tenant_id, owner_id, request, allowed_kinds=allowed
        )
        if candidates is None:
            return empty
        after = _decode(request.cursor, scope) if request.cursor else None
        # Bind continuation to an actual currently authorized result, not client sort claims.
        if after is not None:
            anchor = (
                session.execute(
                    select(candidates).where(
                        candidates.c.kind == after[-2], candidates.c.id == after[-1]
                    )
                )
                .mappings()
                .one_or_none()
            )
            if anchor is None or tuple(anchor[field] for field in SORT_FIELDS) != after:
                raise ValueError("Search results changed. Refresh the search.")
        # A connection savepoint does not flush pending ORM changes (Session.begin_nested does).
        # It also restores the caller's timeout and transaction after cancellation.
        with session.connection().begin_nested():
            previous = session.scalar(text("SHOW statement_timeout"))
            session.execute(
                text("SELECT set_config('statement_timeout', '1200ms', true)")
            )
            rows = []
            for tier in range(after[0] if after else 0, 4):
                remaining = request.limit + 1 - len(rows)
                tier_candidates = candidate_query(
                    tenant_id,
                    owner_id,
                    request,
                    allowed_kinds=allowed,
                    tier_filter=tier,
                    branch_limit=remaining,
                    branch_after=after,
                )
                rows.extend(
                    session.execute(
                        page_query(tier_candidates, remaining - 1, after)
                    ).mappings()
                )
                if len(rows) >= request.limit + 1:
                    break
            session.execute(
                text("SELECT set_config('statement_timeout', :value, true)"),
                {"value": previous},
            )
        has_more = len(rows) > request.limit
        hits = _hits(session, tenant_id, request, rows[: request.limit])
        cursor = (
            base64.urlsafe_b64encode(
                json.dumps({"scope": scope, "after": hits[-1].sort_key}).encode()
            ).decode()
            if has_more
            else None
        )
        return SearchPage(
            items=hits,
            has_more=has_more,
            next_cursor=cursor,
            provider=request.provider,
            scope=scope,
        )


def resolve_search_targets(
    session: Session,
    tenant_id: str,
    principal: Principal | None,
    references: list[RecordTarget],
) -> list[SearchHit]:
    if len(references) > 40:
        raise ValueError("Too many search references.")
    result = {}
    with session.no_autoflush:
        allowed = _access(session, tenant_id, principal)
        for target in references:
            physical = {"payment": "ledger_entry"}.get(
                target.record_kind, target.record_kind
            )
            providers = {
                "party": ["partners"],
                "item": ["items_locations"],
                "location": ["items_locations"],
                "document": ["orders", "finance", "reality"],
                "shipment": ["shipping"],
                "analytics_report": ["reports"],
                "ledger_entry": ["finance", "reality"],
            }.get(physical, ["reality"])
            for provider in providers:
                owner_id = None
                if provider == "reports":
                    from reality.services.analytics.reports import require_author

                    owner_id = require_author(session, tenant_id, principal)
                request = SearchRequest(provider=provider, query=target.id, limit=1)
                candidates = candidate_query(
                    tenant_id,
                    owner_id,
                    request,
                    allowed_kinds=allowed,
                    identity=(physical, target.id),
                )
                if candidates is None:
                    continue
                rows = list(session.execute(page_query(candidates, 1)).mappings())
                for hit in _hits(session, tenant_id, request, rows):
                    result[hit.key] = hit
    return list(result.values())
