"""Spec 182 FR-002, FR-017, FR-019, SC-004, SC-008: the storyline package contract."""

import json
from datetime import UTC, datetime

import pytest

from reality.storyline import package as pkg
from reality.storyline.references import (
    ReferenceError,
    ResolutionContext,
    parse_relative_date,
    resolve_value,
)


def minimal(**overrides):
    document = {
        "storyline": 1,
        "key": "test-story",
        "version": 1,
        "title": {"en": "Test story"},
        "summary": {"en": "A summary"},
        "seed": {
            "parties": {"nordlicht": {"role": "customer", "name": "Nordlicht"}},
            "items": {"fjord": {"sku": "IT-FJORD", "name": "Fjord"}},
            "locations": {"hamburg": {"name": "Hamburg"}},
            "history": [
                {
                    "command": "movement_create",
                    "at": "-60d",
                    "input": {
                        "movement_type": "opening_stock",
                        "item_id": "$ref.items.fjord",
                        "quantity": "8",
                        "to_location_id": "$ref.locations.hamburg",
                        "occurred_at": "-60d",
                    },
                    "as": "opening",
                }
            ],
        },
        "chapters": [
            {
                "key": "order",
                "title": {"en": "Create the order"},
                "situation": {"en": "..."},
                "explain": {"en": "..."},
                "view": "view:orders",
                "command": "order_create",
                "input": {
                    "direction": "sales",
                    "number": "AT-0041",
                    "company_party_id": "$ref.parties.nordlicht",
                    "counterparty_id": "$ref.parties.nordlicht",
                    "location_id": "$ref.locations.hamburg",
                    "gross_amount": "294.00",
                    "requested_delivery_at": "+5d",
                    "lines": [
                        {
                            "item_id": "$ref.items.fjord",
                            "quantity": "12",
                            "unit": "pcs",
                            "unit_price": "24.50",
                            "gross_amount": "294.00",
                        }
                    ],
                },
                "primary": {
                    "record_type": "commitment",
                    "from": "output.commitment_ids[0]",
                },
                "expect": {"raised": ["outgoing_commitment_at_risk"]},
                "next": "review",
            },
            {
                "key": "review",
                "title": {"en": "Review"},
                "situation": {"en": "..."},
                "explain": {"en": "..."},
                "kind": "read",
                "reads": [{"tool": "exceptions"}],
            },
        ],
    }
    document.update(overrides)
    return document


def codes(result):
    return sorted({issue.code for issue in result.errors})


def test_a_well_formed_package_validates_and_reports_missing_languages_as_warnings():
    result = pkg.validate_package(minimal())

    assert result.ok, result.errors
    assert result.package.key == "test-story"
    assert {issue.code for issue in result.warnings} == {"missing_language"}
    assert result.checksum == pkg.checksum(minimal())


def test_built_ins_require_all_four_languages():
    result = pkg.validate_package(minimal(), builtin=True)

    assert not result.ok
    assert codes(result) == ["missing_language"]


def test_every_error_is_collected_in_one_answer():
    document = minimal()
    chapter = document["chapters"][0]
    chapter["command"] = "no_such_command"
    chapter["view"] = "view:nowhere"
    chapter["expect"]["raised"] = ["stock_short"]
    chapter["input"]["counterparty_id"] = "$ref.parties.ghost"
    chapter["input"]["note"] = "pty_0123456789"
    chapter["input"]["quantity"] = "-3d"
    document["chapters"][1]["reads"].append({"tool": "order_create"})

    result = pkg.validate_package(document)

    assert not result.ok
    assert codes(result) == [
        "not_a_read",
        "raw_identity",
        "relative_date_not_allowed_here",
        "unknown_command",
        "unknown_exception_class",
        "unknown_ref",
        "unknown_view",
    ]
    paths = {issue.path for issue in result.errors}
    assert "chapters[0].command" in paths
    assert "chapters[0].input.note" in paths


def test_inputs_are_checked_against_the_command_schema():
    document = minimal()
    chapter = document["chapters"][0]
    del chapter["input"]["gross_amount"]
    chapter["input"]["bogus"] = 1
    chapter["input"]["direction"] = "sideways"

    result = pkg.validate_package(document)

    assert codes(result) == ["missing_input", "not_in_enum", "unknown_input"]


def test_chapter_references_must_point_at_earlier_chapters():
    document = minimal()
    document["chapters"][0]["input"]["customer_reference"] = "$chapter.review.output.x"

    result = pkg.validate_package(document)

    assert codes(result) == ["chapter_not_earlier"]


def test_the_chapter_graph_must_reach_every_chapter_without_cycles():
    document = minimal()
    document["chapters"][1]["next"] = "order"
    document["chapters"].append(
        {
            "key": "orphan",
            "title": {"en": "t"},
            "situation": {"en": "s"},
            "explain": {"en": "e"},
            "kind": "read",
            "reads": [{"tool": "exceptions"}],
        }
    )

    result = pkg.validate_package(document)

    assert set(codes(result)) == {"cycle", "unreachable_chapter"}


