import json
import os
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, cast, or_, select
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.orm import Session as OrmSession

from reality.agent.mcp_chat import ANTHROPIC_BASE_URL, ANTHROPIC_MODEL
from reality.agent.settings import (
    AI_PROVIDER_PRESETS,
    ai_provider_preset,
    ai_settings,
    configured_api_key_metadata,
    has_configured_api_key,
    save_ai_settings,
)
from reality.catalogs import (
    load_operational_exception_catalog,
    runtime_application_catalog,
)
from reality.db.core import (
    AppUser,
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Document,
    DocumentLine,
    Fact,
    ImportJob,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    PaymentTerm,
    PlaygroundRun,
    Reservation,
    Session,
    SourceRecord,
    Tenant,
    TenantMembership,
    uid,
)
from reality.mcp.auth import (
    active_mcp_access_tokens,
    create_mcp_access_token,
    revoke_mcp_access_token,
)
from reality.mcp.catalog import MCP_TOOL_CATALOG, validate_tool_permissions
from reality.mcp.config import configured_mcp_url
from reality.services.core import (
    Conflict,
    InvalidOperation,
    NotFound,
    activity_signal,
    add_chat_assistant_message,
    add_party_group_member,
    allocate_credit_note,
    allocate_supplier_credit_note,
    announce_customer_return,
    archive_tenant,
    assign_group_price_list,
    assign_party_price_list,
    change_proposal_count,
    change_proposals,
    chat_messages,
    chat_sessions,
    chat_suggestions,
    close_stale_promises,
    connector_shells,
    correct_lot_expiry,
    correct_manual_document,
    correct_manual_document_lines,
    correct_movement,
    create_chat_session,
    create_handling_unit,
    create_item,
    create_location,
    create_lot,
    create_manual_document_with_lines,
    create_manual_order,
    create_party,
    create_party_group,
    create_payment_term,
    create_price_list,
    create_price_list_entry,
    create_serial_unit,
    create_source_capability,
    create_source_system,
    create_tenant,
    decision_maker_names,
    delete_chat_session,
    document_detail,
    enqueue_source,
    ensure_demo,
    execute_payment_run,
    expired_lots,
    get_tenant,
    handling_units,
    historical_pricing_explanation,
    hold_commitment,
    hold_document_commitments,
    hold_party_delivery,
    import_jobs,
    install_connector_shell,
    integration_registry,
    item_detail,
    items,
    ledger_reversal_snapshot,
    location_detail,
    locations,
    lots,
    manual_document_line_snapshot,
    movement_correction_snapshot,
    observe_fact,
    parties,
    party_detail,
    party_groups,
    payment_terms,
    permanently_delete_tenant,
    post_customer_payment,
    post_customer_refund,
    post_sales_credit_note,
    post_sales_invoice,
    post_supplier_credit_note,
    post_supplier_invoice,
    post_supplier_payment,
    post_supplier_refund,
    preview_ledger_reversal,
    preview_movement_correction,
    preview_payment_run,
    preview_stale_promise_closure,
    price_list_entries,
    price_lists,
    process_pending_import_jobs,
    record_corrected_document_source,
    record_movement,
    release_commitment_hold,
    release_document_holds,
    release_party_delivery_hold,
    reserve,
    restore_chat_session,
    restore_tenant,
    retry_import_job,
    return_announcements,
    reverse_ledger_posting_group,
    revise_commitment,
    send_chat_message,
    serial_units,
    set_master_data_active,
    set_source_capability_active,
    set_source_system_active,
    source_capabilities,
    source_records,
    source_systems,
    state_lot_expiry,
    tenant_usage_summaries,
    tenants,
    timeline_activity,
    update_item,
    update_location,
    update_party,
    update_party_group,
    update_payment_term,
    update_price_list,
    withdraw_return_announcement,
)
from reality.services.inspector_presentation import display_parts, display_text, money
from reality.services.inspector_register import inspector_records
from reality.services.memberships import (
    Principal,
    access_summary,
    create_invitation,
    remove_member,
    resend_invitation,
    revoke_invitation,
)
from reality.services.projections import (
    FULFILLMENT_BLOCKERS,
    FULFILLMENT_QUEUE,
    ITEM_SUPPLY_DEMAND,
    OPEN_FINANCIAL_ITEMS,
    materialized_resolve_price,
    projection_rows,
    projection_snapshot,
)
from reality.services.reality_gaps import (
    activate_rule,
    add_gap_entry,
    capture_gap,
    decide_gap,
    disable_rule,
    gap_detail,
    list_gaps,
    prepare_implementation,
    recommend_gap,
    replay_rule,
    search_source_examples,
    simulate_rule,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    proposals_awaiting_approval,
    reject_proposal,
)
from reality.web.read_models import (
    commitment_page,
    document_page,
    exception_page,
    inventory_page,
    journal_page,
    model_count,
    page_for,
    payment_page,
    payment_totals,
    projection_page,
)

public_router = APIRouter(prefix="/api/v1", tags=["application"])


def database_session():
    with Session() as session:
        yield session


DatabaseSession = Annotated[OrmSession, Depends(database_session)]


def require_tenant_surface_access(
    request: Request, tenant_id: str, session: DatabaseSession
) -> None:
    """Keep sandbox inspection private even when development auth is disabled."""
    from reality.services.tenant_policy import (
        PlaygroundOperationDenied,
        require_playground_run,
    )
    from reality.web.auth import user_from_request

    with session.no_autoflush:
        purpose = session.scalar(select(Tenant.purpose).where(Tenant.id == tenant_id))
    user = getattr(request.state, "user", None)
    if purpose != "playground":
        if user and user.status != "active" and not user.is_platform_admin:
            raise HTTPException(403, "Access approval is still pending.")
        return
    user = user_from_request(request, session)
    if user is None:
        raise HTTPException(401, "Authentication required.")
    run_id = session.scalar(
        select(PlaygroundRun.id).where(
            PlaygroundRun.tenant_id == tenant_id,
            PlaygroundRun.owner_user_id == user.id,
        )
    )
    if run_id is None:
        raise HTTPException(404, "Playground run not found.")
    try:
        run = require_playground_run(session, run_id, user.id)
    except NotFound as exc:
        raise HTTPException(404, "Playground run not found.") from exc
    if run.status not in {"active", "archived"}:
        raise PlaygroundOperationDenied("This Playground run is not ready.")
    from reality.services.tenant_policy import practice_company_runs

    if tenant_id in practice_company_runs(session, user.id):
        return
    route = request.scope["route"].path.removeprefix("/api/tenants/{tenant_id}")
    readable = {
        "/items",
        "/items/{record_id}",
        "/parties",
        "/parties/{record_id}",
        "/locations",
        "/locations/{record_id}",
        "/facts",
        "/exceptions",
        "/inventory-control",
        "/commitment-control",
        "/finance/open-items",
        "/evidence-documents",
        "/movements",
        "/reservations",
        "/timeline",
        "/change-proposals",
    }
    inspector = route == "/inspector/{kind}/{record_id}" and request.path_params.get(
        "kind"
    ) in {
        "document",
        "fact",
        "commitment",
        "party",
        "item",
        "location",
        "reservation",
        "movement",
        "shipment",
        "shipment_package",
        "exception",
    }
    analytics_read = (request.method == "GET" and route == "/analytics/catalog") or (
        request.method == "POST"
        and route
        in {"/analytics/query", "/analytics/query/contributors", "/analytics/export"}
    )
    if not analytics_read and (
        request.method != "GET" or (route not in readable and not inspector)
    ):
        raise PlaygroundOperationDenied("Playground does not support this operation.")


router = APIRouter(
    prefix="/api/tenants/{tenant_id}",
    tags=["master-data"],
    dependencies=[Depends(require_tenant_surface_access)],
)


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TenantSummary(ApiModel):
    id: str
    name: str
    role: str | None = None
    purpose: str | None = None
    sandbox_run_id: str | None = None
    company_kind: str | None = None
    demo_data_state: str | None = None


class ApplicationBootstrap(ApiModel):
    tenants: list[TenantSummary]
    default_tenant_id: str | None


class CompanyCreate(ApiModel):
    name: str = Field(min_length=1, max_length=200)
    guided_demo: bool = False


class CompanyDelete(ApiModel):
    confirmation_name: str
    confirmation_word: str


class AISettingsWrite(ApiModel):
    provider_preset: str = "local"
    model: str = ""
    custom_base_url: str = ""
    api_key: str = ""
    clear_api_key: bool = False


class MCPTokenWrite(ApiModel):
    name: str = Field(min_length=1, max_length=100)
    allowed_tools: list[str] = Field(default_factory=lambda: ["*"])


class InvitationWrite(ApiModel):
    email: str = Field(min_length=3, max_length=320)
    locale: str = "en"


def request_principal(request: Request) -> Principal:
    user: AppUser | None = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return Principal(user.id, user.is_platform_admin)


def optional_request_principal(request: Request) -> Principal | None:
    user: AppUser | None = getattr(request.state, "user", None)
    if user is None:
        return None
    return Principal(user.id, user.is_platform_admin)


def visible_tenant_ids(request: Request, session: OrmSession) -> set[str] | None:
    user: AppUser | None = getattr(request.state, "user", None)
    if not user or user.is_platform_admin:
        return None
    return set(
        session.scalars(
            select(TenantMembership.tenant_id).where(
                TenantMembership.user_id == user.id, TenantMembership.status == "active"
            )
        ).all()
    )


def require_company_owner(
    request: Request, session: OrmSession, tenant_id: str
) -> None:
    user: AppUser | None = getattr(request.state, "user", None)
    if not user or user.is_platform_admin:
        return
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == user.id,
            TenantMembership.status == "active",
            TenantMembership.role == "owner",
        )
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Company owner access required.")


@public_router.get(
    "/bootstrap",
    response_model=ApplicationBootstrap,
    response_model_exclude_none=True,
)
def application_bootstrap(request: Request, session: DatabaseSession):
    """Return only the identity data required to start an independent client."""
    allowed = visible_tenant_ids(request, session)
    from reality.services.tenant_policy import practice_company_runs
    from reality.web.auth import user_from_request

    user = getattr(request.state, "user", None) or user_from_request(request, session)
    practice = practice_company_runs(session, user.id) if user else {}
    rows = [
        row
        for row in tenants(session)
        if (row.purpose == "business" or row.id in practice)
        and (allowed is None or row.id in allowed)
    ]
    roles = (
        {
            membership.tenant_id: membership.role
            for membership in session.scalars(
                select(TenantMembership).where(
                    TenantMembership.user_id == user.id,
                    TenantMembership.status == "active",
                )
            )
        }
        if user
        else {}
    )
    from reality.services.company_setup import _company_presentation

    presentation = (
        _company_presentation(session, user.id, [row.id for row in rows])
        if user
        else {}
    )
    return ApplicationBootstrap(
        tenants=[
            TenantSummary(
                id=tenant.id,
                name=tenant.name,
                role=roles.get(tenant.id),
                purpose="playground" if tenant.id in practice else None,
                sandbox_run_id=practice.get(tenant.id),
                **presentation.get(tenant.id, {}),
            )
            for tenant in rows
        ],
        default_tenant_id=next(
            (row.id for row in rows if row.purpose == "business"),
            rows[0].id if rows else None,
        ),
    )


@public_router.get("/companies")
def company_management(request: Request, session: DatabaseSession):
    """Return bounded lifecycle and usage data for every company."""
    usage = tenant_usage_summaries(session)
    allowed = visible_tenant_ids(request, session)
    from reality.services.tenant_policy import practice_company_runs
    from reality.web.auth import user_from_request

    user = getattr(request.state, "user", None) or user_from_request(request, session)
    practice = practice_company_runs(session, user.id) if user else {}
    roles = (
        {
            membership.tenant_id: membership.role
            for membership in session.scalars(
                select(TenantMembership).where(
                    TenantMembership.user_id == user.id,
                    TenantMembership.status == "active",
                )
            )
        }
        if user
        else {}
    )
    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "created_at": tenant.created_at,
            "archived_at": tenant.archived_at,
            "role": roles.get(tenant.id),
            **(
                {"purpose": "playground", "sandbox_run_id": practice[tenant.id]}
                if tenant.id in practice
                else {}
            ),
            **usage[tenant.id],
        }
        for tenant in tenants(session, include_archived=True)
        if tenant.purpose == "business" or tenant.id in practice
        if allowed is None or tenant.id in allowed
    ]


@public_router.post("/companies", status_code=status.HTTP_201_CREATED)
def create_company(body: CompanyCreate, request: Request, session: DatabaseSession):
    try:
        tenant = create_tenant(session, body.name)
        user: AppUser | None = getattr(request.state, "user", None)
        if user:
            session.add(
                TenantMembership(
                    id=uid("mem"), tenant_id=tenant.id, user_id=user.id, role="owner"
                )
            )
            session.commit()
        if body.guided_demo:
            ensure_demo(session, tenant)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    return {"id": tenant.id, "name": tenant.name}


