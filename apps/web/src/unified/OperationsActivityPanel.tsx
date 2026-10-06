import { useEffect, useState } from "react";
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
}: {
  selection: Selection;
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
  const [held, setHeld] = useState<CockpitActivityEvent[] | null>(null);
  const [inspected, setInspected] = useState<CockpitActivityEvent | null>(null);
  useEffect(() => {
    setHeld(null);
    setInspected(null);
  }, [selection.tenant, minutes]);
  const changed =
    held !== null && value?.events.some((event) => !held.some((old) => old.id === event.id));
  const events = held || value?.events || [];
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
    <section className="cockpit-card cockpit-activity" aria-labelledby="activity-title">
      <div className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Company-wide · recorded entities")}</span>
          <h2 id="activity-title">{t("Recorded business activity")}</h2>
        </div>
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
          <div className="cockpit-activity-total">
            <strong>{formatNumber(value.total)}</strong>
            <span>{t("Newly recorded entities in this window")}</span>
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
                style={{ height: `${Math.max(2, (bucket.total / maximum) * 100)}%` }}
              >
                <span>{formatNumber(bucket.total)}</span>
                <title>
                  {formatDateTime(bucket.start)} · {formatNumber(bucket.total)}
                  {bucket.partial ? ` · ${t("Partial coverage")}` : ""}
                </title>
              </div>
            ))}
          </div>
          <p className="cockpit-footnote">
            {t(
              "Recording time determines this graph. It does not count completed shipments or successful Agent actions.",
            )}
          </p>
          <div className="cockpit-actions">
            <button className="br-btn" onClick={() => setHeld(held ? null : value.events)}>
              {t(held ? "Resume following" : "Pause following")}
            </button>
            {changed && <span role="status">{t("New activity available")}</span>}
          </div>
          <ul className="cockpit-event-list">
            {events.map((event) => (
              <li key={event.id} data-activity-event={event.id}>
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
              <button className="br-btn" onClick={() => setInspected(null)}>
                {t("Close")}
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
