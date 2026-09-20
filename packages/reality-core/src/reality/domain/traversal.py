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


class StrictModel(BaseModel):
    """What a caller may send: named fields only, and nothing else accepted.

    Not frozen, because a request is built up before it is validated. It lives
    beside the query it accompanies rather than in the retired definition model
    it came from.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


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


class Having(QueryModel):
    """A filter on an aggregate: customers with at least three orders.

    It reads like a filter but runs after grouping, which is why it names a
    measure rather than a property — the measure is the only thing that exists
    at that point.
    """

    measure: str
    op: Literal["eq", "ne", "lt", "lte", "gt", "gte"]
    value: float


class Existence(QueryModel):
    """A sub-path that must exist, without joining it into the answer.

    Joining it would multiply the rows; testing it does not. That is the whole
    reason this is a separate clause rather than another hop.
    """

    follow: tuple[Hop, ...]
    filter: tuple[Condition, ...] = ()
    negated: bool = False

    @model_validator(mode="after")
    def check(self) -> Existence:
        if not self.follow:
            raise ValueError("an existence test follows at least one edge")
        return self


class InventoryCostContext(QueryModel):
    """One retained joint confirmation, never an implicit latest valuation."""

    action_id: str = Field(min_length=1, max_length=128, pattern=r".*\S.*")
    mode: Literal["historical"] = "historical"


class ContributionCostContext(InventoryCostContext):
    """One retained joint scope, optionally requiring unchanged knowledge."""

    mode: Literal["historical", "current"] = "historical"


class CapturedCostContext(QueryModel):
    """One sealed captured report generation, never a mutable latest pointer."""

    generation_id: str = Field(min_length=1, max_length=128, pattern=r".*\S.*")


class CompanyCostContext(QueryModel):
    """One verified financial company generation, never an implicit latest pointer."""

    generation_id: str = Field(min_length=1, max_length=128, pattern=r".*\S.*")


class Traversal(QueryModel):
    """The whole question."""

    from_: str = Field(alias="from")
    inventory_cost_context: InventoryCostContext | None = None
    contribution_cost_context: ContributionCostContext | None = None
    captured_cost_context: CapturedCostContext | None = None
    company_cost_context: CompanyCostContext | None = None
    as_: str = Field(default="root", alias="as")
    follow: tuple[Hop, ...] = ()
    filter: tuple[Condition, ...] = ()
    measures: tuple[str, ...] = ()
    group_by: tuple[Grouping, ...] = ()
    having: tuple[Having, ...] = ()
    exists: tuple[Existence, ...] = ()
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
        for condition in self.having:
            if condition.measure not in self.measures:
                raise ValueError(
                    f"having names {condition.measure!r}, which the question does not ask for"
                )
        for test in self.exists:
            origin = test.follow[0].from_ or self.as_
            if origin not in known:
                raise ValueError(
                    f"an existence test starts at {origin!r}, which the path has not reached"
                )
        if not self.measures and not self.group_by:
            raise ValueError("a question asks for at least a measure or a grouping")
        return self

    def aliases(self) -> tuple[str, ...]:
        return (self.as_, *(hop.as_ for hop in self.follow))
