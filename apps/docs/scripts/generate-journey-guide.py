"""Generate the public-only Business Journey Guide payload."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from reality.domain.business_journeys import load_journey_catalog

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "packages/reality-core/config/business_journey_catalog.yaml"
DATA = ROOT / "apps/docs/.vitepress/data/business-journeys.json"
PUBLIC = ROOT / "apps/docs/public/generated/business-journeys.json"


def main() -> None:
    catalog = load_journey_catalog(yaml.safe_load(SOURCE.read_text(encoding="utf-8")))
    rendered = json.dumps(catalog.public_payload(), ensure_ascii=False, indent=2) + "\n"
    for target in (DATA, PUBLIC):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    print(f"Generated Business Journey Guide: {len(catalog.entries)} journeys")


if __name__ == "__main__":
    main()
