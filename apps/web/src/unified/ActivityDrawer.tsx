import { RegisterTable } from "./RegisterTable";
import { PreviewButton, TablePreview } from "./InlinePreview";
import { historyRecord, shortId } from "./historyRows";
import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, History, RefreshCw, X } from "lucide-react";
import { api, type TimelineEvent } from "../api";
import { formatDateTime, formatShortDateTime, t } from "../localization";
import { Inspector } from "./Inspector";
import { RegisterToolbar, RegisterWorkbench } from "./RegisterWorkbench";

// Presentation only; the shared service owns event classification and business state.
export function eventTitle(event: TimelineEvent): string {
  const titles: Record<string, string> = {
    "party.created": t("Business partner created"),
    "item.created": t("Item created"),
    "location.created": t("Location created"),
    "source_record.received": t("Source received"),
    "source_record.stored": t("Source recorded by confirmed action"),
    "source_record.interpreted": t("Source processing completed"),
    "source_record.unmapped": t("Source needs mapping"),
    "document.recorded": t("Business document recorded"),
    "commitment.created": t("Delivery commitment created"),
    "commitment.changed": t("Delivery commitment changed"),
    "commitment.fulfilled": t("Delivery commitment fulfilled"),
    "commitment.held": t("Delivery hold placed"),
    "commitment.hold_released": t("Delivery hold released"),
    "party.delivery_hold_placed": t("Business partner delivery hold placed"),
    "party.delivery_hold_released": t("Business partner delivery hold released"),
    "reservation.created": t("Inventory reserved"),
    "reservation.released": t("Inventory reservation released"),
    "reservation.consumed": t("Inventory reservation consumed"),
    "movement.recorded": t("Inventory movement recorded"),
    "movement.corrected": t("Inventory movement corrected"),
    "ledger_entry.recorded": t("Ledger entry recorded"),
    "ledger.posted": t("Financial posting recorded"),
    "ledger.reversed": t("Financial posting reversed"),
    "settlement.allocated": t("Payment allocation recorded"),
  };
  return titles[event.type] || event.business_title || event.type;
}

