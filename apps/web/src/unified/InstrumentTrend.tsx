import { formatNumber, t } from "../localization";
import type { OperatingFlows } from "./cockpitModel";
import { instrumentTrend, miniTrendPath } from "./instrumentMiniTrend";

export function InstrumentTrend({
  area,
  title,
  value,
  stale,
}: {
  area: string;
  title: string;
  value?: OperatingFlows;
  stale: boolean;
}) {
  const trend = instrumentTrend(area, value);
  const known = trend.series.flatMap((series) =>
    series.points.flatMap((point) => (point.value === null ? [] : [point.value])),
  );
  const minimum = trend.level && known.length ? Math.max(0, Math.min(...known) - 1) : 0;
  const maximum = known.length ? Math.max(...known) + (trend.level ? 1 : 0) : 0;
  const description = `${t(title)} · ${t("Last 60 minutes")} · ${t(trend.level ? "Open messages" : "Records per interval")} · ${trend.series.map((series) => t(series.label)).join(" / ")}${stale ? ` · ${t("Previous observation")}` : ""}`;
  return (
    <span
      className="cockpit-mini-trend"
      data-instrument-trend={area}
      data-trend-stale={stale ? "true" : undefined}
      title={description}
    >
      {known.length && value ? (
        <svg viewBox="0 0 160 36" preserveAspectRatio="none" role="img" aria-label={description}>
          <title>{description}</title>
          <path d="M2 34H158" className="cockpit-mini-axis" />
          {trend.series.map((series, index) => (
            <path
              key={series.key}
              d={miniTrendPath(series.points, {
                start: value.start,
                end: value.observed_at,
                minimum,
                maximum,
              })}
              className={`cockpit-mini-line line-${index}`}
              data-mini-series={series.key}
              vectorEffect="non-scaling-stroke"
            >
              <title>
                {t(series.label)} ·{" "}
                {series.points
                  .map((point) => (point.value === null ? "—" : formatNumber(point.value)))
                  .join(" → ")}
              </title>
            </path>
          ))}
        </svg>
      ) : (
        <span className="cockpit-mini-empty-plot" data-trend-unavailable aria-hidden="true" />
      )}
      <span className="cockpit-mini-caption">
        {t(known.length ? trend.caption : "No trend available")}
      </span>
      <span className="cockpit-mini-period">
        {t(stale ? "Previous observation" : "Last 60 minutes")}
      </span>
    </span>
  );
}
