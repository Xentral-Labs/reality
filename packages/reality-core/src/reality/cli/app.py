import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer
from rich.console import Console
from rich.table import Table

from reality.cli.context import read_current_tenant, write_current_tenant
from reality.db.core import (
    Item,
    Location,
    Party,
    PaymentTerm,
    Session,
    engine,
    init_db,
)
from reality.demo.normal_month import run_normal_month
from reality.services.core import (
    InvalidOperation,
    NotFound,
    add_party_group_member,
    assign_group_price_list,
    assign_party_price_list,
    connector_shells,
    correct_movement,
    create_handling_unit,
    create_item,
    create_location,
    create_lot,
    create_party,
    create_party_group,
    create_payment_term,
    create_price_list,
    create_price_list_entry,
    create_serial_unit,
    create_source_capability,
    create_source_system,
    create_tenant,
    enqueue_source,
    ensure_demo,
    find_tenant,
    get_tenant,
    handling_units,
    hold_commitment,
    hold_document_commitments,
    hold_party_delivery,
    import_jobs,
    install_connector_shell,
    inventory_rows,
    lots,
    open_invoice_amount,
    payment_terms,
    post_customer_payment,
    post_supplier_payment,
    preview_ledger_reversal,
    preview_movement_correction,
    price_lists,
    process_pending_import_jobs,
    record_movement,
    release_commitment_hold,
    release_document_holds,
    release_party_delivery_hold,
    reserve,
    retry_import_job,
    reverse_ledger_posting_group,
    serial_units,
    set_master_data_active,
    source_capabilities,
    source_records,
    source_systems,
    tenants,
    update_item,
    update_location,
    update_party,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
)
from reality.services.notifications import deliver_next_invitation
from reality.services.projections import materialized_resolve_price
from reality.tools.application import approve_and_execute_proposal
from reality.web.email import send_company_invitation_email

app = typer.Typer(help="Reality playground")
tenant_app = typer.Typer()
scenario_app = typer.Typer()
party_app = typer.Typer()
item_app = typer.Typer()
location_app = typer.Typer()
payment_term_app = typer.Typer()
reorder_point_app = typer.Typer(help="Reorder points per item and location (spec 302).")
stock_app = typer.Typer(help="Blocked stock: block, release, scrap (spec 304).")
kit_app = typer.Typer(help="Kits: components, assembly and the bundle split (spec 333).")
customer_item_app = typer.Typer(
    help="Customer item numbers: a customer's own article numbers (spec 308)."
)
supplier_item_app = typer.Typer(
    help="Supplier item numbers: a supplier's own article numbers (spec 345)."
)
stock_count_app = typer.Typer(help="Stock counts: count a location and post the differences (spec 307).")
external_stock_app = typer.Typer(
    help="External stock: what a 3PL or shop states, compared, never taken over (spec 344)."
)
outbound_delivery_app = typer.Typer(
    help="Planned outbound deliveries: plan, pick into staging, put back (spec 334)."
)
delivery_rule_app = typer.Typer(
    help="Delivery rules: ship complete or no backorders per customer or order (spec 306)."
)
backorder_app = typer.Typer(
    help="Backorders: serve waiting orders, available to promise (spec 305)."
)
pricing_app = typer.Typer()
finance_app = typer.Typer()
commitment_app = typer.Typer()
document_app = typer.Typer()
import_app = typer.Typer()
source_app = typer.Typer()
integration_app = typer.Typer()
handling_unit_app = typer.Typer()
movement_app = typer.Typer()
lot_app = typer.Typer()
serial_app = typer.Typer()
shipment_app = typer.Typer()
app.add_typer(tenant_app, name="tenant")
app.add_typer(scenario_app, name="scenario")
app.add_typer(party_app, name="party")
app.add_typer(item_app, name="item")
app.add_typer(location_app, name="location")
app.add_typer(payment_term_app, name="payment-term")
app.add_typer(reorder_point_app, name="reorder-point")
app.add_typer(kit_app, name="kit")
app.add_typer(stock_app, name="stock-block")
app.add_typer(backorder_app, name="backorders")
app.add_typer(delivery_rule_app, name="delivery-rule")
app.add_typer(stock_count_app, name="stock-count")
app.add_typer(external_stock_app, name="external-stock")
app.add_typer(outbound_delivery_app, name="outbound-delivery")
app.add_typer(customer_item_app, name="customer-item")
app.add_typer(supplier_item_app, name="supplier-item")
supplier_terms_app = typer.Typer(
    help="A supplier's minimum order quantity and order multiple per item (spec 310)."
)
app.add_typer(supplier_terms_app, name="supplier-terms")
purchase_app = typer.Typer(help="Purchase orders: the three-way match (spec 310).")
app.add_typer(purchase_app, name="purchase")
app.add_typer(pricing_app, name="pricing")
app.add_typer(finance_app, name="finance")
app.add_typer(commitment_app, name="commitment")
app.add_typer(document_app, name="document")
app.add_typer(import_app, name="imports")
app.add_typer(source_app, name="source")
app.add_typer(integration_app, name="integration")
app.add_typer(handling_unit_app, name="handling-unit")
app.add_typer(movement_app, name="movement")
app.add_typer(lot_app, name="lot")
app.add_typer(serial_app, name="serial")
app.add_typer(shipment_app, name="shipment")
con = Console()


@shipment_app.command("list")
def shipment_list(
    tenant: str | None = None,
    direction: str = "",
    purpose: str = "",
    query: str = "",
    carrier: str = "",
    tracking: str = "",
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    observation: str = "",
):
    """List real physical shipments rather than delivery commitments."""
    from reality.services.shipments import shipments_list

    with Session() as session:
        selected = selected_tenant(session, tenant)
        result = shipments_list(
            session,
            selected.id,
            direction=direction,
            purpose=purpose,
            query=query,
            carrier=carrier,
            tracking=tracking,
            created_from=created_from,
            created_to=created_to,
            observation=observation,
        )
    table = Table("ID", "Direction", "Purpose", "Counterparty", "Packages")
    for row in result["items"]:
        table.add_row(
            row["id"],
            row["direction"],
            row["purpose"],
            row["counterparty_id"],
            str(len(row["packages"])),
        )
    con.print(table)


