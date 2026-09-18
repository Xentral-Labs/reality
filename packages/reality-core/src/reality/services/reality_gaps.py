from __future__ import annotations

import hashlib
import json
import re
from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as Base64DecodeError
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    Fact,
    InterpretationRule,
    RealityGap,
    RealityGapEntry,
    RuleInterpretationOutcome,
    SourceRecord,
    Tenant,
    now,
    uid,
)
from reality.services.tenant_policy import require_business_operation

ORIGINS = {"chat", "mcp", "web"}
DESTINATIONS = {
    "source_only",
    "fact",
    "typed_evidence",
    "typed_reality",
    "derived_view",
    "rejected",
}
ENTRY_TYPES = {
    "answer",
    "context",
    "evidence",
    "recommendation",
    "decision",
    "implementation_proposal",
    "implementation_result",
    "note",
}
VALUE_TYPES = {"string", "enum", "boolean", "integer", "decimal", "date", "datetime"}
PATH_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.(?:[A-Za-z_][A-Za-z0-9_]*|[0-9]+))*$"
)
SENSITIVE_PATH_PARTS = {"password", "secret", "token", "authorization", "cookie"}
TERMINAL_GAP_STATUSES = {"implemented", "rejected", "source_only"}
CONDITION_OPERATORS = {
    "equals",
    "not_equals",
    "in",
    "not_in",
    "exists",
    "not_exists",
    "greater_than",
    "greater_or_equal",
    "less_than",
    "less_or_equal",
}
ORDERED_OPERATORS = {
    "greater_than",
    "greater_or_equal",
    "less_than",
    "less_or_equal",
}


def _safe_scalar_candidates(value: Any, path: str = "") -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            child = f"{path}.{key}" if path else str(key)
            if not any(part in str(key).lower() for part in SENSITIVE_PATH_PARTS):
                candidates.extend(_safe_scalar_candidates(nested, child))
    elif isinstance(value, list):
        for index, nested in enumerate(value[:10]):
            candidates.extend(_safe_scalar_candidates(nested, f"{path}.{index}"))
    elif value is not None and path:
        rendered = str(value)
        if len(rendered) <= 240:
            value_type = (
                "boolean"
                if isinstance(value, bool)
                else "integer"
                if isinstance(value, int)
                else "decimal"
                if isinstance(value, float)
                else "string"
            )
            candidates.append(
                {"path": path, "value": rendered, "value_type": value_type}
            )
    return candidates


def search_source_examples(
    session: Session, tenant_id: str, query: str, *, limit: int = 10
) -> list[dict[str, Any]]:
    """Find bounded immutable source examples within one tenant."""
    _tenant(session, tenant_id)
    term = query.strip()
    if not term:
        return []
    bounded_limit = max(1, min(limit, 20))
    pattern = f"%{term}%"
    rows = list(
        session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant_id,
                or_(
                    SourceRecord.external_id.ilike(pattern),
                    SourceRecord.source_system.ilike(pattern),
                    SourceRecord.source_type.ilike(pattern),
                    SourceRecord.payload.ilike(pattern),
                ),
            )
            .order_by(SourceRecord.received_at.desc(), SourceRecord.id.desc())
            .limit(bounded_limit)
        )
    )
    return [
        {
            "source_record_id": row.id,
            "source_system": row.source_system,
            "source_type": row.source_type,
            "external_id": row.external_id,
            "received_at": row.received_at,
            "candidates": _safe_scalar_candidates(json.loads(row.payload))[:20],
        }
        for row in rows
    ]


def _errors():
    from reality.services.core import InvalidOperation, NotFound

    return InvalidOperation, NotFound


def _tenant(session: Session, tenant_id: str) -> None:
    _, NotFound = _errors()
    if session.scalar(select(Tenant.id).where(Tenant.id == tenant_id)) is None:
        raise NotFound("Tenant not found.")


def _gap(session: Session, tenant_id: str, gap_id: str) -> RealityGap:
    _, NotFound = _errors()
    row = session.scalar(
        select(RealityGap).where(
            RealityGap.tenant_id == tenant_id, RealityGap.id == gap_id
        )
    )
    if row is None:
        raise NotFound("Missing information not found.")
    return row


def _rule(session: Session, tenant_id: str, rule_id: str) -> InterpretationRule:
    _, NotFound = _errors()
    row = session.scalar(
        select(InterpretationRule).where(
            InterpretationRule.tenant_id == tenant_id,
            InterpretationRule.id == rule_id,
        )
    )
    if row is None:
        raise NotFound("Interpretation rule not found.")
    return row


def _advance(gap: RealityGap, expected_revision: int | None) -> None:
    InvalidOperation, _ = _errors()
    if expected_revision is not None and gap.revision != expected_revision:
        raise InvalidOperation("Missing information changed after it was reviewed.")
    gap.revision += 1
    gap.updated_at = now()


def _entry(
    session: Session,
    gap: RealityGap,
    entry_type: str,
    payload: dict[str, Any],
    *,
    actor_type: str = "human",
    actor_user_id: str | None = None,
) -> RealityGapEntry:
    InvalidOperation, _ = _errors()
    if entry_type not in ENTRY_TYPES:
        raise InvalidOperation("Unsupported missing-information entry type.")
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    if len(encoded) > 20_000:
        raise InvalidOperation("Missing-information entry is too large.")
    row = RealityGapEntry(
        id=uid("gen"),
        tenant_id=gap.tenant_id,
        gap_id=gap.id,
        entry_type=entry_type,
        payload=encoded,
        actor_type=actor_type,
        actor_user_id=actor_user_id,
    )
    session.add(row)
    return row


