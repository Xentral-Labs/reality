import { useEffect, useRef, useState } from "react";
import { formatMoney, t } from "../localization";

// Spec 298: an order held for credit is released by an owner with a stated reason.
// The shared reviewed tool lifts only the credit holds; this dialog states, reviews
// and confirms.

type Review = {
  token: string;
  state: {
    number: string;
    holds: Array<{ id: string; commitment_id: string; note: string }>;
    exposure: { currency: string; credit_limit: string; exposure: string; excess: string };
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

export function CreditHoldRelease({
  tenant,
  order,
  close,
  settled,
}: {
  tenant: string;
  order: string;
  close: () => void;
  settled: () => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenant)}`;
  const dialog = useRef<HTMLDialogElement>(null);
  const request = useRef(crypto.randomUUID());
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [prepared, setPrepared] = useState<Prepared | null>(null);
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
    setBusy(true);
    setError("");
    try {
      setPrepared(
        await call<Prepared>(`${base}/delivery-actions/prepare`, {
          tool: "credit_hold_release",
          request_id: request.current,
          arguments: { document_id: order, reason },
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
      aria-label={t("Release credit hold")}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
      className="m-auto max-h-[90vh] w-[min(640px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <div className="mb-5 flex justify-between gap-3">
        <h2 className="text-lg font-semibold">{t("Release credit hold")}</h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      {error && <p className="mb-4 text-red-600">{error}</p>}
      {done ? (
        <p role="status" className="rounded-lg bg-positive-surface p-4 font-medium">
          {t("The credit hold is released; the order can be reserved and shipped.")}
        </p>
      ) : state ? (
        <>
          <p className="mb-3">
            {state.number} · {t("Exposure")}{" "}
            {formatMoney(state.exposure.exposure, state.exposure.currency)} · {t("Credit limit")}{" "}
            {formatMoney(state.exposure.credit_limit, state.exposure.currency)}
          </p>
          <ul className="mb-4 text-sm">
            {state.holds.map((hold) => (
              <li key={hold.id} data-original-content className="whitespace-pre-wrap">
                {hold.note}
              </li>
            ))}
          </ul>
          <p className="mb-4 text-sm text-fg-muted">
            {t("Only a company owner can confirm this release.")}
          </p>
          <div className="flex gap-2">
            <button className="br-btn" disabled={busy} onClick={() => void confirm()}>
              {t("Confirm")}
            </button>
            <button className="br-btn" disabled={busy} onClick={close}>
              {t("Cancel")}
            </button>
          </div>
        </>
      ) : (
        <form className="grid gap-4" onSubmit={prepare}>
          <label>
            {t("Why is the credit hold released?")}
            <textarea
              className="br-control mt-1 w-full"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              required
            />
          </label>
          <button className="br-btn self-start" disabled={busy || !reason.trim()}>
            {t("Review release")}
          </button>
        </form>
      )}
    </dialog>
  );
}
