import { useEffect, useRef, useState } from "react";

import {
  deliveryActions,
  deliveryApi,
  supplyApi,
  type DeliveryProposal,
  type DeliveryRow,
} from "../api";
import { formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";

type SupplyReview = DeliveryProposal & {
  review: NonNullable<DeliveryProposal["review"]> & {
    state: {
      supplier_before: {
        quantity: string;
        received: string;
        open: string;
        customer_assigned: string;
        stock_replenishment: string;
        unassigned: string;
      };
      supplier_after: {
        customer_assigned: string;
        stock_replenishment: string;
        unassigned: string;
      };
    };
  };
};

export function SupplyAssignmentCard({
  tenant,
  supplier,
  settled,
}: {
  tenant: string;
  supplier: DeliveryRow;
  settled: () => void;
}) {
  const coverage = useRead(() => supplyApi.coverage(tenant, supplier.id), [tenant, supplier.id]);
  const demand = useRead(
    () => deliveryApi.register(tenant, "", 1, "open", "customer_delivery", "", { size: 50 }),
    [tenant, supplier.id],
  );
  const dialog = useRef<HTMLDialogElement>(null);
  const requestId = useRef(crypto.randomUUID());
  const [purpose, setPurpose] = useState<"customer_demand" | "stock_replenishment">(
    "customer_demand",
  );
  const [customer, setCustomer] = useState("");
  const [quantity, setQuantity] = useState("");
  const [proposal, setProposal] = useState<SupplyReview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const matchingDemand = (demand.data?.items || []).filter(
    (row) => row.item_id === supplier.item_id && row.location_id === supplier.location_id,
  );
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const close = () => {
    dialog.current?.close();
    setProposal(null);
    setError("");
  };
  useEffect(() => {
    if (!customer && matchingDemand.length === 1) setCustomer(matchingDemand[0].id);
  }, [customer, matchingDemand]);
  const prepare = () =>
    run(async () => {
      const result = await supplyApi.prepare(tenant, requestId.current, {
        supplier_commitment_id: supplier.id,
        customer_commitment_id: purpose === "customer_demand" ? customer : undefined,
        purpose,
        quantity,
      });
      setProposal(result as SupplyReview);
    });
  const confirm = () =>
    run(async () => {
      if (!proposal?.review) return;
      await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
      await coverage.refresh();
      settled();
      close();
    });
  const summary = coverage.data?.supplier;
  return (
    <article className="rounded-xl border border-border-default bg-surface p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold text-fg-strong">{t("Planned supply use")}</h3>
          <p className="mt-1 text-sm text-fg-muted">
            {t(
              "See what this incoming quantity is intended to cover. This does not receive or reserve stock.",
            )}
          </p>
        </div>
        <button className="br-btn br-btn-primary" onClick={() => dialog.current?.showModal()}>
          {t("Assign supply")}
        </button>
      </div>
      {coverage.loading ? (
        <div className="mt-4">
          <ReadLine />
        </div>
      ) : coverage.error ? (
        <button className="br-btn mt-4" onClick={coverage.refresh}>
          {t("Retry")}
        </button>
      ) : summary ? (
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {[
            ["For customer orders", summary.customer_assigned],
            ["For stock", summary.stock_replenishment],
            ["Not assigned yet", summary.unassigned],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg bg-surface-muted p-4">
              <p className="text-xs text-fg-muted">{t(String(label))}</p>
              <strong className="mt-2 block text-lg">
                {formatQuantity(value)} {supplier.unit}
              </strong>
            </div>
          ))}
        </div>
      ) : null}
      <dialog
        ref={dialog}
        onCancel={(event) => {
          if (busy) event.preventDefault();
          else close();
        }}
        className="m-auto max-h-[90vh] w-[min(620px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-fg-strong">{t("Assign incoming supply")}</h2>
            <p className="mt-1 text-sm text-fg-muted">
              {supplier.item} · {supplier.counterparty}
            </p>
          </div>
          <button className="br-btn" disabled={busy} onClick={close}>
            {t("Close")}
          </button>
        </div>
        {!proposal ? (
          <form
            className="mt-6 space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              void prepare();
            }}
          >
            <fieldset className="space-y-2">
              <legend className="br-label">{t("Intended use")}</legend>
              <label className="flex gap-2">
                <input
                  type="radio"
                  checked={purpose === "customer_demand"}
                  onChange={() => setPurpose("customer_demand")}
                />{" "}
                {t("Cover a customer order")}
              </label>
              <label className="flex gap-2">
                <input
                  type="radio"
                  checked={purpose === "stock_replenishment"}
                  onChange={() => setPurpose("stock_replenishment")}
                />{" "}
                {t("Replenish stock")}
              </label>
            </fieldset>
            {purpose === "customer_demand" && (
              <label className="br-label">
                {t("Customer demand")}
                <select
                  className="br-control mt-2 w-full"
                  required
                  value={customer}
                  onChange={(event) => {
                    setCustomer(event.target.value);
                    requestId.current = crypto.randomUUID();
                  }}
                >
                  <option value="">{t("Choose customer order")}</option>
                  {matchingDemand.map((row) => (
                    <option key={row.id} value={row.id}>
                      {row.counterparty} · {formatQuantity(row.open)} {row.unit} · {row.id}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="br-label">
              {t("Quantity")}
              <input
                className="br-control mt-2 w-full"
                inputMode="decimal"
                required
                value={quantity}
                onChange={(event) => {
                  setQuantity(event.target.value);
                  requestId.current = crypto.randomUUID();
                }}
              />
            </label>
            <p className="rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
              {t(
                "Next you review the exact before-and-after quantities. Nothing changes until you confirm.",
              )}
            </p>
            {error && (
              <p role="alert" className="text-sm text-danger-text">
                {error}
              </p>
            )}
            <button
              className="br-btn br-btn-primary"
              disabled={busy || !quantity || (purpose === "customer_demand" && !customer)}
            >
              {t("Review assignment")}
            </button>
          </form>
        ) : (
          <div className="mt-6 space-y-5">
            <div className="rounded-lg bg-surface-muted p-4">
              <p className="font-medium">{t("After confirmation")}</p>
              <dl className="mt-3 space-y-2 text-sm">
                <div className="flex justify-between gap-4">
                  <dt>{t("Assigned now")}</dt>
                  <dd>
                    {formatQuantity(proposal.review.effect.assigned)} {supplier.unit}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt>{t("Not assigned afterward")}</dt>
                  <dd>
                    {formatQuantity(proposal.review.state.supplier_after.unassigned)}{" "}
                    {supplier.unit}
                  </dd>
                </div>
              </dl>
            </div>
            <p className="text-sm text-fg-muted">
              {t(
                "This records intent only. Receiving, inventory and reservation remain separate and traceable.",
              )}
            </p>
            {error && (
              <p role="alert" className="text-sm text-danger-text">
                {error}
              </p>
            )}
            <div className="flex gap-3">
              <button
                className="br-btn br-btn-primary"
                disabled={busy}
                onClick={() => void confirm()}
              >
                {t("Confirm assignment")}
              </button>
              <button className="br-btn" disabled={busy} onClick={() => setProposal(null)}>
                {t("Back")}
              </button>
            </div>
          </div>
        )}
      </dialog>
    </article>
  );
}
