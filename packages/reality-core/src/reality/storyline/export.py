"""Spec 182 FR-021: a run exported as a storyline draft.

The draft walks the run's confirmed commands in order. Seed identities become
``$ref`` references, the company's own party ``$company.party``, records the seed
history created ``$seed`` references and records an earlier command created
``$chapter`` references. Dates in the known date fields become day offsets from
the run start. Chapters the story itself played keep their texts; free-play
chapters carry texts marked missing. A command the format cannot express is kept
in place as ``kind: unsupported`` with the reason, so the person sees where the
draft needs a hand.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from itertools import pairwise
from typing import Any

from reality.storyline.package import StorylinePackage
from reality.storyline.references import DATE_FIELDS, is_raw_identity, walk_strings

_RECORD_ITEM = re.compile(r"^records\[(\d+)\]\.id$")


class Unsupported(ValueError):
    """An input the draft grammar cannot express."""


def day_offset(value: str, start: datetime) -> str | None:
    """``value`` as a relative day such as ``-3d``; ``None`` when it is not a date."""
    text = value.strip()
    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.combine(
                date.fromisoformat(text), datetime.min.time(), tzinfo=UTC
            )
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    days = (parsed.astimezone(UTC).date() - start.astimezone(UTC).date()).days
    return f"{days:+d}d" if days else "0d"


def register_outputs(identities: dict[str, str], output: Any, prefix: str) -> None:
    """Every identity in ``output`` becomes a reference under ``prefix``, first path wins."""
    if not isinstance(output, (dict, list)):
        return
    for path, value, _key in walk_strings(output):
        if not is_raw_identity(value) or value in identities:
            continue
        match = _RECORD_ITEM.match(path)
        if match and isinstance(output, dict):
            records = output.get("records")
            index = int(match.group(1))
            if isinstance(records, list) and index < len(records):
                family = (
                    records[index].get("family")
                    if isinstance(records[index], dict)
                    else None
                )
                if isinstance(family, str) and family:
                    identities[value] = f"{prefix}records[{family}].id"
                    continue
        identities[value] = f"{prefix}{path}"


def rewrite_input(
    node: Any,
    *,
    identities: dict[str, str],
    terms: dict[str, str],
    start: datetime,
    key: str | None = None,
) -> Any:
    """The input with identities, term codes and dates rewritten to draft grammar."""
    if isinstance(node, dict):
        return {
            str(name): rewrite_input(
                child, identities=identities, terms=terms, start=start, key=str(name)
            )
            for name, child in node.items()
            if not str(name).startswith("_")
        }
    if isinstance(node, list):
        return [
            rewrite_input(
                child, identities=identities, terms=terms, start=start, key=key
            )
            for child in node
        ]
    if isinstance(node, str):
        if is_raw_identity(node):
            if node in identities:
                return identities[node]
            raise Unsupported(
                f"{key or 'input'} names {node}, a record neither the seed nor an earlier command created."
            )
        if key == "payment_term_code" and node in terms:
            return terms[node]
        if key in DATE_FIELDS:
            offset = day_offset(node, start)
            if offset is not None:
                return offset
    return node


def _text(text: Any) -> dict[str, Any]:
    values = {
        code: getattr(text, code)
        for code in ("en", "de", "nl", "es")
        if (getattr(text, code, None) or "").strip()
    }
    return values or {"missing": True}


def draft_document(
    *,
    document: dict[str, Any],
    package: StorylinePackage,
    progress: dict[str, Any],
    confirms: list[dict[str, Any]],
    commands: frozenset[str],
) -> dict[str, Any]:
    """The draft for a run.

    ``confirms`` are the run's confirmed commands in order:
    ``{name, input, result, chapter}`` with ``chapter`` the package chapter key
    when the story played the command and ``None`` for free play.
    """
    start = (
        datetime.fromisoformat(progress["start"])
        if progress.get("start")
        else datetime.now(UTC)
    )
    identities: dict[str, str] = {}
    refs = progress.get("refs") or {}
    for group, names in refs.items():
        if group == "terms" or not isinstance(names, dict):
            continue
        for name, identity in names.items():
            if isinstance(identity, str):
                identities.setdefault(identity, f"$ref.{group}.{name}")
    if progress.get("company_party_id"):
        identities.setdefault(progress["company_party_id"], "$company.party")
    for alias, output in (progress.get("seed_outputs") or {}).items():
        register_outputs(identities, output, f"$seed.{alias}.output.")
    terms = {
        code: f"$ref.terms.{name}"
        for name, code in (refs.get("terms") or {}).items()
        if isinstance(code, str)
    }
    known_chapters = {chapter.key: chapter for chapter in package.chapters}

    chapters: list[dict[str, Any]] = []
    used: set[str] = set()
    for position, entry in enumerate(confirms, start=1):
        known = known_chapters.get(entry.get("chapter") or "")
        key = known.key if known and known.key not in used else f"step-{position}"
        used.add(key)
        chapter: dict[str, Any] = {"key": key}
        if known:
            chapter["title"] = _text(known.title)
            chapter["situation"] = _text(known.situation)
            chapter["explain"] = _text(known.explain)
            if known.view:
                chapter["view"] = known.view
        else:
            chapter["title"] = {"missing": True}
            chapter["situation"] = {"missing": True}
            chapter["explain"] = {"missing": True}
        name = str(entry.get("name") or "")
        raw_input = entry.get("input") if isinstance(entry.get("input"), dict) else {}
        if name not in commands:
            chapter.update(
                kind="unsupported",
                command=name,
                input=raw_input,
                reason=f"'{name}' is not a command a storyline can run.",
            )
        else:
            try:
                chapter.update(
                    command=name,
                    input=rewrite_input(
                        raw_input, identities=identities, terms=terms, start=start
                    ),
                )
            except Unsupported as why:
                chapter.update(
                    kind="unsupported", command=name, input=raw_input, reason=str(why)
                )
        register_outputs(identities, entry.get("result"), f"$chapter.{key}.output.")
        chapters.append(chapter)
    for current, following in pairwise(chapters):
        current["next"] = following["key"]

    draft: dict[str, Any] = {
        "storyline": 1,
        "key": f"{package.key}-draft"[:79].rstrip("-"),
        "version": 1,
        "draft": True,
        "title": {"en": f"{package.title.pick('en') or package.key} (draft)"},
        "summary": {"missing": True},
    }
    if document.get("author"):
        draft["author"] = document["author"]
    if package.process:
        draft["process"] = package.process
    draft["seed"] = document["seed"]
    draft["chapters"] = chapters
    return draft
