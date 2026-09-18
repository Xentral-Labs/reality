"""A Cypher-near surface for people who would rather read the path than the object.

Both surfaces compile to the same `Traversal`, and that object is what is stored,
fingerprinted and executed. Nothing here produces SQL; a name that is not in the
declaration is refused before anything else happens.

One deliberate divergence from Cypher, documented in the catalog and repeated in
every refusal that hits it: `RETURN` names declared measures rather than doing
arithmetic on properties. Literal Cypher allows `sum(o.gross_amount)` along a
fanned-out path and returns a multiplied total without complaint, which is exactly
the defect the model exists to remove. Adopting the syntax wholesale would import
it back through the front door.

    MATCH (c:party {id: $customer})<-[:ordered_by]-(o:order)
    WHERE o.ordered_at >= $from AND o.ordered_at < $until
    RETURN month(o.ordered_at), o.currency, sum(stated_order_amount)
    ORDER BY sum(stated_order_amount) DESC
    LIMIT 10
"""

from __future__ import annotations

import re
from typing import Any

from reality.domain.traversal import Traversal
from reality.services.core import InvalidOperation

BUCKETS = {"day", "week", "month", "quarter", "year"}
AGGREGATES = {"sum", "count", "total"}
COMPARISONS = {
    ">=": "gte",
    "<=": "lte",
    "<>": "ne",
    "!=": "ne",
    "=": "eq",
    ">": "gt",
    "<": "lt",
}

# Both patterns skip leading whitespace: without it "MATCH (a) -[:x]-> (b)" with
# ordinary spacing fails, which nobody would guess from the message.
NODE = re.compile(
    r"\s*\(\s*(?P<alias>\w*)\s*(?::\s*(?P<label>\w+))?\s*(?P<props>\{[^}]*\})?\s*\)"
)
RELATION = re.compile(
    r"\s*(?P<lead><-|-)\[\s*:\s*(?P<edge>\w+)"
    r"\s*(?:\*\s*(?P<low>\d+)\s*\.\.\s*(?P<high>\d+)\s*)?\](?P<tail>->|-)"
)
PROPERTY = re.compile(r"(\w+)\s*:\s*(\$\w+|'[^']*'|\"[^\"]*\"|-?\d+(?:\.\d+)?)")
CONDITION = re.compile(
    r"(?P<field>\w+\.\w+)\s*(?:(?P<is>IS\s+(?:NOT\s+)?NULL)|(?P<in>(?:NOT\s+)?IN)\s*(?P<list>\[[^\]]*\]|\$\w+)"
    r"|(?P<op>>=|<=|<>|!=|=|>|<)\s*(?P<value>\$\w+|'[^']*'|\"[^\"]*\"|-?\d+(?:\.\d+)?))",
    re.IGNORECASE,
)


class CypherRefused(InvalidOperation):
    """The text is not a question this surface accepts, and why.

    Like a traversal refusal, it carries a stable code beside its sentence: the
    caller branches on the code, the person reads the reason.
    """

    def __init__(self, message: str, code: str = "unreadable"):
        super().__init__(message)
        self.code = code


# Clause keywords are matched as whole patterns rather than bare words, because a
# node label is an ordinary word: searching for ORDER finds the `order` inside
# `(o:order)` and cuts the path in half.
KEYWORDS = {
    "MATCH": r"\bMATCH\b",
    "WHERE": r"\bWHERE\b",
    "RETURN": r"\bRETURN\b",
    "HAVING": r"\bHAVING\b",
    "ORDER BY": r"\bORDER\s+BY\b",
    "LIMIT": r"\bLIMIT\s+\d",
}

# An existence test is written as a block so its path cannot be confused with the
# main one: EXISTS { MATCH (o)-[:contains]->(l) WHERE l.sku = $sku }
EXISTENCE = re.compile(r"(?P<not>NOT\s+)?EXISTS\s*\{(?P<body>[^}]*)\}", re.IGNORECASE)


