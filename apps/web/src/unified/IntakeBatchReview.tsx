import { useEffect, useRef, useState } from "react";
import { CompletenessIssues } from "./CompletenessIssues";
import { api, intakeBatches, itemImports } from "../api";
import { formatNumber, t } from "../localization";
import { BusinessFieldList, TechnicalDetails } from "./DecisionReview";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

export const profileLabels: Record<string, string> = {
  "shopify.order": "Sales order",
  "shopify.order_change": "Order changes",
  "shopify.refund": "Refund",
  "item_csv.v1": "Items",
  "artifact:item.v1": "Items",
  "artifact:party.v1": "Business partners",
  "artifact:location.v1": "Locations",
  "artifact:sales_order.v1": "Sales order",
  "artifact:inventory_snapshot.v1": "Stock count",
  "artifact:external_stock.v1": "External stock",
  "artifact:bank_statement.v1": "Bank statement",
  "customer_payment.v1": "Customer payment",
  "supplier_payment.v1": "Supplier payment",
  "sales_invoice.v1": "Sales invoice",
};
const dispositionLabels: Record<string, string> = {
  applied: "Applied",
  replayed: "Previously applied",
  rejected: "Rejected",
  review_required: "Review required",
  stopped: "Stopped",
  waiting: "Waiting",
};

export function IntakeMeaning({
  plan,
  fallback,
}: {
  plan?: Record<string, unknown>;
  fallback: Record<string, unknown>;
}) {
  const effects = plan?.effects as
    Array<{ operation: string; arguments: Record<string, unknown> }> | undefined;
  const labels: Record<string, string> = {
    document: t("Document"),
    commitment: t("Delivery commitment"),
    commitment_revision: t("Revise commitment"),
    commitment_cancellation: t("Cancel commitment remainder"),
    master_item: t("Create item"),
    master_party: t("Create party"),
    master_location: t("Create location"),
    customer_payment: t("Record customer payment"),
    supplier_payment: t("Record supplier payment"),
    invoice_post: t("Post invoice"),
    payment_allocation: t("Payment allocation"),
    credit_hold: t("Credit hold"),
    inventory_adjustment: t("Stock adjustment"),
    external_stock_statement: t("External stock"),
  };
  const issues = (plan?.issues ?? []) as string[];
  return (
    <div data-intake-meaning>
      <h3 className="font-semibold">{t("Prepared preview")}</h3>
      {effects ? (
        effects.map((effect, index) => (
          <section key={index} className="mt-3">
            <h4 className="font-medium">{labels[effect.operation] || effect.operation}</h4>
            <BusinessFieldList record={effect.arguments} />
          </section>
        ))
      ) : (
        <BusinessFieldList record={fallback} />
      )}
      <CompletenessIssues issues={issues} />
    </div>
  );
}

export function SourceMeaning({
  tenant,
  id,
  renewable,
  prepared,
}: {
  tenant: string;
  id: string;
  renewable: boolean;
  prepared?: (id: string) => void;
}) {
  const requestId = useRef(crypto.randomUUID());
  const [renewing, setRenewing] = useState(false);
  const [error, setError] = useState("");
  const detail = useRead(() => api.proposalReview(tenant, id), [tenant, id]);
  if (!detail.data)
    return <ReadState loading={detail.loading} error={detail.error} retry={detail.refresh} />;
  const plan = detail.data.input.plan as Record<string, unknown> | undefined;
  const references = (plan?.references ?? []) as Array<{ record_type: string; record_id: string }>;
  const artifacts = references.filter((reference) => reference.record_type === "source_artifact");
  const renew = async () => {
    if (typeof plan?.import_job_id !== "string" || !prepared) return;
    setRenewing(true);
    setError("");
    try {
      const fresh = await intakeBatches.renew(tenant, id, plan.import_job_id, requestId.current);
      prepared(fresh.id);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setRenewing(false);
    }
  };
  return (
    <div className="mt-3 space-y-3 rounded-lg bg-surface-muted p-4" data-source-meaning>
      <IntakeMeaning plan={plan} fallback={detail.data.input} />
      <a className="br-btn" href={intakeBatches.original(tenant, id)}>
        {t("Download original source")}
      </a>
      {artifacts.map((artifact) => (
        <a
          key={artifact.record_id}
          className="br-btn ml-2"
          href={itemImports.original(tenant, artifact.record_id)}
        >
          {t("Download original file")}
        </a>
      ))}
      {renewable && prepared && (
        <button className="br-btn" disabled={renewing} onClick={() => void renew()}>
          {t("Prepare fresh source review")}
        </button>
      )}
      {error && (
        <p role="alert" className="text-critical-text">
          {error}
        </p>
      )}
      <TechnicalDetails value={detail.data.input} />
    </div>
  );
}

