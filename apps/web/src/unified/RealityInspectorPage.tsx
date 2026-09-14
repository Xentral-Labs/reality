import { languageHref, readLanguage } from "../../../shared/language";
import { ActionDirectory } from "./ActionDirectory";
import { CatalogEntryDetails } from "./CatalogEntryDetails";
import { ProjectionDataDialog } from "./ProjectionDataDialog";
import { RecordGraphPage } from "./RecordGraphPage";
import { InspectorCatalog, InspectorDisclosure, InspectorCatalogHeading } from "./InspectorCatalog";
import { RegisterHeader } from "./RegisterWorkbench";
import { inspectorTabs } from "./inspectorSections";
import { FlightRecorder } from "./FlightRecorder";
import { useState } from "react";
import { api, type SpecializedProjectionRow } from "../api";
import { t } from "../localization";
import { InspectorRecordsPage } from "./InspectorRecordsPage";
import { TableProvider } from "./TableContext";
import { type GraphTarget } from "./ObjectGraph";
import { RulesWorkbench } from "./RulesWorkbench";
import { ActivityDrawer } from "./ActivityDrawer";
import { ExceptionRulesRegister } from "./ExceptionRulesRegister";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import type { Selection } from "./routing";
import type { DeliveryAction } from "./ActionLauncher";
const kinds: Record<string, string> = {
  facts: "fact",
  commitments: "commitment",
  reservations: "reservation",
  movements: "movement",
  documents: "document",
  document_lines: "document_line",
  source_records: "source_record",
  parties: "party",
  items: "item",
  locations: "location",
  ledger_entries: "ledger_entry",
  payments: "payment",
  business_events: "business_event",
};
const kindFor = (name: string) => (Object.values(kinds).includes(name) ? name : kinds[name]);
const catalogRoutes: Record<string, Partial<Selection>> = {
  commitments: { route: "orders-deliveries", ordersView: "deliveries" },
  orders: { route: "orders-deliveries", ordersView: "customer-orders" },
  inventory: { route: "warehouse", warehouseView: "stock" },
  reservations: { route: "warehouse", warehouseView: "reservations" },
  movements: { route: "warehouse", warehouseView: "movements" },
  "open-items": { route: "finance", financeView: "open-items" },
  payments: { route: "finance", financeView: "payments" },
  journal: { route: "finance", financeView: "journal" },
  documents: { route: "data-sources", dataView: "documents" },
  integrations: { route: "data-sources", dataView: "systems" },
  items: { route: "master-data", family: "item" },
  locations: { route: "master-data", family: "location" },
  parties: { route: "master-data", family: "customer" },
  facts: { route: "facts" },
  timeline: { route: "inspector", inspectorView: "history" },
};
const panel = "rounded-xl border border-border-default bg-surface p-4";
export function RealityInspectorPage({
  selection,
  navigate,
  owner,
  companyName,
  user,
  openAction,
}: {
  selection: Selection;
  navigate: (value: Partial<Selection>) => void;
  owner: boolean;
  companyName: string;
  user: string;
  openAction: (tool: DeliveryAction) => void;
}) {
  const tenant = selection.tenant,
    tab = selection.inspectorView === "records" ? "facts" : selection.inspectorView || "overview";
  const needsReference = ["commands", "views"].includes(tab);
  const reference = useRead(
    () => (needsReference ? api.applicationReference(tenant) : Promise.resolve(null)),
    [tenant, needsReference],
  );
  const [query, setQuery] = useState(selection.q || "");
  const [root, setRoot] = useState<GraphTarget | null>(null);
  const [technicalOpen, setTechnicalOpen] = useState(false);
  const explorer = useRead(
    () => (tab === "facts" && technicalOpen ? api.explorer(tenant, query) : Promise.resolve(null)),
    [tenant, tab, query, technicalOpen],
  );
  const [projection, setProjection] = useState("");
  const catalogLinks = (documentation: string, route?: string) => (
    <>
      <a
        className="br-btn"
        href={languageHref(
          `${__DOCS_URL__.replace(/\/+$/, "")}/catalogs/${documentation}`,
          readLanguage() ?? "en",
          true,
        )}
        target="_blank"
        rel="noopener noreferrer"
      >
        {t("Documentation")} ↗
      </a>
      {route && catalogRoutes[route] && (
        <button
          className="br-btn"
          onClick={() =>
            navigate({ ...catalogRoutes[route], tenant, q: "", page: 1, entry: "", record: "" })
          }
        >
          {t("Open in application")}
        </button>
      )}
    </>
  );
  const openGraph = (target: GraphTarget) => {
    setRoot(target);
    navigate({ inspectorView: "graph" });
  };
  const matches = (value: unknown) =>
    JSON.stringify(value).toLowerCase().includes(query.toLowerCase());
  const views = Array.from(
    new Map(
      (reference.data?.workspaces || [])
        .flatMap((workspace) => workspace.views)
        .map((view) => [view.key, view]),
    ).values(),
  );
  return (
    <div className="min-w-0 space-y-4" data-reality-inspector>
      <RegisterHeader title="Reality Inspector" originalTitle>
        <nav className="register-tabs" aria-label={t("Reality Inspector sections")}>
          {inspectorTabs(tab).map(([key, label]) => (
            <button
              key={key}
              aria-pressed={tab === key}
              onClick={() => {
                navigate({ inspectorView: key });
                setQuery("");
                setProjection("");
              }}
            >
              {t(label)}
            </button>
          ))}
        </nav>
      </RegisterHeader>
      {tab === "overview" && <FlightRecorder key={tenant} tenant={tenant} />}
      {tab === "facts" && (
        <TableProvider
          user={user}
          selection={{ ...selection, route: "facts" }}
          navigate={(changes) =>
            navigate({
              ...changes,
              route: changes.route && changes.route !== "facts" ? changes.route : "inspector",
            })
          }
        >
          <InspectorRecordsPage
            selection={{ ...selection, route: "facts" }}
            navigate={(changes) =>
              navigate({
                ...changes,
                route: changes.route && changes.route !== "facts" ? changes.route : "inspector",
              })
            }
            graph={openGraph}
          />
        </TableProvider>
      )}
      {tab === "facts" && (
        <details
          className="rounded-xl border border-border-default bg-surface p-4"
          onToggle={(event) => setTechnicalOpen(event.currentTarget.open)}
        >
          <summary className="cursor-pointer text-sm font-medium">
            {t("Technical record overview")}
          </summary>
          {technicalOpen &&
            (!explorer.data ? (
              <ReadState
                loading={explorer.loading}
                error={explorer.error}
                retry={explorer.refresh}
              />
            ) : (
              <InspectorCatalog
                countPlacement="local"
                query={query}
                onQuery={setQuery}
                count={explorer.data.sections.reduce(
                  (total, section) =>
                    total +
                    section.collections.reduce(
                      (sum, collection) => sum + collection.records.length,
                      0,
                    ),
                  0,
                )}
              >
                <p className="text-xs text-fg-muted">
                  {t("Records per collection")}: {explorer.data.limit_per_collection}
                </p>
                {explorer.data.sections.map((section) => (
                  <section key={section.name} className="space-y-3">
                    <h2 className="font-semibold" data-localization="original">
                      {section.name}
                    </h2>
                    <p className="my-2 text-sm text-fg-muted" data-localization="original">
                      {section.description}
                    </p>
                    {section.collections.map((collection) => (
                      <InspectorDisclosure key={collection.name}>
                        <summary className="cursor-pointer text-sm">
                          {collection.label} · {collection.records.length}
                        </summary>
                        {collection.records.map((record) => (
                          <div
                            key={record.id}
                            className="mt-3 rounded border border-border-default p-3"
                          >
                            <strong
                              className="block break-all text-sm"
                              data-localization="original"
                            >
                              {record.title}
                            </strong>
                            <code className="text-xs">{record.id}</code>
                            {kindFor(collection.name) && (
                              <button
                                className="br-btn ml-3"
                                onClick={() =>
                                  openGraph({ kind: kindFor(collection.name), id: record.id })
                                }
                              >
                                {t("Record graph")}
                              </button>
                            )}
                            <pre
                              className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-all text-xs"
                              data-localization="original"
                            >
                              {JSON.stringify(record.fields, null, 2)}
                            </pre>
                          </div>
                        ))}
                      </InspectorDisclosure>
                    ))}
                  </section>
                ))}
              </InspectorCatalog>
            ))}
        </details>
      )}
      {tab === "graph" && (
        <RecordGraphPage tenant={tenant} initialRoot={root} onRootChange={setRoot} />
      )}
      {tab === "rules" && <RulesWorkbench key={tenant} tenant={tenant} owner={owner} />}
      {tab === "exceptions" && <ExceptionRulesRegister tenant={tenant} navigate={navigate} />}
      {(tab === "commands" || tab === "views") &&
        (!reference.data ? (
          <ReadState
            loading={reference.loading}
            error={reference.error}
            retry={reference.refresh}
          />
        ) : tab === "commands" ? (
          <ActionDirectory
            key={tenant}
            reference={reference.data}
            tenant={tenant}
            openAction={openAction}
          />
        ) : (
          <InspectorCatalog
            query={query}
            onQuery={setQuery}
            count={
              (reference.data.projections || []).filter(matches).length +
              views.filter(matches).length
            }
          >
            {
              <div
                className="grid grid-cols-1 items-start gap-5 md:grid-cols-2"
                data-projection-view-columns
              >
                <section className="min-w-0 space-y-3" aria-label={t("Projections")}>
                  <InspectorCatalogHeading
                    title="Projections"
                    count={(reference.data.projections || []).filter(matches).length}
                    explanation="A projection is a calculated overview, like an ERP stock report. Example: 100 units in stock minus 30 reserved gives 70 available. It uses existing records and does not create a new stock posting."
                  />
                  {(reference.data.projections || []).filter(matches).map((value) => (
                    <InspectorDisclosure key={value.materialized_as}>
                      <summary className="cursor-pointer font-medium" data-localization="original">
                        {value.name}
                      </summary>
                      <CatalogEntryDetails
                        tenant={tenant}
                        kind="projection"
                        actions={
                          <>
                            {value.materialized_as !== "price_resolution" && (
                              <button
                                className="br-btn br-btn-primary"
                                onClick={() => setProjection(value.materialized_as)}
                              >
                                {t("Open view data")}
                              </button>
                            )}
                            {catalogLinks(
                              "projections",
                              views.find((view) => view.projection === value.materialized_as)
                                ?.route,
                            )}
                          </>
                        }
                        entry={value}
                        usedBy={views
                          .filter((view) => view.projection === value.materialized_as)
                          .map((view) => view.label)}
                      />
                    </InspectorDisclosure>
                  ))}
                </section>
                <section className="min-w-0 space-y-3" aria-label={t("Views")}>
                  <InspectorCatalogHeading
                    title="Views"
                    count={views.filter(matches).length}
                    explanation="A view is a screen or list you work with in the application, like an ERP stock list. It can show a calculated projection or stored records such as items. Several views can use the same projection."
                  />
                  {views.filter(matches).map((view) => (
                    <InspectorDisclosure key={view.key}>
                      <summary className="cursor-pointer" data-localization="original">
                        {view.label}
                      </summary>
                      <CatalogEntryDetails
                        tenant={tenant}
                        kind="view"
                        actions={
                          <>
                            <button
                              className="br-btn br-btn-primary"
                              onClick={() => setProjection(view.projection || `view:${view.key}`)}
                            >
                              {t("Open view data")}
                            </button>
                            {catalogLinks("workspaces", view.route)}
                          </>
                        }
                        entry={view}
                        projection={reference.data?.projections?.find(
                          (projection) => projection.materialized_as === view.projection,
                        )}
                      />
                    </InspectorDisclosure>
                  ))}
                </section>
              </div>
            }
          </InspectorCatalog>
        ))}
      {tab === "views" && projection && (
        <ProjectionDataDialog
          key={`${tenant}:${projection}`}
          tenant={tenant}
          name={projection}
          close={() => setProjection("")}
        />
      )}
      {tab === "history" && (
        <ActivityDrawer embedded tenant={tenant} companyName={companyName} close={() => {}} />
      )}
    </div>
  );
}