@public_router.post("/companies/{tenant_id}/archive")
def archive_company(tenant_id: str, request: Request, session: DatabaseSession):
    require_company_owner(request, session, tenant_id)
    try:
        tenant = archive_tenant(session, tenant_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    return {"id": tenant.id, "name": tenant.name, "archived_at": tenant.archived_at}


@public_router.post("/companies/{tenant_id}/restore")
def restore_company(tenant_id: str, request: Request, session: DatabaseSession):
    require_company_owner(request, session, tenant_id)
    try:
        tenant = restore_tenant(session, tenant_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    return {"id": tenant.id, "name": tenant.name, "archived_at": tenant.archived_at}


@public_router.post(
    "/companies/{tenant_id}/delete", status_code=status.HTTP_204_NO_CONTENT
)
def delete_company(
    tenant_id: str, body: CompanyDelete, request: Request, session: DatabaseSession
):
    require_company_owner(request, session, tenant_id)
    try:
        permanently_delete_tenant(
            session,
            tenant_id,
            confirmation_name=body.confirmation_name,
            confirmation_word=body.confirmation_word,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/settings/ai")
def get_ai_configuration(tenant_id: str, request: Request, session: DatabaseSession):
    require_company_owner(request, session, tenant_id)
    settings = ai_settings(session, tenant_id)
    key_metadata = configured_api_key_metadata(settings)
    company_mode = settings.provider in {
        "anthropic",
        "openai_compatible",
    } and has_configured_api_key(settings)
    preset = (
        ai_provider_preset(settings.provider, settings.base_url)
        if company_mode
        else "managed"
    )
    return {
        "copilot": {
            "managed": True,
            "available": company_mode
            or bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
            "provider_name": "Anthropic",
            "credential_mode": "company" if company_mode else "managed",
            "provider_preset": preset,
            "model": settings.model if company_mode else "",
            "base_url": settings.base_url if company_mode else "",
            "presets": AI_PROVIDER_PRESETS,
            "has_company_api_key": company_mode,
            "api_key_fingerprint": key_metadata.fingerprint
            if company_mode and key_metadata
            else "",
        },
        "mcp_url": configured_mcp_url(),
        "tools": [tool.public_metadata() for tool in MCP_TOOL_CATALOG],
        "tokens": [
            {
                "id": token.id,
                "name": token.name,
                "token_prefix": token.token_prefix,
                "allowed_tools": validate_tool_permissions(
                    json.loads(token.allowed_tools)
                ),
                "created_at": token.created_at,
                "last_used_at": token.last_used_at,
            }
            for token in active_mcp_access_tokens(session, tenant_id)
        ],
    }


@router.get("/settings/members")
def company_members(tenant_id: str, request: Request, session: DatabaseSession):
    try:
        result = access_summary(session, tenant_id, request_principal(request))
        session.commit()
        return result
    except (NotFound, InvalidOperation, Conflict) as error:
        raise api_error(error) from error


@router.post("/settings/invitations", status_code=status.HTTP_202_ACCEPTED)
def invite_company_member(
    tenant_id: str,
    body: InvitationWrite,
    request: Request,
    session: DatabaseSession,
):
    try:
        create_invitation(
            session,
            tenant_id,
            request_principal(request),
            body.email,
            locale=body.locale,
        )
        session.commit()
        return {"status": "pending"}
    except (NotFound, InvalidOperation, Conflict) as error:
        raise api_error(error) from error


@router.post("/settings/invitations/{invitation_id}/resend")
def resend_company_invitation(
    tenant_id: str,
    invitation_id: str,
    request: Request,
    session: DatabaseSession,
):
    try:
        invitation = resend_invitation(
            session, tenant_id, request_principal(request), invitation_id
        )
        session.commit()
        return {"id": invitation.id, "status": invitation.status}
    except (NotFound, InvalidOperation, Conflict) as error:
        raise api_error(error) from error


@router.post("/settings/invitations/{invitation_id}/revoke", status_code=204)
def revoke_company_invitation(
    tenant_id: str,
    invitation_id: str,
    request: Request,
    session: DatabaseSession,
):
    try:
        revoke_invitation(session, tenant_id, request_principal(request), invitation_id)
        session.commit()
    except (NotFound, InvalidOperation, Conflict) as error:
        raise api_error(error) from error


@router.post("/settings/members/{membership_id}/remove", status_code=204)
def remove_company_member(
    tenant_id: str,
    membership_id: str,
    request: Request,
    session: DatabaseSession,
):
    try:
        remove_member(session, tenant_id, request_principal(request), membership_id)
        session.commit()
    except (NotFound, InvalidOperation, Conflict) as error:
        raise api_error(error) from error


@router.put("/settings/ai")
def put_ai_configuration(
    tenant_id: str,
    body: AISettingsWrite,
    request: Request,
    session: DatabaseSession,
):
    require_company_owner(request, session, tenant_id)
    if body.provider_preset in {"managed", "company", "anthropic"}:
        try:
            settings = save_ai_settings(
                session,
                tenant_id,
                provider="anthropic"
                if body.provider_preset in {"company", "anthropic"}
                else "local",
                model=ANTHROPIC_MODEL
                if body.provider_preset in {"company", "anthropic"}
                else "",
                base_url=ANTHROPIC_BASE_URL
                if body.provider_preset in {"company", "anthropic"}
                else "",
                api_key=body.api_key,
                clear_api_key=body.provider_preset == "managed",
            )
        except (NotFound, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        key_metadata = configured_api_key_metadata(settings)
        company_mode = settings.provider == "anthropic" and has_configured_api_key(
            settings
        )
        return {
            "copilot": {
                "managed": True,
                "available": company_mode
                or bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
                "provider_name": "Anthropic",
                "credential_mode": "company" if company_mode else "managed",
                "has_company_api_key": company_mode,
                "api_key_fingerprint": key_metadata.fingerprint
                if company_mode and key_metadata
                else "",
            }
        }
    preset = next(
        (entry for entry in AI_PROVIDER_PRESETS if entry["id"] == body.provider_preset),
        None,
    )
    if preset is None:
        raise HTTPException(status_code=400, detail="Unsupported AI provider preset.")
    try:
        settings = save_ai_settings(
            session,
            tenant_id,
            provider="local"
            if body.provider_preset == "local"
            else "openai_compatible",
            model=body.model,
            base_url=body.custom_base_url
            if body.provider_preset == "custom"
            else preset["base_url"],
            api_key=body.api_key,
            clear_api_key=body.clear_api_key,
        )
    except (NotFound, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    key_metadata = configured_api_key_metadata(settings)
    return {
        "provider": settings.provider,
        "model": settings.model,
        "base_url": settings.base_url,
        "has_api_key": has_configured_api_key(settings),
        "api_key_fingerprint": key_metadata.fingerprint if key_metadata else "",
    }


@router.post("/settings/mcp/tokens", status_code=status.HTTP_201_CREATED)
def post_mcp_token(
    tenant_id: str,
    body: MCPTokenWrite,
    request: Request,
    session: DatabaseSession,
):
    require_company_owner(request, session, tenant_id)
    try:
        record, clear_token = create_mcp_access_token(
            session, tenant_id, body.name, body.allowed_tools
        )
    except (NotFound, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "id": record.id,
        "name": record.name,
        "token": clear_token,
        "token_prefix": record.token_prefix,
        "allowed_tools": validate_tool_permissions(json.loads(record.allowed_tools)),
    }


@router.post(
    "/settings/mcp/tokens/{token_id}/revoke", status_code=status.HTTP_204_NO_CONTENT
)
def post_mcp_token_revoke(
    tenant_id: str,
    token_id: str,
    request: Request,
    session: DatabaseSession,
):
    require_company_owner(request, session, tenant_id)
    try:
        revoke_mcp_access_token(session, tenant_id, token_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/warehouse/{view}")
def get_warehouse_register(
    tenant_id: str,
    view: Literal["stock", "reservations", "movements"],
    session: DatabaseSession,
    q: str = Query("", max_length=500),
    state: str = "",
    item_id: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    sort: Literal[
        "",
        "id",
        "name",
        "physical",
        "reserved",
        "available",
        "date",
        "quantity",
        "status",
        "type",
    ] = "",
    sort_direction: Literal["asc", "desc"] = "asc",
):
    from reality.web.warehouse_reads import warehouse_register

    try:
        return warehouse_register(
            session,
            tenant_id,
            view,
            query=q,
            state=state,
            item_id=item_id,
            page=page,
            size=size,
            sort=sort,
            sort_direction=sort_direction,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/attention")
def get_attention_register(
    tenant_id: str,
    session: DatabaseSession,
    q: str = Query("", max_length=500),
    severity: str = "",
    class_id: str = Query("", max_length=120),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    from reality.services.attention_reads import attention_register

    try:
        return json.loads(
            json.dumps(
                attention_register(
                    session,
                    tenant_id,
                    query=q,
                    severity=severity,
                    class_id=class_id,
                    page=page,
                    size=size,
                ),
                default=str,
            )
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/attention/summary")
def get_attention_summary(tenant_id: str, session: DatabaseSession):
    """Open findings per exception class; declared before the identity route on purpose."""
    from reality.services.attention_reads import attention_summary

    try:
        return json.loads(
            json.dumps(attention_summary(session, tenant_id), default=str)
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/attention/{identity}")
def get_attention_detail(tenant_id: str, identity: str, session: DatabaseSession):
    from reality.services.attention_reads import FindingCleared, attention_detail

    try:
        return json.loads(
            json.dumps(attention_detail(session, tenant_id, identity), default=str)
        )
    except FindingCleared as error:
        # Not found, but a distinguishable kind of it: the stored generation still
        # lists this finding while the current records no longer derive it.
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": str(error),
                "code": error.code,
                "completed_at": error.completed_at,
            },
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


ReferenceFamily = Literal["customer", "supplier", "item", "location"]
AnalyticsMetric = Literal[
    "open",
    "fully_reserved",
    "needs_reservation",
    "overdue",
    "unknown_due",
    "created",
    "shipped",
]


@router.get("/activity-volume")
def get_activity_volume(
    tenant_id: str, session: DatabaseSession, days: int = Query(30)
):
    from reality.services.activity_volume import volume

    try:
        return volume(session, tenant_id, days=days)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/activity-volume/events")
def get_activity_volume_events(
    tenant_id: str, session: DatabaseSession, start: str, end: str
):
    from datetime import datetime

    from reality.services.activity_volume import details

    try:
        return details(
            session,
            tenant_id,
            start=datetime.fromisoformat(start),
            end=datetime.fromisoformat(end),
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/readiness")
def tenant_readiness(tenant_id: str, session: DatabaseSession):
    from reality.services.system_readiness import readiness

    try:
        return readiness(session, tenant_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/analytics")
def get_company_insights(
    tenant_id: str, session: DatabaseSession, days: int = Query(30, ge=7, le=90)
):
    from reality.services.company_insights import company_insights

    try:
        return company_insights(session, tenant_id, days=days)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/analytics/contributors")
def get_insight_contributors(
    tenant_id: str,
    session: DatabaseSession,
    metric: AnalyticsMetric,
    days: int = Query(30, ge=7, le=90),
    day: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    from reality.services.company_insights import insight_contributors

    try:
        return insight_contributors(
            session, tenant_id, metric=metric, days=days, day=day, page=page, size=size
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/master-data")
def get_reference_register(
    tenant_id: str,
    session: DatabaseSession,
    family: ReferenceFamily,
    q: str = Query("", max_length=500),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    include_inactive: bool = False,
    sort: Literal["", "id", "name", "status"] = "",
    sort_direction: Literal["asc", "desc"] = "asc",
):
    from reality.services.reference_workspace import reference_register

    try:
        return reference_register(
            session,
            tenant_id,
            family,
            query=q,
            page=page,
            size=size,
            sort=sort,
            sort_direction=sort_direction,
            include_inactive=include_inactive,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


class ReferencePrepare(ApiModel):
    model_config = ConfigDict(extra="forbid")
    family: ReferenceFamily
    operation: Literal["create", "update"]
    request_id: str = Field(min_length=1, max_length=200)
    record: dict[str, Any]


class ReferenceConfirm(ApiModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: Literal[True]


@router.post("/master-data/prepare")
def post_reference_prepare(
    tenant_id: str, body: ReferencePrepare, request: Request, session: DatabaseSession
):
    from reality.services.reference_workspace import (
        prepare_reference,
        reference_proposal,
    )

    try:
        principal = optional_request_principal(request)
        proposal = prepare_reference(
            session,
            tenant_id,
            body.family,
            body.operation,
            body.record,
            request_id=body.request_id,
            actor_id=principal.user_id if principal else "local",
        )
        return reference_proposal(session, tenant_id, proposal.id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/master-data/proposals/{proposal_id}")
def get_reference_proposal(tenant_id: str, proposal_id: str, session: DatabaseSession):
    from reality.services.reference_workspace import reference_proposal

    try:
        return reference_proposal(session, tenant_id, proposal_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/master-data/proposals/{proposal_id}/confirm")
def post_reference_confirm(
    tenant_id: str,
    proposal_id: str,
    body: ReferenceConfirm,
    request: Request,
    session: DatabaseSession,
):
    from reality.services.delivery_actions import require_delivery_principal
    from reality.services.reference_workspace import (
        reference_proposal,
        require_ordinary_workspace,
    )
    from reality.tools.application import approve_and_execute_proposal

    try:
        principal = optional_request_principal(request)
        require_delivery_principal(session, tenant_id, principal)
        require_ordinary_workspace(session, tenant_id)
        reference_proposal(session, tenant_id, proposal_id)
        approve_and_execute_proposal(
            session,
            tenant_id,
            proposal_id,
            confirming_principal=principal,
            confirmed=body.confirmed,
        )
        return reference_proposal(session, tenant_id, proposal_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/master-data/{family}/{record_id}")
def get_reference_detail(
    tenant_id: str, family: ReferenceFamily, record_id: str, session: DatabaseSession
):
    from reality.services.reference_workspace import reference_detail

    try:
        return reference_detail(session, tenant_id, family, record_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


class DeliveryActionPrepare(ApiModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=200)
    tool: Literal[
        "order_create",
        "ledger_reverse",
        "sales_invoice_record",
        "sales_credit_record",
        "supplier_invoice_record",
        "customer_payment_post",
        "customer_refund_post",
        "supplier_payment_post",
        "reserve",
        "movement_create",
        "movement_correct",
        "reservation_release",
        "party_delivery_hold",
        "party_delivery_hold_release",
        "commitment_hold",
        "commitment_hold_release",
        "shipment_notice_record",
        "shipment_dispatch",
        "shipment_receive",
        "shipment_event_record",
        "shipment_event_supersede",
    ]
    arguments: dict[str, Any]
    session_id: str | None = None


@router.post("/delivery-actions/prepare")
def post_delivery_prepare(
    tenant_id: str,
    body: DeliveryActionPrepare,
    request: Request,
    session: DatabaseSession,
):
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        if body.session_id:
            chat_messages(session, tenant_id, body.session_id)
        principal = optional_request_principal(request)
        proposal = prepare_delivery_action(
            session,
            tenant_id,
            body.tool,
            body.arguments,
            request_id=body.request_id,
            actor_id=principal.user_id if principal else "local",
        )
        return delivery_proposal_detail(session, tenant_id, proposal.id)
    except (NotFound, InvalidOperation, TypeError) as error:
        if isinstance(error, TypeError):
            raise HTTPException(
                status_code=422, detail="Check the action fields."
            ) from error
        raise api_error(error) from error


@router.post("/delivery-actions/{proposal_id}/reconcile")
def post_delivery_reconcile(tenant_id: str, proposal_id: str, session: DatabaseSession):
    from reality.services.delivery_actions import reconcile_delivery

    try:
        return reconcile_delivery(session, tenant_id, proposal_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/delivery-actions/{proposal_id}")
def get_delivery_proposal(tenant_id: str, proposal_id: str, session: DatabaseSession):
    from reality.services.delivery_actions import delivery_proposal_detail

    try:
        return delivery_proposal_detail(session, tenant_id, proposal_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/delivery-actions/{proposal_id}/review")
def post_delivery_review(tenant_id: str, proposal_id: str, session: DatabaseSession):
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        review_existing,
    )

    try:
        review_existing(session, tenant_id, proposal_id)
        return delivery_proposal_detail(session, tenant_id, proposal_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/customer-holds/{party_id}")
def get_customer_hold_context(tenant_id: str, party_id: str, session: DatabaseSession):
    from reality.services.customer_hold_actions import customer_hold_context

    try:
        return customer_hold_context(session, tenant_id, party_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/delivery-references")
def get_delivery_references(
    tenant_id: str,
    session: DatabaseSession,
    commitment_id: str,
    family: str,
    q: str = "",
):
    from reality.services.delivery_reads import delivery_references

    try:
        return delivery_references(session, tenant_id, commitment_id, family, q)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/delivery-work")
def get_delivery_work(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    status: str = "open",
    commitment_type: str = "customer_delivery",
    document_id: str = "",
    sort: Literal["", "id", "counterparty", "item", "due_at", "open", "status"] = "",
    sort_direction: Literal["asc", "desc"] = "asc",
):
    from reality.services.delivery_reads import delivery_work

    try:
        return delivery_work(
            session,
            tenant_id,
            page=page,
            size=size,
            sort=sort,
            sort_direction=sort_direction,
            query=q,
            status=status,
            commitment_type=commitment_type,
            document_id=document_id,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/shipments")
def get_shipments(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    direction: Literal["", "inbound", "outbound"] = "",
    purpose: Literal[
        "",
        "customer_delivery",
        "supplier_delivery",
        "customer_return",
        "supplier_return",
    ] = "",
    counterparty_id: str = "",
    carrier: str = "",
    tracking: str = "",
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    observation: Literal[
        "",
        "announced",
        "dispatched",
        "received",
        "externally_delivered",
        "has_exception",
    ] = "",
):
    from reality.services.shipments import shipments_list

    try:
        return shipments_list(
            session,
            tenant_id,
            page=page,
            size=size,
            query=q,
            direction=direction,
            purpose=purpose,
            counterparty_id=counterparty_id,
            carrier=carrier,
            tracking=tracking,
            created_from=created_from,
            created_to=created_to,
            observation=observation,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/shipments/{shipment_id}")
def get_shipment(tenant_id: str, shipment_id: str, session: DatabaseSession):
    from reality.services.shipments import shipment_explain

    try:
        return shipment_explain(session, tenant_id, shipment_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/delivery-work/{commitment_id}")
def get_delivery_case(
    tenant_id: str,
    commitment_id: str,
    session: DatabaseSession,
    before: int | None = Query(None, ge=1),
):
    from reality.services.delivery_reads import delivery_case

    try:
        return delivery_case(session, tenant_id, commitment_id, before=before)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/dashboard")
def tenant_dashboard(tenant_id: str, session: DatabaseSession):
    """Compact, bounded control state for the operations landing surface."""
    try:
        tenant = get_tenant(session, tenant_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    from reality.services.delivery_reads import delivery_work

    open_deliveries = delivery_work(session, tenant_id, size=1)["page"]["total"]
    exception_rows, exception_pager = exception_page(session, tenant_id, size=5)
    inventory_rows, inventory_pager = inventory_page(session, tenant_id, size=8)
    fact_rows = list(
        session.scalars(
            select(Fact)
            .where(Fact.tenant_id == tenant_id)
            .order_by(Fact.observed_at.desc())
            .limit(5)
        )
    )
    source_ids = {row.source_record_id for row in fact_rows if row.source_record_id}
    fact_sources = (
        {
            row.id: row
            for row in session.scalars(
                select(SourceRecord).where(
                    SourceRecord.tenant_id == tenant_id, SourceRecord.id.in_(source_ids)
                )
            )
        }
        if source_ids
        else {}
    )
    source_count = model_count(session, SourceRecord, tenant_id)
    fact_count = model_count(session, Fact, tenant_id)
    movement_count = model_count(session, Movement, tenant_id)
    ledger_count = model_count(session, LedgerEntry, tenant_id)
    document_count = model_count(session, Document, tenant_id)
    commitment_count = model_count(session, Commitment, tenant_id)
    return {
        "tenant": {"id": tenant.id, "name": tenant.name},
        "totals": {
            "open_deliveries": open_deliveries,
            "exceptions": exception_pager.total,
            "open_commitments": model_count(
                session, Commitment, tenant_id, Commitment.status == "open"
            ),
            "stocked_items": inventory_pager.total,
            "documents": document_count,
            "payments": model_count(
                session, LedgerEntry, tenant_id, LedgerEntry.account == "cash"
            ),
            "sources": source_count,
            "facts": fact_count,
            "pending_decisions": model_count(
                session, ChangeProposal, tenant_id, ChangeProposal.status == "proposed"
            ),
            "decision_history": model_count(
                session,
                ChangeProposal,
                tenant_id,
                ChangeProposal.status.in_(("executed", "rejected")),
            ),
        },
        "sample_scope": {
            "exceptions": {
                "limit": 5,
                "total": exception_pager.total,
                "has_more": exception_pager.total > len(exception_rows),
            },
            "inventory": {
                "limit": 8,
                "total": inventory_pager.total,
                "has_more": inventory_pager.total > len(inventory_rows),
            },
            "facts": {
                "limit": 5,
                "total": fact_count,
                "has_more": fact_count > len(fact_rows),
            },
        },
        "exceptions": exception_rows,
        "inventory": [_inventory_response(row) for row in inventory_rows],
        "facts": [
            {
                "id": row.id,
                "subject_type": row.subject_type,
                "subject_id": row.subject_id,
                "predicate": row.predicate,
                "value": row.value,
                "observed_at": row.observed_at,
                "source": (
                    {
                        "system": fact_sources[row.source_record_id].source_system,
                        "type": fact_sources[row.source_record_id].source_type,
                        "external_id": fact_sources[row.source_record_id].external_id,
                    }
                    if row.source_record_id in fact_sources
                    else None
                ),
            }
            for row in fact_rows
        ],
        "capabilities": {
            "sources": source_count > 0,
            "facts": fact_count > 0,
            "operations": document_count > 0 or commitment_count > 0,
            "warehouse": movement_count > 0 or inventory_pager.total > 0,
            "finance": ledger_count > 0,
            "activity": bool(
                exception_pager.total
                or model_count(session, ChangeProposal, tenant_id)
                or source_count
                or fact_count
                or document_count
                or commitment_count
                or movement_count
                or ledger_count
            ),
        },
    }


@router.get("/facts")
def tenant_facts(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    subject_type: str = "",
    subject_id: str = "",
    source_record_id: str = "",
    sort: Literal["", "id", "predicate", "value", "subject_type", "observed_at"] = "",
    sort_direction: Literal["asc", "desc"] = "asc",
):
    """Recorded observations, without selecting a current or valid winner."""
    from reality.web.fact_reads import fact_page

    get_tenant(session, tenant_id)
    return fact_page(
        session,
        tenant_id,
        query=q,
        subject_type=subject_type,
        subject_id=subject_id,
        source_record_id=source_record_id,
        page=page,
        size=size,
        sort=sort,
        sort_direction=sort_direction,
    )


@router.get("/exceptions")
def tenant_exceptions(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    get_tenant(session, tenant_id)
    rows, pager = exception_page(session, tenant_id, page=page, size=size)
    return {
        "items": rows,
        "page": _page_response(pager),
    }


@router.get("/inventory-control")
def tenant_inventory_control(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    state: str = "",
):
    get_tenant(session, tenant_id)
    rows, pager = inventory_page(
        session, tenant_id, page=page, size=size, query=q, stock_state=state
    )
    return {
        "items": [_inventory_response(row) for row in rows],
        "page": _page_response(pager),
    }


@router.get("/commitment-control")
def tenant_commitment_control(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    commitment_status: str = "open",
    commitment_type: str = "",
    due_from: str = "",
    due_to: str = "",
):
    get_tenant(session, tenant_id)
    rows, pager = commitment_page(
        session,
        tenant_id,
        page=page,
        size=size,
        query=q,
        status=commitment_status,
        commitment_type=commitment_type,
        due_from=due_from,
        due_to=due_to,
    )
    return {
        "items": [
            {
                "id": commitment.id,
                "risk": risk.lower().replace(" ", "_"),
                "type": commitment.type,
                "due_at": commitment.due_at.isoformat() if commitment.due_at else None,
                "counterparty": counterparty,
                "item_id": commitment.item_id,
                "location_id": commitment.location_id,
                "item": item,
                "quantity": str(commitment.quantity),
                "open_quantity": str(open_quantity_value),
                "reserved": str(reserved),
                "status": commitment.status,
                "document_id": commitment.document_id,
            }
            for commitment, risk, counterparty, item, reserved, open_quantity_value in rows
        ],
        "page": _page_response(pager),
    }


@router.get("/evidence-documents")
def tenant_evidence_documents(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    document_type: str = "",
    document_status: str = "",
    source_system: str = "",
    source_record_id: str = "",
    sort: Literal[
        "", "id", "number", "date", "type", "status", "amount", "currency"
    ] = "",
    sort_direction: Literal["asc", "desc"] = "asc",
):
    get_tenant(session, tenant_id)
    rows, pager = document_page(
        session,
        tenant_id,
        page=page,
        size=size,
        sort=sort,
        sort_direction=sort_direction,
        query=q,
        document_type=document_type,
        status=document_status,
        source_system=source_system,
        source_record_id=source_record_id,
    )
    party_ids = {document.party_id for document, _, _, _ in rows if document.party_id}
    party_names = (
        {
            party.id: party.name
            for party in session.scalars(
                select(Party).where(
                    Party.tenant_id == tenant_id, Party.id.in_(party_ids)
                )
            )
        }
        if party_ids
        else {}
    )
    return {
        "items": [
            {
                "id": document.id,
                "date": _iso_value(document.document_date),
                "type": document.type,
                "number": document.number,
                "party_id": document.party_id,
                "party": party_names.get(document.party_id, "—"),
                "currency": document.currency,
                "gross_amount": str(document.gross_amount),
                "line_count": len(lines),
                "reality_link_count": len(commitments),
                "source": {
                    "system": source.source_system,
                    "type": source.source_type,
                    "external_id": source.external_id,
                }
                if source
                else None,
                "status": document.status,
            }
            for document, source, lines, commitments in rows
        ],
        "page": _page_response(pager),
    }


@router.get("/finance/open-items")
def tenant_open_items(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    flow: str = "",
    item_status: str = "",
    party_id: str = "",
    credit_only: bool = False,
    sort: Literal[
        "",
        "id",
        "number",
        "party",
        "date",
        "status",
        "gross",
        "settled",
        "open",
        "overdue",
        "credit",
        "balance",
        "oldest_due",
    ] = "",
    sort_direction: Literal["asc", "desc"] = "asc",
):
    if flow in {"customer-balances", "supplier-balances"}:
        from reality.services.finance.balances import party_balances

        try:
            return party_balances(
                session,
                tenant_id,
                side="customer" if flow == "customer-balances" else "supplier",
                credit_only=credit_only,
                query=q,
                page=page,
                size=size,
                sort=sort or "balance",
                sort_direction=sort_direction if sort else "desc",
            )
        except (NotFound, InvalidOperation) as error:
            raise api_error(error) from error
    if flow in {"customer-balance", "supplier-balance"}:
        from reality.services.finance.credits import available_credit_items

        return available_credit_items(
            session,
            tenant_id,
            side="customer" if flow == "customer-balance" else "supplier",
            query=q,
            status=item_status,
            page=page,
            size=size,
            sort=sort,
            sort_direction=sort_direction,
            party_id=party_id or None,
        )
    if flow == "customer-credit":
        from reality.services.payment_actions import _customer_credit_items

        return _customer_credit_items(
            session,
            tenant_id,
            query=q,
            status=item_status,
            page=page,
            size=size,
            sort=sort,
            sort_direction=sort_direction,
        )
    get_tenant(session, tenant_id)
    return projection_page(
        session,
        tenant_id,
        OPEN_FINANCIAL_ITEMS,
        page=page,
        size=size,
        sort=sort,
        sort_direction=sort_direction,
        query=q,
        flow=flow,
        status=item_status,
        party_id=party_id,
        amount_fields=("gross", "settled", "open"),
        with_metadata=True,
    )


@router.get("/finance/reversal-choices")
def financial_reversal_choices(
    tenant_id: str, session: DatabaseSession, q: str = "", page: int = Query(1, ge=1)
):
    from reality.services.financial_reversal_actions import _reversal_choices

    try:
        return _reversal_choices(session, tenant_id, q, page)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/payments")
def tenant_payments(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    direction: str = "",
    sort: Literal["", "id", "date", "amount", "currency"] = "",
    sort_direction: Literal["asc", "desc"] = "asc",
):
    get_tenant(session, tenant_id)
    rows, pager = payment_page(
        session,
        tenant_id,
        page=page,
        size=size,
        sort=sort,
        sort_direction=sort_direction,
        query=q,
        direction=direction,
    )
    return {
        "items": [
            {
                "id": row["cash_entry"].id,
                "effective_at": _iso_value(row["cash_entry"].effective_at),
                "direction": row["direction"],
                "document_id": row["document"].id,
                "reference": row["document"].number,
                "document_type": row["document"].type,
                "party": row["party"],
                "currency": row["cash_entry"].currency,
                "amount": str(row["cash_entry"].amount),
                "allocated": str(row["allocated"]),
                "unallocated": str(row["unallocated"]),
                "posting_group_id": row["cash_entry"].posting_group_id,
                "reversal_role": row["reversal_role"],
            }
            for row in rows
        ],
        "totals": _projection_total_response(
            payment_totals(session, tenant_id, query=q, direction=direction),
            ("amount", "allocated", "unallocated"),
        ),
        "page": _page_response(pager),
    }


@router.get("/finance/journal")
def tenant_journal(
    tenant_id: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    account: str = "",
    date_from: str = "",
    date_to: str = "",
    sort: Literal["", "id", "date", "amount", "currency", "account", "side"] = "",
    sort_direction: Literal["asc", "desc"] = "asc",
):
    get_tenant(session, tenant_id)
    rows, pager, totals = journal_page(
        session,
        tenant_id,
        page=page,
        size=size,
        sort=sort,
        sort_direction=sort_direction,
        query=q,
        account=account,
        date_from=date_from,
        date_to=date_to,
    )
    return {
        "items": [
            {
                "id": row.id,
                "effective_at": _iso_value(row.effective_at),
                "account": row.account,
                "account_id": row.account_id,
                "account_code": row.account_record.code,
                "account_name": row.account_record.name,
                "debit_credit": row.debit_credit,
                "amount": str(row.amount),
                "currency": row.currency,
                "posting_group_id": row.posting_group_id,
                "party_id": row.party_id,
                "document_id": row.document_id,
                "source_record_id": row.source_record_id,
                "inspect_kind": "ledger_entry",
                "inspect_id": row.id,
            }
            for row in rows
        ],
        "totals": [
            {
                "currency": currency,
                "debit": str(debit),
                "credit": str(credit),
                "balance": str(Decimal(debit) - Decimal(credit)),
            }
            for currency, debit, credit in totals
        ],
        "page": _page_response(pager),
    }


@router.get("/timeline")
def tenant_timeline(
    tenant_id: str,
    session: DatabaseSession,
    q: str = "",
    area: str = "",
    event_status: str = "",
    hours: int = Query(24, ge=0, le=720),
    limit: int = Query(100, ge=1, le=250),
    before_sequence: int | None = Query(None, ge=1),
    record_type: str = "",
    after_sequence: int | None = Query(None, ge=0),
):
    """Bounded operational activity from the shared business-event projection."""
    return timeline_activity(
        session,
        tenant_id,
        query=q,
        area=area,
        status=event_status,
        hours=hours,
        limit=limit,
        before_sequence=before_sequence,
        record_type=record_type,
        after_sequence=after_sequence,
    )


@router.get("/activity-signal")
def tenant_activity_signal(
    tenant_id: str,
    session: DatabaseSession,
    after_sequence: int = Query(0, ge=0),
):
    """Lightweight cursor for visible-tab activity polling."""
    return activity_signal(session, tenant_id, after_sequence=after_sequence)


@router.get("/data-sources/{view}")
def tenant_source_metadata(
    tenant_id: str,
    view: Literal["systems", "records"],
    session: DatabaseSession,
    q: str = Query("", max_length=500),
    source_system: str = Query("", max_length=200),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    sort: Literal["", "id", "name", "reference", "date", "version", "type"] = "",
    sort_direction: Literal["asc", "desc"] = "asc",
):
    from reality.web.source_reads import source_metadata_page

    try:
        rows, pager = source_metadata_page(
            session,
            tenant_id,
            view,
            query=q,
            source_system=source_system,
            page=page,
            size=size,
            sort=sort,
            sort_direction=sort_direction,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    return {"items": rows, "page": _page_response(pager)}


@router.get("/integrations")
def tenant_integrations(tenant_id: str, session: DatabaseSession):
    """Tenant-scoped source registry for the independent frontend."""
    registry = integration_registry(session, tenant_id)
    return {
        "systems": [
            {
                "id": system.id,
                "code": system.code,
                "name": system.name,
                "description": system.description,
                "is_active": system.is_active,
                "record_count": registry["record_counts"].get(system.code, 0),
            }
            for system in registry["systems"]
        ],
        "capabilities": [
            {
                "id": row["capability"].id,
                "system_id": row["system"].id,
                "system": row["system"].name,
                "system_code": row["system"].code,
                "source_type": row["capability"].source_type,
                "target_type": row["capability"].target_type,
                "is_active": row["capability"].is_active,
                "interpreter_available": row["interpreter_available"],
            }
            for row in registry["capabilities"]
        ],
        "recent_records": [
            {
                "id": source.id,
                "received_at": _iso_value(source.received_at),
                "source_system": source.source_system,
                "source_type": source.source_type,
                "external_id": source.external_id,
                "version": source.version,
                "job_status": (
                    registry["jobs_by_source"][source.id].status
                    if source.id in registry["jobs_by_source"]
                    else None
                ),
            }
            for source in registry["recent_records"]
        ],
    }


def _financial_totals(
    rows: list[dict],
    *,
    amount_fields: tuple[str, ...],
) -> list[dict[str, str]]:
    """Keep page-level finance summaries separated by currency."""
    totals: dict[str, dict[str, Decimal]] = {}
    for row in rows:
        currency = str(row["currency"])
        bucket = totals.setdefault(
            currency,
            {field: Decimal(0) for field in amount_fields},
        )
        for field in amount_fields:
            bucket[field] += Decimal(str(row[field]))
    return [
        {"currency": currency, **{field: str(values[field]) for field in amount_fields}}
        for currency, values in sorted(totals.items())
    ]


def _projection_total_response(rows, amount_fields: tuple[str, ...]):
    return [
        {
            "currency": str(row.currency),
            **{field: str(getattr(row, field)) for field in amount_fields},
        }
        for row in rows
    ]


def _page_response(page):
    return {
        "number": page.number,
        "size": page.size,
        "total": page.total,
        "pages": page.pages,
        "has_previous": page.has_previous,
        "has_next": page.has_next,
    }


def _iso_value(value):
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _inventory_response(row):
    item = row["item"]
    return {
        "id": item.id,
        "sku": item.sku,
        "name": item.name,
        "unit": item.unit,
        "physical": str(row["physical"]),
        "reserved": str(row["reserved"]),
        "available": str(row["available"]),
        "incoming": str(row["incoming"]),
        "projected": str(row["projected"]),
    }


class Suggestion(ApiModel):
    value: str
    label: str
    description: str = ""
    status: str = "active"


class SuggestionList(ApiModel):
    items: list[Suggestion]
    allow_custom: bool = False


class PartyWrite(ApiModel):
    name: str
    type: str
    source_system: str | None = None
    external_id: str | None = None
    source_payload: dict | None = None
    roles: list[str] | None = None
    accounting_code: str = ""
    payment_term_code: str = ""
    default_currency: str = "EUR"
    credit_limit: str = "0"
    tax_identifier: str = ""


class PartyRead(PartyWrite):
    id: str
    tenant_id: str
    is_active: bool
    source_record_id: str | None


class ItemWrite(ApiModel):
    sku: str
    name: str
    unit: str = "pcs"
    source_system: str | None = None
    external_id: str | None = None
    source_payload: dict | None = None
    item_type: str = "stocked"
    tracking_type: str = "none"
    default_location_id: str | None = None
    purchase_unit: str | None = None
    conversion_factor: str = "1"
    lead_time_days: int = 0


class ItemRead(ItemWrite):
    id: str
    tenant_id: str
    is_active: bool
    source_record_id: str | None


class LocationWrite(ApiModel):
    name: str
    type: str = "warehouse"
    parent_location_id: str | None = None
    allows_stock: bool = True
    source_system: str | None = None
    external_id: str | None = None
    source_payload: dict | None = None


class LocationRead(LocationWrite):
    id: str
    tenant_id: str
    is_active: bool
    source_record_id: str | None


class HandlingUnitWrite(ApiModel):
    nve: str | None = None
    source_record_id: str | None = None


class HandlingUnitRead(HandlingUnitWrite):
    id: str
    tenant_id: str
    created_at: datetime


class LotWrite(ApiModel):
    item_id: str
    lot_number: str
    # The date somebody read off the goods, as a calendar day. Optional because
    # not everything expires, and because an item with no shelf life and a label
    # nobody read are indistinguishable here.
    expires_at: date | None = None
    source_record_id: str | None = None


class LotExpiryWrite(ApiModel):
    expires_at: date


class LotExpiryCorrectionWrite(ApiModel):
    # Absent says the lot has no best-before; absent in the expected value says
    # none is stated now. Both are meaningful, so neither can default silently.
    expires_at: date | None = None
    expected_expires_at: date | None = None
    reason: str
    actor_context: dict[str, str] | None = None


class LotRead(LotWrite):
    id: str
    tenant_id: str
    created_at: datetime


class SerialUnitWrite(ApiModel):
    item_id: str
    serial_number: str
    lot_id: str | None = None
    source_record_id: str | None = None


class SerialUnitRead(SerialUnitWrite):
    id: str
    tenant_id: str
    created_at: datetime


class MovementWrite(ApiModel):
    type: str
    item_id: str
    quantity: str
    from_location_id: str | None = None
    to_location_id: str | None = None
    commitment_id: str | None = None
    source_record_id: str | None = None
    handling_unit_id: str | None = None
    lot_id: str | None = None
    serial_unit_id: str | None = None
    occurred_at: datetime | None = None
    reason: str | None = None
    resolves_movement_id: str | None = None
    return_announcement_id: str | None = None


class MovementRead(ApiModel):
    id: str
    tenant_id: str
    type: str
    item_id: str
    quantity: str
    from_location_id: str | None
    to_location_id: str | None
    commitment_id: str | None
    source_record_id: str | None
    handling_unit_id: str | None
    lot_id: str | None
    serial_unit_id: str | None
    occurred_at: datetime
    resolves_movement_id: str | None = None
    return_announcement_id: str | None = None
    correction_role: str = "normal"
    correction_status: str = "recorded"


class MovementCorrectionWrite(ApiModel):
    expected_revision: str | None = None
    preview_fingerprint: str | None = None
    reason: str
    replacement: MovementWrite | None = None
    actor_context: dict[str, object] | None = None


class LedgerReversalWrite(ApiModel):
    expected_revision: str | None = None
    preview_fingerprint: str | None = None
    reason: str
    actor_context: dict[str, object] | None = None


class ReservationWrite(ApiModel):
    commitment_id: str
    quantity: str | None = None
    handling_unit_id: str | None = None
    lot_id: str | None = None
    serial_unit_id: str | None = None


class ReservationRead(ApiModel):
    id: str | None
    requested: str
    reserved: str
    shortage: str
    handling_unit_id: str | None = None
    lot_id: str | None = None
    serial_unit_id: str | None = None


class ActiveWrite(ApiModel):
    is_active: bool


class PaymentTermWrite(ApiModel):
    code: str
    name: str
    due_days: int
    # Both or neither: half a discount condition is refused by the service.
    discount_percent: Decimal | None = None
    discount_days: int | None = None
    source_system: str | None = None
    external_id: str | None = None
    source_payload: dict | None = None


class PaymentTermRead(PaymentTermWrite):
    id: str
    tenant_id: str
    is_active: bool
    source_record_id: str | None


class PriceListWrite(ApiModel):
    code: str
    name: str
    direction: str
    currency: str
    is_default: bool = False


class PriceListRead(PriceListWrite):
    id: str
    tenant_id: str
    is_active: bool
    source_record_id: str | None
    valid_from: datetime | None
    valid_until: datetime | None


class PriceTierWrite(ApiModel):
    price_list_id: str
    item_id: str
    min_quantity: str
    unit_price: str
    unit: str


class PricingAssignmentWrite(ApiModel):
    price_list_id: str
    priority: int = 100


class PricingGroupWrite(ApiModel):
    code: str
    name: str


class GroupMemberWrite(ApiModel):
    party_id: str


class SourceWrite(ApiModel):
    source_system: str
    source_type: str
    external_id: str
    payload: dict
    source_version_at: datetime | None = None
    context: dict = Field(default_factory=dict)


class DocumentCorrectionWrite(ApiModel):
    type: str
    number: str
    party_id: str
    amount: str
    currency: str = "EUR"
    document_date: str = ""
    ordered_at: datetime | None = None
    requested_delivery_at: datetime | None = None
    customer_reference: str = ""
    sales_channel: str = ""
    payment_term_code: str = ""
    ship_to_party_id: str | None = None


class ManualDocumentLineWrite(ApiModel):
    id: str | None = None
    item_id: str | None = None
    source_line_id: str | None = None
    sku: str = ""
    description: str = ""
    quantity: str
    unit: str = "pcs"
    unit_price: str = "0"
    gross_amount: str
    promised_at: str = ""
    line_type: str = "item"
    price_list_entry_id: str | None = None
    billed_document_line_id: str | None = None


class ManualDocumentWrite(ApiModel):
    type: str
    number: str
    party_id: str
    currency: str = "EUR"
    gross_amount: str
    document_date: str = ""
    ordered_at: datetime | None = None
    requested_delivery_at: datetime | None = None
    customer_reference: str = ""
    sales_channel: str = ""
    payment_term_code: str = ""
    ship_to_party_id: str | None = None
    lines: list[ManualDocumentLineWrite]


class ManualOrderWrite(ApiModel):
    direction: Literal["sales", "purchase"]
    number: str
    company_party_id: str
    counterparty_id: str
    location_id: str
    lines: list[ManualDocumentLineWrite]
    gross_amount: str
    currency: str = "EUR"
    document_date: str = ""
    ordered_at: datetime | None = None
    requested_delivery_at: datetime | None = None
    customer_reference: str = ""
    sales_channel: str = ""
    payment_term_code: str = ""
    ship_to_party_id: str | None = None


class FactObservationWrite(ApiModel):
    source_record_id: str
    subject_type: str
    subject_id: str
    predicate: str
    value: Any
    observed_at: datetime
    idempotency_key: str


class RealityGapWrite(ApiModel):
    question: str
    intended_use: str
    origin: Literal["chat", "mcp", "web"] = "web"
    idempotency_key: str
    origin_reference: str | None = None


class RealityGapEntryWrite(ApiModel):
    entry_type: Literal["answer", "context", "evidence", "note"]
    payload: dict[str, Any]
    expected_revision: int


class RealityGapDecisionWrite(ApiModel):
    destination: Literal[
        "source_only",
        "fact",
        "typed_evidence",
        "typed_reality",
        "derived_view",
        "rejected",
    ]
    rationale: str
    expected_revision: int


class RealityGapImplementationWrite(ApiModel):
    expected_revision: int
    draft: dict[str, Any] | None = None


class RealityGapRevisionWrite(ApiModel):
    expected_revision: int


class RealityGapReplayWrite(ApiModel):
    source_ids: list[str] | None = None
    limit: int = Field(default=500, ge=1, le=500)
    cursor: str | None = None


class PaymentPostingWrite(ApiModel):
    invoice_id: str
    amount: str
    payment_number: str | None = None
    source_record_id: str | None = None
    effective_at: datetime | None = None


class ReturnAnnouncementWrite(ApiModel):
    commitment_id: str
    quantity: str
    # Stated, never generated: a number this product invented would be a number
    # somebody has to tell the customer.
    reference: str = ""
    reason: str = ""
    expected_by: datetime | None = None
    note: str = ""


class ReturnAnnouncementWithdrawalWrite(ApiModel):
    note: str = ""


class PaymentRunPreviewWrite(ApiModel):
    pay_by: datetime


class PaymentRunLineWrite(ApiModel):
    invoice_id: str
    amount: str
    payment_number: str | None = None


class PaymentRunWrite(ApiModel):
    # The total is the confirmation figure rather than a count: a person approves
    # an amount of money, and a list assembled from a preview can be right in
    # every line and wrong in sum.
    payments: list[PaymentRunLineWrite]
    currency: str
    expected_total: str
    reason: str
    effective_at: datetime | None = None


class StaleClosurePreviewWrite(ApiModel):
    direction: str
    due_before: datetime


class StaleClosureWrite(ApiModel):
    direction: str
    due_before: datetime
    expected_count: int
    reason: str


class CommitmentRevisionWrite(ApiModel):
    # Both optional and at least one required; the service refuses a statement
    # that restates nothing.
    due_at: datetime | None = None
    quantity: Decimal | None = None
    note: str = ""
    stated_at: datetime | None = None
    source_record_id: str | None = None


class InvoicePostingWrite(ApiModel):
    document_id: str
    effective_at: datetime | None = None


class CreditNotePostingWrite(ApiModel):
    credit_note_id: str
    effective_at: datetime | None = None


class CreditNoteNettingWrite(ApiModel):
    credit_note_id: str
    invoice_id: str
    amount: str


class CustomerRefundWrite(ApiModel):
    credit_note_id: str
    amount: str
    refund_number: str | None = None
    source_record_id: str | None = None
    effective_at: datetime | None = None


class ManualDocumentLineCorrectionWrite(ApiModel):
    expected_revision: str
    lines: list[ManualDocumentLineWrite]


class DocumentSourceVersionWrite(ApiModel):
    payload: dict
    source_version_at: datetime | None = None


class SourceSystemWrite(ApiModel):
    code: str
    name: str
    description: str = ""


class SourceSystemRead(SourceSystemWrite):
    id: str
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SourceCapabilityWrite(ApiModel):
    source_system_id: str
    source_type: str
    target_type: str


class SourceCapabilityRead(SourceCapabilityWrite):
    id: str
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ConnectorShellInstall(ApiModel):
    source_types: list[str]
    system_code: str
    system_name: str


class SourceRead(ApiModel):
    id: str
    tenant_id: str
    source_system: str
    source_type: str
    external_id: str
    payload: str
    payload_hash: str
    version: int
    supersedes_source_record_id: str | None
    source_version_at: datetime | None
    received_at: datetime


class ImportJobRead(ApiModel):
    id: str
    tenant_id: str
    source_record_id: str
    status: str
    attempts: int
    error: str


class HoldWrite(ApiModel):
    reason_code: str
    note: str = ""


class HoldRead(ApiModel):
    id: str
    tenant_id: str
    commitment_id: str
    reason_code: str
    note: str
    created_by: str
    created_at: datetime
    released_at: datetime | None


class DeliveryHoldRead(ApiModel):
    id: str
    tenant_id: str
    party_id: str
    hold_type: str
    reason_code: str
    note: str
    created_by: str
    created_at: datetime
    released_at: datetime | None


def api_error(error: NotFound | InvalidOperation) -> HTTPException:
    code = (
        status.HTTP_404_NOT_FOUND
        if isinstance(error, NotFound)
        else status.HTTP_409_CONFLICT
        if isinstance(error, Conflict)
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(status_code=code, detail=str(error))


def master_source(
    session: OrmSession, record: Party | Item | Location
) -> SourceRecord | None:
    if not record.source_record_id:
        return None
    return session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == record.tenant_id,
            SourceRecord.id == record.source_record_id,
        )
    )


def location_response(session: OrmSession, location: Location) -> dict:
    source = master_source(session, location)
    return {
        "id": location.id,
        "tenant_id": location.tenant_id,
        "name": location.name,
        "type": location.type,
        "parent_location_id": location.parent_location_id,
        "allows_stock": location.allows_stock,
        "is_active": location.is_active,
        "source_record_id": location.source_record_id,
        "source_system": source.source_system if source else None,
        "external_id": source.external_id if source else None,
        "source_payload": json.loads(source.payload) if source else None,
    }


def party_response(session: OrmSession, party: Party) -> dict:
    source = master_source(session, party)
    payment_term = (
        session.scalar(
            select(PaymentTerm).where(
                PaymentTerm.tenant_id == party.tenant_id,
                PaymentTerm.id == party.payment_term_id,
            )
        )
        if party.payment_term_id
        else None
    )
    return {
        "id": party.id,
        "tenant_id": party.tenant_id,
        "name": party.name,
        "type": party.type,
        "is_active": party.is_active,
        "source_record_id": party.source_record_id,
        "source_system": source.source_system if source else None,
        "external_id": source.external_id if source else None,
        "source_payload": None,
        "roles": [
            role.role
            for role in party_detail(session, party.tenant_id, party.id)["roles"]
        ],
        "accounting_code": party.accounting_code,
        "payment_term_code": payment_term.code if payment_term else "",
        "default_currency": party.default_currency,
        "credit_limit": str(party.credit_limit),
        "tax_identifier": party.tax_identifier,
    }


@router.get("/suggestions/{kind}", response_model=SuggestionList)
def suggestion_list(
    tenant_id: str,
    kind: str,
    session: DatabaseSession,
    q: str = "",
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    source_system_id: str | None = None,
    source_system: str | None = None,
):
    """Tenant-scoped choices for shared web comboboxes."""
    try:
        get_tenant(session, tenant_id)
    except NotFound as error:
        raise api_error(error) from error
    allow_custom = kind in {
        "source-system-codes",
        "source-types",
        "target-types",
        "units",
        "currencies",
    }
    if kind == "parties":
        choices = [
            Suggestion(
                value=x.id,
                label=x.name,
                description=x.type,
                status="active" if x.is_active else "inactive",
            )
            for x in parties(session, tenant_id)
        ]
    elif kind == "items":
        choices = [
            Suggestion(
                value=x.id,
                label=f"{x.sku} · {x.name}",
                description=x.unit,
                status="active" if x.is_active else "inactive",
            )
            for x in items(session, tenant_id)
        ]
    elif kind == "locations":
        choices = [
            Suggestion(
                value=x.id,
                label=x.name,
                description=x.type,
                status="active" if x.is_active else "inactive",
            )
            for x in locations(session, tenant_id)
        ]
    elif kind == "commitments":
        records = session.scalars(
            select(Commitment)
            .where(Commitment.tenant_id == tenant_id)
            .order_by(Commitment.created_at.desc())
            .limit(100)
        )
        choices = [
            Suggestion(
                value=x.id,
                label=f"{x.type.replace('_', ' ').title()} · {x.quantity}",
                description=x.status,
                status="active" if x.status == "open" else "inactive",
            )
            for x in records
        ]
    elif kind == "documents":
        records = session.scalars(
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .order_by(Document.id.desc())
            .limit(100)
        )
        choices = [
            Suggestion(
                value=x.id,
                label=f"{x.number} · {x.type.replace('_', ' ').title()}",
                description=x.document_date,
                status="active",
            )
            for x in records
        ]
    elif kind == "payment-terms":
        choices = [
            Suggestion(
                value=x.code,
                label=f"{x.code} · {x.name}",
                description=(
                    f"{x.due_days} days"
                    + (
                        f", {x.discount_percent.normalize():g}% within {x.discount_days}"
                        if x.discount_percent is not None
                        else ""
                    )
                ),
                status="active" if x.is_active else "inactive",
            )
            for x in payment_terms(session, tenant_id)
        ]
    elif kind in {"source-systems", "source-system-codes"}:
        choices = [
            Suggestion(
                value=x.id if kind == "source-systems" else x.code,
                label=x.name,
                description=x.code,
                status="active" if x.is_active else "inactive",
            )
            for x in source_systems(session, tenant_id)
        ]
    elif kind in {"source-types", "target-types"}:
        capabilities = source_capabilities(session, tenant_id)
        systems = source_systems(session, tenant_id)
        if source_system_id:
            capabilities = [
                x for x in capabilities if x.source_system_id == source_system_id
            ]
        elif source_system:
            ids = {x.id for x in systems if x.code == source_system}
            capabilities = [x for x in capabilities if x.source_system_id in ids]
        attribute = "source_type" if kind == "source-types" else "target_type"
        values = {getattr(x, attribute) for x in capabilities}
        if kind == "target-types":
            values.update(
                {
                    "party",
                    "item",
                    "sales_order",
                    "purchase_order",
                    "payment",
                    "fulfillment",
                    "sales_invoice",
                    "purchase_invoice",
                }
            )
        choices = [
            Suggestion(value=x, label=x, description="Known operational vocabulary")
            for x in sorted(values)
        ]
    elif kind == "price-lists":
        choices = [
            Suggestion(
                value=x.id,
                label=f"{x.code} · {x.name}",
                description=f"{x.direction} · {x.currency}",
                status="active" if x.is_active else "inactive",
            )
            for x in price_lists(session, tenant_id)
        ]
    elif kind == "price-groups":
        choices = [
            Suggestion(
                value=x.id,
                label=f"{x.code} · {x.name}",
                description="Party price group",
            )
            for x in party_groups(session, tenant_id)
        ]
    elif kind == "units":
        values = {"pcs", "kg", "g", "l", "m", "h"}
        values.update(x.unit for x in items(session, tenant_id) if x.unit)
        choices = [
            Suggestion(value=x, label=x, description="Unit of measure")
            for x in sorted(values)
        ]
    elif kind == "currencies":
        values = {"EUR", "USD", "GBP", "CHF"}
        values.update(x.currency for x in price_lists(session, tenant_id) if x.currency)
        choices = [
            Suggestion(value=x, label=x, description="Currency") for x in sorted(values)
        ]
    else:
        raise HTTPException(status_code=404, detail="Suggestion type not found.")
    needle = q.strip().casefold()
    if needle:
        choices = [
            x
            for x in choices
            if needle in f"{x.value} {x.label} {x.description}".casefold()
        ]
    return SuggestionList(items=choices[:limit], allow_custom=allow_custom)


def item_response(session: OrmSession, item: Item) -> dict:
    source = master_source(session, item)
    return {
        "id": item.id,
        "tenant_id": item.tenant_id,
        "sku": item.sku,
        "name": item.name,
        "unit": item.unit,
        "is_active": item.is_active,
        "source_record_id": item.source_record_id,
        "source_system": source.source_system if source else None,
        "external_id": source.external_id if source else None,
        "source_payload": None,
        "item_type": item.item_type,
        "tracking_type": item.tracking_type,
        "default_location_id": item.default_location_id,
        "purchase_unit": item.purchase_unit,
        "conversion_factor": str(item.conversion_factor),
        "lead_time_days": item.lead_time_days,
    }


@router.post("/sources", status_code=201)
def post_source(tenant_id: str, body: SourceWrite, session: DatabaseSession):
    try:
        source, job = enqueue_source(
            session,
            tenant_id,
            body.source_system,
            body.source_type,
            body.external_id,
            body.payload,
            source_version_at=body.source_version_at,
            context=body.context,
        )
        return {
            "source": SourceRead.model_validate(source),
            "import_job": ImportJobRead.model_validate(job),
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/source-systems", response_model=list[SourceSystemRead])
def list_source_systems(tenant_id: str, session: DatabaseSession):
    return source_systems(session, tenant_id)


@router.get("/connector-shells")
def list_connector_shells(tenant_id: str, session: DatabaseSession):
    return connector_shells(session, tenant_id)


@router.post(
    "/connector-shells/{connector_code}/install",
    response_model=SourceSystemRead,
    status_code=201,
)
def post_connector_shell(
    tenant_id: str,
    connector_code: str,
    body: ConnectorShellInstall,
    session: DatabaseSession,
):
    try:
        return install_connector_shell(
            session,
            tenant_id,
            connector_code,
            body.source_types,
            body.system_code,
            body.system_name,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/source-systems", response_model=SourceSystemRead, status_code=201)
def post_source_system(
    tenant_id: str, body: SourceSystemWrite, session: DatabaseSession
):
    try:
        return create_source_system(
            session, tenant_id, body.code, body.name, body.description
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.patch("/source-systems/{record_id}/active", response_model=SourceSystemRead)
def patch_source_system_active(
    tenant_id: str, record_id: str, body: ActiveWrite, session: DatabaseSession
):
    try:
        return set_source_system_active(session, tenant_id, record_id, body.is_active)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/source-capabilities", response_model=SourceCapabilityRead, status_code=201
)
def post_source_capability(
    tenant_id: str, body: SourceCapabilityWrite, session: DatabaseSession
):
    try:
        return create_source_capability(
            session,
            tenant_id,
            body.source_system_id,
            body.source_type,
            body.target_type,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/source-capabilities", response_model=list[SourceCapabilityRead])
def list_source_capabilities(tenant_id: str, session: DatabaseSession):
    return source_capabilities(session, tenant_id)


@router.patch(
    "/source-capabilities/{record_id}/active",
    response_model=SourceCapabilityRead,
)
def patch_source_capability_active(
    tenant_id: str, record_id: str, body: ActiveWrite, session: DatabaseSession
):
    try:
        return set_source_capability_active(
            session, tenant_id, record_id, body.is_active
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/sources", response_model=list[SourceRead])
def list_sources(tenant_id: str, session: DatabaseSession):
    return source_records(session, tenant_id)


@router.get("/import-jobs", response_model=list[ImportJobRead])
def list_import_jobs(tenant_id: str, session: DatabaseSession):
    return import_jobs(session, tenant_id)


@router.post("/import-jobs/{job_id}/retry", response_model=ImportJobRead)
def post_import_retry(tenant_id: str, job_id: str, session: DatabaseSession):
    try:
        return retry_import_job(session, tenant_id, job_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/import-jobs/work")
def post_import_work(tenant_id: str, session: DatabaseSession, limit: int = 100):
    completed, failed = process_pending_import_jobs(session, tenant_id, limit=limit)
    return {"completed": completed, "failed": failed}


@router.get("/payment-terms", response_model=list[PaymentTermRead])
def list_payment_terms(tenant_id: str, session: DatabaseSession):
    try:
        return payment_terms(session, tenant_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/payment-terms",
    response_model=PaymentTermRead,
    status_code=status.HTTP_201_CREATED,
)
def post_payment_term(tenant_id: str, body: PaymentTermWrite, session: DatabaseSession):
    try:
        return create_payment_term(
            session,
            tenant_id,
            body.code,
            body.name,
            body.due_days,
            source_system=body.source_system or "",
            external_id=body.external_id or "",
            source_payload=body.source_payload,
            discount_percent=body.discount_percent,
            discount_days=body.discount_days,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.put("/payment-terms/{record_id}", response_model=PaymentTermRead)
def put_payment_term(
    tenant_id: str, record_id: str, body: PaymentTermWrite, session: DatabaseSession
):
    try:
        return update_payment_term(
            session,
            tenant_id,
            record_id,
            body.code,
            body.name,
            body.due_days,
            discount_percent=body.discount_percent,
            discount_days=body.discount_days,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.patch("/payment-terms/{record_id}/active", response_model=PaymentTermRead)
def patch_payment_term_active(
    tenant_id: str, record_id: str, body: ActiveWrite, session: DatabaseSession
):
    try:
        return set_master_data_active(
            session, tenant_id, PaymentTerm, record_id, body.is_active
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/price-lists", response_model=list[PriceListRead])
def list_price_lists(tenant_id: str, session: DatabaseSession):
    return price_lists(session, tenant_id)


@router.post("/price-lists", response_model=PriceListRead, status_code=201)
def post_price_list(tenant_id: str, body: PriceListWrite, session: DatabaseSession):
    try:
        return create_price_list(
            session,
            tenant_id,
            body.code,
            body.name,
            body.direction,
            body.currency,
            is_default=body.is_default,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.put("/price-lists/{record_id}", response_model=PriceListRead)
def put_price_list(
    tenant_id: str, record_id: str, body: PriceListWrite, session: DatabaseSession
):
    try:
        return update_price_list(
            session,
            tenant_id,
            record_id,
            body.code,
            body.name,
            body.direction,
            body.currency,
            is_default=body.is_default,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/price-tiers")
def list_price_tiers(tenant_id: str, session: DatabaseSession):
    return price_list_entries(session, tenant_id)


@router.post("/price-tiers", status_code=201)
def post_price_tier(tenant_id: str, body: PriceTierWrite, session: DatabaseSession):
    try:
        return create_price_list_entry(
            session,
            tenant_id,
            body.price_list_id,
            body.item_id,
            body.min_quantity,
            body.unit_price,
            body.unit,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/parties/{party_id}/price-lists", status_code=201)
def post_party_price_list(
    tenant_id: str,
    party_id: str,
    body: PricingAssignmentWrite,
    session: DatabaseSession,
):
    try:
        return assign_party_price_list(
            session, tenant_id, party_id, body.price_list_id, body.priority
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/pricing-groups", status_code=201)
def post_pricing_group(
    tenant_id: str, body: PricingGroupWrite, session: DatabaseSession
):
    try:
        return create_party_group(session, tenant_id, body.code, body.name)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.put("/pricing-groups/{group_id}")
def put_pricing_group(
    tenant_id: str, group_id: str, body: PricingGroupWrite, session: DatabaseSession
):
    try:
        return update_party_group(session, tenant_id, group_id, body.code, body.name)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/pricing-groups")
def list_pricing_groups(tenant_id: str, session: DatabaseSession):
    return party_groups(session, tenant_id)


@router.post("/pricing-groups/{group_id}/members", status_code=201)
def post_pricing_group_member(
    tenant_id: str, group_id: str, body: GroupMemberWrite, session: DatabaseSession
):
    try:
        return add_party_group_member(session, tenant_id, group_id, body.party_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/pricing-groups/{group_id}/price-lists", status_code=201)
def post_group_price_list(
    tenant_id: str,
    group_id: str,
    body: PricingAssignmentWrite,
    session: DatabaseSession,
):
    try:
        return assign_group_price_list(
            session, tenant_id, group_id, body.price_list_id, body.priority
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/prices/resolve")
def get_resolved_price(
    tenant_id: str,
    party_id: str,
    item_id: str,
    quantity: str,
    direction: str,
    currency: str,
    unit: str,
    session: DatabaseSession,
):
    try:
        result = materialized_resolve_price(
            session, tenant_id, party_id, item_id, quantity, direction, currency, unit
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
    if result is None:
        raise HTTPException(status_code=404, detail="No applicable price found.")
    return result


@router.get("/projections/{projection_name}")
def get_materialized_projection(
    tenant_id: str, projection_name: str, session: DatabaseSession
):
    try:
        return projection_rows(session, tenant_id, projection_name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/projection-snapshots/{projection_name}")
def get_projection_snapshot(
    tenant_id: str, projection_name: str, session: DatabaseSession
):
    try:
        return projection_snapshot(session, tenant_id, projection_name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NotFound as error:
        raise api_error(error) from error


SPECIALIZED_WORKSPACE_PROJECTIONS = {
    FULFILLMENT_QUEUE,
    FULFILLMENT_BLOCKERS,
    ITEM_SUPPLY_DEMAND,
}


@router.get("/projection-views/{projection_name}")
def specialized_projection_view(
    tenant_id: str,
    projection_name: str,
    session: DatabaseSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
):
    """Return one bounded page for an explicitly classified workspace projection."""
    get_tenant(session, tenant_id)
    if projection_name not in SPECIALIZED_WORKSPACE_PROJECTIONS:
        raise HTTPException(
            status_code=404, detail="Unknown specialized projection view."
        )
    return projection_page(
        session,
        tenant_id,
        projection_name,
        page=page,
        size=size,
        query=q,
        with_metadata=True,
    )


@router.get("/catalog-code")
def get_catalog_code(tenant_id: str, kind: str, key: str):
    from reality.catalogs import catalog_code

    readers = {
        "commitments": (tenant_commitment_control,),
        "documents": (tenant_evidence_documents,),
        "items": (list_items,),
        "parties": (list_parties,),
        "locations": (list_locations,),
        "reservations": (list_reservations,),
        "movements": (list_movements,),
        "payments": (tenant_payments,),
        "journal": (tenant_journal,),
        "activity": (tenant_timeline,),
        "sources_imports": (tenant_integrations,),
        "commercial_terms": (list_payment_terms, list_price_lists, list_pricing_groups),
    }
    try:
        return catalog_code(kind, key, readers)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (OSError, TypeError):
        raise HTTPException(
            status_code=503, detail="Catalog source is unavailable."
        ) from None


@router.get("/application-reference")
def application_reference(tenant_id: str):
    """Return validated global application metadata inside the tenant auth boundary."""
    return runtime_application_catalog()


@router.get("/parties", response_model=list[PartyRead])
def list_parties(tenant_id: str, session: DatabaseSession):
    try:
        return [party_response(session, party) for party in parties(session, tenant_id)]
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/parties", response_model=PartyRead, status_code=status.HTTP_201_CREATED)
def post_party(tenant_id: str, body: PartyWrite, session: DatabaseSession):
    try:
        party = create_party(
            session,
            tenant_id,
            body.name,
            body.type,
            source_system=body.source_system or "",
            external_id=body.external_id or "",
            source_payload=body.source_payload,
            roles=body.roles,
            accounting_code=body.accounting_code,
            payment_term_code=body.payment_term_code,
            default_currency=body.default_currency,
            credit_limit=body.credit_limit,
            tax_identifier=body.tax_identifier,
        )
        return party_response(session, party)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/parties/{record_id}", response_model=PartyRead)
def get_party(tenant_id: str, record_id: str, session: DatabaseSession):
    try:
        return party_response(
            session, party_detail(session, tenant_id, record_id)["party"]
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.put("/parties/{record_id}", response_model=PartyRead)
def put_party(
    tenant_id: str, record_id: str, body: PartyWrite, session: DatabaseSession
):
    try:
        party = update_party(
            session,
            tenant_id,
            record_id,
            body.name,
            body.type,
            source_system=body.source_system,
            external_id=body.external_id,
            source_payload=body.source_payload,
            roles=body.roles,
            accounting_code=body.accounting_code,
            payment_term_code=body.payment_term_code,
            default_currency=body.default_currency,
            credit_limit=body.credit_limit,
            tax_identifier=body.tax_identifier,
        )
        return party_response(session, party)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.patch("/parties/{record_id}/active", response_model=PartyRead)
def patch_party_active(
    tenant_id: str, record_id: str, body: ActiveWrite, session: DatabaseSession
):
    try:
        party = set_master_data_active(
            session, tenant_id, Party, record_id, body.is_active
        )
        return party_response(session, party)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/items", response_model=list[ItemRead])
def list_items(tenant_id: str, session: DatabaseSession):
    try:
        return [item_response(session, item) for item in items(session, tenant_id)]
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def post_item(tenant_id: str, body: ItemWrite, session: DatabaseSession):
    try:
        item = create_item(
            session,
            tenant_id,
            body.sku,
            body.name,
            body.unit,
            source_system=body.source_system or "",
            external_id=body.external_id or "",
            source_payload=body.source_payload,
            item_type=body.item_type,
            tracking_type=body.tracking_type,
            default_location_id=body.default_location_id,
            purchase_unit=body.purchase_unit,
            conversion_factor=body.conversion_factor,
            lead_time_days=body.lead_time_days,
        )
        return item_response(session, item)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/items/{record_id}", response_model=ItemRead)
def get_item(tenant_id: str, record_id: str, session: DatabaseSession):
    try:
        return item_response(
            session, item_detail(session, tenant_id, record_id)["item"]
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.put("/items/{record_id}", response_model=ItemRead)
def put_item(tenant_id: str, record_id: str, body: ItemWrite, session: DatabaseSession):
    try:
        item = update_item(
            session,
            tenant_id,
            record_id,
            body.sku,
            body.name,
            body.unit,
            source_system=body.source_system,
            external_id=body.external_id,
            source_payload=body.source_payload,
            item_type=body.item_type,
            tracking_type=body.tracking_type,
            default_location_id=body.default_location_id,
            purchase_unit=body.purchase_unit,
            conversion_factor=body.conversion_factor,
            lead_time_days=body.lead_time_days,
        )
        return item_response(session, item)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.patch("/items/{record_id}/active", response_model=ItemRead)
def patch_item_active(
    tenant_id: str, record_id: str, body: ActiveWrite, session: DatabaseSession
):
    try:
        item = set_master_data_active(
            session, tenant_id, Item, record_id, body.is_active
        )
        return item_response(session, item)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/locations", response_model=list[LocationRead])
def list_locations(tenant_id: str, session: DatabaseSession):
    try:
        return [
            location_response(session, row) for row in locations(session, tenant_id)
        ]
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/locations", response_model=LocationRead, status_code=status.HTTP_201_CREATED
)
def post_location(tenant_id: str, body: LocationWrite, session: DatabaseSession):
    try:
        location = create_location(
            session,
            tenant_id,
            body.name,
            body.type,
            parent_location_id=body.parent_location_id,
            allows_stock=body.allows_stock,
            source_system=body.source_system or "",
            external_id=body.external_id or "",
            source_payload=body.source_payload,
        )
        return location_response(session, location)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/locations/{record_id}", response_model=LocationRead)
def get_location(tenant_id: str, record_id: str, session: DatabaseSession):
    try:
        return location_response(
            session, location_detail(session, tenant_id, record_id)["location"]
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.put("/locations/{record_id}", response_model=LocationRead)
def put_location(
    tenant_id: str, record_id: str, body: LocationWrite, session: DatabaseSession
):
    try:
        location = update_location(
            session,
            tenant_id,
            record_id,
            body.name,
            body.type,
            parent_location_id=body.parent_location_id,
            allows_stock=body.allows_stock,
            source_system=body.source_system,
            external_id=body.external_id,
            source_payload=body.source_payload,
        )
        return location_response(session, location)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.patch("/locations/{record_id}/active", response_model=LocationRead)
def patch_location_active(
    tenant_id: str, record_id: str, body: ActiveWrite, session: DatabaseSession
):
    try:
        location = set_master_data_active(
            session, tenant_id, Location, record_id, body.is_active
        )
        return location_response(session, location)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/handling-units", response_model=list[HandlingUnitRead])
def list_handling_units(tenant_id: str, session: DatabaseSession):
    try:
        return handling_units(session, tenant_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/handling-units",
    response_model=HandlingUnitRead,
    status_code=status.HTTP_201_CREATED,
)
def post_handling_unit(
    tenant_id: str, body: HandlingUnitWrite, session: DatabaseSession
):
    try:
        return create_handling_unit(
            session,
            tenant_id,
            body.nve,
            source_record_id=body.source_record_id,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/lots", response_model=list[LotRead])
def list_lots(tenant_id: str, session: DatabaseSession, item_id: str | None = None):
    try:
        return lots(session, tenant_id, item_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/lots", response_model=LotRead, status_code=status.HTTP_201_CREATED)
def post_lot(tenant_id: str, body: LotWrite, session: DatabaseSession):
    try:
        return create_lot(
            session,
            tenant_id,
            body.item_id,
            body.lot_number,
            expires_at=body.expires_at,
            source_record_id=body.source_record_id,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/lots/{lot_id}/expiry/correction", response_model=LotRead)
def correct_lot_expiry_web(
    tenant_id: str,
    lot_id: str,
    body: LotExpiryCorrectionWrite,
    session: DatabaseSession,
):
    payload = body.model_dump()
    try:
        return correct_lot_expiry(
            session, tenant_id, lot_id, payload.pop("expires_at"), **payload
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/lots/expired", response_model=list[LotRead])
def list_expired_lots(tenant_id: str, session: DatabaseSession):
    try:
        return expired_lots(session, tenant_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/lots/{lot_id}/expiry", response_model=LotRead)
def state_lot_expiry_web(
    tenant_id: str, lot_id: str, body: LotExpiryWrite, session: DatabaseSession
):
    try:
        return state_lot_expiry(session, tenant_id, lot_id, body.expires_at)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/serial-units", response_model=list[SerialUnitRead])
def list_serial_units(
    tenant_id: str, session: DatabaseSession, item_id: str | None = None
):
    try:
        return serial_units(session, tenant_id, item_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/serial-units",
    response_model=SerialUnitRead,
    status_code=status.HTTP_201_CREATED,
)
def post_serial_unit(tenant_id: str, body: SerialUnitWrite, session: DatabaseSession):
    try:
        return create_serial_unit(
            session,
            tenant_id,
            body.item_id,
            body.serial_number,
            lot_id=body.lot_id,
            source_record_id=body.source_record_id,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/movements", response_model=MovementRead, status_code=status.HTTP_201_CREATED
)
def post_movement(tenant_id: str, body: MovementWrite, session: DatabaseSession):
    try:
        movement = record_movement(
            session,
            tenant_id,
            body.type,
            body.item_id,
            body.quantity,
            from_location_id=body.from_location_id,
            to_location_id=body.to_location_id,
            commitment_id=body.commitment_id,
            source_record_id=body.source_record_id,
            handling_unit_id=body.handling_unit_id,
            lot_id=body.lot_id,
            serial_unit_id=body.serial_unit_id,
            occurred_at=body.occurred_at,
            reason=body.reason,
            resolves_movement_id=body.resolves_movement_id,
            return_announcement_id=body.return_announcement_id,
        )
        return {
            "id": movement.id,
            "tenant_id": movement.tenant_id,
            "type": movement.type,
            "item_id": movement.item_id,
            "quantity": str(movement.quantity),
            "from_location_id": movement.from_location_id,
            "to_location_id": movement.to_location_id,
            "commitment_id": movement.commitment_id,
            "source_record_id": movement.source_record_id,
            "handling_unit_id": movement.handling_unit_id,
            "lot_id": movement.lot_id,
            "serial_unit_id": movement.serial_unit_id,
            "occurred_at": movement.occurred_at,
            "resolves_movement_id": movement.resolves_movement_id,
            "return_announcement_id": movement.return_announcement_id,
            "correction_role": "normal",
            "correction_status": "recorded",
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/movements", response_model=list[MovementRead])
def list_movements(
    tenant_id: str, session: DatabaseSession, limit: int = Query(100, ge=1, le=500)
):
    get_tenant(session, tenant_id)
    rows = session.scalars(
        select(Movement)
        .where(Movement.tenant_id == tenant_id)
        .order_by(Movement.occurred_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "type": row.type,
            "item_id": row.item_id,
            "quantity": str(row.quantity),
            "from_location_id": row.from_location_id,
            "to_location_id": row.to_location_id,
            "commitment_id": row.commitment_id,
            "source_record_id": row.source_record_id,
            "handling_unit_id": row.handling_unit_id,
            "lot_id": row.lot_id,
            "serial_unit_id": row.serial_unit_id,
            "occurred_at": row.occurred_at,
            "resolves_movement_id": row.resolves_movement_id,
            "return_announcement_id": row.return_announcement_id,
            "correction_role": movement_correction_snapshot(session, tenant_id, row.id)[
                "role"
            ],
            "correction_status": movement_correction_snapshot(
                session, tenant_id, row.id
            )["status"],
        }
        for row in rows
    ]


@router.get("/movements/{movement_id}/correction")
def get_movement_correction(tenant_id: str, movement_id: str, session: DatabaseSession):
    try:
        return movement_correction_snapshot(session, tenant_id, movement_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/movements/{movement_id}/correction/preview")
def post_movement_correction_preview(
    tenant_id: str,
    movement_id: str,
    body: MovementCorrectionWrite,
    session: DatabaseSession,
):
    try:
        return preview_movement_correction(
            session,
            tenant_id,
            movement_id,
            reason=body.reason,
            replacement=(
                body.replacement.model_dump(exclude_none=True)
                if body.replacement
                else None
            ),
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/movements/{movement_id}/correction")
def post_movement_correction(
    tenant_id: str,
    movement_id: str,
    body: MovementCorrectionWrite,
    session: DatabaseSession,
):
    try:
        result = correct_movement(
            session,
            tenant_id,
            movement_id,
            reason=body.reason,
            replacement=(
                body.replacement.model_dump(exclude_none=True)
                if body.replacement
                else None
            ),
            actor_context=body.actor_context,
            expected_revision=body.expected_revision,
            preview_fingerprint=body.preview_fingerprint,
        )
        return {
            "correction_id": result.correction_id,
            "original_movement_id": result.original_movement_id,
            "compensating_movement_id": result.compensating_movement_id,
            "replacement_movement_id": result.replacement_movement_id,
            "request_fingerprint": result.request_fingerprint,
            "replayed": result.replayed,
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/ledger/posting-groups/{posting_group_id}/reversal")
def get_ledger_reversal(
    tenant_id: str, posting_group_id: str, session: DatabaseSession
):
    try:
        return ledger_reversal_snapshot(session, tenant_id, posting_group_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/ledger/posting-groups/{posting_group_id}/reversal/preview")
def post_ledger_reversal_preview(
    tenant_id: str,
    posting_group_id: str,
    body: LedgerReversalWrite,
    session: DatabaseSession,
):
    try:
        return preview_ledger_reversal(
            session, tenant_id, posting_group_id, reason=body.reason
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/ledger/posting-groups/{posting_group_id}/reversal")
def post_ledger_reversal(
    tenant_id: str,
    posting_group_id: str,
    body: LedgerReversalWrite,
    session: DatabaseSession,
):
    try:
        result = reverse_ledger_posting_group(
            session,
            tenant_id,
            posting_group_id,
            reason=body.reason,
            actor_context=body.actor_context,
            expected_revision=body.expected_revision,
            preview_fingerprint=body.preview_fingerprint,
        )
        return {
            "reversal_id": result.reversal_id,
            "original_posting_group_id": result.original_posting_group_id,
            "reversing_posting_group_id": result.reversing_posting_group_id,
            "request_fingerprint": result.request_fingerprint,
            "replayed": result.replayed,
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/reservations",
    response_model=ReservationRead,
    status_code=status.HTTP_201_CREATED,
)
def post_reservation(tenant_id: str, body: ReservationWrite, session: DatabaseSession):
    try:
        result = reserve(
            session,
            tenant_id,
            body.commitment_id,
            body.quantity,
            handling_unit_id=body.handling_unit_id,
            lot_id=body.lot_id,
            serial_unit_id=body.serial_unit_id,
        )
        reservation = result.reservation
        return {
            "id": reservation.id if reservation else None,
            "requested": str(result.requested),
            "reserved": str(result.reserved),
            "shortage": str(result.shortage),
            "handling_unit_id": reservation.handling_unit_id
            if reservation
            else body.handling_unit_id,
            "lot_id": reservation.lot_id if reservation else body.lot_id,
            "serial_unit_id": reservation.serial_unit_id
            if reservation
            else body.serial_unit_id,
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/reservations")
def list_reservations(
    tenant_id: str,
    session: DatabaseSession,
    limit: int = Query(100, ge=1, le=500),
    status: str = "",
):
    get_tenant(session, tenant_id)
    rows = session.scalars(
        select(Reservation)
        .where(
            Reservation.tenant_id == tenant_id,
            *([Reservation.status == status] if status else []),
        )
        .order_by(Reservation.reserved_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "commitment_id": row.commitment_id,
            "item_id": row.item_id,
            "location_id": row.location_id,
            "quantity": str(row.quantity),
            "status": row.status,
            "reserved_at": row.reserved_at.isoformat(),
            "handling_unit_id": row.handling_unit_id,
            "lot_id": row.lot_id,
            "serial_unit_id": row.serial_unit_id,
        }
        for row in rows
    ]


@router.post(
    "/commitments/{record_id}/holds",
    response_model=HoldRead,
    status_code=status.HTTP_201_CREATED,
)
def post_commitment_hold(
    tenant_id: str, record_id: str, body: HoldWrite, session: DatabaseSession
):
    try:
        hold = hold_commitment(
            session,
            tenant_id,
            record_id,
            body.reason_code,
            body.note,
            created_by="api",
        )
        return {
            **HoldRead.model_validate(hold).model_dump(),
            "created_at": hold.created_at.isoformat(),
            "released_at": hold.released_at.isoformat() if hold.released_at else None,
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/commitments/{record_id}/holds/release", response_model=list[HoldRead])
def post_commitment_hold_release(
    tenant_id: str, record_id: str, session: DatabaseSession
):
    try:
        holds = release_commitment_hold(session, tenant_id, record_id)
        return [
            {
                **HoldRead.model_validate(hold).model_dump(),
                "created_at": hold.created_at.isoformat(),
                "released_at": hold.released_at.isoformat(),
            }
            for hold in holds
        ]
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/documents/{record_id}/holds", response_model=list[HoldRead])
def post_document_holds(
    tenant_id: str, record_id: str, body: HoldWrite, session: DatabaseSession
):
    try:
        holds = hold_document_commitments(
            session,
            tenant_id,
            record_id,
            body.reason_code,
            body.note,
            created_by="api",
        )
        return [
            {
                **HoldRead.model_validate(hold).model_dump(),
                "created_at": hold.created_at.isoformat(),
                "released_at": None,
            }
            for hold in holds
        ]
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/documents", status_code=201)
def post_manual_document(
    tenant_id: str, body: ManualDocumentWrite, session: DatabaseSession
):
    """Record manual normalized evidence without bypassing the application layer."""
    try:
        document, lines = create_manual_document_with_lines(
            session,
            tenant_id,
            body.type,
            body.number,
            body.party_id,
            [line.model_dump() for line in body.lines],
            body.gross_amount,
            currency=body.currency,
            document_date=body.document_date,
            ordered_at=body.ordered_at,
            requested_delivery_at=body.requested_delivery_at,
            customer_reference=body.customer_reference,
            sales_channel=body.sales_channel,
            payment_term_code=body.payment_term_code,
            ship_to_party_id=body.ship_to_party_id,
        )
        return {"id": document.id, "status": document.status, "line_count": len(lines)}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/manual-orders", status_code=status.HTTP_201_CREATED)
def post_manual_order(tenant_id: str, body: ManualOrderWrite, session: DatabaseSession):
    try:
        source, document, lines, commitments = create_manual_order(
            session, tenant_id, **body.model_dump()
        )
        return {
            "source_record_id": source.id,
            "document_id": document.id,
            "document_line_ids": [line.id for line in lines],
            "commitment_ids": [commitment.id for commitment in commitments],
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/facts", status_code=status.HTTP_201_CREATED)
def post_fact_observation(
    tenant_id: str, body: FactObservationWrite, session: DatabaseSession
):
    try:
        fact = observe_fact(session, tenant_id, **body.model_dump())
        return {"id": fact.id}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/reality-gaps")
def get_reality_gaps(
    tenant_id: str,
    session: DatabaseSession,
    status_filter: str | None = Query(default=None, alias="status"),
    destination: str | None = None,
    origin: str | None = None,
    lifecycle: str | None = None,
    rule_status: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
):
    try:
        result = list_gaps(
            session,
            tenant_id,
            status=status_filter,
            destination=destination,
            origin=origin,
            lifecycle=lifecycle,
            rule_status=rule_status,
            query=q,
            page=page,
            size=size,
        )
        return {
            **result,
            "items": [
                {
                    "id": row.id,
                    "question": row.question,
                    "intended_use": row.intended_use,
                    "origin": row.origin,
                    "status": row.status,
                    "destination": row.destination,
                    "revision": row.revision,
                    "rule_statuses": result["rule_statuses"][row.id],
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                }
                for row in result["items"]
            ],
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/reality-gaps", status_code=status.HTTP_201_CREATED)
def post_reality_gap(tenant_id: str, body: RealityGapWrite, session: DatabaseSession):
    try:
        gap = capture_gap(session, tenant_id, **body.model_dump())
        return gap_detail(session, tenant_id, gap.id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/reality-gaps/source-examples/search")
def get_reality_gap_source_examples(
    tenant_id: str,
    session: DatabaseSession,
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=20),
):
    try:
        return {"items": search_source_examples(session, tenant_id, q, limit=limit)}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/reality-gaps/{gap_id}")
def get_reality_gap(tenant_id: str, gap_id: str, session: DatabaseSession):
    try:
        return gap_detail(session, tenant_id, gap_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/reality-gaps/{gap_id}/entries")
def post_reality_gap_entry(
    tenant_id: str, gap_id: str, body: RealityGapEntryWrite, session: DatabaseSession
):
    try:
        add_gap_entry(
            session,
            tenant_id,
            gap_id,
            body.entry_type,
            body.payload,
            expected_revision=body.expected_revision,
        )
        return gap_detail(session, tenant_id, gap_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/reality-gaps/{gap_id}/recommend")
def post_reality_gap_recommendation(
    tenant_id: str, gap_id: str, body: RealityGapRevisionWrite, session: DatabaseSession
):
    try:
        recommend_gap(
            session, tenant_id, gap_id, expected_revision=body.expected_revision
        )
        return gap_detail(session, tenant_id, gap_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/reality-gaps/{gap_id}/decide")
def post_reality_gap_decision(
    request: Request,
    tenant_id: str,
    gap_id: str,
    body: RealityGapDecisionWrite,
    session: DatabaseSession,
):
    require_company_owner(request, session, tenant_id)
    try:
        principal = optional_request_principal(request)
        decide_gap(
            session,
            tenant_id,
            gap_id,
            destination=body.destination,
            rationale=body.rationale,
            expected_revision=body.expected_revision,
            actor_user_id=principal.user_id if principal else None,
        )
        return gap_detail(session, tenant_id, gap_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/reality-gaps/{gap_id}/implementation")
def post_reality_gap_implementation(
    request: Request,
    tenant_id: str,
    gap_id: str,
    body: RealityGapImplementationWrite,
    session: DatabaseSession,
):
    require_company_owner(request, session, tenant_id)
    try:
        principal = optional_request_principal(request)
        prepare_implementation(
            session,
            tenant_id,
            gap_id,
            body.draft,
            expected_revision=body.expected_revision,
            actor_user_id=principal.user_id if principal else None,
        )
        return gap_detail(session, tenant_id, gap_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/reality-gaps/{gap_id}/rules/{rule_id}/simulate")
def post_reality_gap_simulation(
    tenant_id: str,
    gap_id: str,
    rule_id: str,
    session: DatabaseSession,
    limit: int = Query(100, ge=1, le=100),
):
    try:
        gap_detail(session, tenant_id, gap_id)
        return simulate_rule(session, tenant_id, rule_id, limit=limit)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/reality-gaps/{gap_id}/rules/{rule_id}/activate")
def post_reality_gap_rule_activation(
    request: Request,
    tenant_id: str,
    gap_id: str,
    rule_id: str,
    session: DatabaseSession,
):
    require_company_owner(request, session, tenant_id)
    try:
        gap_detail(session, tenant_id, gap_id)
        activate_rule(session, tenant_id, rule_id)
        return gap_detail(session, tenant_id, gap_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/reality-gaps/{gap_id}/rules/{rule_id}/disable")
def post_reality_gap_rule_disable(
    request: Request,
    tenant_id: str,
    gap_id: str,
    rule_id: str,
    session: DatabaseSession,
):
    require_company_owner(request, session, tenant_id)
    try:
        gap_detail(session, tenant_id, gap_id)
        disable_rule(session, tenant_id, rule_id)
        return gap_detail(session, tenant_id, gap_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/reality-gaps/{gap_id}/rules/{rule_id}/replay")
def post_reality_gap_rule_replay(
    request: Request,
    tenant_id: str,
    gap_id: str,
    rule_id: str,
    body: RealityGapReplayWrite,
    session: DatabaseSession,
):
    require_company_owner(request, session, tenant_id)
    try:
        gap_detail(session, tenant_id, gap_id)
        return replay_rule(
            session,
            tenant_id,
            rule_id,
            source_ids=body.source_ids,
            limit=body.limit,
            cursor=body.cursor,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


def _post_payment(
    service: Callable[..., list[LedgerEntry]],
    tenant_id: str,
    body: PaymentPostingWrite,
    session: OrmSession,
):
    try:
        entries = service(session, tenant_id, **body.model_dump())
        return {"ledger_entry_ids": [entry.id for entry in entries]}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/customer-payments", status_code=status.HTTP_201_CREATED)
def post_customer_payment_web(
    tenant_id: str, body: PaymentPostingWrite, session: DatabaseSession
):
    return _post_payment(post_customer_payment, tenant_id, body, session)


@router.post("/finance/supplier-payments", status_code=status.HTTP_201_CREATED)
def post_supplier_payment_web(
    tenant_id: str, body: PaymentPostingWrite, session: DatabaseSession
):
    return _post_payment(post_supplier_payment, tenant_id, body, session)


@router.post("/returns/announcements", status_code=status.HTTP_201_CREATED)
def announce_customer_return_web(
    tenant_id: str, body: ReturnAnnouncementWrite, session: DatabaseSession
):
    payload = body.model_dump()
    try:
        return announce_customer_return(
            session,
            tenant_id,
            payload.pop("commitment_id"),
            payload.pop("quantity"),
            **payload,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/returns/announcements/{announcement_id}/withdrawal")
def withdraw_return_announcement_web(
    tenant_id: str,
    announcement_id: str,
    body: ReturnAnnouncementWithdrawalWrite,
    session: DatabaseSession,
):
    try:
        return withdraw_return_announcement(
            session, tenant_id, announcement_id, **body.model_dump()
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/returns/announcements")
def return_announcements_web(
    tenant_id: str,
    session: DatabaseSession,
    commitment_id: str | None = None,
    status_filter: str | None = None,
):
    try:
        return return_announcements(
            session, tenant_id, commitment_id=commitment_id, status=status_filter
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/payment-runs/preview")
def preview_payment_run_web(
    tenant_id: str, body: PaymentRunPreviewWrite, session: DatabaseSession
):
    try:
        return preview_payment_run(session, tenant_id, **body.model_dump())
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/payment-runs", status_code=status.HTTP_201_CREATED)
def execute_payment_run_web(
    tenant_id: str, body: PaymentRunWrite, session: DatabaseSession
):
    payload = body.model_dump()
    try:
        return execute_payment_run(session, tenant_id, **payload)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/commitments/stale-closures/preview")
def preview_stale_closure_web(
    tenant_id: str, body: StaleClosurePreviewWrite, session: DatabaseSession
):
    try:
        return preview_stale_promise_closure(session, tenant_id, **body.model_dump())
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/commitments/stale-closures", status_code=status.HTTP_201_CREATED)
def close_stale_promises_web(
    tenant_id: str, body: StaleClosureWrite, session: DatabaseSession
):
    try:
        return close_stale_promises(session, tenant_id, **body.model_dump())
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/sales-invoices/postings", status_code=status.HTTP_201_CREATED)
def post_sales_invoice_web(
    tenant_id: str, body: InvoicePostingWrite, session: DatabaseSession
):
    try:
        entries = post_sales_invoice(session, tenant_id, **body.model_dump())
        return {"ledger_entry_ids": [entry.id for entry in entries]}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/supplier-invoices/postings", status_code=status.HTTP_201_CREATED)
def post_supplier_invoice_web(
    tenant_id: str, body: InvoicePostingWrite, session: DatabaseSession
):
    try:
        entries = post_supplier_invoice(session, tenant_id, **body.model_dump())
        return {"ledger_entry_ids": [entry.id for entry in entries]}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/credit-notes/postings", status_code=status.HTTP_201_CREATED)
def post_credit_note_web(
    tenant_id: str, body: CreditNotePostingWrite, session: DatabaseSession
):
    try:
        entries = post_sales_credit_note(session, tenant_id, **body.model_dump())
        return {"ledger_entry_ids": [entry.id for entry in entries]}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/credit-notes/allocations", status_code=status.HTTP_201_CREATED)
def allocate_credit_note_web(
    tenant_id: str, body: CreditNoteNettingWrite, session: DatabaseSession
):
    try:
        allocation = allocate_credit_note(session, tenant_id, **body.model_dump())
        return {"id": allocation.id}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/customer-refunds", status_code=status.HTTP_201_CREATED)
def post_customer_refund_web(
    tenant_id: str, body: CustomerRefundWrite, session: DatabaseSession
):
    try:
        entries = post_customer_refund(session, tenant_id, **body.model_dump())
        return {"ledger_entry_ids": [entry.id for entry in entries]}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/finance/supplier-credit-notes/postings", status_code=status.HTTP_201_CREATED
)
def post_supplier_credit_note_web(
    tenant_id: str, body: CreditNotePostingWrite, session: DatabaseSession
):
    try:
        entries = post_supplier_credit_note(session, tenant_id, **body.model_dump())
        return {"ledger_entry_ids": [entry.id for entry in entries]}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/finance/supplier-credit-notes/allocations", status_code=status.HTTP_201_CREATED
)
def allocate_supplier_credit_note_web(
    tenant_id: str, body: CreditNoteNettingWrite, session: DatabaseSession
):
    try:
        allocation = allocate_supplier_credit_note(
            session, tenant_id, **body.model_dump()
        )
        return {"id": allocation.id}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/supplier-refunds", status_code=status.HTTP_201_CREATED)
def post_supplier_refund_web(
    tenant_id: str, body: CustomerRefundWrite, session: DatabaseSession
):
    try:
        entries = post_supplier_refund(session, tenant_id, **body.model_dump())
        return {"ledger_entry_ids": [entry.id for entry in entries]}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/commitments/{record_id}/revisions", status_code=status.HTTP_201_CREATED)
def revise_commitment_web(
    tenant_id: str,
    record_id: str,
    body: CommitmentRevisionWrite,
    session: DatabaseSession,
):
    try:
        revision = revise_commitment(session, tenant_id, record_id, **body.model_dump())
        return {"id": revision.id, "due_at": revision.due_at}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.patch("/documents/{record_id}")
def patch_document(
    tenant_id: str,
    record_id: str,
    body: DocumentCorrectionWrite,
    session: DatabaseSession,
):
    try:
        document = correct_manual_document(
            session,
            tenant_id,
            record_id,
            document_type=body.type,
            number=body.number,
            party_id=body.party_id,
            amount=body.amount,
            currency=body.currency,
            document_date=body.document_date,
            ordered_at=body.ordered_at,
            requested_delivery_at=body.requested_delivery_at,
            customer_reference=body.customer_reference,
            sales_channel=body.sales_channel,
            payment_term_code=body.payment_term_code,
            ship_to_party_id=body.ship_to_party_id,
        )
        return {"id": document.id, "status": document.status}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/documents/{record_id}/line-correction")
def get_document_line_correction(
    tenant_id: str,
    record_id: str,
    session: DatabaseSession,
):
    try:
        return manual_document_line_snapshot(session, tenant_id, record_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.put("/documents/{record_id}/line-correction")
def put_document_line_correction(
    tenant_id: str,
    record_id: str,
    body: ManualDocumentLineCorrectionWrite,
    session: DatabaseSession,
):
    try:
        return correct_manual_document_lines(
            session,
            tenant_id,
            record_id,
            expected_revision=body.expected_revision,
            lines=[line.model_dump() for line in body.lines],
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/documents/{record_id}/source-versions", status_code=201)
def post_document_source_version(
    tenant_id: str,
    record_id: str,
    body: DocumentSourceVersionWrite,
    session: DatabaseSession,
):
    try:
        source, job = record_corrected_document_source(
            session,
            tenant_id,
            record_id,
            body.payload,
            source_version_at=body.source_version_at,
        )
        return {
            "source": SourceRead.model_validate(source),
            "import_job": ImportJobRead.model_validate(job),
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/documents/{record_id}/holds/release", response_model=list[HoldRead])
def post_document_holds_release(
    tenant_id: str, record_id: str, session: DatabaseSession
):
    try:
        holds = release_document_holds(session, tenant_id, record_id)
        return [
            {
                **HoldRead.model_validate(hold).model_dump(),
                "created_at": hold.created_at.isoformat(),
                "released_at": hold.released_at.isoformat(),
            }
            for hold in holds
        ]
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/parties/{record_id}/delivery-holds",
    response_model=DeliveryHoldRead,
    status_code=status.HTTP_201_CREATED,
)
def post_party_delivery_hold(
    tenant_id: str, record_id: str, body: HoldWrite, session: DatabaseSession
):
    try:
        return hold_party_delivery(
            session,
            tenant_id,
            record_id,
            body.reason_code,
            body.note,
            created_by="api",
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post(
    "/parties/{record_id}/delivery-holds/release",
    response_model=list[DeliveryHoldRead],
)
def post_party_delivery_hold_release(
    tenant_id: str, record_id: str, session: DatabaseSession
):
    try:
        return release_party_delivery_hold(session, tenant_id, record_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


EXPLORER_LINKS = {
    "source_record_id": "source_record",
    "document_id": "document",
    "document_line_id": "document_line",
    "commitment_id": "commitment",
    "party_id": "party",
    "from_party_id": "party",
    "to_party_id": "party",
    "ship_to_party_id": "party",
    "item_id": "item",
    "location_id": "location",
    "from_location_id": "location",
    "to_location_id": "location",
    "action_id": "action",
    "causation_id": "business_event",
}


class CopilotContext(ApiModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["commitment"]
    id: str


from reality.domain.analytics import AnalyticsDefinition as _ChatAnalyticsDefinition


class CopilotAnalyticsContext(ApiModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["analytics"]
    definition: _ChatAnalyticsDefinition


class CopilotMessageWrite(ApiModel):
    context: CopilotContext | CopilotAnalyticsContext | None = None
    message: str = Field(min_length=1, max_length=4000)


class CopilotProposalDecision(ApiModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str | None = None
    review_token: str | None = None
    confirmed: bool = False


def inspector_row(
    label: str,
    value,
    *,
    tone: str = "",
    kind: str = "",
    record_id: str = "",
    presentation=None,
):
    parts = display_parts(value if presentation is None else presentation)
    return {
        "label": label,
        "value": explorer_value(value),
        **({"display_parts": parts} if parts else {}),
        "tone": tone,
        "link": {"kind": kind, "id": record_id} if kind and record_id else None,
    }


def complete_inspector(payload: dict[str, Any]) -> dict[str, Any]:
    """Complete the shared, business-first inspector read contract."""
    title = payload.get("title") or "Record"
    subtitle = payload.get("subtitle") or ""
    meaning = (
        payload.get("meaning") or display_text(title, ". ", subtitle, ".")
        if subtitle
        else payload.get("meaning") or display_text(title, ".")
    )
    payload = {**payload, "meaning": meaning}
    return {
        **payload,
        **{
            f"{key}_parts": display_parts(payload[key])
            for key in ("title", "subtitle", "meaning")
            if display_parts(payload.get(key))
        },
        "eyebrow": payload.get("eyebrow") or "Reality inspector",
        "meaning": meaning,
        "business_reference": payload.get("business_reference"),
        "guidance": payload.get("guidance"),
        "technical_rows": payload.get("technical_rows")
        or [
            inspector_row("Record type", payload.get("kind")),
            inspector_row("Record ID", payload.get("id")),
        ],
    }


def inspector_events(session: OrmSession, tenant_id: str, subject_ids: list[str]):
    if not subject_ids:
        return []
    events = session.scalars(
        select(BusinessEvent)
        .where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.subject_id.in_(subject_ids),
        )
        .order_by(BusinessEvent.occurred_at.desc(), BusinessEvent.sequence.desc())
        .limit(20)
    ).all()
    return [
        {
            "type": event.event_type,
            "occurred_at": event.occurred_at.isoformat(),
            "subject_type": event.subject_type,
            "subject_id": event.subject_id,
        }
        for event in events
    ]


def fact_inspector(session: OrmSession, tenant_id: str, record_id: str):
    fact = session.scalar(
        select(Fact).where(Fact.tenant_id == tenant_id, Fact.id == record_id)
    )
    if fact is None:
        raise NotFound("Fact not found.")
    source = (
        session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == fact.source_record_id,
            )
        )
        if fact.source_record_id
        else None
    )
    supported_subjects = {
        "party",
        "item",
        "location",
        "document",
        "document_line",
        "commitment",
        "reservation",
        "movement",
        "ledger_entry",
    }
    subject_kind = fact.subject_type if fact.subject_type in supported_subjects else ""
    business_predicate = humanize_api(fact.predicate.replace(".", "_"))
    return {
        "kind": "fact",
        "id": fact.id,
        "eyebrow": "Reality / explicit fact",
        "title": business_predicate,
        "subtitle": f"{humanize_api(fact.subject_type)} · {fact.subject_id}",
        "status": "Observed",
        "meaning": "This is a recorded observation, not a current-state guarantee.",
        "business_reference": (
            {
                "label": f"{humanize_api(source.source_system)} {source.source_type}",
                "value": source.external_id,
            }
            if source
            else None
        ),
        "guidance": None,
        "metrics": [
            inspector_row("Value", fact.value),
            inspector_row("Observed", fact.observed_at),
        ],
        "trail": [
            {
                "label": "Source",
                "value": (
                    f"{source.source_system} · {source.external_id}"
                    if source
                    else "No linked source recorded"
                ),
                "active": bool(source),
            },
            {"label": "Fact", "value": fact.id, "active": True},
            {
                "label": "Subject",
                "value": f"{fact.subject_type} · {fact.subject_id}",
                "active": True,
            },
        ],
        "sections": [
            {
                "title": "Observation",
                "rows": [
                    inspector_row("Subject type", humanize_api(fact.subject_type)),
                    inspector_row("Applies to", humanize_api(fact.subject_type)),
                    inspector_row("Business statement", business_predicate),
                    inspector_row("Value", fact.value),
                    inspector_row("Observed", fact.observed_at),
                ],
            },
            {
                "title": "Context and source",
                "rows": [
                    inspector_row(
                        "Subject",
                        fact.subject_id,
                        kind=subject_kind,
                        record_id=fact.subject_id,
                    ),
                    inspector_row(
                        "Source",
                        source.external_id if source else "No linked source recorded",
                        kind="source_record" if source else "",
                        record_id=source.id if source else "",
                    ),
                ],
            },
        ],
        "technical_rows": [
            inspector_row("Fact ID", fact.id),
            inspector_row("Subject ID", fact.subject_id),
            inspector_row("Exact predicate", fact.predicate),
            inspector_row("Source record ID", fact.source_record_id),
        ],
        "events": inspector_events(session, tenant_id, [fact.id, fact.subject_id]),
        "source_payload": source.payload if source else None,
    }


def commitment_inspector(
    session: OrmSession, tenant_id: str, record_id: str, *, exception: bool = False
):
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id, Commitment.id == record_id
        )
    )
    if commitment is None:
        raise NotFound("Commitment not found.")
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == commitment.item_id)
    )
    party_id = (
        commitment.to_party_id
        if commitment.type == "customer_delivery"
        else commitment.from_party_id
    )
    party = session.scalar(
        select(Party).where(Party.tenant_id == tenant_id, Party.id == party_id)
    )
    reservations = session.scalars(
        select(Reservation)
        .where(
            Reservation.tenant_id == tenant_id,
            Reservation.commitment_id == commitment.id,
        )
        .order_by(Reservation.id)
        .limit(101)
    ).all()
    movements = session.scalars(
        select(Movement)
        .where(Movement.tenant_id == tenant_id, Movement.commitment_id == commitment.id)
        .order_by(Movement.occurred_at.desc(), Movement.id)
        .limit(101)
    ).all()
    from reality.services.delivery_reads import fulfillment_expressions

    reserved = session.scalar(
        select(fulfillment_expressions()[0]).where(
            Commitment.tenant_id == tenant_id, Commitment.id == commitment.id
        )
    ) or Decimal(0)
    completeness = {
        "reservations_has_more": len(reservations) > 100,
        "movements_has_more": len(movements) > 100,
    }
    reservations, movements = reservations[:100], movements[:100]
    from reality.services.core import (
        commitment_due_at,
        commitment_quantity,
        fulfilled_quantity,
    )

    promised = commitment_quantity(session, tenant_id, commitment.id)
    due_at = commitment_due_at(session, tenant_id, commitment.id)
    fulfilled = fulfilled_quantity(session, tenant_id, commitment.id)
    uncovered = max(Decimal(0), promised - fulfilled - reserved)
    document = (
        session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id, Document.id == commitment.document_id
            )
        )
        if commitment.document_id
        else None
    )
    source = (
        session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == (document.source_record_id if document else None),
            )
        )
        if document and document.source_record_id
        else None
    )
    return {
        "coverage": completeness,
        "kind": "exception" if exception else "commitment",
        "id": commitment.id,
        "eyebrow": "Derived operational exception"
        if exception
        else "Operational Reality",
        "title": "Customer commitment insufficiently reserved"
        if exception
        else humanize_api(commitment.type),
        "subtitle": f"{party.name if party else 'Unknown party'} · {item.name if item else 'Unknown item'}",
        "status": "Needs review" if uncovered > 0 else humanize_api(commitment.status),
        "metrics": [
            inspector_row("Committed", promised),
            inspector_row("Reserved", reserved),
            inspector_row("Fulfilled", fulfilled),
            inspector_row(
                "Uncovered", uncovered, tone="danger" if uncovered else "success"
            ),
        ],
        "trail": [
            {
                "label": "Source",
                "value": f"{source.source_system} · {source.external_id}"
                if source
                else "No external source",
                "active": bool(source),
            },
            {
                "label": "Evidence",
                "value": f"{document.type} · {document.number}"
                if document
                else "No document evidence",
                "active": bool(document),
            },
            {"label": "Reality", "value": commitment.id, "active": True},
        ],
        "sections": [
            {
                "title": "Why it appears",
                "rows": [
                    inspector_row(
                        "Explanation",
                        display_text(
                            "The open commitment has ",
                            uncovered,
                            f" {item.unit if item else 'units'} without an active reservation or linked movement.",
                        ),
                    )
                ],
            },
            {
                "title": "Business context",
                "rows": [
                    inspector_row(
                        "Counterparty",
                        party.name if party else party_id,
                        kind="party",
                        record_id=party.id if party else "",
                    ),
                    inspector_row(
                        "Item",
                        item.name if item else commitment.item_id,
                        kind="item",
                        record_id=item.id if item else "",
                    ),
                    inspector_row("Due", due_at),
                    inspector_row("Priority", commitment.priority),
                ],
            },
            {
                "title": "Reservations",
                "rows": [
                    inspector_row(
                        row.status,
                        display_text(row.quantity, f" · {row.location_id}"),
                        kind="reservation",
                        record_id=row.id,
                    )
                    for row in reservations
                ],
            },
            {
                "title": "Movements",
                "rows": [
                    inspector_row(
                        row.type,
                        display_text(row.quantity, f" · {row.occurred_at.isoformat()}"),
                        kind="movement",
                        record_id=row.id,
                    )
                    for row in movements
                ],
            },
        ],
        "events": inspector_events(session, tenant_id, [commitment.id]),
        "source_payload": source.payload if source else None,
    }


def humanize_api(value: str) -> str:
    return value.replace("_", " ").title()


def _historical_pricing_summary(explanation: dict[str, Any]) -> str:
    agreed = explanation["agreed"]
    retained = (
        f"entry {agreed['price_list_entry_id']} · list {agreed['price_list_code']}"
        if agreed["price_list_entry_id"]
        else "manual agreement · no selected pricing entry"
    )
    current = explanation["current_resolution"]
    if current["available"]:
        comparison = display_text(
            "current ",
            money(current["unit_price"], current["currency"], precision=4),
            f"/{current['unit']}",
        )
        state = "changed" if explanation["changed_since_agreement"] else "unchanged"
        comparison = display_text(comparison, f" · {state}")
    else:
        comparison = f"current unavailable · {current['unavailable_reason']}"
    return display_text(
        "agreed ",
        money(agreed["unit_price"], agreed["currency"], precision=4),
        f"/{agreed['unit']} · {retained} · ",
        comparison,
    )


def document_inspector(session: OrmSession, tenant_id: str, record_id: str):
    from reality.services.core import _order_line_billing

    detail = document_detail(session, tenant_id, record_id)
    document = detail["document"]
    source = detail["source"]
    correction = manual_document_line_snapshot(session, tenant_id, record_id)
    pricing = {
        line.id: historical_pricing_explanation(session, tenant_id, line.id)
        for line in detail["lines"]
    }
    return {
        "kind": "document",
        "id": document.id,
        "eyebrow": "Evidence",
        "title": f"{humanize_api(document.type)} {document.number}",
        "evidence_lines": [
            {
                "id": line.id,
                "label": line.sku or line.description or line.id,
                "quantity": str(line.quantity),
                "gross_amount": str(line.gross_amount),
                "unit": line.unit,
                **(
                    {"billing": _order_line_billing(session, tenant_id, line.id)}
                    if document.type in {"sales_order", "purchase_order"}
                    else {}
                ),
            }
            for line in detail["lines"]
        ],
        "subtitle": detail["party"].name if detail["party"] else "No counterparty",
        "status": humanize_api(document.status),
        "metrics": [
            inspector_row(
                "Gross amount", money(document.gross_amount, document.currency)
            ),
            inspector_row("Lines", len(detail["lines"])),
            inspector_row("Commitments", len(detail["commitments"])),
            inspector_row("Ledger entries", len(detail["ledger_entries"])),
        ],
        "trail": [
            {
                "label": "Source",
                "value": f"{source.source_system} · {source.external_id}"
                if source
                else "Manual / internal",
                "active": bool(source),
            },
            {"label": "Evidence", "value": document.number, "active": True},
            {
                "label": "Reality",
                "value": f"{len(detail['commitments'])} linked records",
                "active": bool(detail["commitments"] or detail["ledger_entries"]),
            },
        ],
        "sections": [
            {
                "title": "Document",
                "rows": [
                    inspector_row("Date", document.document_date),
                    inspector_row("Currency", document.currency),
                    inspector_row("Customer reference", document.customer_reference),
                    inspector_row("Sales channel", document.sales_channel),
                ],
            },
            {
                "title": "Correction",
                "rows": [
                    inspector_row(
                        "Evidence",
                        "Manual correction available"
                        if correction["correctable"]
                        else correction["correction_guidance"],
                    ),
                    inspector_row("Version", correction["revision"] or "Source-owned"),
                ],
            },
            {
                "title": "Lines",
                "rows": [
                    inspector_row(
                        line.sku or line.description or line.id,
                        display_text(
                            line.quantity,
                            f" {line.unit} · ",
                            money(line.gross_amount, document.currency),
                        ),
                        kind="item",
                        record_id=line.item_id or "",
                    )
                    for line in detail["lines"]
                ],
            },
            *(
                [
                    {
                        "title": "Referenced positions",
                        "rows": [
                            inspector_row(
                                line.sku or line.description or line.id,
                                "Document line",
                                kind="document_line",
                                record_id=line.billed_document_line_id,
                            )
                            for line in detail["lines"]
                            if line.billed_document_line_id
                        ],
                    }
                ]
                if any(line.billed_document_line_id for line in detail["lines"])
                else []
            ),
            {
                "title": "Historical pricing",
                "rows": [
                    inspector_row(
                        line.sku or line.description or line.id,
                        _historical_pricing_summary(pricing[line.id]),
                    )
                    for line in detail["lines"]
                ],
            },
            {
                "title": "Operational Reality",
                "rows": [
                    inspector_row(
                        humanize_api(row.type),
                        display_text(row.quantity, f" · {humanize_api(row.status)}"),
                        kind="commitment",
                        record_id=row.id,
                    )
                    for row in detail["commitments"]
                ],
            },
            {
                "title": "Financial Reality",
                "rows": [
                    inspector_row(
                        row.account,
                        display_text(
                            f"{row.debit_credit} · ", money(row.amount, row.currency)
                        ),
                    )
                    for row in detail["ledger_entries"]
                ],
            },
        ],
        "events": inspector_events(
            session,
            tenant_id,
            [document.id, *(row.id for row in detail["commitments"])],
        ),
        "source_payload": source.payload if source else None,
    }


def party_inspector(session: OrmSession, tenant_id: str, record_id: str):
    detail = party_detail(session, tenant_id, record_id)
    party = detail["party"]
    source = detail["source"]
    return {
        "kind": "party",
        "id": party.id,
        "eyebrow": "Reference data / party",
        "title": party.name,
        "subtitle": " · ".join(role.role for role in detail["roles"])
        or humanize_api(party.type),
        "status": "Active" if party.is_active else "Inactive",
        "metrics": [
            inspector_row("Documents", len(detail["documents"])),
            inspector_row("Commitments", len(detail["commitments"])),
            inspector_row("Ledger entries", len(detail["ledger_entries"])),
            inspector_row("Currency", party.default_currency),
        ],
        "trail": [
            {
                "label": "Source",
                "value": f"{source.source_system} · {source.external_id}"
                if source
                else "Manual / internal",
                "active": bool(source),
            },
            {"label": "Reference", "value": party.id, "active": True},
            {
                "label": "Reality",
                "value": f"{len(detail['commitments'])} commitments",
                "active": bool(detail["commitments"]),
            },
        ],
        "sections": [
            {
                "title": "Commercial defaults",
                "rows": [
                    inspector_row("Accounting code", party.accounting_code),
                    inspector_row("Payment terms", party.payment_term_code),
                    inspector_row(
                        "Credit limit",
                        party.credit_limit,
                        presentation=money(party.credit_limit, party.default_currency)
                        if party.credit_limit is not None
                        else None,
                    ),
                    inspector_row("Tax identifier", party.tax_identifier),
                ],
            },
            {
                "title": "Commitments",
                "rows": [
                    inspector_row(
                        humanize_api(row.type),
                        display_text(row.quantity, f" · {humanize_api(row.status)}"),
                        kind="commitment",
                        record_id=row.id,
                    )
                    for row in detail["commitments"]
                ],
            },
            {
                "title": "Documents",
                "rows": [
                    inspector_row(
                        humanize_api(row.type),
                        row.number,
                        kind="document",
                        record_id=row.id,
                    )
                    for row in detail["documents"]
                ],
            },
        ],
        "events": inspector_events(session, tenant_id, [party.id]),
        "source_payload": source.payload if source else None,
    }


def item_inspector(session: OrmSession, tenant_id: str, record_id: str):
    detail = item_detail(session, tenant_id, record_id)
    item = detail["item"]
    source = detail["source"]
    active_reserved_quantity = sum(
        (row.quantity for row in detail["reservations"] if row.status == "active"),
        Decimal(0),
    )
    return {
        "kind": "item",
        "id": item.id,
        "eyebrow": "Reference data / item",
        "title": item.name,
        "subtitle": f"{item.sku} · {item.unit}",
        "status": "Active" if item.is_active else "Inactive",
        "metrics": [
            inspector_row("Physical", detail["physical"]),
            inspector_row("Reserved", active_reserved_quantity),
            inspector_row("Commitments", len(detail["commitments"])),
            inspector_row("Movements", len(detail["movements"])),
        ],
        "trail": [
            {
                "label": "Source",
                "value": f"{source.source_system} · {source.external_id}"
                if source
                else "Manual / internal",
                "active": bool(source),
            },
            {"label": "Reference", "value": item.id, "active": True},
            {
                "label": "Reality",
                "value": f"{len(detail['movements'])} movements",
                "active": bool(detail["movements"]),
            },
        ],
        "sections": [
            {
                "title": "Item configuration",
                "rows": [
                    inspector_row("Type", item.item_type),
                    inspector_row("Tracking", item.tracking_type),
                    inspector_row("Purchase unit", item.purchase_unit),
                    inspector_row(
                        "Lead time", display_text(item.lead_time_days, " days")
                    ),
                ],
            },
            {
                "title": "Commitments",
                "rows": [
                    inspector_row(
                        humanize_api(row.type),
                        display_text(row.quantity, f" · {humanize_api(row.status)}"),
                        kind="commitment",
                        record_id=row.id,
                    )
                    for row in detail["commitments"]
                ],
            },
            {
                "title": "Recent movements",
                "rows": [
                    inspector_row(
                        humanize_api(row.type),
                        display_text(row.quantity, " · ", row.occurred_at),
                        kind="movement",
                        record_id=row.id,
                    )
                    for row in detail["movements"][:20]
                ],
            },
        ],
        "events": inspector_events(session, tenant_id, [item.id]),
        "source_payload": source.payload if source else None,
    }


def location_inspector(session: OrmSession, tenant_id: str, record_id: str):
    detail = location_detail(session, tenant_id, record_id)
    location = detail["location"]
    return {
        "kind": "location",
        "id": location.id,
        "eyebrow": "Reference data / location",
        "title": location.name,
        "subtitle": humanize_api(location.type),
        "status": "Active" if location.is_active else "Inactive",
        "metrics": [
            inspector_row("Stocked items", len(detail["stock"])),
            inspector_row("Commitments", len(detail["commitments"])),
            inspector_row("Movements", len(detail["movements"])),
            inspector_row("Allows stock", location.allows_stock),
        ],
        "trail": [
            {"label": "Reference", "value": location.id, "active": True},
            {
                "label": "Inventory",
                "value": f"{len(detail['stock'])} items",
                "active": bool(detail["stock"]),
            },
            {
                "label": "Reality",
                "value": f"{len(detail['movements'])} movements",
                "active": bool(detail["movements"]),
            },
        ],
        "sections": [
            {
                "title": "Current stock",
                "rows": [
                    inspector_row(
                        row["item"].name,
                        row["physical"],
                        kind="item",
                        record_id=row["item"].id,
                    )
                    for row in detail["stock"]
                ],
            },
            {
                "title": "Recent movements",
                "rows": [
                    inspector_row(
                        humanize_api(row.type),
                        display_text(row.quantity, f" · {row.occurred_at.isoformat()}"),
                        kind="movement",
                        record_id=row.id,
                    )
                    for row in detail["movements"][:20]
                ],
            },
        ],
        "events": inspector_events(session, tenant_id, [location.id]),
        "source_payload": None,
    }


def reservation_inspector(session: OrmSession, tenant_id: str, record_id: str):
    row = session.scalar(
        select(Reservation).where(
            Reservation.tenant_id == tenant_id, Reservation.id == record_id
        )
    )
    if row is None:
        raise NotFound("Reservation not found.")
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == row.item_id)
    )
    location = session.scalar(
        select(Location).where(
            Location.tenant_id == tenant_id, Location.id == row.location_id
        )
    )
    return {
        "kind": "reservation",
        "id": row.id,
        "eyebrow": "Operational Reality / reservation",
        "title": display_text(
            row.quantity, f" {item.unit if item else 'units'} reserved"
        ),
        "subtitle": f"{item.name if item else row.item_id} · {location.name if location else row.location_id}",
        "status": humanize_api(row.status),
        "metrics": [
            inspector_row("Quantity", row.quantity),
            inspector_row("Reserved at", row.reserved_at),
            inspector_row("Lot", row.lot_id),
            inspector_row("Serial", row.serial_unit_id),
        ],
        "trail": [
            {"label": "Commitment", "value": row.commitment_id, "active": True},
            {"label": "Reservation", "value": row.id, "active": True},
            {
                "label": "Stock",
                "value": location.name if location else row.location_id,
                "active": True,
            },
        ],
        "sections": [
            {
                "title": "Shortest true links",
                "rows": [
                    inspector_row(
                        "Commitment",
                        row.commitment_id,
                        kind="commitment",
                        record_id=row.commitment_id,
                    ),
                    inspector_row(
                        "Item",
                        item.name if item else row.item_id,
                        kind="item",
                        record_id=row.item_id,
                    ),
                    inspector_row(
                        "Location",
                        location.name if location else row.location_id,
                        kind="location",
                        record_id=row.location_id,
                    ),
                    inspector_row("Handling unit", row.handling_unit_id),
                ],
            }
        ],
        "events": inspector_events(session, tenant_id, [row.id, row.commitment_id]),
        "source_payload": None,
    }


def movement_inspector(session: OrmSession, tenant_id: str, record_id: str):
    row = session.scalar(
        select(Movement).where(
            Movement.tenant_id == tenant_id, Movement.id == record_id
        )
    )
    if row is None:
        raise NotFound("Movement not found.")
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == row.item_id)
    )
    source = (
        session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == row.source_record_id,
            )
        )
        if row.source_record_id
        else None
    )
    correction_snapshot = movement_correction_snapshot(session, tenant_id, record_id)
    chain_rows = []
    for label, member in (
        ("Original", correction_snapshot["original"]),
        ("Compensation", correction_snapshot["compensation"]),
        ("Replacement", correction_snapshot["replacement"]),
    ):
        if member:
            chain_rows.append(
                inspector_row(
                    label,
                    member["id"],
                    kind="movement",
                    record_id=member["id"],
                )
            )
    chain_ids = [
        row["id"]
        for row in (
            correction_snapshot["original"],
            correction_snapshot["compensation"],
            correction_snapshot["replacement"],
        )
        if row
    ]
    return {
        "kind": "movement",
        "id": row.id,
        "eyebrow": "Physical journal / movement",
        "title": humanize_api(row.type),
        "subtitle": display_text(
            f"{item.name if item else row.item_id} · ",
            row.quantity,
            f" {item.unit if item else ''}",
        ),
        "status": correction_snapshot["status"].title(),
        "metrics": [
            inspector_row("Quantity", row.quantity),
            inspector_row("Occurred", row.occurred_at),
            inspector_row("From", row.from_location_id),
            inspector_row("To", row.to_location_id),
        ],
        "trail": [
            {
                "label": "Source",
                "value": source.external_id if source else "Manual / internal",
                "active": bool(source),
            },
            {"label": "Movement", "value": row.id, "active": True},
            {
                "label": "Commitment",
                "value": row.commitment_id or "Unlinked",
                "active": bool(row.commitment_id),
            },
        ],
        "sections": [
            {
                "title": "Links",
                "rows": [
                    inspector_row(
                        "Item",
                        item.name if item else row.item_id,
                        kind="item",
                        record_id=row.item_id,
                    ),
                    inspector_row(
                        "Commitment",
                        row.commitment_id,
                        kind="commitment",
                        record_id=row.commitment_id or "",
                    ),
                    inspector_row("Handling unit", row.handling_unit_id),
                    inspector_row("Lot", row.lot_id),
                    inspector_row("Serial", row.serial_unit_id),
                ],
            },
            {
                "title": "Correction chain",
                "rows": chain_rows
                + (
                    [
                        inspector_row(
                            "Reason", correction_snapshot["correction"]["reason"]
                        ),
                        inspector_row(
                            "Corrected",
                            correction_snapshot["correction"]["corrected_at"],
                        ),
                        inspector_row(
                            "Actor context",
                            json.dumps(
                                correction_snapshot["correction"]["actor_context"],
                                sort_keys=True,
                            ),
                        ),
                    ]
                    if correction_snapshot["correction"]
                    else []
                ),
            },
        ],
        "events": inspector_events(session, tenant_id, chain_ids),
        "source_payload": source.payload if source else None,
    }


def shipment_inspector(
    session: OrmSession, tenant_id: str, record_id: str, *, package: bool = False
):
    from reality.services.shipments import shipment_explain

    detail = shipment_explain(session, tenant_id, record_id)
    selected_package = next(
        (row for row in detail["packages"] if row["id"] == record_id), None
    )
    if package and selected_package is None:
        raise NotFound("Shipment package not found.")
    source_id = (
        selected_package["source_record_id"]
        if selected_package
        else detail["source_record_id"]
    )
    source = (
        session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id, SourceRecord.id == source_id
            )
        )
        if source_id
        else None
    )
    package_ids = (
        {selected_package["id"]}
        if selected_package
        else {row["id"] for row in detail["packages"]}
    )
    movements = [row for row in detail["movements"] if row["package_id"] in package_ids]
    events = [
        row
        for row in detail["events"]
        if row["package_id"] is None or row["package_id"] in package_ids
    ]
    subject_id = selected_package["id"] if selected_package else detail["id"]
    return {
        "kind": "shipment_package" if selected_package else "shipment",
        "id": subject_id,
        "eyebrow": "Physical logistics",
        "title": (
            selected_package["tracking_number"]
            if selected_package and selected_package["tracking_number"]
            else ("Shipment package" if selected_package else "Shipment")
        ),
        "subtitle": f"{detail['direction']} · {detail['purpose']}",
        "status": "Derived at read time",
        "metrics": [
            inspector_row("Packages", len(detail["packages"])),
            inspector_row("Physical movements", len(movements)),
            inspector_row("Current tracking events", len(events)),
            inspector_row("Promised quantity", detail["quantities"]["promised"]),
            inspector_row("Dispatched quantity", detail["quantities"]["dispatched"]),
            inspector_row("Received quantity", detail["quantities"]["received"]),
        ],
        "trail": [
            {
                "label": "Source",
                "value": source.external_id if source else "Manual / internal",
                "active": bool(source),
            },
            {"label": "Shipment", "value": detail["id"], "active": True},
            {
                "label": "Package",
                "value": selected_package["id"] if selected_package else "All packages",
                "active": bool(selected_package),
            },
            {
                "label": "Movement",
                "value": f"{len(movements)} effective",
                "active": bool(movements),
            },
        ],
        "sections": [
            {
                "title": "Identity and party",
                "rows": [
                    inspector_row("Direction", detail["direction"]),
                    inspector_row("Purpose", detail["purpose"]),
                    inspector_row(
                        "Counterparty",
                        detail["counterparty_id"],
                        kind="party",
                        record_id=detail["counterparty_id"],
                    ),
                    inspector_row("Recorded", detail["created_at"]),
                ],
            },
            {
                "title": "Packages",
                "rows": [
                    inspector_row(
                        row["carrier"] or "Package",
                        row["tracking_number"] or row["id"],
                        kind="shipment_package",
                        record_id=row["id"],
                    )
                    for row in detail["packages"]
                ],
            },
            {
                "title": "Effective physical contents",
                "rows": [
                    inspector_row(
                        row["type"],
                        f"{row['quantity']} · {row['item_id']}",
                        kind="movement",
                        record_id=row["id"],
                    )
                    for row in movements
                ],
            },
            {
                "title": "Current tracking observations",
                "rows": [
                    inspector_row(
                        row["event_type"],
                        row["occurred_at"] or "Time not stated",
                    )
                    for row in events
                ],
            },
        ],
        "events": inspector_events(session, tenant_id, [detail["id"]]),
        "source_payload": source.payload if source else None,
    }


def payment_inspector(session: OrmSession, tenant_id: str, record_id: str):
    row = session.scalar(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant_id, LedgerEntry.id == record_id
        )
    )
    if row is None:
        raise NotFound("Payment not found.")
    document = (
        session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id, Document.id == row.document_id
            )
        )
        if row.document_id
        else None
    )
    party = (
        session.scalar(
            select(Party).where(Party.tenant_id == tenant_id, Party.id == row.party_id)
        )
        if row.party_id
        else None
    )
    source = (
        session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == row.source_record_id,
            )
        )
        if row.source_record_id
        else None
    )
    reversal = ledger_reversal_snapshot(session, tenant_id, row.posting_group_id)
    relation = reversal["reversal"]
    chain_group_ids = {
        entry["posting_group_id"]
        for entry in reversal["original_entries"] + reversal["reversing_entries"]
    }
    chain_entry_ids = {
        entry["id"]
        for entry in reversal["original_entries"] + reversal["reversing_entries"]
    }
    reversal_rows = [
        inspector_row("Role", reversal["role"]),
        inspector_row("Operational status", reversal["status"]),
    ]
    if relation:
        reversal_rows.extend(
            [
                inspector_row(
                    "Original posting group",
                    relation["original_posting_group_id"],
                ),
                inspector_row(
                    "Reversing posting group",
                    relation["reversing_posting_group_id"],
                ),
                inspector_row("Reason", relation["reason"]),
                inspector_row("Reversed", relation["reversed_at"]),
                inspector_row(
                    "Actor context",
                    json.dumps(relation["actor_context"], sort_keys=True),
                ),
                inspector_row(
                    "Net effect",
                    "Zero across the original and exact inverse groups",
                ),
            ]
        )
    allocation_rows = [
        inspector_row(
            "Inactive allocation",
            display_text(
                money(allocation["amount"], allocation["currency"]),
                f" · {allocation['id']}",
            ),
        )
        for allocation in reversal["affected_allocations"]
    ]
    return {
        "kind": "payment",
        "id": row.id,
        "eyebrow": "Financial Reality / payment",
        "title": money(row.amount, row.currency),
        "subtitle": party.name if party else row.account,
        "status": "Reversed" if reversal["status"] == "reversed" else "Posted",
        "metrics": [
            inspector_row("Amount", money(row.amount, row.currency)),
            inspector_row("Direction", row.debit_credit),
            inspector_row("Effective", row.effective_at),
            inspector_row("Posting group", row.posting_group_id),
        ],
        "trail": [
            {
                "label": "Source",
                "value": source.external_id if source else "Manual / internal",
                "active": bool(source),
            },
            {
                "label": "Evidence",
                "value": document.number if document else "No document",
                "active": bool(document),
            },
            {"label": "Ledger", "value": row.id, "active": True},
        ],
        "sections": [
            {
                "title": "Links",
                "rows": [
                    inspector_row(
                        "Party",
                        party.name if party else row.party_id,
                        kind="party",
                        record_id=row.party_id or "",
                    ),
                    inspector_row(
                        "Document",
                        document.number if document else row.document_id,
                        kind="document",
                        record_id=row.document_id or "",
                    ),
                    inspector_row("Account", row.account),
                ],
            },
            {"title": "Reversal chain", "rows": reversal_rows},
            {"title": "Allocation history", "rows": allocation_rows},
        ],
        "events": inspector_events(
            session,
            tenant_id,
            sorted(chain_entry_ids | chain_group_ids),
        ),
        "source_payload": source.payload if source else None,
    }


def import_exception_inspector(session: OrmSession, tenant_id: str, record_id: str):
    parts = record_id.split("__")
    if len(parts) != 3 or parts[0] != "import":
        raise NotFound("Import exception not found.")
    job = session.scalar(
        select(ImportJob).where(
            ImportJob.tenant_id == tenant_id, ImportJob.id == parts[1]
        )
    )
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id, SourceRecord.id == parts[2]
        )
    )
    if job is None or source is None or job.source_record_id != source.id:
        raise NotFound("Import exception not found.")
    return {
        "kind": "exception",
        "id": record_id,
        "eyebrow": "Source processing exception",
        "title": "Missing item mapping",
        "subtitle": f"{source.source_system} · {source.source_type} · {source.external_id}",
        "status": "Needs mapping",
        "metrics": [
            inspector_row("Attempts", job.attempts),
            inspector_row("Version", source.version),
            inspector_row("State", job.status, tone="danger"),
        ],
        "trail": [
            {"label": "Source", "value": source.external_id, "active": True},
            {"label": "Evidence", "value": "Not interpreted", "active": False},
            {"label": "Reality", "value": "Not created", "active": False},
        ],
        "sections": [
            {
                "title": "What blocks processing",
                "rows": [
                    inspector_row("Error", job.error),
                    inspector_row(
                        "Next step",
                        "Create or map the missing item, then retry this import.",
                    ),
                ],
            }
        ],
        "events": inspector_events(session, tenant_id, [source.id]),
        "source_payload": source.payload,
    }


@router.get("/finance/invoice-credit/{invoice_id}")
def invoice_credit_context(tenant_id: str, invoice_id: str, session: DatabaseSession):
    from reality.services.credit_actions import _credit_context
    from reality.services.order_actions import _json

    try:
        return json.loads(_json(_credit_context(session, tenant_id, invoice_id)))
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/inspector/{kind}/{record_id}")
def get_inspector(kind: str, record_id: str, tenant_id: str, session: DatabaseSession):
    try:
        if kind in {"document_line", "source_record", "business_event"}:
            from reality.services.delivery_reads import delivery_evidence

            return complete_inspector(
                delivery_evidence(session, tenant_id, kind, record_id)
            )
        if kind == "document":
            payload = document_inspector(session, tenant_id, record_id)
        if kind == "fact":
            payload = fact_inspector(session, tenant_id, record_id)
        if kind == "commitment":
            payload = commitment_inspector(session, tenant_id, record_id)
        if kind == "party":
            payload = party_inspector(session, tenant_id, record_id)
        if kind == "item":
            payload = item_inspector(session, tenant_id, record_id)
        if kind == "location":
            payload = location_inspector(session, tenant_id, record_id)
        if kind == "reservation":
            payload = reservation_inspector(session, tenant_id, record_id)
        if kind == "movement":
            payload = movement_inspector(session, tenant_id, record_id)
        if kind == "shipment":
            payload = shipment_inspector(session, tenant_id, record_id)
        if kind == "shipment_package":
            payload = shipment_inspector(session, tenant_id, record_id, package=True)
        if kind in {"payment", "ledger_entry"}:
            payload = payment_inspector(session, tenant_id, record_id)
        if kind == "exception":
            from reality.services.exceptions import explain_operational_exception

            explanation = explain_operational_exception(session, tenant_id, record_id)
            values = explanation["causal_values"]
            metrics = [
                inspector_row("Class", explanation["class_id"]),
                inspector_row("Record", explanation["record_id"]),
            ]
            # Keyed on the cause, not the class: the same shortfall is now
            # reported by the overdue class as well, and a presentation adapter
            # must not decide which classes carry which reason.
            if "insufficient_reservation" in explanation["cause_ids"]:
                metrics.append(
                    inspector_row(
                        "Uncovered", values["unreserved_quantity"], tone="danger"
                    )
                )
            catalog_entry = next(
                entry
                for entry in load_operational_exception_catalog().classes
                if entry["id"] == explanation["class_id"]
            )
            business_reference = None
            source_reference = explanation["trace"].get("source_record_id")
            evidence_reference = explanation["trace"].get("document_id") or explanation[
                "trace"
            ].get("import_job_id")
            if explanation["record_type"] == "commitment":
                commitment = session.scalar(
                    select(Commitment).where(
                        Commitment.tenant_id == tenant_id,
                        Commitment.id == explanation["record_id"],
                    )
                )
                if commitment:
                    document = (
                        session.scalar(
                            select(Document).where(
                                Document.tenant_id == tenant_id,
                                Document.id == commitment.document_id,
                            )
                        )
                        if commitment.document_id
                        else None
                    )
                    source = (
                        session.scalar(
                            select(SourceRecord).where(
                                SourceRecord.tenant_id == tenant_id,
                                SourceRecord.id == document.source_record_id,
                            )
                        )
                        if document and document.source_record_id
                        else None
                    )
                    party_id = (
                        commitment.to_party_id
                        if commitment.type == "customer_delivery"
                        else commitment.from_party_id
                    )
                    party = session.scalar(
                        select(Party).where(
                            Party.tenant_id == tenant_id, Party.id == party_id
                        )
                    )
                    item = session.scalar(
                        select(Item).where(
                            Item.tenant_id == tenant_id,
                            Item.id == commitment.item_id,
                        )
                    )
                    if source:
                        business_reference = {
                            "label": f"{humanize_api(source.source_system)} {source.source_type}",
                            "value": source.external_id,
                        }
                        source_reference = (
                            f"{source.source_system} · {source.external_id}"
                        )
                    elif document:
                        business_reference = {
                            "label": humanize_api(document.type),
                            "value": document.number,
                        }
                    else:
                        business_reference = {
                            "label": "Affected commitment",
                            "value": f"{party.name if party else 'Unknown party'} · {item.name if item else 'Unknown item'}",
                        }
                    if document:
                        evidence_reference = (
                            f"{humanize_api(document.type)} · {document.number}"
                        )
            payload = {
                "kind": "exception",
                "id": explanation["id"],
                "eyebrow": "Operational exception",
                "title": explanation["title"],
                "subtitle": explanation["impact"],
                "status": "Needs review",
                "meaning": f"{explanation['title']}. {explanation['impact']}.",
                "business_reference": business_reference,
                "guidance": catalog_entry["clears_through"],
                "metrics": metrics,
                "trail": [
                    {
                        "label": "Source",
                        "value": source_reference or "Absent",
                        "active": bool(explanation["trace"].get("source_record_id")),
                    },
                    {
                        "label": "Evidence",
                        "value": evidence_reference or "Absent",
                        "active": bool(
                            explanation["trace"].get("document_id")
                            or explanation["trace"].get("import_job_id")
                        ),
                    },
                    {
                        "label": "Reality",
                        "value": explanation["record_id"],
                        "active": True,
                    },
                ],
                "sections": [
                    {
                        "title": "Why this is an exception",
                        "rows": [
                            inspector_row(key.replace("_", " ").title(), value)
                            for key, value in values.items()
                        ],
                    }
                ],
                "technical_rows": [
                    inspector_row("Exception ID", explanation["id"]),
                    inspector_row("Exception class", explanation["class_id"]),
                    inspector_row("Record ID", explanation["record_id"]),
                ],
                "events": [],
                "source_payload": explanation["raw_source"],
            }
        if kind not in {
            "document",
            "fact",
            "commitment",
            "party",
            "item",
            "location",
            "reservation",
            "movement",
            "shipment",
            "shipment_package",
            "payment",
            "ledger_entry",
            "exception",
        }:
            raise NotFound("Inspector record type not found.")
        return complete_inspector(payload)
    except NotFound as error:
        raise api_error(error) from error


def copilots_payload(
    session: OrmSession,
    tenant_id: str,
    session_id: str | None = None,
    *,
    archived: bool = False,
):
    conversations = chat_sessions(session, tenant_id, limit=50, archived=archived)
    active = next((row for row in conversations if row.id == session_id), None)
    if session_id and active is None:
        raise NotFound("ChatSession not found.")
    active = active or (conversations[0] if conversations else None)
    messages = chat_messages(session, tenant_id, active.id) if active else []
    proposals = (
        proposals_awaiting_approval(session, tenant_id)
        if active and not archived
        else []
    )
    return {
        "sessions": [
            {
                "id": row.id,
                "title": row.title,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
                "archived_at": row.archived_at.isoformat() if row.archived_at else None,
            }
            for row in conversations
        ],
        "active_session_id": active.id if active else None,
        "messages": [
            {
                "id": row.id,
                "role": row.role,
                "content": row.content,
                "created_at": row.created_at.isoformat(),
            }
            for row in messages
        ],
        "proposals": [
            {
                "id": row.id,
                "tool": row.type.removeprefix("tool:"),
                "actor_type": row.actor_type,
                "status": row.status,
                "input": json.loads(row.input),
                "preview": json.loads(row.output),
                "created_at": row.created_at.isoformat(),
            }
            for row in proposals
        ],
        "suggestions": chat_suggestions(session, tenant_id),
        # The client needs this to tell "no conversations at all" apart from
        # "none active", so archived work stays reachable after the last chat is hidden.
        "has_archived": bool(chat_sessions(session, tenant_id, limit=1, archived=True)),
    }


@router.get("/copilot")
def get_copilot(
    tenant_id: str,
    session: DatabaseSession,
    session_id: str | None = None,
    archived: bool = False,
):
    try:
        return copilots_payload(session, tenant_id, session_id, archived=archived)
    except NotFound as error:
        raise api_error(error) from error


@router.post("/copilot/sessions", status_code=201)
def post_copilot_session(tenant_id: str, session: DatabaseSession):
    try:
        conversation = create_chat_session(session, tenant_id)
        return {"id": conversation.id, "title": conversation.title}
    except NotFound as error:
        raise api_error(error) from error


@router.delete("/copilot/sessions/{session_id}", status_code=204)
def delete_copilot_conversation(
    tenant_id: str, session_id: str, session: DatabaseSession
):
    try:
        delete_chat_session(session, tenant_id, session_id)
    except NotFound as error:
        raise api_error(error) from error


@router.post("/copilot/sessions/{session_id}/restore", status_code=204)
def restore_copilot_conversation(
    tenant_id: str, session_id: str, session: DatabaseSession
):
    try:
        restore_chat_session(session, tenant_id, session_id)
    except NotFound as error:
        raise api_error(error) from error


def _proposal_payload(
    row: ChangeProposal, decided_by: str | None = None
) -> dict[str, object]:
    return {
        "id": row.id,
        "tool": row.type.removeprefix("tool:"),
        "actor_type": row.actor_type,
        "status": row.status,
        "input": json.loads(row.input),
        "output": json.loads(row.output),
        "created_at": row.created_at.isoformat(),
        "decided_at": row.decided_at.isoformat() if row.decided_at else None,
        "decided_by": decided_by,
    }


@router.get("/change-proposals")
def get_change_proposals(
    tenant_id: str,
    session: DatabaseSession,
    status: Literal["pending", "history"] = "pending",
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    q: str = "",
    tool: str = "",
):
    pending = status == "pending"
    total = change_proposal_count(
        session, tenant_id, pending=pending, query=q, tool=tool
    )
    pager = page_for(total, page, size)
    rows = change_proposals(
        session,
        tenant_id,
        pending=pending,
        query=q,
        tool=tool,
        offset=pager.offset,
        limit=pager.size,
    )
    deciders = decision_maker_names(
        session, tenant_id, [row.decided_by_user_id for row in rows]
    )
    return {
        "items": [
            _proposal_payload(row, deciders.get(row.decided_by_user_id)) for row in rows
        ],
        "page": _page_response(pager),
    }


@router.post("/copilot/sessions/{session_id}/messages")
def post_copilot_message(
    tenant_id: str,
    session_id: str,
    body: CopilotMessageWrite,
    request: Request,
    session: DatabaseSession,
):
    try:
        user: AppUser | None = getattr(request.state, "user", None)
        from reality.tools.analytics import caller

        with caller(optional_request_principal(request)):
            user_message, assistant_message = send_chat_message(
                session,
                tenant_id,
                session_id,
                body.message.strip(),
                context_commitment_id=body.context.id
                if isinstance(body.context, CopilotContext)
                else None,
                context_analytics=body.context.definition.model_dump(mode="json")
                if isinstance(body.context, CopilotAnalyticsContext)
                else None,
                language=user.language if user else "en",
                locale=user.locale if user else "en-GB",
                timezone=user.timezone if user else "UTC",
            )
        return {
            "user": {"id": user_message.id, "content": user_message.content},
            "assistant": {
                "id": assistant_message.id,
                "content": assistant_message.content,
            },
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/change-proposals/{proposal_id}/approve")
def post_copilot_proposal_approval(
    tenant_id: str,
    proposal_id: str,
    body: CopilotProposalDecision,
    request: Request,
    session: DatabaseSession,
):
    try:
        if body.session_id:
            chat_messages(session, tenant_id, body.session_id)
        proposal = approve_and_execute_proposal(
            session,
            tenant_id,
            proposal_id,
            confirming_principal=optional_request_principal(request),
            review_token=body.review_token,
            confirmed=body.confirmed,
        )
        if body.session_id and "_delivery_review" not in json.loads(proposal.input):
            add_chat_assistant_message(
                session,
                tenant_id,
                body.session_id,
                f"Executed {proposal.type.removeprefix('tool:')}. Result: {proposal.output}",
            )
        return {
            "id": proposal.id,
            "status": proposal.status,
            "output": json.loads(proposal.output),
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/change-proposals/{proposal_id}/reject")
def post_copilot_proposal_rejection(
    tenant_id: str,
    proposal_id: str,
    body: CopilotProposalDecision,
    request: Request,
    session: DatabaseSession,
):
    try:
        proposal = reject_proposal(
            session,
            tenant_id,
            proposal_id,
            confirming_principal=optional_request_principal(request),
        )
        if body.session_id:
            add_chat_assistant_message(
                session, tenant_id, body.session_id, "The proposed action was rejected."
            )
        return {"id": proposal.id, "status": proposal.status}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


def explorer_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def explorer_record(record) -> dict:
    values = {
        column.key: explorer_value(getattr(record, column.key))
        for column in sqlalchemy_inspect(type(record)).columns
        if column.key != "tenant_id"
    }
    title = next(
        (
            str(values[key])
            for key in (
                "name",
                "number",
                "sku",
                "external_id",
                "event_type",
                "predicate",
                "type",
                "account",
                "id",
            )
            if values.get(key) not in (None, "")
        ),
        record.id,
    )
    fields = [
        {
            "name": key,
            "label": key.replace("_", " ").title(),
            "value": value,
            "format": "json"
            if key in {"payload", "input", "output", "context"}
            else "text",
            "target": EXPLORER_LINKS.get(key),
        }
        for key, value in values.items()
    ]
    return {"id": record.id, "title": title, "fields": fields}


@router.get("/inspector-records")
def get_inspector_records(
    tenant_id: str,
    session: DatabaseSession,
    kind: str = "all",
    q: str = Query(default="", max_length=500),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=25, le=100),
):
    """Read all supported Inspector families through the shared scoped register."""
    try:
        return inspector_records(
            session, tenant_id, kind=kind, query=q, page=page, size=size
        )
    except InvalidOperation as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except NotFound as error:
        raise api_error(error) from error


@router.get("/explorer")
def get_explorer(
    tenant_id: str,
    session: DatabaseSession,
    q: str = Query(default="", max_length=120),
    kind: str | None = None,
):
    """Return a bounded, tenant-scoped inspector instead of dumping whole tables."""
    try:
        get_tenant(session, tenant_id)
    except NotFound as error:
        raise api_error(error) from error

    model_specs = [
        (
            "Reference",
            "The identities Reality uses across operational records.",
            Party,
            "Parties",
            ("id", "name", "type"),
        ),
        (
            "Reference",
            "The identities Reality uses across operational records.",
            Item,
            "Items",
            ("id", "sku", "name"),
        ),
        (
            "Reference",
            "The identities Reality uses across operational records.",
            Location,
            "Locations",
            ("id", "name", "type"),
        ),
        (
            "Source",
            "Lossless records received from external systems.",
            SourceRecord,
            "Source records",
            ("id", "source_system", "source_type", "external_id"),
        ),
        (
            "Evidence",
            "Business documents interpreted from their original source.",
            Document,
            "Documents",
            ("id", "number", "type", "status"),
        ),
        (
            "Reality",
            "Operational state derived through the shortest true relationships.",
            Commitment,
            "Commitments",
            ("id", "type", "status", "item_id", "document_id"),
        ),
        (
            "Reality",
            "Operational state derived through the shortest true relationships.",
            Reservation,
            "Reservations",
            ("id", "status", "commitment_id", "item_id", "location_id"),
        ),
        (
            "Reality",
            "Operational state derived through the shortest true relationships.",
            Movement,
            "Movements",
            ("id", "type", "item_id", "commitment_id", "source_record_id"),
        ),
        (
            "Reality",
            "Operational state derived through the shortest true relationships.",
            LedgerEntry,
            "Ledger entries",
            ("id", "account", "posting_group_id", "document_id", "party_id"),
        ),
        (
            "Events",
            "Immutable notifications explaining what changed and when.",
            BusinessEvent,
            "Business events",
            ("id", "event_type", "subject_type", "subject_id", "source_record_id"),
        ),
    ]
    if kind:
        extra_specs = [
            (
                "Reality",
                "Source-supported observations.",
                Fact,
                "Facts",
                ("id", "predicate", "subject_type", "subject_id", "value"),
            ),
            (
                "Evidence",
                "Lines from business documents.",
                DocumentLine,
                "Document lines",
                ("id", "document_id", "sku", "description"),
            ),
        ]
        lookup_kind = "ledger_entry" if kind == "payment" else kind
        model_specs = [
            entry
            for entry in [*model_specs, *extra_specs]
            if entry[2].__tablename__ == lookup_kind
        ]
        if not model_specs:
            raise HTTPException(
                status_code=422, detail="Unknown Inspector record type."
            )
    sections: dict[str, dict] = {}
    pattern = f"%{q.strip()}%"
    for section_name, description, model, label, search_fields in model_specs:
        conditions = [model.tenant_id == tenant_id]
        if q.strip():
            conditions.append(
                or_(
                    *(
                        cast(getattr(model, field), String).ilike(pattern)
                        for field in search_fields
                    )
                )
            )
        order_column = next(
            (
                getattr(model, field)
                for field in ("recorded_at", "occurred_at", "created_at", "received_at")
                if hasattr(model, field)
            ),
            model.id,
        )
        records = session.scalars(
            select(model).where(*conditions).order_by(order_column.desc()).limit(10)
        ).all()
        section = sections.setdefault(
            section_name,
            {"name": section_name, "description": description, "collections": []},
        )
        section["collections"].append(
            {
                "name": model.__tablename__,
                "label": label,
                "records": [explorer_record(record) for record in records],
            }
        )
    return {
        "query": q.strip(),
        "limit_per_collection": 10,
        "sections": list(sections.values()),
    }


class FinanceAccountProposal(ApiModel):
    tool: str
    arguments: dict


@router.get("/finance/accounts")
def get_finance_accounts(tenant_id: str, session: DatabaseSession):
    from reality.services.finance.accounts import list_accounts

    return list_accounts(session, tenant_id)


@router.post("/finance/accounts/proposals")
def propose_finance_account(
    tenant_id: str,
    body: FinanceAccountProposal,
    request: Request,
    session: DatabaseSession,
):
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import ACCOUNT_COMMANDS

    require_company_owner(request, session, tenant_id)
    if body.tool not in ACCOUNT_COMMANDS:
        raise HTTPException(status_code=400, detail="Unsupported account command.")
    try:
        proposal = create_change_proposal(
            session, tenant_id, body.tool, body.arguments, actor_type="human"
        )
        return {
            "id": proposal.id,
            "status": proposal.status,
            "preview": json.loads(proposal.output),
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


class ItemImportPreview(ApiModel):
    model_config = ConfigDict(extra="forbid")
    config: dict[str, Any]


class ItemImportPrepare(ItemImportPreview):
    request_id: str = Field(min_length=1, max_length=200)


@router.post("/item-imports/artifacts", status_code=201)
async def post_item_csv_artifact(
    tenant_id: str,
    request: Request,
    session: DatabaseSession,
    filename: str = Query(min_length=1, max_length=255),
):
    from reality.services.item_imports import MAX_BYTES, stage_item_csv

    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="CSV must be at most 2 MiB.")
    try:
        return stage_item_csv(session, tenant_id, bytes(content), filename)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/item-imports/preview")
def post_item_csv_preview(
    tenant_id: str, body: ItemImportPreview, session: DatabaseSession
):
    from reality.services.item_imports import preview_item_import

    try:
        return preview_item_import(session, tenant_id, body.config)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/item-imports/prepare")
def post_item_csv_prepare(
    tenant_id: str, body: ItemImportPrepare, request: Request, session: DatabaseSession
):
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )
    from reality.services.reference_workspace import require_ordinary_workspace

    try:
        require_ordinary_workspace(session, tenant_id)
        principal = optional_request_principal(request)
        proposal = prepare_delivery_action(
            session,
            tenant_id,
            "item_create",
            {"import_file": body.config},
            request_id=body.request_id,
            actor_id=principal.user_id if principal else "local",
        )
        return delivery_proposal_detail(session, tenant_id, proposal.id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/item-imports/artifacts/{artifact_id}/download")
def get_item_csv_original(tenant_id: str, artifact_id: str, session: DatabaseSession):
    from urllib.parse import quote

    from fastapi.responses import StreamingResponse

    from reality.services.artifacts import get_artifact, materialize_artifact
    from reality.services.core import get_tenant

    try:
        get_tenant(session, tenant_id)
        artifact = get_artifact(session, tenant_id, artifact_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error

    def content():
        with materialize_artifact(artifact) as path, path.open("rb") as stream:
            while chunk := stream.read(65536):
                yield chunk

    return StreamingResponse(
        content(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(artifact.filename, safe='')}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/finance/adjustments/context/{invoice_id}")
def get_adjustment_context(tenant_id: str, invoice_id: str, session: DatabaseSession):
    from reality.services.finance.settlement import adjustment_context

    try:
        return adjustment_context(session, tenant_id, invoice_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/adjustments/proposals")
def propose_adjustment(
    tenant_id: str,
    body: FinanceAccountProposal,
    request: Request,
    session: DatabaseSession,
):
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import ADJUSTMENT_COMMAND

    require_company_owner(request, session, tenant_id)
    if body.tool != ADJUSTMENT_COMMAND:
        raise HTTPException(status_code=400, detail="Unsupported adjustment command.")
    try:
        proposal = create_change_proposal(
            session, tenant_id, body.tool, body.arguments, actor_type="human"
        )
        return {
            "id": proposal.id,
            "status": proposal.status,
            "preview": json.loads(proposal.output),
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/settlements/context/{document_id}")
def get_settlement_context(
    tenant_id: str, document_id: str, session: DatabaseSession, query: str = ""
):
    from reality.services.finance.settlement_flows import settlement_context

    try:
        return settlement_context(session, tenant_id, document_id, query)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/settlements/proposals")
def propose_settlement(
    tenant_id: str,
    body: FinanceAccountProposal,
    request: Request,
    session: DatabaseSession,
):
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import SETTLEMENT_COMMAND

    require_company_owner(request, session, tenant_id)
    if body.tool != SETTLEMENT_COMMAND:
        raise HTTPException(status_code=400, detail="Unsupported settlement command.")
    try:
        proposal = create_change_proposal(
            session, tenant_id, body.tool, body.arguments, actor_type="human"
        )
        return {
            "id": proposal.id,
            "status": proposal.status,
            "preview": json.loads(proposal.output),
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/opening/context")
def get_opening_context(tenant_id: str, session: DatabaseSession, query: str = ""):
    from reality.services.finance.opening import opening_context

    try:
        return opening_context(session, tenant_id, query)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/opening/proposals")
def propose_opening(
    tenant_id: str,
    body: FinanceAccountProposal,
    request: Request,
    session: DatabaseSession,
):
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import OPENING_COMMAND

    require_company_owner(request, session, tenant_id)
    if body.tool != OPENING_COMMAND:
        raise HTTPException(status_code=400, detail="Unsupported opening command.")
    try:
        proposal = create_change_proposal(
            session, tenant_id, body.tool, body.arguments, actor_type="human"
        )
        return {
            "id": proposal.id,
            "status": proposal.status,
            "preview": json.loads(proposal.output),
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/references")
def get_finance_references(
    tenant_id: str,
    session: DatabaseSession,
    kind: str | None = None,
    state: str | None = None,
    query: str = "",
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.references import list_references

    try:
        return list_references(
            session,
            tenant_id,
            kind=kind,
            state=state,
            query=query,
            limit=limit,
            offset=offset,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/references/{reference_id}/history")
def get_finance_reference_history(
    tenant_id: str,
    reference_id: str,
    session: DatabaseSession,
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.references import reference_history

    try:
        return reference_history(
            session, tenant_id, reference_id, limit=limit, offset=offset
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/references/proposals")
def propose_finance_reference(
    tenant_id: str,
    body: FinanceAccountProposal,
    request: Request,
    session: DatabaseSession,
):
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import REFERENCE_COMMANDS

    require_company_owner(request, session, tenant_id)
    if body.tool not in REFERENCE_COMMANDS:
        raise HTTPException(status_code=400, detail="Unsupported reference command.")
    try:
        proposal = create_change_proposal(
            session, tenant_id, body.tool, body.arguments, actor_type="human"
        )
        return {
            "id": proposal.id,
            "status": proposal.status,
            "preview": json.loads(proposal.output),
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/components/context/{document_id}")
def get_component_context(
    tenant_id: str,
    document_id: str,
    session: DatabaseSession,
    limit: int = 50,
    offset: int = 0,
    reference_query: str = "",
):
    from reality.services.finance.components import component_context

    try:
        return component_context(
            session,
            tenant_id,
            document_id,
            limit=limit,
            offset=offset,
            reference_query=reference_query,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/components/{component_id}/history")
def get_component_history(
    tenant_id: str,
    component_id: str,
    session: DatabaseSession,
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.components import component_history

    try:
        return component_history(
            session, tenant_id, component_id, limit=limit, offset=offset
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/components/proposals")
def propose_component_assignment(
    tenant_id: str,
    body: FinanceAccountProposal,
    request: Request,
    session: DatabaseSession,
):
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import ASSIGNMENT_COMMAND

    require_company_owner(request, session, tenant_id)
    if body.tool != ASSIGNMENT_COMMAND:
        raise HTTPException(status_code=400, detail="Unsupported assignment command.")
    try:
        proposal = create_change_proposal(
            session, tenant_id, body.tool, body.arguments, actor_type="human"
        )
        return {
            "id": proposal.id,
            "status": proposal.status,
            "preview": json.loads(proposal.output),
        }
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/matrix")
def get_transaction_matrix(tenant_id: str, session: DatabaseSession) -> dict:
    from reality.services.finance.accounts import transaction_matrix

    try:
        return transaction_matrix(session, tenant_id)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/source-mappings")
def get_source_mappings(
    tenant_id: str,
    session: DatabaseSession,
    query: str = "",
    source_query: str = "",
    reference_query: str = "",
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.source_mappings import list_source_mappings

    try:
        return list_source_mappings(
            session,
            tenant_id,
            query=query,
            source_query=source_query,
            reference_query=reference_query,
            limit=limit,
            offset=offset,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/source-mappings/{mapping_id}/history")
def get_source_mapping_history(
    tenant_id: str,
    mapping_id: str,
    session: DatabaseSession,
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.source_mappings import source_mapping_history

    try:
        return source_mapping_history(
            session, tenant_id, mapping_id, limit=limit, offset=offset
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/source-mappings/proposals")
def propose_source_mapping(
    tenant_id: str,
    body: FinanceAccountProposal,
    request: Request,
    session: DatabaseSession,
):
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import SOURCE_MAPPING_COMMAND

    require_company_owner(request, session, tenant_id)
    if body.tool != SOURCE_MAPPING_COMMAND:
        raise HTTPException(
            status_code=400, detail="Unsupported source mapping command."
        )
    try:
        proposal = create_change_proposal(
            session, tenant_id, body.tool, body.arguments, actor_type="human"
        )
        return {"id": proposal.id, "preview": json.loads(proposal.output)}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/targets")
def finance_targets(
    tenant_id: str,
    session: DatabaseSession,
    query: str = "",
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.target_mappings import list_targets

    try:
        return list_targets(session, tenant_id, query=query, limit=limit, offset=offset)
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/target-references")
def finance_target_references(
    tenant_id: str,
    target_id: str,
    session: DatabaseSession,
    kind: str | None = None,
    query: str = "",
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.target_mappings import list_target_references

    try:
        return list_target_references(
            session,
            tenant_id,
            target_id=target_id,
            kind=kind,
            query=query,
            limit=limit,
            offset=offset,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/target-mappings")
def finance_target_mappings(
    tenant_id: str,
    target_id: str,
    session: DatabaseSession,
    query: str = "",
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.target_mappings import list_mappings

    try:
        return list_mappings(
            session,
            tenant_id,
            target_id=target_id,
            query=query,
            limit=limit,
            offset=offset,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/target-mappings/preview")
def finance_target_preview(
    tenant_id: str,
    target_id: str,
    document_id: str,
    session: DatabaseSession,
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.target_mappings import preview_document

    try:
        return preview_document(
            session,
            tenant_id,
            target_id=target_id,
            document_id=document_id,
            limit=limit,
            offset=offset,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/finance/target-mappings/{mapping_id}/history")
def finance_target_history(
    tenant_id: str,
    mapping_id: str,
    session: DatabaseSession,
    limit: int = 50,
    offset: int = 0,
):
    from reality.services.finance.target_mappings import mapping_history

    try:
        return mapping_history(
            session, tenant_id, mapping_id=mapping_id, limit=limit, offset=offset
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.post("/finance/targets/proposals")
def propose_finance_target(
    tenant_id: str,
    body: FinanceAccountProposal,
    request: Request,
    session: DatabaseSession,
):
    from reality.domain.target_mappings import COMMANDS
    from reality.tools.application import create_change_proposal

    require_company_owner(request, session, tenant_id)
    if body.tool not in COMMANDS:
        raise HTTPException(status_code=400, detail="Unsupported target command.")
    try:
        proposal = create_change_proposal(
            session, tenant_id, body.tool, body.arguments, actor_type="human"
        )
        return {"id": proposal.id, "preview": json.loads(proposal.output)}
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


from reality.web.analytics_api import router as analytics_router

router.include_router(analytics_router)
