// Presentation data matches the independently tested two-site shipping oracle.
const at = (time) => `2026-10-06T${time}:00+00:00`;
export const shipping = {
  observed_at: at("12:30"),
  business_day: "2026-10-06",
  time_zone: "Europe/Berlin",
  location_id: null,
  day_start: "2026-10-05T22:00:00+00:00",
  day_end: "2026-10-06T22:00:00+00:00",
  basis_key: "basis-current",
  basis: { policy_version: "completion-slot-v1", statement_ids: ["plan_1"], source_bindings: [] },
  coverage: { cohort: "complete", handover: "complete", forecast: "complete" },
  totals: { due: 4, handed_over: 1, forecast: 3, risk: 1 },
  sites: [
    {
      location_id: "loc_venlo",
      name: "Venlo",
      time_zone: "Europe/Amsterdam",
      due: 3,
      handed_over: 1,
      forecast: 3,
      risk: 0,
      cutoffs: [
        { at: at("14:00"), confirmation_state: "confirmed", source_record_id: "src_capacity" },
      ],
    },
    {
      location_id: "loc_leipzig",
      name: "Leipzig",
      time_zone: "Europe/Berlin",
      due: 2,
      handed_over: 0,
      forecast: 1,
      risk: 1,
      cutoffs: [
        {
          at: at("14:00"),
          confirmation_state: "confirmed",
          source_record_id: "src_capacity_leipzig",
        },
      ],
    },
  ],
  gaps: [],
  excluded: [],
  opening_baseline: { handover: 0, plan: 0 },
  forecast_horizon: "future",
  series_resolution_seconds: { plan: 0, handover: 0, forecast: 300 },
  series: {
    plan: [
      { at: at("12:00"), count: 1 },
      { at: at("13:00"), count: 2 },
      { at: at("13:30"), count: 3 },
      { at: at("14:00"), count: 4 },
    ],
    handover: [
      { at: "2026-10-05T22:00:00+00:00", count: 0 },
      { at: at("12:10"), count: 1 },
    ],
    forecast: [
      { at: at("12:30"), count: 1 },
      { at: at("13:15"), count: 2 },
      { at: at("14:00"), count: 3 },
    ],
  },
};

export const flows = {
  observed_at: at("12:30"),
  start: at("11:30"),
  coverage_start: at("10:00"),
  scope: "company_wide_live_60_minutes",
  buckets: Array.from({ length: 13 }, (_, i) => ({
    start: new Date(Date.parse(at("11:30")) + i * 300000).toISOString(),
    end: new Date(Date.parse(at("11:30")) + Math.min(i + 1, 12) * 300000).toISOString(),
    known: true,
    orders_received: i % 3,
    dispatch_movements: i % 2,
    receipts: i === 5 ? 3 : 0,
    return_arrivals: i === 7 ? 2 : 0,
    return_dispositions: i === 8 ? 1 : 0,
    messages_incoming: i === 1 ? 2 : 0,
    message_first_replies: i === 8 ? 34 : 0,
  })),
  orders: {
    signal: "progress",
    open_orders: 67,
    unlinked_open_lines: 0,
    received_last_hour: 12,
    dispatch_movements_last_hour: 6,
    exception_total: 0,
    exceptions: [],
    evidence: [{ kind: "document", id: "order_flow", label: "SO-FLOW" }],
  },
  messages: {
    signal: "progress",
    coverage: "complete",
    provider_reply_coverage: "unavailable",
    unanswered: 8,
    backlog_change_last_hour: -36,
    customer_requests: 5,
    unread: 3,
    incoming_last_hour: 2,
    first_replies_last_hour: 34,
    external_incoming: 0,
    series: Array.from({ length: 13 }, (_, i) => ({
      at: new Date(Date.parse(at("11:30")) + i * 300000).toISOString(),
      unanswered: 44 - i * 3,
    })),
    evidence: [{ kind: "source_record", id: "src_mail_flow", label: "Delivery question" }],
  },
  supply: {
    signal: "unknown",
    open_lines: 17,
    fully_received_lines: 12,
    unknown_due_lines: 1,
    receipts_last_hour: 3,
    exception_total: 0,
    exceptions: [],
    evidence: [{ kind: "commitment", id: "supply_flow", label: "PO-FLOW" }],
  },
  stock: {
    signal: "critical",
    oversold_items: 2,
    exception_total: 2,
    exceptions: [
      {
        id: "exc_item",
        title: "Item oversold",
        severity: "high",
        kind: "item",
        record_id: "item_flow",
      },
    ],
    evidence: [{ kind: "item", id: "item_flow", label: "Bike Light" }],
  },
  returns: {
    signal: "progress",
    coverage: "complete",
    expected_announcements: 4,
    arrived_positions: 5,
    resolved_positions: 3,
    pending_positions: 2,
    unknown_positions: 0,
    arrivals_last_hour: 2,
    exception_total: 0,
    exceptions: [],
    evidence: [{ kind: "movement", id: "return_flow", label: "Return receipt" }],
  },
};

// Explicit illustrative partitions for presentation proof; service tests prove authority.
Object.assign(flows.orders, {
  risk: {
    total: 67,
    in_plan: 50,
    at_risk: 10,
    critical: 5,
    unclassified: 2,
    coverage: "partial",
    scope: "open_orders",
  },
});
Object.assign(flows.messages, {
  risk: {
    total: 8,
    in_plan: null,
    at_risk: null,
    critical: null,
    unclassified: 8,
    coverage: "unavailable",
    scope: "unanswered_local_messages",
  },
});
Object.assign(flows.supply, {
  risk: {
    total: 17,
    in_plan: 12,
    at_risk: 2,
    critical: 2,
    unclassified: 1,
    coverage: "partial",
    scope: "open_supplier_lines",
  },
});
Object.assign(flows.stock, {
  risk: {
    total: 2,
    in_plan: 0,
    at_risk: 0,
    critical: 2,
    unclassified: 0,
    coverage: "complete",
    scope: "oversold_items",
  },
});
Object.assign(flows.returns, {
  risk: {
    total: 2,
    in_plan: 0,
    at_risk: 1,
    critical: 0,
    unclassified: 1,
    coverage: "partial",
    scope: "pending_return_positions",
  },
});

// Bounded, server-partitioned member rows for inspection presentation proof.
for (const area of ["orders", "messages", "supply", "stock", "returns"]) {
  const data = flows[area];
  const records = ["in_plan", "at_risk", "critical", "unclassified"].flatMap((category) =>
    Array.from({ length: Math.min(8, data.risk[category] || 0) }, (_, index) => ({
      kind: {
        orders: "document",
        messages: "source_record",
        supply: "commitment",
        stock: "item",
        returns: "movement",
      }[area],
      id: `inspect_${area}_${category}_${index}`,
      label:
        area === "stock"
          ? ["Inspection mug", "Inspection bowl"][index]
          : `Inspection ${area} ${category} ${index + 1}`,
      category,
      conditions: category === "critical" ? ["Item oversold"] : [],
      at: area === "stock" ? null : at("12:20"),
      shortfall: area === "stock" ? "12" : null,
      unit: "pcs",
    })),
  );
  data.inspection = Object.fromEntries(
    ["all", "in_plan", "at_risk", "critical", "unclassified"].map((group) => [
      group,
      {
        total: group === "all" ? data.risk.total : data.risk[group],
        items: records.filter((row) => group === "all" || row.category === group).slice(0, 8),
      },
    ]),
  );
}
