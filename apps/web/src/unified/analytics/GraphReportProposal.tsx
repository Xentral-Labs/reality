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
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
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
        <button
          className="br-btn br-btn-primary"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              await api.approveProposal(tenant, id, null);
              read.refresh();
              refresh();
            } catch (failure) {
              setError(analyticsError(failure));
            } finally {
              setBusy(false);
            }
          }}
        >
          {t("Confirm")}
        </button>
      )}
    </section>
  );
}
