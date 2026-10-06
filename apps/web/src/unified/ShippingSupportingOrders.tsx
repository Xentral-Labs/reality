import { useEffect, useRef, useState } from "react";
import { cockpitApi } from "../api";
import { formatNumber, t } from "../localization";
import { ReadState } from "./ReadState";
import {
  cockpitOriginSelection,
  navigationSelection,
  selectionUrl,
  type Selection,
} from "./routing";
import type { ShippingOrderPage } from "./cockpitModel";
import { cockpitTime } from "./ShippingDayPanel";

export function ShippingSupportingOrders({
  selection,
  basis,
  zone,
  at,
  resolvedDay,
  close,
}: {
  selection: Selection;
  basis: string;
  zone: string;
  at?: string;
  resolvedDay: string;
  close: () => void;
}) {
  const region = useRef<HTMLElement | null>(null);
  useEffect(() => {
    region.current?.focus({ preventScroll: true });
    region.current?.scrollIntoView({ behavior: "instant", block: "nearest" });
  }, []);
  const [page, setPage] = useState<ShippingOrderPage | null>(null),
    [error, setError] = useState(""),
    [cursor, setCursor] = useState(""),
    [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(false);
  const key = JSON.stringify([
    selection.tenant,
    resolvedDay,
    selection.cockpitLocation,
    selection.cockpitMeasure,
    at,
  ]);
  useEffect(() => {
    setCursor("");
    setPage(null);
  }, [key]);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    cockpitApi
      .orders(
        selection.tenant,
        {
          day: resolvedDay,
          measure: selection.cockpitMeasure || "due",
          ...(selection.cockpitLocation && selection.cockpitMeasure !== "unplanned"
            ? { location_id: selection.cockpitLocation }
            : {}),
          ...(at ? { at } : {}),
          after: cursor,
          limit: "10",
          basis_key: basis,
        },
        controller.signal,
      )
      .then((result) => {
        if (active) setPage(result);
      })
      .catch((failure) => {
        if (active) {
          setError(failure.message);
          if ([401, 403, 404].includes(failure.status)) setPage(null);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
    // The inspection stays fixed while sibling live observations arrive. Refresh is explicit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, cursor, refresh]);
  return (
    <section
      ref={region}
      tabIndex={-1}
      data-shipping-inspection
      className="cockpit-card cockpit-order-inspection"
      aria-labelledby="supporting-orders-title"
    >
      <div className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Trace the result")}</span>
          <h2 id="supporting-orders-title">
            {t("Supporting orders")} · {t(selection.cockpitMeasure || "due")}
          </h2>
        </div>
        <div className="cockpit-actions">
          <button className="br-btn" onClick={() => setRefresh(refresh + 1)} disabled={loading}>
            {t("Refresh")}
          </button>
          <button className="br-btn" onClick={close}>
            {t("Close")}
          </button>
        </div>
      </div>
      {error && <ReadState error={error} retry={() => setRefresh(refresh + 1)} />}
      {!page && !error && <ReadState loading />}
      {page && (
        <>
          <p className="cockpit-note">
            {t("Business day")}: {resolvedDay} · {t("Matching orders")}:{" "}
            {page.total === null ? "—" : formatNumber(page.total)} · {t("Observed")}{" "}
            {cockpitTime(page.observed_at, zone)}
            {page.re_evaluated ? ` · ${t("Re-evaluated against the current basis")}` : ""}
          </p>
          {selection.cockpitMeasure === "unplanned" && (
            <p className="cockpit-note">
              {t(
                "Company-wide open work outside the selected day’s plan · no dispatch site or deadline is inferred",
              )}
            </p>
          )}
          <div className="cockpit-table-scroll">
            <table className="cockpit-table" aria-busy={loading}>
              <thead>
                <tr>
                  <th>{t("Order")}</th>
                  <th>{t("Deadline")}</th>
                  <th>{t("Handed over")}</th>
                  <th>{t("Forecast")}</th>
                  <th>{t("Recorded blockers")}</th>
                </tr>
              </thead>
              <tbody>
                {page.items.map((row) => (
                  <tr key={row.order_id}>
                    <th>
                      <a
                        href={selectionUrl(
                          navigationSelection(selection, {
                            route: "orders-deliveries",
                            ordersView: "customer-orders",
                            entry: row.order_id,
                            cockpitOrigin: cockpitOriginSelection(selection),
                          }),
                        )}
                      >
                        {row.number || row.order_id}
                      </a>
                    </th>
                    <td>{row.due_at ? cockpitTime(row.due_at, zone) : "—"}</td>
                    <td>{row.handover_at ? cockpitTime(row.handover_at, zone) : "—"}</td>
                    <td>{row.forecast_at ? cockpitTime(row.forecast_at, zone) : "—"}</td>
                    <td>
                      {Object.values(row.blockers)
                        .flat()
                        .map((blocker, index) => (
                          <span key={index} className="cockpit-blocker">
                            {typeof blocker.detail === "string"
                              ? t(blocker.detail)
                              : typeof blocker.explanation === "string"
                                ? t(blocker.explanation)
                                : blocker.code}
                          </span>
                        ))}
                      {row.coverage_gaps.map((gap) => (
                        <span key={gap} className="cockpit-blocker">
                          {gap}
                        </span>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {page.total === 0 && (
            <p className="cockpit-note">{t("No orders match this observation")}</p>
          )}
          {page.total === null && (
            <p className="cockpit-note">{t("The supporting cohort is unavailable")}</p>
          )}
          <div className="cockpit-pagination cockpit-pagination-actions">
            {cursor && (
              <button className="br-btn" disabled={loading} onClick={() => setCursor("")}>
                {t("Back to beginning")}
              </button>
            )}
            <button
              className="br-btn"
              disabled={!page.has_more || loading}
              onClick={() => setCursor(page.next_after || "")}
            >
              {t("Next orders")}
            </button>
          </div>
        </>
      )}
    </section>
  );
}
