"""Executable evidence contract for the fresh-tenant Spec 257 qualification."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from reality.services import (
    cost_query as cost_query_service,
)
from reality.services import (
    costing,
    credit_actions,
    invoice_actions,
    return_dispositions,
)

FINDING_IDS = tuple(f"F{number}" for number in range(1, 14))
TERMINAL_STATUSES = {"closed", "expected_boundary", "failed", "blocked"}
SECRET_KEYS = {"authorization", "cookie", "password", "secret", "token"}


@dataclass(frozen=True)
class FreshTenantAudit:
    company_name: str
    tenant_id: str
    release_revision: str

    def empty_result(self, *, started_at: str, finished_at: str) -> dict[str, Any]:
        return {
            "schema_version": "external-agent-closure/v1",
            "release_revision": self.release_revision,
            "company": {"name": self.company_name, "tenant_id": self.tenant_id},
            "started_at": started_at,
            "finished_at": finished_at,
            "overall_status": "blocked",
            "findings": [
                {
                    "id": finding_id,
                    "expected_disposition": "pending qualification",
                    "terminal_status": "blocked",
                    "expected_result": "pending qualification",
                    "actual_result": "not run",
                    "mutation_receipts": [],
                    "verification_reads": [],
                    "error_codes": [],
                    "evidence_files": [],
                    "notes": "Fresh public-surface qualification has not run.",
                }
                for finding_id in FINDING_IDS
            ],
            "gates": [],
        }


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<redacted>" if key.lower() in SECRET_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def write_redacted_result(path: Path, result: dict[str, Any]) -> None:
    findings = result.get("findings", [])
    if [finding.get("id") for finding in findings] != list(FINDING_IDS):
        raise ValueError("Audit result must contain ordered findings F1 through F13.")
    if any(finding.get("terminal_status") not in TERMINAL_STATUSES for finding in findings):
        raise ValueError("Audit result contains an invalid terminal status.")
    path.write_text(json.dumps(_redact(result), indent=2) + "\n", encoding="utf-8")


def test_fresh_tenant_harness_writes_ordered_redacted_terminal_result(tmp_path: Path):
    harness = FreshTenantAudit("CanisPro qualification", "ten_opaque", "revision")
    result = harness.empty_result(
        started_at="2026-09-23T10:00:00Z",
        finished_at="2026-09-23T10:01:00Z",
    )
    result["authorization"] = "Bearer must-not-leak"
    result["findings"][0]["notes"] = {"password": "must-not-leak", "safe": "kept"}
    target = tmp_path / "terminal-result.json"

    write_redacted_result(target, result)

    stored = json.loads(target.read_text(encoding="utf-8"))
    assert [finding["id"] for finding in stored["findings"]] == list(FINDING_IDS)
    assert stored["authorization"] == "<redacted>"
    assert stored["findings"][0]["notes"] == {
        "password": "<redacted>",
        "safe": "kept",
    }


@pytest.mark.parametrize("missing", ["F1", "F7", "F13"])
def test_evidence_writer_refuses_incomplete_finding_matrix(tmp_path: Path, missing: str):
    result = FreshTenantAudit("Qualification", "ten_opaque", "revision").empty_result(
        started_at="2026-09-23T10:00:00Z",
        finished_at="2026-09-23T10:01:00Z",
    )
    result["findings"] = [row for row in result["findings"] if row["id"] != missing]

    with pytest.raises(ValueError, match="F1 through F13"):
        write_redacted_result(tmp_path / "invalid.json", result)


def test_source_evidence_reality_paths_do_not_invent_cross_domain_authority():
    free_invoice = inspect.getsource(invoice_actions.record_free_supplier_invoice)
    assert "create_master_source_record" in free_invoice
    assert "create_manual_document_with_lines" in free_invoice
    assert "post_supplier_invoice" in free_invoice
    assert "source_record_id=source.id" in free_invoice
    assert "create_commitment" not in free_invoice
    assert "record_movement" not in free_invoice

    credit = inspect.getsource(credit_actions._record_invoice_credit)
    assert "create_master_source_record" in credit
    assert "create_manual_document_with_lines" in credit
    assert "post_sales_credit_note" in credit
    assert "billed_document_line_id" in inspect.getsource(credit_actions._preview_credit)
    assert "record_movement" not in credit

    returned_goods = inspect.getsource(return_dispositions.record_return_disposition)
    assert "Movement" in returned_goods
    assert "create_master_source_record" in returned_goods
    assert "record_movement" in returned_goods
    assert "source_record_id=source.id" in returned_goods
    assert "create_manual_document_with_lines" not in returned_goods
    assert "post_sales_credit_note" not in returned_goods

    cost_read = inspect.getsource(costing.cost_query) + inspect.getsource(
        cost_query_service._read
    )
    assert "cost_query" in cost_read
    assert "session.add" not in cost_read
    assert "session.commit" not in cost_read
    assert "emit_business_event" not in cost_read
    assert "create_master_source_record" not in cost_read
