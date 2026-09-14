import { useEffect, useRef, useState, type FormEvent } from "react";
import { formatMoney, formatDateTime, t } from "../localization";
import { useRead } from "../unified/useCompanyContext";
import { ReadState } from "../unified/ReadState";
import { reasonLabel, suggestedInvoices, type InvoiceChoice } from "./settlementCandidates";

type Mode = "payment" | "allocate_credit" | "refund_credit";
type Context = {
  document_id: string;
  number: string;
  kind: "invoice" | "credit";
  side: "customer" | "supplier";
  currency: string;
  open?: string;
  available?: string;
  revision: number;
  control_account_code: string;
  counterpart?: { state: string } | null;
  invoices?: InvoiceChoice[];
  more_invoices?: boolean;
  candidates?: InvoiceChoice[];
};
type Evidence = { document_id: string; source_record_id: string; posting_group_id: string };
type Review = {
  document_id: string;
  number: string;
  mode: Mode;
  currency: string;
  party: string;
  invoice_number: string | null;
  cash_amount: string;
  cash_direction: string;
  allocation_amount: string;
  reduction_amount: string;
  remaining_claim: string | null;
  remaining_credit: string;
  control_account_code: string;
  cash_account_code: string | null;
  reference: string | null;
  effective_at: string | null;
  invoice_id: string | null;
  reduction:
    (Evidence & { reason?: string; agreement?: string; counterpart_account_code?: string }) | null;
  payment?: Evidence | null;
  refund?: Evidence | null;
};
type Pending = { id: string; preview: { settlement: Review } };
async function request<T>(url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { method: "POST", body: JSON.stringify(body) }),
  });
  const result = await response.json();
  if (!response.ok)
    throw new Error(typeof result.detail === "string" ? result.detail : t("Request failed"));
  return result;
}
export function SettlementFlow({
  tenant,
  documentId,
  initialMode,
  close,
  explain,
}: {
  tenant: string;
  documentId: string;
  initialMode: Mode;
  close: () => void;
  explain: (id: string) => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenant)}`;
  const key = `reality:settlement:${tenant}:${documentId}`;
  const dialog = useRef<HTMLDialogElement>(null);
  const [mode, setMode] = useState(initialMode);
  const [query, setQuery] = useState("");
  const [reduce, setReduce] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<Review | null>(null);
  const [pending, setPending] = useState<Pending | null>(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem(key) || "null");
      return typeof saved?.id === "string" && saved?.preview?.settlement?.document_id === documentId
        ? saved
        : null;
    } catch {
      return null;
    }
  });
  const read = useRead<Context>(
    () =>
      request(
        `${base}/finance/settlements/context/${encodeURIComponent(documentId)}?query=${encodeURIComponent(query)}`,
      ),
    [tenant, documentId, query],
  );
  const data = read.data;
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  async function prepare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!data || busy || read.loading) return;
    const fields = new FormData(event.currentTarget);
    const get = (name: string) => String(fields.get(name) || "");
    const values: Record<string, unknown> = {
      mode,
      document_id: documentId,
      expected_revision: data.revision,
      amount: get("amount"),
    };
    if (mode === "allocate_credit") values.invoice_id = get("invoice");
    else
      Object.assign(values, {
        reference: get("reference"),
        effective_at: get("effective"),
        source_record_id: get("source") || null,
        source_effect_id: get("effect") || null,
      });
    if (mode === "payment") {
      values.allocation_amount = get("allocation");
      if (reduce)
        values.reduction = {
          amount: get("reduction"),
          reason_category: get("category"),
          reason: get("reason"),
          agreement: get("agreement"),
        };
    }
    setBusy(true);
    setError("");
    try {
      const proposal = await request<Pending>(`${base}/finance/settlements/proposals`, {
        tool: "finance.settlement.apply",
        arguments: values,
      });
      setPending(proposal);
      sessionStorage.setItem(key, JSON.stringify(proposal));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function decide(approve: boolean) {
    if (!pending || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await request<{ output: Review }>(
        `${base}/change-proposals/${pending.id}/${approve ? "approve" : "reject"}`,
        {},
      );
      sessionStorage.removeItem(key);
      setPending(null);
      if (approve) {
        setReceipt(result.output);
        window.dispatchEvent(new Event("reality:delivery-settled"));
      } else read.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const review = receipt || pending?.preview.settlement;
  const amountField = (name: string, label: string, initial?: string) => (
    <label className="grid gap-1">
      {t(label)}
      <input
        className="br-control w-full"
        name={name}
        inputMode="decimal"
        required
        defaultValue={initial}
      />
    </label>
  );
  return (
    <dialog
      ref={dialog}
      aria-labelledby="settlement-title"
      className="m-auto max-h-[90vh] w-[min(680px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) close();
      }}
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <h2 id="settlement-title" className="text-lg font-semibold">
          {t(initialMode === "payment" ? "Record payment and allocation" : "Use available credit")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      <p className="mb-4 text-sm text-fg-muted">
        {t("Record actual money and explicit allocations. Any unaccepted shortfall stays open.")}
      </p>
      {error && (
        <p role="alert" className="mb-4 text-red-600">
          {error}
        </p>
      )}
      {review ? (
        <>
          <p className="mb-2 font-medium">
            {review.number} · {review.party}
          </p>
          {review.invoice_number && review.invoice_number !== review.number && (
            <p className="mb-4">
              {t("Invoice")}: {review.invoice_number}
            </p>
          )}
          {receipt && (
            <p role="status" className="mb-4">
              {t("Settlement recorded")}
            </p>
          )}
          <dl className="mb-4 grid grid-cols-2 gap-3">
            {(
              [
                [
                  review.cash_direction === "incoming"
                    ? "Money received"
                    : review.cash_direction === "outgoing"
                      ? "Money paid"
                      : "Cash change",
                  review.cash_amount,
                ],
                ["Allocated amount", review.allocation_amount],
                ["Accepted reduction", review.reduction_amount],
                ["Remaining claim", review.remaining_claim],
                ["Remaining available credit", review.remaining_credit],
              ] as [string, string | null][]
            )
              .filter(([, value]) => value !== null)
              .map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs text-fg-muted">{t(label)}</dt>
                  <dd>{formatMoney(value!, review.currency)}</dd>
                </div>
              ))}
          </dl>
          <p className="mb-2 text-sm">
            {review.control_account_code}
            {review.cash_account_code ? ` · ${review.cash_account_code}` : ""}
          </p>
          {review.reduction?.counterpart_account_code && (
            <p className="mb-2 text-sm">
              {t("Accepted reduction")}: {review.reduction.counterpart_account_code}
            </p>
          )}
          {review.reference && <p className="mb-2 break-words">{review.reference}</p>}
          {review.effective_at && <p className="mb-2">{formatDateTime(review.effective_at)}</p>}
          {review.reduction?.reason && (
            <p className="mb-2 whitespace-pre-wrap">{review.reduction.reason}</p>
          )}
          {review.reduction?.agreement && (
            <p className="mb-2 whitespace-pre-wrap">{review.reduction.agreement}</p>
          )}
          {receipt ? (
            <div className="flex flex-wrap gap-2">
              {receipt.invoice_id && (
                <button className="br-btn" onClick={() => explain(receipt.invoice_id!)}>
                  {t("Explain invoice")}
                </button>
              )}
              {(
                [
                  ["Payment", receipt.payment],
                  ["Refund", receipt.refund],
                  ["Accepted reduction", receipt.reduction],
                ] as [string, Evidence | null | undefined][]
              )
                .filter(([, evidence]) => evidence)
                .map(([label, evidence]) => (
                  <button
                    key={label}
                    className="br-btn"
                    onClick={() => explain(evidence!.document_id)}
                  >
                    {t("Explain")} · {t(label)}
                  </button>
                ))}
              {receipt.mode !== "payment" && (
                <button className="br-btn" onClick={() => explain(documentId)}>
                  {t("Explain credit")}
                </button>
              )}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              <button className="br-btn" disabled={busy} onClick={() => void decide(true)}>
                {t("Confirm settlement")}
              </button>
              <button className="br-btn" disabled={busy} onClick={() => void decide(false)}>
                {t("Reject")}
              </button>
            </div>
          )}
        </>
      ) : !data ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={5} />
      ) : (
        <>
          <p className="mb-4">
            {data.number} · {t(data.kind === "invoice" ? "Open amount" : "Available credit")}:{" "}
            {formatMoney(data.open ?? data.available!, data.currency)}
          </p>
          <form onSubmit={prepare} className="grid gap-4">
            {data.kind === "credit" && (
              <label className="grid gap-1">
                {t("Credit action")}
                <select
                  className="br-control w-full"
                  aria-label={t("Credit action")}
                  value={mode}
                  onChange={(e) => setMode(e.target.value as Mode)}
                >
                  <option value="allocate_credit">{t("Allocate to invoice")}</option>
                  <option value="refund_credit">
                    {t(
                      data.side === "customer"
                        ? "Record customer credit refund"
                        : "Record supplier credit refund",
                    )}
                  </option>
                </select>
              </label>
            )}
            {mode === "allocate_credit" && (
              <>
                {suggestedInvoices(data.invoices).length > 0 && (
                  <div className="grid gap-1" data-testid="settlement-candidates">
                    <span>{t("Suggested invoices")}</span>
                    <ul className="text-sm text-fg-muted">
                      {suggestedInvoices(data.invoices).map((invoice) => (
                        <li key={invoice.id}>
                          {invoice.number} · {formatMoney(invoice.open, invoice.currency)} ·{" "}
                          {(invoice.reasons || [])
                            .map((reason) => t(reasonLabel(reason)))
                            .join("; ")}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <label className="grid gap-1">
                  {t("Find matching invoice")}
                  <input
                    className="br-control w-full"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </label>
                <label className="grid gap-1">
                  {t("Invoice")}
                  <select
                    aria-label={t("Invoice")}
                    className="br-control w-full"
                    name="invoice"
                    required
                    defaultValue=""
                  >
                    <option value="">{t("Select invoice")}</option>
                    {data.invoices?.map((invoice) => (
                      <option key={invoice.id} value={invoice.id}>
                        {invoice.number} · {formatMoney(invoice.open, invoice.currency)}
                        {(invoice.reasons || []).length > 0 ? ` · ${t("suggested")}` : ""}
                      </option>
                    ))}
                  </select>
                </label>
                {data.more_invoices && (
                  <p className="text-sm text-fg-muted">
                    {t("Refine the search to find more matching invoices.")}
                  </p>
                )}
              </>
            )}
            {amountField(
              "amount",
              mode === "allocate_credit" ? "Allocated amount" : "Actual cash amount",
            )}
            {mode === "payment" && (
              <>
                {amountField("allocation", "Amount allocated to this invoice", "0")}
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={reduce}
                    disabled={!data.counterpart || data.counterpart.state !== "active"}
                    onChange={(e) => setReduce(e.target.checked)}
                  />
                  {t("Also accept a stated reduction")}
                </label>
                {(!data.counterpart || data.counterpart.state !== "active") && (
                  <p className="text-sm text-fg-muted">
                    {t(
                      "Configure an active reduction counterpart in company account settings first.",
                    )}
                  </p>
                )}
                {reduce && (
                  <div className="grid gap-4 rounded-lg border border-border-default p-4">
                    {amountField("reduction", "Stated reduction amount")}
                    <label className="grid gap-1">
                      {t("Reduction reason")}
                      <select className="br-control w-full" name="category">
                        <option value="early_payment_discount">
                          {t("Early-payment discount")}
                        </option>
                        <option value="agreed_deduction">{t("Agreed deduction")}</option>
                        <option value="accepted_small_remainder">
                          {t("Accepted small remainder")}
                        </option>
                      </select>
                    </label>
                    <label className="grid gap-1">
                      {t("Explanation")}
                      <textarea name="reason" className="br-control w-full" required />
                    </label>
                    {data.side === "supplier" && (
                      <label className="grid gap-1">
                        {t("Supplier entitlement or agreement")}
                        <textarea name="agreement" className="br-control w-full" required />
                      </label>
                    )}
                  </div>
                )}
              </>
            )}
            {mode !== "allocate_credit" && (
              <>
                <label className="grid gap-1">
                  {t("Actual payment reference")}
                  <input className="br-control w-full" name="reference" required />
                </label>
                <label className="grid gap-1">
                  {t("Actual payment time (with timezone)")}
                  <input className="br-control w-full" name="effective" required />
                </label>
                <details>
                  <summary>{t("External evidence (optional)")}</summary>
                  <label className="grid gap-1">
                    {t("Source record ID")}
                    <input className="br-control w-full" name="source" />
                  </label>
                  <label className="grid gap-1">
                    {t("Source effect reference")}
                    <input className="br-control w-full" name="effect" />
                  </label>
                </details>
              </>
            )}
            <div className="flex gap-2">
              <button className="br-btn" disabled={busy || read.loading}>
                {t("Review settlement")}
              </button>
              <button className="br-btn" type="button" disabled={busy} onClick={read.refresh}>
                {t("Reload")}
              </button>
            </div>
          </form>
        </>
      )}
    </dialog>
  );
}
