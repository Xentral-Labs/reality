import { useId, useRef } from "react";
import { Check, ChevronDown } from "lucide-react";
import type { Tenant } from "../api";
import { t } from "../localization";

export function CompanySwitcher({
  company,
  companies,
  switchCompany,
}: {
  company: Tenant;
  companies: Tenant[];
  switchCompany: (id: string) => void;
}) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  return (
    <>
      <button
        ref={trigger}
        type="button"
        aria-label={t("Switch company")}
        aria-describedby={company.sandbox_run_id ? `${id}-sandbox` : undefined}
        data-company-id={company.id}
        popoverTarget={id}
        aria-haspopup="dialog"
        className="company-switcher-trigger flex min-w-0 items-center gap-1.5 rounded-lg hover:bg-surface-muted focus-visible:outline-accent"
        onClick={() => {
          if (!panel.current || !trigger.current) return;
          panel.current.style.left = `${Math.max(8, Math.min(trigger.current.getBoundingClientRect().left, window.innerWidth - 344))}px`;
        }}
      >
        <span className="company-switcher-copy min-w-0 flex-1 text-left">
          {company.sandbox_run_id ? (
            <span
              id={`${id}-sandbox`}
              className="company-switcher-context"
              data-company-context="sandbox"
            >
              {t("Sandbox")}
            </span>
          ) : (
            <span className="company-switcher-context" data-localization="original">
              Reality
            </span>
          )}
          <span className="company-switcher-name" data-localization="original">
            {company.name}
          </span>
        </span>
        <ChevronDown size={15} className="shrink-0 text-fg-muted" />
      </button>
      <div
        ref={panel}
        id={id}
        popover="auto"
        role="dialog"
        aria-label={t("Switch company")}
        className="fixed inset-auto top-[60px] m-0 w-[336px] max-w-[calc(100vw-16px)] overflow-hidden rounded-xl border border-border-default bg-surface p-1.5 text-fg-default shadow-xl backdrop:bg-transparent"
      >
        <p className="px-3 py-2 text-xs font-medium text-fg-muted">{t("Switch company")}</p>
        <div className="max-h-[min(420px,calc(100dvh-120px))] overflow-y-auto">
          {companies.map((row) => (
            <button
              key={row.id}
              type="button"
              data-company-option={row.id}
              aria-pressed={row.id === company.id}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm hover:bg-surface-muted focus-visible:outline-accent aria-pressed:bg-accent-soft"
              onClick={() => {
                panel.current?.hidePopover();
                trigger.current?.focus();
                if (row.id !== company.id) switchCompany(row.id);
              }}
            >
              <span
                data-localization="original"
                className="grid size-9 shrink-0 place-items-center rounded-lg bg-surface-muted font-semibold text-fg-muted"
              >
                {Array.from(row.name.trim())[0]?.toUpperCase() || "?"}
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex min-w-0 items-center gap-2">
                  <span className="min-w-0 break-words font-medium" data-localization="original">
                    {row.name}
                  </span>
                  {row.sandbox_run_id && (
                    <span className="company-sandbox-badge shrink-0">{t("Sandbox")}</span>
                  )}
                </span>
                {row.sandbox_run_id && (
                  <span className="block text-xs text-fg-muted">{t("Practice company")}</span>
                )}
                {companies.some((other) => other.id !== row.id && other.name === row.name) && (
                  <span
                    className="block break-all text-xs text-fg-muted"
                    data-localization="original"
                  >
                    {row.id}
                  </span>
                )}
              </span>
              {row.id === company.id && (
                <Check size={17} className="shrink-0 text-accent" aria-hidden="true" />
              )}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
