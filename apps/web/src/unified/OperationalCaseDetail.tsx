import { useEffect, useState } from "react";
import { operationalCases, type OperationalCase } from "../api";
import { t } from "../localization";

export function OperationalCaseDetail({
  tenant,
  documentId,
}: {
  tenant: string;
  documentId?: string;
}) {
  const [status, setStatus] = useState<{
    adopted: boolean;
    can_adopt: boolean;
    can_control: boolean;
  } | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [rows, setRows] = useState<OperationalCase[]>([]);
  const [review, setReview] = useState<(OperationalCase & { digest: string }) | null>(null);
  const [confirm, setConfirm] = useState<OperationalCase | "adopt" | null>(null);
  const [requestKey, setRequestKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
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
  async function act(operation: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await operation();
      setReview(null);
      setConfirm(null);
      setRefresh((value) => value + 1);
    } catch (failure: unknown) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }
  async function prepare(value: OperationalCase) {
    setBusy(true);
    setError("");
    setReview(null);
    setRequestKey(crypto.randomUUID());
    try {
      setReview(await operationalCases.review(tenant, value.case_id));
    } catch (failure: unknown) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }
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
    <details className="br-card" data-operational-cases>
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
      {status && !status.adopted && (
        <p>{t("Case coordination is not enabled. Existing work remains unchanged.")}</p>
      )}
      {status?.can_adopt && !status.adopted && (
        <button
          className="br-btn"
          disabled={busy}
          onClick={() => {
            setRequestKey(crypto.randomUUID());
            setConfirm("adopt");
          }}
        >
          {t("Enable cases for new work")}
        </button>
      )}
      {confirm === "adopt" && (
        <div>
          <p>
            {t(
              "New orders and announced returns will receive cases. Existing orders are not taken over.",
            )}
          </p>
          <button
            className="br-btn"
            disabled={busy}
            onClick={() => act(() => operationalCases.adopt(tenant, requestKey))}
          >
            {t("Confirm activation")}
          </button>
          <button className="br-btn" disabled={busy} onClick={() => setConfirm(null)}>
            {t("Cancel")}
          </button>
        </div>
      )}
      {status?.adopted && visible.length === 0 && <p>{t("No adopted cases in this view.")}</p>}
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
              href={`/app/inspector?tenant=${encodeURIComponent(tenant)}&inspector_view=records&inspector_target_kind=${row.order_document_id ? "document" : "commitment"}&inspector_target_id=${encodeURIComponent(row.order_document_id || row.work[0]?.commitment_id || "")}`}
            >
              {t("Show details")}
            </a>
          </p>
          <ul>
            {row.work.map((work) => (
              <li key={work.commitment_id}>
                <a
                  href={`/app/inspector?tenant=${encodeURIComponent(tenant)}&inspector_view=records&inspector_target_kind=commitment&inspector_target_id=${encodeURIComponent(work.commitment_id)}`}
                >
                  {work.commitment_id}
                </a>
                {" · "}
                {t("Open quantity")}: {work.open_quantity}
              </li>
            ))}
            {row.source_record_ids.map((id) => (
              <li key={id}>
                <a
                  href={`/app/inspector?tenant=${encodeURIComponent(tenant)}&inspector_view=records&inspector_target_kind=source_record&inspector_target_id=${encodeURIComponent(id)}`}
                >
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
          {status?.can_control && row.control_mode === "automation" && (
            <button
              className="br-btn"
              disabled={busy}
              onClick={() => {
                setReview(null);
                setRequestKey(crypto.randomUUID());
                setConfirm(row);
              }}
            >
              {t("Take over manually / stop automation")}
            </button>
          )}
          {status?.can_control && row.control_mode === "human" && (
            <button className="br-btn" disabled={busy} onClick={() => prepare(row)}>
              {t("Review before returning to automation")}
            </button>
          )}
          {confirm !== "adopt" && confirm?.case_id === row.case_id && (
            <div>
              <p>
                {t(
                  "Stop new automated actions for this case? Already started actions remain visible.",
                )}
              </p>
              <button
                className="br-btn"
                disabled={busy}
                onClick={() => act(() => operationalCases.takeover(tenant, row, requestKey))}
              >
                {t("Confirm manual takeover")}
              </button>
              <button className="br-btn" disabled={busy} onClick={() => setConfirm(null)}>
                {t("Cancel")}
              </button>
            </div>
          )}
          {review?.case_id === row.case_id && (
            <div>
              <p>
                {t(
                  "The current state will be checked again when you confirm. Old plans will not be resumed.",
                )}
              </p>
              <ul>
                {review.work.map((work) => (
                  <li key={work.commitment_id}>
                    {work.commitment_id}: {work.open_quantity}
                  </li>
                ))}
              </ul>
              <button
                className="br-btn"
                disabled={
                  busy || review.unsettled_actions.length > 0 || review.coverage_gaps.length > 0
                }
                onClick={() =>
                  act(() =>
                    operationalCases.handback(tenant, row.case_id, review.digest, requestKey),
                  )
                }
              >
                {t("Return to automation")}
              </button>
              <button className="br-btn" disabled={busy} onClick={() => setReview(null)}>
                {t("Cancel")}
              </button>
            </div>
          )}
        </section>
      ))}
    </details>
  );
}
