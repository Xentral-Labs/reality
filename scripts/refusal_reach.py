"""Conservative static reachability of service refusals (spec 286 inventory).

Usage (from the repository root, with the repo venv):
    PYTHONPATH=packages/reality-core/src .venv/bin/python scripts/refusal_reach.py \
        [--tight] [--chat] [--scope forms|approve_all] [--exclude-analytics] [--json out]

Advisory planning tool, not a CI gate: the gate is tests/test_refusal_gate.py with
config/refusal_ratchet.json. --chat starts from core.send_chat_message only.

Graph nodes: module-level functions and class methods ("mod:func", "mod:Class.method").
Nested functions/lambdas are folded into their enclosing node (their raises count there).
Edges: any Name / module.attr reference (call or not) that resolves to a function in
reality.*; calling/referencing a class adds edges to all its methods; self.m()/cls.m()
resolves to the same class. Calls on other objects (obj.method()) are NOT resolved.
Imports: module-level and function-local `from reality.x import y`, `import reality.x as m`,
relative imports, re-export chains are followed.
Registries: seeded explicitly (TOOLS handlers for in-scope tools, read from
tools/application.py by introspection -> tool_handlers.json produced by dump_handlers.py).
"""

from __future__ import annotations

import ast
import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "packages" / "reality-core" / "src"
PKG = ROOT / "reality"
BASE_EXC = {"InvalidOperation", "NotFound", "Conflict"}


