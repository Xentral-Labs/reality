"""Pure meaning for the existing bounded artifact profiles (spec 358)."""

import hashlib
import json
from collections import defaultdict

from reality.domain.intake import (
    PACKAGE_ROWS,
    Effect,
    ObservationState,
    PreparedIntake,
    content_digest,
)
from reality.domain.intake_completeness import is_unstated, order_issues
from reality.services import core
from reality.services.artifacts import get_artifact, materialize_artifact
from reality.services.file_intake import RAW_BYTES, parse_item_csv
from reality.services.file_interpreters import (
    FILE_MAPPING_PROFILES,
    _item,
    _location,
    _mapped_row,
    _party,
    _rows,
    _single_company,
    _stated_price,
    _value,
    validate_mapping,
)


def _prepare_artifact(session, tenant_id, source, job):
    from reality.db.core import ImportJob, SourceRecord
    from reality.services.intake import _payment_state, _reference, _stock_state

    source = core._tenant_record_read(session, SourceRecord, tenant_id, source.id)
    job = core._tenant_record_read(session, ImportJob, tenant_id, job.id)
    context = json.loads(job.input)
    target = context.get("expected_target")
    if target not in FILE_MAPPING_PROFILES:
        raise core.InvalidOperation(code="intake_profile_unsupported")
    artifact, rows = _artifact_rows(session, tenant_id, source, context)
    if not 1 <= len(rows) <= PACKAGE_ROWS:
        raise core.InvalidOperation(code="intake_package_too_large")
    mapping = context.get("column_mapping") or {}
    if mapping:
        validate_mapping(target, mapping)
    rows = [_mapped_row(row, mapping) for row in rows]
    refs = {("source_artifact", artifact.id)}
    observations, effects, issues = [], [], []
    if target == "item":
        from reality.services.item_imports import _validate_new_rows

        _validate_new_rows(
            session,
            tenant_id,
            [
                {
                    "sku": str(_value(row, "sku")).strip(),
                    "name": str(_value(row, "name")).strip(),
                    "unit": str(row.get("unit") or "pcs").strip(),
                }
                for row in rows
            ],
        )
        for row in rows:
            effects.append(
                Effect(
                    operation="master_item",
                    arguments={
                        "sku": str(_value(row, "sku")).strip(),
                        "name": str(_value(row, "name")).strip(),
                        "unit": str(row.get("unit") or "pcs").strip(),
                        "item_type": str(row.get("item_type") or "stocked"),
                        "tracking_type": str(row.get("tracking_type") or "none"),
                        "purchase_unit": str(
                            row.get("purchase_unit") or row.get("unit") or "pcs"
                        ),
                        "conversion_factor": row.get("conversion_factor") or "1",
                        "lead_time_days": int(row.get("lead_time_days") or 0),
                        "source_record_id": source.id,
                    },
                )
            )
    elif target == "party":
        for row in rows:
            party_type = str(row.get("party_type") or row.get("type") or "customer")
            term_code = str(row.get("payment_term_code") or "")
            if term_code:
                refs.add(
                    (
                        "payment_term",
                        core.payment_term_by_code(session, tenant_id, term_code).id,
                    )
                )
            effects.append(
                Effect(
                    operation="master_party",
                    arguments={
                        "name": str(_value(row, "name")),
                        "party_type": party_type,
                        "roles": [
                            value.strip()
                            for value in str(row.get("roles") or party_type).split(",")
                            if value.strip()
                        ],
                        "accounting_code": str(row.get("accounting_code") or ""),
                        "payment_term_code": term_code,
                        "default_currency": str(row.get("default_currency") or "EUR"),
                        "credit_limit": row.get("credit_limit") or "0",
                        "tax_identifier": str(row.get("tax_identifier") or ""),
                        "source_record_id": source.id,
                    },
                )
            )
    elif target == "location":
        for row in rows:
            effects.append(
                Effect(
                    operation="master_location",
                    arguments={
                        "name": str(_value(row, "name")),
                        "location_type": str(row.get("location_type") or "warehouse"),
                        "allows_stock": str(row.get("allows_stock") or "true")
                        .strip()
                        .lower()
                        in {"1", "true", "yes", "y"},
                        "source_record_id": source.id,
                    },
                )
            )
    elif target in {"inventory_snapshot", "external_stock"}:
        seen = set()
        for row in rows:
            item = _item(session, tenant_id, str(_value(row, "sku")).strip())
            location = _location(
                session, tenant_id, str(_value(row, "location")).strip()
            )
            refs.update({("item", item.id), ("location", location.id)})
            quantity = core.decimal(_value(row, "quantity"))
            if target == "inventory_snapshot":
                if (item.id, location.id) in seen:
                    raise core.InvalidOperation(code="intake_review_invalid")
                seen.add((item.id, location.id))
                state = _stock_state(session, tenant_id, item.id, location.id)
                observations.append(
                    ObservationState(
                        kind="stock_state",
                        arguments={"item_id": item.id, "location_id": location.id},
                        digest=content_digest(state),
                    )
                )
                delta = quantity - core.decimal(state["quantity"])
                if delta:
                    effects.append(
                        Effect(
                            operation="inventory_adjustment",
                            arguments={
                                "movement_type": "adjustment",
                                "item_id": item.id,
                                "quantity": str(abs(delta)),
                                "to_location_id": location.id if delta > 0 else None,
                                "from_location_id": location.id if delta < 0 else None,
                                "source_record_id": source.id,
                                "reason": "Imported inventory snapshot",
                            },
                        )
                    )
                issues.append(
                    f"Source states stock {quantity}; reviewed book stock {state['quantity']}."
                )
            else:
                from reality.services.external_stock import _checked_lines

                reporter = (
                    _party(session, tenant_id, row).id
                    if row.get("party_accounting_code") or row.get("party_name")
                    else None
                )
                if reporter:
                    refs.add(("party", reporter))
                line = _checked_lines(
                    session,
                    tenant_id,
                    [
                        {
                            "item_id": item.id,
                            "location_id": location.id,
                            "quantity": str(quantity),
                            "stated_at": _value(row, "stated_at", None) or None,
                        }
                    ],
                    source.received_at,
                )[0]
                effects.append(
                    Effect(
                        operation="external_stock_statement",
                        arguments={
                            "source_record_id": source.id,
                            "reporter_party_id": reporter,
                            "lines": [
                                {
                                    "item_id": item.id,
                                    "location_id": location.id,
                                    "quantity": str(line["quantity"]),
                                    "stated_at": line["stated_at"].isoformat(),
                                }
                            ],
                        },
                    )
                )
    elif target == "bank_statement":
        from reality.services.finance.accounts import resolve_account

        for number, row in enumerate(rows, 2):
            party = _party(session, tenant_id, row)
            direction = core._required_source_field(
                row.get("direction"), "direction"
            ).lower()
            currency = core._required_source_field(
                _value(row, "currency", None), "currency"
            )
            effective_text = core._required_source_field(
                _value(row, "effective_at", None), "effective_at"
            )
            if direction not in {"incoming", "outgoing"}:
                raise core.InvalidOperation(code="intake_review_invalid")
            outgoing = direction == "outgoing"
            control = resolve_account(
                session,
                tenant_id,
                "accounts_payable" if outgoing else "accounts_receivable",
            )
            cash = resolve_account(session, tenant_id, "cash")
            refs.update(
                {("party", party.id), ("account", control.id), ("account", cash.id)}
            )
            effective = core.utc_datetime(effective_text)
            effects.append(
                Effect(
                    operation="supplier_payment" if outgoing else "customer_payment",
                    arguments={
                        "party_id": party.id,
                        "amount": str(core.positive(_value(row, "amount"), "amount")),
                        "currency": currency,
                        "payment_number": str(
                            row.get("payment_number")
                            or _value(row, "external_id")
                            or f"{source.id}:{number}"
                        ),
                        "source_record_id": source.id,
                        "effective_at": effective.isoformat(),
                        "_control_account_id": control.id,
                        "_cash_account_id": cash.id,
                    },
                )
            )
        observations.append(
            ObservationState(
                kind="payment_state",
                arguments={"invoice_id": ""},
                digest=content_digest(_payment_state(session, tenant_id, "")),
            )
        )
        issues.append(
            "Received statements only; no bank transfer is executed and no invoice allocation is inferred."
        )
    elif target == "sales_order":
        company = _single_company(session, tenant_id)
        refs.add(("party", company.id))
        grouped = defaultdict(list)
        for number, row in enumerate(rows, 2):
            identity = str(row.get("order_id") or row.get("order_number") or "").strip()
            if not identity:
                raise core.InvalidOperation(code="intake_review_invalid")
            grouped[identity].append((number, row))
        for identity, members in grouped.items():
            first = members[0][1]
            party = _party(session, tenant_id, first)
            location = _location(
                session, tenant_id, str(_value(first, "location")).strip()
            )
            currency = core._required_source_field(
                _value(first, "currency", None), "currency"
            )
            header = {}
            for field in ("document_date", "ordered_at"):
                stated_values = {
                    str(row[field]).strip()
                    for _, row in members
                    if not is_unstated(row.get(field))
                }
                if len(stated_values) > 1:
                    raise core.InvalidOperation(
                        code="source_order_header_conflict", values={"field": field}
                    )
                header[field] = next(iter(stated_values), None)
            document_date = (
                core._document_day(header["document_date"])
                if header["document_date"] is not None
                else core._source_document_day(session, tenant_id, header["ordered_at"])
            )
            refs.update({("party", party.id), ("location", location.id)})
            total_values = {
                str(row.get("order_amount"))
                for _, row in members
                if row.get("order_amount") not in (None, "")
            }
            if len(total_values) > 1:
                raise core.InvalidOperation(code="intake_review_invalid")
            total = next(iter(total_values), None)
            if total is None:
                issues.append(f"Order {identity}: the source states no order total.")
            lines, commitments = [], []
            for index, (number, row) in enumerate(members):
                if (
                    _party(session, tenant_id, row).id != party.id
                    or _location(
                        session, tenant_id, str(_value(row, "location")).strip()
                    ).id
                    != location.id
                    or core._required_source_field(
                        _value(row, "currency", None), "currency"
                    )
                    != currency
                ):
                    raise core.InvalidOperation(code="intake_review_invalid")
                sku = str(_value(row, "sku") or "").strip()
                quoted = str(_value(row, "customer_item_number") or "").strip()
                from reality.services.customer_item_numbers import resolve_customer_item

                mapped = (
                    resolve_customer_item(session, tenant_id, party.id, quoted)
                    if quoted
                    else None
                )
                if quoted:
                    observations.append(
                        ObservationState(
                            kind="customer_item_resolution",
                            arguments={"party_id": party.id, "number": quoted},
                            digest=content_digest(
                                {
                                    "mapping_id": mapped.id if mapped else None,
                                    "item_id": mapped.item_id if mapped else None,
                                }
                            ),
                        )
                    )
                    if mapped:
                        refs.add(("customer_item_number", mapped.id))
                item = (
                    _item(session, tenant_id, sku)
                    if sku or not quoted
                    else core._tenant_record_read(
                        session, core.Item, tenant_id, mapped.item_id
                    )
                    if mapped
                    else None
                )
                if item and mapped and item.id != mapped.item_id:
                    raise core.InvalidOperation(
                        code="customer_item_number_conflicts_with_item"
                    )
                if item:
                    refs.add(("item", item.id))
                quantity = core.positive(_value(row, "quantity"), "quantity")
                price = _stated_price(row)
                stated_amount = row.get("line_amount")
                amount = (
                    str(core.decimal(stated_amount))
                    if stated_amount not in (None, "")
                    else None
                )
                unit = str(row.get("unit") or (item.unit if item else "pcs"))
                if item:
                    core._validate_sales_stock_unit(item, unit)
                lines.append(
                    {
                        "item_id": item.id if item else None,
                        "sku": item.sku if item else quoted,
                        "description": str(
                            _value(row, "name", item.name if item else quoted)
                        ),
                        "quantity": str(quantity),
                        "unit_price": str(price) if price is not None else None,
                        "gross_amount": amount,
                        "unit": unit,
                        "source_line_id": str(row.get("line_id") or number),
                        "customer_item_number": quoted if item and quoted else None,
                    }
                )
                if item:
                    commitments.append(
                        Effect(
                            operation="commitment",
                            arguments={
                                "line_index": index,
                                "commitment_type": "customer_delivery",
                                "from_party_id": company.id,
                                "to_party_id": party.id,
                                "item_id": item.id,
                                "quantity": str(quantity),
                                "_unit": unit,
                                "amount": amount,
                                "currency": currency,
                                "due_at": row.get("requested_delivery_at") or None,
                                "location_id": location.id,
                            },
                        )
                    )
            effects.append(
                Effect(
                    operation="document",
                    arguments={
                        "document_type": "sales_order",
                        "number": str(first.get("order_number") or identity),
                        "party_id": party.id,
                        "lines": lines,
                        "gross_amount": total,
                        "currency": currency,
                        "source_record_id": source.id,
                        "document_date": document_date,
                        "ordered_at": header["ordered_at"],
                        "requested_delivery_at": first.get("requested_delivery_at")
                        or None,
                        "customer_reference": str(
                            first.get("customer_reference") or ""
                        ),
                        "sales_channel": source.source_system,
                        "_source_line_payloads": [row for _, row in members],
                    },
                )
            )
            issues.extend(order_issues(effects[-1].arguments, lines))
            effects.extend(commitments)
            if party.credit_limit > 0 and commitments:
                from reality.services.credit_exposure import credit_exposure

                as_of = core.now().isoformat()
                current = credit_exposure(
                    session, tenant_id, party.id, as_of=core.utc_datetime(as_of)
                )
                observations.append(
                    ObservationState(
                        kind="credit_exposure",
                        arguments={"party_id": party.id, "as_of": as_of},
                        digest=content_digest(current),
                    )
                )
                unknown = any(
                    line["unit_price"] is None or line["gross_amount"] is None
                    for line in lines
                )
                stated = sum(
                    (
                        core.decimal(line["gross_amount"])
                        for line in lines
                        if line["gross_amount"] is not None
                    ),
                    core.ZERO,
                )
                if (
                    unknown
                    or current["open_orders"]["unpriced"]
                    or (current["exposure"] + stated > party.credit_limit)
                    or currency != party.default_currency
                ):
                    issues.append("credit_check_required")
                    effects.append(
                        Effect(
                            operation="credit_hold",
                            arguments={
                                "commitment_indices": list(range(len(commitments))),
                                "note": "Reviewed file order requires a credit decision: exposure is incomplete, above the limit or in another currency.",
                                "facts": {
                                    "reviewed_exposure": current,
                                    "source_stated_order_amount": total,
                                    "order_currency": currency,
                                },
                            },
                        )
                    )
    return PreparedIntake(
        tenant_id=tenant_id,
        source_record_id=source.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        import_job_id=job.id,
        profile=f"artifact:{target}.v1",
        mapping=context,
        references=tuple(
            _reference(session, tenant_id, kind, identity)
            for kind, identity in sorted(refs)
        ),
        observations=tuple(observations),
        effects=tuple(effects),
        issues=tuple(issues),
        row_count=len(rows),
    )


