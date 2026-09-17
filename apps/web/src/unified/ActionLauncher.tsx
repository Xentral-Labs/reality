import { Search } from "lucide-react";
import { createPortal } from "react-dom";
import {
  createContext,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api, type ApplicationReference } from "../api";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { t } from "../localization";
import {
  entryGroup,
  isActionForm,
  menuEntries,
  type DeliveryAction,
  type DiscoveryEntry,
} from "./actionDiscovery";
import type { Selection } from "./routing";
import type { PageAction } from "./PageActionBar";
export type { DeliveryAction } from "./actionDiscovery";

type DiscoveryContext = {
  data?: ApplicationReference;
  loading: boolean;
  error?: string;
  refresh: () => void;
  open: (tool: DeliveryAction) => void;
  navigate: (target: Partial<Selection>) => void;
  owner: boolean;
  demo: boolean;
};
const Context = createContext<DiscoveryContext | null>(null);
export function ActionDiscoveryProvider({
  tenant,
  open,
  navigate,
  owner,
  demo,
  children,
}: {
  tenant: string;
  open: DiscoveryContext["open"];
  navigate: DiscoveryContext["navigate"];
  owner: boolean;
  demo: boolean;
  children: ReactNode;
}) {
  const read = useRead(() => api.applicationReference(tenant), [tenant]);
  return (
    <Context.Provider value={{ ...read, open, navigate, owner, demo }}>{children}</Context.Provider>
  );
}
export function useActionDiscovery() {
  return useContext(Context);
}
function launch(entry: DiscoveryEntry, context: DiscoveryContext, element: HTMLElement) {
  // Dismiss the launcher before invoking the existing shared action path.
  element.closest<HTMLElement>("[popover]")?.hidePopover();
  if (entry.form && isActionForm(entry.form)) context.open(entry.form);
  else if (entry.destination)
    context.navigate({
      ...entry.destination,
      q: "",
      entry: "",
      record: "",
      commitment: "",
      proposal: "",
      page: 1,
    });
}
// Page-level actions for one placement, in catalog order, ready for the shared PageActionBar.
// Nothing until the discovery read has data; the global launcher reports its failure.
export function useContextActions(
  placement: string,
  options: { onOpen?: (form: DeliveryAction) => void; exclude?: string[] } = {},
): PageAction[] {
  const context = useActionDiscovery();
  if (!context?.data) return [];
  const launcher = options.onOpen ? { ...context, open: options.onOpen } : context;
  return menuEntries(context.data, placement, context)
    .filter((entry) => !(options.exclude || []).includes(entry.form || ""))
    .map((entry) => ({
      key: entry.key,
      label: entry.label,
      onClick: (element) => launch(entry, launcher, element),
    }));
}
export function ContextActions({
  context: placement,
  onOpen,
  exclude = [],
}: {
  context: string;
  onOpen?: (form: DeliveryAction) => void;
  exclude?: string[];
}) {
  const context = useActionDiscovery();
  if (!context) return null;
  if (!context.data)
    return <ReadState loading={context.loading} error={context.error} retry={context.refresh} />;
  return (
    <>
      {menuEntries(context.data, placement, context)
        .filter((e) => !exclude.includes(e.form || ""))
        .map((e) => (
          <button
            key={e.key}
            className="br-btn"
            onClick={(event) =>
              launch(e, onOpen ? { ...context, open: onOpen } : context, event.currentTarget)
            }
          >
            {t(e.label)}
          </button>
        ))}
    </>
  );
}
export function ActionLauncher({ onLaunch }: { onLaunch: () => void }) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const [query, setQuery] = useState("");
  const shortcut = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘ K" : "Ctrl K";
  useEffect(() => {
    const close = () => panel.current?.hidePopover();
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === "Escape" && panel.current?.matches(":popover-open")) {
        event.preventDefault();
        event.stopPropagation();
        panel.current.hidePopover();
        returnFocus.current?.focus();
        return;
      }
      if (
        !(event.metaKey || event.ctrlKey) ||
        event.altKey ||
        event.shiftKey ||
        event.key.toLowerCase() !== "k"
      )
        return;
      if (document.querySelector("dialog[open], [aria-modal='true']")) return;
      event.preventDefault();
      if (event.repeat) return;
      panel.current?.togglePopover();
      if (panel.current?.matches(":popover-open")) search.current?.focus();
      else returnFocus.current?.focus();
    };
    window.addEventListener("resize", close);
    window.addEventListener("keydown", keyboard);
    return () => {
      window.removeEventListener("resize", close);
      window.removeEventListener("keydown", keyboard);
    };
  }, []);
  const context = useActionDiscovery();
  if (!context) return null;
  const { data, loading, error, refresh } = context;
  const entries = menuEntries(data, "global", context);
  const categories = data?.discovery?.categories || [];
  const q = query.trim().toLocaleLowerCase();
  const grouped = categories
    .map((c) => ({
      ...c,
      entries: entries.filter((e) => {
        const group = entryGroup(data!, e);
        const subgroup = c.groups.find((g) => g.key === group);
        return (
          subgroup &&
          `${t(c.label)} ${t(subgroup.label)} ${t(e.label)} ${e.command || ""}`
            .toLocaleLowerCase()
            .includes(q)
        );
      }),
    }))
    .filter((c) => c.entries.length);
  const openEntry = (entry: DiscoveryEntry, element: HTMLElement) => {
    launch(entry, context, element);
    onLaunch();
  };
  const menu = (
    <>
      <input
        className="br-control mb-3 w-full"
        type="search"
        ref={search}
        autoFocus
        aria-label={t("Search actions")}
        placeholder={t("Search actions")}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {!data && <ReadState loading={loading} error={error} retry={refresh} />}
      {grouped.map((c) => (
        <section key={c.key} className="mb-3" aria-label={t(c.label)}>
          <h3 className="px-3 py-2 text-xs font-semibold text-fg-muted">{t(c.label)}</h3>
          {c.entries.map((e) => (
            <button
              aria-label={t(e.label)}
              key={e.key}
              className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-surface-muted"
              onClick={(event) => openEntry(e, event.currentTarget)}
            >
              {t(e.label)}
              {e.destination && <span aria-hidden="true"> ↗</span>}
            </button>
          ))}
        </section>
      ))}
      {data && !grouped.length && (
        <p role="status" className="p-3 text-sm text-fg-muted">
          {t("No matching records")}
        </p>
      )}
      <button
        className="br-btn w-full"
        onClick={(e) =>
          openEntry(
            {
              key: "catalog",
              label: "Available actions",
              placements: [],
              destination: { route: "inspector", inspectorView: "commands" },
            },
            e.currentTarget,
          )
        }
      >
        {t("Available actions")}
      </button>
    </>
  );
  return (
    <div data-action-launcher>
      <button
        type="button"
        className="shell-utility shell-command-trigger"
        aria-label={t("Search actions")}
        data-sidebar-tooltip={t("Search actions")}
        aria-keyshortcuts="Meta+K Control+K"
        aria-haspopup="dialog"
        popoverTarget={id}
      >
        <Search size={16} />
        <span data-navigation-label>{t("Search actions")}</span>
        <kbd data-navigation-label>{t(shortcut)}</kbd>
      </button>
      {createPortal(
        <div
          ref={panel}
          id={id}
          popover="auto"
          role="dialog"
          aria-label={t("Actions")}
          data-action-menu
          className="shell-action-menu"
          onBeforeToggle={(event) => {
            if ((event.nativeEvent as ToggleEvent).newState === "open") {
              returnFocus.current = document.activeElement as HTMLElement | null;
              setQuery("");
            }
          }}
          onToggle={(event) => {
            if ((event.nativeEvent as ToggleEvent).newState === "open") search.current?.focus();
            else if (
              document.activeElement === document.body ||
              panel.current?.contains(document.activeElement)
            )
              returnFocus.current?.focus();
          }}
        >
          {menu}
        </div>,
        document.body,
      )}
    </div>
  );
}
