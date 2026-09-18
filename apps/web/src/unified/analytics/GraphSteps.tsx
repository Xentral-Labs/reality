import { useEffect, useMemo, useRef, useState } from "react";
import {
  APIError,
  graphApi,
  type GraphAnswer,
  type GraphCatalog,
  type GraphNode,
  type GraphQuestion,
  type GraphReport,
} from "../../api";
import {
  currentLanguage,
  formatDate,
  formatDateTime,
  formatExactDecimal,
  t,
} from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { chip } from "./chips";
import { analyticsError } from "./errors";

/** The result is the question.
 *
 * An empty builder is a form, and a form has to be understood before it shows
 * anything. Picking a record shows those records immediately; narrowing,
 * sorting and bounding then happen on the table itself. Only two things are
 * asked of the reader in words — what to count and what to split it by — and
 * only one thing has to be learned: that reaching another record type can
 * multiply a total, which is why that step says so before it is taken.
 */

/** One readable line, which may take more than one condition to mean.
 *
 * "Order date this year" is two comparisons. Keeping them in one row is what
 * lets somebody remove the period rather than half of it.
 */
type Condition = { field: string; op: string; value?: unknown };
type Filter = { shown: string; conditions: Condition[] };
type Block = {
  /** The first block has no hop; every later one carries the edge that reached it.
   *  `from` is the alias it left, which is not always the step before it. */
  edge?: {
    key: string;
    direction: "out" | "in";
    label: string;
    fansOut: boolean;
    from?: string;
  };
  alias: string;
  node: string;
  filters: Filter[];
};
type Group = { field: string; label: string; bucket?: string };
export type Plan = {
  blocks: Block[];
  measures: string[];
  groups: Group[];
  order?: { by: string; descending: boolean };
  limit: number;
};

/** What the answer calls this axis — the same name the compiler labels it with.
 *
 * A bucketed axis is named, a plain one keeps its field path, so sorting has to
 * ask the grouping rather than guess.
 */
export function columnOf(group: Group) {
  return group.bucket ? group.label : group.field;
}

/** Three states, one button: biggest first, smallest first, unsorted.
 *
 * A separate direction control would be a second thing to find for a choice
 * that only ever has two answers.
 */
export function nextOrder(order: Plan["order"], by: string): Plan["order"] {
  if (order?.by !== by) return { by, descending: true };
  if (order.descending) return { by, descending: false };
  return undefined;
}

type Refusal = { headline: string; detail: string };

const REFUSALS: Record<string, string> = {
  fan_out: "Summing this here would multiply the total.",
  unit_mismatch: "These values are not measured in the same unit.",
  not_additive: "This number is a state, not a flow, so it does not add up over time.",
  unknown_node: "The model has no such business record.",
  unknown_edge: "The model has no such connection.",
  unknown_measure: "The model has no such number.",
  unknown_property: "That record has no such field.",
  measure_unreachable: "This path never reaches the record that number lives on.",
  unit_unreachable: "This path never reaches the record that says the unit.",
  edge_direction: "This connection runs the other way round.",
  depth_required: "Say how many levels deep to follow.",
  depth_exceeded: "That is deeper than this connection allows.",
  not_recursive: "This connection does not repeat, so it has no depth.",
  path_too_long: "This path takes more steps than the model allows.",
  not_temporal: "This field is not kept as a date, so it cannot be grouped by period.",
};

function refusalOf(failure: unknown): Refusal {
  const code = failure instanceof APIError ? failure.code : undefined;
  return {
    headline: t((code && REFUSALS[code]) || "This question cannot be answered correctly"),
    detail: failure instanceof Error ? failure.message : analyticsError(failure),
  };
}

/** Where a total would multiply, shown next to the step rather than after it. */
function fansOut(multiplicity: string, direction: "out" | "in") {
  return (multiplicity === "1:n") === (direction === "out");
}

/** Periods people name out loud, resolved here so the question stays absolute. */
function periods(): { key: string; label: string; from: Date; until: Date }[] {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const day = new Date(year, month, now.getDate());
  return [
    {
      key: "this_year",
      label: t("this year"),
      from: new Date(year, 0, 1),
      until: new Date(year + 1, 0, 1),
    },
    {
      key: "last_year",
      label: t("last year"),
      from: new Date(year - 1, 0, 1),
      until: new Date(year, 0, 1),
    },
    {
      key: "this_month",
      label: t("this month"),
      from: new Date(year, month, 1),
      until: new Date(year, month + 1, 1),
    },
    {
      key: "last_month",
      label: t("last month"),
      from: new Date(year, month - 1, 1),
      until: new Date(year, month, 1),
    },
    {
      key: "last_30",
      label: t("the last 30 days"),
      from: new Date(day.getTime() - 30 * 86400000),
      until: new Date(day.getTime() + 86400000),
    },
  ];
}

/** The bound as a real instant.
 *
 * "This year" starts at midnight where the reader is, which is a different
 * moment from midnight UTC. Sending the instant rather than the wall-clock text
 * is what keeps an hour of December out of January.
 */
function instant(value: Date) {
  return value.toISOString();
}

/** A period is one line to read and one line to remove, but two comparisons.
 *
 * Half-open bounds are what make "this month" and "last month" add up to the
 * two months rather than to two months and one shared midnight.
 */
export function periodFilter(
  field: string,
  label: string,
  period: { label: string; from: Date; until: Date },
): Filter {
  return {
    shown: `${label} ${period.label}`,
    conditions: [
      { field, op: "gte", value: instant(period.from) },
      { field, op: "lt", value: instant(period.until) },
    ],
  };
}

