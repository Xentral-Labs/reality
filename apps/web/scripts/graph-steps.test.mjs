import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

/** The step stack, held to the two things a stack of steps has to get right.
 *
 * A period is one line but two comparisons, and taking a step away has to take
 * away everything that pointed at it. Both were wrong the first time: the
 * period was added as two rows that could be half-removed, and a removed hop
 * left a measure behind that the server then refused by alias.
 */
const source = readFileSync(
  new URL("../src/unified/analytics/GraphSteps.tsx", import.meta.url),
  "utf8",
);
const exports = {};
const require = createRequire(import.meta.url);
vm.runInNewContext(
  ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText,
  {
    exports,
    Date,
    require: (name) => {
      if (name.startsWith("."))
        return {
          t: (value) => value,
          APIError: class {},
          // The real one renders in the reader's own timezone, which is the
          // whole point of the test below; Berlin is what the app ships with.
          formatDate: (value) =>
            new Intl.DateTimeFormat("de-DE", {
              day: "2-digit",
              month: "short",
              year: "numeric",
              timeZone: "Europe/Berlin",
            }).format(new Date(value)),
        };
      return require(name);
    },
  },
);
const {
  question,
  pruned,
  periodFilter,
  columnOf,
  nextOrder,
  planOf,
  withMeasure,
  withoutMeasure,
  reachable,
  withRequiredAxes,
} = exports;

/** The module runs in its own context, so its objects carry another realm's
 *  prototype. Comparing the values rather than the identities keeps the test
 *  about the question and not about the sandbox. */
const plain = (value) => JSON.parse(JSON.stringify(value));

const NODES = {
  order: {
    key: "order",
    label: "Auftrag",
    measures: [{ key: "stated_order_amount" }, { key: "order_count" }],
    properties: [
      { key: "currency", label: "Währung", kind: "text" },
      { key: "ordered_at", label: "Bestelldatum", kind: "time" },
    ],
    edges: [
      {
        key: "contains",
        label: "enthält",
        to: "order_line",
        to_label: "Auftragsposition",
        multiplicity: "1:n",
      },
      {
        key: "ordered_by",
        label: "bestellt von",
        to: "party",
        to_label: "Geschäftspartner",
        multiplicity: "n:1",
      },
    ],
    edges_in: [],
  },
  party: {
    key: "party",
    label: "Geschäftspartner",
    measures: [],
    properties: [{ key: "name", label: "Name", kind: "text" }],
    edges: [],
    edges_in: [],
  },
  order_line: {
    key: "order_line",
    label: "Auftragsposition",
    measures: [{ key: "line_amount" }],
    properties: [{ key: "sku", label: "Artikelnummer", kind: "text" }],
    edges: [],
    edges_in: [],
  },
};

const stacked = {
  blocks: [
    { alias: "o", node: "order", filters: [] },
    {
      edge: { key: "contains", direction: "out", label: "enthält", fansOut: true },
      alias: "n1",
      node: "order_line",
      filters: [],
    },
  ],
  measures: ["stated_order_amount", "line_amount"],
  groups: [
    { field: "o.currency", label: "Währung" },
    { field: "n1.sku", label: "Artikelnummer" },
  ],
  order: { by: "line_amount", descending: true },
  limit: 10,
};

test("a period is one line to read and one line to remove", () => {
  const filter = periodFilter("o.ordered_at", "Bestelldatum", {
    label: "dieses Jahr",
    // Local dates, the way the page builds a named period — "this year" means
    // midnight where the reader is, not midnight in UTC.
    from: new Date(2026, 0, 1),
    until: new Date(2027, 0, 1),
  });
  assert.equal(filter.shown, "Bestelldatum dieses Jahr");
  assert.deepEqual(
    plain(filter.conditions).map((condition) => condition.op),
    ["gte", "lt"],
    "half-open, so two adjacent periods neither overlap nor leave a gap",
  );
  const plan = {
    blocks: [{ alias: "o", node: "order", filters: [filter] }],
    measures: ["order_count"],
    groups: [],
    limit: 200,
  };
  assert.equal(question(plan).filter.length, 2, "both bounds travel with the one row");
});