def capture_gap(
    session: Session,
    tenant_id: str,
    *,
    question: str,
    intended_use: str,
    origin: str,
    idempotency_key: str,
    origin_reference: str | None = None,
    created_by_user_id: str | None = None,
) -> RealityGap:
    require_business_operation(session, tenant_id, "capture_gap")
    InvalidOperation, _ = _errors()
    _tenant(session, tenant_id)
    question = question.strip()
    intended_use = intended_use.strip()
    key = idempotency_key.strip()
    if not question or not intended_use or not key or origin not in ORIGINS:
        raise InvalidOperation(
            "Question, intended use, origin and idempotency key are required."
        )
    if len(question) > 100:
        raise InvalidOperation(
            "Question must be a concise queue label of at most 100 characters; "
            "put the full explanation in intended use."
        )
    fingerprint = hashlib.sha256(f"{tenant_id}\x1f{key}".encode()).hexdigest()
    existing = session.scalar(
        select(RealityGap).where(
            RealityGap.tenant_id == tenant_id,
            RealityGap.request_fingerprint == fingerprint,
        )
    )
    intended = (question, intended_use, origin, origin_reference)
    if existing:
        if (
            existing.question,
            existing.intended_use,
            existing.origin,
            existing.origin_reference,
        ) != intended:
            raise InvalidOperation(
                "Idempotency key was already used for another missing-information request."
            )
        return existing
    gap = RealityGap(
        id=uid("gap"),
        tenant_id=tenant_id,
        question=question,
        intended_use=intended_use,
        origin=origin,
        origin_reference=origin_reference,
        request_fingerprint=fingerprint,
        created_by_user_id=created_by_user_id,
    )
    session.add(gap)
    session.commit()
    return gap


def add_gap_entry(
    session: Session,
    tenant_id: str,
    gap_id: str,
    entry_type: str,
    payload: dict[str, Any],
    *,
    expected_revision: int,
    actor_type: str = "human",
    actor_user_id: str | None = None,
) -> RealityGapEntry:
    require_business_operation(session, tenant_id, "add_gap_entry")
    gap = _gap(session, tenant_id, gap_id)
    _advance(gap, expected_revision)
    if gap.status == "open":
        gap.status = "investigating"
    row = _entry(
        session,
        gap,
        entry_type,
        payload,
        actor_type=actor_type,
        actor_user_id=actor_user_id,
    )
    session.commit()
    return row


def recommend_gap(
    session: Session, tenant_id: str, gap_id: str, *, expected_revision: int
) -> RealityGapEntry:
    require_business_operation(session, tenant_id, "recommend_gap")
    gap = _gap(session, tenant_id, gap_id)
    entries = list(
        session.scalars(
            select(RealityGapEntry).where(
                RealityGapEntry.tenant_id == tenant_id, RealityGapEntry.gap_id == gap.id
            )
        )
    )
    evidence = [
        json.loads(row.payload) for row in entries if row.entry_type == "evidence"
    ]
    destination = "fact" if evidence else "source_only"
    reasons = [
        "The request describes contextual business meaning rather than an operational occurrence."
    ]
    limitations = [] if evidence else ["No immutable source example has been attached."]
    _advance(gap, expected_revision)
    gap.status = "awaiting_decision"
    row = _entry(
        session,
        gap,
        "recommendation",
        {
            "destination": destination,
            "reasons": reasons,
            "alternatives": ["source_only", "typed_reality"],
            "limitations": limitations,
        },
        actor_type="agent",
    )
    session.commit()
    return row


def decide_gap(
    session: Session,
    tenant_id: str,
    gap_id: str,
    *,
    destination: str,
    rationale: str,
    expected_revision: int,
    actor_user_id: str | None,
) -> RealityGap:
    require_business_operation(session, tenant_id, "decide_gap")
    InvalidOperation, _ = _errors()
    if destination not in DESTINATIONS or not rationale.strip():
        raise InvalidOperation("A supported destination and rationale are required.")
    gap = _gap(session, tenant_id, gap_id)
    _advance(gap, expected_revision)
    gap.destination = destination
    gap.status = (
        destination if destination in {"rejected", "source_only"} else "accepted"
    )
    _entry(
        session,
        gap,
        "decision",
        {"destination": destination, "rationale": rationale.strip()},
        actor_user_id=actor_user_id,
    )
    session.commit()
    return gap


