"""Finite local operational game through normal confirmed application tools."""

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import yaml

from scenarios.company_simulator.operators import decide
from scenarios.company_simulator.world import World
from scenarios.harness.observer import differences, observe
from scenarios.harness.reporting import Recorder, encode


def profile() -> dict:
    return yaml.safe_load(
        (Path(__file__).parent / "profiles/general_company/scenario.yaml").read_text()
    )


def run_company(
    session,
    owner_id: str,
    scenario: dict,
    *,
    days: int,
    operator: str,
    output_root: Path,
    confirmed: bool = False,
) -> dict:
    if confirmed is not True:
        raise ValueError("explicit confirmation required")
    if scenario.get("kind") == "complete":
        from scenarios.company_simulator.complete import run_complete

        return run_complete(
            session,
            owner_id,
            scenario,
            days=days,
            operator=operator,
            output_root=output_root,
            confirmed=confirmed,
        )
    if (
        type(days) is not int
        or not 1 <= days <= 30
        or operator not in {"prompt", "delayed", "idle"}
    ):
        raise ValueError("invalid horizon or built-in operator")
    # This launch authorizes the shipped profile only, not arbitrary callback code or payloads.
    if scenario != profile():
        raise ValueError("only the reviewed general-company profile is supported")
    from scenarios.reference_week.simulator import Simulator

    run_id = uuid4().hex
    recorder = Recorder(Path(output_root) / run_id)
    world = World(scenario)
    fixture = {**scenario, "orders": {}}
    bridge = Simulator(session, owner_id, fixture, run_id, recorder, datetime.now(UTC))
    from reality.services.company_setup import create_company

    created = create_company(
        session,
        owner_id,
        f"company-simulator:{run_id}",
        f"Company Simulator {run_id}",
        "sandbox",
        "empty",
        confirmed=True,
    )
    bridge.tenant_id = created["tenant_id"]
    recorder.write(
        "manifest.json",
        {
            "run_id": run_id,
            "company_id": bridge.tenant_id,
            "setup_receipt": created,
            "owner_id": owner_id,
            "profile_id": scenario["id"],
            "profile_version": scenario["version"],
            "source_hashes": {
                str(path.relative_to(Path(__file__).parents[1])): sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in [
                    *sorted(Path(__file__).parent.glob("*.py")),
                    Path(__file__).parents[1] / "reference_week/simulator.py",
                    Path(__file__).parents[1] / "harness/observer.py",
                ]
            },
            "profile_hash": sha256(encode(scenario).encode()).hexdigest(),
            "operator": operator,
            "days": days,
            "clock": "ordinal days; application clock remains real",
            "coverage": "operational stock and commitments; no finance or destination proof",
        },
    )
    counter = 0

    def event(day):
        nonlocal counter
        counter += 1
        return {"id": f"D{day}-E{counter}", "scenario_time": f"day:{day}"}

    def order(label, sku, quantity, amount, day, purchase=False):
        fixture["orders"][label] = {
            "supplier" if purchase else "customer": "SUPPLIER"
            if purchase
            else "CUSTOMER",
            "promised_at": bridge.start.isoformat(),
            "total": amount,
            "lines": {sku: quantity},
            "amounts": {sku: amount},
        }
        e = event(day)
        # Ordinal clock is journal metadata, never an application timestamp.
        e["scenario_time"] = bridge.start.isoformat()
        bridge.order(e, label)
        return {"event_id": e["id"], **bridge.refs["orders"][label]}

    def move(label, sku, quantity, kind, day):
        arguments = {
            "movement_type": kind,
            "item_id": bridge.refs["items"][sku],
            "quantity": str(quantity),
        }
        if label:
            arguments["commitment_id"] = bridge.refs["orders"][label]["commitments"][
                sku
            ]
        arguments["from_location_id" if kind == "shipment" else "to_location_id"] = (
            bridge.refs["locations"]["W1"]
        )
        e = event(day)
        proposal_id, receipt = bridge.invoke(e, "movement_create", arguments)
        return {"event_id": e["id"], "proposal_id": proposal_id, "receipt": receipt}

    result = {
        "run_id": run_id,
        "company_id": bridge.tenant_id,
        "artifact_dir": str(recorder.directory),
        "core_status": "passed",
    }
    day = 0
    try:
        bridge.masters(event(0))
        for sku, quantity in scenario["opening"].items():
            move(None, sku, quantity, "opening_stock", 0)
        for day in range(1, days + 1):
            for request in world.release(day):
                order(
                    request["id"],
                    request["sku"],
                    request["quantity"],
                    request["amount"],
                    day,
                )
            for purchase in list(world.purchases.values()):
                if not purchase["received"] and purchase["arrival"] == day:
                    evidence = move(
                        purchase["id"],
                        purchase["sku"],
                        purchase["quantity"],
                        "receipt",
                        day,
                    )
                    world.received(purchase, day)
                    world.events[-1]["evidence"] = evidence
            visible = world.view(day)
            for request in visible["requests"]:
                view = world.view(day)
                decision = decide(view, request, operator)
                sku, quantity = request["sku"], request["quantity"]
                if decision == "ship":
                    cid = bridge.refs["orders"][request["id"]]["commitments"][sku]
                    bridge.invoke(
                        event(day),
                        "reserve",
                        {"commitment_id": cid, "quantity": str(quantity)},
                    )
                    evidence = move(request["id"], sku, quantity, "shipment", day)
                    world.dispatched(world.requests[request["id"]], day)
                    world.events[-1]["evidence"] = evidence
                elif decision == "purchase":
                    label = f"P{len(world.purchases) + 1:03}"
                    quote = view["quote"]
                    evidence = order(
                        label,
                        sku,
                        quote["pack_quantity"],
                        quote["pack_amount"],
                        day,
                        True,
                    )
                    world.purchased(label, sku, day)
                    world.events[-1]["evidence"] = evidence
            actual = observe(session, bridge.tenant_id)
            expected = world.expected()
            for label, row in expected["lines"].items():
                order_label, sku = label.rsplit(":", 1)
                refs = bridge.refs["orders"][order_label]
                row.update(
                    commitment_id=refs["commitments"][sku],
                    document_id=refs["document_id"],
                    source_record_id=refs["source_record_id"],
                    location_id=bridge.refs["locations"]["W1"],
                )
            expected["locations"] = {"W1": expected["physical"]}
            expected["counts"].update(
                items=2,
                locations=1,
                customers=1,
                suppliers=1,
                customer_commitments=len(world.requests),
                supplier_commitments=len(world.purchases),
            )
            mismatch = differences(expected, actual)
            for key in ("invariants", "evidence_errors"):
                mismatch.extend(differences([], actual[key], key))
            recorder.append(
                "checkpoints.jsonl",
                {
                    "day": day,
                    "expected": expected,
                    "actual": actual,
                    "differences": mismatch,
                },
            )
            result["final"] = actual
            if mismatch:
                result.update(
                    core_status="failed", failure={"day": day, "differences": mismatch}
                )
                break
    except Exception as error:  # noqa: BLE001 - retain unknown outcome, never retry
        session.rollback()
        result.update(
            core_status="unknown",
            failure={
                "day": day,
                "kind": "execution_or_observation_error",
                "error_type": type(error).__name__,
                "outcome": "reconcile retained receipts before retry",
            },
        )
    result.update(
        goals=world.goals(day),
        world_events=world.events,
        business_references=bridge.refs,
    )
    recorder.write("report.json", result)
    recorder.write("world.json", world.events)
    (recorder.directory / "report.md").write_text(
        f"# Company simulator\n\nCore: {result['core_status']}\n\n"
        + "\n".join(
            f"- {g['id']}: {g['status']} (arrival {g['arrival']}, deadline {g['deadline']})"
            for g in result["goals"]
        )
        + "\n\nCoverage: stock, reservations and order commitments. Arrivals are simulated; finance and destination evidence are pending.\n"
    )
    return result


