import { useEffect, useRef, useState, type ReactNode } from "react";
import { operationalCases, type OperationalCaseRegisterPage } from "../api";
import { formatNumber, formatZonedDateTime, t } from "../localization";
import { ReadState } from "./ReadState";
import {
  cockpitOriginSelection,
  navigationSelection,
  selectionUrl,
  type Selection,
} from "./routing";

export type BusinessCaseSnapshot = {
  tenant: string;
  page?: OperationalCaseRegisterPage;
  status: string;
};
const families = [
  { kind: "order_fulfillment", title: "Order fulfillment", scope: "Reservations and shipping" },
  { kind: null, title: "Purchasing", scope: "Supplier work" },
  { kind: "customer_return", title: "Announced return", scope: "Receipt and physical processing" },
  { kind: null, title: "Customer inquiries", scope: "Message handling" },
  { kind: null, title: "Financial clarification", scope: "Financial work" },
  { kind: null, title: "Master data", scope: "Source and structure" },
] as const;
const columns = [
  { key: "total", label: "Registered cases", filter: "all" },
  { key: "outstanding", label: "Work remains", filter: "outstanding" },
  { key: "automation", label: "With automation", filter: "automation" },
  { key: "human", label: "Manually taken over", filter: "human" },
] as const;
type Inspection = { kind: string; title: string; filter: (typeof columns)[number]["filter"] };

function CasePreview({
  selection,
  inspection,
  close,
}: {
  selection: Selection;
  inspection: Inspection;
  close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLElement | null>(null);
  const [page, setPage] = useState<OperationalCaseRegisterPage>();
  const [error, setError] = useState<string>();
  useEffect(() => {
    trigger.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialog.current?.showModal();
    return () => {
      dialog.current?.close();
      trigger.current?.focus({ preventScroll: true });
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    operationalCases
      .register(
        selection.tenant,
        {
          kind: inspection.kind,
          limit: "6",
          ...(inspection.filter === "outstanding" ? { outstanding_only: "true" } : {}),
          ...(["human", "automation"].includes(inspection.filter)
            ? { control_mode: inspection.filter }
            : {}),
        },
        controller.signal,
      )
      .then(setPage)
      .catch((failure) => {
        if (!controller.signal.aborted) setError(failure.message);
      });
    return () => controller.abort();
  }, [selection.tenant, inspection.kind, inspection.filter]);
  return (
    <dialog
      ref={dialog}
      className="cockpit-instrument-dialog"
      aria-label={t("Business case inspection")}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) close();
      }}
    >
      <div className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Business cases in operation")}</span>
          <h2>{t(inspection.title)}</h2>
          <p>{t(columns.find((column) => column.filter === inspection.filter)!.label)}</p>
        </div>
        <button className="br-btn" onClick={close}>
          {t("Close")}
        </button>
      </div>
      {!page && (
        <ReadState loading={!error} error={error ? t("Could not load this view") : undefined} />
      )}
      {page && (
        <>
          <p className="cockpit-note">
            {t("Data observed at")}:{" "}
            {page.observed_at ? formatZonedDateTime(page.observed_at) : "—"}
          </p>
          <ul className="cockpit-case-preview-list">
            {page.items.map((row) => (
              <li key={row.case_id}>
                <a
                  href={selectionUrl(
                    navigationSelection(
                      selection,
                      row.order_document_id
                        ? {
                            route: "orders-deliveries",
                            ordersView: "customer-orders",
                            entry: row.order_document_id,
                            cockpitCase: row.case_id,
                            cockpitOrigin: cockpitOriginSelection(selection),
                          }
                        : {
                            route: "inspector",
                            inspectorView: "records",
                            inspectorTargetKind: "return_announcement",
                            inspectorTargetId: row.return_announcement_id || undefined,
                            cockpitOrigin: cockpitOriginSelection(selection),
                          },
                    ),
                  )}
                >
                  {row.business_reference || row.case_id}
                </a>
                <span
                  className={`cockpit-business-badge ${row.control_mode === "human" ? "manual" : "automatic"}`}
                >
                  {t(row.control_mode === "human" ? "Manually taken over" : "With automation")}
                </span>
                <span>
                  {t(
                    row.goal_state === "outstanding"
                      ? "Work remains"
                      : row.goal_state === "abandoned"
                        ? "Work withdrawn"
                        : "Work completed",
                  )}
                </span>
              </li>
            ))}
          </ul>
          {page.items.length === 0 && <p>{t("No records in this group")}</p>}
          <p className="cockpit-note">
            {formatNumber(page.items.length)} {t("shown of")} {formatNumber(page.total)} ·{" "}
            {t("Case details")}
          </p>
        </>
      )}
    </dialog>
  );
}

