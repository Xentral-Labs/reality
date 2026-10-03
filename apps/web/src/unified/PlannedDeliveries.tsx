import { useRef, useState } from "react";
import {
  api,
  deliveryActions,
  outboundDeliveries,
  type OutboundDeliveryLine,
  type OutboundDeliveryView,
} from "../api";
import { formatDateTime, formatQuantity, t } from "../localization";
import { useRead } from "./useCompanyContext";

type Pending = {
  delivery: string;
  kind: "pick" | "put_back" | "ship";
  proposal: string;
  token?: string;
  summary: string;
};

const open = (line: OutboundDeliveryLine) => line.promise_status === "open";

function addressLine(address: Record<string, string>) {
  return ["name", "street", "postal_code", "city", "country"]
    .map((key) => address[key])
    .filter(Boolean)
    .join(", ");
}

/**
 * Spec 334: the planned deliveries that have not shipped, with what is planned,
 * picked and waiting to be put back. Picking, putting back and shipping go
 * through the shared review: nothing moves before the person confirms, and a
 * review walked away from is withdrawn. Deliveries are planned and revised
 * through Chat, the CLI or the API.
 */
export function PlannedDeliveries({ tenant }: { tenant: string }) {
  const read = useRead(() => outboundDeliveries.list(tenant), [tenant]);
  const [pending, setPending] = useState<Pending | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    working = useRef(false);
  const rows = Array.isArray(read.data?.rows) ? read.data!.rows : [];
  if (!rows.length) return null;

  const run = async (action: () => Promise<void>) => {
    // A second click while the first request runs would leave a review behind.
    if (working.current) return;
    working.current = true;
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(t((failure as Error).message));
    } finally {
      working.current = false;
      setBusy(false);
    }
  };
  const withdraw = () =>
    run(async () => {
      if (pending) await api.rejectProposal(tenant, pending.proposal, null).catch(() => undefined);
      setPending(null);
    });
  const pick = (delivery: OutboundDeliveryView) =>
    run(async () => {
      const lines = delivery.lines
        .filter((line) => open(line) && Number(line.planned) > Number(line.picked))
        .map((line) => ({
          commitment_id: line.commitment_id,
          quantity: String(Number(line.planned) - Number(line.picked)),
        }));
      const proposal = await outboundDeliveries.pick(tenant, delivery.id, lines);
      setPending({
        delivery: delivery.id,
        kind: "pick",
        proposal: proposal.id,
        summary: `${t("Pick into")} ${delivery.staging_location}: ${lines
          .map((line) => formatQuantity(line.quantity))
          .join(", ")}`,
      });
    });
  const putBack = (delivery: OutboundDeliveryView) =>
    run(async () => {
      const detail = await outboundDeliveries.detail(tenant, delivery.id);
      // Waiting goods go back where they were picked from.
      const lines = detail.lines
        .filter((line) => Number(line.to_put_back) > 0)
        .map((line) => ({
          commitment_id: line.commitment_id,
          quantity: line.to_put_back,
          to_location_id:
            line.movements?.find((movement) => movement.kind === "pick")?.from_location_id ?? "",
        }));
      const proposal = await outboundDeliveries.putBack(tenant, delivery.id, lines);
      setPending({
        delivery: delivery.id,
        kind: "put_back",
        proposal: proposal.id,
        summary: `${t("Put back")}: ${lines.map((line) => formatQuantity(line.quantity)).join(", ")}`,
      });
    });
  const ship = (delivery: OutboundDeliveryView) =>
    run(async () => {
      const detail = await outboundDeliveries.detail(tenant, delivery.id);
      if (!detail.dispatch) return;
      const proposal = await deliveryActions.prepare(
        tenant,
        `ship-${delivery.id}-${Date.now()}`,
        "shipment_dispatch",
        detail.dispatch,
      );
      setPending({
        delivery: delivery.id,
        kind: "ship",
        proposal: proposal.id,
        token: proposal.review?.token,
        summary: `${t("Ship to")} ${delivery.recipient ?? ""}`,
      });
    });
  const confirm = () =>
    run(async () => {
      if (!pending) return;
      if (pending.kind === "ship" && pending.token)
        await deliveryActions.confirm(tenant, pending.proposal, pending.token);
      else await outboundDeliveries.confirm(tenant, pending.proposal);
      setPending(null);
      read.refresh();
    });

  return (
    <section
      className="mb-5 rounded-xl border border-border-default bg-surface p-4 text-sm"
      data-planned-deliveries
    >
      <h3 className="font-semibold text-fg-strong">{t("Planned deliveries")}</h3>
      <p className="mt-1 text-fg-muted">
        {t(
          "Planned before dispatch, with recipient, address and booked slot. Picking moves the goods and their reservation into the packing zone; nothing moves before you confirm. Plan or change a delivery through Chat.",
        )}
      </p>
      <ul className="mt-3 divide-y divide-border-default">
        {rows.map((delivery) => {
          const waiting = delivery.lines.some((line) => Number(line.to_put_back) > 0),
            toPick = delivery.lines.some(
              (line) => open(line) && Number(line.planned) > Number(line.picked),
            ),
            mine = pending?.delivery === delivery.id;
          return (
            <li key={delivery.id} className="py-3" data-planned-delivery={delivery.id}>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div>
                  <span className="font-medium text-fg-strong">
                    {delivery.recipient ?? delivery.customer}
                  </span>
                  {addressLine(delivery.address) && (
                    <span className="text-fg-muted" data-localization="original">
                      {" "}
                      · {addressLine(delivery.address)}
                    </span>
                  )}
                </div>
                <span className="rounded bg-surface-muted px-2 py-0.5 text-xs">
                  {delivery.state === "picked"
                    ? t("Picked")
                    : delivery.state === "picking"
                      ? t("Picking")
                      : t("Planned")}
                </span>
              </div>
              {delivery.slot && (
                <div
                  className={delivery.slot_passed ? "text-warning-text" : "text-fg-muted"}
                  data-planned-delivery-slot
                >
                  {t("Booked slot")} {formatDateTime(delivery.slot.from)} –{" "}
                  {formatDateTime(delivery.slot.until)}
                  {delivery.slot_passed ? ` · ${t("slot passed")}` : ""}
                </div>
              )}
              <table className="mt-2 w-full text-left">
                <thead className="text-fg-muted">
                  <tr>
                    <th className="py-1 pr-3 font-medium">{t("Item")}</th>
                    <th className="py-1 pr-3 text-right font-medium">{t("Planned")}</th>
                    <th className="py-1 pr-3 text-right font-medium">{t("Picked")}</th>
                    <th className="py-1 text-right font-medium">{t("To put back")}</th>
                  </tr>
                </thead>
                <tbody>
                  {delivery.lines.map((line) => (
                    <tr key={line.line_id} className="border-t border-border-default">
                      <td className="py-1 pr-3">
                        {line.item}
                        {line.document_number ? (
                          <span className="text-fg-muted"> · {line.document_number}</span>
                        ) : null}
                        {!open(line) && (
                          <span className="text-fg-muted"> · {t(line.promise_status)}</span>
                        )}
                      </td>
                      <td className="py-1 pr-3 text-right">
                        {formatQuantity(line.planned)} {line.unit}
                      </td>
                      <td className="py-1 pr-3 text-right">{formatQuantity(line.picked)}</td>
                      <td className="py-1 text-right">{formatQuantity(line.to_put_back)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {mine ? (
                <div className="mt-2 flex flex-wrap items-center justify-end gap-2">
                  <span className="mr-auto" data-planned-delivery-review>
                    {pending.summary}
                  </span>
                  <button className="br-btn" disabled={busy} onClick={withdraw}>
                    {t("Cancel")}
                  </button>
                  <button className="br-btn br-btn-primary" disabled={busy} onClick={confirm}>
                    {t("Confirm")}
                  </button>
                </div>
              ) : (
                <div className="mt-2 flex flex-wrap justify-end gap-2">
                  {delivery.staging_location_id && toPick && (
                    <button
                      className="br-btn"
                      disabled={busy || !!pending}
                      onClick={() => pick(delivery)}
                    >
                      {t("Pick")}
                    </button>
                  )}
                  {waiting && (
                    <button
                      className="br-btn"
                      disabled={busy || !!pending}
                      onClick={() => putBack(delivery)}
                    >
                      {t("Put back")}
                    </button>
                  )}
                  {!waiting && (!delivery.staging_location_id || !toPick) && (
                    <button
                      className="br-btn br-btn-primary"
                      disabled={busy || !!pending}
                      onClick={() => ship(delivery)}
                    >
                      {t("Ship")}
                    </button>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>
      {error && (
        <div role="alert" className="mt-3 text-danger">
          {error}
        </div>
      )}
    </section>
  );
}
