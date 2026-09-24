"""OAuth protocol and browser-consent adapters for interactive MCP access."""

from __future__ import annotations

import os
import re
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from reality.db.mcp_authorization import MCPAuthorizationInteraction
from reality.services.core import InvalidOperation, NotFound
from reality.services.mcp_authorization import (
    SUPPORTED_SCOPES,
    approve_interaction,
    company_grants,
    create_interaction,
    deny_interaction,
    exchange_code,
    interaction_view,
    personal_grants,
    resolve_client_metadata,
    revoke_company_grant,
    revoke_credential_token,
    revoke_personal_grant,
    rotate_refresh_token,
    token_hash,
)
from reality.web.auth import CurrentUser, DatabaseSession

router = APIRouter(tags=["mcp-authorization"])
_PKCE = re.compile(r"[A-Za-z0-9_-]{43,128}")
_COMPLETION_COOKIE = "reality_oauth_completion"


def _enabled() -> bool:
    return os.environ.get("MCP_INTERACTIVE_AUTH_ENABLED", "false").lower() == "true"


def _issuer() -> str:
    return (os.environ.get("API_URL") or "http://127.0.0.1:8000").rstrip("/")


def _resource() -> str:
    return (os.environ.get("MCP_URL") or "http://localhost:8001/").rstrip("/") + "/"


def _app_url() -> str:
    return (os.environ.get("APP_URL") or "http://localhost:8080").rstrip("/")


def _require_enabled() -> None:
    if not _enabled():
        raise HTTPException(
            status_code=503, detail="Interactive MCP authorization is disabled."
        )


def _oauth_error(error: str, description: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        {"error": error, "error_description": description},
        status_code=status_code,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


def _metadata() -> dict:
    issuer = _issuer()
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/oauth/authorize",
        "token_endpoint": f"{issuer}/oauth/token",
        "revocation_endpoint": f"{issuer}/oauth/revoke",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": sorted(SUPPORTED_SCOPES),
        "authorization_response_iss_parameter_supported": True,
    }


@router.get("/.well-known/oauth-authorization-server")
def oauth_metadata():
    _require_enabled()
    return JSONResponse(_metadata(), headers={"Cache-Control": "public, max-age=300"})


@router.get("/.well-known/openid-configuration")
def oidc_metadata():
    _require_enabled()
    return JSONResponse(_metadata(), headers={"Cache-Control": "public, max-age=300"})


@router.get("/oauth/authorize")
def authorize(
    session: DatabaseSession,
    response_type: str = Query(),
    client_id: str = Query(min_length=1, max_length=2048),
    redirect_uri: str = Query(min_length=1, max_length=2048),
    code_challenge: str = Query(min_length=1, max_length=128),
    code_challenge_method: str = Query(),
    resource: str = Query(min_length=1, max_length=2048),
    scope: str = Query(min_length=1, max_length=200),
    state: str = Query(default="", max_length=2048),
):
    _require_enabled()
    try:
        if response_type != "code":
            raise InvalidOperation(
                "Only the authorization code response type is supported."
            )
        if code_challenge_method != "S256" or not _PKCE.fullmatch(code_challenge):
            raise InvalidOperation("PKCE S256 is required.")
        if resource != _resource():
            raise InvalidOperation("The requested resource is not this MCP server.")
        client = resolve_client_metadata(client_id)
        if redirect_uri not in client.redirect_uris:
            raise InvalidOperation(
                "The redirect URI is not registered for this client."
            )
        interaction = create_interaction(
            session,
            client_id=client.client_id,
            client_metadata={
                "client_name": client.client_name,
                "client_uri": client.client_uri,
                "redirect_uris": list(client.redirect_uris),
            },
            redirect_uri=redirect_uri,
            resource=resource,
            requested_scopes=scope.split(),
            code_challenge=code_challenge,
            state=state,
        )
    except InvalidOperation as error:
        return _oauth_error("invalid_request", str(error))
    return RedirectResponse(
        f"{_app_url()}/oauth/authorize?{urlencode({'interaction': interaction.id})}",
        status_code=303,
        headers={"Cache-Control": "no-store"},
    )


