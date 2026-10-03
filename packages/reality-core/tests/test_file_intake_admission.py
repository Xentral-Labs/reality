"""Spec 353: validate the entire raw input before deterministic review packages."""

import pytest

from reality.domain.intake import PACKAGE_BYTES, canonical_json
from reality.services.core import InvalidOperation
from reality.services.file_intake import package_item_csv


def test_large_file_is_partitioned_before_legacy_limit():
    content = (
        "sku,name\n"
        + "".join(f"SKU-{index},Article {index}\n" for index in range(5000))
    ).encode()
    packages = package_item_csv(content, {"sku": "sku", "name": "name"})
    assert len(packages) == 10
    assert sum(len(package.rows) for package in packages) == 5000
    assert all(
        len(package.rows) <= 500 and package.byte_size <= PACKAGE_BYTES
        for package in packages
    )
    assert package_item_csv(content, {"sku": "sku", "name": "name"}) == packages


def test_full_file_validation_covers_package_boundaries():
    rows = "".join(f"SKU-{index},Article\n" for index in range(501))
    with pytest.raises(InvalidOperation, match="duplicate"):
        package_item_csv(
            ("sku,name\n" + rows + "SKU-0,Duplicate\n").encode(),
            {"sku": "sku", "name": "name"},
        )


def test_utf8_bytes_and_multiline_values_define_package_limits():
    value = "ä" * 18000 + "\ncontinued"
    content = (
        "sku,name\n" + "".join(f'SKU-{index},"{value}"\n' for index in range(250))
    ).encode()
    packages = package_item_csv(content, {"sku": "sku", "name": "name"})
    assert len(packages) > 1
    assert sum(len(package.rows) for package in packages) == 250
    assert packages[0].rows[0]["name"] == value
    assert all(
        package.byte_size == len(canonical_json(list(package.rows)).encode())
        for package in packages
    )


def test_oversized_indivisible_row_refuses_before_any_package():
    content = ("sku,name\nSKU," + "x" * PACKAGE_BYTES + "\n").encode()
    with pytest.raises(InvalidOperation, match="coherent"):
        package_item_csv(content, {"sku": "sku", "name": "name"})


def test_structural_failure_in_late_row_refuses_whole_file():
    content = (
        "sku,name\n"
        + "".join(f"SKU-{index},Article\n" for index in range(501))
        + "bad,too,many\n"
    ).encode()
    with pytest.raises(InvalidOperation):
        package_item_csv(content, {"sku": "sku", "name": "name"})
