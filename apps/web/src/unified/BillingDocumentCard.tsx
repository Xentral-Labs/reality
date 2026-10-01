import { useEffect, useRef, useState } from "react";
import { formatMoney, t } from "../localization";

// Spec 299: a down-payment invoice (posted, settled by ordinary payments, counted
// towards prepayment) or a pro-forma (evidence only) for a sales order. The shared
// reviewed tools record them; this dialog states, reviews and confirms.

export type BillingDocumentTool = "down_payment_invoice_record" | "proforma_invoice_record";
type Review = {
  token: string;
  state: {
    order_number: string;
    currency: string;
    order_gross?: string;
    number: string;
    gross_amount: string;
    earlier_down_payments?: { document_id: string; number: string; gross: string; paid: string }[];
  };
};
type Prepared = { id: string; review: Review };

async function call<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(typeof data.detail === "string" ? data.detail : t("Request failed"));
  return data;
}

const titles: Record<BillingDocumentTool, string> = {
  down_payment_invoice_record: "Down-payment invoice",
  proforma_invoice_record: "Pro-forma invoice",
};

export function BillingDocumentCard({
  tenant,
  order,
  tool,
  close,
  settled,
}: {
  tenant: string;
  order: string;
  tool: BillingDocumentTool;
  close: () => void;
  settled: () => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenant)}`;
  const dialog = useRef<HTMLDialogElement>(null);
  const request = useRef(crypto.randomUUID());
  const [number, setNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [prepared, setPrepared] = useState<Prepared | null>(null);
  const [done, setDone] = useState(false);
  const proforma = tool === "proforma_invoice_record";

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
    setBusy(true);
    setError("");
    try {
      const stated = { order_id: order, number: number.trim(), gross_amount: amount.trim() };
      setPrepared(
        await call<Prepared>(`${base}/delivery-actions/prepare`, {
          tool,
          request_id: request.current,
          arguments: proforma
            ? { ...stated, ...(date ? { document_date: date } : {}) }
            : { ...stated, ...(date ? { effective_at: `${date}T12:00:00Z` } : {}) },
        }),
      );
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!prepared || busy) return;
    setBusy(true);
    setError("");
    try {
      await call(`${base}/change-proposals/${prepared.id}/approve`, {
        confirmed: true,
        review_token: prepared.review.token,
      });
      setDone(true);
      settled();
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }

  const state = prepared?.review.state;
  return (
    <dialog
      ref={dialog}
      aria-label={t(titles[tool])}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
      className="m-auto max-h-[90vh] w-[min(640px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <div className="mb-5 flex justify-between gap-3">
        <h2 className="text-lg font-semibold">{t(titles[tool])}</h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      {error && (
        <div role="alert" className="mb-4 text-red-600">
          {error}
        </div>
      )}
      {done ? (
        <div role="status" className="rounded-lg bg-positive-surface p-4 font-medium">
          {proforma
            ? t("The pro-forma invoice is recorded; it posts nothing.")
            : t("The down-payment invoice is recorded and open for payment.")}
        </div>
      ) : state ? (
        <>
          <div className="mb-3">
            {state.number} · {t("for order")} {state.order_number} ·{" "}
            {formatMoney(state.gross_amount, state.currency)}
          </div>
          {state.order_gross && (
            <div className="mb-3 text-sm text-fg-muted">
              {t("Order value")} {formatMoney(state.order_gross, state.currency)}
            </div>
          )}
          {!!state.earlier_down_payments?.length && (
            <ul className="mb-3 text-sm">
              {state.earlier_down_payments.map((row) => (
                <li key={row.document_id}>
                  {t("Earlier down payment")} {row.number}: {formatMoney(row.gross, state.currency)}{" "}
                  · {t("paid")} {formatMoney(row.paid, state.currency)}
                </li>
              ))}
            </ul>
          )}
          <div className="mb-4 text-sm text-fg-muted">
            {proforma
              ? t("A pro-forma posts nothing, is no open item and bills no quantity.")
              : t(
                  "It bills no quantity of the order; once paid it counts towards prepayment and can be offset in the final invoice.",
                )}
          </div>
          <div className="flex gap-2">
            <button className="br-btn" disabled={busy} onClick={() => void confirm()}>
              {t("Confirm")}
            </button>
            <button className="br-btn" disabled={busy} onClick={() => setPrepared(null)}>
              {t("Edit")}
            </button>
          </div>
        </>
      ) : (
        <form className="grid gap-4" onSubmit={prepare}>
          <label>
            {t("Invoice number")}
            <input
              className="br-control mt-1 w-full"
              value={number}
              onChange={(event) => {
                setNumber(event.target.value);
                request.current = crypto.randomUUID();
              }}
              required
            />
          </label>
          <label>
            {t("Gross amount")}
            <input
              className="br-control mt-1 w-full"
              inputMode="decimal"
              value={amount}
              onChange={(event) => {
                setAmount(event.target.value);
                request.current = crypto.randomUUID();
              }}
              required
            />
          </label>
          <label>
            {t("Date")}
            <input
              type="date"
              className="br-control mt-1 w-full"
              value={date}
              onChange={(event) => {
                setDate(event.target.value);
                request.current = crypto.randomUUID();
              }}
            />
          </label>
          <button className="br-btn self-start" disabled={busy || !number.trim() || !amount.trim()}>
            {t("Review")}
          </button>
        </form>
      )}
    </dialog>
  );
}
