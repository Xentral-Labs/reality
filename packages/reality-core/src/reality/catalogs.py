from __future__ import annotations

import ast
import inspect
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

import yaml

from reality.action_discovery import validate_action_discovery
from reality.config import config_text
from reality.db.core import ROOT, Base
from reality.services import artifacts as artifact_service_module
from reality.services import core as service_module
from reality.services import credit_actions as credit_action_service_module
from reality.services import demo_data as demo_data_service_module
from reality.services import dunning as dunning_service_module
from reality.services import file_interpreters as interpreter_service_module
from reality.services import invoice_actions as invoice_action_service_module
from reality.services import memberships as membership_service_module
from reality.services import notifications as notification_service_module
from reality.services import payment_intake as payment_intake_service_module
from reality.services import playground as playground_service_module
from reality.services import projection_jobs as projection_job_service_module
from reality.services import projections as projection_service_module
from reality.services import return_dispositions as return_disposition_service_module
from reality.services import scheduled_jobs as scheduled_job_service_module
from reality.services import shipments as shipment_service_module
from reality.services import supply_assignments as supply_assignment_service_module
from reality.services.finance import accounts as finance_account_service_module
from reality.services.finance import components as finance_component_service_module
from reality.services.finance import opening as finance_opening_service_module
from reality.services.finance import references as finance_reference_service_module
from reality.services.finance import settlement as finance_settlement_service_module
from reality.services.finance import settlement_flows as finance_flow_service_module
from reality.services.finance import source_mappings as finance_source_mapping_module
from reality.services.finance import target_mappings as finance_target_mapping_module
from reality.tools import application as application_tool_module

CATALOG_FILES = {
    "commands": "command_catalog.yaml",
    "events": "business_event_catalog.yaml",
    "projections": "projection_catalog.yaml",
    "fact_predicates": "fact_catalog.yaml",
}
WORKSPACE_CATALOG_FILE = "workspace_catalog.yaml"
WORKSPACE_KEYS = ("company", "operations", "warehouse", "finance", "data")
WEB_ROUTES = {
    "commitments",
    "inventory",
    "open-items",
    "documents",
    "timeline",
    "reservations",
    "movements",
    "locations",
    "payments",
    "journal",
    "parties",
    "items",
    "commercial",
    "integrations",
    "facts",
    "orders",
    "warehouse-queue",
    "fulfillment-blockers",
    "supply-demand",
}

TENANT_ISOLATION_CATALOG_FILE = "tenant_isolation_catalog.yaml"
OPERATIONAL_EXCEPTION_CATALOG_FILE = "operational_exception_catalog.yaml"
RESOURCE_CATALOG_FILE = "resource_catalog.yaml"
OPERATIONAL_EXCEPTION_CLASS_ORDER = (
    "overdue_outgoing_customer_commitment",
    "outgoing_commitment_at_risk",
    "order_stalled",
    "overdue_incoming_supplier_commitment",
    "shipped_not_billed",
    "billed_not_received",
    "invoice_price_differs",
    "sold_below_purchase_price",
    "returned_not_credited",
    "credited_not_returned",
    "supplier_return_not_credited",
    "supplier_credit_not_returned",
    "return_unresolved",
    "receipt_unbilled",
    "units_not_comparable",
    "reservation_exceeds_stock",
    "silent_source",
    "source_interpretation_failure",
    "unexplained_movement",
    "sales_invoice_unposted",
    "supplier_invoice_unposted",
    "credit_note_unposted",
    "credit_note_unsettled",
    "supplier_credit_unposted",
    "supplier_credit_unclaimed",
    "overdue_receivable",
    "credit_limit_exceeded",
    "overdue_payable",
    "purchase_discount_available",
    "duplicate_supplier_invoice",
    "unmatched_financial_event",
    "announced_return_not_arrived",
    "commitment_hold_unreleased",
    "party_hold_unreleased",
    "stock_expired",
    "missing_acquisition_cost",
    "unassigned_cost_component",
    "stale_cost_review",
    "negative_actual_db1",
)
# A cause names a business reason and stays comparable wherever it appears, so
# more than one class may declare the same one. The vocabulary itself stays
# closed: a new reason needs the same authority and evidence as a new class.
OPERATIONAL_EXCEPTION_CAUSE_VOCABULARY = (
    "insufficient_reservation",
    "early_payment_discount_taken",
    "promise_was_revised",
    "reserved_for_delivery",
    "acquisition_cost_unknown",
    "contribution_goods_cost_unknown",
    "cost_component_unassigned",
    "later_relevant_evidence",
    "supported_actual_db1_negative",
)
#: Reads that answer from the capability catalog rather than from tenant business
#: records. Guidance blocks demand a `data_basis` of real tables, which these have
#: none of, so they are the only reads exempt from carrying one (spec 270).
CATALOG_READ_TOOLS = frozenset({"capability_describe", "capability_catalog"})

CAPABILITY_GUIDANCE_REQUIRED_TOOLS = {
    "business_records_discover",
    "commitments_list",
    "exceptions_list",
    "fact_observe_propose",
    "interpretation_coverage",
    "inventory_read",
    "movement_create_propose",
    "order_explain",
    "order_create_propose",
    "proposal_approve_and_execute",
    "proposal_execution_status",
    "reservation_propose",
}
TENANT_ISOLATION_CLASSIFICATIONS = {
    "record_read",
    "collection",
    "aggregate",
    "mutation_relationship",
    "boundary",
    "global_admin",
}
from reality.services import costing as costing_service_module

TENANT_SERVICE_MODULES = {
    "reality.services.costing": costing_service_module,
    "reality.services.projection_jobs": projection_job_service_module,
    "reality.services.finance.source_mappings": finance_source_mapping_module,
    "reality.services.finance.target_mappings": finance_target_mapping_module,
    "reality.services.core": service_module,
    "reality.services.finance.components": finance_component_service_module,
    "reality.services.finance.references": finance_reference_service_module,
    "reality.services.finance.accounts": finance_account_service_module,
    "reality.services.finance.opening": finance_opening_service_module,
    "reality.services.finance.settlement": finance_settlement_service_module,
    "reality.services.finance.settlement_flows": finance_flow_service_module,
    "reality.services.artifacts": artifact_service_module,
    "reality.services.file_interpreters": interpreter_service_module,
    "reality.services.projections": projection_service_module,
    "reality.services.memberships": membership_service_module,
    "reality.services.notifications": notification_service_module,
    "reality.services.scheduled_jobs": scheduled_job_service_module,
    "reality.services.demo_data": demo_data_service_module,
    "reality.services.payment_intake": payment_intake_service_module,
    "reality.services.playground": playground_service_module,
    "reality.services.shipments": shipment_service_module,
}


