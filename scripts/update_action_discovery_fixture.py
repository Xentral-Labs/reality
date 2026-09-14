"""Refresh the portable frontend reference fixture from the canonical catalogs."""
import json
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[1]
config = root / "packages/reality-core/config"
commands = yaml.safe_load((config / "command_catalog.yaml").read_text())["commands"]
workspace = yaml.safe_load((config / "workspace_catalog.yaml").read_text())
fields = {"name", "service", "mode", "adapters", "related_services", "effect"}
payload = {
    "commands": [{k: v for k, v in c.items() if k in fields} for c in commands],
    "workspaces": [{"key": "all", "actions": workspace["actions"], "views": []}],
    "projections": [],
}
target = root / "apps/web/scripts/fixtures/action-reference.json"
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
