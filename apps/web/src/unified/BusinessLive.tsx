import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { api } from "../api";
import { formatNumber, formatDateTime, t } from "../localization";
import { Inspector } from "./Inspector";

export type BusinessOrder = {
  document_id: string;
  number: string;
  source_record_id: string | null;
  party_name: string;
  received_at: string | null;
  first_dispatch_minutes: number | null;
  complete_dispatch_minutes: number | null;
  due_at: string | null;
  open_units: string;
  age_minutes: number | null;
  flags: string[];
  commitment_ids: string[];
};
export type BusinessOperations = {
  goods_flow_last_hour: {
    item_id: string;
    name: string;
    sku: string;
    received: string;
    shipped: string;
  }[];
  replenishment: {
    commitment_id: string;
    document_id: string;
    item_name: string;
    quantity: string;
    due_at: string | null;
  }[];
  open_replenishment_lines: number;
  local_unread_messages: number;
  pending_decisions: number;
  oldest_open_order_minutes: number | null;
  bottleneck: string;
  recent_documents: {
    id: string;
    number: string;
    type: string;
    party_name: string;
    amount: string | null;
    currency: string;
  }[];
  mailbox_counts: { incoming: number; waiting: number; outgoing: number };
  messages: {
    source_record_id: string;
    subject: string;
    body: string;
    direction: string;
    recorded_at: string;
    reply_recorded?: boolean | null;
    replies?: { source_record_id: string; subject: string; body: string; recorded_at: string }[];
    original?: {
      source_record_id: string;
      subject: string;
      body: string;
      recorded_at: string;
    } | null;
  }[];
  observed_at: string;
  orders: BusinessOrder[];
  order_count: number;
  eligible_orders: number;
  complete_dispatch_orders: number;
  ready_orders: number;
  blocked_orders: number;
  inventory: {
    item_id: string;
    name: string;
    physical: string;
    reserved: string;
    available: string;
    incoming: string;
  }[];
  reservation_blocked_orders: number;
  held_orders: number;
  overdue_orders: number;
  at_risk_orders: number;
  partial_orders: number;
  unshipped_orders: number;
  orders_received_last_hour: number;
  orders_completed_last_hour: number;
  dispatch_rate_percent: number | null;
  average_first_dispatch_minutes: number | null;
  average_complete_dispatch_minutes: number | null;
  complete_dispatch_sample_orders: number;
  first_dispatch_sample_orders: number;
};

