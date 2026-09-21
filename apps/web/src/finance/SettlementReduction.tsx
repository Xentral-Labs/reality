import { useEffect, useRef, useState } from "react";
import { formatMoney, t } from "../localization";
import { useRead } from "../unified/useCompanyContext";
import { ReadState } from "../unified/ReadState";

type Context = {
  invoice_id: string;
  number: string;
  side: "customer" | "supplier";
  currency: string;
  open: string;
  revision: number;
  control_account_code: string;
  counterpart: { state: string } | null;
};
type Review = Context & {
  amount: string;
  remaining: string;
  cash_change: string;
  counterpart_account_code: string;
  reason: string;
  agreement: string;
};
type Pending = { id: string; preview: { adjustment: Review } };
async function call<T>(url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { method: "POST", body: JSON.stringify(body) }),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(typeof data.detail === "string" ? data.detail : t("Request failed"));
  return data;
}
export function SettlementReduction({
  tenant,
  invoice,
  close,
}: {
  tenant: string;
  invoice: string;
  close: () => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenant)}`;
  const storageKey = `reality:reduction:${tenant}:${invoice}`;
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState<Pending | null>(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem(storageKey) || "null");
      return typeof saved?.id === "string" && saved?.preview?.adjustment?.invoice_id === invoice
        ? saved
        : null;
    } catch {
      return null;
    }
  });
  const read = useRead<Context>(
    () => call(`${base}/finance/adjustments/context/${encodeURIComponent(invoice)}`),
    [tenant, invoice],
  );
  useEffect(() => {
    const node = dialog.current;
    const previous = document.activeElement as HTMLElement;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, []);
  const data = read.data;
  async function prepare(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!data || busy) return;
    const fields = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const proposal = await call<Pending>(`${base}/finance/adjustments/proposals`, {
        tool: "finance.adjustment.accept",
        arguments: {
          invoice_id: invoice,
          expected_revision: data.revision,
          amount: fields.get("amount"),
          reason_category: fields.get("category"),
          reason: fields.get("reason"),
          agreement: fields.get("agreement") || "",
          source_record_id: fields.get("source") || null,
          source_effect_id: fields.get("effect") || null,
        },
      });
      setPending(proposal);
      sessionStorage.setItem(storageKey, JSON.stringify(proposal));
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }
  async function decide(approve: boolean) {
    if (!pending || busy) return;
    setBusy(true);
    setError("");
    try {
      await call(`${base}/change-proposals/${pending.id}/${approve ? "approve" : "reject"}`, {});
      sessionStorage.removeItem(storageKey);
      setPending(null);
      if (approve) {
        window.dispatchEvent(new Event("reality:delivery-settled"));
        close();
      } else read.refresh();
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }
  const review = pending?.preview.adjustment;
  return (
    <dialog
      ref={dialog}
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) close();
      }}
      className="m-auto max-h-[90vh] w-[min(680px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <div className="mb-5 flex justify-between gap-3">
        <h2 className="text-lg font-semibold">{t("Accept settlement reduction")}</h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      <p className="mb-4 text-sm text-fg-muted">
        {t("Record an agreed reduction separately from actual payment.")}
      </p>
      {error && (
        <p role="alert" className="mb-4 text-red-600">
          {error}
        </p>
      )}
      {review ? (
        <>
          <p className="mb-4 font-medium">{review.number}</p>
          <dl className="mb-4 grid grid-cols-2 gap-3">
            {[
              ["Open amount", review.open],
              ["Accepted reduction", review.amount],
              ["Remaining claim", review.remaining],
              ["Cash change", review.cash_change],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs text-fg-muted">{t(label)}</dt>
                <dd>{formatMoney(value, review.currency)}</dd>
              </div>
            ))}
          </dl>
          <p className="mb-2 text-sm">
            {review.control_account_code} → {review.counterpart_account_code}
          </p>
          <p className="mb-2 whitespace-pre-wrap">{review.reason}</p>
          {review.agreement && <p className="mb-4 whitespace-pre-wrap">{review.agreement}</p>}
          <div className="flex flex-wrap gap-2">
            <button className="br-btn" disabled={busy} onClick={() => void decide(true)}>
              {t("Confirm reduction")}
            </button>
            <button className="br-btn" disabled={busy} onClick={() => void decide(false)}>
              {t("Reject")}
            </button>
          </div>
        </>
      ) : !data ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={4} />
      ) : (
        <>
          <p className="mb-4">
            {data.number} · {t("Open amount")}: {formatMoney(data.open, data.currency)}
          </p>
          {!data.counterpart || data.counterpart.state !== "active" ? (
            <p>
              {t("Configure an active reduction counterpart in company account settings first.")}
            </p>
          ) : (
            <form onSubmit={prepare} className="grid gap-4">
              <label>
                {t("Stated reduction amount")}
                <input
                  className="br-control mt-1 w-full"
                  name="amount"
                  inputMode="decimal"
                  required
                />
              </label>
              <label>
                {t("Reduction reason")}
                <select className="br-control mt-1 w-full" name="category">
                  <option value="early_payment_discount">{t("Early-payment discount")}</option>
                  <option value="agreed_deduction">{t("Agreed deduction")}</option>
                  <option value="accepted_small_remainder">{t("Accepted small remainder")}</option>
                  {data.side === "customer" && <option value="bad_debt">{t("Bad debt")}</option>}
                </select>
              </label>
              <label>
                {t("Explanation")}
                <textarea className="br-control mt-1 w-full" name="reason" required />
              </label>
              {data.side === "supplier" && (
                <label>
                  {t("Supplier entitlement or agreement")}
                  <textarea className="br-control mt-1 w-full" name="agreement" required />
                </label>
              )}
              <details>
                <summary>{t("External evidence (optional)")}</summary>
                <label>
                  {t("Source record ID")}
                  <input className="br-control mt-1 w-full" name="source" />
                </label>
                <label>
                  {t("Source effect reference")}
                  <input className="br-control mt-1 w-full" name="effect" />
                </label>
              </details>
              <div className="flex gap-2">
                <button className="br-btn" disabled={busy || read.loading}>
                  {t("Review reduction")}
                </button>
                <button type="button" className="br-btn" disabled={busy} onClick={read.refresh}>
                  {t("Reload")}
                </button>
              </div>
            </form>
          )}
        </>
      )}
    </dialog>
  );
}
