import { RegisterHeader, RegisterWorkbench, RegisterToolbar } from "./RegisterWorkbench";
import { PageActionBar } from "./PageActionBar";
import { IntegrationPreparation } from "./IntegrationPreparation";
import { useState } from "react";
import { SourceConfiguration } from "./SourceConfiguration";
import { ItemImportPanel } from "./ItemImportPanel";
import { useRegisterQuery } from "./TableContext";
import { RegisterTable } from "./RegisterTable";

import {
  api,
  sourceWorkspaceApi,
  type SourceSystemRow,
  type SourceMetadataRow,
  type DocumentRow,
  type Page,
} from "../api";
import { formatDateTime, formatMoney, formatNumber, t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { RegisterPager } from "./WarehousePage";
import { Inspector } from "./Inspector";
import type { Selection } from "./routing";

type Data =
  | { view: "systems"; items: SourceSystemRow[]; page: Page }
  | { view: "records"; items: SourceMetadataRow[]; page: Page }
  | { view: "documents"; items: DocumentRow[]; page: Page };
const jobs: Record<string, string> = {
  pending: "Pending",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
  unmapped: "Unmapped",
};
export function DataSourcesPage({
  selection,
  navigate,
  user,
}: {
  user: string;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const [importOpen, setImportOpen] = useState(false);
  const [prepareRequest, setPrepareRequest] = useState(0);
  const {
    tenant,
    dataView: view,
    sourceSystem: system,
    sourceRecord: source,
    evidenceType: type,
    q,
    page,
    entry,
  } = selection;
  const table = useRegisterQuery();
  const read = useRead<Data>(async () => {
    if (view === "systems") return { view, ...(await sourceWorkspaceApi.systems(tenant, q, page)) };
    if (view === "records")
      return { view, ...(await sourceWorkspaceApi.records(tenant, q, system, page, table)) };
    return { view, ...(await api.documents(tenant, q, type, "", page, system, source, table)) };
  }, [tenant, view, q, page, system, source, type, table.size, table.sort, table.sort_direction]);
  const data = read.data?.view === view ? read.data : null;
  const kind = view === "records" ? "source_record" : "document";
  return (
    <RegisterWorkbench>
      <RegisterHeader title="Integrations">
        <nav className="register-tabs">
          {(
            [
              ["systems", "My integrations"],
              ["records", "Received data"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              aria-pressed={view === value}
              onClick={() =>
                navigate({ dataView: value, entry: "", q: "", page: 1, sourceRecord: "" })
              }
            >
              {t(label)}
            </button>
          ))}
        </nav>
      </RegisterHeader>
      {view === "documents" && (
        <div className="mb-4 flex items-center gap-3">
          <button
            className="br-btn"
            onClick={() =>
              navigate({ dataView: "records", entry: "", sourceRecord: "", q: "", page: 1 })
            }
          >
            {t("Back")} · {t("Received data")}
          </button>
          <h2 className="font-semibold">{t("Documents")}</h2>
        </div>
      )}
      {entry && view === "systems" && (
        <SourceConfiguration
          key={`${tenant}:${entry}`}
          tenant={tenant}
          id={entry}
          close={() => navigate({ entry: "" })}
          changed={read.refresh}
          records={(code) =>
            navigate({ dataView: "records", sourceSystem: code, entry: "", q: "", page: 1 })
          }
        />
      )}
      {(importOpen || selection.importProposal) && (
        <ItemImportPanel
          tenant={tenant}
          proposalId={selection.importProposal}
          selectProposal={(id) => navigate({ importProposal: id })}
          close={() => {
            setImportOpen(false);
            navigate({ importProposal: "" });
          }}
        />
      )}
      {view === "systems" && (
        <IntegrationPreparation
          key={`${user}:${tenant}`}
          user={user}
          tenant={tenant}
          prepareRequest={prepareRequest}
          importItems={() => {
            navigate({ entry: "" });
            setImportOpen(true);
          }}
        />
      )}
      {view === "systems" && <h2 className="mt-6 mb-3 font-semibold">{t("Registered sources")}</h2>}
      <section className="register-surface">
        <RegisterToolbar
          count={data?.page.total}
          search={
            <input
              className="br-control"
              aria-label={t("Search data")}
              value={q}
              maxLength={500}
              placeholder={t(
                view === "systems"
                  ? "Search system name or code"
                  : view === "records"
                    ? "Search origin, type or external reference"
                    : "Search document number, reference or source",
              )}
              onChange={(event) => navigate({ q: event.target.value, page: 1 })}
            />
          }
          filters={
            <>
              {view !== "systems" && (
                <label className="text-sm">
                  <span className="sr-only">{t("Exact system code")}</span>
                  <input
                    className="br-control"
                    aria-label={t("Exact system code")}
                    maxLength={200}
                    value={system}
                    placeholder={t("Exact system code")}
                    onChange={(event) =>
                      navigate({
                        sourceSystem: event.target.value,
                        sourceRecord: "",
                        entry: "",
                        page: 1,
                      })
                    }
                  />
                </label>
              )}
              {view === "documents" && (
                <label className="text-sm">
                  <span className="sr-only">{t("Document type")}</span>
                  <input
                    className="br-control"
                    aria-label={t("Document type")}
                    value={type}
                    placeholder={t("Document type")}
                    onChange={(event) => navigate({ evidenceType: event.target.value, page: 1 })}
                  />
                </label>
              )}
            </>
          }
        />
        <PageActionBar
          actions={[
            view === "systems" && {
              key: "prepare",
              label: "Add integration",
              onClick: () => setPrepareRequest((value) => value + 1),
            },
            {
              key: "register",
              label: "Register source",
              onClick: () => {
                setImportOpen(false);
                navigate({ dataView: "systems", entry: "new", importProposal: "" });
              },
            },
            {
              key: "import",
              label: "Import items",
              onClick: () => {
                navigate({ entry: "" });
                setImportOpen(true);
              },
            },
          ]}
        />

        {source && view === "documents" && (
          <div className="mb-5 flex flex-wrap items-center gap-3 rounded-lg bg-surface-muted p-3 text-xs">
            <span className="min-w-0 break-all">
              {t("Exact source version")} · {source}
            </span>
            <button
              className="br-btn"
              onClick={() => navigate({ sourceRecord: "", entry: "", page: 1 })}
            >
              {t("Clear source version")}
            </button>
          </div>
        )}
        {!data ? (
          <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={8} />
        ) : (
          <div className="min-w-0 px-4 pb-4" data-source-table-inset>
            {data.view === "systems" ? (
              <RegisterTable
                busy={read.loading}
                cursorView={{ id: "data-sources:systems", widths: [240, 180, 120, 140, 120] }}
                actionWidth={120}
                footer={
                  <div className="border-t border-border-default p-3 [&>div]:mt-0">
                    <RegisterPager page={data.page} change={(page) => navigate({ page })} />
                  </div>
                }
              >
                <thead>
                  <tr>
                    {["Name", "Source code", "Status", "Received records", "Actions"].map(
                      (label) => (
                        <th key={label}>{t(label)}</th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((row) => (
                    <tr data-source-row key={row.id}>
                      <td>
                        <strong>{row.name}</strong>
                        {row.description && (
                          <span className="block text-xs text-fg-muted">{row.description}</span>
                        )}
                      </td>
                      <td>{row.code}</td>
                      <td>{t(row.is_active ? "Enabled" : "Disabled")}</td>
                      <td>{formatNumber(row.record_count)}</td>
                      <td>
                        <div className="flex gap-2">
                          <button
                            className="br-btn"
                            onClick={() => {
                              setImportOpen(false);
                              navigate({ entry: row.id, importProposal: "" });
                            }}
                          >
                            {t("Configure source")}
                          </button>
                          <button
                            className="br-btn"
                            onClick={() =>
                              navigate({
                                dataView: "records",
                                sourceSystem: row.code,
                                sourceRecord: "",
                                entry: "",
                                q: "",
                                page: 1,
                              })
                            }
                          >
                            {t("View received records")}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </RegisterTable>
            ) : (
              <div className="min-w-0">
                <RegisterTable
                  busy={read.loading}
                  footer={<RegisterPager page={data.page} change={(page) => navigate({ page })} />}
                >
                  <thead>
                    <tr className="border-b border-border-default text-left text-fg-muted">
                      {(view === "records"
                        ? [
                            "External reference / origin",
                            "Version",
                            "Received",
                            "Import job",
                            "Details",
                          ]
                        : ["Document / party", "Type", "Recorded amount", "Origin", "Details"]
                      ).map((label) => (
                        <th key={label} className="pb-3 pr-4">
                          {t(label)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.view === "records"
                      ? data.items.map((row) => (
                          <tr
                            data-source-row
                            key={row.id}
                            className="border-b border-border-default"
                          >
                            <td className="max-w-72 py-5 pr-4">
                              <strong className="block break-all text-fg-strong">
                                {row.external_id}
                              </strong>
                              <span className="mt-1 block break-all text-xs text-fg-muted">
                                {row.source_system} · {row.source_type}
                              </span>
                            </td>
                            <td className="py-5 pr-4">{row.version}</td>
                            <td className="py-5 pr-4">{formatDateTime(row.received_at)}</td>
                            <td className="py-5 pr-4">
                              {t(
                                row.job_status
                                  ? jobs[row.job_status] || row.job_status
                                  : "No import job",
                              )}
                            </td>
                            <td className="py-5">
                              <div className="flex gap-2">
                                <button
                                  className="br-btn"
                                  onClick={() => navigate({ entry: row.id })}
                                >
                                  {t("Open received record")}
                                </button>
                                <button
                                  className="br-btn"
                                  onClick={() =>
                                    navigate({
                                      route: "facts",
                                      factSource: row.id,
                                      factSubject: "",
                                      factSubjectType: "",
                                      entry: "",
                                      proposal: "",
                                      q: "",
                                      page: 1,
                                    })
                                  }
                                >
                                  {t("View observations")}
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      : data.items.map((row) => (
                          <tr
                            data-source-row
                            key={row.id}
                            className="border-b border-border-default"
                          >
                            <td className="max-w-72 py-5 pr-4">
                              <strong className="block break-all text-fg-strong">
                                {row.number || row.id}
                              </strong>
                              <span className="mt-1 block text-xs text-fg-muted">
                                {row.party}
                                {row.date ? ` · ${row.date}` : ""}
                              </span>
                            </td>
                            <td className="py-5 pr-4">{row.type}</td>
                            <td className="py-5 pr-4 whitespace-nowrap">
                              {formatMoney(row.gross_amount, row.currency)}
                            </td>
                            <td className="max-w-56 py-5 pr-4 break-all text-xs text-fg-muted">
                              {row.source
                                ? `${row.source.system} · ${row.source.external_id}`
                                : t("No linked source")}
                            </td>
                            <td className="py-5">
                              <button
                                className="br-btn"
                                onClick={() => navigate({ entry: row.id })}
                              >
                                {t("Explain")}
                              </button>
                            </td>
                          </tr>
                        ))}
                  </tbody>
                </RegisterTable>
              </div>
            )}
          </div>
        )}
      </section>

      {entry && view !== "systems" && (
        <Inspector
          key={`${kind}:${entry}`}
          tenant={tenant}
          target={{ kind, id: entry }}
          close={() => navigate({ entry: "" })}
        />
      )}
    </RegisterWorkbench>
  );
}
