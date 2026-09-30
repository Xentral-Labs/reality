import { useEffect, useRef, useState } from "react";
import { formatMoney, t } from "../localization";

// Spec 297: a customer payment that came back. The shared finance command reverses
// the payment and books the stated fee; this dialog only states, reviews and confirms.

type Reopened = { invoice_id: string; number: string; allocated: string; open_after: string };
type Review = {
  payment_number: string;
  currency: string;
  amount: string;
  kind: string;
  fee_amount: string;
  fee_bearer: string;
  reopened: Reopened[];
};
type Pending = { id: string; preview: { payment_return: Review } };

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

function localToday(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

export function PaymentReturn({
  tenant,
  payment,
  close,
}: {
  tenant: string;
  payment: string;
  close: () => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenant)}`;
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [fee, setFee] = useState("0");
  const [pending, setPending] = useState<Pending | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const node = dialog.current;
    const previous = document.activeElement as HTMLElement;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, []);

  async function prepare(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const fields = new FormData(event.currentTarget);
    const stated = String(fields.get("fee") || "0");
    setBusy(true);
    setError("");
    try {
      setPending(
        await call<Pending>(`${base}/finance/commercial/proposals`, {
          tool: "finance.payment.return",
          arguments: {
            payment_document_id: payment,
            kind: fields.get("kind"),
            returned_on: fields.get("date"),
            reason: fields.get("reason") || "",
            reference: fields.get("reference") || "",
            fee_amount: stated,
            fee_bearer: Number(stated) > 0 ? fields.get("bearer") : "none",
          },
        }),
      );
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
      if (!approve) return close();
      window.dispatchEvent(new Event("reality:delivery-settled"));
      setDone(true);
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }

  const review = pending?.preview.payment_return;
  return (
    <dialog
      ref={dialog}
      aria-label={t("Payment returned")}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
      className="m-auto max-h-[90vh] w-[min(640px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <div className="mb-5 flex justify-between gap-3">
        <h2 className="text-lg font-semibold">{t("Payment returned")}</h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      {error && <p className="mb-4 text-red-600">{error}</p>}
      {done ? (
        <p role="status" className="rounded-lg bg-positive-surface p-4 font-medium">
          {t("The payment is recorded as returned; its invoices are open again.")}
        </p>
      ) : review ? (
        <>
          <p className="mb-3">
            {review.payment_number} · {formatMoney(review.amount, review.currency)} ·{" "}
            {t(review.kind === "chargeback" ? "Chargeback" : "Returned direct debit")}
          </p>
          <h3 className="mb-2 font-semibold">{t("Open again")}</h3>
          <ul className="mb-4 text-sm">
            {review.reopened.map((row) => (
              <li key={row.invoice_id}>
                {row.number}: {formatMoney(row.open_after, review.currency)}
              </li>
            ))}
          </ul>
          {Number(review.fee_amount) > 0 && (
            <p className="mb-4 text-sm">
              {t("Fee")}: {formatMoney(review.fee_amount, review.currency)} ·{" "}
              {t(
                review.fee_bearer === "customer"
                  ? "charged on to the customer"
                  : "kept as payment-fee expense",
              )}
            </p>
          )}
          <p className="mb-4 text-sm text-fg-muted">
            {t("An authenticated company owner must approve or reject this finance proposal.")}
          </p>
          <div className="flex gap-2">
            <button className="br-btn" disabled={busy} onClick={() => void decide(true)}>
              {t("Confirm")}
            </button>
            <button className="br-btn" disabled={busy} onClick={() => void decide(false)}>
              {t("Reject")}
            </button>
          </div>
        </>
      ) : (
        <form className="grid gap-4" onSubmit={prepare}>
          <label>
            {t("Kind")}
            <select
              className="br-control mt-1 w-full"
              name="kind"
              defaultValue="direct_debit_return"
            >
              <option value="direct_debit_return">{t("Returned direct debit")}</option>
              <option value="chargeback">{t("Chargeback")}</option>
            </select>
          </label>
          <label>
            {t("Return date")}
            <input
              className="br-control mt-1 w-full"
              name="date"
              type="date"
              defaultValue={localToday()}
              required
            />
          </label>
          <label>
            {t("Reason")}
            <input className="br-control mt-1 w-full" name="reason" required />
          </label>
          <label>
            {t("Bank or provider reference")}
            <input className="br-control mt-1 w-full" name="reference" />
          </label>
          <label>
            {t("Fee")}
            <input
              className="br-control mt-1 w-full"
              name="fee"
              inputMode="decimal"
              value={fee}
              onChange={(event) => setFee(event.target.value)}
            />
          </label>
          {Number(fee) > 0 && (
            <label>
              {t("Who bears the fee")}
              <select className="br-control mt-1 w-full" name="bearer" defaultValue="customer">
                <option value="customer">{t("Charge on to the customer")}</option>
                <option value="company">{t("Keep as payment-fee expense")}</option>
              </select>
            </label>
          )}
          <button className="br-btn self-start" disabled={busy}>
            {t("Review return")}
          </button>
        </form>
      )}
    </dialog>
  );
}
