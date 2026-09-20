"""Owner-authorized admission of exact financial company input manifests."""

from __future__ import annotations

import base64
import json
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.company_generations import (
    CostCompanyContributionInput,
    CostCompanyContributionResult,
    CostCompanyGeneration,
    CostCompanyInventoryInput,
    CostCompanyInventoryResult,
    CostCompanyManifest,
    CostCompanyPublication,
)
from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import BusinessEvent, Tenant, now, uid
from reality.db.cost_census import CostCompanyCensusLine
from reality.db.cost_generations import (
    CostContributionGeneration,
    CostContributionSnapshot,
)
from reality.domain.cost_census import digest
from reality.domain.cost_population import (
    ContributionExpectation,
    ContributionObservation,
    EvaluatedPopulation,
    ExpectedPopulation,
    InventoryExpectation,
    InventoryObservation,
    PopulationBasis,
    close_population,
)
from reality.domain.cost_query import context_envelope
from reality.services import core
from reality.services.cost_census_resolution import _resolve
from reality.services.cost_census_storage import _header, _verify
from reality.services.memberships import Principal, require_owner

INVENTORY_VERSION = "inventory-v1"
CONTRIBUTION_VERSION = "commercial-v1"
ALGORITHM_BUNDLE = "company-v1"


def _summary(manifest: CostCompanyManifest) -> dict:
    return {
        "id": manifest.id,
        "tenant_id": manifest.tenant_id,
        "census_id": manifest.census_id,
        "effective_at": manifest.effective_at.isoformat(),
        "knowledge_at": manifest.knowledge_at.isoformat(),
        "target_event_sequence": manifest.target_event_sequence,
        "inventory_algorithm_version": manifest.inventory_algorithm_version,
        "contribution_algorithm_version": manifest.contribution_algorithm_version,
        "scope_key": manifest.scope_key,
        "population_digest": manifest.population_digest,
        "counts": {
            "inventory": manifest.inventory_count,
            "contribution": manifest.contribution_count,
            "header_gaps": manifest.header_gap_count,
            "source_gaps": manifest.source_gap_count,
        },
        "gap_digest": manifest.gap_digest,
        "state": manifest.state,
        "content_hash": manifest.content_hash,
    }


def _existing(session: Session, tenant: str, census: str):
    return session.scalar(
        select(CostCompanyManifest).where(
            CostCompanyManifest.tenant_id == tenant,
            CostCompanyManifest.census_id == census,
            CostCompanyManifest.inventory_algorithm_version == INVENTORY_VERSION,
            CostCompanyManifest.contribution_algorithm_version == CONTRIBUTION_VERSION,
            CostCompanyManifest.state == "sealed",
        )
    )