const OPERATORS: { key: string; label: string; kinds: string[]; valueless?: boolean }[] = [
  { key: "eq", label: "is", kinds: ["text", "number", "boolean", "time"] },
  { key: "ne", label: "is not", kinds: ["text", "number", "boolean"] },
  { key: "gte", label: "is at least", kinds: ["number"] },
  { key: "lte", label: "is at most", kinds: ["number"] },
  {
    key: "is_null",
    label: "is empty",
    kinds: ["text", "number", "boolean", "time"],
    valueless: true,
  },
  {
    key: "is_not_null",
    label: "is filled in",
    kinds: ["text", "number", "boolean", "time"],
    valueless: true,
  },
];

type Field = { field: string; label: string; kind: string };

export function GraphSteps({
  tenant,
  report,
  onSaved,
}: {
  tenant: string;
  report?: GraphReport | null;
  onSaved?: (report: GraphReport) => void;
}) {
  const language = currentLanguage();
  const read = useRead(() => graphApi.catalog(tenant, language), [tenant, language]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return (
    <Builder
      key={`${tenant}:${report?.id ?? ""}:${report?.revision ?? ""}`}
      tenant={tenant}
      catalog={read.data}
      report={report ?? null}
      onSaved={onSaved}
    />
  );
}

/** The question as the server has to receive it. */
export function question(plan: Plan): GraphQuestion {
  return {
    from: plan.blocks[0].node,
    as: plan.blocks[0].alias,
    follow: plan.blocks.slice(1).map((block, index) => ({
      edge: block.edge!.key,
      direction: block.edge!.direction,
      as: block.alias,
      // Only when it is not the step before, so an ordinary path still reads
      // as an ordinary path.
      ...(block.edge!.from && block.edge!.from !== plan.blocks[index].alias
        ? { from: block.edge!.from }
        : {}),
    })),
    filter: plan.blocks.flatMap((block) =>
      block.filters.flatMap((filter) =>
        filter.conditions.map((condition) => ({
          field: condition.field,
          op: condition.op,
          ...(condition.value === undefined ? {} : { value: condition.value }),
        })),
      ),
    ),
    measures: plan.measures,
    group_by: plan.groups.map((group) => ({
      field: group.field,
      ...(group.bucket ? { bucket: group.bucket, as: group.label } : {}),
    })),
    ...(plan.order ? { order_by: [{ by: plan.order.by, descending: plan.order.descending }] } : {}),
    limit: plan.limit,
  };
}

/** Drop what the remaining steps can no longer reach.
 *
 * Taking a step away takes its records away with it, and a measure or an axis
 * left pointing at them would be refused by the server with a sentence about
 * aliases. Pruning here means removing a step simply removes a step.
 */
export function pruned(plan: Plan, nodes: Record<string, GraphNode>): Plan {
  const aliases = new Set(plan.blocks.map((block) => block.alias));
  const reachable = new Set(
    plan.blocks.flatMap((block) => (nodes[block.node]?.measures ?? []).map((m) => m.key)),
  );
  const measures = plan.measures.filter((key) => reachable.has(key));
  const groups = plan.groups.filter((group) => aliases.has(group.field.split(".")[0]));
  const columns = new Set([...measures, ...groups.map(columnOf)]);
  return {
    ...plan,
    measures,
    groups,
    order: plan.order && columns.has(plan.order.by) ? plan.order : undefined,
  };
}

/** Read a saved question back as the steps that built it.
 *
 * A stored traversal names nodes only at its start; every later one is implied
 * by the edge, so the catalog is walked alongside it. Two bounds on one field
 * fold back into the single line they were entered as, because a period that
 * reopens as two rows can be half-removed — the bug the stack was built to
 * avoid in the first place.
 */
export function planOf(question: GraphQuestion, nodes: Record<string, GraphNode>): Plan | null {
  const start = nodes[question.from];
  if (!start) return null;
  const blocks: Block[] = [{ alias: question.as || "root", node: question.from, filters: [] }];
  for (const hop of question.follow ?? []) {
    // A hop says where it starts when that is not the step before it, so a
    // branching question reopens as the branch it was.
    const origin = hop.from || blocks[blocks.length - 1].alias;
    const at = nodes[blocks.find((block) => block.alias === origin)?.node ?? ""];
    const forward = (at?.edges ?? []).find((edge) => edge.key === hop.edge);
    const backward = (at?.edges_in ?? []).find((edge) => edge.key === hop.edge);
    const edge = hop.direction === "in" ? backward : forward;
    if (!edge) return null;
    blocks.push({
      edge: {
        key: hop.edge,
        direction: hop.direction,
        label:
          hop.direction === "in"
            ? `${(edge as { from_label: string }).from_label} (${edge.label})`
            : `${edge.label} ${(edge as { to_label: string }).to_label}`,
        fansOut: fansOut(edge.multiplicity, hop.direction),
        from: origin,
      },
      alias: hop.as,
      node: hop.direction === "in" ? (edge as { from: string }).from : (edge as { to: string }).to,
      filters: [],
    });
  }
  const labelOf = (field: string) => {
    const [alias, key] = field.split(".");
    const block = blocks.find((candidate) => candidate.alias === alias);
    return (
      (block && nodes[block.node]?.properties.find((property) => property.key === key)?.label) ||
      field
    );
  };
  for (const condition of question.filter ?? []) {
    const block = blocks.find((candidate) => candidate.alias === condition.field.split(".")[0]);
    if (!block) return null;
    const open = block.filters.find(
      (filter) =>
        filter.conditions.length === 1 &&
        filter.conditions[0].field === condition.field &&
        filter.conditions[0].op === "gte" &&
        condition.op === "lt",
    );
    if (open) {
      open.conditions.push(condition);
      open.shown = `${labelOf(condition.field)} ${shortDate(open.conditions[0].value)} – ${lastIncluded(condition.value)}`;
      continue;
    }
    block.filters.push({
      shown: `${labelOf(condition.field)} ${condition.op} ${condition.value ?? ""}`.trim(),
      conditions: [condition],
    });
  }
  return {
    blocks,
    measures: [...(question.measures ?? [])],
    groups: (question.group_by ?? []).map((grouping) => ({
      field: grouping.field,
      label: grouping.as || labelOf(grouping.field),
      ...(grouping.bucket ? { bucket: grouping.bucket } : {}),
    })),
    order: question.order_by?.[0]
      ? { by: question.order_by[0].by, descending: Boolean(question.order_by[0].descending) }
      : undefined,
    limit: question.limit ?? 200,
  };
}

/** The day a bound falls on where the reader is.
 *
 * A bound is stored as a real instant, so local midnight on 1 September is
 * `2026-08-31T22:00:00Z` in Berlin. Slicing the first ten characters off that
 * put "31.08." on a filter somebody had set to 1 September: the query was
 * right and the label was a day out, which is worse than either being wrong,
 * because the reader has no reason to doubt it.
 */
function shortDate(value: unknown) {
  if (typeof value !== "string") return String(value ?? "");
  const instant = new Date(value);
  return Number.isNaN(instant.getTime()) ? value.slice(0, 10) : formatDate(value);
}

/** The last day a half-open period actually includes.
 *
 * A period runs `>= 1 September` and `< 18 September`, so the reader picked
 * 1–17 and the stored upper bound is the 18th. Showing the raw bound made the
 * same filter read as "1. – 17." while it was being set and "1. – 18." after it
 * was saved: the same question, two answers, and the second one looks like a
 * day the report does not cover.
 *
 * Only a bound that falls on local midnight is a whole day; anything else is a
 * real instant and is shown as itself.
 */
function lastIncluded(value: unknown) {
  if (typeof value !== "string") return String(value ?? "");
  const bound = new Date(value);
  if (Number.isNaN(bound.getTime())) return value.slice(0, 10);
  const midnight =
    bound.getHours() === 0 &&
    bound.getMinutes() === 0 &&
    bound.getSeconds() === 0 &&
    bound.getMilliseconds() === 0;
  return formatDate(
    midnight ? new Date(bound.getTime() - 86400000).toISOString() : bound.toISOString(),
  );
}

/** The columns a list of these records opens with.
 *
 * Time first, because "when" is what somebody scans for, then the rest in the
 * order the catalog declares them. Six is as many as reads at a glance; the
 * point is to show the records, not every field they have.
 */
const IDENTITY = ["number", "sku", "name", "reference", "code"];

export function listColumns(node: GraphNode, alias = "o"): Group[] {
  // What somebody looks for first is which record it is, then when it happened.
  const rank = (property: { key: string; kind: string }) =>
    IDENTITY.includes(property.key) ? 0 : property.kind === "time" ? 1 : 2;
  const ordered = [...node.properties].sort((a, b) => rank(a) - rank(b));
  return ordered.slice(0, 6).map((property) => ({
    field: `${alias}.${property.key}`,
    label: property.label,
  }));
}

/** A plan that lists the records of one node and nothing else. */
export function listPlan(node: GraphNode): Plan {
  return {
    blocks: [{ alias: "o", node: node.key, filters: [] }],
    measures: [],
    groups: listColumns(node),
    limit: 50,
  };
}

function Builder({
  tenant,
  catalog,
  report,
  onSaved,
}: {
  tenant: string;
  catalog: GraphCatalog;
  report: GraphReport | null;
  onSaved?: (report: GraphReport) => void;
}) {
  const nodes = useMemo(
    () =>
      Object.fromEntries(catalog.nodes.map((node) => [node.key, node])) as Record<
        string,
        GraphNode
      >,
    [catalog],
  );
  const [plan, setPlan] = useState<Plan | null>(() =>
    report ? planOf(report.definition, nodes) : null,
  );
  const [answer, setAnswer] = useState<GraphAnswer | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [busy, setBusy] = useState(false);

  const ask = async (next: Plan) => {
    // Every change funnels through here, so a hop that makes a required axis
    // reachable brings it in without the reader meeting a refusal first.
    const settled = pruned(
      withRequiredAxes(
        next,
        next.blocks.flatMap((block) => nodes[block.node]?.measures ?? []),
        next.blocks.flatMap((block) =>
          (nodes[block.node]?.properties ?? []).map((property) => ({
            field: `${block.alias}.${property.key}`,
            label: property.label,
            kind: property.kind,
          })),
        ),
      ),
      nodes,
    );
    setPlan(settled);
    if (!settled.measures.length && !settled.groups.length) {
      setAnswer(null);
      setRefusal(null);
      return;
    }
    setBusy(true);
    setRefusal(null);
    try {
      setAnswer(await graphApi.ask(tenant, question(settled)));
    } catch (failure) {
      setAnswer(null);
      setRefusal(refusalOf(failure));
    } finally {
      setBusy(false);
    }
  };

  // A reopened report shows its answer without being touched first, which is
  // the whole point of reopening one.
  const asked = useRef(false);
  useEffect(() => {
    if (plan && !asked.current) {
      asked.current = true;
      void ask(plan);
    }
  });

  if (!plan)
    return (
      <section className="space-y-5">
        <div>
          <h2 className="text-xl font-semibold">{t("What would you like to look at?")}</h2>
          <div className="mt-1 max-w-2xl text-sm text-fg-muted">
            {t(
              "Pick your records and you see them straight away. Everything else happens on the table.",
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {catalog.nodes.map((node) => (
            <button
              key={node.key}
              className="br-btn"
              title={node.grain}
              onClick={() => ask(listPlan(node))}
            >
              {node.label}
            </button>
          ))}
        </div>
      </section>
    );

  return (
    <section className="space-y-4">
      <Toolbar
        catalog={catalog}
        nodes={nodes}
        plan={plan}
        change={ask}
        restart={() => {
          setPlan(null);
          setAnswer(null);
          setRefusal(null);
        }}
      />
      <Result
        answer={answer}
        refusal={refusal}
        busy={busy}
        plan={plan}
        nodes={nodes}
        ceiling={catalog.limits.result_rows}
        change={ask}
      />
      <Save tenant={tenant} plan={plan} report={report} onSaved={onSaved} />
    </section>
  );
}

/** Everything asked in words: which records, what to count, what to split by. */
function Toolbar({
  catalog,
  nodes,
  plan,
  change,
  restart,
}: {
  catalog: GraphCatalog;
  nodes: Record<string, GraphNode>;
  plan: Plan;
  change: (next: Plan) => void;
  restart: () => void;
}) {
  const measures = plan.blocks.flatMap((block) => nodes[block.node]?.measures ?? []);
  const fields: Field[] = plan.blocks.flatMap((block) =>
    (nodes[block.node]?.properties ?? []).map((property) => ({
      field: `${block.alias}.${property.key}`,
      label: property.label,
      kind: property.kind,
    })),
  );
  const summarised = plan.measures.length > 0;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 className="text-xl font-semibold">{nodes[plan.blocks[0].node]?.label}</h2>
        {plan.blocks.slice(1).map((block, index) => (
          <span key={block.alias} className="flex items-center gap-2 text-sm">
            <span aria-hidden="true" className="text-fg-muted">
              ›
            </span>
            {block.edge?.label}
            {block.edge?.fansOut && <span className="text-xs text-warning-600">{t("many")}</span>}
            <button
              className="text-fg-muted hover:text-fg-strong"
              title={t("Remove this step and everything after it")}
              onClick={() => change({ ...plan, blocks: plan.blocks.slice(0, index + 1) })}
            >
              ×
            </button>
          </span>
        ))}
        <Reach catalog={catalog} nodes={nodes} plan={plan} change={change} />
        <button className="text-sm text-fg-muted underline" onClick={restart}>
          {t("Other records")}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {plan.blocks.flatMap((block, index) =>
          block.filters.map((filter, position) => (
            <Chip
              key={`${block.alias}-${position}`}
              filter={filter}
              flip={() =>
                change({
                  ...plan,
                  blocks: plan.blocks.map((candidate, at) =>
                    at === index
                      ? {
                          ...candidate,
                          filters: candidate.filters.map((one, p) =>
                            p === position ? flipped(one) : one,
                          ),
                        }
                      : candidate,
                  ),
                })
              }
              remove={() =>
                change({
                  ...plan,
                  blocks: plan.blocks.map((candidate, at) =>
                    at === index
                      ? {
                          ...candidate,
                          filters: candidate.filters.filter((_, p) => p !== position),
                        }
                      : candidate,
                  ),
                })
              }
            />
          )),
        )}
        <AddFilter fields={fields} add={(filter) => change(withFilter(plan, filter))} />
      </div>

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-fg-muted">{t("Summarise")}</span>
        {plan.measures.map((key) => (
          <button
            key={key}
            className={chip(true)}
            title={t("Remove this number")}
            onClick={() => change(withoutMeasure(plan, key, nodes))}
          >
            {measures.find((measure) => measure.key === key)?.label ?? key}{" "}
            <span className="text-fg-muted">×</span>
          </button>
        ))}
        <select
          className="rounded-lg border border-border-default bg-surface px-2 py-2 text-sm"
          aria-label={t("Number to summarise")}
          value=""
          onChange={(event) => {
            const measure = event.target.value;
            if (measure) change(withMeasure(plan, measure, measures, fields));
          }}
        >
          <option value="">
            {plan.measures.length ? t("Add…") : t("nothing — list the records")}
          </option>
          {measures
            .filter((measure) => !plan.measures.includes(measure.key))
            .map((measure) => (
              <option key={measure.key} value={measure.key}>
                {measure.label}
              </option>
            ))}
        </select>
        {summarised && (
          <>
            <span className="text-fg-muted">{t("by")}</span>
            {plan.groups.map((group) => (
              <button
                key={columnOf(group)}
                className={chip(true)}
                title={t("Remove this axis")}
                onClick={() =>
                  change({
                    ...plan,
                    groups: plan.groups.filter(
                      (candidate) => columnOf(candidate) !== columnOf(group),
                    ),
                  })
                }
              >
                {group.label} <span className="text-fg-muted">×</span>
              </button>
            ))}
            <AddGroup
              fields={fields.filter(
                (field) => !plan.groups.some((group) => group.field === field.field),
              )}
              add={(group) => change({ ...plan, groups: [...plan.groups, group] })}
            />
          </>
        )}
      </div>
    </div>
  );
}

/** Add a number to the summary, with the axis it may not be summed across.
 *
 * A measure that declares `never_across: [currency]` is refused unless the
 * question splits by currency or pins it. Offering it and then refusing it is a
 * wall where an answer was expected, so the axis arrives with the measure.
 *
 * Several numbers side by side is the ordinary case — order count beside order
 * value — and a single-value control made every report a one-number report.
 */
export function withMeasure(
  plan: Plan,
  measure: string,
  measures: { key: string; never_across: string[] }[],
  fields: Field[],
): Plan {
  // The first number turns a list into a summary, so the list columns go.
  const kept = plan.measures.length ? plan.groups : [];
  return withRequiredAxes(
    {
      ...plan,
      measures: [...plan.measures, measure],
      groups: kept,
      order: plan.order ?? { by: measure, descending: true },
    },
    measures,
    fields,
  );
}

/** The axes a chosen number may not be summed across, wherever they are reachable.
 *
 * `moved_quantity` is declared never additive across item and unit, and the unit
 * lives on the article. Picking it before reaching the article is refused for
 * one reason, and reaching the article afterwards is refused for another — two
 * walls in a row for somebody who only wanted movements per article. The axis is
 * added as soon as the path can see it, from wherever the change came.
 */
export function withRequiredAxes(
  plan: Plan,
  measures: { key: string; never_across: string[] }[],
  fields: Field[],
): Plan {
  if (!plan.measures.length) return plan;
  // Kept as an array rather than a spread Set: a Set has no length, and
  // TypeScript's downlevel spread reads one, so the list came out empty under
  // the test transpile while working in the build. A guard that only holds on
  // one of the two is not a guard.
  const wanted = plan.measures
    .flatMap((key) => measures.find((candidate) => candidate.key === key)?.never_across ?? [])
    .filter((key, index, all) => all.indexOf(key) === index);
  const required = wanted
    .map((key) => fields.find((field) => field.field.endsWith(`.${key}`)))
    .filter((field): field is Field => Boolean(field))
    .map((field) => ({ field: field.field, label: field.label }));
  return {
    ...plan,
    groups: [
      ...plan.groups,
      ...required.filter((axis) => !plan.groups.some((group) => group.field === axis.field)),
    ],
  };
}

/** Taking the last number away puts the records back, rather than nothing. */
export function withoutMeasure(
  plan: Plan,
  measure: string,
  nodes: Record<string, GraphNode>,
): Plan {
  const measures = plan.measures.filter((key) => key !== measure);
  if (measures.length)
    return {
      ...plan,
      measures,
      order: plan.order?.by === measure ? undefined : plan.order,
    };
  const tip = plan.blocks[plan.blocks.length - 1];
  const node = nodes[tip.node];
  return {
    ...plan,
    measures: [],
    groups: node ? listColumns(node, tip.alias) : [],
    order: undefined,
  };
}

/** Put a filter on the block that owns its field. */
function withFilter(plan: Plan, filter: Filter): Plan {
  const alias = filter.conditions[0].field.split(".")[0];
  return {
    ...plan,
    blocks: plan.blocks.map((block) =>
      block.alias === alias ? { ...block, filters: [...block.filters, filter] } : block,
    ),
  };
}

/** `is` and `is not` are the same filter read two ways, so one click flips it. */
function flipped(filter: Filter): Filter {
  const swap: Record<string, string> = { eq: "ne", ne: "eq", gte: "lt", lt: "gte" };
  if (!filter.conditions.every((condition) => swap[condition.op])) return filter;
  return {
    shown: filter.shown.includes(" ≠ ")
      ? filter.shown.replace(" ≠ ", " = ")
      : filter.shown.replace(" = ", " ≠ "),
    conditions: filter.conditions.map((condition) => ({ ...condition, op: swap[condition.op] })),
  };
}

function Chip({ filter, flip, remove }: { filter: Filter; flip: () => void; remove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-lg border border-accent bg-accent-soft px-2 py-1 text-sm">
      <button title={t("Turn this filter around")} onClick={flip}>
        {filter.shown}
      </button>
      <button
        className="text-fg-muted hover:text-fg-strong"
        title={t("Remove this filter")}
        onClick={remove}
      >
        ×
      </button>
    </span>
  );
}

/** Every connection the question can still take, from anywhere it has reached.
 *
 * A realistic report branches: an open delivery is asked about by customer AND
 * by article, and both hang off the commitment. Offering only what continues
 * from the last step made those reports impossible to build, although the
 * executor has always accepted a hop that names where it starts.
 *
 * The record a connection leaves from is named only when the same connection is
 * offered from more than one place, because that is the only time it is a
 * question the reader has to answer.
 */
export function reachable(plan: Plan, nodes: Record<string, GraphNode>) {
  const out = plan.blocks.flatMap((block) => [
    ...(nodes[block.node]?.edges ?? []).map((edge) => ({
      key: edge.key,
      label: `${edge.label} ${edge.to_label}`,
      node: edge.to,
      direction: "out" as const,
      from: block.alias,
      at: nodes[block.node]?.label ?? block.node,
      fansOut: fansOut(edge.multiplicity, "out"),
    })),
    ...(nodes[block.node]?.edges_in ?? []).map((edge) => ({
      key: edge.key,
      label: `${edge.from_label} (${edge.label})`,
      node: edge.from,
      direction: "in" as const,
      from: block.alias,
      at: nodes[block.node]?.label ?? block.node,
      fansOut: fansOut(edge.multiplicity, "in"),
    })),
  ]);
  const seen = new Map<string, number>();
  for (const edge of out) seen.set(edge.label, (seen.get(edge.label) ?? 0) + 1);
  return out.map((edge) => ({
    ...edge,
    origin: (seen.get(edge.label) ?? 0) > 1 ? edge.at : "",
  }));
}

/** Reaching another record type, which is the one step that can multiply. */
function Reach({
  catalog,
  nodes,
  plan,
  change,
}: {
  catalog: GraphCatalog;
  nodes: Record<string, GraphNode>;
  plan: Plan;
  change: (next: Plan) => void;
}) {
  const [open, setOpen] = useState(false);
  const onward = reachable(plan, nodes);
  if (!onward.length || plan.blocks.length > catalog.limits.max_path_length) return null;
  if (!open)
    return (
      <button className="text-sm text-fg-muted underline" onClick={() => setOpen(true)}>
        {t("Reach further…")}
      </button>
    );
  return (
    <span className="flex flex-wrap items-center gap-2">
      {onward.map((edge) => (
        <button
          key={`${edge.key}-${edge.direction}`}
          className="br-btn"
          onClick={() => {
            setOpen(false);
            const alias = `n${plan.blocks.length}`;
            const node = nodes[edge.node];
            change({
              ...plan,
              blocks: [
                ...plan.blocks,
                {
                  edge: {
                    key: edge.key,
                    direction: edge.direction,
                    label: edge.label,
                    fansOut: edge.fansOut,
                    from: edge.from,
                  },
                  alias,
                  node: edge.node,
                  filters: [],
                },
              ],
              // A list follows the records it reached; a summary keeps its own.
              groups: plan.measures.length || !node ? plan.groups : listColumns(node, alias),
            });
          }}
        >
          {edge.label}
          {edge.origin && <span className="text-xs text-fg-muted">({edge.origin})</span>}
          <span className={`text-xs ${edge.fansOut ? "text-warning-600" : "text-fg-muted"}`}>
            {edge.fansOut ? t("many") : t("one")}
          </span>
        </button>
      ))}
      <button className="text-xs text-fg-muted underline" onClick={() => setOpen(false)}>
        {t("Cancel")}
      </button>
    </span>
  );
}

/** Numbers line up under each other; axes read as text. */
const NUMERIC_CELL = "text-right tabular-nums";

/** The answer, and the place where most of the question is actually asked.
 *
 * A column header sorts. A value filters. The row count bounds. None of it
 * needs a control anywhere else, and all of it shows its effect immediately —
 * which is the whole reason this reads more easily than a builder.
 */
function Result({
  answer,
  refusal,
  busy,
  plan,
  nodes,
  ceiling,
  change,
}: {
  answer: GraphAnswer | null;
  refusal: Refusal | null;
  busy: boolean;
  plan: Plan;
  nodes: Record<string, GraphNode>;
  ceiling: number;
  change: (next: Plan) => void;
}) {
  const [shown, setShown] = useState(false);
  const axes = new Map(plan.groups.map((group) => [columnOf(group), group]));
  /** What kind of value a column holds, so a timestamp does not read as
   *  `2026-06-24 00:00:00+00:00` — which is a machine's spelling of a date. */
  const kinds = new Map<string, string>(
    plan.blocks.flatMap((block) =>
      (nodes[block.node]?.properties ?? []).map(
        (property) => [`${block.alias}.${property.key}`, property.kind] as [string, string],
      ),
    ),
  );
  const shownValue = (column: string, value: unknown) => {
    const axis = axes.get(column);
    if (!axis || kinds.get(axis.field) !== "time" || axis.bucket) return String(value);
    const text = String(value);
    return /[ T]00:00:00/.test(text) ? formatDate(text) : formatDateTime(text);
  };
  const labels: Record<string, string> = {};
  for (const group of plan.groups) labels[columnOf(group)] = group.label;
  for (const block of plan.blocks)
    for (const measure of nodes[block.node]?.measures ?? []) labels[measure.key] = measure.label;

  if (refusal)
    return (
      <div className="rounded-xl border border-warning-200 bg-warning-50 p-5">
        <div className="text-sm font-semibold text-warning-600">{refusal.headline}</div>
        <div className="mt-2 text-sm">{refusal.detail}</div>
      </div>
    );
  if (!answer)
    return (
      <div className="rounded-xl border border-dashed border-border-default p-10 text-center text-sm text-fg-muted">
        {t("Choose at least one number or one axis.")}
      </div>
    );

  const columns = answer.rows.length ? Object.keys(answer.rows[0]) : [];
  const numeric = (column: string) => (answer.question.measures ?? []).includes(column);
  const sortMark = (column: string) =>
    plan.order?.by === column ? (plan.order.descending ? "↓" : "↑") : "";

  return (
    <div className={`space-y-3 ${busy ? "opacity-60" : ""}`} aria-busy={busy}>
      {answer.rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border-default p-10 text-center text-sm text-fg-muted">
          {t("No records match. That is not proof that none exist upstream.")}
        </div>
      ) : (
        <div className="max-h-[34rem] overflow-auto rounded-xl border border-border-default bg-surface">
          <table className="w-full border-collapse text-sm">
            <thead className="sticky top-0 bg-surface">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    className={`border-b border-border-default px-3 py-2 font-medium ${
                      numeric(column) ? NUMERIC_CELL : "text-left"
                    }`}
                  >
                    <button
                      className="underline-offset-4 hover:underline"
                      title={t("Press again to reverse it, once more to leave it unsorted")}
                      onClick={() => change({ ...plan, order: nextOrder(plan.order, column) })}
                    >
                      {labels[column] ?? column}
                      {sortMark(column) && (
                        <span className="ml-1 text-fg-muted" aria-hidden="true">
                          {sortMark(column)}
                        </span>
                      )}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {answer.rows.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => {
                    const axis = axes.get(column);
                    const value = row[column];
                    return (
                      <td
                        key={column}
                        className={`border-b border-border-subtle px-3 py-2 ${
                          numeric(column) ? NUMERIC_CELL : ""
                        }`}
                      >
                        {value === null ? (
                          <span className="text-fg-muted">{t("Unknown")}</span>
                        ) : numeric(column) ? (
                          formatExactDecimal(value as string)
                        ) : axis && !axis.bucket ? (
                          <button
                            className="underline-offset-4 hover:underline"
                            title={`${t("Only")} ${axis.label} = ${value}`}
                            onClick={() =>
                              change(
                                withFilter(plan, {
                                  shown: `${axis.label} = ${value}`,
                                  conditions: [
                                    { field: axis.field, op: "eq", value: String(value) },
                                  ],
                                }),
                              )
                            }
                          >
                            {shownValue(column, value)}
                          </button>
                        ) : (
                          shownValue(column, value)
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="flex flex-wrap items-center gap-3 text-xs text-fg-muted">
        <span>
          {answer.rows.length} {t("rows")}
        </span>
        <AtMost
          limit={plan.limit}
          ceiling={ceiling}
          change={(limit) => change({ ...plan, limit })}
        />
        <button className="underline" onClick={() => setShown(!shown)}>
          {t("How this was worked out")}
        </button>
        {answer.path.length > 0 && <span>{answer.path.join(" · ")}</span>}
      </div>
      {shown && (
        <pre className="overflow-x-auto rounded-xl border border-border-default bg-surface p-3 font-mono text-xs">
          {answer.sql}
        </pre>
      )}
    </div>
  );
}

/** How many rows to bring back, in the sizes people mean and any other.
 *
 * The presets are the answer almost every time; the field is there because the
 * one time somebody wants 37 rows, a list of four sizes is a wall. It commits
 * on Enter or on leaving, so a question is not re-asked once per keystroke.
 */
function AtMost({
  limit,
  ceiling,
  change,
}: {
  limit: number;
  ceiling: number;
  change: (limit: number) => void;
}) {
  const [typed, setTyped] = useState("");
  const sizes = [10, 50, 200, 1000].filter((size) => size <= ceiling);
  const commit = () => {
    const wanted = Number.parseInt(typed, 10);
    setTyped("");
    if (Number.isFinite(wanted) && wanted >= 1) change(Math.min(wanted, ceiling));
  };
  return (
    <>
      {sizes.map((size) => (
        <button
          key={size}
          className={chip(limit === size)}
          aria-pressed={limit === size}
          onClick={() => change(size)}
        >
          {size}
        </button>
      ))}
      <input
        className="w-24 rounded-lg border border-border-default bg-surface px-2 py-2 text-sm"
        type="number"
        min={1}
        max={ceiling}
        aria-label={t("Another number of rows")}
        placeholder={sizes.includes(limit) ? t("rows") : String(limit)}
        value={typed}
        onChange={(event) => setTyped(event.target.value)}
        onBlur={commit}
        onKeyDown={(event) => {
          if (event.key === "Enter") commit();
        }}
      />
    </>
  );
}

function AddFilter({ fields, add }: { fields: Field[]; add: (filter: Filter) => void }) {
  const [field, setField] = useState("");
  const [op, setOp] = useState("eq");
  const [value, setValue] = useState("");
  const [from, setFrom] = useState("");
  const [until, setUntil] = useState("");
  const chosen = fields.find((candidate) => candidate.field === field);
  if (!fields.length) return null;

  const clear = () => {
    setField("");
    setOp("eq");
    setValue("");
    setFrom("");
    setUntil("");
  };
  const submit = (filter: Filter) => {
    add(filter);
    clear();
  };

  if (!chosen)
    return (
      <select
        className="rounded-lg border border-border-default bg-surface px-2 py-2 text-sm"
        aria-label={t("Add a filter")}
        value=""
        onChange={(event) => setField(event.target.value)}
      >
        <option value="">{t("Only where…")}</option>
        {fields.map((candidate) => (
          <option key={candidate.field} value={candidate.field}>
            {candidate.label}
          </option>
        ))}
      </select>
    );

  const operators = OPERATORS.filter((operator) => operator.kinds.includes(chosen.kind));
  const selected = operators.find((operator) => operator.key === op) ?? operators[0];

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm font-medium">{chosen.label}</span>
      {chosen.kind === "time" && (
        <>
          {periods().map((period) => (
            <button
              key={period.key}
              className="br-btn"
              onClick={() => submit(periodFilter(chosen.field, chosen.label, period))}
            >
              {period.label}
            </button>
          ))}
          <label className="flex items-center gap-1 text-xs text-fg-muted">
            {t("from")}
            <input
              type="date"
              className="rounded-lg border border-border-default bg-surface px-2 py-1 text-sm"
              value={from}
              onChange={(event) => setFrom(event.target.value)}
            />
          </label>
          <label className="flex items-center gap-1 text-xs text-fg-muted">
            {t("to")}
            <input
              type="date"
              className="rounded-lg border border-border-default bg-surface px-2 py-1 text-sm"
              value={until}
              onChange={(event) => setUntil(event.target.value)}
            />
          </label>
          {from && until && (
            <button
              className="br-btn"
              onClick={() =>
                submit(
                  periodFilter(chosen.field, chosen.label, {
                    label: `${formatDate(`${from}T00:00:00`)} – ${formatDate(`${until}T00:00:00`)}`,
                    from: new Date(`${from}T00:00:00`),
                    // The end of a named period is the day after it, so that a
                    // record stamped at noon on the last day is still inside.
                    until: new Date(new Date(`${until}T00:00:00`).getTime() + 86400000),
                  }),
                )
              }
            >
              {t("Use this period")}
            </button>
          )}
        </>
      )}
      {chosen.kind !== "time" && (
        <>
          <select
            className="rounded-lg border border-border-default bg-surface px-2 py-2 text-sm"
            aria-label={t("Comparison")}
            value={selected.key}
            onChange={(event) => setOp(event.target.value)}
          >
            {operators.map((operator) => (
              <option key={operator.key} value={operator.key}>
                {t(operator.label)}
              </option>
            ))}
          </select>
          {!selected.valueless &&
            (chosen.kind === "boolean" ? (
              <select
                className="rounded-lg border border-border-default bg-surface px-2 py-2 text-sm"
                aria-label={t("Value")}
                value={value}
                onChange={(event) => setValue(event.target.value)}
              >
                <option value="">…</option>
                <option value="true">{t("yes")}</option>
                <option value="false">{t("no")}</option>
              </select>
            ) : (
              <input
                className="rounded-lg border border-border-default bg-surface px-2 py-2 text-sm"
                inputMode={chosen.kind === "number" ? "decimal" : "text"}
                aria-label={t("Value")}
                value={value}
                onChange={(event) => setValue(event.target.value)}
              />
            ))}
          <button
            className="br-btn"
            disabled={!selected.valueless && !value}
            onClick={() => {
              const label = t(selected.label);
              submit({
                shown: `${chosen.label} ${label}${selected.valueless ? "" : ` ${value}`}`,
                conditions: [
                  {
                    field: chosen.field,
                    op: selected.key,
                    ...(selected.valueless
                      ? {}
                      : { value: chosen.kind === "boolean" ? value === "true" : value }),
                  },
                ],
              });
            }}
          >
            {t("Add")}
          </button>
        </>
      )}
      <button className="text-xs text-fg-muted underline" onClick={clear}>
        {t("Cancel")}
      </button>
    </div>
  );
}

function AddGroup({ fields, add }: { fields: Field[]; add: (group: Group) => void }) {
  if (!fields.length) return null;
  return (
    <select
      className="rounded-lg border border-border-default bg-surface px-2 py-2 text-sm"
      aria-label={t("Split by another field")}
      value=""
      onChange={(event) => {
        const chosen = fields.find((candidate) => candidate.field === event.target.value);
        if (!chosen) return;
        // A raw timestamp gives one row per instant, which is a list rather
        // than an answer, so time is split by month unless somebody says
        // otherwise.
        add(
          chosen.kind === "time"
            ? { field: chosen.field, label: `${chosen.label} (${t("month")})`, bucket: "month" }
            : { field: chosen.field, label: chosen.label },
        );
      }}
    >
      <option value="">{t("Add…")}</option>
      {fields.map((candidate) => (
        <option key={candidate.field} value={candidate.field}>
          {candidate.label}
        </option>
      ))}
    </select>
  );
}

/** Save the question, never its answer.
 *
 * Reopening re-executes it, so what comes back is a fresh observation rather
 * than a preserved number — the only honest thing a report can be when the
 * records underneath it keep changing.
 */
function Save({
  tenant,
  plan,
  report,
  onSaved,
}: {
  tenant: string;
  plan: Plan;
  report: GraphReport | null;
  onSaved?: (report: GraphReport) => void;
}) {
  const [naming, setNaming] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState("");
  const [saved, setSaved] = useState<string>("");

  const send = async (change: Parameters<typeof graphApi.change>[1]) => {
    setBusy(true);
    setFailed("");
    try {
      const stored = await graphApi.change(tenant, change);
      setNaming(false);
      setName("");
      setSaved(stored.name);
      onSaved?.(stored);
    } catch (failure) {
      setFailed(failure instanceof Error ? failure.message : analyticsError(failure));
    } finally {
      setBusy(false);
    }
  };

  if (naming)
    return (
      <div className="flex flex-wrap items-center gap-2">
        <input
          className="rounded-lg border border-border-default bg-surface px-2 py-2 text-sm"
          aria-label={t("Report name")}
          autoFocus
          value={name}
          onChange={(event) => setName(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && name.trim())
              void send({
                operation: "create",
                request_id: crypto.randomUUID(),
                name: name.trim(),
                question: question(plan),
              });
          }}
        />
        <button
          className="br-btn"
          disabled={busy || !name.trim()}
          onClick={() =>
            void send({
              operation: "create",
              request_id: crypto.randomUUID(),
              name: name.trim(),
              question: question(plan),
            })
          }
        >
          {busy ? t("Saving…") : t("Save")}
        </button>
        <button className="text-xs text-fg-muted underline" onClick={() => setNaming(false)}>
          {t("Cancel")}
        </button>
        {failed && <span className="text-xs text-warning-600">{failed}</span>}
      </div>
    );

  return (
    <div className="flex flex-wrap items-center gap-3 text-sm">
      {report && (
        <button
          className="br-btn"
          disabled={busy}
          onClick={() =>
            void send({
              operation: "update",
              request_id: crypto.randomUUID(),
              report_id: report.id,
              expected_revision: report.revision,
              question: question(plan),
            })
          }
        >
          {busy ? t("Saving…") : `${t("Save")} „${report.name}“`}
        </button>
      )}
      <button className="text-fg-muted underline" onClick={() => setNaming(true)}>
        {report ? t("Save as a new report") : t("Save this question")}
      </button>
      {saved && <span className="text-xs text-fg-muted">{t("Saved")}</span>}
      {failed && <span className="text-xs text-warning-600">{failed}</span>}
    </div>
  );
}
