import { useContextActions } from "./ActionLauncher";
import { PageActionBar } from "./PageActionBar";
import { isPurchasing } from "./pageIntroduction";
import { Fragment, useLayoutEffect, useRef, useState } from "react";
import { DeliveryCase } from "./DeliveryCase";
import { RegisterWorkbench, RegisterHeader, RegisterToolbar } from "./RegisterWorkbench";
import { useRegisterQuery } from "./TableContext";
import { RegisterTable } from "./RegisterTable";
import { api, deliveryApi, type DeliveryRow, type DocumentRow, type Page } from "../api";
import { Inspector } from "./Inspector";
import { SourceBadge } from "./SourceBadge";
import { formatDateTime, formatMoney, formatNumber, formatQuantity, t } from "../localization";
import { ReadState } from "./ReadState";
import { InlineInspector, PreviewButton, TablePreview } from "./InlinePreview";
import { RegisterPager } from "./WarehousePage";
import { useRead } from "./useCompanyContext";
import type { Selection } from "./routing";
import { ShipmentsRegister } from "./ShipmentsRegister";

type Register =
  | { view: "deliveries"; items: DeliveryRow[]; page: Page }
  | { view: "shipments"; items: never[]; page: Page }
  | { view: "customer-orders" | "supplier-orders"; items: DocumentRow[]; page: Page };
