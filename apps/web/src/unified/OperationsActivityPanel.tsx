import { useCockpitMotion } from "./useCockpitMotion";
import { newEventIds, type EventObservation } from "./cockpitLiveSignals";
import { useEffect, useRef, useState } from "react";
import { Pause, Play, X } from "lucide-react";
import {
  formatZonedDateTime as formatDateTime,
  formatNumber,
  formatTime,
  t,
} from "../localization";
import type { LiveReadState } from "./cockpitLiveRead";
import type { CockpitActivity, CockpitActivityEvent } from "./cockpitModel";
import {
  cockpitOriginSelection,
  navigationSelection,
  selectionUrl,
  type Selection,
} from "./routing";
import { ReadState } from "./ReadState";
import { eventTitle } from "./ActivityDrawer";

export function OperationsActivityPanel({
  selection,
  navigate,
  state,
  embedded = false,
}: {
  selection: Selection;
  embedded?: boolean;
  state: LiveReadState<CockpitActivity>;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const minutes = selection.cockpitMinutes || 15;
  const value = state.data;
  useEffect(() => {
    if (state.status === "denied") {
      setHeld(null);
      setInspected(null);
    }
  }, [state.status]);
  const [rateExpanded, setRateExpanded] = useState(false);
  const [held, setHeld] = useState<CockpitActivityEvent[] | null>(null);
  const [inspected, setInspected] = useState<CockpitActivityEvent | null>(null);
  useEffect(() => {
    setHeld(null);
    setInspected(null);
  }, [selection.tenant, minutes]);
  const changed =
    held !== null && value?.events.some((event) => !held.some((old) => old.id === event.id));
  const events = held || value?.events || [];
  const context = `${selection.tenant}:${minutes}`;
  const motion = useCockpitMotion();
  const previous = useRef<EventObservation | null>(null);
  const [newEvents, setNewEvents] = useState<{ context: string; ids: string[] } | null>(null);
  useEffect(() => {
    if (state.status !== "current" || previous.current?.context !== context) {
      previous.current = null;
      setNewEvents(null);
    }
    if (state.status !== "current" || held !== null || !value) return;
    const next = { context, events: value.events };
    const ids = motion ? newEventIds(previous.current, next) : [];
    const sequenceFloor = Math.max(
      previous.current?.sequenceFloor || 0,
      ...value.events.map((event) => event.sequence),
    );
    previous.current = { ...next, sequenceFloor };
    setNewEvents({ context, ids });
  }, [context, held, state.status, value, motion]);
  const maximum = Math.max(1, ...(value?.buckets.map((row) => row.total) || []));
  const reference = (event: CockpitActivityEvent) =>
    selectionUrl(
      navigationSelection(selection, {
        route: "inspector",
        inspectorView: "records",
        inspectorTargetKind: "business_event",
        inspectorTargetId: event.id,
        cockpitOrigin: cockpitOriginSelection(selection),
      }),
    );
  return (
    <section
      className="cockpit-card cockpit-activity"
      aria-labelledby={embedded ? undefined : "activity-title"}
      aria-label={embedded ? t("Recorded business activity") : undefined}
    >
      <div className={`cockpit-card-heading ${embedded ? "cockpit-context-actions" : ""}`}>
        {!embedded && (
          <div>
            <span className="cockpit-eyebrow">{t("Live event log")}</span>
            <h2 id="activity-title">{t("Recorded business activity")}</h2>
          </div>
        )}
        {value && (
          <button
            className="shell-icon-button cockpit-icon-action"
            aria-label={t(held ? "Resume following" : "Pause following")}
            title={t(held ? "Resume following" : "Pause following")}
            aria-pressed={held !== null}
            aria-controls="cockpit-live-events"
            onClick={() => setHeld(held ? null : value.events)}
          >
            {held ? <Play size={16} aria-hidden="true" /> : <Pause size={16} aria-hidden="true" />}
          </button>
        )}
      </div>
      {state.status === "stale" && (
        <p className="cockpit-note" role="status">
          {t("Previous observation — refresh failed")}
        </p>
      )}
      {!value && (
        <ReadState
          loading={!state.error}
          error={state.error instanceof Error ? state.error.message : undefined}
        />
      )}
      {value && (
        <>
          <div className="cockpit-activity-signal" data-live-activity-signal>
            <div className="cockpit-activity-total">
              <strong>{formatNumber(value.total)}</strong>
              <span>
                {t("Recorded entities")} · {minutes} {t("Min.")}
              </span>
            </div>
            <div
              className="cockpit-activity-chart"
              role="img"
              aria-label={t("Recorded business entities per minute")}
            >
              {value.buckets.map((bucket) => (
                <div
                  key={bucket.start}
                  className={bucket.partial ? "partial" : ""}
                  data-recorded-total={bucket.total}
                  title={`${formatDateTime(bucket.start)} · ${formatNumber(bucket.total)}${bucket.partial ? ` · ${t("Partial coverage")}` : ""}`}
                  style={{
                    height: `${bucket.total === 0 ? 0 : Math.max(2, (bucket.total / maximum) * 100)}%`,
                  }}
                >
                  <span>{formatNumber(bucket.total)}</span>
                  <title>
                    {formatDateTime(bucket.start)} · {formatNumber(bucket.total)}
                    {bucket.partial ? ` · ${t("Partial coverage")}` : ""}
                  </title>
                </div>
              ))}
            </div>
          </div>
          <details
            className="cockpit-recording-rate"
            open={rateExpanded}
            onToggle={(event) => setRateExpanded(event.currentTarget.open)}
          >
            <summary>{t("Recording rate & period")}</summary>
            <div className="cockpit-selection" role="group" aria-label={t("Activity period")}>
              {([5, 15, 60] as const).map((window) => (
                <button
                  className="br-btn"
                  key={window}
                  aria-pressed={minutes === window}
                  onClick={() => navigate({ cockpitMinutes: window })}
                >
                  {window} {t("Min.")}
                </button>
              ))}
            </div>
            <p className="cockpit-footnote">
              {t(
                "Recording time determines this graph. It does not count completed shipments or successful Agent actions.",
              )}
            </p>
          </details>
          {changed && (
            <p className="cockpit-note" role="status">
              {t("New activity available")}
            </p>
          )}
          <ul className="cockpit-event-list" id="cockpit-live-events">
            {events.map((event) => (
              <li
                key={event.id}
                data-activity-event={event.id}
                data-live-new-event={
                  motion &&
                  state.status === "current" &&
                  held === null &&
                  newEvents?.context === context &&
                  newEvents.ids.includes(event.id)
                    ? "true"
                    : undefined
                }
                onAnimationEnd={() =>
                  setNewEvents((old) =>
                    old ? { ...old, ids: old.ids.filter((id) => id !== event.id) } : null,
                  )
                }
              >
                <button
                  onClick={() => {
                    setInspected(event);
                    if (!held) setHeld(events);
                  }}
                >
                  <time>{formatTime(event.recorded_at, true)}</time>
                  <span>{eventTitle(event)}</span>
                </button>
                <a href={reference(event)}>{t("Evidence")}</a>
              </li>
            ))}
          </ul>
          {events.length === 0 && (
            <p className="cockpit-note">
              {t("No newly recorded business entities in this window")}
            </p>
          )}
          {value.has_more && (
            <p className="cockpit-note">
              {t("Showing the latest 50 events · full totals are preserved")}
            </p>
          )}
          {inspected && (
            <div className="cockpit-basis">
              <button
                className="shell-icon-button cockpit-icon-action cockpit-detail-close"
                aria-label={t("Close")}
                title={t("Close")}
                onClick={() => setInspected(null)}
              >
                <X size={16} aria-hidden="true" />
              </button>
              <p>{eventTitle(inspected)}</p>
              <details>
                <summary>{t("Technical details")}</summary>
                <code>{inspected.type}</code>
              </details>
              <p>
                {t("Recorded")}: {formatDateTime(inspected.recorded_at)}
              </p>
              <p>
                {t("Occurred")}: {formatDateTime(inspected.occurred_at)}
              </p>
              <a href={reference(inspected)}>{t("Open in Inspector")}</a>
            </div>
          )}
          <p className="cockpit-footnote">
            {t("Observed")} {formatDateTime(value.observed_at)} · {t("Coverage begins")}:{" "}
            {formatDateTime(value.coverage_start)}
          </p>
        </>
      )}
    </section>
  );
}