def modname(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


modules: dict[str, ast.Module] = {}
paths: dict[str, Path] = {}
for p in PKG.rglob("*.py"):
    if "__pycache__" in p.parts:
        continue
    m = modname(p)
    try:
        modules[m] = ast.parse(p.read_text(), str(p))
    except SyntaxError:
        continue
    paths[m] = p
is_pkg = {m for m, p in paths.items() if p.name == "__init__.py"}


def resolve_from(mod: str, node: ast.ImportFrom) -> str | None:
    if node.level:
        base = mod.split(".") if mod in is_pkg else mod.split(".")[:-1]
        base = base[: len(base) - (node.level - 1)] if node.level > 1 else base
        target = ".".join(base + ([node.module] if node.module else []))
    else:
        target = node.module or ""
    return target if target.startswith("reality") else None


def import_bindings(mod: str, stmts) -> dict[str, tuple[str, str | None]]:
    """name -> (module, symbol or None for module binding)."""
    out: dict[str, tuple[str, str | None]] = {}
    for node in stmts:
        if isinstance(node, ast.ImportFrom):
            target = resolve_from(mod, node)
            if not target:
                continue
            for a in node.names:
                name = a.asname or a.name
                sub = f"{target}.{a.name}"
                if sub in modules:
                    out[name] = (sub, None)
                else:
                    out[name] = (target, a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("reality"):
                    if a.asname:
                        out[a.asname] = (a.name, None)
                    else:
                        out["reality"] = ("reality", None)
    return out


# Collect definitions
funcs: dict[str, ast.AST] = {}  # node id -> def node
classes: dict[str, dict] = {}  # "mod:Class" -> {"methods": [...], "bases": [...]}
top_defs: dict[str, dict[str, str]] = defaultdict(dict)  # mod -> name -> kind
mod_imports: dict[str, dict] = {}
node_mod: dict[str, str] = {}
node_class: dict[str, str | None] = {}

for m, tree in modules.items():
    mod_imports[m] = import_bindings(
        m,
        [
            n
            for n in ast.walk(tree)
            if isinstance(n, (ast.Import, ast.ImportFrom)) and n in tree.body or False
        ],
    )
    # module-level imports incl. inside if/try at top level
    top_imports = []
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            top_imports.append(n)
        elif isinstance(n, (ast.If, ast.Try)):
            for s in ast.walk(n):
                if isinstance(s, (ast.Import, ast.ImportFrom)):
                    top_imports.append(s)
    mod_imports[m] = import_bindings(m, top_imports)
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nid = f"{m}:{n.name}"
            funcs[nid] = n
            node_mod[nid] = m
            node_class[nid] = None
            top_defs[m][n.name] = "func"
        elif isinstance(n, ast.ClassDef):
            cid = f"{m}:{n.name}"
            top_defs[m][n.name] = "class"
            meths = []
            for b in n.body:
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nid = f"{m}:{n.name}.{b.name}"
                    funcs[nid] = b
                    node_mod[nid] = m
                    node_class[nid] = cid
                    meths.append(nid)
            classes[cid] = {"methods": meths, "bases": n.bases, "mod": m}
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    top_defs[m].setdefault(t.id, "var")


def resolve_symbol(mod: str, name: str, depth=0) -> str | None:
    """Return 'mod:name' for a function/class, following re-exports."""
    if depth > 10 or mod not in modules:
        return None
    kind = top_defs[mod].get(name)
    if kind in ("func", "class"):
        return f"{mod}:{name}"
    b = mod_imports[mod].get(name)
    if b and b[1] is not None:
        return resolve_symbol(b[0], b[1], depth + 1)
    return None


def resolve_ref(mod: str, local: dict, expr: ast.AST) -> str | None:
    if isinstance(expr, ast.Name):
        b = local.get(expr.id)
        if b:
            if b[1] is None:
                return None
            return resolve_symbol(b[0], b[1])
        if expr.id in top_defs[mod] and top_defs[mod][expr.id] in ("func", "class"):
            return f"{mod}:{expr.id}"
        b = mod_imports[mod].get(expr.id)
        if b and b[1] is not None:
            return resolve_symbol(b[0], b[1])
        return None
    if isinstance(expr, ast.Attribute):
        # module.attr or package.module.attr
        chain = []
        cur = expr
        while isinstance(cur, ast.Attribute):
            chain.append(cur.attr)
            cur = cur.value
        if not isinstance(cur, ast.Name):
            return None
        chain.reverse()
        b = local.get(cur.id) or mod_imports[mod].get(cur.id)
        if not b:
            return None
        if b[1] is None:
            modpath = b[0]
        else:
            sub = f"{b[0]}.{b[1]}"
            if sub in modules:
                modpath = sub
            else:
                return None
        # walk chain through submodules
        for i, part in enumerate(chain):
            sub = f"{modpath}.{part}"
            if sub in modules and i < len(chain) - 1:
                modpath = sub
                continue
            if i == len(chain) - 1:
                return resolve_symbol(modpath, part)
            return None
    return None


# Exception class closure
exc_classes = {
    "reality.services.core:InvalidOperation",
    "reality.services.core:NotFound",
    "reality.services.core:Conflict",
}
changed = True
while changed:
    changed = False
    for cid, info in classes.items():
        if cid in exc_classes:
            continue
        for b in info["bases"]:
            r = resolve_ref(info["mod"], {}, b)
            if r in exc_classes:
                exc_classes.add(cid)
                changed = True
                break


def local_imports(mod: str, fn: ast.AST) -> dict:
    imps = [n for n in ast.walk(fn) if isinstance(n, (ast.Import, ast.ImportFrom))]
    return import_bindings(mod, imps)


def classify_msg(call: ast.Call):
    if not call.args:
        kw = [k for k in call.keywords if k.arg in (None, "message")]
        if not kw:
            return "no_message", []
        arg = kw[0].value
    else:
        arg = call.args[0]

    def lits(a):
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            return [a.value]
        if isinstance(a, ast.IfExp):
            l, r = lits(a.body), lits(a.orelse)
            if l is not None and r is not None:
                return l + r
        return None

    lv = lits(arg)
    if lv is not None:
        return ("literal" if not isinstance(arg, ast.IfExp) else "literal_ifexp"), lv
    if isinstance(arg, ast.JoinedStr):
        return "fstring", []
    if (
        isinstance(arg, ast.Call)
        and isinstance(arg.func, ast.Name)
        and arg.func.id == "str"
    ):
        return "str_error", []
    if isinstance(arg, ast.BinOp) or (
        isinstance(arg, ast.Call)
        and isinstance(arg.func, ast.Attribute)
        and arg.func.attr in ("format", "join")
    ):
        return "concat_or_format", []
    return "other_expr", []


edges: dict[str, set[str]] = defaultdict(set)
raises: dict[str, list[dict]] = defaultdict(list)
for nid, fn in funcs.items():
    mod = node_mod[nid]
    local = local_imports(mod, fn)
    cls = node_class[nid]
    for n in ast.walk(fn):
        if isinstance(n, (ast.Name, ast.Attribute)) and isinstance(
            getattr(n, "ctx", None), ast.Load
        ):
            r = resolve_ref(mod, local, n)
            if r:
                if r in classes:
                    edges[nid].update(classes[r]["methods"])
                elif r in funcs:
                    edges[nid].add(r)
            if (
                isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id in ("self", "cls")
                and cls
            ):
                t = f"{cls}.{n.attr}"
                t = f"{cls.split(':')[0]}:{cls.split(':')[1]}.{n.attr}"
                if t in funcs:
                    edges[nid].add(t)
        if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call):
            r = resolve_ref(mod, local, n.exc.func)
            if r in exc_classes:
                kind, lv = classify_msg(n.exc)
                has_code = any(k.arg == "code" for k in n.exc.keywords)
                raises[nid].append(
                    {
                        "line": n.lineno,
                        "cls": r.split(":")[1],
                        "kind": kind,
                        "lits": lv,
                        "coded": has_code,
                    }
                )

FORM_TOOLS = [
    # web/api.py DeliveryActionPrepare.tool Literal (delivery-actions/prepare)
    "order_create",
    "ledger_reverse",
    "sales_invoice_record",
    "sales_credit_record",
    "supplier_invoice_record",
    "customer_payment_post",
    "customer_refund_post",
    "supplier_payment_post",
    "reserve",
    "movement_create",
    "movement_correct",
    "reservation_release",
    "party_delivery_hold",
    "party_delivery_hold_release",
    "commitment_hold",
    "commitment_hold_release",
    "commitment_revise",
    "commitment_cancel",
    "shipment_notice_record",
    "shipment_dispatch",
    "shipment_receive",
    "shipment_event_record",
    "shipment_event_supersede",
    "supply_assign",
    "return_disposition",
    # master-data workspace (reference_workspace.prepare_reference)
    "party_create",
    "party_update",
    "item_create",
    "item_update",
    "location_create",
    "location_update",
    # cost review draft proposes cost.change; approved via ProposalReviewCard
    "cost.change",
]


def load_handlers() -> dict:
    """Introspect the TOOLS registry (needs the repo venv; the dummy URL never connects)."""
    import inspect
    import os

    os.environ.setdefault(
        "REALITY_DATABASE_URL", "postgresql+psycopg://x:y@localhost/z"
    )
    sys.path.insert(0, str(ROOT))
    from reality.tools.application import TOOLS

    def node_ids(fn):
        out = []
        qn = fn.__qualname__.split(".<locals>")[0]
        out.append(f"{fn.__module__}:{qn}")
        for cell in fn.__closure__ or ():
            v = cell.cell_contents
            if inspect.isfunction(v) and v.__module__.startswith("reality"):
                out.extend(node_ids(v))
        w = getattr(fn, "__wrapped__", None)
        if w:
            out.extend(node_ids(w))
        return out

    return {
        "form_tools": FORM_TOOLS,
        "handlers": {n: node_ids(t.handler) for n, t in TOOLS.items()},
        "mutating": {n: bool(t.mutating) for n, t in TOOLS.items()},
    }


# Roots
FORM_ROOTS = (
    ["reality.services.core:send_chat_message"]
    if "--chat" in sys.argv
    else [
        "reality.services.delivery_actions:prepare_delivery_action",
        "reality.services.delivery_actions:delivery_proposal_detail",
        "reality.services.delivery_actions:reconcile_delivery",
        "reality.services.delivery_actions:review_existing",
        "reality.services.delivery_actions:require_delivery_principal",
        "reality.services.reference_workspace:prepare_reference",
        "reality.services.reference_workspace:reference_proposal",
        "reality.services.reference_workspace:require_ordinary_workspace",
        "reality.tools.application:approve_and_execute_proposal",
        "reality.tools.application:reject_proposal",
        "reality.services.cost_review_draft:propose_drafted_review",
        "reality.services.core:chat_messages",
    ]
)
handlers = load_handlers()
FORM_TOOLS = set(handlers["form_tools"])
scope = "forms"
if "--scope" in sys.argv:
    scope = sys.argv[sys.argv.index("--scope") + 1]
excl_analytics = "--exclude-analytics" in sys.argv
roots = list(FORM_ROOTS)
for tool, targets in [] if "--chat" in sys.argv else handlers["handlers"].items():
    if scope == "approve_all" and handlers["mutating"].get(tool) or tool in FORM_TOOLS:
        roots.extend(targets)
if "--tight" in sys.argv:
    # prune per-tool branches of multi-tool dispatchers to the in-scope tools
    ccp = "reality.tools.application:create_change_proposal"
    edges[ccp] = {
        e
        for e in edges[ccp]
        if not any(
            x in e
            for x in (
                "analytics",
                "dunning",
                "finance.",
                "memberships",
                "preview_free_supplier_invoice",
            )
        )
    }
    aep = "reality.tools.application:approve_and_execute_proposal"
    edges[aep] = {
        e
        for e in edges[aep]
        if "analytics" not in e and "master_tool_execution" not in e
    }
    edges[aep].discard("reality.tools.finance:execute_finance_command")
    edges[aep].add("reality.services.costing:execute_cost_change")
    edges[aep].add("reality.tools.finance:validate_finance_request")
missing = [r for r in roots if r not in funcs]
if missing:
    print("MISSING ROOTS", missing, file=sys.stderr)

seen = set()
dq = deque(r for r in roots if r in funcs)
seen.update(dq)
while dq:
    cur = dq.popleft()
    for nxt in edges[cur]:
        if excl_analytics and node_mod[nxt].startswith("reality.services.analytics"):
            continue
        if nxt not in seen:
            seen.add(nxt)
            dq.append(nxt)


def summarize(nodes, label):
    sites = [(nid, r) for nid in nodes for r in raises.get(nid, [])]
    kinds = Counter(r["kind"] for _, r in sites)
    lits = {l for _, r in sites for l in r["lits"]}
    bymod = Counter(node_mod[nid] for nid, _ in sites)
    fns_with = len({nid for nid, _ in sites})
    print(f"\n=== {label}")
    print(
        f"functions: {len(nodes)}  functions with refusal raises: {fns_with}  modules: {len({node_mod[n] for n in nodes})}"
    )
    print(f"raise sites: {len(sites)}  distinct literal messages: {len(lits)}")
    print("by kind:", dict(kinds))
    print("by class:", dict(Counter(r["cls"] for _, r in sites)))
    print("already coded (code= kw):", sum(1 for _, r in sites if r["coded"]))
    print("top modules:")
    for m, c in bymod.most_common(25):
        print(f"  {c:5d}  {m.removeprefix('reality.')}")
    print("modules with sites:", len(bymod))
    return sites, lits


reach_sites, reach_lits = summarize(
    seen,
    f"REACHABLE scope={scope} exclude_analytics={excl_analytics} roots={len(roots)}",
)
all_sp = [
    n for n in funcs if node_mod[n].startswith(("reality.services", "reality.tools"))
]
all_sites, all_lits = summarize(all_sp, "ALL functions in services/ + tools/")
summarize(list(funcs), "ALL functions in reality/*")
print("\nexception classes in family:", sorted(c.split(":")[1] for c in exc_classes))

if "--json" in sys.argv:
    out = sys.argv[sys.argv.index("--json") + 1]
    rows = sorted(
        (
            str(paths[node_mod[n]].relative_to(ROOT)),
            r["line"],
            n.split(":")[1],
            r["cls"],
            r["kind"],
            r["lits"][0] if r["lits"] else "",
        )
        for n, r in reach_sites
    )
    Path(out).write_text(json.dumps(rows, indent=0))
    print("wrote", out)

if "--why" in sys.argv:
    prefix = sys.argv[sys.argv.index("--why") + 1]
    parent = {}
    dq = deque(r for r in roots if r in funcs)
    for r in dq:
        parent[r] = None
    while dq:
        cur = dq.popleft()
        for nxt in sorted(edges[cur]):
            if nxt not in parent:
                parent[nxt] = cur
                dq.append(nxt)
    hits = [n for n in parent if node_mod[n].startswith(prefix)]
    shown = set()
    for h in hits:
        # first entry into the prefix
        chain = [h]
        while parent[chain[-1]]:
            chain.append(parent[chain[-1]])
        entry = next(c for c in reversed(chain) if node_mod[c].startswith(prefix))
        if entry in shown:
            continue
        shown.add(entry)
        chain = chain[chain.index(entry) :]
        print(
            "WHY:", " -> ".join(reversed([c.removeprefix("reality.") for c in chain]))
        )

if "--edges" in sys.argv:
    n = sys.argv[sys.argv.index("--edges") + 1]
    for e in sorted(edges[n]):
        print("EDGE", e.removeprefix("reality."))

if "--modstats" in sys.argv:
    rm = {node_mod[n] for n in seen if raises.get(n)}
    tot = sum(len(r) for n, r in raises.items() if node_mod[n] in rm)
    meth = sum(len(r) for n, r in raises.items() if node_class[n])
    print(
        f"MODSTATS modules-with-reachable-sites={len(rm)} all-sites-in-those-modules={tot} reachable={len(reach_sites)}"
    )
    print(f"MODSTATS raise sites inside class methods (whole package)={meth}")
    per = Counter(
        node_mod[n] for n, r in raises.items() for _ in r if node_mod[n] in rm
    )
    rper = Counter(node_mod[n] for n, _ in reach_sites)
    for m, c in per.most_common(12):
        print(
            f"MODSTATS {m.removeprefix('reality.')}: reachable {rper[m]} / module {c}"
        )

if "--registries" in sys.argv:
    # module-level variables whose value references functions (registries)
    reg = {}
    for m, tree in modules.items():
        for n in tree.body:
            if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None:
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                fns = set()
                for s in ast.walk(n.value):
                    if isinstance(s, (ast.Name, ast.Attribute)):
                        r = resolve_ref(m, {}, s)
                        if r in funcs:
                            fns.add(r)
                for t in targets:
                    if isinstance(t, ast.Name) and fns:
                        reg[(m, t.id)] = fns
    used = set()
    for nid in seen:
        mod = node_mod[nid]
        local = local_imports(mod, funcs[nid])
        for s in ast.walk(funcs[nid]):
            if isinstance(s, ast.Name):
                key = (mod, s.id)
                b = local.get(s.id) or mod_imports[mod].get(s.id)
                if b and b[1]:
                    key = (b[0], b[1])
                if key in reg:
                    used.add(key)
    for key in sorted(used):
        extra = reg[key] - seen
        xs = sum(len(raises.get(f, [])) for f in extra)
        print(
            f"REG {key[0].removeprefix('reality.')}.{key[1]}: {len(reg[key])} fns, {len(extra)} not otherwise reachable, their direct raise sites {xs}"
        )
