"""Spec392 exact source-backed order review; acceptance is a dedicated authority boundary."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from decimal import localcontext
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    CompanyTimeZone,
    FinanceState,
    Party,
    SourceRecord,
)
from reality.domain.intake import (
    CalendarState,
    PreparedIntake,
    canonical_json,
    content_digest,
)
from reality.domain.shopify_buyer_mapping import decode64, instant
from reality.domain.shopify_order_acceptance import (
    ACTION_TYPE,
    PROFILE,
    PURPOSE,
    AcceptancePolicy,
    AcceptancePrepareInput,
    AcceptanceReceipt,
    AcceptanceReviewInput,
    AcceptanceReviewResult,
    AcceptanceStatusResult,
    StoredAcceptanceProposal,
    inspect_simple_source,
)
from reality.domain.shopify_order_proposal import (
    MAX_PLAN_BYTES,
    MAX_WIRE_BYTES,
    OrderPrepareInput,
)
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.credit_exposure import _json_exposure, credit_exposure
from reality.services.intake_reference_state import mapped_state
from reality.services.shopify_buyer_mapping import _submitter
from reality.services.shopify_order_proposal import _resolve


def _unavailable():
    return core.InvalidOperation(code="shopify_order_acceptance_unavailable")


def _policy(
    tenant_id: str,
    supplied: AcceptancePolicy | None = None,
) -> AcceptancePolicy:
    try:
        if supplied is None:
            path = Path(os.environ["REALITY_SHOPIFY_ORDER_ACCEPTANCE_POLICY_FILE"])
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                info = os.fstat(fd)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.getuid()
                    or info.st_mode & 0o077
                    or info.st_size > 65536
                ):
                    raise ValueError("private_policy_required")
                with os.fdopen(fd, "rb", closefd=False) as handle:
                    supplied = AcceptancePolicy.model_validate_json(handle.read(65537))
            finally:
                os.close(fd)
        supplied = AcceptancePolicy.model_validate(supplied.model_dump())
        if (
            supplied.tenant_id != tenant_id
            or len(decode64(supplied.public_key)) != 32
            or len(set(supplied.allowed_subjects)) != len(supplied.allowed_subjects)
            or len(set(supplied.allowed_token_ids)) != len(supplied.allowed_token_ids)
            or len({entry.id for entry in supplied.mandates}) != len(supplied.mandates)
            or instant(supplied.expires_at) <= core.now()
        ):
            raise ValueError("policy_unavailable")
        return supplied
    except (OSError, KeyError, ValueError, TypeError, ValidationError) as error:
        raise _unavailable() from error


def _material(
    session: Session,
    tenant_id: str,
    request: AcceptancePrepareInput,
    token_id: str,
    trusted: AcceptancePolicy,
    observed_at: str,
) -> StoredAcceptanceProposal:
    old_request = OrderPrepareInput.model_validate(
        request.model_dump(exclude={"interpretation_profile", "delivery_terms"})
    )
    base = _resolve(session, tenant_id, old_request)
    binding = base.source_binding
    if (
        binding.shop != trusted.shop
        or binding.query_digest != trusted.query_digest
        or token_id not in trusted.allowed_token_ids
    ):
        raise _unavailable()
    source = session.scalar(
        select(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.id == binding.source_record_id,
        )
        .execution_options(populate_existing=True)
    )
    raw = json.loads(source.payload)
    source_evidence = inspect_simple_source(raw)
    holds = list(source_evidence["holds"])
    context = json.loads(
        session.scalar(
            select(core.ImportJob.input).where(
                core.ImportJob.tenant_id == tenant_id,
                core.ImportJob.id == binding.import_job_id,
            )
        )
    )
    acquisition = context.get("acquisition", {})
    if acquisition.get("api_version") != "2026-07":
        holds.append("supported_source_api_version_required")
    source_evidence["source_api_version"] = acquisition.get("api_version")
    source_evidence["source_query_digest"] = binding.query_digest
    time_zone = session.scalar(
        select(CompanyTimeZone)
        .where(CompanyTimeZone.tenant_id == tenant_id)
        .execution_options(populate_existing=True)
    )
    calendar = None
    date_text = None
    calendar_evidence = {"status": "missing"}
    if time_zone is not None and time_zone.source_record_id:
        stated_zone = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == time_zone.source_record_id,
            )
        )
        if (
            stated_zone is not None
            and stated_zone.source_system == "internal_company_time_zone"
            and stated_zone.source_type == "company_time_zone"
            and stated_zone.external_id == tenant_id
            and json.loads(stated_zone.payload).get("time_zone") == time_zone.time_zone
        ):
            try:
                if source_evidence.get("processed_at"):
                    date_text = (
                        instant(source_evidence["processed_at"])
                        .astimezone(ZoneInfo(time_zone.time_zone))
                        .date()
                        .isoformat()
                    )
                calendar = CalendarState(
                    time_zone=time_zone.time_zone,
                    source_record_id=time_zone.source_record_id,
                )
                calendar_evidence = {
                    "status": "explicit",
                    "time_zone": time_zone.time_zone,
                    "source_record_id": time_zone.source_record_id,
                    "source_hash": stated_zone.payload_hash,
                    "digest": mapped_state(time_zone),
                    "document_date_rule": "processed_at_in_explicit_company_timezone",
                    "processed_at": source_evidence.get("processed_at"),
                    "interpreted_date": date_text,
                }
            except (ValueError, KeyError):
                holds.append("explicit_company_calendar_required")
    if calendar is None or date_text is None:
        holds.append("explicit_company_calendar_required")
    finance = session.scalar(
        select(FinanceState)
        .where(FinanceState.tenant_id == tenant_id)
        .execution_options(populate_existing=True)
    )
    customer = session.scalar(
        select(Party)
        .where(
            Party.tenant_id == tenant_id, Party.id == base.mapping_bundle["customer_id"]
        )
        .execution_options(populate_existing=True)
    )
    credit = {"status": "unknown"}
    if finance is not None and customer is not None:
        exposure = _json_exposure(
            credit_exposure(session, tenant_id, customer.id, as_of=core.now())
        )
        exposure.pop("as_of", None)  # Current facts, not a permanently frozen cutoff.
        amount = source_evidence["stated_totals"].get("totalPriceSet")
        with localcontext() as decimal_context:
            decimal_context.prec = 160
            supported = (
                customer.credit_limit > 0
                and customer.default_currency == source_evidence["currency"]
                and not exposure["open_orders"]["unpriced"]
                and not exposure["not_counted"]
                and amount is not None
                and core.decimal(exposure["exposure"]) + core.decimal(amount)
                <= customer.credit_limit
            )
        credit = {
            "status": "pass" if supported else "held",
            "observed_at": observed_at,
            "customer_digest": mapped_state(customer),
            "currency": customer.default_currency,
            "configured_limit": str(customer.credit_limit),
            "source_stated_order_amount": amount,
            "exposure_digest": content_digest(exposure),
            "exposure": exposure,
        }
    if credit["status"] != "pass":
        holds.append("complete_current_positive_credit_capacity_required")
    plan_data = base.plan.model_dump(mode="json")
    replaced = {
        "final_unit_price_not_interpreted",
        "line_total_not_interpreted",
        "delivery_date_not_interpreted",
        "business_calendar_not_interpreted",
        "credit_assessment_not_performed",
        "acceptance_not_implemented",
    }
    holds.extend(issue for issue in plan_data["issues"] if issue not in replaced)
    document = plan_data["effects"][0]["arguments"]
    prices = {row["source_line_id"]: row for row in source_evidence["lines"]}
    for line in document["lines"]:
        price = prices.get(line["source_line_id"])
        if price is not None and not source_evidence["holds"]:
            line["unit_price"] = price["unit_price"]
            line["gross_amount"] = price["line_total"]
    document["document_date"] = date_text
    document["ordered_at"] = source_evidence.get("processed_at")
    for effect in plan_data["effects"][1:]:
        if effect["operation"] == "commitment":
            index = effect["arguments"]["line_index"]
            effect["arguments"]["amount"] = document["lines"][index]["gross_amount"]
    plan_data["mapping"]["origin"] = ACTION_TYPE
    plan_data["mapping"]["interpretation_profile"] = PROFILE
    plan_data["mapping"]["delivery_terms"] = "not_promised"
    plan_data["calendar"] = calendar.model_dump() if calendar is not None else None
    plan_data["finance_revision"] = finance.revision if finance is not None else None
    plan_data["issues"] = list(dict.fromkeys(holds))
    stated_amount = source_evidence["stated_totals"].get("totalPriceSet")
    selected_units = sum(int(line["quantity"]) for line in source_evidence["lines"])
    if (
        source_evidence["currency"] != trusted.currency
        or stated_amount is not None
        and core.decimal(stated_amount) > core.decimal(trusted.max_order_amount)
        or selected_units > trusted.max_order_units
        or len(plan_data["effects"]) > trusted.max_effects
    ):
        plan_data["issues"].append("current_host_order_limits_exceeded")
    readiness = {
        "profile": PROFILE,
        "delivery_terms": "not_promised",
        "source": source_evidence,
        "calendar": calendar_evidence,
        "credit": credit,
    }
    return StoredAcceptanceProposal(
        purpose=PURPOSE,
        request=request,
        source_binding=binding,
        buyer_mapping=base.buyer_mapping,
        mapping_bundle=base.mapping_bundle,
        plan=PreparedIntake.model_validate(plan_data),
        readiness=readiness,
        policy_digest=content_digest(trusted.model_dump()),
        observed_at=observed_at,
        submitter_token_id=token_id,
    )


def _view(
    row: ChangeProposal, held: StoredAcceptanceProposal, *, stale: bool = False
) -> dict:
    projection = held.plan.model_dump(mode="json")
    for effect in projection["effects"]:
        if effect["operation"] == "document":
            effect["arguments"].pop("_source_line_payloads", None)
    result = {
        "purpose": PURPOSE,
        "proposal_id": row.id,
        "status": "stale" if stale else row.status,
        "request_id": held.request.request_id,
        "review_digest": content_digest(held.model_dump(mode="json")),
        "source_binding": held.source_binding.model_dump(),
        "buyer_mapping": held.buyer_mapping.model_dump(
            exclude={"remaining_review", "current_basis"}
        ),
        "buyer_mapping_scope": "existing_buyer_mapping_evidence_at_order_review",
        "evidence_observed_at": held.observed_at,
        "readiness_evidence_scope": "frozen_at_order_review",
        "currentness": "historical_accepted_only"
        if row.status == "executed"
        else "changed"
        if stale
        else "unchanged_since_review",
        "mapping_bundle": held.mapping_bundle,
        "plan_digest": held.plan.review_digest(),
        "review_projection": projection,
        "readiness": held.readiness,
        "holds": list(held.plan.issues),
        "eligible_for_exact_authorization": not stale
        and not held.plan.issues
        and row.status == "proposed",
        "generic_confirmation_allowed": False,
        "business_effects_accepted": row.status == "executed",
        "original_source_unchanged": True,
        "import_job_input_unchanged": True,
    }
    if len(canonical_json(result).encode()) > MAX_WIRE_BYTES:
        raise _unavailable()
    return AcceptanceReviewResult.model_validate(result).model_dump(mode="json")


def _retained(session, tenant_id, proposal_id):
    row = session.scalar(
        select(ChangeProposal)
        .where(ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id)
        .execution_options(populate_existing=True)
    )
    if row is None or row.type != ACTION_TYPE:
        raise _unavailable()
    try:
        stored = json.loads(row.input)
        held = StoredAcceptanceProposal.model_validate(stored["proposal"])
        if held.source_binding.tenant_id != tenant_id or stored[
            "review_digest"
        ] != content_digest(held.model_dump(mode="json")):
            raise ValueError("retained_meaning_changed")
    except (KeyError, TypeError, ValueError, ValidationError) as error:
        raise _unavailable() from error
    return row, held


def prepare_order_acceptance(
    session: Session,
    tenant_id: str,
    arguments: dict,
    *,
    policy: AcceptancePolicy | None = None,
):
    """
    BUSINESS PURPOSE:
    Retain one exact source-backed order review without accepting business effects.

    BUSINESS RULE shopify_order_acceptance.prepare:
    Require current exact source, buyer, explicit references, profile, timezone, credit and host policy; preserve received amounts and retain one bounded immutable proposed Action only.
    """
    # reality-rule: shopify_order_acceptance.prepare
    try:
        request = AcceptancePrepareInput.model_validate(arguments)
    except (ValueError, TypeError, ValidationError) as error:
        raise _unavailable() from error
    if (
        session.new
        or session.deleted
        or any(session.is_modified(row) for row in session.dirty)
    ):
        raise _unavailable()
    token_id = _submitter(session, tenant_id, "shopify_source_order_acceptance_prepare")
    if token_id is None:
        raise _unavailable()
    lock_delivery_state(session, tenant_id)
    trusted = _policy(tenant_id, policy)
    key = (
        "act_soa_"
        + hashlib.sha256((tenant_id + "\0" + request.request_id).encode()).hexdigest()[
            :32
        ]
    )
    existing = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == key
        )
    )
    if existing is not None:
        row, held = _retained(session, tenant_id, key)
        if held.request != request:
            raise _unavailable()
        session.commit()
        return review_order_acceptance(
            session, tenant_id, {"proposal_id": key}, policy=policy
        )
    held = _material(
        session, tenant_id, request, token_id, trusted, core.now().isoformat()
    )
    if (
        _material(
            session,
            tenant_id,
            request,
            token_id,
            _policy(tenant_id, policy),
            held.observed_at,
        )
        != held
    ):
        raise _unavailable()
    row = ChangeProposal(
        id=key,
        tenant_id=tenant_id,
        type=ACTION_TYPE,
        status="proposed",
        input=canonical_json(
            {
                "proposal": held.model_dump(mode="json"),
                "review_digest": content_digest(held.model_dump(mode="json")),
            }
        ),
        output="{}",
    )
    _view(row, held)
    if len(row.input.encode()) > MAX_PLAN_BYTES:
        raise _unavailable()
    try:
        with session.begin_nested():
            session.add(row)
            session.flush()
    except IntegrityError as error:
        raise _unavailable() from error
    session.commit()
    return review_order_acceptance(
        session, tenant_id, {"proposal_id": key}, policy=policy
    )


def review_order_acceptance(
    session: Session,
    tenant_id: str,
    arguments: dict,
    *,
    policy: AcceptancePolicy | None = None,
):
    """
    BUSINESS PURPOSE:
    Read exact retained order meaning while separately reporting changed current evidence.

    BUSINESS RULE shopify_order_acceptance.review:
    Return historical immutable successor evidence; compare current source, references, calendar, credit and policy without refreshing or authorizing effects.
    """
    # reality-rule: shopify_order_acceptance.review
    request = AcceptanceReviewInput.model_validate(arguments)
    row, held = _retained(session, tenant_id, request.proposal_id)
    if row.status == "executed":
        _receipt(session, tenant_id, row, held)
        return _view(row, held)
    stale = False
    try:
        current = _material(
            session,
            tenant_id,
            held.request,
            held.submitter_token_id,
            _policy(tenant_id, policy),
            held.observed_at,
        )
        stale = (
            (core.now() - instant(held.observed_at)).total_seconds()
            > _policy(tenant_id, policy).review_max_age_seconds
            or current != held
            or _material(
                session,
                tenant_id,
                held.request,
                held.submitter_token_id,
                _policy(tenant_id, policy),
                held.observed_at,
            )
            != held
        )
    except (core.RealityError, ValueError, TypeError, KeyError, ValidationError):
        stale = True
    return _view(row, held, stale=stale)


def _lock_basis(session, tenant_id, held):
    """Tenant/finance precede immutable source and exact selected master locks."""
    from reality.db.core import ImportJob, Item, Location, PartyRole, SourceStream

    finance = session.scalar(
        select(FinanceState)
        .where(FinanceState.tenant_id == tenant_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if finance is None:
        raise _unavailable()
    binding = held.source_binding
    for model, predicate in [
        (
            SourceStream,
            (SourceStream.source_system == "shopify")
            & (SourceStream.source_type == "order_graphql")
            & (SourceStream.external_id == binding.external_id),
        ),
        (SourceRecord, SourceRecord.id == binding.source_record_id),
        (ImportJob, ImportJob.id == binding.import_job_id),
    ]:
        if (
            session.scalar(
                select(model)
                .where(model.tenant_id == tenant_id, predicate)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            is None
        ):
            raise _unavailable()
    models = {"party": Party, "location": Location, "item": Item}
    for ref in sorted(
        held.plan.references, key=lambda ref: (ref.record_type, ref.record_id)
    ):
        model = models.get(ref.record_type)
        if (
            model is None
            or session.scalar(
                select(model)
                .where(model.tenant_id == tenant_id, model.id == ref.record_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            is None
        ):
            raise _unavailable()
    party_ids = sorted(
        ref.record_id for ref in held.plan.references if ref.record_type == "party"
    )
    list(
        session.scalars(
            select(PartyRole)
            .where(PartyRole.tenant_id == tenant_id, PartyRole.party_id.in_(party_ids))
            .order_by(PartyRole.party_id, PartyRole.role)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    )
    zone = session.scalar(
        select(CompanyTimeZone)
        .where(CompanyTimeZone.tenant_id == tenant_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if (
        zone is None
        or session.scalar(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == zone.source_record_id,
            )
            .with_for_update()
        )
        is None
    ):
        raise _unavailable()


def _expected_claims(row, held):
    return {
        "proposal_id": row.id,
        "review_digest": content_digest(held.model_dump(mode="json")),
        "source_binding_digest": content_digest(held.source_binding.model_dump()),
        "mapping_bundle_digest": content_digest(held.mapping_bundle),
        "plan_digest": held.plan.review_digest(),
    }


def _authorize(session, tenant_id, row, held, signed, token_id, supplied):
    from sqlalchemy import Numeric, cast, func
    from sqlalchemy.dialects.postgresql import JSONB

    from reality.domain.shopify_order_acceptance import verify_acceptance_proof

    trusted = _policy(tenant_id, supplied)
    at = core.now()
    if (
        token_id != held.submitter_token_id
        or token_id not in trusted.allowed_token_ids
        or content_digest(trusted.model_dump()) != held.policy_digest
        or (at - instant(held.observed_at)).total_seconds()
        > trusted.review_max_age_seconds
        or instant(held.observed_at) > at
    ):
        raise _unavailable()
    try:
        claims = verify_acceptance_proof(
            signed, trusted, _expected_claims(row, held), at
        )
    except Exception as error:
        raise _unavailable() from error
    receipt = cast(ChangeProposal.output, JSONB)
    duplicate = session.scalar(
        select(ChangeProposal.id)
        .where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == ACTION_TYPE,
            ChangeProposal.status == "executed",
            receipt["approval"]["jti"].astext == claims.jti,
            ChangeProposal.id != row.id,
        )
        .limit(1)
    )
    if duplicate is not None:
        raise _unavailable()
    if claims.authorization_kind == "standing":
        mandate = next(
            entry
            for entry in trusted.mandates
            if entry.id == claims.mandate_id
            and entry.revision == claims.mandate_revision
        )
        if instant(held.readiness["source"]["created_at"]) <= instant(
            mandate.source_created_after
        ):
            raise _unavailable()
        amount = held.plan.effects[0].arguments["gross_amount"]
        units = sum(int(line["quantity"]) for line in held.readiness["source"]["lines"])
        prior_receipts = (
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == ACTION_TYPE,
            ChangeProposal.status == "executed",
            receipt["approval"]["mandate_id"].astext == mandate.id,
        )
        # A revision retains cumulative exposure. Different or missing currency
        # cannot be added nominally or filtered away as a fresh budget.
        if (
            session.scalar(
                select(ChangeProposal.id)
                .where(
                    *prior_receipts,
                    receipt["currency"].astext.is_distinct_from(trusted.currency),
                )
                .limit(1)
            )
            is not None
        ):
            raise _unavailable()
        orders, used_amount, used_units = session.execute(
            select(
                func.count(),
                func.coalesce(
                    func.sum(
                        cast(receipt["source_stated_order_amount"].astext, Numeric)
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(cast(receipt["admitted_source_units"].astext, Numeric)), 0
                ),
            ).where(*prior_receipts)
        ).one()
        with localcontext() as decimal_context:
            decimal_context.prec = 160
            if (
                mandate.currency != trusted.currency
                or core.decimal(amount) > core.decimal(mandate.max_order_amount)
                or orders + 1 > mandate.max_orders
                or used_amount + core.decimal(amount)
                > core.decimal(mandate.max_total_amount)
                or used_units + units > mandate.max_total_units
            ):
                raise _unavailable()
    return trusted, claims, at


def _receipt(session, tenant_id, row, held):
    """Validate the accepted proof at its accepted instant, never renew it."""
    from reality.domain.shopify_buyer_mapping import proof_digest
    from reality.domain.shopify_order_acceptance import verify_acceptance_proof

    try:
        receipt = json.loads(row.output)
        source = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == receipt["approval_source_record_id"],
            )
        )
        if (
            row.status != "executed"
            or source is None
            or source.source_system != "tuesday"
            or source.source_type != "shopify_order_acceptance_approval"
            or source.external_id != row.id
            or source.source_artifact_id is not None
            or source.payload_hash != receipt["approval_source_hash"]
            or receipt["review_digest"] != content_digest(held.model_dump(mode="json"))
        ):
            raise ValueError("receipt_changed")
        evidence = json.loads(source.payload)
        if (
            evidence.get("purpose") != PURPOSE
            or evidence["proposal_id"] != row.id
            or evidence["review_digest"] != receipt["review_digest"]
            or proof_digest(evidence["approval_proof"])
            != receipt["approval"]["proof_digest"]
        ):
            raise ValueError("approval_evidence_changed")
        accepted = AcceptancePolicy.model_validate(evidence["trusted_policy"])
        if content_digest(accepted.model_dump()) != held.policy_digest:
            raise ValueError("accepted_policy_changed")
        claims = verify_acceptance_proof(
            evidence["approval_proof"],
            accepted,
            _expected_claims(row, held),
            instant(receipt["authorized_at"]),
        )
        if (
            claims.jti != receipt["approval"]["jti"]
            or claims.iss != receipt["approval"]["issuer"]
            or claims.sub != receipt["approval"]["subject"]
            or claims.authorization_kind != receipt["approval"]["authorization_kind"]
            or claims.mandate_id != receipt["approval"]["mandate_id"]
            or claims.mandate_revision != receipt["approval"]["mandate_revision"]
        ):
            raise ValueError("accepted_identity_changed")
        return AcceptanceReceipt.model_validate(receipt).model_dump(mode="json")
    except (KeyError, ValueError, TypeError, ValidationError) as error:
        raise _unavailable() from error


def accept_order(
    session: Session,
    tenant_id: str,
    arguments: dict,
    *,
    policy: AcceptancePolicy | None = None,
):
    """
    BUSINESS PURPOSE:
    Accept only complete exact source-backed order meaning under current verified external authority.

    BUSINESS RULE shopify_order_acceptance.accept:
    Validate current submitting token, literal-purpose issuer proof and human or finite standing mandate, exact source and selected master evidence under locks; use only closed canonical effects and commit business records with original-proof receipt atomically.
    """
    from datetime import UTC, datetime

    from reality.db.core import ImportJob
    from reality.domain.shopify_buyer_mapping import proof_digest
    from reality.domain.shopify_order_acceptance import AcceptanceCommitInput
    from reality.services.case_action_guards import execution_context, guard_operation
    from reality.services.intake import _apply_effects, _effect_scope, _outcome
    from reality.tools.application import _record_decision

    # reality-rule: shopify_order_acceptance.accept
    try:
        request = AcceptanceCommitInput.model_validate(arguments)
    except (ValueError, TypeError, ValidationError) as error:
        raise _unavailable() from error
    if (
        session.new
        or session.deleted
        or any(session.is_modified(item) for item in session.dirty)
    ):
        raise _unavailable()
    token_id = _submitter(session, tenant_id, "shopify_source_order_acceptance_accept")
    if token_id is None:
        raise _unavailable()
    lock_delivery_state(session, tenant_id)
    row, held = _retained(session, tenant_id, request.proposal_id)
    session.refresh(row, with_for_update=True)
    row, held = _retained(session, tenant_id, request.proposal_id)
    if request.review_digest != content_digest(held.model_dump(mode="json")):
        raise _unavailable()
    if row.status == "executed":
        receipt = _receipt(session, tenant_id, row, held)
        if receipt["approval"]["proof_digest"] != proof_digest(request.approval_proof):
            raise _unavailable()
        session.commit()
        return receipt
    if row.status != "proposed" or held.plan.issues:
        raise _unavailable()
    _lock_basis(session, tenant_id, held)
    trusted, claims, at = _authorize(
        session, tenant_id, row, held, request.approval_proof, token_id, policy
    )
    current = _material(
        session, tenant_id, held.request, token_id, trusted, held.observed_at
    )
    if current != held or current.plan.issues:
        raise _unavailable()
    try:
        with session.begin_nested():
            approved, created, disposition = core.store_source_record(
                session,
                tenant_id,
                "tuesday",
                "shopify_order_acceptance_approval",
                row.id,
                {
                    "purpose": PURPOSE,
                    "proposal_id": row.id,
                    "review_digest": request.review_digest,
                    "approval_proof": request.approval_proof,
                    "trusted_policy": trusted.model_dump(),
                },
                source_version_at=datetime.fromtimestamp(claims.iat, UTC),
            )
            if not created or disposition in {"stale", "conflict"}:
                raise _unavailable()
            trusted, claims, at = _authorize(
                session, tenant_id, row, held, request.approval_proof, token_id, policy
            )
            if (
                _material(
                    session,
                    tenant_id,
                    held.request,
                    token_id,
                    trusted,
                    held.observed_at,
                )
                != held
            ):
                raise _unavailable()
            with (
                _effect_scope(session, tenant_id, row.id, request.review_digest),
                core.executing_proposal(tenant_id, row.id),
                execution_context(
                    session,
                    tenant_id,
                    automatic=True,
                    proposal_id=row.id,
                    source_record_id=held.source_binding.source_record_id,
                ),
            ):
                guard_operation(
                    session,
                    tenant_id,
                    "intake_apply",
                    held.plan.model_dump(mode="json"),
                )
                records = _apply_effects(session, tenant_id, row, held.plan)
            # Authority may change while canonical SQL waits. Recheck before ANY
            # receipt/acceptance commits; a changed file rolls back all effects.
            trusted, claims, at = _authorize(
                session, tenant_id, row, held, request.approval_proof, token_id, policy
            )
            _record_decision(row, None, token_id)
            row.status = "executed"
            receipt = {
                "purpose": PURPOSE,
                "proposal_id": row.id,
                "review_digest": request.review_digest,
                "source_binding": held.source_binding.model_dump(),
                "mapping_bundle_digest": content_digest(held.mapping_bundle),
                "plan_digest": held.plan.review_digest(),
                "verification": "applied",
                "authorized_at": at.isoformat(),
                "records": [
                    {"type": kind, "id": identity} for kind, identity in records
                ],
                "approval_source_record_id": approved.id,
                "approval_source_hash": approved.payload_hash,
                "source_stated_order_amount": held.plan.effects[0].arguments[
                    "gross_amount"
                ],
                "currency": trusted.currency,
                "admitted_source_units": sum(
                    int(line["quantity"]) for line in held.readiness["source"]["lines"]
                ),
                "approval": {
                    "issuer": claims.iss,
                    "subject": claims.sub,
                    "jti": claims.jti,
                    "proof_digest": proof_digest(request.approval_proof),
                    "authorization_kind": claims.authorization_kind,
                    "mandate_id": claims.mandate_id,
                    "mandate_revision": claims.mandate_revision,
                },
                "original_source_unchanged": True,
                "import_job_input_unchanged": True,
                "payment_recorded": False,
                "stock_moved": False,
                "fulfillment_dispatched": False,
            }
            row.output = canonical_json(receipt)
            source = session.scalar(
                select(SourceRecord).where(
                    SourceRecord.tenant_id == tenant_id,
                    SourceRecord.id == held.source_binding.source_record_id,
                )
            )
            job = session.scalar(
                select(ImportJob).where(
                    ImportJob.tenant_id == tenant_id,
                    ImportJob.id == held.source_binding.import_job_id,
                )
            )
            core.emit_business_event(
                session,
                tenant_id,
                "source_record.interpreted",
                "source_record",
                source.id,
                {
                    "source_system": source.source_system,
                    "source_type": source.source_type,
                    "import_job_id": job.id,
                },
                source_record_id=source.id,
                action_id=row.id,
            )
            job.status = "completed"
            job.completed_at = core.now()
            job.error = ""
            job.next_attempt_at = None
            _outcome(
                session,
                tenant_id,
                source,
                job,
                "interpreted",
                interpreter_name="shopify_order_acceptance.apply",
                reason_code="intake_applied",
                summary="The exact externally authorized order meaning was accepted.",
                references=records,
            )
            session.flush()
        session.commit()
        return _receipt(session, tenant_id, row, held)
    except Exception:
        session.rollback()
        raise


def order_acceptance_status(session: Session, tenant_id: str, arguments: dict):
    """
    BUSINESS PURPOSE:
    Reconcile an original accepted order receipt without repeating business effects.

    BUSINESS RULE shopify_order_acceptance.status:
    Require current scoped token and same-tenant retained identity, validate original exact proof at acceptance time and return historical receipt without renewing approval or dispatching work.
    """
    # reality-rule: shopify_order_acceptance.status
    request = AcceptanceReviewInput.model_validate(arguments)
    token_id = _submitter(session, tenant_id, "shopify_source_order_acceptance_status")
    if token_id is None:
        raise _unavailable()
    row, held = _retained(session, tenant_id, request.proposal_id)
    # Wait for any original acceptance transaction, including another permitted
    # reader token, before reporting a reconciliation state. No row is changed.
    session.refresh(row, with_for_update=True)
    row, held = _retained(session, tenant_id, request.proposal_id)
    result = {
        "purpose": PURPOSE,
        "proposal_id": row.id,
        "status": row.status,
        "receipt": _receipt(session, tenant_id, row, held)
        if row.status == "executed"
        else None,
        "dispatch_performed": False,
    }

    return AcceptanceStatusResult.model_validate(result).model_dump(mode="json")
