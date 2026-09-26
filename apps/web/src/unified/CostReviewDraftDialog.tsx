import { useEffect, useRef, useState } from "react";
import {
  APIError,
  api,
  recordsChanged,
  type CostReviewAnswers,
  type CostReviewDraft,
} from "../api";
import { formatMoney, formatQuantity, t } from "../localization";
import { useActionDiscovery } from "./ActionLauncher";
import { reasonText } from "./guidanceActions";
import { ReadState } from "./ReadState";

const movementLabels: Record<string, string> = {
  receipt: "Receipts",
  opening_stock: "Opening stock",
  shipment: "Goods issues",
  return: "Customer returns",
  supplier_return: "Supplier returns",
  adjustment: "Stock adjustments",
  transfer: "Transfers",
};
const methodLabels: Record<string, string> = {
  fifo: "FIFO (first in, first out)",
  specific: "Specific selection",
};
const text = (value: unknown) => (typeof value === "string" && value ? value : null);

/**
 * Spec 282: shows the review Reality drafted from held records, asks only the open
 * inputs, and proposes exactly the drafted decision. The server re-drafts on submit, so
 * the browser never assembles review arguments; a company owner confirms in Decisions.
 */
export function CostReviewDraftDialog({
  tenant,
  kind,
  scopeId,
  close,
}: {
  tenant: string;
  kind: "inventory" | "contribution";
  scopeId: string;
  close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const catalog = useActionDiscovery()?.data?.resolution_guidance;
  const [answers, setAnswers] = useState<CostReviewAnswers>({});
  const [draft, setDraft] = useState<CostReviewDraft | null>(null);
  const [error, setError] = useState<string>();
  const [changed, setChanged] = useState(false);
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const element = dialog.current!;
    element.showModal();
    return () => element.close();
  }, []);
  useEffect(() => {
    let current = true;
    setError(undefined);
    api
      .costReviewDraft(tenant, kind, scopeId, answers)
      .then((value) => {
        if (!current) return;
        setDraft(value);
        // Preselect the draft's default, which the person confirms by submitting.
        const method = value.open_inputs.find((entry) => entry.code === "valuation_method");
        if (method?.default && !answers.method)
          setAnswers((previous) => ({ ...previous, method: method.default }));
      })
      .catch((reason) => current && setError(String(reason.message || reason)));
    return () => {
      current = false;
    };
  }, [tenant, kind, scopeId, answers, revision]);
  const summary = draft?.summary || {};
  const currency = text(summary.currency) || "EUR";
  const money = (value: unknown) => (text(value) ? formatMoney(text(value)!, currency) : "—");
  const blocking = (draft?.open_inputs || []).filter(
    (entry) =>
      !(entry.code === "valuation_method" && answers.method) &&
      !(entry.code === "company_party_missing" && answers.owner_party_id),
  );
  const submit = async () => {
    if (!draft) return;
    setBusy(true);
    setChanged(false);
    try {
      await api.proposeCostReview(tenant, {
        kind,
        scope_id: scopeId,
        event_sequence: draft.event_sequence,
        answers,
      });
      window.dispatchEvent(new Event(recordsChanged));
      close();
    } catch (reason) {
      if (reason instanceof APIError && reason.code === "draft_changed") {
        setChanged(true);
        setRevision((value) => value + 1);
      } else setError(String((reason as Error).message || reason));
    } finally {
      setBusy(false);
    }
  };
  return (
    <dialog
      ref={dialog}
      data-cost-review-draft={kind}
      aria-labelledby="cost-review-draft-title"
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(680px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 id="cost-review-draft-title" className="text-xl font-semibold text-fg-strong">
            {t(
              kind === "inventory"
                ? "Prepare the item's cost review"
                : "Prepare the contribution review",
            )}
          </h2>
          <p className="mt-1 text-sm text-fg-muted">
            {t(
              "Reality drafted this review from your records. A company owner confirms it afterwards.",
            )}
          </p>
        </div>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      {!draft ? (
        <ReadState loading={!error} error={error} retry={() => setRevision((v) => v + 1)} />
      ) : (
        <div className="space-y-5 text-sm">
          {changed && (
            <p role="status" className="rounded-lg bg-caution-bg p-3 text-caution-text">
              {t("Your records changed meanwhile. The draft was prepared again; please check it.")}
            </p>
          )}
          <dl className="grid gap-3 sm:grid-cols-2" data-draft-summary>
            {kind === "inventory" ? (
              <>
                <div>
                  <dt className="text-xs text-fg-muted">{t("Item")}</dt>
                  <dd>
                    {text(summary.item_name)} · {text(summary.item_sku)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-fg-muted">{t("Owner")}</dt>
                  <dd>{text(summary.owner_name) || "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs text-fg-muted">{t("Currency")}</dt>
                  <dd>{text(summary.currency) || "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs text-fg-muted">{t("Unit")}</dt>
                  <dd>{text(summary.base_unit)}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-xs text-fg-muted">{t("Stock movements covered")}</dt>
                  <dd>
                    {Object.entries((summary.movement_counts as Record<string, number>) || {})
                      .map(([type, count]) => `${count} × ${t(movementLabels[type] || "Other")}`)
                      .join(", ") || "—"}
                  </dd>
                </div>
                {((summary.openings as { amount: string }[]) || []).map((opening, index) => (
                  <div key={index}>
                    <dt className="text-xs text-fg-muted">
                      {t("Opening stock value per evidence")}
                    </dt>
                    <dd>{money(opening.amount)}</dd>
                  </div>
                ))}
              </>
            ) : (
              <>
                <div>
                  <dt className="text-xs text-fg-muted">{t("Quantity")}</dt>
                  <dd>
                    {text(summary.quantity) ? formatQuantity(text(summary.quantity)!) : "—"}{" "}
                    {text(summary.base_unit)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-fg-muted">{t("Received net revenue")}</dt>
                  <dd>{money(summary.received_net)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-fg-muted">{t("Consumed acquisition cost")}</dt>
                  <dd>{money(summary.goods_cost)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-fg-muted">{t("DB1 after confirmation")}</dt>
                  <dd className="font-medium">{money(summary.known_db1)}</dd>
                </div>
              </>
            )}
          </dl>
          {draft.open_inputs.length > 0 && (
            <ul className="space-y-3" aria-label={t("Still needed")} data-draft-open-inputs>
              {draft.open_inputs.map((entry, index) => {
                const reason = reasonText(catalog, entry.code);
                const detail =
                  entry.reason && catalog?.reasons[entry.reason]
                    ? reasonText(catalog, entry.reason).label
                    : null;
                return (
                  <li
                    key={`${entry.code}:${index}`}
                    data-open-input={entry.code}
                    className="rounded-lg border border-border-default p-3"
                  >
                    <div className="font-medium text-fg-strong">{reason.label}</div>
                    <div className="mt-1 text-fg-muted">{reason.explanation}</div>
                    {detail && <div className="mt-1 text-fg-muted">{detail}</div>}
                    {entry.code === "valuation_method" && (
                      <div className="mt-2 flex flex-wrap gap-4" role="radiogroup">
                        {(entry.choices || []).map((choice) => (
                          <label key={choice} className="flex items-center gap-2">
                            <input
                              type="radio"
                              name="valuation-method"
                              checked={answers.method === choice}
                              onChange={() => setAnswers({ ...answers, method: choice })}
                            />
                            {t(methodLabels[choice] || choice)}
                          </label>
                        ))}
                      </div>
                    )}
                    {entry.code === "company_party_missing" && (entry.choices || []).length > 0 && (
                      <select
                        className="br-control mt-2 w-full"
                        aria-label={t("Owner")}
                        value={answers.owner_party_id || ""}
                        onChange={(event) =>
                          setAnswers({ ...answers, owner_party_id: event.target.value })
                        }
                      >
                        <option value="">{t("Select a record")}</option>
                        {(entry.choices || []).map((choice) => (
                          <option key={choice} value={choice}>
                            {(summary.party_names as Record<string, string>)?.[choice] || choice}
                          </option>
                        ))}
                      </select>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
          <details data-draft-system-details>
            <summary className="cursor-pointer text-fg-muted">{t("System details")}</summary>
            <pre
              className="mt-2 max-h-60 overflow-auto whitespace-pre-wrap break-all text-xs"
              data-localization="original"
            >
              {JSON.stringify(
                { arguments: draft.arguments || draft.partial_arguments, basis: draft.basis },
                null,
                2,
              )}
            </pre>
          </details>
          {error && (
            <p role="alert" className="text-critical-text">
              {error}
            </p>
          )}
          <footer className="flex flex-wrap justify-end gap-2">
            <button
              type="button"
              className="br-btn br-btn-primary"
              data-draft-submit
              disabled={busy || blocking.length > 0}
              onClick={submit}
            >
              {t("Propose for confirmation")}
            </button>
          </footer>
        </div>
      )}
    </dialog>
  );
}
