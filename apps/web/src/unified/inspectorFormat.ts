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
