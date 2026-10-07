import { useEffect, useId, useState } from "react";
import { operationalCases, type OperationalCase } from "../api";
import { formatDateTimeInZone, formatNumber, t } from "../localization";
import { ReadState } from "./ReadState";
import { useCockpitLiveRead } from "./useCockpitLiveRead";
import { useOperationalCaseControls } from "./useOperationalCaseControls";
import { OperationalCaseControls } from "./OperationalCaseControls";
import {
  cockpitOriginSelection,
  navigationSelection,
  selectionUrl,
  type Selection,
} from "./routing";

export function OperationalCaseRegister({
  selection,
  zone,
}: {
  selection: Selection;
  zone: string;
}) {
  const workspaceId = useId();
  const [expanded, setExpanded] = useState(Boolean(selection.cockpitCase));
  const [mode, setMode] = useState<"outstanding" | "human" | "all">("human");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState("");
  const [cursor, setCursor] = useState("");
  const [readRefresh, setReadRefresh] = useState(0);
  const [selected, setSelected] = useState<OperationalCase | null>(null);
  const [canControl, setCanControl] = useState(false);
  const controls = useOperationalCaseControls(selection.tenant, selected?.case_id || "");
  const state = useCockpitLiveRead(
    `${selection.tenant}:${mode}:${cursor}:${query}:${kind}:${controls.refresh}:${readRefresh}`,
    (signal) =>
      operationalCases.register(
        selection.tenant,
        {
          limit: "6",
          after: cursor,
          query,
          ...(kind ? { kind } : {}),
          ...(mode === "human"
            ? { control_mode: "human" }
            : mode === "outstanding"
              ? { outstanding_only: "true" }
              : {}),
        },
        signal,
      ),
  );
  const page = state.data;
  useEffect(() => {
    if (!selection.cockpitCase) return;
    setExpanded(true);
    let active = true;
    operationalCases
      .explain(selection.tenant, selection.cockpitCase, 50)
      .then((value) => {
        if (active) setSelected(value);
      })
      .catch((failure) => {
        if (active) controls.setError(failure.message);
      });

    return () => {
      active = false;
    };
  }, [selection.tenant, selection.cockpitCase]);
  useEffect(() => {
    let active = true;
    setCanControl(false);
    operationalCases
      .status(selection.tenant)
      .then((value) => {
        if (active) setCanControl(value.can_control === true);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [selection.tenant]);
  useEffect(() => {
    if (state.status === "denied") {
      setSelected(null);
      setCanControl(false);
      controls.setConfirm(null);
      controls.setReview(null);
    }
  }, [state.status]);
  useEffect(() => {
    if (controls.refresh && selected) {
      let active = true;
      operationalCases
        .explain(selection.tenant, selected.case_id, 50)
        .then((value) => {
          if (active) setSelected(value);
        })
        .catch((failure) => {
          if (active) controls.setError(failure.message);
        });
      return () => {
        active = false;
      };
    }
  }, [controls.refresh, selection.tenant, selected?.case_id]);
  const link = (kind: string, id: string) =>
    selectionUrl(
      navigationSelection(selection, {
        route: "inspector",
        inspectorView: "records",
        inspectorTargetKind: kind,
        inspectorTargetId: id,
        cockpitOrigin: cockpitOriginSelection({ ...selection, cockpitCase: selected?.case_id }),
      }),
    );
  const caseInspection = selected && (
    <article
      id={`case-inspection-${selected.case_id}`}
      className="cockpit-basis"
      data-case-inspection
    >
      <div className="cockpit-card-heading">
        <h3>{t("Case inspection")}</h3>
        <button className="br-btn" disabled={controls.busy} onClick={() => setSelected(null)}>
          {t("Close case inspection")}
        </button>
      </div>
      <p>
        {t(
          selected.control_mode === "human"
            ? "Manually owned — automation stopped"
            : "Automation owns this work",
        )}
      </p>
      {selected.control && (
        <p>
          <span>{selected.control.actor_label}</span> ·{" "}
          {selected.control.recorded_at ? (
            <time data-control-time dateTime={selected.control.recorded_at}>
              {formatDateTimeInZone(selected.control.recorded_at, zone)}
            </time>
          ) : (
            "—"
          )}{" "}
          · {selected.control.reason}
          <br />
          <a href={link("business_event", selected.control.event_id)}>{t("Control receipt")}</a>
        </p>
      )}
      {selected.order_document_id && (
        <a
          href={selectionUrl(
            navigationSelection(selection, {
              route: "orders-deliveries",
              ordersView: "customer-orders",
              entry: selected.order_document_id,
              cockpitCase: selected.case_id,
              cockpitOrigin: cockpitOriginSelection({
                ...selection,
                cockpitCase: selected.case_id,
              }),
            }),
          )}
        >
          {t("Continue in order workspace")}
        </a>
      )}
      <ul>
        {selected.work.map((work) => (
          <li key={work.commitment_id}>
            <a href={link("commitment", work.commitment_id)}>
              {t("Open quantity")}: {work.open_quantity}
            </a>
          </li>
        ))}
        {selected.source_record_ids.map((id) => (
          <li key={id}>
            <a href={link("source_record", id)}>{t("Source record")}</a>
          </li>
        ))}
      </ul>
      {selected.related_case_ids.length > 0 && (
        <p>{t("Related cases are not automatically taken over.")}</p>
      )}
      {selected.unsettled_actions.length > 0 && (
        <p>
          {t(
            "An execution is unresolved. Stopping automation does not cancel an action already started.",
          )}
        </p>
      )}
      {controls.error && <p role="alert">{controls.error}</p>}
      <OperationalCaseControls row={selected} controls={controls} canControl={canControl} />
    </article>
  );
  return (
    <section className="cockpit-card cockpit-case-register" data-case-register>
      <div className="cockpit-case-entry">
        <div className="cockpit-case-introduction">
          <span className="cockpit-eyebrow">{t("Responsibility")}</span>
          <h2>{t("Cases & takeover")}</h2>
          <p>{t("The system automatically handles order fulfillment and announced returns.")}</p>
          <p className="cockpit-note">
            {t(
              "Want to continue yourself? Select a case and confirm manual takeover. The system then stops starting new automated actions for that case.",
            )}
          </p>
        </div>
        <div className="cockpit-case-entry-actions">
          <div className="cockpit-case-counts">
            {(["automation", "human"] as const).map((owner) => (
              <button
                className="br-btn cockpit-case-count"
                key={owner}
                data-case-count={owner}
                aria-controls={workspaceId}
                aria-expanded={expanded}
                disabled={controls.busy}
                onClick={() => {
                  setMode(owner === "human" ? "human" : "outstanding");
                  setCursor("");
                  setExpanded(true);
                }}
              >
                <span>{t(owner === "human" ? "Manually taken over" : "With automation")}:</span>{" "}
                <strong>{page?.counts ? formatNumber(page.counts[owner]) : "—"}</strong>
              </button>
            ))}
          </div>
          <button
            className="br-btn cockpit-case-toggle"
            aria-expanded={expanded}
            aria-controls={workspaceId}
            disabled={controls.busy}
            onClick={() => {
              if (!expanded) {
                setMode("outstanding");
                setCursor("");
              }
              setExpanded((value) => !value);
            }}
          >
            {t(expanded ? "Hide case list" : "Select a case")}
          </button>
        </div>
      </div>
      <p className="cockpit-note">
        {t(
          "Find stopped cases under Manually taken over. Taking over a case does not mark its work as completed.",
        )}
      </p>
      {state.status === "stale" && (
        <p role="status">{t("Previous observation — refresh failed")}</p>
      )}
      {state.status === "denied" && <p role="status">{t("Access unavailable")}</p>}
      {page && (
        <p className="cockpit-note">
          {t("Data observed at")}:{" "}
          {page.observed_at ? (
            <time data-observed-at dateTime={page.observed_at}>
              {formatDateTimeInZone(page.observed_at, zone)}
            </time>
          ) : (
            t("Unknown")
          )}
        </p>
      )}
      {page?.coordination && !page.coordination.migration_ready && (
        <p role="alert">{t("Operational case upgrade requires the database migration.")}</p>
      )}
      {page?.coordination?.migration_ready && !page.coordination.coverage_ready && (
        <p role="status">{t("Operational case upgrade is still reconciling existing work.")}</p>
      )}
      {page?.coordination?.last_error_code && (
        <p role="alert">{page.coordination.last_error_code}</p>
      )}
      {!expanded && mode === "human" && page && state.status !== "denied" && (
        <div className="cockpit-manual-preview" data-manual-preview>
          <h3>{t("Manually taken over")}</h3>
          {page.items.length === 0 ? (
            <p className="cockpit-note">{t("No manually owned cases")}</p>
          ) : (
            <ul>
              {page.items.slice(0, 3).map((row) => (
                <li key={row.case_id}>
                  <button
                    className="br-link"
                    onClick={() => {
                      setSelected(row);
                      setExpanded(true);
                    }}
                  >
                    <strong>
                      {row.business_reference ||
                        row.order_document_id ||
                        row.return_announcement_id}
                    </strong>
                    <small>{t("Manually owned — automation stopped")}</small>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {page.total > 3 && (
            <p className="cockpit-note">{t("More cases are available in the manual register.")}</p>
          )}
        </div>
      )}
      <div
        id={workspaceId}
        className="cockpit-case-workspace"
        data-case-workspace
        hidden={!expanded}
      >
        <form
          className="cockpit-actions cockpit-case-search"
          onSubmit={(event) => {
            event.preventDefault();
            setQuery(search);
            setCursor("");
          }}
        >
          <label className="br-field">
            {t("Search order or case")}
            <input
              className="br-control"
              type="search"
              maxLength={200}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
          <label className="br-field">
            {t("Case kind")}
            <select
              className="br-control"
              value={kind}
              onChange={(event) => {
                setKind(event.target.value);
                setCursor("");
              }}
            >
              <option value="">{t("All cases")}</option>
              <option value="order_fulfillment">{t("Order fulfillment")}</option>
              <option value="customer_return">{t("Announced return")}</option>
            </select>
          </label>
          <button className="br-btn" type="submit">
            {t("Search")}
          </button>
        </form>
        <div className="cockpit-selection" role="group" aria-label={t("Case register filter")}>
          {(["outstanding", "human", "all"] as const).map((value) => (
            <button
              className="br-btn"
              key={value}
              aria-pressed={mode === value}
              onClick={() => {
                setMode(value);
                setCursor("");
              }}
            >
              {t(
                value === "human"
                  ? "Manually taken over"
                  : value === "all"
                    ? "All cases"
                    : "Still open",
              )}
            </button>
          ))}
        </div>
        {!page && state.status !== "denied" && (
          <ReadState
            loading={!state.error}
            error={state.error ? t("Could not load this view") : undefined}
            retry={() => setReadRefresh((value) => value + 1)}
          />
        )}
        {page && (
          <>
            <p className="cockpit-note">
              {t("Matching cases")}: {formatNumber(page.total)}
            </p>
            <ul className="cockpit-case-list">
              {page.items.map((row) => (
                <li key={row.case_id} data-case-id={row.case_id}>
                  <div>
                    <strong>
                      {row.business_reference ||
                        row.order_document_id ||
                        row.return_announcement_id}
                    </strong>
                    <small>
                      {t(
                        row.kind === "order_fulfillment" ? "Order fulfillment" : "Announced return",
                      )}
                    </small>
                  </div>
                  <span className="cockpit-responsibility">
                    {t(
                      row.control_mode === "human"
                        ? "Manually owned — automation stopped"
                        : "Automation owns this work",
                    )}
                  </span>
                  <span className="cockpit-case-state">
                    {t(
                      row.goal_state === "outstanding"
                        ? "Work remains"
                        : row.goal_state === "abandoned"
                          ? "Work withdrawn"
                          : "Work completed",
                    )}
                  </span>
                  <button
                    className="br-btn"
                    aria-expanded={selected?.case_id === row.case_id}
                    aria-controls={
                      selected?.case_id === row.case_id
                        ? `case-inspection-${row.case_id}`
                        : undefined
                    }
                    onClick={() => setSelected(selected?.case_id === row.case_id ? null : row)}
                  >
                    {t("Case details")}
                  </button>
                  {selected?.case_id === row.case_id && caseInspection}
                </li>
              ))}
            </ul>
            {page.adopted && page.items.length === 0 && <p>{t("No cases in this view.")}</p>}
            <div className="cockpit-pagination">
              <span className="cockpit-note">
                {formatNumber(page.items.length)} {t("cases on this page")} ·{" "}
                {formatNumber(page.total)} {t("matching cases")}
              </span>
              <div className="cockpit-actions">
                {cursor && (
                  <button className="br-btn" onClick={() => setCursor("")}>
                    {t("Back to beginning")}
                  </button>
                )}
                <button
                  className="br-btn"
                  disabled={!page.has_more}
                  onClick={() => setCursor(page.next_after || "")}
                >
                  {t("Next cases")}
                </button>
              </div>
            </div>
          </>
        )}
        {selected && !page?.items.some((row) => row.case_id === selected.case_id) && caseInspection}
      </div>
    </section>
  );
}