def _validate_rule_draft(draft: dict[str, Any]) -> dict[str, Any]:
    InvalidOperation, _ = _errors()
    required = {
        "logical_name",
        "source_system",
        "source_type",
        "predicate",
        "subject_type",
        "subject_resolver",
        "value_type",
        "observed_at_mode",
    }
    if not required <= draft.keys():
        raise InvalidOperation("Interpretation rule is incomplete.")
    output_mode = str(draft.get("output_mode", "source_path"))
    output_path = draft.get("output_path", draft.get("value_path"))
    if output_mode not in {"source_path", "constant"}:
        raise InvalidOperation("Fact output mode is not supported.")
    if output_mode == "source_path" and not PATH_PATTERN.fullmatch(
        str(output_path or "")
    ):
        raise InvalidOperation("Source output path is not supported.")
    draft["output_mode"] = output_mode
    draft["output_path"] = str(output_path) if output_path else None
    draft["value_path"] = str(output_path or "")
    draft["output_scope"] = str(
        draft.get(
            "output_scope", "element" if draft.get("iteration_path") else "source"
        )
    )
    if draft["output_scope"] not in {"source", "element"}:
        raise InvalidOperation("Fact output scope is not supported.")
    if output_mode == "constant" and "constant_value" not in draft:
        raise InvalidOperation("Constant Fact output requires a value.")
    resolver = str(draft["subject_resolver"])
    expected_subject = {
        "source_document_commitments": "commitment",
        "source_document_lines": "document_line",
    }.get(resolver)
    if expected_subject is None or draft["subject_type"] != expected_subject:
        raise InvalidOperation("Subject resolver is not supported.")
    iteration_path = draft.get("iteration_path")
    if iteration_path is not None and not PATH_PATTERN.fullmatch(str(iteration_path)):
        raise InvalidOperation("Iteration path is not supported.")
    if resolver == "source_document_lines":
        if not iteration_path or not PATH_PATTERN.fullmatch(
            str(draft.get("source_line_id_path", ""))
        ):
            raise InvalidOperation("Line rules require an iteration and line ID path.")
    elif iteration_path is not None:
        raise InvalidOperation("Iteration requires the DocumentLine resolver.")
    conditions_mode = str(draft.get("conditions_mode", "all"))
    conditions = list(draft.get("conditions", []))
    if conditions_mode not in {"all", "any"}:
        raise InvalidOperation("Condition group mode is not supported.")
    if not conditions and conditions_mode == "any":
        raise InvalidOperation("An any condition group cannot be empty.")
    leaf_count = 0

    def normalize_condition(condition: Any, depth: int) -> dict[str, Any]:
        nonlocal leaf_count
        if not isinstance(condition, dict):
            raise InvalidOperation("Rule condition is invalid.")
        if "mode" in condition or "conditions" in condition:
            if depth > 3:
                raise InvalidOperation("Condition group depth exceeds three levels.")
            mode = str(condition.get("mode", ""))
            children = condition.get("conditions")
            if mode not in {"all", "any"}:
                raise InvalidOperation("Condition group mode is not supported.")
            if not isinstance(children, list) or not children:
                raise InvalidOperation("A condition group cannot be empty.")
            return {
                "mode": mode,
                "conditions": [
                    normalize_condition(child, depth + 1) for child in children
                ],
            }
        leaf_count += 1
        if leaf_count > 20:
            raise InvalidOperation("A rule supports at most 20 conditions.")
        path = str(condition.get("path", ""))
        operator = str(condition.get("operator", ""))
        value_type = str(condition.get("value_type", "string"))
        scope = str(condition.get("scope", "element" if iteration_path else "source"))
        if (
            not PATH_PATTERN.fullmatch(path)
            or operator not in CONDITION_OPERATORS
            or value_type not in VALUE_TYPES
            or scope not in {"source", "element"}
            or (scope == "element" and not iteration_path)
        ):
            raise InvalidOperation("Rule condition is not supported.")
        if operator not in {"exists", "not_exists"} and "operand" not in condition:
            raise InvalidOperation("Rule condition requires an operand.")
        if operator in {"in", "not_in"} and not isinstance(
            condition.get("operand"), list
        ):
            raise InvalidOperation("Membership condition requires a value list.")
        if operator in ORDERED_OPERATORS and value_type not in {
            "integer",
            "decimal",
            "date",
            "datetime",
        }:
            raise InvalidOperation("Ordered condition requires an ordered value type.")
        if operator not in {"exists", "not_exists"}:
            operands = (
                condition["operand"]
                if operator in {"in", "not_in"}
                else [condition["operand"]]
            )
            if not operands:
                raise InvalidOperation("Membership condition requires values.")
            for operand in operands:
                _typed_value(operand, value_type)
        return {
            "path": path,
            "operator": operator,
            "value_type": value_type,
            "scope": scope,
            **(
                {"operand": condition["operand"]}
                if operator not in {"exists", "not_exists"}
                else {}
            ),
        }

    normalized_conditions = [
        normalize_condition(condition, 2) for condition in conditions
    ]
    draft["conditions_mode"] = conditions_mode
    draft["conditions"] = normalized_conditions
    if draft["value_type"] not in VALUE_TYPES:
        raise InvalidOperation("Fact value type is not supported.")
    if output_mode == "constant":
        _typed_value(draft.get("constant_value"), str(draft["value_type"]))
    normalizers = list(draft.get("normalization", []))
    if any(value not in {"trim", "lowercase"} for value in normalizers):
        raise InvalidOperation("Fact normalizer is not supported.")
    if draft["observed_at_mode"] not in {"source_received_at", "source_path"}:
        raise InvalidOperation("Observation time mode is not supported.")
    if draft["observed_at_mode"] == "source_path" and not PATH_PATTERN.fullmatch(
        str(draft.get("observed_at_path", ""))
    ):
        raise InvalidOperation("Observation time path is required.")
    return draft


