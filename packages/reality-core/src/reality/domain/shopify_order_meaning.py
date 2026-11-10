"""One explicit GraphQL order proposal builder, shared by native and old99."""

from reality.domain.intake import Effect, PreparedIntake, ReferenceState, content_digest
from reality.domain.shopify_order_proposal import ACTION_TYPE
from reality.integrations.shopify.graphql import project_order


def build_explicit_order_plan(
    binding: dict, raw: dict, bundle: dict, references: tuple[ReferenceState, ...]
) -> tuple[PreparedIntake, list[dict[str, str]]]:
    """Read received values; missing final price/date evidence remains unknown."""
    received = project_order(raw, binding["external_id"])
    selected = {line["source_line_id"]: line for line in bundle["lines"]}
    source_lines = received["line_items"]
    if len(source_lines) > 100 or set(selected) != {
        line["id"] for line in source_lines
    }:
        raise ValueError("complete_explicit_line_selection_required")
    lines = []
    promises = []
    prices = []
    issues = [
        "final_unit_price_not_interpreted",
        "line_total_not_interpreted",
        "delivery_date_not_interpreted",
        "business_calendar_not_interpreted",
        "credit_assessment_not_performed",
        "acceptance_not_implemented",
    ]
    for index, line in enumerate(source_lines):
        choice = selected[line["id"]]
        if choice["source_sku"] != line["sku"]:
            raise ValueError("source_sku_mismatch")
        if (
            choice["source_sku"] != choice["item_sku"]
            and "item_sku_differs" not in issues
        ):
            issues.append("item_sku_differs")
        quantity = str(line["quantity"])
        lines.append(
            {
                "source_line_id": line["id"],
                "item_id": choice["item_id"],
                "sku": line["sku"],
                "description": line["name"],
                "quantity": quantity,
                "unit_price": None,
                "gross_amount": None,
                "promised_at": "",
                "unit": choice["stock_unit"],
                "line_type": {
                    "stocked": "item",
                    "service": "service",
                    "charge": "charge",
                }[choice["item_type"]],
            }
        )
        prices.append(
            {
                "source_line_id": line["id"],
                "kind": "observed_original_unit_price_only",
                "amount": line["price"],
                "currency": received["currency"],
            }
        )
        if (
            line["requires_shipping"]
            and choice["item_type"] != "stocked"
            and "shipping_item_type_requires_review" not in issues
        ):
            issues.append("shipping_item_type_requires_review")
        if (
            not line["requires_shipping"]
            and choice["item_type"] == "stocked"
            and "non_shipping_item_fulfillment_not_interpreted" not in issues
        ):
            issues.append("non_shipping_item_fulfillment_not_interpreted")
        if line["requires_shipping"] and choice["item_type"] == "stocked":
            promises.append(
                Effect(
                    operation="commitment",
                    arguments={
                        "commitment_type": "customer_delivery",
                        "from_party_id": bundle["company"]["record_id"],
                        "to_party_id": bundle["customer_id"],
                        "item_id": choice["item_id"],
                        "location_id": bundle["location"]["record_id"],
                        "quantity": quantity,
                        "due_at": None,
                        "amount": None,
                        "currency": received["currency"],
                        "line_index": index,
                    },
                )
            )
    document = {
        "document_type": "sales_order",
        "number": received["name"],
        "party_id": bundle["customer_id"],
        "lines": lines,
        "gross_amount": received["total_price"],
        "currency": received["currency"],
        "document_date": None,
        "ordered_at": received["created_at"],
        "requested_delivery_at": None,
        "sales_channel": "shopify",
        "source_record_id": binding["source_record_id"],
        "_source_line_payloads": raw["lineItems"]["nodes"],
    }
    plan = PreparedIntake(
        tenant_id=binding["tenant_id"],
        source_record_id=binding["source_record_id"],
        source_hash=binding["source_hash"],
        source_version=binding["source_version"],
        import_job_id=binding["import_job_id"],
        profile="shopify.order",
        mapping={
            "origin": ACTION_TYPE,
            "bundle_digest": content_digest(bundle),
            "company_party_id": bundle["company"]["record_id"],
            "customer_party_id": bundle["customer_id"],
            "location_id": bundle["location"]["record_id"],
        },
        references=references,
        effects=(Effect(operation="document", arguments=document), *promises),
        issues=tuple(issues),
        row_count=len(lines),
    )
    return plan, prices