// The History register names areas and record kinds for a reader (spec 269).
const areaLabels: Record<string, string> = {
  sources: "Sources & intake",
  operations: "Operations",
  finance: "Finance",
  master_data: "Master data",
};
const statusTone: Record<string, string> = {
  attention: "bg-caution-bg text-caution-text",
  completed: "bg-positive-bg text-positive-text",
};
const subjectLabels: Record<string, string> = {
  party: "Business partner",
  item: "Item",
  location: "Location",
  document: "Document",
  document_line: "Document line",
  source_record: "Source record",
  commitment: "Commitment",
  reservation: "Reservation",
  movement: "Movement",
  fact: "Fact",
  payment: "Payment",
};
const embeddedActivityBody = "register-table-inset py-4";
const drawerActivityBody = "px-5 py-5 sm:px-7";
const inspectableSubjects = new Set([
  "document",
  "document_line",
  "source_record",
  "business_event",
  "fact",
  "commitment",
  "party",
  "item",
  "location",
  "reservation",
  "movement",
  "payment",
  "exception",
]);
export function BusinessContext({ event }: { event: TimelineEvent }) {
  const context = event.business_context || {};
  const text = (key: string) => (context[key] == null ? "" : String(context[key]));
  const names = [
    ...new Set(["party", "item", "name", "sku", "reference"].map(text).filter(Boolean)),
  ];
  return (
    <div className="mt-2 space-y-1 break-words text-sm text-fg-muted">
      {names.length > 0 && <p data-original-content="">{names.join(" · ")}</p>}
      {text("quantity") && (
        <p>
          {t("Quantity")}:{" "}
          <span data-original-content="">
            {[text("quantity"), text("unit")].filter(Boolean).join(" ")}
          </span>
        </p>
      )}
      {text("amount") && (
        <p>
          {t("Amount")}:{" "}
          <span data-original-content="">
            {[text("amount"), text("currency")].filter(Boolean).join(" ")}
          </span>
        </p>
      )}
      {!names.length && !text("quantity") && !text("amount") && event.business_detail && (
        <p data-original-content="">{event.business_detail}</p>
      )}
    </div>
  );
}
export function ActivityDrawer({
  tenant,
  companyName,
  close,
  embedded = false,
}: {
  tenant: string;
  companyName: string;
  close: () => void;
  embedded?: boolean;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    generation = useRef(0),
    inFlight = useRef(false);
  const [draft, setDraft] = useState(""),
    [query, setQuery] = useState("");
  const [hours, setHours] = useState(24),
    [attention, setAttention] = useState(false),
    [revision, setRevision] = useState(0);
  const [events, setEvents] = useState<TimelineEvent[]>([]),
    [cursor, setCursor] = useState<number>();
  const [hasMore, setHasMore] = useState(false),
    [loading, setLoading] = useState(true),
    [loadingOlder, setLoadingOlder] = useState(false);
  const [error, setError] = useState(false),
    [olderError, setOlderError] = useState(false);
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  const [previewed, setPreviewed] = useState("");
  useEffect(() => {
    if (embedded) return;
    const previous = document.activeElement as HTMLElement | null,
      node = dialog.current;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, [embedded]);
  useEffect(() => {
    const current = ++generation.current;
    inFlight.current = true;
    setLoading(true);
    setLoadingOlder(false);
    setError(false);
    setOlderError(false);
    setEvents([]);
    setCursor(undefined);
    setHasMore(false);
    api
      .timeline(tenant, query, "", attention ? "attention" : "", hours)
      .then((data) => {
        if (generation.current !== current) return;
        setEvents([...new Map(data.events.map((event) => [event.id, event])).values()]);
        setCursor(data.events.at(-1)?.sequence);
        setHasMore(data.has_more && data.events.length > 0);
      })
      .catch(() => {
        if (generation.current === current) setError(true);
      })
      .finally(() => {
        if (generation.current === current) {
          setLoading(false);
          inFlight.current = false;
        }
      });
    return () => {
      generation.current++;
    };
  }, [tenant, query, hours, attention, revision]);
  const loadOlder = async () => {
    if (inFlight.current || cursor === undefined || !hasMore) return;
    inFlight.current = true;
    const current = generation.current;
    setLoadingOlder(true);
    setOlderError(false);
    try {
      const data = await api.timeline(
        tenant,
        query,
        "",
        attention ? "attention" : "",
        hours,
        "",
        cursor,
      );
      if (current !== generation.current) return;
      setEvents((previous) => {
        const ids = new Set(previous.map((event) => event.id));
        return [
          ...previous,
          ...data.events.filter((event) => {
            if (ids.has(event.id)) return false;
            ids.add(event.id);
            return true;
          }),
        ];
      });
      const next = data.events.at(-1)?.sequence;
      setCursor(next);
      setHasMore(data.has_more && next !== undefined && next < cursor);
    } catch {
      if (current === generation.current) setOlderError(true);
    } finally {
      if (current === generation.current) {
        setLoadingOlder(false);
        inFlight.current = false;
      }
    }
  };
  const olderControls = (
    <>
      {olderError && (
        <p role="alert" className="text-sm text-caution-text">
          {t("Older activity could not be loaded.")}
        </p>
      )}
      {hasMore ? (
        <button className="br-btn" disabled={loadingOlder} onClick={() => void loadOlder()}>
          {loadingOlder ? t("Loading activity…") : t("Load older events")}
        </button>
      ) : (
        <p className="text-xs text-fg-muted">{t("End of matching activity.")}</p>
      )}
    </>
  );
  const content = (
    <>
      {embedded ? (
        <RegisterToolbar
          search={
            <input
              aria-label={t("Search activity")}
              placeholder={t("Customer, item, reference or event")}
              className="br-control"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  setQuery(draft.trim());
                  setRevision((value) => value + 1);
                }
              }}
            />
          }
          submit={
            <button
              className="br-btn"
              onClick={() => {
                setQuery(draft.trim());
                setRevision((value) => value + 1);
              }}
            >
              {t("Search")}
            </button>
          }
          filters={
            <>
              <select
                aria-label={t("Period")}
                value={hours}
                onChange={(event) => setHours(Number(event.target.value))}
              >
                <option value={24}>{t("Last 24 hours")}</option>
                <option value={168}>{t("Last 7 days")}</option>
                <option value={720}>{t("Last 30 days")}</option>
                <option value={0}>{t("All time")}</option>
              </select>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={attention}
                  onChange={(event) => setAttention(event.target.checked)}
                />
                {t("Attention events only")}
              </label>
              <button
                className="br-btn"
                disabled={loading}
                onClick={() => setRevision((value) => value + 1)}
              >
                <RefreshCw size={15} />
                {t("Refresh")}
              </button>
            </>
          }
        />
      ) : (
        <header className="sticky top-0 z-10 border-b border-border-default bg-surface px-5 py-5 sm:px-7">
          <div
            hidden={embedded}
            className="flex items-start justify-between gap-3"
            style={embedded ? { display: "none" } : undefined}
          >
            <div className="min-w-0">
              <h2
                hidden={embedded}
                id="activity-title"
                className="flex items-center gap-2 text-xl font-semibold text-fg-strong"
              >
                <History size={20} className="text-accent" />
                {embedded ? t("Event history") : t("Activity")}
              </h2>
              <p data-original-content="" className="mt-1 truncate text-sm text-fg-muted">
                {companyName}
              </p>
            </div>
            {!embedded && (
              <button className="br-btn" aria-label={t("Close")} onClick={close}>
                <X size={18} />
              </button>
            )}
          </div>
          {!embedded && (
            <p className="mt-4 text-sm text-fg-muted">
              {t("What was recorded across your business. Newest recordings first.")}
            </p>
          )}
          <form
            className="flex gap-2"
            style={{ marginTop: embedded ? 0 : 16 }}
            onSubmit={(event) => {
              event.preventDefault();
              setQuery(draft.trim());
              setRevision((value) => value + 1);
            }}
          >
            <input
              aria-label={t("Search activity")}
              placeholder={t("Customer, item, reference or event")}
              className="min-w-0 flex-1 rounded-lg border border-border-default bg-surface px-3 py-2 text-sm"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
            />
            <button className="br-btn" type="submit">
              {t("Search")}
            </button>
          </form>
          <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
            <label className="flex items-center gap-2 text-sm">
              {t("Period")}
              <select
                aria-label={t("Period")}
                className="rounded-lg border border-border-default bg-surface px-2 py-2"
                value={hours}
                onChange={(event) => setHours(Number(event.target.value))}
              >
                <option value={24}>{t("Last 24 hours")}</option>
                <option value={168}>{t("Last 7 days")}</option>
                <option value={720}>{t("Last 30 days")}</option>
                <option value={0}>{t("All time")}</option>
              </select>
            </label>
            <button
              className="br-btn"
              disabled={loading}
              onClick={() => setRevision((value) => value + 1)}
            >
              <RefreshCw size={15} />
              {t("Refresh")}
            </button>
          </div>
          <label className="mt-3 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={attention}
              onChange={(event) => setAttention(event.target.checked)}
            />
            {t("Attention events only")}
          </label>
        </header>
      )}
      <div
        className={embedded ? embeddedActivityBody : drawerActivityBody}
        aria-busy={loading || loadingOlder}
      >
        {loading ? (
          <p role="status" className="py-8 text-sm text-fg-muted">
            {t("Loading activity…")}
          </p>
        ) : error ? (
          <div role="alert" className="space-y-3 py-6">
            <p>{t("Activity could not be loaded.")}</p>
            <button className="br-btn" onClick={() => setRevision((value) => value + 1)}>
              {t("Retry")}
            </button>
          </div>
        ) : !events.length ? (
          <p role="status" className="py-8 text-sm text-fg-muted">
            {t("No matching events.")}
          </p>
        ) : (
          <>
            {embedded ? (
              <RegisterTable
                cursorView={{
                  id: "inspector:history",
                  widths: [112, 108, 112, 88, 80, 80],
                  grow: [1, 2, 3],
                }}
                footer={olderControls}
              >
                <thead>
                  <tr>
                    <th>{t("Recorded at")}</th>
                    <th>{t("Event")}</th>
                    <th>{t("Record")}</th>
                    <th>{t("Area")}</th>
                    <th>{t("Status")}</th>
                    <th>{t("Actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {events.flatMap((event) => {
                    const record = historyRecord(event);
                    const open = previewed === event.id;
                    // A flat list with its own keys: the register flattens fragments.
                    return [
                      <tr key={event.id} data-activity-event={event.id}>
                        <td className="tabular-nums" title={formatDateTime(event.recorded_at)}>
                          {formatShortDateTime(event.recorded_at)}
                        </td>
                        <td>
                          <span
                            className="block truncate"
                            title={event.type}
                            data-original-content=""
                          >
                            {eventTitle(event)}
                          </span>
                        </td>
                        <td>
                          <span
                            className="block truncate"
                            title={record.name || record.id}
                            data-history-record
                            data-original-content=""
                          >
                            {record.name || shortId(record.id)}
                          </span>
                        </td>
                        <td>
                          <span
                            className="inline-block rounded-full border border-border-subtle bg-surface-muted px-2 py-0.5 text-xs"
                            data-history-area={event.area}
                          >
                            {t(areaLabels[event.area] || event.area)}
                          </span>
                        </td>
                        <td>
                          {/* Completed is the norm; only what needs attention carries a badge. */}
                          {event.status === "attention" && (
                            <span
                              className={`inline-block rounded px-1.5 py-0.5 text-xs ${statusTone.attention}`}
                              data-history-status={event.status}
                            >
                              {t("Attention event")}
                            </span>
                          )}
                        </td>
                        <td>
                          <PreviewButton
                            open={open}
                            controls={`history-preview-${event.id}`}
                            label={eventTitle(event)}
                            toggle={() => setPreviewed(open ? "" : event.id)}
                          />
                        </td>
                      </tr>,
                      <TablePreview
                        key={`preview-${event.id}`}
                        id={`history-preview-${event.id}`}
                        open={open}
                        columns={6}
                      >
                        <div className="max-w-3xl space-y-3 text-sm" data-history-details>
                          <BusinessContext event={event} />
                          <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1 break-all text-xs">
                            <dt className="text-fg-muted">{t("Event ID")}</dt>
                            <dd data-original-content="">{event.id}</dd>
                            <dt className="text-fg-muted">{t("Subject")}</dt>
                            <dd data-original-content="">
                              {event.subject_type} · {event.subject_id}
                            </dd>
                            {event.source_record_id && (
                              <>
                                <dt className="text-fg-muted">{t("Source record ID")}</dt>
                                <dd data-original-content="">{event.source_record_id}</dd>
                              </>
                            )}
                            <dt className="text-fg-muted">{t("Recorded sequence")}</dt>
                            <dd>{event.sequence}</dd>
                          </dl>
                          <div className="flex flex-wrap gap-2">
                            <button
                              className="br-btn"
                              onClick={() => setTarget({ kind: "business_event", id: event.id })}
                            >
                              {t("Inspect event")}
                            </button>
                            {inspectableSubjects.has(event.subject_type) && (
                              <button
                                className="br-btn"
                                onClick={() =>
                                  setTarget({ kind: event.subject_type, id: event.subject_id })
                                }
                              >
                                {t("Open related record")}
                              </button>
                            )}
                          </div>
                          <details className="text-xs text-fg-muted">
                            <summary className="cursor-pointer">{t("Technical details")}</summary>
                            <pre
                              data-original-content=""
                              className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-all rounded-lg bg-surface-muted p-3"
                            >
                              {JSON.stringify(event.payload, null, 2)}
                            </pre>
                          </details>
                        </div>
                      </TablePreview>,
                    ];
                  })}
                </tbody>
              </RegisterTable>
            ) : (
              <ol className="space-y-4">
                {events.map((event) => (
                  <li
                    key={event.id}
                    data-activity-event={event.id}
                    className="min-w-0 rounded-xl border border-border-default p-4"
                  >
                    <p className="text-xs text-fg-muted">
                      {t("Recorded at")}{" "}
                      <time dateTime={event.recorded_at}>{formatDateTime(event.recorded_at)}</time>
                    </p>
                    <h3
                      className="mt-2 break-words font-semibold text-fg-strong"
                      data-original-content=""
                    >
                      {eventTitle(event)}
                    </h3>
                    {event.status === "attention" && (
                      <span className="mt-2 inline-block rounded bg-caution-bg px-2 py-1 text-xs text-caution-text">
                        {t("Attention event")}
                      </span>
                    )}
                    <BusinessContext event={event} />
                    <div className="mt-4 flex flex-wrap gap-2">
                      <button
                        className="br-btn text-sm"
                        onClick={() => setTarget({ kind: "business_event", id: event.id })}
                      >
                        {t("Inspect event")}
                        <ArrowUpRight size={14} />
                      </button>
                      {inspectableSubjects.has(event.subject_type) && (
                        <button
                          className="br-btn text-sm"
                          onClick={() =>
                            setTarget({ kind: event.subject_type, id: event.subject_id })
                          }
                        >
                          {t("Open related record")}
                        </button>
                      )}
                    </div>
                    <details className="mt-4 text-xs text-fg-muted">
                      <summary className="cursor-pointer">{t("Technical details")}</summary>
                      <dl className="mt-3 space-y-2 break-all">
                        <div>
                          <dt>{t("Event time")}</dt>
                          <dd>
                            <time dateTime={event.occurred_at}>
                              {formatDateTime(event.occurred_at)}
                            </time>
                          </dd>
                        </div>
                        <div>
                          <dt>{t("Recorded sequence")}</dt>
                          <dd data-original-content="">{event.sequence}</dd>
                        </div>
                        <div>
                          <dt>{t("Event type")}</dt>
                          <dd data-original-content="">{event.type}</dd>
                        </div>
                        <div>
                          <dt>{t("Event ID")}</dt>
                          <dd data-original-content="">{event.id}</dd>
                        </div>
                        <div>
                          <dt>{t("Subject")}</dt>
                          <dd data-original-content="">
                            {event.subject_type} · {event.subject_id}
                          </dd>
                        </div>
                        {event.source_record_id && (
                          <div>
                            <dt>{t("Source record ID")}</dt>
                            <dd data-original-content="">{event.source_record_id}</dd>
                          </div>
                        )}
                        {event.action_id && (
                          <div>
                            <dt>{t("Action ID")}</dt>
                            <dd data-original-content="">{event.action_id}</dd>
                          </div>
                        )}
                        {event.correlation_id && (
                          <div>
                            <dt>{t("Correlation ID")}</dt>
                            <dd data-original-content="">{event.correlation_id}</dd>
                          </div>
                        )}
                        {event.causation_id && (
                          <div>
                            <dt>{t("Causation ID")}</dt>
                            <dd data-original-content="">{event.causation_id}</dd>
                          </div>
                        )}
                      </dl>
                      <pre
                        data-original-content=""
                        className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap break-all rounded-lg bg-surface-muted p-3"
                      >
                        {JSON.stringify(event.payload, null, 2)}
                      </pre>
                    </details>
                  </li>
                ))}
              </ol>
            )}
            {!embedded && olderControls}
          </>
        )}
      </div>
    </>
  );
  // The inspector stays outside the register workbench: its child-position rules
  // (margin, radius, inline padding) would otherwise override the dialog's own styling.
  const inspector = target && (
    <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />
  );
  if (embedded)
    return (
      <>
        <RegisterWorkbench>
          <section className="register-surface min-w-0 overflow-hidden" data-inline-activity>
            {content}
          </section>
        </RegisterWorkbench>
        {inspector}
      </>
    );
  return (
    <dialog
      ref={dialog}
      aria-labelledby="activity-title"
      onCancel={(event) => {
        if (event.target === event.currentTarget) {
          event.preventDefault();
          close();
        }
      }}
      onClick={(event) => {
        if (event.target !== event.currentTarget) return;
        const b = event.currentTarget.getBoundingClientRect();
        if (
          event.clientX < b.left ||
          event.clientX > b.right ||
          event.clientY < b.top ||
          event.clientY > b.bottom
        )
          close();
      }}
      className="fixed inset-y-0 right-0 left-auto m-0 h-dvh max-h-dvh w-[min(600px,100vw)] max-w-full overflow-y-auto border-l border-border-default bg-surface p-0 text-fg-default shadow-xl backdrop:bg-black/30"
    >
      {content}
      {inspector}
    </dialog>
  );
}
