"""Owner-authorized rebuilds of retained cost scopes, never financial approval."""

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.jobs.registry import (
    JobContext,
    JobDefinition,
    JobError,
    JobResult,
    RecordReference,
    require_company_owner,
)


class InventoryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    review_id: str | None = Field(default=None, min_length=1, max_length=128)
    action_id: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def exact_scope(self):
        if (self.review_id is None) == (self.action_id is None):
            raise ValueError("Exactly one review_id or action_id is required.")
        return self

    @model_serializer
    def serialize_scope(self) -> dict[str, str]:
        # Preserve existing manual-run config fingerprints for review-only requests.
        return (
            {"review_id": self.review_id}
            if self.review_id is not None
            else {"action_id": self.action_id}
        )


def authorize(session: Session, context: JobContext, config: InventoryConfig) -> None:
    from reality.db.inventory_costing import CostInventoryReview

    require_company_owner(session, context, config)
    if config.action_id is not None:
        from reality.services import core
        from reality.services.costing import inventory_batch_snapshot

        try:
            inventory_batch_snapshot(session, context.tenant_id, config.action_id)
        except (core.NotFound, core.InvalidOperation) as error:
            raise JobError("cost_basis_unavailable") from error
        return
    if (
        session.scalar(
            select(CostInventoryReview.id).where(
                CostInventoryReview.tenant_id == context.tenant_id,
                CostInventoryReview.id == config.review_id,
            )
        )
        is None
    ):
        raise JobError("cost_basis_unavailable")


def refresh(
    session: Session, context: JobContext, config: InventoryConfig
) -> JobResult:
    from reality.services.costing import build_inventory_generation

    authorize(session, context, config)
    if config.action_id is not None:
        from reality.services.costing import build_inventory_batch_generation

        result = build_inventory_batch_generation(
            session, context.tenant_id, config.action_id, deadline=context.deadline
        )
        return JobResult(
            counts={
                "generations": result["created"],
                "inventory_rows": result["inventory_rows"],
            },
            references=[
                RecordReference(record_type="cost_inventory_generation", id=identity)
                for identity in result["generation_ids"]
            ],
        )
    result = build_inventory_generation(
        session, context.tenant_id, config.review_id, deadline=context.deadline
    )
    return JobResult(
        counts={"generations": int(result["created"]), "inventory_rows": 1},
        references=[
            RecordReference(
                record_type="cost_inventory_generation", id=result["generation_id"]
            )
        ],
    )


REFRESH_INVENTORY = JobDefinition(
    name="costing.inventory.refresh",
    version=1,
    config_model=InventoryConfig,
    authorize=authorize,
    handler=refresh,
)


class ContributionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    action_id: str = Field(min_length=1, max_length=128)


def authorize_contribution(
    session: Session, context: JobContext, config: ContributionConfig
) -> None:
    from reality.services import core
    from reality.services.costing import contribution_snapshot

    require_company_owner(session, context, config)
    try:
        contribution_snapshot(session, context.tenant_id, config.action_id)
    except (core.NotFound, core.InvalidOperation) as error:
        raise JobError("cost_basis_unavailable") from error


def refresh_contribution(
    session: Session, context: JobContext, config: ContributionConfig
) -> JobResult:
    from reality.services.costing import build_contribution_generation

    authorize_contribution(session, context, config)
    result = build_contribution_generation(
        session, context.tenant_id, config.action_id, deadline=context.deadline
    )
    return JobResult(
        counts={
            "generations": int(result["created"]),
            "contribution_rows": result["contribution_rows"],
        },
        references=[
            RecordReference(
                record_type="cost_contribution_generation", id=result["generation_id"]
            )
        ],
    )


REFRESH_CONTRIBUTION = JobDefinition(
    name="costing.contribution.refresh",
    version=1,
    config_model=ContributionConfig,
    authorize=authorize_contribution,
    handler=refresh_contribution,
)


class CapturedReportConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    basis_id: str = Field(min_length=1, max_length=128)


