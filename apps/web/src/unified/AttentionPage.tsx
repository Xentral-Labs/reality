import { useTrialResult } from "./FreePlayground";
import { ExceptionRulesRegister } from "./ExceptionRulesRegister";
import { RegisterHeader } from "./RegisterWorkbench";
import { useState } from "react";
import { ArrowRight, TriangleAlert } from "lucide-react";
import { operationsApi, type AttentionRow } from "../api";
import { t } from "../localization";
import { ReadState } from "./ReadState";
import { Inspector } from "./Inspector";
import { useRead } from "./useCompanyContext";
import type { Selection } from "./routing";
import { WorkFooter, WorkHeader, WorkRow, WorkSearch, useWorkList } from "./WorkList";
import { WorkPreview } from "./InlinePreview";
import { ProjectionFreshness } from "./ProjectionFreshness";
const severities = [
  ["critical", "Critical"],
  ["high", "High"],
  ["normal", "Normal"],
  ["low", "Low"],
] as const;
function OpenExceptions({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const { tenant, q, severity, exception } = selection;
  const read = useWorkList<AttentionRow>(JSON.stringify([tenant, q, severity]), (page) =>
    operationsApi.attention(tenant, q, severity, page),
  );
  useTrialResult(
    "attention",
    tenant,
    !!read.page && !read.loading && !read.error && read.metadata?.state !== "uninitialized",
  );
  const detail = useRead(
    () => (exception ? operationsApi.finding(tenant, exception) : Promise.resolve(null)),
    [tenant, exception],
  );
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  const selected = detail.data?.id === exception ? detail.data : null;
  const severityLabel = (value: string) =>
    t(severities.find(([key]) => key === value)?.[1] || value);
  return (
    <div className="mx-auto max-w-[1200px] space-y-3" data-work-list="exceptions">
      <WorkHeader title="Exceptions" total={read.page?.total} />
      <div className="exceptions-filter-row work-list-toolbar grid gap-2">
        <WorkSearch
          value={q}
          change={(q) => navigate({ q, page: 1, exception: "" })}
          label="Search causes or references"
        />
        <div className="work-list-filters flex min-w-0 flex-wrap gap-2">
          <select
            className="br-control min-w-0 flex-1"
            aria-label={t("Severity")}
            value={severity}
            onChange={(event) => navigate({ severity: event.target.value, page: 1, exception: "" })}
          >
            <option value="">{t("All severities")}</option>
            {severities.map(([value, label]) => (
              <option key={value} value={value}>
                {t(label)}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="br-btn shrink-0"
            onClick={() => navigate({ attentionView: "rules", q: "", page: 1, exception: "" })}
          >
            {t("View all possible findings")}
          </button>
        </div>
      </div>
      <ProjectionFreshness
        metadata={read.metadata}
        refresh={read.refresh}
        loading={read.loading}
        error={read.error}
      />
      <section
        className="overflow-hidden rounded-xl border border-border-default bg-surface"
        aria-busy={read.loading}
      >
        {!read.page && read.loading ? (
          <ReadState loading rows={8} />
        ) : !read.items.length && !read.error ? (
          <p className="px-5 py-14 text-center text-sm text-fg-muted" data-attention-empty>
            {t(
              read.metadata?.state === "uninitialized"
                ? "Awaiting first calculation."
                : q || severity
                  ? "No matching findings"
                  : "No current findings",
            )}
          </p>
        ) : (
          read.items.map((row, index) => (
            <div key={row.id}>
              {(index === 0 || row.severity !== read.items[index - 1].severity) && (
                <h2 className="border-b border-border-default bg-surface-muted px-4 py-1.5 text-xs font-medium text-fg-muted">
                  {severityLabel(row.severity)}
                </h2>
              )}
              <WorkRow
                title={t(row.title)}
                context={row.context || row.impact}
                meta={t("Review")}
                icon={<TriangleAlert size={18} />}
                selected={exception === row.id}
                previewId={`finding-preview-${row.id}`}
                open={() => navigate({ exception: exception === row.id ? "" : row.id })}
              />
              <WorkPreview id={`finding-preview-${row.id}`} open={exception === row.id}>
                {!selected && detail.code === "finding_cleared" ? (
                  <div role="status" data-finding-cleared className="text-sm">
                    <p className="font-medium text-fg-strong">
                      {t("This finding has cleared since the last calculation.")}
                    </p>
                    <p className="mt-1 text-fg-muted">
                      {t("It disappears from the list with the next calculation.")}
                    </p>
                    <button className="br-btn mt-3" onClick={read.refresh}>
                      {t("Refresh")}
                    </button>
                  </div>
                ) : !selected ? (
                  <ReadState loading={detail.loading} error={detail.error} retry={detail.refresh} />
                ) : (
                  <>
                    <h3 className="text-lg font-semibold text-fg-strong">{t(selected.title)}</h3>
                    {selected.context && <p className="mt-2 font-medium">{selected.context}</p>}
                    <p className="mt-2 text-sm text-fg-muted">{selected.impact}</p>
                    <div className="mt-4 rounded-lg bg-surface p-4">
                      <h4 className="font-semibold">{t("Resolution guidance")}</h4>
                      <p className="mt-2 text-sm text-fg-muted">{selected.guidance}</p>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {selected.target.delivery_id && (
                        <button
                          className="br-btn br-btn-primary"
                          onClick={() =>
                            navigate({
                              route: "orders-deliveries",
                              ordersView: "deliveries",
                              commitment: selected.target.delivery_id,
                              proposal: "",
                            })
                          }
                        >
                          {t("Open delivery")}
                          <ArrowRight size={16} aria-hidden="true" />
                        </button>
                      )}
                      <button
                        className="br-btn"
                        onClick={() => setTarget({ kind: "exception", id: selected.id })}
                      >
                        {t("Explain finding")}
                      </button>
                      <button className="br-btn" onClick={() => setTarget(selected.target)}>
                        {t("Supporting record")}
                      </button>
                    </div>
                  </>
                )}
              </WorkPreview>
            </div>
          ))
        )}
        <WorkFooter list={read} />
      </section>

      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </div>
  );
}

export function AttentionPage(props: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const view = props.selection.attentionView || "findings";
  return (
    <div className="min-w-0 space-y-4" data-exceptions-workspace>
      <RegisterHeader title="Exceptions" placement="local">
        <nav className="register-tabs" aria-label={t("Exceptions")}>
          {(
            [
              ["findings", "Open exceptions"],
              ["rules", "Exception rules"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              aria-pressed={view === key}
              onClick={() => props.navigate({ attentionView: key, q: "", page: 1, exception: "" })}
            >
              {t(label)}
            </button>
          ))}
        </nav>
      </RegisterHeader>
      {view === "rules" ? (
        <ExceptionRulesRegister
          key={props.selection.tenant}
          tenant={props.selection.tenant}
          navigate={props.navigate}
        />
      ) : (
        <OpenExceptions {...props} />
      )}
    </div>
  );
}
