"""A company built the way a real one is, because a shortcut measures a shortcut.

The demo interpreters refuse a plain tenant: `require_demo_intake` needs the bounded
profile authority a Sandbox company carries. Creating the rows directly would skip
exactly the authority reads FR-001 is about, so the fixture goes through company
setup, the Demo Data connection and the registered job handlers, driven with the
configuration Demo Data itself wrote. A fixture that invents its own configuration
measures a path nobody uses.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import AppUser, now, uid
from reality.db.scheduled_jobs import ScheduledJob
from reality.services import company_setup, demo_data

ORDER_JOB = "demo.generate_orders"
SETTLE_JOB = "demo.settle_orders"


@dataclass(frozen=True)
class IngestCompany:
    tenant_id: str
    actor_id: str
    order_config: dict
    settle_config: dict


def build(session: Session, name: str = "Ingest cost fixture") -> IngestCompany:
    """A connected Sandbox with its reference data, and nothing generating orders.

    Demo Data is started so that it writes its own schedules and their
    configuration, and left running because the handler refuses an inactive
    connection. Nothing else writes: the benchmark database is disposable and has
    no scheduler or worker pointed at it, which is what keeps the measurement to
    one writer. Running this against a database a worker also serves would measure
    two.
    """
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(user)
    session.flush()

    created = company_setup.create_company(
        session,
        user.id,
        f"ingest-{uuid4().hex[:12]}",
        name,
        "sandbox",
        "empty",
        confirmed=True,
        _initialize_inline=True,
    )
    tenant_id = created["tenant_id"]

    preview = demo_data.preview(session, tenant_id, user.id)
    demo_data.connect(
        session,
        tenant_id,
        user.id,
        f"connect-{uuid4().hex[:12]}",
        preview["fingerprint"],
        confirmed=True,
    )
    state = demo_data.status(session, tenant_id, user.id)
    demo_data.control(
        session,
        tenant_id,
        user.id,
        "start",
        state["revision"],
        f"start-{uuid4().hex[:12]}",
        confirmed=True,
    )
    session.commit()

    # The stored configuration is an envelope: the handler's own arguments sit
    # under "arguments", beside the schedule's initial timing.
    configs = {
        row.job_type: row.configuration.get("arguments", row.configuration)
        for row in session.scalars(
            select(ScheduledJob).where(
                ScheduledJob.tenant_id == tenant_id,
                ScheduledJob.job_type.in_((ORDER_JOB, SETTLE_JOB)),
            )
        )
    }
    return IngestCompany(tenant_id, user.id, configs[ORDER_JOB], configs[SETTLE_JOB])


def claim_for(session: Session, company: IngestCompany, job_type: str):
    """Materialize and claim until a run of this type is held. Not measured.

    The handler refuses a run it does not recognise — it checks that the run
    belongs to the connection's current schedule — so the fixture cannot call it
    directly. Claiming is real work, but it is the queue's cost and not the
    intake's, so it happens outside the measurement: what is measured is the
    execution of the claimed run, which is the step `research.md` reported.
    """
    from reality.services import scheduled_jobs

    for _ in range(64):
        run = scheduled_jobs.claim_next(session, company.tenant_id)
        if run is None:
            scheduled_jobs.materialize_due(session, company.tenant_id)
            session.commit()
            run = scheduled_jobs.claim_next(session, company.tenant_id)
        if run is None:
            return None
        session.commit()
        if run.job_type == job_type:
            return run
        # Not the step being measured: run it so the queue moves on.
        scheduled_jobs.execute_claim(
            session, company.tenant_id, run.id, run.claim_token
        )
        session.commit()
    return None


def execute(session: Session, company: IngestCompany, run) -> str:
    """The measured part: one claimed run doing its work."""
    from reality.services import scheduled_jobs

    status = scheduled_jobs.execute_claim(
        session, company.tenant_id, run.id, run.claim_token
    )
    session.commit()
    return status


@contextmanager
def marked_intake():
    """Wrap the two service calls a real intake makes, wherever they are reached.

    The handlers call them from inside their own selection work, so the span
    cannot be opened from the runner. The functions are wrapped instead — they are
    public services and nothing in the product is changed, only observed.
    """
    from reality.services import core

    from .measure import interpreting

    original_enqueue = core.enqueue_source
    original_process = core.process_import_job_bound

    def enqueue(*args, **kwargs):
        with interpreting():
            return original_enqueue(*args, **kwargs)

    def process(*args, **kwargs):
        with interpreting():
            return original_process(*args, **kwargs)

    core.enqueue_source = enqueue
    core.process_import_job_bound = process
    try:
        yield
    finally:
        core.enqueue_source = original_enqueue
        core.process_import_job_bound = original_process


def make_due(session: Session, company: IngestCompany, ahead: timedelta) -> None:
    """Move the fixture's own schedules and claimable runs into the past.

    An earlier version of this faked the clock by replacing `now`. It could not
    work: a column whose default is `now` captured that function when the module
    was imported, so the rows kept real timestamps while the code thought it was
    two hours later, and settlement was never due. The fixture therefore moves its
    own queue rows instead of pretending about the time — the same effect, and no
    disagreement between what the code believes and what the database holds.

    `ahead` is how far back to place them: far enough that a synthetic invoice,
    due two to ten minutes after its order, and a payment up to ninety minutes
    after that, have both come round.
    """
    from reality.db.core import now
    from reality.db.scheduled_jobs import ScheduledJob, ScheduledJobRun

    moment = now() - ahead
    session.execute(
        ScheduledJob.__table__.update()
        .where(ScheduledJob.tenant_id == company.tenant_id)
        .values(next_run_at=moment)
    )
    session.execute(
        ScheduledJobRun.__table__.update()
        .where(
            ScheduledJobRun.tenant_id == company.tenant_id,
            ScheduledJobRun.status.in_(("queued", "retry")),
        )
        .values(scheduled_for=moment, created_at=now())
    )
    session.commit()


def settle_from(
    session: Session, company: IngestCompany, run, ahead: timedelta
) -> None:
    """Let this settlement run see the orders that are due by now.

    The handler reads what is due `as of` its own run's creation. Placing that
    moment after the orders were recorded is what lets one sweep invoice them,
    without the benchmark waiting out the profile's real minutes.
    """
    from reality.db.core import now
    from reality.db.scheduled_jobs import ScheduledJobRun

    session.execute(
        ScheduledJobRun.__table__.update()
        .where(ScheduledJobRun.id == run.id)
        .values(created_at=now() + ahead)
    )
    session.flush()
