// Since spec 276 a deep-linked proposal loads through /change-proposals/{id}/review, and a
// delivery-kind review hands it to the shared action card. Fixtures answer that read with
// the proposal they already hold.
export const isDecisionReview = (path) => /\/change-proposals\/[^/]+\/review$/.test(path);
export function deliveryReview(proposal) {
  return {
    id: proposal.id,
    tool: proposal.tool,
    label: proposal.tool,
    purpose: "",
    review_kind: "delivery",
    status: proposal.status,
    actor_type: "human",
    created_at: "2026-09-08T12:00:00Z",
    decided_at: null,
    decider: null,
    input: proposal.review?.intent ?? proposal.intent ?? {},
    preview: {},
    receipt: {},
    next_step: {
      review_required: true,
      required_principal: "authorized_human",
      reconciliation_read: "delivery_proposal_detail",
      verification_reads: [],
    },
  };
}