@shipment_app.command("show")
def shipment_show(shipment_id: str, tenant: str | None = None):
    """Explain one physical shipment, its packages, events, and Movements."""
    from reality.services.shipments import shipment_explain

    with Session() as session:
        selected = selected_tenant(session, tenant)
        try:
            result = shipment_explain(session, selected.id, shipment_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@shipment_app.command("propose")
def shipment_propose(
    tool: str,
    arguments: str,
    request_id: str,
    tenant: str | None = None,
):
    """Prepare one state-bound Shipment mutation for explicit confirmation."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )
    from reality.services.shipment_actions import SHIPMENT_TOOLS

    if tool not in SHIPMENT_TOOLS:
        raise typer.BadParameter("Choose one of the five shipment action tools.")
    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        selected = selected_tenant(session, tenant)
        try:
            proposal = prepare_delivery_action(
                session,
                selected.id,
                tool,
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, selected.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@shipment_app.command("confirm")
def shipment_confirm(
    proposal_id: str,
    review_token: str,
    yes: bool = typer.Option(False, "--yes", help="Confirm the reviewed effect."),
    tenant: str | None = None,
):
    """Explicitly confirm and execute one reviewed Shipment mutation."""
    from reality.services.delivery_actions import delivery_proposal_detail
    from reality.tools.application import approve_and_execute_proposal

    if not yes:
        typer.confirm("Execute this exact reviewed shipment action?", abort=True)
    with Session() as session:
        selected = selected_tenant(session, tenant)
        try:
            approve_and_execute_proposal(
                session,
                selected.id,
                proposal_id,
                review_token=review_token,
                confirmed=True,
            )
            result = delivery_proposal_detail(session, selected.id, proposal_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@shipment_app.command("reconcile")
def shipment_reconcile(proposal_id: str, tenant: str | None = None):
    """Inspect and reconcile an interrupted Shipment mutation by proposal ID."""
    from reality.services.delivery_actions import reconcile_delivery

    with Session() as session:
        selected = selected_tenant(session, tenant)
        try:
            result = reconcile_delivery(session, selected.id, proposal_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("invitation-worker-once")
def invitation_worker_once() -> None:
    """Deliver at most one due company invitation using the shared queue service."""
    with Session() as session:
        processed = deliver_next_invitation(session, send_company_invitation_email)
    con.print(
        "Invitation delivered or rescheduled." if processed else "No invitation due."
    )


def selected_tenant(session, explicit_id: str | None = None):
    tenant_id = explicit_id or read_current_tenant()
    if tenant_id:
        return get_tenant(session, tenant_id)
    available = tenants(session)
    if not available:
        raise NotFound("Create a tenant first.")
    return available[0]


@app.callback()
def boot(ctx: typer.Context):
    if ctx.invoked_subcommand not in {"cost-record", "cost-query"}:
        init_db()
    _observe_command(ctx)


def _command_path(argv: list[str]) -> str:
    """The subcommand names of this invocation, never its options or values."""
    command = typer.main.get_command(app)
    names = ["reality"]
    for token in argv:
        commands = getattr(command, "commands", None)
        if not commands or token not in commands:
            break
        names.append(token)
        command = commands[token]
    return " ".join(names)


def _observe_command(ctx: typer.Context) -> None:
    """Spec 266: one CLI command is one engine-room interaction.

    The company is not known yet; the first tool call or event settles it, and a
    command that never touches a company records nothing.
    """
    from reality.services import interaction_recorder as interactions

    observation, token = interactions.begin(None, "cli", _command_path(sys.argv[1:]))
    if observation is None:
        return

    def finish() -> None:
        interactions.end(observation, token, sys.exc_info()[1])

    ctx.call_on_close(finish)


@app.command()
def status():
    con.print(f"[bold]Reality V0[/bold] · {engine.dialect.name} · CLI + Web ready")


@handling_unit_app.command("create")
def handling_unit_create(
    nve: str = "",
    tenant: str | None = None,
    source_record_id: str | None = None,
):
    """Record an optional pallet identity (NVE/SSCC)."""
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            unit = create_handling_unit(
                s,
                selected.id,
                nve or None,
                source_record_id=source_record_id,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Pallet created: {unit.nve or 'without NVE'} ({unit.id})")


@handling_unit_app.command("list")
def handling_unit_list(tenant: str | None = None):
    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = handling_units(s, selected.id)
    table = Table("ID", "NVE / SSCC", "Source record", "Created")
    for unit in rows:
        table.add_row(
            unit.id,
            unit.nve or "—",
            unit.source_record_id or "—",
            unit.created_at.isoformat(),
        )
    con.print(table)


@lot_app.command("create")
def lot_create(
    item_id: str,
    lot_number: str,
    tenant: str | None = None,
    source_record_id: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            lot = create_lot(
                s,
                selected.id,
                item_id,
                lot_number,
                source_record_id=source_record_id,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Lot created: {lot.lot_number} ({lot.id})")


@lot_app.command("list")
def lot_list(item_id: str | None = None, tenant: str | None = None):
    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = lots(s, selected.id, item_id)
    table = Table("ID", "Item", "Lot number", "Created")
    for lot in rows:
        table.add_row(lot.id, lot.item_id, lot.lot_number, lot.created_at.isoformat())
    con.print(table)


@serial_app.command("create")
def serial_create(
    item_id: str,
    serial_number: str,
    tenant: str | None = None,
    lot_id: str | None = None,
    source_record_id: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            serial = create_serial_unit(
                s,
                selected.id,
                item_id,
                serial_number,
                lot_id=lot_id,
                source_record_id=source_record_id,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Serial unit created: {serial.serial_number} ({serial.id})")


@serial_app.command("list")
def serial_list(item_id: str | None = None, tenant: str | None = None):
    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = serial_units(s, selected.id, item_id)
    table = Table("ID", "Item", "Serial number", "Lot", "Created")
    for serial in rows:
        table.add_row(
            serial.id,
            serial.item_id,
            serial.serial_number,
            serial.lot_id or "—",
            serial.created_at.isoformat(),
        )
    con.print(table)


@movement_app.command("record")
def movement_record(
    movement_type: str,
    item_id: str,
    quantity: str,
    tenant: str | None = None,
    from_location_id: str | None = None,
    to_location_id: str | None = None,
    commitment_id: str | None = None,
    source_record_id: str | None = None,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
    reason: str | None = None,
    resolves_movement_id: str | None = None,
    return_announcement_id: str | None = None,
    unit: str | None = None,
):
    """Record one physical item quantity, optionally on a pallet.

    A movement may say which customer return it settles and, when it is a
    return itself, which announced return it fulfils; both are references the
    operator states, never inferred.
    """
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            from reality.services.fulfillment_readiness import require_paid_prepayment

            require_paid_prepayment(
                s, selected.id, movement_type, commitment_id, quantity
            )
            movement = record_movement(
                s,
                selected.id,
                movement_type,
                item_id,
                quantity,
                from_location_id=from_location_id,
                to_location_id=to_location_id,
                commitment_id=commitment_id,
                source_record_id=source_record_id,
                handling_unit_id=handling_unit_id,
                lot_id=lot_id,
                serial_unit_id=serial_unit_id,
                reason=reason,
                resolves_movement_id=resolves_movement_id,
                return_announcement_id=return_announcement_id,
                unit=unit,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Movement recorded: {movement.type} {movement.quantity} "
        f"({movement.id}) · pallet {movement.handling_unit_id or 'none'}"
    )


@movement_app.command("explain")
def movement_explain(movement_id: str, tenant: str | None = None):
    """Explain why a Movement exists from authoritative business links."""
    from reality.services.movement_explanations import movement_explanation

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            result = movement_explanation(s, selected.id, movement_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result)


@movement_app.command("correct")
def movement_correct(
    movement_id: str,
    reason: str,
    tenant: str | None = None,
    replacement_json: str | None = None,
    yes: bool = False,
):
    """Preview and confirm an immutable Movement correction."""
    try:
        replacement = json.loads(replacement_json) if replacement_json else None
    except json.JSONDecodeError as error:
        raise typer.BadParameter("Replacement must be valid JSON.") from error
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            preview = preview_movement_correction(
                s,
                selected.id,
                movement_id,
                reason=reason,
                replacement=replacement,
            )
            con.print_json(data=preview)
            if not yes and not typer.confirm("Apply this Movement correction?"):
                con.print("Correction cancelled; no Movement was created.")
                raise typer.Exit()
            result = correct_movement(
                s,
                selected.id,
                movement_id,
                reason=reason,
                replacement=replacement,
                actor_context={"surface": "cli"},
                expected_revision=preview["revision"],
                preview_fingerprint=preview["request_fingerprint"],
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Movement corrected: {result.original_movement_id} "
        f"→ {result.compensating_movement_id}"
    )


@finance_app.command("reverse")
def ledger_reverse(
    posting_group_id: str,
    reason: str,
    tenant: str | None = None,
    yes: bool = False,
):
    """Preview and confirm a complete immutable posting-group reversal."""
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            preview = preview_ledger_reversal(
                s, selected.id, posting_group_id, reason=reason
            )
            con.print_json(data=preview)
            if not yes and not typer.confirm("Reverse this Ledger posting group?"):
                con.print("Reversal cancelled; no LedgerEntry was created.")
                raise typer.Exit()
            result = reverse_ledger_posting_group(
                s,
                selected.id,
                posting_group_id,
                reason=reason,
                actor_context={"surface": "cli"},
                expected_revision=preview["revision"],
                preview_fingerprint=preview["request_fingerprint"],
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Ledger posting group reversed: {result.original_posting_group_id} "
        f"→ {result.reversing_posting_group_id}"
    )


@commitment_app.command("reserve")
def commitment_reserve(
    commitment_id: str,
    quantity: str | None = None,
    tenant: str | None = None,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
    location_id: str | None = typer.Option(
        None, help="Reserve the rest at this warehouse instead of the promise's own."
    ),
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            result = reserve(
                s,
                selected.id,
                commitment_id,
                quantity,
                handling_unit_id=handling_unit_id,
                lot_id=lot_id,
                serial_unit_id=serial_unit_id,
                location_id=location_id,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Reserved {result.reserved}; shortage {result.shortage}; "
        f"reservation {result.reservation.id if result.reservation else 'none'}"
    )


@import_app.command("work")
def imports_work(tenant: str | None = None, limit: int = 100):
    with Session() as session:
        try:
            selected = selected_tenant(session, tenant)
            completed, failed = process_pending_import_jobs(
                session, selected.id, limit=limit
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"Import jobs: {completed} completed, {failed} failed")


@source_app.command("ingest")
def source_ingest(
    file: Path,
    source_system: str,
    source_type: str,
    external_id: str,
    tenant: str | None = None,
    source_version_at: str | None = None,
    context_json: str = "{}",
):
    try:
        payload = json.loads(file.read_text(encoding="utf-8"))
        context = json.loads(context_json)
    except (OSError, json.JSONDecodeError) as error:
        raise typer.BadParameter(f"Cannot read JSON input: {error}") from error
    if not isinstance(payload, dict) or not isinstance(context, dict):
        raise typer.BadParameter("Payload and context must be JSON objects.")
    with Session() as session:
        try:
            selected = selected_tenant(session, tenant)
            source, job = enqueue_source(
                session,
                selected.id,
                source_system,
                source_type,
                external_id,
                payload,
                source_version_at=source_version_at,
                context=context,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Source stored: {source.id} · version {source.version} · "
        f"job {job.id} {job.status}"
    )


@source_app.command("list")
def source_list(tenant: str | None = None):
    with Session() as session:
        selected = selected_tenant(session, tenant)
        rows = source_records(session, selected.id)
        jobs = {job.source_record_id: job for job in import_jobs(session, selected.id)}
    table = Table("ID", "System", "Type", "External ID", "Version", "Import")
    for source in rows:
        job = jobs.get(source.id)
        table.add_row(
            source.id,
            source.source_system,
            source.source_type,
            source.external_id,
            str(source.version),
            job.status if job else "—",
        )
    con.print(table)


@source_app.command("show")
def source_show(source_id: str, tenant: str | None = None, raw: bool = False):
    with Session() as session:
        selected = selected_tenant(session, tenant)
        source = next(
            (
                row
                for row in source_records(session, selected.id)
                if row.id == source_id
            ),
            None,
        )
    if source is None:
        raise typer.BadParameter("SourceRecord not found.")
    if raw:
        con.print(source.payload)
    else:
        con.print(
            f"{source.id} · {source.source_system}/{source.source_type} · "
            f"{source.external_id} · version {source.version}\n{source.payload}"
        )


@source_app.command("retry")
def source_retry(job_id: str, tenant: str | None = None):
    with Session() as session:
        selected = selected_tenant(session, tenant)
        job = retry_import_job(session, selected.id, job_id)
    con.print(f"Import job {job.id}: {job.status}")


@integration_app.command("system-create")
def integration_system_create(
    code: str,
    name: str,
    tenant: str | None = None,
    description: str = "",
):
    with Session() as session:
        try:
            selected = selected_tenant(session, tenant)
            system = create_source_system(session, selected.id, code, name, description)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Source system created: {system.code} ({system.id})")


@integration_app.command("capability-add")
def integration_capability_add(
    source_system_id: str,
    source_type: str,
    target_type: str,
    tenant: str | None = None,
):
    with Session() as session:
        try:
            selected = selected_tenant(session, tenant)
            capability = create_source_capability(
                session,
                selected.id,
                source_system_id,
                source_type,
                target_type,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Capability added: {capability.source_type} → {capability.target_type}"
    )


@integration_app.command("list")
def integration_list(tenant: str | None = None):
    with Session() as session:
        selected = selected_tenant(session, tenant)
        systems = source_systems(session, selected.id)
        capabilities = source_capabilities(session, selected.id)
    table = Table("ID", "Code", "Name", "Status")
    for system in systems:
        table.add_row(
            system.id,
            system.code,
            system.name,
            "active" if system.is_active else "inactive",
        )
    con.print(table)
    capability_table = Table("System ID", "Source type", "Target type", "Status")
    for capability in capabilities:
        capability_table.add_row(
            capability.source_system_id,
            capability.source_type,
            capability.target_type,
            "active" if capability.is_active else "inactive",
        )
    con.print(capability_table)


@integration_app.command("catalog")
def integration_catalog(tenant: str | None = None):
    with Session() as session:
        selected = selected_tenant(session, tenant)
        shells = connector_shells(session, selected.id)
    table = Table("Code", "Name", "Category", "Capabilities", "Status")
    for shell in shells:
        table.add_row(
            shell["code"],
            shell["name"],
            shell["category"],
            str(len(shell["capabilities"])),
            "installed" if shell["installed"] else "available",
        )
    con.print(table)


@integration_app.command("install-shell")
def integration_install_shell(
    code: str,
    tenant: str | None = None,
    source_types: str = "",
    system_code: str = "",
    system_name: str = "",
):
    with Session() as session:
        try:
            selected = selected_tenant(session, tenant)
            selected_types = [
                value.strip() for value in source_types.split(",") if value.strip()
            ]
            system = install_connector_shell(
                session,
                selected.id,
                code,
                selected_types or None,
                system_code or None,
                system_name or None,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Mock shell installed: {system.name} ({system.id})")


@tenant_app.command("create")
def tenant_create(name: str):
    with Session() as s:
        t = create_tenant(s, name)
        con.print(f"✓ Tenant created: [bold]{t.name}[/bold] ({t.id})")


@tenant_app.command("list")
def tenant_list():
    with Session() as s:
        for t in tenants(s):
            con.print(f"{t.id}  {t.name}")


@tenant_app.command("use")
def tenant_use(name_or_id: str):
    with Session() as s:
        try:
            tenant = find_tenant(s, name_or_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error), param_hint="name_or_id") from error
    write_current_tenant(tenant.id)
    con.print(f"✓ Current tenant: {tenant.name} ({tenant.id})")


@tenant_app.command("current")
def tenant_current():
    tenant_id = read_current_tenant()
    if not tenant_id:
        raise typer.Exit("No current tenant. Run: reality tenant use NAME_OR_ID")
    with Session() as s:
        try:
            tenant = get_tenant(s, tenant_id)
        except NotFound as error:
            raise typer.Exit(str(error)) from error
    con.print(f"{tenant.id}  {tenant.name}")


@party_app.command("create")
def party_create(
    name: str,
    party_type: str,
    tenant: str | None = None,
    source_system: str = "",
    external_id: str = "",
    role: Annotated[list[str] | None, typer.Option("--role")] = None,
    accounting_code: str = "",
    payment_term_code: str = "",
    default_currency: str = "EUR",
    credit_limit: str = "0",
    tax_identifier: str = "",
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            party = create_party(
                s,
                selected.id,
                name,
                party_type,
                source_system=source_system,
                external_id=external_id,
                roles=role,
                accounting_code=accounting_code,
                payment_term_code=payment_term_code,
                default_currency=default_currency,
                credit_limit=credit_limit,
                tax_identifier=tax_identifier,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Party created: {party.name} ({party.id})")


@party_app.command("update")
def party_update(
    party_id: str,
    name: str,
    party_type: str,
    tenant: str | None = None,
    source_system: str | None = None,
    external_id: str | None = None,
    role: Annotated[list[str] | None, typer.Option("--role")] = None,
    accounting_code: str | None = None,
    payment_term_code: str | None = None,
    default_currency: str | None = None,
    credit_limit: str | None = None,
    tax_identifier: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            party = update_party(
                s,
                selected.id,
                party_id,
                name,
                party_type,
                source_system=source_system,
                external_id=external_id,
                roles=role,
                accounting_code=accounting_code,
                payment_term_code=payment_term_code,
                default_currency=default_currency,
                credit_limit=credit_limit,
                tax_identifier=tax_identifier,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Party updated: {party.name} ({party.id})")


def change_party_active(party_id: str, is_active: bool, tenant: str | None) -> None:
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            party = set_master_data_active(s, selected.id, Party, party_id, is_active)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Party {'activated' if is_active else 'deactivated'}: {party.name} ({party.id})"
    )


@party_app.command("deactivate")
def party_deactivate(party_id: str, tenant: str | None = None):
    change_party_active(party_id, False, tenant)


@party_app.command("merge")
def party_merge(
    duplicate_party_id: str,
    surviving_party_id: str,
    reason: str = typer.Option(..., help="Why the two business partners are one."),
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm merging a duplicate business partner into its survivor (spec 339)."""
    from reality.tools.application import create_change_proposal, reject_proposal

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            proposal = create_change_proposal(
                s,
                selected.id,
                "party_merge",
                {
                    "duplicate_party_id": duplicate_party_id,
                    "surviving_party_id": surviving_party_id,
                    "reason": reason,
                },
                actor_type="human",
            )
            con.print_json(data=json.loads(proposal.output)["party_merge"])
            if not yes and not typer.confirm("Confirm this merge?"):
                # A declined review leaves no decision waiting for anyone.
                reject_proposal(s, selected.id, proposal.id)
                con.print("Stopped; nothing changed.")
                raise typer.Exit()
            approve_and_execute_proposal(s, selected.id, proposal.id, confirmed=True)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Merged {duplicate_party_id} into {surviving_party_id}")


@party_app.command("merges")
def party_merges_show(party_id: str = "", tenant: str | None = None):
    """List the business partner merges, or those one partner took part in."""
    from reality.services.party_merges import party_merges

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            rows = party_merges(s, selected.id, party_id=party_id or None)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=rows, default=str)