def authorize_captured_report(
    session: Session, context: JobContext, config: CapturedReportConfig
) -> None:
    from reality.db.cost_captured_basis import CostCapturedBasis

    require_company_owner(session, context, config)
    if (
        session.scalar(
            select(CostCapturedBasis.id).where(
                CostCapturedBasis.tenant_id == context.tenant_id,
                CostCapturedBasis.id == config.basis_id,
                CostCapturedBasis.state == "sealed",
            )
        )
        is None
    ):
        raise JobError("cost_basis_unavailable")


def refresh_captured_report(
    session: Session, context: JobContext, config: CapturedReportConfig
) -> JobResult:
    from reality.services.costing import build_captured_cost_generation

    authorize_captured_report(session, context, config)
    result = build_captured_cost_generation(session, context.tenant_id, config.basis_id)
    return JobResult(
        counts={"generations": 1},
        references=[
            RecordReference(record_type="cost_generation", id=result["generation_id"])
        ],
    )


REFRESH_CAPTURED_REPORT = JobDefinition(
    name="costing.captured_report.refresh",
    version=1,
    config_model=CapturedReportConfig,
    authorize=authorize_captured_report,
    handler=refresh_captured_report,
)


class PublishCapturedReportConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    generation_id: str = Field(min_length=1, max_length=128)
    expected_previous_id: str | None = Field(default=None, min_length=1, max_length=128)


def authorize_captured_publication(
    session: Session, context: JobContext, config: PublishCapturedReportConfig
) -> None:
    from reality.db.captured_report import CostGeneration

    require_company_owner(session, context, config)
    if (
        session.scalar(
            select(CostGeneration.id).where(
                CostGeneration.tenant_id == context.tenant_id,
                CostGeneration.id == config.generation_id,
                CostGeneration.state == "sealed",
            )
        )
        is None
    ):
        raise JobError("cost_basis_unavailable")


def publish_captured_report(
    session: Session, context: JobContext, config: PublishCapturedReportConfig
) -> JobResult:
    from reality.services import core
    from reality.services.costing import publish_captured_cost_generation

    authorize_captured_publication(session, context, config)
    try:
        result = publish_captured_cost_generation(
            session,
            context.tenant_id,
            config.generation_id,
            expected_previous_id=config.expected_previous_id,
        )
    except core.InvalidOperation as error:
        raise JobError("cost_publication_conflict") from error
    return JobResult(
        counts={"publication_changed": int(result["change_pointer"])},
        references=[
            RecordReference(record_type="cost_generation", id=config.generation_id)
        ],
    )


PUBLISH_CAPTURED_REPORT = JobDefinition(
    name="costing.captured_report.publish",
    version=1,
    config_model=PublishCapturedReportConfig,
    authorize=authorize_captured_publication,
    handler=publish_captured_report,
)


class CompanyManifestConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    census_id: str = Field(min_length=1, max_length=128)
    max_subjects: int = Field(default=10, ge=1, le=10)


def authorize_company_manifest(
    session: Session, context: JobContext, config: CompanyManifestConfig
) -> None:
    from reality.db.cost_census import CostCompanyCensus

    require_company_owner(session, context, config)
    if (
        session.scalar(
            select(CostCompanyCensus.id).where(
                CostCompanyCensus.tenant_id == context.tenant_id,
                CostCompanyCensus.id == config.census_id,
                CostCompanyCensus.state == "sealed",
            )
        )
        is None
    ):
        raise JobError("cost_basis_unavailable")


def admit_company_manifest(
    session: Session, context: JobContext, config: CompanyManifestConfig
) -> JobResult:
    from reality.services import core
    from reality.services.costing import admit_company_cost_manifest
    from reality.services.memberships import Principal

    authorize_company_manifest(session, context, config)
    try:
        result = admit_company_cost_manifest(
            session,
            context.tenant_id,
            config.census_id,
            principal=Principal(context.actor_id),
            max_subjects=config.max_subjects,
        )
    except (core.NotFound, core.InvalidOperation) as error:
        raise JobError("cost_basis_unavailable") from error
    return JobResult(
        counts={
            "manifests": 1,
            "inputs": result["counts"]["inventory"] + result["counts"]["contribution"],
        },
        references=[
            RecordReference(record_type="cost_company_manifest", id=result["id"])
        ],
    )


