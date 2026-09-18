import { RegisterHeader, RegisterToolbar } from "../RegisterWorkbench";
import { PageActionBar } from "../PageActionBar";
import { useMemo, useState } from "react";
import { graphApi, type GraphCatalog, type GraphNode, type GraphQuestion } from "../../api";
import {
  currentLanguage,
  formatCalendarDate,
  formatDateTime,
  formatExactDecimal,
  t,
} from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { explorePlan, question } from "./GraphSteps";
import "./AnalysisBuilder.css";
import { catalogGroups } from "./catalog";

export function DataExplorer({
  tenant,
  open,
}: {
  tenant: string;
  open: (value: GraphQuestion) => void;
}) {
  const read = useRead(
    () => graphApi.catalog(tenant, currentLanguage()),
    [tenant, currentLanguage()],
  );
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return <Catalog key={tenant} tenant={tenant} catalog={read.data} open={open} />;
}
function Catalog({
  tenant,
  catalog,
  open,
}: {
  tenant: string;
  catalog: GraphCatalog;
  open: (value: GraphQuestion) => void;
}) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(catalog.nodes[0]?.key ?? "");
  const [tab, setTab] = useState("fields");
  const nodes = useMemo(
    () => Object.fromEntries(catalog.nodes.map((node) => [node.key, node])),
    [catalog],
  );
  const groups = catalogGroups(catalog.nodes, search);
  const node = nodes[selected];
  const use = (field?: string, edge?: string, direction: "in" | "out" = "out") => {
    if (node) open(question(explorePlan(node, nodes, field, edge, direction)));
  };
  const edges = node
    ? [
        ...node.edges.map((edge) => ({ ...edge, target: edge.to, direction: "out" as const })),
        ...node.edges_in.map((edge) => ({ ...edge, target: edge.from, direction: "in" as const })),
      ]
    : [];
  return (
    <section className="analysis-builder analysis-catalog">
      <PageActionBar
        actions={[
          {
            key: "use-analysis",
            label: "Use in analysis",
            disabled: !node?.properties.length,
            onClick: () => use(),
          },
        ]}
      />
      <div className="analysis-catalog-banner">
        <div>
          <p>{t("Explore the available analysis objects and their relationships.")}</p>
        </div>
        <div className="analysis-catalog-counts">
          <span>
            <strong>{catalog.nodes.length}</strong>
            {t("Objects")}
          </span>
          <span>
            <strong>{catalog.nodes.reduce((sum, node) => sum + node.edges.length, 0)}</strong>
            {t("Relationships")}
          </span>
          <span>
            <strong>{catalog.nodes.reduce((sum, node) => sum + node.properties.length, 0)}</strong>
            {t("Fields")}
          </span>
        </div>
      </div>
      <div className="analysis-catalog-layout">
        <aside className="analysis-card analysis-catalog-sidebar">
          <RegisterToolbar
            search={
              <input
                className="br-control w-full"
                aria-label={t("Search data catalog")}
                placeholder={t("Search objects and fields…")}
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            }
          />
          <h3>{t("Business objects")}</h3>
          {groups.map(([category, items]) => (
            <details
              className="analysis-object-group"
              key={category}
              open={Boolean(search.trim()) || items.some((item) => item.key === selected)}
            >
              <summary>
                {category || t("Business objects")} <small>{items.length}</small>
              </summary>
              {items.map((item) => (
                <button
                  key={item.key}
                  aria-pressed={selected === item.key}
                  onClick={() => setSelected(item.key)}
                >
                  <span className="analysis-object-icon">
                    {item.label.slice(0, 2).toLocaleUpperCase()}
                  </span>
                  <strong>{item.label}</strong>
                  <small>
                    {item.properties.length} {t("Fields")}
                  </small>
                </button>
              ))}
            </details>
          ))}
          {!groups.length && <p>{t("No matching objects or fields.")}</p>}
        </aside>
        {node && (
          <div className="analysis-card analysis-catalog-detail">
            <header className="analysis-card-heading">
              <div>
                <h3>{node.label}</h3>
                <p>{t(node.grain)}</p>
              </div>
            </header>
            <RegisterHeader title="Data catalog views" placement="local">
              <div className="register-tabs" aria-label={t("Data catalog views")}>
                {[
                  ["fields", "Fields"],
                  ["relationships", "Relationships"],
                  ["data", "Preview data"],
                ].map(([key, label]) => (
                  <button key={key} aria-pressed={tab === key} onClick={() => setTab(key)}>
                    {t(label)}
                  </button>
                ))}
              </div>
            </RegisterHeader>
            <div className="analysis-panel">
              {tab === "fields" && (
                <div className="erp-table-scroll">
                  <table className="erp-table w-full">
                    <thead>
                      <tr>
                        <th>{t("Field")}</th>
                        <th>{t("Type")}</th>
                        <th>{t("Meaning")}</th>
                        <th>
                          <span className="sr-only">{t("Actions")}</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {node.properties.map((field) => (
                        <tr key={field.key}>
                          <td>
                            <strong>{field.label}</strong>
                            <small>{field.key}</small>
                          </td>
                          <td>
                            {t(
                              field.kind === "time"
                                ? "Date"
                                : field.kind === "number"
                                  ? "Numeric field"
                                  : field.kind === "boolean"
                                    ? "Yes / No"
                                    : "Text",
                            )}
                          </td>
                          <td>{field.identity ? t("Unique record identity") : field.label}</td>
                          <td>
                            <button className="br-btn" onClick={() => use(field.key)}>
                              {t("+ Analysis")}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {tab === "relationships" && (
                <div className="analysis-catalog-edges">
                  {edges.map((edge) => (
                    <div key={`${edge.key}-${edge.direction}`}>
                      <div>
                        <strong>
                          {edge.direction === "out" ? node.label : nodes[edge.target]?.label}
                        </strong>{" "}
                        <span className="analysis-token analysis-relation">{edge.label}</span>{" "}
                        <strong>
                          {edge.direction === "out" ? nodes[edge.target]?.label : node.label}
                        </strong>
                        <p>→ {edge.multiplicity}</p>
                      </div>
                      <button
                        className="br-btn"
                        onClick={() => use(undefined, edge.key, edge.direction)}
                      >
                        {t("Open path")}
                      </button>
                    </div>
                  ))}
                  {!edges.length && <p>{t("No declared relationships.")}</p>}
                </div>
              )}
              {tab === "data" && !node.properties.length && (
                <p>{t("This object has no queryable fields yet.")}</p>
              )}
              {tab === "data" && node.properties.length > 0 && (
                <Preview
                  key={node.key}
                  tenant={tenant}
                  node={node}
                  nodes={nodes}
                  open={() => use()}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
function Preview(props: {
  tenant: string;
  node: GraphNode;
  nodes: Record<string, GraphNode>;
  open: () => void;
}) {
  if (props.node.properties.some((field) => field.input === "date"))
    return (
      <div className="flex flex-wrap items-center gap-3">
        <p>{t("Choose a snapshot date in the analysis to preview historical values.")}</p>
        <button className="br-btn" onClick={props.open}>
          {t("Use in analysis")}
        </button>
      </div>
    );
  return <CurrentPreview {...props} />;
}

function CurrentPreview({
  tenant,
  node,
  nodes,
  open,
}: {
  tenant: string;
  node: GraphNode;
  nodes: Record<string, GraphNode>;
  open: () => void;
}) {
  const plan = useMemo(() => ({ ...explorePlan(node, nodes), limit: 5 }), [node, nodes]);
  const read = useRead(() => graphApi.ask(tenant, question(plan)), [tenant, node.key]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return (
    <>
      <div className="analysis-editor-heading">
        <span>{t("Preview of up to five records")}</span>
        <button className="br-btn" onClick={open}>
          {t("Query these records")}
        </button>
      </div>
      {!read.data.rows.length ? (
        <p>{t("No records match. That is not proof that none exist upstream.")}</p>
      ) : (
        <div className="erp-table-scroll">
          <table className="erp-table w-full">
            <thead>
              <tr>
                {plan.groups.map((group) => (
                  <th key={group.field}>{group.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {read.data.rows.map((row, index) => (
                <tr key={index}>
                  {plan.groups.map((group) => {
                    const value = row[group.field];
                    const property = node.properties.find(
                      (field) => group.field === `o.${field.key}`,
                    );
                    return (
                      <td key={group.field}>
                        {catalogValue(value, property?.kind, property?.temporal)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

export function catalogValue(value: unknown, kind?: string, temporal?: "date"): string {
  if (value == null) return t("Unknown");
  if (kind === "time")
    return temporal === "date" ? formatCalendarDate(String(value)) : formatDateTime(String(value));
  if (kind === "number") return formatExactDecimal(String(value));
  if (kind === "boolean") {
    if (value === true || value === 1 || value === "true") return t("Yes");
    if (value === false || value === 0 || value === "false") return t("No");
  }
  return String(value);
}
