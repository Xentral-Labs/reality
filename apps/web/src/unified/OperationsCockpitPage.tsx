import { useEffect, useRef, useState } from "react";
import { cockpitApi } from "../api";
import { formatNumber, t } from "../localization";
import { useCockpitLiveRead } from "./useCockpitLiveRead";
import { ReadState } from "./ReadState";
import { ShippingDayPanel, cockpitTime } from "./ShippingDayPanel";
import { ShippingSupportingOrders } from "./ShippingSupportingOrders";
import { OperationsActivityPanel } from "./OperationsActivityPanel";
import { OperationalCaseRegister } from "./OperationalCaseRegister";
import { OperationsDeviationsPanel } from "./OperationsDeviationsPanel";
import {
  OperatingFlowsPanel,
  OperatingStatusPanel,
  type AnalysisAreaKey,
} from "./OperatingFlowsPanel";
import { OperationsWorkspacePanel } from "./OperationsWorkspacePanel";
import { AgentAccessPanel } from "./AgentAccessPanel";
import type { ShippingMeasure } from "./cockpitModel";
import type { Selection } from "./routing";
import "./operationsCockpit.css";

export function OperationsCockpitPage({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const inspectionTrigger = useRef<HTMLElement | SVGElement | null>(null);
  const [inspection, setInspection] = useState<{ at?: string; day: string } | null>(null);
  const [sites, setSites] = useState<{ location_id: string; name: string }[]>([]);
  const bookmarkedArea = (): AnalysisAreaKey => {
    const area = window.location.hash.replace("#cockpit-flow-", "");
    return ["shipping", "orders", "messages", "supply", "stock", "returns"].includes(area)
      ? (area as AnalysisAreaKey)
      : "shipping";
  };
  const [selectedArea, setSelectedArea] = useState<AnalysisAreaKey>(bookmarkedArea);
  const previousCompany = useRef(selection.tenant);
  const selectArea = (area: AnalysisAreaKey) => {
    setSelectedArea(area);
    history.replaceState(
      history.state,
      "",
      `${window.location.pathname}${window.location.search}#cockpit-flow-${area}`,
    );
  };
  useEffect(() => {
    const change = () => setSelectedArea(bookmarkedArea());
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    if (previousCompany.current !== selection.tenant) {
      previousCompany.current = selection.tenant;
      setSelectedArea("shipping");
      if (window.location.hash.startsWith("#cockpit-flow-")) {
        history.replaceState(null, "", window.location.pathname + window.location.search);
      }
    }
  }, [selection.tenant]);
  const day = selection.cockpitDay || "today",
    location = selection.cockpitLocation || "";
  const state = useCockpitLiveRead(`${selection.tenant}:${day}:${location}`, (signal) =>
    cockpitApi.overview(selection.tenant, day, location, signal),
  );
  const minutes = selection.cockpitMinutes || 15;
  const activityState = useCockpitLiveRead(`${selection.tenant}:activity:${minutes}`, (signal) =>
    cockpitApi.activity(selection.tenant, minutes, signal),
  );
  const value = state.data?.shipping;
  useEffect(() => {
    setInspection(null);
    setSites([]);
  }, [selection.tenant]);
  useEffect(() => {
    if (value && !location) setSites(value.sites);
  }, [value, location]);
  useEffect(() => {
    if (state.status === "denied" || activityState.status === "denied") navigate({ route: "home" });
  }, [state.status, activityState.status, navigate]);
  const inspect = (measure: ShippingMeasure, at?: string) => {
    selectArea("shipping");
    inspectionTrigger.current =
      document.activeElement instanceof HTMLElement || document.activeElement instanceof SVGElement
        ? document.activeElement
        : null;
    navigate({ cockpitMeasure: measure, cockpitBasis: value?.basis_key });
    if (value) setInspection({ at, day: value.business_day });
  };
  return (
    <div className="operations-cockpit">
      <header className="cockpit-header">
        <div>
          <span className="cockpit-eyebrow">{t("Company operations")}</span>
          <h1>{t("Control Tower")}</h1>
          <p>{t("Observe results. Take over a case only when you need to.")}</p>
        </div>
        <div className="cockpit-filters">
          <label className="br-field">
            {t("Business day")}
            <select
              className="br-control"
              value={day === "today" ? "today" : "pinned"}
              onChange={(event) =>
                navigate({
                  cockpitDay:
                    event.target.value === "today" ? "today" : value?.business_day || "today",
                })
              }
            >
              <option value="today">{t("Today · follows company day")}</option>
              <option value="pinned" disabled={!value}>
                {t("Pinned date")}
              </option>
            </select>
          </label>
          {day !== "today" && (
            <label className="br-field">
              {t("Date")}
              <input
                className="br-control"
                type="date"
                value={day}
                onChange={(event) => {
                  if (event.target.value) navigate({ cockpitDay: event.target.value });
                }}
              />
            </label>
          )}
          <label className="br-field">
            {t("Dispatch site")}
            <select
              className="br-control"
              value={location}
              onChange={(event) => navigate({ cockpitLocation: event.target.value })}
            >
              <option value="">{t("All dispatch sites")}</option>
              {(sites.length ? sites : value?.sites || []).map((site) => (
                <option key={site.location_id} value={site.location_id}>
                  {site.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>
      <div className={`cockpit-status ${state.status}`} role="status">
        <span className="cockpit-status-dot" />
        <strong>
          {t(
            state.status === "current"
              ? "Live observation"
              : state.status === "stale"
                ? "Previous observation — refresh failed"
                : state.status === "suspended"
                  ? "Live updates suspended while hidden"
                  : state.status === "denied"
                    ? "Access unavailable"
                    : "Loading…",
          )}
        </strong>
        {value && (
          <span>
            {t("Data observed at")} {cockpitTime(value.observed_at, value.time_zone)} ·{" "}
            {value.business_day}
          </span>
        )}
      </div>
      {!value && Boolean(state.error) && (
        <ReadState
          error={state.error instanceof Error ? state.error.message : t("Could not load this view")}
        />
      )}
      {!value && !state.error && <ReadState loading rows={7} />}
      {value && (
        <>
          <OperatingStatusPanel
            value={activityState.data?.flows}
            stale={activityState.status !== "current"}
            selection={selection}
          />
          <div className="cockpit-console-row" data-console-primary>
            <div className="cockpit-analysis-column">
              <OperatingFlowsPanel
                value={activityState.data?.flows}
                selection={selection}
                stale={activityState.status !== "current"}
                selected={selectedArea}
                select={selectArea}
                shipping={
                  <>
                    <ShippingDayPanel
                      value={value}
                      inspect={inspect}
                      selection={selection}
                      embedded
                    />
                    {state.data && (
                      <details className="cockpit-shipping-deviations" data-shipping-deviations>
                        <summary>
                          <strong>{t("What is holding up shipping")}</strong>
                          <span>
                            {t("Affected orders")}:{" "}
                            {state.data.deviation_total === undefined
                              ? "—"
                              : formatNumber(state.data.deviation_total)}
                          </span>
                        </summary>
                        <OperationsDeviationsPanel
                          value={state.data}
                          selection={selection}
                          inspect={() => inspect("risk")}
                          embedded
                        />
                      </details>
                    )}
                  </>
                }
              />
              {inspection && (
                <div hidden={selectedArea !== "shipping"} data-shipping-investigation>
                  <ShippingSupportingOrders
                    key={`${selection.tenant}:${day}:${location}:${selection.cockpitMeasure}:${inspection.at}`}
                    selection={selection}
                    at={inspection.at}
                    resolvedDay={inspection.day}
                    basis={selection.cockpitBasis || value.basis_key}
                    zone={value.time_zone}
                    close={() => {
                      setInspection(null);
                      requestAnimationFrame(() =>
                        inspectionTrigger.current?.focus({ preventScroll: true }),
                      );
                    }}
                  />
                </div>
              )}
            </div>
            <div className="cockpit-log-column">
              <OperationsWorkspacePanel
                key={selection.tenant}
                responsibility={
                  <OperationalCaseRegister
                    key={selection.tenant}
                    selection={selection}
                    zone={value.time_zone}
                  />
                }
                activity={
                  <OperationsActivityPanel
                    state={activityState}
                    key={selection.tenant}
                    selection={selection}
                    navigate={navigate}
                  />
                }
                agents={<AgentAccessPanel key={selection.tenant} tenant={selection.tenant} />}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