def prepare_implementation(
    session: Session,
    tenant_id: str,
    gap_id: str,
    draft: dict[str, Any] | None,
    *,
    expected_revision: int,
    actor_user_id: str | None = None,
) -> InterpretationRule | RealityGapEntry:
    require_business_operation(session, tenant_id, "prepare_implementation")
    gap = _gap(session, tenant_id, gap_id)
    if gap.destination != "fact":
        _advance(gap, expected_revision)
        gap.status = "implemented"
        row = _entry(
            session,
            gap,
            "implementation_result",
            {
                "kind": "developer_package",
                "question": gap.question,
                "destination": gap.destination,
                "requirements": [
                    "Preserve Source → Evidence → Reality",
                    "Add acceptance and tenant tests",
                ],
            },
            actor_user_id=actor_user_id,
        )
        session.commit()
        return row
    normalized = _validate_rule_draft(dict(draft or {}))
    _advance(gap, expected_revision)
    version = (
        int(
            session.scalar(
                select(func.coalesce(func.max(InterpretationRule.version), 0)).where(
                    InterpretationRule.tenant_id == tenant_id,
                    InterpretationRule.logical_name == str(normalized["logical_name"]),
                )
            )
            or 0
        )
        + 1
    )
    rule = InterpretationRule(
        id=uid("irl"),
        tenant_id=tenant_id,
        gap_id=gap.id,
        logical_name=str(normalized["logical_name"]),
        version=version,
        source_system=str(normalized["source_system"]),
        source_type=str(normalized["source_type"]),
        value_path=str(normalized["value_path"]),
        conditions_mode=str(normalized["conditions_mode"]),
        conditions=json.dumps(normalized["conditions"], sort_keys=True),
        iteration_path=normalized.get("iteration_path"),
        source_line_id_path=normalized.get("source_line_id_path"),
        output_mode=str(normalized["output_mode"]),
        output_path=normalized.get("output_path"),
        output_scope=str(normalized["output_scope"]),
        constant_value=(
            json.dumps(normalized.get("constant_value"), sort_keys=True)
            if normalized["output_mode"] == "constant"
            else None
        ),
        predicate=str(normalized["predicate"]),
        subject_type=str(normalized["subject_type"]),
        subject_resolver=str(normalized["subject_resolver"]),
        value_type=str(normalized["value_type"]),
        allowed_values=json.dumps(normalized.get("allowed_values", []), sort_keys=True),
        value_mapping=json.dumps(normalized.get("value_mapping", {}), sort_keys=True),
        normalization=json.dumps(normalized.get("normalization", []), sort_keys=True),
        observed_at_mode=str(normalized["observed_at_mode"]),
        observed_at_path=normalized.get("observed_at_path"),
        created_by_user_id=actor_user_id,
    )
    session.add(rule)
    gap.status = "implementation_ready"
    _entry(
        session,
        gap,
        "implementation_proposal",
        {"kind": "fact_rule", "rule_id": rule.id, "draft": normalized},
        actor_user_id=actor_user_id,
    )
    session.commit()
    return rule


