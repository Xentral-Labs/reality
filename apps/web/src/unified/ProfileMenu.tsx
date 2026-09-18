import { languageHref } from "../../../shared/language";
import { useEffect, useId, useRef, useState } from "react";
import {
  BookOpen,
  ChevronUp,
  ExternalLink,
  Globe,
  LogOut,
  Settings,
  UserRound,
} from "lucide-react";
import { api, type AuthUser } from "../api";
import { t } from "../localization";
import { selectionUrl, type Selection } from "./routing";

export function ProfileMenu({
  user,
  selection,
  navigate,
  closeNavigation,
}: {
  user: AuthUser;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
  closeNavigation: () => void;
}) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [error, setError] = useState(false);
  useEffect(() => {
    const close = () => panel.current?.hidePopover();
    window.addEventListener("resize", close);
    return () => window.removeEventListener("resize", close);
  }, []);
  const itemClass =
    "flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-left text-sm hover:bg-surface-muted focus-visible:outline-accent";
  const personal = {
    ...selection,
    route: "settings" as const,
    settingsView: "personal" as const,
    proposal: "",
    q: "",
    page: 1,
  };
  async function signOut() {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError(false);
    try {
      await api.logout();
      sessionStorage.removeItem("reality.app.return");
      sessionStorage.removeItem("reality.playground.return");
      location.assign("/login");
    } catch {
      setError(true);
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }
  return (
    <div
      className="sticky bottom-0 mt-auto shrink-0 border-t border-border-default bg-surface pt-2"
      data-profile-menu
    >
      <button
        ref={trigger}
        type="button"
        aria-label={t("My account")}
        data-sidebar-tooltip={t("My account")}
        aria-haspopup="dialog"
        popoverTarget={id}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left hover:bg-surface-muted focus-visible:outline-accent"
        onClick={() => {
          if (!panel.current || !trigger.current) return;
          const rect = trigger.current.getBoundingClientRect();
          panel.current.style.left = `${Math.max(8, Math.min(rect.left, innerWidth - 280))}px`;
          panel.current.style.maxHeight = `${Math.max(100, rect.top - 16)}px`;
          panel.current.style.bottom = `${Math.max(8, innerHeight - rect.top + 8)}px`;
        }}
      >
        <span className="grid size-8 shrink-0 place-items-center rounded-full bg-accent-soft text-accent">
          <UserRound size={17} />
        </span>
        <span data-profile-label className="min-w-0 flex-1">
          <span className="block text-[13px] font-medium">{t("My account")}</span>
        </span>
        <ChevronUp data-profile-chevron size={15} className="shrink-0 text-fg-muted" />
      </button>
      <div
        ref={panel}
        id={id}
        popover="auto"
        role="dialog"
        aria-label={t("My account")}
        className="fixed inset-auto m-0 w-[272px] max-w-[calc(100vw-16px)] max-h-[calc(100dvh-100px)] overflow-y-auto rounded-xl border border-border-default bg-surface p-1.5 text-fg-default shadow-xl backdrop:bg-transparent"
      >
        <div className="border-b border-border-default px-3 py-2.5">
          <p className="break-all text-sm text-fg-muted" data-localization="original">
            {user.email}
          </p>
        </div>
        <a
          className={itemClass}
          href={selectionUrl(personal)}
          onClick={(event) => {
            event.preventDefault();
            panel.current?.hidePopover();
            trigger.current?.focus();
            navigate(personal);
            closeNavigation();
          }}
        >
          <Settings size={17} />
          {t("Account settings")}
        </a>
        {(
          [
            ["Documentation", __DOCS_URL__, BookOpen],
            ["Reality website", __SITE_URL__, Globe],
          ] as const
        ).map(([label, url, Icon]) => (
          <a
            key={label}
            className={itemClass}
            href={languageHref(url, user.language, label === "Documentation")}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Icon size={17} />
            {t(label)}
            <ExternalLink size={13} className="ml-auto shrink-0 text-fg-muted" />
          </a>
        ))}
        <div className="mt-1 border-t border-border-default pt-1">
          {error && (
            <p role="alert" className="px-3 py-2 text-sm text-critical-text">
              {t("Could not sign out. Please try again.")}
            </p>
          )}
          <button
            type="button"
            className={itemClass}
            disabled={busy}
            onClick={() => void signOut()}
          >
            <LogOut size={17} />
            {t(busy ? "Signing out…" : "Sign out")}
          </button>
        </div>
      </div>
    </div>
  );
}
