import { useEffect, useRef, useState } from "react";
import { api, deliveryActions, type DeliveryProposal } from "../api";
import { t } from "../localization";
import type { DeliveryAction } from "./ActionLauncher";

type ShipmentTool = Extract<
  DeliveryAction,
  | "shipment_notice_record"
  | "shipment_dispatch"
  | "shipment_receive"
  | "shipment_event_record"
  | "shipment_event_supersede"
>;

export function ShipmentActions({
  tenant,
  tool,
  proposalId = "",
  close,
  prepared,
  settled,
}: {
  tenant: string;
  tool: ShipmentTool;
  proposalId?: string;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const requestId = useRef(crypto.randomUUID());
  const [proposal, setProposal] = useState<DeliveryProposal | null>(null);
  const [purpose, setPurpose] = useState(
    tool === "shipment_receive" ? "supplier_delivery" : "customer_delivery",
  );
  const [counterparty, setCounterparty] = useState("");
  const [carrier, setCarrier] = useState("");
  const [tracking, setTracking] = useState("");
  const [shipment, setShipment] = useState("");
  const [packageId, setPackageId] = useState("");
  const [eventType, setEventType] = useState("in_transit");
  const [reporter, setReporter] = useState("carrier");
  const [eventId, setEventId] = useState("");
  const [replacement, setReplacement] = useState("");
  const [reason, setReason] = useState("");
  const [movements, setMovements] = useState("[]");
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
      if (tool === "shipment_event_record") {
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
          ...(carrier ? { carrier } : {}),
          ...(tracking ? { tracking_number: tracking } : {}),
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
          {tool === "shipment_event_record" ? (
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
              <Field label="Carrier" value={carrier} set={setCarrier} />
              <Field label="Tracking number" value={tracking} set={setTracking} />
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
          <pre
            data-original-content
            className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-surface-muted p-4 text-xs"
          >
            {JSON.stringify(
              proposal.status === "executed" ? proposal.receipt : proposal.review,
              null,
              2,
            )}
          </pre>
          {proposal.status === "proposed" && (
            <div className="mt-4 flex gap-3">
              <button disabled={busy} className="br-btn br-btn-primary" onClick={confirm}>
                {t("Confirm")}
              </button>
              <button disabled={busy} className="br-btn" onClick={reject}>
                {t("Reject")}
              </button>
            </div>
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
