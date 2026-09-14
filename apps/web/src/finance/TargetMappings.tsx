import { SettingsEmptyState } from "./SettingsEmptyState";
import { SettingsToolbar } from "./SettingsToolbar";
import { SettingsDialog, ReviewNotice } from "./SettingsDialog";
import { useEffect, useState, type FormEvent } from "react";
import { t } from "../localization";

type Row = {
  id: string;
  name?: string;
  code?: string;
  namespace?: string;
  state?: string;
  revision?: number;
  [key: string]: unknown;
};
type Page = { items: Row[]; total: number; revision: number };
export async function targetCall<T>(url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...(body ? { method: "POST", body: JSON.stringify(body) } : {}),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || t("Request failed"));
  return result;
}
export function TargetPicker({
  label,
  url,
  value,
  onChange,
  optional = false,
  allowBlocked = false,
  locked = false,
}: {
  label: string;
  url: string;
  value: string;
  onChange: (id: string) => void;
  optional?: boolean;
  allowBlocked?: boolean;
  locked?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [loaded, setData] = useState<(Page & { requestKey: string }) | null>(null);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const requestKey = `${url}:${query}:${offset}:${reload}`;
  const data = loaded?.requestKey === requestKey ? loaded : null;
  useEffect(() => {
    let current = true;
    setData(null);
    setError("");
    targetCall<Page & { accounts?: Row[] }>(
      `${url}${url.includes("?") ? "&" : "?"}${new URLSearchParams({ query, offset: String(offset), limit: "50" })}`,
    )
      .then((result) => {
        if (current) {
          const items = result.accounts || result.items;
          setData(
            result.accounts
              ? {
                  ...result,
                  requestKey,
                  items: items
                    .filter((r) =>
                      `${r.code} ${r.name}`.toLowerCase().includes(query.toLowerCase()),
                    )
                    .slice(offset, offset + 50),
                  total: items.filter((r) =>
                    `${r.code} ${r.name}`.toLowerCase().includes(query.toLowerCase()),
                  ).length,
                }
              : { ...result, requestKey },
          );
        }
      })
      .catch((e) => {
        if (current) setError(e.message);
      });
    return () => {
      current = false;
    };
  }, [url, query, offset, reload]);
  return (
    <fieldset disabled={locked} className="min-w-0 space-y-1">
      <legend>
        {label}
        {optional && <span className="text-sm text-fg-muted"> · {t("Optional")}</span>}
      </legend>
      <input
        aria-label={`${t("Search")} · ${label}`}
        className="br-control w-full"
        placeholder={t("Search by code or name")}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOffset(0);
        }}
      />
      <select
        aria-label={label}
        required={!optional}
        className="br-control w-full"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">{t("Select")}</option>
        {value && !data?.items.some((r) => r.id === value) && (
          <option value={value}>{value}</option>
        )}
        {data?.items.map((r) => (
          <option key={r.id} value={r.id} disabled={!allowBlocked && r.state === "blocked"}>
            {r.code || r.namespace} · {r.name}
            {r.state === "blocked" ? ` · ${t("Blocked")}` : ""}
          </option>
        ))}
      </select>
      {error && (
        <p role="alert">
          {error}{" "}
          <button
            type="button"
            className="finance-row-button"
            onClick={() => setReload((x) => x + 1)}
          >
            {t("Retry")}
          </button>
        </p>
      )}
      {!data && !error && <p role="status">{t("Loading")}</p>}
      {data && data.total === 0 && <p>{t("No matching references")}</p>}
      {data && (offset > 0 || data.total > 50) && (
        <div className="flex gap-2">
          <button
            type="button"
            className="finance-row-button"
            disabled={!offset}
            onClick={() => setOffset((x) => Math.max(0, x - 50))}
          >
            {t("Previous")}
          </button>
          <button
            type="button"
            className="finance-row-button"
            disabled={offset + 50 >= data.total}
            onClick={() => setOffset((x) => x + 50)}
          >
            {t("Next")}
          </button>
        </div>
      )}
    </fieldset>
  );
}
const tabStyles = { active: "bg-accent-soft text-accent", inactive: "" };
const operations = {
  sales_invoice: "Sales invoice",
  supplier_invoice: "Supplier invoice",
  credit_note: "Customer credit note",
  supplier_credit_note: "Supplier credit note",
};
function Snapshot({ value }: { value: Row | null }) {
  if (!value) return <p>{t("No previous mapping")}</p>;
  const snapshot = value.configuration_snapshot as Record<string, Row | null> | undefined;
  return (
    <div className="space-y-1 break-words">
      <p data-original>{[value.namespace || value.code, value.name].filter(Boolean).join(" · ")}</p>
      {!!value.mapping_kind && (
        <p>
          {t(value.mapping_kind === "local_account" ? "Operational account" : "Received component")}{" "}
          ·{" "}
          {t(
            operations[value.transaction_kind as keyof typeof operations] || "Operational account",
          )}
        </p>
      )}
      {snapshot &&
        Object.entries({
          target: "Accounting target",
          local_account: "Operational account",
          case: "Case code",
          group: "Coding group",
          external_account: "External account",
          external_tax_code: "Tax code",
        }).map(
          ([key, label]) =>
            snapshot[key] && (
              <p key={key}>
                {t(label)}:{" "}
                <span data-original>
                  {snapshot[key]?.code || snapshot[key]?.namespace} · {snapshot[key]?.name}
                </span>
              </p>
            ),
        )}
      {!!value.group_mode && (
        <p>
          {t(value.group_mode === "exact" ? "Exact coding group" : "Without group discrimination")}
        </p>
      )}
      <p>
        {t(value.state === "blocked" ? "Blocked" : "Active")} · {t("Revision")} {value.revision}
      </p>
    </div>
  );
}
type Pending = {
  id: string;
  preview: { target_configuration: { before: Row | null; after: Row; reason: string } };
};
export function TargetMappings({ tenantId, canManage }: { tenantId: string; canManage: boolean }) {
  const targetStorage = `finance-account-target:${tenantId}`;
  const [target, changeTarget] = useState(() => sessionStorage.getItem(targetStorage) || "");
  const [targetLabel, setTargetLabel] = useState(
    () => sessionStorage.getItem(`${targetStorage}:label`) || "",
  );
  const setTarget = (value: string, label = "") => {
    sessionStorage.setItem(`${targetStorage}:label`, label);
    setTargetLabel(label);
    sessionStorage.setItem(targetStorage, value);
    changeTarget(value);
  };
  return (
    <section
      aria-label={t("External accounting")}
      className="space-y-4 rounded-xl border border-border-default bg-surface p-5"
    >
      <h2 className="text-lg font-semibold">{t("External accounting")}</h2>
      <p className="text-sm text-fg-muted">
        {t(
          "Set up the accounts and tax codes used by your external bookkeeping software, then define how Reality assigns them.",
        )}
      </p>
      {target && (
        <p className="font-medium">
          <span>{t("Accounting target")}: </span>
          <span data-original>{targetLabel || t("Selected accounting target")}</span>
        </p>
      )}
      <TargetBody
        key={`${tenantId}:${target}`}
        tenantId={tenantId}
        target={target}
        canManage={canManage}
        openTarget={(row) => setTarget(row.id, `${row.namespace} · ${row.name}`)}
        back={() => setTarget("")}
      />
    </section>
  );
}
function TargetBody({
  tenantId,
  target,
  canManage,
  openTarget,
  back,
}: {
  tenantId: string;
  target: string;
  canManage: boolean;
  openTarget: (row: Row) => void;
  back: () => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenantId)}`;
  const tabStorage = `finance-account-tab:${tenantId}:${target}`;
  const [tab, changeTab] = useState(() => {
    const saved = sessionStorage.getItem(tabStorage);
    return target && saved && ["rules", "account", "tax_code"].includes(saved)
      ? saved
      : target
        ? "account"
        : "targets";
  });
  const setTab = (value: string) => {
    sessionStorage.setItem(tabStorage, value);
    changeTab(value);
  };
  const [loaded, setData] = useState<(Page & { requestKey: string }) | null>(null);
  const [offset, setOffset] = useState(0);
  const [query, setQuery] = useState("");
  const [reload, setReload] = useState(0);
  const [catalogPresence, setCatalogPresence] = useState<Record<string, boolean>>({});
  const requestKey = `${target}:${tab}:${query}:${offset}:${reload}`;
  const data = loaded?.requestKey === requestKey ? loaded : null;
  const [editing, setEditing] = useState<Row | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<{
    id: string;
    offset: number;
    total: number;
    items: Row[];
  } | null>(null);
  const storage = `finance-target-review:${tenantId}:${target}`;
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
  }, [storage, pending]);
  useEffect(() => {
    let current = true;
    setData(null);
    setError("");
    const path =
      tab === "targets" ? "targets" : tab === "rules" ? "target-mappings" : "target-references";
    targetCall<Page>(
      `${base}/finance/${path}?${new URLSearchParams({ ...(tab === "targets" ? {} : { target_id: target }), ...(tab === "account" || tab === "tax_code" ? { kind: tab } : {}), query, offset: String(offset), limit: "50" })}`,
    )
      .then((r) => {
        if (current) {
          setData({ ...r, requestKey });
          if (!query && offset === 0)
            setCatalogPresence((previous) => ({ ...previous, [tab]: r.total > 0 }));
        }
      })
      .catch((e) => {
        if (current) setError(e.message);
      });
    return () => {
      current = false;
    };
  }, [base, target, tab, query, offset, reload]);
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
  async function propose(values: Record<string, unknown>) {
    if (!data) return;
    const tool =
      tab === "rules"
        ? "finance.target_mapping.set"
        : tab === "targets"
          ? `finance.target.${editing ? "update" : "create"}`
          : `finance.target_reference.${editing ? "update" : "create"}`;
    await run(async () => {
      const result = await targetCall<Pending>(`${base}/finance/targets/proposals`, {
        tool,
        arguments: { ...values, expected_revision: data.revision },
      });
      sessionStorage.setItem(storage, JSON.stringify(result));
      setPending(result);
    });
  }
  async function decide(approve: boolean) {
    if (!pending) return;
    await run(async () => {
      await targetCall(
        `${base}/change-proposals/${pending.id}/${approve ? "approve" : "reject"}`,
        {},
      );
      sessionStorage.removeItem(storage);
      setPending(null);
      setEditorOpen(false);
      setEditing(null);
      setReload((x) => x + 1);
    });
  }
  async function showHistory(id: string, next = 0) {
    await run(async () => {
      setHistory({
        ...(await targetCall<{ total: number; items: Row[] }>(
          `${base}/finance/target-mappings/${encodeURIComponent(id)}/history?limit=50&offset=${next}`,
        )),
        id,
        offset: next,
      });
    });
  }
  const createTitle =
    tab === "targets"
      ? "Create accounting target"
      : tab === "account"
        ? "Create external account"
        : tab === "tax_code"
          ? "Create tax code"
          : "Create mapping rule";
  const editTitle =
    tab === "targets"
      ? "Edit accounting target"
      : tab === "account"
        ? "Edit external account"
        : tab === "tax_code"
          ? "Edit tax code"
          : "Edit mapping rule";
  return (
    <div className="space-y-4">
      {target && (
        <button className="br-btn" disabled={busy || !!pending} onClick={back}>
          {t("Back to accounting targets")}
        </button>
      )}
      {target && (
        <nav aria-label={t("External accounting areas")} className="flex flex-wrap gap-2">
          {Object.entries({
            account: "External accounts",
            tax_code: "Tax codes",
            rules: "Rules",
          }).map(([key, label]) => (
            <button
              key={key}
              className={`br-btn ${tab === key ? tabStyles.active : tabStyles.inactive}`}
              aria-current={tab === key ? "page" : undefined}
              disabled={busy || !!pending || (!target && key !== "targets")}
              onClick={() => {
                setTab(key);
                setEditing(null);
                setOffset(0);
                setQuery("");
                setHistory(null);
              }}
            >
              {t(label)}
            </button>
          ))}
        </nav>
      )}
      {error && !editorOpen && (
        <p role="alert">
          {error}{" "}
          <button className="br-btn" onClick={() => setReload((x) => x + 1)}>
            {t("Retry")}
          </button>
        </p>
      )}
      <SettingsToolbar>
        <h3 className="font-semibold">
          {t(
            tab === "targets"
              ? "Accounting targets"
              : tab === "account"
                ? "External accounts"
                : tab === "tax_code"
                  ? "Tax codes"
                  : "Rules",
          )}
        </h3>
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
            {t(createTitle)}
          </button>
        )}
      </SettingsToolbar>
      <p className="text-sm text-fg-muted">
        {t(
          tab === "targets"
            ? "Add your external bookkeeping system here. Open its account setup to maintain accounts, tax codes and assignment rules."
            : tab === "account"
              ? "Add the account numbers used in this bookkeeping system. Rules can then assign transactions to these accounts."
              : tab === "tax_code"
                ? "Add the tax codes used in this bookkeeping system. You can select them when defining assignment rules."
                : "Define which external account and tax code a transaction should use. Add the required accounts and tax codes first.",
        )}
      </p>
      {pending && !editorOpen && <ReviewNotice open={() => setEditorOpen(true)} />}
      {pending ? (
        <>
          {editorOpen && (
            <SettingsDialog
              title={t("Review configuration")}
              description={t(
                "Check the proposed values. The change takes effect only after confirmation.",
              )}
              busy={busy}
              error={error}
              close={() => setEditorOpen(false)}
            >
              <section aria-label={t("Review configuration")} className="space-y-5">
                <p>{t("Before")}</p>
                <Snapshot value={pending.preview.target_configuration.before} />
                <p>{t("After")}</p>
                <Snapshot value={pending.preview.target_configuration.after} />
                <p data-original>{pending.preview.target_configuration.reason}</p>
                <div className="finance-form-actions">
                  <button
                    className="br-btn br-btn-primary"
                    disabled={!canManage || busy}
                    onClick={() => decide(true)}
                  >
                    {t("Confirm")}
                  </button>
                  <button
                    className="br-btn"
                    disabled={!canManage || busy}
                    onClick={() => decide(false)}
                  >
                    {t("Cancel")}
                  </button>
                </div>
              </section>
            </SettingsDialog>
          )}
        </>
      ) : (
        <>
          {(query || offset > 0 || catalogPresence[tab]) && (
            <label className="grid w-full gap-1 text-sm sm:max-w-md">
              {t("Search")}
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
              {data.items.length === 0 && (
                <SettingsEmptyState
                  message={
                    tab === "targets"
                      ? "No accounting targets yet."
                      : tab === "account"
                        ? "No external accounts yet."
                        : tab === "tax_code"
                          ? "No tax codes yet."
                          : "No assignment rules yet."
                  }
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
              {data.items.map((row) => (
                <article
                  key={row.id}
                  className="space-y-2 rounded-lg border border-border-default p-3"
                >
                  <Snapshot value={row} />
                  <div className="flex gap-2">
                    {tab === "targets" && (
                      <button className="finance-row-button" onClick={() => openTarget(row)}>
                        {t("Open account setup")}
                      </button>
                    )}
                    {canManage && (
                      <button
                        className="finance-row-button"
                        disabled={busy}
                        onClick={() => {
                          setEditing(row);
                          setEditorOpen(true);
                          setError("");
                        }}
                      >
                        {t("Edit")}
                      </button>
                    )}
                    {tab === "rules" && (
                      <button className="finance-row-button" onClick={() => showHistory(row.id)}>
                        {t("History")}
                      </button>
                    )}
                  </div>
                </article>
              ))}
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
              {canManage && editorOpen && (
                <SettingsDialog
                  title={t(editing ? editTitle : createTitle)}
                  description={t(
                    tab === "rules"
                      ? "Choose when this rule applies and which external account it selects. All conditions must match exactly."
                      : "Enter the code and name used by your external accounting software.",
                  )}
                  busy={busy}
                  error={error}
                  close={() => setEditorOpen(false)}
                >
                  <ConfigurationForm
                    key={`${tab}:${editing?.id || "new"}`}
                    base={base}
                    target={target}
                    tab={tab}
                    editing={editing}
                    disabled={busy}
                    propose={propose}
                    cancel={() => setEditorOpen(false)}
                  />
                </SettingsDialog>
              )}
            </>
          )}
        </>
      )}
      {history && (
        <SettingsDialog
          title={t("Mapping history")}
          busy={busy}
          error={error}
          close={() => setHistory(null)}
        >
          <section
            aria-label={t("Mapping history")}
            className="space-y-3 border-t border-border-default pt-3"
          >
            {history.items.map((row) => (
              <article key={row.id}>
                <Snapshot value={row} />
                <p data-original>
                  {String(row.reason)} · {String(row.actor_id || "")} · {String(row.created_at)}
                </p>
              </article>
            ))}
            <div className="flex gap-2">
              <button
                className="br-btn"
                disabled={!history.offset || busy}
                onClick={() => showHistory(history.id, history.offset - 50)}
              >
                {t("Previous")}
              </button>
              <button
                className="br-btn"
                disabled={history.offset + 50 >= history.total || busy}
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
function ConfigurationForm({
  base,
  target,
  tab,
  editing,
  disabled,
  propose,
  cancel,
}: {
  base: string;
  target: string;
  tab: string;
  editing: Row | null;
  disabled: boolean;
  propose: (values: Record<string, unknown>) => Promise<void>;
  cancel: () => void;
}) {
  const [scope, setScope] = useState(String(editing?.mapping_kind || "case_routing"));
  const [mode, setMode] = useState(String(editing?.group_mode || "none"));
  const [ids, setIds] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      [
        "local_account_id",
        "case_reference_id",
        "group_reference_id",
        "external_account_id",
        "external_tax_code_id",
      ].map((k) => [k, String(editing?.[k] || "")]),
    ),
  );
  const pick = (key: string, label: string, path: string, optional = false) => (
    <TargetPicker
      label={t(label)}
      url={`${base}/finance/${path}`}
      value={ids[key]}
      onChange={(id) => setIds((v) => ({ ...v, [key]: id }))}
      optional={optional}
      locked={
        !!editing && ["case_reference_id", "group_reference_id", "local_account_id"].includes(key)
      }
    />
  );
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    let values: Record<string, unknown> = { reason: String(form.get("reason")) };
    if (tab === "rules")
      values = {
        ...values,
        target_id: target,
        mapping_kind: scope,
        local_account_id: scope === "local_account" ? ids.local_account_id : null,
        transaction_kind:
          scope === "case_routing"
            ? String(editing?.transaction_kind || form.get("transaction"))
            : null,
        case_reference_id: scope === "case_routing" ? ids.case_reference_id : null,
        group_mode: scope === "case_routing" ? mode : null,
        group_reference_id:
          scope === "case_routing" && mode === "exact" ? ids.group_reference_id : null,
        external_account_id: ids.external_account_id,
        external_tax_code_id: scope === "case_routing" ? ids.external_tax_code_id || null : null,
        state: String(form.get("state")),
      };
    else {
      values.name = String(form.get("name"));
      if (editing) {
        values[tab === "targets" ? "target_id" : "reference_id"] = editing.id;
        values.state = String(form.get("state"));
      } else if (tab === "targets") values.namespace = String(form.get("code"));
      else Object.assign(values, { target_id: target, kind: tab, code: String(form.get("code")) });
    }
    await propose(values);
  }
  return (
    <form onSubmit={submit} className="space-y-5">
      <p className="text-sm text-fg-muted sm:col-span-2">
        {t("All fields are required unless marked optional.")}
      </p>
      <fieldset disabled={disabled} className="grid min-w-0 gap-3 sm:grid-cols-2">
        {tab === "rules" ? (
          <>
            <label>
              {t("Mapping scope")}
              <select
                name="scope"
                disabled={!!editing}
                className="br-control w-full"
                value={scope}
                onChange={(e) => setScope(e.target.value)}
              >
                <option value="case_routing">{t("Received component")}</option>
                <option value="local_account">{t("Operational account")}</option>
              </select>
            </label>
            {scope === "case_routing" ? (
              <>
                <label>
                  {t("Transaction")}
                  <select
                    name="transaction"
                    disabled={!!editing}
                    className="br-control w-full"
                    defaultValue={String(editing?.transaction_kind || "sales_invoice")}
                  >
                    {Object.entries(operations).map(([key, label]) => (
                      <option key={key} value={key}>
                        {t(label)}
                      </option>
                    ))}
                  </select>
                </label>
                {pick("case_reference_id", "Case code", "references?kind=case_code")}
                <label>
                  {t("Coding group condition")}
                  <select
                    className="br-control w-full"
                    disabled={!!editing}
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                  >
                    <option value="none">{t("No coding group condition")}</option>
                    <option value="exact">{t("Exact coding group")}</option>
                  </select>
                </label>
                {mode === "exact" &&
                  pick("group_reference_id", "Coding group", "references?kind=coding_group")}
              </>
            ) : (
              pick("local_account_id", "Operational account", "accounts")
            )}
            {pick(
              "external_account_id",
              "External account",
              `target-references?target_id=${encodeURIComponent(target)}&kind=account`,
            )}
            {scope === "case_routing" &&
              pick(
                "external_tax_code_id",
                "Tax code",
                `target-references?target_id=${encodeURIComponent(target)}&kind=tax_code`,
                true,
              )}
          </>
        ) : (
          <>
            <label>
              {t(tab === "targets" ? "Target identifier" : "Code")}
              <input
                name="code"
                required
                maxLength={200}
                className="br-control w-full"
                defaultValue={editing?.code || editing?.namespace || ""}
                disabled={!!editing}
              />
            </label>
            <label>
              {t("Name")}
              <input
                name="name"
                required
                maxLength={200}
                defaultValue={editing?.name || ""}
                className="br-control w-full"
              />
            </label>
          </>
        )}
        {(editing || tab === "rules") && (
          <label>
            {t("Status")}
            <select
              name="state"
              className="br-control w-full"
              defaultValue={editing?.state || "active"}
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
          <input name="reason" required maxLength={4000} className="br-control w-full" />
        </label>
        <div className="finance-form-actions sm:col-span-2">
          <button className="br-btn br-btn-primary" type="submit">
            {t("Review configuration")}
          </button>
          {
            <button type="button" className="br-btn" onClick={cancel}>
              {t("Cancel")}
            </button>
          }
        </div>
      </fieldset>
    </form>
  );
}
