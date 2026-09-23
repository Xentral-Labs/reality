import { useEffect, useState, type ReactNode } from "react";
import { TriangleAlert } from "lucide-react";
import { api, type ActivityVolume, type SystemReadiness } from "../api";
import { formatDateTime, t } from "../localization";
import { ActivityGraph } from "./ActivityGraph";

export function HomePulse({
  user,
  tenant,
  lead,
}: {
  user: string;
  tenant: string;
  /** What needs a person comes first, between readiness and the activity graph. */
  lead?: ReactNode;
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
      lead={lead}
      days={days}
      setDays={setDays}
    />
  );
}
function HomePulseBody({
  tenant,
  lead,
  days,
  setDays,
}: {
  tenant: string;
  lead?: ReactNode;
  days: number;
  setDays: (value: number) => void;
}) {
  const [data, setData] = useState<ActivityVolume | null>(null),
    [readiness, setReadiness] = useState<SystemReadiness | null>(null);
  const [stale, setStale] = useState(false),
    [checked, setChecked] = useState(false);
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
  const components = (
    [
      ["connection", "Connection"],
      ["scheduler", "Automatic scheduling"],
      ["worker", "Background processing"],
    ] as const
  ).map(([key, name]) => `${t(name)}: ${label(readiness?.components[key])}`);
  const period = (
    <div className="inbox-local-controls">
      <div className="register-tabs" aria-label={t("Time range")}>
        {(
          [
            [1, "24 hours"],
            [7, "7 days"],
            [30, "30 days"],
          ] as const
        ).map(([value, name]) => (
          <button key={value} aria-pressed={days === value} onClick={() => setDays(value)}>
            {t(name)}
          </button>
        ))}
      </div>
    </div>
  );
  return (
    <section data-home-pulse="" className="min-w-0 space-y-5 text-[13px]">
      {/* Readiness is quiet while everything works and speaks up only when it does not. */}
      {ready || !checked ? (
        <p role="status" className="sr-only">
          {ready ? t("Everything is ready") : t("Checking…")}
        </p>
      ) : (
        <div
          role="status"
          aria-label={t("System status")}
          className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg bg-caution-bg px-3 py-2 text-xs text-caution-text"
        >
          <span className="flex items-center gap-1.5 font-medium">
            <TriangleAlert size={14} className="shrink-0" aria-hidden="true" />
            {t("Availability is not fully confirmed")}
          </span>
          {components.map((text) => (
            <span key={text}>{text}</span>
          ))}
        </div>
      )}
      {lead}
      {data ? (
        <ActivityGraph data={data} days={days} tenant={tenant} stale={stale} controls={period} />
      ) : (
        <div>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <p className="font-medium">{t("Recorded business activity")}</p>
            {period}
          </div>
          <p className="py-16 text-center text-fg-muted" role="status">
            {stale
              ? t("Activity is currently unavailable. We will retry automatically.")
              : t("Loading…")}
          </p>
        </div>
      )}
    </section>
  );
}
