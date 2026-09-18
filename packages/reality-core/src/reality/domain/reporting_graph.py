"""The declared property graph: what a node, an edge and a measure must say.

Three declarations carry the whole design, because they are the three things a
traversal cannot infer and a query author is never reminded of:

    grain          what one row of a node is, so a measure is summed once per thing
    multiplicity   whether an edge fans out, so the compiler knows when to fold
    unit and additivity   what a number is, so it is not added to something else

A fourth joined them once the correction mechanisms were read: the same table can
net its own corrections out, or hold revisions where only the latest is true, and
summing them follows opposite rules. So a node says that too.

Everything else about a query stays free. These four cannot be, and that is the
entire boundary between flexible and wrong. A declaration missing one of them is
refused here rather than producing a confident wrong number later.

Storage coupling stays out of this module by intention: whether the named tables
and columns actually exist is checked against the live schema in
`services/analytics/graph_model.py`, because that check needs the database
metadata and this one does not.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Multiplicity = Literal["n:1", "1:n"]
Direction = Literal["out", "in"]
Corrections = Literal["replace", "revise", "compensate"]
UnitKind = Literal["currency", "measure", "count"]
CyclePolicy = Literal["stop"]
Coverage = Literal["current", "activity_period", "as_of_effective", "as_of_knowledge"]
UnknownPolicy = Literal["keep"]


class GraphModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)


class Label(GraphModel):
    """What a person calls this, in the languages the product speaks.

    The declaration is the only place that knows both the column and the word for
    it, so the word lives here rather than in each surface. Chat, terminal and
    browser then say the same thing, and a question can be read back to somebody
    in their own language — which is the whole reason the query is an object.
    """

    en: str
    de: str | None = None

    def pick(self, language: str = "en") -> str:
        return getattr(self, language, None) or self.en


class Property(GraphModel):
    """A readable field of a node.

    `enumerated` says the column holds a short fixed vocabulary — a type, a
    status — worth listing in the catalog. The values themselves are not
    declared here: they are read from the company being asked about, so they
    cannot drift away from what the records actually say.
    """

    column: str
    label: Label
    enumerated: bool = False
    temporal: Literal["date"] | None = None
    input: Literal["date"] | None = None


class Unit(GraphModel):
    """What a number is measured in, and where that is written down.

    A currency or a unit of measure normally lives in a column of the node's own
    table. Sometimes it lives one hop away — a line's quantity is in the article's
    base unit — and then `from_node` names that node. A count has no unit at all.
    """

    kind: UnitKind
    column: str | None = None
    from_node: str | None = None

    @model_validator(mode="after")
    def check(self) -> Unit:
        if self.kind == "count" and (self.column or self.from_node):
            raise ValueError("a count carries no unit column")
        if self.column and self.from_node is None and "." in self.column:
            raise ValueError("a unit column is a plain column name")
        return self


class Recursive(GraphModel):
    """Bounds for a self-referencing edge.

    Unbounded is not offered. A depth is a business statement — six levels of
    storage location, eight of bill of materials — and a cycle in real data is a
    defect to report, not a reason to exhaust a connection.
    """

    max_depth: int = Field(ge=1, le=16)
    on_cycle: CyclePolicy = "stop"


class CorrectionTable(GraphModel):
    """Where a compensating row for this node is recorded.

    `original` and `compensating` are columns on the correction table. `joins_on`
    is the column on the *node's* own table that they identify — usually the key,
    but a ledger reversal names a posting group rather than a single entry.
    """

    table: str
    original: str
    compensating: str
    replacement: str | None = None
    joins_on: str | None = None


class RevisionTable(GraphModel):
    """Where the revisions of this node are recorded, and how to find the latest.

    `of` and `order_by` are both columns on the revision table: the reference back
    to the node, and the ordering that decides which revision is current.
    """

    table: str
    of: str
    order_by: str


class FactSource(GraphModel):
    """A node whose rows are Facts rather than a table.

    This is how a business concept the schema does not model becomes queryable
    without a migration. `fact.value` is text, so every property names the cast it
    needs; a failed cast is an error and never a zero.
    """

    subject_type: str
    properties: dict[str, dict[str, str]] = Field(default_factory=dict)


class FactEdge(GraphModel):
    """An edge whose instances are Fact rows somebody creates.

    The structural edges in this model are carried by a column that already holds
    the link, so declaring them stores nothing. This kind has no such column: each
    instance is a row. Both are traversed identically.
    """

    predicate: str
    subject: Literal["from", "to"] = "from"
    cast: str = "id"


class Writable(GraphModel):
    """Who may assert an edge, and what the assertion counts as.

    An asserted link is a human statement, not an observation of a source system,
    and a result has to be able to say which of the two it stands on.
    """

    by: tuple[str, ...]
    as_: Literal["assertion", "observation"] = Field(default="assertion", alias="as")


class MeasureSource(GraphModel):
    """A measure that is not a plain column."""

    distinct: str | None = None
    service: str | None = None

    @model_validator(mode="after")
    def check(self) -> MeasureSource:
        if bool(self.distinct) == bool(self.service):
            raise ValueError("a measure source is either a distinct key or a service")
        return self


class Step(GraphModel):
    """One edge of a path, named the way a question names it."""

    edge: str
    direction: Direction = "out"


class Deduction(GraphModel):
    """What to take off the base number, and along which path it is counted.

    "How much is still open" is the question every operational report is really
    asking, and it is never one column: a promise is open by what has not moved
    against it, an invoice by what has not been settled. The far side names a
    declared measure rather than a raw column, so its unit and its additivity
    are declared once and not re-derived here.
    """

    measure: str
    over: tuple[Step, ...]

    @model_validator(mode="after")
    def check(self) -> Deduction:
        if not self.over:
            raise ValueError("a deduction is counted along at least one edge")
        return self


class Node(GraphModel):
    """One business concept, and the rows that are instances of it."""

    table: str | None = None
    from_facts: FactSource | None = None
    where: dict[str, Any] | None = None
    of: str | None = None
    derivation: (
        Literal[
            "finance.aging",
            "warehouse.inventory",
            "positions.customer",
            "positions.supplier",
            "positions.stock",
            "positions.customer.history",
            "positions.supplier.history",
            "positions.stock.history",
        ]
        | None
    ) = None
    grain: str
    key: str
    tenant: str = "tenant_id"
    corrections: Corrections
    correction_table: CorrectionTable | None = None
    revision_table: RevisionTable | None = None
    time: str | None = None
    coverage: tuple[Coverage, ...] = ("current",)
    evidence: str | None = None
    properties: dict[str, str | Property] = Field(default_factory=dict)
    measures: Literal["none"] | None = None
    label: Label | None = None

    description: Label | None = None
    category: Label | None = None
    category_order: int = 100
    aliases: tuple[str, ...] = ()

    def column_of(self, prop: str) -> str:
        # The key is groupable without being declared a property: it is what the
        # node is, and grouping by it is the only way to keep two records with
        # the same name apart.
        if prop == self.key and prop not in self.properties:
            return self.key
        found = self.properties.get(prop)
        if isinstance(found, Property):
            return found.column
        return found or ""

    def enumerated(self) -> dict[str, str]:
        """The properties worth listing values for, as name to column."""
        return {
            name: found.column
            for name, found in self.properties.items()
            if isinstance(found, Property) and found.enumerated
        }

    def label_of(self, prop: str, language: str = "en") -> str:
        if prop == self.key and prop not in self.properties:
            return {"de": "Kennung", "nl": "Kenmerk", "es": "Identidad"}.get(
                language, "Identity"
            )
        found = self.properties.get(prop)
        return found.label.pick(language) if isinstance(found, Property) else prop

    @model_validator(mode="after")
    def check(self) -> Node:
        if bool(self.table) == bool(self.from_facts):
            raise ValueError("a node is backed by exactly one of table or from_facts")
        if self.corrections == "revise" and not self.revision_table:
            raise ValueError(
                "a revised node must name its revision table, or the latest "
                "revision cannot be selected and every sum multiplies the promise"
            )
        if self.corrections == "compensate" and not self.correction_table:
            raise ValueError(
                "a compensating node must name its correction table, or a row "
                "count cannot tell a corrected event from three separate ones"
            )
        if self.corrections != "revise" and self.revision_table:
            raise ValueError("only a revised node has a revision table")
        if self.corrections != "compensate" and self.correction_table:
            raise ValueError("only a compensating node has a correction table")
        unsupported = set(self.coverage) & {"as_of_effective", "as_of_knowledge"}
        if self.derivation and self.derivation.endswith(".history"):
            unsupported.discard("as_of_effective")
        if unsupported:
            raise ValueError(
                f"{sorted(unsupported)} is not backed by a tested history model; "
                "an as-of question must fail rather than return today's rows"
            )
        return self


class Edge(GraphModel):
    """One named relationship, and how many rows of the target one row reaches."""

    from_: str = Field(alias="from")
    to: str
    via: str | None = None
    fact: FactEdge | None = None
    multiplicity: Multiplicity
    nullable: bool = False
    recursive: Recursive | None = None
    target_where: dict[str, Any] | None = None
    writable: Writable | None = None
    label: Label | None = None

    @model_validator(mode="after")
    def check(self) -> Edge:
        if bool(self.via) == bool(self.fact):
            raise ValueError("an edge is carried by exactly one of via or fact")
        if self.via and self.via.count(".") != 1:
            raise ValueError(f"via must be table.column, got {self.via!r}")
        if self.recursive and self.from_ != self.to:
            raise ValueError("only a self-referencing edge can be recursive")
        if self.writable and not self.fact:
            raise ValueError(
                "only a Fact edge can be written; a column already holds the link"
            )
        return self


class Measure(GraphModel):
    """One number, and the axes along which adding it up means something."""

    node: str
    source: str | MeasureSource
    unit: Unit
    additive_over: tuple[str, ...]
    never_across: tuple[str, ...] = ()
    unknown: UnknownPolicy = "keep"
    sign_from: str | None = None
    less: Deduction | None = None
    note: str | None = None
    label: Label | None = None

    @model_validator(mode="after")
    def check(self) -> Measure:
        if self.less and not isinstance(self.source, str):
            raise ValueError(
                "a deduction is taken off a column; a distinct count or a service "
                "value has no row to take it off"
            )
        both = set(self.additive_over) & set(self.never_across)
        if both:
            raise ValueError(
                f"{sorted(both)} cannot be both additive and never additive"
            )
        if not self.additive_over:
            raise ValueError(
                "a measure with no additive axis can never be aggregated; say so "
                "on the node with measures: none instead"
            )
        # A column measure has to say where its unit is written down. A service
        # measure does not: the canonical service returns the unit with the value,
        # which is the reason to bind to it rather than to re-derive the number.
        from_service = isinstance(self.source, MeasureSource) and self.source.service
        if self.unit.kind != "count" and not self.unit.column and not from_service:
            raise ValueError(
                f"a {self.unit.kind} measure read from a column must name the "
                "column its unit is written in"
            )
        return self


class Limits(GraphModel):
    """Every number here is checked somewhere. A limit nobody enforces is a claim.

    `statements_per_traversal` used to be pinned to one and was not true: a path
    that reaches a derived position runs the canonical service first, and that was
    measured at thirteen to twenty-five reads. It now states what an ordinary path
    costs, and `statements_per_derivation` states the ceiling a canonical bulk read
    may reach before the traversal is refused as a regression rather than served
    slowly.
    """

    max_path_length: int = Field(default=8, ge=1, le=32)
    max_recursive_depth: int = Field(default=6, ge=1, le=16)
    result_rows: int = Field(default=10_000, ge=1)
    page_rows: int = Field(default=200, ge=1)
    statement_timeout_seconds: int = Field(default=30, ge=1)
    statements_per_traversal: Literal[1] = 1
    statements_per_derivation: int = Field(default=40, ge=1, le=500)


Window = Literal["this_month", "last_month", "this_year", "last_year", "last_30_days"]


class TemplatePeriod(GraphModel):
    """A period a template means but cannot yet hold.

    A stored question carries absolute instants, because that is the only form
    that keeps meaning once it is saved. A template is not a question yet — it is
    the shape of one — so it names the window and the field, and whoever adopts
    it resolves that against their own calendar. Baking September 2026 into a
    template would make it wrong the following month.
    """

    field: str
    window: Window


class ReportTemplate(GraphModel):
    """A question worth starting from, declared beside the model it reads.

    It lives here rather than in a table because it names nodes, edges and
    measures: a template that names something the model does not have should
    fail when the model loads, not when somebody clicks it.
    """

    label: Label
    about: Label
    question: dict[str, Any]
    period: TemplatePeriod | None = None
    snapshot: str | None = None


class ReportingGraph(GraphModel):
    """The whole declaration, cross-checked so a dangling name cannot be published."""

    version: int
    model_version: str
    language: str | None = None
    defaults: dict[str, Any] | None = None
    nodes: dict[str, Node]
    edges: dict[str, Edge]
    measures: dict[str, Measure]
    templates: dict[str, ReportTemplate] = Field(default_factory=dict)
    limits: Limits = Field(default_factory=Limits)

    @model_validator(mode="after")
    def check(self) -> ReportingGraph:
        for name, edge in self.edges.items():
            for side, target in (("from", edge.from_), ("to", edge.to)):
                if target not in self.nodes:
                    raise ValueError(
                        f"edge {name} {side} names an unknown node {target!r}"
                    )
            if (
                edge.recursive
                and edge.recursive.max_depth > self.limits.max_recursive_depth
            ):
                raise ValueError(
                    f"edge {name} declares a depth beyond the model's own limit"
                )
        for name, measure in self.measures.items():
            if measure.node not in self.nodes:
                raise ValueError(
                    f"measure {name} names an unknown node {measure.node!r}"
                )
            origin = measure.unit.from_node
            if origin and origin not in self.nodes:
                raise ValueError(
                    f"measure {name} takes its unit from an unknown node {origin!r}"
                )
        carried = {m.node for m in self.measures.values()}
        for name, node in self.nodes.items():
            if name in carried:
                if node.measures == "none":
                    raise ValueError(
                        f"node {name} says it has no measure but carries one"
                    )
                continue
            if node.measures != "none":
                raise ValueError(
                    f"node {name} carries no measure. Say 'measures: none' to confirm "
                    "it is only traversed and filtered — a forgotten measure and a "
                    "deliberate one look identical otherwise"
                )
        for name, node in self.nodes.items():
            if node.of and node.of not in self.nodes:
                raise ValueError(f"node {name} is of an unknown node {node.of!r}")
        return self

    def measures_of(self, node: str) -> dict[str, Measure]:
        return {k: v for k, v in self.measures.items() if v.node == node}

    def edges_from(self, node: str) -> dict[str, Edge]:
        return {k: v for k, v in self.edges.items() if v.from_ == node}

    def edges_to(self, node: str) -> dict[str, Edge]:
        return {k: v for k, v in self.edges.items() if v.to == node}
