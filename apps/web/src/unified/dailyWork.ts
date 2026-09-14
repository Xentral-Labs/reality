import type { Selection } from "./routing";

export const dailyWork = [
  {
    label: "Commitments",
    total: "open_deliveries",
    selection: {
      route: "orders-deliveries",
      ordersView: "commitments",
      deliveryType: "customer_delivery",
      deliveryStatus: "open",
      commitment: "",
      order: "",
      entry: "",
      proposal: "",
      q: "",
      page: 1,
    },
  },
  {
    label: "Exceptions",
    total: "exceptions",
    selection: {
      route: "attention",
      exception: "",
      severity: "",
      proposal: "",
      q: "",
      page: 1,
    },
  },
  {
    label: "Decisions",
    total: "pending_decisions",
    selection: {
      route: "decisions",
      proposal: "",
      q: "",
      page: 1,
    },
  },
] as const satisfies readonly {
  label: string;
  total: "open_deliveries" | "exceptions" | "pending_decisions";
  selection: Partial<Selection>;
}[];

export function isCommitmentsSelection(selection: Selection): boolean {
  return selection.route === "orders-deliveries" && selection.ordersView === "commitments";
}
