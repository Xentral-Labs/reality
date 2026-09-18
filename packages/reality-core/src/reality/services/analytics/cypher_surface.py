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
    r"(?P<field>\w+\.\w+)\s*(?:(?P<is>IS\s+(?:NOT\s+)?NULL)|(?P<in>IN)\s*(?P<list>\[[^\]]*\])"
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
    consumed = 0
    for found in CONDITION.finditer(clause):
        consumed += found.end() - found.start()
        field = found.group("field")
        if found.group("is"):
            negated = "NOT" in found.group("is").upper()
            conditions.append(
                {"field": field, "op": "is_not_null" if negated else "is_null"}
            )
        elif found.group("in"):
            items = [
                _value(token, parameters)
                for token in re.findall(
                    r"\$\w+|'[^']*'|\"[^\"]*\"|-?\d+(?:\.\d+)?", found.group("list")
                )
            ]
            conditions.append({"field": field, "op": "in", "value": items})
        else:
            conditions.append(
                {
                    "field": field,
                    "op": COMPARISONS[found.group("op")],
                    "value": _value(found.group("value"), parameters),
                }
            )
    leftovers = re.sub(r"\bAND\b", "", clause, flags=re.IGNORECASE).strip()
    if conditions and len(leftovers) > consumed + 8 * len(conditions):
        raise CypherRefused(
            "WHERE accepts comparisons on properties joined by AND, and nothing else"
        )
    if "OR" in re.findall(r"\b\w+\b", clause.upper()):
        raise CypherRefused(
            "WHERE joins its comparisons with AND; OR is not admitted",
            "unsupported_syntax",
        )
    return conditions


def _having(clause: str) -> list[dict]:
    """A filter that runs after grouping, so it names a measure, not a property."""
    out: list[dict] = []
    for found in re.finditer(
        # The measure pattern has to see the dot, or "o.number" arrives as "number"
        # and the check below never fires.
        r"(?:\w+\s*\(\s*)?(?P<measure>[\w.]+?)\s*\)?\s*(?P<op>>=|<=|<>|!=|=|>|<)\s*"
        r"(?P<value>-?\d+(?:\.\d+)?)",
        clause,
    ):
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
        _root, follow, pattern = _match(f"(__start__:_){inner_match}", parameters)
        if follow:
            follow[0] = {k: v for k, v in follow[0].items() if k != "from"}
        tests.append(
            {
                "follow": follow,
                "filter": pattern + _where(inner_where, parameters),
                "negated": bool(found.group("not")),
            }
        )
    return tests, EXISTENCE.sub("", clause)


def _return(clause: str) -> tuple[list[dict], list[str]]:
    groupings: list[dict] = []
    measures: list[str] = []
    for item in [part.strip() for part in clause.split(",") if part.strip()]:
        call = re.fullmatch(r"(\w+)\s*\(\s*([\w.]+)\s*\)", item)
        if call:
            function, argument = call.group(1).lower(), call.group(2)
            if function in BUCKETS:
                groupings.append(
                    {"field": argument, "bucket": function, "as": function}
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
                measures.append(argument)
                continue
            raise CypherRefused(f"{function}() is not admitted in RETURN")
        if "." in item:
            groupings.append({"field": item})
            continue
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
            {"by": call.group(1) if call else name, "descending": descending}
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
