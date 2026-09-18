import { useEffect, useState } from "react";
import { ChevronRight, BookOpen, SearchCheck, Zap, ArrowUpRight } from "lucide-react";
import type { ApplicationReference, ToolCapability } from "../api";
import { t, currentLanguage } from "../localization";
import { useActionDiscovery } from "./ActionLauncher";
import { isActionForm, menuEntries, type DeliveryAction } from "./actionDiscovery";
import { RegisterToolbar } from "./RegisterWorkbench";
import { CatalogEntryDetails } from "./CatalogEntryDetails";
import { ReportExplanation } from "./ReportExplanation";
import { buildReports, type Report } from "./reportCatalogEntries";
import { capabilityTitle, filterCapabilities } from "./toolCatalogEntries";

const purposes = {
  read: "Retrieve",
  understand: "Check and explain",
  change: "Change",
  navigate: "Page shortcut",
};
const icons = { read: BookOpen, understand: SearchCheck, change: Zap, navigate: ArrowUpRight };

export function ToolCatalog({
  reference,
  tenant,
  openAction,
  openReport,
  initialQuery = "",
  initialCapability = "",
}: {
  initialQuery?: string;
  initialCapability?: string;
  reference: ApplicationReference;
  tenant: string;
  openAction: (form: DeliveryAction) => void;
  openReport: (report: Report) => void;
}) {
  const context = useActionDiscovery();
  const [query, setQuery] = useState(initialQuery);
  const [topic, setTopic] = useState("");
  const [purpose, setPurpose] = useState("");
  const [expanded, setExpanded] = useState<string | null>(initialCapability || null);
  useEffect(() => {
    setQuery(initialQuery);
    setTopic("");
    setPurpose("");
    setExpanded(initialCapability || null);
    if (initialCapability)
      requestAnimationFrame(() => {
        const target = document.getElementById(`capability-${initialCapability}`);
        target?.scrollIntoView({ block: "nearest" });
        target?.querySelector<HTMLButtonElement>("button")?.focus({ preventScroll: true });
      });
  }, [initialQuery, initialCapability]);
  const catalog = reference.tool_catalog;
  const language = currentLanguage();
  const reports = buildReports(reference);
  const representations = (row: ToolCapability) =>
    reports.filter(
      (report) =>
        row.projections.includes(report.target) ||
        row.id === `report:${report.target}` ||
        report.views.some((view) => row.views.includes(view.key)),
    );
  // Existing business wording for calculated views is more useful than technical names.
  const entries = (catalog?.entries || []).map((row) => {
    const report = representations(row)[0];
    return report
      ? { ...row, title: report.title, description: report.description, labels: {} }
      : row;
  });
  const filtered = filterCapabilities(entries, query, topic, purpose, t, language);
  const available = menuEntries(reference, "global", context || undefined);
  const title = (row: ToolCapability) => capabilityTitle(row, t, language);
  if (!catalog)
    return (
      <p role="status" className="text-sm text-fg-muted">
        {t("Tool catalog is unavailable. Reload to try again.")}
      </p>
    );
  const details = (row: ToolCapability) => {
    const tools = catalog.mcp_tools.filter((tool) => row.mcp.includes(tool.name));
    const forms = available.filter((form) => row.discovery.includes(form.key));
    const report = representations(row)[0];
    return (
      <div className="tool-capability-details">
        {row.description && <p className="text-sm text-fg-muted">{t(row.description)}</p>}
        {row.purpose === "change" && (
          <p className="text-xs text-fg-muted">
            {t("Changes use the existing review and confirmation flow.")}
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          {tools.some((tool) => tool.access !== "confirm") && (
            <button
              className="br-btn"
              onClick={() => {
                window.dispatchEvent(
                  new CustomEvent("reality:open-chat", {
                    detail: {
                      kind: "tool-capability",
                      tenant,
                      prompt: `${t("Help me use this capability:")} ${title(row)} (${tools
                        .filter((tool) => tool.access !== "confirm")
                        .map((tool) => tool.name)
                        .join(", ")})`,
                    },
                  }),
                );
              }}
            >
              {t("Use in chat")}
            </button>
          )}
          {forms.map((form) => (
            <button
              key={form.key}
              className="br-btn"
              onClick={() => {
                if (form.form && isActionForm(form.form)) openAction(form.form);
                else if (form.destination)
                  context?.navigate({
                    ...form.destination,
                    q: "",
                    entry: "",
                    record: "",
                    proposal: "",
                    page: 1,
                  });
              }}
            >
              {t(form.label)}
            </button>
          ))}
          {report && (
            <button className="br-btn" data-tool-report-open onClick={() => openReport(report)}>
              {t(report.dataAvailable ? "Open report" : "Show details")}
            </button>
          )}
        </div>
        {!forms.length && !report && (
          <p className="text-xs text-fg-muted">{t("No direct Web action is available here.")}</p>
        )}
        {!!tools.length && (
          <p className="text-xs text-fg-muted">
            {t("MCP support describes available tools, not permission for your connection.")}
          </p>
        )}
        {!!row.related.length && (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-fg-muted">{t("Related capabilities")}</span>
            {row.related.map((id) => {
              const related = entries.find((entry) => entry.id === id);
              return (
                related && (
                  <button
                    key={id}
                    className="br-btn"
                    onClick={() => {
                      setQuery("");
                      setTopic("");
                      setPurpose("");
                      setExpanded(id);
                      requestAnimationFrame(() => {
                        const target = document.getElementById(`capability-${id}`);
                        target
                          ?.querySelector<HTMLButtonElement>("button")
                          ?.focus({ preventScroll: true });
                        target?.scrollIntoView({ block: "center" });
                      });
                    }}
                  >
                    {title(related)}
                  </button>
                )
              );
            })}
          </div>
        )}
        <details className="tool-technical-details">
          <summary>{t("Technical details")}</summary>
          <div className="space-y-4 pt-3">
            {tools.map((tool) => (
              <div key={tool.name} className="space-y-2" data-tool-mcp={tool.name}>
                <h4 className="break-all text-sm font-medium">{tool.name}</h4>
                <p className="text-xs text-fg-muted">
                  {t(
                    tool.access === "read"
                      ? "Read only"
                      : tool.access === "confirm"
                        ? "Approve and execute"
                        : "Prepares a proposal; does not execute it.",
                  )}
                </p>
                <p className="text-sm" data-localization="original">
                  {tool.description}
                </p>
                <details>
                  <summary>{t("Parameters")}</summary>
                  <pre
                    className="overflow-auto rounded bg-surface-muted p-3 text-xs"
                    data-localization="original"
                  >
                    {JSON.stringify(tool.input_schema, null, 2)}
                  </pre>
                </details>
              </div>
            ))}
            {row.commands.map((service) => {
              const command = reference.commands?.find((c) => c.service === service);
              return (
                command && (
                  <CatalogEntryDetails
                    key={service}
                    tenant={tenant}
                    kind="command"
                    entry={command}
                    actions={null}
                  />
                )
              );
            })}
            {representations(row).map((representation) => (
              <div key={representation.target}>
                {representation !== report && (
                  <button className="br-btn" onClick={() => openReport(representation)}>
                    {t("Open report")}: {t(representation.title)}
                  </button>
                )}
                <ReportExplanation report={representation} tenant={tenant} workspaceLinks={[]} />
              </div>
            ))}
          </div>
        </details>
      </div>
    );
  };
  return (
    <section data-tool-catalog className="tool-catalog">
      <p className="mb-4 text-sm text-fg-muted">{t("What Reality and your agents can do.")}</p>
      <RegisterToolbar
        count={filtered.length}
        search={
          <input
            className="br-control"
            type="search"
            aria-label={t("Search capabilities")}
            placeholder={t("Search capabilities")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        }
        filters={
          <>
            <select
              aria-label={t("Topic")}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            >
              <option value="">{t("All topics")}</option>
              {catalog.topics.map((item) => (
                <option key={item.key} value={item.key}>
                  {t(item.label)}
                </option>
              ))}
            </select>
            <select
              aria-label={t("Purpose")}
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
            >
              <option value="">{t("All purposes")}</option>
              {Object.entries(purposes).map(([key, label]) => (
                <option key={key} value={key}>
                  {t(label)}
                </option>
              ))}
            </select>
            {(query || topic || purpose) && (
              <button
                className="br-btn"
                onClick={() => {
                  setQuery("");
                  setTopic("");
                  setPurpose("");
                }}
              >
                {t("Reset filters")}
              </button>
            )}
          </>
        }
      />
      {!filtered.length && (
        <p role="status" className="py-8 text-sm text-fg-muted">
          {t("No matching records")}
        </p>
      )}
      {catalog.topics.map((group) => {
        const rank = { read: 0, understand: 1, change: 2, navigate: 3 };
        const rows = filtered
          .filter((row) => row.topic === group.key)
          .sort(
            (a, b) =>
              rank[a.purpose] - rank[b.purpose] || title(a).localeCompare(title(b), language),
          );
        return (
          !!rows.length && (
            <section key={group.key} className="tool-topic" aria-label={t(group.label)}>
              <h2>
                {t(group.label)} <span>{rows.length}</span>
              </h2>
              {rows.map((row) => {
                const Icon = icons[row.purpose];
                return (
                  <div key={row.id} id={`capability-${row.id}`} data-tool-capability={row.id}>
                    <button
                      className="tool-capability"
                      aria-expanded={expanded === row.id}
                      aria-controls={`details-${row.id}`}
                      onClick={() => setExpanded(expanded === row.id ? null : row.id)}
                    >
                      <Icon size={16} aria-hidden="true" />
                      <span className="tool-capability-name">{title(row)}</span>
                      <span className="tool-capability-kind">{t(purposes[row.purpose])}</span>
                      {!!row.mcp.length && <span className="tool-capability-access">MCP</span>}
                      <ChevronRight
                        size={14}
                        className={expanded === row.id ? "rotate-90" : ""}
                        aria-hidden="true"
                      />
                    </button>
                    {expanded === row.id && <div id={`details-${row.id}`}>{details(row)}</div>}
                  </div>
                );
              })}
            </section>
          )
        );
      })}
    </section>
  );
}
