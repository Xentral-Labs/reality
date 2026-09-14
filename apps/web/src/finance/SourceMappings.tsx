import { SettingsEmptyState } from "./SettingsEmptyState";
import { SettingsToolbar } from "./SettingsToolbar";
import { SettingsDialog, ReviewNotice } from "./SettingsDialog";
import { useEffect, useState, type FormEvent } from "react";
import { formatDateTime, t } from "../localization";

type Reference = { id: string; code: string; name: string };
type Mapping = {
  id: string;
  source_system_id: string;
  namespace: string;
  source_code: string;
  field_kind: string;
  reference_id: string;
  state: string;
  revision: number;
  reference_snapshot: Reference;
  reason: string;
  actor_id: string | null;
  action_id: string;
  created_at: string;
};
type Context = {
  revision: number;
  total: number;
  items: Mapping[];
  sources: { id: string; code: string; name: string; active: boolean }[];
  sources_total: number;
  references: Record<string, { total: number; items: Reference[] }>;
};
type Pending = {
  id: string;
  preview: {
    source_mapping: { before: Mapping | null; after: Mapping; reason: string; source: Reference };
  };
};
async function call<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...(body ? { method: "POST", body: JSON.stringify(body) } : {}),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || t("Request failed"));
  return result;
}
function Snapshot({ row }: { row: Mapping | null }) {
  if (!row) return <p>{t("No previous mapping")}</p>;
  return (
    <p className="break-words">
      <span data-original>
        {row.namespace} · {row.source_code}
      </span>{" "}
      →{" "}
      <span data-original>
        {row.reference_snapshot.code} · {row.reference_snapshot.name}
      </span>{" "}
      · {t(row.state === "active" ? "Active" : row.state === "blocked" ? "Blocked" : "Retired")} ·{" "}
      {t("Revision")} {row.revision}
    </p>
  );
}
export function SourceMappings({
  tenantId,
  canManage,
  embedded = false,
}: {
  tenantId: string;
  canManage: boolean;
  embedded?: boolean;
}) {
  const [open, setOpen] = useState(false);
  if (embedded)
    return (
      <section
        aria-label={t("Source code mappings")}
        className="min-w-0 space-y-4 rounded-xl border border-border-default bg-surface p-5"
      >
        <h2 className="text-lg font-semibold">{t("Source code mappings")}</h2>
        <MappingBody key={tenantId} tenantId={tenantId} canManage={canManage} />
      </section>
    );
  return (
    <details
      className="space-y-4 rounded-xl border border-border-default bg-surface p-5"
      onToggle={(e) => setOpen(e.currentTarget.open)}
    >
      <summary className="cursor-pointer font-semibold">{t("Source code mappings")}</summary>
      {open && <MappingBody key={tenantId} tenantId={tenantId} canManage={canManage} />}
    </details>
  );
}
function MappingBody({ tenantId, canManage }: { tenantId: string; canManage: boolean }) {
  const base = `/api/tenants/${encodeURIComponent(tenantId)}`;
  const storage = `source-mapping-proposal:${tenantId}`;
  const [query, setQuery] = useState("");
  const [sourceQuery, setSourceQuery] = useState("");
  const [referenceQuery, setReferenceQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const [data, setData] = useState<Context | null>(null);
  const [hasEntries, setHasEntries] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<Mapping | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [kind, setKind] = useState("case_code");
  const [history, setHistory] = useState<{
    total: number;
    items: Mapping[];
    id: string;
    offset: number;
  } | null>(null);
  const [pending, setPending] = useState<Pending | null>(() => {
    try {
      return JSON.parse(sessionStorage.getItem(storage) || "null");
    } catch {
      return null;
    }
  });
  useEffect(() => {
    if (pending) setEditorOpen(true);
  }, [pending]);
  useEffect(() => {
    if (pending) sessionStorage.setItem(storage, JSON.stringify(pending));
    else sessionStorage.removeItem(storage);
  }, [pending, storage]);
  useEffect(() => {
    let active = true;

    call<Context>(
      `${base}/finance/source-mappings?${new URLSearchParams({ query, source_query: sourceQuery, reference_query: referenceQuery, offset: String(offset), limit: "50" })}`,
    )
      .then((value) => {
        if (active) {
          setData(value);
          if (!query && offset === 0) setHasEntries(value.total > 0);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [base, query, sourceQuery, referenceQuery, offset, reload]);
  async function run(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await work();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  async function propose(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!data) return;
    const form = new FormData(event.currentTarget);
    await run(async () => {
      setPending(
        await call<Pending>(`${base}/finance/source-mappings/proposals`, {
          tool: "finance.source_mapping.set",
          arguments: {
            expected_revision: data.revision,
            source_system_id: editing?.source_system_id || String(form.get("source")),
            namespace: editing?.namespace || String(form.get("namespace")),
            source_code: editing?.source_code || String(form.get("code")),
            field_kind: editing?.field_kind || kind,
            reference_id: String(form.get("reference")),
            state: String(form.get("state")),
            reason: String(form.get("reason")),
          },
        }),
      );
    });
  }
  async function decide(approve: boolean) {
    if (!pending) return;
    await run(async () => {
      await call(`${base}/change-proposals/${pending.id}/${approve ? "approve" : "reject"}`, {});
      setPending(null);
      setEditorOpen(false);
      setData(null);
      setEditing(null);
      setReload((x) => x + 1);
    });
  }
  async function showHistory(id: string, next = 0) {
    await run(async () => {
      const value = await call<{ total: number; items: Mapping[] }>(
        `${base}/finance/source-mappings/${encodeURIComponent(id)}/history?limit=50&offset=${next}`,
      );
      setHistory({ ...value, id, offset: next });
    });
  }
  const choices = data?.references[editing?.field_kind || kind];
  return (
    <div className="space-y-4">
      <p className="text-sm text-fg-muted">
        {t(
          "Translate declared source codes into defined internal references. No amounts or postings change.",
        )}
      </p>
      {error && !editorOpen && (
        <div role="alert">
          <p>{error}</p>
          <button
            className="br-btn"
            onClick={() => {
              setError("");
              setReload((x) => x + 1);
            }}
          >
            {t("Retry")}
          </button>
        </div>
      )}
      <SettingsToolbar>
        {hasEntries && (
          <button className="br-btn" onClick={() => setReload((x) => x + 1)}>
            {t("Refresh")}
          </button>
        )}
        {canManage && (
          <button
            className="br-btn br-btn-primary"
            disabled={!data || busy || !!pending}
            onClick={() => {
              setEditing(null);
              setError("");
              setEditorOpen(true);
            }}
          >
            {t("New source mapping")}
          </button>
        )}
      </SettingsToolbar>
      {(hasEntries || query) && (
        <label className="grid w-full gap-1 text-sm sm:max-w-md">
          {t("Search source mappings")}
          <input
            className="br-control w-full"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setOffset(0);
            }}
          />
        </label>
      )}
      {!data && !error && <p role="status">{t("Loading")}</p>}
      {data && (
        <>
          {data.total === 0 && (
            <SettingsEmptyState
              reset={
                query || offset > 0
                  ? () => {
                      setQuery("");
                      setOffset(0);
                    }
                  : undefined
              }
            />
          )}
          <div className="space-y-2">
            {data.items.map((row) => (
              <article
                key={row.id}
                className="space-y-2 rounded-lg border border-border-default p-3"
              >
                <p data-original>
                  {data.sources.find((s) => s.id === row.source_system_id)?.name ||
                    row.source_system_id}
                </p>
                <p>{t(row.field_kind === "case_code" ? "Case code" : "Coding group")}</p>
                <Snapshot row={row} />
                <div className="flex flex-wrap gap-2">
                  {canManage && (
                    <button
                      className="finance-row-button"
                      disabled={busy || !!pending}
                      onClick={() => {
                        setEditing(row);
                        setEditorOpen(true);
                        setError("");
                        setKind(row.field_kind);
                      }}
                    >
                      {t("Edit")}
                    </button>
                  )}
                  <button
                    className="finance-row-button"
                    disabled={busy}
                    onClick={() => showHistory(row.id)}
                  >
                    {t("History")}
                  </button>
                </div>
              </article>
            ))}
          </div>
          {(offset > 0 || data.total > 50) && (
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <button
                className="br-btn"
                disabled={!offset}
                onClick={() => setOffset((x) => Math.max(0, x - 50))}
              >
                {t("Previous")}
              </button>
              <button
                className="br-btn"
                disabled={offset + 50 >= data.total}
                onClick={() => setOffset((x) => x + 50)}
              >
                {t("Next")}
              </button>
            </div>
          )}
          {canManage && editorOpen && !pending && (
            <SettingsDialog
              title={t(editing ? "Edit source mapping" : "New source mapping")}
              description={t(
                "Choose the source system and its original code, then the internal case code or coding group it means.",
              )}
              busy={busy}
              error={error}
              close={() => setEditorOpen(false)}
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <label>
                  {t("Search source systems…")}
                  <input
                    className="br-control w-full"
                    value={sourceQuery}
                    onChange={(e) => setSourceQuery(e.target.value)}
                  />
                </label>
                <label>
                  {t("Search references")}
                  <input
                    className="br-control w-full"
                    value={referenceQuery}
                    onChange={(e) => setReferenceQuery(e.target.value)}
                  />
                </label>
              </div>
              <form key={editing?.id || "new"} onSubmit={propose} className="space-y-5">
                <p className="text-sm text-fg-muted sm:col-span-2">
                  {t("All fields are required unless marked optional.")}
                </p>
                <fieldset disabled={busy} className="min-w-0 space-y-5">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <label>
                      {t("Source system")}
                      <select
                        name="source"
                        aria-label={t("Source system")}
                        className="br-control w-full"
                        required
                        disabled={!!editing}
                        defaultValue={editing?.source_system_id || ""}
                      >
                        <option value="">{t("Select source system")}</option>
                        {data.sources.map((s) => (
                          <option key={s.id} value={s.id} disabled={!s.active && !editing}>
                            {s.code} · {s.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      {t("Classification kind")}
                      <select
                        className="br-control w-full"
                        value={kind}
                        aria-label={t("Classification kind")}
                        disabled={!!editing}
                        onChange={(e) => setKind(e.target.value)}
                      >
                        <option value="case_code">{t("Case code")}</option>
                        <option value="coding_group">{t("Coding group")}</option>
                      </select>
                    </label>
                    <label>
                      {t("Source namespace")}
                      <input
                        name="namespace"
                        className="br-control w-full"
                        required
                        maxLength={200}
                        readOnly={!!editing}
                        defaultValue={editing?.namespace || ""}
                      />
                    </label>
                    <label>
                      {t("Declared source code")}
                      <input
                        name="code"
                        className="br-control w-full"
                        required
                        maxLength={200}
                        readOnly={!!editing}
                        defaultValue={editing?.source_code || ""}
                      />
                    </label>
                    <label>
                      {t("Internal reference")}
                      <select
                        key={`${kind}:${editing?.id}`}
                        name="reference"
                        aria-label={t("Internal reference")}
                        className="br-control w-full"
                        required
                        defaultValue={editing?.reference_id || ""}
                      >
                        <option value="">{t("Select reference")}</option>
                        {editing && !choices?.items.some((r) => r.id === editing.reference_id) && (
                          <option value={editing.reference_id}>
                            {editing.reference_snapshot.code} · {editing.reference_snapshot.name}
                          </option>
                        )}
                        {choices?.items.map((r) => (
                          <option key={r.id} value={r.id}>
                            {r.code} · {r.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      {t("Status")}
                      <select
                        name="state"
                        aria-label={t("Status")}
                        className="br-control w-full"
                        defaultValue={editing?.state || "active"}
                      >
                        <option value="active">{t("Active")}</option>
                        {editing && <option value="blocked">{t("Blocked")}</option>}
                      </select>
                    </label>
                  </div>
                  {choices && choices.total > choices.items.length && (
                    <p>{t("Refine the search to find more references.")}</p>
                  )}
                  {data.sources_total > data.sources.length && (
                    <p>{t("Refine the search to find more source systems.")}</p>
                  )}
                  <p className="text-sm text-fg-muted sm:col-span-2">
                    {t(
                      "The source namespace groups codes from the same source, for example a tax-code list. Copy namespace and code exactly as received.",
                    )}
                  </p>
                  <label className="block">
                    {t("Reason")}
                    <textarea
                      name="reason"
                      className="br-control w-full"
                      required
                      maxLength={4000}
                    />
                  </label>
                  <div className="finance-form-actions">
                    <button className="br-btn br-btn-primary" disabled={busy}>
                      {t("Review source mapping")}
                    </button>
                    {
                      <button type="button" className="br-btn" onClick={() => setEditorOpen(false)}>
                        {t("Cancel")}
                      </button>
                    }
                  </div>
                </fieldset>
              </form>
            </SettingsDialog>
          )}
        </>
      )}
      {pending && !editorOpen && <ReviewNotice open={() => setEditorOpen(true)} />}
      {pending && (
        <>
          {editorOpen && (
            <SettingsDialog
              title={t("Confirm source mapping")}
              description={t(
                "Check the proposed values. The change takes effect only after confirmation.",
              )}
              busy={busy}
              error={error}
              close={() => setEditorOpen(false)}
            >
              <section
                className="space-y-3 rounded-lg border border-border-default p-4"
                aria-label={t("Confirm source mapping")}
              >
                <p data-original>{pending.preview.source_mapping.source.name}</p>
                <p>{t("Before")}</p>
                <Snapshot row={pending.preview.source_mapping.before} />
                <p>{t("After")}</p>
                <Snapshot row={pending.preview.source_mapping.after} />
                <p data-original>{pending.preview.source_mapping.reason}</p>
                <div className="flex gap-2">
                  {canManage && (
                    <button
                      className="br-btn br-btn-primary"
                      disabled={busy}
                      onClick={() => decide(true)}
                    >
                      {t("Confirm")}
                    </button>
                  )}
                  <button
                    className="br-btn"
                    disabled={busy || !canManage}
                    onClick={() => decide(false)}
                  >
                    {t("Cancel")}
                  </button>
                </div>
              </section>
            </SettingsDialog>
          )}
        </>
      )}
      {history && (
        <SettingsDialog
          title={t("Source mapping history")}
          busy={busy}
          error={error}
          close={() => setHistory(null)}
        >
          <section className="space-y-3" aria-label={t("Source mapping history")}>
            {history.items.map((row) => (
              <article key={row.id} className="space-y-2 border-b border-border-default pb-3">
                <Snapshot row={row} />
                <time dateTime={row.created_at}>{formatDateTime(row.created_at)}</time>
                <p data-original>{row.reason}</p>
                <p className="break-all">
                  {t("Actor")}: <span data-original>{row.actor_id || "—"}</span> · {t("Action")}:{" "}
                  <span data-original>{row.action_id}</span>
                </p>
              </article>
            ))}
            <div className="flex gap-2">
              <button
                className="br-btn"
                disabled={busy || history.offset === 0}
                onClick={() => showHistory(history.id, history.offset - 50)}
              >
                {t("Previous")}
              </button>
              <button
                className="br-btn"
                disabled={busy || history.offset + 50 >= history.total}
                onClick={() => showHistory(history.id, history.offset + 50)}
              >
                {t("Next")}
              </button>
              <button className="br-btn" onClick={() => setHistory(null)}>
                {t("Close")}
              </button>
            </div>
          </section>
        </SettingsDialog>
      )}
    </div>
  );
}

export type SourceResolution = Record<
  string,
  { status: string; mapping_id: string | null; reference: Reference | null }
>;
export const resolutionLabels: Record<string, string> = {
  missing: "No declared code",
  malformed: "Invalid source declaration",
  missing_source: "Source system not registered",
  blocked_source: "Source system blocked",
  unmapped: "No source mapping",
  blocked_mapping: "Source mapping blocked",
  blocked_reference: "Internal reference blocked",
  conflict: "Conflicts with internal assignment",
  resolved: "Source code resolved",
};
export function SourceResolutionView({
  value,
  tenantId,
}: {
  value?: SourceResolution;
  tenantId: string;
}) {
  const [historyId, setHistoryId] = useState<string | null>(null);
  if (!value) return null;
  return (
    <section className="space-y-2 rounded-lg border border-border-default p-3">
      <h4 className="font-semibold">{t("Source classification")}</h4>
      <p>{t("Source classification and internal assignments remain separate.")}</p>
      {Object.entries(value).map(([kind, row]) => (
        <p key={kind} className="break-words">
          {t(kind === "case" ? "Case code" : "Coding group")}:{" "}
          {t(resolutionLabels[row.status] || "Unknown")}
          {row.reference && (
            <>
              {" "}
              ·{" "}
              <span data-original>
                {row.reference.code} · {row.reference.name}
              </span>
            </>
          )}
          {row.mapping_id && (
            <button className="br-btn block text-xs" onClick={() => setHistoryId(row.mapping_id)}>
              {t("Source mapping history")}
            </button>
          )}
        </p>
      ))}
      {historyId && (
        <ResolutionHistory
          key={historyId}
          tenantId={tenantId}
          mappingId={historyId}
          close={() => setHistoryId(null)}
        />
      )}
    </section>
  );
}

function ResolutionHistory({
  tenantId,
  mappingId,
  close,
}: {
  tenantId: string;
  mappingId: string;
  close: () => void;
}) {
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const [data, setData] = useState<{ total: number; items: Mapping[] } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setData(null);
    setError("");
    call<{ total: number; items: Mapping[] }>(
      `/api/tenants/${encodeURIComponent(tenantId)}/finance/source-mappings/${encodeURIComponent(mappingId)}/history?limit=50&offset=${offset}`,
    )
      .then((result) => {
        if (active) setData(result);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [tenantId, mappingId, offset, reload]);
  return (
    <section className="space-y-3" aria-label={t("Source mapping history")}>
      <h4>{t("Source mapping history")}</h4>
      {error && (
        <div role="alert">
          {error}
          <button className="br-btn" onClick={() => setReload((x) => x + 1)}>
            {t("Retry")}
          </button>
        </div>
      )}
      {!data && !error && <p role="status">{t("Loading")}</p>}
      {data?.items.map((row) => (
        <article key={row.id} className="space-y-2 border-b border-border-default pb-2">
          <Snapshot row={row} />
          <time dateTime={row.created_at}>{formatDateTime(row.created_at)}</time>
          <p data-original>{row.reason}</p>
          <p className="break-all">
            {t("Actor")}: <span data-original>{row.actor_id || "—"}</span> · {t("Action")}:{" "}
            <span data-original>{row.action_id}</span>
          </p>
        </article>
      ))}
      <div className="flex gap-2">
        <button
          className="br-btn"
          disabled={!data || !offset}
          onClick={() => setOffset((x) => x - 50)}
        >
          {t("Previous")}
        </button>
        <button
          className="br-btn"
          disabled={!data || offset + 50 >= data.total}
          onClick={() => setOffset((x) => x + 50)}
        >
          {t("Next")}
        </button>
        <button className="br-btn" onClick={close}>
          {t("Close")}
        </button>
      </div>
    </section>
  );
}
