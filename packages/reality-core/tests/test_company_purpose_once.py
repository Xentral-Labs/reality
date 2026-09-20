"""The company purpose is read once per transaction (spec 181 FR-001).

Every service call on a write path asks whether this company may be written to, and
the answer begins with what the company is *for*. The ingest measurement found that
question asked five times while recording one payment.

It cannot change underneath the answer: the database refuses it, with a trigger that
raises `Tenant purpose is immutable` on any update of that column. So the rules this
file holds are the ones that make remembering it safe — not that it is fast.
"""

import pytest
from sqlalchemy import event

from reality.services.core import (
    NotFound,
    create_party,
    create_tenant,
)


def purpose_reads(session):
    """How often this transaction asked what a company is for."""
    counted = [0]
    bind = session.get_bind()

    def before(conn, cursor, statement, *args):
        # The narrow question only: loading a whole company row also mentions the
        # column, and that is a different read with a different reason.
        if " ".join(statement.split()).startswith("SELECT tenant.purpose FROM tenant"):
            counted[0] += 1

    event.listen(bind, "before_cursor_execute", before)

    class Counter:
        def __enter__(self):
            return counted

        def __exit__(self, *args):
            event.remove(bind, "before_cursor_execute", before)

    return Counter()


def test_four_service_calls_do_not_ask_four_times(session, business):
    """Every service call on a write path asks; the transaction answers once.

    Four calls used to be four reads, and one payment's call tree five. What is
    left is the read that opens a scope: the first call in this transaction, and
    one more where the session moves from the fixture's scope into its own.
    """
    tenant = business.tenant.id
    with purpose_reads(session) as counted:
        for name in ("Eins", "Zwei", "Drei", "Vier"):
            create_party(session, tenant, name, "customer", _commit=False)
    assert counted[0] <= 2, f"asked {counted[0]} times in one transaction"


def test_a_savepoint_asks_again_on_purpose(session, business):
    """The answer is remembered per scope, and a savepoint is its own.

    A service that opens one — `record_customer_payment` does — asks once inside it
    and reuses that answer for every call it makes. Keying on the enclosing scope
    rather than the outermost transaction means an answer learned inside a savepoint
    is forgotten when that savepoint rolls back, which costs a read and cannot
    outlive what it rests on.
    """
    tenant = business.tenant.id
    with purpose_reads(session) as counted:
        create_party(session, tenant, "Vor dem Savepoint", "customer", _commit=False)
        with session.begin_nested():
            create_party(session, tenant, "Im Savepoint", "customer", _commit=False)
            create_party(session, tenant, "Auch darin", "customer", _commit=False)
    assert counted[0] == 2, f"expected one read per scope, got {counted[0]}"


def test_a_second_company_is_asked_about_on_its_own(session, business):
    """The answer belongs to the company it was read for, not to the transaction."""
    other = create_tenant(session, "Zweite Firma", _commit=False)
    with purpose_reads(session) as counted:
        create_party(session, business.tenant.id, "Kunde A", "customer", _commit=False)
        create_party(session, other.id, "Kunde B", "customer", _commit=False)
    assert counted[0] == 2


def test_a_company_created_in_this_transaction_is_seen(session):
    """Absence is never remembered: the company may arrive a moment later."""
    from reality.services import tenant_policy

    missing = "ten_not_there_yet"
    with pytest.raises(NotFound, match="Company not found"):
        tenant_policy.require_business_operation(session, missing, "party_create")

    fresh = create_tenant(session, "Gerade entstanden", _commit=False)
    session.flush()
    # The same transaction, and the company now exists.
    tenant_policy.require_business_operation(session, fresh.id, "party_create")


def test_a_playground_company_is_still_refused(session):
    """Remembering the answer must not turn a refusal into a permission."""
    from reality.db.core import Tenant
    from reality.services import tenant_policy
    from reality.services.tenant_policy import PlaygroundOperationDenied

    # Created as a practice company: the purpose cannot be set afterwards, because
    # the database refuses to change it — which is also why remembering it is safe.
    sandbox = Tenant(id="ten_sandbox_purpose", name="Übungsfirma", purpose="playground")
    session.add(sandbox)
    session.flush()

    with pytest.raises(PlaygroundOperationDenied):
        tenant_policy.require_business_operation(session, sandbox.id, "party_create")
    # Asked twice, refused twice.
    with pytest.raises(PlaygroundOperationDenied):
        tenant_policy.require_business_operation(session, sandbox.id, "party_create")
