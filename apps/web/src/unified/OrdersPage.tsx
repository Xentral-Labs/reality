import { SelectedRecordPreview } from "./SelectedRecordPreview";
import { useContextActions } from "./ActionLauncher";
import { PageActionBar } from "./PageActionBar";
import { isPurchasing } from "./pageIntroduction";
import { Fragment, useEffect, useLayoutEffect, useRef, useState } from "react";
import { DeliveryCase } from "./DeliveryCase";
import { RegisterWorkbench, RegisterHeader, RegisterToolbar } from "./RegisterWorkbench";
import { DocumentContributionExplanations } from "./DocumentContributionExplanations";
import { useRegisterQuery } from "./TableContext";
import { RegisterTable } from "./RegisterTable";
import { useWorkCount } from "./workCounts";
import { withWorkCount } from "./TabWorkCount";
import {
  api,
  deliveryApi,
  type DeliveryRow,
  type DocumentRow,
  type FulfillmentQueueRow,
  type Page,
  type ProjectionMetadata,
} from "../api";
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
  | {
      view: "readiness";
      items: FulfillmentQueueRow[];
      page: Page;
      metadata?: ProjectionMetadata;
    }
  | { view: "customer-orders" | "supplier-orders"; items: DocumentRow[]; page: Page };
const numericHeader = "!text-right";
const cell = "px-4 py-4 text-sm align-top";
const headerCell = "px-4 py-3 text-left text-xs font-medium text-fg-muted";
const freshnessReadyTone = "border-border-default bg-surface-muted";
const freshnessWarningTone = "border-warning-border bg-warning-soft";
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
function ProjectionFreshness({ metadata }: { metadata?: ProjectionMetadata }) {
  if (!metadata || metadata.state === "uninitialized")
    return (
      <p className="mb-4 rounded-lg border border-border-default bg-surface-muted px-4 py-3 text-sm">
        {t("Readiness is unavailable until the first projection completes.")}
      </p>
    );
  const pending = Math.max(
    0,
    metadata.target_event_sequence - (metadata.processed_event_sequence || 0),
  );
  let message = `${t("New business events are waiting for readiness refresh")}: ${formatNumber(pending)} (${metadata.processed_event_sequence || 0} → ${metadata.target_event_sequence}). ${t("The last completed snapshot is shown.")}`;
  if (metadata.state === "ready")
    message = `${t("Readiness observed at")} ${metadata.completed_at ? formatDateTime(metadata.completed_at) : "—"}`;
  if (metadata.state === "failed")
    message = t("The latest readiness refresh failed; the last completed snapshot is shown.");
  const tone = metadata.state === "ready" ? freshnessReadyTone : freshnessWarningTone;
  return <p className={`mb-4 rounded-lg border px-4 py-3 text-sm ${tone}`}>{message}</p>;
}

function lineBlockerExplanation(line: FulfillmentQueueRow["lines"][number], code: string) {
  if (code === "insufficient_reservation")
    return `${formatQuantity(line.reserved_quantity)} ${line.unit} ${t("of")} ${formatQuantity(line.open_quantity)} ${line.unit} ${t("reserved")}`;
  if (code === "insufficient_stock")
    return `${formatQuantity(line.physical_quantity)} ${line.unit} ${t("of")} ${formatQuantity(line.open_quantity)} ${line.unit} ${t("physically available")}`;
  if (code === "prepayment_required" && line.fulfillment_readiness)
    return `${formatMoney(line.fulfillment_readiness.remaining_amount, line.fulfillment_readiness.currency)} ${t("prepayment remaining")}`;
  const labels: Record<string, string> = {
    prepayment_invoice_missing: "Prepayment invoice evidence is missing",
    prepayment_attribution_ambiguous: "Prepayment cannot be attributed unambiguously",
    commitment_hold: "Commitment is on hold",
    party_delivery_hold: "Customer delivery is on hold",
  };
  return t(labels[code] || code);
}

function ReadinessBlockers({ row }: { row: FulfillmentQueueRow }) {
  const blockers = row.lines.flatMap((line) =>
    line.blocking_reasons.map((code) => ({ key: `${line.commitment_id}:${code}`, line, code })),
  );
  if (!blockers.length) return <>{t("None")}</>;
  return (
    <ul className="space-y-1">
      {blockers.map(({ key, line, code }) => (
        <li key={key}>{lineBlockerExplanation(line, code)}</li>
      ))}
    </ul>
  );
}

