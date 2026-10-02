import { useEffect, useRef, useState } from "react";
import { deliveryActions, workspaceApi, type DeliveryProposal, type ReferenceRow } from "../api";
import { formatQuantity, t } from "../localization";
import { DecisionActionBar } from "./DecisionReview";
import { ReadLine } from "./ReadState";

// Spec 296: a shop order line whose SKU matched no item gets the item the shop meant.
// The shared reviewed tool creates the delivery promise; this card only prepares and confirms.

type Review = {
  token: string;
  state: {
    order_number: string;
    stated_sku: string;
    item_sku: string;
    quantity: string;
  };
};

export function OrderLineItemCard({
  tenant,
  documentLineId,
  customerItemNumber = "",
  close,
  settled,
}: {
  tenant: string;
  documentLineId: string;
  /** Spec 308: the customer number the line quotes, if any. */
  customerItemNumber?: string;
  close: () => void;
  settled: () => void;
}) {
  const requestId = useRef(crypto.randomUUID());
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<ReferenceRow[]>([]);
  const [itemId, setItemId] = useState("");
  const [proposal, setProposal] = useState<DeliveryProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      workspaceApi
        .references(tenant, "item", query, 1, false)
        .then((page) => active && setItems(page.items))
        .catch((reason) => active && setError(reason.message));
    }, 200);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [tenant, query]);

  const run = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await operation();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const [remember, setRemember] = useState(Boolean(customerItemNumber));
  const prepare = () =>
    run(async () => {
      setProposal(
        await deliveryActions.prepare(tenant, requestId.current, "order_line_item_assign", {
          document_line_id: documentLineId,
          item_id: itemId,
          ...(remember && customerItemNumber ? { remember_for_customer: true } : {}),
        }),
      );
    });

  const confirm = () =>
    run(async () => {
      if (!proposal?.review) return;
      await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
      setProposal(await deliveryActions.detail(tenant, proposal.id));
      settled();
    });

  const review = proposal?.review as unknown as Review | null | undefined;
  return (
    <dialog
      open
      aria-labelledby="order-line-item-title"
      className="m-auto max-h-[90vh] w-[min(560px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-6 flex items-center justify-between gap-4">
        <h2 id="order-line-item-title" className="text-xl font-semibold text-fg-strong">
          {t("Assign item")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      {!proposal ? (
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            void prepare();
          }}
        >
          <label className="br-label">
            {t("Search items")}
            <input
              className="br-control mt-2 w-full"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label className="br-label">
            {t("Item")}
            <select
              className="br-control mt-2 w-full"
              required
              value={itemId}
              onChange={(event) => {
                setItemId(event.target.value);
                requestId.current = crypto.randomUUID();
              }}
            >
              <option value="">{t("Choose an item")}</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.sku ? `${item.sku} · ` : ""}
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          {customerItemNumber && (
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={remember}
                onChange={(event) => {
                  setRemember(event.target.checked);
                  requestId.current = crypto.randomUUID();
                }}
              />
              {t("Remember for this customer")} ({customerItemNumber})
            </label>
          )}
          <p className="text-sm text-fg-muted">
            {t("Preparing a review changes nothing; confirming creates the delivery promise.")}
          </p>
          <button className="br-btn br-btn-primary self-start" disabled={busy || !itemId}>
            {t("Review change")}
          </button>
        </form>
      ) : (
        <div className="space-y-4">
          {review && (
            <dl className="grid grid-cols-2 gap-2 rounded-lg bg-surface-muted p-4 text-sm">
              <dt className="text-fg-muted">{t("Order")}</dt>
              <dd>{review.state.order_number}</dd>
              <dt className="text-fg-muted">{t("Stated SKU")}</dt>
              <dd>{review.state.stated_sku}</dd>
              <dt className="text-fg-muted">{t("Item")}</dt>
              <dd>{review.state.item_sku}</dd>
              <dt className="text-fg-muted">{t("Quantity")}</dt>
              <dd>{formatQuantity(review.state.quantity)}</dd>
            </dl>
          )}
          {proposal.status === "proposed" && (
            <DecisionActionBar
              nextStep={proposal.next_step}
              busy={busy}
              confirm={() => void confirm()}
            >
              <button className="br-btn" disabled={busy} onClick={close}>
                {t("Cancel")}
              </button>
            </DecisionActionBar>
          )}
          {proposal.status === "executing" && <ReadLine />}
          {proposal.status === "executed" && (
            <p role="status" className="rounded-lg bg-positive-surface p-4 font-medium">
              {t("Item assigned; the delivery promise was created.")}
            </p>
          )}
        </div>
      )}
      {error && (
        <p role="alert" className="mt-5 text-critical-text">
          {error}
        </p>
      )}
    </dialog>
  );
}
