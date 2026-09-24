import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { formatDateTime, t } from "../localization";
import { DecisionLine } from "./DecisionLine";
import { ActionCard } from "./ActionCard";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";

export function ProposalReviewCard({
  tenant,
  proposalId,
  close,
}: {
  tenant: string;
  proposalId: string;
  close: () => void;
}) {
  const review = useRead(() => api.proposalReview(tenant, proposalId), [tenant, proposalId]);
  const dialog = useRef<HTMLDialogElement>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    dialog.current?.showModal();
    return () => previous?.focus();
  }, []);
  if (!review.data)
    return (
      <dialog
        ref={dialog}
        className="m-auto rounded-xl border border-border-default bg-surface p-6"
        onCancel={(event) => {
          event.preventDefault();
          close();
        }}
      >
        {review.error ? <p role="alert">{review.error}</p> : <ReadLine />}
        <button className="br-btn mt-4" onClick={close}>
          {t("Close")}
        </button>
      </dialog>
    );
  if (review.data.review_kind === "delivery")
    return (
      <ActionCard
        tenant={tenant}
        proposalId={proposalId}
        tool="reserve"
        close={close}
        settled={close}
      />
    );

  const decide = async (approve: boolean) => {
    setWorking(true);
    setError("");
    try {
      if (approve) await api.approveProposal(tenant, proposalId, null);
      else await api.rejectProposal(tenant, proposalId, null);
      await review.refresh();
    } catch (failure) {
      setError(
        failure instanceof Error ? failure.message : t("The proposal could not be decided."),
      );
    } finally {
      setWorking(false);
    }
  };
  const data = review.data;
  const content = data.status === "proposed" ? data.preview : data.receipt;
  return (
    <dialog
      ref={dialog}
      className="m-auto max-h-[90vh] w-[min(720px,calc(100vw-2rem))] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default"
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
    >
      <h2 className="text-xl font-semibold text-fg-strong">{t(data.label)}</h2>
      {data.purpose && <p className="mt-2 text-sm text-fg-default">{data.purpose}</p>}
      <p className="mt-2 text-sm text-fg-muted">
        {t(data.actor_type === "agent" ? "Proposed by an agent" : "Prepared for review")} ·{" "}
        {formatDateTime(data.created_at)}
      </p>
      {data.status !== "proposed" && (
        <p className="mt-1 text-sm" data-decision-attribution>
          <DecisionLine
            decision={{
              id: data.id,
              outcome: data.status,
              decided_at: data.decided_at,
              decider: data.decider || { kind: "unknown" },
            }}
            link={false}
          />
        </p>
      )}
      {data.next_step.required_principal === "authenticated_active_owner" && (
        <p className="mt-4 rounded-xl bg-surface-muted p-4 text-sm">
          {t("Owner decision required")}.{" "}
          {t("An authenticated company owner must approve or reject this finance proposal.")}
        </p>
      )}
      {data.message && (
        <p role="alert" className="mt-4 rounded-xl bg-surface-muted p-4">
          {t(data.message)}
        </p>
      )}
      <section className="mt-5">
        <h3 className="font-semibold">{t("Stated input")}</h3>
        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-xl bg-surface-muted p-4 text-xs">
          {JSON.stringify(data.input, null, 2)}
        </pre>
      </section>
      {data.status !== "proposed" && (
        <p className="mt-4 text-sm text-fg-muted">
          {t("Reconcile with")} <code>{data.next_step.reconciliation_read}</code>
          {data.next_step.verification_reads.length > 0 && (
            <>
              {" "}
              · {t("Verify with")} <code>{data.next_step.verification_reads.join(", ")}</code>
            </>
          )}
        </p>
      )}
      <section className="mt-5">
        <h3 className="font-semibold">
          {t(data.status === "proposed" ? "Prepared preview" : "Stored receipt")}
        </h3>
        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-xl bg-surface-muted p-4 text-xs">
          {JSON.stringify(content, null, 2)}
        </pre>
      </section>
      {error && (
        <p role="alert" className="mt-4 text-critical-text">
          {error}
        </p>
      )}
      <div className="mt-6 flex flex-wrap justify-end gap-2">
        <button className="br-btn" disabled={working} onClick={close}>
          {t("Close")}
        </button>
        {data.rejectable && (
          <button className="br-btn" disabled={working} onClick={() => void decide(false)}>
            {t("Reject")}
          </button>
        )}
        {data.confirmable && (
          <button
            className="br-btn br-btn-primary"
            disabled={working}
            onClick={() => void decide(true)}
          >
            {t("Confirm")}
          </button>
        )}
      </div>
    </dialog>
  );
}
