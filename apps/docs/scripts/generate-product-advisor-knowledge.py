"""Generate the public-safe Reality Product Advisor evidence artifact."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from reality.domain.business_journeys import load_journey_catalog
from reality.domain.product_advisor import (
    EvidenceSource,
    EvidenceUnit,
    ProductAdvisorKnowledge,
)

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "packages/reality-core/config/product_advisor_sources.yaml"
JOURNEYS = ROOT / "packages/reality-core/config/business_journey_catalog.yaml"
COMMANDS = ROOT / "packages/reality-core/config/command_catalog.yaml"
TARGET = ROOT / "packages/reality-core/config/product_advisor_knowledge.json"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _clean_markdown(value: str) -> str:
    value = re.sub(r"^---\n.*?\n---\n", "", value, flags=re.S)
    value = re.sub(r"```.*?```", " ", value, flags=re.S)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[#>*_`|]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _chunks(value: str, *, limit: int = 6000) -> list[str]:
    words = value.split()
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for word in words:
        if current and size + len(word) + 1 > limit:
            chunks.append(" ".join(current))
            current = []
            size = 0
        current.append(word)
        size += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


def _journey_evidence() -> tuple[list[EvidenceSource], list[EvidenceUnit]]:
    catalog = load_journey_catalog(yaml.safe_load(JOURNEYS.read_text(encoding="utf-8")))
    sources: list[EvidenceSource] = []
    units: list[EvidenceUnit] = []
    support = {
        "supported": "proven",
        "partial": "limited",
        "recognition_only": "limited",
        "missing": "unavailable",
        "out_of_scope": "unavailable",
    }
    for entry in catalog.entries:
        slug = entry.id.lower()
        raw = json.dumps(entry.public_payload(), ensure_ascii=False, sort_keys=True)
        source = EvidenceSource(
            id=f"source_journey_{slug}",
            kind="journey",
            title=entry.title,
            visibility="public",
            authority="capability",
            public_url=(
                "https://docs.runreality.ai/getting-started/business-journeys"
                f"#{entry.id}"
            ),
            fingerprint=_hash(raw),
        )
        unit = EvidenceUnit(
            id=f"evidence_journey_{slug}",
            source_id=source.id,
            subject=entry.section,
            title=entry.title,
            search_text=" ".join(
                (
                    entry.id,
                    entry.section,
                    entry.title,
                    entry.question,
                    *entry.keywords,
                    *entry.question_examples,
                )
            ),
            claim_text=entry.summary,
            support=support[entry.status],
            limitations=entry.limitations,
            references=(entry.id, *entry.tools),
            fingerprint=_hash(raw + ":evidence"),
        )
        sources.append(source)
        units.append(unit)
    return sources, units


def _command_evidence() -> tuple[list[EvidenceSource], list[EvidenceUnit]]:
    payload = yaml.safe_load(COMMANDS.read_text(encoding="utf-8"))
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    source = EvidenceSource(
        id="source_executable_commands",
        kind="executable_catalog",
        title="Application commands",
        visibility="public",
        authority="executable_vocabulary",
        public_url="https://docs.runreality.ai/tool-usage/commands",
        fingerprint=_hash(raw),
    )
    units: list[EvidenceUnit] = []
    for row in payload.get("commands", []):
        name = str(row.get("service", "")).strip()
        if not name or not re.fullmatch(r"[a-z0-9_]+", name):
            continue
        title = str(row.get("name", name)).strip()
        effect = str(row.get("effect", "")).strip()
        mode = str(row.get("mode", "")).strip()
        text = " ".join(part for part in (name, title, effect, mode) if part)
        units.append(
            EvidenceUnit(
                id=f"evidence_command_{name}",
                source_id=source.id,
                subject=title,
                title=title,
                search_text=text,
                claim_text=(
                    f"{name} is a governed {mode or 'application'} command for "
                    f"{effect or title}."
                ),
                support="vocabulary_only",
                references=(name,),
                fingerprint=_hash(text),
            )
        )
    return [source], units


def _document_evidence(
    configured: dict[str, Any],
) -> tuple[list[EvidenceSource], list[EvidenceUnit]]:
    sources: list[EvidenceSource] = []
    units: list[EvidenceUnit] = []
    for item in configured.get("documents", []):
        path = ROOT / str(item["path"])
        if not path.is_file():
            raise ValueError(f"Advisor source does not exist: {item['path']}")
        raw = path.read_text(encoding="utf-8")
        clean = _clean_markdown(raw)
        if not clean:
            raise ValueError(f"Advisor source is empty: {item['path']}")
        slug = str(item["id"])
        source = EvidenceSource(
            id=f"source_document_{slug}",
            kind="public_contract"
            if item["authority"] == "technical_contract"
            else "public_document",
            title=str(item["title"]),
            visibility="public",
            authority=str(item["authority"]),
            public_url=str(item["public_url"]),
            fingerprint=_hash(raw),
        )
        topics = tuple(str(value) for value in item.get("topics", []))
        sources.append(source)
        for index, chunk in enumerate(_chunks(clean), start=1):
            units.append(
                EvidenceUnit(
                    id=f"evidence_document_{slug}_{index}",
                    source_id=source.id,
                    subject=topics[0] if topics else slug,
                    title=f"{source.title} ({index})",
                    search_text=" ".join((*topics, chunk)),
                    claim_text=chunk,
                    support="explanatory",
                    references=(),
                    fingerprint=_hash(chunk),
                )
            )
    return sources, units


def build_knowledge() -> ProductAdvisorKnowledge:
    configured = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    sources: list[EvidenceSource] = []
    evidence: list[EvidenceUnit] = []
    for source_loader in (
        _journey_evidence,
        _command_evidence,
        lambda: _document_evidence(configured),
    ):
        source_rows, evidence_rows = source_loader()
        sources.extend(source_rows)
        evidence.extend(evidence_rows)
    body = {
        "schema_version": int(configured.get("version", 1)),
        "sources": [item.model_dump(mode="json") for item in sources],
        "evidence": [item.model_dump(mode="json") for item in evidence],
    }
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return ProductAdvisorKnowledge.model_validate(
        {**body, "knowledge_version": f"advisor-v1:sha256:{_hash(canonical)}"}
    )


def main() -> None:
    knowledge = build_knowledge()
    TARGET.write_text(
        json.dumps(knowledge.public_payload(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "Generated Product Advisor knowledge: "
        f"{len(knowledge.sources)} sources, {len(knowledge.evidence)} evidence units"
    )


if __name__ == "__main__":
    main()