def _clause(text: str, name: str, following: tuple[str, ...]) -> str:
    start = re.search(KEYWORDS[name], text, re.IGNORECASE)
    if start is None:
        return ""
    rest = text[start.end() :]
    ends = [
        match.start()
        for word in following
        if (match := re.search(KEYWORDS[word], rest, re.IGNORECASE))
    ]
    return rest[: min(ends)] if ends else rest


def _value(token: str, parameters: dict[str, Any]) -> Any:
    token = token.strip()
    if token.startswith("$"):
        name = token[1:]
        if name not in parameters:
            raise CypherRefused(
                f"no value was supplied for ${name}", "missing_parameter"
            )
        return parameters[name]
    if token[:1] in "'\"":
        return token[1:-1]
    return float(token) if "." in token else int(token)


def _match(
    clause: str, parameters: dict[str, Any]
) -> tuple[dict, list[dict], list[dict]]:
    """Read the path: node, relationship, node, relationship, node, …"""
    root: dict | None = None
    follow: list[dict] = []
    filters: list[dict] = []
    counter = 0

    def read_node(segment: str, position: int) -> tuple[str, str | None, int]:
        nonlocal counter
        node = NODE.match(segment, position)
        if node is None:
            raise CypherRefused(
                f"expected a node pattern like (o:order) at {segment[position:][:24]!r}"
            )
        alias = node.group("alias")
        if not alias:
            counter += 1
            alias = f"_{counter}"
        for name, token in PROPERTY.findall(node.group("props") or ""):
            filters.append(
                {
                    "field": f"{alias}.{name}",
                    "op": "eq",
                    "value": _value(token, parameters),
                }
            )
        return alias, node.group("label"), node.end()

    for raw in clause.split(","):
        segment = raw.strip()
        if not segment:
            continue
        alias, label, position = read_node(segment, 0)
        if root is None:
            if not label:
                raise CypherRefused(
                    "the first node of a path names its kind, as (o:order)",
                    "untyped_start",
                )
            root = {"from": label, "as": alias}
        while position < len(segment):
            relation = RELATION.match(segment, position)
            if relation is None:
                raise CypherRefused(
                    "expected a relationship like -[:contains]-> at "
                    f"{segment[position:][:24]!r}"
                )
            inward = relation.group("lead") == "<-"
            outward = relation.group("tail") == "->"
            if inward == outward:
                raise CypherRefused(
                    "a relationship points one way: -[:edge]-> or <-[:edge]-",
                    "ambiguous_direction",
                )
            hop: dict[str, Any] = {
                "edge": relation.group("edge"),
                "direction": "in" if inward else "out",
                "from": alias,
            }
            if relation.group("low"):
                hop["depth"] = [int(relation.group("low")), int(relation.group("high"))]
            alias, _label, position = read_node(segment, relation.end())
            hop["as"] = alias
            follow.append(hop)
    if root is None:
        raise CypherRefused("MATCH names no path")
    return root, follow, filters


def _where(clause: str, parameters: dict[str, Any]) -> list[dict]:
    conditions: list[dict] = []
    remaining = clause.strip()
    while remaining:
        found = CONDITION.match(remaining)
        if not found:
            raise CypherRefused(
                "WHERE accepts comparisons on properties joined by AND; OR is not admitted",
                "unsupported_syntax",
            )
        field = found.group("field")
        if found.group("is"):
            op = "is_not_null" if "NOT" in found.group("is").upper() else "is_null"
            conditions.append({"field": field, "op": op})
        elif found.group("in"):
            token = found.group("list")
            items = (
                _value(token, parameters)
                if token.startswith("$")
                else [
                    _value(value, parameters)
                    for value in re.findall(
                        r"\$\w+|'[^']*'|\"[^\"]*\"|-?\d+(?:\.\d+)?", token
                    )
                ]
            )
            if not isinstance(items, list):
                raise CypherRefused("IN needs a list", "unsupported_syntax")
            conditions.append(
                {
                    "field": field,
                    "op": "not_in" if "NOT" in found.group("in").upper() else "in",
                    "value": items,
                }
            )
        else:
            conditions.append(
                {
                    "field": field,
                    "op": COMPARISONS[found.group("op")],
                    "value": _value(found.group("value"), parameters),
                }
            )
        remaining = remaining[found.end() :].strip()
        if remaining:
            joined = re.match(r"AND\b", remaining, re.IGNORECASE)
            if not joined:
                raise CypherRefused(
                    "WHERE joins comparisons with AND; OR is not admitted",
                    "unsupported_syntax",
                )
            remaining = remaining[joined.end() :].strip()
            if not remaining:
                raise CypherRefused(
                    "AND needs another comparison", "unsupported_syntax"
                )
    return conditions


