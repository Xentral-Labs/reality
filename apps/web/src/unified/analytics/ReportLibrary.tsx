import { PageActionBar } from "../PageActionBar";
import { RegisterToolbar } from "../RegisterWorkbench";
import { analyticsError } from "./errors";
import { useState } from "react";
import { graphApi, type GraphReport } from "../../api";
import { formatDateTime, t } from "../../localization";
import { useRead } from "../useCompanyContext";
import { ReadState } from "../ReadState";

export function ReportLibrary({
  tenant,
  open,
  create,
}: {
  tenant: string;
  create?: () => void;
  open: (report: GraphReport) => void;
}) {
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState<string | undefined>();
  const read = useRead(() => graphApi.reports(tenant, query, cursor), [tenant, query, cursor]);
  const [edit, setEdit] = useState<{
    report: GraphReport;
    operation: "rename" | "duplicate" | "delete";
    key: string;
  } | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    if (!edit) return;
    setBusy(true);
    setError("");
    try {
      await graphApi.change(tenant, {
        operation: edit.operation,
        request_id: edit.key,
        report_id: edit.report.id,
        expected_revision: edit.report.revision,
        ...(edit.operation === "delete" ? {} : { name }),
      });
      setEdit(null);
      read.refresh();
    } catch (failure) {
      setError(analyticsError(failure));
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="register-surface">
      {create && (
        <PageActionBar
          actions={[{ key: "new-analysis", label: "New analysis", onClick: create }]}
        />
      )}
      <div>
        <p className="mb-3 text-xs text-fg-muted">
          {t("Private to you in this company. Each opening runs against current records.")}
        </p>
      </div>
      <RegisterToolbar
        search={
          <input
            className="br-control w-full"
            aria-label={t("Search reports")}
            placeholder={t("Search reports")}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setCursor(undefined);
            }}
          />
        }
      />
      {!read.data ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} />
      ) : (
        <>
          {!read.data.records.length && (
            <p className="erp-empty text-center text-fg-muted">
              {query
                ? t("No reports match your search.")
                : t("Your saved analyses will appear here.")}
              {!query && create && (
                <button className="br-btn mt-3" onClick={create}>
                  {t("Create your first analysis")}
                </button>
              )}
            </p>
          )}
          <div className="divide-y divide-border-default">
            {read.data.records.map((report) => (
              <article
                key={report.id}
                className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm"
              >
                <button className="text-left" onClick={() => open(report)}>
                  <h3 className="font-medium text-fg-strong">{report.name}</h3>
                  <p className="mt-2 text-xs text-fg-muted">
                    {t("Updated")} {formatDateTime(report.updated_at)}
                  </p>
                </button>
                <div className="flex flex-wrap gap-2">
                  {(
                    [
                      ["rename", "Rename"],
                      ["duplicate", "Duplicate"],
                      ["delete", "Delete"],
                    ] as const
                  ).map(([operation, label]) => (
                    <button
                      className="br-btn"
                      key={operation}
                      onClick={() => {
                        setEdit({ report, operation, key: crypto.randomUUID() });
                        setName(report.name);
                        setError("");
                      }}
                    >
                      {t(label)}
                    </button>
                  ))}
                </div>
              </article>
            ))}
          </div>
          <div className="erp-register-footer flex gap-2">
            <button className="br-btn" disabled={!cursor} onClick={() => setCursor(undefined)}>
              {t("First page")}
            </button>
            <button
              className="br-btn"
              disabled={!read.data.has_more}
              onClick={() => setCursor(read.data!.next_cursor || undefined)}
            >
              {t("Next")}
            </button>
          </div>
        </>
      )}
      {edit && (
        <div
          className="rounded-xl border border-accent bg-surface p-5"
          role="dialog"
          aria-label={t("Change report")}
        >
          <h3 className="font-semibold">
            {edit.operation === "delete" ? t("Delete this report?") : t("Report name")}
          </h3>
          {edit.operation !== "delete" && (
            <input
              className="br-control my-3"
              maxLength={120}
              value={name}
              aria-label={t("Report name")}
              onChange={(event) => {
                setName(event.target.value);
                setEdit({ ...edit, key: crypto.randomUUID() });
              }}
            />
          )}
          {error && (
            <p role="alert" className="my-3 text-critical-text">
              {error}
            </p>
          )}
          <div className="mt-4 flex gap-2">
            <button
              className="br-btn br-btn-primary"
              disabled={busy || (edit.operation !== "delete" && !name.trim())}
              onClick={() => void submit()}
            >
              {busy ? t("Saving…") : t("Confirm")}
            </button>
            {error && (
              <button
                className="br-btn"
                disabled={busy}
                onClick={() => {
                  setEdit(null);
                  read.refresh();
                }}
              >
                {t("Reload")}
              </button>
            )}
            <button className="br-btn" disabled={busy} onClick={() => setEdit(null)}>
              {t("Cancel")}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
