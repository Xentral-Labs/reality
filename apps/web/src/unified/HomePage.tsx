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
      {/* What needs a person comes first; the activity overview follows (spec 254). */}
      <HomePulse
        key={`${user}:${tenant}`}
        user={user}
        tenant={tenant}
        lead={
          <div className="grid divide-y divide-border-default border-y border-border-default sm:grid-cols-3 sm:divide-x sm:divide-y-0">
            {dailyWork.map(({ label, total, selection }) => {
              // A decision waiting for a person is the one tile that asks for attention.
              const waiting =
                total === "pending_decisions" && !!data && (data.totals[total] ?? 0) > 0;
              return (
                <button
                  key={label}
                  data-home-work={total}
                  data-waiting={waiting || undefined}
                  className="px-4 py-3 text-left transition-colors hover:bg-surface-muted"
                  onClick={() => navigate(selection)}
                >
                  <p className="text-xs text-fg-muted">{t(label)}</p>
                  <p className="mt-1 min-h-8 text-xl font-medium tabular-nums text-fg-strong">
                    {data && data.totals[total] != null ? (
                      formatNumber(data.totals[total])
                    ) : loading ? (
                      <ReadLine />
                    ) : (
                      "—"
                    )}
                  </p>
                  <p className="mt-1 text-xs text-fg-muted">
                    {t(waiting ? "waiting for you" : "open")}
                  </p>
                </button>
              );
            })}
          </div>
        }
      />
      {!data && !loading && <ReadState error={error} retry={refresh} />}
    </div>
  );
}
