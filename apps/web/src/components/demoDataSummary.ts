// Feature 168: the order-to-cash observations of a Demo Data connection.
// Pure shaping for the integration panel; every value comes from the status read.

export type OrderToCash = {
  invoices_issued: number;
  payments_received: number;
  payments_allocated: number;
  invoices_settled: number;
  open_residuals: number;
  credit_created: string;
  unmatched_payments: number;
  failed: number;
  last_settlement: string | null;
  next_settlement: string | null;
};

export type OrderToCashRow = { key: keyof OrderToCash; label: string; value: string };

/** Counter rows in reading order; labels are English source strings for t(). */
export function orderToCashRows(block: OrderToCash | undefined): OrderToCashRow[] {
  if (!block) return [];
  const rows: [keyof OrderToCash, string][] = [
    ["invoices_issued", "Invoices issued"],
    ["payments_received", "Payments received"],
    ["payments_allocated", "Payments allocated"],
    ["invoices_settled", "Invoices settled"],
    ["open_residuals", "Open residuals"],
    ["credit_created", "Customer credit created"],
    ["unmatched_payments", "Unmatched payments"],
    ["failed", "Settlement failures"],
  ];
  return rows.map(([key, label]) => ({ key, label, value: String(block[key]) }));
}

/** Anything a person may want to look at: a difference, a credit or a failure. */
export function needsAttention(block: OrderToCash | undefined): boolean {
  if (!block) return false;
  return (
    block.open_residuals > 0 ||
    block.unmatched_payments > 0 ||
    block.failed > 0 ||
    Number(block.credit_created) > 0
  );
}

export type FinanceView = "payments" | "open-items" | "journal";

/** Deep links into the Finance page of the unified app, filtered to the synthetic source. */
export function financeLink(tenantId: string, view: FinanceView): string {
  const query = new URLSearchParams({ tenant: tenantId, finance_view: view, source: "demo_data" });
  return `/app/finance?${query.toString()}`;
}

// Feature 256: why a live source is not producing, said once for every surface.

export type Stall = NonNullable<import("../api").DemoDataStatus["stall"]>;

/** The headline of a stall, as an English source string for t(). */
export function stallHeadline(stall: Stall): string {
  return {
    suspended: "Execution was interrupted and will resume by itself",
    stopped: "Execution stopped and will not resume by itself",
    unresolved: "The last run ended with an unknown outcome",
    overdue: "No arrival has been executed as scheduled",
    throttled: "Paused: resolve failed imports",
  }[stall.kind];
}

/** The cause behind the error code, as an English source string for t(). */
export function stallCause(code: string | null): string {
  if (!code) return "";
  return (
    {
      database_error: "The database could not be reached.",
      handler_timeout: "The run exceeded its time budget.",
      child_exited: "The run ended unexpectedly.",
      outcome_unresolved: "Whether the work completed is unknown.",
      incompatible_references: "This company's references no longer match the simulation.",
      not_authorized: "The simulation is no longer authorized for this company.",
      inactive_source: "The source system was switched off.",
    }[code] || "The scheduler reported an error."
  );
}

/** A live source the person should look at, rather than one quietly at work. */
export function sourceNeedsAttention(derivedState: string | undefined): boolean {
  return ["suspended", "overdue", "error", "throttled"].includes(derivedState || "");
}
