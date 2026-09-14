import { inspectorValue } from "./inspectorFormat";
import { useEffect, useState } from "react";
import { GraphStartingPoints, useGraphStartingPoint } from "./graphStartingPoints";
import { api, type InspectorRow } from "../api";
import { t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { ObjectGraph, type GraphTarget } from "./ObjectGraph";
import type { Selection } from "./routing";
const stages = [
  ["Original source", "What was received? Original values remain unchanged."],
  [
    "Documents",
    "What does the evidence state? Documents and lines retain their source references.",
  ],
  [
    "Operational records & facts",
    "What is recorded? Business commitments, reservations, movements and facts describe the situation.",
  ],
  [
    "Derived insights",
    "What follows from the records? Rules and views derive observations without becoming a new source of truth.",
  ],
  ["Actions", "What can happen next? Existing tools prepare changes for explicit review."],
];
const supportedKinds = [
  "fact",
  "commitment",
  "reservation",
  "movement",
  "document",
  "document_line",
  "source_record",
  "party",
  "item",
  "location",
  "ledger_entry",
  "payment",
  "business_event",
];
const authority = (kind: string) =>
  kind === "source_record"
    ? "Original source"
    : ["document", "document_line"].includes(kind)
      ? "Documents"
      : "Operational records & facts";
export function ContextExplorer({
  tenant,
  navigate,
}: {
  tenant: string;
  navigate: (value: Partial<Selection>) => void;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [stage, setStage] = useState(2);
  const seed = useGraphStartingPoint(tenant);
  const { root, setRoot } = seed;
  const [viewed, setViewed] = useState<GraphTarget | null>(null);
  useEffect(() => {
    setViewed(root);
  }, [root]);
  const records = useRead(() => api.explorer(tenant, query), [tenant, query]);
  const detail = useRead(
    () => (viewed ? api.inspector(tenant, viewed.kind, viewed.id) : Promise.resolve(null)),
    [tenant, viewed?.kind, viewed?.id],
  );
  const choose = (target: GraphTarget) => {
    seed.manual();
    setRoot(target);
    setViewed(target);
  };
  const rows =
    records.data?.sections.flatMap((section) =>
      section.collections.flatMap((collection) =>
        supportedKinds.includes(collection.name)
          ? collection.records.map((record) => ({
              ...record,
              kind: collection.name,
              label: collection.label,
            }))
          : [],
      ),
    ) || [];
  const visible = rows.filter((row) => filter === "all" || row.kind === filter);
  const renderRow = (row: InspectorRow, index: number) => (
    <div
      key={index}
      className="flex flex-wrap justify-between gap-2 border-b border-border-default py-2 text-sm"
    >
      <span className="text-fg-muted">{t(row.label)}</span>
      {row.link ? (
        <button
          className="max-w-full break-all text-left text-accent underline"
          onClick={() => choose(row.link!)}
          data-localization="original"
        >
          {inspectorValue(row.value, row.display_parts)}
        </button>
      ) : (
        <span className="max-w-full break-all" data-localization="original">
          {inspectorValue(row.value, row.display_parts)}
        </span>
      )}
    </div>
  );
  return (
    <div className="space-y-5">
      <GraphStartingPoints {...seed} />
      {seed.label && (
        <p className="text-sm text-fg-muted" data-graph-start>
          {t("Starting point")}: <strong data-localization="original">{seed.label}</strong>
        </p>
      )}
      {seed.loading || seed.error ? (
        <ReadState loading={seed.loading} error={seed.error} retry={seed.retry} />
      ) : root && viewed ? (
        <div className="grid items-start gap-4 2xl:grid-cols-[minmax(0,1.4fr)_minmax(280px,1fr)]">
          <div className="min-w-0">
            <ObjectGraph
              key={`${tenant}:${root.kind}:${root.id}`}
              tenant={tenant}
              root={root}
              onNavigate={setViewed}
            />
          </div>
          <aside
            data-context-detail
            className="min-w-0 rounded-xl border border-border-default bg-surface p-5"
          >
            {!detail.data || detail.data.id !== viewed.id || detail.data.kind !== viewed.kind ? (
              <ReadState loading={detail.loading} error={detail.error} retry={detail.refresh} />
            ) : (
              <>
                <span className="text-xs font-medium text-accent">{t(authority(viewed.kind))}</span>
                <h2 className="mt-2 break-words text-xl font-semibold" data-localization="original">
                  {inspectorValue(detail.data.title, detail.data.title_parts)}
                </h2>
                <p className="mt-2 text-sm text-fg-muted" data-localization="original">
                  {inspectorValue(detail.data.meaning, detail.data.meaning_parts)}
                </p>
                {(detail.data.metrics || []).map(renderRow)}
                {detail.data.sections.map((section) => (
                  <section key={section.title} className="mt-4">
                    <h3 className="text-sm font-semibold">{t(section.title)}</h3>
                    {section.rows.map(renderRow)}
                  </section>
                ))}
                {detail.data.source_payload && (
                  <details className="mt-4">
                    <summary>{t("Original source")}</summary>
                    <pre
                      className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-all text-xs"
                      data-localization="original"
                    >
                      {detail.data.source_payload}
                    </pre>
                  </details>
                )}
                <p className="mt-4 text-xs text-fg-muted">
                  {t(
                    "Derived insights belong to rules and views; they are not received source values.",
                  )}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button className="br-btn" onClick={() => navigate({ inspectorView: "rules" })}>
                    {t("Rules")}
                  </button>
                  <button className="br-btn" onClick={() => navigate({ inspectorView: "history" })}>
                    {t("Actions")}
                  </button>
                </div>
              </>
            )}
          </aside>
        </div>
      ) : (
        <p className="rounded-xl border border-dashed border-border-default p-6 text-sm text-fg-muted">
          {t(
            seed.empty
              ? "No records are available for this starting point yet."
              : "Choose a starting point or search for a record.",
          )}
        </p>
      )}
      <section className="rounded-xl border border-border-default bg-surface p-4">
        <div className="flex flex-wrap gap-3">
          <input
            className="br-control min-w-0 flex-1"
            aria-label={t("Find a business record")}
            placeholder={t("Find a business record")}
            value={query}
            onChange={(event) => {
              seed.manual();
              setQuery(event.target.value);
            }}
          />
          <select
            className="br-control w-auto"
            aria-label={t("Record type")}
            value={filter}
            onChange={(event) => {
              seed.manual();
              setFilter(event.target.value);
            }}
          >
            <option value="all">{t("All records")}</option>
            <option value="document">{t("Documents")}</option>
            <option value="commitment">{t("Commitments")}</option>
            <option value="party">{t("Customers & suppliers")}</option>
            <option value="item">{t("Items")}</option>
            <option value="fact">{t("Facts")}</option>
          </select>
        </div>
        {!records.data ? (
          <ReadState loading={records.loading} error={records.error} retry={records.refresh} />
        ) : (
          <>
            <p className="my-3 text-xs text-fg-muted">
              {t("Records per collection")}: {records.data.limit_per_collection}
            </p>
            <div className="grid max-h-52 gap-2 overflow-auto sm:grid-cols-2 xl:grid-cols-3">
              {visible.map((row) => (
                <button
                  key={`${row.kind}:${row.id}`}
                  aria-label={row.title}
                  aria-pressed={root?.id === row.id && root?.kind === row.kind}
                  onClick={() => choose({ kind: row.kind, id: row.id })}
                  className="min-w-0 rounded-lg border border-border-default p-3 text-left aria-pressed:border-accent aria-pressed:bg-accent-soft"
                >
                  <strong className="block truncate text-sm" data-localization="original">
                    {row.title}
                  </strong>
                  <span className="block text-xs text-fg-muted">{t(row.label)}</span>
                </button>
              ))}
            </div>
            {!visible.length && <p className="py-3 text-sm text-fg-muted">{t("No results")}</p>}
          </>
        )}
      </section>
      <details className="rounded-xl border border-border-default bg-surface p-5">
        <summary className="cursor-pointer text-sm font-semibold">
          {t("How context is built")}
        </summary>
        <div className="mt-4">
          <h2 className="text-xl font-semibold">
            {t("Understand the situation, not just one record.")}
          </h2>
          <p className="mt-2 text-sm text-fg-muted">
            {t(
              "Choose a business record. Follow its connections to see what is known, where it comes from and what it means.",
            )}
          </p>
          <div className="mt-5 grid gap-2 sm:grid-cols-5" aria-label={t("How context is built")}>
            {stages.map(([label], index) => (
              <button
                key={label}
                aria-pressed={stage === index}
                onClick={() => setStage(index)}
                className="rounded-lg border border-border-default p-3 text-left text-sm aria-pressed:border-accent aria-pressed:bg-accent-soft"
              >
                <span className="mb-2 block text-xs text-accent">
                  0{index + 1}
                  {index < 4 ? " →" : ""}
                </span>
                {t(label)}
              </button>
            ))}
          </div>
          <p className="mt-3 text-sm">{t(stages[stage][1])}</p>
          <p className="mt-2 text-xs text-fg-muted">
            {t(
              "This explains the model. The graph below shows only links actually returned for your record.",
            )}
          </p>
        </div>
      </details>
    </div>
  );
}