def _artifact_rows(session, tenant_id, source, context):
    from reality.services.artifact_batches import _cached_rows

    cached = _cached_rows(session, source, context)
    if cached is not None:
        return cached
    artifact = get_artifact(session, tenant_id, source.source_artifact_id or "")
    if not 0 < artifact.byte_size <= RAW_BYTES:
        raise core.InvalidOperation(code="intake_file_size_invalid")
    with materialize_artifact(artifact) as path:
        content = path.read_bytes()
        if (
            len(content) != artifact.byte_size
            or hashlib.sha256(content).hexdigest() != artifact.sha256
        ):
            raise core.InvalidOperation(code="item_import_file_hash_mismatch")
        if (
            artifact.filename.lower().endswith((".csv", ".tsv"))
            or "csv" in artifact.content_type
        ):
            _, rows = parse_item_csv(content)
        else:
            rows = list(_rows(path, artifact.content_type, artifact.filename))
    numbers = context.get("row_numbers")
    if numbers is not None:
        if (
            not numbers
            or len(set(numbers)) != len(numbers)
            or any(
                not isinstance(number, int) or not 2 <= number < len(rows) + 2
                for number in numbers
            )
        ):
            raise core.InvalidOperation(code="intake_review_invalid")
        rows = [rows[number - 2] for number in numbers]
    return artifact, rows
