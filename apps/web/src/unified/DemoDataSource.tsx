import { useEffect, useState } from "react";
import { AlertTriangle, FlaskConical } from "lucide-react";
import { api, type DemoDataStatus, type Tenant } from "../api";
import { formatDateTime, t } from "../localization";
import { sourceNeedsAttention, stallCause, stallHeadline } from "../components/demoDataSummary";
import { selectionUrl, type Selection } from "./routing";

const stateLabels: Record<string, string> = {
  running: "Running",
  paused: "Paused",
  stopped: "Stopped",
  disconnected: "Disconnected",
  not_connected: "Not connected",
  suspended: "Waiting to resume",
  overdue: "No arrivals",
  error: "Execution needs attention",
  throttled: "Paused: resolve failed imports",
};

/** A company that may run the simulation: practice companies and the demo company. */
export function hasDemoDataSource(company: Tenant): boolean {
  return !!(
    company.demo_data_state ||
    company.sandbox_run_id ||
    company.company_kind === "sandbox" ||
    company.company_kind === "demo"
  );
}

/**
 * The simulation writes orders into the company like any connected system, so it belongs
 * beside the other integrations instead of carrying its own place in the navigation.
 */
/**
 * The live state of this company's simulation, read from the same service the
 * simulation page uses. One read, so the card and the source row cannot disagree.
 */
export function useDemoDataStatus(companyId: string): DemoDataStatus | null {
  const [status, setStatus] = useState<DemoDataStatus | null>(null);
  useEffect(() => {
    if (!companyId) return;
    let disposed = false;
    const controller = new AbortController();
    async function refresh() {
      try {
        const next = await api.demoDataStatus(
          `/api/tenants/${encodeURIComponent(companyId)}/demo-data`,
          controller.signal,
        );
        if (!disposed) setStatus(next);
      } catch {
        // The surface falls back to the state the company carries in the bootstrap.
      }
    }
    const changed = (event: Event) => {
      if ((event as CustomEvent<{ tenantId: string }>).detail?.tenantId === companyId)
        void refresh();
    };
    void refresh();
    window.addEventListener("reality:demo-data-changed", changed);
    return () => {
      disposed = true;
      controller.abort();
      window.removeEventListener("reality:demo-data-changed", changed);
    };
  }, [companyId]);
  return status;
}

export function DemoDataSource({
  company,
  selection,
  navigate,
}: {
  company: Tenant;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const status = useDemoDataStatus(company.id);
  const state = status?.state || company.demo_data_state || "not_connected";
  const derived = status?.derived_state;
  const attention = sourceNeedsAttention(derived);
  const running = state === "running" && (!derived || derived === "running");
  // A stalled source says so here, so that nobody has to open it to find out.
  const badgeState = attention ? derived : running ? "running" : state;
  const target: Partial<Selection> = {
    route: "demo-data",
    entry: "",
    proposal: "",
    q: "",
    page: 1,
  };
  return (
    <section
      data-demo-data-source
      aria-label={t("Demo data simulation")}
      className="mb-4 rounded-xl border border-border-default bg-surface p-5 sm:p-6"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent">
            <FlaskConical size={18} />
          </span>
          <div className="min-w-0">
            <h3 className="font-semibold">{t("Demo data simulation")}</h3>
            <p className="mt-1 text-sm text-fg-muted">
              {t("Generated orders arrive in this company like data from a connected system.")}
            </p>
          </div>
        </div>
        <span
          className="demo-live-badge"
          data-state={badgeState}
          data-demo-attention={attention || undefined}
        >
          {attention && (
            <AlertTriangle size={13} aria-hidden className="mr-1 inline align-[-2px]" />
          )}
          {t(stateLabels[badgeState || state] || "Not connected")}
        </span>
      </div>
      {status?.stall && (
        <p className="mt-4 text-sm text-fg-muted" data-demo-source-stall={status.stall.kind}>
          <strong>{t(stallHeadline(status.stall))}</strong> {t(stallCause(status.stall.code))}
          {status.stall.recovery_at
            ? ` ${t("Next attempt")}: ${formatDateTime(status.stall.recovery_at)}.`
            : ""}
        </p>
      )}
      <p className="mt-4 text-sm">
        {status && state !== "not_connected"
          ? `${status.rate} ${t("orders per hour")} · ${t("Last successful import")}: ${
              status.last_success ? formatDateTime(status.last_success) : "—"
            }`
          : t(
              "Connect the simulation to watch orders, deliveries and payments arrive by themselves.",
            )}
      </p>
      <a
        data-demo-data-open
        className="br-btn mt-4 inline-flex"
        href={selectionUrl({ ...selection, ...target })}
        onClick={(event) => {
          if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
            return;
          event.preventDefault();
          navigate(target);
        }}
      >
        {t(state === "not_connected" ? "Connect demo data" : "Open simulation")}
      </a>
    </section>
  );
}
