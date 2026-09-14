import type { Selection } from "./routing";
export type StarterTask = "attention" | "delivery" | "invoices";
export type ActiveTask = { task: StarterTask; tenant: string } | null;
export const promptKey = (user: string) => `reality.trial.github-dismissed:${user}`;
export function resultCompletesTask(
  active: ActiveTask,
  task: StarterTask,
  tenant: string,
  ready: boolean,
): boolean {
  return ready && active?.task === task && active.tenant === tenant;
}
export function starterSelection(task: StarterTask, tenant: string): Partial<Selection> {
  const clear = {
    tenant,
    q: "",
    page: 1,
    proposal: "",
    commitment: "",
    order: "",
    entry: "",
    exception: "",
    severity: "",
    partyId: "",
  };
  if (task === "attention") return { ...clear, route: "attention" };
  if (task === "delivery")
    return {
      ...clear,
      route: "orders-deliveries",
      ordersView: "commitments",
      deliveryType: "customer_delivery",
      deliveryStatus: "open",
    };
  return {
    ...clear,
    route: "finance",
    financeView: "open-items",
    flow: "receivable",
    financeStatus: "outstanding",
  };
}
