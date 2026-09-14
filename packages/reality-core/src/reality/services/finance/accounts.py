"""Managed operational accounts and one transaction lock for finance mutations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from reality.db.core import FinanceRoleDestination, FinanceState, SubledgerAccount, uid
from reality.domain.finance import ACCOUNT_ROLES, BASE_ACCOUNT_ROLES


def lock_finance(session: Session, tenant_id: str) -> FinanceState:
    from reality.services.business_locks import lock_delivery_state

    lock_delivery_state(session, tenant_id)
    session.execute(
        insert(FinanceState)
        .values(id=uid("fin"), tenant_id=tenant_id, revision=0)
        .on_conflict_do_nothing(index_elements=["tenant_id"])
    )
    state = session.scalar(
        select(FinanceState)
        .where(FinanceState.tenant_id == tenant_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return state


def _mutation(
    session: Session, tenant_id: str, expected_revision: int | None = None
) -> FinanceState:
    from reality.services.core import Conflict, _require_business_mutation

    _require_business_mutation(session, tenant_id, "finance_account_maintain")
    state = lock_finance(session, tenant_id)
    if expected_revision is not None and state.revision != expected_revision:
        raise Conflict("Finance preview is stale; reload and confirm again.")
    return state


def _get(session: Session, tenant_id: str, account_id: str) -> SubledgerAccount:
    from reality.services.core import NotFound

    account = session.scalar(
        select(SubledgerAccount)
        .where(
            SubledgerAccount.tenant_id == tenant_id, SubledgerAccount.id == account_id
        )
        .execution_options(populate_existing=True)
    )
    if account is None:
        raise NotFound("SubledgerAccount not found.")
    return account


def _result(account: SubledgerAccount) -> dict[str, Any]:
    return {
        key: getattr(account, key)
        for key in ("id", "code", "name", "role", "state", "revision")
    }


def list_accounts(session: Session, tenant_id: str) -> dict:
    from reality.services.core import get_tenant

    get_tenant(session, tenant_id)
    state = session.scalar(
        select(FinanceState).where(FinanceState.tenant_id == tenant_id)
    )
    defaults = {
        r.role: r.account_id
        for r in session.scalars(
            select(FinanceRoleDestination).where(
                FinanceRoleDestination.tenant_id == tenant_id
            )
        )
    }
    return {
        "revision": state.revision if state else 0,
        "roles": ACCOUNT_ROLES,
        "defaults": defaults,
        "accounts": [
            _result(a)
            for a in session.scalars(
                select(SubledgerAccount)
                .where(SubledgerAccount.tenant_id == tenant_id)
                .order_by(SubledgerAccount.code, SubledgerAccount.id)
            )
        ],
    }


def _audit(
    session: Session,
    tenant_id: str,
    state: FinanceState,
    account: SubledgerAccount,
    operation: str,
    action_id: str | None,
) -> None:
    from reality.services.core import emit_business_event

    state.revision += 1
    emit_business_event(
        session,
        tenant_id,
        "finance.account_changed",
        "subledger_account",
        account.id,
        {"operation": operation, **_result(account)},
        action_id=action_id,
    )
    session.flush()


def create_account(
    session: Session,
    tenant_id: str,
    *,
    code: str,
    name: str,
    role: str,
    expected_revision: int | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict:
    from reality.services.core import Conflict, InvalidOperation

    state = _mutation(session, tenant_id, expected_revision)
    code, name = code.strip(), name.strip()
    if not code or not name or role not in ACCOUNT_ROLES:
        raise InvalidOperation("Account code, name and supported role are required.")
    if session.scalar(
        select(SubledgerAccount.id).where(
            SubledgerAccount.tenant_id == tenant_id, SubledgerAccount.code == code
        )
    ):
        raise Conflict("Account code already exists.")
    account = SubledgerAccount(
        id=uid("acc"),
        tenant_id=tenant_id,
        code=code,
        name=name,
        role=role,
        state="active",
        revision=1,
    )
    session.add(account)
    _audit(session, tenant_id, state, account, "create", action_id)
    if _commit:
        session.commit()
    return _result(account)


def update_account(
    session: Session,
    tenant_id: str,
    account_id: str,
    *,
    code: str | None = None,
    name: str | None = None,
    state: str | None = None,
    expected_revision: int | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict:
    from reality.services.core import Conflict, InvalidOperation

    coordinator = _mutation(session, tenant_id, expected_revision)
    account = _get(session, tenant_id, account_id)
    if state is not None and state not in {"active", "blocked"}:
        raise InvalidOperation("Account state must be active or blocked.")
    if (code is not None and not code.strip()) or (
        name is not None and not name.strip()
    ):
        raise InvalidOperation("Account code and name cannot be empty.")
    if code is not None and session.scalar(
        select(SubledgerAccount.id).where(
            SubledgerAccount.tenant_id == tenant_id,
            SubledgerAccount.code == code.strip(),
            SubledgerAccount.id != account.id,
        )
    ):
        raise Conflict("Account code already exists.")
    for key, value in [("code", code), ("name", name), ("state", state)]:
        if value is not None:
            setattr(account, key, value.strip())
    account.revision += 1
    _audit(session, tenant_id, coordinator, account, "update", action_id)
    if _commit:
        session.commit()
    return _result(account)


def set_default_account(
    session: Session,
    tenant_id: str,
    *,
    role: str,
    account_id: str,
    expected_revision: int | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict:
    from reality.services.core import InvalidOperation

    state = _mutation(session, tenant_id, expected_revision)
    account = _get(session, tenant_id, account_id)
    if account.role != role or account.state != "active":
        raise InvalidOperation(
            "Default requires an active account with the matching role."
        )
    dest = session.scalar(
        select(FinanceRoleDestination).where(
            FinanceRoleDestination.tenant_id == tenant_id,
            FinanceRoleDestination.role == role,
        )
    )
    if dest is None:
        dest = FinanceRoleDestination(
            id=uid("dest"), tenant_id=tenant_id, role=role, account_id=account_id
        )
        session.add(dest)
    else:
        dest.account_id = account_id
    _audit(session, tenant_id, state, account, "default", action_id)
    if _commit:
        session.commit()
    return _result(account)


def initialize_accounts(
    session: Session,
    tenant_id: str,
    *,
    expected_revision: int | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict:
    _mutation(session, tenant_id, expected_revision)
    with session.begin_nested():
        for role, label in ACCOUNT_ROLES.items():
            dest = session.scalar(
                select(FinanceRoleDestination.id).where(
                    FinanceRoleDestination.tenant_id == tenant_id,
                    FinanceRoleDestination.role == role,
                )
            )
            if dest is not None:
                continue
            account = create_account(
                session,
                tenant_id,
                code=role,
                name=label,
                role=role,
                action_id=action_id,
                _commit=False,
            )
            set_default_account(
                session,
                tenant_id,
                role=role,
                account_id=account["id"],
                action_id=action_id,
                _commit=False,
            )
    if _commit:
        session.commit()
    return list_accounts(session, tenant_id)


def resolve_account(
    session: Session, tenant_id: str, role: str, account_id: str | None = None
) -> SubledgerAccount:
    from reality.services.core import InvalidOperation

    if account_id is None:
        dest = session.scalar(
            select(FinanceRoleDestination)
            .execution_options(populate_existing=True)
            .where(
                FinanceRoleDestination.tenant_id == tenant_id,
                FinanceRoleDestination.role == role,
            )
        )
        if dest is None:
            raise InvalidOperation(
                f"Missing account default for {role}. Configure finance accounts first."
            )
        account_id = dest.account_id
    account = _get(session, tenant_id, account_id)
    if account.role != role or account.state != "active":
        raise InvalidOperation("Account is blocked or has the wrong operational role.")
    return account


def _bootstrap_accounts(session: Session, tenant_id: str) -> None:
    """Fixed references inside new-company creation; no financial postings."""
    rows = [
        SubledgerAccount(
            id=uid("acc"),
            tenant_id=tenant_id,
            code=role,
            name=name,
            role=role,
            state="active",
            revision=1,
        )
        for role, name in BASE_ACCOUNT_ROLES.items()
    ]
    session.add_all(rows)
    session.flush()
    session.add_all(
        [
            FinanceRoleDestination(
                id=uid("dest"), tenant_id=tenant_id, role=row.role, account_id=row.id
            )
            for row in rows
        ]
    )
    session.add(FinanceState(id=uid("fin"), tenant_id=tenant_id, revision=0))
    session.flush()


def transaction_matrix(session: Session, tenant_id: str) -> dict:
    """Describe current defaults; a specific action still validates its own evidence."""
    from reality.domain.finance import TRANSACTION_MATRIX

    configured = list_accounts(session, tenant_id)
    by_id = {row["id"]: row for row in configured["accounts"]}
    operations = []
    for kind, label, debit, credit, basis, policy in TRANSACTION_MATRIX:
        legs = []
        for side, role in (("debit", debit), ("credit", credit)):
            account = by_id.get(configured["defaults"].get(role))
            status = (
                "missing"
                if account is None
                else "wrong_role"
                if account["role"] != role
                else "blocked"
                if account["state"] != "active"
                else "configured"
            )
            legs.append(
                {
                    "side": side,
                    "role": role,
                    "role_label": ACCOUNT_ROLES[role],
                    "account": account,
                    "status": status,
                }
            )
        operations.append(
            {
                "transaction": kind,
                "label": label,
                "basis": basis,
                "control_policy": policy,
                "legs": legs,
            }
        )
    return {"revision": configured["revision"], "operations": operations}
