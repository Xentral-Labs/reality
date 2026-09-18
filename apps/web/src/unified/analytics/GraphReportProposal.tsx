import { useState } from "react";
import { api, graphApi, type GraphQuestion } from "../../api";
import { currentLanguage, t } from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { analyticsError } from "./errors";

/** A report change the copilot proposed, shown in the words of the model.
 *
 * The proposal carries the question, not its answer, so what is confirmed is
 * what will be re-executed every time the report is opened. It is spelled out
 * in business labels because a person confirms it, and the raw question stays
 * one disclosure away for whoever wants to check it.
 */
export function GraphReportProposal({
  tenant,
  id,
  refresh,
}: {
  tenant: string;
  id: string;
  refresh: () => void;
}) {
  const language = currentLanguage();
  const read = useRead(() => graphApi.proposal(tenant, id), [tenant, id]);
  const catalog = useRead(() => graphApi.catalog(tenant, language), [tenant, language]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const act = async (decide: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await decide();
      read.refresh();
      refresh();
    } catch (failure) {
      setError(analyticsError(failure));
    } finally {
      setBusy(false);
    }
  };
  if (read.loading) return <ReadState loading={true} retry={read.refresh} />;
  if (!read.data)
    // A proposal that cannot be shown still has to be dismissible. Offering only
    // "try again" leaves the reader pressing a button that can never work — for
    // a card that follows them into every conversation they open.
    return (
      <section className="space-y-3 rounded-xl border border-warning-200 bg-warning-50 p-4">
        <h3 className="text-sm font-semibold text-warning-600">
          {t("This proposal cannot be shown")}
        </h3>
        <p className="text-sm">{analyticsError(read.error)}</p>
        <div className="flex flex-wrap gap-2">
          <button className="br-btn" disabled={busy} onClick={() => read.refresh()}>
            {t("Try again")}
          </button>
          <button
            className="br-btn"
            disabled={busy}
            onClick={() => act(() => api.rejectProposal(tenant, id, null))}
          >
            {t("Reject")}
          </button>
        </div>
        {error && <p className="text-sm text-critical-text">{error}</p>}
      </section>
    );
  const proposal = read.data;
  const question = proposal.definition as GraphQuestion | null;
  const node = catalog.data?.nodes.find((candidate) => candidate.key === question?.from);
  const measures = (question?.measures ?? []).map(
    (key) =>
      catalog.data?.nodes
        .flatMap((candidate) => candidate.measures)
        .find((measure) => measure.key === key)?.label ?? key,
  );
  const OPERATIONS: Record<string, string> = {
    create: "Create",
    update: "Update",
    rename: "Rename",
    duplicate: "Duplicate",
    delete: "Delete",
  };
  return (
    <section className="space-y-3 rounded-xl border border-border-default bg-surface p-4">
      <h3 className="font-semibold">
        {t("Change private report")}: {proposal.name}
      </h3>
      <p className="text-sm">
        {t(OPERATIONS[proposal.operation] ?? proposal.operation)}
        {node && ` · ${node.label}`}
      </p>
      {measures.length > 0 && <p className="text-sm">{measures.join(" · ")}</p>}
      <details className="text-xs">
        <summary>{t("The saved question")}</summary>
        <pre className="mt-2 overflow-auto whitespace-pre-wrap">
          {JSON.stringify(proposal.definition, null, 2)}
        </pre>
      </details>
      {error && (
        <p role="alert" className="text-sm text-critical-text">
          {error}
        </p>
      )}
      {proposal.status === "proposed" && (
        <div className="flex flex-wrap gap-2">
          <button
            className="br-btn br-btn-primary"
            disabled={busy}
            onClick={() => act(() => api.approveProposal(tenant, id, null))}
          >
            {t("Confirm")}
          </button>
          {/* A proposal that can never succeed — a reused retry key, a revision
              that moved on — has to be dismissible, or it sits in every chat
              the reader opens with no way out. Every other proposal card in the
              application already had this button; this one did not. */}
          <button
            className="br-btn"
            disabled={busy}
            onClick={() => act(() => api.rejectProposal(tenant, id, null))}
          >
            {t("Reject")}
          </button>
        </div>
      )}
    </section>
  );
}
