import { useMemo, useState } from "react";
import { APIError, graphApi, type GraphAnswer, type GraphCatalog, type GraphNode } from "../../api";
import { currentLanguage, formatExactDecimal, t } from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { analyticsError } from "./errors";

/** A refusal names what cannot be answered, in this language and in detail.
 *
 * The code carries the kind of problem, which translates. The server's own
 * sentence carries the specifics — which connection reached too many rows, which
 * number fits instead — so both are shown.
 */
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

/** Where a total would multiply, shown before the step is taken rather than after. */
function fansOut(multiplicity: string, direction: "out" | "in") {
  return (multiplicity === "1:n") === (direction === "out");
}

type Step = {
  edge: string;
  direction: "out" | "in";
  alias: string;
  node: string;
  label: string;
};
type Draft = {
  start: string;
  steps: Step[];
  measures: string[];
  groups: { field: string; label: string; bucket?: string }[];
};

const EMPTY: Draft = { start: "", steps: [], measures: [], groups: [] };
const TIME_FIELDS = ["ordered_at", "document_date", "occurred_at", "effective_at", "allocated_at"];

export function GraphExplorer({ tenant }: { tenant: string }) {
  const language = currentLanguage();
  const read = useRead(() => graphApi.catalog(tenant, language), [tenant, language]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return <Workbench key={tenant} tenant={tenant} catalog={read.data} />;
}

/** Questions somebody would actually ask, built from what this company declares.
 *
 * A first screen of empty fields asks the reader to know the model. A first
 * screen of real questions asks them to recognise their own work, which is the
 * only thing anybody can be expected to do.
 */
function suggestions(catalog: GraphCatalog): { title: string; draft: Draft }[] {
  const out: { title: string; draft: Draft }[] = [];
  for (const node of catalog.nodes) {
    const amount = node.measures.find((measure) => measure.unit === "currency");
    const count = node.measures.find((measure) => measure.unit === "count");
    const currency = node.properties.find((property) => property.key === "currency");
    const time = node.properties.find((property) => TIME_FIELDS.includes(property.key));
    const base = { start: node.key, steps: [] as Step[] };
    if (amount && currency) {
      out.push({
        title: `${amount.label} ${t("by")} ${currency.label}`,
        draft: {
          ...base,
          measures: [amount.key],
          groups: [{ field: `o.${currency.key}`, label: currency.label }],
        },
      });
      if (time)
        // A raw date gives one row per day, which is a list rather than an
        // answer. A month is the coarsest bucket somebody still recognises.
        out.push({
          title: `${amount.label} ${t("by")} ${t("month")}`,
          draft: {
            ...base,
            measures: [amount.key],
            groups: [
              { field: `o.${time.key}`, label: t("Month"), bucket: "month" },
              { field: `o.${currency.key}`, label: currency.label },
            ],
          },
        });
    }
    if (count && currency)
      out.push({
        title: `${count.label} ${t("by")} ${currency.label}`,
        draft: {
          ...base,
          measures: [count.key],
          groups: [{ field: `o.${currency.key}`, label: currency.label }],
        },
      });
  }
  return out.slice(0, 6);
}

function Workbench({ tenant, catalog }: { tenant: string; catalog: GraphCatalog }) {
  const nodes = useMemo(
    () =>
      Object.fromEntries(catalog.nodes.map((node) => [node.key, node])) as Record<
        string,
        GraphNode
      >,
    [catalog],
  );
  const starters = useMemo(() => suggestions(catalog), [catalog]);
  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [answer, setAnswer] = useState<GraphAnswer | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [busy, setBusy] = useState(false);
  const [detailed, setDetailed] = useState(false);

  const reached = useMemo(() => {
    if (!draft.start) return [];
    return [
      { alias: "o", node: draft.start },
      ...draft.steps.map((step) => ({ alias: step.alias, node: step.node })),
    ];
  }, [draft]);

  const ask = async (next: Draft) => {
    setDraft(next);
    if (!next.start || !next.measures.length) {
      setAnswer(null);
      setRefusal(null);
      return;
    }
    setBusy(true);
    setRefusal(null);
    try {
      setAnswer(
        await graphApi.ask(tenant, {
          from: next.start,
          as: "o",
          follow: next.steps.map((step) => ({
            edge: step.edge,
            direction: step.direction,
            as: step.alias,
          })),
          measures: next.measures,
          group_by: next.groups.map((group) => ({
            field: group.field,
            ...(group.bucket ? { bucket: group.bucket, as: group.label } : {}),
          })),
        }),
      );
    } catch (failure) {
      setAnswer(null);
      setRefusal(refusalOf(failure));
    } finally {
      setBusy(false);
    }
  };

  if (!draft.start)
    return (
      <section className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold">{t("What would you like to know?")}</h2>
          <div className="mt-1 max-w-2xl text-sm text-fg-muted">
            {t(
              "Pick a question to start, then change what it asks. For anything else, ask in the chat beside this page — it reads the same records.",
            )}
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {starters.map((starter) => (
            <button
              key={starter.title}
              className="rounded-xl border border-border-default p-4 text-left hover:border-fg-muted"
              onClick={() => ask(starter.draft)}
            >
              <div className="font-medium">{starter.title}</div>
              <div className="mt-1 text-xs text-fg-muted">{nodes[starter.draft.start]?.label}</div>
            </button>
          ))}
        </div>
      </section>
    );

  const measureLabels = draft.measures.map(
    (key) =>
      reached
        .flatMap(({ node }) => nodes[node]?.measures ?? [])
        .find((measure) => measure.key === key)?.label ?? key,
  );
  // The answer comes back keyed by field path and measure key. A person reads
  // neither, so the words from the model travel with the question.
  const columnLabels: Record<string, string> = {};
  for (const group of draft.groups) columnLabels[group.bucket ? group.label : group.field] = group.label;
  for (const measure of reached.flatMap(({ node }) => nodes[node]?.measures ?? []))
    columnLabels[measure.key] = measure.label;

  const sentence = [
    measureLabels.join(", ") || t("Nothing chosen"),
    ...draft.steps.map((step) => step.label),
    draft.groups.length ? `${t("by")} ${draft.groups.map((group) => group.label).join(", ")}` : "",
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 className="text-xl font-semibold">{sentence}</h2>
        <button className="text-sm text-fg-muted underline" onClick={() => ask(EMPTY)}>
          {t("Ask something else")}
        </button>
      </div>

      <Answer
        answer={answer}
        refusal={refusal}
        busy={busy}
        modelVersion={catalog.model_version}
        labels={columnLabels}
      />

      <Refine
        catalog={catalog}
        nodes={nodes}
        draft={draft}
        reached={reached}
        open={detailed}
        toggle={() => setDetailed(!detailed)}
        change={ask}
      />
    </section>
  );
}

function Refine({
  catalog,
  nodes,
  draft,
  reached,
  open,
  toggle,
  change,
}: {
  catalog: GraphCatalog;
  nodes: Record<string, GraphNode>;
  draft: Draft;
  reached: { alias: string; node: string }[];
  open: boolean;
  toggle: () => void;
  change: (next: Draft) => void;
}) {
  const measures = reached.flatMap(({ node }) => nodes[node]?.measures ?? []);
  const fields = reached.flatMap(({ alias, node }) =>
    (nodes[node]?.properties ?? []).map((property) => ({
      field: `${alias}.${property.key}`,
      label: property.label,
    })),
  );
  const tip = reached[reached.length - 1];
  const onward = tip
    ? [
        ...(nodes[tip.node]?.edges ?? []).map((edge) => ({
          key: edge.key,
          label: edge.label,
          to: edge.to,
          toLabel: edge.to_label,
          multiplicity: edge.multiplicity,
          direction: "out" as const,
        })),
        ...(nodes[tip.node]?.edges_in ?? []).map((edge) => ({
          key: edge.key,
          label: edge.label,
          to: edge.from,
          toLabel: edge.from_label,
          multiplicity: edge.multiplicity,
          direction: "in" as const,
        })),
      ]
    : [];

  return (
    <div className="rounded-xl border border-border-default">
      <button
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium"
        aria-expanded={open}
        onClick={toggle}
      >
        {t("Change what this asks")}
        <span aria-hidden="true">{open ? "▴" : "▾"}</span>
      </button>
      {open && (
        <div className="space-y-5 border-t border-border-default p-4">
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">{t("Numbers")}</legend>
            <div className="flex flex-wrap gap-2">
              {measures.map((measure) => (
                <button
                  key={measure.key}
                  className="br-btn"
                  aria-pressed={draft.measures.includes(measure.key)}
                  onClick={() =>
                    change({
                      ...draft,
                      measures: draft.measures.includes(measure.key)
                        ? draft.measures.filter((item) => item !== measure.key)
                        : [...draft.measures, measure.key],
                    })
                  }
                >
                  {measure.label}
                  {measure.never_across.length > 0 && (
                    <span className="ml-2 text-xs text-fg-muted">
                      {t("never across")} {measure.never_across.join(", ")}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">{t("Split by")}</legend>
            <div className="flex flex-wrap gap-2">
              {fields.map((field) => (
                <button
                  key={field.field}
                  className="br-btn"
                  aria-pressed={draft.groups.some((group) => group.field === field.field)}
                  onClick={() =>
                    change({
                      ...draft,
                      groups: draft.groups.some((group) => group.field === field.field)
                        ? draft.groups.filter((group) => group.field !== field.field)
                        : [...draft.groups, { field: field.field, label: field.label }],
                    })
                  }
                >
                  {field.label}
                </button>
              ))}
            </div>
          </fieldset>

          {onward.length > 0 && draft.steps.length < catalog.limits.max_path_length && (
            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">{t("Reach further")}</legend>
              <div className="flex flex-wrap gap-2">
                {onward.map((edge) => {
                  const multiplies = fansOut(edge.multiplicity, edge.direction);
                  return (
                    <button
                      key={`${edge.key}-${edge.direction}`}
                      className="br-btn"
                      onClick={() =>
                        change({
                          ...draft,
                          steps: [
                            ...draft.steps,
                            {
                              edge: edge.key,
                              direction: edge.direction,
                              alias: `n${draft.steps.length + 1}`,
                              node: edge.to,
                              label: `${edge.label} ${edge.toLabel}`,
                            },
                          ],
                        })
                      }
                    >
                      {edge.label} {edge.toLabel}
                      <span
                        className={`ml-2 text-xs ${
                          multiplies ? "text-warning-600" : "text-fg-muted"
                        }`}
                      >
                        {multiplies ? t("many") : t("one")}
                      </span>
                    </button>
                  );
                })}
              </div>
            </fieldset>
          )}

          {draft.steps.length > 0 && (
            <button
              className="br-btn"
              onClick={() => change({ ...draft, steps: draft.steps.slice(0, -1), groups: [] })}
            >
              {t("Undo the last step")}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/** Numbers line up under each other; axes read as text. */
const NUMERIC_CELL = "text-right tabular-nums";

function Answer({
  answer,
  refusal,
  busy,
  modelVersion,
  labels,
}: {
  answer: GraphAnswer | null;
  refusal: Refusal | null;
  busy: boolean;
  modelVersion: string;
  labels: Record<string, string>;
}) {
  const [shown, setShown] = useState(false);
  if (refusal)
    return (
      <div className="rounded-xl border border-warning-200 bg-warning-50 p-5">
        <div className="text-sm font-semibold text-warning-600">{refusal.headline}</div>
        <div className="mt-2 text-sm">{refusal.detail}</div>
      </div>
    );
  if (!answer)
    return (
      <div className="rounded-xl border border-dashed border-border-default p-10 text-center text-fg-muted">
        {t("Choose at least one number below.")}
      </div>
    );
  const columns = answer.rows.length ? Object.keys(answer.rows[0]) : [];
  const numeric = (column: string) => (answer.question.measures ?? []).includes(column);
  return (
    <div className={`space-y-3 ${busy ? "opacity-60" : ""}`} aria-busy={busy}>
      {answer.rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border-default p-10 text-center text-fg-muted">
          {t("No records match. That is not proof that none exist upstream.")}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
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
                      className={`border-b border-border-default px-3 py-2 ${
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
      <button className="text-xs text-fg-muted underline" onClick={() => setShown(!shown)}>
        {t("How this was worked out")}
      </button>
      {shown && (
        <div className="text-xs text-fg-muted">
          {answer.path.length > 0 && <span>{answer.path.join(" · ")} · </span>}
          {t("model")} {answer.model_version || modelVersion} · {answer.statements} {t("statement")}
        </div>
      )}
    </div>
  );
}
