import { useMemo, useState } from "react";
import {
  APIError,
  graphApi,
  type GraphAnswer,
  type GraphCatalog,
  type GraphNode,
  type GraphQuestion,
} from "../../api";
import { currentLanguage, formatExactDecimal, t } from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { chip } from "./chips";
import { analyticsError } from "./errors";

/** A question read top to bottom as the steps that build it.
 *
 * The model is already a sequence — start somewhere, reach further, narrow,
 * count, split — so the page shows that sequence instead of three lists side by
 * side. Each step offers only what is valid where it stands, which is the part
 * a fixed form cannot do and the declaration makes free.
 */

/** One readable line, which may take more than one condition to mean.
 *
 * "Order date this year" is two comparisons. Keeping them in one row is what
 * lets somebody remove the period rather than half of it.
 */
type Condition = { field: string; op: string; value?: unknown };
type Filter = { shown: string; conditions: Condition[] };
type Block = {
  /** The first block has no hop; every later one carries the edge that reached it. */
  edge?: { key: string; direction: "out" | "in"; label: string; fansOut: boolean };
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

const TIME_FIELDS = ["ordered_at", "document_date", "occurred_at", "effective_at", "allocated_at"];

/** Questions somebody would actually ask, built from what this company declares.
 *
 * A first screen of empty steps asks the reader to know the model. A first
 * screen of real questions asks them to recognise their own work, and every one
 * of them opens as a stack they can take apart step by step.
 */
function suggestions(catalog: GraphCatalog): { title: string; where: string; plan: Plan }[] {
  const out: { title: string; where: string; plan: Plan }[] = [];
  for (const node of catalog.nodes) {
    const amount = node.measures.find((measure) => measure.unit === "currency");
    const count = node.measures.find((measure) => measure.unit === "count");
    const currency = node.properties.find((property) => property.key === "currency");
    const time = node.properties.find((property) => TIME_FIELDS.includes(property.key));
    const base = {
      blocks: [{ alias: "o", node: node.key, filters: [] }],
      groups: [] as Group[],
      limit: 200,
    };
    if (amount && currency) {
      out.push({
        title: `${amount.label} ${t("by")} ${currency.label}`,
        where: node.label,
        plan: {
          ...base,
          measures: [amount.key],
          groups: [{ field: `o.${currency.key}`, label: currency.label }],
        },
      });
      if (time)
        out.push({
          title: `${amount.label} ${t("by")} ${t("month")}`,
          where: node.label,
          plan: {
            ...base,
            measures: [amount.key],
            groups: [
              { field: `o.${time.key}`, label: `${time.label} (${t("month")})`, bucket: "month" },
              { field: `o.${currency.key}`, label: currency.label },
            ],
          },
        });
    }
    if (count && currency)
      out.push({
        title: `${count.label} ${t("by")} ${currency.label}`,
        where: node.label,
        plan: {
          ...base,
          measures: [count.key],
          groups: [{ field: `o.${currency.key}`, label: currency.label }],
        },
      });
  }
  return out.slice(0, 6);
}

export function GraphSteps({ tenant }: { tenant: string }) {
  const language = currentLanguage();
  const read = useRead(() => graphApi.catalog(tenant, language), [tenant, language]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return <Builder key={tenant} tenant={tenant} catalog={read.data} />;
}

/** The question as the server has to receive it. */
export function question(plan: Plan): GraphQuestion {
  return {
    from: plan.blocks[0].node,
    as: plan.blocks[0].alias,
    follow: plan.blocks.slice(1).map((block) => ({
      edge: block.edge!.key,
      direction: block.edge!.direction,
      as: block.alias,
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
  return {
    ...plan,
    measures,
    groups: plan.groups.filter((group) => aliases.has(group.field.split(".")[0])),
    order: plan.order && measures.includes(plan.order.by) ? plan.order : undefined,
  };
}

function Builder({ tenant, catalog }: { tenant: string; catalog: GraphCatalog }) {
  const nodes = useMemo(
    () =>
      Object.fromEntries(catalog.nodes.map((node) => [node.key, node])) as Record<
        string,
        GraphNode
      >,
    [catalog],
  );
  const starters = useMemo(() => suggestions(catalog), [catalog]);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [answer, setAnswer] = useState<GraphAnswer | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [busy, setBusy] = useState(false);

  const ask = async (next: Plan) => {
    const settled = pruned(next, nodes);
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

  if (!plan)
    return (
      <section className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold">{t("What would you like to know?")}</h2>
          <div className="mt-1 max-w-2xl text-sm text-fg-muted">
            {t(
              "Open a question and take it apart step by step, or start from the records themselves.",
            )}
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {starters.map((starter) => (
            <button
              key={`${starter.where}-${starter.title}`}
              className="rounded-xl border border-border-default bg-surface p-4 text-left hover:border-accent"
              onClick={() => ask(starter.plan)}
            >
              <div className="font-medium">{starter.title}</div>
              <div className="mt-1 text-xs text-fg-muted">{starter.where}</div>
            </button>
          ))}
        </div>
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">{t("Or start from the records")}</legend>
          <div className="flex flex-wrap gap-2">
            {catalog.nodes
              .filter((node) => node.measures.length > 0)
              .map((node) => (
                <button
                  key={node.key}
                  className="br-btn"
                  title={node.grain}
                  onClick={() =>
                    ask({
                      blocks: [{ alias: "o", node: node.key, filters: [] }],
                      measures: [node.measures[0].key],
                      groups: [],
                      limit: 200,
                    })
                  }
                >
                  {node.label}
                </button>
              ))}
          </div>
        </fieldset>
      </section>
    );

  return (
    <section className="grid items-start gap-6 lg:grid-cols-[minmax(0,460px)_minmax(0,1fr)]">
      <Stack
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
      <Answer answer={answer} refusal={refusal} busy={busy} plan={plan} nodes={nodes} />
    </section>
  );
}

function Step({
  label,
  children,
  remove,
}: {
  label: string;
  children: React.ReactNode;
  remove?: { title: string; act: () => void };
}) {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      <div className="w-28 shrink-0 pt-2 text-xs uppercase tracking-wide text-fg-muted">
        {label}
      </div>
      <div className="flex flex-1 flex-wrap items-center gap-2">{children}</div>
      {remove && (
        <button
          className="shrink-0 pt-2 text-fg-muted hover:text-fg-strong"
          title={remove.title}
          aria-label={remove.title}
          onClick={remove.act}
        >
          ×
        </button>
      )}
    </div>
  );
}

function Stack({
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
  const [reaching, setReaching] = useState(false);
  const measures = plan.blocks.flatMap((block) => nodes[block.node]?.measures ?? []);
  const fieldsOf = (block: Block): Field[] =>
    (nodes[block.node]?.properties ?? []).map((property) => ({
      field: `${block.alias}.${property.key}`,
      label: property.label,
      kind: property.kind,
    }));
  const fields = plan.blocks.flatMap(fieldsOf);
  const tip = plan.blocks[plan.blocks.length - 1];
  const onward = [
    ...(nodes[tip.node]?.edges ?? []).map((edge) => ({
      key: edge.key,
      label: `${edge.label} ${edge.to_label}`,
      node: edge.to,
      direction: "out" as const,
      fansOut: fansOut(edge.multiplicity, "out"),
    })),
    // An edge is worded for the way it was declared. Followed backwards that
    // wording reads the wrong way round — "for order Commitment" — so the
    // record reached leads and the relation follows it in brackets.
    ...(nodes[tip.node]?.edges_in ?? []).map((edge) => ({
      key: edge.key,
      label: `${edge.from_label} (${edge.label})`,
      node: edge.from,
      direction: "in" as const,
      fansOut: fansOut(edge.multiplicity, "in"),
    })),
  ];
  const withBlocks = (blocks: Block[]) => ({ ...plan, blocks });

  return (
    <div className="space-y-3">
      <div className="divide-y divide-border-default rounded-xl border border-border-default bg-surface">
        {plan.blocks.map((block, index) => (
          <div key={block.alias} className="divide-y divide-border-subtle">
            <Step
              label={index === 0 ? t("Data") : t("Then")}
              remove={
                index > 0
                  ? {
                      title: t("Remove this step and everything after it"),
                      act: () => change(withBlocks(plan.blocks.slice(0, index))),
                    }
                  : undefined
              }
            >
              <span className="font-medium">
                {index === 0 ? nodes[block.node]?.label : block.edge?.label}
              </span>
              {block.edge?.fansOut && <span className="text-xs text-warning-600">{t("many")}</span>}
            </Step>
            {block.filters.map((filter, position) => (
              <Step
                key={`${block.alias}-${position}`}
                label={t("Only")}
                remove={{
                  title: t("Remove this filter"),
                  act: () =>
                    change(
                      withBlocks(
                        plan.blocks.map((candidate, at) =>
                          at === index
                            ? {
                                ...candidate,
                                filters: candidate.filters.filter((_, p) => p !== position),
                              }
                            : candidate,
                        ),
                      ),
                    ),
                }}
              >
                <span className="text-sm">{filter.shown}</span>
              </Step>
            ))}
            <Step label="">
              <AddFilter
                key={block.alias}
                fields={fieldsOf(block)}
                add={(filter) =>
                  change(
                    withBlocks(
                      plan.blocks.map((candidate, at) =>
                        at === index
                          ? { ...candidate, filters: [...candidate.filters, filter] }
                          : candidate,
                      ),
                    ),
                  )
                }
              />
            </Step>
          </div>
        ))}

        {onward.length > 0 && plan.blocks.length <= catalog.limits.max_path_length && (
          <Step label={t("Then")}>
            {reaching ? (
              <>
                {onward.map((edge) => (
                  <button
                    key={`${edge.key}-${edge.direction}`}
                    className="br-btn"
                    onClick={() => {
                      setReaching(false);
                      change(
                        withBlocks([
                          ...plan.blocks,
                          {
                            edge: {
                              key: edge.key,
                              direction: edge.direction,
                              label: edge.label,
                              fansOut: edge.fansOut,
                            },
                            alias: `n${plan.blocks.length}`,
                            node: edge.node,
                            filters: [],
                          },
                        ]),
                      );
                    }}
                  >
                    {edge.label}
                    <span
                      className={`text-xs ${edge.fansOut ? "text-warning-600" : "text-fg-muted"}`}
                    >
                      {edge.fansOut ? t("many") : t("one")}
                    </span>
                  </button>
                ))}
                <button
                  className="text-xs text-fg-muted underline"
                  onClick={() => setReaching(false)}
                >
                  {t("Cancel")}
                </button>
              </>
            ) : (
              <button className="text-sm text-fg-muted underline" onClick={() => setReaching(true)}>
                {t("Reach further…")}
              </button>
            )}
          </Step>
        )}

        <Step label={t("Count")}>
          {measures.map((measure) => (
            <button
              key={measure.key}
              className={chip(plan.measures.includes(measure.key))}
              aria-pressed={plan.measures.includes(measure.key)}
              onClick={() =>
                change({
                  ...plan,
                  measures: plan.measures.includes(measure.key)
                    ? plan.measures.filter((item) => item !== measure.key)
                    : [...plan.measures, measure.key],
                })
              }
            >
              {measure.label}
            </button>
          ))}
        </Step>

        <Step label={t("Split by")}>
          {plan.groups.map((group) => (
            <button
              key={`${group.field}-${group.bucket ?? ""}`}
              className={chip(true)}
              aria-pressed={true}
              title={t("Remove this axis")}
              onClick={() =>
                change({
                  ...plan,
                  groups: plan.groups.filter(
                    (candidate) =>
                      !(candidate.field === group.field && candidate.bucket === group.bucket),
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
        </Step>

        {plan.measures.length > 0 && (
          <Step label={t("Biggest first")}>
            {plan.measures.map((key) => (
              <button
                key={key}
                className={chip(plan.order?.by === key)}
                aria-pressed={plan.order?.by === key}
                onClick={() =>
                  change({
                    ...plan,
                    order: plan.order?.by === key ? undefined : { by: key, descending: true },
                  })
                }
              >
                {measures.find((measure) => measure.key === key)?.label ?? key}
              </button>
            ))}
          </Step>
        )}

        <Step label={t("At most")}>
          {[10, 50, 200, 1000].map((size) => (
            <button
              key={size}
              className={chip(plan.limit === size)}
              aria-pressed={plan.limit === size}
              onClick={() => change({ ...plan, limit: size })}
            >
              {size}
            </button>
          ))}
        </Step>
      </div>
      <button className="text-sm text-fg-muted underline" onClick={restart}>
        {t("Start a different question")}
      </button>
    </div>
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
                    label: `${from} – ${until}`,
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

/** Numbers line up under each other; axes read as text. */
const NUMERIC_CELL = "text-right tabular-nums";

function Answer({
  answer,
  refusal,
  busy,
  plan,
  nodes,
}: {
  answer: GraphAnswer | null;
  refusal: Refusal | null;
  busy: boolean;
  plan: Plan;
  nodes: Record<string, GraphNode>;
}) {
  const [shown, setShown] = useState(false);
  // The answer comes back keyed by field path and measure key. A person reads
  // neither, so the words from the model travel with the question.
  const labels: Record<string, string> = {};
  for (const group of plan.groups) labels[group.bucket ? group.label : group.field] = group.label;
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
                    {labels[column] ?? column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {answer.rows.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => (
                    <td
                      key={column}
                      className={`border-b border-border-subtle px-3 py-2 ${
                        numeric(column) ? NUMERIC_CELL : ""
                      }`}
                    >
                      {row[column] === null
                        ? t("Unknown")
                        : numeric(column)
                          ? formatExactDecimal(row[column] as string)
                          : String(row[column])}
                    </td>
                  ))}
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
        {answer.path.length > 0 && <span>{answer.path.join(" · ")}</span>}
        <button className="underline" onClick={() => setShown(!shown)}>
          {t("How this was worked out")}
        </button>
      </div>
      {shown && (
        <pre className="overflow-x-auto rounded-xl border border-border-default bg-surface p-3 font-mono text-xs">
          {answer.sql}
        </pre>
      )}
    </div>
  );
}
