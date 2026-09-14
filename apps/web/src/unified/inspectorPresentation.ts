export type InspectorPart =
  | { type: "text" | "number"; value: string }
  | { type: "date" | "datetime"; value: string }
  | { type: "money"; value: string; currency: string; precision?: number };

export function renderInspectorValue(
  value: unknown,
  parts: InspectorPart[] | undefined,
  format: {
    number: (value: string) => string;
    money: (value: string, currency: string, precision?: number) => string;
    date?: (value: string) => string;
    dateTime?: (value: string) => string;
  },
): string {
  const readableText = (text: string) =>
    format.dateTime
      ? text.replace(
          /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})/g,
          (value) => format.dateTime!(value),
        )
      : text;
  if (!parts)
    return typeof value === "object" && value !== null
      ? JSON.stringify(value)
      : String(value ?? "—");
  return parts
    .map((part) =>
      part.type === "money"
        ? format.money(part.value, part.currency, part.precision)
        : part.type === "date"
          ? (format.date?.(part.value) ?? part.value)
          : part.type === "datetime"
            ? (format.dateTime?.(part.value) ?? part.value)
            : part.type === "number"
              ? format.number(part.value)
              : readableText(part.value),
    )
    .join("");
}
