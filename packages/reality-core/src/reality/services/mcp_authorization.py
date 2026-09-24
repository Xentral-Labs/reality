"""Transaction-bound interactive MCP authorization authority."""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import os
import secrets
import socket
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlparse

import httpx
from sqlalchemy import delete, or_, select

from reality.db.core import (
    AppUser,
    SecurityAuditEvent,
    Tenant,
    TenantMembership,
    now,
    uid,
)
from reality.db.mcp_authorization import (
    MCPAuthorizationInteraction,
    MCPClientGrant,
    MCPUserCredential,
)
from reality.mcp.catalog import MCP_TOOL_REGISTRY, validate_tool_permissions
from reality.mcp.principal import MCPPrincipal
from reality.services.account_policy import account_eligible
from reality.services.core import InvalidOperation, NotFound
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    require_business_operation,
)

SUPPORTED_SCOPES = frozenset({"reality:read", "reality:propose", "reality:confirm"})
ACCESS_SCOPE = {
    "read": "reality:read",
    "propose": "reality:propose",
    "confirm": "reality:confirm",
}
ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=30)
INTERACTION_TTL = timedelta(minutes=10)
MAX_CLIENT_METADATA_BYTES = 64 * 1024


@dataclass(frozen=True)
class OAuthClientMetadata:
    client_id: str
    client_name: str
    redirect_uris: tuple[str, ...]
    client_uri: str | None = None


def _validated_redirects(values: object) -> tuple[str, ...]:
    if not isinstance(values, list) or not 1 <= len(values) <= 20:
        raise InvalidOperation("OAuth client redirect metadata is invalid.")
    redirects = tuple(str(value) for value in values)
    for value in redirects:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username:
            raise InvalidOperation("OAuth client redirect metadata is invalid.")
    return redirects


def _client_from_document(client_id: str, document: object) -> OAuthClientMetadata:
    if not isinstance(document, dict) or document.get("client_id") not in {
        None,
        client_id,
    }:
        raise InvalidOperation("OAuth client metadata identity does not match.")
    name = str(document.get("client_name") or "").strip()
    if not 1 <= len(name) <= 200:
        raise InvalidOperation("OAuth client display name is invalid.")
    uri = document.get("client_uri")
    if uri is not None:
        parsed_uri = urlparse(str(uri))
        if parsed_uri.scheme != "https" or not parsed_uri.netloc:
            raise InvalidOperation("OAuth client display URI is invalid.")
        uri = str(uri)
    return OAuthClientMetadata(
        client_id, name, _validated_redirects(document.get("redirect_uris")), uri
    )


def _public_addresses(hostname: str) -> frozenset[str]:
    try:
        addresses = frozenset(
            result[4][0]
            for result in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        )
    except OSError as error:
        raise InvalidOperation("OAuth client metadata host is unavailable.") from error
    if not addresses:
        raise InvalidOperation("OAuth client metadata host is unavailable.")
    for value in addresses:
        address = ipaddress.ip_address(value)
        if not address.is_global:
            raise InvalidOperation("OAuth client metadata host is not public.")
    return addresses


def resolve_client_metadata(
    client_id: str,
    *,
    environ: Mapping[str, str] = os.environ,
    fetch: Callable[[str], bytes] | None = None,
) -> OAuthClientMetadata:
    """Resolve an exact pre-registration or a bounded, public HTTPS CIMD."""

    try:
        registered = json.loads(environ.get("MCP_OAUTH_CLIENTS", "{}"))
    except json.JSONDecodeError as error:
        raise InvalidOperation("OAuth client registration is invalid.") from error
    if isinstance(registered, dict) and client_id in registered:
        return _client_from_document(client_id, registered[client_id])
    parsed = urlparse(client_id)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.path in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise InvalidOperation("OAuth client is not registered or a valid CIMD URL.")
    before = _public_addresses(parsed.hostname)
    try:
        if fetch is None:
            response = httpx.get(client_id, timeout=3.0, follow_redirects=False)
            if response.is_redirect:
                raise InvalidOperation(
                    "OAuth client metadata redirects are not allowed."
                )
            response.raise_for_status()
            raw = response.content
        else:
            raw = fetch(client_id)
        if not isinstance(raw, bytes) or len(raw) > MAX_CLIENT_METADATA_BYTES:
            raise InvalidOperation("OAuth client metadata exceeds the size limit.")
        document = json.loads(raw)
    except (httpx.HTTPError, json.JSONDecodeError) as error:
        raise InvalidOperation("OAuth client metadata is unavailable.") from error
    if _public_addresses(parsed.hostname) != before:
        raise InvalidOperation("OAuth client metadata address changed during fetch.")
    if not isinstance(document, dict) or document.get("client_id") != client_id:
        raise InvalidOperation("OAuth client metadata identity does not match.")
    return _client_from_document(client_id, document)


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _audit(
    session,
    event_type: str,
    *,
    user_id: str | None = None,
    tenant_id: str | None = None,
    subject_id: str | None = None,
    outcome: str = "success",
) -> None:
    session.add(
        SecurityAuditEvent(
            id=uid("audit"),
            user_id=user_id,
            actor_user_id=user_id,
            tenant_id=tenant_id,
            subject_type="mcp_client_grant",
            subject_id=subject_id,
            outcome=outcome,
            event_type=event_type,
            detail="{}",
        )
    )


