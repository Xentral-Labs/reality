import { analyticsError } from "./errors";
import { useState } from "react";
import { analyticsApi, type AnalyticsReport } from "../../api";
import { formatDateTime, t } from "../../localization";
import { useRead } from "../useCompanyContext";
import { ReadState } from "../ReadState";

export function ReportLibrary({
  tenant,
  open,
}: {
  tenant: string;
  open: (report: AnalyticsReport) => void;
}) {
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState<string | undefined>();
  const read = useRead(() => analyticsApi.reports(tenant, query, cursor), [tenant, query, cursor]);
  const [edit, setEdit] = useState<{
    report: AnalyticsReport;
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
      await analyticsApi.change(tenant, {
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
    <section className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold">{t("My reports")}</h2>
        <p className="mt-1 text-sm text-fg-muted">
          {t("Private to you in this company. Each opening runs against current records.")}
        </p>
      </div>
      <input
        className="br-input max-w-md"
        aria-label={t("Search reports")}
        placeholder={t("Search reports")}
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setCursor(undefined);
        }}
      />
      {!read.data ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} />
      ) : (
        <>
          {!read.data.records.length && (
            <p className="rounded-xl border border-dashed border-border-default p-10 text-center text-fg-muted">
              {t("Save an analysis to find it here.")}
            </p>
          )}
          <div className="grid gap-4 lg:grid-cols-2">
            {read.data.records.map((report) => (
              <article
                key={report.id}
                className="rounded-xl border border-border-default bg-surface p-5"
              >
                <button className="text-left" onClick={() => open(report)}>
                  <h3 className="font-semibold text-accent">{report.name}</h3>
                  <p className="mt-2 text-xs text-fg-muted">
                    {t("Updated")} {formatDateTime(report.updated_at)}
                  </p>
                </button>
                <div className="mt-4 flex gap-2">
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
          <div className="flex gap-2">
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
              className="br-input my-3"
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
            <p role="alert" className="my-3 text-negative-text">
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
