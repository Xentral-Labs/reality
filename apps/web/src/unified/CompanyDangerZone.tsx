import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { api, type Bootstrap, type CompanyRow, type SandboxRun, type Tenant } from "../api";
import { formatDate, t } from "../localization";
import {
  ARCHIVE_GUARD_MESSAGES,
  archiveGuard,
  archivedCompanies,
  archivedSandboxes,
  DELETE_CONFIRMATION_WORD,
  deleteConfirmationValid,
  lossSummary,
} from "./companyLifecycle";

const message = (error: unknown) => (error instanceof Error ? error.message : String(error));

type Dialog = { kind: "archive" } | { kind: "delete"; row: CompanyRow } | null;
type Read<T> = { rows: T[] | null; error: string };

/**
 * Spec 186: the lifecycle of the selected company. A business company is archived through
 * the tenant lifecycle, a sandbox or demo company through its playground run. Archived
 * companies and sandboxes are listed with restore; permanent deletion exists for companies.
 * Every guard is repeated only to explain a disabled control; the API stays the authority.
 */
export function CompanyDangerZone({
  company,
  companies,
  openCompany,
}: {
  company: Tenant;
  companies: Tenant[];
  openCompany: (data: Bootstrap, id: string, options?: { announce?: boolean }) => void;
}) {
  const [companyRead, setCompanyRead] = useState<Read<CompanyRow>>({ rows: null, error: "" });
  const [sandboxRead, setSandboxRead] = useState<Read<SandboxRun>>({ rows: null, error: "" });
  const [dialog, setDialog] = useState<Dialog>(null);
  const [rowError, setRowError] = useState<{ id: string; text: string } | null>(null);
  const [busy, setBusy] = useState("");
  const guard = archiveGuard(company, companies);
  const sandbox = guard.kind === "sandbox";

  const load = useCallback(async () => {
    setCompanyRead((state) => ({ ...state, error: "" }));
    setSandboxRead((state) => ({ ...state, error: "" }));
    await Promise.all([
      api
        .companies()
        .then((rows) => setCompanyRead({ rows, error: "" }))
        .catch((error) => setCompanyRead((state) => ({ ...state, error: message(error) }))),
      api
        .sandboxRuns()
        .then((page) => setSandboxRead({ rows: page.runs, error: "" }))
        .catch((error) => setSandboxRead((state) => ({ ...state, error: message(error) }))),
    ]);
  }, []);
  useEffect(() => {
    void load();
  }, [load]);

  // The bootstrap decides which companies the switcher shows; after a lifecycle change the
  // selected company is kept when it is still listed, otherwise the default takes over.
  const reopen = async (preferred: string) => {
    const data = await api.bootstrap();
    const target = data.tenants.some((row) => row.id === preferred)
      ? preferred
      : data.default_tenant_id || data.tenants[0]?.id;
    // Not a creation: the shell must not announce a new company.
    if (target) openCompany(data, target, { announce: false });
  };

  const restore = async (id: string, request: () => Promise<unknown>) => {
    setBusy(id);
    setRowError(null);
    try {
      await request();
      await load();
      await reopen(company.id);
    } catch (error) {
      setRowError({ id, text: message(error) });
    } finally {
      setBusy("");
    }
  };

  const archived = companyRead.rows ? archivedCompanies(companyRead.rows) : [];
  const archivedRuns = sandboxRead.rows ? archivedSandboxes(sandboxRead.rows) : [];
  return (
    <section
      aria-labelledby="company-danger-zone-title"
      data-danger-zone={company.id}
      className="overflow-hidden rounded-xl border border-critical"
    >
      <header className="border-b border-critical bg-critical-bg px-5 py-4">
        <h2 id="company-danger-zone-title" className="text-base font-semibold text-critical-text">
          {t("Danger zone")}
        </h2>
        <p className="mt-1 text-sm text-fg-muted">
          {t(
            "Archiving hides a company or sandbox from every member. Permanent deletion removes company data and cannot be undone.",
          )}
        </p>
      </header>
      <div className="divide-y divide-border-default bg-surface">
        <div
          data-danger-action="archive"
          data-lifecycle-kind={guard.kind}
          className="flex flex-wrap items-start justify-between gap-4 px-5 py-4"
        >
          <div className="min-w-0 max-w-2xl space-y-1">
            <p className="font-medium">
              {t(sandbox ? "Archive this sandbox" : "Archive this company")}
            </p>
            <p className="break-words text-sm text-fg-muted">
              <span data-localization="original">{company.name}</span>.{" "}
              {t(
                sandbox
                  ? "The sandbox leaves the company switcher. Its records stay and you can restore it here."
                  : "The company leaves the company switcher for every member. Nothing is deleted; you can restore it here.",
              )}
            </p>
            {!guard.allowed && (
              <p data-danger-reason={guard.reason} className="text-sm text-caution-text">
                {t(ARCHIVE_GUARD_MESSAGES[guard.reason])}
              </p>
            )}
          </div>
          <button
            type="button"
            className="br-btn br-btn-critical shrink-0"
            disabled={!guard.allowed}
            onClick={() => setDialog({ kind: "archive" })}
          >
            {t(sandbox ? "Archive sandbox" : "Archive company")}
          </button>
        </div>
        <ArchivedList
          marker="archived"
          title="Archived companies"
          read={companyRead}
          loading="Loading archived companies"
          failure="Archived companies could not be loaded."
          empty="No archived companies."
          retry={load}
        >
          {archived.map((row) => (
            <li
              key={row.id}
              data-archived-company={row.id}
              className="flex flex-wrap items-start justify-between gap-4 rounded-lg border border-border-default bg-surface-sunken px-4 py-3"
            >
              <div className="min-w-0 space-y-1">
                <p className="break-words font-medium" data-localization="original">
                  {row.name}
                </p>
                <p className="text-sm text-fg-muted">
                  {t("Archived on")} {formatDate(row.archived_at)}
                </p>
                <Counts row={row} />
                {row.role !== "owner" && (
                  <p className="text-sm text-fg-muted">
                    {t("Only company owners can restore or delete this company.")}
                  </p>
                )}
                <RowError id={row.id} error={rowError} />
              </div>
              {row.role === "owner" && (
                <div className="flex shrink-0 flex-wrap gap-2">
                  <button
                    type="button"
                    className="br-btn"
                    disabled={busy === row.id}
                    onClick={() => void restore(row.id, () => api.restoreCompany(row.id))}
                  >
                    {t("Restore")}
                  </button>
                  <button
                    type="button"
                    className="br-btn br-btn-critical"
                    disabled={busy === row.id}
                    onClick={() => setDialog({ kind: "delete", row })}
                  >
                    {t("Delete permanently")}
                  </button>
                </div>
              )}
            </li>
          ))}
        </ArchivedList>
        <ArchivedList
          marker="archived-sandboxes"
          title="Archived sandboxes"
          read={sandboxRead}
          loading="Loading archived sandboxes"
          failure="Archived sandboxes could not be loaded."
          empty="No archived sandboxes."
          retry={load}
        >
          {archivedRuns.map((run) => (
            <li
              key={run.id}
              data-archived-sandbox={run.id}
              className="flex flex-wrap items-start justify-between gap-4 rounded-lg border border-border-default bg-surface-sunken px-4 py-3"
            >
              <div className="min-w-0 space-y-1">
                <p className="break-words font-medium" data-localization="original">
                  {run.company_name}
                </p>
                <p className="text-sm text-fg-muted">
                  {t(run.sandbox_kind === "practice" ? "Practice company" : "Sandbox")}
                  {" · "}
                  {t("Archived on")} {formatDate(run.archived_at)}
                </p>
                <p className="text-sm text-fg-muted">
                  {t("Deleting sandbox data is not available yet.")}
                </p>
                <RowError id={run.id} error={rowError} />
              </div>
              <button
                type="button"
                className="br-btn shrink-0"
                disabled={busy === run.id}
                onClick={() => void restore(run.id, () => api.restoreSandbox(run.id))}
              >
                {t("Restore")}
              </button>
            </li>
          ))}
        </ArchivedList>
      </div>
      {dialog?.kind === "archive" && (
        <ArchiveDialog
          company={company}
          sandbox={sandbox}
          close={() => setDialog(null)}
          confirm={async () => {
            if (sandbox) await api.archiveSandbox(company.sandbox_run_id!);
            else await api.archiveCompany(company.id);
            setDialog(null);
            await load();
            await reopen(company.id);
          }}
        />
      )}
      {dialog?.kind === "delete" && (
        <DeleteDialog
          row={dialog.row}
          close={() => setDialog(null)}
          confirm={async (name, word) => {
            await api.deleteCompany(dialog.row.id, name, word);
            setDialog(null);
            await load();
          }}
        />
      )}
    </section>
  );
}

