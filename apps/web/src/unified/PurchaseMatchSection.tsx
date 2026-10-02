import { purchaseMatchApi } from "../api";
import { formatMoney, formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";

// Spec 310: the three-way match of a purchase order, per line, read from the
// shared service; this section only shows it.
const DIFFERENCES: Record<string, string> = {
  received_short: "Received less than in force",
  received_over: "Received more than in force",
  billed_short: "Billed less than received",
  billed_over: "Billed more than received",
  price_differs: "Billed at another price",
  units_not_comparable: "Units cannot be compared",
};

export function PurchaseMatchSection({ tenant, document }: { tenant: string; document: string }) {
  const read = useRead(() => purchaseMatchApi.read(tenant, document), [tenant, document]);
  const match = read.data;
  if (!match) return read.loading ? <ReadLine /> : null;
  if (!match.lines.length) return null;
  return (
    <section className="mt-4 text-sm" data-purchase-match>
      <div className="font-medium text-fg-strong">
        {t("Three-way match")}:{" "}
        <span className={match.matched ? "text-positive-text" : "text-warning-text"}>
          {match.matched ? t("Matched") : t("Not matched")}
        </span>
      </div>
      <table className="mt-2 w-full text-left">
        <thead className="text-fg-muted">
          <tr>
            <th className="py-1 pr-3 font-normal">{t("Item")}</th>
            <th className="py-1 pr-3 font-normal">{t("Ordered")}</th>
            <th className="py-1 pr-3 font-normal">{t("Received")}</th>
            <th className="py-1 pr-3 font-normal">{t("Billed")}</th>
            <th className="py-1 pr-3 font-normal">{t("Agreed price")}</th>
            <th className="py-1 font-normal">{t("Match")}</th>
          </tr>
        </thead>
        <tbody>
          {match.lines.map((line) => (
            <tr key={line.document_line_id} className="border-t border-border-default align-top">
              <td className="py-1 pr-3">
                {line.sku ? `${line.sku} · ` : ""}
                {line.item}
              </td>
              <td className="py-1 pr-3">
                {formatQuantity(line.in_force)}
                {line.in_force !== line.ordered && (
                  <span className="block text-fg-muted">
                    {t("Ordered")} {formatQuantity(line.ordered)}
                  </span>
                )}
              </td>
              <td className="py-1 pr-3">{formatQuantity(line.received)}</td>
              <td className="py-1 pr-3">
                {line.billed !== null ? formatQuantity(line.billed) : "–"}
              </td>
              <td className="py-1 pr-3">
                {line.agreed_unit_price !== null
                  ? formatMoney(line.agreed_unit_price, match.currency, 4)
                  : "–"}
                {line.ordered_unit_price !== null &&
                  line.agreed_unit_price !== line.ordered_unit_price && (
                    <span className="block text-fg-muted">
                      {t("Ordered at")} {formatMoney(line.ordered_unit_price, match.currency, 4)}
                    </span>
                  )}
              </td>
              <td className="py-1">
                {line.cancelled && <span className="block">{t("Cancelled")}</span>}
                {line.matched ? (
                  <span className="text-positive-text">{t("Matched")}</span>
                ) : (
                  line.differences.map((code) => (
                    <span key={code} className="block text-warning-text">
                      {t(DIFFERENCES[code] || code)}
                    </span>
                  ))
                )}
                {line.charges.map((charge) => (
                  <span key={charge.document_line_id} className="block text-fg-muted">
                    {t("Charge")} {formatMoney(charge.amount, match.currency)}
                  </span>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