def _sweep(session) -> None:
    interaction_ids = list(
        session.scalars(
            select(MCPAuthorizationInteraction.id)
            .where(
                MCPAuthorizationInteraction.status.in_(
                    ("denied", "consumed", "expired")
                ),
                MCPAuthorizationInteraction.created_at < now() - timedelta(days=7),
            )
            .order_by(MCPAuthorizationInteraction.created_at)
            .limit(500)
        )
    )
    if interaction_ids:
        session.execute(
            delete(MCPAuthorizationInteraction).where(
                MCPAuthorizationInteraction.id.in_(interaction_ids)
            )
        )
    credential_keys = list(
        session.execute(
            select(MCPUserCredential.tenant_id, MCPUserCredential.id)
            .where(
                or_(
                    MCPUserCredential.revoked_at.is_not(None),
                    MCPUserCredential.access_expires_at < now() - timedelta(days=90),
                )
            )
            .order_by(MCPUserCredential.created_at)
            .limit(500)
        )
    )
    for tenant_id, credential_id in credential_keys:
        session.execute(
            delete(MCPUserCredential).where(
                MCPUserCredential.tenant_id == tenant_id,
                MCPUserCredential.id == credential_id,
            )
        )


def create_interaction(
    session,
    *,
    client_id: str,
    client_metadata: dict,
    redirect_uri: str,
    resource: str,
    requested_scopes: list[str],
    code_challenge: str,
    state: str = "",
) -> MCPAuthorizationInteraction:
    scopes = list(dict.fromkeys(requested_scopes))
    if not scopes or not set(scopes) <= SUPPORTED_SCOPES:
        raise InvalidOperation("Unsupported OAuth scope request.")
    if not code_challenge or len(code_challenge) > 128:
        raise InvalidOperation("A bounded PKCE S256 challenge is required.")
    _sweep(session)
    row = MCPAuthorizationInteraction(
        id="oai_" + secrets.token_urlsafe(24),
        client_id=client_id,
        client_metadata=client_metadata,
        redirect_uri=redirect_uri,
        resource=resource,
        requested_scopes=scopes,
        code_challenge=code_challenge,
        code_challenge_method="S256",
        client_state=state,
        status="pending",
        expires_at=now() + INTERACTION_TTL,
    )
    session.add(row)
    session.commit()
    return row


def eligible_tools(interaction: MCPAuthorizationInteraction) -> tuple[str, ...]:
    requested = set(interaction.requested_scopes)
    return tuple(
        sorted(
            name
            for name, definition in MCP_TOOL_REGISTRY.items()
            if ACCESS_SCOPE[definition.access] in requested
        )
    )


