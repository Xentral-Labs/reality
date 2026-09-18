"""Answer a question that was too large for the request that asked it (spec 236)."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.jobs.registry import (
    JobContext,
    JobDefinition,
    JobError,
    JobResult,
    RecordReference,
)

#: What a worker may hold that a request may not. Ten times the declared caps, which
#: is the point at which the memory spec 235 measures — 5.3 KiB of heap per finance
#: document — reaches roughly a gigabyte. Raising it further is a decision about the
#: worker's memory, not about analysis, and belongs with that measurement.
DEFERRED_INPUT_CEILING = 200_000


class AnalysisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis_request_id: str = Field(min_length=1, max_length=128)


def run_requested_analysis(
    session: Session, context: JobContext, config: AnalysisConfig
) -> JobResult:
    """Run the stored question and keep its answer beside it.

    The question is read from the row rather than carried in the configuration, so
    there is one copy of what was asked and no way for the two to disagree.
    """
    from reality.db.analytics import AnalysisRequest
    from reality.domain.traversal import Traversal
    from reality.services.analytics.budget import DEFERRED_INPUTS
    from reality.services.analytics.requests import _member
    from reality.services.analytics.traversal import TraversalRefused, run_traversal
    from reality.services.core import RealityError

    row = session.scalar(
        select(AnalysisRequest).where(
            AnalysisRequest.tenant_id == context.tenant_id,
            AnalysisRequest.id == config.analysis_request_id,
        )
    )
    if row is None:
        raise JobError("unknown_analysis_request")

    # Minutes pass between asking and running, and that is exactly when access
    # changes. The membership is checked again here, against the requester the row
    # records rather than whoever happens to claim the run.
    try:
        _member(session, context.tenant_id, row.requested_by_user_id)
    except RealityError as error:
        raise JobError("not_authorized") from error

    row.state = "running"
    session.flush()

    token = DEFERRED_INPUTS.set(DEFERRED_INPUT_CEILING)
    try:
        result = run_traversal(
            session, context.tenant_id, Traversal.model_validate(row.question)
        )
    except TraversalRefused as refusal:
        # A question that still cannot be answered says why, on the row, where the
        # asker will look for it. The run itself succeeded: it did what it was for.
        row.state = "failed"
        row.failure_code = refusal.code
        row.failure_message = str(refusal)[:500]
        row.answered_at = datetime.now(UTC)
        session.flush()
        return JobResult(
            counts={"answered": 0, "refused": 1},
            references=[RecordReference(record_type="analysis_request", id=row.id)],
        )
    finally:
        DEFERRED_INPUTS.reset(token)

    row.state = "ready"
    row.rows = [dict(item) for item in result.rows]
    row.row_count = len(result.rows)
    row.statements = result.statements
    row.answered_at = datetime.now(UTC)
    row.failure_code = None
    row.failure_message = None
    session.flush()
    return JobResult(
        counts={"answered": 1, "rows": row.row_count},
        references=[RecordReference(record_type="analysis_request", id=row.id)],
    )


def require_analysis_requester(
    session: Session, context: JobContext, config: BaseModel | None = None
) -> None:
    """Whoever may ask a question interactively may ask it deferred, and no more."""
    from reality.services.analytics.requests import _member
    from reality.services.core import RealityError

    try:
        _member(session, context.tenant_id, context.actor_id)
    except RealityError as error:
        raise JobError("not_authorized") from error


ANALYSIS = JobDefinition(
    "analysis.run",
    1,
    AnalysisConfig,
    require_analysis_requester,
    run_requested_analysis,
)
