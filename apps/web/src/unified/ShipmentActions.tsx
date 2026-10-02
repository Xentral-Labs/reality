import { useEffect, useRef, useState } from "react";
import { api, deliveryActions, type DeliveryProposal } from "../api";
import { t } from "../localization";
import { BusinessFieldList, DecisionActionBar, TechnicalDetails } from "./DecisionReview";
import type { DeliveryAction } from "./ActionLauncher";

type ShipmentTool = Extract<
  DeliveryAction,
  | "shipment_notice_record"
  | "shipment_dispatch"
  | "shipment_receive"
  | "shipment_event_record"
  | "shipment_event_supersede"
  | "return_disposition"
  | "customer_exchange_record"
>;

export function ShipmentActions({
  tenant,
  tool,
  proposalId = "",
  close,
  prepared,
  settled,
  shipmentInput,
}: {
  tenant: string;
  tool: ShipmentTool;
  proposalId?: string;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
  shipmentInput?: {
    counterparty_id: string;
    movements: Record<string, string>[];
  };
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const requestId = useRef(crypto.randomUUID());
  const [proposal, setProposal] = useState<DeliveryProposal | null>(null);
  const [purpose, setPurpose] = useState(
    tool === "shipment_receive" ? "supplier_delivery" : "customer_delivery",
  );
  const [counterparty, setCounterparty] = useState(shipmentInput?.counterparty_id || "");
  const [carrier, setCarrier] = useState("");
  const [tracking, setTracking] = useState("");
  // Spec 312: a customer pickup, who collected, and when the goods actually moved.
  const [pickup, setPickup] = useState(false);
  const [collectedBy, setCollectedBy] = useState("");
  const [movedAt, setMovedAt] = useState("");
  const [shipment, setShipment] = useState("");
  const [packageId, setPackageId] = useState("");
  const [eventType, setEventType] = useState("in_transit");
  const [reporter, setReporter] = useState("carrier");
  const [eventId, setEventId] = useState("");
  const [replacement, setReplacement] = useState("");
  const [reason, setReason] = useState("");
  const [movements, setMovements] = useState(JSON.stringify(shipmentInput?.movements || []));
  const [returnMovement, setReturnMovement] = useState("");
  const [disposition, setDisposition] = useState("restock");
  const [quantity, setQuantity] = useState("");
  const [destination, setDestination] = useState("");
  const [announcement, setAnnouncement] = useState("");
  const [replacementItem, setReplacementItem] = useState("");
  const [replacementQuantity, setReplacementQuantity] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    dialog.current?.showModal();
    return () => previous?.focus();
  }, []);
  useEffect(() => {
    if (!proposalId) return;
    setBusy(true);
    deliveryActions
      .review(tenant, proposalId)
      .then(setProposal)
      .catch((failure) => setError(failure.message))
      .finally(() => setBusy(false));
  }, [tenant, proposalId]);

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const prepare = () =>
    run(async () => {
      let arguments_: Record<string, unknown>;
      if (tool === "customer_exchange_record") {
        arguments_ = {
          ...(announcement
            ? { return_announcement_id: announcement }
            : { return_movement_id: returnMovement }),
          quantity,
          replacement_item_id: replacementItem,
          replacement_quantity: replacementQuantity || quantity,
          reason,
        };
      } else if (tool === "return_disposition") {
        arguments_ = {
          return_movement_id: returnMovement,
          disposition,
          quantity,
          ...(destination ? { destination_location_id: destination } : {}),
          ...(reason ? { reason } : {}),
        };
      } else if (tool === "shipment_event_record") {
        arguments_ = {
          shipment_id: shipment,
          event_type: eventType,
          reporter_type: reporter,
          ...(packageId ? { shipment_package_id: packageId } : {}),
        };
      } else if (tool === "shipment_event_supersede") {
        arguments_ = {
          event_id: eventId,
          reason,
          ...(replacement ? { replacement_event_id: replacement } : {}),
        };
      } else {
        arguments_ = {
          purpose,
          counterparty_id: counterparty,
          ...(carrier && !pickup ? { carrier } : {}),
          ...(tracking && !pickup ? { tracking_number: tracking } : {}),
          ...(pickup ? { delivery_mode: "pickup" } : {}),
          ...(pickup && collectedBy ? { collected_by: collectedBy } : {}),
          ...(movedAt && tool !== "shipment_notice_record"
            ? { occurred_at: new Date(movedAt).toISOString() }
            : {}),
        };
        if (tool === "shipment_notice_record")
          arguments_.direction =
            purpose === "supplier_delivery" || purpose === "customer_return"
              ? "inbound"
              : "outbound";
        else {
          const parsed = JSON.parse(movements);
          if (!Array.isArray(parsed)) throw new Error(t("Movements must be a JSON array"));
          arguments_.movements = parsed;
        }
      }
      const result = await deliveryActions.prepare(tenant, requestId.current, tool, arguments_);
      setProposal(result);
      prepared?.(result.id);
    });
  const confirm = () =>
    run(async () => {
      if (!proposal?.review) return;
      await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
      const result = await deliveryActions.detail(tenant, proposal.id);
      setProposal(result);
      settled();
    });
  const reject = () =>
    run(async () => {
      if (!proposal) return;
      await api.rejectProposal(tenant, proposal.id, null);
      close();
    });

  return (
    <dialog
      ref={dialog}
      onCancel={close}
      className="m-auto w-[min(46rem,calc(100%-2rem))] rounded-xl border border-border-default bg-surface p-6 text-fg-default shadow-xl"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-fg-strong">{t(tool)}</h2>
          <p className="mt-1 text-sm text-fg-muted">
            {t("Prepare the exact shipment change, then review it before confirmation.")}
          </p>
        </div>
        <button className="br-btn" onClick={close}>
          {t("Close")}
        </button>
      </div>

      {!proposal && (
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {tool === "customer_exchange_record" ? (
            <>
              <Field label="Return movement ID" value={returnMovement} set={setReturnMovement} />
              <Field
                label="Return announcement ID (instead, to exchange in advance)"
                value={announcement}
                set={setAnnouncement}
              />
              <Field label="Exchanged quantity" value={quantity} set={setQuantity} />
              <Field label="Replacement item ID" value={replacementItem} set={setReplacementItem} />
              <Field
                label="Replacement quantity"
                value={replacementQuantity}
                set={setReplacementQuantity}
              />
              <label className="text-sm sm:col-span-2">
                {t("Reason")}
                <textarea
                  className="br-control mt-2 w-full"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
              <p className="rounded-lg bg-surface-muted p-3 text-sm text-fg-muted sm:col-span-2">
                {t(
                  "The replacement goes to the same customer free of charge. No credit note, invoice, payment or refund is created.",
                )}
              </p>
            </>
          ) : tool === "return_disposition" ? (
            <>
              <Field label="Return movement ID" value={returnMovement} set={setReturnMovement} />
              <Select
                label="Physical outcome"
                value={disposition}
                set={setDisposition}
                options={["restock", "quarantine_repair", "scrap_loss", "return_to_supplier"]}
              />
              <Field label="Quantity" value={quantity} set={setQuantity} />
              {(disposition === "restock" || disposition === "quarantine_repair") && (
                <Field label="Destination location ID" value={destination} set={setDestination} />
              )}
              {(disposition === "scrap_loss" || disposition === "return_to_supplier") && (
                <label className="text-sm sm:col-span-2">
                  {t("Reason")}
                  <textarea
                    className="br-control mt-2 w-full"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
              )}
              <p className="rounded-lg bg-surface-muted p-3 text-sm text-fg-muted sm:col-span-2">
                {t(
                  "This decides only what physically happens to the goods. Credit and refund remain separate.",
                )}
              </p>
            </>
          ) : tool === "shipment_event_record" ? (
            <>
              <Field label="Shipment ID" value={shipment} set={setShipment} />
              <Field label="Package ID (optional)" value={packageId} set={setPackageId} />
              <Select
                label="Event type"
                value={eventType}
                set={setEventType}
                options={[
                  "announced",
                  "handed_over",
                  "in_transit",
                  "delivered",
                  "delivery_exception",
                  "received",
                ]}
              />
              <Select
                label="Reporter"
                value={reporter}
                set={setReporter}
                options={["company", "counterparty", "carrier", "integration"]}
              />
            </>
          ) : tool === "shipment_event_supersede" ? (
            <>
              <Field label="Event ID" value={eventId} set={setEventId} />
              <Field
                label="Replacement event ID (optional)"
                value={replacement}
                set={setReplacement}
              />
              <label className="text-sm sm:col-span-2">
                {t("Reason")}
                <textarea
                  className="br-control mt-2 w-full"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
            </>
          ) : (
            <>
              <Select
                label="Purpose"
                value={purpose}
                set={setPurpose}
                options={
                  tool === "shipment_receive"
                    ? ["supplier_delivery", "customer_return"]
                    : tool === "shipment_dispatch"
                      ? ["customer_delivery", "supplier_return"]
                      : [
                          "customer_delivery",
                          "supplier_delivery",
                          "customer_return",
                          "supplier_return",
                        ]
                }
              />
              <Field label="Counterparty ID" value={counterparty} set={setCounterparty} />
              {tool === "shipment_dispatch" && purpose === "customer_delivery" && (
                <label className="flex items-center gap-2 text-sm sm:col-span-2">
                  <input
                    type="checkbox"
                    checked={pickup}
                    onChange={(e) => setPickup(e.target.checked)}
                  />
                  {t("Customer collects (pickup)")}
                </label>
              )}
              {pickup ? (
                <Field label="Collected by" value={collectedBy} set={setCollectedBy} />
              ) : (
                <>
                  <Field label="Carrier" value={carrier} set={setCarrier} />
                  <Field label="Tracking number" value={tracking} set={setTracking} />
                </>
              )}
              {tool !== "shipment_notice_record" && (
                <label className="text-sm">
                  {t("Goods moved at (optional)")}
                  <input
                    className="br-control mt-2 w-full"
                    type="datetime-local"
                    value={movedAt}
                    onChange={(e) => setMovedAt(e.target.value)}
                  />
                </label>
              )}
              {tool !== "shipment_notice_record" && (
                <label className="text-sm sm:col-span-2">
                  {t("Movement inputs (JSON)")}
                  <textarea
                    className="br-control mt-2 min-h-32 w-full font-mono text-xs"
                    value={movements}
                    onChange={(e) => setMovements(e.target.value)}
                  />
                </label>
              )}
            </>
          )}
          <div className="sm:col-span-2">
            <button disabled={busy} className="br-btn br-btn-primary" onClick={prepare}>
              {t("Review")}
            </button>
          </div>
        </div>
      )}

      {proposal && (
        <div className="mt-6">
          <p className="font-medium text-fg-strong">
            {t(proposal.status === "executed" ? "Recorded" : "Review exact effect")}
          </p>
          {tool === "customer_exchange_record" && proposal.review ? (
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <section className="rounded-lg bg-surface-muted p-4">
                <h3 className="font-medium text-fg-strong">{t("Returned goods")}</h3>
                <p className="mt-2 text-sm">
                  {t("Exchanged quantity")}: {String(proposal.review.effect.exchanged_quantity)}
                </p>
                <p className="mt-1 text-sm">
                  {t("Replaced delivery")}: {String(proposal.review.effect.returned_delivery_id)}
                </p>
              </section>
              <section className="rounded-lg bg-surface-muted p-4">
                <h3 className="font-medium text-fg-strong">{t("Replacement delivery")}</h3>
                <p className="mt-2 text-sm">
                  {t("Item")}:{" "}
                  {String(
                    (proposal.review.effect.replacement as unknown as Record<string, unknown>)
                      .item_id,
                  )}
                </p>
                <p className="mt-1 text-sm">
                  {t("Quantity")}:{" "}
                  {String(
                    (proposal.review.effect.replacement as unknown as Record<string, unknown>)
                      .quantity,
                  )}
                </p>
              </section>
              <section className="rounded-lg border border-border-default p-4 sm:col-span-2">
                <h3 className="font-medium text-fg-strong">{t("Money")}</h3>
                <p className="mt-2 text-sm text-fg-muted">
                  {t("No money moves: nothing is invoiced, credited, paid or refunded.")}
                </p>
              </section>
            </div>
          ) : tool === "return_disposition" && proposal.review ? (
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <section className="rounded-lg bg-surface-muted p-4">
                <h3 className="font-medium text-fg-strong">{t("Physical goods")}</h3>
                <p className="mt-2 text-sm">
                  {t("Outcome")}: {t(String(proposal.review.effect.disposition))}
                </p>
                <p className="mt-1 text-sm">
                  {t("Quantity")}: {String(proposal.review.effect.resolved)}
                </p>
                <p className="mt-1 text-sm">
                  {t("Still unresolved afterward")}:{" "}
                  {String(proposal.review.effect.unresolved_after)}
                </p>
              </section>
              <section className="rounded-lg border border-border-default p-4">
                <h3 className="font-medium text-fg-strong">{t("Credit or refund")}</h3>
                <p className="mt-2 text-sm text-fg-muted">
                  {t("Not changed here. Review the separate customer credit state in Finance.")}
                </p>
              </section>
            </div>
          ) : (
            <div className="mt-3 space-y-4">
              {proposal.status === "executed" ? (
                <BusinessFieldList record={proposal.receipt || {}} />
              ) : (
                <>
                  <section className="rounded-xl bg-surface-muted p-4">
                    <h3 className="font-medium">{t("Proposed change")}</h3>
                    <BusinessFieldList record={proposal.review?.intent || {}} />
                  </section>
                  <section className="rounded-xl bg-surface-muted p-4">
                    <h3 className="font-medium">{t("Prepared preview")}</h3>
                    <BusinessFieldList record={proposal.review?.effect || {}} />
                  </section>
                </>
              )}
              <TechnicalDetails
                value={proposal.status === "executed" ? proposal.receipt : proposal.review}
              />
            </div>
          )}
          {proposal.status === "proposed" && (
            <DecisionActionBar
              nextStep={proposal.next_step}
              busy={busy}
              reject={reject}
              confirm={confirm}
              confirmLabel="Confirm"
            />
          )}
        </div>
      )}
      {error && (
        <p role="alert" className="mt-4 text-critical-text">
          {error}
        </p>
      )}
    </dialog>
  );
}

function Field({
  label,
  value,
  set,
}: {
  label: string;
  value: string;
  set: (value: string) => void;
}) {
  return (
    <label className="text-sm">
      {t(label)}
      <input
        className="br-control mt-2 w-full"
        value={value}
        onChange={(e) => set(e.target.value)}
      />
    </label>
  );
}
function Select({
  label,
  value,
  set,
  options,
}: {
  label: string;
  value: string;
  set: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="text-sm">
      {t(label)}
      <select
        className="br-control mt-2 w-full"
        value={value}
        onChange={(e) => set(e.target.value)}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {t(option)}
          </option>
        ))}
      </select>
    </label>
  );
}
