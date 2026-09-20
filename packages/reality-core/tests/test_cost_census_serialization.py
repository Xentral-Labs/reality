"""Snapshot precision and memory bounds do not infer financial values."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from reality.domain.cost_census import (
    CAPTURE_BYTES,
    MEMBER_BYTES,
    canonical,
    check_size,
    digest,
    normalize,
)


def test_exact_received_precision_and_utc_canonicalization():
    value = {"amount": Decimal("12.3400"), "at": datetime(2026, 9, 1, tzinfo=UTC)}
    assert normalize(value) == {"amount": "12.3400", "at": "2026-09-01T00:00:00+00:00"}
    assert digest(value) == digest(dict(reversed(list(value.items()))))
    assert b"12.3400" in canonical(value)


# Intentionally invalid naive timestamp exercises refusal.
NAIVE = datetime(2026, 9, 1)  # noqa: DTZ001


@pytest.mark.parametrize("value", [1.25, Decimal("NaN"), NAIVE, {1: "bad"}, object()])
def test_unsupported_snapshot_values_refuse(value):
    with pytest.raises(ValueError):
        normalize(value)


def test_member_and_combined_byte_limits_refuse_without_truncation():
    with pytest.raises(ValueError, match="byte limit"):
        check_size("x" * MEMBER_BYTES)
    with pytest.raises(ValueError, match="byte limit"):
        check_size({"one": 1}, total=CAPTURE_BYTES)
    assert check_size({"one": 1}, total=0) == len(canonical({"one": 1}))
