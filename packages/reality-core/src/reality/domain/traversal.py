"""A question as a checkable object: a path, some filters, and measures.

The reason this is an object rather than text is that it can be held against the
model before it runs, and read back to somebody in business language before they
confirm it. A SQL string cannot be shown to a merchant for confirmation, and a
language model produces a small constrained object far more reliably than it
produces correct text.

Nothing here knows about tables or SQL. What a path means — where it fans out,
which measure may be summed along it — is decided in
`services/analytics/traversal.py` against the declaration.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Direction = Literal["out", "in"]
Operator = Literal[
    "eq", "ne", "in", "not_in", "lt", "lte", "gt", "gte", "is_null", "is_not_null"
]
TimeBucket = Literal["day", "week", "month", "quarter", "year"]


class QueryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)


class Parameter(QueryModel):
    """A value supplied separately from the question, always bound, never inlined."""

    param: str


class Hop(QueryModel):
    """One step along a declared edge.

    `direction` is `out` when the edge is followed the way it was declared and
    `in` when it is followed backwards — a customer reaching its orders follows
    `ordered_by` inwards, because the edge was declared from the order.
    """

    edge: str
    direction: Direction = "out"
    as_: str = Field(alias="as")
    from_: str | None = Field(default=None, alias="from")
    depth: tuple[int, int] | None = None

    @model_validator(mode="after")
    def check(self) -> Hop:
        if self.depth:
            low, high = self.depth
            if low < 1 or high < low:
                raise ValueError("a depth range runs from at least one upwards")
        return self


class Condition(QueryModel):
    """One filter on a property of a node already reached by the path."""

    field: str
    op: Operator
    value: Any = None

    @model_validator(mode="after")
    def check(self) -> Condition:
        if self.op in ("is_null", "is_not_null"):
            if self.value is not None:
                raise ValueError(f"{self.op} takes no value")
        elif self.value is None:
            raise ValueError(f"{self.op} needs a value")
        if self.field.count(".") != 1:
            raise ValueError(f"a field is alias.property, got {self.field!r}")
        return self


class Grouping(QueryModel):
    """One axis of the result: a property, or a time bucket over a timestamp."""

    field: str
    bucket: TimeBucket | None = None
    as_: str | None = Field(default=None, alias="as")

    @model_validator(mode="after")
    def check(self) -> Grouping:
        if self.field.count(".") != 1:
            raise ValueError(f"a field is alias.property, got {self.field!r}")
        return self


class Ordering(QueryModel):
    by: str
    descending: bool = False


class Traversal(QueryModel):
    """The whole question."""

    from_: str = Field(alias="from")
    as_: str = Field(default="root", alias="as")
    follow: tuple[Hop, ...] = ()
    filter: tuple[Condition, ...] = ()
    measures: tuple[str, ...] = ()
    group_by: tuple[Grouping, ...] = ()
    order_by: tuple[Ordering, ...] = ()
    limit: int = Field(default=200, ge=1)

    @model_validator(mode="after")
    def check(self) -> Traversal:
        aliases = [self.as_, *(hop.as_ for hop in self.follow)]
        duplicates = {a for a in aliases if aliases.count(a) > 1}
        if duplicates:
            raise ValueError(f"alias {sorted(duplicates)} is used twice")
        known = {self.as_}
        for hop in self.follow:
            origin = hop.from_ or aliases[aliases.index(hop.as_) - 1]
            if origin not in known:
                raise ValueError(
                    f"hop {hop.edge} starts at {origin!r}, which the path has not reached"
                )
            known.add(hop.as_)
        for condition in self.filter:
            alias = condition.field.split(".")[0]
            if alias not in known:
                raise ValueError(
                    f"filter on {condition.field} names an unreached alias"
                )
        for grouping in self.group_by:
            alias = grouping.field.split(".")[0]
            if alias not in known:
                raise ValueError(f"group by {grouping.field} names an unreached alias")
        if not self.measures and not self.group_by:
            raise ValueError("a question asks for at least a measure or a grouping")
        return self

    def aliases(self) -> tuple[str, ...]:
        return (self.as_, *(hop.as_ for hop in self.follow))
