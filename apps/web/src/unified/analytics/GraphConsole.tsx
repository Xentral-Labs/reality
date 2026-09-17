import { useMemo, useState } from "react";
import { APIError, graphApi, type GraphAnswer, type GraphCatalog, type GraphNode } from "../../api";
import { currentLanguage, formatExactDecimal, t } from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { analyticsError } from "./errors";

/** A refusal names what cannot be answered, in this language and in detail. */
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
  read_only: "This surface only reads.",
  no_match_clause: "A question starts with MATCH.",
  no_return_clause: "A question says what it wants back, with RETURN.",
  unsupported_syntax: "That is not part of this path syntax.",
  missing_parameter: "A value is missing.",
  ambiguous_direction: "A connection points one way.",
  untyped_start: "The first record of a path names its kind.",
};

type Refusal = { headline: string; detail: string };

function refusalOf(failure: unknown): Refusal {
  const code = failure instanceof APIError ? failure.code : undefined;
  return {
    headline: t((code && REFUSALS[code]) || "This question cannot be answered correctly"),
    detail: failure instanceof Error ? failure.message : analyticsError(failure),
  };
}

function fansOut(multiplicity: string, direction: "out" | "in") {
  return (multiplicity === "1:n") === (direction === "out");
}

/** Worked questions that double as the syntax reference.
 *
 * Nobody reads a grammar. Loading a real question into the editor teaches the
 * shape and leaves something to edit, which is the same trick a query console
 * has always used.
 */
function examples(catalog: GraphCatalog) {
  const out: { title: string; text: string }[] = [];
  for (const node of catalog.nodes) {
    const amount = node.measures.find((measure) => measure.unit === "currency");
    const currency = node.properties.find((property) => property.key === "currency");
    const time = node.properties.find((property) =>
      ["ordered_at", "document_date", "occurred_at", "effective_at", "allocated_at"].includes(
        property.key,
      ),
    );
    if (!amount || !currency) continue;
    out.push({
      title: `${amount.label} ${t("by")} ${currency.label}`,
      text: `MATCH (o:${node.key})\nRETURN o.${currency.key}, sum(${amount.key})`,
    });
    if (time)
      out.push({
        title: `${amount.label} ${t("by")} ${t("month")}`,
        text:
          `MATCH (o:${node.key})\n` +
          `RETURN month(o.${time.key}), o.${currency.key}, sum(${amount.key})\n` +
          `ORDER BY month DESC\nLIMIT 12`,
      });
    const fanning = node.edges.find((edge) => edge.multiplicity === "1:n");
    if (fanning)
      out.push({
        title: `${amount.label} ${t("by")} ${fanning.to_label}`,
        text:
          `MATCH (o:${node.key})-[:${fanning.key}]->(l:${fanning.to})\n` +
          `RETURN l.sku, o.${currency.key}, sum(${amount.key})`,
      });
    break;
  }
  const recursive = catalog.nodes
    .flatMap((node) => node.edges.map((edge) => ({ node, edge })))
    .find(({ edge }) => edge.recursive);
  if (recursive)
    out.push({
      title: `${recursive.node.label} ${t("and everything inside it")}`,
      text:
        `MATCH (a:${recursive.node.key})<-[:${recursive.edge.key}*1..6]-(b:${recursive.edge.to})\n` +
        `RETURN a.name, b.name`,
    });
  return out;
}

export function GraphConsole({ tenant }: { tenant: string }) {
  const language = currentLanguage();
  const read = useRead(() => graphApi.catalog(tenant, language), [tenant, language]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return <Console key={tenant} tenant={tenant} catalog={read.data} />;
}

function Console({ tenant, catalog }: { tenant: string; catalog: GraphCatalog }) {
  const ready = useMemo(() => examples(catalog), [catalog]);
  const [text, setText] = useState(ready[0]?.text ?? "MATCH (o:order)\nRETURN o.currency");
  const [answer, setAnswer] = useState<GraphAnswer | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async (source = text) => {
    setBusy(true);
    setRefusal(null);
    try {
      setAnswer(await graphApi.askPath(tenant, source));
    } catch (failure) {
      setAnswer(null);
      setRefusal(refusalOf(failure));
    } finally {
      setBusy(false);
    }
  };

  const insert = (token: string) => setText((current) => `${current.trimEnd()} ${token}`);

  return (
    <section className="grid gap-5 lg:grid-cols-[minmax(0,320px)_minmax(0,1fr)]">
      <Catalogue catalog={catalog} insert={insert} />
      <div className="space-y-4">
        <div className="space-y-2">
          <label className="block text-sm font-medium" htmlFor="graph-query">
            {t("Question")}
          </label>
          <textarea
            id="graph-query"
            className="w-full rounded-xl border border-border-default bg-surface p-3 font-mono text-sm"
            rows={6}
            spellCheck={false}
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => {
              if ((event.metaKey || event.ctrlKey) && event.key === "Enter") run();
            }}
          />
          <div className="flex flex-wrap items-center gap-2">
            <button className="br-btn br-btn-primary" disabled={busy} onClick={() => run()}>
              {busy ? t("Asking…") : t("Ask")}
            </button>
            <span className="text-xs text-fg-muted">{t("or press Cmd+Enter")}</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {ready.map((example) => (
            <button
              key={example.title}
              className="br-btn"
              onClick={() => {
                setText(example.text);
                run(example.text);
              }}
            >
              {example.title}
            </button>
          ))}
        </div>

        <Result answer={answer} refusal={refusal} busy={busy} />
      </div>
    </section>
  );
}

