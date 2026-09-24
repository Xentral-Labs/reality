import { InventoryValuationSelector, InventoryValuationBasis } from "./InventoryValuation";
import { catalogGroups } from "./catalog";
import { openAnalysisChat } from "./chatHandoff";
import "./AnalysisBuilder.css";
import { RegisterHeader } from "../RegisterWorkbench";
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
  formatCalendarDate,
  formatDateTime,
  formatExactDecimal,
  t,
} from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { chip } from "./chips";
import { analyticsError } from "./errors";
import { sameQuestion, suggestedName } from "./reportName";

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
  capturedCostContext?: GraphQuestion["captured_cost_context"];
  companyCostContext?: GraphQuestion["company_cost_context"];
  contributionCostContext?: GraphQuestion["contribution_cost_context"];
  inventoryCostContext?: GraphQuestion["inventory_cost_context"];
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
  cost_basis_pending:
    "New data arrived after this confirmation. Turn off the freshness requirement to inspect its historical values, or select a newly confirmed basis.",
  cost_basis_unavailable: "The selected valuation is not fully available yet.",
  cost_context_required: "Select a confirmed inventory valuation.",
  cost_context_invalid: "This valuation belongs to a standalone inventory report.",
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
  service_measure:
    "This number is worked out in one authoritative place, and this page cannot run it yet.",
};

function refusalOf(failure: unknown): Refusal {
  const code = failure instanceof APIError ? failure.code : undefined;
  return {
    headline: t((code && REFUSALS[code]) || "This question cannot be answered correctly"),
    detail: analyticsError(failure),
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
      key: "last_30_days",
      label: t("the last 30 days"),
      from: new Date(year, month, day.getDate() - 29),
      until: new Date(year, month, day.getDate() + 1),
    },
  ];
}

/** One named window, resolved where the reader is.
 *
 * A template says which window it means and leaves the resolving to whoever
 * adopts it: "this month" is a different pair of instants in Auckland and in
 * Lisbon, and only the browser asking knows which.
 */
export function periodOf(window: string, temporal?: "date"): Filter | null {
  const found = periods().find((period) => period.key === window);
  return found ? periodFilter("", "", found, temporal) : null;
}

/** The bound as a real instant.
 *
 * "This year" starts at midnight where the reader is, which is a different
 * moment from midnight UTC. Sending the instant rather than the wall-clock text
 * is what keeps an hour of December out of January.
 */
