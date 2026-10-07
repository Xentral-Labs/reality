import { useState } from "react";
import { formatNumber, formatCalendarDate, t } from "../localization";
import type { CockpitObservation } from "./cockpitModel";
import {
  cockpitOriginSelection,
  navigationSelection,
  selectionUrl,
  type Selection,
} from "./routing";

type Deviation = NonNullable<CockpitObservation["deviations"]>[number];

function DeviationTable({
  rows,
  selection,
  compact = false,
}: {
  rows: Deviation[];
  selection: Selection;
  compact?: boolean;
}) {
  if (!rows.length) return null;
  const proposalUrl = (id: string) =>
    selectionUrl(
      navigationSelection(selection, {
        route: "inspector",
        inspectorView: "records",
        inspectorTargetKind: "change_proposal",
        inspectorTargetId: id,
        cockpitOrigin: cockpitOriginSelection(selection),
      }),
    );
  const causeText = (blocker: Record<string, unknown>) =>
    typeof blocker.detail === "string"
      ? t(blocker.detail)
      : typeof blocker.explanation === "string"
        ? t(blocker.explanation)
        : typeof blocker.code === "string"
          ? t(blocker.code)
          : "—";
  return (
    <div
      className="cockpit-deviation-table-wrap"
      role="region"
      tabIndex={0}
      aria-label={t("Shipping deviations & recorded actions")}
    >
      <table className="cockpit-deviation-table" data-deviation-table>
        <thead>
          <tr>
            <th scope="col">{t("Order")}</th>
            <th scope="col">{t("Recorded cause")}</th>
            <th scope="col">{t("Responsibility")}</th>
            <th scope="col">{t("Recorded case action")}</th>
          </tr>
        </thead>
        {rows.map((row) => {
          const blockers = Object.values(row.blockers).flat();
          const blocker = blockers[0];
          const action = row.recorded_case_actions[0];
          return (
            <tbody
              key={row.order_id}
              data-deviation-preview={compact ? undefined : ""}
              data-briefing-order={compact ? row.order_id : undefined}
            >
              <tr data-deviation-summary>
                <th scope="row">
                  <a
                    href={selectionUrl(
                      navigationSelection(selection, {
                        route: "orders-deliveries",
                        ordersView: "customer-orders",
                        entry: row.order_id,
                        cockpitCase: row.case_id || undefined,
                        cockpitOrigin: cockpitOriginSelection({
                          ...selection,
                          cockpitCase: row.case_id || undefined,
                        }),
                      }),
                    )}
                  >
                    {row.number || row.order_id}
                  </a>
                </th>
                <td>
                  <span className={`cockpit-business-badge ${row.at_risk ? "risk" : "attention"}`}>
                    {t(row.at_risk ? "At risk" : "Data incomplete")}
                  </span>
                  <p className="cockpit-blocker">
                    {blocker
                      ? causeText(blocker)
                      : t(
                          row.coverage_gaps.length > 0
                            ? "Required evidence is incomplete"
                            : "No blocker recorded",
                        )}
                  </p>
                </td>
                <td>
                  <span
                    className={`cockpit-business-badge ${row.responsibility === "human" ? "manual" : row.responsibility === "automation" ? "automatic" : "unavailable"}`}
                  >
                    {t(
                      row.responsibility === "human"
                        ? "Manually taken over"
                        : row.responsibility === "automation"
                          ? "With automation"
                          : "No linked operational case",
                    )}
                  </span>
                </td>
                <td>
                  {action ? (
                    <a href={proposalUrl(action.proposal_id)}>
                      {action.type || t("Recorded action")} ·{" "}
                      <span className="cockpit-business-badge automatic">{t(action.status)}</span>
                    </a>
                  ) : (
                    <span className="cockpit-note">{t("No recorded response on this case")}</span>
                  )}
                </td>
              </tr>
              {!compact && (
                <tr className="cockpit-deviation-detail-row">
                  <td colSpan={4}>
                    <details className="cockpit-deviation-evidence">
                      <summary>
                        {t("Causes and recorded actions")} ·{" "}
                        {formatNumber(row.recorded_case_actions.length)} {t("actions")}
                      </summary>
                      {blockers.map((held, index) => (
                        <p className="cockpit-blocker" key={index}>
                          {causeText(held)}
                        </p>
                      ))}
                      {row.coverage_gaps.length > 0 && (
                        <p>{t("Required evidence is incomplete")}</p>
                      )}
                      {row.recorded_case_actions.length === 0 ? (
                        <p>{t("No recorded response on this case")}</p>
                      ) : (
                        <>
                          <ul className="cockpit-deviation-actions">
                            {row.recorded_case_actions.map((held) => (
                              <li key={held.proposal_id}>
                                <a href={proposalUrl(held.proposal_id)}>
                                  {held.type || t("Recorded action")}
                                </a>{" "}
                                · {t(held.status)}
                              </li>
                            ))}
                          </ul>
                          <p className="cockpit-note">
                            {t(
                              "Case-linked actions do not establish a response to this blocker or an external delivery outcome.",
                            )}
                          </p>
                        </>
                      )}
                    </details>
                  </td>
                </tr>
              )}
            </tbody>
          );
        })}
      </table>
    </div>
  );
}

