"""Systematic coverage of the reporting graph against the real schema.

Two axes, because one alone misses half the gaps:

  STRUCTURAL   every business table a node, every foreign key an edge.
  ENUMERATIVE  every value of a discriminating column covered by some node.
               This is the axis that matters most here: the purchase side lives
               in the SAME tables as the sales side, under different type values,
               so a foreign-key audit alone reports full coverage and is wrong.

Run:  REALITY_DATABASE_URL=... PYTHONPATH=packages/reality-core/src \
      .venv/bin/python specs/224-native-reporting-platform/check_coverage.py
Becomes a test in T002.
"""

import pathlib

import yaml
from reality.db import core

ROOT = pathlib.Path(__file__).resolve().parents[2]
DECL = ROOT / "specs/224-native-reporting-platform/reporting-graph.draft.yaml"
SRC = ROOT / "packages/reality-core/src"

INFRA = {
    "tenant",
    "app_user",
    "user_session",
    "email_verification_code",
    "tenant_membership",
    "access_application",
    "access_admission_counter",
    "security_audit_event",
    "company_invitation",
    "invitation_delivery",
    "chat_session",
    "chat_message",
    "ai_settings",
    "secret",
    "secret_audit_event",
    "mcp_access_token",
    "playground_run",
    "playground_step",
    "storyline_trace_entry",
    "storyline_package",
    "analytics_report",
    "analytics_report_draft",
    "business_event",
    "projection_row",
    "projection_checkpoint",
    "action",
    "reality_gap",
    "reality_gap_entry",
    "interpretation_rule",
    "rule_interpretation_outcome",
    "import_job",
    "source_system",
    "source_capability",
    "source_stream",
    "source_artifact",
    "interpretation_outcome",
    "interpretation_record_reference",
    "scheduled_job",
    "scheduled_job_run",
    "demo_data_connection",
    "ordinary_company_creation",
    "opening_scope",
    "opening_item_detail",
    "source_classification_mapping_revision",
}

# Discriminating columns whose values split one table into several business concepts.
# These value lists are NOT catalogued anywhere in the repository — see coverage.md,
# finding 4. Each value below was counted in packages/reality-core/src; the count is
# the evidence that it is real and not a typo. When a vocabulary catalog exists, this
# block is replaced by a read from it.
VOCABULARY = {
    ("document", "type"): {
        "sales_order": 30,
        "purchase_order": 14,
        "sales_invoice": 44,
        "supplier_invoice": 35,
        "credit_note": 33,
        "supplier_credit_note": 13,
    },
    ("commitment", "type"): {"customer_delivery": 8, "supplier_delivery": 6},
    ("movement", "type"): {
        "opening_stock": 22,
        "receipt": 89,
        "shipment": 59,
        "return": 33,
        "supplier_return": 19,
        "transfer": 3,
        "adjustment": 7,
        "correction": 13,
    },
}

DATA_MODEL = ROOT / "packages/reality-core/config/data_model.yaml"


def main():
    d = yaml.safe_load(DECL.read_text())
    meta = core.Base.metadata
    nodes = d["nodes"]
    node_tables = {v["table"] for v in nodes.values() if v.get("table")}
    aux = {
        v[k]["table"]
        for v in nodes.values()
        for k in ("correction_table", "revision_table")
        if v.get(k)
    }
    declared_fk = {e["via"] for e in d["edges"].values() if e.get("via")}
    biz = {t.name for t in meta.tables.values()} - INFRA

    print("=" * 72)
    print("ACHSE 1 — STRUKTUR")
    print("=" * 72)
    print(
        f"Geschäftstabellen: {len(biz)} | als Knoten: {len(biz & node_tables)} | "
        f"als Korrektur-/Revisionstabelle: {len(biz & aux)}"
    )
    open_edges = []
    for t in meta.tables.values():
        if t.name in INFRA:
            continue
        for col in t.columns:
            if col.name == "tenant_id":
                continue
            for fk in col.foreign_keys:
                tgt = fk.column.table.name
                if tgt in INFRA or tgt == "source_record":
                    continue
                ref = f"{t.name}.{col.name}"
                if ref not in declared_fk:
                    open_edges.append((t.name, col.name, tgt, t.name in node_tables))
    inside = [e for e in open_edges if e[3]]
    print(
        f"Fremdschlüssel ohne Kante: {len(open_edges)} "
        f"(davon {len(inside)} zwischen Tabellen, die bereits Knoten sind)"
    )
    print("\nOffen, obwohl die Quelltabelle schon ein Knoten ist:")
    for t, c, tgt, _ in sorted(inside):
        print(f"   {t}.{c} -> {tgt}")

    print()
    print("=" * 72)
    print("ACHSE 2 — TYPWERTE  (die Achse, die den Einkauf sichtbar macht)")
    print("=" * 72)
    for (table, column), counts in VOCABULARY.items():
        found = set(counts)
        covered = set()
        for name, n in nodes.items():
            if n.get("table") != table:
                continue
            w = (n.get("where") or {}).get(column)
            if w is None:
                covered |= {"<alle>"}
            elif isinstance(w, list):
                covered |= set(w)
            else:
                covered.add(w)
        uncov = sorted(found - covered) if "<alle>" not in covered else []
        print(f"\n{table}.{column}")
        for v in sorted(found):
            mark = "deklariert" if ("<alle>" in covered or v in covered) else "OFFEN"
            print(f"   {v:<24} {counts[v]:>4}x im Code   {mark}")
        if uncov:
            print(f"   -> nicht gedeckt: {', '.join(uncov)}")

    print()
    print("=" * 72)
    print("ACHSE 3 — KENNZAHLEN JE KNOTEN")
    print("=" * 72)
    by_node = {}
    for m, v in d["measures"].items():
        by_node.setdefault(v["node"], []).append(m)
    for name in nodes:
        ms = by_node.get(name, [])
        flag = "" if ms else "   <-- keine Kennzahl: nur filter- und zählbar"
        print(f"   {name:<20} {', '.join(ms) or '—'}{flag}")

    print()
    print("=" * 72)
    print("ACHSE 4 — ABGLEICH MIT config/data_model.yaml")
    print("=" * 72)
    dm = yaml.safe_load(DATA_MODEL.read_text())
    dm_tables = set(dm["tables"])
    live = {t.name for t in meta.tables.values()}
    print(
        f"   data_model.yaml kennt {len(dm_tables)} Tabellen, das Schema hat {len(live)}"
    )
    print(f"   im Schema, nicht dokumentiert: {sorted(live - dm_tables) or 'keine'}")
    print(f"   dokumentiert, nicht im Schema: {sorted(dm_tables - live) or 'keine'}")
    undoc = sorted(node_tables - dm_tables)
    print(f"   Knoten ohne Eintrag in data_model.yaml: {undoc or 'keine'}")


if __name__ == "__main__":
    main()
