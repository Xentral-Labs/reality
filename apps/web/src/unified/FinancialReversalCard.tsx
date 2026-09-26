import { useEffect, useRef, useState } from "react";
import {
  api,
  deliveryActions,
  financialReversalActions,
  type FinancialReversalInput,
  type FinancialReversalProposal,
} from "../api";
import { formatMoney, formatQuantity, t } from "../localization";
import { useRead } from "./useCompanyContext";
import { useProposalRecovery } from "./useProposal";
import { Inspector } from "./Inspector";
import { DecisionActionBar } from "./DecisionReview";
import { ReadLine, ReadState } from "./ReadState";
import { RegisterPager } from "./WarehousePage";

export function FinancialReversalCard({
  tenant,
  proposalId = "",
  postingGroup = "",
  close,
  prepared,
  settled,
}: {
  tenant: string;
  proposalId?: string;
  postingGroup?: string;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true),
    request = useRef(crypto.randomUUID());
  const [draft, setDraft] = useState<FinancialReversalInput>({
    posting_group_id: postingGroup,
    reason: "",
  });
  const [proposal, setProposal] = useState<FinancialReversalProposal | null>(null),
    [editing, setEditing] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [uncertain, setUncertain] = useState(false);
  const [inspection, inspect] = useState<{ kind: string; id: string } | null>(null),
    [query, setQuery] = useState(""),
    [page, setPage] = useState(1);
  const choices = useRead(
    () => financialReversalActions.choices(tenant, query, page),
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
      financialReversalActions
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
    financialReversalActions.detail,
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
  const change = (next: Partial<FinancialReversalInput>) => {
    setDraft((old) => ({ ...old, ...next }));
    request.current = crypto.randomUUID();
  };
  const prepare = () =>
    run(async () => {
      const value = await financialReversalActions.prepare(tenant, request.current, draft);
      if (alive.current) {
        setProposal(value);
        setEditing(false);
        prepared?.(value.id);
      }
    });
  const refresh = async () => {
    if (!proposal) return;
    const value = await financialReversalActions.reconcile(tenant, proposal.id);
    if (alive.current) {
      setProposal(value);
      setUncertain(false);
      if (value.status === "executed") settled();
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
      const original = proposal.review.intent;
      setDraft({ posting_group_id: original.posting_group_id, reason: original.reason });
      request.current = crypto.randomUUID();
      setEditing(true);
      setProposal(null);
    });
  const review = proposal?.review;
  const money = (value: string, currency: string) => formatMoney(value, currency, 4);
  const observation = proposal?.observation;
  const inverseId = proposal?.links
    .filter((link) => link.kind === "ledger_entry")
    .find((link) => !review?.state.preview.original_entries.some((row) => row.id === link.id))?.id;
  return (
    <dialog
      ref={dialog}
      aria-labelledby="financial-reversal-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(820px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="financial-reversal-title" className="text-xl font-semibold text-fg-strong">
          {t("Reverse posting")}
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
                "Reverse a recorded financial posting. Review the full financial effect before confirming.",
              )}
            </p>
            <label className="block text-sm">
              {t("Search postings")}
              <input
                className="br-control mt-2 w-full"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setPage(1);
                }}
              />
            </label>
            <label className="block text-sm">
              {t("Posting")}
              <select
                className="br-control mt-2 w-full"
                aria-label={t("Posting")}
                required
                value={draft.posting_group_id}
                onChange={(e) => change({ posting_group_id: e.target.value })}
              >
                <option value="">{t("Select a record")}</option>
                {draft.posting_group_id &&
                  !choices.data?.items.some((row) => row.id === draft.posting_group_id) && (
                    <option value={draft.posting_group_id}>{draft.posting_group_id}</option>
                  )}
                {choices.data?.items.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.number} · {row.party} · {money(row.amount, row.currency)}
                  </option>
                ))}
              </select>
            </label>
            {(!choices.data || choices.error) && (
              <ReadState loading={choices.loading} error={choices.error} retry={choices.refresh} />
            )}
            {choices.data && !choices.data.items.length && (
              <p role="status">{t("No reversible postings found")}</p>
            )}
            {choices.data && choices.data.page.pages > 1 && (
              <RegisterPager page={choices.data.page} change={setPage} />
            )}
            <label className="block text-sm">
              {t("Reversal reason")}
              <textarea
                rows={3}
                className="br-control mt-2 w-full"
                aria-label={t("Reversal reason")}
                required
                value={draft.reason}
                onChange={(e) => change({ reason: e.target.value })}
              />
            </label>
            <button
              type="submit"
              className="br-btn br-btn-primary"
              disabled={!draft.posting_group_id || !draft.reason.trim()}
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
                <p className="text-sm text-fg-muted">{t("Full posting reversal")}</p>
                <h3 className="mt-2 text-xl font-semibold">
                  {review.state.party?.name || t("Posting")}
                </h3>
                {review.state.documents.map((doc) => (
                  <button
                    key={doc.id}
                    className="mt-2 mr-3 text-accent underline"
                    onClick={() => inspect({ kind: "document", id: doc.id })}
                  >
                    {doc.number}
                  </button>
                ))}
                <p className="mt-3 whitespace-pre-wrap text-sm">{review.state.preview.reason}</p>
              </section>
              <section className="space-y-3">
                <h3 className="font-semibold">{t("Financial effect")}</h3>
                {review.state.effects.invoices.map((row) => (
                  <div key={row.id} className="rounded-lg border border-border-default p-3">
                    <button
                      className="font-medium text-accent underline"
                      onClick={() => inspect({ kind: "document", id: row.id })}
                    >
                      {row.number}
                    </button>
                    <p className="mt-1 text-xs text-fg-muted">{t("Open amount")}</p>
                    <p className="mt-2 flex flex-wrap items-center gap-3">
                      <span>{money(row.before, row.currency)}</span>
                      <span aria-hidden="true">→</span>
                      <strong>{money(row.after, row.currency)}</strong>
                    </p>
                  </div>
                ))}
                {review.state.effects.billing?.map((row) => (
                  <div
                    key={row.order_line_id}
                    className="rounded-lg border border-border-default p-3"
                  >
                    <button
                      className="text-accent underline"
                      onClick={() => inspect({ kind: "document", id: row.order_id })}
                    >
                      {row.label}
                    </button>
                    <p className="mt-1 text-xs text-fg-muted">
                      {t("Remaining billable after reversal")}
                    </p>
                    <p className="mt-2 font-semibold">
                      {formatQuantity(row.remaining_before)} → {formatQuantity(row.remaining_after)}{" "}
                      {row.unit}
                    </p>
                  </div>
                ))}
                {review.state.effects.payments.map((row) => (
                  <div key={row.id} className="rounded-lg border border-border-default p-3">
                    <span className="font-medium">{row.number}</span>
                    <p className="mt-1 text-xs text-fg-muted">{t("Unallocated payment amount")}</p>
                    <p className="mt-2 flex flex-wrap items-center gap-3">
                      <span>{money(row.before, row.currency)}</span>
                      <span aria-hidden="true">→</span>
                      <strong>{money(row.after, row.currency)}</strong>
                    </p>
                  </div>
                ))}
                <p className="text-sm">
                  {t("Allocations becoming inactive")}:{" "}
                  <strong>{review.state.effects.newly_inactive.length}</strong>
                </p>
                {review.state.effects.newly_inactive.map((row) => (
                  <p key={row.id} className="text-sm text-fg-muted">
                    {money(row.amount, row.currency)}
                  </p>
                ))}
                {!!review.state.effects.already_inactive.length && (
                  <p className="text-sm text-fg-muted">
                    {t("Already inactive allocations")}:{" "}
                    {review.state.effects.already_inactive.length}
                  </p>
                )}
              </section>
              <details className="rounded-lg border border-border-default p-3">
                <summary className="cursor-pointer text-sm font-medium">
                  {t("Inverse entries")}
                </summary>
                <div className="mt-3 space-y-2">
                  {review.state.preview.inverse_entries.map((row, index) => (
                    <div key={index} className="flex flex-wrap justify-between gap-2 text-sm">
                      <span>
                        {row.account} · {t(row.debit_credit === "debit" ? "Debit" : "Credit")}
                      </span>
                      <span>{money(row.amount, row.currency)}</span>
                    </div>
                  ))}
                </div>
              </details>
              <p className="text-sm text-fg-muted">
                {t(
                  "Reversal time: at confirmation. Original records remain in history; no bank transfer or stock movement is made.",
                )}
              </p>
              {review.state.documents.some((doc) =>
                ["sales_invoice", "supplier_invoice"].includes(doc.type),
              ) && (
                <p className="text-sm text-fg-muted">
                  {t(
                    "Invoice evidence stays in history. Its quantity becomes billable again once all invoice posting groups are reversed.",
                  )}
                </p>
              )}
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
                confirmLabel="Confirm reversal"
              />
            )}
            {(uncertain || ["executing", "executed"].includes(proposal.status)) && (
              <button className="br-btn" disabled={busy} onClick={() => run(refresh)}>
                {t("Check outcome")}
              </button>
            )}
            {proposal.verification === "verified" && inverseId && (
              <a
                className="br-btn"
                href={`/app/finance?${new URLSearchParams({ tenant, finance_view: "journal", entry: inverseId })}`}
              >
                {t("Open reversal")}
              </a>
            )}
          </div>
          {observation && (
            <section className="rounded-lg bg-surface-muted p-3 text-sm">
              <h3 className="font-medium">{t("Current financial position")}</h3>
              {observation.invoices.map((row) => (
                <p key={row.id} className="mt-2">
                  {row.number} · {t("Currently open")}: {money(row.before, row.currency)}
                </p>
              ))}
              {observation.payments.map((row) => (
                <p key={row.id} className="mt-2">
                  {row.number} · {t("Unallocated payment amount")}:{" "}
                  {money(row.before, row.currency)}
                </p>
              ))}
            </section>
          )}
          {proposal.observation_error && (
            <p role="alert">
              {t("Recorded result is separate from the current observation.")}{" "}
              {proposal.observation_error}
            </p>
          )}
          <details>
            <summary className="cursor-pointer text-sm">{t("Technical details")}</summary>
            <div className="my-3 flex flex-wrap gap-2">
              {proposal.links.map((link) => (
                <button key={link.id} className="br-btn" onClick={() => inspect(link)}>
                  {t("Inspect")} · {t(link.kind)}
                </button>
              ))}
            </div>
            <pre className="overflow-auto whitespace-pre-wrap break-all text-xs">
              {JSON.stringify(
                { review, receipt: proposal.receipt, verification: proposal.verification },
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