export function OperationsDeviationsPanel({
  value,
  selection,
  inspect,
  embedded = false,
  compact = false,
}: {
  embedded?: boolean;
  compact?: boolean;
  value: CockpitObservation;
  selection: Selection;
  inspect: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const rows = value.deviations || [];
  const shown = expanded ? rows : rows.slice(0, 4);
  if (compact)
    return (
      <section className="cockpit-briefing" data-deviation-briefing>
        <p className="cockpit-note">
          {t("Shipping risks")} · {formatCalendarDate(value.shipping.business_day)} ·{" "}
          {value.shipping.time_zone}
        </p>
        {value.deviation_total == null && (
          <p className="cockpit-note">
            {t("Shipping deviations cannot be evaluated without a complete daily plan.")}
          </p>
        )}
        {value.deviation_total === 0 && (
          <p className="cockpit-note">{t("No deviations in the current shipping observation")}</p>
        )}
        <DeviationTable rows={rows.slice(0, 3)} selection={selection} compact />
        <p className="cockpit-footnote">
          {t(
            "Case-linked actions do not establish a response to this blocker or an external delivery outcome.",
          )}
        </p>
        <p className="cockpit-note">
          {formatNumber(Math.min(rows.length, 3))} {t("shown of")}{" "}
          {value.deviation_total == null ? "—" : formatNumber(value.deviation_total)}{" "}
          {t("affected orders")}
        </p>
        <button className="br-btn" onClick={inspect}>
          {t("Inspect all affected orders")}
        </button>
      </section>
    );
  return (
    <section
      className={`cockpit-deviations ${embedded ? "" : "cockpit-card"}`}
      data-operational-deviations
    >
      <div className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Shipping risks")}</span>
          <h2>{t("What is holding up shipping")}</h2>
          <p>
            {t(
              "Causes, responsibility and recorded case actions. Agents handle their cases automatically.",
            )}
          </p>
        </div>
        <strong>{value.deviation_total == null ? "—" : formatNumber(value.deviation_total)}</strong>
      </div>
      {value.deviation_total == null && (
        <p className="cockpit-note">
          {t("Shipping deviations cannot be evaluated without a complete daily plan.")}
        </p>
      )}
      {value.deviation_total === 0 && (
        <p className="cockpit-note">{t("No deviations in the current shipping observation")}</p>
      )}
      <DeviationTable rows={shown} selection={selection} />
      {rows.length > 0 && (
        <div className="cockpit-pagination cockpit-preview-navigation">
          <span className="cockpit-note">
            {formatNumber(shown.length)} {t("shown of")}{" "}
            {value.deviation_total == null ? "—" : formatNumber(value.deviation_total)}{" "}
            {t("affected orders")}
          </span>
          <div className="cockpit-actions">
            {rows.length > 4 && (
              <button
                className="br-btn"
                onClick={() => setExpanded(!expanded)}
                aria-expanded={expanded}
              >
                {t(expanded ? "Show fewer deviations" : "Show more deviations")}
              </button>
            )}
            <button className="br-btn" onClick={inspect}>
              {t("Inspect all affected orders")}
            </button>
          </div>
        </div>
      )}
      {value.deviations_has_more && (
        <p>
          {t("Showing a bounded sample. Inspect supporting orders for the full matching result.")}
        </p>
      )}
    </section>
  );
}