def test_branches_need_exactly_one_default_and_known_targets():
    document = minimal()
    document["chapters"][0].pop("next")
    document["chapters"][0]["branches"] = [
        {"key": "aa", "label": {"en": "A"}, "next": "review"},
        {"key": "bb", "label": {"en": "B"}, "next": "missing"},
    ]

    result = pkg.validate_package(document)

    assert set(codes(result)) == {"default_branch", "unknown_chapter"}


def test_shape_errors_name_their_path_and_stop_there():
    document = minimal()
    document["chapters"][1]["kind"] = "read"
    document["chapters"][1]["reads"] = []
    document["seed"]["parties"]["Bad Name"] = {"role": "customer", "name": "x"}

    result = pkg.validate_package(document)

    assert result.package is None
    assert codes(result) == ["shape"]
    assert any(issue.path.startswith("chapters.1") for issue in result.errors)


def test_size_bound_is_checked_before_parsing_and_after():
    oversized = b"a" * (pkg.PACKAGE_BYTE_BOUND + 1)
    with pytest.raises(pkg.PackageTooLarge):
        pkg.parse_document(oversized)
    with pytest.raises(pkg.PackageUnreadable):
        pkg.parse_document(b"- just\n- a list")
    with pytest.raises(pkg.PackageUnreadable):
        pkg.parse_document(b"{not json", filename="x.json")
    big = minimal()
    big["summary"]["en"] = "x" * 3999
    big["chapters"][0]["situation"]["en"] = "y" * 3999
    big["chapters"] = big["chapters"][:1] * 1
    document = json.loads(json.dumps(big))
    document["chapters"][0]["input"]["customer_reference"] = "z" * (
        pkg.PACKAGE_BYTE_BOUND
    )
    result = pkg.validate_package(document)
    assert codes(result) == ["too_large"]


def test_yaml_and_json_documents_parse_to_the_same_mapping():
    document = minimal()
    from_json = pkg.parse_document(json.dumps(document).encode(), filename="s.json")
    import yaml

    from_yaml = pkg.parse_document(
        yaml.safe_dump(document).encode(), filename="s.storyline.yaml"
    )
    assert from_json == from_yaml == document


def test_drafts_are_refused_until_edited():
    document = minimal(draft=True)
    document["chapters"][0]["title"] = {"missing": True}

    result = pkg.validate_package(document)

    assert set(codes(result)) == {"draft", "missing_text"}


def test_a_spoken_line_is_optional_and_carries_every_language_when_present():
    document = minimal()
    document["chapters"][0]["say"] = {"en": "Create the order"}

    imported = pkg.validate_package(document)
    builtin = pkg.validate_package(document, builtin=True)

    assert imported.ok, [(i.path, i.code) for i in imported.errors]
    assert imported.package.chapters[0].say.en == "Create the order"
    # A built-in must translate what it ships, the spoken line included.
    assert ("chapters[0].say", "missing_language") in [
        (i.path, i.code) for i in builtin.errors
    ]
    # Without the field the chapter is still valid and nothing is demanded of it.
    del document["chapters"][0]["say"]
    without = pkg.validate_package(document, builtin=True)
    assert without.package.chapters[0].say is None
    assert not any(i.path.endswith(".say") for i in without.errors)


def test_every_built_in_ships_a_spoken_line_for_every_chapter():
    for result in pkg.builtin_packages():
        for index, chapter in enumerate(result.package.chapters):
            assert chapter.say is not None, (result.package.key, index, chapter.key)


def test_every_built_in_package_validates_as_a_built_in():
    results = pkg.builtin_packages()

    assert results, "at least one built-in storyline ships"
    for result in results:
        assert result.ok, [(i.path, i.code, i.detail) for i in result.errors]
        assert result.package.chapters[0].key
    keys = [result.package.key for result in results]
    assert "order-to-close" in keys


def test_json_schema_is_published_with_its_id():
    schema = pkg.json_schema()

    assert schema["$id"] == pkg.SCHEMA_ID
    assert schema["properties"]["storyline"]["const"] == 1
    assert "chapters" in schema["required"]


