import { useState } from "react";
import type { ApplicationReference } from "../api";
import { t } from "../localization";
import { RegisterToolbar } from "./RegisterWorkbench";
import { DirectoryBranch } from "./DirectoryBranch";
import { buildReports, filterReports, groupReports, type Report } from "./reportCatalogEntries";

export function ReportCatalog({
  reference,
  open,
}: {
  reference: ApplicationReference;
  open: (report: Report) => void;
}) {
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const reports = filterReports(buildReports(reference), query, "All", t);
  const groups = groupReports(reports);
  const searching = !!query.trim();
  const toggle = (key: string) =>
    setExpanded((previous) => {
      const next = new Set(previous);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  return (
    <section className="register-surface overflow-hidden" data-report-catalog>
      <RegisterToolbar
        count={reports.length}
        search={
          <input
            type="search"
            className="br-control"
            placeholder={t("Search reports")}
            aria-label={t("Search reports")}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        }
        submit={
          query ? (
            <button className="br-btn" onClick={() => setQuery("")}>
              {t("Clear search")}
            </button>
          ) : undefined
        }
        filters={
          <>
            <button
              className="br-btn"
              disabled={searching}
              onClick={() => setExpanded(new Set(groups.map((group) => group.key)))}
            >
              {t("Expand all")}
            </button>
            <button className="br-btn" disabled={searching} onClick={() => setExpanded(new Set())}>
              {t("Collapse all")}
            </button>
          </>
        }
      />
      <div className="py-4">
        {!reports.length && (
          <div role="status" className="p-4 text-sm text-fg-muted">
            <p>{t("No matching reports")}</p>
          </div>
        )}
        {groups.map((group) => (
          <DirectoryBranch
            key={group.key}
            id={`reports-${group.key}`}
            label={t(group.key)}
            count={group.reports.length}
            open={searching || expanded.has(group.key)}
            toggle={() => {
              if (!searching) toggle(group.key);
            }}
          >
            {group.reports.map((report) => (
              <details
                key={report.target}
                data-report={report.target}
                className="ml-3 border-l border-border-default pl-3 sm:ml-6"
              >
                <summary className="cursor-pointer rounded-lg px-2 py-3 text-sm hover:bg-surface-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent">
                  <span className="ml-1">{t(report.title)}</span>
                </summary>
                <div className="min-w-0 space-y-3 px-2 pb-4">
                  <p className="text-sm leading-6 text-fg-muted">{t(report.description)}</p>
                  <p className="text-xs text-fg-muted">{report.categories.map(t).join(" · ")}</p>
                  <button
                    type="button"
                    className="br-btn"
                    data-report-open
                    onClick={() => open(report)}
                  >
                    {t(report.dataAvailable ? "Open report" : "Show details")}
                  </button>
                </div>
              </details>
            ))}
          </DirectoryBranch>
        ))}
      </div>
    </section>
  );
}