@router.post("/oauth/token")
def token(
    session: DatabaseSession,
    grant_type: str = Form(),
    client_id: str = Form(),
    resource: str = Form(),
    code: str | None = Form(default=None),
    redirect_uri: str | None = Form(default=None),
    code_verifier: str | None = Form(default=None),
    refresh_token: str | None = Form(default=None),
):
    _require_enabled()
    if resource != _resource():
        return _oauth_error("invalid_target", "The requested resource is invalid.")
    try:
        if grant_type == "authorization_code":
            if not code or not redirect_uri or not code_verifier:
                raise InvalidOperation("The authorization code exchange is incomplete.")
            issued = exchange_code(
                session,
                code=code,
                client_id=client_id,
                redirect_uri=redirect_uri,
                resource=resource,
                code_verifier=code_verifier,
            )
        elif grant_type == "refresh_token":
            if not refresh_token:
                raise InvalidOperation("The refresh exchange is incomplete.")
            issued = rotate_refresh_token(
                session, refresh_token=refresh_token, client_id=client_id
            )
        else:
            return _oauth_error("unsupported_grant_type", "Unsupported grant type.")
    except InvalidOperation:
        return _oauth_error("invalid_grant", "The credential is invalid or expired.")
    return JSONResponse(
        {
            "access_token": issued.access_token,
            "token_type": "Bearer",
            "expires_in": issued.expires_in,
            "refresh_token": issued.refresh_token,
            "scope": " ".join(issued.scopes),
        },
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@router.post("/oauth/revoke")
def revoke(session: DatabaseSession, token: str = Form()):
    _require_enabled()
    revoke_credential_token(session, token)
    return JSONResponse({}, headers={"Cache-Control": "no-store"})


class Approval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: str = Field(min_length=1)
    allowed_tools: list[str] = Field(min_length=1, max_length=200)
    confirmed: StrictBool = False


class Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: StrictBool = False


def _interaction_or_404(
    session: DatabaseSession, interaction_id: str
) -> MCPAuthorizationInteraction:
    interaction = session.get(MCPAuthorizationInteraction, interaction_id)
    if interaction is None:
        raise HTTPException(
            status_code=404, detail="Authorization interaction not found."
        )
    return interaction


@router.get("/api/oauth/interactions/{interaction_id}")
def read_interaction(interaction_id: str, user: CurrentUser, session: DatabaseSession):
    _require_enabled()
    try:
        return interaction_view(session, interaction_id, user.id)
    except NotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def _approval_redirect(
    interaction: MCPAuthorizationInteraction, code: str
) -> RedirectResponse:
    target = f"{interaction.redirect_uri}?{urlencode({'code': code, 'state': interaction.client_state, 'iss': _issuer()})}"
    return RedirectResponse(
        target, status_code=303, headers={"Cache-Control": "no-store"}
    )


def _browser_completion(
    request: Request,
    interaction: MCPAuthorizationInteraction,
    code: str | None = None,
):
    if "application/json" not in request.headers.get("accept", ""):
        if code is not None:
            return _approval_redirect(interaction, code)
        target = f"{interaction.redirect_uri}?{urlencode({'error': 'access_denied', 'state': interaction.client_state, 'iss': _issuer()})}"
        return RedirectResponse(
            target, status_code=303, headers={"Cache-Control": "no-store"}
        )
    path = f"/oauth/complete/{interaction.id}"
    response = JSONResponse(
        {"completion_path": path}, headers={"Cache-Control": "no-store"}
    )
    if code is not None:
        response.set_cookie(
            _COMPLETION_COOKIE,
            code,
            max_age=120,
            httponly=True,
            secure=_issuer().startswith("https://"),
            samesite="lax",
            path=path,
        )
    return response


@router.get("/oauth/complete/{interaction_id}")
def complete_browser_authorization(
    interaction_id: str,
    session: DatabaseSession,
    completion_code: str | None = Cookie(default=None, alias=_COMPLETION_COOKIE),
):
    _require_enabled()
    interaction = _interaction_or_404(session, interaction_id)
    if interaction.status == "approved":
        if (
            not completion_code
            or token_hash(completion_code) != interaction.authorization_code_hash
        ):
            raise HTTPException(
                status_code=404, detail="Authorization completion unavailable."
            )
        response = _approval_redirect(interaction, completion_code)
    elif interaction.status == "denied":
        target = f"{interaction.redirect_uri}?{urlencode({'error': 'access_denied', 'state': interaction.client_state, 'iss': _issuer()})}"
        response = RedirectResponse(
            target, status_code=303, headers={"Cache-Control": "no-store"}
        )
    else:
        raise HTTPException(
            status_code=409, detail="Authorization completion unavailable."
        )
    response.delete_cookie(_COMPLETION_COOKIE, path=f"/oauth/complete/{interaction.id}")
    return response


@router.post("/api/oauth/interactions/{interaction_id}/approve")
def approve(
    interaction_id: str,
    body: Approval,
    request: Request,
    user: CurrentUser,
    session: DatabaseSession,
):
    _require_enabled()
    if not body.confirmed:
        raise HTTPException(
            status_code=400, detail="Explicit confirmation is required."
        )
    interaction = _interaction_or_404(session, interaction_id)
    try:
        client = resolve_client_metadata(interaction.client_id)
        if interaction.redirect_uri not in client.redirect_uris:
            raise InvalidOperation("The client redirect registration has changed.")
        _, code = approve_interaction(
            session,
            interaction_id,
            user_id=user.id,
            tenant_id=body.company_id,
            allowed_tools=body.allowed_tools,
        )
    except NotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidOperation as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return _browser_completion(request, interaction, code)


@router.post("/api/oauth/interactions/{interaction_id}/deny")
def deny(
    interaction_id: str,
    body: Confirmation,
    request: Request,
    user: CurrentUser,
    session: DatabaseSession,
):
    _require_enabled()
    if not body.confirmed:
        raise HTTPException(
            status_code=400, detail="Explicit confirmation is required."
        )
    interaction = _interaction_or_404(session, interaction_id)
    try:
        deny_interaction(session, interaction_id, user_id=user.id)
    except InvalidOperation as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return _browser_completion(request, interaction)


@router.get("/api/auth/mcp-grants")
def read_personal_grants(user: CurrentUser, session: DatabaseSession):
    _require_enabled()
    return {"grants": personal_grants(session, user.id)}


@router.post("/api/auth/mcp-grants/{grant_id}/revoke", status_code=204)
def revoke_personal(
    grant_id: str, body: Confirmation, user: CurrentUser, session: DatabaseSession
):
    _require_enabled()
    if not body.confirmed:
        raise HTTPException(
            status_code=400, detail="Explicit confirmation is required."
        )
    try:
        revoke_personal_grant(session, grant_id, user.id)
    except NotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/api/tenants/{tenant_id}/settings/mcp/grants")
def read_company_grants(tenant_id: str, user: CurrentUser, session: DatabaseSession):
    _require_enabled()
    try:
        return {"grants": company_grants(session, tenant_id, user.id)}
    except NotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidOperation as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.post(
    "/api/tenants/{tenant_id}/settings/mcp/grants/{grant_id}/revoke",
    status_code=204,
)
def revoke_company(
    tenant_id: str,
    grant_id: str,
    body: Confirmation,
    user: CurrentUser,
    session: DatabaseSession,
):
    _require_enabled()
    if not body.confirmed:
        raise HTTPException(
            status_code=400, detail="Explicit confirmation is required."
        )
    try:
        revoke_company_grant(session, tenant_id, grant_id, user.id)
    except NotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidOperation as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
