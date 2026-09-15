import type { Selection } from "./routing";

const introductions = {
  home: {
    title: "Home",
    description: "See open commitments, exceptions and decisions across your company.",
  },
  customers: {
    title: "Commitments",
    description: "Track outstanding deliveries to your customers.",
  },
  suppliers: {
    title: "Commitments",
    description: "Track outstanding deliveries from your suppliers.",
  },
  attention: {
    title: "Exceptions",
    description: "Review issues that need attention and inspect the records behind them.",
  },
  decisions: {
    title: "Decisions",
    description: "Review proposed actions and decide whether to proceed.",
  },
  stock: {
    title: "Warehouse",
    description: "See physical, reserved and available stock for each item.",
  },
  reservations: {
    title: "Warehouse",
    description: "See which stock is reserved for each commitment.",
  },
  movements: {
    title: "Warehouse",
    description: "Follow recorded stock receipts, shipments and adjustments.",
  },
  "open-items": {
    title: "Finance",
    description: "See outstanding receivables and payables, grouped by currency.",
  },
  payments: {
    title: "Finance",
    description: "Review recorded incoming and outgoing payments.",
  },
  "finance-settings": {
    title: "Finance",
    description:
      "Manage accounts, internal classifications and source code mappings for this company.",
  },
  journal: {
    title: "Finance",
    description: "Inspect recorded ledger entries and their supporting records.",
  },
  balances: {
    title: "Finance",
    description:
      "See where each customer or supplier stands: open, overdue, available credit and balance per currency.",
  },
  overview: {
    title: "Reality Inspector",
    description: "Follow how sources, documents and business records connect over time.",
  },
  graph: {
    title: "Reality Inspector",
    description: "Explore a record and follow its links to related information.",
  },
  "all-records": {
    title: "Reality Inspector",
    description: "Explore your company’s recorded information and trace it to its sources.",
  },
  views: {
    title: "Reality Inspector",
    description: "Explore how existing records are combined into calculated views.",
  },
  rules: {
    title: "Reality Inspector",
    description:
      "Review the rules that record additional facts from source data on the right business record.",
  },
  exceptions: {
    title: "Reality Inspector",
    description: "Explore the conditions that identify issues requiring attention.",
  },
  history: {
    title: "Reality Inspector",
    description: "See what was recorded across your company, newest first.",
  },
  commands: {
    title: "Reality Inspector",
    description: "Explore available actions, their inputs and what they do.",
  },
  facts: {
    title: "Facts",
    description: "Explore additional observations, their sources and the records they describe.",
  },
  deliveries: {
    title: "Orders & deliveries",
    description: "Track delivery commitments and inspect their reservations and movements.",
  },
  "customer-orders": {
    title: "Orders & deliveries",
    description: "Review customer orders and follow their linked delivery commitments.",
  },
  "supplier-orders": {
    title: "Orders & deliveries",
    description: "Review purchase orders and follow their linked delivery commitments.",
  },
  customer: {
    title: "Master data",
    description: "Find customers and review their details and commercial defaults.",
  },
  supplier: {
    title: "Master data",
    description: "Find suppliers and review their details and commercial defaults.",
  },
  item: {
    title: "Master data",
    description: "Find items and review their reference details.",
  },
  location: {
    title: "Master data",
    description: "Find locations and review their reference details.",
  },
  systems: {
    title: "Integrations",
    description: "Plan integrations and manage registered data sources.",
  },
  records: {
    title: "Integrations",
    description: "Inspect received data, its import status and linked business records.",
  },
  documents: {
    title: "Integrations",
    description: "Inspect recorded documents and trace them to their original sources.",
  },
  analytics: {
    title: "Reports",
    description: "Explore your business. Trace every answer.",
  },
  company: {
    title: "Companies",
    description: "Switch companies or manage their users, agents and AI settings.",
  },
  personal: {
    title: "Profile & preferences",
    description: "Set your language, number format, timezone and appearance.",
  },
  "demo-data": {
    title: "Demo Data",
    description: "Control synthetic data arrivals and review recent demo activity.",
  },
  "free-play": {
    title: "Free play",
    description: "Chat freely with the company selected in the main navigation.",
  },
  storyline: {
    title: "Storyline",
    description: "Play a business flow step by step and read what each one recorded.",
  },
} as const;

export function pageIntroduction(
  selection: Pick<Selection, "route"> &
    Partial<Omit<Selection, "route" | "ordersView">> & { ordersView?: string },
) {
  const { route } = selection;
  let key: keyof typeof introductions;
  switch (route) {
    case "inspector": {
      const view = selection.inspectorView || "overview";
      key =
        view === "facts" || view === "records"
          ? "all-records"
          : ["overview", "graph", "views", "rules", "exceptions", "history", "commands"].includes(
                view,
              )
            ? (view as keyof typeof introductions)
            : "overview";
      break;
    }
    case "warehouse":
      key = selection.warehouseView || "stock";
      break;
    case "finance":
      key =
        selection.financeView === "settings"
          ? "finance-settings"
          : selection.financeView || "open-items";
      break;
    case "master-data":
      key = selection.family || "customer";
      break;
    case "data-sources":
      key = selection.dataView || "systems";
      break;
    case "orders-deliveries":
      key =
        selection.ordersView === "commitments"
          ? selection.deliveryType === "supplier_delivery"
            ? "suppliers"
            : "customers"
          : selection.ordersView === "supplier-orders"
            ? "supplier-orders"
            : selection.ordersView === "customer-orders"
              ? "customer-orders"
              : "deliveries";
      break;
    case "settings":
      key = selection.settingsView === "personal" ? "personal" : "company";
      break;
    case "copilot":
      key = "home";
      break;
    case "work":
      key = "deliveries";
      break;
    default:
      key = route;
  }
  const introduction = introductions[key];
  return selection.route === "orders-deliveries" && selection.ordersView !== "commitments"
    ? { ...introduction, title: isPurchasing(selection) ? "Purchasing" : "Sales" }
    : introduction;
}

export function isPurchasing(selection: { ordersView?: string; deliveryType?: string }): boolean {
  return (
    selection.ordersView === "supplier-orders" ||
    (selection.ordersView === "deliveries" && selection.deliveryType === "supplier_delivery")
  );
}