@dataclass(frozen=True)
class TenantIsolationCatalog:
    version: int
    discovered_operations: tuple[str, ...]
    families: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class OperationalExceptionCatalog:
    version: int
    classes: tuple[dict[str, Any], ...]


def validate_workspace_catalog(
    payload: dict[str, Any],
    *,
    commands: list[dict[str, Any]],
    projections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate and compose presentation-only workspace metadata."""
    views = payload.get("views", [])
    actions = payload.get("actions", [])
    workspaces = payload.get("workspaces", [])
    view_keys = _unique(views, "key", "workspace views")
    action_keys = _unique(actions, "key", "workspace actions")
    workspace_keys = [entry.get("key") for entry in workspaces]
    if len(workspace_keys) != len(set(workspace_keys)):
        raise ValueError("Duplicate workspace keys")
    if tuple(workspace_keys) != WORKSPACE_KEYS:
        raise ValueError(f"Workspace keys differ: {workspace_keys}")
    materializations = {entry["materialized_as"] for entry in projections}
    commands_by_service = {entry["service"]: entry for entry in commands}
    views_by_key = {entry["key"]: entry for entry in views}
    actions_by_key = {entry["key"]: entry for entry in actions}
    for entry in views:
        if entry.get("route") not in WEB_ROUTES:
            raise ValueError(f"Workspace view has unknown route: {entry.get('route')}")
        kind = entry.get("kind")
        if kind not in {"authoritative_register", "materialized_projection"}:
            raise ValueError(f"Workspace view has unknown kind: {kind}")
        projection = entry.get("projection")
        if kind == "materialized_projection" and projection not in materializations:
            raise ValueError(f"Workspace view has unknown projection: {projection}")
        if kind == "authoritative_register" and projection:
            raise ValueError("Authoritative workspace view cannot declare projection")
    for entry in actions:
        command = commands_by_service.get(entry.get("command"))
        if command is None:
            raise ValueError(
                f"Workspace action has unknown command: {entry.get('command')}"
            )
        effect = command.get("effect")
        if not isinstance(effect, str) or not effect.strip():
            raise ValueError(
                f"Workspace action command has no non-empty effect: {entry['command']}"
            )
        if "Web" not in command.get("adapters", []):
            raise ValueError(
                f"Workspace action command is not Web eligible: {entry['command']}"
            )
        if entry.get("target_route") not in WEB_ROUTES:
            raise ValueError(
                f"Workspace action has unknown route: {entry.get('target_route')}"
            )
        if entry.get("confirmation") not in {"summary", "server_preview"}:
            raise ValueError(
                f"Workspace action has invalid confirmation: {entry.get('confirmation')}"
            )
    composed = []
    for workspace in workspaces:
        view_refs = workspace.get("views", [])
        action_refs = workspace.get("actions", [])
        unknown = (set(view_refs) - view_keys) | (set(action_refs) - action_keys)
        if unknown:
            raise ValueError(f"Workspace has unknown references: {sorted(unknown)}")
        if len(view_refs) != len(set(view_refs)) or len(action_refs) != len(
            set(action_refs)
        ):
            raise ValueError(
                f"Workspace has duplicate order entries: {workspace['key']}"
            )
        complete = workspace.get("complete_navigation", False)
        if not isinstance(complete, bool):
            raise TypeError(
                f"Workspace complete_navigation must be a boolean: {workspace['key']}"
            )
        composed.append(
            {
                "key": workspace["key"],
                "label": workspace["label"],
                "complete_navigation": complete,
                "views": [views_by_key[key] for key in view_refs],
                "actions": [
                    {
                        **actions_by_key[key],
                        "description": commands_by_service[
                            actions_by_key[key]["command"]
                        ]["effect"].strip(),
                    }
                    for key in action_refs
                ],
            }
        )
    return composed


def validate_capability_guidance(
    guidance: dict[str, Any] | list[dict[str, Any]],
    *,
    commands: list[dict[str, Any]],
    agent_coverage: dict[str, dict[str, Any]],
    event_types: set[str],
    projection_names: set[str],
    read_tool_names: set[str],
    mutating_tool_names: set[str],
    proposal_targets: dict[str, str],
    required_tools: set[str] | None = None,
    public_tool_names: set[str] | None = None,
    data_basis_names: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Validate and normalize non-authoritative guidance for public agent tools."""
    if isinstance(guidance, list):
        names = [str(item.get("tool_name", "")) for item in guidance]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"Duplicate capability guidance: {duplicates}")
        guidance = {
            str(item.get("tool_name", "")): {
                key: value for key, value in item.items() if key != "tool_name"
            }
            for item in guidance
        }
    if not isinstance(guidance, dict):
        raise TypeError("Capability guidance must be a mapping")
    required = required_tools or set()
    missing_required = sorted(required - set(guidance))
    if missing_required:
        raise ValueError(
            f"Capability guidance missing required tools: {missing_required}"
        )

    command_by_service = {entry["service"]: entry for entry in commands}
    tool_services: dict[str, list[str]] = {}
    for service_name, coverage in agent_coverage.items():
        if coverage.get("classification") != "eligible":
            continue
        for tool_name in coverage.get("tools", []):
            tool_services.setdefault(tool_name, []).append(service_name)

    normalized: dict[str, dict[str, Any]] = {}
    mandatory_lists = (
        "use_when",
        "do_not_use_when",
        "required_context",
        "preconditions",
        "events",
        "verification_reads",
    )
    for tool_name, raw in guidance.items():
        if not isinstance(raw, dict):
            raise TypeError(f"Capability guidance for {tool_name} must be a mapping")
        kind = str(raw.get("kind", "proposal")).strip()
        if kind == "confirm":
            if tool_name not in (public_tool_names or set()):
                raise ValueError(
                    f"Confirm capability guidance references unknown public tool: {tool_name}"
                )
            if raw.get("confirmation") != "explicit_decision":
                raise ValueError(
                    f"Capability guidance confirmation mismatch: {tool_name}"
                )
            for field in (
                "purpose",
                "principal_semantics",
                "retry_behavior",
                "unknown_behavior",
            ):
                if not str(raw.get(field, "")).strip():
                    raise ValueError(
                        f"Capability guidance for {tool_name} missing {field}"
                    )
            for field in (
                "use_when",
                "do_not_use_when",
                "required_context",
                "preconditions",
                "refusals",
                "events",
                "verification_reads",
            ):
                if not isinstance(raw.get(field), list) or not raw[field]:
                    raise ValueError(
                        f"Capability guidance for {tool_name} missing {field}"
                    )
            idempotency = raw.get("idempotency")
            if (
                not isinstance(idempotency, dict)
                or idempotency.get("mode") != "single_use_replay"
                or not str(idempotency.get("guidance", "")).strip()
            ):
                raise ValueError(
                    f"Capability guidance for {tool_name} has invalid idempotency"
                )
            receipt = raw.get("receipt")
            if (
                not isinstance(receipt, dict)
                or not isinstance(receipt.get("fields"), list)
                or not receipt["fields"]
                or not str(receipt.get("limitations", "")).strip()
            ):
                raise ValueError(
                    f"Capability guidance for {tool_name} has invalid receipt"
                )
            normalized[tool_name] = {"tool_name": tool_name, **raw}
            continue
        if kind == "read":
            purpose = str(raw.get("purpose", "")).strip()
            if not purpose:
                raise ValueError(f"Capability guidance for {tool_name} missing purpose")
            application_tool = str(raw.get("application_tool", "")).strip()
            if tool_name not in (public_tool_names or set(proposal_targets)):
                raise ValueError(
                    f"Read capability guidance references unknown public tool: {tool_name}"
                )
            if application_tool not in read_tool_names:
                raise ValueError(
                    f"Read capability guidance target is not read-only: {tool_name}"
                )
            if raw.get("confirmation") != "none" or raw.get("side_effects") != "none":
                raise ValueError(
                    f"Read capability guidance side-effect mismatch: {tool_name}"
                )
            list_fields = (
                "use_when",
                "do_not_use_when",
                "required_context",
                "data_basis",
                "limitations",
                "unknown_when",
                "next_steps",
            )
            for field in list_fields:
                value = raw.get(field)
                if (
                    not isinstance(value, list)
                    or not value
                    or not all(isinstance(item, str) and item.strip() for item in value)
                ):
                    raise ValueError(
                        f"Capability guidance for {tool_name} missing {field}"
                    )
            unknown_basis = sorted(
                set(raw["data_basis"])
                - (data_basis_names or (read_tool_names | projection_names))
            )
            if unknown_basis:
                raise ValueError(
                    f"Capability guidance for {tool_name} has unknown data basis: {unknown_basis}"
                )
            for field in ("freshness", "empty_result", "refusal_behavior"):
                if not str(raw.get(field, "")).strip():
                    raise ValueError(
                        f"Capability guidance for {tool_name} missing {field}"
                    )
            verification = raw.get("verification")
            if not isinstance(verification, dict) or verification.get("role") not in {
                "discovery",
                "context",
                "independent",
            }:
                raise ValueError(
                    f"Capability guidance for {tool_name} has invalid verification role"
                )
            for field in ("proves", "does_not_prove"):
                values = verification.get(field)
                if (
                    not isinstance(values, list)
                    or not values
                    or not all(
                        isinstance(item, str) and item.strip() for item in values
                    )
                ):
                    raise ValueError(
                        f"Capability guidance for {tool_name} missing verification {field}"
                    )
            examples = raw.get("examples")
            if not isinstance(examples, dict):
                raise TypeError(f"Capability guidance for {tool_name} missing examples")
            for example_kind in ("use", "do_not_use"):
                values = examples.get(example_kind)
                if (
                    not isinstance(values, list)
                    or not values
                    or not all(
                        isinstance(item, dict)
                        and str(item.get("scenario", "")).strip()
                        and str(item.get("reason", "")).strip()
                        for item in values
                    )
                ):
                    raise ValueError(
                        f"Capability guidance for {tool_name} has invalid {example_kind} examples"
                    )
            normalized[tool_name] = {"tool_name": tool_name, **raw}
            continue
        if kind != "proposal":
            raise ValueError(f"Capability guidance for {tool_name} has invalid kind")
        services = tool_services.get(tool_name, [])
        if len(services) != 1:
            raise ValueError(
                f"Capability guidance tool mapping must resolve once: {tool_name}"
            )
        service_name = services[0]
        command = command_by_service.get(service_name)
        if command is None:
            raise ValueError(
                f"Capability guidance references unknown command: {tool_name}"
            )
        purpose = str(raw.get("purpose", "")).strip()
        if not purpose:
            raise ValueError(f"Capability guidance for {tool_name} missing purpose")
        for field in mandatory_lists:
            value = raw.get(field)
            if not isinstance(value, list) or not value:
                raise ValueError(f"Capability guidance for {tool_name} missing {field}")
        for field in (
            "use_when",
            "do_not_use_when",
            "required_context",
            "preconditions",
        ):
            if not all(isinstance(item, str) and item.strip() for item in raw[field]):
                raise ValueError(
                    f"Capability guidance for {tool_name} has invalid {field}"
                )

        application_tool = str(raw.get("application_tool", "")).strip()
        if proposal_targets.get(tool_name) != application_tool:
            raise ValueError(
                f"Capability guidance proposal target mismatch: {tool_name}"
            )
        expected_confirmation = (
            "required" if application_tool in mutating_tool_names else "none"
        )
        if raw.get("confirmation") != expected_confirmation:
            raise ValueError(f"Capability guidance confirmation mismatch: {tool_name}")

        idempotency = raw.get("idempotency")
        if (
            not isinstance(idempotency, dict)
            or idempotency.get("mode")
            not in {
                "required",
                "supported",
                "unsafe_retry",
            }
            or not str(idempotency.get("guidance", "")).strip()
        ):
            raise ValueError(
                f"Capability guidance for {tool_name} has invalid idempotency"
            )

        unknown_events = sorted(set(raw["events"]) - event_types)
        if unknown_events:
            raise ValueError(
                f"Capability guidance for {tool_name} has unknown events: {unknown_events}"
            )
        verification_reads: list[dict[str, str]] = []
        unknown_reads: list[str] = []
        for item in raw["verification_reads"]:
            if not isinstance(item, dict):
                raise TypeError(
                    f"Capability guidance for {tool_name} has invalid verification reads"
                )
            name = str(item.get("name", "")).strip()
            proves = str(item.get("proves", "")).strip()
            if not name or not proves:
                raise ValueError(
                    f"Capability guidance for {tool_name} has invalid verification reads"
                )
            if name in projection_names:
                kind = "projection"
            elif name in read_tool_names:
                kind = "read_tool"
            else:
                unknown_reads.append(name)
                continue
            verification_reads.append({"name": name, "kind": kind, "proves": proves})
        if unknown_reads:
            raise ValueError(
                f"Capability guidance for {tool_name} has unknown verification reads: {sorted(unknown_reads)}"
            )

        refusals = raw.get("refusals")
        if not isinstance(refusals, list) or not all(
            isinstance(item, dict)
            and str(item.get("code", "")).strip()
            and str(item.get("description", "")).strip()
            for item in refusals
        ):
            raise ValueError(
                f"Capability guidance for {tool_name} has invalid refusals"
            )
        examples = raw.get("examples")
        if not isinstance(examples, dict):
            raise TypeError(f"Capability guidance for {tool_name} missing examples")
        for kind in ("use", "do_not_use"):
            values = examples.get(kind)
            if (
                not isinstance(values, list)
                or not values
                or not all(
                    isinstance(item, dict)
                    and str(item.get("scenario", "")).strip()
                    and str(item.get("reason", "")).strip()
                    for item in values
                )
            ):
                raise ValueError(
                    f"Capability guidance for {tool_name} has invalid {kind} examples"
                )

        normalized[tool_name] = {
            "tool_name": tool_name,
            "command": command["name"],
            "kind": "proposal",
            **raw,
            "verification_reads": verification_reads,
        }
    return normalized


