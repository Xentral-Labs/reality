import { SelectedRecordPreview } from "./SelectedRecordPreview";
import { recordOpened } from "./usePaletteHistory";
import { RegisterWorkbench, RegisterHeader, RegisterToolbar } from "./RegisterWorkbench";
import { PageActionBar } from "./PageActionBar";
import { CustomerHoldCard } from "./CustomerHoldCard";
import { useRegisterQuery } from "./TableContext";
import { RegisterTable } from "./RegisterTable";
import { Fragment, useEffect, useRef, useState } from "react";
import { Search, Users, Package, MapPin } from "lucide-react";
import { workspaceApi, type ReferenceDetail, type ReferenceFamily } from "../api";
import { t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { Inspector, InspectorContent } from "./Inspector";
import { PreviewButton, TablePreview } from "./InlinePreview";
import { ContributingSystems, SourceBadge } from "./SourceBadge";
import {
  MasterDataCard,
  displayValue,
  RecordSummary,
  referenceFields,
  savedReferenceDraft,
} from "./MasterDataCard";
import type { Selection } from "./routing";

const families = {
  customer: "Customers",
  supplier: "Suppliers",
  item: "Items",
  location: "Locations",
};
const createLabels: Record<ReferenceFamily, string> = {
  customer: "New customer",
  supplier: "New supplier",
  item: "New item",
  location: "New location",
};
export function MasterDataPage({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const [holdCustomer, setHoldCustomer] = useState("");
  const { tenant, family, q, page, active, record, proposal } = selection;
  const table = useRegisterQuery();
  const read = useRead(
    () => workspaceApi.references(tenant, family, q, page, active, table),
    [tenant, family, q, page, active, table.size, table.sort, table.sort_direction],
  );
  const detailRead = useRead(
    () => (record ? workspaceApi.reference(tenant, family, record) : Promise.resolve(null)),
    [tenant, family, record],
  );
  const [editor, setEditor] = useState<"create" | ReferenceDetail | null>(null);
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  const detail = detailRead.data?.id === record ? detailRead.data : null;
  useEffect(() => {
    if (detail && !detailRead.loading && !detailRead.error)
      recordOpened(
        tenant,
        family === "customer" || family === "supplier" ? "party" : family,
        detail.id,
      );
  }, [detail, detailRead.loading, detailRead.error, tenant, family]);
  const preview = useRef<HTMLDivElement>(null);
  const readyId = detail?.id;
  useEffect(() => {
    if (readyId) preview.current?.scrollIntoView({ block: "start", behavior: "instant" });
  }, [readyId, record]);
  const draft = savedReferenceDraft(tenant);
  const selectedPreview = !detail ? (
    <ReadState loading={detailRead.loading} error={detailRead.error} retry={detailRead.refresh} />
  ) : (
    <div ref={preview} className="w-full" data-master-preview>
      <div className="mb-4 text-sm">
        <SourceBadge origin={detail.origin} inspect={setTarget} tenant={tenant} />
        <ContributingSystems systems={detail.contributing_systems} />
      </div>
      <InspectorContent
        data={{
          title: detail.name,
          sections: detail.preview_sections || [],
          preview_sections: detail.preview_sections,
        }}
        selectedKind={family === "customer" || family === "supplier" ? "party" : family}
        follow={setTarget}
        compact
      />
      {!detail.preview_sections && (
        <RecordSummary
          record={Object.fromEntries(
            referenceFields(family)
              .filter((field) => field.key !== "name")
              .map((field) => [field.key, detail[field.key]]),
          )}
        />
      )}
      <details className="mt-4 text-sm">
        <summary>{t("Source")}</summary>
        <RecordSummary
          record={{
            id: detail.id,
            source_system: detail.source_system,
            external_id: detail.external_id,
          }}
        />
        {detail.source_record_id && (
          <button
            className="br-btn mt-3"
            onClick={() =>
              setTarget({
                kind: "source_record",
                id: detail.source_record_id!,
              })
            }
          >
            {t("Original source")}
          </button>
        )}
      </details>
      <div className="mt-5 flex flex-wrap justify-end gap-2">
        {family === "customer" && (
          <button className="br-btn" onClick={() => setHoldCustomer(detail.id)}>
            {t("Customer delivery holds")}
          </button>
        )}
        <button className="br-btn br-btn-primary" onClick={() => setEditor(detail)}>
          {t("Edit details")}
        </button>
        {(family === "item" || family === "location") && (
          <button
            className="br-btn"
            onClick={() =>
              navigate({
                route: "warehouse",
                warehouseView: "stock",
                item: family === "item" ? detail.id : "",
                location: family === "location" ? detail.id : "",
                entry: "",
                state: "",
                q: "",
                page: 1,
              })
            }
          >
            {t("Open warehouse")}
          </button>
        )}
        <button
          className="br-btn"
          onClick={() =>
            setTarget({
              kind: family === "customer" || family === "supplier" ? "party" : family,
              id: detail.id,
            })
          }
        >
          {t("Open full explanation")}
        </button>
      </div>
    </div>
  );
  return (
    <RegisterWorkbench>
      {record && !read.data?.items.some((row) => row.id === record) && (
        <SelectedRecordPreview kind="master" close={() => navigate({ record: "" })}>
          {selectedPreview}
        </SelectedRecordPreview>
      )}
      {holdCustomer && (
        <CustomerHoldCard
          key={holdCustomer}
          tenant={tenant}
          party={holdCustomer}
          close={() => setHoldCustomer("")}
          prepared={(id) => {
            setHoldCustomer("");
            navigate({ route: "decisions", proposal: id });
          }}
          settled={() => window.dispatchEvent(new Event("reality:delivery-settled"))}
        />
      )}
      <RegisterHeader title="Master data">
        <div className="register-tabs">
          {(Object.entries(families) as [ReferenceFamily, string][]).map(([key, label]) => {
            const Icon = key === "item" ? Package : key === "location" ? MapPin : Users;
            return (
              <button
                key={key}
                className="flex items-center gap-3 rounded-xl border border-border-default bg-surface p-4 text-left aria-pressed:border-accent aria-pressed:bg-accent-soft aria-pressed:text-accent"
                aria-pressed={family === key}
                onClick={() => navigate({ family: key, record: "", q: "", page: 1, proposal: "" })}
              >
                <Icon size={20} />
                {t(label)}
              </button>
            );
          })}
        </div>
      </RegisterHeader>

      {draft && !editor && !proposal && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-accent-soft p-4">
          <p>{t("A prepared request is saved. Check it before starting another change.")}</p>
          <button className="br-btn" onClick={() => setEditor("create")}>
            {t("Resume request")}
          </button>
        </div>
      )}
      <div className="space-y-5">
        <section className="register-surface">
          <RegisterToolbar
            count={read.data?.page.total}
            search={
              <label className="relative min-w-0 basis-full sm:flex-1">
                <span className="sr-only">{t("Search master data")}</span>
                <Search size={16} className="absolute left-3 top-3 text-fg-muted" />
                <input
                  className="br-control w-full"
                  style={{ paddingInlineStart: "2.25rem" }}
                  value={q}
                  placeholder={t("Search by name, SKU or ID")}
                  onChange={(event) => navigate({ q: event.target.value, page: 1 })}
                />
              </label>
            }
            filters={
              <>
                <button
                  className="br-btn"
                  aria-pressed={active}
                  onClick={() => navigate({ active: !active, page: 1 })}
                >
                  {t("Include inactive")}
                </button>
              </>
            }
          />
          <PageActionBar
            actions={[
              { key: "create", label: createLabels[family], onClick: () => setEditor("create") },
            ]}
          />
          {!read.data ? (
            <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={8} />
          ) : (
            <>
              <RegisterTable
                busy={read.loading}
                empty={{ hint: t("Adjust your search or create the first record.") }}
                footer={
                  <div className="mt-5 flex items-center gap-3">
                    <button
                      className="br-btn"
                      disabled={!read.data.page.has_previous}
                      onClick={() => navigate({ page: read.data!.page.number - 1 })}
                    >
                      {t("Previous")}
                    </button>
                    <span>
                      {read.data.page.number} / {read.data.page.pages}
                    </span>
                    <button
                      className="br-btn"
                      disabled={!read.data.page.has_next}
                      onClick={() => navigate({ page: read.data!.page.number + 1 })}
                    >
                      {t("Next")}
                    </button>
                  </div>
                }
              >
                <thead>
                  <tr>
                    {(family === "item"
                      ? [
                          "Name",
                          "SKU",
                          "Unit",
                          "Item type",
                          "Default location",
                          "Source",
                          "Status",
                          "Actions",
                        ]
                      : family === "location"
                        ? [
                            "Name",
                            "Type",
                            "Parent location",
                            "Allows physical stock",
                            "Source",
                            "Status",
                            "Actions",
                          ]
                        : [
                            "Name",
                            "Accounting code",
                            "Payment term",
                            "Currency",
                            "Source",
                            "Status",
                            "Actions",
                          ]
                    ).map((label) => (
                      <th key={label}>{t(label)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {read.data.items.map((row) => (
                    <Fragment key={row.id}>
                      <tr data-master-row>
                        <td data-original-content>{row.name}</td>
                        {family === "item" ? (
                          <>
                            <td data-original-content>{row.sku || "—"}</td>
                            <td data-original-content>{row.unit || "—"}</td>
                            <td>{displayValue("item_type", row.item_type)}</td>
                            <td data-original-content>{row.default_location_name || "—"}</td>
                          </>
                        ) : family === "location" ? (
                          <>
                            <td>
                              {t(row.type ? row.type[0].toUpperCase() + row.type.slice(1) : "—")}
                            </td>
                            <td data-original-content>{row.parent_location_name || "—"}</td>
                            <td>
                              {row.allows_stock == null ? "—" : t(row.allows_stock ? "Yes" : "No")}
                            </td>
                          </>
                        ) : (
                          <>
                            <td data-original-content>{row.accounting_code || "—"}</td>
                            <td data-original-content>{row.payment_term_code || "—"}</td>
                            <td data-original-content>{row.default_currency || "—"}</td>
                          </>
                        )}
                        <td>
                          <SourceBadge origin={row.origin} inspect={setTarget} tenant={tenant} />
                        </td>
                        <td>{t(row.is_active ? "Active" : "Inactive")}</td>
                        <td>
                          <PreviewButton
                            open={record === row.id}
                            controls={`master-preview-${row.id}`}
                            label={row.name}
                            toggle={() => navigate({ record: record === row.id ? "" : row.id })}
                          />
                        </td>
                      </tr>
                      <TablePreview
                        id={`master-preview-${row.id}`}
                        open={record === row.id}
                        columns={family === "item" ? 8 : 7}
                      >
                        {selectedPreview}
                      </TablePreview>
                    </Fragment>
                  ))}
                </tbody>
              </RegisterTable>
            </>
          )}
        </section>
        <section className={record ? "hidden" : "register-empty-guidance"}>
          <details>
            <summary>{t("Start with a record")}</summary>
            <p className="mt-3 text-sm leading-relaxed text-fg-muted">
              {t(
                "Choose a customer, supplier, item or location to see its details and prepare a change.",
              )}
            </p>
            <div className="mt-6 rounded-lg bg-accent-soft p-4 text-sm">
              <p className="font-semibold">{t("Also available in chat")}</p>
              <p className="mt-2 text-fg-muted">
                {t(
                  "Ask Reality to prepare a change. You review the same fields before confirming.",
                )}
              </p>
              <button className="br-btn mt-4" onClick={() => navigate({ route: "copilot" })}>
                {t("Ask Reality")}
              </button>
            </div>
          </details>
        </section>
      </div>
      {(editor || proposal) && (
        <MasterDataCard
          key={`${tenant}:${proposal || (typeof editor === "object" && editor ? editor.id : "new")}`}
          tenant={tenant}
          family={draft?.family || family}
          detail={typeof editor === "object" && editor ? editor : undefined}
          proposalId={proposal}
          close={() => {
            setEditor(null);
            navigate({ proposal: "" });
          }}
          prepared={(id) => {
            setEditor(null);
            navigate({ proposal: id });
          }}
          settled={() => window.dispatchEvent(new Event("reality:delivery-settled"))}
        />
      )}
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </RegisterWorkbench>
  );
}
