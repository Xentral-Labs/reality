import { useEffect, useRef, useState } from "react";
import { api, APIError, type IntegrationData } from "../api";
import { t } from "../localization";
import { DemoDataIntegration } from "../components/DemoDataIntegration";
import { ReadState } from "./ReadState";

type Action =
  | { kind: "create"; code: string; name: string; description: string }
  | { kind: "system" | "capability"; id: string; name: string; active: boolean };
export function SourceConfiguration({
  tenant,
  id,
  close,
  changed,
  records,
}: {
  tenant: string;
  id: string;
  close: () => void;
  changed: () => void;
  records: (code: string) => void;
}) {
  const storageKey = `reality.source-configuration.pending:${tenant}`;
  const [pending] = useState<Action | null>(() => {
    try {
      return JSON.parse(sessionStorage.getItem(storageKey) || "null");
    } catch {
      return null;
    }
  });
  const [action, setAction] = useState<Action | null>(pending);
  const [unknown, setUnknown] = useState(!!pending);
  const [data, setData] = useState<IntegrationData | null>(null);
  const [readError, setReadError] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(id === "new" ? "" : id);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [baseUrl, setBaseUrl] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const active = useRef(true),
    lock = useRef(false),
    review = useRef<HTMLElement>(null),
    panel = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    active.current = true;
    const trigger = document.activeElement as HTMLElement | null;
    const element = panel.current!;
    element.showModal();
    if (!pending) element.focus();
    return () => {
      active.current = false;
      element.close();
      trigger?.focus();
    };
  }, []);
  const load = async () => {
    setReadError("");
    try {
      const value = await api.integrations(tenant);
      if (active.current) setData(value);
    } catch (e) {
      if (active.current) setReadError((e as Error).message);
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
    setError("");
    try {
      await work();
    } catch (e) {
      if (active.current) setError((e as Error).message);
    } finally {
      lock.current = false;
      if (active.current) setBusy(false);
    }
  };
  const choose = (value: Action) => {
    setAction(value);
    setError("");
    setNotice("");
  };
  const confirm = () =>
    run(async () => {
      if (!action || unknown) return;
      sessionStorage.setItem(storageKey, JSON.stringify(action));
      setUnknown(true);
      try {
        let createdId = "";
        if (action.kind === "create") {
          const value = await api.createSourceSystem(tenant, {
            code: action.code,
            name: action.name,
            description: action.description,
          });
          createdId = value.id;
        } else if (action.kind === "system")
          await api.setSourceSystemActive(tenant, action.id, action.active);
        else await api.setSourceCapabilityActive(tenant, action.id, action.active);
        if (sessionStorage.getItem(storageKey) === JSON.stringify(action))
          sessionStorage.removeItem(storageKey);
        if (!active.current) return;
        setUnknown(false);
        setAction(null);
        setNotice(action.kind === "create" ? "Source registered." : "Registry state saved.");
        if (createdId) setSelected(createdId);
        setData(null);
        await load();
        if (active.current) changed();
      } catch (e) {
        if (e instanceof APIError && e.status >= 400 && e.status < 500) {
          if (sessionStorage.getItem(storageKey) === JSON.stringify(action))
            sessionStorage.removeItem(storageKey);
          if (active.current) setUnknown(false);
        }
        throw e;
      }
    });
  const recover = () =>
    run(async () => {
      const value = await api.integrations(tenant);
      if (!active.current) return;
      setData(value);
      setReadError("");
      if (action?.kind === "create") {
        const match = value.systems.find((row) => row.code === action.code);
        if (match) setSelected(match.id);
        else {
          setCode(action.code);
          setName(action.name);
          setDescription(action.description);
        }
      }
      if (sessionStorage.getItem(storageKey) === JSON.stringify(action))
        sessionStorage.removeItem(storageKey);
      setUnknown(false);
      setAction(null);
      setNotice("Current configuration loaded. This does not prove which request changed it.");
      changed();
    });
  const system = data?.systems.find((row) => row.id === selected);
  const types = data?.capabilities.filter((row) => row.system_id === selected) || [];
  return (
    <dialog
      onCancel={(event) => {
        event.preventDefault();
        if (event.target === event.currentTarget && !busy) close();
      }}
      data-source-configuration
      ref={panel}
      tabIndex={-1}
      aria-label={t("Source configuration")}
      className="m-auto max-h-[90dvh] w-[min(1000px,94vw)] min-w-0 overflow-auto space-y-5 rounded-xl border border-border-default bg-surface p-5 text-fg shadow-xl backdrop:bg-black/30 sm:p-7"
    >
      <header className="flex items-start justify-between gap-4">
        <h2 className="text-xl font-semibold">
          {t(selected ? "Source configuration" : "Register source")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      <p className="text-sm leading-relaxed text-fg-muted">
        {t(
          "Source definitions describe origins. They do not connect an account or synchronize data.",
        )}
      </p>
      {notice && (
        <p role="status" className="text-sm">
          {t(notice)}
        </p>
      )}
      {error && (
        <p role="alert" className="break-words text-sm text-danger">
          {error.startsWith("Source system code already exists:")
            ? `${t("Source code already exists.")} ${error.split(":").slice(1).join(":")}`
            : t(error)}
        </p>
      )}
      {action && (
        <section
          data-source-review
          ref={review}
          tabIndex={-1}
          className="space-y-4 rounded-lg border border-accent p-4"
        >
          <h3 className="font-semibold">
            {t(action.kind === "create" ? "Review source" : "Review registry change")}
          </h3>
          <p className="break-words">{action.name}</p>
          {action.kind === "create" ? (
            <>
              <p className="break-all text-sm">{action.code}</p>
              <p className="break-words text-sm">{action.description}</p>
            </>
          ) : (
            <>
              <p className="break-all text-xs text-fg-muted">{action.id}</p>
              <p>
                {t("After this change")}: {t(action.active ? "In use" : "Switched off")}
              </p>
            </>
          )}
          {unknown && (
            <p className="text-sm">
              {t("The result is uncertain. Check current configuration before another change.")}
            </p>
          )}
          <div className="flex flex-wrap gap-3">
            <button
              className="br-btn br-btn-primary"
              disabled={busy || unknown}
              onClick={() => void confirm()}
            >
              {t("Confirm")}
            </button>
            {!unknown && (
              <button
                className="br-btn"
                disabled={busy}
                onClick={() => {
                  setAction(null);
                  setError("");
                }}
              >
                {t("Cancel")}
              </button>
            )}
            {unknown && (
              <button data-check className="br-btn" disabled={busy} onClick={() => void recover()}>
                {t("Check current configuration")}
              </button>
            )}
          </div>
        </section>
      )}
      {!data ? (
        <ReadState loading={!readError} error={readError} retry={() => void load()} />
      ) : (
        !action &&
        (selected ? (
          system ? (
            <div className="space-y-6">
              {/* What this source is, with the one control that changes it. */}
              <div className="space-y-1">
                <h3 className="break-words text-lg font-semibold">{system.name}</h3>
                <p className="break-words text-sm text-fg-muted">{system.description}</p>
                <p className="break-all text-xs text-fg-muted">
                  {system.code} · {system.id}
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-surface-muted p-4">
                <div className="min-w-0">
                  <p className="text-sm font-medium">
                    {t(
                      system.is_active ? "This source is in use." : "This source is switched off.",
                    )}
                  </p>
                  <p className="mt-1 text-xs text-fg-muted">
                    {t("Everything already received stays as it is. Nothing is deleted.")}
                    {system.is_active && system.code === "demo_data"
                      ? ` ${t("Switching it off also stops the simulation, which then has to be started again.")}`
                      : ""}
                  </p>
                </div>
                <button
                  className="br-btn"
                  disabled={busy || unknown}
                  onClick={() =>
                    choose({
                      kind: "system",
                      id: system.id,
                      name: `${system.name} · ${system.code}`,
                      active: !system.is_active,
                    })
                  }
                >
                  {t(system.is_active ? "Switch off this source" : "Switch on this source")}
                </button>
              </div>
              <section data-source-system-settings={system.code} className="space-y-3">
                <h3 className="font-semibold">{t("Settings for this system")}</h3>
                {system.code === "demo_data" ? (
                  // What this source does is set here, beside what it is. Every
                  // system earns its own part here; the simulation is the first.
                  <div data-source-simulation-settings>
                    <DemoDataIntegration tenantId={tenant} variant="settings" />
                  </div>
                ) : (
                  <p className="text-sm text-fg-muted">
                    {t("This system has no settings of its own yet.")}
                  </p>
                )}
              </section>
              <section className="space-y-2">
                <label className="block font-semibold" htmlFor="source-base-url">
                  {t("Address of the source system")}
                </label>
                <p className="text-xs text-fg-muted">
                  {t(
                    "Where this system's records can be opened, for example https://acme.myshopify.com/admin. Configuration only: the address is never called and holds no credentials.",
                  )}
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    id="source-base-url"
                    data-source-base-url
                    className="br-control min-w-0 flex-1"
                    type="url"
                    inputMode="url"
                    placeholder="https://"
                    value={baseUrl ?? system.base_url ?? ""}
                    onChange={(event) => setBaseUrl(event.target.value)}
                  />
                  <button
                    className="br-btn"
                    disabled={busy || baseUrl === null}
                    onClick={async () => {
                      setBusy(true);
                      setError("");
                      try {
                        await api.setSourceSystemBaseUrl(tenant, system.id, baseUrl ?? "");
                        setBaseUrl(null);
                        setNotice(t("Address of the source system saved."));
                        await load();
                      } catch (e) {
                        setError((e as Error).message);
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    {t("Save address")}
                  </button>
                </div>
              </section>
              <section className="space-y-3">
                <h3 className="font-semibold">{t("Declared data types")}</h3>
                <p className="text-sm text-fg-muted">
                  {t(
                    "A declared target describes intended interpretation. An available interpreter does not prove a live connection.",
                  )}
                </p>
                {!types.length && (
                  <p className="text-sm text-fg-muted">{t("No declared data types.")}</p>
                )}
                {types.slice((page - 1) * 25, page * 25).map((row) => (
                  <article
                    key={row.id}
                    className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border-default p-4"
                  >
                    <div className="min-w-0 space-y-1">
                      <p className="break-all font-medium">
                        {row.source_type} → {row.target_type}
                      </p>
                      <p className="text-sm text-fg-muted">
                        {t(
                          row.interpreter_available
                            ? "Interpreter available"
                            : "No registered interpreter",
                        )}{" "}
                        · {t(row.is_active ? "Enabled" : "Disabled")}
                      </p>
                    </div>
                    <button
                      className="br-btn"
                      disabled={busy || unknown}
                      onClick={() =>
                        choose({
                          kind: "capability",
                          id: row.id,
                          name: `${system.name} · ${row.source_type} → ${row.target_type}`,
                          active: !row.is_active,
                        })
                      }
                    >
                      {t(row.is_active ? "Switch off this data type" : "Switch on this data type")}
                    </button>
                  </article>
                ))}
                {types.length > 25 && (
                  <div className="flex items-center gap-3">
                    <button
                      className="br-btn"
                      disabled={page === 1}
                      onClick={() => setPage(page - 1)}
                    >
                      {t("Previous")}
                    </button>
                    <span>
                      {page} / {Math.ceil(types.length / 25)}
                    </span>
                    <button
                      className="br-btn"
                      disabled={page * 25 >= types.length}
                      onClick={() => setPage(page + 1)}
                    >
                      {t("Next")}
                    </button>
                  </div>
                )}
              </section>
              <div className="flex flex-wrap justify-end gap-3 border-t border-border-default pt-4">
                <button className="br-btn" onClick={() => records(system.code)}>
                  {t("View received records")}
                </button>
              </div>
            </div>
          ) : (
            <p role="alert">{t("Source definition not found.")}</p>
          )
        ) : (
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              choose({
                kind: "create",
                code: code.trim().toLowerCase(),
                name: name.trim(),
                description: description.trim(),
              });
            }}
          >
            <label className="block text-sm">
              {t("Source code")}
              <input
                className="br-control mt-2 w-full"
                required
                maxLength={100}
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              {t("Source name")}
              <input
                className="br-control mt-2 w-full"
                required
                maxLength={255}
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              {t("Description")}
              <textarea
                className="br-control mt-2 w-full"
                maxLength={2000}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>
            <button
              className="br-btn br-btn-primary"
              disabled={busy || unknown || !code.trim() || !name.trim()}
            >
              {t("Review source")}
            </button>
          </form>
        ))
      )}
    </dialog>
  );
}