function ReadinessEvidence({
  row,
  inspect,
  prepareInvoice,
  prepareShipment,
  actionsCurrent,
}: {
  row: FulfillmentQueueRow;
  inspect: (target: { kind: string; id: string }) => void;
  prepareInvoice?: (order: string) => void;
  prepareShipment?: (input: {
    counterparty_id: string;
    movements: Record<string, string>[];
  }) => void;
  actionsCurrent: boolean;
}) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {row.document_id && (
          <button
            className="br-btn"
            onClick={() => inspect({ kind: "document", id: row.document_id! })}
          >
            {t("Inspect order document")}
          </button>
        )}
        {actionsCurrent &&
          row.document_id &&
          prepareInvoice &&
          row.lines.some((line) =>
            line.blocking_reasons.includes("prepayment_invoice_missing"),
          ) && (
            <button className="br-btn" onClick={() => prepareInvoice(row.document_id!)}>
              {t("Prepare prepayment invoice")}
            </button>
          )}
      </div>
      {!actionsCurrent && (
        <p className="rounded-lg border border-border-default bg-surface px-3 py-2 text-sm text-fg-muted">
          {t("Actions are unavailable until the readiness projection is current.")}
        </p>
      )}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] text-sm">
          <thead>
            <tr>
              {["Item", "Open", "Fulfilled", "Reserved", "Shortage", "Payment", "Evidence"].map(
                (label) => (
                  <th key={label} className={headerCell}>
                    {t(label)}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-default">
            {row.lines.map((line) => {
              const payment = line.fulfillment_readiness;
              return (
                <tr key={line.commitment_id}>
                  <td className={cell}>{line.item || line.sku || line.item_id}</td>
                  {[
                    line.open_quantity,
                    line.fulfilled_quantity,
                    line.reserved_quantity,
                    line.shortage_quantity,
                  ].map((value, index) => (
                    <td key={index} className={`${cell} whitespace-nowrap text-right`}>
                      {formatQuantity(value)} <span className="text-fg-muted">{line.unit}</span>
                    </td>
                  ))}
                  <td className={cell}>
                    {payment?.requires_prepayment
                      ? `${formatMoney(payment.received_amount, payment.currency)} / ${formatMoney(payment.required_amount, payment.currency)}`
                      : t("No prepayment gate")}
                  </td>
                  <td className={cell}>
                    {actionsCurrent &&
                      prepareShipment &&
                      row.party_id &&
                      line.location_id &&
                      Number(line.shippable_quantity) > 0 && (
                        <button
                          className="br-btn mr-2"
                          onClick={() =>
                            prepareShipment({
                              counterparty_id: row.party_id!,
                              movements: [
                                {
                                  commitment_id: line.commitment_id,
                                  item_id: line.item_id,
                                  from_location_id: line.location_id!,
                                  quantity: line.shippable_quantity,
                                },
                              ],
                            })
                          }
                        >
                          {t("Prepare available shipment")}
                        </button>
                      )}
                    <button
                      className="br-btn"
                      onClick={() => inspect({ kind: "commitment", id: line.commitment_id })}
                    >
                      {t("Inspect commitment")}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
export function OrdersPage({
  selection,
  navigate,
  receive,
  create,
  prepareInvoice,
  prepareShipment,
}: {
  receive?: (id: string) => void;
  create?: (direction: string) => void;
  prepareInvoice?: (order: string) => void;
  prepareShipment?: (input: {
    counterparty_id: string;
    movements: Record<string, string>[];
  }) => void;
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
  const [settledNotice, setSettledNotice] = useState(false);
  useEffect(() => {
    const settled = () => setSettledNotice(true);
    window.addEventListener("reality:delivery-settled", settled);
    return () => window.removeEventListener("reality:delivery-settled", settled);
  }, []);
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
    if (view === "readiness")
      return {
        view,
        ...(await api.specializedProjection<FulfillmentQueueRow>(
          tenant,
          "fulfillment_queue",
          q,
          page,
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
  // The Commitments tab states the open commitments it opens (spec 254).
  const side = purchasing ? "supplier_delivery" : "customer_delivery";
  const openCommitments = useWorkCount(
    `commitments:${side}:${tenant}`,
    () =>
      deliveryApi
        .register(tenant, "", 1, "open", side, "", { size: 1 })
        .then((result) => result.page.total),
    view !== "deliveries",
  );
  const change = (values: Partial<Selection>) =>
    navigate({ ...values, page: 1, entry: "", commitment: "" });
  return (
    <>
      <div hidden={!!selection.commitment}>
        <RegisterWorkbench>
          {entry &&
            (data?.view === "customer-orders" || data?.view === "supplier-orders") &&
            !data.items.some((row) => row.id === entry) && (
              <SelectedRecordPreview kind="order" close={() => navigate({ entry: "" })}>
                <InlineInspector tenant={tenant} target={{ kind: "document", id: entry }}>
                  <button
                    className="br-btn"
                    onClick={() =>
                      change({
                        ordersView: "deliveries",
                        order: entry,
                        deliveryType:
                          view === "supplier-orders" ? "supplier_delivery" : "customer_delivery",
                        deliveryStatus: "all",
                        q: "",
                      })
                    }
                  >
                    {t("View commitments")}
                  </button>
                </InlineInspector>
              </SelectedRecordPreview>
            )}
          <RegisterHeader title={purchasing ? "Purchasing" : "Sales"}>
            <div className="register-tabs">
              {(
                [
                  [
                    purchasing ? "supplier-orders" : "customer-orders",
                    purchasing ? "Supplier orders" : "Customer orders",
                  ],
                  ["deliveries", "Commitments"],
                  ...(!purchasing ? ([["readiness", "Readiness"]] as const) : []),
                  ["shipments", "Shipments"],
                ] as const
              ).flatMap(([value, label]) =>
                withWorkCount(
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
                  </button>,
                  {
                    count: value === "deliveries" ? openCommitments : null,
                    active: view === value,
                    description: t("Open commitments"),
                  },
                ),
              )}
            </div>
          </RegisterHeader>

          {purchasing && view === "deliveries" && (
            <p className="rounded-lg border border-border-default bg-surface-muted px-4 py-3 text-sm text-fg-muted">
              {t(
                "Open an incoming commitment to assign its quantity to customer demand or planned stock.",
              )}
            </p>
          )}

          <section className="register-surface">
            {view === "readiness" && settledNotice && (
              <div
                role="status"
                className="mb-4 flex items-start justify-between gap-3 rounded-lg border border-border-default bg-accent-soft px-4 py-3 text-sm"
              >
                <span>
                  {t(
                    "Confirmed action recorded. Readiness was reloaded; review the current blockers and projection freshness.",
                  )}
                </span>
                <button className="br-btn" onClick={() => setSettledNotice(false)}>
                  {t("Dismiss")}
                </button>
              </div>
            )}
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
                          : view === "readiness"
                            ? "Search order, customer or item"
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
                {data.view === "readiness" ? (
                  <>
                    <ProjectionFreshness metadata={data.metadata} />
                    {data.metadata?.state !== "uninitialized" && (
                      <RegisterTable
                        busy={read.loading}
                        className="w-full min-w-[900px] border-collapse"
                        footer={
                          <RegisterPager
                            page={data.page}
                            change={(page) => navigate({ page, entry: "" })}
                          />
                        }
                      >
                        <thead className="bg-surface-muted">
                          <tr>
                            {["Order", "Customer", "Due", "Readiness", "Blockers", "Actions"].map(
                              (label) => (
                                <th key={label} className={headerCell}>
                                  {t(label)}
                                </th>
                              ),
                            )}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border-default">
                          {data.items.map((row) => (
                            <Fragment key={row.order_key}>
                              <tr data-orders-row={row.order_key}>
                                <td className={cell}>
                                  <p className="font-medium text-fg-strong">
                                    {row.document_number || row.order_key}
                                  </p>
                                </td>
                                <td className={cell}>{row.party || t("Unknown party")}</td>
                                <td className={cell}>
                                  {row.due_at ? formatDateTime(row.due_at) : t("No due date")}
                                </td>
                                <td className={cell}>{t(row.ship_ready ? "Ready" : "Blocked")}</td>
                                <td className={cell}>
                                  <ReadinessBlockers row={row} />
                                </td>
                                <td className={cell}>
                                  <PreviewButton
                                    open={entry === row.order_key}
                                    controls={`readiness-preview-${row.order_key}`}
                                    label={row.document_number || row.order_key}
                                    toggle={() =>
                                      navigate({
                                        entry: entry === row.order_key ? "" : row.order_key,
                                      })
                                    }
                                  />
                                </td>
                              </tr>
                              <TablePreview
                                id={`readiness-preview-${row.order_key}`}
                                open={entry === row.order_key}
                                columns={6}
                              >
                                <ReadinessEvidence
                                  row={row}
                                  inspect={setTarget}
                                  prepareInvoice={prepareInvoice}
                                  prepareShipment={prepareShipment}
                                  actionsCurrent={data.metadata?.state === "ready"}
                                />
                              </TablePreview>
                            </Fragment>
                          ))}
                        </tbody>
                      </RegisterTable>
                    )}
                  </>
                ) : data.view === "deliveries" ? (
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
                              reveal
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
                          "Source",
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
                              reveal
                              tenant={tenant}
                              target={{ kind: "document", id: row.id }}
                              supplement={(detail) =>
                                view === "customer-orders" ? (
                                  <DocumentContributionExplanations
                                    tenant={tenant}
                                    detail={detail}
                                    source="billed_invoice_lines"
                                  />
                                ) : null
                              }
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
