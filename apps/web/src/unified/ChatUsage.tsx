import { useId, useRef } from "react";
import { api, type ManagedAllowance } from "../api";
import { t, formatDateTime } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import type { Selection } from "./routing";

function UsageDetails({ allowance }: { allowance: ManagedAllowance }) {
  return (
    <div className="space-y-3 text-sm" data-usage-details>
      <p className="font-medium text-fg-strong">{t("Included AI questions")}</p>
      <p>
        {t("{used} of {limit} used")
          .replace("{used}", String(allowance.used))
          .replace("{limit}", String(allowance.limit))}
      </p>
      <progress
        className="h-2 w-full accent-accent"
        value={allowance.used}
        max={Math.max(1, allowance.limit)}
        aria-label={t("Usage")}
      />
      <p>
        {t("{remaining} of {limit} AI questions left")
          .replace("{remaining}", String(allowance.remaining))
          .replace("{limit}", String(allowance.limit))}
      </p>
      <p className="text-xs text-fg-muted">
        {t("Resets at")} {formatDateTime(allowance.resets_at)}
      </p>
    </div>
  );
}

export function ChatUsage({
  allowance,
  navigate,
}: {
  allowance?: ManagedAllowance | null;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  if (!allowance) return null;
  return (
    <div data-chat-usage>
      <button
        type="button"
        popoverTarget={id}
        aria-haspopup="dialog"
        className="whitespace-nowrap rounded-full border border-border-default px-3 py-1.5 text-xs text-fg-muted hover:bg-surface-muted hover:text-fg-strong"
        onClick={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          if (panel.current) {
            panel.current.style.left = `${Math.max(8, Math.min(rect.right - 288, innerWidth - 296))}px`;
            panel.current.style.top = `${rect.bottom + 8}px`;
          }
        }}
      >
        {t("Usage")} · {t("{remaining} left").replace("{remaining}", String(allowance.remaining))}
      </button>
      <div
        ref={panel}
        id={id}
        popover="auto"
        role="dialog"
        aria-label={t("Usage")}
        className="fixed m-0 w-72 max-w-[calc(100vw-1rem)] rounded-xl border border-border-default bg-surface p-4 text-fg-strong shadow-xl"
      >
        <UsageDetails allowance={allowance} />
        <button
          className="br-btn mt-4 w-full"
          onClick={() => {
            panel.current?.hidePopover();
            navigate({ route: "settings", settingsView: "usage" });
          }}
        >
          {t("View usage")}
        </button>
      </div>
    </div>
  );
}

export function UsageSettings({ tenant }: { tenant: string }) {
  const { data, loading, error, refresh } = useRead(() => api.copilot(tenant), [tenant]);
  if (!data) return <ReadState loading={loading} error={error} retry={refresh} />;
  return (
    <section className="max-w-md" data-usage-settings>
      {data.allowance ? (
        <UsageDetails allowance={data.allowance} />
      ) : (
        <p className="text-sm text-fg-muted">
          {t("No included AI allowance is active for this company.")}
        </p>
      )}
    </section>
  );
}
