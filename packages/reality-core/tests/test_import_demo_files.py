from __future__ import annotations

import csv
import json
from pathlib import Path

from reality.db.core import Document, Item, Location, Movement, Party
from reality.services.artifacts import stage_artifact
from reality.services.core import create_tenant, process_import_job
from reality.services.file_interpreters import suggested_mapping, validate_mapping
from reality.tools.application import confirm_tool, propose_tool

FIXTURES = Path(__file__).parents[1] / "fixtures" / "imports"


def _import_csv(session, tenant_id: str, filename: str, target: str, source_type: str):
    path = FIXTURES / filename
    with path.open("r", encoding="utf-8", newline="") as handle:
        columns = next(csv.reader(handle))
    mapping = suggested_mapping(columns, target)
    validate_mapping(target, mapping)
    with path.open("rb") as handle:
        artifact, _ = stage_artifact(
            session, tenant_id, handle, filename=filename, content_type="text/csv"
        )
    proposal = propose_tool(
        session,
        tenant_id,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "fixture_demo",
            "source_type": source_type,
            "expected_target": target,
            "column_mapping": mapping,
        },
    )
    action = confirm_tool(session, tenant_id, proposal.id)
    output = json.loads(action.output)
    return process_import_job(session, tenant_id, output["import_job_id"])


def test_ordered_import_demo_files_form_one_operational_story(
    session, tmp_path, monkeypatch
):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    tenant = create_tenant(session, "File Import Demo")

    _import_csv(session, tenant.id, "01_parties.csv", "party", "party")
    _import_csv(session, tenant.id, "02_locations.csv", "location", "location")
    _import_csv(session, tenant.id, "03_items.csv", "item", "item")
    _import_csv(
        session,
        tenant.id,
        "04_inventory_snapshot.csv",
        "inventory_snapshot",
        "inventory_snapshot",
    )
    orders = _import_csv(
        session, tenant.id, "05_sales_orders.csv", "sales_order", "order"
    )
    payments = _import_csv(
        session, tenant.id, "06_bank_statement.csv", "bank_statement", "bank_statement"
    )

    assert session.query(Party).filter_by(tenant_id=tenant.id).count() == 3
    assert session.query(Location).filter_by(tenant_id=tenant.id).count() == 2
    assert session.query(Item).filter_by(tenant_id=tenant.id).count() == 3
    assert session.query(Movement).filter_by(tenant_id=tenant.id).count() == 2
    assert (
        session.query(Document)
        .filter_by(tenant_id=tenant.id, type="sales_order")
        .count()
        == 2
    )
    assert orders["rows"] == 2
    assert payments["rows"] == 2
