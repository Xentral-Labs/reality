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
    assert kinds == {"command", "tool", "action", "view", "projection"}


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