@party_app.command("activate")
def party_activate(party_id: str, tenant: str | None = None):
    change_party_active(party_id, True, tenant)


@stock_app.command("list")
def stock_block_list(
    item_id: str = "", location_id: str = "", status: str = "active",
    tenant: str | None = None,
):
    """List stock blocks."""
    from reality.services.stock_blocks import stock_blocks

    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = stock_blocks(
            s,
            selected.id,
            item_id=item_id or None,
            location_id=location_id or None,
            status=status,
        )
    con.print_json(data=rows, default=str)


def _stock_block_change(
    tool: str,
    arguments: dict,
    tenant: str | None,
    yes: bool,
    preview_key: str = "stock_block",
):
    from reality.tools.application import create_change_proposal, reject_proposal

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            proposal = create_change_proposal(
                s, selected.id, tool, arguments, actor_type="human"
            )
            con.print_json(data=json.loads(proposal.output)[preview_key], default=str)
            if not yes and not typer.confirm("Confirm this change?"):
                reject_proposal(s, selected.id, proposal.id)
                con.print("Stopped; nothing changed.")
                raise typer.Exit()
            approve_and_execute_proposal(s, selected.id, proposal.id, confirmed=True)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error


@stock_app.command("block")
def stock_block_command(
    item_id: str,
    location_id: str,
    quantity: str,
    reason_code: str = typer.Option(..., "--reason", help="quality, damage, expiry or inspection"),
    note: str = "",
    lot_id: str = "",
    handling_unit_id: str = "",
    serial_unit_id: str = "",
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm blocking stock where it lies."""
    arguments = {
        "item_id": item_id,
        "location_id": location_id,
        "quantity": quantity,
        "reason_code": reason_code,
        "note": note,
        **{
            key: value
            for key, value in (
                ("lot_id", lot_id),
                ("handling_unit_id", handling_unit_id),
                ("serial_unit_id", serial_unit_id),
            )
            if value
        },
    }
    _stock_block_change("stock_block", arguments, tenant, yes)
    con.print("✓ Stock blocked")


@stock_app.command("release")
def stock_block_release_command(
    block_id: str,
    reason: str = typer.Option(..., "--reason"),
    quantity: str = "",
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm releasing a stock block, wholly or partly."""
    arguments = {"block_id": block_id, "reason": reason}
    if quantity:
        arguments["quantity"] = quantity
    _stock_block_change("stock_block_release", arguments, tenant, yes)
    con.print("✓ Stock released")


_BACKORDER_LINE = typer.Option(
    None, "--line", help="COMMITMENT_ID=QUANTITY; repeat per order"
)


@backorder_app.command("serve")
def backorders_serve_command(
    item_id: str,
    location_id: str,
    purchase: str = typer.Option("", "--purchase", help="The received purchase"),
    line: list[str] | None = _BACKORDER_LINE,
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm reserving available stock for waiting orders."""
    arguments: dict = {"item_id": item_id, "location_id": location_id}
    if purchase:
        arguments["supplier_commitment_id"] = purchase
    if line:
        try:
            arguments["lines"] = [
                {"commitment_id": identity, "quantity": quantity}
                for identity, quantity in (entry.split("=", 1) for entry in line)
            ]
        except ValueError as error:
            raise typer.BadParameter("--line takes COMMITMENT_ID=QUANTITY") from error
    _stock_block_change(
        "backorders_serve", arguments, tenant, yes, preview_key="backorder_serving"
    )
    con.print("✓ Backorders served")


@customer_item_app.command("list")
def customer_item_list_command(
    party: str = typer.Option("", "--party"),
    item: str = typer.Option("", "--item"),
    tenant: str | None = None,
):
    """A customer's own article numbers, or the numbers used for one item."""
    from reality.services.customer_item_numbers import customer_item_numbers

    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = customer_item_numbers(
            s, selected.id, party_id=party or None, item_id=item or None
        )
    con.print_json(data=rows, default=str)


@customer_item_app.command("set")
def customer_item_set_command(
    party_id: str,
    customer_item_number: str,
    item_id: str,
    name: str = typer.Option("", "--name"),
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm which of our items a customer's number names."""
    _stock_block_change(
        "customer_item_number_set",
        {
            "party_id": party_id,
            "customer_item_number": customer_item_number,
            "item_id": item_id,
            "customer_item_name": name,
        },
        tenant,
        yes,
        preview_key="customer_item_number",
    )
    con.print("✓ Customer item number stated")


@customer_item_app.command("remove")
def customer_item_remove_command(
    party_id: str,
    customer_item_number: str,
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm withdrawing a customer's number."""
    _stock_block_change(
        "customer_item_number_remove",
        {"party_id": party_id, "customer_item_number": customer_item_number},
        tenant,
        yes,
        preview_key="customer_item_number",
    )
    con.print("✓ Customer item number withdrawn")


@supplier_item_app.command("list")
def supplier_item_list_command(
    party: str = typer.Option("", "--party"),
    item: str = typer.Option("", "--item"),
    tenant: str | None = None,
):
    """A supplier's own article numbers, or the numbers used for one item."""
    from reality.services.supplier_item_numbers import supplier_item_numbers

    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = supplier_item_numbers(
            s, selected.id, party_id=party or None, item_id=item or None
        )
    con.print_json(data=rows, default=str)


@supplier_item_app.command("set")
def supplier_item_set_command(
    party_id: str,
    supplier_item_number: str,
    item_id: str,
    name: str = typer.Option("", "--name"),
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm which of our items a supplier's number names."""
    _stock_block_change(
        "supplier_item_number_set",
        {
            "party_id": party_id,
            "supplier_item_number": supplier_item_number,
            "item_id": item_id,
            "supplier_item_name": name,
        },
        tenant,
        yes,
        preview_key="supplier_item_number",
    )
    con.print("✓ Supplier item number stated")


@supplier_item_app.command("remove")
def supplier_item_remove_command(
    party_id: str,
    supplier_item_number: str,
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm withdrawing a supplier's number."""
    _stock_block_change(
        "supplier_item_number_remove",
        {"party_id": party_id, "supplier_item_number": supplier_item_number},
        tenant,
        yes,
        preview_key="supplier_item_number",
    )
    con.print("✓ Supplier item number withdrawn")


company_currency_app = typer.Typer(
    help="The company currency the books are kept in (spec 309)."
)
finance_app.add_typer(company_currency_app, name="company-currency")


@company_currency_app.command("show")
def company_currency_show_command(tenant: str | None = None):
    """The company currency and whether anything is posted yet."""
    from reality.services.finance.company_currency import company_currency_state

    with Session() as s:
        selected = selected_tenant(s, tenant)
        state = company_currency_state(s, selected.id)
    con.print_json(data=state, default=str)


@company_currency_app.command("set")
def company_currency_set_command(
    currency: str,
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm the company currency; refused once anything is posted."""
    _stock_block_change(
        "company_currency_set",
        {"currency": currency},
        tenant,
        yes,
        preview_key="company_currency",
    )
    con.print("✓ Company currency stated")


company_time_zone_app = typer.Typer(
    help="The time zone the company's business days are counted in (spec 349)."
)
app.add_typer(company_time_zone_app, name="company-time-zone")


@company_time_zone_app.command("show")
def company_time_zone_show_command(tenant: str | None = None):
    """The company time zone and whether it was stated."""
    from reality.services.company_time_zone import company_time_zone_state

    with Session() as s:
        selected = selected_tenant(s, tenant)
        state = company_time_zone_state(s, selected.id)
    con.print_json(data=state, default=str)


@company_time_zone_app.command("set")
def company_time_zone_set_command(
    time_zone: str,
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm the company time zone (an IANA name such as Europe/Berlin)."""
    _stock_block_change(
        "company_time_zone_set",
        {"time_zone": time_zone},
        tenant,
        yes,
        preview_key="company_time_zone",
    )
    con.print("✓ Company time zone stated")


@supplier_terms_app.command("list")
def supplier_terms_list_command(
    party: str = typer.Option("", "--party"),
    item: str = typer.Option("", "--item"),
    tenant: str | None = None,
):
    """Suppliers' minimum order quantities and order multiples."""
    from reality.services.supplier_item_terms import supplier_item_terms

    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = supplier_item_terms(
            s, selected.id, party_id=party or None, item_id=item or None
        )
    con.print_json(data=rows, default=str)


@supplier_terms_app.command("set")
def supplier_terms_set_command(
    party_id: str,
    item_id: str,
    minimum: str | None = typer.Option(None, "--minimum"),
    multiple: str | None = typer.Option(None, "--multiple"),
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm a supplier's minimum and order multiple for an item."""
    _stock_block_change(
        "supplier_item_terms_set",
        {
            "party_id": party_id,
            "item_id": item_id,
            **({"minimum_quantity": minimum} if minimum else {}),
            **({"order_multiple": multiple} if multiple else {}),
        },
        tenant,
        yes,
        preview_key="supplier_item_terms",
    )
    con.print("✓ Supplier item terms stated")


@supplier_terms_app.command("remove")
def supplier_terms_remove_command(
    party_id: str, item_id: str, tenant: str | None = None, yes: bool = False
):
    """Review and confirm withdrawing a supplier's terms for an item."""
    _stock_block_change(
        "supplier_item_terms_remove",
        {"party_id": party_id, "item_id": item_id},
        tenant,
        yes,
        preview_key="supplier_item_terms",
    )
    con.print("✓ Supplier item terms withdrawn")


@purchase_app.command("match")
def purchase_match_command(document_id: str, tenant: str | None = None):
    """Whether each line of a purchase order is ordered = received = billed."""
    from reality.services.purchase_match import purchase_match

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            result = purchase_match(s, selected.id, document_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@purchase_app.command("substitute")
def purchase_substitute_command(
    commitment_id: str,
    item_id: str,
    reason: str = typer.Option(..., help="Why the substitute is accepted."),
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm another item in place of what a purchase line ordered (spec 338)."""
    from reality.tools.application import create_change_proposal, reject_proposal

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            proposal = create_change_proposal(
                s,
                selected.id,
                "commitment_substitute_accept",
                {"commitment_id": commitment_id, "item_id": item_id, "reason": reason},
                actor_type="human",
            )
            con.print_json(data=json.loads(proposal.output)["substitute"])
            if not yes and not typer.confirm("Accept this substitute?"):
                reject_proposal(s, selected.id, proposal.id)
                con.print("Stopped; nothing changed.")
                raise typer.Exit()
            approve_and_execute_proposal(s, selected.id, proposal.id, confirmed=True)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Substitute accepted: {item_id} for {commitment_id}")


_COUNT_LINE = typer.Option(
    None, "--line", help="ITEM_ID[:LOT_ID]=QUANTITY; repeat per counted line"
)


@stock_count_app.command("record")
def stock_count_record_command(
    location_id: str,
    line: list[str] | None = _COUNT_LINE,
    note: str = "",
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm a count of a location; differences are posted."""
    lines = []
    for entry in line or []:
        try:
            subject, quantity = entry.split("=", 1)
        except ValueError as error:
            raise typer.BadParameter("--line takes ITEM_ID[:LOT_ID]=QUANTITY") from error
        item_id, _, lot_id = subject.partition(":")
        lines.append(
            {
                "item_id": item_id,
                "counted_quantity": quantity,
                **({"lot_id": lot_id} if lot_id else {}),
            }
        )
    _stock_block_change(
        "stock_count",
        {"location_id": location_id, "note": note, "lines": lines},
        tenant,
        yes,
        preview_key="stock_count",
    )
    con.print("✓ Count recorded")


@stock_count_app.command("list")
def stock_count_list_command(location_id: str = "", tenant: str | None = None):
    """The counts of a location or of the company, newest first."""
    from reality.services.stock_counts import stock_counts

    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = stock_counts(s, selected.id, location_id=location_id or None)
    con.print_json(data=rows, default=str)


@stock_count_app.command("show")
def stock_count_show_command(stock_count_id: str, tenant: str | None = None):
    """One count with its lines and the adjustments that posted it."""
    from reality.services.stock_counts import stock_count_detail

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            answer = stock_count_detail(s, selected.id, stock_count_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=answer, default=str)

_EXTERNAL_LINE = typer.Option(
    None,
    "--line",
    help="ITEM_ID@LOCATION_ID=QUANTITY[@STATED_AT]; repeat per stated line",
)


@external_stock_app.command("state")
def external_stock_state_command(
    line: list[str] | None = _EXTERNAL_LINE,
    reporter_party_id: str = "",
    note: str = "",
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm stock someone outside states; nothing moves."""
    lines = []
    for entry in line or []:
        try:
            subject, stated = entry.split("=", 1)
            item_id, location_id = subject.split("@", 1)
        except ValueError as error:
            raise typer.BadParameter(
                "--line takes ITEM_ID@LOCATION_ID=QUANTITY[@STATED_AT]"
            ) from error
        quantity, _, stated_at = stated.partition("@")
        lines.append(
            {
                "item_id": item_id,
                "location_id": location_id,
                "quantity": quantity,
                **({"stated_at": stated_at} if stated_at else {}),
            }
        )
    _stock_block_change(
        "external_stock_state",
        {
            "lines": lines,
            "reporter_party_id": reporter_party_id or None,
            "note": note,
        },
        tenant,
        yes,
        preview_key="external_stock",
    )
    con.print("✓ External stock stated")


@external_stock_app.command("list")
def external_stock_list_command(
    item_id: str = "",
    location_id: str = "",
    differing_only: bool = False,
    tenant: str | None = None,
):
    """The latest statement per item and location, with Reality's stock then."""
    from reality.services.external_stock import external_stock

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            rows = external_stock(
                s,
                selected.id,
                item_id=item_id or None,
                location_id=location_id or None,
                differing_only=differing_only,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=rows, default=str)


_DELIVERY_LINE = typer.Option(
    None, "--line", help="COMMITMENT_ID=QUANTITY; repeat per promise"
)
_PICK_LINE = typer.Option(
    None,
    "--line",
    help="COMMITMENT_ID=QUANTITY[@LOCATION_ID]; repeat per promise",
)


def _delivery_lines(entries: list[str] | None, location_key: str | None = None):
    lines = []
    for entry in entries or []:
        try:
            commitment_id, rest = entry.split("=", 1)
        except ValueError as error:
            raise typer.BadParameter(
                "--line takes COMMITMENT_ID=QUANTITY[@LOCATION_ID]"
            ) from error
        quantity, _, location_id = rest.partition("@")
        line = {"commitment_id": commitment_id, "quantity": quantity}
        if location_key and location_id:
            line[location_key] = location_id
        lines.append(line)
    return lines


def _delivery_statement(
    recipient: str, address: str, slot_from: str, slot_until: str, staging: str
) -> dict:
    statement: dict = {}
    if recipient:
        statement["recipient_party_id"] = recipient
    if address:
        try:
            statement["address"] = json.loads(address)
        except ValueError as error:
            raise typer.BadParameter("--address takes a JSON object") from error
    if slot_from or slot_until:
        statement["slot"] = {"from": slot_from, "until": slot_until}
    if staging:
        statement["staging_location_id"] = staging
    return statement


@outbound_delivery_app.command("plan")
def outbound_delivery_plan_command(
    customer_id: str,
    line: list[str] | None = _DELIVERY_LINE,
    recipient: str = "",
    address: str = typer.Option("", help='JSON, e.g. {"street": "...", "city": "..."}'),
    slot_from: str = "",
    slot_until: str = "",
    staging: str = "",
    note: str = "",
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm a planned delivery of a customer's open promises."""
    _stock_block_change(
        "outbound_delivery_plan",
        {
            "customer_id": customer_id,
            "lines": _delivery_lines(line),
            "note": note,
            **_delivery_statement(recipient, address, slot_from, slot_until, staging),
        },
        tenant,
        yes,
        preview_key="outbound_delivery",
    )
    con.print("✓ Delivery planned")


@outbound_delivery_app.command("revise")
def outbound_delivery_revise_command(
    outbound_delivery_id: str,
    line: list[str] | None = _DELIVERY_LINE,
    recipient: str = "",
    address: str = typer.Option("", help="JSON object; replaces the stated address"),
    slot_from: str = "",
    slot_until: str = "",
    staging: str = "",
    note: str | None = None,
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm a revision; options left out stay as stated."""
    changes = _delivery_statement(recipient, address, slot_from, slot_until, staging)
    if line:
        changes["lines"] = _delivery_lines(line)
    if note is not None:
        changes["note"] = note
    _stock_block_change(
        "outbound_delivery_revise",
        {"outbound_delivery_id": outbound_delivery_id, **changes},
        tenant,
        yes,
        preview_key="outbound_delivery",
    )
    con.print("✓ Delivery revised")


@outbound_delivery_app.command("pick")
def outbound_delivery_pick_command(
    outbound_delivery_id: str,
    line: list[str] | None = _PICK_LINE,
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm picking into the delivery's staging location."""
    _stock_block_change(
        "outbound_delivery_pick",
        {
            "outbound_delivery_id": outbound_delivery_id,
            "lines": _delivery_lines(line, "from_location_id"),
        },
        tenant,
        yes,
        preview_key="outbound_delivery",
    )
    con.print("✓ Picked")


@outbound_delivery_app.command("put-back")
def outbound_delivery_put_back_command(
    outbound_delivery_id: str,
    line: list[str] | None = _PICK_LINE,
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm putting picked goods back (COMMITMENT_ID=QUANTITY@LOCATION_ID)."""
    _stock_block_change(
        "outbound_delivery_put_back",
        {
            "outbound_delivery_id": outbound_delivery_id,
            "lines": _delivery_lines(line, "to_location_id"),
        },
        tenant,
        yes,
        preview_key="outbound_delivery",
    )
    con.print("✓ Put back")


@outbound_delivery_app.command("list")
def outbound_delivery_list_command(
    customer_id: str = "", open_only: bool = False, tenant: str | None = None
):
    """The planned deliveries, newest first."""
    from reality.services.outbound_deliveries import outbound_deliveries

    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = outbound_deliveries(
            s, selected.id, customer_id=customer_id or None, open_only=open_only
        )
    con.print_json(data=rows, default=str)


@outbound_delivery_app.command("show")
def outbound_delivery_show_command(outbound_delivery_id: str, tenant: str | None = None):
    """One planned delivery with its picks, statements and dispatch arguments."""
    from reality.services.outbound_deliveries import outbound_delivery_detail

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            answer = outbound_delivery_detail(s, selected.id, outbound_delivery_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=answer, default=str)


@delivery_rule_app.command("show")
def delivery_rule_show(
    party: str = typer.Option("", "--party"),
    order: str = typer.Option("", "--order"),
    tenant: str | None = None,
):
    """The delivery rule in force for a customer or an order, with its history."""
    from reality.services.delivery_rules import delivery_rules

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            answer = delivery_rules(
                s, selected.id, party_id=party or None, document_id=order or None
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=answer, default=str)


@delivery_rule_app.command("set")
def delivery_rule_set_command(
    rule: str,
    reason: str = typer.Option(..., "--reason"),
    party: str = typer.Option("", "--party"),
    order: str = typer.Option("", "--order"),
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm a delivery rule for a customer or an order."""
    arguments = {"rule": rule, "reason": reason}
    if party:
        arguments["party_id"] = party
    if order:
        arguments["document_id"] = order
    _stock_block_change(
        "delivery_rule_set", arguments, tenant, yes, preview_key="delivery_rule"
    )
    con.print("✓ Delivery rule stated")


@backorder_app.command("promise")
def backorders_promise_command(item_id: str, tenant: str | None = None):
    """Available to promise: free now, then each open purchase by its date."""
    from reality.services.backorders import available_to_promise

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            answer = available_to_promise(s, selected.id, item_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=answer, default=str)


@stock_app.command("scrap")
def stock_block_scrap_command(
    block_id: str,
    reason: str = typer.Option(..., "--reason"),
    quantity: str = "",
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm scrapping blocked stock, wholly or partly."""
    arguments = {"block_id": block_id, "reason": reason}
    if quantity:
        arguments["quantity"] = quantity
    _stock_block_change("stock_block_scrap", arguments, tenant, yes)
    con.print("✓ Stock scrapped")


@reorder_point_app.command("list")
def reorder_point_list(
    item_id: str = "", location_id: str = "", tenant: str | None = None
):
    """List the stated reorder points."""
    from reality.services.reorder_points import reorder_points

    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = reorder_points(
            s, selected.id, item_id=item_id or None, location_id=location_id or None
        )
    con.print_json(data=rows, default=str)


def _reorder_point_change(tool: str, arguments: dict, tenant: str | None, yes: bool):
    from reality.tools.application import create_change_proposal, reject_proposal

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            proposal = create_change_proposal(
                s, selected.id, tool, arguments, actor_type="human"
            )
            con.print_json(data=json.loads(proposal.output)["reorder_point"])
            if not yes and not typer.confirm("Confirm this reorder point change?"):
                # A declined review leaves no decision waiting for anyone.
                reject_proposal(s, selected.id, proposal.id)
                con.print("Stopped; the reorder point is unchanged.")
                raise typer.Exit()
            approve_and_execute_proposal(s, selected.id, proposal.id, confirmed=True)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error


@reorder_point_app.command("set")
def reorder_point_set(
    item_id: str,
    location_id: str,
    point: str = typer.Option(..., "--point", help="Reorder point, stock unit."),
    quantity: str = typer.Option(..., "--quantity", help="Reorder quantity, stock unit."),
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm the reorder point and quantity of an item at a location."""
    _reorder_point_change(
        "reorder_point_set",
        {
            "item_id": item_id,
            "location_id": location_id,
            "reorder_point": point,
            "reorder_quantity": quantity,
        },
        tenant,
        yes,
    )
    con.print(f"✓ Reorder point set: {item_id} at {location_id}")


@reorder_point_app.command("remove")
def reorder_point_remove(
    item_id: str, location_id: str, tenant: str | None = None, yes: bool = False
):
    """Review and confirm removing the reorder point of an item at a location."""
    _reorder_point_change(
        "reorder_point_remove",
        {"item_id": item_id, "location_id": location_id},
        tenant,
        yes,
    )
    con.print(f"✓ Reorder point removed: {item_id} at {location_id}")


@kit_app.command("show")
def kit_show(item_id: str = "", tenant: str | None = None):
    """List the kits, or the kit an item is or is part of, with what each location builds."""
    from reality.services.kits import kits

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            rows = kits(s, selected.id, item_id=item_id or None)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=rows, default=str)


@kit_app.command("split")
def kit_split_show(document_line_id: str, tenant: str | None = None):
    """Show how a kit's order or invoice line splits across its components."""
    from reality.services.kits import kit_split

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            split = kit_split(s, selected.id, document_line_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=split, default=str)


def _kit_change(tool: str, arguments: dict, tenant: str | None, yes: bool):
    from reality.tools.application import create_change_proposal, reject_proposal

    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            proposal = create_change_proposal(
                s, selected.id, tool, arguments, actor_type="human"
            )
            con.print_json(data=json.loads(proposal.output)["kit"])
            if not yes and not typer.confirm("Confirm this kit change?"):
                # A declined review leaves no decision waiting for anyone.
                reject_proposal(s, selected.id, proposal.id)
                con.print("Stopped; nothing changed.")
                raise typer.Exit()
            approve_and_execute_proposal(s, selected.id, proposal.id, confirmed=True)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error


@kit_app.command("define")
def kit_define(
    kit_item_id: str,
    component: Annotated[
        list[str],
        typer.Option(
            "--component",
            help="ITEM_ID:QUANTITY or ITEM_ID:QUANTITY:SHARE, once per component.",
        ),
    ],
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm the components of a kit."""
    components = []
    for entry in component:
        parts = entry.split(":")
        if len(parts) not in (2, 3):
            raise typer.BadParameter("--component is ITEM_ID:QUANTITY[:SHARE]")
        components.append(
            {"item_id": parts[0], "quantity": parts[1]}
            | ({"share": parts[2]} if len(parts) == 3 else {})
        )
    _kit_change(
        "kit_define",
        {"kit_item_id": kit_item_id, "components": components},
        tenant,
        yes,
    )
    con.print(f"✓ Kit defined: {kit_item_id}")


@kit_app.command("assemble")
def kit_assemble(
    kit_item_id: str,
    location_id: str,
    quantity: str,
    occurred_at: str = typer.Option("", help="When it was assembled, ISO 8601 with offset."),
    note: str = "",
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm assembling whole kits at a location from their components."""
    arguments = {
        "kit_item_id": kit_item_id,
        "location_id": location_id,
        "quantity": quantity,
    }
    if occurred_at:
        arguments["occurred_at"] = occurred_at
    if note:
        arguments["note"] = note
    _kit_change("kit_assemble", arguments, tenant, yes)
    con.print(f"✓ Assembled: {quantity} × {kit_item_id} at {location_id}")


@payment_term_app.command("create")
def payment_term_create(
    code: str,
    name: str,
    due_days: int,
    tenant: str | None = None,
    source_system: str = "",
    external_id: str = "",
    discount_percent: str = "",
    discount_days: int = -1,
    requires_prepayment: bool = False,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            term = create_payment_term(
                s,
                selected.id,
                code,
                name,
                due_days,
                source_system=source_system,
                external_id=external_id,
                discount_percent=discount_percent or None,
                # A negative default is how "not stated" reaches a typed CLI
                # flag that cannot carry None.
                discount_days=None if discount_days < 0 else discount_days,
                requires_prepayment=requires_prepayment,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Payment term created: {term.code} ({term.id})")


@payment_term_app.command("list")
def payment_term_list(tenant: str | None = None):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            rows = payment_terms(s, selected.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    table = Table(
        "ID", "Code", "Name", "Due days", "Prepayment", "Discount", "Status"
    )
    for term in rows:
        table.add_row(
            term.id,
            term.code,
            term.name,
            str(term.due_days),
            "yes" if term.requires_prepayment else "no",
            "—"
            if term.discount_percent is None
            else f"{term.discount_percent.normalize():g}% / {term.discount_days}d",
            "active" if term.is_active else "inactive",
        )
    con.print(table)


def change_payment_term_active(
    payment_term_id: str, is_active: bool, tenant: str | None
) -> None:
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            term = set_master_data_active(
                s, selected.id, PaymentTerm, payment_term_id, is_active
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Payment term {'activated' if is_active else 'deactivated'}: "
        f"{term.code} ({term.id})"
    )


@payment_term_app.command("deactivate")
def payment_term_deactivate(payment_term_id: str, tenant: str | None = None):
    change_payment_term_active(payment_term_id, False, tenant)


@payment_term_app.command("activate")
def payment_term_activate(payment_term_id: str, tenant: str | None = None):
    change_payment_term_active(payment_term_id, True, tenant)


@pricing_app.command("list")
def pricing_list(tenant: str | None = None):
    with Session() as s:
        selected = selected_tenant(s, tenant)
        rows = price_lists(s, selected.id)
    table = Table("ID", "Code", "Direction", "Currency", "Default", "Status")
    for row in rows:
        table.add_row(
            row.id,
            row.code,
            row.direction,
            row.currency,
            "yes" if row.is_default else "",
            "active" if row.is_active else "inactive",
        )
    con.print(table)


@pricing_app.command("create-list")
def pricing_create_list(
    code: str,
    name: str,
    direction: str,
    currency: str,
    tenant: str | None = None,
    is_default: bool = False,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            row = create_price_list(
                s, selected.id, code, name, direction, currency, is_default=is_default
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Price list created: {row.code} ({row.id})")


@pricing_app.command("add-tier")
def pricing_add_tier(
    price_list_id: str,
    item_id: str,
    min_quantity: str,
    unit_price: str,
    unit: str,
    tenant: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            row = create_price_list_entry(
                s, selected.id, price_list_id, item_id, min_quantity, unit_price, unit
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Price tier created: {row.id}")


@pricing_app.command("assign-party")
def pricing_assign_party(
    party_id: str, price_list_id: str, priority: int = 100, tenant: str | None = None
):
    with Session() as s:
        selected = selected_tenant(s, tenant)
        row = assign_party_price_list(s, selected.id, party_id, price_list_id, priority)
    con.print(f"✓ Party price list assigned: {row.id}")


@pricing_app.command("create-group")
def pricing_create_group(code: str, name: str, tenant: str | None = None):
    with Session() as s:
        selected = selected_tenant(s, tenant)
        row = create_party_group(s, selected.id, code, name)
    con.print(f"✓ Pricing group created: {row.code} ({row.id})")


@pricing_app.command("add-group-member")
def pricing_add_group_member(
    party_group_id: str, party_id: str, tenant: str | None = None
):
    with Session() as s:
        selected = selected_tenant(s, tenant)
        row = add_party_group_member(s, selected.id, party_group_id, party_id)
    con.print(f"✓ Pricing group member added: {row.id}")


@pricing_app.command("assign-group")
def pricing_assign_group(
    party_group_id: str,
    price_list_id: str,
    priority: int = 100,
    tenant: str | None = None,
):
    with Session() as s:
        selected = selected_tenant(s, tenant)
        row = assign_group_price_list(
            s, selected.id, party_group_id, price_list_id, priority
        )
    con.print(f"✓ Group price list assigned: {row.id}")


@pricing_app.command("resolve")
def pricing_resolve(
    party_id: str,
    item_id: str,
    quantity: str,
    direction: str,
    currency: str,
    unit: str,
    tenant: str | None = None,
):
    with Session() as s:
        selected = selected_tenant(s, tenant)
        result = materialized_resolve_price(
            s, selected.id, party_id, item_id, quantity, direction, currency, unit
        )
    if result is None:
        raise typer.Exit("No applicable price found.")
    con.print(
        f"{result['unit_price']} {result['currency']}/{result['unit']} · "
        f"{result['source']} · entry {result['price_list_entry_id']}"
    )


@party_app.command("delivery-hold")
def party_delivery_hold(
    party_id: str,
    reason_code: str,
    note: str = "",
    tenant: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            hold = hold_party_delivery(
                s, selected.id, party_id, reason_code, note, created_by="cli"
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Customer delivery held: {hold.party_id} ({hold.reason_code})")


@party_app.command("release-delivery-hold")
def party_release_delivery_hold(party_id: str, tenant: str | None = None):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            released = release_party_delivery_hold(s, selected.id, party_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Released {len(released)} delivery hold(s): {party_id}")


@item_app.command("create")
def item_create(
    sku: str,
    name: str,
    unit: str = "pcs",
    tenant: str | None = None,
    source_system: str = "",
    external_id: str = "",
    item_type: str = "stocked",
    tracking_type: str = "none",
    default_location_id: str | None = None,
    purchase_unit: str | None = None,
    conversion_factor: str = "1",
    lead_time_days: int = 0,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            item = create_item(
                s,
                selected.id,
                sku,
                name,
                unit,
                source_system=source_system,
                external_id=external_id,
                item_type=item_type,
                tracking_type=tracking_type,
                default_location_id=default_location_id,
                purchase_unit=purchase_unit,
                conversion_factor=conversion_factor,
                lead_time_days=lead_time_days,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Item created: {item.name} · {item.sku} ({item.id})")


@item_app.command("update")
def item_update(
    item_id: str,
    sku: str,
    name: str,
    unit: str = "pcs",
    tenant: str | None = None,
    source_system: str | None = None,
    external_id: str | None = None,
    item_type: str | None = None,
    tracking_type: str | None = None,
    default_location_id: str | None = None,
    purchase_unit: str | None = None,
    conversion_factor: str | None = None,
    lead_time_days: int | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            item = update_item(
                s,
                selected.id,
                item_id,
                sku,
                name,
                unit,
                source_system=source_system,
                external_id=external_id,
                item_type=item_type,
                tracking_type=tracking_type,
                default_location_id=default_location_id,
                purchase_unit=purchase_unit,
                conversion_factor=conversion_factor,
                lead_time_days=lead_time_days,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Item updated: {item.name} · {item.sku} ({item.id})")


def change_item_active(item_id: str, is_active: bool, tenant: str | None) -> None:
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            item = set_master_data_active(s, selected.id, Item, item_id, is_active)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Item {'activated' if is_active else 'deactivated'}: {item.name} ({item.id})"
    )


@item_app.command("deactivate")
def item_deactivate(item_id: str, tenant: str | None = None):
    change_item_active(item_id, False, tenant)


@item_app.command("activate")
def item_activate(item_id: str, tenant: str | None = None):
    change_item_active(item_id, True, tenant)


@location_app.command("create")
def location_create(
    name: str,
    location_type: str = "warehouse",
    tenant: str | None = None,
    parent_location_id: str | None = None,
    allows_stock: bool = True,
    source_system: str = "",
    external_id: str = "",
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            location = create_location(
                s,
                selected.id,
                name,
                location_type,
                parent_location_id=parent_location_id,
                allows_stock=allows_stock,
                source_system=source_system,
                external_id=external_id,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Location created: {location.name} ({location.id})")


@location_app.command("update")
def location_update(
    location_id: str,
    name: str,
    location_type: str = "warehouse",
    tenant: str | None = None,
    parent_location_id: str | None = None,
    allows_stock: bool | None = None,
    source_system: str | None = None,
    external_id: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            location = update_location(
                s,
                selected.id,
                location_id,
                name,
                location_type,
                parent_location_id=parent_location_id,
                allows_stock=allows_stock,
                source_system=source_system,
                external_id=external_id,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Location updated: {location.name} ({location.id})")


def change_location_active(
    location_id: str, is_active: bool, tenant: str | None
) -> None:
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            location = set_master_data_active(
                s, selected.id, Location, location_id, is_active
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Location {'activated' if is_active else 'deactivated'}: "
        f"{location.name} ({location.id})"
    )


@location_app.command("deactivate")
def location_deactivate(location_id: str, tenant: str | None = None):
    change_location_active(location_id, False, tenant)


@location_app.command("activate")
def location_activate(location_id: str, tenant: str | None = None):
    change_location_active(location_id, True, tenant)


@commitment_app.command("hold")
def commitment_hold(
    commitment_id: str,
    reason_code: str,
    note: str = "",
    tenant: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            hold = hold_commitment(
                s, selected.id, commitment_id, reason_code, note, created_by="cli"
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Commitment held: {hold.commitment_id} ({hold.reason_code})")


@commitment_app.command("release-hold")
def commitment_release_hold(commitment_id: str, tenant: str | None = None):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            released = release_commitment_hold(s, selected.id, commitment_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Released {len(released)} hold(s): {commitment_id}")


@commitment_app.command("cancel")
def commitment_cancel(
    commitment_id: str,
    reason: str,
    tenant: str | None = None,
    yes: bool = False,
):
    """Review and confirm cancellation of a commitment's open remainder."""
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            proposal = prepare_delivery_action(
                s,
                selected.id,
                "commitment_cancel",
                {"commitment_id": commitment_id, "reason": reason},
                request_id=f"cli-commitment-cancel-{uuid4()}",
                actor_id="cli",
            )
            detail = delivery_proposal_detail(s, selected.id, proposal.id)
            con.print_json(data=detail["review"])
            if not yes and not typer.confirm("Cancel this commitment remainder?"):
                con.print("Cancellation stopped; the commitment remains open.")
                raise typer.Exit()
            approve_and_execute_proposal(
                s,
                selected.id,
                proposal.id,
                review_token=detail["review"]["token"],
                confirmed=True,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Commitment remainder cancelled: {commitment_id}")


@document_app.command("hold")
def document_hold(
    document_id: str,
    reason_code: str,
    note: str = "",
    tenant: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            holds = hold_document_commitments(
                s, selected.id, document_id, reason_code, note, created_by="cli"
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Document held through {len(holds)} commitment(s): {document_id}")


@document_app.command("release-holds")
def document_release_holds(document_id: str, tenant: str | None = None):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            released = release_document_holds(s, selected.id, document_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"✓ Released {len(released)} document hold(s): {document_id}")


@app.command()
def demo(tenant: str | None = None, auto: bool = False):
    with Session() as s:
        try:
            t = (
                selected_tenant(s, tenant)
                if tenant or read_current_tenant() or tenants(s)
                else create_tenant(s, "Acme Bikes GmbH")
            )
        except NotFound as error:
            raise typer.BadParameter(str(error), param_hint="--tenant") from error
        con.print(
            "[bold]Interactive demo[/bold]\nWe will create a small trading company with stock, a Shopify order, a customer promise, a reservation and a supplier promise."
        )
        if not auto:
            typer.confirm("Run the demo now?", abort=True)
        ensure_demo(s, t)
        con.print("✓ Demo company created. Try: reality stock")


@scenario_app.command("run")
def scenario_run(name: str, tenant: str = typer.Option(..., "--tenant")):
    if name != "normal-month":
        raise typer.BadParameter("Only normal-month is available.", param_hint="name")
    with Session() as s:
        try:
            get_tenant(s, tenant)
            result = run_normal_month(s, tenant)
        except NotFound as error:
            raise typer.BadParameter(str(error), param_hint="--tenant") from error
    con.print(
        "✓ September 2026 complete · "
        f"physical {result['physical']:g} · reserved {result['reserved']:g} · "
        f"receivable EUR {result['receivable']:g}"
    )


@app.command()
def stock(tenant: str | None = None):
    with Session() as s:
        try:
            t = selected_tenant(s, tenant)
        except NotFound as error:
            raise typer.BadParameter(str(error), param_hint="--tenant") from error
        tb = Table("Item", "Physical", "Reserved", "Available", "Incoming", "Projected")
        for x in inventory_rows(s, t.id):
            tb.add_row(
                x["item"].name,
                str(int(x["physical"])),
                str(int(x["reserved"])),
                str(int(x["available"])),
                str(int(x["incoming"])),
                str(int(x["projected"])),
            )
        con.print(tb)


@finance_app.command("open")
def finance_open(invoice_id: str, tenant: str | None = None):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            amount = open_invoice_amount(s, selected.id, invoice_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(f"{invoice_id} · open {amount:g}")


@finance_app.command("pay-customer")
def finance_pay_customer(
    invoice_id: str,
    amount: str,
    number: str | None = typer.Option(None, "--number"),
    tenant: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            entries = post_customer_payment(
                s, selected.id, invoice_id, amount, payment_number=number
            )
            open_amount = open_invoice_amount(s, selected.id, invoice_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Customer payment posted ({entries[0].posting_group_id}) · open {open_amount:g}"
    )


@finance_app.command("pay-supplier")
def finance_pay_supplier(
    invoice_id: str,
    amount: str,
    number: str | None = typer.Option(None, "--number"),
    paid: str | None = typer.Option(
        None, "--paid", help="What was paid in the company currency (spec 309)"
    ),
    tenant: str | None = None,
):
    with Session() as s:
        try:
            selected = selected_tenant(s, tenant)
            entries = post_supplier_payment(
                s,
                selected.id,
                invoice_id,
                amount,
                payment_number=number,
                paid_amount=paid,
            )
            open_amount = open_invoice_amount(s, selected.id, invoice_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print(
        f"✓ Supplier payment posted ({entries[0].posting_group_id}) · open {open_amount:g}"
    )


@app.command()
def web(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn

    con.print(f"Opening Reality at http://{host}:{port}")
    uvicorn.run("reality.web.app:app", host=host, port=port, reload=False)


@app.command("finance-adjustment-context")
def finance_adjustment_context(invoice_id: str, tenant_id: str | None = None) -> None:
    """Read a current invoice claim and reduction account configuration."""
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "finance.adjustment.context",
                {"invoice_id": invoice_id},
            )
        )


@app.command("supply-coverage")
def supply_coverage_command(
    supplier_commitment_id: str = "",
    customer_commitment_id: str = "",
    tenant_id: str | None = None,
) -> None:
    """Read explicit supplier-supply coverage without implying receipt."""
    from reality.services.supply_assignments import supply_coverage

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            result = supply_coverage(
                session,
                tenant.id,
                supplier_commitment_id=supplier_commitment_id or None,
                customer_commitment_id=customer_commitment_id or None,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("supply-assign-propose")
def supply_assign_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare a supply assignment for explicit confirmation."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "supply_assign",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("supply-assign-confirm")
def supply_assign_confirm(
    proposal_id: str,
    review_token: str,
    yes: bool = typer.Option(False, "--yes", help="Confirm the reviewed assignment."),
    tenant_id: str | None = None,
) -> None:
    """Explicitly confirm one reviewed supply assignment."""
    from reality.services.delivery_actions import delivery_proposal_detail
    from reality.tools.application import approve_and_execute_proposal

    if not yes:
        typer.confirm("Execute this exact reviewed supply assignment?", abort=True)
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            approve_and_execute_proposal(
                session,
                tenant.id,
                proposal_id,
                review_token=review_token,
                confirmed=True,
            )
            result = delivery_proposal_detail(session, tenant.id, proposal_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("return-disposition")
def return_disposition_command(
    return_movement_id: str,
    tenant_id: str | None = None,
) -> None:
    """Read resolved and unresolved quantity for arrived returned goods."""
    from reality.services.return_dispositions import return_disposition_summary

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            result = return_disposition_summary(session, tenant.id, return_movement_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("return-disposition-propose")
def return_disposition_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare one returned-goods outcome for explicit confirmation."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "return_disposition",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("return-disposition-confirm")
def return_disposition_confirm(
    proposal_id: str,
    review_token: str,
    yes: bool = typer.Option(False, "--yes", help="Confirm the reviewed disposition."),
    tenant_id: str | None = None,
) -> None:
    """Explicitly confirm one reviewed returned-goods outcome."""
    from reality.services.delivery_actions import delivery_proposal_detail
    from reality.tools.application import approve_and_execute_proposal

    if not yes:
        typer.confirm("Execute this exact reviewed return disposition?", abort=True)
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            approve_and_execute_proposal(
                session,
                tenant.id,
                proposal_id,
                review_token=review_token,
                confirmed=True,
            )
            result = delivery_proposal_detail(session, tenant.id, proposal_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("customer-exchange")
def customer_exchange_command(
    exchange_id: str | None = None,
    return_movement_id: str | None = None,
    replacement_commitment_id: str | None = None,
    tenant_id: str | None = None,
) -> None:
    """Read what a customer exchange replaced, sent and still settles."""
    from reality.services.customer_exchanges import customer_exchange_detail

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            result = customer_exchange_detail(
                session,
                tenant.id,
                exchange_id=exchange_id,
                return_movement_id=return_movement_id,
                replacement_commitment_id=replacement_commitment_id,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("customer-exchange-propose")
def customer_exchange_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare a replacement for returned goods for explicit confirmation."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "customer_exchange_record",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("customer-exchange-confirm")
def customer_exchange_confirm(
    proposal_id: str,
    review_token: str,
    yes: bool = typer.Option(False, "--yes", help="Confirm the reviewed exchange."),
    tenant_id: str | None = None,
) -> None:
    """Explicitly confirm one reviewed customer exchange."""
    from reality.services.delivery_actions import delivery_proposal_detail
    from reality.tools.application import approve_and_execute_proposal

    if not yes:
        typer.confirm("Execute this exact reviewed exchange?", abort=True)
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            approve_and_execute_proposal(
                session,
                tenant.id,
                proposal_id,
                review_token=review_token,
                confirmed=True,
            )
            result = delivery_proposal_detail(session, tenant.id, proposal_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("delivery-failure")
def delivery_failure_command(
    delivery_failure_id: str | None = None,
    shipment_id: str | None = None,
    tenant_id: str | None = None,
) -> None:
    """Read a failed delivery: what happened, what it reversed and its claim."""
    from reality.services.delivery_failures import delivery_failure_summary

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            result = delivery_failure_summary(
                session,
                tenant.id,
                delivery_failure_id=delivery_failure_id,
                shipment_id=shipment_id,
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("delivery-failure-propose")
def delivery_failure_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare recording an undeliverable, refused or lost shipment for confirmation."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "shipment_delivery_failure",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("delivery-failure-confirm")
def delivery_failure_confirm(
    proposal_id: str,
    review_token: str,
    yes: bool = typer.Option(False, "--yes", help="Confirm the reviewed failure."),
    tenant_id: str | None = None,
) -> None:
    """Explicitly confirm one reviewed failed delivery."""
    from reality.services.delivery_actions import delivery_proposal_detail
    from reality.tools.application import approve_and_execute_proposal

    if not yes:
        typer.confirm("Execute this exact reviewed failed delivery?", abort=True)
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            approve_and_execute_proposal(
                session,
                tenant.id,
                proposal_id,
                review_token=review_token,
                confirmed=True,
            )
            result = delivery_proposal_detail(session, tenant.id, proposal_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("drop-shipments")
def drop_shipments_command(commitment_id: str, tenant_id: str | None = None) -> None:
    """Read a promise's drop shipping: the purchase assigned and what shipped."""
    from reality.services.drop_shipping import drop_shipments

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            result = drop_shipments(session, tenant.id, commitment_id=commitment_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("drop-shipment-propose")
def drop_shipment_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare recording that a supplier shipped straight to the customer."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "drop_shipment_record",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("drop-shipment-confirm")
def drop_shipment_confirm(
    proposal_id: str,
    review_token: str,
    yes: bool = typer.Option(False, "--yes", help="Confirm the reviewed drop shipment."),
    tenant_id: str | None = None,
) -> None:
    """Explicitly confirm one reviewed drop shipment."""
    from reality.services.delivery_actions import delivery_proposal_detail
    from reality.tools.application import approve_and_execute_proposal

    if not yes:
        typer.confirm("Execute this exact reviewed drop shipment?", abort=True)
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            approve_and_execute_proposal(
                session,
                tenant.id,
                proposal_id,
                review_token=review_token,
                confirmed=True,
            )
            result = delivery_proposal_detail(session, tenant.id, proposal_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("order-line-item-assign-propose")
def order_line_item_assign_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare assigning an item to an order line whose SKU matched none."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "order_line_item_assign",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("credit-hold-release-propose")
def credit_hold_release_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare releasing an order's credit hold with a reason; an owner confirms."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "credit_hold_release",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("prepayment-release-propose")
def prepayment_release_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare shipping a prepayment order before it is paid; an owner confirms."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "prepayment_release",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("down-payment-invoice-record-propose")
def down_payment_invoice_record_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare a down-payment invoice for a sales order; a person confirms."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "down_payment_invoice_record",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("proforma-invoice-record-propose")
def proforma_invoice_record_propose(
    arguments: str,
    request_id: str,
    tenant_id: str | None = None,
) -> None:
    """Prepare a pro-forma invoice for a sales order; it posts nothing."""
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        prepare_delivery_action,
    )

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = prepare_delivery_action(
                session,
                tenant.id,
                "proforma_invoice_record",
                values,
                request_id=request_id,
                actor_id="cli",
            )
            result = delivery_proposal_detail(session, tenant.id, proposal.id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("month-end-billing")
def month_end_billing_read(
    as_of: str | None = None, tenant_id: str | None = None
) -> None:
    """List order lines shipped and not invoiced, and invoiced and not shipped."""
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            result = run_read_tool(
                session,
                tenant.id,
                "month_end_billing",
                {"as_of": as_of} if as_of else {},
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("credit-exposure")
def credit_exposure_read(party_id: str, tenant_id: str | None = None) -> None:
    """Read a customer's credit exposure against its limit."""
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            result = run_read_tool(
                session, tenant.id, "credit_exposure", {"party_id": party_id}
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("order-line-item-assign-confirm")
def order_line_item_assign_confirm(
    proposal_id: str,
    review_token: str,
    yes: bool = typer.Option(False, "--yes", help="Confirm the reviewed assignment."),
    tenant_id: str | None = None,
) -> None:
    """Explicitly confirm one reviewed item assignment."""
    from reality.services.delivery_actions import delivery_proposal_detail
    from reality.tools.application import approve_and_execute_proposal

    if not yes:
        typer.confirm("Execute this exact reviewed assignment?", abort=True)
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            approve_and_execute_proposal(
                session,
                tenant.id,
                proposal_id,
                review_token=review_token,
                confirmed=True,
            )
            result = delivery_proposal_detail(session, tenant.id, proposal_id)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
    con.print_json(data=result, default=str)


@app.command("finance-adjustment-propose")
def finance_adjustment_propose(arguments: str, tenant_id: str | None = None) -> None:
    """Prepare an explicit stated reduction for owner confirmation."""
    from reality.tools.application import create_change_proposal

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        proposal = create_change_proposal(
            session,
            tenant.id,
            "finance.adjustment.accept",
            json.loads(arguments),
            actor_type="human",
        )
        con.print_json(
            data={"proposal_id": proposal.id, "preview": json.loads(proposal.output)}
        )


def _finance_propose(tool: str, arguments: str, tenant_id: str | None) -> None:
    from reality.tools.application import create_change_proposal

    try:
        values = json.loads(arguments)
        if not isinstance(values, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as error:
        raise typer.BadParameter("Arguments must be a JSON object.") from error
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            proposal = create_change_proposal(
                session, tenant.id, tool, values, actor_type="human"
            )
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
        con.print_json(
            data={"id": proposal.id, "preview": json.loads(proposal.output)},
            default=str,
        )


def _finance_read(tool: str, arguments: dict, tenant_id: str | None) -> None:
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        try:
            result = run_read_tool(session, tenant.id, tool, arguments)
        except (NotFound, InvalidOperation) as error:
            raise typer.BadParameter(str(error)) from error
        con.print_json(data=result, default=str)


@app.command("finance-dunning-schedule")
def finance_dunning_schedule(tenant_id: str | None = None) -> None:
    """Read the company dunning schedule: waiting days and fee per level."""
    _finance_read("finance.dunning.schedule", {}, tenant_id)


@app.command("finance-dunning-schedule-propose")
def finance_dunning_schedule_propose(
    arguments: str, tenant_id: str | None = None
) -> None:
    """Prepare the company dunning schedule for owner confirmation."""
    _finance_propose("finance.dunning.schedule.set", arguments, tenant_id)


@app.command("finance-dunning-run-context")
def finance_dunning_run_context(
    run_date: str,
    party_id: Annotated[list[str] | None, typer.Option("--party-id")] = None,
    tenant_id: str | None = None,
) -> None:
    """Preview a dunning run: notices per customer and level, and items left out."""
    _finance_read(
        "finance.dunning.run_context",
        {"run_date": run_date, "party_ids": party_id or []},
        tenant_id,
    )


@app.command("finance-dunning-run-propose")
def finance_dunning_run_propose(arguments: str, tenant_id: str | None = None) -> None:
    """Prepare the reviewed dunning run for owner confirmation."""
    _finance_propose("finance.dunning.run", arguments, tenant_id)


@app.command("finance-dunning-collection-propose")
def finance_dunning_collection_propose(
    arguments: str, tenant_id: str | None = None
) -> None:
    """Prepare handing level-3 invoices to collection for owner confirmation."""
    _finance_propose("finance.dunning.collection.handover", arguments, tenant_id)


@app.command("finance-payment-return-propose")
def finance_payment_return_propose(arguments: str, tenant_id: str | None = None) -> None:
    """Prepare a returned direct debit or chargeback for owner confirmation."""
    _finance_propose("finance.payment.return", arguments, tenant_id)


@app.command("finance-payment-returns")
def finance_payment_returns(
    return_id: str | None = None, tenant_id: str | None = None
) -> None:
    """List returned customer payments, or read one by its identity."""
    if return_id:
        _finance_read("finance.payment_return", {"return_id": return_id}, tenant_id)
    else:
        _finance_read("finance.payment_returns", {}, tenant_id)


@app.command("finance-payout-settle-propose")
def finance_payout_settle_propose(
    arguments: str | None = None,
    file: Path | None = None,
    tenant_id: str | None = None,
) -> None:
    """Prepare a payout statement for owner confirmation, as JSON or from a JSON file."""
    if (arguments is None) == (file is None):
        raise typer.BadParameter("State the payout as arguments or as a file.")
    _finance_propose(
        "finance.payout.settle",
        arguments if arguments is not None else file.read_text(),
        tenant_id,
    )


@app.command("finance-payouts")
def finance_payouts(payout_id: str | None = None, tenant_id: str | None = None) -> None:
    """List payouts, or read one with every line and what it booked."""
    if payout_id:
        _finance_read("finance.payout", {"payout_id": payout_id}, tenant_id)
    else:
        _finance_read("finance.payouts", {}, tenant_id)


@app.command("finance-payment-authorization-propose")
def finance_payment_authorization_propose(
    arguments: str, tenant_id: str | None = None
) -> None:
    """Prepare a payment authorization of a sales order for owner confirmation."""
    _finance_propose("finance.payment.authorization.record", arguments, tenant_id)


@app.command("finance-payment-capture-propose")
def finance_payment_capture_propose(arguments: str, tenant_id: str | None = None) -> None:
    """Prepare a capture against a payment authorization for owner confirmation."""
    _finance_propose("finance.payment.capture.record", arguments, tenant_id)


@app.command("finance-payment-authorizations")
def finance_payment_authorizations(
    order_document_id: str | None = None, tenant_id: str | None = None
) -> None:
    """List payment authorizations with what was captured and what is left."""
    _finance_read(
        "finance.payment_authorizations",
        {"order_document_id": order_document_id} if order_document_id else {},
        tenant_id,
    )


@app.command("finance-dunning-collection")
def finance_dunning_collection(
    handover_id: str | None = None, tenant_id: str | None = None
) -> None:
    """List collection handovers, or read one by its identity."""
    if handover_id:
        _finance_read(
            "finance.dunning.collection_handover",
            {"handover_id": handover_id},
            tenant_id,
        )
    else:
        _finance_read("finance.dunning.collection_handovers", {}, tenant_id)


@app.command("finance-settlement-context")
def finance_settlement_context(
    document_id: str, query: str = "", tenant_id: str | None = None
) -> None:
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "finance.settlement.context",
                {"document_id": document_id, "query": query},
            )
        )


@app.command("finance-settlement-propose")
def finance_settlement_propose(arguments: str, tenant_id: str | None = None) -> None:
    from reality.tools.application import create_change_proposal

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        proposal = create_change_proposal(
            session,
            tenant.id,
            "finance.settlement.apply",
            json.loads(arguments),
            actor_type="human",
        )
        con.print_json(data={"id": proposal.id, "preview": json.loads(proposal.output)})


@app.command("finance-opening-context")
def finance_opening_context(query: str = "", tenant_id: str | None = None) -> None:
    """Read accounts and parties available to the opening import."""
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session, tenant.id, "finance.opening.context", {"query": query}
            )
        )


@app.command("finance-opening-propose")
def finance_opening_propose(arguments: str, tenant_id: str | None = None) -> None:
    """Prepare stated opening residuals for separate owner confirmation."""
    from reality.tools.application import create_change_proposal

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        proposal = create_change_proposal(
            session,
            tenant.id,
            "finance.opening.import",
            json.loads(arguments),
            actor_type="human",
        )
        con.print_json(data={"id": proposal.id, "preview": json.loads(proposal.output)})


@app.command("finance-accounts")
def finance_accounts(tenant_id: str | None = None) -> None:
    """Read the current permitted accounts and finance preview revision."""
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(session, tenant.id, "finance.accounts.list", {})
        )


@app.command("finance-account-propose")
def finance_account_propose(
    tool: str, arguments: str, tenant_id: str | None = None
) -> None:
    """Prepare a typed account change for owner confirmation in the application."""
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import ACCOUNT_COMMANDS

    if tool not in ACCOUNT_COMMANDS:
        raise typer.BadParameter("Unknown finance account command.")
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        proposal = create_change_proposal(
            session, tenant.id, tool, json.loads(arguments), actor_type="human"
        )
        con.print_json(
            data={"proposal_id": proposal.id, "preview": json.loads(proposal.output)}
        )


@app.command("finance-references")
def finance_references(
    kind: str | None = None,
    state: str | None = None,
    query: str = "",
    limit: int = 50,
    offset: int = 0,
    tenant_id: str | None = None,
) -> None:
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "finance.references.list",
                {
                    "kind": kind,
                    "state": state,
                    "query": query,
                    "limit": limit,
                    "offset": offset,
                },
            )
        )


@app.command("finance-reference-history")
def finance_reference_history(
    reference_id: str, limit: int = 50, offset: int = 0, tenant_id: str | None = None
) -> None:
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "finance.references.history",
                {"reference_id": reference_id, "limit": limit, "offset": offset},
            )
        )


@app.command("finance-reference-propose")
def finance_reference_propose(
    tool: str, arguments: str, tenant_id: str | None = None
) -> None:
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import REFERENCE_COMMANDS

    if tool not in REFERENCE_COMMANDS:
        raise typer.BadParameter("Unknown finance reference command.")
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        proposal = create_change_proposal(
            session, tenant.id, tool, json.loads(arguments), actor_type="human"
        )
        con.print_json(data={"id": proposal.id, "preview": json.loads(proposal.output)})


@app.command("finance-components")
def finance_components(
    document_id: str,
    limit: int = 50,
    offset: int = 0,
    reference_query: str = "",
    tenant_id: str | None = None,
) -> None:
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "finance.components.context",
                {
                    "document_id": document_id,
                    "limit": limit,
                    "offset": offset,
                    "reference_query": reference_query,
                },
            )
        )


@app.command("finance-component-history")
def finance_component_history(
    component_id: str, limit: int = 50, offset: int = 0, tenant_id: str | None = None
) -> None:
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "finance.component.history",
                {"component_id": component_id, "limit": limit, "offset": offset},
            )
        )


@app.command("finance-component-propose")
def finance_component_propose(arguments: str, tenant_id: str | None = None) -> None:
    from reality.tools.application import create_change_proposal

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        proposal = create_change_proposal(
            session,
            tenant.id,
            "finance.component.assign",
            json.loads(arguments),
            actor_type="human",
        )
        con.print_json(data={"id": proposal.id, "preview": json.loads(proposal.output)})


@app.command("finance-matrix")
def finance_matrix(tenant_id: str | None = None) -> None:
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(session, tenant.id, "finance.matrix.read", {})
        )


@app.command("finance-source-mappings")
def finance_source_mappings(
    query: str = "",
    source_query: str = "",
    reference_query: str = "",
    limit: int = 50,
    offset: int = 0,
    tenant_id: str | None = None,
) -> None:
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "finance.source_mappings.list",
                {
                    "query": query,
                    "source_query": source_query,
                    "reference_query": reference_query,
                    "limit": limit,
                    "offset": offset,
                },
            )
        )


@app.command("finance-source-mapping-history")
def finance_source_mapping_history(
    mapping_id: str, limit: int = 50, offset: int = 0, tenant_id: str | None = None
) -> None:
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "finance.source_mappings.history",
                {"mapping_id": mapping_id, "limit": limit, "offset": offset},
            )
        )


@app.command("finance-source-mapping-propose")
def finance_source_mapping_propose(
    arguments: str, tenant_id: str | None = None
) -> None:
    from reality.tools.application import create_change_proposal

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        proposal = create_change_proposal(
            session,
            tenant.id,
            "finance.source_mapping.set",
            json.loads(arguments),
            actor_type="human",
        )
        con.print_json(data={"id": proposal.id, "preview": json.loads(proposal.output)})


@app.command("finance-target-read")
def finance_target_read(
    tool: str = "finance.targets.list",
    arguments: str = "{}",
    tenant_id: str | None = None,
) -> None:
    from reality.tools.application import run_read_tool

    if tool not in {
        "finance.targets.list",
        "finance.target_references.list",
        "finance.target_mappings.list",
        "finance.target_mappings.history",
        "finance.target_mappings.preview",
    }:
        raise typer.BadParameter("Select a Finance target read tool.")
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(session, tenant.id, tool, json.loads(arguments))
        )


@app.command("finance-target-propose")
def finance_target_propose(
    tool: str, arguments: str, tenant_id: str | None = None
) -> None:
    from reality.domain.target_mappings import COMMANDS
    from reality.tools.application import create_change_proposal

    if tool not in COMMANDS:
        raise typer.BadParameter("Select a Finance target configuration command.")
    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        proposal = create_change_proposal(
            session, tenant.id, tool, json.loads(arguments), actor_type="human"
        )
        con.print_json(data={"id": proposal.id, "preview": json.loads(proposal.output)})


analytics_app = typer.Typer(help="Ask the Business Recorder and read its catalog.")
app.add_typer(analytics_app, name="analytics")

graph_app = typer.Typer(help="Ask the reporting graph a question.")
app.add_typer(graph_app, name="graph")


@graph_app.command("catalog")
def graph_catalog(node: str | None = None):
    """What can be asked: the nodes, how they connect, and what each number means."""
    from reality.services.analytics.graph_model import reporting_catalog

    con.print_json(data=reporting_catalog(node))


@graph_app.command("ask")
def graph_ask(
    query: Annotated[
        str | None, typer.Argument(help="A question in the path syntax.")
    ] = None,
    file: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    tenant: str | None = None,
    show_sql: bool = False,
):
    """Ask in the path syntax, or from a file holding either syntax.

    A refusal here is the product: it names the edge that fanned out, the unit
    that cannot be added, or the property that does not exist.
    """
    from reality.domain.traversal import Traversal
    from reality.services.analytics.cypher_surface import parse
    from reality.services.analytics.traversal import TraversalRefused, run_traversal

    if (query is None) == (file is None):
        raise typer.BadParameter("give a question, or a file holding one")
    text = query if query is not None else file.read_text()
    asked = (
        Traversal.model_validate(json.loads(text))
        if text.lstrip().startswith("{")
        else parse(text)
    )
    with Session() as session:
        selected = selected_tenant(session, tenant)
        try:
            result = run_traversal(session, selected.id, asked)
        except TraversalRefused as refusal:
            con.print(f"[red]Refused.[/red] {refusal}")
            raise typer.Exit(code=1) from refusal
    if show_sql:
        con.print(result.sql)
    if not result.rows:
        con.print("[dim]No rows.[/dim]")
        return
    table = Table(*result.rows[0].keys())
    for row in result.rows:
        table.add_row(*("—" if value is None else str(value) for value in row.values()))
    con.print(table)
    con.print(
        f"[dim]{len(result.rows)} rows · model {result.model_version} · "
        f"{result.statements} statement[/dim]"
    )


@app.command("cost-record")
def cost_record_read(
    kind: str,
    record_id: str,
    tenant_id: str | None = None,
    page: int = 1,
    language: str = "en",
) -> None:
    """Inspect retained cost evidence and page its exact review membership."""
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "cost.record.get",
                {
                    "kind": kind,
                    "record_id": record_id,
                    "page": page,
                    "language": language,
                },
            )
        )


@app.command("cost-query")
def cost_query_read(
    kind: str,
    scope_id: str,
    tenant_id: str | None = None,
    review_id: str | None = None,
    effective_at: str | None = None,
    knowledge_at: str | None = None,
    policy_revision_id: str | None = None,
) -> None:
    """Read a bounded costing answer together with its constrained retained basis."""
    from reality.tools.application import run_read_tool

    with Session() as session:
        tenant = selected_tenant(session, tenant_id)
        con.print_json(
            data=run_read_tool(
                session,
                tenant.id,
                "cost.query.get",
                {
                    "kind": kind,
                    "scope_id": scope_id,
                    "review_id": review_id,
                    "effective_at": effective_at,
                    "knowledge_at": knowledge_at,
                    "policy_revision_id": policy_revision_id,
                },
            )
        )


if __name__ == "__main__":
    app()