def _extract(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                raise KeyError(path)
            current = current[index]
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(path)
    return current


def _canonical(rule: InterpretationRule, raw: Any) -> str:
    InvalidOperation, _ = _errors()
    mapping = json.loads(rule.value_mapping)
    value = mapping.get(str(raw), raw)
    if isinstance(value, str):
        for operation in json.loads(rule.normalization):
            value = value.strip() if operation == "trim" else value.lower()
    try:
        if rule.value_type in {"string", "enum"}:
            value = str(value)
            if not value or (
                rule.value_type == "enum"
                and value not in json.loads(rule.allowed_values)
            ):
                raise ValueError
            return value
        if rule.value_type == "boolean":
            if not isinstance(value, bool):
                raise ValueError
            return json.dumps(value)
        if rule.value_type == "integer":
            return str(int(value))
        if rule.value_type == "decimal":
            return format(Decimal(str(value)).normalize(), "f")
        if rule.value_type == "date":
            return date.fromisoformat(str(value)).isoformat()
        if rule.value_type == "datetime":
            parsed = datetime.fromisoformat(str(value))
            return parsed.isoformat()
    except (ValueError, TypeError, ArithmeticError) as error:
        raise InvalidOperation(
            "Source value does not satisfy the rule contract."
        ) from error
    raise InvalidOperation("Unsupported rule value.")


def _typed_value(raw: Any, value_type: str) -> Any:
    InvalidOperation, _ = _errors()
    try:
        if value_type in {"string", "enum"}:
            if not isinstance(raw, str):
                raise ValueError
            return raw
        if value_type == "boolean":
            if not isinstance(raw, bool):
                raise ValueError
            return raw
        if value_type == "integer":
            if isinstance(raw, bool):
                raise ValueError
            return int(raw)
        if value_type == "decimal":
            if isinstance(raw, bool):
                raise ValueError
            return Decimal(str(raw))
        if value_type == "date":
            return date.fromisoformat(str(raw))
        if value_type == "datetime":
            value = datetime.fromisoformat(str(raw))
            if value.tzinfo is None:
                raise ValueError
            return value.astimezone(UTC)
    except (ValueError, TypeError, ArithmeticError) as error:
        raise InvalidOperation("Condition value has the wrong type.") from error
    raise InvalidOperation("Condition value type is not supported.")


def _conditions_apply(
    rule: InterpretationRule, payload: dict[str, Any], element: Any | None
) -> bool:
    return _condition_group_applies(
        rule.conditions_mode,
        json.loads(rule.conditions),
        payload,
        element,
    )


def _condition_group_applies(
    mode: str,
    conditions: list[dict[str, Any]],
    payload: dict[str, Any],
    element: Any | None,
) -> bool:
    InvalidOperation, _ = _errors()
    results: list[bool] = []
    errors: list[InvalidOperation] = []
    for condition in conditions:
        if "mode" in condition:
            try:
                results.append(
                    _condition_group_applies(
                        condition["mode"],
                        condition["conditions"],
                        payload,
                        element,
                    )
                )
            except InvalidOperation as error:
                errors.append(error)
            continue
        context = element if condition["scope"] == "element" else payload
        try:
            raw = _extract(context, condition["path"])
            present = raw is not None
        except KeyError:
            raw = None
            present = False
        operator = condition["operator"]
        if operator == "exists":
            results.append(present)
            continue
        if operator == "not_exists":
            results.append(not present)
            continue
        if not present:
            errors.append(InvalidOperation("Condition path is missing."))
            continue
        try:
            actual = _typed_value(raw, condition["value_type"])
            operands = (
                condition["operand"]
                if operator in {"in", "not_in"}
                else [condition["operand"]]
            )
            expected = [
                _typed_value(item, condition["value_type"]) for item in operands
            ]
            results.append(
                {
                    "equals": actual == expected[0],
                    "not_equals": actual != expected[0],
                    "in": actual in expected,
                    "not_in": actual not in expected,
                    "greater_than": actual > expected[0],
                    "greater_or_equal": actual >= expected[0],
                    "less_than": actual < expected[0],
                    "less_or_equal": actual <= expected[0],
                }[operator]
            )
        except InvalidOperation as error:
            errors.append(error)
    if mode == "all" and False in results:
        return False
    if mode == "any" and True in results:
        return True
    if errors:
        raise errors[0]
    return all(results) if mode == "all" else any(results)


def _observed_at(
    rule: InterpretationRule, payload: dict[str, Any], source: SourceRecord
) -> datetime:
    InvalidOperation, _ = _errors()
    if rule.observed_at_mode == "source_received_at":
        return source.received_at
    try:
        raw = _extract(payload, str(rule.observed_at_path))
        value = datetime.fromisoformat(str(raw))
        if value.tzinfo is None:
            raise ValueError
        return value.astimezone(UTC)
    except (KeyError, ValueError, TypeError) as error:
        raise InvalidOperation("Observation time is missing or invalid.") from error


def _contexts(
    rule: InterpretationRule, payload: dict[str, Any]
) -> list[tuple[str, Any | None]]:
    InvalidOperation, _ = _errors()
    if not rule.iteration_path:
        return [("", None)]
    try:
        values = _extract(payload, rule.iteration_path)
    except KeyError as error:
        raise InvalidOperation("Iteration path is missing.") from error
    if not isinstance(values, list) or len(values) > 500:
        raise InvalidOperation("Iteration must be an array with at most 500 elements.")
    return [(str(index), element) for index, element in enumerate(values)]


def _evaluate_one(
    session: Session,
    rule: InterpretationRule,
    source: SourceRecord,
    payload: dict[str, Any],
    element_index: str,
    element: Any | None,
    *,
    persist: bool,
) -> dict[str, Any]:
    InvalidOperation, _ = _errors()
    if (
        source.source_system != rule.source_system
        or source.source_type != rule.source_type
    ):
        return {"status": "not_matched"}
    try:
        if not _conditions_apply(rule, payload, element):
            return {"status": "not_applicable", "element_key": element_index}
        if rule.output_mode == "constant":
            raw = json.loads(str(rule.constant_value))
        else:
            context = element if rule.output_scope == "element" else payload
            raw = _extract(context, str(rule.output_path or rule.value_path))
        value = _canonical(rule, raw)
        observed_at = _observed_at(rule, payload, source)
    except (KeyError, json.JSONDecodeError, InvalidOperation) as error:
        return {
            "status": "invalid_value",
            "detail": str(error),
            "element_key": element_index,
        }
    documents = list(
        session.scalars(
            select(Document).where(
                Document.tenant_id == rule.tenant_id,
                Document.source_record_id == source.id,
            )
        )
    )
    if rule.subject_resolver == "source_document_lines":
        try:
            source_line_id = str(_extract(element, str(rule.source_line_id_path)))
        except KeyError:
            return {
                "status": "invalid_value",
                "detail": "Source line identity is missing.",
                "element_key": element_index,
            }
        subjects = list(
            session.scalars(
                select(DocumentLine).where(
                    DocumentLine.tenant_id == rule.tenant_id,
                    DocumentLine.document_id.in_([row.id for row in documents]),
                    DocumentLine.source_line_id == source_line_id,
                )
            )
        )
        element_key = f"{element_index}:{source_line_id}"
    else:
        subjects = (
            list(
                session.scalars(
                    select(Commitment).where(
                        Commitment.tenant_id == rule.tenant_id,
                        Commitment.document_id.in_([row.id for row in documents]),
                    )
                )
            )
            if documents
            else []
        )
        element_key = ""
    if len(subjects) != 1:
        return {
            "status": "ambiguous_subject",
            "subject_count": len(subjects),
            "element_key": element_key,
        }
    conflicting = session.scalar(
        select(Fact).where(
            Fact.tenant_id == rule.tenant_id,
            Fact.subject_type == rule.subject_type,
            Fact.subject_id == subjects[0].id,
            Fact.predicate == rule.predicate,
            Fact.observed_at == observed_at,
            Fact.value != value,
        )
    )
    if conflicting is not None:
        return {
            "status": "conflict",
            "subject_id": subjects[0].id,
            "value": value,
            "conflicting_fact_id": conflicting.id,
            "conflicting_value": conflicting.value,
            "element_key": element_key,
        }
    if not persist:
        return {
            "status": "matched",
            "subject_id": subjects[0].id,
            "value": value,
            "element_key": element_key,
        }
    fingerprint = hashlib.sha256(
        f"{rule.tenant_id}\x1frule:{rule.id}:source:{source.id}:element:{element_key}:subject:{subjects[0].id}".encode()
    ).hexdigest()
    from reality.services.core import _persist_fact_observation

    fact, created = _persist_fact_observation(
        session,
        rule.tenant_id,
        source=source,
        subject_type=rule.subject_type,
        subject_id=subjects[0].id,
        predicate=rule.predicate,
        value=value,
        observed_at=observed_at,
        request_fingerprint=fingerprint,
        action_id=None,
        interpretation_rule_id=rule.id,
        commit=False,
    )
    return {
        "status": "fact_created" if created else "fact_existing",
        "fact": fact,
        "element_key": element_key,
    }


def _evaluate(
    session: Session, rule: InterpretationRule, source: SourceRecord, *, persist: bool
) -> list[dict[str, Any]]:
    InvalidOperation, _ = _errors()
    if (
        source.source_system != rule.source_system
        or source.source_type != rule.source_type
    ):
        return [{"status": "not_matched", "element_key": ""}]
    try:
        payload = json.loads(source.payload)
        if not isinstance(payload, dict):
            raise InvalidOperation("Source payload must be an object.")
        contexts = _contexts(rule, payload)
    except (json.JSONDecodeError, InvalidOperation) as error:
        return [{"status": "invalid_value", "detail": str(error), "element_key": ""}]
    return [
        _evaluate_one(
            session,
            rule,
            source,
            payload,
            element_index,
            element,
            persist=persist,
        )
        for element_index, element in contexts
    ]


def simulate_rule(
    session: Session, tenant_id: str, rule_id: str, *, limit: int = 100
) -> dict[str, Any]:
    rule = _rule(session, tenant_id, rule_id)
    sources = list(
        session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == rule.source_system,
                SourceRecord.source_type == rule.source_type,
            )
            .order_by(SourceRecord.received_at, SourceRecord.id)
            .limit(max(1, min(limit, 100)))
        )
    )
    results = [
        {
            **result,
            "source_record_id": source.id,
            "external_id": source.external_id,
        }
        for source in sources
        for result in _evaluate(session, rule, source, persist=False)
    ]
    return {
        "sources_considered": len(sources),
        "matches": sum(row["status"] == "matched" for row in results),
        "expected_facts": sum(row["status"] == "matched" for row in results),
        "not_applicable": sum(row["status"] == "not_applicable" for row in results),
        "invalid_values": sum(row["status"] == "invalid_value" for row in results),
        "ambiguous_subjects": sum(
            row["status"] == "ambiguous_subject" for row in results
        ),
        "conflicts": sum(row["status"] == "conflict" for row in results),
        "examples": results[:10],
    }


