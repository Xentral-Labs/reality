"""Dynamic syntax evidence and controlled business wording; never execute source."""

from __future__ import annotations

import ast
import re
import textwrap

from reality.domain.business_blueprints import RuleEdge, RuleNode, SourceEvidence

# Vocabulary only: expressions, operators, values and outcomes always come from source.
LABELS = {
    "limit": "credit limit", "exposure": "credit exposure", "over_limit": "credit limit exceeded",
    "open_invoices": "open invoice amount", "open_orders": "uninvoiced order amount",
    "available_credits": "available customer credits", "uninvoiced": "uninvoiced quantity",
    "ZERO": "0", "True": "yes", "False": "no", "None": "not supplied",
    "gross_amount": "stated gross amount", "unit_price": "stated unit price",
    "holds": "active credit holds", "stated": "stated value", "party": "business partner",
    "commitment": "delivery commitment", "promises": "delivery commitments", "order": "sales order",
    "checked_quantity": "quantity being checked", "required": "required prepayment amount",
    "received": "received prepayment amount", "remaining": "remaining prepayment amount",
    "operational_blockers": "operational delivery blockers", "blockers": "delivery blockers",
    "qualifying": "qualifying payment allocations", "reversed_groups": "reversed posting groups",
    "counted": "counted order lines", "unpriced": "unpriced order lines", "other": "excluded currency lines",
    "as_of": "evaluation time", "tenant_id": "current company identity",
    "session": "application transaction", "document": "evidence document",
    "physical_quantity": "unblocked physical stock", "reserved_quantity": "reserved stock",
    "ready_quantity": "physically covered reserved stock", "term": "payment term",
    "by_commitment": "holds grouped by delivery commitment", "hold": "execution hold",
}
COMPARISONS = {
    ast.Gt: "is greater than", ast.GtE: "is greater than or equal to", ast.Lt: "is less than",
    ast.LtE: "is less than or equal to", ast.Eq: "equals", ast.NotEq: "differs from",
    ast.Is: "is", ast.IsNot: "is not", ast.In: "is included in", ast.NotIn: "is not included in",
}


def business_label(name: str) -> str:
    return LABELS.get(name, re.sub(r"[_\.]+", " ", name).strip())


def expression_text(node: ast.AST | None) -> str:
    """Preserve syntax semantics; business labels do not define alternative rules."""
    if node is None:
        return "no value"
    if isinstance(node, ast.Name):
        return business_label(node.id)
    if isinstance(node, ast.Constant):
        if node.value is None:
            return "not supplied"
        if isinstance(node.value, bool):
            return "yes" if node.value else "no"
        return repr(node.value) if isinstance(node.value, str) else str(node.value)
    if isinstance(node, ast.Attribute):
        return f"{expression_text(node.value)}: {business_label(node.attr)}"
    if isinstance(node, ast.Subscript):
        return f"{expression_text(node.value)}: {expression_text(node.slice).strip(chr(39))}"
    if isinstance(node, ast.Compare):
        parts = [expression_text(node.left)]
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            parts.extend([COMPARISONS[type(op)], expression_text(comparator)])
        return " ".join(parts)
    if isinstance(node, ast.BoolOp):
        return (" and " if isinstance(node.op, ast.And) else " or ").join(f"({expression_text(v)})" for v in node.values)
    if isinstance(node, ast.UnaryOp):
        return ("not " if isinstance(node.op, ast.Not) else "negative " if isinstance(node.op, ast.USub) else "") + expression_text(node.operand)
    if isinstance(node, ast.BinOp):
        operator = {ast.Add: "+", ast.Sub: "−", ast.Mult: "×", ast.Div: "÷", ast.BitAnd: "and", ast.BitOr: "or"}.get(type(node.op), ast.unparse(node.op))
        return f"({expression_text(node.left)} {operator} {expression_text(node.right)})"
    if isinstance(node, ast.IfExp):
        return f"{expression_text(node.body)} when {expression_text(node.test)}; otherwise {expression_text(node.orelse)}"
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return "[" + ", ".join(expression_text(e) for e in node.elts) + "]"
    if isinstance(node, ast.Dict):
        return "; ".join(f"{expression_text(k)}: {expression_text(v)}" for k, v in zip(node.keys, node.values, strict=True))
    if isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)):
        value = expression_text(node.value) if isinstance(node, ast.DictComp) else expression_text(node.elt)
        for gen in node.generators:
            value += f" for each {expression_text(gen.target)} in {expression_text(gen.iter)}"
            if gen.ifs:
                value += "; include only when " + " and ".join(expression_text(i) for i in gen.ifs)
        return value
    if isinstance(node, ast.Lambda):
        return "for " + ", ".join(business_label(a.arg) for a in node.args.args) + ": " + expression_text(node.body)
    if isinstance(node, ast.NamedExpr):
        return f"set {expression_text(node.target)} to {expression_text(node.value)}"
    if isinstance(node, ast.JoinedStr):
        return "".join(str(part.value) if isinstance(part, ast.Constant) else "{" + expression_text(part.value) + "}" for part in node.values)
    if isinstance(node, ast.Starred):
        return "each value of " + expression_text(node.value)
    if isinstance(node, ast.Slice):
        return "range " + expression_text(node.lower) + " to " + expression_text(node.upper)
    if isinstance(node, ast.Call):
        name = ast.unparse(node.func)
        args = [expression_text(a) for a in node.args]
        args += [f"{business_label(k.arg or 'additional fields')}: {expression_text(k.value)}" for k in node.keywords]
        if name in {"Decimal", "decimal", "str", "bool"} and len(node.args) == 1:
            return expression_text(node.args[0])
        if name == "sum":
            return "sum of " + (args[0] if args else "values") + (f"; starting at {args[1]}" if len(args) > 1 else "")
        if name in {"min", "max"}:
            return ("smallest of " if name == "min" else "largest of ") + ", ".join(args)
        if name == "len":
            return "number of " + ", ".join(args)
        if name.endswith(".where"):
            return "select records where " + " and ".join(args)
        return f"{business_label(name)} ({'; '.join(args)})"
    return ast.unparse(node)


