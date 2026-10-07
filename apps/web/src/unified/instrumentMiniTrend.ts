import type { OperatingFlows } from "./cockpitModel";

export type TrendPoint = { at: string; value: number | null };
export type TrendSeries = { key: string; label: string; points: TrendPoint[] };
export type MiniTrend = { caption: string; level: boolean; series: TrendSeries[] };

const definitions: Record<string, { caption: string; fields: [string, string][] }> = {
  orders: {
    caption: "Intake / dispatch",
    fields: [
      ["orders_received", "New orders"],
      ["dispatch_movements", "Physical dispatch records"],
    ],
  },
  supply: { caption: "Goods receipts", fields: [["receipts", "Goods receipt records"]] },
  stock: {
    caption: "Receipts / dispatch",
    fields: [
      ["receipts", "Goods receipt records"],
      ["dispatch_movements", "Physical dispatch records"],
    ],
  },
  returns: {
    caption: "Arrivals / processing",
    fields: [
      ["return_arrivals", "Return receipt records"],
      ["return_dispositions", "Disposition movement records"],
    ],
  },
};
const finite = (value: unknown): number | null =>
  typeof value === "number" && Number.isFinite(value) ? value : null;

/** Select held observations only; these movement counts are not stock quantities. */
export function instrumentTrend(area: string, value?: OperatingFlows): MiniTrend {
  if (!value || area === "finance")
    return { caption: "No trend available", level: false, series: [] };
  if (area === "messages")
    return {
      caption: "Unanswered messages",
      level: true,
      series: [
        {
          key: "unanswered",
          label: "Unanswered backlog",
          points: value.messages.series.map((point) => ({
            at: point.at,
            value: finite(point.unanswered),
          })),
        },
      ],
    };
  const definition = definitions[area];
  if (!definition) return { caption: "No trend available", level: false, series: [] };
  return {
    caption: definition.caption,
    level: false,
    series: definition.fields.map(([key, label]) => ({
      key,
      label,
      points: value.buckets.map((bucket) => ({
        at: bucket.end,
        value: bucket.known ? finite(bucket[key]) : null,
      })),
    })),
  };
}

/** Time-positioned SVG geometry, with a new segment after every missing observation. */
export function miniTrendPath(
  points: TrendPoint[],
  options: {
    start: string;
    end: string;
    minimum: number;
    maximum: number;
  },
): string {
  const start = Date.parse(options.start),
    end = Date.parse(options.end);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return "";
  const range = Math.max(1, options.maximum - options.minimum);
  let open = false;
  return points
    .map((point) => {
      const at = Date.parse(point.at);
      if (
        point.value === null ||
        !Number.isFinite(point.value) ||
        !Number.isFinite(at) ||
        at < start ||
        at > end
      ) {
        open = false;
        return "";
      }
      const x = +(2 + ((at - start) / (end - start)) * 156).toFixed(2);
      const y = +(34 - ((point.value - options.minimum) / range) * 32).toFixed(2);
      const segment = open ? `L${x},${y}` : `M${x},${y}L${x},${y}`;
      open = true;
      return segment;
    })
    .filter(Boolean)
    .join(" ");
}