/** The model, browsable. Clicking a name writes it into the question. */
function Catalogue({
  catalog,
  insert,
}: {
  catalog: GraphCatalog;
  insert: (token: string) => void;
}) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState<string | null>(catalog.nodes[0]?.key ?? null);
  const needle = search.trim().toLowerCase();
  const matches = (node: GraphNode) =>
    !needle ||
    node.key.toLowerCase().includes(needle) ||
    node.label.toLowerCase().includes(needle) ||
    node.measures.some((measure) => measure.label.toLowerCase().includes(needle)) ||
    node.properties.some((property) => property.label.toLowerCase().includes(needle));

  return (
    <aside className="space-y-3">
      <input
        className="w-full rounded-xl border border-border-default bg-surface px-3 py-2 text-sm"
        placeholder={t("Search the model")}
        aria-label={t("Search the model")}
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />
      <div className="divide-y divide-border-default rounded-xl border border-border-default">
        {catalog.nodes.filter(matches).map((node) => (
          <div key={node.key}>
            <button
              className="flex w-full items-baseline justify-between gap-2 px-3 py-2 text-left text-sm"
              aria-expanded={open === node.key}
              onClick={() => setOpen(open === node.key ? null : node.key)}
            >
              <span className="font-medium">{node.label}</span>
              <span className="font-mono text-xs text-fg-muted">{node.key}</span>
            </button>
            {open === node.key && (
              <div className="space-y-3 px-3 pb-3 text-xs">
                <div className="text-fg-muted">{node.grain}</div>
                {node.measures.length > 0 && (
                  <Group title={t("Numbers")}>
                    {node.measures.map((measure) => (
                      <button
                        key={measure.key}
                        className="br-btn"
                        title={
                          measure.never_across.length
                            ? `${t("never across")} ${measure.never_across.join(", ")}`
                            : undefined
                        }
                        onClick={() => insert(`sum(${measure.key})`)}
                      >
                        {measure.label}
                      </button>
                    ))}
                  </Group>
                )}
                {node.edges.length + node.edges_in.length > 0 && (
                  <Group title={t("Connections")}>
                    {node.edges.map((edge) => (
                      <button
                        key={`out-${edge.key}`}
                        className="br-btn"
                        onClick={() => insert(`-[:${edge.key}]->(x:${edge.to})`)}
                      >
                        {edge.label} {edge.to_label}
                        <span
                          className={`ml-1 ${
                            fansOut(edge.multiplicity, "out") ? "text-warning-600" : "text-fg-muted"
                          }`}
                        >
                          {fansOut(edge.multiplicity, "out") ? t("many") : t("one")}
                        </span>
                      </button>
                    ))}
                    {node.edges_in.map((edge) => (
                      <button
                        key={`in-${edge.key}`}
                        className="br-btn"
                        onClick={() => insert(`<-[:${edge.key}]-(x:${edge.from})`)}
                      >
                        {edge.label} {edge.from_label}
                        <span
                          className={`ml-1 ${
                            fansOut(edge.multiplicity, "in") ? "text-warning-600" : "text-fg-muted"
                          }`}
                        >
                          {fansOut(edge.multiplicity, "in") ? t("many") : t("one")}
                        </span>
                      </button>
                    ))}
                  </Group>
                )}
                {node.properties.length > 0 && (
                  <Group title={t("Fields")}>
                    {node.properties.map((property) => (
                      <button
                        key={property.key}
                        className="br-btn"
                        onClick={() => insert(`o.${property.key}`)}
                      >
                        {property.label}
                      </button>
                    ))}
                  </Group>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="text-xs text-fg-muted">
        {t("model")} {catalog.model_version}
      </div>
    </aside>
  );
}

function Group({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <div className="font-medium">{title}</div>
      <div className="flex flex-wrap gap-1">{children}</div>
    </div>
  );
}

const NUMERIC = /^-?\d+([.,]\d+)?$/;
/** Numbers line up under each other; anything else reads as text. */
const NUMERIC_CELL = "text-right tabular-nums";

function Result({
  answer,
  refusal,
  busy,
}: {
  answer: GraphAnswer | null;
  refusal: Refusal | null;
  busy: boolean;
}) {
  const [showSql, setShowSql] = useState(false);
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
        {t("Ask a question, or load one of the examples above.")}
      </div>
    );
  const columns = answer.rows.length ? Object.keys(answer.rows[0]) : [];
  const numeric = (column: string) =>
    (answer.question.measures ?? []).includes(column) ||
    answer.rows.every((row) => row[column] === null || NUMERIC.test(String(row[column])));
  return (
    <div className={`space-y-3 ${busy ? "opacity-60" : ""}`} aria-busy={busy}>
      {answer.rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border-default p-10 text-center text-sm text-fg-muted">
          {t("No records match. That is not proof that none exist upstream.")}
        </div>
      ) : (
        <div className="max-h-[28rem] overflow-auto rounded-xl border border-border-default">
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
        <span>
          {answer.statements} {t("statement")}
        </span>
        <button className="underline" onClick={() => setShowSql(!showSql)}>
          {t("Show the statement")}
        </button>
      </div>
      {showSql && (
        <pre className="overflow-x-auto rounded-xl border border-border-default bg-surface p-3 font-mono text-xs">
          {answer.sql}
        </pre>
      )}
    </div>
  );
}