def source_tree(source: SourceEvidence) -> ast.FunctionDef | ast.AsyncFunctionDef:
    tree = ast.parse(textwrap.dedent(source.code))
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    return node


def analyze_function(source: SourceEvidence) -> tuple[list[RuleNode], list[RuleEdge], list[str]]:
    function = source_tree(source)
    lines = source.code.splitlines()
    nodes: list[RuleNode] = []
    edges: list[RuleEdge] = []
    limitations: list[str] = []
    markers: set[str] = set()
    counter = 0
    active_function = source.function
    loop_stack: list[tuple[str, list[tuple[str, str]]]] = []

    def add(kind: str, statement: ast.AST, text: str, expression: str, context: tuple[str, ...]) -> RuleNode:
        nonlocal counter
        counter += 1
        line = statement.lineno
        marker = re.search(r"#\s*reality-rule:\s*([\w.:-]+)", lines[line - 2]) if line > 1 else None
        durable = marker is not None
        identity = marker.group(1) if marker else f"{source.function}:{source.digest[:12]}:{counter}"
        if identity in markers:
            raise ValueError(f"Duplicate rule identity: {identity}")
        markers.add(identity)
        condition_source = getattr(statement, "test", None) if isinstance(statement, (ast.If, ast.While, ast.Assert)) else getattr(statement, "value", None)
        predicates = []
        if condition_source is not None:
            for part in ast.walk(condition_source):
                if isinstance(part, ast.Compare):
                    predicates.append(ast.unparse(part))
                elif isinstance(part, ast.IfExp):
                    predicates.append(ast.unparse(part.test))
                elif isinstance(part, ast.comprehension):
                    predicates.extend(ast.unparse(test) for test in part.ifs)
                elif isinstance(part, ast.Call) and isinstance(part.func, ast.Attribute) and part.func.attr in {"is_", "is_not", "isnot"}:
                    predicates.append(ast.unparse(part))
        predicates = tuple(dict.fromkeys(predicates))
        n = RuleNode(id=identity, function=active_function, kind=kind, text=text,
                     expression=expression, evidence_id=source.id,
                     line=source.start_line + line - 1,
                     end_line=source.start_line + getattr(statement, "end_lineno", line) - 1,
                     predicates=predicates, durable=durable, context=context)
        nodes.append(n)
        return n

    def connect(pending: list[tuple[str, str]], target: str) -> None:
        edges.extend(RuleEdge(source=n, target=target, outcome=o) for n, o in pending)

    def block(statements: list[ast.stmt], pending: list[tuple[str, str]], context: tuple[str, ...] = ()) -> list[tuple[str, str]]:
        nonlocal active_function
        for statement in statements:
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
                continue  # A docstring is context, not proof of behavior.
            expression = ast.unparse(statement)
            if isinstance(statement, ast.If):
                condition = expression_text(statement.test)
                decision = add("decision", statement, "Check whether " + condition, ast.unparse(statement.test), context)
                connect(pending, decision.id)
                yes = block(statement.body, [(decision.id, "yes")], (*context, condition))
                no = block(statement.orelse, [(decision.id, "no")], (*context, "not (" + condition + ")")) if statement.orelse else [(decision.id, "no")]
                pending = yes + no
                continue
            if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
                condition = expression_text(statement.iter) if isinstance(statement, (ast.For, ast.AsyncFor)) else expression_text(statement.test)
                loop = add("loop", statement, "Process each eligible entry: " + condition, expression.split(":\n")[0], context)
                connect(pending, loop.id)
                breaks: list[tuple[str, str]] = []
                loop_stack.append((loop.id, breaks))
                body = block(statement.body, [(loop.id, "entry")], (*context, "for each " + condition))
                loop_stack.pop()
                connect(body, loop.id)
                pending = [(loop.id, "finished")]
                if statement.orelse:
                    pending = block(statement.orelse, pending, context)
                pending += breaks
                continue
            if isinstance(statement, ast.Try):
                if statement.finalbody and any(isinstance(part, (ast.Return, ast.Break, ast.Continue, ast.Raise)) for child in statement.body for part in ast.walk(child)):
                    limitations.append(f"Finally transitions after early exits are not fully resolved at {active_function}:{statement.lineno}; inspect the exact source.")
                guard = add("decision", statement, "Attempt the following operation; handle the stated failures", "try", context)
                connect(pending, guard.id)
                body = block(statement.body, [(guard.id, "attempt")], context)
                body = block(statement.orelse, body, context)
                for handler in statement.handlers:
                    body += block(handler.body, [(guard.id, "failure: " + expression_text(handler.type))], context)
                pending = block(statement.finalbody, body, context)
                continue
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                guard = add("context", statement, "Within " + "; ".join(expression_text(i.context_expr) for i in statement.items), expression.split(":\n")[0], context)
                connect(pending, guard.id)
                pending = block(statement.body, [(guard.id, "next")], context)
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                previous = active_function
                active_function = previous + "." + statement.name
                block(statement.body, [])
                active_function = previous
                continue
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                continue
            terminal = False
            if isinstance(statement, ast.Raise):
                kind, text, terminal = "refusal", "Stop with " + expression_text(statement.exc), True
            elif isinstance(statement, ast.Return):
                kind, text, terminal = "result", "Return " + expression_text(statement.value), True
            elif isinstance(statement, (ast.Continue, ast.Break)):
                kind, text, terminal = "control", "Skip this entry" if isinstance(statement, ast.Continue) else "End this loop", True
            elif isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                value = statement.value
                kind = "calculation"
                if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {"scalar", "scalars", "execute"} for n in ast.walk(value)):
                    kind = "read"
                text = ("Read " if kind == "read" else "Set ") + ", ".join(expression_text(t) for t in targets) + " = " + expression_text(value)
                if isinstance(statement, ast.AugAssign):
                    text = "Update " + expression_text(statement.target) + " using " + expression_text(value) + " (" + type(statement.op).__name__ + ")"
            elif isinstance(statement, ast.Expr):
                kind, text = "call", "Use " + expression_text(statement.value)
                if isinstance(statement.value, ast.Call) and ast.unparse(statement.value.func).endswith((".add", ".commit", ".flush", "emit_business_event")):
                    kind = "effect"
            elif isinstance(statement, ast.Assert):
                kind, text = "decision", "Require " + expression_text(statement.test)
            else:
                kind, text = "opaque", "Source step requires further interpretation: " + expression
                limitations.append(f"Unsupported {type(statement).__name__} at {source.function}:{statement.lineno}")
            if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Return, ast.Assert, ast.Raise)):
                unsupported = {type(part).__name__ for part in ast.walk(statement) if isinstance(part, (ast.Await, ast.Yield, ast.YieldFrom))}
                for part in sorted(unsupported):
                    limitations.append(f"Unsupported expression {part} at {active_function}:{statement.lineno}; exact source remains available.")
            n = add(kind, statement, text, expression, context)
            connect(pending, n.id)
            if isinstance(statement, ast.Continue) and loop_stack:
                edges.append(RuleEdge(source=n.id, target=loop_stack[-1][0], outcome="next entry"))
            elif isinstance(statement, ast.Break) and loop_stack:
                loop_stack[-1][1].append((n.id, "loop ended"))
            pending = [] if terminal else [(n.id, "next")]
        return pending

    block(function.body, [])
    return nodes, edges, limitations
