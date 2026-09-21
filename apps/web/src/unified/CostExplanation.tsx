import { type ReactNode } from "react";
import { api, type CostQueryEnvelope } from "../api";
import { formatDateTime, formatExactDecimal, formatMoney, t } from "../localization";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

const text = (value: unknown) => (typeof value === "string" ? value : null);
const list = (value: unknown) => (Array.isArray(value) ? value.map(String) : []);

export function CostExplanationFrame({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section
      className="my-3 space-y-3 rounded-xl border border-border-default bg-surface-muted p-4"
      aria-label={title}
    >
      {children}
    </section>
  );
}

export function CostExplanation({
  tenant,
  kind,
  scopeId,
}: {
  tenant: string;
  kind: "inventory" | "contribution";
  scopeId: string;
}) {
  const read = useRead(() => api.costQuery(tenant, kind, scopeId), [tenant, kind, scopeId]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return <CostExplanationResult tenant={tenant} envelope={read.data} />;
}

export function CostExplanationResult({
  tenant,
  envelope,
}: {
  tenant: string;
  envelope: CostQueryEnvelope;
}) {
  const { freshness, resolved } = envelope;
  const current = envelope.result;
  const basis = envelope.basis_result || {};
  const shown = current || basis;
  const currency = resolved?.currency || text(shown.currency) || "EUR";
  const contribution = envelope.requested.kind === "contribution";
  const missing = list(shown.missing_basis);
  const money = (value: unknown) =>
    text(value) ? (
      <>
        <span>{formatMoney(text(value)!, currency)}</span>
        <small className="mt-1 block text-fg-muted">
          {t("Exact retained value")}: {formatExactDecimal(text(value)!, true)}
        </small>
      </>
    ) : (
      <span className="text-fg-muted">{t("Not evidenced")}</span>
    );
  const trace = (shown.trace || {}) as Record<string, unknown>;
  const consumed = text((trace.consumption as Record<string, unknown> | undefined)?.cost);
  const reviewKind = contribution ? "cost_contribution_review" : "cost_inventory_review";
  const reviewId = text(shown.review_id);
  const inspector = (targetKind: string, id: string) =>
    `/app/inspector?${new URLSearchParams({
      tenant,
      inspector_view: "records",
      inspector_target_kind: targetKind,
      inspector_target_id: id,
    })}`;

  return (
    <CostExplanationFrame title={t("Cost explanation")}>
      <div>
        <h3>{t(contribution ? "Contribution explanation" : "Inventory cost explanation")}</h3>
        <p className="text-sm text-fg-muted">
          {t(
            "Calculated by the shared retained cost service; this view records no financial authority.",
          )}
        </p>
      </div>
      {freshness.state === "stale" && (
        <p role="status" className="text-sm text-warning">
          {t("Retained basis — not current")}.{" "}
          {t("Newer business evidence exists; current values remain unavailable until reviewed.")}
        </p>
      )}
      {freshness.state === "uninitialized" && (
        <p role="status">{t("No reviewed cost basis exists for this scope.")}</p>
      )}
      <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {contribution ? (
          <>
            <div>
              <dt>{t("Received net revenue")}</dt>
              <dd>{money(trace.received_net)}</dd>
            </div>
            <div>
              <dt>{t("Consumed acquisition cost")}</dt>
              <dd>{money(consumed)}</dd>
            </div>
            <div>
              <dt>{t("DB1")}</dt>
              <dd>{money(shown.db1 ?? shown.basis_db1)}</dd>
            </div>
            <div>
              <dt>{t("Reviewed selling costs")}</dt>
              <dd>{money(shown.known_selling_cost)}</dd>
            </div>
            <div>
              <dt>{t("DB2")}</dt>
              <dd>{money(shown.db2 ?? shown.basis_db2)}</dd>
            </div>
          </>
        ) : (
          <>
            <div>
              <dt>{t("Acquisition value")}</dt>
              <dd>{money(shown.acquisition_value ?? shown.basis_acquisition_value)}</dd>
            </div>
            <div>
              <dt>{t("Carrying value")}</dt>
              <dd>{money(current?.carrying_value)}</dd>
            </div>
            <div>
              <dt>{t("Unit cost")}</dt>
              <dd>{text(shown.unit_cost) || t("Not evidenced")}</dd>
            </div>
          </>
        )}
        {resolved && (
          <>
            <div>
              <dt>{t("Valuation cutoff")}</dt>
              <dd>{formatDateTime(resolved.effective_at)}</dd>
            </div>
            <div>
              <dt>{t("Knowledge cutoff")}</dt>
              <dd>{formatDateTime(resolved.knowledge_at)}</dd>
            </div>
          </>
        )}
      </dl>
      {missing.length > 0 && (
        <div>
          <strong>{t("Missing basis")}</strong>
          <ul className="list-disc pl-5">
            {missing.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </div>
      )}
      {reviewId && (
        <a className="br-btn inline-flex" href={inspector(reviewKind, reviewId)}>
          {t("Inspect cost basis")}
        </a>
      )}
    </CostExplanationFrame>
  );
}
