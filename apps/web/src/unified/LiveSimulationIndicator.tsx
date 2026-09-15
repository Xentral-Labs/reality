import { useEffect, useState } from "react";
import { api, type Tenant } from "../api";
import { t } from "../localization";
import { selectionUrl, type Selection } from "./routing";

export function LiveSimulationIndicator({
  company,
  selection,
  navigate,
}: {
  company: Tenant;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const [running, setRunning] = useState(false);
  useEffect(() => {
    if (company.role !== "owner" || company.purpose !== "playground") return;
    let disposed = false;
    let controller: AbortController | undefined;
    let refreshAgain = false;
    async function refresh() {
      if (disposed || document.hidden) return;
      if (controller) {
        refreshAgain = true;
        return;
      }
      controller = new AbortController();
      const timeout = window.setTimeout(() => controller?.abort(), 8000);
      try {
        const status = await api.demoDataStatus(
          `/api/tenants/${encodeURIComponent(company.id)}/demo-data`,
          controller.signal,
        );
        if (!disposed && !document.hidden)
          setRunning(
            status.state === "running" &&
              (!status.derived_state || status.derived_state === "running"),
          );
      } catch {
        if (!disposed) setRunning(false);
      } finally {
        window.clearTimeout(timeout);
        controller = undefined;
        if (refreshAgain && !disposed) {
          refreshAgain = false;
          void refresh();
        }
      }
    }
    const changed = (event: Event) => {
      if ((event as CustomEvent<{ tenantId: string }>).detail?.tenantId === company.id)
        void refresh();
    };
    const visible = () => {
      if (document.hidden) {
        controller?.abort();
        setRunning(false);
      } else void refresh();
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    document.addEventListener("visibilitychange", visible);
    window.addEventListener("reality:demo-data-changed", changed);
    return () => {
      disposed = true;
      controller?.abort();
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", visible);
      window.removeEventListener("reality:demo-data-changed", changed);
    };
  }, [company.id, company.role, company.purpose]);
  if (!running || company.role !== "owner" || company.purpose !== "playground") return null;
  const target: Partial<Selection> = { route: "demo-data", page: 1, q: "" };
  return (
    <a
      data-live-simulation
      className="live-simulation-link"
      href={selectionUrl({ ...selection, ...target })}
      aria-label={t("Live simulation")}
      title={t("Live simulation")}
      aria-current={selection.route === "demo-data" ? "page" : undefined}
      onClick={(event) => {
        if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
          return;
        event.preventDefault();
        navigate(target);
      }}
    >
      <span data-live-dot aria-hidden="true" />
      <span className="live-simulation-label">{t("Live simulation")}</span>
    </a>
  );
}
