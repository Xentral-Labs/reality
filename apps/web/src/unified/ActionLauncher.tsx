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
import { api, deliveryApi, type ApplicationReference, type Tenant } from "../api";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { t } from "../localization";
import {
  isActionForm,
  menuEntries,
  type DeliveryAction,
  type DiscoveryEntry,
} from "./actionDiscovery";
import type { Selection } from "./routing";
import { paletteActionPrefill, type PaletteActionTarget } from "./commandPaletteTargets";
import type { PaletteEntry } from "./commandPaletteEntries";
import { usePaletteHistory } from "./usePaletteHistory";
import { CommandPalette } from "./CommandPalette";
import type { PageAction } from "./PageActionBar";
export type { DeliveryAction } from "./actionDiscovery";

export type DiscoveryContext = {
  tenant: string;
  user: string;
  companies: Tenant[];
  switchCompany: (id: string) => void;
  companyName: string;
  selection: Selection;
  data?: ApplicationReference;
  loading: boolean;
  error?: string;
  refresh: () => void;
  open: (tool: DeliveryAction, target?: PaletteActionTarget) => void;
  contextual: PaletteEntry[];
  navigate: (target: Partial<Selection>) => void;
  owner: boolean;
  demo: boolean;
};
const Context = createContext<DiscoveryContext | null>(null);
export function ActionDiscoveryProvider({
  tenant,
  user,
  companies,
  switchCompany,
  companyName,
  selection,
  open,
  navigate,
  owner,
  demo,
  children,
}: {
  tenant: string;
  user: string;
  companies: Tenant[];
  switchCompany: (id: string) => void;
  companyName: string;
  selection: Selection;
  open: DiscoveryContext["open"];
  navigate: DiscoveryContext["navigate"];
  owner: boolean;
  demo: boolean;
  children: ReactNode;
}) {
  const read = useRead(() => api.applicationReference(tenant), [tenant]);
  usePaletteHistory(user, tenant, selection, { owner, demo });
  const selected = useRead(
    () =>
      selection.commitment
        ? deliveryApi.detail(tenant, selection.commitment)
        : Promise.resolve(null),
    [tenant, selection.commitment],
  );
  const detail =
    !selected.loading && !selected.error && selected.data?.case.id === selection.commitment
      ? selected.data.case
      : null;
  const eligible =
    detail && (detail.type === "customer_delivery" || detail.status === "open")
      ? menuEntries(
          read.data,
          detail.type === "customer_delivery" ? "commitment.customer" : "commitment.supplier",
          { owner, demo },
        )
      : [];
  const contextual: PaletteEntry[] = eligible
    .filter(
      (entry) =>
        entry.form &&
        [
          "reserve",
          "movement_create",
          "receipt",
          "commitment_hold",
          "commitment_hold_release",
        ].includes(entry.form),
    )
    .filter(
      (entry) =>
        entry.form !==
        (detail?.blockers.some((blocker) => blocker.scope === "commitment")
          ? "commitment_hold"
          : "commitment_hold_release"),
    )
    .map((entry) => ({
      key: `action:${entry.form}`,
      group: "actions",
      label: `${t(entry.label)} · ${selection.commitment}`,
      aliases: [entry.label],
      references: [selection.commitment],
      outcome: "Open form",
      target: {
        kind: "action",
        id: entry.form as DeliveryAction,
        prefill: paletteActionPrefill(entry.form!, { commitment: selection.commitment }),
      },
    }));

  return (
    <Context.Provider
      value={{
        ...read,
        tenant,
        user,
        companies,
        switchCompany,
        companyName,
        selection,
        open,
        contextual,
        navigate,
        owner,
        demo,
      }}
    >
      {children}
    </Context.Provider>
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
  const [generation, setGeneration] = useState(0);
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
      if (event.isComposing) return;
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
  const menu = (
    <CommandPalette
      key={generation}
      context={context}
      searchRef={search}
      close={() => panel.current?.hidePopover()}
      onLaunch={onLaunch}
    />
  );
  return (
    <div data-action-launcher>
      <button
        type="button"
        className="shell-utility shell-command-trigger"
        aria-label={t("Search or start an action")}
        data-sidebar-tooltip={t("Search or start an action")}
        aria-keyshortcuts="Meta+K Control+K"
        aria-haspopup="dialog"
        popoverTarget={id}
      >
        <Search size={16} />
        <span data-navigation-label>{t("Search")}…</span>
        <kbd data-navigation-label>{t(shortcut)}</kbd>
      </button>
      {createPortal(
        <div
          ref={panel}
          id={id}
          popover="auto"
          role="dialog"
          aria-label={t("Search or start an action")}
          data-action-menu
          className="shell-action-menu"
          onBeforeToggle={(event) => {
            if ((event.nativeEvent as ToggleEvent).newState === "open") {
              returnFocus.current = document.activeElement as HTMLElement | null;
              setGeneration((value) => value + 1);
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
