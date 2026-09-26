import { useEffect, useRef, useState } from "react";
import { api, deliveryActions, refundActions, type RefundInput, type RefundProposal } from "../api";
import { formatMoney, formatDateTime, t } from "../localization";
import { useRead } from "./useCompanyContext";
import { useProposalRecovery } from "./useProposal";
import { Inspector } from "./Inspector";
import { DecisionActionBar } from "./DecisionReview";
import { ReadLine, ReadState } from "./ReadState";
import { RegisterPager } from "./WarehousePage";
export function RefundCard({
  tenant,
  proposalId = "",
  creditNote = "",
  close,
  prepared,
  settled,
}: {
  tenant: string;
  proposalId?: string;
  creditNote?: string;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true),
    request = useRef(crypto.randomUUID());
  const [draft, setDraft] = useState<RefundInput>({
    credit_note_id: creditNote,
    amount: "",
    refund_number: "",
  });
  const [proposal, setProposal] = useState<RefundProposal | null>(null),
    [editing, setEditing] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [uncertain, setUncertain] = useState(false);
  const [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);
  const [query, setQuery] = useState(""),
    [page, setPage] = useState(1),
    [invoiceSeed, setInvoiceSeed] = useState("");
  const invoices = useRead(
    () => api.openItems(tenant, query, "customer-credit", "outstanding", page),
    [tenant, query, page],
  );
  useEffect(() => {
    alive.current = true;
    const previous = document.activeElement as HTMLElement;
    const node = dialog.current;
    node?.showModal();
    return () => {
      alive.current = false;
      node?.close();
      previous?.focus();
    };
  }, []);
  useEffect(() => {
    let active = true;
    if (proposalId && !editing) {
      setBusy(true);
      refundActions
        .review(tenant, proposalId)
        .then((value) => {
          if (active) setProposal(value);
        })
        .catch((e) => {
          if (active) setError(e.message);
        })
        .finally(() => {
          if (active) setBusy(false);
        });
    }
    return () => {
      active = false;
    };
  }, [tenant, proposalId, editing]);
  useProposalRecovery(
    tenant,
    proposal?.id || proposalId,
    uncertain || proposal?.status === "executing",
    (value) => {
      setProposal(value);
      setUncertain(false);
      if (value.status === "executed") settled();
    },
    setError,
    refundActions.detail,
  );
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      if (alive.current) setError((e as Error).message);
    } finally {
      if (alive.current) setBusy(false);
    }
  };
  const change = (next: Partial<RefundInput>) => {
    setDraft((old) => ({ ...old, ...next }));
    request.current = crypto.randomUUID();
  };
  const prepare = () =>
    run(async () => {
      const result = await refundActions.prepare(
        tenant,
        request.current,
        Object.fromEntries(
          Object.entries(draft).filter(([key, value]) => key !== "effective_at" || !!value),
        ) as RefundInput,
      );
      if (alive.current) {
        setProposal(result);
        setEditing(false);
        prepared?.(result.id);
      }
    });
  const refresh = async () => {
    if (!proposal) return;
    const result = await refundActions.reconcile(tenant, proposal.id);
    if (alive.current) {
      setProposal(result);
      setUncertain(false);
      if (result.status === "executed") settled();
    }
  };
  const confirm = () =>
    run(async () => {
      if (!proposal?.review) return;
      try {
        await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
      } catch (e) {
        if (alive.current) setUncertain(true);
        throw e;
      }
      if (alive.current) {
        setUncertain(true);
        settled();
        await refresh();
      }
    });
  const edit = () =>
    run(async () => {
      if (!proposal?.review) return;
      await api.rejectProposal(tenant, proposal.id, null);
      setDraft(structuredClone(proposal.review.intent));
      setInvoiceSeed(proposal.review.state.invoice.number);
      request.current = crypto.randomUUID();
      setEditing(true);
      setProposal(null);
    });

  const review = proposal?.review;
  const money = (value: string, currency: string) => formatMoney(value, currency, 4);
  const field = (label: string, key: string, required = true) => (
    <label className="block text-sm">
      {label}
      <input
        className="br-control mt-2 w-full"
        aria-label={label}
        required={required}
        value={String(draft[key] || "")}
        onChange={(e) => change({ [key]: e.target.value })}
      />
    </label>
  );
  return (
    <dialog
      ref={dialog}
      aria-labelledby="refund-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(760px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="refund-title" className="text-xl font-semibold text-fg-strong">
          {t("Record refund")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      {!proposal ? (
        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            void prepare();
          }}
        >
          <fieldset disabled={busy || (!!proposalId && !editing)} className="min-w-0 space-y-5">
            <p className="rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
              {t(
                "Record a refund already made against one customer credit. Partial refunds are supported.",
              )}
            </p>
            <label className="block text-sm">
              {t("Search credit notes")}
              <input
                className="br-control mt-2 w-full"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setPage(1);
                  change({ credit_note_id: "" });
                }}
              />
            </label>
            <label className="block text-sm">
              {t("Credit note")}
              <select
                aria-label={t("Credit note")}
                className="br-control mt-2 w-full"
                required
                value={draft.credit_note_id}
                onChange={(e) => change({ credit_note_id: e.target.value })}
              >
                <option value="">{t("Select a record")}</option>
                {draft.credit_note_id &&
                  !invoices.data?.items.some((r) => r.document_id === draft.credit_note_id) && (
                    <option value={draft.credit_note_id}>
                      {invoiceSeed || draft.credit_note_id}
                    </option>
                  )}
                {invoices.data?.items.map((r) => (
                  <option key={r.document_id} value={r.document_id}>
                    {r.number} · {r.party} · {t("Open")}: {money(r.open, r.currency)}
                  </option>
                ))}
              </select>
            </label>
            {(!invoices.data || invoices.error) && (
              <ReadState
                loading={invoices.loading}
                error={invoices.error}
                retry={invoices.refresh}
              />
            )}
            {invoices.data && !invoices.data.items.length && (
              <p role="status">{t("No matching open customer credits")}</p>
            )}
            {invoices.data && invoices.data.page.pages > 1 && (
              <RegisterPager
                page={invoices.data.page}
                change={(value) => {
                  setPage(value);
                  change({ credit_note_id: "" });
                }}
              />
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              {field(t("Refund amount"), "amount")}
              {field(t("Refund reference"), "refund_number", false)}
              {field(t("Effective time (UTC ISO, optional)"), "effective_at", false)}
            </div>
            <p className="text-sm text-fg-muted">
              {t(
                "Enter the amount actually refunded. This records the refund; it does not initiate a bank transfer.",
              )}
            </p>
            <button
              type="submit"
              className="br-btn br-btn-primary"
              disabled={!draft.credit_note_id || invoices.loading || !!invoices.error}
            >
              {t("Review change")}
            </button>
          </fieldset>
          {busy && <ReadLine />}
        </form>
      ) : (
        <div className="space-y-5">
          {review && (
            <>
              <section className="rounded-lg bg-surface-muted p-4">
                <p className="text-xs text-fg-muted">{t("Customer refund")}</p>
                <h3 className="mt-2 text-xl font-semibold">{review.state.party.name}</h3>
                <button
                  className="mt-2 text-accent underline"
                  onClick={() => inspect({ kind: "document", id: review.state.invoice.id })}
                >
                  {t("Credit note")}: {review.state.invoice.number}
                </button>
              </section>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span>{t("Refund amount")}</span>
                <strong className="text-2xl">
                  {money(review.state.creation.amount, review.state.creation.currency)}
                </strong>
              </div>
              <div className="grid gap-4 rounded-lg border border-border-default p-4 sm:grid-cols-2">
                <div>
                  <p className="text-sm text-fg-muted">{t("Credit open before refund")}</p>
                  <strong className="mt-2 block text-lg">
                    {money(review.state.open_before, review.state.creation.currency)}
                  </strong>
                </div>
                <div>
                  <p className="text-sm text-fg-muted">{t("Credit open after refund")}</p>
                  <strong className="mt-2 block text-lg">
                    {money(review.state.open_after, review.state.creation.currency)}
                  </strong>
                </div>
              </div>
              <p className="text-sm">
                {t("Refund reference")}:{" "}
                {review.state.creation.payment_number || t("Assigned at recording")}
              </p>
              <p className="text-sm">
                {t("Effective time")}:{" "}
                {review.state.creation.effective_at
                  ? formatDateTime(review.state.creation.effective_at)
                  : t("At confirmation")}
              </p>
              {review.state.source ? (
                <button
                  className="text-sm text-accent underline"
                  onClick={() => inspect({ kind: "source_record", id: review.state.source!.id })}
                >
                  {t("Original source")}: {review.state.source.source_system} ·{" "}
                  {review.state.source.external_id}
                </button>
              ) : (
                <p className="text-sm text-fg-muted">{t("No original refund source attached.")}</p>
              )}
              <p className="text-sm text-fg-muted">
                {t(
                  "Enter the amount actually refunded. This records the refund; it does not initiate a bank transfer.",
                )}
              </p>
            </>
          )}
          <p role="status">
            {t(
              proposal.status === "executed"
                ? "Recorded"
                : proposal.status === "rejected"
                  ? "Rejected"
                  : uncertain || proposal.status === "executing"
                    ? "Execution outcome is being checked. Do not repeat the action."
                    : "Review the exact change before confirming.",
            )}
          </p>
          {proposal.status === "executed" && proposal.verification !== "verified" && (
            <p role="alert">{t("Recorded result is not yet verified.")}</p>
          )}
          {proposal.observation_error && (
            <p role="alert" className="text-sm">
              {t("Recorded result is separate from the current observation.")}{" "}
              {proposal.observation_error}
            </p>
          )}
          <div className="flex flex-wrap gap-3">
            {proposal.status === "proposed" && !uncertain && (
              <DecisionActionBar
                busy={busy || !review}
                reject={() =>
                  run(async () => {
                    await api.rejectProposal(tenant, proposal.id, null);
                    setProposal({ ...proposal, status: "rejected" });
                    settled();
                  })
                }
                edit={edit}
                confirm={confirm}
              />
            )}
            {(uncertain || ["executing", "executed"].includes(proposal.status)) && (
              <button className="br-btn" disabled={busy} onClick={() => run(refresh)}>
                {t("Check outcome")}
              </button>
            )}
            {proposal.verification === "verified" && review && (
              <a
                className="br-btn"
                href={`/app/finance?${new URLSearchParams({ tenant, finance_view: "open-items", flow: "customer-credit", entry: review.state.creation.invoice_id })}`}
              >
                {t("Open credit note")}
              </a>
            )}
            {proposal.verification === "verified" && proposal.payment_document_id && (
              <a
                className="br-btn"
                href={`/app/finance?${new URLSearchParams({ tenant, finance_view: "open-items", flow: "customer-credit", entry: proposal.payment_document_id })}`}
              >
                {t("Open refund")}
              </a>
            )}
          </div>
          {proposal.observation && (
            <section className="rounded-lg bg-surface-muted p-4 text-sm">
              <p>
                {t("Currently open")}:{" "}
                {money(proposal.observation.open, review?.state.creation.currency || "EUR")}
              </p>
              {!proposal.observation.allocation_active && (
                <p className="mt-2">
                  {t(
                    "This allocation is no longer active. The original refund remains in history.",
                  )}
                </p>
              )}
            </section>
          )}
          {proposal.links.map((link) => (
            <button key={link.id} className="br-btn mr-2" onClick={() => inspect(link)}>
              {t("Inspect")} · {t(link.kind)}
            </button>
          ))}
          <details>
            <summary className="cursor-pointer text-sm">{t("Technical details")}</summary>
            <pre className="mt-3 overflow-auto whitespace-pre-wrap break-all text-xs">
              {JSON.stringify(
                {
                  id: proposal.id,
                  review,
                  receipt: proposal.receipt,
                  verification: proposal.verification,
                  links: proposal.links,
                },
                null,
                2,
              )}
            </pre>
          </details>
        </div>
      )}
      {error && (
        <p role="alert" className="mt-4 text-critical-text">
          {error}
        </p>
      )}
      {inspection && <Inspector tenant={tenant} target={inspection} close={() => inspect(null)} />}
    </dialog>
  );
}
