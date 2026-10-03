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
    from reality.services.core import _batch_memo

    memo = _batch_memo(session)
    if memo is not None and ("finance_lock", tenant_id) in memo:
        # Locked for the rest of the transaction; callers raise the revision on
        # the same row object (spec 342).
        return memo[("finance_lock", tenant_id)]
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
    if memo is not None:
        memo[("finance_lock", tenant_id)] = state
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
        raise NotFound(code="subledger_account_not_found")
    return account


def _result(account: SubledgerAccount) -> dict[str, Any]:
    return {
        key: getattr(account, key)
        for key in ("id", "code", "name", "role", "state", "revision")
    }


def list_accounts(session: Session, tenant_id: str) -> dict:
    """
    BUSINESS PURPOSE:
    Read this company's subledger accounts and their current configuration.

    BUSINESS RULE services.finance.accounts.list_accounts.result:
    Return the current result with revision, roles, defaults, accounts.
    """
    from reality.services.core import get_tenant

    get_tenant(session, tenant_id)
    state = session.scalar(
        select(FinanceState).where(FinanceState.tenant_id == tenant_id)
    )
    defaults = {
        r.role: r.account_id
        for r in session.scalars(
            select(FinanceRoleDestination)
            .where(FinanceRoleDestination.tenant_id == tenant_id)
            .execution_options(populate_existing=True)
        )
    }
    # reality-rule: services.finance.accounts.list_accounts.result
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
    """
    BUSINESS PURPOSE:
    Create a company subledger account after validating its code, name and supported business role.

    BUSINESS RULE services.finance.accounts.create_account.refusal-15:
    IF account code or name is empty after trimming, or the role is unsupported:
        Refuse: Account code, name and supported role are required.

    BUSINESS RULE services.finance.accounts.create_account.refusal-17:
    IF the proposed account code already belongs to another account in this company:
        Refuse: Account code already exists.

    BUSINESS RULE services.finance.accounts.create_account.step-33:
    Record finance.account_changed with operation create and the account values; advance the company finance revision.

    BUSINESS RULE services.finance.accounts.create_account.result:
    Return the created account identity, code, name, role, active state and revision. Preserve its company scope and record the account-change audit.
    """
    from reality.services.core import Conflict, InvalidOperation

    state = _mutation(session, tenant_id, expected_revision)
    code, name = code.strip(), name.strip()
    # reality-rule: services.finance.accounts.create_account.refusal-15
    if not code or not name or role not in ACCOUNT_ROLES:
        raise InvalidOperation("Account code, name and supported role are required.")
    # reality-rule: services.finance.accounts.create_account.refusal-17
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
    # reality-rule: services.finance.accounts.create_account.step-33
    _audit(session, tenant_id, state, account, "create", action_id)
    if _commit:
        session.commit()
    # reality-rule: services.finance.accounts.create_account.result
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
    """
    BUSINESS PURPOSE:
    Update a company account configuration after validating the supplied changes.

    BUSINESS RULE services.finance.accounts.update_account.refusal-16:
    IF an account state was supplied other than active or blocked:
        Refuse: Account state must be active or blocked.

    BUSINESS RULE services.finance.accounts.update_account.refusal-18:
    IF a supplied account code or name is empty after trimming whitespace:
        Refuse: Account code and name cannot be empty.

    BUSINESS RULE services.finance.accounts.update_account.refusal-22:
    IF the proposed account code already belongs to another account in this company:
        Refuse: Account code already exists.

    BUSINESS RULE services.finance.accounts.update_account.step-34:
    Record finance.account_changed with operation update and the account values; advance the company finance revision.

    BUSINESS RULE services.finance.accounts.update_account.result:
    Return the updated account identity, code, name, role, state and revision. Record the account-change audit through the common account service.
    """
    from reality.services.core import Conflict, InvalidOperation

    coordinator = _mutation(session, tenant_id, expected_revision)
    account = _get(session, tenant_id, account_id)
    # reality-rule: services.finance.accounts.update_account.refusal-16
    if state is not None and state not in {"active", "blocked"}:
        raise InvalidOperation("Account state must be active or blocked.")
    # reality-rule: services.finance.accounts.update_account.refusal-18
    if (code is not None and not code.strip()) or (
        name is not None and not name.strip()
    ):
        raise InvalidOperation("Account code and name cannot be empty.")
    # reality-rule: services.finance.accounts.update_account.refusal-22
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
    # reality-rule: services.finance.accounts.update_account.step-34
    _audit(session, tenant_id, coordinator, account, "update", action_id)
    if _commit:
        session.commit()
    # reality-rule: services.finance.accounts.update_account.result
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
    """
    BUSINESS PURPOSE:
    Choose a validated company account as the default for the requested business role.

    BUSINESS RULE services.finance.accounts.set_default_account.refusal-14:
    IF the chosen default account is inactive or has a different business role:
        Refuse: Default requires an active account with the matching role.

    BUSINESS RULE services.finance.accounts.set_default_account.step-34:
    Record finance.account_changed with operation default and the account values; advance the company finance revision.

    BUSINESS RULE services.finance.accounts.set_default_account.result:
    Return the selected account identity, code, name, role, state and revision after recording it as the default for the matching role.
    """
    from reality.services.core import InvalidOperation

    state = _mutation(session, tenant_id, expected_revision)
    account = _get(session, tenant_id, account_id)
    # reality-rule: services.finance.accounts.set_default_account.refusal-14
    if account.role != role or account.state != "active":
        raise InvalidOperation(
            "Default requires an active account with the matching role."
        )
    previous = session.scalar(
        select(SubledgerAccount)
        .where(
            SubledgerAccount.tenant_id == tenant_id,
            SubledgerAccount.role == role,
            SubledgerAccount.default_destination_id.is_not(None),
        )
        .execution_options(populate_existing=True)
    )
    destination_id = previous.default_destination_id if previous else uid("dest")
    if previous is not None and previous.id != account.id:
        previous.default_destination_id = None
        # Both uniqueness constraints are immediate. Retire the old selection
        # before transferring its identity within the same locked transaction.
        session.flush()
    account.default_destination_id = destination_id
    # reality-rule: services.finance.accounts.set_default_account.step-34
    _audit(session, tenant_id, state, account, "default", action_id)
    if _commit:
        session.commit()
    # reality-rule: services.finance.accounts.set_default_account.result
    return _result(account)


