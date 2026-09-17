// Presentation only: every original field remains available in row details.
const labels = {
  en: {
    party: "Business partner",
    external_order_id: "Order reference",
    document_number: "Document number",
    due_at: "Due date",
    ship_ready: "Ready to ship",
    readiness: "Status",
    blocking_reasons: "Blocking reasons",
    priority: "Priority",
    lines: "Items",
    sku: "SKU",
    item: "Item",
    name: "Name",
    physical: "Physical stock",
    reserved: "Reserved",
    available: "Available",
    incoming: "Incoming",
    quantity: "Quantity",
    status: "Status",
    source_system: "Source",
    description: "Description",
    currency: "Currency",
    amount: "Amount",
    unit: "Unit",
    location: "Location",
  } as Record<string, string>,
};
export const reportFieldLabel = (key: string, report?: string): string =>
  key === "party" && report === "fulfillment_queue" ? "Customer" : labels.en[key] || key;
const dispatch = [
  "party",
  "external_order_id",
  "due_at",
  "ship_ready",
  "blocking_reasons",
  "priority",
  "lines",
];
const general = [
  "name",
  "sku",
  "item",
  "party",
  "document_number",
  "physical",
  "reserved",
  "available",
  "incoming",
  "quantity",
  "status",
];
export function reportColumns(name: string, rows: Record<string, unknown>[]): string[] {
  const keys = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  const preferred =
    name === "fulfillment_queue" ? dispatch.filter((key) => keys.includes(key)) : [];
  if (preferred.length) return preferred;
  const business = keys.filter(
    (key) =>
      key === "external_order_id" ||
      !(key === "id" || key.endsWith("_id") || key.endsWith("_ids") || key === "order_key"),
  );
  if (!business.length) return keys;
  return [
    ...general.filter((key) => business.includes(key)),
    ...business.filter((key) => !general.includes(key)),
  ];
}
