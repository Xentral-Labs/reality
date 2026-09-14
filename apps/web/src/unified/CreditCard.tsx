import { useEffect, useRef, useState } from "react";
import { api, deliveryActions, creditActions, type CreditInput, type CreditProposal } from "../api";
import { formatMoney, formatQuantity, formatDateTime, t } from "../localization";
import { useRead } from "./useCompanyContext";
import { useProposalRecovery } from "./useProposal";
import { Inspector } from "./Inspector";
import { ReadLine, ReadState } from "./ReadState";
import { RegisterPager } from "./WarehousePage";
export function CreditCard({
  tenant,
  proposalId = "",
  invoice = "",
  close,
  prepared,
  settled,
}: {
  tenant: string;
  proposalId?: string;
  invoice?: string;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true),
    request = useRef(crypto.randomUUID());
  const [draft, setDraft] = useState<CreditInput>({
    lines: [{ invoice_line_id: "", quantity: "", gross_amount: "" }],
    invoice_id: invoice,
    reason: "",
    allocation_amount: "0",
    gross_amount: "",
    number: "",
  });
  const [proposal, setProposal] = useState<CreditProposal | null>(null),
    [editing, setEditing] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [uncertain, setUncertain] = useState(false);
  const [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);
  const [query, setQuery] = useState(""),
    [page, setPage] = useState(1),
    [invoiceId, setInvoiceId] = useState(invoice);
  const orders = useRead(
    () => api.documents(tenant, query, "sales_invoice", "", page),
    [tenant, query, page],
  );
  const lines = useRead(
    () => (invoiceId ? creditActions.context(tenant, invoiceId) : Promise.resolve(null)),
    [tenant, invoiceId],
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
      creditActions
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
    creditActions.detail,
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
  const change = (next: Partial<CreditInput>) => {
    setDraft((old) => ({ ...old, ...next }));
    request.current = crypto.randomUUID();
  };
  const changePosition = (
    index: number,
    next: Partial<NonNullable<CreditInput["lines"]>[number]>,
  ) => change({ lines: draft.lines?.map((row, i) => (i === index ? { ...row, ...next } : row)) });
  const prepare = () =>
    run(async () => {
      const result = await creditActions.prepare(
        tenant,
        request.current,
        "sales_credit_record",
        Object.fromEntries(
          Object.entries({ ...draft, invoice_id: invoiceId }).filter(
            ([key, value]) => key !== "effective_at" || !!value,
          ),
        ) as CreditInput,
      );
      if (alive.current) {
        setProposal(result);
        setEditing(false);
        prepared?.(result.id);
      }
    });
  const refresh = async () => {
    if (!proposal) return;
    const result = await creditActions.reconcile(tenant, proposal.id);
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
      const original = structuredClone(proposal.review.intent);
      setDraft(original);
      setInvoiceId(original.invoice_id);
      request.current = crypto.randomUUID();
      setEditing(true);
      setProposal(null);
    });

  const review = proposal?.review;
  const documentId = (
    proposal?.receipt as { records?: { family: string; id: string }[] } | null
  )?.records?.find((r) => r.family === "document")?.id;
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
      aria-labelledby="credit-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(760px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="credit-title" className="text-xl font-semibold text-fg-strong">
          {t("New credit note")}
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
              {t("Correct selected invoice positions. No goods are moved and no refund is sent.")}
            </p>
            <label className="block text-sm">
              {t("Search invoices")}
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
              {t("Invoice")}
              <select
                className="br-control mt-2 w-full"
                required
                aria-label={t("Invoice")}
                value={invoiceId}
                onChange={(e) => {
                  setInvoiceId(e.target.value);
                  change({
                    lines: [{ invoice_line_id: "", quantity: "", gross_amount: "" }],
                    allocation_amount: "0",
                  });
                }}
              >
                <option value="">{t("Select a record")}</option>
                {invoiceId && !orders.data?.items.some((row) => row.id === invoiceId) && (
                  <option value={invoiceId}>{lines.data?.invoice.number || invoiceId}</option>
                )}
                {orders.data?.items.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.number} · {row.party} · {formatMoney(row.gross_amount, row.currency)}
                  </option>
                ))}
              </select>
            </label>
            {(!orders.data || orders.error) && (
              <ReadState loading={orders.loading} error={orders.error} retry={orders.refresh} />
            )}
            {orders.data && !orders.data.items.length && (
              <p role="status">{t("No matching records")}</p>
            )}
            {orders.data && orders.data.page.pages > 1 && (
              <RegisterPager page={orders.data.page} change={setPage} />
            )}
            {invoiceId && (lines.loading || lines.error) && (
              <ReadState loading={lines.loading} error={lines.error} retry={lines.refresh} />
            )}
            {lines.data && (
              <div className="grid gap-3 rounded-lg bg-surface-muted p-3 text-sm sm:grid-cols-2">
                <p>
                  {t("Open invoice amount")}
                  <strong className="mt-1 block">
                    {formatMoney(lines.data.open_amount, lines.data.invoice.currency, 4)}
                  </strong>
                </p>
                <p>
                  {t("Remaining credit amount")}
                  <strong className="mt-1 block">
                    {formatMoney(lines.data.remaining_amount, lines.data.invoice.currency, 4)}
                  </strong>
                </p>
              </div>
            )}
            <section className="space-y-3" aria-label={t("Credit positions")}>
              <h3 className="font-semibold">{t("Credit positions")}</h3>
              {draft.lines.map((position, index) => (
                <fieldset key={index} className="rounded-lg border border-border-default p-3">
                  <legend className="px-1 text-xs text-fg-muted">{index + 1}</legend>
                  <div className="grid items-end gap-3 sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)]">
                    <label className="min-w-0 text-sm">
                      {t("Invoice position")}
                      <select
                        aria-label={t("Invoice position")}
                        className="br-control mt-2 w-full"
                        required
                        value={position.invoice_line_id}
                        disabled={!lines.data || lines.loading || !!lines.error}
                        onChange={(e) => changePosition(index, { invoice_line_id: e.target.value })}
                      >
                        <option value="">{t("Select a record")}</option>
                        {lines.data?.positions.map((row) => (
                          <option
                            key={row.id}
                            value={row.id}
                            disabled={
                              Number(row.remaining) <= 0 ||
                              lines.data?.positions.some((p) => p.legacy_credit_ids.length > 0) ||
                              !!row.legacy_credit_ids.length ||
                              draft.lines.some(
                                (other, i) => i !== index && other.invoice_line_id === row.id,
                              )
                            }
                          >
                            {row.label} · {formatQuantity(row.remaining)} {row.unit} ·{" "}
                            {t("Remaining credit quantity")}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="min-w-0 text-sm">
                      {t("Quantity")}
                      <input
                        aria-label={t("Quantity")}
                        className="br-control mt-2 w-full"
                        required
                        inputMode="decimal"
                        value={position.quantity}
                        onChange={(e) => changePosition(index, { quantity: e.target.value })}
                      />
                    </label>
                    <label className="min-w-0 text-sm">
                      {t("Stated line amount")}
                      <input
                        aria-label={t("Stated line amount")}
                        className="br-control mt-2 w-full"
                        required
                        inputMode="decimal"
                        value={position.gross_amount}
                        onChange={(e) => changePosition(index, { gross_amount: e.target.value })}
                      />
                    </label>
                  </div>
                  {lines.data?.positions
                    .filter((row) => row.id === position.invoice_line_id)
                    .map((row) => (
                      <div key={row.id} className="mt-3 rounded-lg bg-surface-muted p-3 text-sm">
                        <p>
                          {t("Already credited")}: {formatQuantity(row.credited)} {row.unit} ·{" "}
                          {t("Remaining credit quantity")}: {formatQuantity(row.remaining)}{" "}
                          {row.unit}
                        </p>
                        {!!row.evidence.length && (
                          <details className="mt-2">
                            <summary className="cursor-pointer">{t("Prior credit notes")}</summary>
                            {row.evidence.map((e) => (
                              <button
                                type="button"
                                key={e.id}
                                className="mr-3 text-accent underline"
                                onClick={() => inspect({ kind: "document", id: e.id })}
                              >
                                {e.number}
                              </button>
                            ))}
                          </details>
                        )}
                      </div>
                    ))}
                  <button
                    type="button"
                    className="mt-3 text-sm text-fg-muted underline"
                    disabled={draft.lines.length === 1}
                    onClick={() => change({ lines: draft.lines.filter((_, i) => i !== index) })}
                  >
                    {t("Remove position")}
                  </button>
                </fieldset>
              ))}
              <button
                type="button"
                className="br-btn"
                disabled={!lines.data || !!lines.error}
                onClick={() =>
                  change({
                    lines: [
                      ...draft.lines,
                      { invoice_line_id: "", quantity: "", gross_amount: "" },
                    ],
                  })
                }
              >
                {t("Add credit position")}
              </button>
              {lines.data?.positions.some((row) => row.legacy_credit_ids.length > 0) && (
                <p role="status" className="text-sm text-fg-muted">
                  {t(
                    "Some positions have older credits without an invoice reference. Inspect those credits before continuing.",
                  )}
                </p>
              )}
              {lines.data?.positions.flatMap((row) =>
                row.legacy_credit_ids.map((id) => (
                  <button
                    key={`${row.id}-${id}`}
                    type="button"
                    className="br-btn mr-2"
                    onClick={() => inspect({ kind: "document", id })}
                  >
                    {row.label} · {t("Inspect")}
                  </button>
                )),
              )}
            </section>
            <div className="grid gap-4 sm:grid-cols-2">
              {field(t("Credit note number"), "number")}
              {field(t("Stated credit amount"), "gross_amount")}
              {field(t("Amount to offset against this invoice"), "allocation_amount")}
              {field(t("Effective time (UTC ISO, optional)"), "effective_at", false)}
            </div>
            {field(t("Credit reason"), "reason")}
            <p className="text-sm text-fg-muted">
              {t(
                "Enter 0 to leave the credit unsettled. Only the entered offset reduces this invoice; a refund is a separate action.",
              )}
            </p>
            <button
              type="submit"
              className="br-btn br-btn-primary"
              disabled={
                !draft.lines?.length ||
                draft.lines.some((row) => !row.invoice_line_id) ||
                lines.loading ||
                !!lines.error ||
                lines.data?.positions.some((row) => row.legacy_credit_ids.length > 0)
              }
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
                <p className="text-sm text-fg-muted">{t("New credit note")}</p>
                <h3 className="mt-2 text-xl font-semibold">{review.state.creation.number}</h3>
                <p className="mt-2">{review.state.context.party.name}</p>
                <button
                  className="mt-2 text-accent underline"
                  onClick={() => inspect({ kind: "document", id: review.state.context.invoice.id })}
                >
                  {t("Invoice")}: {review.state.context.invoice.number}
                </button>
              </section>
              <div className="divide-y divide-border-default rounded-lg border border-border-default px-4">
                {review.state.creation.selections.map((row) => (
                  <div
                    key={row.invoice_line_id}
                    className="flex flex-wrap justify-between gap-2 py-3 text-sm"
                  >
                    <div>
                      <strong>
                        {
                          review.state.context.positions.find((p) => p.id === row.invoice_line_id)
                            ?.label
                        }
                      </strong>
                      <p>
                        {formatQuantity(row.quantity)}{" "}
                        {
                          review.state.context.positions.find((p) => p.id === row.invoice_line_id)
                            ?.unit
                        }
                      </p>
                    </div>
                    <span>
                      {formatMoney(row.gross_amount, review.state.context.invoice.currency, 4)}
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-sm">
                <strong>{t("Credit reason")}: </strong>
                {review.state.creation.reason}
              </p>
              <dl className="grid gap-4 rounded-lg bg-surface-muted p-4 text-sm sm:grid-cols-2">
                {(
                  [
                    ["Stated credit amount", review.state.creation.gross_amount],
                    [
                      "Amount to offset against this invoice",
                      review.state.creation.allocation_amount,
                    ],
                    ["Open invoice amount", review.state.context.open_amount],
                    ["Invoice open after credit", review.state.invoice_after],
                    ["Credit remaining to settle", review.state.credit_open],
                  ] as [string, string][]
                ).map(([label, value]) => (
                  <div key={label}>
                    <dt className="text-fg-muted">{t(label)}</dt>
                    <dd className="mt-1 font-semibold">
                      {formatMoney(value, review.state.context.invoice.currency, 4)}
                    </dd>
                  </div>
                ))}
              </dl>
              <p className="text-sm">
                {t("Effective time")}:{" "}
                {review.state.creation.effective_at
                  ? formatDateTime(review.state.creation.effective_at)
                  : t("At confirmation")}
              </p>
              <p className="text-sm text-fg-muted">
                {t("Correct selected invoice positions. No goods are moved and no refund is sent.")}
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
              <>
                <button
                  className="br-btn br-btn-primary"
                  disabled={busy || !review}
                  onClick={confirm}
                >
                  {t("Confirm change")}
                </button>
                <button
                  className="br-btn"
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      await api.rejectProposal(tenant, proposal.id, null);
                      setProposal({ ...proposal, status: "rejected" });
                      settled();
                    })
                  }
                >
                  {t("Reject")}
                </button>
                <button className="br-btn" disabled={busy} onClick={edit}>
                  {t("Edit")}
                </button>
              </>
            )}
            {(uncertain || ["executing", "executed"].includes(proposal.status)) && (
              <button className="br-btn" disabled={busy} onClick={() => run(refresh)}>
                {t("Check outcome")}
              </button>
            )}
            {proposal.verification === "verified" && documentId && (
              <a
                className="br-btn"
                href={`/app/finance?${new URLSearchParams({ tenant, finance_view: "open-items", flow: review?.state.creation.direction === "purchase" ? "payable" : "receivable", entry: documentId })}`}
              >
                {t("Open credit note")}
              </a>
            )}
          </div>
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
