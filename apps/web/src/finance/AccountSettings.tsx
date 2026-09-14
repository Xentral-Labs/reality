import { SettingsEmptyState } from "./SettingsEmptyState";
import { SettingsToolbar } from "./SettingsToolbar";
import { SettingsDialog, ReviewNotice } from "./SettingsDialog";
import { RowActions } from "./RowActions";
import { TransactionMatrix } from "./TransactionMatrix";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { t } from "../localization";

const headingStyles = {
  embedded: "text-lg font-semibold",
  standalone: "cursor-pointer font-semibold",
};

type Account = {
  id: string;
  code: string;
  name: string;
  role: string;
  state: string;
  revision: number;
};
type Accounts = {
  revision: number;
  accounts: Account[];
  roles: Record<string, string>;
  defaults: Record<string, string>;
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
export function AccountSettings({
  tenantId,
  embedded = false,
  canManage = true,
}: {
  tenantId: string;
  embedded?: boolean;
  canManage?: boolean;
}) {
  const controls = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<Accounts | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<Account | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const storage = `finance-account-review:${tenantId}`;
  const [defaultRole, setDefaultRole] = useState<string | null>(null);
  const [defaultAccount, setDefaultAccount] = useState("");
  const [pending, setPending] = useState<{ id: string; description: string } | null>(() => {
    try {
      return JSON.parse(sessionStorage.getItem(storage) || "null");
    } catch {
      return null;
    }
  });
  useEffect(() => {
    if (pending) sessionStorage.setItem(storage, JSON.stringify(pending));
    else sessionStorage.removeItem(storage);
  }, [storage, pending]);
  useEffect(() => {
    if (pending) {
      setDefaultRole(null);
      setEditorOpen(true);
    }
  }, [pending]);
  const base = `/api/tenants/${encodeURIComponent(tenantId)}`;
  async function load() {
    setData(await call<Accounts>(`${base}/finance/accounts`));
  }
  useEffect(() => {
    let active = true;
    setData(null);
    setError("");
    call<Accounts>(`${base}/finance/accounts`)
      .then((v) => {
        if (active) setData(v);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [base]);
  async function propose(tool: string, args: Record<string, unknown>, description: string) {
    if (!data) return;
    setBusy(true);
    setError("");
    try {
      const result = await call<{ id: string }>(`${base}/finance/accounts/proposals`, {
        tool,
        arguments: { ...args, expected_revision: data.revision },
      });
      setPending({ id: result.id, description });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  async function confirm() {
    if (!pending) return;
    setBusy(true);
    setError("");
    try {
      await call(`${base}/change-proposals/${pending.id}/approve`, {});
      setPending(null);
      setEditorOpen(false);
      setEditing(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const code = String(form.get("code"));
    const name = String(form.get("name"));
    const role = String(form.get("role"));
    void propose(
      editing ? "finance.account.update" : "finance.account.create",
      editing ? { account_id: editing.id, code, name } : { code, name, role },
      `${code} · ${name} · ${t(data?.roles[editing?.role || role] || role)}`,
    );
  }
  const Container = embedded ? "section" : "details";
  const Heading = embedded ? "h2" : "summary";
  return (
    <Container
      aria-label={embedded ? t("Accounts & account mapping") : undefined}
      className="min-w-0 space-y-4 rounded-xl border border-border-default bg-surface p-5"
    >
      <Heading className={embedded ? headingStyles.embedded : headingStyles.standalone}>
        {t("Operational accounts")}
      </Heading>
      <p className="text-sm text-fg-muted">
        {t(
          "Choose the accounts Reality uses for receivables, payables, payments and settlement differences.",
        )}
      </p>
      <p className="text-sm text-fg-muted">
        {t(
          "Default means Reality selects this account automatically for its role. External ledger numbers are managed under External accounting.",
        )}
      </p>
      {error && !editorOpen && !defaultRole && <p role="alert">{error}</p>}
      {!data && !error && <p role="status">{t("Loading")}</p>}
      {error && !editorOpen && !defaultRole && (
        <button
          className="br-btn"
          type="button"
          onClick={() => {
            setError("");
            void load().catch((e) => setError(e.message));
          }}
        >
          {t("Retry")}
        </button>
      )}
      {data && (
        <>
          <SettingsToolbar>
            <TransactionMatrix
              tenantId={tenantId}
              revision={data.revision}
              canManage={canManage && !busy && !pending}
              configure={(role) => {
                if (role) {
                  setDefaultRole(role);
                  setDefaultAccount(data.defaults[role] || "");
                  setError("");
                } else controls.current?.scrollIntoView({ block: "start", behavior: "smooth" });
              }}
            />
            {canManage && (
              <button
                className="br-btn br-btn-primary"
                disabled={busy || !!pending}
                onClick={() => {
                  setEditing(null);
                  setError("");
                  setEditorOpen(true);
                }}
              >
                {t("Add account")}
              </button>
            )}
          </SettingsToolbar>
          {Object.keys(data.roles).some((role) => !data.defaults[role]) && (
            <button
              className="br-btn"
              disabled={!canManage || busy || !!pending}
              onClick={() =>
                void propose("finance.account.initialize", {}, t("Set up standard accounts"))
              }
            >
              {t("Set up standard accounts")}
            </button>
          )}
          {data.accounts.length === 0 ? (
            <SettingsEmptyState />
          ) : (
            <div ref={controls} className="overflow-x-auto">
              <table className="w-full min-w-[42rem] text-left text-sm">
                <thead>
                  <tr>
                    <th className="border-b border-border-default p-2">{t("Code")}</th>
                    <th className="border-b border-border-default p-2">{t("Name")}</th>
                    <th className="border-b border-border-default p-2">{t("Role")}</th>
                    <th className="border-b border-border-default p-2">{t("Status")}</th>
                    <th className="border-b border-border-default p-2">{t("Actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.accounts.map((account) => (
                    <tr key={account.id}>
                      <td className="border-b border-border-default p-2">{account.code}</td>
                      <td className="border-b border-border-default p-2">{account.name}</td>
                      <td className="border-b border-border-default p-2">
                        {t(data.roles[account.role])}
                      </td>
                      <td className="border-b border-border-default p-2">
                        {t(account.state === "active" ? "Active" : "Blocked")}
                        {data.defaults[account.role] === account.id && (
                          <span className="finance-default-badge">{t("Default")}</span>
                        )}
                      </td>
                      <td className="border-b border-border-default p-2">
                        <div className="finance-row-actions">
                          <button
                            className="finance-row-button"
                            disabled={!canManage || busy || !!pending}
                            onClick={() => {
                              setEditing(account);
                              setEditorOpen(true);
                              setError("");
                            }}
                          >
                            {t("Edit")}
                          </button>
                          <RowActions disabled={!canManage || busy || !!pending}>
                            <button
                              className="finance-menu-action"
                              disabled={!canManage || busy || !!pending}
                              onClick={() =>
                                void propose(
                                  "finance.account.update",
                                  {
                                    account_id: account.id,
                                    state: account.state === "active" ? "blocked" : "active",
                                  },
                                  `${account.code} · ${t(account.state === "active" ? "Block account" : "Activate account")}`,
                                )
                              }
                            >
                              {t(account.state === "active" ? "Block account" : "Activate account")}
                            </button>
                            {data.defaults[account.role] !== account.id && (
                              <button
                                className="finance-menu-action"
                                disabled={
                                  !canManage ||
                                  busy ||
                                  !!pending ||
                                  account.state !== "active" ||
                                  data.defaults[account.role] === account.id
                                }
                                onClick={() =>
                                  void propose(
                                    "finance.account.set_default",
                                    { account_id: account.id, role: account.role },
                                    `${account.code} · ${t("Use as default")}`,
                                  )
                                }
                              >
                                {t("Use as default")}
                              </button>
                            )}
                          </RowActions>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {canManage && editorOpen && !pending && (
            <SettingsDialog
              title={t(editing ? "Edit account" : "Create account")}
              description={t(
                "The account role determines which operational transactions can use this account. External ledger numbers are configured under External accounting.",
              )}
              busy={busy}
              error={error}
              close={() => setEditorOpen(false)}
            >
              <form
                className="grid gap-4 sm:grid-cols-2"
                onSubmit={create}
                key={editing?.id || "new-account"}
              >
                <p className="text-sm text-fg-muted sm:col-span-2">
                  {t("All fields are required unless marked optional.")}
                </p>
                <label>
                  {t("Code")}
                  <input
                    className="br-control w-full"
                    name="code"
                    defaultValue={editing?.code || ""}
                    required
                    disabled={!canManage || busy || !!pending}
                  />
                </label>
                <label>
                  {t("Name")}
                  <input
                    className="br-control w-full"
                    name="name"
                    defaultValue={editing?.name || ""}
                    required
                    disabled={!canManage || busy || !!pending}
                  />
                </label>
                <p className="text-sm text-fg-muted sm:col-span-2">
                  {t(
                    "The role is fixed after creation. The default account is used when a transaction does not specify another eligible account.",
                  )}
                </p>
                <label>
                  {t("Role")}
                  <select
                    className="br-control w-full"
                    aria-label={t("Role")}
                    name="role"
                    defaultValue={editing?.role}
                    disabled={!canManage || busy || !!pending || !!editing}
                  >
                    {Object.entries(data.roles).map(([key, label]) => (
                      <option key={key} value={key}>
                        {t(label)}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="finance-form-actions sm:col-span-2">
                  <button
                    className="br-btn br-btn-primary"
                    disabled={!canManage || busy || !!pending}
                  >
                    {t("Review account change")}
                  </button>
                  <button
                    type="button"
                    className="br-btn"
                    disabled={busy}
                    onClick={() => setEditorOpen(false)}
                  >
                    {t("Cancel")}
                  </button>
                </div>
              </form>
            </SettingsDialog>
          )}
        </>
      )}
      {defaultRole && data && canManage && (
        <SettingsDialog
          title={t("Change default account")}
          busy={busy}
          error={error}
          close={() => setDefaultRole(null)}
        >
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              void propose(
                "finance.account.set_default",
                { account_id: defaultAccount, role: defaultRole },
                `${t(data.roles[defaultRole])} · ${data.accounts.find((a) => a.id === defaultAccount)?.code} · ${t("Use as default")}`,
              );
            }}
          >
            <p className="font-medium">{t(data.roles[defaultRole])}</p>
            <p className="text-sm text-fg-muted">
              {t(
                "This default applies to every transaction using this account role. Existing postings keep their original accounts.",
              )}
            </p>
            <label className="block">
              {t("Account")}
              <select
                required
                className="br-control mt-2 w-full"
                aria-label={t("Account")}
                value={defaultAccount}
                disabled={busy}
                onChange={(e) => setDefaultAccount(e.target.value)}
              >
                <option value="">{t("Select")}</option>
                {data.accounts
                  .filter((a) => a.role === defaultRole && a.state === "active")
                  .map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.code} · {a.name}
                    </option>
                  ))}
              </select>
            </label>
            {!data.accounts.some((a) => a.role === defaultRole && a.state === "active") && (
              <p>{t("Add an active account with this role before changing the default.")}</p>
            )}
            <div className="finance-form-actions">
              <button
                className="br-btn br-btn-primary"
                disabled={
                  busy ||
                  !defaultAccount ||
                  defaultAccount === data.defaults[defaultRole] ||
                  !data.accounts.some(
                    (a) =>
                      a.id === defaultAccount && a.role === defaultRole && a.state === "active",
                  )
                }
              >
                {t("Review account change")}
              </button>
              <button
                type="button"
                className="br-btn"
                disabled={busy}
                onClick={() => setDefaultRole(null)}
              >
                {t("Cancel")}
              </button>
            </div>
          </form>
        </SettingsDialog>
      )}
      {pending && !editorOpen && <ReviewNotice open={() => setEditorOpen(true)} />}
      {pending && (
        <>
          {editorOpen && (
            <SettingsDialog
              title={t("Confirm account change")}
              description={t(
                "Check the proposed values. The change takes effect only after confirmation.",
              )}
              busy={busy}
              error={error}
              close={() => setEditorOpen(false)}
            >
              <section className="space-y-4" aria-label={t("Confirm account change")}>
                <p>{pending.description}</p>
                <div className="finance-form-actions">
                  <button
                    className="br-btn br-btn-primary"
                    autoFocus
                    disabled={busy || !canManage}
                    onClick={() => void confirm()}
                  >
                    {t("Confirm")}
                  </button>
                  <button
                    className="br-btn"
                    disabled={busy || !canManage}
                    onClick={() => {
                      if (pending) {
                        setBusy(true);
                        void call(`${base}/change-proposals/${pending.id}/reject`, {})
                          .then(() => {
                            setPending(null);
                            setEditorOpen(false);
                          })
                          .catch((e) => setError(e.message))
                          .finally(() => setBusy(false));
                      }
                    }}
                  >
                    {t("Cancel")}
                  </button>
                </div>
              </section>
            </SettingsDialog>
          )}
        </>
      )}
    </Container>
  );
}
