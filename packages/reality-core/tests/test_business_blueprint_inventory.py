from reality.services.business_blueprints import discover, explain


def test_all_public_entry_kinds_are_inventoried_without_hiding_missing_sources():
    result = discover(limit=100)
    assert result["total"] > len(result["entries"])
    kinds = set()
    cursor = 0
    while True:
        page = discover(cursor=cursor, limit=100)
        kinds.update(e["kind"] for e in page["entries"])
        assert all(e["status"] in {"partial", "missing"} for e in page["entries"])
        if page["next_cursor"] is None:
            break
        cursor = page["next_cursor"]
    assert kinds == {"command", "tool", "action", "view", "projection", "exception"}


def test_tool_and_command_share_real_exposure_rules():
    tool = explain("tool", "credit_exposure")
    command = explain("command", "credit_exposure")
    assert tool.evidence_digest
    assert {n.id for n in command.nodes} <= {n.id for n in tool.nodes}
    assert any("exposure > limit" in n.expression for n in tool.nodes)


def test_wrong_kind_discovery_returns_existing_alternatives_not_false_absence():
    result = discover(query="credit_exposure", kind="view")
    assert result["entries"] == [] and result["total"] == 0
    assert {(e["kind"], e["key"]) for e in result["alternative_entries"]} == {
        ("tool", "credit_exposure"),
        ("command", "credit_exposure"),
    }
    assert result["alternative_total"] == 2
    assert "tests" in result["recovery_hint"]
    assert (
        discover(query="certainly_missing_unregistered_entry", kind="view")[
            "alternative_entries"
        ]
        == []
    )


def test_wrong_kind_recovery_is_generic_for_future_catalog_entries(monkeypatch):
    from reality.services import business_blueprints as blueprints

    monkeypatch.setattr(
        blueprints,
        "_inventory",
        lambda: {
            ("tool", "future_unknown"): {
                "kind": "tool",
                "key": "future_unknown",
                "label": "Future operation",
            }
        },
    )
    monkeypatch.setattr(blueprints, "_roots", lambda *args: [])
    result = blueprints.discover(query="future_unknown", kind="projection")
    assert result["entries"] == []
    assert result["alternative_entries"][0]["key"] == "future_unknown"
    assert result["alternative_entries"][0]["kind"] == "tool"


def test_registered_exception_source_discloses_shared_evaluator():
    from reality.services.business_blueprints import explain

    result = explain(
        "exception", "overdue_outgoing_customer_commitment", interpret=False
    )
    assert result.sources
    assert result.status == "partial"
    assert any(
        "shared exception evaluator" in limitation for limitation in result.limitations
    )


def test_projection_source_starts_with_real_stored_reader_and_registered_builder():
    from reality.services import projections
    from reality.services.business_blueprints import _inventory, _roots

    inventory = _inventory()
    for (kind, key), entry in inventory.items():
        if kind != "projection":
            continue
        roots = _roots(entry, inventory)
        assert roots[0].__name__ == "projection_rows"
        builder = projections.NARROWED_BUILDERS.get(key)
        if builder is not None:
            assert builder in roots


def test_all_registered_view_and_projection_sources_fit_public_response(monkeypatch):
    import json

    from reality.services import business_blueprint_presentation as presentation
    from reality.services.business_blueprints import _inventory

    def forbidden():
        raise AssertionError("Source inspection must not invoke the interpreter")

    monkeypatch.setattr(presentation, "deployment_provider", forbidden)
    for kind, key in _inventory():
        if kind not in {"view", "projection"}:
            continue
        result = explain(kind, key, interpret=False, brief=True)
        assert result.sources, (kind, key, result.limitations)
        assert (
            len(json.dumps(result.model_dump(mode="json")).encode()) <= 2 * 1024 * 1024
        )
        for source in result.sources:
            assert source.code and source.start_line > 0 and source.digest
        if kind == "projection":
            assert any("shared projection" in text for text in result.limitations)


def test_public_rejection_handler_has_actual_source():
    result = explain("tool", "proposal_reject", interpret=False)
    assert any(
        source.function.endswith("._reject_proposal") for source in result.sources
    )


def test_projection_builder_links_to_verified_called_calculation():
    result = explain("projection", "fulfillment_queue", interpret=False)
    builder = next(source for source in result.sources if source.role == "builder")
    helper = next(
        source
        for source in result.sources
        if source.function.endswith("._narrowed_open_work")
    )
    assert builder.function in helper.called_by
    assert helper.digest and helper.code


def test_projection_binding_uses_live_constant_not_function_name():
    import types

    from reality.services.business_blueprints import _bound_projection_keys, _inventory
    from reality.tools import application

    bindings = {
        **application._fulfillment_queue.__globals__,
        "FULFILLMENT_QUEUE": "inventory",
    }
    future = types.FunctionType(
        application._fulfillment_queue.__code__,
        bindings,
        "future_unrelated_public_name",
    )
    assert _bound_projection_keys([future], _inventory()) == {"inventory"}


def test_projection_binding_does_not_guess_dynamic_or_shadowed_arguments(monkeypatch):
    from reality.services import business_blueprints as blueprints
    from reality.services.business_blueprint_source import capture_source
    from reality.tools import application

    function = application._fulfillment_queue
    source = capture_source(function)
    inventory = blueprints._inventory()
    for expression in ['arguments["projection_name"]', "arguments", "unknown_name"]:
        changed = source.model_copy(
            update={
                "code": f"def handler(session, tenant_id, arguments):\n    return _projection_read(session, tenant_id, {expression}, arguments)\n"
            }
        )
        monkeypatch.setattr(blueprints, "capture_source", lambda function, changed=changed: changed)
        assert blueprints._bound_projection_keys([function], inventory) == set()


def test_frozen_invocation_resolves_actual_business_callback_without_framework_walk():
    from reality.services import business_blueprints as blueprints
    from reality.services import core
    from reality.services.business_blueprint_analysis import source_tree
    from reality.services.business_blueprint_source import capture_source
    from reality.services.intake import _invoke

    helpers, _ = blueprints._resolve_calls(core.revise_commitment, source_tree(capture_source(core.revise_commitment)))
    assert core.release_commitment_hold in helpers
    assert _invoke not in helpers


def test_command_sources_include_its_registered_application_adapter():
    from reality.services import business_blueprints as blueprints
    from reality.tools import application

    inventory = blueprints._inventory()
    assert application.TOOLS["movement_create"].handler in blueprints._roots(inventory["command", "record_movement"], inventory)
