import { useEffect, useRef, useState } from "react";
import {
  api,
  deliveryActions,
  invoiceActions,
  workspaceApi,
  type InvoiceInput,
  type BillingAvailability,
  type BillablePositions,
  type InvoiceProposal,
  type ReferenceRow,
  type Page,
} from "../api";
import { formatMoney, formatQuantity, formatDateTime, t } from "../localization";
import { useRead } from "./useCompanyContext";
import { useProposalRecovery } from "./useProposal";
import { Inspector } from "./Inspector";
import { DecisionActionBar } from "./DecisionReview";
import { ReadLine, ReadState } from "./ReadState";
import { RegisterPager } from "./WarehousePage";
type InvoiceTool = "sales_invoice_record" | "supplier_invoice_record";
type InvoiceSource = "order" | "party";
const emptyPosition = () => [{ order_line_id: "", quantity: "", gross_amount: "" }];
export function InvoiceCard({
  tenant,
  proposalId = "",
  tool = "sales_invoice_record",
  close,
  prepared,
  settled,
  order = "",
}: {
  tenant: string;
  proposalId?: string;
  tool?: InvoiceTool;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
  order?: string;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true),
    request = useRef(crypto.randomUUID());
  const [activeTool, setActiveTool] = useState<InvoiceTool>(tool);
  const [draft, setDraft] = useState<InvoiceInput>({
    lines: [{ order_line_id: "", quantity: "", gross_amount: "" }],
    gross_amount: "",
    number: "",
  });
  const [proposal, setProposal] = useState<InvoiceProposal | null>(null),
    [editing, setEditing] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [uncertain, setUncertain] = useState(false);
  const [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);
  const [query, setQuery] = useState(""),
    [page, setPage] = useState(1),
    [orderId, setOrderId] = useState(order),
    [source, setSource] = useState<InvoiceSource>("order"),
    [partyQuery, setPartyQuery] = useState(""),
    [partyId, setPartyId] = useState(""),
    [partyName, setPartyName] = useState(""),
    [currency, setCurrency] = useState("EUR");
  const direction = activeTool === "sales_invoice_record" ? "sales" : "purchase";
  const parties = useRead(
    () =>
      source === "party"
        ? workspaceApi.references(
            tenant,
            direction === "sales" ? "customer" : "supplier",
            partyQuery,
            1,
            false,
            { size: 25 },
          )
        : Promise.resolve(null),
    [tenant, source, direction, partyQuery],
  );
  const billable = useRead(
    () =>
      source === "party" && partyId && currency
        ? invoiceActions.billable(tenant, direction, partyId, currency)
        : Promise.resolve(null),
    [tenant, source, direction, partyId, currency],
  );
  const selected = (id: string) => draft.lines?.find((row) => row.order_line_id === id);
  const togglePosition = (id: string, quantity: string) =>
    change({
      lines: selected(id)
        ? (draft.lines || []).filter((row) => row.order_line_id !== id)
        : [...(draft.lines || []), { order_line_id: id, quantity, gross_amount: "" }],
    });
  const changeSelected = (id: string, next: Partial<NonNullable<InvoiceInput["lines"]>[number]>) =>
    change({
      lines: draft.lines?.map((row) => (row.order_line_id === id ? { ...row, ...next } : row)),
    });
  const orders = useRead(
    () =>
      api.documents(
        tenant,
        query,
        activeTool === "sales_invoice_record" ? "sales_order" : "purchase_order",
        "",
        page,
      ),
    [tenant, query, activeTool, page],
  );
  const lines = useRead(
    () => (orderId ? api.inspector(tenant, "document", orderId) : Promise.resolve(null)),
    [tenant, orderId],
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
      invoiceActions
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
    invoiceActions.detail,
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
  const change = (next: Partial<InvoiceInput>) => {
    setDraft((old) => ({ ...old, ...next }));
    request.current = crypto.randomUUID();
  };
  const changePosition = (
    index: number,
    next: Partial<NonNullable<InvoiceInput["lines"]>[number]>,
  ) => change({ lines: draft.lines?.map((row, i) => (i === index ? { ...row, ...next } : row)) });
  const prepare = () =>
    run(async () => {
      const result = await invoiceActions.prepare(
        tenant,
        request.current,
        activeTool,
        Object.fromEntries(
          Object.entries(draft).filter(([key, value]) => key !== "effective_at" || !!value),
        ) as InvoiceInput,
      );
      if (alive.current) {
        setProposal(result);
        setEditing(false);
        prepared?.(result.id);
      }
    });
  const refresh = async () => {
    if (!proposal) return;
    const result = await invoiceActions.reconcile(tenant, proposal.id);
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
      const { order_line_id, quantity, ...rest } = original;
      setDraft({
        ...rest,
        lines: original.lines || [
          {
            order_line_id: order_line_id || "",
            quantity: quantity || "",
            gross_amount: original.gross_amount,
          },
        ],
      });
      setActiveTool(proposal.tool as InvoiceTool);
      if (proposal.review.state.order) {
        setSource("order");
        setOrderId(proposal.review.state.order.id);
      } else {
        setSource("party");
        setPartyId(proposal.review.state.party.id || "");
        setPartyName(proposal.review.state.party.name);
        setCurrency(proposal.review.state.creation.currency);
      }
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
      aria-labelledby="invoice-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(760px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="invoice-title" className="text-xl font-semibold text-fg-strong">
          {t("New invoice")}
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
            <label className="block text-sm">
              {t("Invoice type")}
              <select
                className="br-control mt-2 w-full"
                aria-label={t("Invoice type")}
                value={activeTool}
                onChange={(e) => {
                  setActiveTool(e.target.value as InvoiceTool);
                  setOrderId("");
                  setPartyId("");
                  setPartyName("");
                  setPage(1);
                  change({ lines: source === "order" ? emptyPosition() : [] });
                }}
              >
                <option value="sales_invoice_record">{t("Customer invoice")}</option>
                <option value="supplier_invoice_record">{t("Supplier invoice")}</option>
              </select>
            </label>
            <label className="block text-sm">
              {t("Collect positions")}
              <select
                className="br-control mt-2 w-full"
                aria-label={t("Collect positions")}
                value={source}
                onChange={(e) => {
                  const next = e.target.value as InvoiceSource;
                  setSource(next);
                  setOrderId("");
                  setPartyId("");
                  setPartyName("");
                  change({ lines: next === "order" ? emptyPosition() : [] });
                }}
              >
                <option value="order">{t("From one order")}</option>
                <option value="party">{t("From a party's deliveries")}</option>
              </select>
            </label>
            <p className="rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
              {t(
                "Select positions and enter the quantity to invoice now. You can invoice the remaining quantity later.",
              )}
            </p>
            {source === "party" ? (
              <PartyPositions
                parties={parties}
                billable={billable}
                partyQuery={partyQuery}
                setPartyQuery={setPartyQuery}
                partyId={partyId}
                partyName={partyName}
                choose={(id, name) => {
                  setPartyId(id);
                  setPartyName(name);
                  change({ lines: [] });
                }}
                currency={currency}
                setCurrency={(value) => {
                  setCurrency(value);
                  change({ lines: [] });
                }}
                selected={selected}
                toggle={togglePosition}
                changeSelected={changeSelected}
                inspect={inspect}
              />
            ) : (
              <>
                <label className="block text-sm">
                  {t("Search orders")}
                  <input
                    className="br-control mt-2 w-full"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setPage(1);
                      setOrderId("");
                      change({ lines: [{ order_line_id: "", quantity: "", gross_amount: "" }] });
                    }}
                  />
                </label>
                <label className="block text-sm">
                  {t("Order")}
                  <select
                    aria-label={t("Order")}
                    className="br-control mt-2 w-full"
                    required
                    value={orderId}
                    onChange={(e) => {
                      setOrderId(e.target.value);
                      change({ lines: [{ order_line_id: "", quantity: "", gross_amount: "" }] });
                    }}
                  >
                    <option value="">{t("Select a record")}</option>
                    {orderId && !orders.data?.items.some((r) => r.id === orderId) && (
                      <option value={orderId}>{orderId}</option>
                    )}
                    {orders.data?.items.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.number} · {r.party} · {formatMoney(r.gross_amount, r.currency)}
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
                  <RegisterPager
                    page={orders.data.page}
                    change={(value) => {
                      setPage(value);
                      setOrderId("");
                      change({ lines: [{ order_line_id: "", quantity: "", gross_amount: "" }] });
                    }}
                  />
                )}
                <section className="space-y-3" aria-label={t("Invoice positions")}>
                  <h3 className="font-semibold">{t("Invoice positions")}</h3>
                  {(draft.lines || []).map((position, index) => (
                    <fieldset key={index} className="rounded-lg border border-border-default p-3">
                      <legend className="px-1 text-xs text-fg-muted">{index + 1}</legend>
                      <div className="grid items-end gap-3 sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)]">
                        <label className="min-w-0 text-sm">
                          {t("Order line")}
                          <select
                            className="br-control mt-2 w-full"
                            aria-label={t("Order line")}
                            required
                            value={position.order_line_id}
                            disabled={!orderId || lines.loading || !!lines.error}
                            onChange={(e) =>
                              changePosition(index, { order_line_id: e.target.value })
                            }
                          >
                            <option value="">{t("Select a record")}</option>
                            {lines.data?.evidence_lines?.map((row) => (
                              <option
                                key={row.id}
                                value={row.id}
                                disabled={
                                  row.billing?.can_invoice === false ||
                                  draft.lines?.some(
                                    (other, i) => i !== index && other.order_line_id === row.id,
                                  )
                                }
                              >
                                {row.label} ·{" "}
                                {formatQuantity(row.billing?.remaining ?? row.quantity)} {row.unit}
                                {row.billing ? ` · ${t("Remaining billable")}` : ""}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="min-w-0 text-sm">
                          {t("Quantity")}
                          <input
                            className="br-control mt-2 w-full"
                            aria-label={t("Quantity")}
                            required
                            inputMode="decimal"
                            value={position.quantity}
                            onChange={(e) => changePosition(index, { quantity: e.target.value })}
                          />
                        </label>
                        <label className="min-w-0 text-sm">
                          {t("Stated line amount")}
                          <input
                            className="br-control mt-2 w-full"
                            aria-label={t("Stated line amount")}
                            required
                            inputMode="decimal"
                            value={position.gross_amount}
                            onChange={(e) =>
                              changePosition(index, { gross_amount: e.target.value })
                            }
                          />
                        </label>
                      </div>
                      {lines.data?.evidence_lines
                        ?.filter((row) => row.id === position.order_line_id && row.billing)
                        .map((row) => (
                          <InvoiceAvailability
                            key={row.id}
                            value={row.billing!}
                            inspect={inspect}
                          />
                        ))}
                      <button
                        type="button"
                        className="mt-3 text-sm text-fg-muted underline"
                        disabled={draft.lines?.length === 1}
                        onClick={() =>
                          change({ lines: draft.lines?.filter((_, i) => i !== index) })
                        }
                      >
                        {t("Remove position")}
                      </button>
                    </fieldset>
                  ))}
                  <button
                    type="button"
                    className="br-btn"
                    disabled={!orderId}
                    onClick={() =>
                      change({
                        lines: [
                          ...(draft.lines || []),
                          { order_line_id: "", quantity: "", gross_amount: "" },
                        ],
                      })
                    }
                  >
                    {t("Add invoice position")}
                  </button>
                </section>
                {orderId && (lines.loading || lines.error) && (
                  <ReadState loading={lines.loading} error={lines.error} retry={lines.refresh} />
                )}
              </>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              {field(t("Invoice number"), "number")}
              {field(t("Stated invoice amount"), "gross_amount")}
              {field(t("Effective time (UTC ISO, optional)"), "effective_at", false)}
            </div>
            <p className="text-sm text-fg-muted">
              {t(
                "Enter the invoice amount as stated. Recording also posts the receivable or payable; it does not record payment or move goods.",
              )}
            </p>
            <button
              type="submit"
              className="br-btn br-btn-primary"
              disabled={
                !draft.lines?.length ||
                draft.lines.some((row) => !row.order_line_id) ||
                (source === "order" ? lines.loading || !!lines.error : billable.loading)
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
                <p className="text-xs text-fg-muted">
                  {t(
                    review.state.creation.direction === "sales"
                      ? "Customer invoice"
                      : "Supplier invoice",
                  )}
                </p>
                <h3 className="mt-2 text-xl font-semibold">{review.state.creation.number}</h3>
                <p className="mt-2">{review.state.party.name}</p>
                {(review.state.orders ?? (review.state.order ? [review.state.order] : [])).map(
                  (order) => (
                    <button
                      key={order.id}
                      className="mt-2 mr-3 text-accent underline"
                      onClick={() => inspect({ kind: "document", id: order.id })}
                    >
                      {t("Order")}: {order.number}
                    </button>
                  ),
                )}
              </section>
              {review.state.positions ? (
                <div className="divide-y divide-border-default rounded-lg border border-border-default px-4">
                  {review.state.positions.map((row) => (
                    <div
                      key={row.order_line_id}
                      className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm"
                    >
                      <div>
                        <strong>{row.item.name}</strong>
                        <p className="text-fg-muted">
                          {formatQuantity(row.quantity)} {row.line.unit}
                        </p>
                      </div>
                      <span>
                        {formatMoney(row.gross_amount, review.state.creation.currency, 4)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p>
                  {review.state.item?.name} · {formatQuantity(review.state.creation.quantity)}{" "}
                  {review.state.creation.unit}
                </p>
              )}
              {review.state.billing?.map((row) => (
                <InvoiceAvailability
                  key={row.order_line_id}
                  value={row}
                  after={row.remaining_after}
                  inspect={inspect}
                />
              ))}
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span>{t("Stated invoice amount")}</span>
                <strong className="text-2xl">
                  {formatMoney(
                    review.state.creation.gross_amount,
                    review.state.creation.currency,
                    4,
                  )}
                </strong>
              </div>
              <p className="text-sm">
                {t("Effective time")}:{" "}
                {review.state.creation.effective_at
                  ? formatDateTime(review.state.creation.effective_at)
                  : t("At confirmation")}
              </p>
              <p className="text-sm text-fg-muted">
                {t(
                  review.state.creation.direction === "sales"
                    ? "Records the customer receivable and revenue."
                    : "Records the supplier payable and financial inventory posting.",
                )}
              </p>
              <p className="text-sm text-fg-muted">
                {t(
                  "Enter the invoice amount as stated. Recording also posts the receivable or payable; it does not record payment or move goods.",
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
            {proposal.verification === "verified" && documentId && (
              <a
                className="br-btn"
                href={`/app/finance?${new URLSearchParams({ tenant, finance_view: "open-items", flow: review?.state.creation.direction === "purchase" ? "payable" : "receivable", entry: documentId })}`}
              >
                {t("Open invoice")}
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

function InvoiceAvailability({
  value,
  after,
  inspect,
}: {
  value: BillingAvailability;
  after?: string;
  inspect: (target: { kind: string; id: string }) => void;
}) {
  return (
    <section
      className="mt-3 rounded-lg bg-surface-muted p-3 text-sm"
      aria-label={t("Billing availability")}
    >
      {after !== undefined && <p className="mb-2 font-medium">{value.label}</p>}
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {(
          [
            ["Ordered quantity", value.ordered],
            ["Already invoiced", value.invoiced],
            ["Remaining billable", value.remaining],
            ...(after === undefined ? [] : [["Remaining after this invoice", after]]),
          ] as [string, string][]
        ).map(([label, amount]) => (
          <div key={label}>
            <dt className="text-xs text-fg-muted">{t(label)}</dt>
            <dd className="mt-1 font-medium">
              {formatQuantity(amount)} {value.unit}
            </dd>
          </div>
        ))}
      </dl>
      {!!value.evidence.length && (
        <details className="mt-3">
          <summary className="cursor-pointer text-fg-muted">{t("Prior invoice evidence")}</summary>
          <ul className="mt-2 space-y-2">
            {value.evidence.map((row) => (
              <li key={row.invoice_line_id}>
                <button
                  type="button"
                  className="text-accent underline"
                  onClick={() => inspect({ kind: "document", id: row.invoice_id })}
                >
                  {row.number}
                </button>{" "}
                · {formatQuantity(row.quantity)} {value.unit}
                {row.released ? ` · ${t("Quantity released by reversal")}` : ""}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

type Read<T> = { data?: T; error?: string; loading: boolean; refresh: () => void };
type Position = NonNullable<InvoiceInput["lines"]>[number];

/** Spec 283: pick positions of several orders of one party for one invoice. */
function PartyPositions({
  parties,
  billable,
  partyQuery,
  setPartyQuery,
  partyId,
  partyName,
  choose,
  currency,
  setCurrency,
  selected,
  toggle,
  changeSelected,
  inspect,
}: {
  parties: Read<{ items: ReferenceRow[]; page: Page } | null>;
  billable: Read<BillablePositions | null>;
  partyQuery: string;
  setPartyQuery: (value: string) => void;
  partyId: string;
  partyName: string;
  choose: (id: string, name: string) => void;
  currency: string;
  setCurrency: (value: string) => void;
  selected: (id: string) => Position | undefined;
  toggle: (id: string, quantity: string) => void;
  changeSelected: (id: string, next: Partial<Position>) => void;
  inspect: (target: { kind: string; id: string }) => void;
}) {
  const shown = billable.data?.orders.reduce((sum, order) => sum + order.positions.length, 0) ?? 0;
  return (
    <>
      <label className="block text-sm">
        {t("Search parties")}
        <input
          className="br-control mt-2 w-full"
          value={partyQuery}
          onChange={(e) => setPartyQuery(e.target.value)}
        />
      </label>
      <div className="grid gap-4 sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <label className="block min-w-0 text-sm">
          {t("Party")}
          <select
            aria-label={t("Party")}
            className="br-control mt-2 w-full"
            required
            value={partyId}
            onChange={(e) =>
              choose(
                e.target.value,
                parties.data?.items.find((row) => row.id === e.target.value)?.name || "",
              )
            }
          >
            <option value="">{t("Select a record")}</option>
            {partyId && !parties.data?.items.some((row) => row.id === partyId) && (
              <option value={partyId}>{partyName || partyId}</option>
            )}
            {parties.data?.items.map((row) => (
              <option key={row.id} value={row.id}>
                {row.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block min-w-0 text-sm">
          {t("Currency")}
          <input
            className="br-control mt-2 w-full"
            aria-label={t("Currency")}
            required
            value={currency}
            onChange={(e) => setCurrency(e.target.value.toUpperCase())}
          />
        </label>
      </div>
      {parties.error && <ReadState loading={false} error={parties.error} retry={parties.refresh} />}
      <section className="space-y-3" aria-label={t("Billable positions")}>
        <h3 className="font-semibold">{t("Billable positions")}</h3>
        {partyId && (billable.loading || billable.error) && (
          <ReadState loading={billable.loading} error={billable.error} retry={billable.refresh} />
        )}
        {billable.data && !billable.data.orders.length && (
          <p role="status">{t("Nothing delivered is waiting to be invoiced for this party.")}</p>
        )}
        {billable.data && billable.data.total > shown && (
          <p className="text-sm text-fg-muted">
            {t("Showing {shown} of {total} billable positions.")
              .replace("{shown}", String(shown))
              .replace("{total}", String(billable.data.total))}
          </p>
        )}
        {billable.data?.orders.map((order) => (
          <fieldset key={order.id} className="rounded-lg border border-border-default p-3">
            <legend className="px-1 text-sm">
              <button
                type="button"
                className="text-accent underline"
                onClick={() => inspect({ kind: "document", id: order.id })}
              >
                {t("Order")}: {order.number}
              </button>
            </legend>
            {order.positions.map((row) => {
              const chosen = selected(row.order_line_id);
              return (
                <div
                  key={row.order_line_id}
                  className="border-t border-border-default py-3 first:border-t-0"
                >
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      aria-label={`${t("Include")} ${row.label}`}
                      checked={!!chosen}
                      onChange={() => toggle(row.order_line_id, row.billable)}
                    />
                    <span>
                      {row.label} · {formatQuantity(row.billable)} {row.unit} {t("billable")}
                    </span>
                  </label>
                  {chosen && (
                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      <label className="min-w-0 text-sm">
                        {t("Quantity")}
                        <input
                          className="br-control mt-2 w-full"
                          aria-label={t("Quantity")}
                          required
                          inputMode="decimal"
                          value={chosen.quantity}
                          onChange={(e) =>
                            changeSelected(row.order_line_id, { quantity: e.target.value })
                          }
                        />
                      </label>
                      <label className="min-w-0 text-sm">
                        {t("Stated line amount")}
                        <input
                          className="br-control mt-2 w-full"
                          aria-label={t("Stated line amount")}
                          required
                          inputMode="decimal"
                          value={chosen.gross_amount}
                          onChange={(e) =>
                            changeSelected(row.order_line_id, { gross_amount: e.target.value })
                          }
                        />
                      </label>
                    </div>
                  )}
                </div>
              );
            })}
          </fieldset>
        ))}
      </section>
    </>
  );
}
