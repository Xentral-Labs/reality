import { useEffect, useRef, useState } from "react";
import {
  api,
  deliveryActions,
  orderActions,
  type OrderInput,
  type OrderLineInput,
  type OrderProposal,
} from "../api";
import { formatMoney, formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";
import { useProposalRecovery } from "./useProposal";
import { Inspector } from "./Inspector";
import { DecisionActionBar, DecisionReviewHeader } from "./DecisionReview";

function ReferenceSelect({
  tenant,
  kind,
  label,
  value,
  seed,
  change,
}: {
  tenant: string;
  kind: string;
  label: string;
  value: string;
  seed?: string;
  change: (id: string) => void;
}) {
  const [query, setQuery] = useState("");
  const read = useRead(() => api.suggestions(tenant, kind, query), [tenant, kind, query]);
  return (
    <div className="min-w-0 space-y-2">
      <label className="block text-sm">
        {t(label)}
        <input
          className="br-control mt-2 w-full"
          aria-label={`${t("Search")} ${t(label)}`}
          placeholder={t("Search")}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="br-control mt-2 w-full"
          aria-label={t(label)}
          required
          value={value}
          onChange={(e) => change(e.target.value)}
        >
          <option value="">{t("Select a record")}</option>
          {value && !read.data?.items.some((row) => row.value === value) && (
            <option value={value}>{seed || value}</option>
          )}
          {read.data?.items.map((row) => (
            <option key={row.value} value={row.value}>
              {row.label} · {row.description}
            </option>
          ))}
        </select>
      </label>
      {read.loading && (
        <p className="text-xs text-fg-muted">
          <ReadLine />
        </p>
      )}
      {read.error && (
        <p role="alert">
          {read.error}{" "}
          <button type="button" className="br-btn" onClick={read.refresh}>
            {t("Retry")}
          </button>
        </p>
      )}
      {read.data && !read.data.items.length && (
        <p className="text-xs text-fg-muted">{t("No matching records")}</p>
      )}
    </div>
  );
}
const blankLine = (): OrderLineInput => ({
  item_id: "",
  quantity: "",
  unit_price: "",
  gross_amount: "",
});
export function OrderCard({
  tenant,
  proposalId = "",
  direction = "sales",
  close,
  prepared,
  settled,
}: {
  tenant: string;
  proposalId?: string;
  direction?: string;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true),
    request = useRef(crypto.randomUUID());
  const [draft, setDraft] = useState<OrderInput>({
    direction,
    number: "",
    company_party_id: "",
    counterparty_id: "",
    location_id: "",
    currency: "EUR",
    gross_amount: "",
    lines: [blankLine()],
  });
  const [proposal, setProposal] = useState<OrderProposal | null>(null),
    [editing, setEditing] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [uncertain, setUncertain] = useState(false);
  const [seeds, setSeeds] = useState<Record<string, string>>({}),
    [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);
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
      orderActions
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
    orderActions.detail,
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
  const change = (next: Partial<OrderInput>) => {
    setDraft((old) => ({ ...old, ...next }));
    request.current = crypto.randomUUID();
  };
  const lineChange = (index: number, next: Partial<OrderLineInput>) =>
    change({ lines: draft.lines.map((line, i) => (i === index ? { ...line, ...next } : line)) });
  const prepare = () =>
    run(async () => {
      const result = await orderActions.prepare(tenant, request.current, draft);
      if (alive.current) {
        setProposal(result);
        setEditing(false);
        prepared?.(result.id);
      }
    });
  const refresh = async () => {
    if (!proposal) return;
    const result = await orderActions.reconcile(tenant, proposal.id);
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
      setSeeds(
        Object.fromEntries(
          [
            ...Object.values(proposal.review.state.references),
            ...Object.values(proposal.review.state.items),
          ].map((row) => [row.id, row.name]),
        ),
      );
      request.current = crypto.randomUUID();
      setEditing(true);
      setProposal(null);
    });
  const input = (label: string, key: string, required = false, type = "text") => (
    <label className="block min-w-0 text-sm">
      {t(label)}
      <input
        className="br-control mt-2 w-full"
        aria-label={t(label)}
        type={type}
        required={required}
        value={String(draft[key] ?? "")}
        onChange={(e) => change({ [key]: e.target.value })}
      />
    </label>
  );
  const review = proposal?.review;
  const receipt = proposal?.receipt as { document_id?: string; commitment_ids?: string[] } | null;
  return (
    <dialog
      ref={dialog}
      aria-labelledby="order-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(940px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <DecisionReviewHeader
        category={proposal ? "Decision" : "Order"}
        title={
          proposal?.status === "proposed" && review
            ? review.state.creation.direction === "sales"
              ? "Confirm customer order"
              : "Confirm supplier order"
            : "New order"
        }
        close={close}
        busy={busy}
        titleId="order-title"
      />
      {!proposal ? (
        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            void prepare();
          }}
        >
          <fieldset
            disabled={busy || Boolean(proposalId && !editing)}
            className="min-w-0 space-y-5"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-sm">
                {t("Order direction")}
                <select
                  className="br-control mt-2 w-full"
                  aria-label={t("Order direction")}
                  value={draft.direction}
                  onChange={(e) => change({ direction: e.target.value, counterparty_id: "" })}
                >
                  <option value="sales">{t("Customer order")}</option>
                  <option value="purchase">{t("Supplier order")}</option>
                </select>
              </label>
              {input(t("Order number"), "number", true)}
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <ReferenceSelect
                tenant={tenant}
                kind="parties"
                label="Company party"
                value={draft.company_party_id}
                seed={seeds[draft.company_party_id]}
                change={(id) => change({ company_party_id: id })}
              />
              <ReferenceSelect
                tenant={tenant}
                kind="parties"
                label={draft.direction === "sales" ? "Customer" : "Supplier"}
                value={draft.counterparty_id}
                seed={seeds[draft.counterparty_id]}
                change={(id) => change({ counterparty_id: id })}
              />
              <ReferenceSelect
                tenant={tenant}
                kind="locations"
                label="Warehouse"
                value={draft.location_id}
                seed={seeds[draft.location_id]}
                change={(id) => change({ location_id: id })}
              />
            </div>
            <p className="text-sm text-fg-muted">
              {t("Enter the agreed amounts. Reality does not calculate prices, tax or totals.")}
            </p>
            <div className="space-y-4">
              {draft.lines.map((line, index) => (
                <fieldset
                  key={index}
                  className="min-w-0 rounded-lg border border-border-default p-4"
                >
                  <legend className="px-1 text-sm font-medium">
                    {t("Line")} {index + 1}
                  </legend>
                  <div className="grid gap-3 sm:grid-cols-[2fr_1fr_1fr_1fr]">
                    <ReferenceSelect
                      tenant={tenant}
                      kind="items"
                      label="Item"
                      value={line.item_id}
                      seed={seeds[line.item_id]}
                      change={(id) => lineChange(index, { item_id: id })}
                    />
                    {(
                      [
                        ["quantity", "Quantity"],
                        ["unit_price", "Unit price"],
                        ["gross_amount", "Stated line amount"],
                      ] as const
                    ).map(([key, label]) => (
                      <label
                        key={key}
                        className="min-w-0 text-sm sm:flex sm:flex-col sm:justify-end"
                      >
                        {t(label)}
                        <input
                          className="br-control mt-2 w-full"
                          aria-label={t(label)}
                          inputMode="decimal"
                          required
                          value={String(line[key])}
                          onChange={(e) => lineChange(index, { [key]: e.target.value })}
                        />
                      </label>
                    ))}
                  </div>
                  <details className="mt-3">
                    <summary className="cursor-pointer text-sm text-fg-muted">
                      {t("Line details")}
                    </summary>
                    <div className="mt-3 grid gap-3 sm:grid-cols-3">
                      {(
                        [
                          ["unit", "Unit"],
                          ["description", "Description"],
                          ["promised_at", "Requested date"],
                        ] as const
                      ).map(([key, label]) => (
                        <label key={key} className="text-sm">
                          {t(label)}
                          <input
                            className="br-control mt-2 w-full"
                            aria-label={t(label)}
                            value={String(line[key] ?? "")}
                            placeholder={key === "promised_at" ? t("YYYY-MM-DD") : ""}
                            onChange={(e) => lineChange(index, { [key]: e.target.value })}
                          />
                        </label>
                      ))}
                    </div>
                  </details>
                  <button
                    type="button"
                    className="br-btn mt-3"
                    disabled={draft.lines.length === 1}
                    onClick={() => change({ lines: draft.lines.filter((_, i) => i !== index) })}
                  >
                    {t("Remove line")}
                  </button>
                </fieldset>
              ))}
            </div>
            <button
              type="button"
              className="br-btn"
              onClick={() => change({ lines: [...draft.lines, blankLine()] })}
            >
              {t("Add line")}
            </button>
            <div className="grid gap-4 sm:grid-cols-2">
              {input(t("Currency"), "currency", true)}
              {input(t("Stated order total"), "gross_amount", true)}
            </div>
            <details>
              <summary className="cursor-pointer text-sm">{t("Order details")}</summary>
              <div className="mt-3 grid gap-4 sm:grid-cols-2">
                {input(t("Customer reference"), "customer_reference")}
                {input(t("Requested delivery date"), "requested_delivery_at")}
                {input(t("Document date"), "document_date")}
                {input(t("Sales channel"), "sales_channel")}
              </div>
            </details>
            <p className="text-sm text-fg-muted">
              {t("Creates the agreement and its deliveries. Stock and money remain unchanged.")}
            </p>
            <button className="br-btn br-btn-primary" type="submit">
              {t("Review change")}
            </button>
          </fieldset>
          {busy && <ReadLine />}
        </form>
      ) : (
        <div className="space-y-5">
          {review && (
            <>
              {proposal.status === "proposed" && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-accent">
                    {t("Decision required")}
                  </p>
                  <p className="mt-1 text-sm text-fg-muted">
                    {t("Check the order and its effect before you decide.")}
                  </p>
                </div>
              )}
              <div className="rounded-lg bg-surface-muted p-4">
                <p className="text-xs text-fg-muted">
                  {t(
                    review.state.creation.direction === "sales"
                      ? "Customer order"
                      : "Supplier order",
                  )}
                </p>
                <p className="mt-1 text-lg font-semibold">
                  {String(review.state.creation.document.number)}
                </p>
                <p className="mt-2 break-words">
                  {review.state.references.company_party_id?.name} →{" "}
                  {review.state.references.counterparty_id?.name}
                </p>
                <p className="mt-1 text-sm text-fg-muted">
                  {t("Warehouse")}: {review.state.references.location_id?.name}
                </p>
              </div>
              <div className="space-y-3">
                {review.state.creation.lines.map((line, index) => (
                  <div key={index} className="rounded-lg border border-border-default p-4">
                    <p className="font-medium">
                      {index + 1}. {review.state.items[line.item_id]?.name}
                    </p>
                    <p className="mt-1 break-words text-sm text-fg-muted">
                      {String(line.description || "")}
                    </p>
                    <div className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
                      <p>
                        {t("Quantity")}
                        <strong className="mt-1 block">
                          {formatQuantity(line.quantity)} {String(line.unit || "")}
                        </strong>
                      </p>
                      <p>
                        {t("Unit price")}
                        <strong className="mt-1 block">
                          {formatMoney(
                            line.unit_price,
                            String(review.state.creation.document.currency),
                          )}
                        </strong>
                      </p>
                      <p>
                        {t("Stated line amount")}
                        <strong className="mt-1 block">
                          {formatMoney(
                            line.gross_amount,
                            String(review.state.creation.document.currency),
                          )}
                        </strong>
                      </p>
                    </div>
                    {Boolean(line.promised_at) && (
                      <p className="mt-2 text-sm">
                        {t("Requested date")}: {String(line.promised_at)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-surface-muted p-4">
                <span>{t("Stated order total")}</span>
                <strong className="text-xl">
                  {formatMoney(
                    String(review.state.creation.document.gross_amount),
                    String(review.state.creation.document.currency),
                  )}
                </strong>
              </div>
              {Object.entries(review.intent)
                .filter(
                  ([key, value]) =>
                    ![
                      "direction",
                      "number",
                      "company_party_id",
                      "counterparty_id",
                      "location_id",
                      "currency",
                      "gross_amount",
                      "lines",
                    ].includes(key) &&
                    value !== null &&
                    value !== "",
                )
                .map(([key, value]) => (
                  <p key={key} className="break-words text-sm">
                    {t(
                      (
                        {
                          customer_reference: "Customer reference",
                          requested_delivery_at: "Requested delivery date",
                          document_date: "Document date",
                          sales_channel: "Sales channel",
                          payment_term_code: "Payment term",
                          ship_to_party_id: "Ship to",
                          ordered_at: "Order date",
                        } as Record<string, string>
                      )[key] || key,
                    )}
                    : {String(value)}
                  </p>
                ))}
              <section className="rounded-lg border border-border-default p-4">
                <h3 className="font-semibold text-fg-strong">
                  {t("What happens when you confirm?")}
                </h3>
                <p className="mt-2 text-sm text-fg-muted">
                  {t("Creates the agreement and its deliveries. Stock and money remain unchanged.")}
                </p>
              </section>
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
          {proposal.status === "proposed" && !uncertain ? (
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
              confirmLabel={
                review?.state.creation.direction === "purchase"
                  ? "Confirm supplier order"
                  : "Confirm customer order"
              }
            />
          ) : (
            <DecisionActionBar>
              {(uncertain || ["executing", "executed"].includes(proposal.status)) && (
                <button className="br-btn" disabled={busy} onClick={() => run(refresh)}>
                  {t("Check outcome")}
                </button>
              )}
              {proposal.verification === "verified" && receipt?.document_id && (
                <a
                  className="br-btn"
                  href={`/app/orders-deliveries?${new URLSearchParams({ tenant, orders_view: review?.intent.direction === "purchase" ? "supplier-orders" : "customer-orders", q: receipt.document_id })}`}
                >
                  {t("Open order")}
                </a>
              )}
            </DecisionActionBar>
          )}
          {proposal.verification === "verified" &&
            receipt?.commitment_ids?.map((id, index) => (
              <a
                key={id}
                className="block rounded-lg border border-border-default p-3 text-sm hover:bg-surface-muted"
                href={`/app/work?${new URLSearchParams({ tenant, commitment: id })}`}
              >
                {t("Open delivery")} · {t("Line")} {index + 1} →
              </a>
            ))}
          {proposal.observation?.deliveries.map((row) => (
            <p key={row.id} className="text-sm text-fg-muted">
              {row.item} · {t("Still open")}: {formatQuantity(row.open)}
            </p>
          ))}
          {proposal.links.map((link) => (
            <button key={link.id} className="br-btn mr-2" onClick={() => inspect(link)}>
              {t("Inspect")} · {t(link.kind)}
            </button>
          ))}
          <details>
            <summary className="cursor-pointer text-sm">{t("System details")}</summary>
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
