import type { ProposalReviewKind } from "../api";

export type ProposalReviewLocation = {
  route: "data-sources" | "master-data" | "analytics" | "decisions";
  proposal: string;
  importProposal?: string;
  analyticsProposal?: string;
  analyticsView?: "graph";
};

/** Map the server-owned review class to its single Web destination. */
export function proposalReviewLocation(
  proposal: string,
  reviewKind: ProposalReviewKind,
): ProposalReviewLocation {
  if (reviewKind === "import")
    return { route: "data-sources", proposal: "", importProposal: proposal };
  if (reviewKind === "reference") return { route: "master-data", proposal };
  if (reviewKind === "analytics_report")
    return {
      route: "analytics",
      proposal: "",
      analyticsProposal: proposal,
      analyticsView: "graph",
    };
  return { route: "decisions", proposal };
}