ADMIT_COMPANY_MANIFEST = JobDefinition(
    name="costing.company_manifest.admit",
    version=1,
    config_model=CompanyManifestConfig,
    authorize=authorize_company_manifest,
    handler=admit_company_manifest,
)


class CompanyGenerationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    manifest_id: str = Field(min_length=1, max_length=128)
    start: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=100)


def authorize_company_generation(
    session: Session, context: JobContext, config: CompanyGenerationConfig
) -> None:
    from reality.db.company_generations import CostCompanyManifest

    require_company_owner(session, context, config)
    if (
        session.scalar(
            select(CostCompanyManifest.id).where(
                CostCompanyManifest.tenant_id == context.tenant_id,
                CostCompanyManifest.id == config.manifest_id,
                CostCompanyManifest.state == "sealed",
            )
        )
        is None
    ):
        raise JobError("cost_basis_unavailable")


def build_company_generation(
    session: Session, context: JobContext, config: CompanyGenerationConfig
) -> JobResult:
    from reality.services import core
    from reality.services.costing import build_company_cost_generation

    authorize_company_generation(session, context, config)
    try:
        result = build_company_cost_generation(
            session,
            context.tenant_id,
            config.manifest_id,
            start=config.start,
            limit=config.limit,
            deadline=context.deadline,
        )
    except (core.NotFound, core.InvalidOperation) as error:
        raise JobError("cost_basis_unavailable") from error
    return JobResult(
        counts={
            "completed_work": result["completed_work_count"],
            "expected_work": result["expected_work_count"],
        },
        references=[
            RecordReference(
                record_type="cost_company_generation", id=result["generation_id"]
            )
        ],
    )


BUILD_COMPANY_GENERATION = JobDefinition(
    name="costing.company_generation.build",
    version=1,
    config_model=CompanyGenerationConfig,
    authorize=authorize_company_generation,
    handler=build_company_generation,
)


class PublishCompanyGenerationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    generation_id: str = Field(min_length=1, max_length=128)
    expected_previous_id: str | None = Field(default=None, min_length=1, max_length=128)


def authorize_company_publication(
    session: Session, context: JobContext, config: PublishCompanyGenerationConfig
) -> None:
    from reality.db.company_generations import CostCompanyGeneration

    require_company_owner(session, context, config)
    if (
        session.scalar(
            select(CostCompanyGeneration.id).where(
                CostCompanyGeneration.tenant_id == context.tenant_id,
                CostCompanyGeneration.id == config.generation_id,
                CostCompanyGeneration.state == "sealed",
            )
        )
        is None
    ):
        raise JobError("cost_basis_unavailable")


def publish_company_generation(
    session: Session, context: JobContext, config: PublishCompanyGenerationConfig
) -> JobResult:
    from reality.services import core
    from reality.services.costing import publish_company_cost_generation

    authorize_company_publication(session, context, config)
    try:
        result = publish_company_cost_generation(
            session,
            context.tenant_id,
            config.generation_id,
            previous_generation_id=config.expected_previous_id,
        )
    except (core.Conflict, core.InvalidOperation) as error:
        raise JobError("cost_publication_conflict") from error
    return JobResult(
        counts={"publication_changed": int(result["changed"])},
        references=[
            RecordReference(
                record_type="cost_company_generation", id=config.generation_id
            )
        ],
    )


PUBLISH_COMPANY_GENERATION = JobDefinition(
    name="costing.company_generation.publish",
    version=1,
    config_model=PublishCompanyGenerationConfig,
    authorize=authorize_company_publication,
    handler=publish_company_generation,
)