def _having(clause: str) -> list[dict]:
    """A filter that runs after grouping, so it names a measure, not a property."""
    out: list[dict] = []
    if not clause.strip():
        return out
    for term in re.split(r"\s+AND\s+", clause.strip(), flags=re.IGNORECASE):
        found = re.fullmatch(
            r"(?:\w+\s*\(\s*)?(?P<measure>[\w.]+?)\s*\)?\s*(?P<op>>=|<=|<>|!=|=|>|<)\s*"
            r"(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
            term,
        )
        if not found:
            raise CypherRefused(
                "HAVING compares declared measures with numbers joined by AND",
                "unsupported_syntax",
            )
        if "." in found.group("measure"):
            raise CypherRefused(
                "HAVING filters a declared measure, not a property",
                "unsupported_syntax",
            )
        out.append(
            {
                "measure": found.group("measure"),
                "op": COMPARISONS[found.group("op")],
                "value": float(found.group("value")),
            }
        )
    if clause.strip() and not out:
        raise CypherRefused(
            "HAVING compares a measure with a number", "unsupported_syntax"
        )
    return out


def _existence(clause: str, parameters: dict[str, Any]) -> tuple[list[dict], str]:
    """Pull the EXISTS blocks out of WHERE, and give back what is left."""
    tests: list[dict] = []
    for found in EXISTENCE.finditer(clause):
        body = found.group("body")
        inner_match = _clause(body, "MATCH", ("WHERE",))
        inner_where = _clause(body, "WHERE", ())
        if not inner_match.strip():
            raise CypherRefused(
                "an existence test names a path with MATCH", "no_match_clause"
            )
        # The block continues the outer path, so its first node is already reached
        # and carries no kind of its own.
        # The synthetic start only gives the block a node to hang the first
        # relationship on. Its alias must not travel onwards: it would collide
        # with a real alias of the outer question, and the test would then be
        # resolved against the wrong record.
        explicit_origin = inner_match.lstrip().startswith("(")
        prefix = "(__start__:_), " if explicit_origin else "(__start__:_)"
        _root, follow, pattern = _match(prefix + inner_match, parameters)
        if follow and not explicit_origin:
            follow[0] = {
                key: value for key, value in follow[0].items() if key != "from"
            }
        tests.append(
            {
                "follow": follow,
                "filter": pattern + _where(inner_where, parameters),
                "negated": bool(found.group("not")),
            }
        )
    remainder = EXISTENCE.sub("", clause)
    remainder = re.sub(r"\bAND\s*(?=AND\b)", "", remainder, flags=re.IGNORECASE)
    remainder = re.sub(
        r"(?:^\s*AND\b|\bAND\s*$)", "", remainder, flags=re.IGNORECASE
    ).strip()
    return tests, remainder