def interaction_view(session, interaction_id: str, user_id: str) -> dict:
    interaction = session.scalar(
        select(MCPAuthorizationInteraction)
        .where(MCPAuthorizationInteraction.id == interaction_id)
        .with_for_update()
    )
    if interaction is None:
        raise NotFound("Authorization interaction not found.")
    if interaction.user_id is None:
        interaction.user_id = user_id
        session.flush()
    elif interaction.user_id != user_id:
        raise NotFound("Authorization interaction not found.")
    if interaction.expires_at <= now() and interaction.status in {
        "pending",
        "approved",
    }:
        interaction.status = "expired"
        session.commit()
    company_rows = session.execute(
        select(Tenant, TenantMembership.role)
        .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
        .where(
            TenantMembership.user_id == user_id,
            TenantMembership.status == "active",
            Tenant.archived_at.is_(None),
        )
        .order_by(Tenant.name, Tenant.id)
    )
    companies = []
    for tenant, role in company_rows:
        try:
            require_business_operation(session, tenant.id, "mcp_token_use")
        except (NotFound, PlaygroundOperationDenied):
            continue
        companies.append(
            {"id": tenant.id, "name": tenant.name, "role": role, "ready": True}
        )
    tools = [
        {
            "name": name,
            "label": MCP_TOOL_REGISTRY[name].label,
            "access": MCP_TOOL_REGISTRY[name].access,
        }
        for name in eligible_tools(interaction)
    ]
    user = session.get(AppUser, user_id)
    return {
        "id": interaction.id,
        "client": {
            "id": interaction.client_id,
            "name": interaction.client_metadata.get("client_name", "MCP client"),
            "uri": interaction.client_metadata.get("client_uri"),
        },
        "requested_scopes": interaction.requested_scopes,
        "eligible_tools": tools,
        "selected_tools": [tool["name"] for tool in tools],
        "companies": companies,
        "company_setup": {
            "eligible": bool(user and account_eligible(session, user)),
            "external_mcp_requires_business_company": False,
        },
        "expires_at": interaction.expires_at.isoformat(),
        "status": interaction.status,
    }


def _eligible_company(session, user_id: str, tenant_id: str) -> tuple[AppUser, Tenant]:
    row = session.execute(
        select(AppUser, Tenant)
        .join(TenantMembership, TenantMembership.user_id == AppUser.id)
        .join(Tenant, Tenant.id == TenantMembership.tenant_id)
        .where(
            AppUser.id == user_id,
            Tenant.id == tenant_id,
            TenantMembership.status == "active",
        )
    ).one_or_none()
    if row is None:
        raise NotFound("Eligible company not found.")
    user, tenant = row
    if not account_eligible(session, user) or tenant.archived_at is not None:
        raise NotFound("Eligible company not found.")
    try:
        require_business_operation(session, tenant.id, "mcp_token_use")
    except PlaygroundOperationDenied as error:
        raise NotFound("Eligible company not found.") from error
    return user, tenant


def approve_interaction(
    session,
    interaction_id: str,
    *,
    user_id: str,
    tenant_id: str,
    allowed_tools: list[str],
) -> tuple[MCPClientGrant, str]:
    interaction = session.scalar(
        select(MCPAuthorizationInteraction)
        .where(MCPAuthorizationInteraction.id == interaction_id)
        .with_for_update()
    )
    if (
        interaction is None
        or interaction.status != "pending"
        or interaction.expires_at <= now()
    ):
        raise InvalidOperation("Authorization interaction is unavailable.")
    if interaction.user_id not in {None, user_id}:
        raise NotFound("Authorization interaction not found.")
    _eligible_company(session, user_id, tenant_id)
    tools = validate_tool_permissions(allowed_tools)
    if "*" in tools or not set(tools) <= set(eligible_tools(interaction)):
        raise InvalidOperation("Selected tools exceed the requested scopes.")
    session.execute(
        select(MCPClientGrant)
        .where(
            MCPClientGrant.user_id == user_id,
            MCPClientGrant.tenant_id == tenant_id,
            MCPClientGrant.client_id == interaction.client_id,
            MCPClientGrant.revoked_at.is_(None),
        )
        .with_for_update()
    )
    for old in session.scalars(
        select(MCPClientGrant).where(
            MCPClientGrant.user_id == user_id,
            MCPClientGrant.tenant_id == tenant_id,
            MCPClientGrant.client_id == interaction.client_id,
            MCPClientGrant.revoked_at.is_(None),
        )
    ):
        old.revoked_at = now()
        old.revoked_by_user_id = user_id
        old.revoke_reason = "reconsent"
        for credential in session.scalars(
            select(MCPUserCredential).where(
                MCPUserCredential.tenant_id == old.tenant_id,
                MCPUserCredential.grant_id == old.id,
                MCPUserCredential.revoked_at.is_(None),
            )
        ):
            credential.revoked_at = now()
    scopes = sorted({ACCESS_SCOPE[MCP_TOOL_REGISTRY[name].access] for name in tools})
    grant = MCPClientGrant(
        id=uid("mcpg"),
        tenant_id=tenant_id,
        user_id=user_id,
        client_id=interaction.client_id,
        client_name=str(interaction.client_metadata.get("client_name") or "MCP client")[
            :200
        ],
        client_uri=interaction.client_metadata.get("client_uri"),
        allowed_tools=tools,
        scopes=scopes,
    )
    clear_code = "ros_code_" + secrets.token_urlsafe(32)
    session.add(grant)
    session.flush()
    interaction.user_id = user_id
    interaction.tenant_id = tenant_id
    interaction.grant_id = grant.id
    interaction.authorization_code_hash = token_hash(clear_code)
    interaction.status = "approved"
    interaction.decided_at = now()
    _audit(
        session,
        "mcp.authorization.approved",
        user_id=user_id,
        tenant_id=tenant_id,
        subject_id=grant.id,
    )
    session.commit()
    return grant, clear_code


