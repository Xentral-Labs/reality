import { useEffect, useRef, useState } from "react";
import { api, APIError, type AIConfiguration } from "../api";
import { t } from "../localization";
import { ReadState } from "./ReadState";
import { MCPAccess, accessLabel } from "./MCPAccess";
type Action =
  | {
      kind: "provider";
      mode: "managed" | "anthropic";
      effect: string;
      model: string;
      endpoint: string;
    }
  | { kind: "token"; name: string; tools: string[] }
  | { kind: "revoke"; id: string; name: string; prefix: string };
type Pending = { id: string; kind: Action["kind"] };
export function AISettings({
  tenant,
  tokensOnly = false,
  onBusyChange,
}: {
  tenant: string;
  tokensOnly?: boolean;
  onBusyChange?: (blocked: boolean) => void;
}) {
  const storageKey = `reality.ai-settings.pending:${tenant}`;
  const [pending, setPending] = useState<Pending | null>(() => {
    try {
      return JSON.parse(sessionStorage.getItem(storageKey) || "null");
    } catch {
      return null;
    }
  });
  const [data, setData] = useState<AIConfiguration | null>(null),
    [readError, setReadError] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState(false),
    [busy, setBusy] = useState(false),
    [editing, setEditing] = useState(false),
    [mode, setMode] = useState<"managed" | "anthropic">("managed"),
    [apiKey, setApiKey] = useState(""),
    [action, setAction] = useState<Action | null>(null),
    [secret, setSecret] = useState<{ id: string; value: string } | null>(null),
    [copyError, setCopyError] = useState(false),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    onBusyChange?.(busy || !!pending);
  }, [busy, pending, onBusyChange]);
  const active = useRef(true),
    lock = useRef(false),
    key = useRef(""),
    review = useRef<HTMLElement>(null);
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
      key.current = "";
    };
  }, []);
  const load = async () => {
    try {
      const value = await api.aiSettings(tenant);
      if (active.current) {
        setData(value);
        setReadError(false);
      }
      return value;
    } catch {
      if (active.current) setReadError(true);
      return null;
    }
  };
  useEffect(() => {
    void load();
  }, [tenant]);
  useEffect(() => {
    if (action) review.current?.focus();
  }, [action]);
  const run = async (work: () => Promise<void>) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setMessage("");
    setError(false);
    try {
      await work();
    } catch {
      if (active.current) {
        setError(true);
        setMessage(
          "Could not complete the request. Check the current settings before trying again.",
        );
      }
    } finally {
      lock.current = false;
      if (active.current) setBusy(false);
    }
  };
  const clearPending = (value: Pending) => {
    if (sessionStorage.getItem(storageKey) === JSON.stringify(value))
      sessionStorage.removeItem(storageKey);
  };
  const recover = () =>
    run(async () => {
      const value = await load();
      if (!value) throw new Error("read failed");
      if (!active.current) return;
      if (pending) clearPending(pending);
      setPending(null);
      setAction(null);
      setEditing(false);
      setApiKey("");
      key.current = "";
      setMessage("Current AI settings loaded. This is not a receipt for the previous request.");
      setRevision((value) => value + 1);
    });
  const confirm = () =>
    run(async () => {
      if (!action || pending) return;
      const attempt = { id: crypto.randomUUID(), kind: action.kind };
      sessionStorage.setItem(storageKey, JSON.stringify(attempt));
      setPending(attempt);
      const submittedKey = key.current;
      key.current = "";
      setApiKey("");
      try {
        if (action.kind === "provider")
          await api.saveAISettings(tenant, { provider_preset: action.mode, api_key: submittedKey });
        else if (action.kind === "token") {
          const value = await api.createMCPToken(tenant, action.name, action.tools);
          if (active.current) setSecret({ id: value.id, value: value.token });
        } else await api.revokeMCPToken(tenant, action.id);
        clearPending(attempt);
        if (!active.current) return;
        setPending(null);
        setAction(null);
        setEditing(false);
        setRevision((value) => value + 1);
        setMessage(
          action.kind === "provider"
            ? "AI setup saved."
            : action.kind === "token"
              ? "MCP token created."
              : "MCP token revoked.",
        );
        await load();
      } catch (e) {
        if (e instanceof APIError && e.status >= 400 && e.status < 500) {
          clearPending(attempt);
          if (active.current) {
            setPending(null);
            setAction(null);
            setEditing(false);
            setError(true);
            setMessage(
              "The change was rejected. Review the current settings and enter credentials again if needed.",
            );
          }
        } else throw e;
      }
    });
  const config = data?.copilot;
  const unsupported =
    !!config?.provider_preset && !["managed", "anthropic"].includes(config.provider_preset);
  const anthropic = config?.presets?.find((preset) => preset.id === "anthropic");
  const canRetain = config?.provider_preset === "anthropic" && config.has_company_api_key;
  const disabled = busy || !!pending || !!action || readError || !!secret;
  const choose = (value: Action) => {
    setMessage("");
    setError(false);
    setAction(value);
  };
  return (
    <div data-ai-settings className="space-y-6">
      {message && (
        <p role={error ? "alert" : "status"} className="rounded-lg bg-surface-muted p-4 text-sm">
          {t(message)}
        </p>
      )}
      {pending && (
        <div className="space-y-3 rounded-lg border border-accent p-4">
          <p className="text-sm">
            {t("The result needs checking. No change will be sent again automatically.")}
          </p>
          {pending.kind === "token" && (
            <p className="text-sm">
              {t(
                "A token secret cannot be recovered. Inspect active tokens and revoke an unwanted token before creating a replacement.",
              )}
            </p>
          )}
          <button
            data-ai-recovery
            className="br-btn"
            disabled={busy}
            onClick={() => void recover()}
          >
            {t("Check saved AI settings")}
          </button>
        </div>
      )}
      {secret && (
        <section className="space-y-3 rounded-lg border border-accent p-4">
          <h3 className="font-semibold">{t("Copy this token now")}</h3>
          <p className="break-all text-xs">{secret.id}</p>
          <p className="text-sm">{t("It will not be shown again.")}</p>
          <textarea
            className="br-control w-full font-mono text-xs"
            aria-label={t("New MCP token secret")}
            readOnly
            value={secret.value}
          />
          <div className="flex flex-wrap gap-3">
            <button
              className="br-btn"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(secret.value);
                  setCopyError(false);
                } catch {
                  setCopyError(true);
                }
              }}
            >
              {t("Copy token")}
            </button>
            <button
              className="br-btn"
              onClick={() => {
                setSecret(null);
                setCopyError(false);
              }}
            >
              {t("Hide token secret")}
            </button>
          </div>
          {copyError && (
            <p role="alert" className="text-sm">
              {t("Copy failed. Select and copy the value manually.")}
            </p>
          )}
        </section>
      )}
      {readError && (
        <ReadState error={t("AI settings are unavailable.")} retry={() => void load()} />
      )}
      {!data && !readError && <ReadState loading />}
      {data && config && (
        <>
          {!tokensOnly && (
            <>
              <div className="rounded-lg bg-accent-soft p-5">
                <p className="font-medium">
                  {t(
                    config.available
                      ? "AI credentials configured"
                      : "AI credentials not configured",
                  )}
                </p>
                <p className="mt-2 text-sm text-fg-muted">
                  {t("Configuration status does not confirm a live connection to the AI provider.")}
                </p>
              </div>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-fg-muted">{t("Credential management")}</dt>
                  <dd>
                    {t(
                      config.credential_mode === "company"
                        ? "Company credentials"
                        : "Managed by Reality",
                    )}
                  </dd>
                </div>
                {config.credential_mode === "company" && (
                  <div>
                    <dt className="text-fg-muted">{t("Model")}</dt>
                    <dd className="break-all">{config.model || t("Not configured")}</dd>
                  </div>
                )}
              </dl>
              {unsupported && (
                <p className="rounded-lg bg-surface-muted p-4 text-sm">
                  {t(
                    "Other provider settings are stored, but Ask Reality currently uses managed AI or a company Anthropic key.",
                  )}
                </p>
              )}
              {unsupported && (
                <details className="rounded-lg border border-border-default p-4 text-sm">
                  <summary className="cursor-pointer">{t("Stored provider details")}</summary>
                  <dl className="mt-3 space-y-3">
                    <div>
                      <dt className="text-fg-muted">{t("Provider")}</dt>
                      <dd className="break-words">
                        {config.presets?.find((value) => value.id === config.provider_preset)
                          ?.name || config.provider_preset}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-fg-muted">{t("Endpoint")}</dt>
                      <dd className="break-all">{config.base_url}</dd>
                    </div>
                  </dl>
                </details>
              )}
              <button
                className="br-btn"
                disabled={disabled}
                onClick={() => {
                  setMode(config.provider_preset === "anthropic" ? "anthropic" : "managed");
                  setEditing(true);
                  setApiKey("");
                  setMessage("");
                }}
              >
                {t("Change AI setup")}
              </button>
              {editing && !action && (
                <form
                  className="space-y-4 rounded-lg border border-border-default p-4"
                  onSubmit={(e) => {
                    e.preventDefault();
                    key.current = apiKey.trim();
                    setApiKey("");
                    choose({
                      kind: "provider",
                      mode,
                      model: mode === "anthropic" ? anthropic?.models[0]?.[0] || "" : "",
                      endpoint: mode === "anthropic" ? anthropic?.base_url || "" : "",
                      effect:
                        mode === "managed"
                          ? "Remove the company key and use deployment-managed AI."
                          : key.current
                            ? "Replace the company key with the new key."
                            : "Keep the stored company key.",
                    });
                  }}
                >
                  <fieldset disabled={disabled} className="space-y-4">
                    <label className="block text-sm">
                      {t("AI credential source")}
                      <select
                        aria-label={t("AI credential source")}
                        className="br-control mt-2 w-full"
                        value={mode}
                        onChange={(e) => {
                          setMode(e.target.value as typeof mode);
                          setApiKey("");
                        }}
                      >
                        <option value="managed">{t("Managed by Reality")}</option>
                        <option value="anthropic" disabled={!anthropic}>
                          {t("Company Anthropic key")}
                        </option>
                      </select>
                    </label>
                    {mode === "anthropic" && (
                      <>
                        <p className="break-words text-sm">
                          {t("Fixed chat model")}: {anthropic?.models[0]?.[0]}
                        </p>
                        <p className="break-all text-xs text-fg-muted">{anthropic?.base_url}</p>
                        <label className="block text-sm">
                          {t("API key")}
                          <input
                            className="br-control mt-2 w-full"
                            type="password"
                            autoComplete="new-password"
                            required={!canRetain}
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                          />
                        </label>
                        <p className="text-sm text-fg-muted">
                          {t(
                            canRetain
                              ? "Leave the key empty to keep the stored company key."
                              : "Enter a new company API key.",
                          )}
                        </p>
                      </>
                    )}
                    <div className="flex flex-wrap gap-3">
                      <button
                        className="br-btn br-btn-primary"
                        disabled={
                          mode === "anthropic" && (!anthropic || (!canRetain && !apiKey.trim()))
                        }
                      >
                        {t("Review AI setup")}
                      </button>
                      <button
                        type="button"
                        className="br-btn"
                        onClick={() => {
                          setEditing(false);
                          setApiKey("");
                        }}
                      >
                        {t("Close")}
                      </button>
                    </div>
                  </fieldset>
                </form>
              )}
            </>
          )}
          {action && (
            <section
              data-ai-review
              ref={review}
              tabIndex={-1}
              className="space-y-4 rounded-lg border border-accent p-4"
            >
              <h3 className="font-semibold">
                {t(
                  action.kind === "provider"
                    ? "Review AI setup"
                    : action.kind === "token"
                      ? "Review token"
                      : "Review token revocation",
                )}
              </h3>
              {action.kind === "provider" ? (
                <>
                  <p>
                    {t(action.mode === "managed" ? "Managed by Reality" : "Company Anthropic key")}
                  </p>
                  {action.model && <p className="break-all text-sm">{action.model}</p>}
                  {action.endpoint && <p className="break-all text-xs">{action.endpoint}</p>}
                  <p className="text-sm">{t(action.effect)}</p>
                </>
              ) : action.kind === "token" ? (
                <>
                  <p className="break-words">{action.name}</p>
                  {action.tools.some(
                    (name) => data.tools.find((tool) => tool.name === name)?.access === "confirm",
                  ) && (
                    <p className="rounded-lg bg-surface-muted p-3 text-sm">
                      {t("This token may approve and execute changes through its selected tools.")}
                    </p>
                  )}
                  <ul className="max-h-64 space-y-2 overflow-auto text-sm">
                    {action.tools.map((name) => (
                      <li className="break-all" key={name}>
                        {name} ·{" "}
                        {accessLabel(
                          data.tools.find((tool) => tool.name === name)?.access || "Unknown",
                        )}
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <>
                  <p className="break-words">{action.name}</p>
                  <p className="break-all text-xs">
                    {action.id} · {action.prefix}…
                  </p>
                  <p className="text-sm">
                    {t("This token will no longer authorize new MCP requests.")}
                  </p>
                </>
              )}
              <div className="flex flex-wrap gap-3">
                <button
                  className="br-btn br-btn-primary"
                  disabled={busy || !!pending}
                  onClick={() => void confirm()}
                >
                  {t("Confirm")}
                </button>
                {!pending && (
                  <button
                    className="br-btn"
                    disabled={busy}
                    onClick={() => {
                      setAction(null);
                      key.current = "";
                    }}
                  >
                    {t("Cancel")}
                  </button>
                )}
              </div>
            </section>
          )}
          {tokensOnly && (
            <MCPAccess
              tenant={tenant}
              data={data}
              disabled={disabled}
              revision={revision}
              create={(name, tools) => choose({ kind: "token", name, tools })}
              revoke={(token) =>
                choose({
                  kind: "revoke",
                  id: token.id,
                  name: token.name,
                  prefix: token.token_prefix,
                })
              }
            />
          )}
        </>
      )}
    </div>
  );
}
