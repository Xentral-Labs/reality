"""Read captured observations without becoming business authority."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

FILES = {
    "manifest.json",
    "report.json",
    "spectator.json",
    "events.jsonl",
    "messages.jsonl",
    "checkpoints.jsonl",
    "world.json",
}


def references(value: Any):
    """Walk retained references; never infer identity from display numbers."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "id" or key.endswith(("_id", "_ids")):
                if isinstance(item, str):
                    yield item
                elif isinstance(item, list):
                    yield from (v for v in item if isinstance(v, str))
            if isinstance(item, (dict, list)):
                yield from references(item)
    elif isinstance(value, list):
        for item in value:
            yield from references(item)


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def directory(self, key: str) -> Path:
        relative = Path(key)
        if relative.is_absolute() or any(p in {"..", "."} for p in key.split("/")):
            raise FileNotFoundError(key)
        directory = (self.root / relative).resolve()
        if (
            directory == self.root
            or not directory.is_relative_to(self.root)
            or not directory.is_dir()
        ):
            raise FileNotFoundError(key)
        manifest = directory / "manifest.json"
        if not manifest.is_file() or not manifest.resolve().is_relative_to(directory):
            raise FileNotFoundError(key)
        return directory

    def load(self, directory: Path, filename: str, notices: list):
        if filename not in FILES:
            raise ValueError("Unsupported artifact")
        path = directory / filename
        if not path.exists():
            return [] if filename.endswith("jsonl") else {}
        if not path.resolve().is_relative_to(directory):
            notices.append(f"{filename}: unsafe file link ignored")
            return [] if filename.endswith("jsonl") else {}
        try:
            content = path.read_text(encoding="utf-8")
            if not filename.endswith("jsonl"):
                result = json.loads(content)
                if not isinstance(result, list if filename == "world.json" else dict):
                    raise ValueError("Unexpected artifact structure")
                return result
            rows = []
            lines = content.splitlines(keepends=True)
            for index, line in enumerate(lines):
                if index == len(lines) - 1 and not line.endswith("\n"):
                    notices.append(
                        f"{filename}: incomplete trailing record; waiting for writer"
                    )
                    continue
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise TypeError("Expected record object")
                    rows.append(row)
                except (ValueError, TypeError):
                    notices.append(f"{filename}: malformed record at line {index + 1}")
            return rows
        except (OSError, UnicodeError, ValueError):
            notices.append(f"{filename}: unreadable or updating; no result inferred")
            return [] if filename.endswith("jsonl") else {}

    def list_runs(self) -> dict:
        runs, notices = [], []
        if not self.root.is_dir():
            return {
                "runs": [],
                "notices": [
                    "No artifact directory yet. Start a simulator run to create journals."
                ],
            }
        candidates = []
        for child in sorted(self.root.iterdir()):
            if not child.is_dir() or not child.resolve().is_relative_to(self.root):
                continue
            if (child / "manifest.json").is_file():
                candidates.append(child)
            else:
                candidates.extend(
                    p
                    for p in sorted(child.iterdir())
                    if p.is_dir() and (p / "manifest.json").is_file()
                )
        for path in candidates:
            key = str(path.relative_to(self.root))
            try:
                directory = self.directory(key)
                manifest = self.load(directory, "manifest.json", notices)
                if not manifest.get("run_id"):
                    continue
                runs.append(
                    {
                        "key": key,
                        **{
                            k: manifest.get(k)
                            for k in ("run_id", "profile_id", "operator", "days")
                        },
                        "has_report": (directory / "report.json").is_file(),
                    }
                )
            except (FileNotFoundError, OSError):
                notices.append(f"{key}: unavailable run")
        return {"runs": runs, "notices": notices}

    def story_data(self, run_key: str) -> dict:
        """Expose only known captured artifacts for read-only day replay."""
        directory = self.directory(run_key)
        notices = []
        data = {}
        for key, filename in (
            ("manifest", "manifest.json"),
            ("snapshot", "spectator.json"),
            ("report", "report.json"),
            ("checkpoints", "checkpoints.jsonl"),
            ("messages", "messages.jsonl"),
            ("actions", "events.jsonl"),
        ):
            data[key] = self.load(directory, filename, notices)
        for key in ("snapshot", "report"):
            if data[key].get("run_id") not in (None, data["manifest"].get("run_id")):
                data[key] = {}
                notices.append(f"{key}: run identity mismatch; ignored")
        data["notices"] = notices
        return data

    def read_run(self, key: str) -> dict:
        directory = self.directory(key)
        notices = []
        manifest = self.load(directory, "manifest.json", notices)
        report = self.load(directory, "report.json", notices)
        snapshot = self.load(directory, "spectator.json", notices)
        for name, document in (("report", report), ("snapshot", snapshot)):
            if document.get("run_id") not in (None, manifest.get("run_id")):
                notices.append(f"{name}: run identity mismatch; ignored")
                if name == "report":
                    report = {}
                else:
                    snapshot = {}
        events = self.load(directory, "events.jsonl", notices)
        raw_messages = self.load(directory, "messages.jsonl", notices)
        checkpoints = self.load(directory, "checkpoints.jsonl", notices)
        checkpoint = checkpoints[-1] if checkpoints else None
        state = report or snapshot
        prepared = {
            e.get("proposal_id", e.get("id")): e
            for e in events
            if e.get("phase") == "prepared"
        }
        accepted = []
        for event in events:
            if event.get("phase") != "committed":
                continue
            before = prepared.get(event.get("proposal_id", event.get("id")), {})
            accepted.append(
                {
                    **before,
                    **event,
                    "arguments": before.get("arguments", event.get("arguments", {})),
                }
            )

        parties, source_party, orders, reference_party = {}, {}, {}, {}
        for event in accepted:
            args, receipt = event.get("arguments", {}), event.get("receipt", {})
            if event.get("tool") == "party_create":
                records = [
                    r
                    for r in receipt.get("records", [])
                    if r.get("family", r.get("type")) == "party"
                ]
                inputs = args.get("records", [])
                if len(records) != len(inputs):
                    notices.append(
                        "Party creation receipt does not match input; names remain unresolved"
                    )
                    continue
                for item, record in zip(inputs, records, strict=True):
                    for role in item.get("roles", []):
                        if role in {"customer", "supplier"}:
                            parties[record["id"]] = {
                                "id": record["id"],
                                "name": item.get("name", record["id"]),
                                "role": role,
                            }
            if event.get("tool") == "source_record_ingest":
                context = args.get("context", {})
                party = context.get("customer_party_id") or context.get(
                    "supplier_party_id"
                )
                if party and receipt.get("source_record_id"):
                    source_party[receipt["source_record_id"]] = party
                    reference_party[receipt["source_record_id"]] = party
            if event.get("tool") == "order_create":
                party = args.get("counterparty_id")
                orders[args.get("number")] = {
                    "party_id": party,
                    "document_id": receipt.get("document_id"),
                    "arguments": args,
                }
                for reference in references(receipt):
                    reference_party[reference] = party
        # New snapshots export actual roles/names; older journals use accepted creation receipts.
        for item in snapshot.get("parties", []):
            parties[item["id"]] = item
        for operation in accepted:
            args = operation.get("arguments", {})
            party = (
                args.get("customer_party_id")
                or args.get("supplier_party_id")
                or args.get("counterparty_id")
                or args.get("recipient_party_id")
                or source_party.get(operation.get("source_record_id"))
            )
            if not party:
                party = next(
                    (
                        reference_party[v]
                        for v in references(args)
                        if reference_party.get(v)
                    ),
                    None,
                )
            operation["party_id"] = party
            operation["day"] = operation.get(
                "scenario_day",
                int(operation.get("scenario_time", "day:0").split(":")[-1]),
            )
            if party:
                for reference in references(operation.get("receipt", {})):
                    reference_party[reference] = party

        # Reviewed Shopify intake does not use order_create. Retained references
        # link authored order labels to source/document identities, never shop numbers.
        for label, refs in state.get("order_references", {}).items():
            party = next(
                (
                    reference_party[v]
                    for v in references(refs)
                    if reference_party.get(v)
                ),
                None,
            )
            if label not in orders and party:
                orders[label] = {"party_id": party, **refs}

        messages = []
        for row in raw_messages:
            payload = row.get("payload", {})
            party = row.get("party_id") or source_party.get(row.get("source_record_id"))
            if party and party not in parties:
                parties[party] = {"id": party, "name": party, "role": "unknown"}
            messages.append(
                {
                    **row,
                    "payload": payload,
                    "party_id": party,
                    "direction": row.get(
                        "direction",
                        payload.get(
                            "direction",
                            "incoming"
                            if row.get("source_record_id") in source_party
                            else "not_recorded",
                        ),
                    ),
                    "status": row.get("status", payload.get("status", "not_recorded")),
                }
            )

        world_events = state.get("world_events")
        if world_events is None and report:
            world_events = self.load(directory, "world.json", notices)
        timeline = []
        for index, event in enumerate(world_events or []):
            party = event.get("party_id") or orders.get(event.get("id"), {}).get(
                "party_id"
            )
            if not party:
                party = next(
                    (
                        reference_party[v]
                        for v in event.get("ledger_entry_ids", [])
                        if reference_party.get(v)
                    ),
                    None,
                )
            if not party:
                party = source_party.get(event.get("source_record_id"))
            timeline.append(
                {
                    **event,
                    "party_id": party,
                    "sequence": index,
                    "order": orders.get(event.get("id")),
                }
            )
        timeline.sort(key=lambda e: (e.get("day", 0), e["sequence"]))
        core = state.get("core_status")
        if (
            checkpoint
            and checkpoint.get("differences")
            and core in {"passed", "passed_at_checkpoint"}
        ):
            core = "failed_at_checkpoint"
        if not core:
            core = (
                "failed_at_checkpoint"
                if checkpoint and checkpoint.get("differences")
                else "passed_at_checkpoint"
                if checkpoint
                else "unchecked"
            )
        # Corrupt records make the available evidence partial; they never silently pass.
        if notices:
            notices.insert(
                0,
                "Some evidence is incomplete. Status below is the last recorded result, not a fresh verification.",
            )
        coverage = state.get("coverage", {})
        actual = (checkpoint or {}).get("actual", report.get("final", {}))
        finance = (checkpoint or {}).get(
            "actual_finance", report.get("final_finance", {})
        )
        summary = {
            "run_state": "finished"
            if report
            else snapshot.get("run_state", "unfinished"),
            "core_status": core,
            "day": (checkpoint or {}).get("day", snapshot.get("day")),
            "last_observed_at": (checkpoint or {}).get(
                "recorded_at", snapshot.get("observed_at")
            ),
            "physical": actual.get("physical", {}),
            "warehouse_stock": actual.get(
                "physical_by_location", actual.get("locations", {})
            ),
            "accounts": finance.get("accounts", {}),
            "counts": actual.get("counts", {}),
            "differences": (checkpoint or {}).get(
                "differences", report.get("failure", {}).get("differences", [])
            ),
            "goals": dict(
                Counter(g.get("status", "unknown") for g in state.get("goals", []))
            ),
            "coverage": coverage,
            "event_count": len(timeline) if world_events is not None else None,
            "case_counts": dict(Counter(e.get("kind", "unknown") for e in timeline)),
            "operation_count": len(accepted),
        }
        return {
            "key": key,
            "manifest": manifest,
            "report": report,
            "snapshot": snapshot,
            "checkpoint": checkpoint,
            "parties": list(parties.values()),
            "messages": messages,
            "timeline": timeline,
            "operations": accepted,
            "summary": summary,
            "notices": notices,
        }
