import { ChevronDown, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, storylineApi, type Bootstrap } from "../api";
import { t } from "../localization";
import { companySelection, type Selection } from "./routing";
import { ChatPage } from "./ChatPage";
import { StorylineChatEvidence } from "./StorylineChatEvidence";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

const openSessionsClass =
  "absolute inset-y-0 left-0 z-20 flex w-60 flex-col rounded-xl border border-border-default bg-surface p-3 shadow-xl xl:static xl:z-auto xl:w-52 xl:shrink-0 xl:border-0 xl:bg-transparent xl:shadow-none";
const closedSessionsClass = "hidden w-52 shrink-0 flex-col p-3 xl:flex";

export function FreePlayPage({
  selection,
  bootstrap,
  navigate,
  openCompany,
}: {
  selection: Selection;
  bootstrap: Bootstrap;
  navigate: (changes: Partial<Selection>) => void;
  openCompany: (data: Bootstrap, id: string, options?: { announce?: boolean }) => void;
}) {
  const { data, loading, error, refresh } = useRead(() => storylineApi.freePlayEntry(), []);
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
  const [picked, setPicked] = useState(selection.tenant);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const selected = bootstrap.tenants.find((company) => company.id === picked);
  const current = bootstrap.tenants.find((company) => company.id === selection.tenant);
  const chatting = selection.freePlayChat && !!current;
  const isSandbox = (company: Bootstrap["tenants"][number]) =>
    company.company_kind === "sandbox" ||
    company.purpose === "playground" ||
    !!company.sandbox_run_id;
  const open = (tenant: string, updated = bootstrap) => {
    if (!updated.tenants.some((company) => company.id === tenant)) return;
    openCompany(updated, tenant, { announce: false });
    navigate({ ...companySelection(selection, tenant), route: "free-play", freePlayChat: true });
  };
  const start = async () => {
    setBusy(true);
    setFailure("");
    try {
      const result = await storylineApi.startFreePlay();
      if (result.status === "ready") open(result.tenant_id, await api.bootstrap());
      else {
        if (result.status !== "archived") setFailure(t("Sandbox setup is not ready. Try again."));
        refresh();
      }
    } catch (error) {
      setFailure((error as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="relative flex h-full min-h-0 w-full gap-4" data-free-play-layout>
      {chatting && (
        <>
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
        </>
      )}
      <section
        className="mx-auto flex h-full min-h-0 min-w-0 w-full max-w-5xl flex-col overflow-hidden rounded-xl border border-border-default bg-surface"
        data-independent-free-play
      >
        {chatting ? (
          <header
            className="flex h-12 shrink-0 items-center gap-2 border-b border-border-default px-3"
            data-free-play-toolbar
          >
            <button
              className="flex min-w-0 flex-1 items-center gap-1 text-left text-sm font-medium"
              data-free-play-choose
              aria-label={t("Choose company")}
              title={`${current.name} · ${t(isSandbox(current) ? "Sandbox" : "Company")}`}
              onClick={() => {
                setPicked(selection.tenant);
                navigate({ freePlayChat: false, session: "" });
              }}
            >
              <span className="truncate" data-original-content>
                {current.name}
              </span>
              <ChevronDown size={14} className="shrink-0 text-fg-muted" />
            </button>
            <div className="shrink-0" ref={setUsageTarget} />
            <div className="shrink-0" ref={setControlsTarget} />
          </header>
        ) : (
          <header className="flex shrink-0 items-center justify-between gap-3 border-b border-border-default p-4">
            <h2 className="font-semibold">{t("Free play")}</h2>
            <button
              className="br-btn"
              onClick={() =>
                navigate({ route: "storyline", storylineChapter: "library", freePlayChat: false })
              }
            >
              {t("Storylines")}
            </button>
          </header>
        )}
        {failure && (
          <p role="alert" className="p-4 text-sm text-critical-text">
            {failure}
          </p>
        )}
        {chatting ? (
          <>
            {!isSandbox(current) && (
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
          </>
        ) : (
          <div className="overflow-y-auto p-6">
            <p className="mb-6 text-fg-muted">
              {t("Choose an existing company or create a Sandbox with sample data.")}
            </p>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="flex flex-col items-start gap-4 rounded-xl border border-border-default p-5">
                <label htmlFor="free-play-company" className="font-semibold">
                  {t("Choose company")}
                </label>
                <select
                  id="free-play-company"
                  data-free-play-company
                  className="w-full min-w-0 rounded-lg border border-border-default bg-surface p-3 text-fg"
                  value={picked}
                  onChange={(event) => setPicked(event.target.value)}
                  disabled={busy}
                >
                  {bootstrap.tenants.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name} · {t(isSandbox(company) ? "Sandbox" : "Company")}
                    </option>
                  ))}
                </select>
                {selected && !isSandbox(selected) && (
                  <p className="text-sm text-fg-muted" data-free-play-real-data>
                    {t(
                      "You are working with this company's real data. Changes require confirmation.",
                    )}
                  </p>
                )}
                <button
                  className="br-btn br-btn-primary"
                  data-free-play-open
                  disabled={!selected || busy}
                  onClick={() => selected && open(selected.id)}
                >
                  {t("Open company chat")}
                </button>
              </div>
              <div className="flex flex-col items-start gap-4 rounded-xl border border-border-default p-5">
                <h3 className="font-semibold">{t("Sandbox with sample data")}</h3>
                <p className="text-sm text-fg-muted">
                  {t("Explore freely in your own Sandbox with sample data.")}
                </p>
                {!data ? (
                  <ReadState loading={loading} error={error} retry={refresh} />
                ) : data.available && data.status === "ready" ? (
                  <button className="br-btn" disabled={busy} onClick={() => open(data.tenant_id)}>
                    {t("Open Free Play Sandbox")}
                  </button>
                ) : data.available && data.status === "archived" ? (
                  <p>{t("This Sandbox is archived. Restore it under Companies.")}</p>
                ) : (
                  <button
                    className="br-btn"
                    disabled={busy || loading}
                    onClick={() => void start()}
                    data-free-play-start
                  >
                    {busy ? t("Loading…") : t("Create Sandbox and start")}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
