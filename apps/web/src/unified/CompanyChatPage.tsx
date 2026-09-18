import { X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { Tenant } from "../api";
import { t } from "../localization";
import type { Selection } from "./routing";
import { ChatPage } from "./ChatPage";
import { StorylineChatEvidence } from "./StorylineChatEvidence";

const openSessionsClass =
  "absolute right-3 top-0 z-20 flex max-h-[min(32rem,calc(100%-4rem))] w-80 max-w-[calc(100%-1.5rem)] flex-col rounded-xl border border-border-default bg-surface p-3 shadow-xl";

export function CompanyChatPage({
  selection,
  company,
  navigate,
}: {
  selection: Selection;
  company: Tenant;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const [sessionsTarget, setSessionsTarget] = useState<HTMLDivElement | null>(null);
  const [sessionsOpen, setSessionsOpen] = useState(false);
  const [history, setHistory] = useState<{
    tenant: string;
    available: boolean;
  } | null>(null);
  const available = history?.tenant === selection.tenant && history.available;
  const reportHistory = useCallback(
    (available: boolean) => {
      setHistory((previous) =>
        previous?.tenant === selection.tenant
          ? previous.available === available
            ? previous
            : { ...previous, available }
          : { tenant: selection.tenant, available },
      );
    },
    [selection.tenant],
  );
  useEffect(() => {
    if (!available) setSessionsOpen(false);
  }, [available, selection.tenant]);
  useEffect(() => setSessionsOpen(false), [selection.tenant]);
  const closeSessions = useRef<HTMLButtonElement>(null);
  const historyPanel = useRef<HTMLElement>(null);
  const historyTrigger = useRef<HTMLElement | null>(null);
  const dismissHistory = () => {
    setSessionsOpen(false);
    historyTrigger.current?.focus({ preventScroll: true });
  };
  useEffect(() => {
    if (!sessionsOpen) return;
    historyTrigger.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    closeSessions.current?.focus({ preventScroll: true });
    const dismiss = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !document.querySelector("dialog[open]")) dismissHistory();
    };
    const outside = (event: PointerEvent) => {
      if (document.querySelector("dialog[open]")) return;
      if (
        event.target instanceof Node &&
        !historyPanel.current?.contains(event.target) &&
        !historyTrigger.current?.contains(event.target)
      )
        setSessionsOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", dismiss);
    return () => {
      document.removeEventListener("keydown", dismiss);
      document.removeEventListener("pointerdown", outside);
    };
  }, [sessionsOpen]);
  const isSandbox =
    company.company_kind === "sandbox" ||
    company.purpose === "playground" ||
    !!company.sandbox_run_id;
  return (
    <div className="relative flex h-full min-h-0 w-full" data-free-play-layout>
      <aside
        ref={historyPanel}
        data-free-play-sessions
        aria-label={t("Conversation history")}
        className={available && sessionsOpen ? openSessionsClass : "hidden"}
      >
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold">{t("Conversation history")}</h2>
          <div className="flex items-center gap-1">
            <button
              ref={closeSessions}
              className="reality-chat-icon"
              aria-label={t("Close")}
              onClick={dismissHistory}
            >
              <X size={18} />
            </button>
          </div>
        </div>
        <div
          ref={setSessionsTarget}
          className="min-h-0 flex-1 overflow-y-auto overscroll-contain"
        />
      </aside>
      <section
        className="flex h-full min-h-0 min-w-0 w-full flex-col overflow-hidden bg-surface"
        data-independent-free-play
      >
        {!isSandbox && (
          <p className="px-4 pt-3 text-sm text-fg-muted" data-free-play-real-data>
            {t("You are working with this company's real data. Changes require confirmation.")}
          </p>
        )}
        <ChatPage
          standaloneActions
          sessionsTarget={sessionsTarget}
          sessionsOpen={sessionsOpen}
          onHistoryAvailability={reportHistory}
          standaloneHistoryAvailable={!!available}
          toggleSessions={() => {
            setSessionsOpen((open) => !open);
          }}
          onSessionSelected={() => {
            setSessionsOpen(false);
          }}
          key={selection.tenant}
          selection={{ ...selection, commitment: "" }}
          navigate={navigate}
          dock
          compact
          renderMessageEvidence={(messageId) => (
            <StorylineChatEvidence
              key={messageId}
              tenant={selection.tenant}
              messageId={messageId}
              navigate={navigate}
            />
          )}
        />
      </section>
    </div>
  );
}
