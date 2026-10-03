import { useEffect, useRef, useState } from "react";
import { deliveryActions, type ProposalReview } from "../api";
import { ReadLine } from "./ReadState";
import { ProposalApprovalRequirement } from "./DecisionReview";
import { formatMoney, t } from "../localization";

// Spec 347: an owner lets a prepayment order ship before it is paid, with a stated
// reason. The shared reviewed tool records the release; this dialog states, reviews
// and confirms. The unpaid rest stays an open receivable.

type Review = {
  token: string;
  state: {
    number: string;
    payment: { currency: string; required: string; received: string; remaining: string };
  };
};
type Prepared = {
  id: string;
  status?: string;
  review: Review;
  next_step?: ProposalReview["next_step"];
};

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

export function PrepaymentRelease({
  tenant,
  order = "",
  proposalId,
  close,
  settled,
}: {
  tenant: string;
  order?: string;
  proposalId?: string;
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
  const [retry, retryReview] = useState(0);

  useEffect(() => {
    const node = dialog.current;
    const previous = document.activeElement as HTMLElement;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, []);

  useEffect(() => {
    if (!proposalId) return;
    let active = true;
    setBusy(true);
    deliveryActions
      .review(tenant, proposalId)
      .then((value) => {
        if (active) {
          setPrepared(value as unknown as Prepared);
          setDone(value.status === "executed" && value.verification === "verified");
        }
      })
      .catch((failure) => {
        if (active) setError(failure.message);
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [tenant, proposalId, retry]);

  async function prepare(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      setPrepared(
        await call<Prepared>(`${base}/delivery-actions/prepare`, {
          tool: "prepayment_release",
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
      aria-label={t("Release prepayment")}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
      className="m-auto max-h-[90vh] w-[min(640px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <div className="mb-5 flex justify-between gap-3">
        <h2 className="text-lg font-semibold">{t("Release prepayment")}</h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      {error && <p className="mb-4 text-red-600">{error}</p>}
      {done ? (
        <p role="status" className="rounded-lg bg-positive-surface p-4 font-medium">
          {t("The prepayment is released; the order can ship. The unpaid rest stays open.")}
        </p>
      ) : prepared?.status && prepared.status !== "proposed" ? (
        <p role="status">
          {t(
            prepared.status === "rejected"
              ? "Rejected"
              : "Execution outcome is being checked. Do not repeat the action.",
          )}
        </p>
      ) : state ? (
        <>
          <p className="mb-3">
            {state.number} · {t("Prepayment required")}{" "}
            {formatMoney(state.payment.required, state.payment.currency)} · {t("Received")}{" "}
            {formatMoney(state.payment.received, state.payment.currency)} · {t("Still open")}{" "}
            {formatMoney(state.payment.remaining, state.payment.currency)}
          </p>
          {prepared?.next_step ? (
            <ProposalApprovalRequirement nextStep={prepared.next_step} />
          ) : (
            <p className="mb-4 text-sm text-fg-muted">
              {t("Only a company owner can confirm this release.")}
            </p>
          )}
          <div className="flex gap-2">
            <button className="br-btn" disabled={busy} onClick={() => void confirm()}>
              {t("Confirm")}
            </button>
            <button className="br-btn" disabled={busy} onClick={close}>
              {t("Cancel")}
            </button>
          </div>
        </>
      ) : proposalId ? (
        <div>
          {busy ? (
            <ReadLine />
          ) : (
            <button className="br-btn" onClick={() => retryReview((value) => value + 1)}>
              {t("Retry")}
            </button>
          )}
        </div>
      ) : (
        <form className="grid gap-4" onSubmit={prepare}>
          <label>
            {t("Why does the order ship before it is paid?")}
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