export function BusinessLive({ tenant }: { tenant: string }) {
  const [data, setData] = useState<BusinessOperations | null>(null);
  const [failed, setFailed] = useState(false);
  const [filter, setFilter] = useState("");
  const [loadedFilter, setLoadedFilter] = useState("");
  const [tab, setTab] = useState("overview");
  const [mailListOpen, setMailListOpen] = useState(false);
  const [mailFilter, setMailFilter] = useState("incoming");
  const [loadedMailFilter, setLoadedMailFilter] = useState("");
  const [mail, setMail] = useState<BusinessOperations["messages"][number] | null>(null);
  const panelId = useId();
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  useEffect(() => {
    let disposed = false,
      busy = false;
    let controller: AbortController | null = null;
    const read = async () => {
      if (busy) return;
      busy = true;
      controller = new AbortController();
      const timeout = window.setTimeout(() => controller?.abort(), 15000);
      try {
        const value = await api.businessOperations(tenant, controller.signal, filter, mailFilter);
        if (!disposed) {
          setData(value);
          setLoadedFilter(filter);
          setLoadedMailFilter(mailFilter);
          setFailed(false);
        }
      } catch {
        if (!disposed) setFailed(true);
      } finally {
        window.clearTimeout(timeout);
        busy = false;
      }
    };
    void read();
    const timer = window.setInterval(() => void read(), 5000);
    return () => {
      disposed = true;
      controller?.abort();
      window.clearInterval(timer);
    };
  }, [tenant, filter, mailFilter]);
  if (!data)
    return <p role="status">{failed ? t("Business data could not be loaded.") : t("Loading…")}</p>;
  const metrics: [string, number, string][] = [
    ["Ready to dispatch", data.ready_orders, "ready"],
    ["Blocked orders", data.blocked_orders, "blocked"],
    ["Missing reservations", data.reservation_blocked_orders, "reservation_blocked"],
    ["Delivery on hold", data.held_orders, "held"],
    ["At risk", data.at_risk_orders, "at_risk"],
    ["Overdue", data.overdue_orders, "overdue"],
    ["Completely dispatched", data.complete_dispatch_orders, "complete"],
    ["Partially dispatched", data.partial_orders, "partial"],
    ["Not yet dispatched", data.unshipped_orders, "unshipped"],
  ];
  const labels: Record<string, string> = Object.fromEntries(
    metrics.map(([label, , flag]) => [flag, label]),
  );
  Object.assign(labels, {
    eligible: "Complete dispatch share",
    received_last_hour: "Orders",
    completed_last_hour: "Completely dispatched",
    first_dispatch_sample: "First dispatch",
    complete_dispatch_sample: "Complete dispatch",
  });
  const tabs = [
    ["overview", "Overview"],
    ["orders", "Orders"],
    ["stock", "Inventory"],
    ["flow", "Goods flow"],
    ["replenishment", "Replenishment"],
    ["messages", "Messages"],
    ["documents", "Business documents"],
  ];
  const duration = (value: number | null) =>
    value === null ? "—" : `${formatNumber(value)} ${t("min")}`;
  const activeTone = "border-accent bg-accent-soft";
  const inactiveTone = "border-border-subtle bg-surface";
  const orders = data.orders.filter((o) => !filter || o.flags.includes(filter));
  const orderContent = (
    <>
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{filter ? t(labels[filter] || "Orders") : t("Orders")}</h3>
      </div>
      <p className="text-xs text-fg-muted">
        {t(
          "Company-wide counts; the oldest 200 orders are available below. Dispatch is not customer arrival.",
        )}
      </p>
      <div className="overflow-auto rounded-lg border border-border-subtle">
        <table className="w-full text-left text-sm" data-business-orders>
          <thead className="bg-surface-muted">
            <tr>
              {[
                "Order",
                "Customer",
                "Status",
                "Age",
                "Due",
                "First dispatch",
                "Complete dispatch",
              ].map((label) => (
                <th className="p-3" key={label}>
                  {t(label)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.document_id} className="border-t border-border-subtle">
                <td className="p-3">
                  <button
                    className="text-accent"
                    onClick={() => {
                      setFilter("");
                      setTarget({ kind: "document", id: o.document_id });
                    }}
                  >
                    {o.number}
                  </button>
                  <button
                    className="ml-2 text-xs text-fg-muted"
                    disabled={!o.source_record_id}
                    onClick={() =>
                      o.source_record_id &&
                      (() => {
                        setFilter("");
                        setTarget({ kind: "source_record", id: o.source_record_id });
                      })()
                    }
                  >
                    {t("Source")}
                  </button>
                </td>
                <td className="p-3" data-original-content>
                  {o.party_name}
                </td>
                <td className="p-3">
                  {o.flags
                    .filter((flag) => metrics.some((m) => m[2] === flag))
                    .map((flag) => t(labels[flag]))
                    .join(" · ")}
                </td>
                <td className="p-3 whitespace-nowrap">{duration(o.age_minutes)}</td>
                <td className="p-3 whitespace-nowrap">
                  {o.due_at ? formatDateTime(o.due_at) : "—"}
                </td>
                <td className="p-3 whitespace-nowrap">
                  {duration(o.first_dispatch_minutes ?? null)}
                </td>
                <td className="p-3 whitespace-nowrap">
                  {duration(o.complete_dispatch_minutes ?? null)}
                </td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr>
                <td colSpan={7} className="p-6 text-fg-muted">
                  {t("No matching orders.")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
  const mailContent = (
    <section className="rounded-xl border border-border-subtle p-4">
      <div className="mb-3 flex flex-wrap gap-2" aria-label={t("Recent correspondence")}>
        {[
          ["incoming", "Incoming"],
          ["waiting", "Awaiting reply (simulator)"],
          ["outgoing", "Outgoing"],
        ].map(([key, label]) => (
          <button
            key={key}
            aria-pressed={mailFilter === key}
            onClick={() => setMailFilter(key)}
            className={`rounded-lg border px-3 py-2 ${mailFilter === key ? activeTone : inactiveTone}`}
          >
            {t(label)} ·{" "}
            {data.mailbox_counts
              ? formatNumber(data.mailbox_counts[key as keyof BusinessOperations["mailbox_counts"]])
              : "—"}
          </button>
        ))}
      </div>
      <p className="mb-3 text-xs text-fg-muted">
        {t(
          "Latest 50 matching messages. Waiting means a simulator request without a recorded reply; acknowledgement alone is not an answer.",
        )}
      </p>
      {loadedMailFilter !== mailFilter ? (
        <p role="status">{failed ? t("Business data could not be loaded.") : t("Loading…")}</p>
      ) : (
        <div className="overflow-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr>
                {["Direction", "Subject", "Reply", "Date"].map((label) => (
                  <th key={label} className="p-2">
                    {t(label)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.messages.map((m) => (
                <tr key={m.source_record_id} className="border-t border-border-subtle">
                  <td className="p-2">
                    {["incoming", "inbound"].includes(m.direction) ? t("Incoming") : t("Outgoing")}
                  </td>
                  <td className="p-2">
                    <button
                      className="text-accent text-left"
                      onClick={() => {
                        setMailListOpen(false);
                        setMail(m);
                      }}
                      data-original-content
                    >
                      {m.subject}
                    </button>
                  </td>
                  <td className="p-2">
                    {m.reply_recorded === true
                      ? t("Reply recorded")
                      : m.reply_recorded === false
                        ? t("Awaiting reply (simulator)")
                        : "—"}
                  </td>
                  <td className="p-2 whitespace-nowrap">{formatDateTime(m.recorded_at)}</td>
                </tr>
              ))}
              {data.messages.length === 0 && (
                <tr>
                  <td colSpan={4} className="p-6 text-fg-muted">
                    {t("No messages.")}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
  return (
    <section className="space-y-4 py-3" data-business-live>
      <div
        className="flex gap-2 overflow-x-auto border-b border-border-subtle pb-2"
        role="tablist"
        aria-label={t("Business flow")}
      >
        {tabs.map(([key, label], index) => (
          <button
            key={key}
            id={`${panelId}-${key}`}
            role="tab"
            aria-selected={tab === key}
            aria-controls={`${panelId}-panel`}
            tabIndex={tab === key ? 0 : -1}
            onClick={() => setTab(key)}
            onKeyDown={(e) => {
              const next =
                e.key === "ArrowRight"
                  ? (index + 1) % tabs.length
                  : e.key === "ArrowLeft"
                    ? (index + tabs.length - 1) % tabs.length
                    : e.key === "Home"
                      ? 0
                      : e.key === "End"
                        ? tabs.length - 1
                        : -1;
              if (next >= 0) {
                e.preventDefault();
                setTab(tabs[next][0]);
                e.currentTarget.parentElement
                  ?.querySelectorAll<HTMLButtonElement>("[role=tab]")
                  [next]?.focus();
              }
            }}
            className={`shrink-0 rounded-lg px-3 py-2 text-sm ${tab === key ? activeTone : inactiveTone}`}
          >
            {t(label)}
          </button>
        ))}
      </div>
      <div
        role="tabpanel"
        id={`${panelId}-panel`}
        aria-labelledby={`${panelId}-${tab}`}
        className="space-y-4"
      >
        {tab !== "overview" && (
          <p className="text-xs text-fg-muted">
            {t("Updated")}: {formatDateTime(data.observed_at)}
            {failed && (
              <span role="status">
                {" "}
                · {t("Refresh failed. Showing the last recorded snapshot.")}
              </span>
            )}
          </p>
        )}
        {tab === "overview" && (
          <>
            <div className="rounded-xl border border-border-subtle bg-surface-muted p-5">
              <div className="flex flex-wrap justify-between gap-2">
                <h2 className="text-lg font-semibold">{t("Business flow")}</h2>
                <span className="text-xs text-fg-muted">
                  {t("Updated")}: {formatDateTime(data.observed_at)}
                </span>
              </div>
              {failed && (
                <p role="status" className="text-caution-text">
                  {t("Refresh failed. Showing the last recorded snapshot.")}
                </p>
              )}
              <p className="mt-3 text-base font-semibold">
                {t(
                  data.bottleneck === "dispatch"
                    ? "Bottleneck: ready orders are waiting for dispatch."
                    : data.bottleneck === "blocked"
                      ? "Bottleneck: open orders are blocked."
                      : "No open dispatch backlog recorded.",
                )}
              </p>
              <p className="mt-2 text-sm">
                {t("Awaiting decisions")}: {formatNumber(data.pending_decisions)} ·{" "}
                {t("Oldest open order")}: {duration(data.oldest_open_order_minutes)}
              </p>
              <p className="mt-3 text-sm">
                {t("Ready to dispatch")}: <strong>{formatNumber(data.ready_orders)}</strong> ·{" "}
                {t("Missing reservations")}:{" "}
                <strong>{formatNumber(data.reservation_blocked_orders)}</strong> ·{" "}
                {t("Delivery on hold")}: <strong>{formatNumber(data.held_orders)}</strong>
              </p>
              <p className="mt-2 text-xs text-fg-muted">
                {t(
                  "Risk: an open order with a recorded dispatch blocker, due within two hours. Missing reservations do not prove missing stock.",
                )}
              </p>
            </div>
            <div>
              <h2 className="text-base font-semibold">{t("Orders and shipping")}</h2>
              <p className="mt-1 text-xs text-fg-muted">
                {t("Click a number to view the matching orders.")}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
              {metrics.map(([label, value, flag]) => (
                <button
                  key={flag}
                  onClick={() => setFilter(flag)}
                  aria-haspopup="dialog"
                  className={`rounded-xl border p-4 text-left ${filter === flag ? activeTone : inactiveTone}`}
                >
                  <div className="text-3xl font-semibold tabular-nums">{formatNumber(value)}</div>
                  <div className="mt-2 text-sm text-fg-muted">{t(label)}</div>
                </button>
              ))}
            </div>
            <h2 className="text-base font-semibold">{t("Shipping performance")}</h2>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-lg bg-surface-muted p-4">
                <p className="text-xs text-fg-muted">
                  {t("Last hour: orders in / completely dispatched")}
                </p>
                <p className="mt-2 text-2xl">
                  <button
                    aria-label={t("Orders")}
                    aria-haspopup="dialog"
                    className="text-accent"
                    onClick={() => setFilter("received_last_hour")}
                  >
                    {formatNumber(data.orders_received_last_hour)}
                  </button>{" "}
                  →{" "}
                  <button
                    aria-label={t("Completely dispatched")}
                    aria-haspopup="dialog"
                    className="text-accent"
                    onClick={() => setFilter("completed_last_hour")}
                  >
                    {formatNumber(data.orders_completed_last_hour)}
                  </button>
                </p>
              </div>
              <button
                aria-haspopup="dialog"
                onClick={() => setFilter("eligible")}
                className="rounded-lg bg-surface-muted p-4 text-left"
              >
                <p className="text-xs text-fg-muted">{t("Complete dispatch share")}</p>
                <p className="mt-2 text-2xl">
                  {data.dispatch_rate_percent === null
                    ? "—"
                    : `${formatNumber(data.dispatch_rate_percent)}%`}
                </p>
                <p className="text-xs text-fg-muted">
                  {formatNumber(data.complete_dispatch_orders)} /{" "}
                  {formatNumber(data.eligible_orders)} · {t("Cancelled orders excluded")}
                </p>
              </button>
              <div className="rounded-lg bg-surface-muted p-4">
                <p className="text-xs text-fg-muted">{t("Average first / complete dispatch")}</p>
                <p className="mt-2 text-xl">
                  <button
                    aria-label={t("First dispatch")}
                    aria-haspopup="dialog"
                    className="text-accent"
                    onClick={() => setFilter("first_dispatch_sample")}
                  >
                    {duration(data.average_first_dispatch_minutes)}
                  </button>{" "}
                  /{" "}
                  <button
                    aria-label={t("Complete dispatch")}
                    aria-haspopup="dialog"
                    className="text-accent"
                    onClick={() => setFilter("complete_dispatch_sample")}
                  >
                    {duration(data.average_complete_dispatch_minutes)}
                  </button>
                </p>
                <p className="text-xs text-fg-muted">
                  {t("First / complete dispatch samples")}:{" "}
                  {formatNumber(data.first_dispatch_sample_orders)} /{" "}
                  {formatNumber(data.complete_dispatch_sample_orders)}
                </p>
              </div>
            </div>
            <h2 className="text-base font-semibold">{t("Customer and supplier messages")}</h2>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {[
                ["incoming", "Received messages", "All recorded incoming messages"],
                [
                  "waiting",
                  "Messages awaiting a reply",
                  "Simulator requests without a recorded reply",
                ],
                ["outgoing", "Sent messages", "All recorded outgoing messages"],
              ].map(([key, label, explanation]) => (
                <button
                  key={key}
                  aria-haspopup="dialog"
                  className="rounded-xl border border-border-subtle bg-surface p-4 text-left hover:bg-surface-muted"
                  onClick={() => {
                    setMailListOpen(true);
                    setMailFilter(key);
                  }}
                >
                  <div className="text-3xl font-semibold tabular-nums">
                    {data.mailbox_counts
                      ? formatNumber(
                          data.mailbox_counts[key as keyof BusinessOperations["mailbox_counts"]],
                        )
                      : "—"}
                  </div>
                  <div className="mt-2 text-sm font-medium">{t(label)}</div>
                  <p className="mt-1 text-xs text-fg-muted">{t(explanation)}</p>
                </button>
              ))}
            </div>
          </>
        )}
        {tab === "stock" && (
          <div className="overflow-auto rounded-xl border border-border-subtle p-4">
            <h3 className="font-semibold">{t("Stock and replenishment")}</h3>
            <table className="mt-3 w-full text-left text-sm">
              <thead>
                <tr>
                  {["Item", "Physical stock", "Reserved", "Available", "Incoming"].map((label) => (
                    <th key={label} className="p-2">
                      {t(label)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.inventory.map((i) => (
                  <tr key={i.item_id} className="border-t border-border-subtle">
                    <td className="p-2">
                      <button
                        className="text-accent"
                        onClick={() => setTarget({ kind: "item", id: i.item_id })}
                      >
                        {i.name}
                      </button>
                    </td>
                    {[i.physical, i.reserved, i.available, i.incoming].map((value, index) => (
                      <td key={index} className="p-2 tabular-nums">
                        {formatNumber(Number(value))}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {tab === "flow" && (
          <div className="rounded-xl border border-border-subtle p-4">
            <h3 className="font-semibold">{t("Goods in / out · last hour")}</h3>
            {data.goods_flow_last_hour.map((g) => (
              <div
                key={g.item_id}
                className="flex justify-between gap-3 border-b border-border-subtle py-3"
              >
                <button
                  className="text-accent"
                  onClick={() => setTarget({ kind: "item", id: g.item_id })}
                >
                  {g.name}
                </button>
                <span>
                  {formatNumber(Number(g.received))} → {formatNumber(Number(g.shipped))}
                </span>
              </div>
            ))}
            {data.goods_flow_last_hour.length === 0 && (
              <p className="mt-3 text-sm text-fg-muted">
                {t("No recorded goods movements in the last hour.")}
              </p>
            )}
          </div>
        )}
        {tab === "replenishment" && (
          <div className="rounded-xl border border-border-subtle p-4">
            <h3 className="font-semibold">
              {t("Expected replenishment")} · {formatNumber(data.open_replenishment_lines)}
            </h3>
            {data.replenishment.map((r) => (
              <button
                key={r.commitment_id}
                onClick={() => setTarget({ kind: "commitment", id: r.commitment_id })}
                className="flex w-full justify-between gap-3 border-b border-border-subtle py-3 text-left text-sm"
              >
                <span>
                  {r.item_name} · {formatNumber(Number(r.quantity))}
                </span>
                <span>{r.due_at ? formatDateTime(r.due_at) : t("No stated date")}</span>
              </button>
            ))}
            <p className="mt-3 text-xs text-fg-muted">
              {t("Stated supplier dates; no inferred customer delivery forecast.")}
            </p>
          </div>
        )}
        {tab === "messages" && mailContent}
        {tab === "documents" && (
          <div className="rounded-xl border border-border-subtle p-4">
            <h3 className="font-semibold">{t("Recent business documents")}</h3>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {data.recent_documents.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setTarget({ kind: "document", id: d.id })}
                  className="flex justify-between gap-3 rounded-lg bg-surface-muted p-3 text-left text-sm"
                >
                  <span data-original-content>
                    {d.number} · {d.party_name}
                  </span>
                  <span>
                    {d.amount === null ? "—" : formatNumber(Number(d.amount))} {d.currency}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
        {tab === "orders" && !filter && orderContent}
      </div>
      {filter && (
        <BusinessOrdersDialog title={t(labels[filter] || "Orders")} close={() => setFilter("")}>
          <p className="mb-3 text-xs text-fg-muted">
            {t("Updated")}: {formatDateTime(data.observed_at)}
          </p>
          {loadedFilter !== filter ? (
            <p role="status">{failed ? t("Business data could not be loaded.") : t("Loading…")}</p>
          ) : (
            <>
              {failed && (
                <p role="status">{t("Refresh failed. Showing the last recorded snapshot.")}</p>
              )}
              {orderContent}
            </>
          )}
        </BusinessOrdersDialog>
      )}
      {mailListOpen && (
        <BusinessOrdersDialog
          title={t("Customer and supplier messages")}
          close={() => setMailListOpen(false)}
        >
          <p className="mb-3 text-xs text-fg-muted">
            {t("Updated")}: {formatDateTime(data.observed_at)}
          </p>
          {failed && (
            <p role="status">{t("Refresh failed. Showing the last recorded snapshot.")}</p>
          )}
          {mailContent}
        </BusinessOrdersDialog>
      )}
      {mail && (
        <BusinessOrdersDialog title={mail.subject} close={() => setMail(null)}>
          {[
            {
              label: "Original incoming message",
              messages: [
                ["outgoing", "outbound"].includes(mail.direction) ? mail.original : mail,
              ].filter(Boolean),
              empty: "No linked incoming message recorded.",
            },
            {
              label: "Outgoing",
              messages: ["outgoing", "outbound"].includes(mail.direction)
                ? [mail]
                : mail.replies || [],
              empty: mail.reply_recorded === false ? "Awaiting reply (simulator)" : "Not recorded",
            },
          ].map((group) => (
            <section key={group.label} className="mb-4 rounded-lg border border-border-subtle p-4">
              <h3 className="font-semibold">{t(group.label)}</h3>
              {group.messages.length ? (
                group.messages.map(
                  (message) =>
                    message && (
                      <article
                        key={message.source_record_id}
                        className="mt-3 border-t border-border-subtle pt-3"
                      >
                        <p className="text-xs text-fg-muted">
                          {formatDateTime(message.recorded_at)}
                        </p>
                        <strong className="mt-2 block" data-original-content>
                          {message.subject}
                        </strong>
                        <p className="my-3 whitespace-pre-wrap break-words" data-original-content>
                          {message.body}
                        </p>
                        <button
                          className="text-accent"
                          onClick={() => {
                            setMail(null);
                            setTarget({ kind: "source_record", id: message.source_record_id });
                          }}
                        >
                          {t("Source")}
                        </button>
                      </article>
                    ),
                )
              ) : (
                <p className="mt-3 text-fg-muted">{t(group.empty)}</p>
              )}
            </section>
          ))}
        </BusinessOrdersDialog>
      )}
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </section>
  );
}

function BusinessOrdersDialog({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const dialog = ref.current!;
    dialog.showModal();
    return () => {
      dialog.close();
      trigger?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) close();
      }}
      className="m-auto max-h-[85vh] w-[min(1100px,95vw)] rounded-xl border border-border-subtle bg-surface p-0 text-fg shadow-xl backdrop:bg-black/60"
    >
      <div className="sticky top-0 flex items-center justify-between gap-4 border-b border-border-subtle bg-surface p-4">
        <h2 id={titleId} className="text-lg font-semibold">
          {title}
        </h2>
        <button
          autoFocus
          onClick={close}
          className="rounded-lg border border-border-subtle px-3 py-2"
        >
          {t("Close")}
        </button>
      </div>
      <div className="overflow-auto p-4">{children}</div>
    </dialog>
  );
}
