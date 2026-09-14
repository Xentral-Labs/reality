from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_migration():
    path = (
        Path(__file__).parents[1]
        / "migrations"
        / "versions"
        / "0056_physical_shipments.py"
    )
    spec = spec_from_file_location("physical_shipments_migration", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Operations:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))

        return record


def test_physical_shipment_migration_is_additive_and_has_no_backfill(monkeypatch):
    migration = load_migration()
    operations = Operations()
    monkeypatch.setattr(migration, "op", operations)

    migration.upgrade()

    assert not {name for name, _, _ in operations.calls} & {
        "bulk_insert",
        "execute",
    }
    movement_column = next(
        args[1]
        for name, args, _ in operations.calls
        if name == "add_column" and args[0] == "movement"
    )
    assert movement_column.name == "shipment_package_id"
    assert movement_column.nullable is True
    assert [
        args[0] for name, args, _ in operations.calls if name == "create_table"
    ] == [
        "shipment",
        "shipment_package",
        "shipment_event",
        "shipment_event_supersession",
    ]


def test_physical_shipment_downgrade_drops_only_feature_structures(monkeypatch):
    migration = load_migration()
    operations = Operations()
    monkeypatch.setattr(migration, "op", operations)

    migration.downgrade()

    assert ("drop_column", ("movement", "shipment_package_id"), {}) in operations.calls
    assert [args[0] for name, args, _ in operations.calls if name == "drop_table"] == [
        "shipment_event_supersession",
        "shipment_event",
        "shipment_package",
        "shipment",
    ]
