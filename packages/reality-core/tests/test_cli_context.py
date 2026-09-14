from reality.cli import context


def test_current_tenant_context_round_trips(tmp_path, monkeypatch):
    context_file = tmp_path / "current_tenant"
    monkeypatch.setattr(context, "CONTEXT_FILE", context_file)

    assert context.read_current_tenant() is None
    context.write_current_tenant("ten_opaque")

    assert context.read_current_tenant() == "ten_opaque"