def _admit(
    session: Session,
    tenant_id: str,
    census_id: str,
    *,
    principal: Principal,
    max_subjects: int = 10,
) -> dict:
    """Retain the exact reviewed/unknown inputs of one current sealed census."""
    if session.new or session.dirty or session.deleted:
        raise core.InvalidOperation(
            "Company manifest admission requires a clean session."
        )
    if session.connection().get_isolation_level() != "READ COMMITTED":
        raise core.InvalidOperation(
            "Company manifest admission requires READ COMMITTED."
        )
    with session.begin_nested():
        tenant = session.scalar(
            select(Tenant).where(Tenant.id == tenant_id).with_for_update()
        )
        if tenant is None:
            raise core.NotFound("Company not found.")
        require_owner(session, tenant_id, principal)
        prior = _existing(session, tenant_id, census_id)
        if prior is not None:
            return _summary(prior)

        records: dict = {}
        _verify(session, tenant_id, census_id, _records=records)
        census = _header(session, tenant_id, census_id)
        cursor = int(
            session.scalar(
                select(BusinessEvent.sequence)
                .where(BusinessEvent.tenant_id == tenant_id)
                .order_by(BusinessEvent.sequence.desc())
                .limit(1)
            )
            or 0
        )
        if cursor != census["event_sequence"]:
            raise core.InvalidOperation(
                "Company census is stale for manifest admission."
            )
        resolved = _resolve(
            session,
            tenant_id,
            census_id,
            max_subjects=max_subjects,
            _tenant_locked=True,
        )

        movement_items = {
            row["observed_values"]["item_id"] for row in records["movement"]
        }
        lines = {row["document_line_id"]: row for row in records["line"]}
        if {row["item_id"] for row in resolved["inventory"]} != movement_items or {
            row["document_line_id"] for row in resolved["contribution"]
        } != set(lines):
            raise core.InvalidOperation("Company manifest population is incomplete.")

        inventory = []
        for row in resolved["inventory"]:
            known = row["state"] == "available_at_capture"
            authority = {
                "item_id": row["item_id"],
                "review_id": row["review_id"] if known else None,
                "review_content_hash": row["review_content_hash"],
                "state": "known" if known else "unknown",
                "gaps": sorted(row["gaps"]),
                "freshness_proof": row.get("freshness_proof"),
            }
            inventory.append(authority | {"input_fingerprint": digest(authority)})

        contribution = []
        for row in resolved["contribution"]:
            known = row["state"] == "available_at_capture"
            result = row["result"] if known else None
            db1 = "known" if known else "unknown"
            db2 = (
                "known"
                if result is not None and result.get("db2") is not None
                else "unknown"
            )
            authority = {
                "census_line_id": lines[row["document_line_id"]]["id"],
                "document_line_id": row["document_line_id"],
                "review_id": row["review_id"] if known else None,
                "review_content_hash": row["review_content_hash"],
                "inventory_review_id": (
                    result["trace"]["inventory_review_id"] if known else None
                ),
                "db1_state": db1,
                "db2_state": db2,
                "gaps": sorted(row["gaps"]),
                "freshness_proof": row.get("freshness_proof"),
            }
            contribution.append(authority | {"input_fingerprint": digest(authority)})

        populated = {row["document_member_id"] for row in records["line"]}
        header_gaps = [
            {
                "member_id": row["id"],
                "document_id": row["document_id"],
                "content_hash": row["content_hash"],
                "classification": "document_lines_missing",
            }
            for row in records["document"]
            if row["id"] not in populated
        ]
        source_gaps = [
            {
                "member_id": row["id"],
                "source_record_id": row["source_record_id"],
                "content_hash": row["content_hash"],
                "classification": row["observed_values"]["classification"],
            }
            for row in records["source"]
            if row["observed_values"]["classification"] != "interpreted"
        ]
        gaps = {
            "headers": sorted(header_gaps, key=lambda row: row["member_id"]),
            "sources": sorted(source_gaps, key=lambda row: row["member_id"]),
        }
        population = {
            "inventory": sorted(inventory, key=lambda row: row["item_id"]),
            "contribution": sorted(
                contribution, key=lambda row: row["document_line_id"]
            ),
        }
        population_digest = digest(population)
        gap_digest = digest(gaps)
        scope_key = digest(
            {
                "effective_at": census["effective_at"],
                "target_event_sequence": cursor,
                "inventory_algorithm_version": INVENTORY_VERSION,
                "contribution_algorithm_version": CONTRIBUTION_VERSION,
            }
        )
        admitted_at = now()
        content = {
            "census_id": census_id,
            "effective_at": census["effective_at"],
            "knowledge_at": admitted_at,
            "target_event_sequence": cursor,
            "scope_key": scope_key,
            "population_digest": population_digest,
            "gap_digest": gap_digest,
            "counts": {
                "inventory": len(inventory),
                "contribution": len(contribution),
                "header_gaps": len(header_gaps),
                "source_gaps": len(source_gaps),
            },
        }
        manifest = CostCompanyManifest(
            id=uid("ccm"),
            tenant_id=tenant_id,
            census_id=census_id,
            effective_at=census["effective_at"],
            knowledge_at=admitted_at,
            target_event_sequence=cursor,
            inventory_algorithm_version=INVENTORY_VERSION,
            contribution_algorithm_version=CONTRIBUTION_VERSION,
            scope_key=scope_key,
            population_digest=population_digest,
            inventory_count=len(inventory),
            contribution_count=len(contribution),
            header_gap_count=len(header_gaps),
            source_gap_count=len(source_gaps),
            gap_digest=gap_digest,
            state="building",
            sealed_at=None,
            content_hash=digest(content),
        )
        session.add(manifest)
        session.flush()
        for row in inventory:
            session.add(
                CostCompanyInventoryInput(
                    id=uid("cci"),
                    tenant_id=tenant_id,
                    manifest_id=manifest.id,
                    item_id=row["item_id"],
                    review_id=row["review_id"],
                    input_fingerprint=row["input_fingerprint"],
                    support_state=row["state"],
                )
            )
        for row in contribution:
            session.add(
                CostCompanyContributionInput(
                    id=uid("ccc"),
                    tenant_id=tenant_id,
                    manifest_id=manifest.id,
                    census_line_id=row["census_line_id"],
                    review_id=row["review_id"],
                    inventory_review_id=row["inventory_review_id"],
                    input_fingerprint=row["input_fingerprint"],
                    db1_state=row["db1_state"],
                    db2_state=row["db2_state"],
                )
            )
        session.flush()
        manifest.state = "sealed"
        manifest.sealed_at = now()
        session.flush()
        return _summary(manifest)


