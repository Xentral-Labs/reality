import { t } from "../localization";

/** Render the shared service's observations; do not infer missing business facts here. */
export function CompletenessIssues({ issues }: { issues: string[] }) {
  if (!issues.length) return null;
  return (
    <ul className="mt-3 list-disc pl-5 text-sm" data-order-completeness>
      {issues.map((issue, index) => {
        const sourceLine = /^line:(\d+):(amount_unstated|price_unstated|item_unknown)$/.exec(issue);
        const observedLine = /^Line (\d+) states no (unit price|line amount)\.$/.exec(issue);
        let label = t(issue);
        if (sourceLine) {
          const text =
            sourceLine[2] === "amount_unstated"
              ? t("Line amount was not stated.")
              : sourceLine[2] === "price_unstated"
                ? t("Unit price was not stated.")
                : t("Unknown item");
          label = `${Number(sourceLine[1]) + 1}: ${text}`;
        } else if (observedLine) {
          label = `${observedLine[1]}: ${observedLine[2] === "unit price" ? t("Unit price was not stated.") : t("Line amount was not stated.")}`;
        }
        return <li key={index}>{label}</li>;
      })}
    </ul>
  );
}
