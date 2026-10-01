import { useState } from "react";
import { monthEndBillingApi, type MonthEndBillingRow } from "../api";
import { formatDateTime, formatQuantity, t } from "../localization";
import { Inspector } from "../unified/Inspector";
import { ReadState } from "../unified/ReadState";
import { useRead } from "../unified/useCompanyContext";

// Spec 299: what the month-end close must invoice or accrue. Both lists are the
// findings at one instant, read through the shared month_end_billing tool.

const headerCell = "border-b border-border-default px-3 py-2 text-left font-medium";
const cell = "border-b border-border-subtle px-3 py-2 align-top";

function BillingList({
  title,
  description,
  quantityLabel,
  rows,
  inspect,
}: {
  title: string;
  description: string;
  quantityLabel: string;
  rows: MonthEndBillingRow[];
  inspect: (target: { kind: string; id: string }) => void;
}) {
  return (
    <section className="mb-8" aria-label={t(title)}>
      <h2 className="text-base font-semibold">
        {t(title)} <span className="text-fg-muted">({rows.length})</span>
      </h2>
      <div className="mb-3 text-sm text-fg-muted">{t(description)}</div>
      {rows.length === 0 ? (
        <div className="rounded-lg border border-border-default px-3 py-2 text-sm">
          {t("Nothing to report.")}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead className="bg-surface-muted">
              <tr>
                <th className={headerCell}>{t("Order")}</th>
                <th className={headerCell}>{t("Item")}</th>
                <th className={headerCell}>{t(quantityLabel)}</th>
                <th className={headerCell}>{t("Evidence")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.exception_id}>
                  <td className={cell}>
                    <button
                      className="text-accent underline"
                      onClick={() => inspect({ kind: "document", id: row.order_id })}
                    >
                      {row.order_number || row.order_id}
                    </button>
                  </td>
                  <td className={cell}>{row.sku || row.item_id || "—"}</td>
                  <td className={cell}>
                    {formatQuantity(row.quantity)} {row.unit || ""}
                  </td>
                  <td className={cell}>
                    <button
                      className="br-btn"
                      onClick={() => inspect({ kind: "document_line", id: row.order_line_id })}
                    >
                      {t("Inspect order line")}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function MonthEndBilling({ tenant }: { tenant: string }) {
  const [asOf, setAsOf] = useState("");
  const [target, inspect] = useState<{ kind: string; id: string } | null>(null);
  const read = useRead(
    () => monthEndBillingApi.read(tenant, asOf ? new Date(`${asOf}T23:59:59`).toISOString() : ""),
    [tenant, asOf],
  );
  return (
    <div className="min-w-0">
      <div className="mb-5 flex flex-wrap items-end gap-3">
        <label className="text-sm">
          {t("As of")}
          <input
            type="date"
            className="br-control mt-1 block"
            value={asOf}
            onChange={(event) => setAsOf(event.target.value)}
          />
        </label>
        {read.data && (
          <span className="text-sm text-fg-muted">
            {t("Findings at")} {formatDateTime(read.data.as_of)}
          </span>
        )}
      </div>
      {!read.data ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={6} />
      ) : (
        <>
          <BillingList
            title="Shipped and not invoiced"
            description="Goods that left against a customer order line and that no invoice line bills yet."
            quantityLabel="Not invoiced"
            rows={read.data.shipped_not_billed}
            inspect={inspect}
          />
          <BillingList
            title="Invoiced and not shipped"
            description="Invoice lines that bill more of a customer order line than has shipped. Down-payment and pro-forma invoices bill no line and never appear here."
            quantityLabel="Not shipped"
            rows={read.data.billed_not_shipped}
            inspect={inspect}
          />
        </>
      )}
      {target && <Inspector tenant={tenant} target={target} close={() => inspect(null)} />}
    </div>
  );
}