def deny_interaction(session, interaction_id: str, *, user_id: str) -> None:
    interaction = session.scalar(
        select(MCPAuthorizationInteraction)
        .where(MCPAuthorizationInteraction.id == interaction_id)
        .with_for_update()
    )
    if interaction is None or interaction.status != "pending":
        raise InvalidOperation("Authorization interaction is unavailable.")
    if interaction.user_id not in {None, user_id}:
        raise NotFound("Authorization interaction not found.")
    interaction.user_id = user_id
    interaction.status = "denied"
    interaction.decided_at = now()
    _audit(session, "mcp.authorization.denied", user_id=user_id, outcome="denied")
    session.commit()


@dataclass(frozen=True)
class IssuedCredential:
    access_token: str
    refresh_token: str
    expires_in: int = 900
    scopes: tuple[str, ...] = ()


def _pkce_challenge(verifier: str) -> str:
    return (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )


def exchange_code(
    session,
    *,
    code: str,
    client_id: str,
    redirect_uri: str,
    resource: str,
    code_verifier: str,
) -> IssuedCredential:
    interaction = session.scalar(
        select(MCPAuthorizationInteraction)
        .where(MCPAuthorizationInteraction.authorization_code_hash == token_hash(code))
        .with_for_update()
    )
    if (
        interaction is None
        or interaction.status != "approved"
        or interaction.expires_at <= now()
        or interaction.client_id != client_id
        or interaction.redirect_uri != redirect_uri
        or interaction.resource != resource
        or _pkce_challenge(code_verifier) != interaction.code_challenge
    ):
        raise InvalidOperation("Invalid or expired authorization code.")
    access = "ros_oauth_" + secrets.token_urlsafe(32)
    refresh = "ros_refresh_" + secrets.token_urlsafe(32)
    credential = MCPUserCredential(
        id=uid("mcpc"),
        tenant_id=interaction.tenant_id,
        grant_id=interaction.grant_id,
        access_token_hash=token_hash(access),
        access_token_prefix=access[:20],
        access_expires_at=now() + ACCESS_TTL,
        refresh_token_hash=token_hash(refresh),
        refresh_expires_at=now() + REFRESH_TTL,
    )
    session.add(credential)
    interaction.status = "consumed"
    interaction.consumed_at = now()
    _audit(
        session,
        "mcp.credential.issued",
        user_id=interaction.user_id,
        tenant_id=interaction.tenant_id,
        subject_id=interaction.grant_id,
    )
    session.commit()
    grant = session.get(MCPClientGrant, (interaction.tenant_id, interaction.grant_id))
    return IssuedCredential(
        access, refresh, scopes=tuple(grant.scopes if grant else ())
    )


