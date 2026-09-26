import type { InspectorData } from "../api";
import { t } from "../localization";
import { CostExplanation } from "./CostExplanation";

export function DocumentContributionExplanations({
  tenant,
  detail,
  source,
}: {
  tenant: string;
  detail: InspectorData;
  source: "document_lines" | "billed_invoice_lines";
}) {
  const lines = detail.evidence_lines || [];
  const scopes =
    source === "document_lines"
      ? lines.map((line) => ({ id: line.id, label: line.label }))
      : lines.flatMap((line) =>
          (line.billing?.evidence || []).map((invoice) => ({
            id: invoice.invoice_line_id,
            label: `${line.label} · ${invoice.number}`,
          })),
        );
  const unique = [...new Map(scopes.map((scope) => [scope.id, scope])).values()];
  if (!unique.length) return null;
  return (
    <section className="mt-5 space-y-4" aria-label={t("Contribution by invoice line")}>
      <h3>{t("Contribution by invoice line")}</h3>
      {unique.map((scope) => (
        <div key={scope.id}>
          <p className="text-sm font-medium text-fg-strong">{scope.label}</p>
          <CostExplanation
            tenant={tenant}
            kind="contribution"
            scopeId={scope.id}
            scopeLabel={scope.label}
          />
        </div>
      ))}
    </section>
  );
}
