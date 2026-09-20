"""Read fixed retained cost records and exact child membership, never derived state."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import Base
from reality.domain.cost_records import RECORDS, CostRecordRead
from reality.services import core

# Only immutable, owned memberships are reverse-listed, not live related history.
CHILDREN = {
    "cost_attribution_revision": (
        ("cost_attribution_part", "attribution_revision_id"),
        ("cost_selling_attribution_part", "attribution_revision_id"),
    ),
    "cost_input_manifest": tuple(
        (kind, "manifest_id")
        for kind in (
            "cost_manifest_attribution",
            "cost_manifest_component",
            "cost_manifest_correction",
            "cost_manifest_receipt",
            "cost_manifest_replacement",
        )
    ),
    "cost_scope_review": (("cost_scope_review_category", "review_id"),),
    "cost_inventory_review": (("cost_inventory_member", "review_id"),),
    "cost_valuation_assessment_revision": (
        ("cost_valuation_assessment_part", "assessment_revision_id"),
    ),
    "cost_contribution_review": (
        ("cost_selling_review_category", "review_id"),
        ("cost_selling_review_member", "review_id"),
    ),
    "cost_company_census": tuple(
        (kind, "census_id")
        for kind in (
            "cost_company_census_document",
            "cost_company_census_line",
            "cost_company_census_movement",
            "cost_company_census_source",
        )
    ),
    "cost_captured_basis": (
        ("cost_captured_contribution_basis", "basis_id"),
        ("cost_captured_inventory_basis", "basis_id"),
    ),
    "cost_company_manifest": (
        ("cost_company_contribution_input", "manifest_id"),
        ("cost_company_inventory_input", "manifest_id"),
    ),
}
EXTERNAL = {
    "document",
    "document_line",
    "source_record",
    "business_event",
    "movement",
    "party",
    "item",
}
GERMAN_FIELDS = {
    "id": "Datensatz-ID",
    "reason": "Begründung",
    "revision": "Revision",
    "category": "Kostenart",
    "disposition": "Prüfergebnis",
    "source_share": "Beleganteil",
    "cost_effect": "Kostenwirkung",
    "assignment_kind": "Zuordnungsart",
    "base_quantity": "Basismenge",
    "base_unit": "Basiseinheit",
    "quantity": "Menge",
    "stated_net": "Belegter Nettobetrag",
    "stated_tax": "Belegter Steuerbetrag",
    "stated_gross": "Belegter Bruttobetrag",
    "stated_base": "Belegter Basisbetrag",
    "currency": "Währung",
    "method": "Bewertungsmethode",
    "profile": "Deckungsbeitragsprofil",
    "economic_at": "Wirtschaftlicher Zeitpunkt",
    "effective_at": "Bewertungsstichtag",
    "knowledge_at": "Kenntnisstand",
    "history_start": "Beginn der Bestandshistorie",
    "occurred_at": "Bewegungszeitpunkt",
    "created_at": "Aufgezeichnet am",
    "decided_at": "Entschieden am",
    "sealed_at": "Abgeschlossen am",
    "completed_at": "Abgeschlossen am",
    "state": "Aufgezeichneter Status",
    "status": "Aufgezeichneter Status",
    "tax_treatment": "Steuerbehandlung",
    "nonrecoverable_tax_amount": "Nicht abziehbare Vorsteuer",
    "acquisition_cost": "Belegte Anschaffungskosten",
    "assessed_value": "Belegter Bewertungsbetrag",
    "kind": "Bewertungsart",
    "from_code": "Ausgangseinheit oder -währung",
    "to_code": "Zieleinheit oder -währung",
    "numerator": "Belegter Zähler",
    "denominator": "Belegter Nenner",
    "invoice_date": "Rechnungsdatum",
    "sales_channel": "Vertriebskanal",
    "content_hash": "Prüfsumme",
    "evidence_hash": "Belegprüfsumme",
    "recorded": "Aufgezeichnet",
}


def _value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _label(field: str, german: bool) -> str:
    return (
        GERMAN_FIELDS.get(field, field.replace("_", " ").title())
        if german
        else field.replace("_", " ").title()
    )


def _existing(session: Session, tenant: str, kind: str, identity: str) -> bool:
    table = Base.metadata.tables[kind]
    return (
        session.scalar(
            select(table.c.id).where(
                table.c.tenant_id == tenant, table.c.id == identity
            )
        )
        is not None
    )


def _members(
    session: Session,
    tenant: str,
    kind: str,
    identity: str,
    requested: int,
    german: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    definitions = []
    total = 0
    for child, column in sorted(CHILDREN.get(kind, ())):
        table = Base.metadata.tables[child]
        conditions = (table.c.tenant_id == tenant, table.c[column] == identity)
        count = (
            session.scalar(select(func.count()).select_from(table).where(*conditions))
            or 0
        )
        definitions.append((child, table, conditions, count))
        total += count
    pages = max(1, (total + 24) // 25)
    page = min(requested, pages)
    skip = (page - 1) * 25
    rows = []
    for child, table, conditions, count in definitions:
        if skip >= count:
            skip -= count
            continue
        for child_id in session.scalars(
            select(table.c.id)
            .where(*conditions)
            .order_by(table.c.id)
            .offset(skip)
            .limit(25 - len(rows))
        ):
            rows.append(
                {
                    "label": RECORDS[child]["labels"][int(german)],
                    "value": child_id,
                    "link": {"kind": child, "id": child_id},
                }
            )
        skip = 0
        if len(rows) == 25:
            break
    return rows, {
        "number": page,
        "size": 25,
        "total": total,
        "pages": pages,
        "has_previous": page > 1,
        "has_next": page < pages,
    }


def _read(
    session: Session,
    tenant: str,
    kind: str,
    record_id: str,
    *,
    page: int = 1,
    language: str = "en",
) -> dict[str, Any]:
    try:
        request = CostRecordRead(
            kind=kind, record_id=record_id, page=page, language=language
        )
    except ValidationError as error:
        raise core.InvalidOperation(str(error)) from error
    kind, record_id = request.kind, request.record_id
    with session.no_autoflush:
        core.get_tenant(session, tenant)
        if request.kind not in RECORDS:
            raise core.NotFound("Cost record not found.")
        definition = RECORDS[request.kind]
        table = Base.metadata.tables[request.kind]
        row = (
            session.execute(
                select(*(table.c[f] for f in definition["fields"])).where(
                    table.c.tenant_id == tenant, table.c.id == request.record_id
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            raise core.NotFound("Cost record not found.")
        german = language == "de"
        recorded = []
        links = []
        for field, value in row.items():
            entry = {
                "label": _label(field, german),
                "value": _value(value),
                "link": None,
            }
            if isinstance(value, datetime):
                entry["display_parts"] = [{"type": "datetime", "value": _value(value)}]
            targets = {
                fk.column.table.name
                for fk in table.c[field].foreign_keys
                if fk.column.name == "id"
            }
            targets &= set(RECORDS) | EXTERNAL
            if value is not None and len(targets) == 1:
                target = next(iter(targets))
                if not _existing(session, tenant, target, value):
                    raise core.NotFound("Cost record not found.")
                entry["link"] = {"kind": target, "id": value}
                links.append(entry)
            else:
                recorded.append(entry)
        children, member_page = _members(session, tenant, kind, record_id, page, german)
        title = definition["labels"][int(german)]
        return {
            "kind": kind,
            "id": record_id,
            "title": title,
            "subtitle": record_id,
            "status": "recorded",
            "eyebrow": "Kostennachweis" if german else "Cost evidence",
            "meaning": (
                "Festgehaltener Datensatz. Dies bestätigt keine aktuelle Kostenabdeckung."
                if german
                else "Retained record. This does not establish current cost completeness."
            ),
            "business_reference": None,
            "guidance": None,
            "metrics": [],
            "trail": [],
            "technical_rows": [],
            "events": [],
            "source_payload": None,
            "fields": {field: _value(value) for field, value in row.items()},
            "sections": [
                {
                    "title": "Aufgezeichnete Werte" if german else "Recorded values",
                    "rows": recorded,
                },
                {
                    "title": "Verknüpfte Datensätze" if german else "Linked records",
                    "rows": links,
                },
                {
                    "title": "Zugehörige Einträge" if german else "Retained members",
                    "rows": children,
                },
            ],
            "member_page": member_page,
            "persistence": {"business_writes": False, "projection_writes": False},
        }
