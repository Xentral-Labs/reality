"""Static documentation of the validated reporting model, never tenant records."""
from typing import Any


def build_analytics_model() -> dict[str, Any]:
    from reality.services.analytics.graph_model import (
        reporting_catalog,
        reporting_graph,
        reporting_templates,
    )

    graph = reporting_graph()
    result = {}
    for language in ("en", "de"):
        catalog = reporting_catalog(language=language)
        for node in catalog["nodes"]:
            node["definition"] = graph.nodes[node["key"]].model_dump(mode="json")
            for measure in node["measures"]:
                measure["definition"] = graph.measures[measure["key"]].model_dump(mode="json")
            for edge in [*node["edges"], *node["edges_in"]]:
                edge["definition"] = graph.edges[edge["key"]].model_dump(mode="json")
        catalog["templates"] = reporting_templates(language)
        result[language] = catalog
    # Public entry names are canonical; localized prose and search remain available.
    english = result["en"]
    nodes = {node["key"]: node for node in english["nodes"]}
    for node in result["de"]["nodes"]:
        canonical = nodes[node["key"]]
        node["search_terms"] = [node["label"], node["category"] or ""]
        node["label"] = canonical["label"]
        node["category"] = canonical["category"]
        for part in ("properties", "measures", "edges", "edges_in"):
            entries = {entry["key"]: entry for entry in canonical[part]}
            for entry in node[part]:
                node["search_terms"].append(entry["label"])
                for field in ("label", "to_label", "from_label"):
                    if field in entries[entry["key"]]:
                        entry[field] = entries[entry["key"]][field]
    templates = {template["key"]: template for template in english["templates"]}
    for template in result["de"]["templates"]:
        template["label"] = templates[template["key"]]["label"]
    return result
