export type TableLayout = {
  density: "normal" | "compact";
  hidden: number[];
  widths: Record<number, number>;
};
export function layoutKey(user: string, table: string) {
  return `reality.table.v1:${encodeURIComponent(user)}:${encodeURIComponent(table)}`;
}
export function validateLayout(value: unknown, count: number): TableLayout {
  const raw = value && typeof value === "object" ? (value as Partial<TableLayout>) : {};
  const hidden = Array.isArray(raw.hidden)
    ? [...new Set(raw.hidden.filter((i) => Number.isInteger(i) && i > 0 && i < count - 1))]
    : [];
  const widths: Record<number, number> = {};
  if (raw.widths && typeof raw.widths === "object")
    for (const [key, width] of Object.entries(raw.widths)) {
      const i = Number(key);
      if (
        Number.isInteger(i) &&
        i >= 0 &&
        i < count &&
        typeof width === "number" &&
        Number.isFinite(width)
      )
        widths[i] = Math.min(i === count - 1 ? 80 : 320, Math.max(70, Math.round(width)));
    }
  return { density: raw.density === "compact" ? "compact" : "normal", hidden, widths };
}
