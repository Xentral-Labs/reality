import { FlaskConical } from "lucide-react";
import { Inspector } from "../unified/Inspector";
import { useEffect, useRef, useState } from "react";
import {
  api,
  APIError,
  type DemoDataStatus,
  type DemoDataPreview,
  type DemoImportPage,
} from "../api";
import { t, formatDateTime } from "../localization";
import { financeLink, needsAttention, orderToCashRows } from "./demoDataSummary";

type Change = {
  action: string;
  expected_revision: number;
  request_key: string;
  rate?: number;
  confirmed: true;
};
const labels: Record<string, string> = {
  start: "Start simulation",
  pause: "Pause",
  resume: "Resume",
  stop: "Stop",
  disconnect: "Disconnect",
  reconnect: "Reconnect",
  set_rate: "Change rate",
  stopped: "Stopped",
  running: "Running",
  paused: "Paused",
  disconnected: "Disconnected",
  throttled: "Paused: resolve failed imports",
  error: "Execution needs attention",
  not_connected: "Not connected",
};

export function DemoDataIntegration(props: {
  tenantId: string;
  runId?: string;
  showCompanyLink?: boolean;
}) {
  return <DemoDataIntegrationView key={`${props.tenantId}:${props.runId || ""}`} {...props} />;
}

function DemoDataIntegrationView({
  tenantId,
  runId,
  showCompanyLink = false,
}: {
  tenantId: string;
  runId?: string;
  showCompanyLink?: boolean;
}) {
  const scope = runId
    ? `/api/playground/runs/${encodeURIComponent(runId)}/demo-data`
    : `/api/tenants/${encodeURIComponent(tenantId)}/demo-data`;
  const storage = `reality.demo-data.${scope}`;
  const [intake, setIntake] = useState<Record<string, unknown>>();
  const [inspectedOrder, setInspectedOrder] = useState<string>();
  const [state, setState] = useState<DemoDataStatus>();
  const [preview, setPreview] = useState<DemoDataPreview>();
  const [page, setPage] = useState<DemoImportPage>();
  const [change, setChange] = useState<Change>();
  const [rate, setRate] = useState(60);
  const [busy, setBusy] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState<Date>();
  const [stale, setStale] = useState(false);
  const active = useRef(true);
  const working = useRef(false);
  const reading = useRef<Promise<DemoDataStatus> | null>(null);
  const initialized = useRef(false);
  const refresh = () => {
    if (reading.current) return reading.current;
    const request = (async () => {
      try {
        const next = await api.demoDataStatus(scope);
        const loaded =
          next.state !== "not_connected" ? await api.demoDataImports(scope, "", true) : undefined;
        if (!active.current) return next;
        setState(next);
        setPage(loaded);
        setUpdatedAt(new Date());
        setStale(false);
        if (!initialized.current) {
          setRate(next.rate);
          const saved = sessionStorage.getItem(storage);
          if (saved) {
            const pending = JSON.parse(saved) as Change;
            if (next.last_request_key === pending.request_key) sessionStorage.removeItem(storage);
            else setChange(pending);
          }
          initialized.current = true;
        }
        return next;
      } catch (failure) {
        if (active.current) {
          if (
            !initialized.current &&
            failure instanceof APIError &&
            [403, 404].includes(failure.status)
          )
            setUnavailable(true);
          else setStale(true);
        }
        throw failure;
      } finally {
        reading.current = null;
      }
    })();
    reading.current = request;
    return request;
  };
  useEffect(() => {
    active.current = true;
    const poll = () => {
      if (!working.current && document.visibilityState !== "hidden") void refresh().catch(() => {});
    };
    poll();
    const timer = window.setInterval(poll, 5000);
    document.addEventListener("visibilitychange", poll);
    return () => {
      active.current = false;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", poll);
    };
  }, [scope]);
  const act = async (operation: () => Promise<unknown>, reload = true) => {
    working.current = true;
    setBusy(true);
    setError("");
    try {
      await reading.current?.catch(() => {});
      if (!active.current) return;
      await operation();
      if (reload) await refresh();
    } catch (failure) {
      if (failure instanceof APIError && failure.status === 409) {
        sessionStorage.removeItem(storage);
        setChange(undefined);
      }
      setError(t("The change could not be confirmed. Refresh the status before retrying."));
    } finally {
      working.current = false;
      setBusy(false);
    }
  };
  if (unavailable)
    return (
      <section
        data-simulation-unavailable
        aria-labelledby={`simulation-unavailable-${tenantId}`}
        className="max-w-3xl rounded-xl border border-border-default bg-surface p-6 sm:p-8"
      >
        <div className="flex flex-col gap-5 sm:flex-row sm:gap-6">
          <span
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent-soft text-accent"
            aria-hidden="true"
          >
            <FlaskConical size={24} />
          </span>
          <div className="min-w-0 flex-1">
            <h2
              id={`simulation-unavailable-${tenantId}`}
              className="text-xl font-semibold tracking-tight text-fg-strong"
            >
              {t("Live simulation")}
            </h2>
            <p className="mt-2 text-sm leading-6 text-fg-muted">
              {t("Live simulation is not available in this Sandbox.")}
            </p>
            <p className="mt-3 max-w-xl text-sm leading-6 text-fg-muted">
              {t(
                "Live simulation supports empty and standard demo Sandbox setups. Storyline Sandboxes use a different data setup that is not yet supported.",
              )}
            </p>
            {showCompanyLink && (
              <>
                <p className="mt-3 max-w-xl text-sm leading-6 text-fg-muted">
                  {t(
                    "Create an empty Sandbox under Companies → New company, then enable live simulation there. No historical demo data is needed.",
                  )}
                </p>
                <a
                  className="br-btn br-btn-primary mt-6"
                  href={`/app/settings?tenant=${encodeURIComponent(tenantId)}&settings_view=company`}
                >
                  {t("Companies")}
                </a>
              </>
            )}
          </div>
        </div>
      </section>
    );
  return (
    <section
      className="panel integration-section demo-data-integration"
      aria-labelledby={`demo-data-${tenantId}`}
      aria-busy={busy}
    >
      <header className="demo-live-header">
        <div>
          <h2 id={`demo-data-${tenantId}`}>{t("Live simulation")}</h2>
          <p className="demo-live-description">
            {t(
              (state?.derived_state || state?.state) === "running"
                ? "New demo orders arrive automatically."
                : state?.state === "paused"
                  ? "New arrivals are paused. Existing orders remain available."
                  : "Explore your business with synthetic orders.",
            )}
          </p>
        </div>
        {state && (
          <span className="demo-live-badge" data-state={state.derived_state || state.state}>
            {t(labels[state.derived_state || state.state] || state.state)}
          </span>
        )}
      </header>
      {stale && (
        <p role="alert" className="demo-live-warning">
          {t("Live updates are unavailable. Showing the last known information.")}
        </p>
      )}
      {!state && !stale && <p role="status">{t("Loading")}</p>}
      {error && <p role="alert">{error}</p>}
      {!state && (error || stale) && (
        <button disabled={busy} onClick={() => void refresh().catch(() => {})}>
          {t("Refresh status")}
        </button>
      )}
      {intake && (
        <details open>
          <summary>{t("Original source and interpretation")}</summary>
          <button onClick={() => setIntake(undefined)}>{t("Close")}</button>
          <pre data-localization="original">{JSON.stringify(intake, null, 2)}</pre>
        </details>
      )}
      {inspectedOrder && (
        <aside aria-label={t("Reality inspector")}>
          <button onClick={() => setInspectedOrder(undefined)}>{t("Close")}</button>
          <Inspector
            key={inspectedOrder}
            tenant={tenantId}
            target={{ kind: "document", id: inspectedOrder }}
            close={() => setInspectedOrder(undefined)}
          />
        </aside>
      )}
      {state?.state === "not_connected" ? (
        <>
          <button
            className="secondary-button"
            disabled={busy}
            onClick={() => void act(async () => setPreview(await api.demoDataPreview(scope)))}
          >
            {t("Review demo connection")}
          </button>
          {preview && (
            <div>
              <p>
                {t(
                  "Only the following missing references will be added. No stock or history is created.",
                )}
              </p>
              <ul data-localization="original">
                {Object.entries(preview.add).flatMap(([kind, rows]) =>
                  rows.map((row) => <li key={`${kind}:${row.key}`}>{row.name}</li>),
                )}
              </ul>
              <button
                className="primary-button"
                disabled={busy}
                onClick={() =>
                  void act(async () => {
                    const key = sessionStorage.getItem(`${storage}.connect`) || crypto.randomUUID();
                    sessionStorage.setItem(`${storage}.connect`, key);
                    await api.demoDataConnect(scope, {
                      request_key: key,
                      preview_fingerprint: preview.fingerprint,
                      confirmed: true,
                    });
                    sessionStorage.removeItem(`${storage}.connect`);
                    setPreview(undefined);
                  })
                }
              >
                {t("Confirm connection")}
              </button>
              <button
                className="secondary-button"
                disabled={busy}
                onClick={() => setPreview(undefined)}
              >
                {t("Cancel")}
              </button>
            </div>
          )}
        </>
      ) : (
        state && (
          <>
            <dl className="demo-data-counts">
              <div>
                <dt>{t("Imported orders")}</dt>
                <dd>{state.imported}</dd>
              </div>
              <div>
                <dt>{t("Generated orders")}</dt>
                <dd>{state.generated}</dd>
              </div>
              <div>
                <dt>{t("Pending")}</dt>
                <dd>{state.pending}</dd>
              </div>
              <div>
                <dt>{t("Failed")}</dt>
                <dd>{state.failed}</dd>
              </div>
            </dl>
            <p>
              {t("Next scheduled arrival")}:{" "}
              {state.next_arrival ? formatDateTime(state.next_arrival) : "—"}
            </p>
            <p>
              {t("Last successful import")}:{" "}
              {state.last_success ? formatDateTime(state.last_success) : "—"}
            </p>
            {state.order_to_cash && (
              <section className="demo-order-to-cash" aria-label={t("Order to cash")}>
                <h4>{t("Order to cash")}</h4>
                <dl className="demo-data-counts">
                  {orderToCashRows(state.order_to_cash).map((row) => (
                    <div key={row.key}>
                      <dt>{t(row.label)}</dt>
                      <dd>{row.value}</dd>
                    </div>
                  ))}
                </dl>
                <p>
                  {t("Next settlement")}:{" "}
                  {state.order_to_cash.next_settlement
                    ? formatDateTime(state.order_to_cash.next_settlement)
                    : "—"}
                  {" · "}
                  {t("Last settlement")}:{" "}
                  {state.order_to_cash.last_settlement
                    ? formatDateTime(state.order_to_cash.last_settlement)
                    : "—"}
                </p>
                {!runId && (
                  <p className="demo-order-to-cash-links">
                    <a href={financeLink(tenantId, "payments")}>{t("Open payments")}</a>
                    {" · "}
                    <a href={financeLink(tenantId, "open-items")}>{t("Open open items")}</a>
                    {" · "}
                    <a href={financeLink(tenantId, "journal")}>{t("Open journal")}</a>
                    {needsAttention(state.order_to_cash) && (
                      <>
                        {" · "}
                        <span>{t("Differences wait for your decision in Payments.")}</span>
                      </>
                    )}
                  </p>
                )}
              </section>
            )}
            <div className="demo-live-controls">
              <div className="demo-live-primary">
                {(state.state === "running"
                  ? ["pause"]
                  : state.state === "paused"
                    ? ["resume"]
                    : state.state === "stopped"
                      ? ["start"]
                      : ["reconnect"]
                ).map((action) => (
                  <button
                    key={action}
                    className="primary-button"
                    disabled={busy || !!change}
                    onClick={() =>
                      setChange({
                        action,
                        expected_revision: state.revision,
                        request_key: crypto.randomUUID(),
                        confirmed: true,
                        ...(action === "start" ? { rate } : {}),
                      })
                    }
                  >
                    {t(labels[action])}
                  </button>
                ))}
                {state.state !== "disconnected" && (
                  <div className="demo-live-rate">
                    <label htmlFor={`demo-rate-${tenantId}`}>{t("Orders per hour")}</label>
                    <select
                      id={`demo-rate-${tenantId}`}
                      value={rate}
                      onChange={(event) => setRate(Number(event.target.value))}
                      disabled={busy || !!change}
                    >
                      {[10, 60, 300].map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                    {rate !== state.rate && (
                      <button
                        className="secondary-button"
                        disabled={busy || !!change}
                        onClick={() =>
                          setChange({
                            action: "set_rate",
                            expected_revision: state.revision,
                            request_key: crypto.randomUUID(),
                            confirmed: true,
                            rate,
                          })
                        }
                      >
                        {t("Apply")}
                      </button>
                    )}
                  </div>
                )}
              </div>
              {state.state !== "disconnected" && (
                <div className="demo-live-secondary">
                  {(state.state === "stopped" ? ["disconnect"] : ["stop", "disconnect"]).map(
                    (action) => (
                      <button
                        key={action}
                        className="secondary-button"
                        disabled={busy || !!change}
                        onClick={() =>
                          setChange({
                            action,
                            expected_revision: state.revision,
                            request_key: crypto.randomUUID(),
                            confirmed: true,
                          })
                        }
                      >
                        {t(labels[action])}
                      </button>
                    ),
                  )}
                </div>
              )}
            </div>
            {change && (
              <div className="demo-live-confirmation" aria-live="polite">
                <p>
                  {t("Confirm Demo Data change")}: {t(labels[change.action])}
                  {change.rate ? ` · ${change.rate}` : ""}
                </p>
                <div className="onboarding-actions">
                  <button
                    className="primary-button"
                    disabled={busy}
                    onClick={() =>
                      void act(async () => {
                        sessionStorage.setItem(storage, JSON.stringify(change));
                        await api.demoDataControl(scope, change);
                        sessionStorage.removeItem(storage);
                        setChange(undefined);
                      })
                    }
                  >
                    {t("Confirm")}
                  </button>
                  <button
                    className="secondary-button"
                    disabled={busy || !!sessionStorage.getItem(storage)}
                    onClick={() => setChange(undefined)}
                  >
                    {t("Cancel")}
                  </button>
                </div>
              </div>
            )}
            <section className="demo-live-activity" aria-label={t("Live activity")}>
              <header className="demo-live-header">
                <div>
                  <h3>{t("Live activity")}</h3>
                  <p className="demo-live-description">
                    {t("Latest 25 demo orders. Updates automatically while this page is visible.")}
                  </p>
                </div>
                <button
                  className="secondary-button"
                  disabled={busy}
                  onClick={() => void refresh().catch(() => {})}
                >
                  {t("Refresh status")}
                </button>
              </header>
              {updatedAt && (
                <p className="demo-live-updated">
                  {t("Last checked")}: {formatDateTime(updatedAt.toISOString())}
                </p>
              )}
              {page?.items.length === 0 && (
                <p className="demo-live-empty">{t("Waiting for the first demo order.")}</p>
              )}
              <ol className="demo-live-events">
                {page?.items.map((row) => (
                  <li key={row.id} className="demo-live-event" data-status={row.status}>
                    <span className="demo-live-event-dot" aria-hidden="true" />
                    <div className="demo-live-event-content">
                      <div className="demo-live-event-title">
                        <strong>
                          {t(
                            row.status === "completed"
                              ? "Demo order imported"
                              : row.status === "failed"
                                ? "Demo import failed"
                                : "Demo import pending",
                          )}
                        </strong>
                        {row.document_number && (
                          <span data-localization="original">{row.document_number}</span>
                        )}
                      </div>
                      {(row.completed_at || row.created_at) && (
                        <p className="demo-live-description">
                          {t(row.completed_at ? "Completed" : "Received")}:{" "}
                          <time dateTime={row.completed_at || row.created_at}>
                            {formatDateTime((row.completed_at || row.created_at)!)}
                          </time>
                        </p>
                      )}
                      <details>
                        <summary>{t("Details")}</summary>
                        <p data-localization="original">{row.id}</p>
                        <button
                          className="secondary-button"
                          disabled={busy}
                          onClick={() =>
                            void act(
                              async () => setIntake(await api.demoDataImport(scope, row.id)),
                              false,
                            )
                          }
                        >
                          {t("Original source and interpretation")}
                        </button>
                      </details>
                    </div>
                    <div className="demo-live-event-actions">
                      {row.document_id && (
                        <button
                          className="secondary-button"
                          onClick={() => setInspectedOrder(row.document_id!)}
                        >
                          {t("Open order")}
                        </button>
                      )}
                      {row.status === "failed" && (
                        <button
                          className="secondary-button"
                          disabled={busy}
                          onClick={() => void act(() => api.demoDataRetry(scope, row.id))}
                        >
                          {t("Confirm import retry")}
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            </section>
          </>
        )
      )}
    </section>
  );
}
