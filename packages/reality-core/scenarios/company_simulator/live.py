"""Trusted local launcher/mailbox adapter for external code agents."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from reality.db.core import (
    Item,
    Location,
    Movement,
    Party,
    PartyRole,
    build_engine,
    resolve_database_url,
)
from reality.services import core, live_company


def bootstrap(session, actor, request_id):
    from reality.services.company_setup import create_company

    receipt = create_company(
        session,
        actor,
        "live-company:" + request_id,
        "Live Company Simulator",
        "business",
        "empty",
        confirmed=True,
    )
    tenant = receipt["tenant_id"]
    roles = list(
        session.execute(
            select(Party.id, PartyRole.role)
            .join(
                PartyRole,
                (PartyRole.tenant_id == Party.tenant_id)
                & (PartyRole.party_id == Party.id),
            )
            .where(Party.tenant_id == tenant)
        )
    )
    for role, names in [
        ("customer", ["Retail North", "Retail South"]),
        ("supplier", ["Reference supplier"]),
    ]:
        if not any(r == role for _, r in roles):
            core.create_parties(
                session, tenant, [{"name": name, "roles": [role]} for name in names]
            )
    if not session.scalar(select(Item.id).where(Item.tenant_id == tenant).limit(1)):
        core.create_items(
            session,
            tenant,
            [
                {"sku": "A", "name": "Everyday mug", "unit": "piece"},
                {"sku": "B", "name": "Everyday bowl", "unit": "piece"},
            ],
        )
    if not session.scalar(
        select(Location.id).where(Location.tenant_id == tenant).limit(1)
    ):
        core.create_locations(session, tenant, [{"name": "Main warehouse"}])
    location = session.scalar(select(Location).where(Location.tenant_id == tenant))
    for item in session.scalars(select(Item).where(Item.tenant_id == tenant)):
        source = live_company._store(
            session,
            tenant,
            "company_simulator",
            "opening",
            request_id + ":" + item.id,
            {"item_id": item.id, "quantity": "100", "location_id": location.id},
        )
        if not session.scalar(
            select(Movement.id)
            .where(Movement.tenant_id == tenant, Movement.source_record_id == source.id)
            .limit(1)
        ):
            core.record_movement(
                session,
                tenant,
                "opening_stock",
                item.id,
                Decimal(100),
                to_location_id=location.id,
                source_record_id=source.id,
                _commit=False,
            )
    from reality.services.finance.accounts import initialize_accounts

    initialize_accounts(session, tenant, _commit=False)
    session.commit()
    return tenant


def main():
    parser = argparse.ArgumentParser(
        description="Live local company and simulated inbox. No real mail transport."
    )
    parser.add_argument(
        "command",
        choices=[
            "start",
            "prepare-purchasing",
            "inbox",
            "ack",
            "reply",
            "preview",
            "inject",
            "check",
            "serve",
            "pause",
            "resume",
        ],
    )
    parser.add_argument("--actor-id", required=True)
    parser.add_argument("--tenant")
    parser.add_argument("--run-id")
    parser.add_argument("--supplier-id")
    parser.add_argument("--request-id", default="live-company")
    parser.add_argument("--rate", type=int, default=180)
    parser.add_argument("--hours", type=int, choices=[72, 96], default=72)
    parser.add_argument("--message-id")
    parser.add_argument("--cursor")
    parser.add_argument("--text-file", type=Path)
    parser.add_argument("--event-file", type=Path)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--port", type=int, default=8768)
    args = parser.parse_args()
    database_url = resolve_database_url()
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" or url.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        parser.error(
            "This developer simulator requires local PostgreSQL for the connected Reality instance"
        )
    engine = build_engine(database_url)
    try:
        with Session(engine, expire_on_commit=False) as session:
            if args.command == "start":
                if not args.confirm:
                    parser.error("--confirm is required")
                tenant = args.tenant or bootstrap(
                    session, args.actor_id, args.request_id
                )
                result = live_company.start(
                    session,
                    tenant,
                    args.actor_id,
                    request_id=args.request_id,
                    rate=args.rate,
                    hours=args.hours,
                    confirmed=True,
                )
                if not args.tenant:
                    from reality.services.live_company_purchasing import prepare

                    prepare(
                        session, tenant, args.actor_id, result["run_id"], confirmed=True
                    )
                session.commit()
            else:
                if not args.tenant or not args.run_id:
                    parser.error("--tenant and --run-id are required")
                live_company._owner(session, args.tenant, args.actor_id)
                if args.command == "serve":
                    from scenarios.company_simulator.live_web import serve

                    session.close()
                    serve(engine, args.tenant, args.actor_id, args.run_id, args.port)
                    return 0
                if args.command == "prepare-purchasing":
                    from reality.services.live_company_purchasing import prepare

                    result = prepare(
                        session,
                        args.tenant,
                        args.actor_id,
                        args.run_id,
                        supplier_id=args.supplier_id,
                        confirmed=args.confirm,
                    )
                elif args.command == "inbox":
                    result = live_company.inbox(
                        session, args.tenant, args.run_id, cursor=args.cursor
                    )
                elif args.command == "check":
                    result = live_company.monitor(session, args.tenant, args.run_id)
                elif args.command == "ack":
                    result = live_company.acknowledge(
                        session,
                        args.tenant,
                        args.actor_id,
                        args.run_id,
                        args.message_id,
                        confirmed=args.confirm,
                    )
                elif args.command == "reply":
                    if not args.text_file:
                        parser.error("--text-file is required")
                    result = live_company.reply(
                        session,
                        args.tenant,
                        args.actor_id,
                        args.run_id,
                        args.message_id,
                        args.text_file.read_text(),
                        request_id=args.request_id,
                        confirmed=args.confirm,
                    )
                elif args.command in {"pause", "resume"}:
                    from reality.db.scheduled_jobs import ScheduledJob
                    from reality.services import scheduled_jobs

                    if not args.confirm:
                        parser.error("--confirm is required")
                    schedules = list(
                        session.scalars(
                            select(ScheduledJob).where(
                                ScheduledJob.tenant_id == args.tenant,
                                ScheduledJob.job_type == "simulator.world",
                            )
                        )
                    )
                    row = next(
                        r
                        for r in schedules
                        if r.configuration["arguments"]["run_id"] == args.run_id
                    )
                    scheduled_jobs.control_schedule(
                        session,
                        args.tenant,
                        args.actor_id,
                        row.id,
                        args.command,
                        row.revision,
                        args.request_id,
                    )
                    result = {
                        "schedule_id": row.id,
                        "enabled": row.enabled,
                        "revision": row.revision,
                    }
                else:
                    if not args.event_file:
                        parser.error("--event-file is required")
                    event = json.loads(args.event_file.read_text())
                    if args.command == "preview":
                        result = live_company.preview_event(
                            session, args.tenant, args.run_id, event
                        )
                    else:
                        result = live_company.inject(
                            session,
                            args.tenant,
                            args.actor_id,
                            args.run_id,
                            event,
                            request_id=args.request_id,
                            confirmed=args.confirm,
                        )
                session.commit()
        print(json.dumps(result, ensure_ascii=False, default=str))
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
