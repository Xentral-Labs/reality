import { useEffect, useRef, useState } from "react";
import { formatDateTimeInZone, formatNumber, formatTimeInZone, t } from "../localization";
import {
  cockpitOriginSelection,
  navigationSelection,
  selectionUrl,
  type Selection,
} from "./routing";
import type { ShippingMeasure, ShippingObservation, ShippingPoint } from "./cockpitModel";

export const cockpitTime = formatTimeInZone;

const seriesLabels = {
  plan: "Shipping plan",
  handover: "Confirmed handovers",
  forecast: "Future forecast",
};

/** Geometry renders returned cumulative points; it does not estimate business progress. */
export function ShippingDayPanel({
  value,
  inspect,
  selection,
}: {
  value: ShippingObservation;
  selection: Selection;
  inspect: (measure: ShippingMeasure, at?: string) => void;
}) {
  const [basisOpen, setBasisOpen] = useState(false);
  const plot = useRef<SVGSVGElement>(null);
  const [plotWidth, setPlotWidth] = useState(600);
  useEffect(() => {
    if (!plot.current) return;
    const observer = new ResizeObserver(([entry]) => {
      if (entry.contentRect.width > 0) setPlotWidth(Math.max(220, entry.contentRect.width));
    });
    observer.observe(plot.current);
    return () => observer.disconnect();
  }, [value.coverage.cohort]);
  const plotLeft = 50,
    plotRight = plotWidth - 16;
  const timeTicks = plotWidth < 420 ? [0, 0.5, 1] : [0, 0.25, 0.5, 0.75, 1];
  const start = Date.parse(value.day_start),
    end = Date.parse(value.day_end);
  const all = Object.values(value.series).flatMap((points) => points || []);
  const ceiling = Math.max(1, value.totals.due || 0, ...all.map((point) => point.count));
  const x = (at: string) =>
    plotLeft + ((Date.parse(at) - start) / (end - start)) * (plotRight - plotLeft);
  const y = (count: number) => 250 - (count / ceiling) * 205;
  const path = (points: ShippingPoint[]) =>
    points
      .map(
        (point, index) => `${index ? "H" : "M"}${x(point.at)}${index ? "V" : ","}${y(point.count)}`,
      )
      .join(" ");
  const observed = Math.min(end, Math.max(start, Date.parse(value.observed_at)));
  const dueLabel =
    (selection.cockpitDay || "today") === "today" ? "Due today" : "Due on selected day";
  const measures = [
    { key: "due", label: dueLabel, value: value.totals.due },
    { key: "handover", label: "Handed over", value: value.totals.handed_over },
    { key: "forecast", label: "Forecast by day end", value: value.totals.forecast },
    { key: "risk", label: "At risk", value: value.totals.risk },
  ] as const;
  return (
    <section className="cockpit-card cockpit-shipping" aria-labelledby="shipping-title">
      <div className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Shipping performance")}</span>
          <h2 id="shipping-title">{t("Shipping by end of day")}</h2>
          <p>
            {t("Cumulative orders · company business day")} · {value.time_zone}
          </p>
        </div>
        <button
          className="br-btn"
          onClick={() => setBasisOpen(!basisOpen)}
          aria-expanded={basisOpen}
        >
          {t(basisOpen ? "Hide calculation basis" : "Show calculation basis")}
        </button>
      </div>
      <div className="cockpit-metrics">
        {measures.map((measure) => (
          <button
            key={measure.key}
            className={`cockpit-metric ${measure.key === "risk" ? "cockpit-risk" : ""}`}
            disabled={measure.value === null}
            onClick={() => inspect(measure.key)}
            aria-label={`${t(measure.label)}: ${measure.value === null ? t("Unavailable") : measure.value}`}
          >
            <span>{t(measure.label)}</span>
            <strong>{measure.value === null ? "—" : formatNumber(measure.value)}</strong>
            <small>{t("View supporting orders")}</small>
          </button>
        ))}
      </div>
      <button className="br-btn" onClick={() => inspect("unplanned")}>
        {t("Work outside this day's plan")}
      </button>
      {value.coverage.cohort === "unavailable" ? (
        <div className="cockpit-unavailable" role="status">
          <strong>{t("Shipping plan unavailable")}</strong>
          <p>
            {t(
              "A source-backed daily cohort and confirmed capacity are required to show these curves.",
            )}
          </p>
        </div>
      ) : (
        <>
          <div className="cockpit-legend">
            {Object.entries(seriesLabels).map(([key, label]) => (
              <button
                key={key}
                className={`cockpit-series-label ${key}`}
                disabled={value.series[key as keyof typeof value.series] === null}
                onClick={() => inspect(key as ShippingMeasure)}
              >
                <i />
                {t(label)}
                {value.series[key as keyof typeof value.series] === null
                  ? ` · ${t("Unavailable")}`
                  : ""}
              </button>
            ))}
          </div>
          {Object.values(value.series_resolution_seconds || {}).some((seconds) => seconds > 0) && (
            <p className="cockpit-note" data-shipping-resolution>
              {t("Five-minute chart intervals · every order included")}
            </p>
          )}
          <svg
            className="cockpit-chart"
            ref={plot}
            viewBox={`0 0 ${plotWidth} 295`}
            role="group"
            aria-label={t("Cumulative shipping plan, confirmed handovers and future forecast")}
          >
            {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
              <g key={fraction}>
                <line
                  x1={plotLeft}
                  x2={plotRight}
                  y1={y(ceiling * fraction)}
                  y2={y(ceiling * fraction)}
                  className="cockpit-grid-line"
                />
                <text x={plotLeft - 10} y={y(ceiling * fraction) + 4} textAnchor="end">
                  {formatNumber(Math.round(ceiling * fraction))}
                </text>
              </g>
            ))}
            {timeTicks.map((fraction) => (
              <text
                key={fraction}
                x={plotLeft + (plotRight - plotLeft) * fraction}
                y="278"
                textAnchor={fraction === 0 ? "start" : fraction === 1 ? "end" : "middle"}
              >
                {cockpitTime(
                  new Date(start + (end - start) * fraction).toISOString(),
                  value.time_zone,
                )}
              </text>
            ))}
            {value.sites.flatMap((site) =>
              site.cutoffs.map((cutoff, index) => (
                <g key={`${site.location_id}-${index}`}>
                  <line
                    x1={x(cutoff.at)}
                    x2={x(cutoff.at)}
                    y1="40"
                    y2="250"
                    className="cockpit-cutoff"
                  />
                  <title>
                    {site.name} · {formatDateTimeInZone(cutoff.at, site.time_zone)} ·{" "}
                    {t(
                      cutoff.confirmation_state === "confirmed"
                        ? "Confirmed collection"
                        : "Requested collection",
                    )}
                  </title>
                </g>
              )),
            )}
            <line
              x1={x(new Date(observed).toISOString())}
              x2={x(new Date(observed).toISOString())}
              y1="34"
              y2="250"
              className="cockpit-now"
            />
            <text
              x={Math.max(
                plotLeft,
                Math.min(plotRight - 100, x(new Date(observed).toISOString()) + 6),
              )}
              y="25"
            >
              {t("Observed")} {cockpitTime(value.observed_at, value.time_zone)}
            </text>
            {Object.entries(value.series).map(([key, points]) =>
              points && points.length > 0 ? (
                <path
                  key={key}
                  data-shipping-series={key}
                  d={path(points)}
                  className={`cockpit-series ${key}`}
                  role="button"
                  tabIndex={0}
                  aria-label={`${t(seriesLabels[key as keyof typeof seriesLabels])} · ${t("View supporting orders")}`}
                  onClick={(event) => {
                    const box = event.currentTarget.ownerSVGElement!.getBoundingClientRect();
                    const position = ((event.clientX - box.left) / box.width) * plotWidth;
                    const nearest = points.reduce((best, point) =>
                      Math.abs(x(point.at) - position) < Math.abs(x(best.at) - position)
                        ? point
                        : best,
                    );
                    inspect(key as ShippingMeasure, nearest.at);
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      inspect(key as ShippingMeasure, points[points.length - 1].at);
                    }
                  }}
                >
                  <title>{t(seriesLabels[key as keyof typeof seriesLabels])}</title>
                </path>
              ) : null,
            )}
          </svg>
          <p className="cockpit-footnote">
            {t(
              "Forecast uses confirmed completion slots and current readiness. Requested collections do not add capacity.",
            )}
          </p>
          {value.forecast_horizon === "selected_day_ended" && (
            <p className="cockpit-note">
              {t("Selected day has ended — no historical forecast is reconstructed.")}
            </p>
          )}
        </>
      )}
      {value.gaps.length > 0 && (
        <details className="cockpit-gaps">
          <summary>
            {t("Observation gaps")} · {value.gaps.length}
          </summary>
          <ul>
            {value.gaps.map((gap, index) => (
              <li key={index}>{gap.code}</li>
            ))}
          </ul>
        </details>
      )}
      {value.sites.length > 0 && (
        <div className="cockpit-table-scroll">
          <table className="cockpit-table">
            <caption>{t("Dispatch sites · split orders may appear at more than one site")}</caption>
            <thead>
              <tr>
                <th>{t("Site")}</th>
                <th>{t(dueLabel)}</th>
                <th>{t("Handed over")}</th>
                <th>{t("Forecast")}</th>
                <th>{t("At risk")}</th>
                <th>{t("Collection cut-offs")}</th>
              </tr>
            </thead>
            <tbody>
              {value.sites.map((site) => (
                <tr key={site.location_id}>
                  <th>
                    {site.name}
                    <small>{site.time_zone}</small>
                  </th>
                  <td>{formatNumber(site.due)}</td>
                  <td>{formatNumber(site.handed_over)}</td>
                  <td>{site.forecast === null ? "—" : formatNumber(site.forecast)}</td>
                  <td>{site.risk === null ? "—" : formatNumber(site.risk)}</td>
                  <td>
                    <div data-cutoff-preview>
                      {site.cutoffs.slice(0, 2).map((cutoff, index) => (
                        <div key={index}>
                          {formatDateTimeInZone(cutoff.at, site.time_zone)} ·{" "}
                          {t(cutoff.confirmation_state === "confirmed" ? "Confirmed" : "Requested")}
                        </div>
                      ))}
                    </div>
                    {site.cutoffs.length > 2 && (
                      <details data-cutoff-details className="cockpit-collection-details">
                        <summary>
                          {t("All collection times")} ({formatNumber(site.cutoffs.length)})
                        </summary>
                        <div className="cockpit-collection-list">
                          {site.cutoffs.map((cutoff, index) => (
                            <div key={index} data-cutoff-entry>
                              {formatDateTimeInZone(cutoff.at, site.time_zone)} ·{" "}
                              {t(
                                cutoff.confirmation_state === "confirmed"
                                  ? "Confirmed"
                                  : "Requested",
                              )}
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {basisOpen && (
        <div className="cockpit-basis">
          <h3>{t("Current calculation basis")}</h3>
          {(value.basis.disclosure as { sampled?: boolean } | undefined)?.sampled && (
            <p>
              {t(
                "Basis preview is bounded to 50 records per section. Inspect supporting orders for full evidence.",
              )}
            </p>
          )}
          <p>
            <code>
              {typeof value.basis.policy_version === "string"
                ? value.basis.policy_version
                : t("Unknown")}
            </code>
          </p>
          <p>
            {t("Observed")} {cockpitTime(value.observed_at, value.time_zone)}
          </p>
          <p>
            {t("Basis identity")}: <code>{value.basis_key}</code>
          </p>
          <p>
            {t(
              "Each planned order counts once after every required dispatch quantity has been handed over. The forecast assumes current ready work and confirmed capacity.",
            )}
          </p>
          <ul>
            {[
              ...new Set(
                Object.values(
                  (value.basis.sources || {}) as Record<string, Record<string, unknown>>,
                ).flatMap((sources) => Object.keys(sources)),
              ),
            ]
              .slice(0, 50)
              .map((id) => (
                <li key={id}>
                  <a
                    href={selectionUrl(
                      navigationSelection(selection, {
                        route: "inspector",
                        inspectorView: "records",
                        inspectorTargetKind: "source_record",
                        inspectorTargetId: id,
                        cockpitOrigin: cockpitOriginSelection(selection),
                      }),
                    )}
                  >
                    {t("Source record")} · {id}
                  </a>
                </li>
              ))}
          </ul>
          <details>
            <summary>{t("Technical evidence details")}</summary>
            <pre>{JSON.stringify(value.basis, null, 2)}</pre>
          </details>
        </div>
      )}
    </section>
  );
}
