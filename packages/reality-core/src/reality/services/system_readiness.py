"""Volatile infrastructure readiness, never business facts or job-success claims."""

import json
import math
import os
from datetime import UTC, datetime
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener

from sqlalchemy.orm import Session

from reality.services.core import get_tenant


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


_open = build_opener(ProxyHandler({}), _NoRedirect()).open


def probe(url: str, role: str) -> str:
    if not url:
        return "unknown"
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path != "/healthz"
        ):
            return "unavailable"
        with _open(url, timeout=0.75) as response:
            raw = response.read(4097)
        if len(raw) > 4096:
            return "unavailable"
        data = json.loads(raw)
        if not isinstance(data, dict):
            return "unavailable"
        age = data.get("last_sweep_age_seconds")
        if (
            data.get("role") == role
            and data.get("status") == "ready"
            and type(age) in (int, float)
            and math.isfinite(age)
            and 0 <= age <= 90
        ):
            return "ready"
    except (URLError, OSError, ValueError, TypeError):
        pass
    return "unavailable"


def readiness(session: Session, tenant_id: str) -> dict:
    get_tenant(session, tenant_id)
    components = {"connection": "ready"}
    for role in ("scheduler", "worker"):
        components[role] = probe(
            os.environ.get(f"REALITY_{role.upper()}_HEALTH_URL", ""), role
        )
    overall = (
        "ready"
        if all(value == "ready" for value in components.values())
        else "unavailable"
        if "unavailable" in components.values()
        else "unknown"
    )
    return {
        "status": overall,
        "components": components,
        "observed_at": datetime.now(UTC).isoformat(),
    }
