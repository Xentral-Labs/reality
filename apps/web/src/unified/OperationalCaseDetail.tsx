import { useEffect, useState } from "react";
import { operationalCases, type OperationalCase } from "../api";
import { useOperationalCaseControls } from "./useOperationalCaseControls";
import { OperationalCaseControls } from "./OperationalCaseControls";
import { t } from "../localization";
import { navigationSelection, selectionUrl, type Selection } from "./routing";

export function OperationalCaseDetail({
  tenant,
  documentId,
  initiallyOpen = false,
  selection,
}: {
  tenant: string;
  documentId?: string;
  initiallyOpen?: boolean;
  selection?: Selection;
}) {
  const [expanded, setExpanded] = useState(initiallyOpen);
  const inspectorLink = (kind: string, id: string) =>
    selection?.tenant === tenant
      ? selectionUrl(
          navigationSelection(selection, {
            route: "inspector",
            inspectorView: "records",
            inspectorTargetKind: kind,
            inspectorTargetId: id,
          }),
        )
      : `/app/inspector?tenant=${encodeURIComponent(tenant)}&inspector_view=records&inspector_target_kind=${kind}&inspector_target_id=${encodeURIComponent(id)}`;
  const [status, setStatus] = useState<{
    adopted: boolean;
    migration_ready: boolean;
    coverage_ready: boolean;
    last_error_code: string | null;
    can_control: boolean;
  } | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [rows, setRows] = useState<OperationalCase[]>([]);
  const controls = useOperationalCaseControls(tenant, documentId || "");
  const {
    setReview,
    setConfirm,
    confirm,
    requestKey,
    setRequestKey,
    busy,
    setBusy,
    error,
    setError,
    refresh,
    setRefresh,
    act,
  } = controls;
  useEffect(() => {
    let active = true;
    setStatus(null);
    setRows([]);
    setReview(null);
    setConfirm(null);
    setError("");
    const work = documentId
      ? operationalCases.object(tenant, documentId).then(async ({ case_ids }) => {
          const roots = await Promise.all(
            case_ids.map((id) => operationalCases.explain(tenant, id)),
          );
          const relatedIds = [...new Set(roots.flatMap((row) => row.related_case_ids))].filter(
            (id) => !case_ids.includes(id),
          );
          const related = await Promise.all(
            relatedIds.map((id) => operationalCases.explain(tenant, id)),
          );
          return [...roots, ...related];
        })
      : operationalCases.list(tenant);
    Promise.all([operationalCases.status(tenant), work])
      .then(([next, cases]) => {
        if (!Array.isArray(cases)) throw new Error(t("Could not load this view"));
        if (active) {
          setStatus(next);
          setRows(cases);
          setHasMore(!documentId && cases.length === 100);
        }
      })
      .catch((failure: unknown) => {
        if (active) setError(String(failure));
      });
    return () => {
      active = false;
    };
  }, [tenant, documentId, refresh]);
  const visible = documentId
    ? rows.filter(
        (row) =>
          row.order_document_id === documentId ||
          rows.some(
            (root) =>
              root.order_document_id === documentId && root.related_case_ids.includes(row.case_id),
          ),
      )
    : rows;
  return (
    <details
      className="br-card"
      data-operational-cases
      open={expanded}
      onToggle={(event) => setExpanded(event.currentTarget.open)}
    >
      <summary>{t("Operational cases")}</summary>
      <button className="br-btn" disabled={busy} onClick={() => setRefresh((value) => value + 1)}>
        {t("Refresh")}
      </button>
      {hasMore && (
        <button
          className="br-btn"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              const next = await operationalCases.list(tenant, rows.at(-1)?.case_id);
              if (!Array.isArray(next)) throw new Error(t("Could not load this view"));
              setRows((previous) => [...previous, ...next]);
              setHasMore(next.length === 100);
            } catch (failure: unknown) {
              setError(String(failure));
            } finally {
              setBusy(false);
            }
          }}
        >
          {t("Load more")}
        </button>
      )}
      {error && <p role="alert">{error}</p>}
      {status && !status.migration_ready && (
        <p role="alert">{t("Operational case upgrade requires the database migration.")}</p>
      )}
      {status?.migration_ready && !status.coverage_ready && (
        <p role="status">{t("Operational case upgrade is still reconciling existing work.")}</p>
      )}
      {status?.last_error_code && <p role="alert">{status.last_error_code}</p>}
      {status?.migration_ready && visible.length === 0 && <p>{t("No cases in this view.")}</p>}
      {visible.map((row) => (
        <section key={row.case_id} className="br-card" data-case-id={row.case_id}>
          <strong>
            {row.kind === "order_fulfillment" ? t("Order fulfillment") : t("Announced return")}
          </strong>
          <p>
            {row.control_mode === "human"
              ? t("Manually owned — automation stopped")
              : t("Automation owns this work")}
          </p>
          <p>
            {row.goal_state === "outstanding"
              ? t("Work remains")
              : row.goal_state === "abandoned"
                ? t("Work withdrawn")
                : t("Work completed")}
          </p>
          <code>{row.case_id}</code>{" "}
          <button
            className="br-btn"
            onClick={() =>
              navigator.clipboard
                .writeText(row.case_id)
                .catch((failure) => setError(String(failure)))
            }
          >
            {t("Copy case ID")}
          </button>
          <p>
            <a
              href={inspectorLink(
                row.order_document_id ? "document" : "commitment",
                row.order_document_id || row.work[0]?.commitment_id || "",
              )}
            >
              {t("Show details")}
            </a>
          </p>
          <ul>
            {row.work.map((work) => (
              <li key={work.commitment_id}>
                <a href={inspectorLink("commitment", work.commitment_id)}>{work.commitment_id}</a>
                {" · "}
                {t("Open quantity")}: {work.open_quantity}
              </li>
            ))}
            {row.source_record_ids.map((id) => (
              <li key={id}>
                <a href={inspectorLink("source_record", id)}>
                  {t("Source record")}: {id}
                </a>
              </li>
            ))}
          </ul>
          {row.unsettled_actions.length > 0 && (
            <p role="status">
              {t(
                "An execution is unresolved. Stopping automation does not cancel an action already started.",
              )}{" "}
              {row.unsettled_actions.join(", ")}
            </p>
          )}
          {row.coverage_gaps.length > 0 && (
            <p>{t("Relevant source changes still need reconciliation.")}</p>
          )}
          {row.actions.some((action) => action.obsolete) && (
            <p>{t("Older plans are obsolete and require a fresh review.")}</p>
          )}
          {row.related_case_ids.length > 0 && (
            <p>
              {t("Related cases are not automatically taken over.")}{" "}
              {row.related_case_ids.join(", ")}
            </p>
          )}
          <OperationalCaseControls
            row={row}
            controls={controls}
            canControl={Boolean(status?.can_control)}
          />
        </section>
      ))}
    </details>
  );
}