def test_references_resolve_against_a_run_and_refuse_raw_ids():
    start = datetime(2026, 9, 12, 12, tzinfo=UTC)
    context = ResolutionContext(
        start=start,
        refs={
            "parties": {"nordlicht": "pty_0123456789"},
            "items": {},
            "locations": {},
            "terms": {"net14": "NET14"},
        },
        company_party_id="pty_cccccccccc",
        seed_outputs={
            "opening": {"records": [{"family": "movement", "id": "mov_aaaaaaaaaa"}]},
            "invoice": {"document_id": "doc_dddddddddd"},
        },
        chapter_outputs={"order": {"commitment_ids": ["com_bbbbbbbbbb"]}},
        context_values={"settlement": {"revision": 2}},
    )

    resolved = resolve_value(
        {
            "party_id": "$ref.parties.nordlicht",
            "company_party_id": "$company.party",
            "payment_term_code": "$ref.terms.net14",
            "movement": "$seed.opening.output.records[0].id",
            "commitment_id": "$chapter.order.output.commitment_ids[0]",
            "expected_revision": "$context.settlement.revision",
            "exception_id": "$exception.overdue_receivable.$seed.invoice.output.document_id",
            "effective_at": "-56d",
            "document_date": "-56d",
            "lines": [{"promised_at": "+5d", "quantity": "12"}],
            "note": "+5d",
        },
        context,
    )

    assert resolved["party_id"] == "pty_0123456789"
    assert resolved["company_party_id"] == "pty_cccccccccc"
    assert resolved["payment_term_code"] == "NET14"
    assert resolved["movement"] == "mov_aaaaaaaaaa"
    assert resolved["commitment_id"] == "com_bbbbbbbbbb"
    assert resolved["expected_revision"] == 2
    assert resolved["exception_id"] == "exc__overdue_receivable__doc_dddddddddd"
    assert resolved["effective_at"] == parse_relative_date("-56d", start).isoformat()
    assert resolved["document_date"] == "2026-07-18"
    assert (
        resolved["lines"][0]["promised_at"]
        == parse_relative_date("+5d", start).isoformat()
    )
    assert resolved["note"] == "+5d"

    with pytest.raises(ReferenceError, match="Raw identity"):
        resolve_value({"party_id": "pty_9999999999"}, context)
    with pytest.raises(ReferenceError, match="no party named"):
        resolve_value({"party_id": "$ref.parties.ghost"}, context)
    with pytest.raises(ReferenceError, match="has not produced"):
        resolve_value({"x": "$chapter.later.output.id"}, context)
    with pytest.raises(ReferenceError, match="was not read"):
        resolve_value({"x": "$context.missing.revision"}, context)


def test_context_reads_exception_ids_and_company_party_are_validated():
    document = minimal()
    document["chapters"][1]["context"] = {
        "settlement": {
            "tool": "finance.settlement.context",
            "input": {"document_id": "$seed.opening.output.records[0].id"},
        },
        "wrong": {"tool": "order_create"},
    }
    document["chapters"][1]["reads"] = [
        {
            "tool": "exception_explain",
            "input": {
                "exception_id": "$exception.overdue_receivable.$seed.opening.output.records[0].id"
            },
        },
        {
            "tool": "exception_explain",
            "input": {"exception_id": "$exception.no_such_class.$company.party"},
        },
        {
            "tool": "exception_explain",
            "input": {"exception_id": "$context.nothing.value"},
        },
    ]
    document["chapters"][0]["input"]["company_party_id"] = "$company.party"

    result = pkg.validate_package(document)

    assert codes(result) == ["not_a_read", "unknown_context", "unknown_exception_class"]


def test_chapter_references_must_lie_on_every_path():
    document = minimal()
    document["chapters"][0].pop("next")
    document["chapters"][0]["branches"] = [
        {"key": "via-side", "label": {"en": "Side"}, "next": "side", "default": True},
        {"key": "straight", "label": {"en": "Straight"}, "next": "review"},
    ]
    document["chapters"].insert(
        1,
        {
            "key": "side",
            "title": {"en": "t"},
            "situation": {"en": "s"},
            "explain": {"en": "e"},
            "kind": "read",
            "reads": [{"tool": "exceptions"}],
            "next": "review",
        },
    )
    document["chapters"][2]["reads"] = [
        {
            "tool": "exception_explain",
            "input": {"exception_id": "$chapter.order.output.document_id"},
        },
        {
            "tool": "exception_explain",
            "input": {"exception_id": "$chapter.side.output.x"},
        },
    ]

    result = pkg.validate_package(document)

    assert [(i.code, i.path) for i in result.errors] == [
        ("chapter_not_earlier", "chapters[2].reads[1].input.exception_id")
    ]


def test_catalog_labels_name_commands_and_views_per_language():
    from reality.catalogs import load_catalog_labels

    labels = load_catalog_labels()

    assert set(labels) == {
        "commands",
        "views",
        "projections",
        "exceptions",
        "workspaces",
    }
    assert labels["views"]["open_items"]["de"] == "Offene Posten"
    assert "de" in labels["exceptions"]["overdue_receivable"]
    assert all(
        isinstance(language, str) and isinstance(label, str)
        for section in labels.values()
        for languages in section.values()
        for language, label in languages.items()
    )