def _generation_summary(generation: CostCompanyGeneration) -> dict:
    return {
        "generation_id": generation.id,
        "manifest_id": generation.manifest_id,
        "scope_key": generation.scope_key,
        "state": generation.state,
        "expected_work_count": generation.expected_work_count,
        "completed_work_count": generation.completed_work_count,
        "counts": {
            "inventory": generation.inventory_count,
            "contribution": generation.contribution_count,
        },
    }


def _generation(session: Session, tenant: str, manifest_id: str):
    return session.scalar(
        select(CostCompanyGeneration).where(
            CostCompanyGeneration.tenant_id == tenant,
            CostCompanyGeneration.manifest_id == manifest_id,
            CostCompanyGeneration.algorithm_bundle == ALGORITHM_BUNDLE,
        )
    )


def _result_hashes(
    session: Session, tenant: str, generation_id: str
) -> tuple[str, str]:
    inventory = [
        row.result_fingerprint
        for row in session.scalars(
            select(CostCompanyInventoryResult)
            .where(
                CostCompanyInventoryResult.tenant_id == tenant,
                CostCompanyInventoryResult.generation_id == generation_id,
            )
            .order_by(CostCompanyInventoryResult.inventory_input_id)
        )
    ]
    contribution = [
        row.result_fingerprint
        for row in session.scalars(
            select(CostCompanyContributionResult)
            .where(
                CostCompanyContributionResult.tenant_id == tenant,
                CostCompanyContributionResult.generation_id == generation_id,
            )
            .order_by(CostCompanyContributionResult.contribution_input_id)
        )
    ]
    return digest(inventory), digest(contribution)


def _contribution_cache(
    session: Session, tenant: str, review: CostContributionReview
) -> str:
    """Build the existing single-review cache shape from its canonical reader."""
    from reality.services.costing import reviewed_contribution

    generation = session.scalar(
        select(CostContributionGeneration).where(
            CostContributionGeneration.tenant_id == tenant,
            CostContributionGeneration.action_id == review.action_id,
            CostContributionGeneration.algorithm_version == CONTRIBUTION_VERSION,
        )
    )
    if generation is not None:
        if (
            session.scalar(
                select(CostContributionSnapshot.id).where(
                    CostContributionSnapshot.tenant_id == tenant,
                    CostContributionSnapshot.generation_id == generation.id,
                    CostContributionSnapshot.review_id == review.id,
                )
            )
            is None
        ):
            raise core.InvalidOperation("Contribution cache integrity mismatch.")
        return generation.id
    line = session.scalar(
        select(CostRevenueMatchBasis.document_line_id).where(
            CostRevenueMatchBasis.tenant_id == tenant,
            CostRevenueMatchBasis.id == review.revenue_basis_id,
        )
    )
    if line is None:
        raise core.InvalidOperation("Contribution cache integrity mismatch.")
    result = reviewed_contribution(session, tenant, line, review_id=review.id)
    observation = {
        "review_id": review.id,
        "goods_cost": result["trace"]["consumption"]["cost"],
        "known_direct_selling_cost": result["known_direct_selling_cost"],
        "known_allocated_selling_cost": result["known_allocated_selling_cost"],
        "selling_complete": result["db2"] is not None,
    }
    generation = CostContributionGeneration(
        id=uid("ccg"),
        tenant_id=tenant,
        action_id=review.action_id,
        algorithm_version=CONTRIBUTION_VERSION,
        completed_at=now(),
        output_hash=digest(
            {
                "review_id": review.id,
                "input_hash": review.content_hash,
                "algorithm_version": CONTRIBUTION_VERSION,
                "observation": observation,
            }
        ),
    )
    session.add(generation)
    session.flush()
    session.add(
        CostContributionSnapshot(
            id=uid("ccs"),
            tenant_id=tenant,
            generation_id=generation.id,
            review_id=review.id,
            goods_cost=Decimal(observation["goods_cost"]),
            known_direct_selling_cost=(
                Decimal(observation["known_direct_selling_cost"])
                if observation["known_direct_selling_cost"] is not None
                else None
            ),
            known_allocated_selling_cost=(
                Decimal(observation["known_allocated_selling_cost"])
                if observation["known_allocated_selling_cost"] is not None
                else None
            ),
            selling_complete=observation["selling_complete"],
        )
    )
    session.flush()
    return generation.id