def validate_operational_exception_catalog(
    payload: dict[str, Any], *, registry_keys: tuple[str, ...]
) -> OperationalExceptionCatalog:
    version = payload.get("version")
    classes = payload.get("classes")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError(
            "Operational exception catalog version must be a positive integer"
        )
    if not isinstance(classes, list) or not classes:
        raise ValueError("Operational exception catalog requires non-empty classes")
    ids: list[str] = []
    derivations: list[str] = []
    cause_ids: set[str] = set()
    for index, entry in enumerate(classes):
        if not isinstance(entry, dict):
            raise TypeError(
                f"Operational exception class at index {index} must be a mapping"
            )
        context = f"Operational exception class at index {index}"
        class_id = _required_text(entry, "id", context)
        if class_id in ids:
            raise ValueError(f"Duplicate operational exception class: {class_id}")
        ids.append(class_id)
        for field in (
            "label",
            "severity",
            "record_type",
            "authority",
            # An operator must be able to read what a class means, who owns it
            # and what makes it leave. That is as much a property of a class as
            # its evidence, so it is refused just as hard.
            "description",
            "owner",
            "clears_through",
        ):
            _required_text(entry, field, class_id)
        derivations.append(_required_text(entry, "derivation", class_id))
        evidence = entry.get("evidence")
        if (
            not isinstance(evidence, list)
            or not evidence
            or not all(isinstance(item, str) and item.strip() for item in evidence)
        ):
            raise ValueError(f"{class_id} requires non-empty evidence")
        class_cause_ids: set[str] = set()
        for cause in entry.get("causes", []):
            if not isinstance(cause, dict):
                raise TypeError(f"{class_id} cause entries must be mappings")
            cause_id = _required_text(cause, "id", f"{class_id} cause")
            if cause_id in class_cause_ids:
                raise ValueError(
                    f"Duplicate operational exception cause in {class_id}: {cause_id}"
                )
            class_cause_ids.add(cause_id)
            cause_ids.add(cause_id)
            for field in ("label", "authority"):
                _required_text(cause, field, cause_id)
            cause_evidence = cause.get("evidence")
            if not isinstance(cause_evidence, list) or not cause_evidence:
                raise ValueError(f"{cause_id} requires non-empty evidence")
    missing = sorted(set(registry_keys) - set(derivations))
    stale = sorted(set(derivations) - set(registry_keys))
    if missing or stale:
        raise ValueError(
            f"Operational exception registry drift: missing={missing}, stale={stale}"
        )
    if tuple(ids) != OPERATIONAL_EXCEPTION_CLASS_ORDER:
        raise ValueError(
            "Operational exception class order mismatch: "
            f"expected={list(OPERATIONAL_EXCEPTION_CLASS_ORDER)}, actual={ids}"
        )
    vocabulary = set(OPERATIONAL_EXCEPTION_CAUSE_VOCABULARY)
    if cause_ids != vocabulary:
        raise ValueError(
            "Operational exception cause drift: "
            f"missing={sorted(vocabulary - cause_ids)}, "
            f"stale={sorted(cause_ids - vocabulary)}"
        )
    return OperationalExceptionCatalog(version, tuple(classes))