function ArchivedList<T>({
  marker,
  title,
  read,
  loading,
  failure,
  empty,
  retry,
  children,
}: {
  marker: string;
  title: string;
  read: Read<T>;
  loading: string;
  failure: string;
  empty: string;
  retry: () => Promise<void>;
  children: ReactNode[];
}) {
  return (
    <div data-danger-action={marker} className="space-y-3 px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-medium">{t(title)}</p>
        {read.error && (
          <button type="button" className="br-btn" onClick={() => void retry()}>
            {t("Retry")}
          </button>
        )}
      </div>
      {read.error ? (
        <p role="alert" className="text-sm text-critical-text">
          {t(failure)} {read.error}
        </p>
      ) : read.rows === null ? (
        <p aria-busy="true" className="text-sm text-fg-muted">
          {t(loading)}
        </p>
      ) : children.length === 0 ? (
        <p className="text-sm text-fg-muted">{t(empty)}</p>
      ) : (
        <ul className="space-y-3">{children}</ul>
      )}
    </div>
  );
}

function RowError({ id, error }: { id: string; error: { id: string; text: string } | null }) {
  if (error?.id !== id) return null;
  return (
    <p role="alert" className="text-sm text-critical-text">
      {error.text}
    </p>
  );
}

function Counts({ row }: { row: CompanyRow }) {
  return (
    <p className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-fg-muted" data-loss-summary>
      {lossSummary(row).map((entry) => (
        <span key={entry.label}>
          {t(entry.label)}: {entry.count}
        </span>
      ))}
    </p>
  );
}