def _verify_generation(
    session: Session, tenant: str, generation: CostCompanyGeneration
):
    manifest = session.scalar(
        select(CostCompanyManifest).where(
            CostCompanyManifest.tenant_id == tenant,
            CostCompanyManifest.id == generation.manifest_id,
            CostCompanyManifest.state == "sealed",
        )
    )
    if manifest is None:
        raise core.NotFound("Company generation not found.")
    inventory_hash, contribution_hash = _result_hashes(session, tenant, generation.id)
    inventory_count = session.scalar(
        select(func.count())
        .select_from(CostCompanyInventoryResult)
        .where(
            CostCompanyInventoryResult.tenant_id == tenant,
            CostCompanyInventoryResult.generation_id == generation.id,
        )
    )
    contribution_count = session.scalar(
        select(func.count())
        .select_from(CostCompanyContributionResult)
        .where(
            CostCompanyContributionResult.tenant_id == tenant,
            CostCompanyContributionResult.generation_id == generation.id,
        )
    )
    if (
        generation.scope_key != manifest.scope_key
        or generation.expected_work_count
        != manifest.inventory_count + manifest.contribution_count
        or generation.completed_work_count != inventory_count + contribution_count
        or (
            generation.state == "sealed"
            and generation.completed_work_count != generation.expected_work_count
        )
        or (
            generation.state == "sealed"
            and inventory_hash != generation.inventory_content_hash
        )
        or (
            generation.state == "sealed"
            and contribution_hash != generation.contribution_content_hash
        )
    ):
        raise core.InvalidOperation("Company generation integrity mismatch.")
    from reality.services import inventory_generations

    for result, member in session.execute(
        select(CostCompanyInventoryResult, CostCompanyInventoryInput)
        .join(
            CostCompanyInventoryInput,
            (CostCompanyInventoryInput.tenant_id == tenant)
            & (
                CostCompanyInventoryInput.id
                == CostCompanyInventoryResult.inventory_input_id
            ),
        )
        .where(
            CostCompanyInventoryResult.tenant_id == tenant,
            CostCompanyInventoryResult.generation_id == generation.id,
            CostCompanyInventoryResult.state == "known",
        )
    ):
        inventory_generations._read(
            session,
            tenant,
            member.item_id,
            review_id=member.review_id,
            generation_id=result.inventory_generation_id,
        )
    return manifest


