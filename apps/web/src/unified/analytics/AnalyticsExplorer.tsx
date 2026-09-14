import "./AnalyticsExplorer.css";
import { analyticsError } from "./errors";
import { useEffect, useState, type ComponentProps } from "react";
import { Play, Download, Save, Plus, X, ChevronDown, SlidersHorizontal } from "lucide-react";
import {
  analyticsApi,
  workspaceApi,
  type AnalyticsDefinition,
  type AnalyticsDataset,
  type AnalyticsFilter,
  type AnalyticsReport,
  type ReferenceRow,
} from "../../api";
import { formatDateTime, formatNumber, t } from "../../localization";
import { useRead } from "../useCompanyContext";
import { ReadState } from "../ReadState";
import { readAnalyticsHandoff, validAnalyticsHandoff } from "../context";
import { Inspector } from "../Inspector";
import { AnalyticsTable, analyticValue } from "./AnalyticsTable";
import { AnalyticsPivot } from "./AnalyticsPivot";
import { AnalyticsChart } from "./AnalyticsChart";
import { useAnalyticsExecution } from "./useAnalyticsExecution";

const initial: AnalyticsDefinition = {
  dataset: "sales_order_lines",
  dimensions: ["customer_id"],
  measures: ["order_count", "ordered_quantity"],
  time: {
    field: "ordered_at",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    window: { kind: "last_complete_weeks", count: 12 },
  },
};
const box = "rounded-xl border border-border-default bg-surface p-5";
const input = "br-control w-full";
function AnalyticsSelect({ className = "", ...props }: ComponentProps<"select">) {
  return (
    <span className={`relative block min-w-0 ${className}`}>
      <select {...props} className="br-control cursor-pointer appearance-none pr-12" />
      <ChevronDown
        aria-hidden="true"
        className="pointer-events-none absolute right-3 top-1/2 size-5 -translate-y-1/2 text-fg-secondary"
      />
    </span>
  );
}

