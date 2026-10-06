export type ShippingMeasure = "due" | "plan" | "handover" | "forecast" | "risk" | "unplanned";
export type ShippingPoint = { at: string; count: number };
export type ShippingObservation = {
  observed_at: string;
  business_day: string;
  time_zone: string;
  location_id: string | null;
  day_start: string;
  day_end: string;
  basis_key: string;
  basis: Record<string, unknown>;
  coverage: { cohort: string; handover: string; forecast: string };
  totals: {
    due: number | null;
    handed_over: number | null;
    forecast: number | null;
    risk: number | null;
  };
  sites: {
    location_id: string;
    name: string;
    time_zone: string;
    due: number;
    handed_over: number;
    forecast: number | null;
    risk: number | null;
    cutoffs: { at: string; confirmation_state: string; source_record_id: string | null }[];
  }[];
  gaps: { code: string; [key: string]: unknown }[];
  excluded: unknown[];
  opening_baseline: { handover: number; plan: number };
  forecast_horizon: string;
  series: Record<"plan" | "handover" | "forecast", ShippingPoint[] | null>;
};
export type ShippingOrder = {
  order_id: string;
  number: string;
  commitment_ids: string[];
  source_record_ids?: string[];
  readiness?: Record<string, Record<string, unknown>>;
  location_ids: string[];
  due_at: string | null;
  plan_at: string | null;
  handover_at: string | null;
  forecast_at: string | null;
  at_risk: boolean;
  risk_at: string | null;
  risk_requirements: unknown[];
  blockers: Record<string, { code: string; [key: string]: unknown }[]>;
  coverage_gaps: string[];
  physical_contents: Record<string, unknown>;
};
export type ShippingOrderPage = {
  items: ShippingOrder[];
  total: number | null;
  has_more: boolean;
  next_after: string | null;
  observed_at: string;
  basis_key: string;
  re_evaluated: boolean;
  coverage: ShippingObservation["coverage"];
  totals: ShippingObservation["totals"];
};
export type CockpitObservation = {
  flows?: OperatingFlows;
  observed_at: string;
  shipping: ShippingObservation;
  deviation_total?: number;
  deviations_has_more?: boolean;
  deviations?: (ShippingOrder & {
    case_id: string | null;
    responsibility: string;
    recorded_case_actions: { proposal_id: string; type?: string; status: string }[];
  })[];
};

export type CockpitActivityEvent = {
  id: string;
  sequence: number;
  type: string;
  subject_type: string;
  subject_id: string;
  recorded_at: string;
  occurred_at: string;
  source_record_id: string | null;
};
export type CockpitActivity = {
  observed_at: string;
  start: string;
  coverage_start: string;
  minutes: 5 | 15 | 60;
  bucket_seconds: number;
  total: number;
  counts: Record<string, number>;
  buckets: {
    start: string;
    end: string;
    partial: boolean;
    counts: Record<string, number>;
    total: number;
  }[];
  events: CockpitActivityEvent[];
  has_more: boolean;
};
export type AgentAccess = {
  identity: string;
  name: string;
  connection_kind: "manual" | "oauth";
  access_state: string;
  access_reason: string | null;
  last_used_at: string | null;
  runtime_state: "unknown";
  permitted_tools: string[];
  observed_action: null | {
    interaction_id: string;
    operation: string;
    outcome: string;
    recorded_at: string;
    proposal_id: string | null;
    business_references: { event_id: string; record_type: string; record_id: string }[];
    references_bounded: boolean;
  };
};
export type AgentAccessPage = {
  observed_at: string;
  coverage: Record<string, string>;
  scope: string;
  total: number;
  items: AgentAccess[];
  has_more: boolean;
  next_after: string | null;
};

export type FlowEvidence = { kind: string; id: string; label: string };
export type FlowArea = {
  signal: "critical" | "attention" | "progress" | "clear" | "unknown";
  evidence: FlowEvidence[];
  exceptions?: { id: string; title: string; severity: string; kind: string; record_id: string }[];
  exception_total?: number;
  [key: string]: unknown;
};
export type OperatingFlows = {
  observed_at: string;
  start: string;
  coverage_start: string;
  scope: string;
  buckets: { start: string; end: string; known: boolean; [key: string]: unknown }[];
  messages: FlowArea & {
    coverage: string;
    series: { at: string; unanswered: number | null }[];
  };
  orders: FlowArea;
  supply: FlowArea;
  stock: FlowArea;
  returns: FlowArea;
};
