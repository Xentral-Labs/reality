import { SettingsEmptyState } from "./SettingsEmptyState";
import { SettingsToolbar } from "./SettingsToolbar";
import { SettingsDialog, ReviewNotice } from "./SettingsDialog";
import { useEffect, useState, type FormEvent } from "react";
import { t } from "../localization";

const headingStyles = {
  embedded: "text-lg font-semibold",
  standalone: "cursor-pointer font-semibold",
};

type Reference = {
  id?: string;
  kind: string;
  code: string;
  name: string;
  state: string;
  revision: number;
};
type Page = { revision: number; total: number; items: Reference[] };
type Change = { before: Reference | null; after: Reference; reason: string };
type History = {
  reference: Reference;
  total: number;
  items: (Change & {
    event_id: string;
    action_id: string;
    actor_id: string | null;
    occurred_at: string;
  })[];
};
type Pending = { id: string; preview: { reference: Change } };
const kinds = {
  cost_center: "Cost centers",
  case_code: "Case codes",
  coding_group: "Coding groups",
};
async function call<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    ...(body ? { method: "POST" } : { method: "GET" }),
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || t("Request failed"));
  return result;
}
function snapshot(row: Reference | null) {
  return row
    ? `${t(kinds[row.kind as keyof typeof kinds])} · ${row.code} · ${row.name} · ${t(row.state === "active" ? "Active" : "Blocked")} · ${t("Revision")} ${row.revision}`
    : t("New reference");
}
export function ReferenceSettings({
  tenantId,
  embedded = false,
  referenceArea,
  canManage,
}: {
  tenantId: string;
  embedded?: boolean;
  referenceArea?: "cost-centers" | "classifications";
  canManage: boolean;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenantId)}`;
  const storage = `finance-reference-proposal:${tenantId}${referenceArea ? `:${referenceArea}` : ""}`;
  const [kind, setKind] = useState(
    referenceArea === "classifications" ? "case_code" : "cost_center",
  );
  const [query, setQuery] = useState("");
  const [state, setState] = useState("");
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const [data, setData] = useState<Page | null>(null);
  const [hasEntries, setHasEntries] = useState(false);
  const [editing, setEditing] = useState<Reference | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [history, setHistory] = useState<History | null>(null);
  const [historyOffset, setHistoryOffset] = useState(0);
  const [pending, setPending] = useState<Pending | null>(() => {
    try {
      const own = sessionStorage.getItem(storage);
      if (own) return JSON.parse(own);
      const legacy = JSON.parse(
        sessionStorage.getItem(`finance-reference-proposal:${tenantId}`) || "null",
      ) as Pending | null;
      const legacyKind = legacy?.preview.reference.after.kind;
      return legacy &&
        (!referenceArea ||
          (referenceArea === "cost-centers"
            ? legacyKind === "cost_center"
            : ["case_code", "coding_group"].includes(legacyKind || "")))
        ? legacy
        : null;
    } catch {
      return null;
    }
  });
  useEffect(() => {
    if (pending) setEditorOpen(true);
  }, [pending]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<Reference | null>(null);
  useEffect(() => {
    if (pending) {
      sessionStorage.setItem(storage, JSON.stringify(pending));
      const legacyKey = `finance-reference-proposal:${tenantId}`;
      if (referenceArea && sessionStorage.getItem(legacyKey) === JSON.stringify(pending))
        sessionStorage.removeItem(legacyKey);
    } else sessionStorage.removeItem(storage);
  }, [pending, storage, tenantId, referenceArea]);
  useEffect(() => {
    let active = true;
    setData(null);
    const parameters = new URLSearchParams({
      kind,
      query,
      limit: "50",
      offset: String(offset),
      ...(state ? { state } : {}),
    });
    call<Page>(`${base}/finance/references?${parameters}`)
      .then((value) => {
        if (active) {
          setData(value);
          if (!query && !state && offset === 0) setHasEntries(value.total > 0);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [base, kind, query, state, offset, reload]);
  async function showHistory(row: Reference, next = 0) {
    setError("");
    setBusy(true);
    try {
      setHistory(
        await call<History>(`${base}/finance/references/${row.id}/history?offset=${next}&limit=50`),
      );
      setHistoryOffset(next);
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
    setBusy(true);
    setError("");
    setReceipt(null);
    try {
      const result = await call<Pending>(`${base}/finance/references/proposals`, {
        tool: editing ? "finance.reference.update" : "finance.reference.create",
        arguments: {
          expected_revision: data.revision,
          name: String(form.get("name")),
          reason: String(form.get("reason")),
          ...(editing
            ? { reference_id: editing.id, state: String(form.get("state")) }
            : { kind, code: String(form.get("code")) }),
        },
      });
      setPending(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  async function decide(approve: boolean) {
    if (!pending) return;
    setBusy(true);
    setError("");
    try {
      const result = await call<{ output: Reference }>(
        `${base}/change-proposals/${pending.id}/${approve ? "approve" : "reject"}`,
        {},
      );
      setPending(null);
      setEditorOpen(false);
      setEditing(null);
      setHistory(null);
      setReload((v) => v + 1);
      if (approve) setReceipt(result.output);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  const createTitle =
    kind === "cost_center"
      ? "Create cost center"
      : kind === "case_code"
        ? "Create case code"
        : "Create coding group";
  const editTitle =
    kind === "cost_center"
      ? "Edit cost center"
      : kind === "case_code"
        ? "Edit case code"
        : "Edit coding group";
  const Container = embedded ? "section" : "details";
  const Heading = embedded ? "h2" : "summary";
  return (
    <Container
      aria-label={
        embedded
          ? t(
              referenceArea === "cost-centers"
                ? "Cost centers"
                : referenceArea === "classifications"
                  ? "Case codes & coding groups"
                  : "Finance references",
            )
          : undefined
      }
      className="min-w-0 space-y-4 rounded-xl border border-border-default bg-surface p-5"
    >
      <Heading className={embedded ? headingStyles.embedded : headingStyles.standalone}>
        {t(
          embedded
            ? referenceArea === "cost-centers"
              ? "Cost centers"
              : referenceArea === "classifications"
                ? "Case codes & coding groups"
                : "Finance references"
            : "Finance references",
        )}
      </Heading>
      <p className="text-sm text-fg-muted">
        {t(
          referenceArea === "cost-centers"
            ? "Define cost centers for internal cost allocation."
            : referenceArea === "classifications"
              ? "Define case codes and coding groups for internal classification."
              : "Define cost centers, case codes and coding groups for internal classification.",
        )}
      </p>
      <p className="text-sm text-fg-muted">
        {t("Codes are permanent. Block unused references to preserve their history.")}
      </p>
      {error && !editorOpen && (
        <div role="alert">
          <p>{error}</p>
          <button
            className="br-btn"
            onClick={() => {
              setError("");
              setReload((v) => v + 1);
            }}
          >
            {t("Retry")}
          </button>
        </div>
      )}
      <SettingsToolbar>
        {referenceArea !== "cost-centers" && (
          <label className="grid w-full gap-1 text-sm sm:w-56">
            {t("Reference type")}
            <select
              className="br-control"
              aria-label={t("Reference type")}
              value={kind}
              disabled={busy || !!pending}
              onChange={(e) => {
                setKind(e.target.value);
                setQuery("");
                setState("");
                setHasEntries(false);
                setOffset(0);
                setEditing(null);
                setHistory(null);
              }}
            >
              {Object.entries(kinds)
                .filter(([key]) => !referenceArea || key !== "cost_center")
                .map(([key, label]) => (
                  <option key={key} value={key}>
                    {t(label)}
                  </option>
                ))}
            </select>
          </label>
        )}
        {canManage && (
          <button
            className="br-btn br-btn-primary"
            disabled={!data || busy || !!pending}
            onClick={() => {
              setEditing(null);
              setReceipt(null);
              setError("");
              setEditorOpen(true);
            }}
          >
            {t(createTitle)}
          </button>
        )}
      </SettingsToolbar>
      {(hasEntries || query || state) && (
        <div className="flex flex-wrap items-end gap-3">
          <label className="grid w-full gap-1 text-sm sm:max-w-md">
            {t("Search references")}
            <input
              className="br-control"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <label className="grid w-full gap-1 text-sm sm:w-40">
            {t("Status")}
            <select
              className="br-control"
              aria-label={t("Reference status filter")}
              value={state}
              onChange={(e) => {
                setState(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">{t("All")}</option>
              <option value="active">{t("Active")}</option>
              <option value="blocked">{t("Blocked")}</option>
            </select>
          </label>
        </div>
      )}
      {!data && !error && <p role="status">{t("Loading")}</p>}
      {data && (
        <>
          {data.total === 0 ? (
            <SettingsEmptyState
              reset={
                query || state || offset > 0
                  ? () => {
                      setQuery("");
                      setState("");
                      setOffset(0);
                    }
                  : undefined
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[36rem] text-left text-sm">
                <thead>
                  <tr>
                    {["Code", "Name", "Status", "Actions"].map((label) => (
                      <th className="border-b border-border-default p-2" key={label}>
                        {t(label)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((row) => (
                    <tr key={row.id}>
                      <td className="border-b border-border-default p-2">{row.code}</td>
                      <td className="border-b border-border-default p-2">{row.name}</td>
                      <td className="border-b border-border-default p-2">
                        {t(row.state === "active" ? "Active" : "Blocked")}
                      </td>
                      <td className="border-b border-border-default p-2">
                        <button
                          className="finance-row-button"
                          disabled={busy}
                          onClick={() => void showHistory(row)}
                        >
                          {t("History")}
                        </button>
                        {canManage && (
                          <button
                            className="finance-row-button"
                            disabled={busy || !!pending}
                            onClick={() => {
                              setEditing(row);
                              setEditorOpen(true);
                              setError("");
                              setReceipt(null);
                            }}
                          >
                            {t("Edit")}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {(offset > 0 || data.total > 50) && (
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span>
                {t("References")}: {data.total}
              </span>
              <button
                className="br-btn"
                disabled={offset === 0}
                onClick={() => setOffset((v) => Math.max(0, v - 50))}
              >
                {t("Previous")}
              </button>
              <button
                className="br-btn"
                disabled={offset + 50 >= data.total}
                onClick={() => setOffset((v) => v + 50)}
              >
                {t("Next")}
              </button>
            </div>
          )}
          {canManage && editorOpen && !pending && (
            <SettingsDialog
              title={t(editing ? editTitle : createTitle)}
              description={t(
                kind === "cost_center"
                  ? "Identify the department, location or project receiving the cost, for example SALES or BERLIN. Codes remain permanent."
                  : kind === "case_code"
                    ? "Define a business case such as domestic sales or export. A case code is a declared classification, not an automatic tax calculation."
                    : "Group products or services that need the same account mapping. A rule can require an exact coding group.",
              )}
              busy={busy}
              error={error}
              close={() => setEditorOpen(false)}
            >
              <form
                key={`${kind}:${editing?.id || "new"}:${reload}`}
                className="grid gap-3 sm:grid-cols-2"
                onSubmit={(e) => void propose(e)}
              >
                <p className="text-sm text-fg-muted sm:col-span-2">
                  {t("All fields are required unless marked optional.")}
                </p>
                <label>
                  {t("Code")}
                  <input
                    className="br-control w-full"
                    name="code"
                    maxLength={100}
                    required
                    defaultValue={editing?.code || ""}
                    disabled={busy || !!editing}
                  />
                </label>
                <label>
                  {t("Name")}
                  <input
                    className="br-control w-full"
                    name="name"
                    maxLength={200}
                    required
                    defaultValue={editing?.name || ""}
                    disabled={busy}
                  />
                </label>
                {editing && (
                  <label>
                    {t("Status")}
                    <select
                      className="br-control w-full"
                      aria-label={t("Reference status")}
                      name="state"
                      defaultValue={editing.state}
                      disabled={busy}
                    >
                      <option value="active">{t("Active")}</option>
                      <option value="blocked">{t("Blocked")}</option>
                    </select>
                  </label>
                )}
                <p className="text-sm text-fg-muted sm:col-span-2">
                  {t(
                    "Explain why you are adding or changing this entry. This note is retained in its history.",
                  )}
                </p>
                <label>
                  {t("Reason")}
                  <input
                    className="br-control w-full"
                    name="reason"
                    required
                    maxLength={4000}
                    disabled={busy}
                  />
                </label>
                <div className="finance-form-actions sm:col-span-2">
                  <button className="br-btn br-btn-primary" disabled={busy}>
                    {t(
                      referenceArea === "cost-centers"
                        ? "Review cost center"
                        : "Review reference change",
                    )}
                  </button>
                  {
                    <button
                      className="br-btn"
                      type="button"
                      disabled={busy}
                      onClick={() => setEditorOpen(false)}
                    >
                      {t("Cancel")}
                    </button>
                  }
                </div>
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
              title={t("Confirm reference change")}
              description={t(
                "Check the proposed values. The change takes effect only after confirmation.",
              )}
              busy={busy}
              error={error}
              close={() => setEditorOpen(false)}
            >
              <section className="space-y-3" aria-label={t("Confirm reference change")}>
                <p>
                  {t("Before")}: {snapshot(pending.preview.reference.before)}
                </p>
                <p>
                  {t("After")}: {snapshot(pending.preview.reference.after)}
                </p>
                <p>
                  {t("Reason")}: {pending.preview.reference.reason}
                </p>
                <div className="finance-form-actions">
                  <button
                    className="br-btn br-btn-primary"
                    disabled={busy || !canManage}
                    onClick={() => void decide(true)}
                  >
                    {t("Confirm")}
                  </button>
                  <button
                    className="br-btn"
                    disabled={busy || !canManage}
                    onClick={() => void decide(false)}
                  >
                    {t("Cancel")}
                  </button>
                </div>
              </section>
            </SettingsDialog>
          )}
        </>
      )}
      {receipt && (
        <p role="status">
          {t("Reference saved")}: {snapshot(receipt)}
        </p>
      )}
      {history && (
        <SettingsDialog
          title={t("Reference history")}
          busy={busy}
          error={error}
          close={() => setHistory(null)}
        >
          <section className="space-y-3" aria-label={t("Reference history")}>
            <h3 className="font-semibold">{history.reference.code}</h3>
            {history.items.map((row) => (
              <article
                className="space-y-1 border-b border-border-default py-3 text-sm"
                key={row.event_id}
              >
                <p>{row.occurred_at}</p>
                <p>
                  {t("Before")}: {snapshot(row.before)}
                </p>
                <p>
                  {t("After")}: {snapshot(row.after)}
                </p>
                <p>
                  {t("Reason")}: {row.reason}
                </p>
                <p className="break-all">
                  {t("Action")}: {row.action_id} · {t("Actor")}: {row.actor_id || t("Unknown")}
                </p>
              </article>
            ))}
            <button
              className="br-btn"
              disabled={busy || historyOffset === 0}
              onClick={() => void showHistory(history.reference, Math.max(0, historyOffset - 50))}
            >
              {t("Previous")}
            </button>
            <button
              className="br-btn"
              disabled={busy || historyOffset + 50 >= history.total}
              onClick={() => void showHistory(history.reference, historyOffset + 50)}
            >
              {t("Next")}
            </button>
            <button className="br-btn" onClick={() => setHistory(null)}>
              {t("Close")}
            </button>
          </section>
        </SettingsDialog>
      )}
    </Container>
  );
}
