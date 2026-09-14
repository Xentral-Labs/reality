"""Verify documentation against the actual storage schema without a database."""

import os
import unittest

os.environ.setdefault(
    "REALITY_DATABASE_URL", "postgresql+psycopg://docs:docs@localhost/docs"
)

from data_model_reference import build_data_models
from reality.db.core import Base
from sqlalchemy.dialects import postgresql


class DataModelReferenceTests(unittest.TestCase):
    def test_schema_parity_and_no_invented_example_fields(self):
        models = build_data_models([])
        self.assertEqual(len(models), 35)
        for model in models:
            table = Base.metadata.tables[model["key"]]
            self.assertEqual(
                [f["name"] for f in model["fields"]], list(table.columns.keys())
            )
            self.assertLessEqual(set(model["example"]), set(table.columns.keys()))
            for field in model["fields"]:
                column = table.columns[field["name"]]
                self.assertEqual(field["nullable"], column.nullable)
                self.assertEqual(
                    field["type"],
                    str(column.type.compile(dialect=postgresql.dialect())),
                )
                self.assertTrue(field["meaning"]["en"])
                self.assertTrue(field["meaning"]["de"])
                self.assertEqual(
                    field["references"],
                    sorted(fk.target_fullname for fk in column.foreign_keys),
                )
                expected = (
                    "none"
                    if column.default is None
                    else "generated"
                    if column.default.is_callable
                    else "scalar"
                )
                self.assertEqual(field["default"]["kind"], expected)

    def test_derived_account_is_not_stored(self):
        model = next(m for m in build_data_models([]) if m["key"] == "ledger_entry")
        self.assertIn("account_id", [f["name"] for f in model["fields"]])
        self.assertNotIn("account", [f["name"] for f in model["fields"]])

    def test_generation_is_deterministic(self):
        self.assertEqual(build_data_models([]), build_data_models([]))
