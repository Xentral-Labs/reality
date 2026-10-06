"""Bounded company-world job using the shared transactional worker."""

from pydantic import BaseModel, ConfigDict, Field

from reality.jobs.registry import JobDefinition, JobResult, require_company_owner


class LiveConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1, max_length=128)


def authorize(session, context, config):
    from reality.services.live_company import _owner, _run

    require_company_owner(session, context, config)
    _owner(session, context.tenant_id, context.actor_id)
    _, run = _run(session, context.tenant_id, config.run_id)
    if run["owner_id"] != context.actor_id:
        from reality.jobs.registry import JobError

        raise JobError("not_authorized")


def generate(session, context, config):
    from reality.db.core import now
    from reality.services.live_company import tick

    result = tick(
        session,
        context.tenant_id,
        config.run_id,
        context.run_id,
        now(),
    )
    return JobResult(counts={"orders_generated": result["generated"]})


LIVE = JobDefinition(
    name="simulator.world",
    version=1,
    config_model=LiveConfig,
    authorize=authorize,
    handler=generate,
    timeout_seconds=120,
)


def react(session, context, config):
    from reality.db.core import now
    from reality.services.live_company import reactions

    return JobResult(counts=reactions(session, context.tenant_id, config.run_id, now()))


def check(session, context, config):
    from reality.db.core import now
    from reality.services.live_company import save_monitor

    result = save_monitor(
        session,
        context.tenant_id,
        config.run_id,
        context.run_id,
        now(),
    )
    return JobResult(
        counts={"differences": len(result["differences"]), "orders": result["orders"]}
    )


REACT = JobDefinition(
    name="simulator.reactions",
    version=1,
    config_model=LiveConfig,
    authorize=authorize,
    handler=react,
    timeout_seconds=120,
)
CHECK = JobDefinition(
    name="simulator.monitor",
    version=1,
    config_model=LiveConfig,
    authorize=authorize,
    handler=check,
    timeout_seconds=120,
)