test("taking a step away takes away what pointed at it", () => {
  const shortened = { ...stacked, blocks: stacked.blocks.slice(0, 1) };
  const settled = pruned(shortened, NODES);
  assert.deepEqual(
    plain(settled.measures),
    ["stated_order_amount"],
    "the line measure is unreachable now",
  );
  assert.deepEqual(
    plain(settled.groups).map((group) => group.field),
    ["o.currency"],
    "an axis on the removed record would be refused by alias",
  );
  assert.equal(settled.order, undefined, "and nothing is sorted by a number that is gone");
});

test("the stack compiles to the question the server checks", () => {
  const asked = question(pruned(stacked, NODES));
  assert.equal(asked.from, "order");
  assert.equal(asked.as, "o");
  assert.deepEqual(plain(asked.follow), [{ edge: "contains", direction: "out", as: "n1" }]);
  assert.deepEqual(plain(asked.measures), ["stated_order_amount", "line_amount"]);
  assert.deepEqual(plain(asked.order_by), [{ by: "line_amount", descending: true }]);
  assert.equal(asked.limit, 10);
});

test("one button carries all three states a sort can be in", () => {
  const first = nextOrder(undefined, "stated_order_amount");
  assert.deepEqual(plain(first), { by: "stated_order_amount", descending: true });
  const reversed = nextOrder(first, "stated_order_amount");
  assert.equal(reversed.descending, false, "pressing it again reverses rather than clears");
  assert.equal(nextOrder(reversed, "stated_order_amount"), undefined, "and once more unsorts");
  assert.deepEqual(
    plain(nextOrder(reversed, "o.currency")),
    { by: "o.currency", descending: true },
    "a different column starts over rather than inheriting the direction",
  );
});

test("an axis can be sorted by the name the answer gives it", () => {
  assert.equal(columnOf({ field: "o.currency", label: "Währung" }), "o.currency");
  assert.equal(
    columnOf({ field: "o.ordered_at", label: "Bestelldatum (Monat)", bucket: "month" }),
    "Bestelldatum (Monat)",
    "a bucketed axis is named, and the compiler orders by that name",
  );
  const asked = question({
    blocks: [{ alias: "o", node: "order", filters: [] }],
    measures: ["order_count"],
    groups: [{ field: "o.ordered_at", label: "Bestelldatum (Monat)", bucket: "month" }],
    order: { by: "Bestelldatum (Monat)", descending: false },
    limit: 200,
  });
  assert.deepEqual(plain(asked.order_by), [{ by: "Bestelldatum (Monat)", descending: false }]);
});

test("a sort on a removed axis goes with it", () => {
  const settled = pruned(
    {
      ...stacked,
      blocks: stacked.blocks.slice(0, 1),
      order: { by: "n1.sku", descending: true },
    },
    NODES,
  );
  assert.equal(settled.order, undefined, "nothing is sorted by a column that is gone");
});

test("a time axis is bucketed, because one row per instant is a list not an answer", () => {
  const asked = question({
    blocks: [{ alias: "o", node: "order", filters: [] }],
    measures: ["order_count"],
    groups: [{ field: "o.ordered_at", label: "Bestelldatum (month)", bucket: "month" }],
    limit: 200,
  });
  assert.deepEqual(plain(asked.group_by), [
    { field: "o.ordered_at", bucket: "month", as: "Bestelldatum (month)" },
  ]);
});

test("a saved question reopens as the steps that built it", () => {
  const saved = question(pruned(stacked, NODES));
  const reopened = plain(planOf(saved, NODES));
  assert.equal(reopened.blocks.length, 2);
  assert.equal(reopened.blocks[1].node, "order_line", "the hop names the record it reaches");
  assert.equal(reopened.blocks[1].edge.fansOut, true, "and still says it fans out");
  assert.deepEqual(reopened.measures, ["stated_order_amount", "line_amount"]);
  assert.deepEqual(
    reopened.groups.map((group) => group.field),
    ["o.currency", "n1.sku"],
  );
  assert.deepEqual(plain(reopened.order), { by: "line_amount", descending: true });
  assert.equal(reopened.limit, 10);
});