const families: Record<string, "customer" | "supplier" | "item" | "location"> = {
  customer_id: "customer",
  supplier_id: "supplier",
  product_id: "item",
  location_id: "location",
};
function FilterValue({
  tenant,
  filter,
  change,
}: {
  tenant: string;
  filter: AnalyticsFilter;
  change: (value: AnalyticsFilter) => void;
}) {
  const [search, setSearch] = useState("");
  const family = families[filter.field || ""];
  const read = useRead<{ items: ReferenceRow[] }>(
    () =>
      family
        ? workspaceApi.references(tenant, family, search, 1, true)
        : Promise.resolve({ items: [] }),
    [tenant, family, search],
  );
  if (["is_missing", "is_present"].includes(filter.op || "")) return null;
  if (family && ["eq", "ne"].includes(filter.op || ""))
    return (
      <div className="min-w-0 space-y-1">
        <input
          className={input}
          placeholder={t("Search records")}
          aria-label={t("Search records")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <AnalyticsSelect
          aria-label={t("Select record")}
          value={String(filter.value || "")}
          onChange={(e) => change({ ...filter, value: e.target.value })}
        >
          <option value="">{t("Select record")}</option>
          {filter.value && !read.data?.items.some((r) => r.id === filter.value) && (
            <option value={String(filter.value)}>{String(filter.value)}</option>
          )}
          {read.data?.items.map((row) => (
            <option key={row.id} value={row.id}>
              {row.name}
            </option>
          ))}
        </AnalyticsSelect>
        {read.error && <p role="alert">{read.error}</p>}
      </div>
    );
  return (
    <input
      className={input}
      aria-label={t("Filter value")}
      value={filter.values?.join(", ") ?? String(filter.value ?? "")}
      onChange={(e) =>
        change(
          ["in", "not_in"].includes(filter.op || "")
            ? {
                field: filter.field,
                op: filter.op,
                values: e.target.value.split(",").map((v) => v.trim()),
              }
            : { ...filter, value: e.target.value },
        )
      }
    />
  );
}
function Filters({
  datasets,
  tenant,
  dataset,
  value,
  change,
  depth = 1,
}: {
  tenant: string;
  dataset: AnalyticsDataset;
  datasets: AnalyticsDataset[];
  value: AnalyticsFilter;
  change: (value: AnalyticsFilter) => void;
  depth?: number;
}) {
  if (value.relationship) {
    const relatedKey =
      value.relationship === "outbound"
        ? "outbound_movements"
        : dataset.key === "purchase_orders"
          ? "purchase_order_lines"
          : "sales_order_lines";
    const related = datasets.find((d) => d.key === relatedKey);
    return (
      <div className="space-y-2 rounded-lg border border-border-default p-3">
        <p className="text-sm font-medium">{t(related?.label || relatedKey)}</p>
        <AnalyticsSelect
          value={value.op}
          aria-label={t("Match related records")}
          onChange={(e) => change({ ...value, op: e.target.value })}
        >
          <option value="exists">{t("Has matching records")}</option>
          <option value="not_exists">{t("Has no matching records")}</option>
        </AnalyticsSelect>
        {related && (
          <Filters
            tenant={tenant}
            dataset={related}
            datasets={datasets}
            value={value.where || { all: [] }}
            depth={depth + 1}
            change={(where) =>
              change({
                ...value,
                where: (where.all || where.any)?.length === 0 ? undefined : where,
              })
            }
          />
        )}
        <label className="block text-xs">
          {t("From")}
          <input
            className={input}
            type="date"
            value={value.time?.window.start || ""}
            onChange={(e) =>
              change({
                ...value,
                time: {
                  field: value.relationship === "outbound" ? "occurred_at" : "ordered_at",
                  timezone: value.time?.timezone || "UTC",
                  window: {
                    kind: "absolute",
                    start: e.target.value,
                    end: value.time?.window.end || e.target.value,
                  },
                },
              })
            }
          />
        </label>
        <label className="block text-xs">
          {t("Until (exclusive)")}
          <input
            className={input}
            type="date"
            value={value.time?.window.end || ""}
            onChange={(e) =>
              change({
                ...value,
                time: {
                  field: value.relationship === "outbound" ? "occurred_at" : "ordered_at",
                  timezone: value.time?.timezone || "UTC",
                  window: {
                    kind: "absolute",
                    start: value.time?.window.start || e.target.value,
                    end: e.target.value,
                  },
                },
              })
            }
          />
        </label>
      </div>
    );
  }
  const children = value.all || value.any;
  if (children)
    return (
      <div className="space-y-3 rounded-lg border border-border-default p-3">
        <div className="flex flex-wrap items-center gap-2">
          <AnalyticsSelect
            aria-label={t("Match conditions")}
            value={value.all ? "all" : "any"}
            onChange={(e) => change({ [e.target.value]: children })}
          >
            <option value="all">{t("All conditions")}</option>
            <option value="any">{t("Any condition")}</option>
          </AnalyticsSelect>
          <button
            className="br-btn"
            onClick={() =>
              change({
                [value.all ? "all" : "any"]: [
                  ...children,
                  { field: dataset.dimensions[0].key, op: "eq", value: "" },
                ],
              })
            }
          >
            <Plus size={14} />
            {t("Filter")}
          </button>
          {depth < 2 &&
            dataset.relationships?.map((relationship) => (
              <button
                key={relationship}
                className="br-btn"
                onClick={() =>
                  change({
                    [value.all ? "all" : "any"]: [...children, { relationship, op: "exists" }],
                  })
                }
              >
                {t("Related records")} ·{" "}
                {t(relationship === "outbound" ? "Outbound movements" : "Order lines")}
              </button>
            ))}
          {depth < 2 && (
            <button
              className="br-btn"
              onClick={() =>
                change({
                  [value.all ? "all" : "any"]: [
                    ...children,
                    { all: [{ field: dataset.dimensions[0].key, op: "eq", value: "" }] },
                  ],
                })
              }
            >
              {t("Group")}
            </button>
          )}
        </div>
        {children.map((child, i) => (
          <div key={i} className="flex items-start gap-2">
            <div className="min-w-0 flex-1">
              <Filters
                tenant={tenant}
                datasets={datasets}
                dataset={dataset}
                value={child}
                depth={depth + 1}
                change={(next) =>
                  change({
                    [value.all ? "all" : "any"]: children.map((v, j) => (j === i ? next : v)),
                  })
                }
              />
            </div>
            <button
              className="br-btn"
              aria-label={t("Remove filter")}
              onClick={() =>
                change({ [value.all ? "all" : "any"]: children.filter((_, j) => i !== j) })
              }
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    );
  const field = dataset.dimensions.find((f) => f.key === value.field) || dataset.dimensions[0];
  return (
    <div className="grid gap-2 md:grid-cols-3">
      <AnalyticsSelect
        aria-label={t("Filter field")}
        value={field.key}
        onChange={(e) => change({ field: e.target.value, op: "eq", value: "" })}
      >
        {dataset.dimensions.map((f) => (
          <option key={f.key} value={f.key}>
            {t(f.label)}
          </option>
        ))}
      </AnalyticsSelect>
      <AnalyticsSelect
        aria-label={t("Filter operator")}
        value={value.op || "eq"}
        onChange={(e) =>
          change({
            field: field.key,
            op: e.target.value,
            ...(["is_present", "is_missing"].includes(e.target.value)
              ? {}
              : ["in", "not_in"].includes(e.target.value)
                ? { values: [""] }
                : { value: "" }),
          })
        }
      >
        {field.operators.map((op) => (
          <option key={op} value={op}>
            {t(
              (
                {
                  eq: "Equals",
                  ne: "Does not equal",
                  in: "In list",
                  not_in: "Not in list",
                  contains: "Contains",
                  gte: "At least",
                  gt: "Greater than",
                  lte: "At most",
                  lt: "Less than",
                  is_missing: "Is missing",
                  is_present: "Is present",
                } as Record<string, string>
              )[op],
            )}
          </option>
        ))}
      </AnalyticsSelect>
      <FilterValue tenant={tenant} filter={value} change={change} />
    </div>
  );
}
export function AnalyticsExplorer({
  tenant,
  report,
  onSaved,
}: {
  tenant: string;
  report: AnalyticsReport | null;
  onSaved: (report: AnalyticsReport | null) => void;
}) {
  const catalog = useRead(() => analyticsApi.catalog(tenant), [tenant]);
  const [draft, setDraft] = useState<AnalyticsDefinition>(initial);
  const [kind, setKind] = useState<"table" | "bar" | "line">("table");
  const [notice, setNotice] = useState("");
  const [support, setSupport] = useState<Awaited<
    ReturnType<typeof analyticsApi.contributors>
  > | null>(null);
  const [supportSelection, setSupportSelection] = useState<{
    definition: AnalyticsDefinition;
    group: Record<string, unknown>;
    measure: string;
  } | null>(null);
  const [supportBusy, setSupportBusy] = useState(false);
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  const [save, setSave] = useState<{
    key: string;
    name: string;
    definition: AnalyticsDefinition;
  } | null>(null);
  const [saving, setSaving] = useState(false);
  const { result, submitted, running, error, run, cancel } = useAnalyticsExecution(tenant);
  useEffect(() => {
    if (report) {
      setDraft(structuredClone(report.definition));
      void run(report.definition);
      setKind(
        report.definition.presentation?.kind === "line"
          ? "line"
          : report.definition.presentation?.kind === "bar"
            ? "bar"
            : "table",
      );
    }
  }, [report]);
  useEffect(() => {
    const apply = (event?: Event) => {
      const value =
        event instanceof CustomEvent ? event.detail : readAnalyticsHandoff(location.hash, tenant);
      if (validAnalyticsHandoff(value, tenant)) {
        setDraft(structuredClone(value.definition));
        onSaved(null);
        setNotice(t("Analysis attached. Review the settings and run it."));
      }
    };
    apply();
    window.addEventListener("reality:analytics-handoff", apply);
    window.addEventListener("hashchange", apply);
    return () => {
      window.removeEventListener("reality:analytics-handoff", apply);
      window.removeEventListener("hashchange", apply);
    };
  }, [tenant]);
  const dataset = catalog.data?.datasets.find((d) => d.key === draft.dataset);
  if (!catalog.data || !dataset)
    return <ReadState loading={catalog.loading} error={catalog.error} retry={catalog.refresh} />;
  const update = (change: Partial<AnalyticsDefinition>) => setDraft({ ...draft, ...change });
  const changed = !!result && JSON.stringify(draft) !== JSON.stringify(submitted);
  const inspect = async (row: Record<string, string | number | null>, measure: string) => {
    if (!result) return;
    setNotice("");
    try {
      const group = Object.fromEntries(
        result.columns
          .filter(
            (c) =>
              result.executed_definition.dimensions.includes(c.key) ||
              ["currency", "unit"].includes(c.key),
          )
          .map((c) => [c.key, row[c.key]]),
      );
      setSupportSelection({ definition: result.executed_definition, group, measure });
      setSupport(
        await analyticsApi.contributors(tenant, result.executed_definition, group, measure),
      );
    } catch (failure) {
      setNotice(analyticsError(failure));
    }
  };
  const exportResult = async () => {
    if (!result) return;
    setNotice("");
    try {
      const data = await analyticsApi.export(tenant, result.executed_definition);
      const url = URL.createObjectURL(new Blob([data.csv], { type: "text/csv;charset=utf-8" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = data.filename;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice(t("Export created from a fresh observation."));
    } catch (failure) {
      setNotice(analyticsError(failure));
    }
  };
  const saveReport = async () => {
    if (!save) return;
    setSaving(true);
    setNotice("");
    try {
      const next = await analyticsApi.change(tenant, {
        operation: report ? "update" : "create",
        request_id: save.key,
        name: save.name,
        definition: save.definition,
        ...(report ? { report_id: report.id, expected_revision: report.revision } : {}),
      });
      onSaved(next);
      setSave(null);
      setNotice(t("Report saved."));
    } catch (failure) {
      setNotice(analyticsError(failure));
    } finally {
      setSaving(false);
    }
  };
  return (
    <div className="analytics-explorer space-y-5">
      <div className="flex flex-wrap gap-2">
        {catalog.data.starters.map((starter) => (
          <button
            key={starter.name}
            className="br-btn"
            onClick={() => {
              setDraft(structuredClone(starter.definition));
              onSaved(null);
            }}
          >
            {t(starter.name)}
          </button>
        ))}
      </div>
      <div className="grid items-start gap-5 xl:grid-cols-[300px_minmax(0,1fr)]">
        <aside className={`${box} space-y-5`}>
          <label className="block text-sm font-medium">
            {t("Data perspective")}
            <AnalyticsSelect
              className="mt-2"
              value={draft.dataset}
              onChange={(e) => {
                const next = catalog.data!.datasets.find((d) => d.key === e.target.value)!;
                setDraft({ dataset: next.key, dimensions: [], measures: [next.measures[0].key] });
                onSaved(null);
              }}
            >
              {catalog.data.datasets.map((d) => (
                <option key={d.key} value={d.key}>
                  {t(d.label)}
                </option>
              ))}
            </AnalyticsSelect>
          </label>
          <fieldset>
            <legend className="mb-2 text-sm font-medium">{t("Measures")}</legend>
            <div className="space-y-2">
              {dataset.measures.map((m) => (
                <label key={m.key} className="flex gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={draft.measures.includes(m.key)}
                    disabled={!draft.measures.includes(m.key) && draft.measures.length >= 4}
                    onChange={(e) =>
                      update({
                        measures: e.target.checked
                          ? [...draft.measures, m.key]
                          : draft.measures.filter((v) => v !== m.key),
                      })
                    }
                  />
                  {t(m.label)}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend className="mb-2 text-sm font-medium">{t("Group by")}</legend>
            <div className="max-h-64 space-y-2 overflow-auto">
              {dataset.dimensions
                .filter((f) => f.groupable !== false)
                .map((f) => (
                  <label key={f.key} className="flex gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={draft.dimensions.includes(f.key)}
                      disabled={!draft.dimensions.includes(f.key) && draft.dimensions.length >= 4}
                      onChange={(e) =>
                        update({
                          dimensions: e.target.checked
                            ? [...draft.dimensions, f.key]
                            : draft.dimensions.filter((v) => v !== f.key),
                        })
                      }
                    />
                    {t(f.label)}
                  </label>
                ))}
            </div>
          </fieldset>
          <label className="block text-sm font-medium">
            {t("Sort by")}
            <AnalyticsSelect
              className="mt-2"
              value={draft.sort?.[0]?.field || ""}
              onChange={(e) =>
                update({
                  sort: e.target.value ? [{ field: e.target.value, direction: "desc" }] : [],
                })
              }
            >
              <option value="">{t("Default")}</option>
              {[...draft.dimensions, ...draft.measures].map((key) => (
                <option key={key} value={key}>
                  {t(
                    [...dataset.dimensions, ...dataset.measures].find((f) => f.key === key)
                      ?.label || key,
                  )}
                </option>
              ))}
              {draft.compare &&
                draft.measures.map((key) =>
                  ["change", "percent_change"].map((prefix) => (
                    <option key={`${prefix}:${key}`} value={`${prefix}:${key}`}>
                      {t(prefix === "change" ? "Change" : "Change (%)")} ·{" "}
                      {t(dataset.measures.find((m) => m.key === key)?.label || key)}
                    </option>
                  )),
                )}
            </AnalyticsSelect>
          </label>
          {draft.sort?.length ? (
            <AnalyticsSelect
              aria-label={t("Sort direction")}
              value={draft.sort[0].direction}
              onChange={(e) =>
                update({
                  sort: [{ ...draft.sort![0], direction: e.target.value as "asc" | "desc" }],
                })
              }
            >
              <option value="desc">{t("Descending")}</option>
              <option value="asc">{t("Ascending")}</option>
            </AnalyticsSelect>
          ) : null}
        </aside>
        <main className="min-w-0 space-y-5">
          <section className={`${box} space-y-4`}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">{report?.name || t("New analysis")}</h2>
              <span className="text-xs text-fg-muted">{t("Read-only analysis")}</span>
            </div>
            {dataset.dimensions.some((f) => f.type === "datetime") && (
              <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,210px),1fr))] gap-3">
                <label className="text-sm">
                  {t("Date field")}
                  <AnalyticsSelect
                    className="mt-1"
                    value={draft.time?.field || ""}
                    onChange={(e) =>
                      update({
                        time: e.target.value
                          ? {
                              field: e.target.value,
                              timezone: initial.time!.timezone,
                              window: { kind: "last_complete_weeks", count: 12 },
                            }
                          : null,
                        compare: null,
                      })
                    }
                  >
                    <option value="">{t("All recorded history")}</option>
                    {dataset.dimensions
                      .filter((f) => f.type === "datetime")
                      .map((f) => (
                        <option key={f.key} value={f.key}>
                          {t(f.label)}
                        </option>
                      ))}
                  </AnalyticsSelect>
                </label>
                {draft.time && (
                  <>
                    <label className="text-sm">
                      {t("Period")}
                      <AnalyticsSelect
                        className="mt-1"
                        value={draft.time.window.kind}
                        onChange={(e) =>
                          update({
                            time: {
                              ...draft.time!,
                              window:
                                e.target.value === "iso_week"
                                  ? { kind: "iso_week", year: new Date().getFullYear(), week: 7 }
                                  : e.target.value === "absolute"
                                    ? {
                                        kind: "absolute",
                                        start: new Date().toISOString().slice(0, 10),
                                        end: new Date(Date.now() + 86400000)
                                          .toISOString()
                                          .slice(0, 10),
                                      }
                                    : { kind: e.target.value, count: 12 },
                            },
                          })
                        }
                      >
                        {(
                          [
                            ["last_complete_weeks", "Last complete weeks"],
                            ["last_complete_months", "Last complete months"],
                            ["last_days", "Last days"],
                            ["current_month", "This month"],
                            ["current_quarter", "This quarter"],
                            ["current_year", "This year"],
                            ["iso_week", "ISO week"],
                            ["absolute", "Custom dates"],
                          ] as const
                        ).map(([v, l]) => (
                          <option key={v} value={v}>
                            {t(l)}
                          </option>
                        ))}
                      </AnalyticsSelect>
                    </label>
                    <label className="text-sm">
                      {t("Timezone")}
                      <input
                        className={`${input} mt-1`}
                        value={draft.time.timezone}
                        onChange={(e) =>
                          update({ time: { ...draft.time!, timezone: e.target.value } })
                        }
                      />
                    </label>
                    {["last_complete_weeks", "last_complete_months", "last_days"].includes(
                      draft.time.window.kind,
                    ) && (
                      <label className="text-sm">
                        {t("Number of periods")}
                        <input
                          type="number"
                          min="1"
                          max="3660"
                          className={`${input} mt-1`}
                          value={draft.time.window.count}
                          onChange={(e) =>
                            update({
                              time: {
                                ...draft.time!,
                                window: { ...draft.time!.window, count: Number(e.target.value) },
                              },
                            })
                          }
                        />
                      </label>
                    )}
                    {draft.time.window.kind === "iso_week" &&
                      (["year", "week"] as const).map((key) => (
                        <label key={key} className="text-sm">
                          {t(key === "year" ? "Year" : "Week")}
                          <input
                            type="number"
                            min={key === "year" ? 1900 : 1}
                            max={key === "year" ? 9998 : 53}
                            className={`${input} mt-1`}
                            value={draft.time!.window[key]}
                            onChange={(e) =>
                              update({
                                time: {
                                  ...draft.time!,
                                  window: { ...draft.time!.window, [key]: Number(e.target.value) },
                                },
                              })
                            }
                          />
                        </label>
                      ))}
                    {draft.time.window.kind === "absolute" &&
                      (["start", "end"] as const).map((key) => (
                        <label key={key} className="text-sm">
                          {t(key === "start" ? "Start date" : "End date (exclusive)")}
                          <input
                            type="date"
                            className={`${input} mt-1`}
                            value={draft.time!.window[key]}
                            onChange={(e) =>
                              update({
                                time: {
                                  ...draft.time!,
                                  window: { ...draft.time!.window, [key]: e.target.value },
                                },
                              })
                            }
                          />
                        </label>
                      ))}
                  </>
                )}
              </div>
            )}
            {draft.dimensions.length >= 2 && draft.dimensions.length <= 3 && (
              <label className="flex gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={draft.presentation?.kind === "pivot"}
                  onChange={(e) =>
                    update({
                      presentation: e.target.checked
                        ? {
                            kind: "pivot",
                            rows: draft.dimensions.slice(0, -1),
                            column: draft.dimensions.at(-1),
                            measures: draft.measures.slice(0, 2),
                          }
                        : { kind: "table" },
                    })
                  }
                />
                {t("Pivot by selected dimensions")}
              </label>
            )}
            {draft.time && (
              <label className="flex gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={draft.compare === "previous_period"}
                  onChange={(e) => update({ compare: e.target.checked ? "previous_period" : null })}
                />
                {t("Compare with previous period")}
              </label>
            )}
            <details
              className="group rounded-lg border border-border-strong bg-surface"
              open={!!draft.where}
            >
              <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 rounded-lg px-3 text-sm font-medium hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-accent [&::-webkit-details-marker]:hidden">
                <SlidersHorizontal aria-hidden="true" className="size-4 text-fg-secondary" />
                {t("Filters")}
                <ChevronDown
                  aria-hidden="true"
                  className="ml-auto size-5 text-fg-secondary transition-transform group-open:rotate-180"
                />
              </summary>
              <div className="border-t border-border-default p-3">
                <Filters
                  tenant={tenant}
                  datasets={catalog.data.datasets}
                  dataset={dataset}
                  value={draft.where || { all: [] }}
                  change={(where) =>
                    update({ where: (where.all || where.any)?.length === 0 ? null : where })
                  }
                />
              </div>
            </details>
            <div className="flex flex-wrap gap-2 border-t border-border-default pt-4">
              <button
                className="br-btn br-btn-primary"
                disabled={running || !draft.measures.length}
                onClick={() => {
                  setSupport(null);
                  void run(draft);
                }}
              >
                <Play size={15} />
                {running ? t("Running analysis…") : t("Run analysis")}
              </button>
              {running && (
                <button className="br-btn" onClick={cancel}>
                  {t("Cancel")}
                </button>
              )}
              <button
                className="br-btn"
                disabled={!draft.measures.length}
                onClick={() =>
                  setSave({
                    key: crypto.randomUUID(),
                    name: report?.name || "",
                    definition: structuredClone(draft),
                  })
                }
              >
                <Save size={15} />
                {t("Save report")}
              </button>
              <button
                className="br-btn"
                onClick={() =>
                  window.dispatchEvent(
                    new CustomEvent("reality:open-chat", {
                      detail: { version: 1, tenant_id: tenant, definition: structuredClone(draft) },
                    }),
                  )
                }
              >
                {t("Start new chat about analysis")}
              </button>
            </div>
          </section>
          {error && (
            <p role="alert" className="rounded-lg border border-border-default p-4 text-sm">
              {error}
            </p>
          )}
          {notice && (
            <p role="status" className="rounded-lg border border-border-default p-4 text-sm">
              {notice}
            </p>
          )}
          {save && (
            <section className={box} role="dialog" aria-label={t("Save report")}>
              <label className="block text-sm">
                {t("Report name")}
                <input
                  autoFocus
                  className={`${input} mt-2`}
                  maxLength={120}
                  value={save.name}
                  onChange={(e) =>
                    setSave({ ...save, key: crypto.randomUUID(), name: e.target.value })
                  }
                />
              </label>
              <p className="my-3 text-xs text-fg-muted">
                {t("Only the definition is saved. Results are refreshed when you run it.")}
              </p>
              <div className="flex gap-2">
                <button
                  className="br-btn br-btn-primary"
                  disabled={saving || !save.name.trim()}
                  onClick={() => void saveReport()}
                >
                  {t("Save")}
                </button>
                <button className="br-btn" disabled={saving} onClick={() => setSave(null)}>
                  {t("Cancel")}
                </button>
              </div>
            </section>
          )}
          {!result && (
            <div className="rounded-xl border border-dashed border-border-default p-12 text-center">
              <h3 className="font-medium">{t("Start with a business question")}</h3>
              <p className="mx-auto mt-2 max-w-md text-sm text-fg-muted">
                {t(
                  "Choose a perspective, measures and filters, then run your analysis. Select any result to see its supporting records.",
                )}
              </p>
            </div>
          )}
          {result && (
            <section className={`${box} space-y-4`}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{t("Analysis results")}</h3>
                  <p className="mt-1 text-xs text-fg-muted">
                    {formatNumber(result.page.total)} {t("groups")} · {t("Observed at")}{" "}
                    {formatDateTime(result.metadata.observed_at)}
                  </p>
                </div>
                <button className="br-btn" onClick={() => void exportResult()}>
                  <Download size={15} />
                  {t("Export CSV")}
                </button>
              </div>
              {changed && (
                <p className="rounded-lg bg-surface-muted p-3 text-sm">
                  {t("Results show the last executed settings. Run again to apply your edits.")}
                </p>
              )}
              <div className="flex flex-wrap gap-3">
                {result.population_totals.map((total, i) => (
                  <div key={i} className="min-w-40 flex-1 rounded-lg bg-surface-muted p-4">
                    <p className="text-xs text-fg-muted">
                      {t("Full population")} · {total.currency ?? total.unit ?? ""}
                    </p>
                    {result.executed_definition.measures.map((key) => (
                      <div key={key} className="mt-2 flex items-baseline justify-between gap-3">
                        <span className="text-xs">
                          {t(result.columns.find((c) => c.key === key)!.label)}
                        </span>
                        <strong className="tabular-nums">
                          {analyticValue(
                            total[key],
                            result.columns.find((c) => c.key === key)!.type,
                          )}
                        </strong>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                {(["table", "bar", "line"] as const).map((value) => (
                  <button
                    className="br-btn aria-pressed:bg-accent-soft"
                    key={value}
                    aria-pressed={kind === value}
                    onClick={() => {
                      setKind(value);
                      if (draft.presentation?.kind !== "pivot")
                        update({ presentation: { kind: value } });
                    }}
                  >
                    {t(value === "table" ? "Table" : value === "bar" ? "Bar chart" : "Line chart")}
                  </button>
                ))}
              </div>
              {kind !== "table" && <AnalyticsChart result={result} kind={kind} />}
              {result.pivot && (
                <AnalyticsPivot
                  result={result}
                  inspect={(row, measure) => void inspect(row, measure)}
                />
              )}
              <AnalyticsTable
                result={result}
                inspect={(row, measure) => void inspect(row, measure)}
              />
              <div className="flex gap-2">
                <button
                  className="br-btn"
                  disabled={running}
                  onClick={() => void run(result.executed_definition)}
                >
                  {t("Refresh first page")}
                </button>
                <button
                  className="br-btn"
                  disabled={running || !result.page.has_more}
                  onClick={() =>
                    void run(result.executed_definition, result.page.next_cursor || undefined)
                  }
                >
                  {t("Next")}
                </button>
              </div>
              {result.comparison && (
                <details>
                  <summary className="cursor-pointer text-sm">{t("Previous period")}</summary>
                  <AnalyticsTable
                    result={result.comparison}
                    inspect={() =>
                      setNotice(t("Run the comparison period directly to inspect its records."))
                    }
                  />
                </details>
              )}
              <details className="text-xs text-fg-muted">
                <summary className="cursor-pointer">{t("Scope and data quality")}</summary>
                <p className="mt-2">
                  {t(
                    "Based on interpreted records held in this company. Upstream history may be incomplete. Pages and exports use fresh observations.",
                  )}
                </p>
                {result.metadata.resolved_window && (
                  <p className="mt-2">
                    {formatDateTime(result.metadata.resolved_window.start)} →{" "}
                    {formatDateTime(result.metadata.resolved_window.end)} ·{" "}
                    {result.metadata.resolved_window.timezone}
                  </p>
                )}
                <p className="mt-2">
                  {t("Undated records excluded")}: {formatNumber(result.metadata.undated_excluded)}
                </p>
                {Object.entries(result.metadata.missing_values).map(([key, count]) => (
                  <p key={key}>
                    {t(result.columns.find((c) => c.key === key)?.label || key)} ·{" "}
                    {t("Missing values")}: {formatNumber(count)}
                  </p>
                ))}
              </details>
            </section>
          )}
          {support && (
            <section className={box}>
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">
                  {t("Supporting records")} · {formatNumber(support.total)}
                </h3>
                <button className="br-btn" onClick={() => setSupport(null)}>
                  {t("Close")}
                </button>
              </div>
              <p className="my-3 text-xs text-fg-muted">
                {t("Fresh observation of the selected value.")}
              </p>
              <div className="divide-y divide-border-default">
                {support.records.map((row, i) => (
                  <button
                    key={i}
                    className="flex w-full flex-wrap items-center justify-between gap-2 py-3 text-left text-sm"
                    disabled={!row.record_id && !row.order_id && !row.product_id}
                    onClick={() =>
                      setTarget({
                        id: (row.record_id || row.order_id || row.product_id)!,
                        kind: row.record_kind || (row.order_id ? "document" : "item"),
                      })
                    }
                  >
                    <span>
                      {row.order || row.product || row.party || row.record_id || row.product_id}
                    </span>
                    <span className="text-fg-muted">
                      {row.customer || row.supplier || row.location}
                    </span>
                  </button>
                ))}
              </div>
              {support.has_more && (
                <button
                  className="br-btn"
                  disabled={supportBusy}
                  onClick={async () => {
                    if (!supportSelection || !support.next_cursor) return;
                    setSupportBusy(true);
                    try {
                      setSupport(
                        await analyticsApi.contributors(
                          tenant,
                          supportSelection.definition,
                          supportSelection.group,
                          supportSelection.measure,
                          support.next_cursor,
                        ),
                      );
                    } catch (failure) {
                      setNotice(analyticsError(failure));
                    } finally {
                      setSupportBusy(false);
                    }
                  }}
                >
                  {t("Next")}
                </button>
              )}
            </section>
          )}
        </main>
      </div>
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </div>
  );
}