def _replay_scope(source_ids: list[str] | None) -> str:
    return hashlib.sha256(
        json.dumps(sorted(source_ids) if source_ids is not None else None).encode()
    ).hexdigest()


def _encode_replay_cursor(payload: dict[str, Any]) -> str:
    return urlsafe_b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).decode()


def _decode_replay_cursor(
    cursor: str, tenant_id: str, rule_id: str, scope: str
) -> tuple[datetime, str]:
    InvalidOperation, _ = _errors()
    try:
        payload = json.loads(urlsafe_b64decode(cursor.encode()))
        if (
            payload["tenant_id"] != tenant_id
            or payload["rule_id"] != rule_id
            or payload["scope"] != scope
        ):
            raise ValueError
        received_at = datetime.fromisoformat(payload["received_at"])
        if received_at.tzinfo is None:
            raise ValueError
        return received_at, str(payload["source_record_id"])
    except (
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        Base64DecodeError,
    ) as error:
        raise InvalidOperation(
            "Replay cursor does not match this rule and scope."
        ) from error


def activate_rule(session: Session, tenant_id: str, rule_id: str) -> InterpretationRule:
    require_business_operation(session, tenant_id, "activate_rule")
    rule = _rule(session, tenant_id, rule_id)
    for active in session.scalars(
        select(InterpretationRule).where(
            InterpretationRule.tenant_id == tenant_id,
            InterpretationRule.logical_name == rule.logical_name,
            InterpretationRule.status == "active",
        )
    ):
        active.status = "disabled"
        active.disabled_at = now()
    rule.status = "active"
    rule.activated_at = now()
    gap = _gap(session, tenant_id, rule.gap_id)
    gap.status = "implemented"
    gap.revision += 1
    gap.updated_at = now()
    _entry(
        session,
        gap,
        "implementation_result",
        {"kind": "fact_rule", "rule_id": rule.id, "status": "active"},
    )
    session.commit()
    return rule


def disable_rule(session: Session, tenant_id: str, rule_id: str) -> InterpretationRule:
    require_business_operation(session, tenant_id, "disable_rule")
    rule = _rule(session, tenant_id, rule_id)
    rule.status = "disabled"
    rule.disabled_at = now()
    session.commit()
    return rule


