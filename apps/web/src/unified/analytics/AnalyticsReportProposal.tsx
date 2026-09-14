import { analyticsError } from "./errors";
import { useState } from "react";
import { analyticsApi, api } from "../../api";
import { t } from "../../localization";
import { useRead } from "../useCompanyContext";
import { ReadState } from "../ReadState";

export function AnalyticsReportProposal({
  tenant,
  id,
  refresh,
}: {
  tenant: string;
  id: string;
  refresh: () => void;
}) {
  const read = useRead(() => analyticsApi.proposal(tenant, id), [tenant, id]);
  const catalog = useRead(() => analyticsApi.catalog(tenant), [tenant]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  const proposal = read.data;
  const dataset = catalog.data?.datasets.find((d) => d.key === proposal.definition.dataset);
  return (
    <section className="space-y-3 rounded-xl border border-border-default bg-surface p-4">
      <h3 className="font-semibold">
        {t("Change private report")}: {proposal.name}
      </h3>
      <p className="text-sm">
        {t(
          (
            {
              create: "Create",
              update: "Update",
              rename: "Rename",
              duplicate: "Duplicate",
              delete: "Delete",
            } as Record<string, string>
          )[proposal.operation],
        )}{" "}
        · {t(dataset?.label || proposal.definition.dataset)}
      </p>
      <p className="text-sm">
        {proposal.definition.measures
          .map((key) => t(dataset?.measures.find((m) => m.key === key)?.label || key))
          .join(" · ")}
      </p>
      <details className="text-xs">
        <summary>{t("Analysis settings")}</summary>
        <pre className="mt-2 overflow-auto whitespace-pre-wrap">
          {JSON.stringify(proposal.definition, null, 2)}
        </pre>
      </details>
      {error && (
        <p role="alert" className="text-sm text-negative-text">
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
