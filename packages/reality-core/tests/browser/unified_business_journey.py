"""Explicit real-browser proof; owns all database and process resources."""

import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from conftest import record_by_id
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import AppUser, TenantMembership, build_engine
from reality.services import core
from reality.web.auth import password_hasher

ROOT = Path(__file__).resolve().parents[4]


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def ready(url, process):
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        assert process.poll() is None, f"Server exited before {url} was ready"
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise AssertionError(f"Server was not ready: {url}")


def test_real_unified_business_journey(postgres_database, tmp_path):
    assert os.environ.get("PLAYWRIGHT_MODULE"), (
        "Set PLAYWRIGHT_MODULE for this explicit browser test"
    )
    artifacts = Path(os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path)))
    artifacts.mkdir(parents=True, exist_ok=True)
    api_port, web_port = free_port(), free_port()
    while web_port == api_port:
        web_port = free_port()
    env = dict(
        os.environ,
        REALITY_DATABASE_URL=postgres_database,
        REALITY_AUTH_MODE="enabled",
        REALITY_BOOTSTRAP_TENANT_NAME="",
        REALITY_PLATFORM_ADMIN_EMAIL="",
        REALITY_PLATFORM_ADMIN_PASSWORD="",
        REALITY_COOKIE_SECURE="false",
        APP_URL=f"http://127.0.0.1:{web_port}",
        API_URL=f"http://127.0.0.1:{api_port}",
        PYTHONPATH="src",
    )
    processes, logs = [], []
    engine = None
    try:
        with (artifacts / "migration.log").open("w") as output:
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=ROOT / "packages/reality-core",
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                check=True,
                timeout=90,
            )
        engine = build_engine(postgres_database)
        factory = sessionmaker(engine, expire_on_commit=False)
        password = secrets.token_urlsafe(24)
        with factory() as session:
            tenant = core.create_tenant(session, "Journey test company")
            company = core.create_party(
                session, tenant.id, "Journey company", "company"
            )
            customer = core.create_party(
                session, tenant.id, "Journey customer", "customer"
            )
            supplier = core.create_party(
                session, tenant.id, "Journey supplier", "supplier"
            )
            core.record_customer_payment(
                session,
                tenant.id,
                customer.id,
                "30",
                payment_number="CUSTOMER-AVAILABLE",
            )
            core.record_supplier_payment(
                session,
                tenant.id,
                supplier.id,
                "50",
                payment_number="SUPPLIER-AVAILABLE",
            )
            from reality.services.finance.accounts import (
                create_account,
                set_default_account,
            )

            for side, party in (("customer", customer), ("supplier", supplier)):
                role = f"{side}_reduction"
                account = create_account(
                    session, tenant.id, code=role, name=role, role=role
                )
                set_default_account(
                    session, tenant.id, role=role, account_id=account["id"]
                )
                invoice = core.create_document(
                    session,
                    tenant.id,
                    "sales_invoice" if side == "customer" else "supplier_invoice",
                    f"{side.upper()}-REDUCTION",
                    party.id,
                    "100",
                )
                getattr(
                    core,
                    f"post_{'sales' if side == 'customer' else 'supplier'}_invoice",
                )(session, tenant.id, invoice.id)
                getattr(core, f"post_{side}_payment")(
                    session, tenant.id, invoice.id, "80"
                )
                for suffix, amount in (
                    ("COMBINED", "100"),
                    ("EXCESS", "100"),
                    ("TARGET", "10"),
                ):
                    claim = core.create_document(
                        session,
                        tenant.id,
                        "sales_invoice" if side == "customer" else "supplier_invoice",
                        f"{side.upper()}-{suffix}",
                        party.id,
                        amount,
                    )
                    getattr(
                        core,
                        "post_sales_invoice"
                        if side == "customer"
                        else "post_supplier_invoice",
                    )(session, tenant.id, claim.id)
            from reality.services.finance.references import list_references
            from reality.tools.application import (
                approve_and_execute_proposal,
                create_change_proposal,
            )

            attribution_centers = []
            for code in ("SPLIT-A", "SPLIT-B"):
                proposal = create_change_proposal(
                    session,
                    tenant.id,
                    "finance.reference.create",
                    {
                        "kind": "cost_center",
                        "code": code,
                        "name": code,
                        "reason": "Explicit fixture responsibility",
                        "expected_revision": list_references(session, tenant.id)[
                            "revision"
                        ],
                    },
                )
                attribution_centers.append(
                    json.loads(
                        approve_and_execute_proposal(
                            session, tenant.id, proposal.id
                        ).output
                    )["id"]
                )
            mapping_source = core.create_source_system(
                session, tenant.id, "journey", "Journey source"
            )
            source, _, _ = core.store_source_record(
                session,
                tenant.id,
                "journey",
                "invoice",
                "ATTRIBUTION",
                {
                    "reality_finance_v1": {
                        "net": "1000",
                        "tax": "190",
                        "codes": {"case": {"namespace": "journey-tax", "code": "EU"}},
                    }
                },
            )
            attribution_invoice = core.create_document(
                session,
                tenant.id,
                "sales_invoice",
                "ATTRIBUTION",
                customer.id,
                "1190",
                source_record_id=source.id,
            )
            core.post_sales_invoice(session, tenant.id, attribution_invoice.id)
            opening_customer = core.create_party(
                session, tenant.id, "Opening customer", "customer"
            )
            opening_supplier = core.create_party(
                session, tenant.id, "Opening supplier", "supplier"
            )
            opening_account = create_account(
                session,
                tenant.id,
                code="OPEN",
                name="Neutral opening",
                role="opening_counterpart",
            )
            set_default_account(
                session,
                tenant.id,
                role="opening_counterpart",
                account_id=opening_account["id"],
            )
            item = core.create_item(session, tenant.id, "JOURNEY-LAMP", "Journey lamp")
            warehouse = core.create_location(session, tenant.id, "Journey warehouse")
            core.record_movement(
                session,
                tenant.id,
                "receipt",
                item.id,
                "20",
                to_location_id=warehouse.id,
            )
            # Authentication scaffolding only; business setup above uses canonical services.
            owner = AppUser(
                id=core.uid("usr"),
                email="journey@example.test",
                password_hash=password_hasher.hash(password),
                status="active",
                email_verified_at=core.now(),
                is_platform_admin=False,
            )
            session.add(owner)
            session.flush()
            session.add(
                TenantMembership(
                    id=core.uid("mem"),
                    tenant_id=tenant.id,
                    user_id=owner.id,
                    role="owner",
                    status="active",
                )
            )
            session.commit()
            fixture = {
                "mapping_source": mapping_source.id,
                "attribution_invoice": attribution_invoice.id,
                "attribution_centers": attribution_centers,
                "tenant": tenant.id,
                "company": company.id,
                "customer": customer.id,
                "opening_customer": opening_customer.id,
                "opening_supplier": opening_supplier.id,
                "item": item.id,
                "warehouse": warehouse.id,
                "email": owner.email,
                "password": password,
            }
        for name, command, cwd, child_env in [
            (
                "api",
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "reality.web.app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(api_port),
                ],
                ROOT / "packages/reality-core",
                env,
            ),
            (
                "web",
                [
                    "npm",
                    "run",
                    "preview" if os.environ.get("JOURNEY_PREVIEW_DIR") else "dev",
                    "--",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(web_port),
                    "--strictPort",
                    *(
                        ["--outDir", os.environ["JOURNEY_PREVIEW_DIR"]]
                        if os.environ.get("JOURNEY_PREVIEW_DIR")
                        else []
                    ),
                ],
                ROOT / "apps/web",
                dict(
                    env,
                    VITE_API_PROXY_TARGET=f"http://127.0.0.1:{api_port}",
                ),
            ),
        ]:
            output = (artifacts / f"{name}.log").open("w")
            logs.append(output)
            processes.append(
                subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=child_env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            )
        ready(f"http://127.0.0.1:{api_port}/healthz", processes[0])
        ready(f"http://127.0.0.1:{web_port}", processes[1])
        browser_env = dict(
            env,
            JOURNEY_BASE_URL=f"http://127.0.0.1:{web_port}",
            JOURNEY_FIXTURE=json.dumps(fixture),
            JOURNEY_ARTIFACTS=str(artifacts),
        )
        with (artifacts / "browser.log").open("w") as output:
            browser_process = subprocess.Popen(
                ["node", "scripts/unified-business-journey-browser.mjs"],
                cwd=ROOT / "apps/web",
                env=browser_env,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            processes.append(browser_process)
            browser_process.wait(timeout=240)
        assert browser_process.returncode == 0, (artifacts / "browser.log").read_text()
        if os.environ.get("JOURNEY_VERIFY_PAGE_CHROME") == "1":
            for script in (
                "page-title-counts-browser.mjs",
                "page-introduction-browser.mjs",
            ):
                with (artifacts / (script + ".log")).open("w") as output:
                    result_process = subprocess.run(
                        ["node", "scripts/" + script],
                        cwd=ROOT / "apps/web",
                        env={**browser_env, "BASE_URL": f"http://127.0.0.1:{web_port}"},
                        stdout=output,
                        stderr=subprocess.STDOUT,
                        timeout=180,
                        check=False,
                    )
                assert result_process.returncode == 0, (
                    artifacts / (script + ".log")
                ).read_text()
        result = json.loads((artifacts / "result.json").read_text())
        with factory() as session:
            from reality.db.core import DocumentLine, Movement
            from reality.services.delivery_actions import delivery_proposal_detail

            for proposal in result["proposals"]:
                assert (
                    delivery_proposal_detail(session, tenant.id, proposal["id"])[
                        "verification"
                    ]
                    == "verified"
                )
            from reality.db.core import SourceRecord

            for reduction in json.loads((artifacts / "reductions.json").read_text()):
                source = record_by_id(
                    session, SourceRecord, reduction["source_record_id"]
                )
                assert json.loads(source.payload)["actor_id"] == owner.id
                assert json.loads(source.payload)["reason"] == "Agreed stated discount"
                assert reduction["cash_change"] == "0"
            for settlement in json.loads((artifacts / "settlements.json").read_text()):
                for family in ("payment", "refund", "reduction"):
                    if settlement.get(family):
                        source = record_by_id(
                            session,
                            SourceRecord,
                            settlement[family]["source_record_id"],
                        )
                        assert json.loads(source.payload)["actor_id"] == owner.id
            opening = json.loads((artifacts / "opening.json").read_text())
            assert len(opening["items"]) == 4
            for position in opening["items"]:
                source = record_by_id(
                    session, SourceRecord, position["source_record_id"]
                )
                assert json.loads(source.payload)["actor_id"] == owner.id
                assert source.source_system == "internal_opening_subledger"
            assert (
                core.open_invoice_amount(
                    session, tenant.id, opening["items"][0]["document_id"]
                )
                == 600
            )
            assert core.open_invoice_amount(session, tenant.id, result["invoice"]) == 0
            assert core.open_invoice_amount(session, tenant.id, result["credit"]) == 200
            invoice_line = record_by_id(session, DocumentLine, result["invoiceLine"])
            credit_line = record_by_id(session, DocumentLine, result["creditLine"])
            assert invoice_line.billed_document_line_id == result["orderLine"]
            assert credit_line.billed_document_line_id == invoice_line.id
            assert (
                len(
                    list(
                        session.scalars(
                            select(Movement).where(Movement.tenant_id == tenant.id)
                        )
                    )
                )
                == 2
            )
        print(f"Real business journey verified; artifacts: {artifacts}")
    finally:
        import signal

        for process in reversed(processes):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
        for output in logs:
            output.close()
        if engine:
            engine.dispose()
