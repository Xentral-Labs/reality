import "./operationalCases.css";
import type { OperationalCase } from "../api";
import { t } from "../localization";
import type { useOperationalCaseControls } from "./useOperationalCaseControls";

type Controls = ReturnType<typeof useOperationalCaseControls>;
export function OperationalCaseControls({
  row,
  controls,
  canControl,
}: {
  row: OperationalCase;
  controls: Controls;
  canControl: boolean;
}) {
  const { busy, confirm, review } = controls;
  if (!canControl) return null;
  return (
    <div className="operational-case-controls">
      {row.control_mode === "automation" ? (
        <button className="br-btn" disabled={busy} onClick={() => controls.beginTakeover(row)}>
          {t("Take over manually / stop automation")}
        </button>
      ) : (
        <button className="br-btn" disabled={busy} onClick={() => controls.prepare(row)}>
          {t("Review before returning to automation")}
        </button>
      )}
      {confirm !== "adopt" && confirm?.case_id === row.case_id && (
        <div
          role="group"
          aria-label={t("Confirm manual takeover")}
          className="operational-case-review"
        >
          <p>
            {t("Stop new automated actions for this case? Already started actions remain visible.")}
          </p>
          <p>{t("Related cases are not automatically taken over.")}</p>
          <label className="br-field">
            {t("Takeover reason")}
            <textarea
              className="br-control"
              value={controls.reason}
              maxLength={1000}
              disabled={busy || controls.reasonLocked}
              onChange={(e) => controls.setReason(e.target.value)}
            />
          </label>
          <div className="operational-case-actions">
            <button className="br-btn" disabled={busy} onClick={() => controls.takeover()}>
              {t("Confirm manual takeover")}
            </button>
            <button className="br-btn" disabled={busy} onClick={() => controls.setConfirm(null)}>
              {t("Cancel")}
            </button>
          </div>
        </div>
      )}
      {review?.case_id === row.case_id && (
        <div
          className="operational-case-review"
          role="group"
          aria-label={t("Return to automation")}
        >
          <p>
            {t(
              "The current state will be checked again when you confirm. Old plans will not be resumed.",
            )}
          </p>
          <ul>
            {review.work.map((work) => (
              <li key={work.commitment_id}>
                {t("Open quantity")}: {work.open_quantity} · {work.commitment_id}
              </li>
            ))}
          </ul>
          {review.unsettled_actions.length > 0 && (
            <p>
              {t(
                "An execution is unresolved. Stopping automation does not cancel an action already started.",
              )}
            </p>
          )}
          {review.coverage_gaps.length > 0 && (
            <p>{t("Relevant source changes still need reconciliation.")}</p>
          )}
          <div className="operational-case-actions">
            <button
              className="br-btn"
              disabled={
                busy || review.unsettled_actions.length > 0 || review.coverage_gaps.length > 0
              }
              onClick={() => controls.handback()}
            >
              {t("Return to automation")}
            </button>
            <button className="br-btn" disabled={busy} onClick={() => controls.setReview(null)}>
              {t("Cancel")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
