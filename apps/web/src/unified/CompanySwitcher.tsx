import { useEffect, useId, useRef } from "react";
import { Check, ChevronDown, Plus, Settings } from "lucide-react";
import type { Tenant } from "../api";
import { t } from "../localization";
import { selectionUrl, type Selection } from "./routing";

const simulationLabels = {
  running: "Running",
  paused: "Paused",
  stopped: "Stopped",
  disconnected: "Disconnected",
} as const;

export function CompanySwitcher({
  company,
  companies,
  selection,
  navigate,
  switchCompany,
}: {
  company: Tenant;
  companies: Tenant[];
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
  switchCompany: (id: string) => void;
}) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const close = () => panel.current?.hidePopover();
    window.addEventListener("resize", close);
    return () => window.removeEventListener("resize", close);
  }, []);
  return (
    <>
      <button
        ref={trigger}
        type="button"
        aria-label={t("Switch company")}
        aria-describedby={company.sandbox_run_id ? `${id}-sandbox` : undefined}
        data-company-id={company.id}
        data-sidebar-tooltip={company.name}
        popoverTarget={id}
        aria-haspopup="dialog"
        className="company-switcher-trigger flex min-w-0 items-center gap-1.5 rounded-lg hover:bg-surface-muted focus-visible:outline-accent"
        onClick={() => {
          if (!panel.current || !trigger.current) return;
          panel.current.style.top = `${trigger.current.getBoundingClientRect().bottom + 8}px`;
          panel.current.style.left = `${Math.max(8, Math.min(trigger.current.getBoundingClientRect().left, window.innerWidth - 344))}px`;
        }}
      >
        <span className="company-switcher-initial" aria-hidden="true" data-localization="original">
          {Array.from(company.name.trim())[0]?.toUpperCase() || "?"}
        </span>
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
                {row.demo_data_state && (
                  <span className="company-simulation-state" data-simulation={row.demo_data_state}>
                    <span data-simulation-dot aria-hidden="true" />
                    {t("Live simulation")} · {t(simulationLabels[row.demo_data_state])}
                  </span>
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
        <div className="mt-1.5 border-t border-border-default pt-1.5">
          {(
            [
              ["Manage companies", "company", Settings],
              ["New company", "new", Plus],
            ] as const
          ).map(([label, view, Icon]) => {
            const target: Partial<Selection> = {
              route: "settings",
              settingsView: view,
              proposal: "",
              entry: "",
              q: "",
              page: 1,
            };
            return (
              <a
                key={view}
                data-company-management={view}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm hover:bg-surface-muted focus-visible:outline-accent"
                href={selectionUrl({ ...selection, ...target })}
                onClick={(event) => {
                  if (
                    event.button ||
                    event.metaKey ||
                    event.ctrlKey ||
                    event.shiftKey ||
                    event.altKey
                  )
                    return;
                  event.preventDefault();
                  panel.current?.hidePopover();
                  trigger.current?.focus();
                  navigate(target);
                }}
              >
                <Icon size={17} className="shrink-0 text-fg-muted" />
                {t(label)}
              </a>
            );
          })}
        </div>
      </div>
    </>
  );
}
