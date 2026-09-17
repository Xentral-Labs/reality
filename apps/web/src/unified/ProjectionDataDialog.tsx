import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { api, operationsApi, type ProjectionSnapshot } from "../api";
import { t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { ProjectionFreshness } from "./ProjectionFreshness";
import { ReportDataTable } from "./ReportDataTable";

async function readView(tenant: string, name: string): Promise<ProjectionSnapshot> {
  if (!name.startsWith("view:")) return api.inspectorProjection(tenant, name);
  return { items: await readLiveView(tenant, name) };
}

export async function readLiveView(
  tenant: string,
  name: string,
): Promise<Record<string, unknown>[]> {
  const key = name.slice(5);
  switch (key) {
    case "commitments":
      return (await api.commitments(tenant, "", "")).items.map((row) => ({ ...row }));
    case "documents":
      return (await api.documents(tenant)).items.map((row) => ({ ...row }));
    case "reservations":
      return (await api.reservations(tenant)).map((row) => ({ ...row }));
    case "movements":
      return (await api.movements(tenant)).map((row) => ({ ...row }));
    case "items":
      return (await api.items(tenant)).map((row) => ({ ...row }));
    case "locations":
      return (await api.locations(tenant)).map((row) => ({ ...row }));
    case "parties":
      return (await api.parties(tenant)).map((row) => ({ ...row }));
    case "payments":
      return (await api.payments(tenant)).items.map((row) => ({ ...row }));
    case "journal":
      return (await api.journal(tenant)).items.map((row) => ({ ...row }));
    case "activity":
      return (await api.timeline(tenant)).activities.map((row) => ({ ...row }));
    case "sources_imports":
      return (await api.integrations(tenant)).recent_records.map((row) => ({ ...row }));
    case "commercial_terms": {
      const [terms, lists, groups] = await Promise.all([
        api.paymentTerms(tenant),
        api.priceLists(tenant),
        api.pricingGroups(tenant),
      ]);
      return [
        ...terms.map((row) => ({ collection: "payment_terms", ...row })),
        ...lists.map((row) => ({ collection: "price_lists", ...row })),
        ...groups.map((row) => ({ collection: "pricing_groups", ...row })),
      ];
    }
    case "orders":
      return (await api.documents(tenant)).items
        .filter((row) => String((row as { type?: string }).type || "").endsWith("_order"))
        .map((row) => ({ ...row }));
    case "open_items":
      return (await api.openItems(tenant)).items.map((row) => ({ ...row }));
    case "inventory":
      return (await api.inventory(tenant)).items.map((row) => ({ ...row }));
    case "fulfillment_blockers":
      return (await operationsApi.attention(tenant, "", "", 1)).items.map((row) => ({ ...row }));
    default:
      throw new Error("Unsupported catalog view");
  }
}

export function ProjectionDataDialog({
  tenant,
  name,
  close,
  title,
  description,
  dataAvailable = true,
  details,
}: {
  tenant: string;
  name: string;
  close: () => void;
  title?: string;
  description?: string;
  dataAvailable?: boolean;
  details?: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [detailsOpen, setDetailsOpen] = useState(
    () => !dataAvailable || window.matchMedia("(min-width: 1024px)").matches,
  );
  const read = useRead(
    () => (dataAvailable ? readView(tenant, name) : Promise.resolve(null)),
    [tenant, name, dataAvailable],
  );
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const element = dialog.current!;
    element.showModal();
    return () => {
      element.close();
      trigger?.focus();
    };
  }, []);
  const rows = read.data?.items.slice(0, 100);
  const splitLayout = "lg:grid-cols-[minmax(0,1fr)_340px] lg:grid-rows-1";
  const besideData = "max-h-[32dvh] lg:order-2 lg:max-h-none lg:border-b-0 lg:border-l";
  const detailsOnly = "row-span-2 max-h-none";
  return (
    <dialog
      ref={dialog}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
      className="m-auto h-[90dvh] max-h-[90dvh] w-[min(1400px,94vw)] overflow-hidden rounded-xl border border-border-default bg-surface p-0 text-fg shadow-xl backdrop:bg-black/30"
    >
      <div className="flex h-full min-h-0 flex-col">
        <header className="flex shrink-0 items-start justify-between gap-4 border-b border-border-default p-5">
          <div>
            <h2 id={titleId} className="text-lg font-semibold">
              {t(title || "View data")}
            </h2>
            {description ? (
              <p className="mt-2 text-sm leading-relaxed text-fg-muted">{t(description)}</p>
            ) : (
              <p className="mt-1 break-all text-sm text-fg-muted" data-localization="original">
                {name.replace(/^view:/, "")}
              </p>
            )}
          </div>
          <button className="br-btn" onClick={close}>
            {t("Close")}
          </button>
        </header>
        <div
          className={`grid min-h-0 flex-1 grid-rows-[auto_minmax(0,1fr)] overflow-hidden ${details && dataAvailable ? splitLayout : "grid-cols-1"}`}
        >
          {details && (
            <aside
              className={`min-h-0 min-w-0 overflow-auto border-b border-border-default bg-surface-muted p-4 ${dataAvailable ? besideData : detailsOnly}`}
            >
              <details
                open={detailsOpen}
                onToggle={(event) => setDetailsOpen(event.currentTarget.open)}
                data-report-details
              >
                <summary className="cursor-pointer font-medium">{t("About this report")}</summary>
                <div className="mt-4 space-y-5">{details}</div>
              </details>
            </aside>
          )}
          <div
            data-report-data
            className={`min-h-0 min-w-0 overflow-auto p-5 ${details ? "lg:order-1" : "row-span-2"} ${!dataAvailable && details ? "hidden" : ""}`}
          >
            <ProjectionFreshness
              metadata={read.data?.metadata}
              refresh={read.refresh}
              loading={read.loading}
              error={read.error}
            />
            {!dataAvailable ? (
              <p className="py-4 text-sm text-fg-muted">
                {t(
                  "This report needs a business partner and an item. See the details for its inputs and calculation.",
                )}
              </p>
            ) : !rows ? (
              <ReadState loading={read.loading} error={read.error} retry={read.refresh} />
            ) : !rows.length &&
              read.data?.metadata &&
              read.data.metadata.state !== "ready" ? null : !rows.length ? (
              <p role="status" className="py-6 text-sm text-fg-muted">
                {t("No results")}
              </p>
            ) : (
              <>
                <p className="mb-3 text-xs text-fg-muted">
                  {t("Preview of returned data; up to 100 rows from the first response.")}
                </p>
                <ReportDataTable key={name} name={name} rows={rows} />
              </>
            )}
          </div>
        </div>
      </div>
    </dialog>
  );
}