def replay_rule(
    session: Session,
    tenant_id: str,
    rule_id: str,
    *,
    source_ids: list[str] | None = None,
    limit: int = 500,
    cursor: str | None = None,
) -> dict[str, Any]:
    require_business_operation(session, tenant_id, "replay_rule")
    rule = _rule(session, tenant_id, rule_id)
    query = select(SourceRecord).where(
        SourceRecord.tenant_id == tenant_id,
        SourceRecord.source_system == rule.source_system,
        SourceRecord.source_type == rule.source_type,
    )
    if source_ids is not None:
        query = query.where(SourceRecord.id.in_(source_ids))
    scope = _replay_scope(source_ids)
    if cursor:
        received_at, source_record_id = _decode_replay_cursor(
            cursor, tenant_id, rule.id, scope
        )
        query = query.where(
            or_(
                SourceRecord.received_at > received_at,
                and_(
                    SourceRecord.received_at == received_at,
                    SourceRecord.id > source_record_id,
                ),
            )
        )
    page_limit = max(1, min(limit, 500))
    sources = list(
        session.scalars(
            query.order_by(SourceRecord.received_at, SourceRecord.id).limit(
                page_limit + 1
            )
        )
    )
    has_more = len(sources) > page_limit
    sources = sources[:page_limit]
    counts = {
        "facts_created": 0,
        "facts_existing": 0,
        "not_applicable": 0,
        "conflicts": 0,
        "failed": 0,
    }
    for source in sources:
        for result in _evaluate(session, rule, source, persist=True):
            status = result["status"]
            fact = result.get("fact")
            element_key = str(result.get("element_key", ""))
            outcome = session.scalar(
                select(RuleInterpretationOutcome).where(
                    RuleInterpretationOutcome.tenant_id == tenant_id,
                    RuleInterpretationOutcome.rule_id == rule.id,
                    RuleInterpretationOutcome.source_record_id == source.id,
                    RuleInterpretationOutcome.element_key == element_key,
                )
            )
            if outcome is None:
                outcome = RuleInterpretationOutcome(
                    id=uid("rio"),
                    tenant_id=tenant_id,
                    rule_id=rule.id,
                    source_record_id=source.id,
                    element_key=element_key,
                    status=status,
                    fact_id=fact.id if fact else None,
                    detail=json.dumps(
                        {key: value for key, value in result.items() if key != "fact"},
                        default=str,
                    ),
                )
                session.add(outcome)
            if status == "fact_created":
                counts["facts_created"] += 1
            elif status == "fact_existing":
                counts["facts_existing"] += 1
            elif status == "not_applicable":
                counts["not_applicable"] += 1
            elif status == "conflict":
                counts["conflicts"] += 1
            else:
                counts["failed"] += 1
    session.commit()
    outcome_query = select(RuleInterpretationOutcome.status, func.count()).where(
        RuleInterpretationOutcome.tenant_id == tenant_id,
        RuleInterpretationOutcome.rule_id == rule.id,
    )
    if source_ids is not None:
        outcome_query = outcome_query.where(
            RuleInterpretationOutcome.source_record_id.in_(source_ids)
        )
    cumulative_rows = session.execute(
        outcome_query.group_by(RuleInterpretationOutcome.status)
    ).all()
    cumulative = {
        "facts_created": 0,
        "facts_existing": 0,
        "not_applicable": 0,
        "conflicts": 0,
        "failed": 0,
    }
    for status, count in cumulative_rows:
        if status == "fact_created":
            cumulative["facts_created"] += count
        elif status == "fact_existing":
            cumulative["facts_existing"] += count
        elif status == "not_applicable":
            cumulative["not_applicable"] += count
        elif status == "conflict":
            cumulative["conflicts"] += count
        else:
            cumulative["failed"] += count
    next_cursor = None
    if has_more and sources:
        last = sources[-1]
        next_cursor = _encode_replay_cursor(
            {
                "tenant_id": tenant_id,
                "rule_id": rule.id,
                "scope": scope,
                "received_at": last.received_at.isoformat(),
                "source_record_id": last.id,
            }
        )
    return {
        **counts,
        "cumulative": cumulative,
        "next_cursor": next_cursor,
        "complete": not has_more,
    }


def evaluate_active_rules(
    session: Session, tenant_id: str, source_record_id: str
) -> None:
    require_business_operation(session, tenant_id, "evaluate_active_rules")
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id, SourceRecord.id == source_record_id
        )
    )
    if source is None:
        return
    rules = list(
        session.scalars(
            select(InterpretationRule).where(
                InterpretationRule.tenant_id == tenant_id,
                InterpretationRule.status == "active",
                InterpretationRule.source_system == source.source_system,
                InterpretationRule.source_type == source.source_type,
            )
        )
    )
    for rule in rules:
        replay_rule(session, tenant_id, rule.id, source_ids=[source.id])


def _gap_dict(gap: RealityGap) -> dict[str, Any]:
    return {
        "id": gap.id,
        "question": gap.question,
        "intended_use": gap.intended_use,
        "origin": gap.origin,
        "origin_reference": gap.origin_reference,
        "status": gap.status,
        "destination": gap.destination,
        "revision": gap.revision,
        "created_at": gap.created_at,
        "updated_at": gap.updated_at,
    }


