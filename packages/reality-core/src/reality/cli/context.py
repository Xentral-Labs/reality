from pathlib import Path

CONTEXT_FILE = Path(__file__).resolve().parents[3] / "data" / "current_tenant"


def read_current_tenant() -> str | None:
    if not CONTEXT_FILE.exists():
        return None
    value = CONTEXT_FILE.read_text().strip()
    return value or None


def write_current_tenant(tenant_id: str) -> None:
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTEXT_FILE.write_text(f"{tenant_id}\n")