def _close_population(
    session: Session,
    tenant: str,
    manifest: CostCompanyManifest,
    generation: CostCompanyGeneration,
) -> None:
    basis = PopulationBasis(
        tenant_id=tenant,
        effective_at=manifest.effective_at,
        knowledge_at=manifest.knowledge_at,
        event_sequence=manifest.target_event_sequence,
        inventory_algorithm=manifest.inventory_algorithm_version,
        contribution_algorithm=manifest.contribution_algorithm_version,
    )
    inventory = list(
        session.execute(
            select(CostCompanyInventoryInput, CostCompanyInventoryResult)
            .join(
                CostCompanyInventoryResult,
                (CostCompanyInventoryResult.tenant_id == tenant)
                & (
                    CostCompanyInventoryResult.inventory_input_id
                    == CostCompanyInventoryInput.id
                )
                & (CostCompanyInventoryResult.generation_id == generation.id),
            )
            .where(
                CostCompanyInventoryInput.tenant_id == tenant,
                CostCompanyInventoryInput.manifest_id == manifest.id,
            )
        )
    )
    contribution = list(
        session.execute(
            select(
                CostCompanyContributionInput,
                CostCompanyContributionResult,
                CostCompanyCensusLine.document_line_id,
            )
            .join(
                CostCompanyContributionResult,
                (CostCompanyContributionResult.tenant_id == tenant)
                & (
                    CostCompanyContributionResult.contribution_input_id
                    == CostCompanyContributionInput.id
                )
                & (CostCompanyContributionResult.generation_id == generation.id),
            )
            .join(
                CostCompanyCensusLine,
                (CostCompanyCensusLine.tenant_id == tenant)
                & (
                    CostCompanyCensusLine.id
                    == CostCompanyContributionInput.census_line_id
                ),
            )
            .where(
                CostCompanyContributionInput.tenant_id == tenant,
                CostCompanyContributionInput.manifest_id == manifest.id,
            )
        )
    )
    close_population(
        tenant,
        ExpectedPopulation(
            basis=basis,
            inventory=tuple(
                InventoryExpectation(
                    item_id=member.item_id, input_fingerprint=member.input_fingerprint
                )
                for member, _ in inventory
            ),
            contribution=tuple(
                ContributionExpectation(
                    document_line_id=line, input_fingerprint=member.input_fingerprint
                )
                for member, _, line in contribution
            ),
        ),
        EvaluatedPopulation(
            basis=basis,
            inventory=tuple(
                InventoryObservation(
                    item_id=member.item_id,
                    input_fingerprint=member.input_fingerprint,
                    acquisition=result.state,
                    carrying="unknown",
                )
                for member, result in inventory
            ),
            contribution=tuple(
                ContributionObservation(
                    document_line_id=line,
                    input_fingerprint=member.input_fingerprint,
                    db1=result.db1_state,
                    db2=result.db2_state,
                )
                for member, result, line in contribution
            ),
        ),
    )