function LifecycleDialog({
  title,
  name,
  blocked,
  close,
  children,
}: {
  title: string;
  name: string;
  blocked: boolean;
  close: () => void;
  children: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const node = dialog.current!;
    node.showModal();
    return () => {
      node.close();
      trigger?.focus();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      aria-label={t(title)}
      data-lifecycle-dialog
      onCancel={(event) => {
        event.preventDefault();
        if (!blocked) close();
      }}
      className="m-auto max-h-[90dvh] w-[min(560px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-5">
        <h2 className="text-xl font-semibold">{t(title)}</h2>
        <p className="mt-2 break-words font-medium" data-localization="original">
          {name}
        </p>
      </header>
      {children}
    </dialog>
  );
}

function ArchiveDialog({
  company,
  sandbox,
  close,
  confirm,
}: {
  company: Tenant;
  sandbox: boolean;
  close: () => void;
  confirm: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const title = sandbox ? "Archive sandbox" : "Archive company";
  return (
    <LifecycleDialog title={title} name={company.name} blocked={busy} close={close}>
      <p className="text-sm text-fg-muted">
        {t(
          sandbox
            ? "The sandbox leaves the company switcher. Its records stay and you can restore it here."
            : "The company leaves the company switcher for every member. Nothing is deleted; you can restore it here.",
        )}
      </p>
      {error && (
        <p role="alert" className="mt-4 text-sm text-critical-text">
          {error}
        </p>
      )}
      <div className="mt-6 flex flex-wrap justify-end gap-2">
        <button type="button" className="br-btn" disabled={busy} onClick={close}>
          {t("Cancel")}
        </button>
        <button
          type="button"
          className="br-btn br-btn-critical"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              await confirm();
            } catch (failure) {
              setError(message(failure));
              setBusy(false);
            }
          }}
        >
          {t(title)}
        </button>
      </div>
    </LifecycleDialog>
  );
}

function DeleteDialog({
  row,
  close,
  confirm,
}: {
  row: CompanyRow;
  close: () => void;
  confirm: (name: string, word: string) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [word, setWord] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const valid = deleteConfirmationValid(row, name, word);
  return (
    <LifecycleDialog
      title="Delete company permanently"
      name={row.name}
      blocked={busy}
      close={close}
    >
      <p className="text-sm text-fg-muted">
        {t("This removes every record of the company. It cannot be undone.")}
      </p>
      <div className="mt-3">
        <Counts row={row} />
      </div>
      <form
        className="mt-5 space-y-4"
        onSubmit={async (event) => {
          event.preventDefault();
          if (!valid || busy) return;
          setBusy(true);
          setError("");
          try {
            await confirm(name, word);
          } catch (failure) {
            setError(message(failure));
            setBusy(false);
          }
        }}
      >
        <label className="block space-y-1 text-sm">
          <span className="font-medium">{t("Company name")}</span>
          <span className="block text-fg-muted">
            {t("Type the company name exactly as shown.")}
          </span>
          <input
            name="confirmation_name"
            autoComplete="off"
            spellCheck={false}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="w-full rounded-lg border border-border-default bg-surface px-3 py-2"
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">{t("Confirmation word")}</span>
          <span className="block text-fg-muted">
            {t("Type the word shown exactly.")}{" "}
            <code data-localization="original" className="font-mono text-fg-strong">
              {DELETE_CONFIRMATION_WORD}
            </code>
          </span>
          <input
            name="confirmation_word"
            autoComplete="off"
            spellCheck={false}
            value={word}
            onChange={(event) => setWord(event.target.value)}
            className="w-full rounded-lg border border-border-default bg-surface px-3 py-2"
          />
        </label>
        {error && (
          <p role="alert" className="text-sm text-critical-text">
            {error}
          </p>
        )}
        <div className="flex flex-wrap justify-end gap-2">
          <button type="button" className="br-btn" disabled={busy} onClick={close}>
            {t("Cancel")}
          </button>
          <button type="submit" className="br-btn br-btn-critical" disabled={!valid || busy}>
            {t("Delete permanently")}
          </button>
        </div>
      </form>
    </LifecycleDialog>
  );
}