def initialize_accounts(
    session: Session,
    tenant_id: str,
    *,
    expected_revision: int | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict:
    """
    BUSINESS PURPOSE:
    Initialize the company subledger accounts from the registered account definitions.

    BUSINESS RULE services.finance.accounts.initialize_accounts.result:
    Return the result from list accounts; inspect that called function for its calculation and eligibility rules.

    BUSINESS RULE services.finance.accounts.initialize_accounts.effect-40:
    Pass the stated inputs to the shared create account service. Its own source describes validation and record changes.
    """
    _mutation(session, tenant_id, expected_revision)
    from reality.services.core import (
        _company_amounts_stored,
        _delivery_failures_stored,
    )

    with session.begin_nested():
        for role, label in ACCOUNT_ROLES.items():
            if role == "exchange_difference" and not _company_amounts_stored(session):
                # A schema from before spec 309, only in the migration tests.
                continue
            if role == "carrier_claim_income" and not _delivery_failures_stored(
                session
            ):
                # A schema from before spec 335, only in the migration tests.
                continue
            dest = session.scalar(
                select(SubledgerAccount.default_destination_id).where(
                    SubledgerAccount.tenant_id == tenant_id,
                    SubledgerAccount.role == role,
                    SubledgerAccount.default_destination_id.is_not(None),
                )
            )
            if dest is not None:
                continue
            # reality-rule: services.finance.accounts.initialize_accounts.effect-40
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
    # reality-rule: services.finance.accounts.initialize_accounts.result
    return list_accounts(session, tenant_id)


def resolve_account(
    session: Session, tenant_id: str, role: str, account_id: str | None = None
) -> SubledgerAccount:
    from reality.services.core import InvalidOperation, _batch_memo

    memo = _batch_memo(session)
    key = ("account", tenant_id, role, account_id)
    if memo is not None and key in memo:
        # A batch changes no account or default (spec 342).
        return memo[key]
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
                code="finance_account_default_missing", values={"role": str(role)}
            )
        account_id = dest.account_id
    account = _get(session, tenant_id, account_id)
    if account.role != role or account.state != "active":
        raise InvalidOperation(code="finance_account_blocked_or_wrong_role")
    if memo is not None:
        memo[key] = account
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
            default_destination_id=uid("dest"),
        )
        for role, name in BASE_ACCOUNT_ROLES.items()
    ]
    session.add_all(rows)
    session.flush()
    session.add(FinanceState(id=uid("fin"), tenant_id=tenant_id, revision=0))
    session.flush()


def transaction_matrix(session: Session, tenant_id: str) -> dict:
    """
    Describe current defaults; a specific action still validates its own evidence.

    BUSINESS PURPOSE:
    Describe current defaults; a specific action still validates its own evidence.

    BUSINESS RULE services.finance.accounts.transaction_matrix.result:
    Return the current result with revision, operations.
    """
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
    # reality-rule: services.finance.accounts.transaction_matrix.result
    return {"revision": configured["revision"], "operations": operations}
