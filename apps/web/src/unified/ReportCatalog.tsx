import { useState } from "react";
import { ArrowRight, BarChart3 } from "lucide-react";
import type { ApplicationReference } from "../api";
import { t } from "../localization";
import { RegisterToolbar, RegisterWorkbench } from "./RegisterWorkbench";
import { buildReports, filterReports, reportCategories, type Report } from "./reportCatalogEntries";

export function ReportCatalog({
  reference,
  open,
}: {
  reference: ApplicationReference;
  open: (report: Report) => void;
}) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const reports = filterReports(buildReports(reference), query, category, t);
  return (
    <RegisterWorkbench>
      <section className="register-surface" data-report-catalog>
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
        />
        <div
          className="flex flex-wrap gap-2 border-b border-border-default px-4 pb-4"
          role="group"
          aria-label={t("Workspaces")}
        >
          {reportCategories.map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={category === value}
              className={`br-btn ${category === value ? "br-btn-primary" : ""}`}
              onClick={() => setCategory(value)}
            >
              {t(value)}
            </button>
          ))}
        </div>
        <div className="divide-y divide-border-default">
          {reports.map((report) => (
            <button
              key={report.target}
              type="button"
              data-report={report.target}
              onClick={() => open(report)}
              className="flex w-full min-w-0 items-start gap-4 px-4 py-5 text-left transition-colors hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-primary sm:px-6"
            >
              <span className="mt-1 hidden rounded-lg bg-surface-muted p-2 text-primary sm:block">
                <BarChart3 size={20} aria-hidden="true" />
              </span>
              <span className="flex min-w-0 flex-1 flex-col gap-2">
                <span className="font-semibold text-fg-strong">{t(report.title)}</span>
                <span className="text-sm leading-relaxed text-fg-muted">
                  {t(report.description)}
                </span>
                <span className="flex flex-wrap gap-2">
                  {report.categories.map((value) => (
                    <span
                      key={value}
                      className="rounded-md bg-surface-muted px-2 py-1 text-xs text-fg-muted"
                    >
                      {t(value)}
                    </span>
                  ))}
                </span>
              </span>
              <span className="mt-1 flex shrink-0 items-center gap-2 text-sm font-medium text-primary">
                <span className="hidden sm:inline">
                  {t(report.dataAvailable ? "Open report" : "Show details")}
                </span>
                <ArrowRight size={18} aria-hidden="true" />
              </span>
            </button>
          ))}
          {!reports.length && (
            <div role="status" className="px-6 py-12 text-center">
              <p className="font-medium">{t("No matching reports")}</p>
              <p className="mt-2 text-sm text-fg-muted">{t("Try another search or workspace.")}</p>
            </div>
          )}
        </div>
      </section>
    </RegisterWorkbench>
  );
}
