import { useContextActions } from "./ActionLauncher";
import { PageActionBar } from "./PageActionBar";
import { RegisterWorkbench, RegisterHeader, RegisterToolbar } from "./RegisterWorkbench";
import { useRegisterQuery } from "./TableContext";
import { RegisterTable } from "./RegisterTable";
import { Boxes, Search } from "lucide-react";
import { Fragment } from "react";
import { operationsApi, type Page, type WarehouseView } from "../api";
import { formatDateTime, formatNumber, formatQuantity, t } from "../localization";
import { ReadState } from "./ReadState";
import { InlineInspector, PreviewButton, TablePreview } from "./InlinePreview";
import { useRead } from "./useCompanyContext";
import type { Selection } from "./routing";

const states: Record<WarehouseView, [string, string][]> = {
  stock: [
    ["available", "Available stock"],
    ["fully_allocated", "No available stock"],
    ["shortage", "Overallocated stock"],
  ],
  reservations: [
    ["active", "Active"],
    ["released", "Released"],
    ["consumed", "Consumed"],
  ],
  movements: [
    ["receipt", "Receipt"],
    ["shipment", "Shipment"],
    ["transfer", "Transfer"],
    ["return", "Customer return"],
    ["supplier_return", "Supplier return"],
    ["adjustment", "Adjustment"],
    ["correction", "Correction"],
  ],
};
export function RegisterPager({ page, change }: { page: Page; change: (page: number) => void }) {
  return (
    <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-fg-muted">
        {formatNumber(page.total)} {t("records")}
      </p>
      <div className="flex items-center gap-3">
        <button
          className="br-btn"
          disabled={!page.has_previous}
          onClick={() => change(page.number - 1)}
        >
          {t("Previous")}
        </button>
        <span className="text-sm">
          {page.number} / {page.pages}
        </span>
        <button
          className="br-btn"
          disabled={!page.has_next}
          onClick={() => change(page.number + 1)}
        >
          {t("Next")}
        </button>
      </div>
    </div>
  );
}
export function WarehousePage({
  selection,
  navigate,
  release,
  correct,
  opening,
}: {
  opening?: () => void;
  release?: (id: string) => void;
  correct?: (id: string) => void;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const { tenant, warehouseView: view, q, state, item, page, entry } = selection;
  const table = useRegisterQuery();
  const read = useRead(
    () => operationsApi.warehouse(tenant, view, q, state, item, page, table),
    [tenant, view, q, state, item, page, table.size, table.sort, table.sort_direction],
  );
  const kind = view === "stock" ? "item" : view === "reservations" ? "reservation" : "movement";
  const stock = view === "stock";
  const data = read.data?.scope.view === view ? read.data : undefined;
  const warehouseActions = useContextActions(`warehouse.${view}`);
  return (
    <RegisterWorkbench>
      <RegisterHeader title="Warehouse">
        <div className="register-tabs">
          {(
            [
              ["stock", "Stock"],
              ["reservations", "Reservations"],
              ["movements", "Movements"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              className="br-btn aria-pressed:border-accent aria-pressed:bg-accent-soft"
              aria-pressed={view === value}
              onClick={() =>
                navigate({ warehouseView: value, state: "", entry: "", q: "", page: 1 })
              }
            >
              {t(label)}
            </button>
          ))}
        </div>
      </RegisterHeader>

      <section className="register-surface">
        <RegisterToolbar
          count={data?.page.total}
          search={
            <label className="relative min-w-0 basis-full sm:flex-1">
              <span className="sr-only">{t("Search warehouse")}</span>
              <Search size={16} className="absolute left-3 top-3 text-fg-muted" />
              <input
                className="br-control w-full"
                style={{ paddingInlineStart: "2.25rem" }}
                aria-label={t("Search warehouse")}
                placeholder={t(stock ? "Search by item name or SKU" : "Search by reference ID")}
                value={q}
                onChange={(event) => navigate({ q: event.target.value, page: 1 })}
              />
            </label>
          }
          filters={
            <>
              <label className="min-w-40 text-sm">
                <span className="sr-only">{t("State")}</span>
                <select
                  className="br-control w-full"
                  aria-label={t("State")}
                  value={state}
                  onChange={(event) => navigate({ state: event.target.value, page: 1 })}
                >
                  <option value="">{t("All states")}</option>
                  {states[view].map(([value, label]) => (
                    <option key={value} value={value}>
                      {t(label)}
                    </option>
                  ))}
                </select>
              </label>
            </>
          }
        />
        <PageActionBar actions={warehouseActions} />
        <div className="warehouse-scope-filter my-5 flex flex-wrap items-center justify-between gap-3">
          {item && (
            <button className="br-btn" onClick={() => navigate({ item: "", entry: "", page: 1 })}>
              {data?.scope.item || item} · {t("Clear item filter")}
            </button>
          )}
        </div>
        {!data ? (
          <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={8} />
        ) : (
          <>
            <div className="min-w-0">
              <RegisterTable
                busy={read.loading}
                className="w-full min-w-[700px] text-sm"
                footer={<RegisterPager page={data.page} change={(page) => navigate({ page })} />}
              >
                <thead>
                  <tr className="border-b border-border-default text-fg-muted">
                    <th className="pb-3 text-left">{t("Item")}</th>
                    {stock ? (
                      <>
                        <th className="pb-3 text-right">{t("Physical")}</th>
                        <th className="pb-3 text-right">{t("Reserved")}</th>
                        <th className="pb-3 text-right">{t("Available")}</th>
                      </>
                    ) : (
                      <>
                        <th className="pb-3 text-left">
                          {t(view === "reservations" ? "Location" : "Movement")}
                        </th>
                        <th className="pb-3 text-right">{t("Quantity")}</th>
                        <th className="pb-3 pl-5 text-left">{t("Status")}</th>
                      </>
                    )}
                    <th className="pb-3 text-right">{t("Details")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((row) => (
                    <Fragment key={row.id}>
                      <tr className="border-b border-border-default">
                        <td className="py-5 pr-4">
                          <strong className="block text-fg-strong">{row.name || row.item}</strong>
                          <span className="mt-1 block text-xs text-fg-muted">
                            {row.sku}
                            {row.at ? ` · ${formatDateTime(row.at)}` : ""}
                          </span>
                        </td>
                        {stock ? (
                          <>
                            {(["physical", "reserved", "available"] as const).map((field) => (
                              <td key={field} className="py-5 text-right">
                                <button
                                  className="rounded px-2 py-1 hover:bg-surface-muted"
                                  aria-label={`${t(field === "physical" ? "Physical" : field === "reserved" ? "Reserved" : "Available")} · ${row.name}`}
                                  onClick={() => navigate({ entry: row.id })}
                                >
                                  {formatQuantity(row[field]!)}{" "}
                                  <span className="text-xs text-fg-muted">{row.unit}</span>
                                </button>
                              </td>
                            ))}
                          </>
                        ) : (
                          <>
                            <td className="py-5 pr-4">
                              {view === "reservations" ? (
                                row.location
                              ) : (
                                <>
                                  <span className="block">
                                    {t(
                                      states.movements.find(([value]) => value === row.type)?.[1] ||
                                        row.type ||
                                        "",
                                    )}
                                  </span>
                                  <span className="mt-1 block text-xs text-fg-muted">
                                    {row.from_location || "—"} → {row.to_location || "—"}
                                  </span>
                                </>
                              )}
                            </td>
                            <td className="py-5 text-right">
                              {formatQuantity(row.quantity!)}{" "}
                              <span className="text-xs text-fg-muted">{row.unit}</span>
                            </td>
                            <td className="py-5 pl-5 text-xs">
                              {t(
                                view === "reservations"
                                  ? states.reservations.find(
                                      ([value]) => value === row.status,
                                    )?.[1] ||
                                      row.status ||
                                      ""
                                  : row.correction_role === "normal"
                                    ? "Recorded"
                                    : row.correction_role === "corrected"
                                      ? "Corrected"
                                      : row.correction_role === "compensation"
                                        ? "Compensation"
                                        : "Replacement",
                              )}
                            </td>
                          </>
                        )}
                        <td className="py-5 pl-3 text-right">
                          <PreviewButton
                            open={entry === row.id}
                            controls={`warehouse-preview-${row.id}`}
                            label={row.name || row.item || row.id}
                            toggle={() => navigate({ entry: entry === row.id ? "" : row.id })}
                          />
                        </td>
                      </tr>
                      <TablePreview
                        id={`warehouse-preview-${row.id}`}
                        open={entry === row.id}
                        columns={5}
                      >
                        <InlineInspector tenant={tenant} target={{ kind, id: row.id }}>
                          {view === "reservations" && row.status === "active" && release && (
                            <button
                              className="br-btn"
                              data-action-meaning="work"
                              onClick={() => release(row.id)}
                            >
                              {t("Release reservation")}
                            </button>
                          )}
                          {view === "movements" &&
                            ["normal", "replacement"].includes(row.correction_role || "") &&
                            correct && (
                              <button
                                className="br-btn"
                                data-action-meaning="edit"
                                onClick={() => correct(row.id)}
                              >
                                {t("Correct movement")}
                              </button>
                            )}
                          {stock ? (
                            <>
                              <button
                                className="br-btn"
                                data-action-meaning="filter"
                                onClick={() =>
                                  navigate({
                                    warehouseView: "reservations",
                                    item: row.id,
                                    entry: "",
                                    q: "",
                                    state: "",
                                    page: 1,
                                  })
                                }
                              >
                                {t("Reservations")}
                              </button>
                              <button
                                className="br-btn"
                                data-action-meaning="filter"
                                onClick={() =>
                                  navigate({
                                    warehouseView: "movements",
                                    item: row.id,
                                    entry: "",
                                    q: "",
                                    state: "",
                                    page: 1,
                                  })
                                }
                              >
                                {t("Movements")}
                              </button>
                            </>
                          ) : row.delivery_id ? (
                            <button
                              className="br-btn"
                              data-action-meaning="navigate"
                              onClick={() =>
                                navigate({
                                  route: "orders-deliveries",
                                  ordersView: "deliveries",
                                  commitment: row.delivery_id,
                                  proposal: "",
                                  entry: "",
                                })
                              }
                            >
                              {t("Open delivery")}
                            </button>
                          ) : null}
                        </InlineInspector>
                      </TablePreview>
                    </Fragment>
                  ))}
                </tbody>
              </RegisterTable>
            </div>
          </>
        )}
      </section>
      <div className="flex flex-wrap justify-between gap-3 text-xs text-fg-muted">
        <span>{data ? `${t("Observed at")} ${formatDateTime(data.observed_at)}` : ""}</span>
      </div>
    </RegisterWorkbench>
  );
}