def _build(
    session: Session,
    tenant: str,
    manifest_id: str,
    *,
    start: int = 0,
    limit: int = 100,
    deadline=None,
) -> dict:
    """Build a deterministic member range; retries never duplicate completed work."""
    if session.new or session.dirty or session.deleted:
        raise core.InvalidOperation("Company generation requires a clean session.")
    if session.connection().get_isolation_level() != "READ COMMITTED":
        raise core.InvalidOperation("Company generation requires READ COMMITTED.")
    if (
        type(start) is not int
        or start < 0
        or type(limit) is not int
        or not 1 <= limit <= 100
    ):
        raise core.InvalidOperation("Invalid company generation range.")
    from reality.services import inventory_generations

    inventory_generations._deadline(deadline)

    with session.begin_nested():
        manifest = session.scalar(
            select(CostCompanyManifest)
            .where(
                CostCompanyManifest.tenant_id == tenant,
                CostCompanyManifest.id == manifest_id,
                CostCompanyManifest.state == "sealed",
            )
            .with_for_update()
        )
        if manifest is None:
            raise core.NotFound("Company manifest not found.")
        generation = _generation(session, tenant, manifest_id)
        if generation is None:
            generation = CostCompanyGeneration(
                id=uid("ccg"),
                tenant_id=tenant,
                manifest_id=manifest.id,
                algorithm_bundle=ALGORITHM_BUNDLE,
                scope_key=manifest.scope_key,
                state="building",
                expected_work_count=manifest.inventory_count
                + manifest.contribution_count,
                completed_work_count=0,
                inventory_count=manifest.inventory_count,
                contribution_count=manifest.contribution_count,
                inventory_content_hash=digest([]),
                contribution_content_hash=digest([]),
                started_at=now(),
                completed_at=None,
            )
            session.add(generation)
            session.flush()
        else:
            _verify_generation(session, tenant, generation)
            if generation.state == "sealed":
                return _generation_summary(generation)

        inventory = list(
            session.scalars(
                select(CostCompanyInventoryInput)
                .where(
                    CostCompanyInventoryInput.tenant_id == tenant,
                    CostCompanyInventoryInput.manifest_id == manifest.id,
                )
                .order_by(CostCompanyInventoryInput.item_id)
            )
        )
        contribution = list(
            session.scalars(
                select(CostCompanyContributionInput)
                .where(
                    CostCompanyContributionInput.tenant_id == tenant,
                    CostCompanyContributionInput.manifest_id == manifest.id,
                )
                .order_by(CostCompanyContributionInput.census_line_id)
            )
        )
        work = [("inventory", row) for row in inventory] + [
            ("contribution", row) for row in contribution
        ]
        for family, member in work[start : start + limit]:
            inventory_generations._deadline(deadline)
            model = (
                CostCompanyInventoryResult
                if family == "inventory"
                else CostCompanyContributionResult
            )
            member_key = (
                "inventory_input_id"
                if family == "inventory"
                else "contribution_input_id"
            )
            if session.scalar(
                select(model.id).where(
                    model.tenant_id == tenant,
                    model.generation_id == generation.id,
                    getattr(model, member_key) == member.id,
                )
            ):
                continue
            if family == "inventory":
                cache_id = None
                if member.support_state == "known":
                    cache_id = inventory_generations._build(
                        session, tenant, member.review_id
                    )["generation_id"]
                values = {
                    "input_fingerprint": member.input_fingerprint,
                    "state": member.support_state,
                    "inventory_generation_id": cache_id,
                }
                session.add(
                    CostCompanyInventoryResult(
                        id=uid("cir"),
                        tenant_id=tenant,
                        generation_id=generation.id,
                        inventory_input_id=member.id,
                        inventory_generation_id=cache_id,
                        state=member.support_state,
                        result_fingerprint=digest(values),
                    )
                )
            else:
                cache_id = None
                if member.db1_state == "known":
                    review = session.scalar(
                        select(CostContributionReview).where(
                            CostContributionReview.tenant_id == tenant,
                            CostContributionReview.id == member.review_id,
                        )
                    )
                    if review is None:
                        raise core.InvalidOperation(
                            "Company contribution review integrity mismatch."
                        )
                    cache_id = _contribution_cache(session, tenant, review)
                values = {
                    "input_fingerprint": member.input_fingerprint,
                    "db1_state": member.db1_state,
                    "db2_state": member.db2_state,
                    "contribution_generation_id": cache_id,
                    "review_id": member.review_id,
                }
                session.add(
                    CostCompanyContributionResult(
                        id=uid("ccr"),
                        tenant_id=tenant,
                        generation_id=generation.id,
                        contribution_input_id=member.id,
                        contribution_generation_id=cache_id,
                        review_id=member.review_id,
                        db1_state=member.db1_state,
                        db2_state=member.db2_state,
                        result_fingerprint=digest(values),
                    )
                )
            session.flush()

        inventory_hash, contribution_hash = _result_hashes(
            session, tenant, generation.id
        )
        completed = session.scalar(
            select(func.count())
            .select_from(CostCompanyInventoryResult)
            .where(
                CostCompanyInventoryResult.tenant_id == tenant,
                CostCompanyInventoryResult.generation_id == generation.id,
            )
        ) + session.scalar(
            select(func.count())
            .select_from(CostCompanyContributionResult)
            .where(
                CostCompanyContributionResult.tenant_id == tenant,
                CostCompanyContributionResult.generation_id == generation.id,
            )
        )
        generation.completed_work_count = completed
        generation.inventory_content_hash = inventory_hash
        generation.contribution_content_hash = contribution_hash
        if completed == generation.expected_work_count:
            inventory_generations._deadline(deadline)
            _close_population(session, tenant, manifest, generation)
            generation.state = "sealed"
            generation.completed_at = now()
        session.flush()
        _verify_generation(session, tenant, generation)
        return _generation_summary(generation)


