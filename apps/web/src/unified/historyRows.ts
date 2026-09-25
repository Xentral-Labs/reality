// How the History register names the record an event concerns (spec 269). Pure,
// so it is tested alone; the names come from the timeline's business context.

type Contextual = {
  subject_type: string;
  subject_id: string;
  business_context?: Record<string, unknown>;
};

const text = (value: unknown) => (value == null ? "" : String(value).trim());

/** The record's business name and kind; null name when the context names none. */
export function historyRecord(event: Contextual): {
  name: string | null;
  kind: string;
  id: string;
} {
  const context = event.business_context || {};
  const named = text(context.name);
  const sku = text(context.sku);
  const parts = named
    ? [named, sku]
    : [text(context.party), text(context.item), sku, text(context.reference)];
  const name = [...new Set(parts.filter(Boolean))].join(" · ");
  return { name: name || null, kind: event.subject_type, id: event.subject_id };
}

/** An opaque id shortened for a glance; the full id stays in the details. */
export function shortId(id: string): string {
  const [prefix, rest] = id.includes("_")
    ? [id.slice(0, id.indexOf("_") + 1), id.slice(id.indexOf("_") + 1)]
    : ["", id];
  return rest.length > 6 ? `${prefix}…${rest.slice(-4)}` : id;
}
