import type { ApplicationReference, ProjectionDefinition, WorkspaceViewDefinition } from "../api";
export type Report = {
  target: string;
  title: string;
  description: string;
  categories: string[];
  projection?: ProjectionDefinition;
  views: WorkspaceViewDefinition[];
  dataAvailable: boolean;
};
export const reportCategories = [
  "All",
  "Sales",
  "Purchasing",
  "Warehouse",
  "Finance",
  "Master data",
  "Company",
];

const presentation: Record<
  string,
  Pick<Report, "title" | "description" | "categories"> | undefined
> = {
  fulfillment_queue: {
    title: "Dispatch readiness",
    description: "See open customer deliveries, due dates and what prevents shipment.",
    categories: ["Sales", "Warehouse"],
  },
  fulfillment_blockers: {
    title: "Delivery blockers",
    description: "Find missing reservations and delivery holds affecting open commitments.",
    categories: ["Sales", "Purchasing", "Warehouse"],
  },
  item_supply_demand: {
    title: "Stock and demand",
    description: "Compare stock, expected receipts and uncovered customer demand by item.",
    categories: ["Sales", "Purchasing", "Warehouse"],
  },
  tenant_usage: {
    title: "Company activity overview",
    description: "See recorded data volumes and the latest activity for this company.",
    categories: ["Company"],
  },
  inventory: {
    title: "Stock overview",
    description: "See physical, reserved, available and expected stock.",
    categories: ["Warehouse", "Purchasing", "Sales"],
  },
  exceptions: {
    title: "Operational issues",
    description: "Find shortages, overdue commitments and active delivery restrictions.",
    categories: ["Sales", "Purchasing", "Warehouse"],
  },
  commitment_register: {
    title: "Delivery progress overview",
    description: "Compare committed, reserved, fulfilled and outstanding quantities.",
    categories: ["Sales", "Purchasing", "Warehouse"],
  },
  document_register: {
    title: "Document overview",
    description: "See received documents and their links to operational records.",
    categories: ["Sales", "Purchasing", "Finance"],
  },
  open_financial_items: {
    title: "Outstanding invoice amounts",
    description: "See invoice amounts, allocated payments and the remaining balance.",
    categories: ["Finance"],
  },
  payments: {
    title: "Payment allocation overview",
    description: "See payment postings together with their invoice allocations.",
    categories: ["Finance"],
  },
  journal: {
    title: "Posting overview",
    description: "Review ledger postings by posting group, account and currency.",
    categories: ["Finance"],
  },
  timeline: {
    title: "Business activity timeline",
    description: "Follow when source data, documents and operational records were recorded.",
    categories: ["Company"],
  },
  price_resolution: {
    title: "Price determination",
    description: "Understand how a price is selected for a business partner and item.",
    categories: ["Sales", "Purchasing"],
  },
  "view:commitments": {
    title: "Delivery commitments",
    description: "Browse delivery commitments and their current execution position.",
    categories: ["Sales", "Purchasing", "Warehouse"],
  },
  "view:documents": {
    title: "Recorded documents",
    description: "Browse recorded documents and their original references.",
    categories: ["Sales", "Purchasing", "Finance"],
  },
  "view:reservations": {
    title: "Stock reservations",
    description: "See which stock is allocated to delivery commitments.",
    categories: ["Warehouse"],
  },
  "view:movements": {
    title: "Stock movement history",
    description: "Review recorded receipts, shipments and other stock movements.",
    categories: ["Warehouse"],
  },
  "view:locations": {
    title: "Warehouse locations",
    description: "Browse physical and logical storage locations.",
    categories: ["Warehouse", "Master data"],
  },
  "view:payments": {
    title: "Recorded payments",
    description: "Browse payment records and their allocation details.",
    categories: ["Finance"],
  },
  "view:journal": {
    title: "Ledger posting register",
    description: "Browse the recorded debit and credit entries in the ledger.",
    categories: ["Finance"],
  },
  "view:parties": {
    title: "Business partner register",
    description: "Browse customers, suppliers and company records.",
    categories: ["Master data", "Sales", "Purchasing"],
  },
  "view:items": {
    title: "Item register",
    description: "Browse item records and their reference data.",
    categories: ["Master data", "Warehouse"],
  },
  "view:commercial_terms": {
    title: "Payment and pricing terms",
    description: "Review payment terms, price lists and pricing groups.",
    categories: ["Master data", "Sales", "Purchasing"],
  },
  "view:sources_imports": {
    title: "Received source data",
    description: "Browse received source records and their import context.",
    categories: ["Company"],
  },
  "view:activity": {
    title: "Recorded business events",
    description: "Review operational and financial activities across the company.",
    categories: ["Company"],
  },
};

/** Combine aliases only when they open the same reader, never by similar labels. */
export function buildReports(reference: ApplicationReference): Report[] {
  const reports = new Map<string, Report>();
  for (const projection of reference.projections || []) {
    const target = projection.materialized_as;
    reports.set(target, {
      target,
      title: projection.name,
      description: projection.calculation,
      categories: ["Company"],
      ...presentation[target],
      projection,
      views: [],
      dataAvailable: target !== "price_resolution",
    });
  }
  for (const workspace of reference.workspaces || []) {
    for (const view of workspace.views) {
      const target = view.projection || `view:${view.key}`;
      let report = reports.get(target);
      if (!report) {
        report = {
          target,
          title: view.label,
          description: view.description,
          categories: ["Company"],
          ...presentation[target],
          views: [],
          dataAvailable: target !== "price_resolution",
        };
        reports.set(target, report);
      }
      if (!report.views.some((entry) => entry.key === view.key)) report.views.push(view);
    }
  }
  return [...reports.values()];
}

export function filterReports(
  reports: Report[],
  query: string,
  category: string,
  translate: (key: string) => string,
): Report[] {
  const needle = query.trim().toLocaleLowerCase();
  return reports.filter(
    (report) =>
      (category === "All" || report.categories.includes(category)) &&
      [
        translate(report.title),
        translate(report.description),
        ...report.categories.map(translate),
        report.target,
        ...report.views.flatMap((view) => [view.key, view.label]),
      ]
        .join(" ")
        .toLocaleLowerCase()
        .includes(needle),
  );
}

/** One directory home per report; secondary workspaces remain searchable metadata. */
export function groupReports(reports: Report[]): Array<{ key: string; reports: Report[] }> {
  return reportCategories
    .filter((key) => key !== "All")
    .map((key) => ({
      key,
      reports: reports.filter(
        (report) =>
          (reportCategories.includes(report.categories[0]) ? report.categories[0] : "Company") ===
          key,
      ),
    }))
    .filter((group) => group.reports.length > 0);
}