def _publish(
    session: Session, tenant: str, generation_id: str, previous: str | None
) -> dict:
    if session.connection().get_isolation_level() != "READ COMMITTED":
        raise core.InvalidOperation("Company publication requires READ COMMITTED.")
    from reality.services.business_locks import lock_delivery_state

    with session.begin_nested():
        lock_delivery_state(session, tenant)
        generation = session.scalar(
            select(CostCompanyGeneration)
            .where(
                CostCompanyGeneration.tenant_id == tenant,
                CostCompanyGeneration.id == generation_id,
            )
            .with_for_update()
        )
        if generation is None:
            raise core.NotFound("Company generation not found.")
        manifest = _verify_generation(session, tenant, generation)
        if generation.state != "sealed":
            raise core.InvalidOperation("Company generation is not sealed.")
        pointer = session.scalar(
            select(CostCompanyPublication)
            .where(
                CostCompanyPublication.tenant_id == tenant,
                CostCompanyPublication.scope_key == generation.scope_key,
            )
            .with_for_update()
        )
        if pointer is not None and pointer.generation_id == generation.id:
            return {"generation_id": generation.id, "changed": False}
        actual = pointer.generation_id if pointer else None
        if actual != previous:
            raise core.Conflict("Company cost publication conflict.")
        if manifest.target_event_sequence != int(
            session.scalar(
                select(func.max(BusinessEvent.sequence)).where(
                    BusinessEvent.tenant_id == tenant
                )
            )
            or 0
        ):
            raise core.InvalidOperation("Company generation is stale for publication.")
        if pointer is None:
            session.add(
                CostCompanyPublication(
                    id=uid("ccp"),
                    tenant_id=tenant,
                    scope_key=generation.scope_key,
                    generation_id=generation.id,
                    updated_at=now(),
                )
            )
        else:
            pointer.generation_id = generation.id
            pointer.updated_at = now()
        session.flush()
        return {"generation_id": generation.id, "changed": True}


def _money(value: Decimal | None) -> str | None:
    return None if value is None else format(value, ".4f")


def _page_cursor(generation_id: str, family: str, after: str) -> str:
    return base64.urlsafe_b64encode(
        json.dumps([generation_id, family, after], separators=(",", ":")).encode()
    ).decode()


def _after(cursor: str | None, generation_id: str, family: str) -> str | None:
    if cursor is None:
        return None
    try:
        value = json.loads(base64.b64decode(cursor, altchars=b"-_", validate=True))
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        raise core.InvalidOperation("Invalid company generation cursor.") from error
    if (
        not isinstance(value, list)
        or len(value) != 3
        or value[0] != generation_id
        or value[1] != family
        or type(value[2]) is not str
        or not value[2]
    ):
        raise core.InvalidOperation("Invalid company generation cursor.")
    return value[2]


