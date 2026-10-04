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
    ...(Array.isArray(input.retry_acknowledgements) && input.retry_acknowledgements.length
      ? { retry_acknowledgements: input.retry_acknowledgements }
      : {}),
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
  initialSourceId,
}: {
  tenant: string;
  proposalId?: string;
  decisionStatus?: string;
  initialSourceId?: string;
}) {
  const [sourceId, setSourceId] = useState<string | undefined>(initialSourceId);
  const [executionId, setExecutionId] = useState<string>();
  const history = useRead(
    () =>
      api.emailHistory(
        tenant,
        sourceId
          ? { source_id: sourceId }
          : executionId
            ? { execution_id: executionId }
            : { proposal_id: proposalId! },
      ),
    [tenant, proposalId, sourceId, executionId, decisionStatus, initialSourceId],
  );
  const data = history.data;
  if (!data)
    return <ReadState loading={history.loading} error={history.error} retry={history.refresh} />;
  const sources = data.source ? [data.source] : data.supporting_sources;
  return (
    <section className="mt-4 space-y-3" data-email-evidence>
      <h4 className="font-semibold">{t("Email evidence history")}</h4>
      {data.authorization === "external_unverified" && (
        <p data-email-external-authorization>
          {t("Externally sent; no Reality approval is documented.")}
        </p>
      )}
      {data.decision?.duplicate_send_risk && (
        <p role="alert" data-email-retry-risk>
          {t("A previous send remains uncertain. Sending again may deliver this email twice.")}
        </p>
      )}
      {data.state && outcomeLabels[data.state] && (
        <p data-email-outcome>{t(outcomeLabels[data.state])}</p>
      )}
      <p className="text-sm text-fg-muted">
        {t(
          "The external agent sends the email after approval. Provider acceptance does not verify recipient delivery.",
        )}
      </p>
      {(data.decision?.retry_acknowledgements || []).map((ack) => (
        <button
          key={ack.execution_id}
          className="br-btn"
          data-email-prior-execution
          onClick={() => {
            setSourceId(undefined);
            setExecutionId(ack.execution_id);
          }}
        >
          {t("Open previous execution evidence")}
        </button>
      ))}
      {(data.business_references || []).length > 0 && (
        <div data-email-business-context>
          <h5 className="font-medium">{t("Business context")}</h5>
          {(data.business_references || []).map((reference) => (
            <a
              key={`${reference.kind}:${reference.id}`}
              className="block text-accent underline"
              data-original-content
              href={`/app/inspector?${new URLSearchParams({ tenant, inspector_view: "facts", inspector_target_kind: reference.kind, inspector_target_id: reference.id })}`}
            >
              {reference.label}
            </a>
          ))}
        </div>
      )}
      {data.context_missing && (
        <p className="text-sm text-fg-muted">
          {t(
            "This historical email has no verified business context. Capture a new version with existing business references.",
          )}
        </p>
      )}
      {(data.related_decisions || []).map((decision) => (
        <a
          key={decision.proposal_id}
          className="block text-accent underline"
          href={`/app/decisions?${new URLSearchParams({ tenant, proposal: decision.proposal_id })}`}
        >
          {t("Open decision")}
        </a>
      ))}
      {((sourceId && proposalId) || executionId) && (
        <button
          className="br-btn"
          onClick={() => {
            setSourceId(initialSourceId);
            setExecutionId(undefined);
          }}
        >
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
