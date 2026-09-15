import { createPortal } from "react-dom";
import { ChatUsage } from "./ChatUsage";
import { AnalyticsReportProposal } from "./analytics/AnalyticsReportProposal";
import { AllowanceNotice, ChatComposer } from "./ChatComposer";
import { History, LoaderCircle, SquarePen, Sparkles } from "lucide-react";
const dockFrame = "reality-chat flex h-full min-h-0 min-w-0 flex-col";
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
import { api, referenceTools, deliveryApi } from "../api";
import { t, formatDateTime } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import type { Selection } from "./routing";

export function ChatPage({
  selection,
  navigate,
  compact = false,
  dock = false,
  active = true,
  initialDraft = "",
  onInitialDraftUsed,
  renderMessageEvidence,
  usageTarget,
}: {
  usageTarget?: HTMLElement | null;
  selection: Selection;
  compact?: boolean;
  dock?: boolean;
  active?: boolean;
  initialDraft?: string;
  onInitialDraftUsed?: () => void;
  renderMessageEvidence?: (messageId: string) => ReactNode;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const composerId = useId();
  const [historyOpen, setHistoryOpen] = useState(false);
  const { data, loading, error, refresh } = useRead(
    () => api.copilot(selection.tenant, selection.session),
    [selection.tenant, selection.session],
  );
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
  }, [data?.messages.length, echo, sending]);
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
  const sessionReady = !selection.session || data?.active_session_id === selection.session;
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
      await api.sendCopilotMessage(
        selection.tenant,
        session,
        text,
        selection.commitment,
        analyticsContext?.definition,
      );
      if (!alive.current) return;
      pendingSend.current = null;
      if (session !== selection.session) navigate({ session });
      else refresh();
    } catch (error) {
      setFailure((error as Error).message);
      setEcho(null);
      setQuestion(text);
    } finally {
      refresh();
      setSending(false);
    }
  };
  if (!data || !sessionReady) return <ReadState loading={loading} error={error} retry={refresh} />;
  const frame = dock ? dockFrame : compact ? compactFrame : fullFrame;
  return (
    <div className={frame}>
      {usageTarget &&
        createPortal(<ChatUsage allowance={data.allowance} navigate={navigate} />, usageTarget)}
      {!dock && !usageTarget && (
        <div className="flex justify-end">
          <ChatUsage allowance={data.allowance} navigate={navigate} />
        </div>
      )}
      {dock && (
        <header className="flex h-16 shrink-0 items-center justify-between gap-2 border-b border-border-default px-4">
          <div className="flex min-w-0 items-center gap-2">
            <Sparkles size={21} className="shrink-0 text-accent" />
            <span className="truncate font-semibold" data-original-content="">
              {data.sessions.find((row) => row.id === data.active_session_id)?.title ||
                t("New chat")}
            </span>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            {!usageTarget && <ChatUsage allowance={data.allowance} navigate={navigate} />}
            <button
              className="reality-chat-icon"
              aria-label={t("Conversation history")}
              aria-expanded={historyOpen}
              onClick={() => setHistoryOpen(!historyOpen)}
            >
              <History size={20} />
            </button>
            <button
              className="reality-chat-icon"
              aria-label={t("New conversation")}
              disabled={sending || startingChat}
              onClick={() => void startConversation()}
            >
              <SquarePen size={20} />
            </button>
          </div>
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
      {dock && historyOpen && !data.sessions.length && (
        <p className="px-4 py-3 text-sm text-fg-muted">{t("No conversations yet.")}</p>
      )}
      {(!dock || historyOpen) && !!data.sessions.length && (
        <label className="flex items-center gap-3 p-3 text-sm">
          {t("Conversation")}
          <select
            aria-label={t("Conversation")}
            className="br-control min-w-0 max-w-sm flex-1"
            value={data.active_session_id || ""}
            disabled={sending || startingChat}
            onChange={(event) => {
              pendingSend.current = null;
              setQuestion("");
              setFailure("");
              setHistoryOpen(false);
              navigate({ session: event.target.value });
            }}
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
        className="min-h-0 w-full max-w-3xl flex-1 self-center space-y-7 overflow-y-auto overscroll-contain px-5 py-6"
        aria-live="polite"
      >
        {!data.messages.length && !echo && (
          <div className="reality-chat-empty rounded-xl border border-border-default bg-surface p-6">
            <p className="mb-3 text-sm text-accent">{"Reality"}</p>
            <h2 className="text-xl font-semibold text-fg-strong">
              {t("What would you like to understand or do?")}
            </h2>
            <p className="mt-3 text-fg-muted">{t("Ask about orders, stock and money.")}</p>
          </div>
        )}
        {[
          ...data.messages,
          ...(echo && !recorded
            ? [{ id: "", role: "user" as const, content: echo.text, created_at: "" }]
            : []),
        ].map((message) => (
          <article
            key={message.id || "echo"}
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
          className="mx-4 mb-3 flex shrink-0 items-center gap-3 rounded-xl border border-accent/30 bg-accent-soft px-4 py-3 text-sm font-semibold text-fg-strong"
        >
          <span
            aria-hidden="true"
            className="grid size-10 shrink-0 place-items-center rounded-xl bg-accent text-white"
          >
            <LoaderCircle
              size={24}
              strokeWidth={2.5}
              className="animate-spin motion-reduce:animate-none"
            />
          </span>
          {t("Reality is working…")}
        </div>
      )}
      {dock && failure && (
        <p role="alert" className="px-4 text-sm text-critical-text">
          {failure}
        </p>
      )}
      {dock ? (
        <ChatComposer
          allowance={data.allowance}
          key={data.active_session_id || "new"}
          id={composerId}
          value={question}
          change={setQuestion}
          sending={sending || startingChat || loading}
          active={active}
          send={() => void send()}
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
    </div>
  );
}