def _report(
    session: Session,
    tenant: str,
    generation_id: str,
    *,
    page_size: int = 50,
    inventory_cursor: str | None = None,
    contribution_cursor: str | None = None,
) -> dict:
    if type(page_size) is not int or not 1 <= page_size <= 100:
        raise core.InvalidOperation("Page size must be between 1 and 100.")
    if session.new or session.dirty or session.deleted:
        raise core.InvalidOperation("Company generation reads require a clean session.")
    from reality.services.analytics.costing_relation import (
        company_contribution_relation,
        company_inventory_relation,
    )

    with session.no_autoflush:
        generation = session.scalar(
            select(CostCompanyGeneration).where(
                CostCompanyGeneration.tenant_id == tenant,
                CostCompanyGeneration.id == generation_id,
            )
        )
        if generation is None:
            raise core.NotFound("Company generation not found.")
        manifest = _verify_generation(session, tenant, generation)
        if generation.state != "sealed":
            raise core.InvalidOperation("Company generation is not sealed.")
        inventory_relation = company_inventory_relation(
            tenant, generation.id
        ).subquery()
        contribution_relation = company_contribution_relation(
            tenant, generation.id
        ).subquery()
        inventory_after = _after(inventory_cursor, generation.id, "inventory")
        contribution_after = _after(contribution_cursor, generation.id, "contribution")
        inventory_page = list(
            session.execute(
                select(inventory_relation)
                .where(
                    True
                    if inventory_after is None
                    else inventory_relation.c.input_id > inventory_after
                )
                .order_by(inventory_relation.c.input_id)
                .limit(page_size + 1)
            ).mappings()
        )
        contribution_page = list(
            session.execute(
                select(contribution_relation)
                .where(
                    True
                    if contribution_after is None
                    else contribution_relation.c.input_id > contribution_after
                )
                .order_by(contribution_relation.c.input_id)
                .limit(page_size + 1)
            ).mappings()
        )
        inventory_totals = (
            session.execute(
                select(
                    func.count().label("total"),
                    func.count()
                    .filter(inventory_relation.c.state == "known")
                    .label("known"),
                    func.sum(inventory_relation.c.acquisition_value)
                    .filter(inventory_relation.c.state == "known")
                    .label("acquisition_value"),
                )
            )
            .mappings()
            .one()
        )
        contribution_totals = (
            session.execute(
                select(
                    func.count().label("total"),
                    func.count()
                    .filter(contribution_relation.c.db1_state == "known")
                    .label("db1_known"),
                    func.count()
                    .filter(contribution_relation.c.db2_state == "known")
                    .label("db2_known"),
                    func.sum(
                        contribution_relation.c.revenue
                        - contribution_relation.c.goods_cost
                    )
                    .filter(contribution_relation.c.db1_state == "known")
                    .label("db1"),
                )
            )
            .mappings()
            .one()
        )
        inventory_more = len(inventory_page) > page_size
        contribution_more = len(contribution_page) > page_size
        inventory = [dict(row) for row in inventory_page[:page_size]]
        contribution = [dict(row) for row in contribution_page[:page_size]]
        current = int(
            session.scalar(
                select(func.max(BusinessEvent.sequence)).where(
                    BusinessEvent.tenant_id == tenant
                )
            )
            or 0
        )
        state = "ready" if current == manifest.target_event_sequence else "pending"
        requested = {
            "kind": "company",
            "generation_id": generation.id,
            "freshness": "allow_previous",
        }
        resolved = {
            "tenant_id": tenant,
            "kind": "company",
            "basis_kind": "financial_company_generation",
            "generation_id": generation.id,
            "manifest_id": manifest.id,
            "scope_key": manifest.scope_key,
            "effective_at": manifest.effective_at.isoformat(),
            "knowledge_at": manifest.knowledge_at.isoformat(),
            "policy_revision_id": None,
            "profile_revision_id": None,
            "authority_scope": "independent_member_reviews",
            "inventory_algorithm_version": manifest.inventory_algorithm_version,
            "contribution_algorithm_version": manifest.contribution_algorithm_version,
            "event_sequence": manifest.target_event_sequence,
        }
        freshness = {
            "state": state,
            "processed_event_sequence": manifest.target_event_sequence,
            "target_event_sequence": current,
        }
        return {
            **_generation_summary(generation),
            **context_envelope(
                requested=requested, resolved=resolved, freshness=freshness
            ),
            "freshness": state,
            "coverage": {
                "inventory": {
                    "expected": manifest.inventory_count,
                    "known": inventory_totals["known"],
                },
                "contribution": {
                    "expected": manifest.contribution_count,
                    "db1_known": contribution_totals["db1_known"],
                    "db2_known": contribution_totals["db2_known"],
                },
            },
            "totals": {
                "acquisition_value": _money(inventory_totals["acquisition_value"]),
                "db1": _money(contribution_totals["db1"]),
            },
            "inventory": {
                "rows": inventory,
                "total": inventory_totals["total"],
                "next_cursor": _page_cursor(
                    generation.id, "inventory", inventory[-1]["input_id"]
                )
                if inventory_more
                else None,
            },
            "contribution": {
                "rows": contribution,
                "total": contribution_totals["total"],
                "next_cursor": _page_cursor(
                    generation.id, "contribution", contribution[-1]["input_id"]
                )
                if contribution_more
                else None,
            },
        }