def _return(clause: str) -> tuple[list[dict], list[str]]:
    groupings: list[dict] = []
    measures: list[str] = []
    for item in [part.strip() for part in clause.split(",") if part.strip()]:
        named = re.fullmatch(r"(.+?)\s+AS\s+(`[^`]+`|\w+)", item, re.IGNORECASE)
        alias = named.group(2).strip("`") if named else None
        item = named.group(1).strip() if named else item
        call = re.fullmatch(r"(\w+)\s*\(\s*([\w.]+)\s*\)", item)
        if call:
            function, argument = call.group(1).lower(), call.group(2)
            if function in BUCKETS:
                groupings.append(
                    {"field": argument, "bucket": function, "as": alias or function}
                )
                continue
            if function in AGGREGATES:
                if "." in argument:
                    raise CypherRefused(
                        f"{item} does arithmetic on a property. This surface names declared "
                        "measures instead, because summing a property along a path that fans "
                        "out returns a multiplied total without complaint. Ask the catalog "
                        "which measure lives at the grain you reached."
                    )
                if alias:
                    raise CypherRefused(
                        "A declared measure keeps its name; a measure alias is not admitted"
                    )
                measures.append(argument)
                continue
            raise CypherRefused(f"{function}() is not admitted in RETURN")
        if "." in item:
            groupings.append({"field": item, **({"as": alias} if alias else {})})
            continue
        if alias:
            raise CypherRefused(
                "A declared measure keeps its name; a measure alias is not admitted"
            )
        measures.append(item)
    if not groupings and not measures:
        raise CypherRefused("RETURN names nothing")
    return groupings, measures


def parse(text: str, parameters: dict[str, Any] | None = None) -> Traversal:
    """Read the text into the same object the typed surface produces."""
    parameters = parameters or {}
    # A write attempt is named as one before anything else, so the answer is about
    # what was asked for rather than about the shape of the text.
    for forbidden in (
        "CREATE",
        "MERGE",
        "DELETE",
        "SET",
        "REMOVE",
        "DETACH",
        "CALL",
        "LOAD",
    ):
        if re.search(rf"\b{forbidden}\b", text, re.IGNORECASE):
            raise CypherRefused(
                f"{forbidden} is not admitted; this surface only reads", "read_only"
            )
    if not re.search(r"\bMATCH\b", text, re.IGNORECASE):
        raise CypherRefused("a question starts with MATCH", "no_match_clause")

    match_clause = _clause(text, "MATCH", ("WHERE", "RETURN", "ORDER BY", "LIMIT"))
    where_clause = _clause(text, "WHERE", ("RETURN", "ORDER BY", "LIMIT"))
    return_clause = _clause(text, "RETURN", ("HAVING", "ORDER BY", "LIMIT"))
    having_clause = _clause(text, "HAVING", ("ORDER BY", "LIMIT"))
    order_clause = _clause(text, "ORDER BY", ("LIMIT",))
    # Read the number from the text rather than from a clause: the LIMIT keyword
    # pattern has to include a digit so it cannot match a property called limit,
    # which means the clause after it starts past that digit and is empty.
    limit = re.search(r"\bLIMIT\s+(\d+)", text, re.IGNORECASE)

    if not return_clause.strip():
        raise CypherRefused(
            "a question says what it wants back, with RETURN", "no_return_clause"
        )

    root, follow, pattern_filters = _match(match_clause, parameters)
    tests, where_clause = _existence(where_clause, parameters)
    conditions = pattern_filters + _where(where_clause, parameters)
    groupings, measures = _return(return_clause)

    order_by = []
    for item in [part.strip() for part in order_clause.split(",") if part.strip()]:
        descending = bool(re.search(r"\bDESC\b", item, re.IGNORECASE))
        name = re.sub(r"\b(ASC|DESC)\b", "", item, flags=re.IGNORECASE).strip()
        call = re.fullmatch(r"\w+\s*\(\s*([\w.]+)\s*\)", name)
        order_by.append(
            {"by": call.group(1) if call else name.strip("`"), "descending": descending}
        )

    query: dict[str, Any] = {
        **root,
        "follow": follow,
        "filter": conditions,
        "measures": measures,
        "group_by": groupings,
        "having": _having(having_clause),
        "exists": tests,
        "order_by": order_by,
    }
    if limit:
        query["limit"] = int(limit.group(1))
    try:
        return Traversal.model_validate(query)
    except ValueError as error:
        raise CypherRefused(str(error)) from error


