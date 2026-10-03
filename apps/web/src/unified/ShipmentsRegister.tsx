import { Fragment } from "react";
import { shipmentApi, type Page, type ShipmentRow } from "../api";
import { formatDateTime, t } from "../localization";
import { InlineInspector, PreviewButton, TablePreview } from "./InlinePreview";
import { ReadState } from "./ReadState";
import { RegisterPager } from "./WarehousePage";
import { RegisterTable } from "./RegisterTable";
import { useRead } from "./useCompanyContext";
import type { Selection } from "./routing";

const cell = "px-4 py-4 text-sm align-top";
const heading = "px-4 py-3 text-left text-xs font-medium text-fg-muted";

const FAILURE_LABELS = {
  undeliverable: "Came back undeliverable",
  refused: "Delivery refused",
  lost: "Lost in transit",
} as const;

function state(row: ShipmentRow) {
  if (row.delivery_failure) return FAILURE_LABELS[row.delivery_failure.kind];
  if (row.observations.has_exception) return "Exception reported";
  if (row.observations.externally_delivered) return "Carrier reports delivered";
  if (row.observations.received) return "Received";
  if (row.observations.dispatched) return "Dispatched";
  return "Announced";
}

/** Spec 338: the total of one advised quantity across a shipment's purchase lines. */
function sumOf(
  advice: NonNullable<ShipmentRow["advice"]>,
  key: "advised" | "received" | "in_transit",
): number {
  return advice.reduce((total, line) => total + Number(line[key]), 0);
}
export function ShipmentsRegister({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const direction = selection.deliveryType === "supplier_delivery" ? "inbound" : "outbound";
  const read = useRead(
    () =>
      shipmentApi.list(
        selection.tenant,
        selection.q,
        selection.page,
        direction,
        selection.deliveryType,
        "",
        selection.tableSize,
      ),
    [
      selection.tenant,
      selection.q,
      selection.page,
      direction,
      selection.deliveryType,
      selection.tableSize,
    ],
  );
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={8} />;
  return (
    <RegisterTable
      busy={read.loading}
      className="w-full min-w-[850px] border-collapse"
      footer={
        <RegisterPager
          page={read.data.page as Page}
          change={(page) => navigate({ page, entry: "" })}
        />
      }
    >
      <thead className="bg-surface-muted">
        <tr>
          {[
            "Created",
            "Direction",
            "Purpose",
            "Carrier",
            "Tracking number",
            "Contents",
            "Observed state",
            "Actions",
          ].map((label) => (
            <th key={label} className={heading}>
              {t(label)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-border-default">
        {read.data.items.map((row) => {
          const packageRow = row.packages[0];
          return (
            <Fragment key={row.id}>
              <tr data-shipment-row={row.id}>
                <td className={cell}>{formatDateTime(row.created_at)}</td>
                <td className={cell}>{t(row.direction === "inbound" ? "Incoming" : "Outgoing")}</td>
                <td className={cell}>{t(row.purpose)}</td>
                <td className={cell} data-localization="original">
                  {row.delivery_mode === "pickup" ? t("Pickup") : packageRow?.carrier || "—"}
                </td>
                <td className={cell} data-localization="original">
                  {packageRow?.tracking_number || "—"}
                </td>
                <td className={cell}>{row.movements.length}</td>
                <td className={cell}>{t(state(row))}</td>
                <td className={cell}>
                  <PreviewButton
                    open={selection.entry === row.id}
                    controls={`shipment-preview-${row.id}`}
                    label={packageRow?.tracking_number || row.id}
                    toggle={() => navigate({ entry: selection.entry === row.id ? "" : row.id })}
                  />
                </td>
              </tr>
              <TablePreview
                id={`shipment-preview-${row.id}`}
                open={selection.entry === row.id}
                columns={8}
              >
                <InlineInspector
                  tenant={selection.tenant}
                  target={{ kind: "shipment", id: row.id }}
                >
                  {row.delivery_mode === "pickup" && (
                    <p className="text-sm" data-shipment-pickup>
                      {t("Collected by the customer")}
                      {row.collected_by ? `: ${row.collected_by}` : ""}
                    </p>
                  )}
                  {row.delivery_failure && (
                    <p className="text-sm text-warning-text" data-shipment-failure>
                      {t(FAILURE_LABELS[row.delivery_failure.kind])} ·{" "}
                      {formatDateTime(row.delivery_failure.occurred_at)}
                      {" · "}
                      <span data-localization="original">{row.delivery_failure.reason}</span>
                    </p>
                  )}
                  {!!row.address && Object.keys(row.address).length > 0 && (
                    <p className="text-sm" data-shipment-address>
                      {t("Delivered to")}{" "}
                      <span data-localization="original">
                        {["name", "street", "postal_code", "city", "country"]
                          .map((key) => row.address?.[key])
                          .filter(Boolean)
                          .join(", ")}
                      </span>
                    </p>
                  )}
                  {row.slot && (
                    <p className="text-sm" data-shipment-slot>
                      {t("Booked slot")} {formatDateTime(row.slot.from)} –{" "}
                      {formatDateTime(row.slot.until)}
                    </p>
                  )}
                  {row.moved_at && (
                    <p className="text-sm" data-shipment-timing>
                      {t("Goods moved at")} {formatDateTime(row.moved_at)}
                      {row.confirmation_lag_seconds && row.recorded_at
                        ? ` · ${t("recorded")} ${formatDateTime(row.recorded_at)} (${t("confirmation lag")} ${row.confirmation_lag_seconds >= 3600 ? `${Math.round(row.confirmation_lag_seconds / 3600)} h` : `${Math.round(row.confirmation_lag_seconds / 60)} min`})`
                        : ""}
                    </p>
                  )}
                  {!!row.advice?.length && (
                    <p className="text-sm" data-shipment-advice>
                      {t("Advised")} {sumOf(row.advice, "advised")} · {t("received")}{" "}
                      {sumOf(row.advice, "received")}
                      {sumOf(row.advice, "in_transit") > 0
                        ? ` · ${t("in transit")} ${sumOf(row.advice, "in_transit")}`
                        : ""}
                    </p>
                  )}
                  {(row.discrepancies.external_delivery_without_warehouse_receipt ||
                    row.discrepancies.warehouse_receipt_without_external_delivery) && (
                    <p className="text-sm text-warning-text">
                      {t("Warehouse and carrier observations differ")}
                    </p>
                  )}
                </InlineInspector>
              </TablePreview>
            </Fragment>
          );
        })}
      </tbody>
    </RegisterTable>
  );
}
