import { formatDate, formatDateTime, formatMoney, formatQuantity } from "../localization";
import { renderInspectorValue, type InspectorPart } from "./inspectorPresentation";
export function inspectorValue(value: unknown, parts?: InspectorPart[]) {
  return renderInspectorValue(value, parts, {
    number: formatQuantity,
    money: formatMoney,
    date: formatDate,
    dateTime: formatDateTime,
  });
}
/** The qualifier a row carries beside its value: when it happened, what state it is in. */
export function inspectorMeta(row: { meta?: string; meta_parts?: InspectorPart[] }) {
  return row.meta ? inspectorValue(row.meta, row.meta_parts) : "";
}
/** Value and qualifier as one string, for the places that have room for only one. */
export function inspectorRowText(row: {
  value: unknown;
  display_parts?: InspectorPart[];
  meta?: string;
  meta_parts?: InspectorPart[];
}) {
  const meta = inspectorMeta(row);
  const value = inspectorValue(row.value, row.display_parts);
  return meta ? `${value} · ${meta}` : value;
}