def format_query(query: Traversal) -> dict[str, Any]:
    """Produce an editable path with separately bound values, never SQL.

    All clauses travel with the question. Simple controls may not understand an
    existence test or recursion, but the expert editor must not lose them.
    """
    parameters: dict[str, Any] = {}
    operators = {value: key for key, value in COMPARISONS.items()}

    def identifier(value: str) -> str:
        if not re.fullmatch(r"\w+", value):
            raise CypherRefused(
                "This identifier cannot be represented in path syntax",
                "unsupported_syntax",
            )
        return value

    def bound(value: Any) -> str:
        key = f"value{len(parameters) + 1}"
        parameters[key] = value
        return f"${key}"

    def conditions(values) -> list[str]:
        result = []
        for condition in values:
            field = ".".join(identifier(part) for part in condition.field.split("."))
            if condition.op in {"is_null", "is_not_null"}:
                result.append(
                    f"{field} IS {'NOT ' if condition.op == 'is_not_null' else ''}NULL"
                )
            elif condition.op in {"in", "not_in"}:
                result.append(
                    f"{field} {'NOT ' if condition.op == 'not_in' else ''}IN {bound(condition.value)}"
                )
            else:
                result.append(
                    f"{field} {operators[condition.op]} {bound(condition.value)}"
                )
        return result

    def paths(hops, origin: str) -> str:
        segments = []
        for hop in hops:
            start = identifier(hop.from_ or origin)
            target = identifier(hop.as_)
            depth = f"*{hop.depth[0]}..{hop.depth[1]}" if hop.depth else ""
            edge = identifier(hop.edge)
            relation = (
                f"<-[:{edge}{depth}]-"
                if hop.direction == "in"
                else f"-[:{edge}{depth}]->"
            )
            segments.append(f"({start}){relation}({target})")
            origin = hop.as_
        return ", ".join(segments)

    def quoted(value: str) -> str:
        if (
            "`" in value
            or "," in value
            or re.search(
                r"\b(?:MATCH|WHERE|RETURN|HAVING|ORDER BY|LIMIT|CREATE|SET|DELETE)\b",
                value,
                re.IGNORECASE,
            )
        ):
            raise CypherRefused(
                "This column alias cannot be represented in path syntax",
                "unsupported_syntax",
            )
        return f"`{value}`"

    text = f"MATCH ({identifier(query.as_)}:{identifier(query.from_)})"
    if query.follow:
        text += ", " + paths(query.follow, query.as_)
    where = conditions(query.filter)
    for test in query.exists:
        inner = paths(test.follow, query.as_)
        filtered = conditions(test.filter)
        where.append(
            f"{'NOT ' if test.negated else ''}EXISTS {{ MATCH {inner}"
            + (" WHERE " + " AND ".join(filtered) if filtered else "")
            + " }"
        )
    if where:
        text += "\nWHERE " + " AND ".join(where)
    returned = []
    for group in query.group_by:
        field = ".".join(identifier(part) for part in group.field.split("."))
        term = f"{group.bucket}({field})" if group.bucket else field
        if group.as_ or group.bucket:
            term += " AS " + quoted(group.as_ or group.field)
        returned.append(term)
    returned.extend(identifier(measure) for measure in query.measures)
    text += "\nRETURN " + ", ".join(returned)
    if query.having:
        text += "\nHAVING " + " AND ".join(
            f"{identifier(item.measure)} {operators[item.op]} {item.value}"
            for item in query.having
        )
    if query.order_by:
        text += "\nORDER BY " + ", ".join(
            (item.by if re.fullmatch(r"[\w.]+", item.by) else quoted(item.by))
            + (" DESC" if item.descending else " ASC")
            for item in query.order_by
        )
    text += f"\nLIMIT {query.limit}"
    return {"path": text, "parameters": parameters}
