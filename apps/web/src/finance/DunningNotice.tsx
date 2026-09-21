import { useEffect, useRef, useState } from "react";
import { formatMoney, t } from "../localization";
import { ReadState } from "../unified/ReadState";
import { useRead } from "../unified/useCompanyContext";

type Context = {
  invoice_id: string;
  number: string;
  side: "customer" | "supplier";
  currency: string;
  open: string;
  revision: number;
};
type Review = {
  number: string;
  notice_date: string;
  level: number;
  fee_amount: string;
  currency: string;
  invoice_open: Record<string, string>;
};
type Pending = { id: string; preview: { dunning: Review } };

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

export function DunningNotice({
  tenant,
  invoice,
  close,
}: {
  tenant: string;
  invoice: string;
  close: () => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenant)}`;
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState<Pending | null>(null);
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

  async function prepare(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!read.data || busy) return;
    const fields = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      setPending(
        await call<Pending>(`${base}/finance/commercial/proposals`, {
          tool: "finance.dunning.record",
          arguments: {
            expected_revision: read.data.revision,
            invoice_ids: [invoice],
            notice_date: fields.get("date"),
            level: Number(fields.get("level")),
            fee_amount: fields.get("fee") || "0",
            number: fields.get("number") || "",
            reason: fields.get("reason") || "",
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
      if (approve) window.dispatchEvent(new Event("reality:delivery-settled"));
      close();
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }

  const review = pending?.preview.dunning;
  return (
    <dialog
      ref={dialog}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
      className="m-auto max-h-[90vh] w-[min(680px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <div className="mb-5 flex justify-between gap-3">
        <h2 className="text-lg font-semibold">{t("Create dunning notice")}</h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      {error && <p className="mb-4 text-red-600">{error}</p>}
      {review ? (
        <>
          <p className="mb-4">
            {read.data?.number} · {t("Open amount")}: {formatMoney(review.invoice_open[invoice], review.currency)}
          </p>
          <dl className="mb-5 grid grid-cols-2 gap-3">
            <div><dt className="text-xs text-fg-muted">{t("Dunning level")}</dt><dd>{review.level}</dd></div>
            <div><dt className="text-xs text-fg-muted">{t("Notice date")}</dt><dd>{review.notice_date}</dd></div>
            <div><dt className="text-xs text-fg-muted">{t("Dunning fee")}</dt><dd>{formatMoney(review.fee_amount, review.currency)}</dd></div>
            <div><dt className="text-xs text-fg-muted">{t("Notice number")}</dt><dd>{review.number || t("Generated automatically")}</dd></div>
          </dl>
          <p className="mb-4 text-sm text-fg-muted">{t("The fee is a separate receivable. No email is sent automatically.")}</p>
          <div className="flex gap-2">
            <button className="br-btn" disabled={busy} onClick={() => void decide(true)}>{t("Confirm dunning notice")}</button>
            <button className="br-btn" disabled={busy} onClick={() => void decide(false)}>{t("Reject")}</button>
          </div>
        </>
      ) : !read.data ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={4} />
      ) : read.data.side !== "customer" ? (
        <p>{t("Dunning notices are available for customer invoices only.")}</p>
      ) : (
        <form className="grid gap-4" onSubmit={prepare}>
          <p>{read.data.number} · {t("Open amount")}: {formatMoney(read.data.open, read.data.currency)}</p>
          <label>{t("Notice date")}<input className="br-control mt-1 w-full" name="date" type="date" defaultValue={new Date().toISOString().slice(0, 10)} required /></label>
          <label>{t("Dunning level")}<select className="br-control mt-1 w-full" name="level" defaultValue="1"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select></label>
          <label>{t("Dunning fee")}<input className="br-control mt-1 w-full" name="fee" inputMode="decimal" defaultValue="0" required /></label>
          <label>{t("Notice number (optional)")}<input className="br-control mt-1 w-full" name="number" /></label>
          <label>{t("Reason (optional)")}<textarea className="br-control mt-1 w-full" name="reason" /></label>
          <button className="br-btn" disabled={busy}>{t("Review dunning notice")}</button>
        </form>
      )}
    </dialog>
  );
}
