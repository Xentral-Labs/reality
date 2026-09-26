import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { formatDateTime, t } from "../localization";
import { DecisionLine } from "./DecisionLine";
import { ActionCard } from "./ActionCard";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";
import { BusinessFieldList, DecisionActionBar, DecisionReviewHeader } from "./DecisionReview";

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
        aria-labelledby="proposal-review-title"
        aria-busy={review.loading}
        className="m-auto max-h-[90vh] min-h-72 w-[min(720px,calc(100vw-2rem))] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
        onCancel={(event) => {
          event.preventDefault();
          close();
        }}
      >
        <DecisionReviewHeader
          category="Decision required"
          title="Review decision"
          close={close}
          titleId="proposal-review-title"
        />
        {review.error ? (
          <ReadState error={review.error} retry={review.refresh} />
        ) : (
          <ReadState loading rows={5} retry={review.refresh} />
        )}
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
      aria-labelledby="proposal-review-title"
      className="m-auto max-h-[90vh] w-[min(720px,calc(100vw-2rem))] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default"
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
    >
      <DecisionReviewHeader
        category={data.status === "proposed" ? "Decision required" : "Decision"}
        title={data.label}
        close={close}
        busy={working}
        titleId="proposal-review-title"
      />
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
        <div className="mt-2 rounded-xl bg-surface-muted p-4">
          <BusinessFieldList record={data.input} />
        </div>
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
        <div className="mt-2 rounded-xl bg-surface-muted p-4">
          <BusinessFieldList record={content} />
        </div>
      </section>
      {error && (
        <p role="alert" className="mt-4 text-critical-text">
          {error}
        </p>
      )}
      {(data.rejectable || data.confirmable) && (
        <DecisionActionBar
          busy={working}
          reject={data.rejectable ? () => void decide(false) : undefined}
          confirm={data.confirmable ? () => void decide(true) : undefined}
          confirmLabel="Confirm change"
        />
      )}
    </dialog>
  );
}
