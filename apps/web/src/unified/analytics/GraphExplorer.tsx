import { useMemo, useState } from "react";
import {
  APIError,
  graphApi,
  type GraphAnswer,
  type GraphCatalog,
  type GraphQuestion,
} from "../../api";
import { formatExactDecimal, t } from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { analyticsError } from "./errors";

/** A refusal names what cannot be answered, in this language and in detail.
 *
 * The code carries the kind of problem, which translates. The server's own
 * sentence carries the specifics — which edge fanned out, which measure fits the
 * grain — and those are identifiers that read the same in every language. Showing
 * both keeps the meaning readable without throwing away what makes it actionable.
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

/** A hop the reader can see the consequence of: 1:n is where a total multiplies. */
function fansOut(multiplicity: string, direction: "out" | "in") {
  return (multiplicity === "1:n") === (direction === "out");
}

type Step = { edge: string; direction: "out" | "in"; alias: string; node: string };

export function GraphExplorer({ tenant }: { tenant: string }) {
  const read = useRead(() => graphApi.catalog(tenant), [tenant]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return <Workbench key={tenant} tenant={tenant} catalog={read.data} />;
}

function Workbench({ tenant, catalog }: { tenant: string; catalog: GraphCatalog }) {
  const nodes = useMemo(
    () => Object.fromEntries(catalog.nodes.map((node) => [node.key, node])),
    [catalog],
  );
  const [start, setStart] = useState(catalog.nodes[0]?.key ?? "");
  const [steps, setSteps] = useState<Step[]>([]);
  const [measures, setMeasures] = useState<string[]>([]);
  const [groups, setGroups] = useState<string[]>([]);
  const [answer, setAnswer] = useState<GraphAnswer | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [busy, setBusy] = useState(false);

  /** Every node the path has reached, as alias → node. The root is always `o`. */
  const reached = useMemo(() => {
    const out: { alias: string; node: string }[] = [{ alias: "o", node: start }];
    for (const step of steps) out.push({ alias: step.alias, node: step.node });
    return out;
  }, [start, steps]);

  const tip = reached[reached.length - 1];
  const onward = tip
    ? [
        ...(nodes[tip.node]?.edges ?? []).map((edge) => ({ ...edge, direction: "out" as const })),
        ...(nodes[tip.node]?.edges_in ?? []).map((edge) => ({
          key: edge.key,
          to: edge.from,
          multiplicity: edge.multiplicity,
          recursive: false,
          stored: false,
          direction: "in" as const,
        })),
      ]
    : [];

  const reset = (next: Partial<{ start: string; steps: Step[] }>) => {
    if (next.start !== undefined) setStart(next.start);
    if (next.steps !== undefined) setSteps(next.steps);
    setMeasures([]);
    setGroups([]);
    setAnswer(null);
    setRefusal(null);
  };

  const availableMeasures = reached.flatMap(({ alias, node }) =>
    (nodes[node]?.measures ?? []).map((measure) => ({ ...measure, alias, node })),
  );
  const availableFields = reached.flatMap(({ alias, node }) =>
    (nodes[node]?.properties ?? []).map((property) => ({ field: `${alias}.${property}`, node })),
  );

  const question: GraphQuestion = {
    from: start,
    as: "o",
    follow: steps.map((step) => ({ edge: step.edge, direction: step.direction, as: step.alias })),
    measures,
    group_by: groups.map((field) => ({ field })),
  };

  const ask = async () => {
    setBusy(true);
    setRefusal(null);
    try {
      setAnswer(await graphApi.ask(tenant, question));
    } catch (failure) {
      setAnswer(null);
      setRefusal(refusalOf(failure));
    } finally {
      setBusy(false);
    }
  };

  const toggle = (list: string[], value: string, set: (next: string[]) => void) =>
    set(list.includes(value) ? list.filter((item) => item !== value) : [...list, value]);

  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
      <div className="space-y-5">
        <div>
          <h2 className="text-xl font-semibold">{t("Build a question")}</h2>
          <div className="mt-1 text-sm text-fg-muted">
            {t(
              "Follow the connections your records already have. Every step says how many rows it reaches.",
            )}
          </div>
        </div>

        <label className="block space-y-1">
          <span className="text-sm font-medium">{t("Start at")}</span>
          <select
            className="br-input"
            value={start}
            onChange={(event) => reset({ start: event.target.value, steps: [] })}
          >
            {catalog.nodes.map((node) => (
              <option key={node.key} value={node.key}>
                {t(node.key)} — {t(node.grain)}
              </option>
            ))}
          </select>
        </label>

        {steps.length > 0 && (
          <div className="space-y-2">
            <span className="text-sm font-medium">{t("Path")}</span>
            <ol className="flex flex-wrap items-center gap-2">
              <li className="br-btn" aria-disabled="true">
                {t(start)}
              </li>
              {steps.map((step, index) => (
                <li key={step.alias} className="flex items-center gap-2">
                  <span aria-hidden="true" className="text-fg-muted">
                    →
                  </span>
                  <button
                    className="br-btn"
                    onClick={() => reset({ steps: steps.slice(0, index) })}
                    title={t("Remove this step and everything after it")}
                  >
                    {step.edge} → {t(step.node)}
                  </button>
                </li>
              ))}
            </ol>
          </div>
        )}

        {steps.length < (catalog.limits.max_path_length ?? 8) && onward.length > 0 && (
          <div className="space-y-2">
            <span className="text-sm font-medium">{t("Follow")}</span>
            <div className="flex flex-wrap gap-2">
              {onward.map((edge) => {
                const multiplies = fansOut(edge.multiplicity, edge.direction);
                return (
                  <button
                    key={`${edge.key}-${edge.direction}`}
                    className="br-btn"
                    onClick={() =>
                      reset({
                        steps: [
                          ...steps,
                          {
                            edge: edge.key,
                            direction: edge.direction,
                            alias: `n${steps.length + 1}`,
                            node: edge.to,
                          },
                        ],
                      })
                    }
                  >
                    {edge.key} → {t(edge.to)}
                    <span
                      className={`ml-2 text-xs ${multiplies ? "text-warning-600" : "text-fg-muted"}`}
                    >
                      {multiplies ? t("many") : t("one")}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">{t("Measure")}</legend>
          {availableMeasures.length === 0 ? (
            <div className="text-sm text-fg-muted">
              {t("Nothing on this path is summed. It can still be listed and grouped.")}
            </div>
          ) : (
            availableMeasures.map((measure) => (
              <label key={measure.key} className="flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={measures.includes(measure.key)}
                  onChange={() => toggle(measures, measure.key, setMeasures)}
                />
                <span>
                  {t(measure.key)}
                  {measure.never_across.length > 0 && (
                    <span className="ml-2 text-xs text-fg-muted">
                      {t("never across")} {measure.never_across.join(", ")}
                    </span>
                  )}
                </span>
              </label>
            ))
          )}
        </fieldset>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">{t("Group by")}</legend>
          <div className="flex flex-wrap gap-2">
            {availableFields.map((field) => (
              <button
                key={field.field}
                className="br-btn"
                aria-pressed={groups.includes(field.field)}
                onClick={() => toggle(groups, field.field, setGroups)}
              >
                {field.field}
              </button>
            ))}
          </div>
        </fieldset>

        <button className="br-btn br-btn-primary" disabled={busy} onClick={ask}>
          {busy ? t("Asking…") : t("Ask")}
        </button>
      </div>

      <Answer answer={answer} refusal={refusal} busy={busy} modelVersion={catalog.model_version} />
    </section>
  );
}

function Answer({
  answer,
  refusal,
  busy,
  modelVersion,
}: {
  answer: GraphAnswer | null;
  refusal: Refusal | null;
  busy: boolean;
  modelVersion: string;
}) {
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
        {t("Choose a measure and ask. Nothing is saved until you say so.")}
      </div>
    );
  const columns = answer.rows.length ? Object.keys(answer.rows[0]) : [];
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
                      isNumeric(answer, column) ? NUMERIC_CELL : "text-left"
                    }`}
                  >
                    {column}
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
                        isNumeric(answer, column) ? NUMERIC_CELL : ""
                      }`}
                    >
                      {row[column] === null
                        ? t("Unknown")
                        : isNumeric(answer, column)
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
      <div className="text-xs text-fg-muted">
        {answer.path.length > 0 && <span>{answer.path.join(" · ")} · </span>}
        {t("model")} {answer.model_version || modelVersion} · {answer.statements} {t("statement")}
      </div>
    </div>
  );
}

/** Numbers line up under each other; axes read as text. */
const NUMERIC_CELL = "text-right tabular-nums";

/** A measure is what the question asked to sum; everything else is an axis. */
function isNumeric(answer: GraphAnswer, column: string) {
  return (answer.question.measures ?? []).includes(column);
}
