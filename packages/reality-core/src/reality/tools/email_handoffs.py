"""Permission-scoped email evidence/execution adapters, never proposal approval."""

import os
from typing import Any

from sqlalchemy.orm import Session

from reality.mcp.principal import current_mcp_principal
from reality.services import emails
from reality.services.core import InvalidOperation


def email_mutation_handler(operation: str):
    function = {
        "stage_email_chunk": emails.stage_email_chunk,
        "complete_email_file": emails.complete_email_file,
        "capture_email": emails.capture_email,
        "claim_dispatch": emails.claim_dispatch,
        "report_dispatch": emails.report_dispatch,
    }[operation]

    def handler(session: Session, tenant_id: str, arguments: dict[str, Any]):
        principal = current_mcp_principal()
        executor = "mcp:" + principal.credential_id if principal else "local:trusted"
        if principal is None and os.environ.get("REALITY_AUTH_MODE") != "disabled":
            raise InvalidOperation(code="email_executor_mismatch")
        if operation in {"claim_dispatch", "report_dispatch"}:
            return function(session, tenant_id, arguments, executor=executor)
        return function(session, tenant_id, arguments)

    # Keep executable catalog/source explanations attached to the actual service,
    # like other transport wrappers; this attribute never grants permission.
    handler.__wrapped__ = function
    return handler
