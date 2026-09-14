import type { RealityGapDetail } from "../api";

export const wizardStages = [
  "Choose a goal",
  "Find a real example",
  "Describe the rule",
  "Test with existing data",
  "Review and activate",
] as const;
export type WizardStage = 0 | 1 | 2 | 3 | 4;
export const usesWizard = (statuses: string[]) =>
  !statuses.some((s) => s === "active" || s === "disabled");
export const latestDraft = (detail: RealityGapDetail | null) =>
  detail?.rules.filter((r) => r.status === "draft").sort((a, b) => b.version - a.version)[0];
export function resumeStage(detail: RealityGapDetail | null): WizardStage {
  if (!detail) return 0;
  if (detail.gap.destination !== "fact") return 1;
  return latestDraft(detail) ? 3 : 2;
}
export const ruleStarters = [
  {
    title: "Delivery instructions",
    description: "Keep the delivery instruction stated on an order.",
    question: "What delivery instruction was stated on this order?",
    purpose: "Help the warehouse follow the customer's delivery instructions.",
    predicate: "order.delivery_instruction",
  },
  {
    title: "Priority handling",
    description: "Remember a priority flag supplied with an order.",
    question: "Does the source mark this order for priority handling?",
    purpose: "Help the team identify orders marked as a priority.",
    predicate: "order.priority_flag",
  },
  {
    title: "My own rule",
    description: "Start with a different property stated in your data.",
    question: "",
    purpose: "",
    predicate: "",
  },
] as const;
