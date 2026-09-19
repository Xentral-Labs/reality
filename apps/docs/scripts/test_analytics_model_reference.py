"""The public model is generated from the same declaration as the query engine."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("REALITY_DATABASE_URL", "postgresql+psycopg://unused:unused@localhost/unused")

from analytics_model_reference import build_analytics_model
from reality.services.analytics.graph_model import reporting_graph


class AnalyticsModelReferenceTests(unittest.TestCase):
    def test_complete_bilingual_model_without_tenant_values(self):
        model = build_analytics_model()
        graph = reporting_graph()
        for language in ("en", "de"):
            catalog = model[language]
            self.assertEqual({n["key"] for n in catalog["nodes"]}, set(graph.nodes))
            self.assertEqual({t["key"] for t in catalog["templates"]}, set(graph.templates))
            self.assertEqual(catalog["limits"], graph.limits.model_dump())
            for node in catalog["nodes"]:
                self.assertEqual(node["definition"], graph.nodes[node["key"]].model_dump(mode="json"))
                self.assertEqual({m["key"] for m in node["measures"]}, set(graph.measures_of(node["key"])))
                self.assertEqual({e["key"] for e in node["edges"]}, set(graph.edges_from(node["key"])))
                self.assertEqual({e["key"] for e in node["edges_in"]}, set(graph.edges_to(node["key"])))
                self.assertTrue(all("values" not in p for p in node["properties"]))
                for measure in node["measures"]:
                    self.assertEqual(measure["definition"], graph.measures[measure["key"]].model_dump(mode="json"))

    def test_build_never_connects_to_a_database(self):
        with patch("sqlalchemy.engine.Engine.connect", side_effect=AssertionError("database read")):
            self.assertTrue(build_analytics_model()["en"]["nodes"])

    def test_names_are_canonical_and_descriptions_stay_localized(self):
        model = build_analytics_model()
        for english, german in zip(model["en"]["nodes"], model["de"]["nodes"], strict=True):
            self.assertEqual(english["label"], german["label"])
            self.assertEqual(english["category"], german["category"])
            for part in ("properties", "measures", "edges", "edges_in"):
                self.assertEqual([x["label"] for x in english[part]], [x["label"] for x in german[part]])
        self.assertEqual([t["label"] for t in model["en"]["templates"]], [t["label"] for t in model["de"]["templates"]])
        self.assertNotEqual(model["en"]["templates"][0]["about"], model["de"]["templates"][0]["about"])
        german_order = next(n for n in model["de"]["nodes"] if n["key"] == "order")
        self.assertIn("Kundenauftrag", german_order["search_terms"])

    def test_output_is_deterministic(self):
        self.assertEqual(build_analytics_model(), build_analytics_model())


if __name__ == "__main__":
    unittest.main()
