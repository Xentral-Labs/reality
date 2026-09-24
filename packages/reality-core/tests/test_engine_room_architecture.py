"""Spec 266 DR-001: the engine room observes; no business code reads it."""

from __future__ import annotations

import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src" / "reality"

#: Modules allowed to touch the telemetry table or its reader.
ALLOWED = {
    "db/core.py",  # registers the model module with the shared metadata
    "db/interactions.py",
    "services/interaction_recorder.py",
    "services/interactions.py",
    "web/interactions_api.py",
}
TOUCHES = re.compile(
    r"reality\.db\.interactions|reality\.services\.interactions\b|"
    r"from reality\.db import interactions|from reality\.services import interactions\b"
)


def _touching() -> set[str]:
    return {
        str(path.relative_to(SOURCE))
        for path in SOURCE.rglob("*.py")
        if TOUCHES.search(path.read_text(encoding="utf-8"))
    }


def test_only_the_engine_room_reads_its_table():
    touching = _touching()
    # Positive control: the scan finds the modules that legitimately touch it.
    assert {"services/interaction_recorder.py", "web/interactions_api.py"} <= touching
    assert touching <= ALLOWED, sorted(touching - ALLOWED)


def test_the_recorder_is_the_only_thing_business_code_calls():
    """Services, tools and adapters may annotate the open interaction; the recorder
    module is the one import they share, and it writes nothing business code reads."""
    recorder_users = {
        str(path.relative_to(SOURCE))
        for path in SOURCE.rglob("*.py")
        if "interaction_recorder" in path.read_text(encoding="utf-8")
    }
    assert "services/core.py" in recorder_users  # emit_business_event notes events
    assert "tools/application.py" in recorder_users