test("a reopened period is one line again, not two halves", () => {
  const filter = periodFilter("o.ordered_at", "Bestelldatum", {
    label: "dieses Jahr",
    // Local dates, the way the page builds a named period — "this year" means
    // midnight where the reader is, not midnight in UTC.
    from: new Date(2026, 0, 1),
    until: new Date(2027, 0, 1),
  });
  const saved = question({
    blocks: [{ alias: "o", node: "order", filters: [filter] }],
    measures: ["order_count"],
    groups: [],
    limit: 200,
  });
  const reopened = plain(planOf(saved, NODES));
  assert.equal(reopened.blocks[0].filters.length, 1, "two bounds, one removable line");
  assert.equal(reopened.blocks[0].filters[0].conditions.length, 2);
  assert.match(
    reopened.blocks[0].filters[0].shown,
    /Bestelldatum 01\. Jan\. 2026 – 31\. Dez\. 2026/,
    "the upper bound is exclusive, so the last day it covers is the one shown",
  );
});

test("a question naming a record this model does not have reopens as nothing", () => {
  assert.equal(planOf({ from: "not_a_node", measures: ["x"] }, NODES), null);
  assert.equal(
    planOf(
      { from: "order", follow: [{ edge: "no_such_edge", direction: "out", as: "n1" }] },
      NODES,
    ),
    null,
    "rather than a stack with a step that cannot be taken",
  );
});

/** Found by an ERP acceptance run: every report was a one-number report. */
const CATALOGUE = [
  { key: "stated_order_amount", never_across: ["currency"] },
  { key: "order_count", never_across: [] },
];
const FIELDS = [
  { field: "o.currency", label: "Währung", kind: "text" },
  { field: "o.number", label: "Nummer", kind: "text" },
];

test("a second number stands beside the first, not in place of it", () => {
  const listing = {
    blocks: [{ alias: "o", node: "order", filters: [] }],
    measures: [],
    groups: [{ field: "o.number", label: "Nummer" }],
    limit: 50,
  };
  const one = plain(withMeasure(listing, "stated_order_amount", CATALOGUE, FIELDS));
  assert.deepEqual(one.measures, ["stated_order_amount"]);
  assert.deepEqual(
    one.groups.map((group) => group.field),
    ["o.currency"],
    "the first number replaces the list columns with the axis it needs",
  );
  const two = plain(withMeasure(one, "order_count", CATALOGUE, FIELDS));
  assert.deepEqual(two.measures, ["stated_order_amount", "order_count"]);
  assert.deepEqual(
    two.groups.map((group) => group.field),
    ["o.currency"],
    "and a second number keeps the axes the first one established",
  );
});

test("taking the last number away puts the records back", () => {
  const summary = {
    blocks: [{ alias: "o", node: "order", filters: [] }],
    measures: ["stated_order_amount", "order_count"],
    groups: [{ field: "o.currency", label: "Währung" }],
    order: { by: "stated_order_amount", descending: true },
    limit: 50,
  };
  const one = plain(withoutMeasure(summary, "stated_order_amount", NODES));
  assert.deepEqual(one.measures, ["order_count"]);
  assert.equal(one.order, undefined, "a sort on the removed number goes with it");
  const none = plain(withoutMeasure(one, "order_count", NODES));
  assert.deepEqual(none.measures, []);
  assert.ok(none.groups.length > 0, "an empty table is not an answer; the records are");
});

test("a reopened period reads as the day it was picked, not the day before", () => {
  // Berlin's local midnight on 1 September is 2026-08-31T22:00:00Z. Slicing the
  // stored instant put "2026-08-31" on a filter somebody had set to 1 September:
  // the query was right and the label was a day out, which is the worse failure,
  // because the reader has no reason to doubt it.
  const saved = question({
    blocks: [
      {
        alias: "o",
        node: "order",
        filters: [
          periodFilter("o.ordered_at", "Bestelldatum", {
            label: "September",
            from: new Date(2026, 8, 1),
            until: new Date(2026, 8, 18),
          }),
        ],
      },
    ],
    measures: ["order_count"],
    groups: [],
    limit: 50,
  });
  const shown = plain(planOf(saved, NODES)).blocks[0].filters[0].shown;
  assert.doesNotMatch(shown, /31/, `a September filter must not read as August: ${shown}`);
});

