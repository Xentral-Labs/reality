import { useCockpitMotion } from "./useCockpitMotion";
import { useEffect, useRef, useState } from "react";
import { formatNumber, t } from "../localization";
import { metricChange, type MetricObservation } from "./cockpitLiveSignals";

/** A brief neutral signal for a changed current observation, never a success signal. */
export function ObservedMetric({
  value,
  context,
  current,
}: {
  value: number | null;
  context: string;
  current: boolean;
}) {
  const motion = useCockpitMotion();
  const previous = useRef<MetricObservation | null>(null);
  const revision = useRef(0);
  const [change, setChange] = useState<{
    context: string;
    value: number;
    delta: number;
    revision: number;
  } | null>(null);
  useEffect(() => {
    const next = current && value !== null && Number.isFinite(value) ? { context, value } : null;
    const delta = motion ? metricChange(previous.current, next) : null;
    previous.current = next;
    setChange(next && delta !== null ? { ...next, delta, revision: ++revision.current } : null);
  }, [context, current, value, motion]);
  const visible =
    motion && current && change?.context === context && change.value === value ? change : null;
  return (
    <strong
      key={visible?.revision || "steady"}
      data-status-metric
      data-live-change={visible?.delta}
      className={visible ? "cockpit-live-metric-change" : undefined}
      title={
        visible
          ? `${t("Change since previous observation")}: ${visible.delta > 0 ? "+" : ""}${formatNumber(visible.delta)}`
          : undefined
      }
      onAnimationEnd={() => setChange(null)}
    >
      {value === null ? "—" : formatNumber(value)}
    </strong>
  );
}