def gap_detail(session: Session, tenant_id: str, gap_id: str) -> dict[str, Any]:
    gap = _gap(session, tenant_id, gap_id)
    entries = list(
        session.scalars(
            select(RealityGapEntry)
            .where(
                RealityGapEntry.tenant_id == tenant_id, RealityGapEntry.gap_id == gap.id
            )
            .order_by(RealityGapEntry.created_at, RealityGapEntry.id)
        )
    )
    rules = list(
        session.scalars(
            select(InterpretationRule)
            .where(
                InterpretationRule.tenant_id == tenant_id,
                InterpretationRule.gap_id == gap.id,
            )
            .order_by(InterpretationRule.version)
        )
    )
    rule_rows = []
    for row in rules:
        outcome_counts = dict(
            session.execute(
                select(RuleInterpretationOutcome.status, func.count())
                .where(
                    RuleInterpretationOutcome.tenant_id == tenant_id,
                    RuleInterpretationOutcome.rule_id == row.id,
                )
                .group_by(RuleInterpretationOutcome.status)
            ).all()
        )
        outcome_examples = list(
            session.scalars(
                select(RuleInterpretationOutcome)
                .where(
                    RuleInterpretationOutcome.tenant_id == tenant_id,
                    RuleInterpretationOutcome.rule_id == row.id,
                    RuleInterpretationOutcome.status.in_(
                        ["invalid_value", "ambiguous_subject", "conflict", "failed"]
                    ),
                )
                .order_by(
                    RuleInterpretationOutcome.evaluated_at.desc(),
                    RuleInterpretationOutcome.id,
                )
                .limit(10)
            )
        )
        fact_outcomes = list(
            session.scalars(
                select(RuleInterpretationOutcome)
                .where(
                    RuleInterpretationOutcome.tenant_id == tenant_id,
                    RuleInterpretationOutcome.rule_id == row.id,
                    RuleInterpretationOutcome.fact_id.is_not(None),
                )
                .order_by(
                    RuleInterpretationOutcome.evaluated_at.desc(),
                    RuleInterpretationOutcome.id,
                )
                .limit(10)
            )
        )
        last_evaluated_at = session.scalar(
            select(func.max(RuleInterpretationOutcome.evaluated_at)).where(
                RuleInterpretationOutcome.tenant_id == tenant_id,
                RuleInterpretationOutcome.rule_id == row.id,
            )
        )
        rule_rows.append(
            {
                "id": row.id,
                "logical_name": row.logical_name,
                "version": row.version,
                "status": row.status,
                "predicate": row.predicate,
                "source_system": row.source_system,
                "source_type": row.source_type,
                "value_path": row.value_path,
                "conditions_mode": row.conditions_mode,
                "conditions": json.loads(row.conditions),
                "iteration_path": row.iteration_path,
                "source_line_id_path": row.source_line_id_path,
                "output_mode": row.output_mode,
                "output_path": row.output_path,
                "output_scope": row.output_scope,
                "constant_value": (
                    json.loads(row.constant_value)
                    if row.constant_value is not None
                    else None
                ),
                "subject_type": row.subject_type,
                "subject_resolver": row.subject_resolver,
                "observed_at_mode": row.observed_at_mode,
                "observed_at_path": row.observed_at_path,
                "value_type": row.value_type,
                "allowed_values": json.loads(row.allowed_values),
                "summary": {
                    "last_evaluated_at": last_evaluated_at,
                    "counts": outcome_counts,
                    "examples": [
                        {
                            "id": outcome.id,
                            "source_record_id": outcome.source_record_id,
                            "element_key": outcome.element_key,
                            "status": outcome.status,
                            "detail": json.loads(outcome.detail),
                            "evaluated_at": outcome.evaluated_at,
                        }
                        for outcome in outcome_examples
                    ],
                    "facts": [
                        {
                            "fact_id": outcome.fact_id,
                            "source_record_id": outcome.source_record_id,
                            "element_key": outcome.element_key,
                            "evaluated_at": outcome.evaluated_at,
                        }
                        for outcome in fact_outcomes
                    ],
                },
            }
        )
    return {
        "gap": _gap_dict(gap),
        "entries": [
            {
                "id": row.id,
                "type": row.entry_type,
                "payload": json.loads(row.payload),
                "actor_type": row.actor_type,
                "created_at": row.created_at,
            }
            for row in entries
        ],
        "rules": rule_rows,
    }


def list_gaps(
    session: Session,
    tenant_id: str,
    *,
    status: str | None = None,
    destination: str | None = None,
    origin: str | None = None,
    lifecycle: str | None = None,
    rule_status: str | None = None,
    query: str | None = None,
    page: int = 1,
    size: int = 25,
) -> dict[str, Any]:
    _tenant(session, tenant_id)
    InvalidOperation, _ = _errors()
    criteria = [RealityGap.tenant_id == tenant_id]
    if rule_status is not None:
        if rule_status not in {"active", "draft", "disabled"}:
            raise InvalidOperation("Rule status must be active, draft, or disabled.")
        criteria.append(
            select(InterpretationRule.id)
            .where(
                InterpretationRule.tenant_id == tenant_id,
                InterpretationRule.gap_id == RealityGap.id,
                InterpretationRule.status == rule_status,
            )
            .exists()
        )
    if lifecycle == "open":
        criteria.append(RealityGap.status.not_in(TERMINAL_GAP_STATUSES))
    elif lifecycle == "completed":
        criteria.append(RealityGap.status.in_(TERMINAL_GAP_STATUSES))
    elif lifecycle not in {None, "all"}:
        raise InvalidOperation("Lifecycle must be open, completed, or all.")
    if status:
        criteria.append(RealityGap.status == status)
    if destination:
        criteria.append(RealityGap.destination == destination)
    if origin:
        criteria.append(RealityGap.origin == origin)
    if query and query.strip():
        search = f"%{query.strip()}%"
        criteria.append(
            or_(
                RealityGap.question.ilike(search), RealityGap.intended_use.ilike(search)
            )
        )
    tenant_criteria = RealityGap.tenant_id == tenant_id
    completed_criteria = RealityGap.status.in_(TERMINAL_GAP_STATUSES)
    completed_total = int(
        session.scalar(
            select(func.count())
            .select_from(RealityGap)
            .where(tenant_criteria, completed_criteria)
        )
        or 0
    )
    all_total = int(
        session.scalar(
            select(func.count()).select_from(RealityGap).where(tenant_criteria)
        )
        or 0
    )
    total = int(
        session.scalar(select(func.count()).select_from(RealityGap).where(*criteria))
        or 0
    )
    rows = list(
        session.scalars(
            select(RealityGap)
            .where(*criteria)
            .order_by(RealityGap.updated_at.desc(), RealityGap.id)
            .offset((max(page, 1) - 1) * min(max(size, 1), 100))
            .limit(min(max(size, 1), 100))
        )
    )
    rule_statuses: dict[str, list[str]] = {row.id: [] for row in rows}
    if rows:
        for gap_id, state in session.execute(
            select(InterpretationRule.gap_id, InterpretationRule.status)
            .where(
                InterpretationRule.tenant_id == tenant_id,
                InterpretationRule.gap_id.in_(rule_statuses),
            )
            .distinct()
            .order_by(InterpretationRule.gap_id, InterpretationRule.status)
        ):
            rule_statuses[gap_id].append(state)
    return {
        "rule_statuses": rule_statuses,
        "items": rows,
        "total": total,
        "page": max(page, 1),
        "size": min(max(size, 1), 100),
        "counts": {
            "open": all_total - completed_total,
            "completed": completed_total,
            "all": all_total,
        },
    }
