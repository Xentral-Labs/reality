import { companySelection, type Selection } from "./routing.ts";

import type { SearchRecordTarget } from "../api";

export type PaletteTarget =
  | (SearchRecordTarget & { kind: "record"; family: string; roles?: string[] })
  | { kind: "page"; id: string }
  | { kind: "capability" | "calculated_report" | "saved_report" | "template"; id: string };

type Page = {
  key: string;
  label: string;
  destination: Partial<Selection>;
  access?: "owner" | "demo";
};
const pages: Page[] = [
  {
    key: "outstanding-customers",
    label: "Outstanding customer invoices",
    destination: {
      route: "finance",
      financeView: "open-items",
      flow: "receivable",
      financeStatus: "outstanding",
    },
  },
  {
    key: "outstanding-suppliers",
    label: "Outstanding supplier invoices",
    destination: {
      route: "finance",
      financeView: "open-items",
      flow: "payable",
      financeStatus: "outstanding",
    },
  },
  {
    key: "overdue-customers",
    label: "Overdue customer invoices",
    destination: {
      route: "finance",
      financeView: "open-items",
      flow: "receivable",
      financeStatus: "outstanding",
      financeOverdue: true,
    },
  },
  {
    key: "overdue-suppliers",
    label: "Overdue supplier invoices",
    destination: {
      route: "finance",
      financeView: "open-items",
      flow: "payable",
      financeStatus: "outstanding",
      financeOverdue: true,
    },
  },
  {
    key: "open-outbound",
    label: "Open outbound commitments",
    destination: {
      route: "orders-deliveries",
      ordersView: "deliveries",
      deliveryType: "customer_delivery",
      deliveryStatus: "open",
    },
  },
  {
    key: "open-inbound",
    label: "Open inbound commitments",
    destination: {
      route: "orders-deliveries",
      ordersView: "deliveries",
      deliveryType: "supplier_delivery",
      deliveryStatus: "open",
    },
  },
  {
    key: "blocked-outbound",
    label: "Blocked outbound commitments",
    destination: {
      route: "inspector",
      inspectorView: "views",
      calculatedReport: "fulfillment_blockers",
    },
  },
  {
    key: "exceptions",
    label: "Exceptions",
    destination: { route: "attention", attentionView: "findings" },
  },
  { key: "decisions", label: "Pending decisions", destination: { route: "decisions" } },
  { key: "home", label: "Inbox", destination: { route: "home" } },
  {
    key: "orders",
    label: "Sales",
    destination: { route: "orders-deliveries", ordersView: "customer-orders" },
  },
  {
    key: "purchases",
    label: "Purchasing",
    destination: { route: "orders-deliveries", ordersView: "supplier-orders" },
  },
  {
    key: "warehouse",
    label: "Warehouse",
    destination: { route: "warehouse", warehouseView: "stock" },
  },
  {
    key: "finance",
    label: "Finance",
    destination: { route: "finance", financeView: "open-items" },
  },
  {
    key: "master",
    label: "Master data",
    destination: { route: "master-data", family: "customer" },
  },
  {
    key: "analytics",
    label: "Analytics",
    destination: { route: "analytics", analyticsView: "reports" },
  },
  { key: "tools", label: "Tools", destination: { route: "inspector", inspectorView: "commands" } },
  { key: "chat", label: "Chat", destination: { route: "chat" } },
  { key: "facts", label: "Business Facts", destination: { route: "facts" } },
  {
    key: "graph",
    label: "Business Graph",
    destination: { route: "inspector", inspectorView: "graph" },
  },
  {
    key: "activities",
    label: "Activities",
    destination: { route: "inspector", inspectorView: "history" },
  },
  {
    key: "engine-room",
    label: "Engine room",
    access: "owner",
    destination: { route: "inspector", inspectorView: "live", liveFilter: "" },
  },
  {
    key: "integrations",
    label: "Integrations",
    destination: { route: "data-sources", dataView: "systems" },
  },
  { key: "storyline", label: "Storyline", destination: { route: "storyline" } },
  {
    key: "members",
    label: "Members",
    access: "owner",
    destination: { route: "settings", settingsView: "access" },
  },
  {
    key: "company",
    label: "Company settings",
    access: "owner",
    destination: { route: "settings", settingsView: "company" },
  },
  { key: "demo", label: "Demo data", access: "demo", destination: { route: "demo-data" } },
];

export function palettePages(access: { owner: boolean; demo: boolean }): Page[] {
  return pages.filter((page) => !page.access || access[page.access]);
}

/** Dispatch identifiers only; authorization and reader availability remain with the destination. */
export function paletteTargetSelection(selection: Selection, target: PaletteTarget): Selection {
  const base = companySelection(selection, selection.tenant);
  switch (target.kind) {
    case "record": {
      if (["party", "item", "location"].includes(target.record_kind))
        return {
          ...base,
          route: "master-data",
          record: target.id,
          family:
            target.record_kind === "party"
              ? target.roles?.includes("customer")
                ? "customer"
                : "supplier"
              : (target.record_kind as "item" | "location"),
        };
      if (["customer_order", "supplier_order"].includes(target.family))
        return {
          ...base,
          route: "orders-deliveries",
          ordersView: target.family === "customer_order" ? "customer-orders" : "supplier-orders",
          entry: target.id,
        };
      return {
        ...base,
        route: "inspector",
        inspectorView: "records",
        inspectorTargetKind: target.record_kind,
        inspectorTargetId: target.id,
      };
    }
    case "page": {
      const page = pages.find((entry) => entry.key === target.id);
      if (!page) throw new Error("Unknown palette page");
      return { ...base, ...page.destination };
    }
    case "capability":
      return { ...base, route: "inspector", inspectorView: "commands", toolCapability: target.id };
    case "calculated_report":
      return { ...base, route: "inspector", inspectorView: "views", calculatedReport: target.id };
    case "saved_report":
      return { ...base, route: "analytics", analyticsView: "graph", analyticsReport: target.id };
    case "template":
      return {
        ...base,
        route: "analytics",
        analyticsView: "templates",
        analyticsTemplate: target.id,
      };
    default:
      throw new Error("Unknown palette target");
  }
}

export type PaletteActionTarget = {
  postingGroup?: string;
  invoice?: string;
  creditNote?: string;
  commitment?: string;
  reservation?: string;
  movement?: string;
  direction?: string;
};
export function paletteActionPrefill(
  form: string,
  target?: PaletteActionTarget,
): PaletteActionTarget {
  if (!target) return {};
  const allowed: Record<string, keyof PaletteActionTarget> = {
    reserve: "commitment",
    movement_create: "commitment",
    receipt: "commitment",
    commitment_hold: "commitment",
    commitment_hold_release: "commitment",
    reservation_release: "reservation",
    movement_correct: "movement",
    sales_credit_record: "invoice",
    customer_refund_post: "creditNote",
    ledger_reverse: "postingGroup",
    order_create: "direction",
    customer_payment_post: "invoice",
    supplier_payment_post: "invoice",
  };
  const key = allowed[form];
  if (!key || typeof target[key] !== "string" || !target[key] || target[key]!.length > 256)
    return {};
  if (key === "direction" && !["sales", "purchase"].includes(target[key]!)) return {};
  return { [key]: target[key] };
}