export function BusinessCaseOverview({
  selection,
  snapshot,
  children,
}: {
  selection: Selection;
  snapshot: BusinessCaseSnapshot | null;
  children: ReactNode;
}) {
  const overview = useRef<HTMLDetailsElement>(null);
  const management = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    if (selection.cockpitCase) {
      if (overview.current) overview.current.open = true;
      if (management.current) management.current.open = true;
    }
  }, [selection.cockpitCase]);
  const [inspection, setInspection] = useState<Inspection | null>(null);
  useEffect(() => {
    if (snapshot?.status === "denied") setInspection(null);
  }, [snapshot?.status]);
  const page =
    snapshot?.tenant === selection.tenant && snapshot.status !== "denied"
      ? snapshot.page
      : undefined;
  return (
    <details ref={overview} className="cockpit-upper-disclosure" data-business-case-overview>
      <summary>
        <strong>{t("Business cases in operation")}</strong>
        <span className="cockpit-business-badge automatic">
          {t("With automation")} · {page?.counts ? formatNumber(page.counts.automation) : "—"}
        </span>
        <span className="cockpit-business-badge manual">
          {t("Manually taken over")} · {page?.counts ? formatNumber(page.counts.human) : "—"}
        </span>
      </summary>
      {snapshot?.status === "stale" && (
        <p className="cockpit-note" role="status">
          {t("Previous observation — refresh failed")}
        </p>
      )}
      {page?.coordination && !page.coordination.coverage_ready && (
        <p className="cockpit-note" role="status">
          {t("Operational case upgrade is still reconciling existing work.")}
        </p>
      )}
      <div className="cockpit-case-table-wrap">
        <table className="cockpit-business-table">
          <caption>{t("Responsibility and open work by case kind")}</caption>
          <thead>
            <tr>
              <th>{t("Case kind")}</th>
              {columns.map((column) => (
                <th key={column.key}>{t(column.label)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {families.map((family) => (
              <tr key={family.title} data-business-kind={family.kind || "unsupported"}>
                <th scope="row">
                  <strong>{t(family.title)}</strong>
                  <small>{t(family.scope)}</small>
                  {!family.kind && (
                    <span className="cockpit-business-badge unavailable">
                      {t("No case takeover")}
                    </span>
                  )}
                </th>
                {columns.map((column) => (
                  <td key={column.key}>
                    {family.kind ? (
                      <button
                        className="cockpit-risk-trigger"
                        disabled={
                          typeof page?.kind_counts?.[family.kind]?.[column.key] !== "number"
                        }
                        onClick={() =>
                          setInspection({
                            kind: family.kind!,
                            title: family.title,
                            filter: column.filter,
                          })
                        }
                        aria-haspopup="dialog"
                        aria-label={`${t(family.title)} · ${t(column.label)}`}
                      >
                        {page?.kind_counts?.[family.kind]
                          ? formatNumber(page.kind_counts[family.kind][column.key])
                          : "—"}
                      </button>
                    ) : (
                      <span aria-label={t("Not available as a controllable case")}>—</span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="cockpit-footnote">
        {t(
          "Automation and manual ownership include completed cases. Open work is shown separately; ownership does not prove an Agent is currently running.",
        )}
      </p>
      <p className="cockpit-footnote">
        {t(
          "Only order fulfillment and announced returns currently support whole-case takeover. Other case families are not available.",
        )}
      </p>
      {page?.observed_at && (
        <p className="cockpit-footnote">
          {t("Data observed at")}: {formatZonedDateTime(page.observed_at)}
        </p>
      )}
      <details ref={management} className="cockpit-case-management" data-case-management>
        <summary>{t("Cases & takeover")}</summary>
        {children}
      </details>
      {inspection && page && (
        <CasePreview
          key={`${selection.tenant}:${inspection.kind}:${inspection.filter}`}
          selection={selection}
          inspection={inspection}
          close={() => setInspection(null)}
        />
      )}
    </details>
  );
}
