import { useState } from "react";
import { t } from "../localization";
import { RegisterHeader } from "./RegisterWorkbench";
import { AnalyticsExplorer } from "./analytics/AnalyticsExplorer";
import { GraphConsole } from "./analytics/GraphConsole";
import { GraphSteps } from "./analytics/GraphSteps";
import { ReportLibrary } from "./analytics/ReportLibrary";
import type { AnalyticsReport } from "../api";
import type { Selection } from "./routing";

export function AnalyticsPage(props: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const { selection } = props;
  return <AnalyticsWorkspace key={selection.tenant} {...props} />;
}
function AnalyticsWorkspace({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const [report, setReport] = useState<AnalyticsReport | null>(null);
  const view = selection.analyticsView || "explore";
  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <RegisterHeader title="Reports">
        <nav className="register-tabs" aria-label={t("Analytics views")}>
          {(
            [
              ["explore", "Explore"],
              ["graph", "Business graph"],
              ["console", "Query console"],
              ["reports", "My reports"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              className="br-btn"
              aria-pressed={view === key}
              onClick={() => navigate({ analyticsView: key, page: 1 })}
            >
              {t(label)}
            </button>
          ))}
        </nav>
      </RegisterHeader>
      <div hidden={view !== "explore"}>
        <AnalyticsExplorer tenant={selection.tenant} report={report} onSaved={setReport} />
      </div>
      {view === "graph" && <GraphSteps tenant={selection.tenant} />}
      {view === "console" && <GraphConsole tenant={selection.tenant} />}
      {view === "reports" && (
        <ReportLibrary
          tenant={selection.tenant}
          open={(value) => {
            setReport(value);
            navigate({ analyticsView: "explore" });
          }}
        />
      )}
    </div>
  );
}