def rotate_refresh_token(
    session, *, refresh_token: str, client_id: str
) -> IssuedCredential:
    """Rotate one refresh credential or revoke its grant family on reuse."""

    row = session.execute(
        select(MCPUserCredential, MCPClientGrant)
        .join(
            MCPClientGrant,
            (MCPClientGrant.tenant_id == MCPUserCredential.tenant_id)
            & (MCPClientGrant.id == MCPUserCredential.grant_id),
        )
        .where(MCPUserCredential.refresh_token_hash == token_hash(refresh_token))
        .with_for_update()
    ).one_or_none()
    if row is None:
        raise InvalidOperation("Invalid refresh credential.")
    current, grant = row
    if current.rotated_at is not None or current.replaced_by_id is not None:
        for credential in session.scalars(
            select(MCPUserCredential).where(
                MCPUserCredential.tenant_id == current.tenant_id,
                MCPUserCredential.grant_id == current.grant_id,
                MCPUserCredential.revoked_at.is_(None),
            )
        ):
            credential.revoked_at = now()
        grant.revoked_at = now()
        grant.revoke_reason = "refresh_reuse"
        _audit(
            session,
            "mcp.credential.refresh_reuse",
            user_id=grant.user_id,
            tenant_id=grant.tenant_id,
            subject_id=grant.id,
            outcome="denied",
        )
        session.commit()
        raise InvalidOperation("Invalid refresh credential.")
    if (
        current.revoked_at is not None
        or current.refresh_expires_at is None
        or current.refresh_expires_at <= now()
        or grant.revoked_at is not None
        or grant.client_id != client_id
    ):
        raise InvalidOperation("Invalid refresh credential.")
    access = "ros_oauth_" + secrets.token_urlsafe(32)
    refresh = "ros_refresh_" + secrets.token_urlsafe(32)
    replacement = MCPUserCredential(
        id=uid("mcpc"),
        tenant_id=current.tenant_id,
        grant_id=current.grant_id,
        access_token_hash=token_hash(access),
        access_token_prefix=access[:20],
        access_expires_at=now() + ACCESS_TTL,
        refresh_token_hash=token_hash(refresh),
        refresh_expires_at=min(current.refresh_expires_at, now() + REFRESH_TTL),
        generation=current.generation + 1,
    )
    session.add(replacement)
    session.flush()
    current.rotated_at = now()
    current.replaced_by_id = replacement.id
    session.commit()
    return IssuedCredential(access, refresh, scopes=tuple(grant.scopes))


def revoke_credential_token(session, token: str) -> None:
    """Apply RFC 7009's non-disclosing, idempotent credential revocation."""

    digest = token_hash(token)
    credential = session.scalar(
        select(MCPUserCredential).where(
            or_(
                MCPUserCredential.access_token_hash == digest,
                MCPUserCredential.refresh_token_hash == digest,
            )
        )
    )
    if credential is not None and credential.revoked_at is None:
        credential.revoked_at = now()
    session.commit()


def resolve_interactive_principal(session, token: str) -> MCPPrincipal | None:
    row = session.execute(
        select(MCPUserCredential, MCPClientGrant)
        .join(
            MCPClientGrant,
            (MCPClientGrant.tenant_id == MCPUserCredential.tenant_id)
            & (MCPClientGrant.id == MCPUserCredential.grant_id),
        )
        .where(MCPUserCredential.access_token_hash == token_hash(token))
    ).one_or_none()
    if row is None:
        return None
    credential, grant = row
    if (
        credential.revoked_at is not None
        or credential.access_expires_at <= now()
        or grant.revoked_at is not None
    ):
        return None
    try:
        _eligible_company(session, grant.user_id, grant.tenant_id)
    except NotFound:
        return None
    tools = frozenset(
        name
        for name in grant.allowed_tools
        if name in MCP_TOOL_REGISTRY
        and ACCESS_SCOPE[MCP_TOOL_REGISTRY[name].access] in grant.scopes
    )
    if not tools:
        return None
    credential.last_used_at = now()
    grant.last_used_at = now()
    session.commit()
    return MCPPrincipal(
        "interactive",
        credential.id,
        grant.id,
        grant.user_id,
        grant.tenant_id,
        grant.client_id,
        frozenset(grant.scopes),
        tools,
    )


def revoke_grant(
    session, *, tenant_id: str, grant_id: str, actor_user_id: str, reason: str = "user"
) -> None:
    grant = session.scalar(
        select(MCPClientGrant)
        .where(MCPClientGrant.tenant_id == tenant_id, MCPClientGrant.id == grant_id)
        .with_for_update()
    )
    if grant is None:
        raise NotFound("Connected client not found.")
    if grant.revoked_at is None:
        revoked_at = now()
        grant.revoked_at = revoked_at
        grant.revoked_by_user_id = actor_user_id
        grant.revoke_reason = reason
        for credential in session.scalars(
            select(MCPUserCredential).where(
                MCPUserCredential.tenant_id == tenant_id,
                MCPUserCredential.grant_id == grant_id,
                MCPUserCredential.revoked_at.is_(None),
            )
        ):
            credential.revoked_at = revoked_at
        _audit(
            session,
            "mcp.grant.revoked",
            user_id=actor_user_id,
            tenant_id=tenant_id,
            subject_id=grant_id,
        )
    session.commit()