def load_exception_class_labels() -> dict[str, dict[str, str]]:
    """Translated labels per operational exception class: class id -> language -> label.

    They live in the resource catalog next to the ERP vocabulary the documentation uses.
    A class without a label in a language is simply absent for it; callers fall back to
    the class label the exception catalog itself carries.
    """
    payload = yaml.safe_load(config_text(RESOURCE_CATALOG_FILE))
    if not isinstance(payload, dict):
        raise TypeError("Resource catalog root must be a mapping")
    labels: dict[str, dict[str, str]] = {}
    for language, groups in (payload.get("labels") or {}).items():
        for class_id, label in ((groups or {}).get("exceptions") or {}).items():
            labels.setdefault(str(class_id), {})[str(language)] = str(label)
    return labels


LABEL_SECTIONS = ("commands", "views", "projections", "exceptions", "workspaces")


def load_catalog_labels() -> dict[str, dict[str, dict[str, str]]]:
    """Translated labels per catalog section: section -> key -> language -> label.

    The same block of the resource catalog that feeds the documentation's German
    labels, exposed so that the app can name a command or a view in the reader's
    language (spec 182, FR-007). A key without a label in a language is absent for
    it; callers fall back to the catalog's own English label.
    """
    payload = yaml.safe_load(config_text(RESOURCE_CATALOG_FILE))
    if not isinstance(payload, dict):
        raise TypeError("Resource catalog root must be a mapping")
    labels: dict[str, dict[str, dict[str, str]]] = {
        section: {} for section in LABEL_SECTIONS
    }
    for language, groups in (payload.get("labels") or {}).items():
        for section in LABEL_SECTIONS:
            for key, label in ((groups or {}).get(section) or {}).items():
                labels[section].setdefault(str(key), {})[str(language)] = str(label)
    return labels


