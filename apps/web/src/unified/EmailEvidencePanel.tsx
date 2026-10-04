import { useState } from "react";
import { api } from "../api";
import { t } from "../localization";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

export function emailReviewInput(input: Record<string, unknown>) {
  const message = (input.message || {}) as Record<string, unknown>;
  const transportEvidence = new Set([
    "original_artifact_id",
    "original_filename",
    "external_payload",
    "message_id",
    "thread_id",
    "stated_at",
  ]);
  const fields = Object.entries(message).filter(([key]) => !transportEvidence.has(key));
  return {
    message: Object.fromEntries(
      fields.map(([key, value]) => [
        key,
        key === "attachments" && Array.isArray(value)
          ? value.map((part: Record<string, unknown>) => ({
              filename: part.filename,
              content_type: part.content_type,
              inline: part.inline,
              content_id: part.content_id,
            }))
          : value,
      ]),
    ),
    rationale: input.rationale,
  };
}

const outcomeLabels: Record<string, string> = {
  decision_pending: "Email decision pending",
  decision_rejected: "Email decision rejected",
  decision_failed: "Email decision failed",
  dispatch_authorized: "Email dispatch authorized",
  dispatch_claimed: "Email dispatch claimed",
  execution_uncertain: "Email execution uncertain",
  execution_failed: "Email execution failed",
  provider_accepted: "Email accepted by provider",
  approval_deviation: "Email differs from approved version",
  conflicting_evidence: "Conflicting email execution evidence",
};

export function EmailEvidencePanel({
  tenant,
  proposalId,
  decisionStatus,
}: {
  tenant: string;
  proposalId: string;
  decisionStatus: string;
}) {
  const [sourceId, setSourceId] = useState<string>();
  const history = useRead(
    () =>
      api.emailHistory(tenant, sourceId ? { source_id: sourceId } : { proposal_id: proposalId }),
    [tenant, proposalId, sourceId, decisionStatus],
  );
  const data = history.data;
  if (!data)
    return <ReadState loading={history.loading} error={history.error} retry={history.refresh} />;
  const sources = data.source ? [data.source] : data.supporting_sources;
  return (
    <section className="mt-4 space-y-3" data-email-evidence>
      <h4 className="font-semibold">{t("Email evidence history")}</h4>
      {data.state && outcomeLabels[data.state] && (
        <p data-email-outcome>{t(outcomeLabels[data.state])}</p>
      )}
      <p className="text-sm text-fg-muted">
        {t(
          "The external agent sends the email after approval. Provider acceptance does not verify recipient delivery.",
        )}
      </p>
      {sourceId && (
        <button className="br-btn" onClick={() => setSourceId(undefined)}>
          {t("Return to email decision")}
        </button>
      )}
      {(data.outgoing_files || []).map((file) => (
        <div key={file.part_id}>
          <span data-original-content>{file.filename}</span>{" "}
          <a className="text-accent underline" href={file.download_url}>
            {t("Download original file")}
          </a>
        </div>
      ))}
      {sources.map((source) => (
        <details key={source.id} className="rounded-lg border border-border-default p-3">
          <summary className="cursor-pointer break-all">{source.id}</summary>
          {!sourceId && (
            <button className="br-btn mt-2" onClick={() => setSourceId(source.id)}>
              {t("Open original evidence")}
            </button>
          )}
          <pre
            data-original-content
            className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs"
          >
            {JSON.stringify(source.payload, null, 2)}
          </pre>
        </details>
      ))}
      {data.original_file && (
        <a className="block text-accent underline" href={data.original_file.download_url}>
          {t("Download original file")}
        </a>
      )}
      {data.attachments.map((part) => (
        <div key={part.id}>
          <span data-original-content>{String(part.payload.filename || part.id)}</span>{" "}
          {part.file && (
            <a className="text-accent underline" href={part.file.download_url}>
              {t("Download original file")}
            </a>
          )}
        </div>
      ))}
      {data.reports.map((report) => (
        <details key={report.id} className="rounded-lg border border-border-default p-3">
          <summary className="cursor-pointer">{t("Stored receipt")}</summary>
          {typeof report.payload.actual_source_id === "string" && (
            <button
              className="br-btn mt-2"
              onClick={() => setSourceId(String(report.payload.actual_source_id))}
            >
              {t("Open original evidence")}
            </button>
          )}
          <pre
            data-original-content
            className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs"
          >
            {JSON.stringify(report.payload, null, 2)}
          </pre>
        </details>
      ))}
    </section>
  );
}
