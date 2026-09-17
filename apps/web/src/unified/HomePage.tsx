import { TrialTasks } from "./FreePlayground";
import { dailyWork } from "./dailyWork";
import { HomePulse } from "./HomePulse";
import { ArrowRight, Sparkles } from "lucide-react";
import { api } from "../api";
import { formatNumber, t } from "../localization";
import type { Selection } from "./routing";
import { ReadLine, ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

export function HomePage({
  user,
  tenant,
  companyName,
  navigate,
}: {
  user: string;
  tenant: string;
  companyName: string;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const { data, loading, error, refresh } = useRead(() => api.dashboard(tenant), [tenant]);
  return (
    <div className="mx-auto max-w-[1500px] space-y-7">
      <TrialTasks tenant={tenant} navigate={navigate} />
      <section className="rounded-xl border border-accent bg-surface p-7">
        <p className="mb-4 flex items-center gap-2 text-xs uppercase tracking-wide text-fg-muted">
          <Sparkles size={16} />
          {t("Current recorded position")}
        </p>
        <h2 className="text-xl font-semibold text-fg-strong">
          {!data || data.totals.open_deliveries ? t("Your open work") : t("No open commitments")}
        </h2>
        <p className="my-4 text-fg-muted">
          {t("Open a case to understand the position and its supporting records.")}
        </p>
        <div className="flex flex-wrap gap-3">
          <button
            className="br-btn br-btn-primary"
            onClick={() =>
              navigate({
                route: "orders-deliveries",
                ordersView: "commitments",
                deliveryType: "customer_delivery",
                deliveryStatus: "open",
                commitment: "",
                order: "",
                q: "",
                page: 1,
              })
            }
          >
            {t("Review commitments")}
            <ArrowRight size={16} />
          </button>
          <button className="br-btn" onClick={() => navigate({ route: "copilot" })}>
            {t("Discuss with Reality")}
          </button>
        </div>
      </section>
      <div className="grid gap-4 sm:grid-cols-3">
        {dailyWork.map(({ label, total, selection }) => (
          <button
            key={label}
            className="rounded-xl border border-border-default bg-surface p-6 text-left hover:border-accent"
            onClick={() => navigate(selection)}
          >
            <p className="text-sm text-fg-muted">{t(label)}</p>
            <p className="mt-3 min-h-9 text-3xl font-semibold text-fg-strong">
              {data ? formatNumber(data.totals[total]) : loading ? <ReadLine /> : "—"}
            </p>
            <p className="mt-1 text-xs text-fg-muted">{t("open")}</p>
          </button>
        ))}
      </div>
      <HomePulse key={`${user}:${tenant}`} user={user} tenant={tenant} companyName={companyName} />
      {!data && !loading && <ReadState error={error} retry={refresh} />}
      <button
        className="br-btn"
        onClick={() => navigate({ route: "analytics", analyticsView: "graph", page: 1 })}
      >
        {t("Open analytics")}
        <ArrowRight size={16} />
      </button>
      <section className="rounded-xl border border-border-default bg-surface p-6">
        <h2 className="text-xl font-semibold text-fg-strong">{t("Decisions & control")}</h2>
        <p className="my-4 text-fg-muted">
          {t("Review each proposed change before it is recorded.")}
        </p>
        <button className="br-btn" onClick={() => navigate({ route: "decisions" })}>
          {t("Review decisions")}
        </button>
      </section>
    </div>
  );
}
