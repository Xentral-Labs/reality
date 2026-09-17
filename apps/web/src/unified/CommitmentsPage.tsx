import { ArrowRight, PackageCheck } from "lucide-react";
import { useState } from "react";
import { deliveryApi, type DeliveryRow } from "../api";
import { formatDate, formatNumber, formatQuantity, t } from "../localization";
import { RegisterHeader } from "./RegisterWorkbench";
import { DeliveryCase } from "./DeliveryCase";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";
import type { Selection } from "./routing";
import { WorkFooter, WorkHeader, WorkRow, WorkSearch, useWorkList } from "./WorkList";
import { InlineInspector, WorkPreview } from "./InlinePreview";

export function CommitmentsPage({
  selection,
  navigate,
  receive,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
  receive: (id: string) => void;
}) {
  const { tenant, deliveryType, q, commitment } = selection;
  const [preview, setPreview] = useState("");
  const list = useWorkList<DeliveryRow>(JSON.stringify([tenant, deliveryType, q]), (page) =>
    deliveryApi.register(tenant, q, page, "open", deliveryType, "", { size: 50 }),
  );
  const counts = useRead(
    () =>
      Promise.all([
        deliveryApi.register(tenant, "", 1, "open", "customer_delivery", "", { size: 1 }),
        deliveryApi.register(tenant, "", 1, "open", "supplier_delivery", "", { size: 1 }),
      ]),
    [tenant],
  );
  const change = (values: Partial<Selection>) => navigate({ ...values, commitment: "", page: 1 });
  const today = formatDate(new Date().toISOString());
  const group = (row: DeliveryRow) =>
    !row.due_at
      ? "No due date"
      : formatDate(row.due_at) === today
        ? "Due today"
        : new Date(row.due_at).getTime() < Date.now()
          ? "Overdue"
          : "Upcoming";
  return (
    <div className="mx-auto max-w-[1200px] space-y-3" data-work-list="commitments">
      <WorkHeader title="Commitments" total={list.page?.total} />
      <RegisterHeader title="Commitments" placement="local">
        <nav className="register-tabs" aria-label={t("Delivery direction")}>
          {(
            [
              ["customer_delivery", "Customer side"],
              ["supplier_delivery", "Supplier side"],
            ] as const
          ).map(([value, label], index) => (
            <button
              key={value}
              aria-pressed={deliveryType === value}
              onClick={() => change({ deliveryType: value, q: "" })}
            >
              {t(label)}{" "}
              {counts.data && (
                <span className="ml-2 rounded-full bg-surface-muted px-2 py-0.5 text-xs tabular-nums">
                  {formatNumber(counts.data[index].page.total)}
                </span>
              )}
            </button>
          ))}
        </nav>
      </RegisterHeader>
      <div className="flex flex-wrap items-center gap-3">
        <WorkSearch
          value={q}
          change={(q) => change({ q })}
          label="Search party, item or delivery ID"
        />
        <span className="text-xs text-fg-muted">
          {t("Earliest due first")} · {t("Open only")}
        </span>
      </div>
      <section
        className="overflow-hidden rounded-xl border border-border-default bg-surface"
        aria-busy={list.loading}
      >
        {!list.page && list.loading ? (
          <ReadState loading rows={8} />
        ) : !list.items.length && !list.error ? (
          <p className="px-5 py-14 text-center text-sm text-fg-muted">
            {t(q ? "No matching records" : "No open commitments")}
          </p>
        ) : (
          list.items.map((row, index) => (
            <div key={row.id}>
              {(index === 0 || group(row) !== group(list.items[index - 1])) && (
                <h2 className="border-b border-border-default bg-surface-muted px-4 py-1.5 text-xs font-medium text-fg-muted">
                  {t(group(row))}
                </h2>
              )}
              <WorkRow
                title={row.counterparty || t("Unknown")}
                context={
                  <>
                    {formatQuantity(row.open)} {row.unit} · {row.item || t("Unknown")}
                  </>
                }
                meta={row.due_at ? formatDate(row.due_at) : t("No due date")}
                icon={<PackageCheck size={18} aria-hidden="true" />}
                selected={preview === row.id}
                previewId={`commitment-preview-${row.id}`}
                open={() => setPreview(preview === row.id ? "" : row.id)}
              />
              <WorkPreview id={`commitment-preview-${row.id}`} open={preview === row.id}>
                <InlineInspector tenant={tenant} target={{ kind: "commitment", id: row.id }} />
                <button
                  className="br-btn mt-5"
                  onClick={() => navigate({ commitment: row.id, proposal: "", entry: "" })}
                >
                  <ArrowRight size={15} aria-hidden="true" />
                  {t("Open commitment")}
                </button>
              </WorkPreview>
            </div>
          ))
        )}
        <WorkFooter list={list} />
      </section>
      {commitment && (
        <section className="rounded-xl border border-border-default bg-surface p-5 sm:p-6">
          <button className="br-btn mb-5" onClick={() => navigate({ commitment: "" })}>
            {t("Close")}
          </button>
          <DeliveryCase
            key={commitment}
            tenant={tenant}
            id={commitment}
            navigate={navigate}
            receive={receive}
          />
        </section>
      )}
    </div>
  );
}
