import { useState } from "react";
import { api } from "../api";
import { formatDateTime, t } from "../localization";
import { EmailEvidencePanel } from "./EmailEvidencePanel";
import { ReadState } from "./ReadState";
import { RegisterPager } from "./WarehousePage";
import { useRead } from "./useCompanyContext";

export function ObjectCorrespondencePanel({
  tenant,
  kind,
  id,
}: {
  tenant: string;
  kind: string;
  id: string;
}) {
  const [page, setPage] = useState(1);
  const [decisionPage, setDecisionPage] = useState(1);
  const [sourceId, setSourceId] = useState<string>();
  const read = useRead(
    () => api.emailCorrespondence(tenant, kind, id, page, decisionPage),
    [tenant, kind, id, page, decisionPage],
  );
  const data = read.data;
  return (
    <section className="mt-6 space-y-3" data-object-correspondence>
      <h3 className="font-medium">{t("Linked correspondence")}</h3>
      {sourceId ? (
        <>
          <button className="br-btn" onClick={() => setSourceId(undefined)}>
            {t("Back to linked correspondence")}
          </button>
          <EmailEvidencePanel key={sourceId} tenant={tenant} initialSourceId={sourceId} />
        </>
      ) : !data ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} />
      ) : (
        <div aria-busy={read.loading} className={read.loading ? "opacity-60" : ""}>
          <p className="text-sm text-fg-muted">
            {t("Only emails explicitly linked to this business record are shown.")}
          </p>
          {!data.items.length && (
            <p className="mt-2 text-sm">{t("No linked emails on this page.")}</p>
          )}
          {data.items.map((email) => (
            <button
              key={email.source_id}
              className="block w-full rounded border-b border-border-default py-3 text-left hover:bg-surface-muted"
              onClick={() => setSourceId(email.source_id)}
            >
              <span data-original-content className="block break-words font-medium">
                {email.subject}
              </span>
              <span data-original-content className="block break-words text-sm">
                {email.sender}
              </span>
              {email.authorization === "external_unverified" && (
                <span className="block text-sm" data-email-external-authorization>
                  {t("Externally sent; no Reality approval is documented.")}
                </span>
              )}
              <span className="text-xs text-fg-muted">
                {t(email.direction === "inbound" ? "Incoming email" : "Outgoing email")} ·{" "}
                {t("Recorded")} {formatDateTime(email.received_at)}
              </span>
            </button>
          ))}
          {data.page.total > 0 && <RegisterPager page={data.page} change={setPage} />}
          {data.decision_page.total > 0 && (
            <>
              <h4 className="mt-4 font-medium">{t("Related email decisions")}</h4>
              {data.related_decisions.map((decision) => (
                <a
                  key={decision.proposal_id}
                  className="block py-2 text-accent underline"
                  href={decision.review_url}
                >
                  <span data-original-content>{decision.subject}</span>
                </a>
              ))}
              <RegisterPager page={data.decision_page} change={setDecisionPage} />
            </>
          )}
        </div>
      )}
    </section>
  );
}
