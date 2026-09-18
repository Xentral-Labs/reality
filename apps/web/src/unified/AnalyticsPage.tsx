import { recordOpened } from "./usePaletteHistory";
import { useEffect, useRef, useState } from "react";
import { t } from "../localization";
import { RegisterHeader, RegisterWorkbench } from "./RegisterWorkbench";
import { DataExplorer } from "./analytics/DataExplorer";
import { GraphSteps } from "./analytics/GraphSteps";
import { GraphTemplates } from "./analytics/GraphTemplates";
import { ReportLibrary } from "./analytics/ReportLibrary";
import { openAnalysisChat } from "./analytics/chatHandoff";
import { graphApi, type GraphReport, type GraphQuestion } from "../api";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import type { Selection } from "./routing";

export function AnalyticsPage(props: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  return <AnalyticsWorkspace key={props.selection.tenant} {...props} />;
}
function AnalyticsWorkspace({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const [report, setReport] = useState<GraphReport | null>(null);
  const [draft, setDraft] = useState<{ question?: GraphQuestion; revision: number } | null>(null);
  const [templates, setTemplates] = useState(selection.analyticsView === "templates");
  const targetKey = `${selection.analyticsReport || ""}:${selection.analyticsTemplate || ""}`;
  const currentTarget = useRef(targetKey);
  useEffect(() => {
    if (currentTarget.current === targetKey) return;
    currentTarget.current = targetKey;
    setReport(null);
    setDraft(null);
    setTemplates(selection.analyticsView === "templates");
  }, [targetKey, selection.analyticsView]);
  const view =
    selection.analyticsView === "templates" ? "graph" : selection.analyticsView || "reports";
  const open = (question?: GraphQuestion, saved: GraphReport | null = null) => {
    currentTarget.current = ":";
    setReport(saved);
    setDraft((previous) => ({ question, revision: (previous?.revision ?? 0) + 1 }));
    setTemplates(false);
    navigate({
      analyticsView: "graph",
      analyticsProposal: "",
      analyticsTemplate: "",
      analyticsReport: "",
    });
  };
  const start = () => {
    currentTarget.current = ":";
    setReport(null);
    setDraft(null);
    setTemplates(false);
    navigate({
      analyticsView: "graph",
      analyticsProposal: "",
      analyticsTemplate: "",
      analyticsReport: "",
    });
  };
  return (
    <RegisterWorkbench>
      <RegisterHeader title="Reports">
        <nav className="register-tabs" aria-label={t("Analytics views")}>
          {(
            [
              ["reports", "My reports"],
              ["graph", "Analysis"],
              ["explore", "Explore data"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              className="br-btn"
              aria-pressed={view === key}
              onClick={() => navigate({ analyticsView: key, analyticsProposal: "", page: 1 })}
            >
              {t(label)}
            </button>
          ))}
        </nav>
      </RegisterHeader>
      {view === "graph" && selection.analyticsReport && !draft ? (
        <SavedReportAnalysis
          tenant={selection.tenant}
          id={selection.analyticsReport}
          loaded={(value) => {
            setReport(value);
            setDraft({ question: value.definition, revision: 1 });
          }}
        />
      ) : view === "graph" && selection.analyticsProposal ? (
        <ProposalAnalysis
          key={`${selection.tenant}:${selection.analyticsProposal}`}
          tenant={selection.tenant}
          id={selection.analyticsProposal}
          open={open}
        />
      ) : (
        view === "graph" &&
        !draft && (
          <section className="register-surface space-y-4">
            <p className="text-sm text-fg-muted">
              {t("How would you like to create your analysis?")}
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                className="br-btn"
                onClick={() => openAnalysisChat(selection.tenant, t("New analysis"))}
              >
                {t("Create with chat")}
              </button>
              <button
                className="br-btn"
                aria-pressed={templates || selection.analyticsView === "templates"}
                onClick={() => setTemplates(!templates)}
              >
                {t("Use a template")}
              </button>
              <button className="br-btn" onClick={() => open()}>
                {t("Build it yourself")}
              </button>
            </div>
            <p className="text-xs text-fg-muted">
              {t(
                "Describe your question in chat or choose the data yourself. Both lead to the same analysis.",
              )}
            </p>
            {(templates || selection.analyticsView === "templates") && (
              <GraphTemplates
                tenant={selection.tenant}
                selectedKey={selection.analyticsTemplate}
                onAdopted={(question) => {
                  setDraft({ question, revision: 1 });
                  setTemplates(false);
                  navigate({ analyticsView: "graph" });
                }}
              />
            )}
          </section>
        )
      )}
      {draft && (
        <div
          hidden={
            view !== "graph" ||
            !!selection.analyticsProposal ||
            selection.analyticsView === "templates"
          }
        >
          <GraphSteps
            key={draft.revision}
            tenant={selection.tenant}
            report={report}
            initialQuestion={draft.question}
            active={
              view === "graph" &&
              !selection.analyticsProposal &&
              selection.analyticsView !== "templates"
            }
            onSaved={setReport}
            onNew={start}
          />
        </div>
      )}
      {view === "explore" && <DataExplorer tenant={selection.tenant} open={open} />}
      {view === "reports" && (
        <ReportLibrary
          tenant={selection.tenant}
          create={start}
          open={(value) => open(value.definition, value)}
        />
      )}
    </RegisterWorkbench>
  );
}

function ProposalAnalysis({
  tenant,
  id,
  open,
}: {
  tenant: string;
  id: string;
  open: (question: GraphQuestion) => void;
}) {
  const read = useRead(() => graphApi.proposal(tenant, id), [tenant, id]);
  const proposal = read.data;
  const supported =
    proposal?.kind === "graph" &&
    ["create", "update"].includes(proposal.operation) &&
    !!proposal.definition;
  useEffect(() => {
    if (supported && proposal?.definition) open(proposal.definition);
  }, [proposal, supported]);
  if (!proposal)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return (
    <p className="text-sm text-fg-muted" role="status">
      {t(supported ? "Reading data…" : "This proposal cannot be opened as an analysis.")}
    </p>
  );
}

function SavedReportAnalysis({
  tenant,
  id,
  loaded,
}: {
  tenant: string;
  id: string;
  loaded: (report: GraphReport) => void;
}) {
  const read = useRead(() => graphApi.report(tenant, id), [tenant, id]);
  useEffect(() => {
    if (read.data) {
      recordOpened(tenant, "analytics_report", id);
      loaded(read.data);
    }
  }, [read.data]);
  return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
}
