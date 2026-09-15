import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { Tenant } from "../api";
import { t } from "../localization";
import type { Selection } from "./routing";
import { ChatPage } from "./ChatPage";
import { StorylineChatEvidence } from "./StorylineChatEvidence";

const openSessionsClass =
  "absolute inset-y-0 left-0 z-20 flex w-64 flex-col rounded-xl border border-border-default bg-surface p-3 shadow-xl xl:static xl:z-auto xl:w-60 xl:shrink-0 xl:border-0 xl:bg-transparent xl:shadow-none";
const closedSessionsClass =
  "hidden w-60 shrink-0 flex-col border-r border-border-default p-3 xl:flex";

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
  const closeSessions = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!sessionsOpen) return;
    const previous = document.activeElement;
    closeSessions.current?.focus({ preventScroll: true });
    const dismiss = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSessionsOpen(false);
    };
    document.addEventListener("keydown", dismiss);
    return () => {
      document.removeEventListener("keydown", dismiss);
      if (previous instanceof HTMLElement && previous.isConnected)
        previous.focus({ preventScroll: true });
    };
  }, [sessionsOpen]);
  const [controlsTarget, setControlsTarget] = useState<HTMLDivElement | null>(null);
  const [usageTarget, setUsageTarget] = useState<HTMLDivElement | null>(null);
  const isSandbox =
    company.company_kind === "sandbox" ||
    company.purpose === "playground" ||
    !!company.sandbox_run_id;
  return (
    <div className="relative flex h-full min-h-0 w-full gap-4" data-free-play-layout>
      {sessionsOpen && (
        <button
          className="absolute inset-0 z-10 bg-black/20 xl:hidden"
          aria-label={t("Close")}
          onClick={() => setSessionsOpen(false)}
        />
      )}
      <aside
        data-free-play-sessions
        aria-label={t("Conversation history")}
        className={sessionsOpen ? openSessionsClass : closedSessionsClass}
      >
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold">{t("Conversation history")}</h2>
          <button
            ref={closeSessions}
            className="reality-chat-icon free-play-mobile-control"
            aria-label={t("Close")}
            onClick={() => setSessionsOpen(false)}
          >
            <X size={18} />
          </button>
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
        <header
          className="flex h-12 shrink-0 items-center gap-2 border-b border-border-default px-3"
          data-free-play-toolbar
        >
          <h2 className="text-sm font-medium">{t("Chat")}</h2>
          <div className="ml-auto shrink-0" ref={setUsageTarget} />
          <div className="shrink-0" ref={setControlsTarget} />
        </header>
        {!isSandbox && (
          <p className="px-4 pt-3 text-sm text-fg-muted" data-free-play-real-data>
            {t("You are working with this company's real data. Changes require confirmation.")}
          </p>
        )}
        <ChatPage
          usageTarget={usageTarget}
          controlsTarget={controlsTarget}
          sessionsTarget={sessionsTarget}
          sessionsOpen={sessionsOpen}
          toggleSessions={() => setSessionsOpen((open) => !open)}
          onSessionSelected={() => setSessionsOpen(false)}
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