export function IntakeBatchReview({
  tenant,
  id,
  decisionStatus,
  prepared,
}: {
  tenant: string;
  id: string;
  decisionStatus: string;
  prepared?: (id: string) => void;
}) {
  const [cursor, setCursor] = useState(0);
  const [opened, setOpened] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [stopping, setStopping] = useState(false);
  const data = useRead(
    async () => ({
      cursor,
      review: await intakeBatches.review(tenant, id, cursor),
      progress: await intakeBatches.status(tenant, id, cursor),
    }),
    [tenant, id, cursor, decisionStatus],
  );
  const active = data.data?.progress.status === "executing";
  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(data.refresh, 5000);
    return () => window.clearInterval(timer);
  }, [active, tenant, id, cursor]);
  if (!data.data || data.data.cursor !== cursor)
    return <ReadState loading={data.loading} error={data.error} retry={data.refresh} />;
  const { review, progress } = data.data;
  const stop = async () => {
    setStopping(true);
    setError("");
    try {
      await intakeBatches.stop(tenant, id);
      await data.refresh();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setStopping(false);
    }
  };
  return (
    <section className="mt-5 space-y-3" data-intake-batch-review aria-busy={data.loading}>
      <h3 className="font-semibold">
        {t("Selected source decisions")} · {formatNumber(review.total)}
      </h3>
      <p className="text-sm text-fg-muted">
        {t("Settled source decisions")}: {formatNumber(progress.settled)} /{" "}
        {formatNumber(progress.total)}
      </p>
      <div className="flex flex-wrap gap-3 text-sm">
        {Object.entries(progress.counts).map(([kind, count]) => (
          <span key={kind}>
            {t(dispositionLabels[kind] || kind)}: {formatNumber(count)}
          </span>
        ))}
      </div>
      {progress.status === "proposed" && (
        <p className="text-sm">
          {t(
            "This selection has changed nothing. Confirmation applies each source independently; changed or refused units remain available for review.",
          )}
        </p>
      )}
      {progress.status === "executing" && !progress.stopped && (
        <button className="br-btn" disabled={stopping} onClick={() => void stop()}>
          {t("Stop remaining sources")}
        </button>
      )}
      {progress.stopped && <p>{t("Further source acceptance has been stopped.")}</p>}
      {error && (
        <p role="alert" className="text-critical-text">
          {error}
        </p>
      )}
      {review.entries.map((entry) => {
        const result = progress.results.find((result) => result.proposal_id === entry.proposal_id);
        return (
          <article
            key={entry.proposal_id}
            className="rounded-lg border border-border-default p-3"
            data-intake-member={entry.proposal_id}
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <span>{t(profileLabels[entry.profile] || "Source")}</span> ·{" "}
                {formatNumber(entry.row_count)} {t("Rows")} ·{" "}
                {t(dispositionLabels[result?.disposition || "waiting"] || "Review required")}
              </div>
              <button
                className="br-btn"
                aria-expanded={opened === entry.proposal_id}
                onClick={() => setOpened(opened === entry.proposal_id ? null : entry.proposal_id)}
              >
                {t("Review source meaning")}
              </button>
            </div>
            {!!entry.issues.length && (
              <ul className="mt-2 text-sm text-warning-text" data-original-content>
                {entry.issues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            )}
            {result?.reason_code && (
              <p className="mt-2 text-sm text-fg-muted" data-original-content>
                {result.reason_code}
              </p>
            )}
            {opened === entry.proposal_id && (
              <SourceMeaning
                key={entry.proposal_id}
                tenant={tenant}
                id={entry.proposal_id}
                renewable={result?.disposition === "review_required"}
                prepared={prepared}
              />
            )}
            {result?.receipt && <TechnicalDetails value={result.receipt} />}
          </article>
        );
      })}
      <nav className="flex items-center justify-between gap-3" aria-label={t("Selected sources")}>
        <button
          className="br-btn"
          disabled={cursor === 0}
          onClick={() => {
            setOpened(null);
            setCursor(Math.max(0, cursor - 100));
          }}
        >
          {t("Previous")}
        </button>
        <span className="text-sm">
          {formatNumber(cursor + 1)}–{formatNumber(Math.min(cursor + 100, review.total))} /{" "}
          {formatNumber(review.total)}
        </span>
        <button
          className="br-btn"
          disabled={!review.has_more}
          onClick={() => {
            setOpened(null);
            setCursor(cursor + 100);
          }}
        >
          {t("Next")}
        </button>
      </nav>
      {data.error && <ReadState error={data.error} retry={data.refresh} />}
    </section>
  );
}
