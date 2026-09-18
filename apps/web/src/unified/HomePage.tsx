import { dailyWork } from "./dailyWork";
import { HomePulse } from "./HomePulse";
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
    <div className="mx-auto max-w-[1500px] space-y-5 text-[13px]">
      <HomePulse key={`${user}:${tenant}`} user={user} tenant={tenant} companyName={companyName} />
      <div className="grid divide-y divide-border-default border-t border-border-default sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        {dailyWork.map(({ label, total, selection }) => (
          <button
            key={label}
            className="px-4 py-3 text-left transition-colors hover:bg-surface-muted"
            onClick={() => navigate(selection)}
          >
            <p className="text-xs text-fg-muted">{t(label)}</p>
            <p className="mt-1 min-h-8 text-xl font-medium tabular-nums text-fg-strong">
              {data ? formatNumber(data.totals[total]) : loading ? <ReadLine /> : "—"}
            </p>
            <p className="mt-1 text-xs text-fg-muted">{t("open")}</p>
          </button>
        ))}
      </div>
      {!data && !loading && <ReadState error={error} retry={refresh} />}
    </div>
  );
}