/** A realistic report branches. Found by building B02 in the browser: an open
 *  delivery is asked about by customer AND by article, and both hang off the
 *  commitment, so a control that only continued from the last step could not
 *  express it — although the executor has always taken a hop that says where
 *  it starts. */
const BRANCHED = {
  blocks: [
    { alias: "o", node: "order", filters: [] },
    {
      edge: { key: "contains", direction: "out", label: "enthält", fansOut: true, from: "o" },
      alias: "n1",
      node: "order_line",
      filters: [],
    },
  ],
  measures: [],
  groups: [{ field: "o.currency", label: "Währung" }],
  limit: 50,
};

test("a connection is offered from everywhere the question has reached", () => {
  const offered = plain(reachable(BRANCHED, NODES));
  assert.ok(
    offered.some((edge) => edge.from === "o"),
    "the order it started at still offers its own connections",
  );
});

test("a branching hop says where it starts, and an ordinary one does not", () => {
  const branched = {
    ...BRANCHED,
    blocks: [
      ...BRANCHED.blocks,
      {
        edge: {
          key: "ordered_by",
          direction: "out",
          label: "bestellt von",
          fansOut: false,
          from: "o",
        },
        alias: "n2",
        node: "party",
        filters: [],
      },
    ],
  };
  const asked = plain(question(branched));
  assert.equal(asked.follow[0].from, undefined, "a plain step needs no origin");
  assert.equal(asked.follow[1].from, "o", "a branch back to the order names it");
  const reopened = plain(planOf(asked, NODES));
  assert.equal(reopened.blocks[2].edge.from, "o", "and it reopens as the same branch");
});

test("a period reads the same before and after it is saved", () => {
  // Entering 1 to 17 September stores `< 18 September`. Showing the raw bound
  // made the same filter read as "1. – 17." while it was being set and
  // "1. – 18." once reopened: two answers to one question, and the second one
  // names a day the report does not cover.
  const entered = periodFilter("o.ordered_at", "Bestelldatum", {
    label: "picked",
    from: new Date(2026, 8, 1),
    until: new Date(2026, 8, 18),
  });
  const reopened = plain(
    planOf(
      question({
        blocks: [{ alias: "o", node: "order", filters: [entered] }],
        measures: ["order_count"],
        groups: [],
        limit: 50,
      }),
      NODES,
    ),
  ).blocks[0].filters[0].shown;
  assert.match(reopened, /01\. Sept\. 2026 – 17\. Sept\. 2026/, reopened);
});

test("an axis a number may not be summed across arrives as soon as it is reachable", () => {
  // Found by building B05: picking moved quantity before reaching the article
  // is refused because the unit is unreachable, and reaching the article
  // afterwards is refused because the question does not split by it. Two walls
  // in a row for somebody who only wanted movements per article.
  const beforeTheHop = withRequiredAxes(
    {
      blocks: [{ alias: "o", node: "order", filters: [] }],
      measures: ["stated_order_amount"],
      groups: [],
      limit: 50,
    },
    CATALOGUE,
    [],
  );
  assert.deepEqual(plain(beforeTheHop).groups, [], "nothing to add while it is out of reach");

  const afterTheHop = plain(withRequiredAxes(beforeTheHop, CATALOGUE, FIELDS));
  assert.deepEqual(
    afterTheHop.groups.map((group) => group.field),
    ["o.currency"],
    "and it arrives the moment the path can see it",
  );
  assert.deepEqual(
    plain(withRequiredAxes(afterTheHop, CATALOGUE, FIELDS)).groups.length,
    1,
    "without adding it twice",
  );
});
