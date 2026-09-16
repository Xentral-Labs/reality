import { useEffect, useId, useRef } from "react";
import { api, operationsApi, type ProjectionSnapshot } from "../api";
import { t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { ProjectionFreshness } from "./ProjectionFreshness";
import { RegisterTable } from "./RegisterTable";

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
}: {
  tenant: string;
  name: string;
  close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const read = useRead(() => readView(tenant, name), [tenant, name]);
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
  const columns = Array.from(new Set(rows?.flatMap((row) => Object.keys(row)) || []));
  const text = (value: unknown) =>
    value === null || value === undefined
      ? "—"
      : typeof value === "object"
        ? JSON.stringify(value)
        : String(value);
  return (
    <dialog
      ref={dialog}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
      className="m-auto max-h-[90dvh] w-[min(1100px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-5 text-fg shadow-xl backdrop:bg-black/30"
    >
      <header className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 id={titleId} className="text-lg font-semibold">
            {t("View data")}
          </h2>
          <p className="mt-1 break-all text-sm text-fg-muted" data-localization="original">
            {name.replace(/^view:/, "")}
          </p>
        </div>
        <button className="br-btn" onClick={close}>
          {t("Close")}
        </button>
      </header>
      <ProjectionFreshness
        metadata={read.data?.metadata}
        refresh={read.refresh}
        loading={read.loading}
      />
      {!rows ? (
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
          <RegisterTable
            cursorView={{ id: `inspector:projection:${name}`, widths: columns.map(() => 180) }}
          >
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column} data-localization="original">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => (
                    <td key={column} data-localization="original">
                      {text(row[column])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </RegisterTable>
          <details className="mt-4">
            <summary className="cursor-pointer text-sm">{t("Technical details")}</summary>
            <pre
              className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-all text-xs"
              data-localization="original"
            >
              {JSON.stringify(rows, null, 2)}
            </pre>
          </details>
        </>
      )}
    </dialog>
  );
}