function instant(value: Date, temporal?: "date") {
  if (temporal === "date")
    return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
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
  temporal?: "date",
): Filter {
  return {
    shown: `${label} ${period.label}`,
    conditions: [
      { field, op: "gte", value: instant(period.from, temporal) },
      { field, op: "lt", value: instant(period.until, temporal) },
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

type Field = {
  field: string;
  label: string;
  kind: string;
  temporal?: "date";
  input?: "date";
  values?: string[];
};

export function GraphSteps({
  tenant,
  report,
  onSaved,
  onLibrary,
  initialQuestion,
  initialName,
  active = true,
  onNew,
}: {
  tenant: string;
  active?: boolean;
  onNew?: () => void;
  onLibrary?: () => void;
  initialQuestion?: GraphQuestion;
  /** The name this analysis arrived with: a template's label, or the name the
   *  copilot proposed. Without it the naming field opened blank on exactly the
   *  two paths that already knew what this report is called. */
  initialName?: string;
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
      initialQuestion={initialQuestion}
      initialName={initialName}
      active={active}
      onNew={onNew}
      onLibrary={onLibrary}
      onSaved={onSaved}
    />
  );
}

/** The question as the server has to receive it. */
export function question(plan: Plan): GraphQuestion {
  return {
    from: plan.blocks[0].node,
    ...(plan.capturedCostContext ? { captured_cost_context: plan.capturedCostContext } : {}),
    ...(plan.companyCostContext ? { company_cost_context: plan.companyCostContext } : {}),
    ...(plan.contributionCostContext
      ? { contribution_cost_context: plan.contributionCostContext }
      : {}),
    ...(plan.inventoryCostContext ? { inventory_cost_context: plan.inventoryCostContext } : {}),
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
  if (
    question.having?.length ||
    question.exists?.length ||
    (question.order_by?.length ?? 0) > 1 ||
    question.follow?.some((hop) => hop.depth) ||
    question.group_by?.some((group) => group.as && !group.bucket)
  )
    return null;
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
        direction: hop.direction ?? "out",
        label:
          hop.direction === "in"
            ? `${(edge as { from_label: string }).from_label} (${edge.label})`
            : `${edge.label} ${(edge as { to_label: string }).to_label}`,
        fansOut: fansOut(edge.multiplicity, hop.direction ?? "out"),
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
    capturedCostContext: question.captured_cost_context,
    companyCostContext: question.company_cost_context,
    inventoryCostContext: question.inventory_cost_context,
    contributionCostContext: question.contribution_cost_context,
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
function nextCalendarDay(value: string) {
  const date = new Date(`${value}T00:00:00`);
  date.setDate(date.getDate() + 1);
  return date;
}

function shortDate(value: unknown) {
  if (typeof value !== "string") return String(value ?? "");
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return formatCalendarDate(value);
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
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const previous = new Date(`${value}T00:00:00Z`);
    previous.setUTCDate(previous.getUTCDate() - 1);
    return formatCalendarDate(previous.toISOString().slice(0, 10));
  }
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
  if (node.key === "contribution_valuation")
    return {
      blocks: [{ alias: "o", node: node.key, filters: [] }],
      measures: [
        "contribution_db1",
        "contribution_db2",
        "contribution_db1_rate",
        "contribution_db2_rate",
        "contribution_db1_covered",
        "contribution_db2_covered",
        "contribution_db2_required",
      ],
      groups: ["currency", "base_unit"].map((key) => ({
        field: `o.${key}`,
        label: node.properties.find((p) => p.key === key)?.label ?? key,
      })),
      limit: 50,
    };
  if (node.key === "inventory_valuation")
    return {
      blocks: [{ alias: "o", node: node.key, filters: [] }],
      measures: ["inventory_acquisition_value"],
      groups: [
        {
          field: "o.currency",
          label: node.properties.find((p) => p.key === "currency")?.label ?? t("Currency"),
        },
      ],
      limit: 50,
    };
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
  onLibrary,
  initialQuestion,
  initialName,
  active = true,
  onNew,
}: {
  tenant: string;
  active?: boolean;
  onNew?: () => void;
  onLibrary?: () => void;
  catalog: GraphCatalog;
  report: GraphReport | null;
  initialQuestion?: GraphQuestion;
  initialName?: string;
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
  const first = nodes.order ?? catalog.nodes[0];
  const [plan, setPlan] = useState<Plan | null>(() =>
    report
      ? planOf(report.definition, nodes)
      : initialQuestion
        ? planOf(initialQuestion, nodes)
        : first
          ? listPlan(first)
          : null,
  );
  const [canonical, setCanonical] = useState<GraphQuestion | null>(
    report?.definition ?? initialQuestion ?? null,
  );
  const [activeReport, setActiveReport] = useState(report);
  // The question as it stands saved, so "unsaved changes" is a comparison and
  // not a guess. The server answers canonicalized, so what is compared is the
  // canonical form of the first answer after a load or a save, never the text
  // that was stored.
  const [baseline, setBaseline] = useState<GraphQuestion | null>(null);
  const capture = useRef(Boolean(report));
  const [answer, setAnswer] = useState<GraphAnswer | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState<"result" | "connections" | "cypher">("result");
  const [path, setPath] = useState("");
  const [parameters, setParameters] = useState("{}");
  const [draft, setDraft] = useState(false);
  const [readAt, setReadAt] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const start = () => {
    controller.current?.abort();
    controller.current = new AbortController();
    const id = ++generation.current;
    setBusy(true);
    setRefusal(null);
    setNotice("");
    setAnswer(null);
    setReadAt(null);
    return { id, signal: controller.current.signal };
  };
  const receive = (value: GraphAnswer, id: number, keepText = false) => {
    if (id !== generation.current) return;
    setAnswer(value);
    setCanonical(value.question);
    setPlan(planOf(value.question, nodes));
    setReadAt(new Date().toISOString());
    setDraft(false);
    if (capture.current) {
      capture.current = false;
      setBaseline(value.question);
    }
    if (!keepText) {
      setPath(value.editor?.path ?? "");
      setParameters(JSON.stringify(value.editor?.parameters ?? {}, null, 2));
    }
    if (!planOf(value.question, nodes))
      setNotice(t("This query uses expert clauses. Its full definition is preserved."));
    if (
      value.editor?.reason &&
      !value.question.captured_cost_context &&
      !value.question.company_cost_context &&
      !value.question.inventory_cost_context &&
      !value.question.contribution_cost_context
    )
      setNotice(value.editor.reason);
  };
  const fail = (error: unknown, id: number) => {
    if (
      id === generation.current &&
      !(error instanceof DOMException && error.name === "AbortError")
    )
      setRefusal(refusalOf(error));
  };
  const execute = async (value: GraphQuestion, keepText = false) => {
    const { id, signal } = start();
    setCanonical(value);
    if (
      (value.from === "inventory_valuation" &&
        !value.inventory_cost_context &&
        !value.captured_cost_context &&
        !value.company_cost_context) ||
      (value.from === "contribution_valuation" &&
        !value.contribution_cost_context &&
        !value.captured_cost_context &&
        !value.company_cost_context)
    ) {
      setBusy(false);
      return;
    }
    try {
      receive(await graphApi.ask(tenant, value, signal), id, keepText);
    } catch (error) {
      fail(error, id);
    } finally {
      if (id === generation.current) setBusy(false);
    }
  };
  const ask = async (next: Plan) => {
    const settled = pruned(
      withRequiredAxes(
        next,
        next.blocks.flatMap((block) => nodes[block.node]?.measures ?? []),
        fieldsOf(next, nodes),
      ),
      nodes,
    );
    setPlan(settled);
    setSelected(null);
    setDraft(false);
    await execute(question(settled));
  };
  useEffect(() => {
    if (report) void execute(report.definition);
    else if (initialQuestion) void execute(initialQuestion);
    else if (plan) void execute(question(plan));
    return () => {
      controller.current?.abort();
      generation.current++;
    };
  }, []);
  const executePath = async () => {
    const { id, signal } = start();
    try {
      const values: unknown = JSON.parse(parameters);
      if (!values || Array.isArray(values) || typeof values !== "object")
        throw new Error(t("Parameters must be a JSON object."));
      receive(
        await graphApi.askPath(tenant, path, signal, values as Record<string, unknown>),
        id,
        true,
      );
    } catch (error) {
      fail(error, id);
    } finally {
      if (id === generation.current) setBusy(false);
    }
  };
  const editDraft = () => {
    controller.current?.abort();
    generation.current++;
    setBusy(false);
    setDraft(true);
    setReadAt(null);
    setRefusal(null);
  };
  const inspectPlan =
    plan ??
    (canonical
      ? planOf(
          {
            ...canonical,
            having: [],
            exists: [],
            order_by: [],
            follow: canonical.follow?.map((hop) => ({ ...hop, depth: undefined })),
            group_by: canonical.group_by?.map((group) => ({ ...group, as: undefined })),
          },
          nodes,
        )
      : null);
  const shownPlan = inspectPlan ?? (first ? listPlan(first) : null);
  if (!shownPlan)
    return <div className="analysis-empty">{t("No analysis records are available.")}</div>;
  const controlsLocked = draft || !plan;
  const change = (next: Plan) => {
    if (!controlsLocked) void ask(next);
  };
  const tabs = [
    ["result", "Result"],
    ["connections", "Connections"],
    ["cypher", "Cypher"],
  ] as const;
  return (
    <section className="analysis-builder register-surface" aria-busy={busy}>
      <div className="analysis-card">
        <fieldset disabled={busy || draft || !answer} className="analysis-save">
          <Save
            tenant={tenant}
            plan={shownPlan}
            nodes={nodes}
            definition={canonical ?? undefined}
            report={activeReport}
            draftName={initialName ?? ""}
            changed={!activeReport || !sameQuestion(baseline, canonical)}
            onSaved={(stored) => {
              // Without this the builder never learned that it had been saved:
              // it kept offering to create, and a second save wrote a second
              // report with the same question.
              setActiveReport(stored);
              setBaseline(canonical);
              onSaved?.(stored);
            }}
            onLibrary={onLibrary}
            active={active}
            onNew={onNew}
            disabled={busy || draft || !answer}
          />
        </fieldset>
        <section
          className="analysis-question-section"
          aria-label={t("How Reality understands your question")}
        >
          <header className="analysis-question-heading">
            <h2>{t("How Reality understands your question")}</h2>
            <button
              className="br-btn analysis-chat-action"
              disabled={busy || draft || !answer}
              onClick={() =>
                openAnalysisChat(
                  tenant,
                  activeReport?.name ?? t("Current analysis"),
                  canonical ?? question(shownPlan),
                )
              }
            >
              <svg
                aria-hidden="true"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
              >
                <path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H5l-3 3V11.5A7.5 7.5 0 0 1 9.5 4h3a7.5 7.5 0 0 1 7.5 7.5Z" />
              </svg>
              {t("Adapt with chat")}
            </button>
          </header>
          {notice && (
            <p className="analysis-notice" role="status">
              {notice}
            </p>
          )}
          {controlsLocked ? (
            <div className="analysis-interpretation">
              <p>
                {draft
                  ? t("Execute your edited query before changing the sentence or saving.")
                  : t("This query uses expert clauses. Its full definition is preserved.")}
              </p>
              <button className="br-btn" onClick={() => setTab("cypher")}>
                {t("Open query editor")}
              </button>
              <button
                className="br-btn"
                onClick={() => {
                  setDraft(false);
                  setActiveReport(null);
                  setPath("");
                  setParameters("{}");
                  void ask(listPlan(first));
                }}
              >
                {t("Start a new analysis")}
              </button>
            </div>
          ) : (
            <Toolbar catalog={catalog} nodes={nodes} plan={plan} change={change} />
          )}
          {shownPlan.blocks[0].node === "contribution_valuation" && (
            <InventoryValuationSelector
              key={`${tenant}:contribution`}
              contribution
              tenant={tenant}
              context={shownPlan.contributionCostContext}
              capturedContext={shownPlan.capturedCostContext}
              companyContext={shownPlan.companyCostContext}
              disabled={controlsLocked}
              select={(context) =>
                change({
                  ...shownPlan,
                  contributionCostContext: context,
                  capturedCostContext: undefined,
                  companyCostContext: undefined,
                })
              }
              selectCaptured={(context) =>
                change({
                  ...shownPlan,
                  capturedCostContext: context,
                  contributionCostContext: undefined,
                  companyCostContext: undefined,
                })
              }
              selectCompany={(context) =>
                change({
                  ...shownPlan,
                  companyCostContext: context,
                  contributionCostContext: undefined,
                  capturedCostContext: undefined,
                })
              }
            />
          )}
          {shownPlan.blocks[0].node === "inventory_valuation" && (
            <InventoryValuationSelector
              key={tenant}
              tenant={tenant}
              context={shownPlan.inventoryCostContext}
              capturedContext={shownPlan.capturedCostContext}
              companyContext={shownPlan.companyCostContext}
              disabled={controlsLocked}
              select={(context) =>
                change({
                  ...shownPlan,
                  inventoryCostContext: context
                    ? { action_id: context.action_id, mode: "historical" }
                    : undefined,
                  capturedCostContext: undefined,
                  companyCostContext: undefined,
                })
              }
              selectCaptured={(context) =>
                change({
                  ...shownPlan,
                  capturedCostContext: context,
                  inventoryCostContext: undefined,
                  companyCostContext: undefined,
                })
              }
              selectCompany={(context) =>
                change({
                  ...shownPlan,
                  companyCostContext: context,
                  inventoryCostContext: undefined,
                  capturedCostContext: undefined,
                })
              }
            />
          )}
        </section>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <RegisterHeader title="Analysis views" placement="local">
            <div className="register-tabs" role="tablist" aria-label={t("Analysis views")}>
              {tabs.map(([key, label], index) => (
                <button
                  key={key}
                  id={`analysis-tab-${key}`}
                  role="tab"
                  aria-selected={tab === key}
                  aria-pressed={tab === key}
                  aria-controls={`analysis-panel-${key}`}
                  tabIndex={tab === key ? 0 : -1}
                  onClick={() => setTab(key)}
                  onKeyDown={(event) => {
                    const target =
                      event.key === "ArrowRight"
                        ? (index + 1) % 3
                        : event.key === "ArrowLeft"
                          ? (index + 2) % 3
                          : event.key === "Home"
                            ? 0
                            : event.key === "End"
                              ? 2
                              : -1;
                    if (target >= 0) {
                      event.preventDefault();
                      setTab(tabs[target][0]);
                      document.getElementById(`analysis-tab-${tabs[target][0]}`)?.focus();
                    }
                  }}
                >
                  {t(label)}
                </button>
              ))}
            </div>
          </RegisterHeader>
        </div>
        <div
          className="analysis-panel"
          id={`analysis-panel-${tab}`}
          role="tabpanel"
          aria-labelledby={`analysis-tab-${tab}`}
          tabIndex={0}
        >
          {tab === "result" && (
            <>
              {answer?.cost_basis && !busy && !draft && (
                <InventoryValuationBasis tenant={tenant} basis={answer.cost_basis} />
              )}
              <div className="analysis-metrics">
                <div>
                  <span>{t("Returned rows")}</span>
                  <strong>{answer && !busy && !draft ? answer.rows.length : "—"}</strong>
                  <small>{t("Bounded by the selected row limit")}</small>
                </div>
                <div>
                  <span>{t("Selected measures")}</span>
                  <strong>{canonical?.measures?.length ?? 0}</strong>
                  <small>{t("Currencies and units stay separate")}</small>
                </div>
                <div>
                  <span>{t("Last successful read")}</span>
                  <strong className="analysis-read-time">
                    {readAt ? formatDateTime(readAt) : "—"}
                  </strong>
                  <small>{t("An observation of the available records")}</small>
                </div>
              </div>
              {draft ? (
                <p className="analysis-notice">
                  {t("Execute your edited query to update the result.")}
                </p>
              ) : (
                <Result
                  answer={answer}
                  refusal={refusal}
                  busy={busy}
                  plan={shownPlan}
                  nodes={nodes}
                  ceiling={catalog.limits.result_rows}
                  change={change}
                />
              )}
            </>
          )}
          {tab === "connections" && (
            <ConnectionDiagram
              plan={shownPlan}
              nodes={nodes}
              selected={selected}
              select={setSelected}
              change={controlsLocked ? undefined : change}
            />
          )}
          {tab === "cypher" &&
            ["inventory_valuation", "contribution_valuation"].includes(
              shownPlan.blocks[0].node,
            ) && (
              <p className="analysis-notice">
                {t(
                  "Use the valuation selector and report controls. The text editor cannot preserve this valuation basis.",
                )}
              </p>
            )}
          {tab === "cypher" &&
            !["inventory_valuation", "contribution_valuation"].includes(
              shownPlan.blocks[0].node,
            ) && (
              <div className="analysis-expert">
                <div className="analysis-editor-heading">
                  <span>{t("Generated from the interpreted question")}</span>
                  <button
                    className="br-btn br-btn-primary"
                    disabled={busy || !path.trim()}
                    onClick={() => void executePath()}
                  >
                    {t("Execute query")}
                  </button>
                </div>
                <textarea
                  aria-label={t("Cypher query")}
                  className="analysis-code"
                  value={path}
                  spellCheck={false}
                  onChange={(event) => {
                    setPath(event.target.value);
                    editDraft();
                  }}
                />
                <details>
                  <summary>{t("Query parameters")}</summary>
                  <textarea
                    aria-label={t("Query parameters")}
                    className="analysis-code analysis-parameters"
                    value={parameters}
                    spellCheck={false}
                    onChange={(event) => {
                      setParameters(event.target.value);
                      editDraft();
                    }}
                  />
                </details>
                <p>
                  {t(
                    "Expert mode: edits remain in the query and may not translate fully back into the sentence. Only declared read queries are supported.",
                  )}
                </p>
                {!path && canonical && (
                  <button
                    className="br-btn"
                    disabled={busy}
                    onClick={async () => {
                      const id = generation.current;
                      setBusy(true);
                      setRefusal(null);
                      try {
                        const editor = await graphApi.format(
                          tenant,
                          canonical,
                          controller.current?.signal,
                        );
                        if (id === generation.current) {
                          setPath(editor.path ?? "");
                          setParameters(JSON.stringify(editor.parameters, null, 2));
                          if (editor.reason) setNotice(editor.reason);
                        }
                      } catch (error) {
                        fail(error, id);
                      } finally {
                        if (id === generation.current) setBusy(false);
                      }
                    }}
                  >
                    {t("Generate query")}
                  </button>
                )}
              </div>
            )}
          {tab !== "result" && refusal && (
            <div className="analysis-notice" role="alert">
              <strong>{refusal.headline}</strong>
              <p>{refusal.detail}</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function fieldsOf(plan: Plan, nodes: Record<string, GraphNode>): Field[] {
  return plan.blocks.flatMap((block) =>
    (nodes[block.node]?.properties ?? []).map((property) => ({
      field: `${block.alias}.${property.key}`,
      label: `${nodes[block.node].label} · ${property.label}`,
      kind: property.kind,
      temporal: property.temporal,
      input: property.input,
      ...(property.values ? { values: property.values } : {}),
    })),
  );
}

export function questionPeriod(plan: Plan, nodes: Record<string, GraphNode>): Filter | undefined {
  const dates = new Set(
    fieldsOf(plan, nodes)
      .filter((field) => field.kind === "time" && !field.input)
      .map((field) => field.field),
  );
  return plan.blocks
    .flatMap((block) => block.filters)
    .find(
      (filter) =>
        filter.conditions.length === 2 &&
        dates.has(filter.conditions[0].field) &&
        filter.conditions.every((condition) => condition.field === filter.conditions[0].field) &&
        filter.conditions.some((condition) => ["gte", "gt"].includes(condition.op)) &&
        filter.conditions.some((condition) => ["lt", "lte"].includes(condition.op)),
    );
}

export function withoutQuestionPeriod(plan: Plan, period: Filter): Plan {
  return {
    ...plan,
    blocks: plan.blocks.map((block) => ({
      ...block,
      filters: block.filters.filter((filter) => filter !== period),
    })),
  };
}

function periodCaption(period: Filter): string {
  const match = periods().find((window) =>
    period.conditions.every(
      (condition) =>
        (condition.op === "gte" &&
          [window.from.toISOString(), instant(window.from, "date")].includes(
            String(condition.value),
          )) ||
        (condition.op === "lt" &&
          [window.until.toISOString(), instant(window.until, "date")].includes(
            String(condition.value),
          )),
    ),
  );
  return match?.label ?? period.shown;
}

function SentenceChevron() {
  return (
    <svg
      className="analysis-chevron"
      aria-hidden="true"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

/** Human captions only; the full grouping grain stays untouched in the plan. */
export function groupCaptions(plan: Plan, nodes: Record<string, GraphNode>): string[] {
  const described = plan.groups.filter((group) => {
    const [alias, key] = group.field.split(".");
    const node = nodes[plan.blocks.find((block) => block.alias === alias)?.node ?? ""];
    const property = node?.properties.find((property) => property.key === key);
    if (
      property?.identity ||
      property?.input ||
      key === "id" ||
      key.endsWith("_id") ||
      key === "unit"
    )
      return false;
    if (
      ["sku", "number", "code"].includes(key) &&
      plan.groups.some((other) => other.field === `${alias}.name`)
    )
      return false;
    return true;
  });
  return (described.length ? described : plan.groups).map((group) => {
    const [alias, key] = group.field.split(".");
    const node = nodes[plan.blocks.find((block) => block.alias === alias)?.node ?? ""];
    const property = node?.properties.find((property) => property.key === key);
    const label = property?.label ?? group.label;
    return group.bucket
      ? group.label
      : key === "name" && /^(name|naam|nombre)$/i.test(label)
        ? (node?.label ?? label)
        : label;
  });
}

/** The sentence is another editor of the checked plan, not a second query language. */
function Toolbar({
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
  const fields = fieldsOf(plan, nodes);
  const measures = plan.blocks.flatMap((block) => nodes[block.node]?.measures ?? []);
  const [periodField, setPeriodField] = useState("");
  const timeFields = fields.filter((field) => field.kind === "time" && !field.input);
  const settings = useRef<HTMLDetailsElement>(null);
  const activePeriod = questionPeriod(plan, nodes);
  const effectivePeriodField =
    periodField || activePeriod?.conditions[0].field || timeFields[0]?.field;
  const groupNames = groupCaptions(plan, nodes);
  const recordControls = (
    <>
      <select
        className="br-control analysis-token analysis-root-choice"
        style={{
          width: `${Math.min(28, (nodes[plan.blocks[0].node]?.label.length ?? 10) + 4)}ch`,
        }}
        aria-label={t("Analysis records")}
        value={plan.blocks[0].node}
        onChange={(event) => change(listPlan(nodes[event.target.value]))}
      >
        {catalogGroups(catalog.nodes).map(([category, items]) => (
          <optgroup key={category} label={category || t("Business objects")}>
            {items.map((node) => (
              <option key={node.key} value={node.key}>
                {node.label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      {plan.blocks.slice(1).map((block, index) => (
        <span key={block.alias} className="analysis-hop">
          <span className="analysis-token analysis-relation">{t("with")}</span>
          <details className="analysis-inline-menu">
            <summary className="analysis-token">
              {nodes[block.node]?.label} <SentenceChevron />
            </summary>
            <div className="analysis-menu-content">
              <p>{block.edge?.label}</p>
              <AddFilter
                fields={fieldsOf({ ...plan, blocks: [block] }, nodes)}
                add={(filter) => change(withFilter(plan, filter))}
              />
              <button
                className="br-btn"
                onClick={() => change({ ...plan, blocks: plan.blocks.slice(0, index + 1) })}
              >
                {t("Remove this step and everything after it")}
              </button>
            </div>
          </details>
        </span>
      ))}
      <Reach catalog={catalog} nodes={nodes} plan={plan} change={change} />
    </>
  );
  return (
    <div className="analysis-interpretation">
      <div className="analysis-sentence">
        <span>{t("Show me")}</span>
        {plan.measures.length ? (
          <button
            className="analysis-token"
            onClick={() => {
              if (settings.current) {
                settings.current.open = true;
                settings.current.querySelector("summary")?.focus();
              }
            }}
            aria-label={t("Measures and columns")}
          >
            {plan.measures
              .map((key) => measures.find((measure) => measure.key === key)?.label ?? key)
              .join(" + ")}
            <SentenceChevron />
          </button>
        ) : (
          recordControls
        )}
        {timeFields.length > 0 && (
          <>
            <span>{t("from the")}</span>
            <details className="analysis-inline-menu">
              <summary className="analysis-token analysis-period">
                {activePeriod ? periodCaption(activePeriod) : t("All periods")} <SentenceChevron />
              </summary>
              <div className="analysis-menu-content">
                <select
                  className="analysis-token analysis-period"
                  aria-label={t("Period field")}
                  value={effectivePeriodField}
                  onChange={(event) => setPeriodField(event.target.value)}
                >
                  {timeFields.map((field) => (
                    <option key={field.field} value={field.field}>
                      {field.label}
                    </option>
                  ))}
                </select>
                <select
                  className="analysis-token analysis-period"
                  aria-label={t("Analysis period")}
                  value=""
                  onChange={(event) => {
                    const period = periods().find((period) => period.key === event.target.value);
                    const field =
                      timeFields.find((field) => field.field === effectivePeriodField) ??
                      timeFields[0];
                    if (period)
                      change(
                        withFilter(
                          {
                            ...plan,
                            blocks: plan.blocks.map((block) => ({
                              ...block,
                              filters: block.filters.filter(
                                (filter) =>
                                  !filter.conditions.every(
                                    (condition) => condition.field === field.field,
                                  ),
                              ),
                            })),
                          },
                          periodFilter(field.field, field.label, period, field.temporal),
                        ),
                      );
                  }}
                >
                  <option value="">{t("Choose period")}</option>
                  {periods().map((period) => (
                    <option key={period.key} value={period.key}>
                      {period.label}
                    </option>
                  ))}
                </select>
                <AddFilter fields={timeFields} add={(filter) => change(withFilter(plan, filter))} />
                {activePeriod && (
                  <button
                    className="br-btn"
                    onClick={() => change(withoutQuestionPeriod(plan, activePeriod))}
                  >
                    {t("Remove period")}
                  </button>
                )}
              </div>
            </details>
          </>
        )}
        <span>{plan.measures.length ? t("grouped by") : t("showing")}</span>
        <details className="analysis-inline-menu">
          <summary className="analysis-token">
            {groupNames.join(" · ") || t("Choose fields")} <SentenceChevron />
          </summary>
          <div className="analysis-menu-content">
            {plan.groups.map((group) => (
              <button
                className="br-btn"
                key={columnOf(group)}
                onClick={() =>
                  change({
                    ...plan,
                    groups: plan.groups.filter(
                      (candidate) => columnOf(candidate) !== columnOf(group),
                    ),
                  })
                }
              >
                {group.label} ×
              </button>
            ))}
            <AddGroup
              fields={fields.filter(
                (field) => !plan.groups.some((group) => group.field === field.field),
              )}
              add={(group) => change({ ...plan, groups: [...plan.groups, group] })}
            />
          </div>
        </details>
        {fields.some((field) => field.input === "date") && (
          <span className="analysis-snapshot-inline">
            {fields
              .filter((field) => field.input === "date")
              .map((field) => {
                const value = plan.blocks
                  .flatMap((block) => block.filters)
                  .flatMap((filter) => filter.conditions)
                  .find(
                    (condition) => condition.field === field.field && condition.op === "eq",
                  )?.value;
                return (
                  <label
                    key={field.field}
                    className="analysis-snapshot-label"
                    title={t("End of the selected day in UTC")}
                  >
                    <span>{t("as of")}</span>
                    <input
                      className="br-control"
                      aria-label={field.label}
                      type="date"
                      value={typeof value === "string" ? value : ""}
                      max={new Date().toISOString().slice(0, 10)}
                      onChange={(event) => {
                        const date = event.target.value;
                        const cleared = {
                          ...plan,
                          blocks: plan.blocks.map((block) => ({
                            ...block,
                            filters: block.filters.filter(
                              (filter) =>
                                !filter.conditions.some(
                                  (condition) => condition.field === field.field,
                                ),
                            ),
                          })),
                        };
                        change(
                          date
                            ? withFilter(cleared, {
                                shown: `${field.label} = ${formatCalendarDate(date)}`,
                                conditions: [{ field: field.field, op: "eq", value: date }],
                              })
                            : cleared,
                        );
                      }}
                    />
                  </label>
                );
              })}
          </span>
        )}
      </div>
      <div className="analysis-chips register-filter-row">
        <span className="analysis-section-label">{t("Filters")}</span>
        {!plan.blocks.some((block) =>
          block.filters.some(
            (filter) =>
              filter !== activePeriod &&
              !filter.conditions.every((condition) =>
                fields.some((field) => field.input && field.field === condition.field),
              ),
          ),
        ) && <span className="analysis-filter-empty">{t("No restrictions")}</span>}
        <AddFilter
          fields={fields.filter((field) => !field.input)}
          add={(filter) => change(withFilter(plan, filter))}
        />
        {plan.blocks.flatMap((block, index) =>
          block.filters.flatMap((filter, position) =>
            filter === activePeriod ||
            filter.conditions.every((condition) =>
              fields.some((field) => field.input && field.field === condition.field),
            ) ? (
              []
            ) : (
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
            ),
          ),
        )}
      </div>
      <details ref={settings} className="analysis-settings">
        <summary>{t("Measures and columns")}</summary>
        {plan.measures.length > 0 && (
          <div className="analysis-record-controls">
            <span className="analysis-section-label">{t("Records and connections")}</span>
            {recordControls}
          </div>
        )}
        <div className="analysis-measures register-filter-row">
          <span>{t("Summarise")}</span>
          {plan.measures.map((key) => (
            <button
              key={key}
              className="analysis-token"
              title={t("Remove this number")}
              onClick={() => change(withoutMeasure(plan, key, nodes))}
            >
              {measures.find((measure) => measure.key === key)?.label ?? key} ×
            </button>
          ))}
          <select
            className="br-control"
            aria-label={t("Number to summarise")}
            value=""
            onChange={(event) => {
              if (event.target.value)
                change(withMeasure(plan, event.target.value, measures, fields));
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
          {plan.groups.map((group) => (
            <button
              key={columnOf(group)}
              className="br-btn"
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
              {group.label} ×
            </button>
          ))}
        </div>
        <div className="analysis-sort-controls register-filter-row">
          <span className="analysis-section-label">{t("Sort")}</span>
          {plan.order && (
            <button className="br-btn" onClick={() => change({ ...plan, order: undefined })}>
              {t("Sort")}:{" "}
              {measures.find((m) => m.key === plan.order?.by)?.label ??
                plan.groups.find((g) => columnOf(g) === plan.order?.by)?.label ??
                plan.order.by}{" "}
              {plan.order.descending ? "↓" : "↑"} ×
            </button>
          )}

          {!plan.order && <span>{t("No sorting selected")}</span>}
        </div>
      </details>
    </div>
  );
}

export function connectionLayout(plan: Plan) {
  const levels = new Map<string, number>();
  const slots = new Map<number, number>();
  const nodes = plan.blocks.map((block, index) => {
    const origin = block.edge?.from ?? plan.blocks[index - 1]?.alias;
    const level = index === 0 ? 0 : (levels.get(origin) ?? 0) + 1;
    levels.set(block.alias, level);
    const slot = slots.get(level) ?? 0;
    slots.set(level, slot + 1);
    return { alias: block.alias, x: 130 + level * 300, y: 145 + slot * 170, block };
  });
  const maximumLevel = Math.max(1, ...Array.from(levels.values()));
  const width = Math.max(850, 280 + maximumLevel * 300);
  for (const point of nodes)
    point.x = 130 + ((levels.get(point.alias) ?? 0) / maximumLevel) * (width - 260);
  const edges = plan.blocks.slice(1).map((block, index) => ({
    from: block.edge?.from ?? plan.blocks[index].alias,
    to: block.alias,
    label: block.edge?.label ?? "",
    inward: block.edge?.direction === "in",
  }));
  return {
    nodes,
    edges,
    width,
    height: Math.max(300, ...nodes.map((node) => node.y + 100)),
  };
}

function ConnectionDiagram({
  plan,
  nodes,
  selected,
  select,
  change,
}: {
  plan: Plan;
  nodes: Record<string, GraphNode>;
  selected: string | null;
  select: (alias: string | null) => void;
  change?: (plan: Plan) => void;
}) {
  const layout = connectionLayout(plan);
  const arrowMarker = "url(#analysis-arrow)";
  const block = plan.blocks.find((block) => block.alias === selected);
  return (
    <div className="analysis-connections">
      <div className="analysis-graph-scroll">
        <div
          className="analysis-graph"
          style={{ width: layout.width, minWidth: "100%", height: layout.height }}
        >
          <svg
            width="100%"
            height={layout.height}
            viewBox={`0 0 ${layout.width} ${layout.height}`}
            preserveAspectRatio="none"
            aria-label={t("Connections in this question")}
          >
            <defs>
              <marker
                id="analysis-arrow"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
              </marker>
            </defs>
            {layout.edges.map((edge) => {
              const from = layout.nodes.find((node) => node.alias === edge.from)!;
              const to = layout.nodes.find((node) => node.alias === edge.to)!;
              return (
                <g key={edge.to}>
                  <line
                    x1={from.x + 60}
                    y1={from.y}
                    x2={to.x - 60}
                    y2={to.y}
                    markerEnd={edge.inward ? undefined : arrowMarker}
                    markerStart={edge.inward ? arrowMarker : undefined}
                  />
                  <text x={(from.x + to.x) / 2} y={(from.y + to.y) / 2 - 16} textAnchor="middle">
                    {edge.label}
                  </text>
                </g>
              );
            })}
          </svg>
          {layout.nodes.map((point, index) => (
            <button
              key={point.alias}
              className={`analysis-node analysis-node-${index % 3}`}
              aria-pressed={selected === point.alias}
              style={{ left: `${(point.x / layout.width) * 100}%`, top: point.y }}
              onClick={() => select(selected === point.alias ? null : point.alias)}
            >
              <strong
                style={{
                  fontSize: (nodes[point.block.node]?.label.length ?? 0) > 12 ? 11 : undefined,
                }}
              >
                {nodes[point.block.node]?.label ?? point.block.node}
              </strong>
              <small>
                {point.block.edge
                  ? point.block.edge.fansOut
                    ? t("Many related records")
                    : t("One related record")
                  : t("Starting records")}
              </small>
            </button>
          ))}
        </div>
      </div>
      <p>{t("Select a node to edit its filters and fields.")}</p>
      {block && (
        <div className="analysis-node-editor">
          <h4>{nodes[block.node]?.label}</h4>
          <p>{t(nodes[block.node]?.grain ?? "")}</p>
          {change ? (
            <>
              <AddFilter
                fields={fieldsOf({ ...plan, blocks: [block] }, nodes)}
                add={(filter) => change(withFilter(plan, filter))}
              />
              <AddGroup
                fields={fieldsOf({ ...plan, blocks: [block] }, nodes).filter(
                  (field) => !plan.groups.some((group) => group.field === field.field),
                )}
                add={(group) => change({ ...plan, groups: [...plan.groups, group] })}
              />
              {block.filters.map((filter, i) => (
                <button
                  className="br-btn"
                  key={i}
                  onClick={() =>
                    change({
                      ...plan,
                      blocks: plan.blocks.map((candidate) =>
                        candidate.alias === block.alias
                          ? { ...candidate, filters: candidate.filters.filter((_, at) => at !== i) }
                          : candidate,
                      ),
                    })
                  }
                >
                  {filter.shown} ×
                </button>
              ))}
            </>
          ) : (
            <p>{t("Edit this query in expert mode.")}</p>
          )}
        </div>
      )}
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
      block.alias === alias
        ? {
            ...block,
            filters: [
              ...block.filters.filter(
                (existing) =>
                  !filter.conditions[0].field.endsWith(".snapshot_date") ||
                  !existing.conditions.some(
                    (condition) => condition.field === filter.conditions[0].field,
                  ),
              ),
              filter,
            ],
          }
        : block,
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
          key={`${edge.from}-${edge.key}-${edge.direction}`}
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
    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return formatCalendarDate(text);
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
      <div className="erp-empty text-center text-sm text-fg-muted">
        {busy
          ? t("Reading data…")
          : plan.blocks[0].node === "contribution_valuation" && !plan.contributionCostContext
            ? t("Select a confirmed contribution valuation.")
            : plan.blocks[0].node === "inventory_valuation" && !plan.inventoryCostContext
              ? t("Select a confirmed inventory valuation.")
              : t("Choose at least one number or one axis.")}
      </div>
    );

  const columns = answer.rows.length ? Object.keys(answer.rows[0]) : [];
  const numeric = (column: string) => (answer.question.measures ?? []).includes(column);
  const sortMark = (column: string) =>
    plan.order?.by === column ? (plan.order.descending ? "↓" : "↑") : "";

  return (
    <div className={`erp-register ${busy ? "opacity-60" : ""}`} aria-busy={busy}>
      {answer.rows.length === 0 ? (
        <div className="erp-empty text-center text-sm">
          {answer.matched_nothing?.length ? (
            <>
              <div className="font-medium text-warning-600">{t("Nothing has that value.")}</div>
              <div className="mt-2 text-fg-muted">{answer.matched_nothing.join(" · ")}</div>
              <div className="mt-2 text-fg-muted">
                {t(
                  "The answer is empty because the question named something no record carries, not because the business has none.",
                )}
              </div>
            </>
          ) : (
            <span className="text-fg-muted">
              {t("No records match. That is not proof that none exist upstream.")}
            </span>
          )}
        </div>
      ) : (
        <div className="erp-table-scroll">
          <table className="erp-table w-full">
            <thead className="sticky top-0 bg-surface">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    style={{ textAlign: numeric(column) ? "right" : "left" }}
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
                        style={{ textAlign: numeric(column) ? "right" : "left" }}
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
      <div className="erp-register-footer flex flex-wrap items-center gap-3">
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
        className="w-24 br-control"
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
        className="br-control"
        aria-label={t("Add a filter")}
        value=""
        onChange={(event) => setField(event.target.value)}
      >
        <option value="">{t("+ Filter")}</option>
        {fields.map((candidate) => (
          <option key={candidate.field} value={candidate.field}>
            {candidate.label}
          </option>
        ))}
      </select>
    );

  if (chosen.input === "date")
    return (
      <div className="flex flex-wrap items-center gap-2">
        <label className="text-sm">
          {chosen.label}
          <input
            className="br-control ml-2"
            type="date"
            value={value}
            max={new Date().toISOString().slice(0, 10)}
            onChange={(event) => setValue(event.target.value)}
          />
        </label>
        <button
          className="br-btn"
          disabled={!value}
          onClick={() =>
            submit({
              shown: `${chosen.label} = ${formatCalendarDate(value)}`,
              conditions: [{ field: chosen.field, op: "eq", value }],
            })
          }
        >
          {t("Apply")}
        </button>
        <button className="br-btn" onClick={clear}>
          {t("Cancel")}
        </button>
      </div>
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
              onClick={() =>
                submit(periodFilter(chosen.field, chosen.label, period, chosen.temporal))
              }
            >
              {period.label}
            </button>
          ))}
          <label className="flex items-center gap-1 text-xs text-fg-muted">
            {t("from")}
            <input
              type="date"
              className="br-control"
              value={from}
              onChange={(event) => setFrom(event.target.value)}
            />
          </label>
          <label className="flex items-center gap-1 text-xs text-fg-muted">
            {t("to")}
            <input
              type="date"
              className="br-control"
              value={until}
              onChange={(event) => setUntil(event.target.value)}
            />
          </label>
          {from && until && (
            <button
              className="br-btn"
              onClick={() =>
                submit(
                  periodFilter(
                    chosen.field,
                    chosen.label,
                    {
                      label: `${formatCalendarDate(from)} – ${formatCalendarDate(until)}`,
                      from: new Date(`${from}T00:00:00`),
                      // The end of a named period is the day after it, so that a
                      // record stamped at noon on the last day is still inside.
                      until: nextCalendarDay(until),
                    },
                    chosen.temporal,
                  ),
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
            className="br-control"
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
            (chosen.kind === "boolean" || chosen.values?.length ? (
              // The catalog knows which words this company's records use, so
              // nobody has to guess one. Typing "sale" where the records say
              // "customer_delivery" returns nothing and looks like an answer.
              <select
                className="br-control"
                aria-label={t("Value")}
                value={value}
                onChange={(event) => setValue(event.target.value)}
              >
                <option value="">…</option>
                {chosen.kind === "boolean" ? (
                  <>
                    <option value="true">{t("yes")}</option>
                    <option value="false">{t("no")}</option>
                  </>
                ) : (
                  chosen.values?.map((known) => (
                    <option key={known} value={known}>
                      {known || t("(empty)")}
                    </option>
                  ))
                )}
              </select>
            ) : (
              <input
                className="br-control"
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
      className="br-control"
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
 *
 * It renders where the analysis is, rather than portalling its buttons into the
 * page header. There they collapsed into a generic "More actions" menu, so the
 * one step that turns a question into a report of your own was the one step
 * nothing on the page mentioned — and the naming field then appeared somewhere
 * else entirely from the control that opened it.
 */
function Save({
  tenant,
  plan,
  nodes,
  report,
  onSaved,
  onLibrary,
  definition,
  active = true,
  onNew,
  disabled = false,
  changed = false,
  draftName = "",
}: {
  tenant: string;
  active?: boolean;
  onNew?: () => void;
  onLibrary?: () => void;
  disabled?: boolean;
  /** True when the question on screen is no longer the one that was saved. */
  changed?: boolean;
  /** The name this analysis arrived with — a template's, or a proposal's. */
  draftName?: string;
  plan: Plan;
  nodes: Record<string, GraphNode>;
  definition?: GraphQuestion;
  report: GraphReport | null;
  onSaved?: (report: GraphReport) => void;
}) {
  const [naming, setNaming] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState("");
  const [saved, setSaved] = useState(false);

  const send = async (change: Parameters<typeof graphApi.change>[1]) => {
    setBusy(true);
    setFailed("");
    try {
      const stored = await graphApi.change(tenant, change);
      setNaming(false);
      setName("");
      setSaved(true);
      onSaved?.(stored);
    } catch (failure) {
      // The entered name stays: a refused save is not a reason to make somebody
      // type it again.
      setFailed(failure instanceof Error ? failure.message : analyticsError(failure));
    } finally {
      setBusy(false);
    }
  };
  const create = () =>
    void send({
      operation: "create",
      request_id: crypto.randomUUID(),
      name: name.trim(),
      question: definition ?? question(plan),
    });
  const open = () => {
    setName(draftName || suggestedName(plan, nodes, groupCaptions(plan, nodes)));
    setFailed("");
    setNaming(true);
  };

  const state = report
    ? changed
      ? t("Unsaved changes")
      : saved
        ? t("Saved")
        : t("Saved report")
    : t("Draft · not saved yet");
  return (
    <div className="analysis-identity">
      <div className="analysis-identity-name">
        <h2>{report?.name || draftName || t("New analysis")}</h2>
        <p className={report && !changed ? "analysis-identity-saved" : undefined}>{state}</p>
      </div>
      {naming ? (
        <div className="analysis-identity-actions">
          <input
            className="br-control"
            aria-label={t("Report name")}
            autoFocus
            maxLength={120}
            value={name}
            // Selected, so the suggestion is a starting point and not something
            // to delete before typing.
            onFocus={(event) => event.currentTarget.select()}
            onChange={(event) => setName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && name.trim()) create();
              if (event.key === "Escape") setNaming(false);
            }}
          />
          <button
            className="br-btn br-btn-primary"
            disabled={busy || !name.trim()}
            onClick={create}
          >
            {busy ? t("Saving…") : t("Save")}
          </button>
          <button className="br-btn" disabled={busy} onClick={() => setNaming(false)}>
            {t("Cancel")}
          </button>
        </div>
      ) : (
        active && (
          <div className="analysis-identity-actions">
            {report && (
              <button
                // Emphasis follows what can actually be done: a disabled button
                // that still looks like the primary one is an instruction the
                // page then refuses.
                className={`br-btn ${changed ? "br-btn-primary" : ""}`}
                disabled={disabled || busy || !changed}
                onClick={() =>
                  void send({
                    operation: "update",
                    request_id: crypto.randomUUID(),
                    report_id: report.id,
                    expected_revision: report.revision,
                    question: definition ?? question(plan),
                  })
                }
              >
                {busy ? t("Saving…") : t("Save changes")}
              </button>
            )}
            <button
              className={`br-btn ${report ? "" : "br-btn-primary"}`}
              disabled={disabled || busy}
              onClick={open}
            >
              {t(report ? "Save as a new report" : "Save analysis")}
            </button>
            {/* The confirmation and the way onward belong together: once the
                question moves on, this row is about saving again. */}
            {saved && !changed && onLibrary && (
              <button className="br-btn" onClick={onLibrary}>
                {t("My reports")}
              </button>
            )}
            {onNew && (
              <button className="br-btn" onClick={onNew}>
                {t("New analysis")}
              </button>
            )}
          </div>
        )
      )}
      {failed && (
        <p role="alert" className="analysis-identity-failure">
          {failed}
        </p>
      )}
    </div>
  );
}

/** A catalog selection becomes an ordinary unsaved plan. */
export function explorePlan(
  node: GraphNode,
  nodes: Record<string, GraphNode>,
  field?: string,
  edgeKey?: string,
  direction: "out" | "in" = "out",
): Plan {
  const plan = listPlan(node);
  if (field) {
    const property = node.properties.find((property) => property.key === field);
    if (property && !plan.groups.some((group) => group.field === `o.${field}`))
      plan.groups.push({ field: `o.${field}`, label: property.label });
  }
  if (edgeKey) {
    const edge = reachable(plan, nodes).find(
      (edge) => edge.key === edgeKey && edge.direction === direction,
    );
    if (edge) {
      plan.blocks.push({ alias: "n1", node: edge.node, filters: [], edge: { ...edge } });
      plan.groups = listColumns(nodes[edge.node], "n1");
    }
  }
  return plan;
}
