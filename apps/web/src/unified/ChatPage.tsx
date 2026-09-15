import type { ChatReply } from "../chatStream";
import { createPortal } from "react-dom";
import { ChatUsage } from "./ChatUsage";
import { AnalyticsReportProposal } from "./analytics/AnalyticsReportProposal";
import { AllowanceNotice, ChatComposer } from "./ChatComposer";
import {
  Archive,
  ArchiveRestore,
  ChevronLeft,
  History,
  LoaderCircle,
  MoreHorizontal,
  SquarePen,
  Sparkles,
  Trash2,
} from "lucide-react";
const emptyMessageClass = "flex flex-col justify-center";
const compactHistoryClass = "reality-chat-icon free-play-mobile-control";
const activeSessionClass = "bg-accent-soft font-medium text-accent";
const inactiveSessionClass = "text-fg-default hover:bg-surface-muted";
const dockFrame = "reality-chat flex h-full min-h-0 min-w-0 flex-col";
const criticalButtonClass = "br-btn br-btn-critical";
const primaryButtonClass = "br-btn br-btn-primary";
import {
  analyticsHash,
  readAnalyticsHandoff,
  validAnalyticsHandoff,
  type AnalyticsHandoff,
  messageContext,
} from "./context";
const compactFrame = "flex h-[min(720px,75dvh)] min-w-0 flex-col gap-4";
const fullFrame = "mx-auto flex h-[calc(100dvh-152px)] min-h-[500px] max-w-5xl flex-col gap-4";
import { useEffect, useRef, useState, useId, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { APIError, api, referenceTools, deliveryApi } from "../api";
import { t, formatDateTime } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import type { Selection } from "./routing";

type RemovableSession = { id: string; title: string; message_count: number };

export function ChatPage({
  selection,
  navigate,
  compact = false,
  dock = false,
  active = true,
  initialDraft = "",
  onInitialDraftUsed,
  renderMessageEvidence,
  controlsTarget,
  newSessionTarget,
  sessionsTarget,
  sessionsOpen,
  toggleSessions,
  onSessionSelected,
}: {
  controlsTarget?: HTMLElement | null;
  newSessionTarget?: HTMLElement | null;
  sessionsTarget?: HTMLElement | null;
  sessionsOpen?: boolean;
  toggleSessions?: () => void;
  onSessionSelected?: () => void;
  selection: Selection;
  compact?: boolean;
  dock?: boolean;
  active?: boolean;
  initialDraft?: string;
  onInitialDraftUsed?: () => void;
  renderMessageEvidence?: (messageId: string) => ReactNode;
  navigate: (changes: Partial<Selection>, options?: { replace?: boolean }) => void;
}) {
  const composerId = useId();
  const [historyOpen, setHistoryOpen] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [changingSession, setChangingSession] = useState(false);
  const [removalSession, setRemovalSession] = useState<RemovableSession | null>(null);
  const { data, loading, error, code, refresh } = useRead(async () => {
    try {
      return await api.copilot(selection.tenant, selection.session, showArchived);
    } catch (error) {
      if (
        selection.session &&
        error instanceof APIError &&
        error.status === 404 &&
        error.message === "ChatSession not found."
      ) {
        throw new APIError(
          error.message,
          error.status,
          `chat_session_missing:${selection.session}`,
        );
      }
      throw error;
    }
  }, [selection.tenant, selection.session, showArchived]);
  const recoveringSession =
    !showArchived && !!selection.session && code === `chat_session_missing:${selection.session}`;
  useEffect(() => {
    if (recoveringSession && selection.session) navigate({ session: "" }, { replace: true });
  }, [recoveringSession, selection.session]);
  useEffect(() => {
    const changed = () => refresh();
    window.addEventListener("reality:ai-usage-changed", changed);
    return () => window.removeEventListener("reality:ai-usage-changed", changed);
  }, []);
  const { data: deliveryContext } = useRead(
    () =>
      selection.commitment
        ? deliveryApi.detail(selection.tenant, selection.commitment)
        : Promise.resolve(null),
    [selection.tenant, selection.commitment],
  );
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  const pendingSend = useRef<{ session: string; text: string; before: string[] } | null>(null);
  const [question, setQuestion] = useState(initialDraft);
  useEffect(() => {
    if (initialDraft) onInitialDraftUsed?.();
  }, []);
  const [analyticsContext, setAnalyticsContext] = useState<AnalyticsHandoff | null>(null);
  const attachedSession = useRef<string | null>(null);
  const creatingSession = useRef(false);
  const [startingChat, setStartingChat] = useState(false);
  useEffect(() => {
    if (attachedSession.current && attachedSession.current !== selection.session) {
      setAnalyticsContext(null);
      attachedSession.current = null;
    }
  }, [selection.session]);
  const openAnalytics = (value: AnalyticsHandoff) => {
    if (!validAnalyticsHandoff(value, selection.tenant)) return;
    navigate({ route: "analytics", analyticsView: "explore", commitment: "" });
    location.hash = analyticsHash(value);
    window.dispatchEvent(new CustomEvent("reality:analytics-handoff", { detail: value }));
  };

  const [sending, setSending] = useState(false);
  const [liveReply, setLiveReply] = useState<{
    session: string;
    text: string;
    result?: ChatReply;
  } | null>(null);
  const visibleReply = liveReply && liveReply.session === selection.session ? liveReply : null;
  useEffect(() => {
    if (
      liveReply?.result &&
      data?.messages.some((row) => row.id === liveReply.result?.assistant.id)
    )
      setLiveReply(null);
  }, [data?.messages, liveReply]);
  const restoreComposerFocus = useRef(false);
  const [failure, setFailure] = useState("");
  /**
   * The question a person just sent, shown as their message until the reload carries it.
   * The ids seen before sending tell a recorded copy apart from earlier messages.
   */
  const [echo, setEcho] = useState<{ text: string; before: string[] } | null>(null);
  const messageList = useRef<HTMLDivElement>(null);
  const recorded =
    !!echo && !!data?.messages.some((row) => row.role === "user" && !echo.before.includes(row.id));
  useEffect(() => {
    if (recorded) setEcho(null);
  }, [recorded]);
  useEffect(() => {
    const list = messageList.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [data?.messages.length, echo, sending, visibleReply?.text]);
  const startConversation = async (analysis: AnalyticsHandoff | null = null) => {
    if (creatingSession.current) return;
    if (sending) {
      setFailure(t("Wait for the current reply before starting a new chat."));
      return;
    }
    creatingSession.current = true;
    setStartingChat(true);
    try {
      const created = await api.createCopilotSession(selection.tenant);
      if (!alive.current) return;
      attachedSession.current = analysis ? created.id : null;
      setAnalyticsContext(analysis);
      pendingSend.current = null;
      setEcho(null);
      setQuestion("");
      setFailure("");
      setHistoryOpen(false);
      navigate({ session: created.id, commitment: "" });
    } catch (error) {
      if (alive.current) setFailure((error as Error).message);
    } finally {
      creatingSession.current = false;
      if (alive.current) setStartingChat(false);
    }
  };
  useEffect(() => {
    const receive = (event: Event) => {
      const value = (event as CustomEvent).detail;
      if (validAnalyticsHandoff(value, selection.tenant))
        void startConversation(structuredClone(value));
    };
    window.addEventListener("reality:open-chat", receive);
    return () => window.removeEventListener("reality:open-chat", receive);
  }, [selection.tenant, sending, navigate]);
  useEffect(() => {
    if (!data?.allowance) return;
    const delay = Math.max(1000, new Date(data.allowance.resets_at).getTime() - Date.now() + 1000);
    const timer = window.setTimeout(refresh, Math.min(delay, 86401000));
    return () => window.clearTimeout(timer);
  }, [data?.allowance?.resets_at]);
  const sessionReady =
    showArchived || !selection.session || data?.active_session_id === selection.session;
  useEffect(() => {
    if (!restoreComposerFocus.current || sending || startingChat || loading || !sessionReady)
      return;
    const input = document.getElementById(composerId) as HTMLTextAreaElement | null;
    if (!input) return;
    restoreComposerFocus.current = false;
    const focused = document.activeElement;
    if (active && (focused === document.body || input.form?.contains(focused)))
      input.focus({ preventScroll: true });
  }, [sending, startingChat, loading, sessionReady, active, composerId]);
  const send = async () => {
    const text = question;
    if (
      data?.allowance?.remaining === 0 ||
      !text.trim() ||
      sending ||
      creatingSession.current ||
      !sessionReady ||
      loading
    )
      return;
    restoreComposerFocus.current = true;
    setSending(true);
    setFailure("");
    setEcho({ text, before: data?.messages.map((row) => row.id) || [] });
    setQuestion("");
    try {
      if (pendingSend.current) {
        const pending = pendingSend.current;
        const recovered = await api.copilot(selection.tenant, pending.session);
        if (!alive.current) return;
        if (
          recovered.messages.some(
            (row) =>
              row.role === "user" &&
              !pending.before.includes(row.id) &&
              messageContext(row.content).text === pending.text,
          )
        ) {
          pendingSend.current = null;
          setQuestion("");
          navigate({ session: pending.session });
          refresh();
          return;
        }
      }
      const session =
        pendingSend.current?.session ||
        data?.active_session_id ||
        (await api.createCopilotSession(selection.tenant)).id;
      if (!alive.current) return;
      pendingSend.current = {
        session,
        text,
        before: data?.messages.map((row) => row.id) || [],
      };
      navigate({ session });
      setLiveReply({ session, text: "" });
      const result = await api.sendCopilotMessage(
        selection.tenant,
        session,
        text,
        selection.commitment,
        analyticsContext?.definition,
        (event) => {
          if (!alive.current) return;
          if (event.type === "reset") setLiveReply({ session, text: "" });
          else if (event.type === "delta")
            setLiveReply((previous) => ({
              session,
              text: (previous?.session === session ? previous.text : "") + event.text,
            }));
        },
      );
      if (!alive.current) return;
      pendingSend.current = null;
      setLiveReply({ session, text: result.assistant.content, result });
      setEcho(null);
      if (session !== selection.session) navigate({ session });
    } catch (error) {
      setFailure((error as Error).message);
      setLiveReply(null);
      setEcho(null);
      setQuestion(text);
    } finally {
      refresh();
      setSending(false);
    }
  };
  if (recoveringSession) return <ReadState loading />;
  if (!data || !sessionReady)
    return (
      <div>
        <ReadState loading={loading} error={error} retry={refresh} />
        {error && selection.session && (
          <button className="br-btn m-4" onClick={() => navigate({ session: "" })}>
            {t("Back to chats")}
          </button>
        )}
      </div>
    );
  const selectSession = (session: string) => {
    pendingSend.current = null;
    setQuestion("");
    setFailure("");
    setHistoryOpen(false);
    onSessionSelected?.();
    navigate({ session });
  };
  const removeSession = async (row: RemovableSession) => {
    setChangingSession(true);
    setFailure("");
    try {
      await api.deleteCopilotSession(selection.tenant, row.id);
      setRemovalSession(null);
      if (selection.session === row.id || data.active_session_id === row.id)
        navigate({ session: "" }, { replace: true });
      refresh();
    } catch (error) {
      setFailure((error as Error).message);
    } finally {
      setChangingSession(false);
    }
  };
  const restoreSession = async (row: { id: string }) => {
    setChangingSession(true);
    setFailure("");
    try {
      await api.restoreCopilotSession(selection.tenant, row.id);
      setShowArchived(false);
      navigate({ session: row.id }, { replace: true });
    } catch (error) {
      setFailure((error as Error).message);
    } finally {
      setChangingSession(false);
    }
  };
  const chatControls = (
    <div className="flex shrink-0 items-center gap-1">
      {!sessionsTarget && <ChatUsage allowance={data.allowance} navigate={navigate} />}
      <button
        className={sessionsTarget ? compactHistoryClass : "reality-chat-icon"}
        aria-label={t("Conversation history")}
        aria-expanded={sessionsTarget ? sessionsOpen : historyOpen}
        onClick={() => (sessionsTarget ? toggleSessions?.() : setHistoryOpen(!historyOpen))}
      >
        <History size={20} />
      </button>
      {!sessionsTarget && (
        <button
          className="reality-chat-icon"
          aria-label={t("New conversation")}
          disabled={sending || startingChat}
          onClick={() => void startConversation()}
        >
          <SquarePen size={20} />
        </button>
      )}
    </div>
  );
  const frame = dock ? dockFrame : compact ? compactFrame : fullFrame;
  return (
    <div className={frame}>
      {sessionsTarget &&
        createPortal(
          <div className="flex h-full min-h-0 flex-col" data-chat-session-list>
            {showArchived ? (
              <button
                className="br-btn mb-3 w-full justify-start gap-2"
                onClick={() => {
                  setShowArchived(false);
                  navigate({ session: "" }, { replace: true });
                }}
              >
                <ChevronLeft size={18} />
                {t("Back to chats")}
              </button>
            ) : null}
            <div className="min-h-0 flex-1 space-y-1 overflow-y-auto overscroll-contain xl:space-y-0">
              {!data.sessions.length && (
                <p className="text-sm text-fg-muted">
                  {t(showArchived ? "No archived chats" : "No conversations yet.")}
                </p>
              )}
              {data.sessions.map((row) => (
                <div key={row.id} className="group flex min-w-0 items-center gap-1">
                  <button
                    data-chat-session={row.id}
                    aria-current={row.id === data.active_session_id ? "true" : undefined}
                    className={`min-w-0 flex-1 truncate rounded-lg px-3 py-2.5 text-left text-sm xl:py-2 ${row.id === data.active_session_id ? activeSessionClass : inactiveSessionClass}`}
                    title={row.title}
                    disabled={sending || startingChat || changingSession}
                    onClick={() => selectSession(row.id)}
                  >
                    <span data-original-content>{row.title}</span>
                  </button>
                  {showArchived ? (
                    <button
                      className="reality-chat-icon shrink-0"
                      data-chat-session-restore={row.id}
                      aria-label={t("Restore chat")}
                      title={t("Restore chat")}
                      disabled={sending || startingChat || changingSession}
                      onClick={() => void restoreSession(row)}
                    >
                      <ArchiveRestore size={17} />
                    </button>
                  ) : (
                    <details
                      className="chat-session-options relative shrink-0"
                      data-chat-session-menu={row.id}
                    >
                      <summary
                        className="reality-chat-icon list-none cursor-pointer"
                        aria-label={t("More options")}
                        title={t("More options")}
                      >
                        <MoreHorizontal size={18} />
                      </summary>
                      <div className="absolute right-0 z-20 mt-1 min-w-48 rounded-lg border border-border-default bg-surface p-1 shadow-lg">
                        <button
                          className="flex w-full items-center gap-2 whitespace-nowrap rounded-md px-3 py-2 text-left text-sm hover:bg-surface-muted"
                          data-chat-session-delete={row.message_count === 0 ? row.id : undefined}
                          data-chat-session-archive={row.message_count === 0 ? undefined : row.id}
                          disabled={sending || startingChat || changingSession}
                          onClick={() => setRemovalSession(row)}
                        >
                          {row.message_count === 0 ? (
                            <Trash2 size={17} className="shrink-0" />
                          ) : (
                            <Archive size={17} className="shrink-0" />
                          )}
                          {t(row.message_count === 0 ? "Delete chat" : "Archive chat")}
                        </button>
                      </div>
                    </details>
                  )}
                </div>
              ))}
            </div>
            {!showArchived && data.has_archived && (
              <button
                className="mt-3 flex w-full shrink-0 items-center gap-2 border-t border-border-default px-3 pt-3 text-left text-sm text-fg-muted hover:text-fg-default"
                data-chat-archive-entry
                onClick={() => {
                  setShowArchived(true);
                  navigate({ session: "" }, { replace: true });
                }}
              >
                <Archive size={17} />
                {t("Archived chats")}
              </button>
            )}
          </div>,
          sessionsTarget,
        )}
      {newSessionTarget &&
        createPortal(
          <button
            className="reality-chat-icon"
            data-new-chat-action
            aria-label={t("New chat")}
            title={t("New chat")}
            disabled={sending || startingChat}
            onClick={() => {
              setShowArchived(false);
              onSessionSelected?.();
              void startConversation();
            }}
          >
            <SquarePen size={18} />
          </button>,
          newSessionTarget,
        )}
      {!dock && (
        <div className="flex justify-end">
          <ChatUsage allowance={data.allowance} navigate={navigate} />
        </div>
      )}
      {controlsTarget && createPortal(chatControls, controlsTarget)}
      {dock && !controlsTarget && (
        <header className="flex h-16 shrink-0 items-center justify-between gap-2 border-b border-border-default px-4">
          <div className="flex min-w-0 items-center gap-2">
            <Sparkles size={21} className="shrink-0 text-accent" />
            <span className="truncate font-semibold" data-original-content="">
              {data.sessions.find((row) => row.id === data.active_session_id)?.title ||
                t("New chat")}
            </span>
          </div>
          {chatControls}
        </header>
      )}
      {!compact && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          {!dock && (
            <div>
              <p className="mb-2 text-xs uppercase tracking-widest text-fg-muted">
                {t("Ask Reality")}
              </p>
              <h1 className="text-2xl font-semibold text-fg-strong">
                {t("One conversation across your business.")}
              </h1>
            </div>
          )}
          <button
            className="br-btn"
            disabled={sending || startingChat}
            onClick={() => void startConversation()}
          >
            {t("New conversation")}
          </button>
        </div>
      )}
      {analyticsContext && (
        <div className="m-3 flex items-center justify-between gap-2 rounded-lg bg-accent-soft p-3 text-xs">
          <button onClick={() => openAnalytics(analyticsContext)}>
            {t("Attached analysis")} · {analyticsContext.definition.dataset}
          </button>
          <button className="br-btn" onClick={() => setAnalyticsContext(null)}>
            {t("Remove")}
          </button>
        </div>
      )}
      {selection.commitment && (
        <button
          className="br-btn self-start"
          onClick={() => navigate({ route: "orders-deliveries", ordersView: "deliveries" })}
        >
          {t("Selected delivery")}
          {deliveryContext &&
            ` · ${deliveryContext.case.counterparty} · ${deliveryContext.case.item}`}
        </button>
      )}
      {!sessionsTarget && dock && historyOpen && !data.sessions.length && (
        <p className="px-4 py-3 text-sm text-fg-muted">{t("No conversations yet.")}</p>
      )}
      {!sessionsTarget && (!dock || historyOpen) && !!data.sessions.length && (
        <label className="flex items-center gap-3 p-3 text-sm">
          {t("Conversation")}
          <select
            aria-label={t("Conversation")}
            className="br-control min-w-0 max-w-sm flex-1"
            value={data.active_session_id || ""}
            disabled={sending || startingChat}
            onChange={(event) => selectSession(event.target.value)}
          >
            {data.sessions.map((row) => (
              <option key={row.id} value={row.id}>
                {row.title}
              </option>
            ))}
          </select>
        </label>
      )}
      <div
        ref={messageList}
        data-chat-messages
        className={`min-h-0 w-full max-w-3xl flex-1 self-center space-y-7 overflow-y-auto overscroll-contain px-5 py-6 ${sessionsTarget && !data.messages.length && !echo && !visibleReply ? emptyMessageClass : ""}`}
        aria-live="polite"
      >
        {!data.messages.length && !echo && !visibleReply && (
          <div className="reality-chat-empty rounded-xl border border-border-default bg-surface p-6">
            <p className="mb-3 text-sm text-accent">{"Reality"}</p>
            <h2 className="text-xl font-semibold text-fg-strong">
              {t("What would you like to understand or do?")}
            </h2>
            <p className="mt-3 text-fg-muted">{t("Ask about orders, stock and money.")}</p>
            <div data-chat-starters className="mt-5 flex flex-col items-start gap-2">
              {[
                t("Which customer orders are still open?"),
                t("Which items have insufficient stock for open orders?"),
                t("Which customer invoices are overdue?"),
              ].map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="min-h-11 max-w-full rounded-xl border border-border-default bg-surface px-4 py-2 text-left text-sm text-fg-strong transition-colors hover:border-accent hover:bg-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-default disabled:opacity-50"
                  disabled={!!question || sending || startingChat || loading}
                  onClick={() => {
                    setQuestion(prompt);
                    document.getElementById(composerId)?.focus();
                  }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}
        {[
          ...data.messages,
          ...(visibleReply?.result
            ? [
                { ...visibleReply.result.user, role: "user" as const, created_at: "" },
                { ...visibleReply.result.assistant, role: "assistant" as const, created_at: "" },
              ].filter((row) => !data.messages.some((saved) => saved.id === row.id))
            : []),
          ...(echo && !recorded
            ? [{ id: "", role: "user" as const, content: echo.text, created_at: "" }]
            : []),
          ...(visibleReply?.text && !visibleReply.result
            ? [{ id: "", role: "assistant" as const, content: visibleReply.text, created_at: "" }]
            : []),
        ].map((message) => (
          <article
            key={message.id || `pending-${message.role}`}
            data-chat-pending={message.id ? undefined : ""}
            data-chat-role={message.role}
            className="reality-chat-message"
          >
            <p className="sr-only">
              {message.role === "user" ? t("You") : "Reality"}{" "}
              {message.created_at && (
                <time className="ml-2">{formatDateTime(message.created_at)}</time>
              )}
            </p>
            {messageContext(message.content).analytics && (
              <button
                className="mb-3 text-xs text-accent underline"
                onClick={() => openAnalytics(messageContext(message.content).analytics!)}
              >
                {t("Open in Reports")}
              </button>
            )}
            {messageContext(message.content).context && (
              <button
                className="mb-3 text-xs text-accent underline"
                onClick={() =>
                  navigate({
                    route: "orders-deliveries",
                    ordersView: "deliveries",
                    commitment: messageContext(message.content).context!.id,
                  })
                }
              >
                {t("Selected delivery")} · {messageContext(message.content).context!.label}
              </button>
            )}
            <div data-original-content className="space-y-3 overflow-x-auto break-words">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                skipHtml
                disallowedElements={["img"]}
                components={{
                  a: ({ children, href }) => {
                    if (href?.startsWith("/app/analytics?")) {
                      const link = new URL(href, location.origin);
                      const handoff = readAnalyticsHandoff(link.hash, selection.tenant);
                      if (link.searchParams.get("tenant") === selection.tenant && handoff)
                        return (
                          <button
                            className="text-accent underline"
                            onClick={() => openAnalytics(handoff)}
                          >
                            {children}
                          </button>
                        );
                    }
                    if (href?.startsWith("/app/work?")) {
                      const link = new URL(href, location.origin);
                      if (
                        link.searchParams.get("tenant") === selection.tenant &&
                        link.searchParams.get("commitment")
                      )
                        return (
                          <button
                            className="text-accent underline"
                            onClick={() =>
                              navigate({
                                route: "orders-deliveries",
                                ordersView: "deliveries",
                                commitment: link.searchParams.get("commitment")!,
                              })
                            }
                          >
                            {children}
                          </button>
                        );
                    }
                    return <span>{children}</span>;
                  },
                }}
              >
                {messageContext(message.content).text}
              </ReactMarkdown>
            </div>
            {message.id && message.role === "assistant" && renderMessageEvidence?.(message.id)}
          </article>
        ))}
        {data.proposals.map((proposal) =>
          proposal.tool === "analytics.reports.change" ? (
            <AnalyticsReportProposal
              key={proposal.id}
              tenant={selection.tenant}
              id={proposal.id}
              refresh={refresh}
            />
          ) : (
            <button
              key={proposal.id}
              className="br-btn self-start"
              onClick={() => {
                if (proposal.input.import_file) {
                  navigate({ route: "data-sources", proposal: "", importProposal: proposal.id });
                } else if (referenceTools.includes(proposal.tool)) {
                  navigate({ route: "master-data", proposal: proposal.id });
                } else if (
                  proposal.tool === "party_delivery_hold" ||
                  proposal.tool === "party_delivery_hold_release" ||
                  proposal.tool === "reserve" ||
                  proposal.tool === "reservation_release" ||
                  proposal.tool === "commitment_hold" ||
                  proposal.tool === "commitment_hold_release" ||
                  proposal.tool === "ledger_reverse" ||
                  proposal.tool === "movement_correct" ||
                  proposal.tool === "order_create" ||
                  (proposal.tool === "sales_credit_record" && !!proposal.input.invoice_id) ||
                  proposal.tool === "sales_invoice_record" ||
                  proposal.tool === "supplier_invoice_record" ||
                  proposal.tool === "customer_refund_post" ||
                  proposal.tool === "customer_payment_post" ||
                  proposal.tool === "supplier_payment_post" ||
                  (proposal.tool === "movement_create" &&
                    proposal.input.movement_type === "opening_stock") ||
                  (proposal.tool === "movement_create" &&
                    ["shipment", "receipt"].includes(String(proposal.input.movement_type)) &&
                    proposal.input.commitment_id)
                )
                  navigate({ route: "decisions", proposal: proposal.id });
                else navigate({ route: "decisions", proposal: "" });
              }}
            >
              {t("Review proposed changes")} · {proposal.tool}
            </button>
          ),
        )}
      </div>
      {sending && (
        <div
          role="status"
          data-chat-working
          className="mx-auto mb-2 flex w-full max-w-4xl shrink-0 items-center gap-2 px-4 text-sm text-fg-muted"
        >
          <LoaderCircle
            aria-hidden="true"
            size={16}
            strokeWidth={2}
            className="shrink-0 animate-spin text-accent motion-reduce:animate-none"
          />
          {t("Reality is working…")}
        </div>
      )}
      {dock && failure && (
        <p role="alert" className="px-4 text-sm text-critical-text">
          {failure}
        </p>
      )}
      {showArchived ? (
        <p className="shrink-0 border-t border-border-default px-4 py-3 text-sm text-fg-muted">
          {t("Archived — read only")}
        </p>
      ) : dock && sessionsTarget && data.allowance?.remaining === 0 ? (
        <div
          role="status"
          data-free-play-limit
          className="flex shrink-0 flex-wrap items-center justify-center gap-x-2 gap-y-1 border-t border-border-default px-4 py-4 text-sm text-fg-muted"
        >
          <span className="font-medium text-fg-default">{t("Daily limit reached")}</span>
          <button
            className="text-accent underline"
            onClick={() => navigate({ route: "settings", settingsView: "usage" })}
          >
            {t("View usage")}
          </button>
          <span>
            · {t("Resets at")} {formatDateTime(data.allowance.resets_at)}
          </span>
        </div>
      ) : dock ? (
        <ChatComposer
          allowance={data.allowance}
          key={data.active_session_id || "new"}
          id={composerId}
          value={question}
          change={setQuestion}
          sending={sending || startingChat || loading}
          active={active}
          send={() => void send()}
          disclaimerAction={<ChatUsage inline allowance={data.allowance} navigate={navigate} />}
        />
      ) : (
        <form
          className="rounded-xl border border-accent bg-surface p-4"
          onSubmit={(event) => {
            event.preventDefault();
            void send();
          }}
        >
          <AllowanceNotice allowance={data.allowance} />
          <label className="mb-3 block text-sm text-fg-muted" htmlFor={composerId}>
            {t("Ask about your company")}
          </label>
          <textarea
            id={composerId}
            className="br-control min-h-24 w-full resize-y"
            value={question}
            disabled={sending || startingChat}
            onChange={(event) => setQuestion(event.target.value)}
          />
          {failure && (
            <p role="alert" className="mt-3 text-critical-text">
              {failure}
            </p>
          )}
          <div className="mt-4 flex justify-end">
            <button
              className="br-btn br-btn-primary"
              disabled={
                data.allowance?.remaining === 0 ||
                sending ||
                startingChat ||
                loading ||
                !question.trim()
              }
            >
              {t("Send question")}
            </button>
          </div>
        </form>
      )}
      {removalSession && (
        <ChatRemovalDialog
          row={removalSession}
          busy={changingSession}
          close={() => setRemovalSession(null)}
          confirm={() => void removeSession(removalSession)}
        />
      )}
    </div>
  );
}

function ChatRemovalDialog({
  row,
  busy,
  close,
  confirm,
}: {
  row: RemovableSession;
  busy: boolean;
  close: () => void;
  confirm: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const empty = row.message_count === 0;
  const title = empty ? t("Delete chat") : t("Archive chat");
  const description = empty
    ? t("This empty chat has no messages. It will be permanently deleted and cannot be restored.")
    : t("This chat will move to Archived chats. You can restore it later.");
  const confirmClass = empty ? criticalButtonClass : primaryButtonClass;
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const node = dialog.current;
    node?.showModal();
    return () => {
      node?.close();
      trigger?.focus();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      aria-labelledby={titleId}
      data-chat-removal-dialog
      className="m-auto w-[min(440px,calc(100vw-2rem))] rounded-2xl border border-border-default bg-surface p-6 text-fg-default shadow-xl backdrop:bg-black/40"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
    >
      <h2 id={titleId} className="text-lg font-semibold text-fg-strong">
        {title}
      </h2>
      <p className="mt-3 text-sm leading-6 text-fg-muted">{description}</p>
      <div className="mt-6 flex justify-end gap-3">
        <button type="button" className="br-btn" disabled={busy} onClick={close}>
          {t("Cancel")}
        </button>
        <button type="button" className={confirmClass} disabled={busy} onClick={confirm}>
          {title}
        </button>
      </div>
    </dialog>
  );
}
