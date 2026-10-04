import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { formatDateTime, t } from "../localization";
import { DecisionLine } from "./DecisionLine";
import { EmailEvidencePanel, emailReviewInput } from "./EmailEvidencePanel";
import { ActionCard } from "./ActionCard";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";
import {
  BusinessFieldList,
  DecisionActionBar,
  DecisionReviewHeader,
  ProposalApprovalRequirement,
  TechnicalDetails,
} from "./DecisionReview";
import { proposalBusinessLabel } from "./proposalPresentation";

export function ProposalReviewCard({
  tenant,
  proposalId,
  close,
  prepared,
}: {
  tenant: string;
  proposalId: string;
  close: () => void;
  /** A revised proposal replaces this one; the host keeps it addressable (spec 119 FR-003). */
  prepared?: (id: string) => void;
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
        prepared={prepared}
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
  const privateChange =
    Boolean(data.private_review) ||
    data.tool === "graph.reports.change" ||
    data.tool === "graph.requests.create" ||
    "private_report_change" in data.input ||
    "requested_analysis" in data.input;
  const readablePrivate = data.private_review?.state === "readable";
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
        title={
          privateChange ? "Review private change" : proposalBusinessLabel(data.tool, data.label)
        }
        close={close}
        busy={working}
        titleId="proposal-review-title"
      />
      {data.purpose && <p className="mt-2 text-sm text-fg-default">{t(data.purpose)}</p>}
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
      <ProposalApprovalRequirement nextStep={data.next_step} />
      {data.message && (
        <p role="alert" className="mt-4 rounded-xl bg-surface-muted p-4">
          {t(data.message)}
        </p>
      )}
      <section className="mt-5">
        <h3 className="font-semibold">{t(privateChange ? "Proposed change" : "Stated input")}</h3>
        <div className="mt-2 rounded-xl bg-surface-muted p-4">
          {privateChange ? (
            readablePrivate ? (
              <BusinessFieldList
                record={data.private_review?.details || {}}
                omit={["proposal_id", "status", "kind"]}
              />
            ) : (
              <p className="text-sm text-fg-muted">
                {t(
                  data.private_review?.message ||
                    "This change is private. Only its original author can view its contents.",
                )}
              </p>
            )
          ) : (
            <>
              <div
                data-original-content={data.tool === "email_dispatch_authorize" || undefined}
                className={data.tool === "email_dispatch_authorize" ? "whitespace-pre-wrap" : ""}
              >
                <BusinessFieldList
                  record={
                    data.tool === "email_dispatch_authorize"
                      ? emailReviewInput(data.input)
                      : data.input
                  }
                />
              </div>
              {data.tool === "email_dispatch_authorize" && (
                <EmailEvidencePanel
                  tenant={tenant}
                  proposalId={proposalId}
                  decisionStatus={data.status}
                />
              )}
            </>
          )}
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
      {(!privateChange || readablePrivate) && data.tool !== "email_dispatch_authorize" && (
        <section className="mt-5">
          <h3 className="font-semibold">
            {t(data.status === "proposed" ? "Prepared preview" : "Stored receipt")}
          </h3>
          <div className="mt-2 rounded-xl bg-surface-muted p-4">
            <BusinessFieldList record={content} />
          </div>
        </section>
      )}
      {(!privateChange || readablePrivate) && (
        <TechnicalDetails
          value={{
            input: privateChange ? data.private_review?.details : data.input,
            [data.status === "proposed" ? "preview" : "receipt"]: content,
          }}
        />
      )}
      {error && (
        <p role="alert" className="mt-4 text-critical-text">
          {error}
        </p>
      )}
      {(data.rejectable || data.confirmable) && (
        <DecisionActionBar
          busy={working}
          reject={data.rejectable ? () => void decide(false) : undefined}
          confirm={
            data.confirmable && (!privateChange || readablePrivate)
              ? () => void decide(true)
              : undefined
          }
          confirmLabel="Confirm change"
        />
      )}
    </dialog>
  );
}
