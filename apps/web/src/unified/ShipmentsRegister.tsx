import { Fragment } from "react";
import { shipmentApi, type Page, type ShipmentRow } from "../api";
import { formatDateTime, formatQuantity, t } from "../localization";
import { InlineInspector, PreviewButton, TablePreview } from "./InlinePreview";
import { ReadState } from "./ReadState";
import { RegisterPager } from "./WarehousePage";
import { RegisterTable } from "./RegisterTable";
import { useRead } from "./useCompanyContext";
import type { Selection } from "./routing";

const cell = "px-4 py-4 text-sm align-top";
const heading = "px-4 py-3 text-left text-xs font-medium text-fg-muted";

function state(row: ShipmentRow) {
  if (row.observations.has_exception) return "Exception reported";
  if (row.observations.externally_delivered) return "Carrier reports delivered";
  if (row.observations.received) return "Received";
  if (row.observations.dispatched) return "Dispatched";
  return "Announced";
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
                  {packageRow?.carrier || "—"}
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
                  <div className="grid gap-4 md:grid-cols-2">
                    <section>
                      <h3 className="font-medium text-fg-strong">{t("Physical contents")}</h3>
                      <p className="mt-2 text-sm text-fg-muted">
                        {t("Promised")}: {row.quantities.promised ?? "—"} · {t("Dispatched")}:{" "}
                        {row.quantities.dispatched ?? "—"} · {t("Received")}:{" "}
                        {row.quantities.received ?? "—"}
                      </p>
                      {row.movements.length ? (
                        row.movements.map((movement) => (
                          <p key={movement.id} className="mt-2 text-sm">
                            <span data-localization="original">{movement.item_id}</span>:{" "}
                            {formatQuantity(movement.quantity)} · {t(movement.type)}
                          </p>
                        ))
                      ) : (
                        <p className="mt-2 text-sm text-fg-muted">
                          {t("No stock movement recorded")}
                        </p>
                      )}
                    </section>
                    <section>
                      <h3 className="font-medium text-fg-strong">{t("Tracking observations")}</h3>
                      {row.events.map((event) => (
                        <p key={event.id} className="mt-2 text-sm">
                          {t(event.event_type)} · {t(event.reporter_type)}
                          {event.occurred_at ? ` · ${formatDateTime(event.occurred_at)}` : ""}
                        </p>
                      ))}
                      {(row.discrepancies.external_delivery_without_warehouse_receipt ||
                        row.discrepancies.warehouse_receipt_without_external_delivery) && (
                        <p className="mt-2 text-sm text-warning-text">
                          {t("Warehouse and carrier observations differ")}
                        </p>
                      )}
                    </section>
                  </div>
                </InlineInspector>
              </TablePreview>
            </Fragment>
          );
        })}
      </tbody>
    </RegisterTable>
  );
}