def load_operational_exception_catalog() -> OperationalExceptionCatalog:
    from reality.services.exceptions import DERIVATION_REGISTRY

    payload = yaml.safe_load(config_text(OPERATIONAL_EXCEPTION_CATALOG_FILE))
    if not isinstance(payload, dict):
        raise TypeError("Operational exception catalog root must be a mapping")
    catalog = validate_operational_exception_catalog(
        payload, registry_keys=tuple(DERIVATION_REGISTRY)
    )
    # Test evidence is verified in a source checkout, but tests are intentionally
    # absent from the production wheel. Runtime catalog reads must not depend on
    # development-only files after the metadata and derivation registry validate.
    if not (ROOT / "tests").is_dir():
        return catalog
    evidence_functions: dict[Path, set[str]] = {}
    for entry in catalog.classes:
        evidence_ids = [*entry["evidence"]]
        for cause in entry.get("causes", []):
            evidence_ids.extend(cause["evidence"])
        for evidence_id in evidence_ids:
            path_text, separator, test_name = evidence_id.partition("::")
            evidence_path = ROOT / path_text
            if not separator or not evidence_path.is_file():
                raise ValueError(
                    f"Missing operational exception evidence: {evidence_id}"
                )
            if evidence_path not in evidence_functions:
                tree = ast.parse(
                    evidence_path.read_text(encoding="utf-8"),
                    filename=str(evidence_path),
                )
                evidence_functions[evidence_path] = {
                    node.name
                    for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
            functions = evidence_functions[evidence_path]
            if test_name not in functions:
                raise ValueError(
                    f"Missing operational exception evidence: {evidence_id}"
                )
    return catalog


def discover_tenant_operations(
    modules: dict[str, Any] | None = None,
    *,
    projection_names: tuple[str, ...] | None = None,
    tool_names: tuple[str, ...] | None = None,
    explicit_operations: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Return the deterministic public tenant-aware application surface."""
    discovered: set[str] = set(explicit_operations)
    selected_modules = TENANT_SERVICE_MODULES if modules is None else modules
    for module_name, module in selected_modules.items():
        for name, value in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or value.__module__ != module.__name__:
                continue
            if "tenant_id" in inspect.signature(value).parameters:
                discovered.add(f"{module_name}:{name}")
    for name in projection_names or projection_service_module.OPERATIONAL_PROJECTIONS:
        discovered.add(f"projection:{name}")
    for name in tool_names or tuple(application_tool_module.TOOLS):
        discovered.add(f"tool:{name}")
    return tuple(sorted(discovered))


def _required_text(entry: dict[str, Any], field: str, context: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context} missing {field}")
    return value.strip()


def validate_tenant_isolation_catalog(
    payload: dict[str, Any],
    *,
    discovered_operations: tuple[str, ...] | None = None,
) -> TenantIsolationCatalog:
    """Validate complete operation classification and executable evidence mapping."""
    version = payload.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError("Tenant isolation catalog version must be a positive integer")
    families = payload.get("families")
    if not isinstance(families, list) or not families:
        raise ValueError("Tenant isolation catalog requires non-empty families")
    explicit = payload.get("explicit_operations", [])
    if not isinstance(explicit, list) or not all(
        isinstance(item, str) for item in explicit
    ):
        raise ValueError("explicit_operations must be a list of operation names")
    discovered = discovered_operations or discover_tenant_operations(
        explicit_operations=tuple(explicit)
    )

    keys: set[str] = set()
    mapped: dict[str, str] = {}
    evidence_ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, raw_family in enumerate(families):
        if not isinstance(raw_family, dict):
            raise TypeError(
                f"Tenant isolation family at index {index} must be a mapping"
            )
        context = f"Tenant isolation family at index {index}"
        key = _required_text(raw_family, "key", context)
        if key in keys:
            raise ValueError(f"Duplicate tenant isolation family: {key}")
        keys.add(key)
        _required_text(raw_family, "description", key)
        authority = _required_text(raw_family, "authority", key)
        classification = _required_text(raw_family, "classification", key)
        if classification not in TENANT_ISOLATION_CLASSIFICATIONS:
            raise ValueError(
                f"Unknown tenant isolation classification for {key}: {classification}"
            )
        if classification in {"boundary", "global_admin"}:
            _required_text(raw_family, "reason", key)
        operations = raw_family.get("operations")
        if (
            not isinstance(operations, list)
            or not operations
            or not all(isinstance(item, str) and item for item in operations)
        ):
            raise ValueError(f"{key} requires non-empty operations")
        for operation in operations:
            previous = mapped.get(operation)
            if previous:
                raise ValueError(
                    f"Duplicate tenant isolation operation: {operation} ({previous}, {key})"
                )
            mapped[operation] = key
        evidence = raw_family.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f"{key} requires non-empty evidence")
        covered: set[str] = set()
        for item in evidence:
            if not isinstance(item, dict):
                raise TypeError(f"{key} evidence entries must be mappings")
            evidence_id = _required_text(item, "id", f"{key} evidence")
            if evidence_id in evidence_ids:
                raise ValueError(f"Duplicate tenant isolation evidence: {evidence_id}")
            evidence_ids.add(evidence_id)
            assertion = _required_text(item, "assertion", f"{key} evidence")
            if assertion != classification:
                raise ValueError(
                    f"Evidence classification mismatch for {evidence_id}: {assertion} != {classification}"
                )
            evidence_operations = item.get("operations")
            if not isinstance(evidence_operations, list) or not evidence_operations:
                raise ValueError(f"{evidence_id} requires covered operations")
            unknown_evidence = set(evidence_operations) - set(operations)
            if unknown_evidence:
                raise ValueError(
                    f"Evidence {evidence_id} references unknown family operations: {sorted(unknown_evidence)}"
                )
            covered.update(evidence_operations)
        missing_evidence = sorted(set(operations) - covered)
        if missing_evidence:
            raise ValueError(f"Unproven operations in {key}: {missing_evidence}")
        normalized.append({**raw_family, "authority": authority})

    discovered_set = set(discovered)
    mapped_set = set(mapped)
    missing = sorted(discovered_set - mapped_set)
    stale = sorted(mapped_set - discovered_set)
    if missing or stale:
        raise ValueError(
            f"Tenant isolation catalog drift: missing={missing}, stale={stale}"
        )
    return TenantIsolationCatalog(version, tuple(sorted(discovered)), tuple(normalized))


REFERENCE_CATALOG_FILE = "reference_catalog.yaml"
# The records the operational exception queue reasons about. Every nullable
# foreign key on them has to be classified, and the set is discovered from the
# mapper rather than listed, so a migration adding one fails the build until
# somebody says what it is for.
REFERENCE_GOVERNED_RECORDS = (
    "DocumentLine",
    "Movement",
    "Commitment",
    "ReturnAnnouncement",
)
REFERENCE_CLASSIFICATIONS = ("load_bearing", "trace_only")
# How a class reads a load-bearing reference. Discovery proves which classes
# read one; only a person can say whether a read is a conclusion, because a
# conclusion and a mention are the same attribute access.
REFERENCE_READINGS = ("reports_absence", "requires_presence", "traces_only")


def discovered_nullable_references() -> dict[str, tuple[str, ...]]:
    """Every nullable foreign key on the governed records, from the mapper."""
    from reality.db import core as db

    found: dict[str, tuple[str, ...]] = {}
    for name in REFERENCE_GOVERNED_RECORDS:
        model = getattr(db, name)
        found[name] = tuple(
            sorted(
                column.name
                for column in model.__table__.columns
                if column.foreign_keys and column.nullable
            )
        )
    return found


def load_reference_catalog(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """The references the queue leans on, validated where it is loaded.

    Validation lives here rather than only in a test so that anything reading
    the catalog gets the same refusal, which is the rule every other catalog in
    this package follows.
    """
    if payload is None:
        payload = yaml.safe_load(config_text(REFERENCE_CATALOG_FILE))
    if not isinstance(payload, dict):
        raise TypeError("Reference catalog root must be a mapping")
    records = payload.get("records")
    if not isinstance(records, dict) or not records:
        raise ValueError("Reference catalog requires non-empty records")
    discovered = discovered_nullable_references()
    if set(records) != set(discovered):
        raise ValueError(
            "Reference catalog governs the wrong records: "
            f"expected {sorted(discovered)}, got {sorted(records)}"
        )
    class_ids = set(OPERATIONAL_EXCEPTION_CLASS_ORDER)
    for record, references in records.items():
        if not isinstance(references, dict):
            raise TypeError(f"{record} references must be a mapping")
        for name in discovered[record]:
            if name not in references:
                raise ValueError(f"{record}.{name} is not classified")
        for name, entry in references.items():
            if name not in discovered[record]:
                # A stale entry is as much a failure as a missing one, because
                # it hides the next real gap.
                raise ValueError(f"{record}.{name} no longer exists")
            if not isinstance(entry, dict):
                raise TypeError(f"{record}.{name} must be a mapping")
            classification = entry.get("classification")
            if classification not in REFERENCE_CLASSIFICATIONS:
                raise ValueError(
                    f"{record}.{name} has an unsupported classification: {classification}"
                )
            if not str(entry.get("meaning", "")).strip():
                raise ValueError(f"{record}.{name} does not say what it means")
            if classification == "trace_only":
                if not str(entry.get("reason", "")).strip():
                    raise ValueError(
                        f"{record}.{name} is trace-only and gives no reason"
                    )
                if entry.get("consumers"):
                    raise ValueError(
                        f"{record}.{name} is trace-only and names consumers"
                    )
                continue
            consumers = entry.get("consumers")
            if not isinstance(consumers, dict) or not consumers:
                raise ValueError(
                    f"{record}.{name} is load-bearing and names no consumers"
                )
            for class_id, reading in consumers.items():
                if class_id not in class_ids:
                    raise ValueError(
                        f"{record}.{name} names an unknown class: {class_id}"
                    )
                if reading not in REFERENCE_READINGS:
                    raise ValueError(
                        f"{record}.{name}/{class_id} has no supported reading direction: "
                        f"{reading}"
                    )
    for key in (
        "writers_that_do_not_set_a_reference",
        "adapters_that_forward_without_naming",
    ):
        entries = payload.get(key, [])
        if not isinstance(entries, list):
            raise TypeError(f"{key} must be a list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise TypeError(f"{key} entries must be mappings")
            if not str(entry.get("reason", "")).strip():
                raise ValueError(f"{key} entry gives no reason: {entry}")
    return payload


def load_tenant_isolation_catalog() -> TenantIsolationCatalog:
    payload = yaml.safe_load(config_text(TENANT_ISOLATION_CATALOG_FILE))
    if not isinstance(payload, dict):
        raise TypeError("Tenant isolation catalog root must be a mapping")
    catalog = validate_tenant_isolation_catalog(payload)
    for family in catalog.families:
        for evidence in family["evidence"]:
            path_text, separator, test_name = evidence["id"].partition("::")
            evidence_path = ROOT / path_text
            if not separator or not evidence_path.is_file():
                raise ValueError(f"Missing tenant isolation evidence: {evidence['id']}")
            tree = ast.parse(
                evidence_path.read_text(encoding="utf-8"), filename=str(evidence_path)
            )
            functions = {
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            if test_name not in functions:
                raise ValueError(f"Missing tenant isolation evidence: {evidence['id']}")
    return catalog


def _service(name: str) -> Any:
    if hasattr(costing_service_module, name):
        return getattr(costing_service_module, name)
    if hasattr(credit_action_service_module, name):
        return getattr(credit_action_service_module, name)
    if hasattr(dunning_service_module, name):
        return getattr(dunning_service_module, name)
    if hasattr(invoice_action_service_module, name):
        return getattr(invoice_action_service_module, name)
    if name == "change_graph_report":
        from reality.services.analytics import reports

        return getattr(reports, name)
    if hasattr(shipment_service_module, name):
        return getattr(shipment_service_module, name)
    if hasattr(supply_assignment_service_module, name):
        return getattr(supply_assignment_service_module, name)
    if hasattr(return_disposition_service_module, name):
        return getattr(return_disposition_service_module, name)
    if hasattr(finance_target_mapping_module, name):
        return getattr(finance_target_mapping_module, name)
    if hasattr(finance_source_mapping_module, name):
        return getattr(finance_source_mapping_module, name)
    if hasattr(finance_component_service_module, name):
        return getattr(finance_component_service_module, name)
    if hasattr(finance_reference_service_module, name):
        return getattr(finance_reference_service_module, name)
    if hasattr(finance_opening_service_module, name):
        return getattr(finance_opening_service_module, name)
    if hasattr(finance_flow_service_module, name):
        return getattr(finance_flow_service_module, name)
    if hasattr(finance_settlement_service_module, name):
        return getattr(finance_settlement_service_module, name)
    return getattr(
        service_module,
        name,
        getattr(
            projection_service_module,
            name,
            getattr(
                membership_service_module,
                name,
                getattr(finance_account_service_module, name, None),
            ),
        ),
    )


def catalog_code(
    kind: str, key: str, register_readers: dict[str, tuple[Any, ...]]
) -> dict[str, Any]:
    """Read bounded function source for validated catalog entries, never caller paths."""
    catalog = load_application_catalog()
    projections = {entry["materialized_as"]: entry for entry in catalog["projections"]}
    commands = {entry["service"]: entry for entry in catalog["commands"]}
    views = {
        entry["key"]: entry
        for workspace in catalog["workspaces"]
        for entry in workspace["views"]
    }
    actions = {
        entry["key"]: entry
        for workspace in catalog["workspaces"]
        for entry in workspace["actions"]
    }
    relationship = kind
    entry = None
    readers = ()
    if kind == "command":
        entry = commands.get(key)
    elif kind == "projection":
        entry = projections.get(key)
    elif kind == "action" and key in actions:
        entry = commands[actions[key]["command"]]
        relationship = "action_command"
    elif kind == "view" and key in views:
        if views[key].get("projection"):
            entry = projections[views[key]["projection"]]
            relationship = "view_projection"
        else:
            readers = register_readers.get(key, ())
            relationship = "view_reader"
    if entry is not None:
        readers = tuple(
            _service(name)
            for name in [entry["service"], *entry.get("related_services", [])]
        )
    if not readers:
        raise ValueError("No code is available for this catalog entry.")
    sources = []
    for reader in readers:
        path = (
            Path(inspect.getsourcefile(reader))
            .resolve()
            .relative_to(Path(__file__).resolve().parent)
        )
        lines = inspect.getsource(reader).splitlines(keepends=True)
        bounded = (
            "".join(lines[:600])
            .encode("utf-8")[:65536]
            .decode("utf-8", errors="ignore")
        )
        sources.append(
            {
                "path": "packages/reality-core/src/reality/" + path.as_posix(),
                "function": reader.__name__,
                "code": bounded,
                "truncated": len(lines) > 600
                or len("".join(lines).encode("utf-8")) > 65536,
            }
        )
    return {"kind": kind, "key": key, "relationship": relationship, "sources": sources}


def _type_name(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "Any"
    origin = get_origin(annotation)
    if origin in (UnionType, Union):
        return " | ".join(_type_name(item) for item in get_args(annotation))
    if origin:
        arguments = get_args(annotation)
        base = getattr(origin, "__name__", str(origin).replace("typing.", ""))
        return f"{base}[{', '.join(_type_name(item) for item in arguments)}]"
    if annotation is type(None):
        return "null"
    return getattr(annotation, "__name__", str(annotation).replace("typing.", ""))


def _service_contract(name: str, descriptions: dict[str, str]) -> dict[str, Any]:
    service = _service(name)
    hints = get_type_hints(service)
    inputs = []
    for parameter_name, parameter in inspect.signature(service).parameters.items():
        if parameter_name in {"session", "tenant_id"} or parameter_name.startswith("_"):
            continue
        required = parameter.default is inspect.Parameter.empty
        default = None if required else parameter.default
        inputs.append(
            {
                "name": parameter_name,
                "description": descriptions.get(parameter_name, ""),
                "type": _type_name(hints.get(parameter_name, parameter.annotation)),
                "required": required,
                "default": "—"
                if required
                else "null"
                if default is None
                else repr(default)
                if isinstance(default, str)
                else str(default),
            }
        )
    return {
        "service": name,
        "source": {
            "path": "packages/reality-core/src/reality/"
            + Path(inspect.getsourcefile(service))
            .resolve()
            .relative_to(Path(__file__).resolve().parent)
            .as_posix(),
            "function": service.__name__,
        },
        "inputs": inputs,
        "returns": _type_name(hints.get("return", inspect.Signature.empty)),
    }


def _unique(entries: list[dict[str, Any]], key: str, category: str) -> set[str]:
    values = [entry.get(key) for entry in entries]
    missing = [index for index, value in enumerate(values) if not value]
    if missing:
        raise ValueError(f"{category} entries missing {key}: {missing}")
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"Duplicate {category}: {duplicates}")
    return set(values)


def _literal_business_events() -> set[str]:
    events: set[str] = set()
    from reality.services import credit_actions

    for module in (
        service_module,
        costing_service_module,
        credit_actions,
        dunning_service_module,
        finance_account_service_module,
        finance_reference_service_module,
        finance_component_service_module,
        finance_source_mapping_module,
        finance_target_mapping_module,
        shipment_service_module,
    ):
        source = Path(inspect.getsourcefile(module) or "")
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if (
                not isinstance(node, ast.Call)
                or getattr(node.func, "id", None) != "emit_business_event"
            ):
                continue
            if (
                len(node.args) > 2
                and isinstance(node.args[2], ast.Constant)
                and isinstance(node.args[2].value, str)
            ):
                events.add(node.args[2].value)
    return events


def load_application_catalog() -> dict[str, Any]:
    operational_exception_catalog = load_operational_exception_catalog()
    resources = {
        kind: yaml.safe_load(config_text(filename))
        for kind, filename in CATALOG_FILES.items()
    }
    versions = {resource.get("version") for resource in resources.values()}
    if len(versions) != 1:
        raise ValueError(f"Catalog versions differ: {sorted(versions)}")

    commands = resources["commands"].get("commands", [])
    agent_coverage = resources["commands"].get("agent_command_coverage", {})
    additional_agent_commands = resources["commands"].get(
        "agent_additional_commands", {}
    )
    capability_guidance_raw = resources["commands"].get("capability_guidance", {})
    events = resources["events"].get("events", [])
    projections = resources["projections"].get("projections", [])
    fact_predicates = resources["fact_predicates"].get("fact_predicates", [])
    descriptions = resources["commands"].get("parameter_descriptions", {})
    workspace_payload = yaml.safe_load(config_text(WORKSPACE_CATALOG_FILE))
    known_tables = set(Base.metadata.tables)

    _unique(commands, "name", "commands")
    projection_names = _unique(projections, "name", "projections")
    materialized_names = _unique(
        projections, "materialized_as", "projection materializations"
    )
    event_types = _unique(events, "type", "events")
    _unique(fact_predicates, "predicate", "fact predicates")
    supported_fact_value_types = {
        "string",
        "date",
        "datetime",
        "integer",
        "decimal",
        "boolean",
        "enum",
    }
    for entry in fact_predicates:
        predicate = _required_text(entry, "predicate", "fact predicate")
        _required_text(entry, "description", predicate)
        subject_types = entry.get("subject_types")
        if (
            not isinstance(subject_types, list)
            or not subject_types
            or not all(isinstance(item, str) and item.strip() for item in subject_types)
        ):
            raise ValueError(f"{predicate} requires non-empty subject_types")
        value_type = _required_text(entry, "value_type", predicate)
        if value_type not in supported_fact_value_types:
            raise ValueError(f"{predicate} has unsupported value_type: {value_type}")
        allowed_values = entry.get("allowed_values")
        if value_type == "enum" and (
            not isinstance(allowed_values, list)
            or not allowed_values
            or not all(isinstance(item, str) for item in allowed_values)
        ):
            raise ValueError(f"{predicate} enum requires allowed_values")

    command_services = [entry["service"] for entry in commands]
    missing_coverage = sorted(set(command_services) - set(agent_coverage))
    stale_coverage = sorted(set(agent_coverage) - set(command_services))
    if missing_coverage or stale_coverage:
        raise ValueError(
            "Agent command coverage drift: "
            f"missing={missing_coverage}, stale={stale_coverage}"
        )
    from reality.mcp.catalog import MCP_TOOL_CATALOG, MCP_TOOL_NAMES

    public_business_read_names = {
        tool.name
        for tool in MCP_TOOL_CATALOG
        if tool.access == "read" and tool.name not in CATALOG_READ_TOOLS
    }

    mapped_tools: list[str] = []
    for service_name, coverage in {
        **agent_coverage,
        **additional_agent_commands,
    }.items():
        classification = coverage.get("classification")
        if classification not in {"eligible", "excluded", "blocked"}:
            raise ValueError(
                f"Invalid agent classification for {service_name}: {classification}"
            )
        tools = coverage.get("tools", [])
        reason = str(coverage.get("reason", "")).strip()
        if classification == "eligible" and not tools:
            raise ValueError(f"Eligible agent command has no tools: {service_name}")
        if classification != "eligible" and not reason:
            raise ValueError(
                f"Non-eligible agent command has no reason: {service_name}"
            )
        mapped_tools.extend(tools)
    duplicate_tools = sorted(
        {name for name in mapped_tools if mapped_tools.count(name) > 1}
    )
    missing_tools = sorted(set(mapped_tools) - MCP_TOOL_NAMES)
    if duplicate_tools or missing_tools:
        raise ValueError(
            "Agent tool mapping drift: "
            f"missing={missing_tools}, duplicate={duplicate_tools}"
        )

    application_tools = application_tool_module.TOOLS
    proposal_targets = {
        tool_name: str(entry.get("application_tool", "")).strip()
        for tool_name, entry in capability_guidance_raw.items()
        if isinstance(entry, dict) and str(entry.get("application_tool", "")).strip()
    }
    unknown_application_tools = sorted(
        {name for name in proposal_targets.values() if name not in application_tools}
    )
    if unknown_application_tools:
        raise ValueError(
            "Capability guidance references unknown application tools: "
            f"{unknown_application_tools}"
        )
    capability_guidance = validate_capability_guidance(
        capability_guidance_raw,
        commands=commands,
        agent_coverage=agent_coverage,
        event_types=event_types,
        projection_names=materialized_names,
        read_tool_names={
            name for name, tool in application_tools.items() if not tool.mutating
        },
        mutating_tool_names={
            name for name, tool in application_tools.items() if tool.mutating
        },
        proposal_targets=proposal_targets,
        required_tools=CAPABILITY_GUIDANCE_REQUIRED_TOOLS | public_business_read_names,
        public_tool_names=set(MCP_TOOL_NAMES),
        data_basis_names=known_tables
        | projection_names
        | materialized_names
        | {
            "change_proposal",
            "interpretation_outcome",
            "operational_exception",
        },
    )

    for entry in [*commands, *projections]:
        services = [entry["service"], *entry.get("related_services", [])]
        for service_name in services:
            if not callable(_service(service_name)):
                raise TypeError(f"Catalog references missing service: {service_name}")
        entry["contracts"] = [
            _service_contract(name, descriptions) for name in services
        ]
        undocumented = sorted(
            {
                item["name"]
                for contract in entry["contracts"]
                for item in contract["inputs"]
                if not item["description"]
            }
        )
        if undocumented:
            raise ValueError(
                f"Catalog services for {entry['name']} have undocumented inputs: {undocumented}"
            )
        unknown = (
            set(entry.get("reads", [])) | set(entry.get("writes", []))
        ) - known_tables
        if unknown:
            raise ValueError(
                f"Catalog entry {entry['name']} references unknown tables: {sorted(unknown)}"
            )

    for event in events:
        if not callable(_service(event["producer"])):
            raise TypeError(f"Event producer does not exist: {event['producer']}")
        unknown = set(event.get("invalidates", [])) - projection_names
        if unknown:
            raise ValueError(
                f"Event {event['type']} invalidates unknown projections: {sorted(unknown)}"
            )

    emitted = _literal_business_events()
    if emitted != event_types:
        raise ValueError(
            f"Business Event catalog drift: missing={sorted(emitted - event_types)}, stale={sorted(event_types - emitted)}"
        )
    registered = set(projection_service_module.OPERATIONAL_PROJECTIONS)
    if registered != materialized_names:
        raise ValueError(
            f"Projection catalog drift: missing={sorted(registered - materialized_names)}, stale={sorted(materialized_names - registered)}"
        )

    for projection in projections:
        projection["invalidated_by"] = [
            event["type"]
            for event in events
            if projection["name"] in event.get("invalidates", [])
        ]

    workspaces = validate_workspace_catalog(
        workspace_payload, commands=commands, projections=projections
    )

    return {
        "version": versions.pop(),
        "principle": resources["commands"].get("principle", ""),
        "parameter_descriptions": descriptions,
        "commands": commands,
        "agent_command_coverage": agent_coverage,
        "agent_additional_commands": additional_agent_commands,
        "capability_guidance": capability_guidance,
        "events": events,
        "projections": projections,
        "fact_predicates": fact_predicates,
        "command_count": len(commands),
        "event_count": len(events),
        "projection_count": len(projections),
        "fact_predicate_count": len(fact_predicates),
        "workspaces": workspaces,
        "discovery": validate_action_discovery(
            yaml.safe_load(config_text("action_discovery.json")), commands=commands
        ),
        "operational_exception_classes": [
            entry["id"] for entry in operational_exception_catalog.classes
        ],
    }


@lru_cache(maxsize=1)
def _runtime_catalog_snapshot() -> dict[str, Any]:
    """Validate immutable deployment metadata once; failures are never cached."""
    from reality.tool_catalog import build_tool_catalog

    catalog = load_application_catalog()
    catalog["tool_catalog"] = build_tool_catalog(catalog)
    vocabulary = yaml.safe_load(config_text(RESOURCE_CATALOG_FILE))["resources"]
    catalog["search_vocabulary"] = [
        {
            "key": row["key"],
            "labels": row.get("label", {}),
            "synonyms": row.get("synonyms", []),
            "match": row.get("match", ""),
            "views": row.get("views", []),
            "projections": row.get("projections", []),
        }
        for row in vocabulary
    ]
    return catalog


def runtime_application_catalog() -> dict[str, Any]:
    """Return an isolated copy of the process's validated global metadata."""
    return deepcopy(_runtime_catalog_snapshot())


def runtime_tool_catalog() -> dict[str, Any]:
    """Return an isolated copy of the capability classification alone.

    Copying all nineteen catalog sections costs roughly twice as much as copying
    this one, which a capability discovery call should not pay for eighteen
    sections it never reads. The isolation is unchanged; only the amount copied
    is (spec 270).
    """
    return deepcopy(_runtime_catalog_snapshot()["tool_catalog"])


def clear_runtime_application_catalog() -> None:
    """Reset deployment metadata for explicit development reloads and tests."""
    _runtime_catalog_snapshot.cache_clear()
