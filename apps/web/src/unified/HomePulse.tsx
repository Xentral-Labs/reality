import { useEffect, useState } from "react";
import { Activity, CheckCircle2, Circle, History } from "lucide-react";
import { api, type ActivityVolume, type SystemReadiness } from "../api";
import { formatDateTime, t } from "../localization";
import { ActivityDrawer } from "./ActivityDrawer";
import { ActivityGraph } from "./ActivityGraph";

export function HomePulse({
  user,
  tenant,
  companyName,
}: {
  user: string;
  tenant: string;
  companyName: string;
}) {
  const storageKey = `reality.home.activity-days.${user}`;
  const [days, updateDays] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved === "7" ? 7 : saved === "30" ? 30 : 1;
    } catch {
      return 1;
    }
  });
  function setDays(value: number) {
    updateDays(value);
    try {
      localStorage.setItem(storageKey, String(value));
    } catch {
      // The current view remains usable when browser storage is unavailable.
    }
  }
  return (
    <HomePulseBody
      key={`${tenant}-${days}`}
      tenant={tenant}
      companyName={companyName}
      days={days}
      setDays={setDays}
    />
  );
}
function HomePulseBody({
  tenant,
  companyName,
  days,
  setDays,
}: {
  tenant: string;
  companyName: string;
  days: number;
  setDays: (value: number) => void;
}) {
  const [data, setData] = useState<ActivityVolume | null>(null),
    [readiness, setReadiness] = useState<SystemReadiness | null>(null);
  const [stale, setStale] = useState(false),
    [checked, setChecked] = useState(false),
    [history, setHistory] = useState(false);
  useEffect(() => {
    let disposed = false,
      busy = false;
    let controller: AbortController | undefined;
    async function refresh() {
      if (disposed || busy || document.hidden) return;
      busy = true;
      controller = new AbortController();
      const timeout = window.setTimeout(() => controller?.abort(), 8000);
      await Promise.allSettled([
        api
          .activityVolume(tenant, days, controller.signal)
          .then((result) => {
            if (!disposed) {
              setData(result);
              setStale(false);
            }
          })
          .catch(() => {
            if (!disposed) setStale(true);
          }),
        api
          .readiness(tenant, controller.signal)
          .then((result) => {
            if (!disposed) {
              setReadiness(result);
              setChecked(true);
            }
          })
          .catch(() => {
            if (!disposed) {
              setReadiness(null);
              setChecked(true);
            }
          }),
      ]);
      window.clearTimeout(timeout);
      busy = false;
    }
    void refresh();
    const timer = window.setInterval(() => void refresh(), 10000);
    const visible = () => {
      if (!document.hidden) void refresh();
    };
    document.addEventListener("visibilitychange", visible);
    return () => {
      disposed = true;
      controller?.abort();
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [tenant, days]);
  const ready = readiness?.status === "ready";
  const label = (value?: string) =>
    value === "ready"
      ? t("Ready")
      : value === "unknown"
        ? t("Not yet verified")
        : !checked
          ? t("Checking…")
          : t("Currently unavailable");
  return (
    <section
      data-home-pulse=""
      className="overflow-hidden rounded-xl border border-border-default bg-surface"
    >
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border-default p-6">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-semibold text-fg-strong">
            <Activity size={20} className="text-accent" />
            {t("Your company, in motion")}
          </h2>
          <p className="mt-2 text-sm text-fg-muted">
            {t("Recorded activity · updates every 10 seconds")}
          </p>
        </div>
        <button className="br-btn" onClick={() => setHistory(true)}>
          <History size={16} />
          {t("View all activity")}
        </button>
      </div>
      <div
        className="flex flex-wrap items-center gap-x-6 gap-y-3 border-b border-border-default bg-surface-muted px-6 py-3 text-xs"
        aria-label={t("System status")}
      >
        <p className="flex items-center gap-2 font-medium" role="status">
          {ready ? <CheckCircle2 size={16} className="text-accent" /> : <Circle size={16} />}{" "}
          {ready
            ? t("Everything is ready")
            : !checked
              ? t("Checking…")
              : t("Availability is not fully confirmed")}
        </p>
        {(
          [
            ["connection", "Connection"],
            ["scheduler", "Automatic scheduling"],
            ["worker", "Background processing"],
          ] as const
        ).map(([key, name]) => (
          <span key={key} className="text-fg-muted">
            {t(name)}: {label(readiness?.components[key])}
          </span>
        ))}
      </div>
      <div className="p-5 sm:p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-1" aria-label={t("Time range")}>
            {(
              [
                [1, "24 hours"],
                [7, "7 days"],
                [30, "30 days"],
              ] as const
            ).map(([value, name]) => (
              <button
                key={value}
                className={`br-btn ${days === value ? "br-btn-primary" : ""}`}
                aria-pressed={days === value}
                onClick={() => setDays(value)}
              >
                {t(name)}
              </button>
            ))}
          </div>
          <p className="text-xs text-fg-muted">
            {data ? `${t("Updated")}: ${formatDateTime(data.observed_at)}` : t("Loading…")}
          </p>
        </div>
        {data ? (
          <ActivityGraph data={data} days={days} tenant={tenant} stale={stale} />
        ) : (
          <p className="py-16 text-center text-fg-muted" role="status">
            {stale
              ? t("Activity is currently unavailable. We will retry automatically.")
              : t("Loading…")}
          </p>
        )}
      </div>
      {history && (
        <ActivityDrawer tenant={tenant} companyName={companyName} close={() => setHistory(false)} />
      )}
    </section>
  );
}