def main() -> int:
    import argparse

    from sqlalchemy.engine import make_url
    from sqlalchemy.orm import Session

    parser = argparse.ArgumentParser(
        description="Run a bounded local reactive company rehearsal"
    )
    parser.add_argument("--actor-id", required=True)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument(
        "--operator",
        choices=("prompt", "delayed", "idle", "wrong_address"),
        default="prompt",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("../../artifacts/company_simulator")
    )
    parser.add_argument(
        "--profile", choices=("complete", "operational", "shopify"), default="complete"
    )
    parser.add_argument(
        "--operator-module",
        help="Trusted local module:function implementing a live decision policy; exact actions are reviewed interactively",
    )
    args = parser.parse_args()
    if not args.confirm or not 1 <= args.days <= 30:
        parser.error("--confirm and a 1–30 day horizon are required")
    from reality.db.core import build_engine, resolve_database_url

    database_url = resolve_database_url()
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" or url.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        parser.error("this runner requires local PostgreSQL")
    engine = build_engine(database_url)
    try:
        with Session(engine, expire_on_commit=False) as session:
            if args.profile == "shopify":
                if args.operator_module:
                    parser.error(
                        "custom live operators currently use the general complete profile"
                    )
                from scenarios.company_simulator.shopify import run_shopify

                result = run_shopify(
                    session,
                    args.actor_id,
                    days=args.days,
                    operator=args.operator,
                    output_root=args.output,
                    confirmed=True,
                )
            elif args.profile == "complete":
                from scenarios.company_simulator.complete import (
                    complete_profile,
                    run_complete,
                )

                policy = args.operator
                reviewer = None
                if args.operator_module:
                    import importlib
                    import json

                    from reality.services.memberships import Principal

                    module_name, function = args.operator_module.rsplit(":", 1)
                    policy = getattr(importlib.import_module(module_name), function)

                    def reviewer(proposal):
                        print(json.dumps(proposal, indent=2))
                        return (
                            Principal(args.actor_id)
                            if input("Approve this exact proposal? [yes/no] ").strip()
                            == "yes"
                            else None
                        )

                result = run_complete(
                    session,
                    args.actor_id,
                    complete_profile(),
                    days=args.days,
                    operator=policy,
                    review=reviewer,
                    output_root=args.output,
                    confirmed=True,
                )
            else:
                if args.operator_module:
                    parser.error("custom live operators require the complete profile")
                result = run_company(
                    session,
                    args.actor_id,
                    profile(),
                    days=args.days,
                    operator=args.operator,
                    output_root=args.output,
                    confirmed=True,
                )
        print(f"core={result['core_status']}: {result['artifact_dir']}/report.md")
        return 0 if result["core_status"] == "passed" else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