const numericHeader = "!text-right";
const cell = "px-4 py-4 text-sm align-top";
const headerCell = "px-4 py-3 text-left text-xs font-medium text-fg-muted";
function statusLabel(status: string) {
  return (
    (
      { open: t("Open"), fulfilled: t("Fulfilled"), cancelled: t("Cancelled") } as Record<
        string,
        string
      >
    )[status] || t("Unknown")
  );
}
export function OrdersPage({
  selection,
  navigate,
  receive,
  create,
}: {
  receive?: (id: string) => void;
  create?: (direction: string) => void;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const { tenant, ordersView, deliveryType, deliveryStatus, order, q, page, entry } = selection;
  const view = ordersView === "commitments" ? "deliveries" : ordersView;
  const purchasing = isPurchasing(selection);
  const orderActions = useContextActions(purchasing ? "purchasing.orders" : "sales.orders", {
    onOpen: () => create?.(purchasing ? "purchase" : "sales"),
  });
  const table = useRegisterQuery();
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  const listScroll = useRef(0);
  const openCommitment = (id: string) => {
    listScroll.current = window.scrollY;
    navigate({ commitment: id, entry: "", proposal: "" });
  };
  useLayoutEffect(() => {
    window.scrollTo(0, selection.commitment ? 0 : listScroll.current);
  }, [selection.commitment]);
  const read = useRead<Register>(async () => {
    if (view === "shipments")
      return {
        view,
        items: [],
        page: { total: 0, number: 1, size: 50, pages: 0, has_previous: false, has_next: false },
      };
    if (view === "deliveries")
      return {
        view,
        ...(await deliveryApi.register(
          tenant,
          q,
          page,
          deliveryStatus,
          deliveryType,
          order,
          table,
        )),
      };
    return {
      view,
      ...(await api.documents(
        tenant,
        q,
        view === "customer-orders" ? "sales_order" : "purchase_order",
        "",
        page,
        "",
        "",
        table,
      )),
    };
  }, [
    tenant,
    view,
    deliveryType,
    deliveryStatus,
    order,
    q,
    page,
    table.size,
    table.sort,
    table.sort_direction,
  ]);
  const data = read.data?.view === view ? read.data : null;
  const change = (values: Partial<Selection>) =>
    navigate({ ...values, page: 1, entry: "", commitment: "" });
  return (
    <>
      <div hidden={!!selection.commitment}>
        <RegisterWorkbench>
          <RegisterHeader title={purchasing ? "Purchasing" : "Sales"}>
            <div className="register-tabs">
              {(
                [
                  [
                    purchasing ? "supplier-orders" : "customer-orders",
                    purchasing ? "Supplier orders" : "Customer orders",
                  ],
                  ["deliveries", "Commitments"],
                  ["shipments", "Shipments"],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  className="br-btn aria-pressed:border-accent aria-pressed:bg-accent-soft"
                  aria-pressed={view === value}
                  onClick={() =>
                    change({
                      ordersView: value,
                      deliveryType: purchasing ? "supplier_delivery" : "customer_delivery",
                      order: "",
                      q: "",
                    })
                  }
                >
                  {t(label)}
                </button>
              ))}
            </div>
          </RegisterHeader>

          <section className="register-surface">
            <RegisterToolbar
              count={view === "shipments" ? undefined : data?.page.total}
              search={
                <label className="min-w-0 basis-full text-sm sm:basis-0 sm:flex-1">
                  {t("Search orders and deliveries")}
                  <input
                    className="br-control mt-2 w-full"
                    value={q}
                    maxLength={500}
                    onChange={(e) => change({ q: e.target.value })}
                    placeholder={t(
                      view === "deliveries"
                        ? "Search party, item or delivery ID"
                        : view === "shipments"
                          ? "Search carrier, tracking number or shipment ID"
                          : "Search document number, reference or source",
                    )}
                  />
                </label>
              }
              filters={
                <>
                  {view === "deliveries" && (
                    <>
                      <label className="min-w-0 text-sm">
                        {t("Delivery scope")}
                        <select
                          aria-label={t("Delivery scope")}
                          className="br-control mt-2 w-full"
                          value={deliveryStatus}
                          onChange={(e) =>
                            change({
                              deliveryStatus: e.target.value as Selection["deliveryStatus"],
                            })
                          }
                        >
                          <option value="open">{t("Open deliveries")}</option>
                          <option value="all">{t("All delivery history")}</option>
                        </select>
                      </label>
                    </>
                  )}
                </>
              }
            />
            <PageActionBar
              actions={!selection.commitment && create && view !== "deliveries" ? orderActions : []}
            />

            {view === "deliveries" && order && (
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-accent-soft p-4 text-sm">
                <span>{t("Commitments for the selected order")}</span>
                <button className="br-btn" onClick={() => change({ order: "" })}>
                  {t("Clear order filter")}
                </button>
              </div>
            )}
            {view === "shipments" ? (
              <ShipmentsRegister selection={selection} navigate={navigate} />
            ) : !data ? (
              <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={8} />
            ) : (
              <div className="min-w-0">
                {data.view === "deliveries" ? (
                  <RegisterTable
                    busy={read.loading}
                    className="w-full min-w-[850px] border-collapse"
                    footer={
                      <RegisterPager
                        page={data.page}
                        change={(page) => navigate({ page, entry: "" })}
                      />
                    }
                  >
                    <thead className="bg-surface-muted">
                      <tr>
                        {[
                          "Party",
                          "Item",
                          "Location",
                          "Due",
                          "Promised",
                          "Fulfilled",
                          "Remaining quantity",
                          "Status",
                          "Actions",
                        ].map((label) => (
                          <th
                            key={label}
                            className={`${headerCell} ${["Promised", "Fulfilled", "Remaining quantity", "Recorded amount", "Lines"].includes(label) ? numericHeader : ""}`}
                          >
                            {t(label)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-default">
                      {data.items.map((row) => (
                        <Fragment key={row.id}>
                          <tr data-orders-row={row.id}>
                            <td className={cell} data-original-content>
                              {row.counterparty || t("Unknown party")}
                            </td>
                            <td className={cell} data-original-content>
                              {row.item || t("Unknown item")}
                            </td>
                            <td className={cell} data-original-content>
                              {row.location || t("Unknown location")}
                            </td>
                            <td className={cell}>
                              {row.due_at ? formatDateTime(row.due_at) : t("No due date")}
                            </td>
                            {["promised", "fulfilled", "open"].map((key) => (
                              <td key={key} className={`${cell} text-right whitespace-nowrap`}>
                                {formatQuantity(row[key as "promised" | "fulfilled" | "open"])}{" "}
                                <span className="text-fg-muted">{row.unit}</span>
                              </td>
                            ))}
                            <td className={cell}>{statusLabel(row.status)}</td>
                            <td className={cell}>
                              <PreviewButton
                                open={entry === row.id}
                                controls={`order-preview-${row.id}`}
                                label={row.counterparty || row.id}
                                toggle={() => navigate({ entry: entry === row.id ? "" : row.id })}
                              />
                            </td>
                          </tr>
                          <TablePreview
                            id={`order-preview-${row.id}`}
                            open={entry === row.id}
                            columns={9}
                          >
                            <InlineInspector
                              tenant={tenant}
                              target={{ kind: "commitment", id: row.id }}
                            >
                              {row.type === "supplier_delivery" &&
                                row.status === "open" &&
                                receive && (
                                  <button
                                    className="br-btn"
                                    data-action-meaning="work"
                                    onClick={() => receive(row.id)}
                                  >
                                    {t("Receive goods")}
                                  </button>
                                )}
                              <button
                                className="br-btn"
                                data-action-meaning="navigate"
                                onClick={() => openCommitment(row.id)}
                              >
                                {t("Open commitment")}
                              </button>
                            </InlineInspector>
                          </TablePreview>
                        </Fragment>
                      ))}
                    </tbody>
                  </RegisterTable>
                ) : (
                  <RegisterTable
                    busy={read.loading}
                    className="w-full min-w-[800px] border-collapse"
                    footer={
                      <RegisterPager
                        page={data.page}
                        change={(page) => navigate({ page, entry: "" })}
                      />
                    }
                  >
                    <thead className="bg-surface-muted">
                      <tr>
                        {[
                          "Order document",
                          "Party",
                          "Date",
                          "Recorded amount",
                          "Lines",
                          "Origin",
                          "Actions",
                        ].map((label) => (
                          <th
                            key={label}
                            className={`${headerCell} ${["Promised", "Fulfilled", "Remaining quantity", "Recorded amount", "Lines"].includes(label) ? numericHeader : ""}`}
                          >
                            {t(label)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-default">
                      {data.items.map((row) => (
                        <Fragment key={row.id}>
                          <tr data-orders-row={row.id}>
                            <td className={cell}>
                              <p className="font-medium text-fg-strong">{row.number || row.id}</p>
                            </td>
                            <td className={cell}>{row.party || t("Unknown party")}</td>
                            <td className={cell}>{row.date || "—"}</td>
                            <td className={`${cell} text-right whitespace-nowrap`}>
                              {formatMoney(row.gross_amount, row.currency)}
                            </td>
                            <td className={`${cell} text-right`}>{formatNumber(row.line_count)}</td>
                            <td className={cell}>
                              <SourceBadge origin={row.origin} inspect={setTarget} />
                            </td>
                            <td className={cell}>
                              <PreviewButton
                                open={entry === row.id}
                                controls={`order-preview-${row.id}`}
                                label={row.number || row.id}
                                toggle={() => navigate({ entry: entry === row.id ? "" : row.id })}
                              />
                            </td>
                          </tr>
                          <TablePreview
                            id={`order-preview-${row.id}`}
                            open={entry === row.id}
                            columns={7}
                          >
                            <InlineInspector
                              tenant={tenant}
                              target={{ kind: "document", id: row.id }}
                            >
                              <button
                                className="br-btn"
                                data-action-meaning="filter"
                                onClick={() =>
                                  change({
                                    ordersView: "deliveries",
                                    order: row.id,
                                    deliveryType:
                                      view === "supplier-orders"
                                        ? "supplier_delivery"
                                        : "customer_delivery",
                                    deliveryStatus: "all",
                                    q: "",
                                  })
                                }
                              >
                                {t("View commitments")}
                              </button>
                            </InlineInspector>
                          </TablePreview>
                        </Fragment>
                      ))}
                    </tbody>
                  </RegisterTable>
                )}
              </div>
            )}
          </section>
        </RegisterWorkbench>
      </div>
      {selection.commitment && (
        <DeliveryCase
          key={selection.commitment}
          tenant={tenant}
          id={selection.commitment}
          navigate={navigate}
          receive={receive}
        />
      )}
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </>
  );
}
