"""Read-time binding of verified captured reviews; never a financial input manifest."""

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation

from reality.domain.cost_census import canonical, digest, normalize
from reality.domain.cost_population import Coverage


def _refuse() -> None:
    raise ValueError("Captured basis context, membership or result is inconsistent.")


def _known(value: str | None) -> bool:
    if value is None:
        return False
    try:
        if not isinstance(value, str) or not Decimal(value).is_finite():
            _refuse()
    except InvalidOperation:
        _refuse()
    return True


def _members(rows: list[dict], expected: Iterable[str], key: str) -> list[dict]:
    expected = tuple(expected)
    identities = [row[key] for row in rows]
    if (
        len(set(expected)) != len(expected)
        or len(set(identities)) != len(identities)
        or set(identities) != set(expected)
    ):
        _refuse()
    members = []
    for row in sorted(rows, key=lambda row: row[key]):
        result, historical = row["result"], row["basis_result"]
        available = row["state"] == "available_at_capture"
        if (
            row["state"] not in ("available_at_capture", "unknown_at_capture")
            or available != (result is not None)
            or (available and row["gaps"])
            or (row["review_id"] is None) != (row["review_content_hash"] is None)
        ):
            _refuse()
        for value in (result, historical):
            if value is not None and (
                row["review_id"] is None
                or value["review_id"] != row["review_id"]
                or value[key] != row[key]
            ):
                _refuse()
        metadata = historical or result or {}
        members.append(
            {
                key: row[key],
                "state": row["state"],
                "review_id": row["review_id"],
                "review_content_hash": row["review_content_hash"],
                "knowledge_at": metadata.get("knowledge_at"),
                "policy_id": metadata.get("policy_id"),
                "profile_revision_id": metadata.get("profile_revision_id"),
                "inventory_review_id": metadata.get("trace", {}).get(
                    "inventory_review_id"
                ),
                "result_digest": digest(result) if result is not None else None,
                "historical_result_digest": digest(historical)
                if historical is not None
                else None,
                "gaps": sorted(row["gaps"]),
                "freshness_proof": row.get("freshness_proof"),
            }
        )
    return members


def _coverage(rows: list[dict], first: str, second: str) -> tuple[dict, dict]:
    counts = [0, 0]
    for row in rows:
        values = row["result"] or {}
        supported = [_known(values.get(field)) for field in (first, second)]
        if supported[1] and not supported[0]:
            _refuse()
        for index, known in enumerate(supported):
            counts[index] += known
    result = []
    for count in counts:
        coverage = Coverage(len(rows), count)
        result.append(
            {
                "expected": coverage.expected,
                "covered": coverage.covered,
                "unknown": coverage.unknown,
                "state": coverage.state,
            }
        )
    return result[0], result[1]


def assemble_captured_basis(
    header: dict,
    resolved: dict,
    inventory_ids: Iterable[str],
    contribution_ids: Iterable[str],
) -> dict:
    """Assemble trusted service results against independently captured identity sets.

    Caller verifies retained census and canonical review contents in one snapshot. This
    helper neither supplies missing authority nor accepts user assertions of approval.
    Per-review knowledge remains separate from the current census observation time.
    """
    header = normalize(header)
    if any(
        resolved[result_key] != header[header_key]
        for result_key, header_key in (
            ("census_id", "id"),
            ("tenant_id", "tenant_id"),
            ("effective_at", "effective_at"),
            ("event_sequence", "event_sequence"),
        )
    ):
        _refuse()
    # Reject malformed monetary output before canonical hashing, with the same refusal
    # for unsupported floats and invalid/non-finite decimal strings.
    acquisition, carrying = _coverage(
        resolved["inventory"], "acquisition_value", "carrying_value"
    )
    db1, db2 = _coverage(resolved["contribution"], "db1", "db2")
    inventory = _members(resolved["inventory"], inventory_ids, "item_id")
    contribution = _members(
        resolved["contribution"], contribution_ids, "document_line_id"
    )
    content = normalize(
        {
            "version": "captured-review-basis-v2",
            "context": {
                "census_id": header["id"],
                "census_content_hash": header["content_hash"],
                **{
                    key: header[key]
                    for key in (
                        "tenant_id",
                        "effective_at",
                        "observed_at",
                        "snapshot_identity",
                        "event_sequence",
                    )
                },
            },
            "inventory": inventory,
            "contribution": contribution,
            "coverage_scope": "captured_subjects_and_candidates",
            "coverage": {
                "acquisition": acquisition,
                "carrying": carrying,
                "db1": db1,
                "db2": db2,
            },
            "gaps": {
                "documents": sorted(
                    resolved["document_gaps"], key=lambda row: row["document_id"]
                ),
                "sources": sorted(
                    resolved["source_gaps"], key=lambda row: row["source_record_id"]
                ),
            },
        }
    )
    return {
        **content,
        "digest": digest(content),
        "retained": False,
        "publication_eligible": False,
    }


CONTENT_FIELDS = frozenset(
    {
        "version",
        "context",
        "inventory",
        "contribution",
        "coverage_scope",
        "coverage",
        "gaps",
    }
)
MEMBER_BYTES = 1024 * 1024
BASIS_BYTES = 8 * 1024 * 1024


def verify_captured_basis(value: dict) -> None:
    """Verify explicitly versioned exported content, never financial authority."""
    if (
        type(value.get("retained")) is not bool
        or value.get("publication_eligible") is not False
    ):
        _refuse()
    fields = CONTENT_FIELDS
    if value.get("version") == "captured-review-basis-v1":
        fields = fields | {"retained", "publication_eligible"}
        if set(value) != fields | {"digest"}:
            _refuse()
    elif value.get("version") != "captured-review-basis-v2" or set(value) not in (
        fields | {"digest", "retained", "publication_eligible"},
        fields | {"digest", "retained", "publication_eligible", "basis_id"},
    ):
        _refuse()
    if not fields <= value.keys() or digest(
        {key: value[key] for key in fields}
    ) != value.get("digest"):
        _refuse()
    members = value["inventory"] + value["contribution"]
    if len(members) > 10:
        _refuse()
    header = {
        key: value[key] for key in fields if key not in ("inventory", "contribution")
    }
    if (
        any(len(canonical(part)) > MEMBER_BYTES for part in [header, *members])
        or len(canonical(value)) > BASIS_BYTES
    ):
        raise ValueError("Captured basis byte limit exceeded.")