def _grant_view(session, grant: MCPClientGrant, *, include_user: bool) -> dict:
    tenant = session.get(Tenant, grant.tenant_id)
    user = session.get(AppUser, grant.user_id)
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == grant.tenant_id,
            TenantMembership.user_id == grant.user_id,
            TenantMembership.status == "active",
        )
    )
    if grant.revoked_at is not None:
        effective_state, reason = "revoked", grant.revoke_reason or "revoked"
    elif tenant is None or tenant.archived_at is not None:
        effective_state, reason = "inactive", "company_unavailable"
    elif user is None or not account_eligible(session, user):
        effective_state, reason = "inactive", "account_ineligible"
    elif membership is None:
        effective_state, reason = "inactive", "membership_inactive"
    else:
        try:
            require_business_operation(session, grant.tenant_id, "mcp_token_use")
        except (NotFound, PlaygroundOperationDenied):
            effective_state, reason = "inactive", "company_not_ready"
        else:
            effective_state, reason = "active", None
    tools = [
        {
            "name": name,
            "label": MCP_TOOL_REGISTRY[name].label,
            "access": MCP_TOOL_REGISTRY[name].access,
        }
        for name in grant.allowed_tools
        if name in MCP_TOOL_REGISTRY
    ]
    result = {
        "id": grant.id,
        "client": {
            "id": grant.client_id,
            "name": grant.client_name,
            "uri": grant.client_uri,
        },
        "company": {
            "id": grant.tenant_id,
            "name": tenant.name if tenant else "Unavailable company",
        },
        "tools": tools,
        "scopes": grant.scopes,
        "created_at": grant.created_at.isoformat(),
        "last_used_at": grant.last_used_at.isoformat() if grant.last_used_at else None,
        "revoked_at": grant.revoked_at.isoformat() if grant.revoked_at else None,
        "effective_state": effective_state,
        "effective_reason": reason,
    }
    if include_user:
        result["authorized_by"] = {
            "id": grant.user_id,
            "display_name": user.display_name if user else "Unavailable user",
            "email": user.email if user else None,
        }
    return result


def personal_grants(session, user_id: str) -> list[dict]:
    grants = session.scalars(
        select(MCPClientGrant)
        .where(MCPClientGrant.user_id == user_id)
        .order_by(MCPClientGrant.created_at.desc(), MCPClientGrant.id)
    )
    return [_grant_view(session, grant, include_user=False) for grant in grants]


def company_grants(session, tenant_id: str, actor_user_id: str) -> list[dict]:
    from reality.services.memberships import Principal, require_owner

    require_owner(session, tenant_id, Principal(actor_user_id))
    grants = session.scalars(
        select(MCPClientGrant)
        .where(MCPClientGrant.tenant_id == tenant_id)
        .order_by(MCPClientGrant.created_at.desc(), MCPClientGrant.id)
    )
    return [_grant_view(session, grant, include_user=True) for grant in grants]


def revoke_personal_grant(session, grant_id: str, user_id: str) -> None:
    grant = session.scalar(
        select(MCPClientGrant).where(
            MCPClientGrant.id == grant_id, MCPClientGrant.user_id == user_id
        )
    )
    if grant is None:
        raise NotFound("Connected client not found.")
    revoke_grant(
        session,
        tenant_id=grant.tenant_id,
        grant_id=grant.id,
        actor_user_id=user_id,
    )


def revoke_company_grant(
    session, tenant_id: str, grant_id: str, actor_user_id: str
) -> None:
    from reality.services.memberships import Principal, require_owner

    require_owner(session, tenant_id, Principal(actor_user_id))
    revoke_grant(
        session,
        tenant_id=tenant_id,
        grant_id=grant_id,
        actor_user_id=actor_user_id,
        reason="company_owner",
    )
