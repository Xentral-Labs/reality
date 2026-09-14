export type CompanyProfileManifest = {
  tenant_id: string;
  windows: { prior_start: string; current_start: string; end: string };
  cases: Record<string, Record<string, string>>;
};
export type DemoDataStatus = {
  id?: string;
  state: string;
  derived_state?: string;
  revision: number;
  rate: number;
  schedule_id?: string;
  next_arrival: string | null;
  last_success?: string | null;
  last_request_key?: string;
  generated: number;
  imported: number;
  failed: number;
  pending: number;
  settlement_schedule_id?: string | null;
  order_to_cash?: import("./components/demoDataSummary").OrderToCash;
};
export type DemoDataPreview = {
  fingerprint: string;
  add: Record<string, { key: string; name: string }[]>;
};
export type DemoImportPage = {
  items: {
    id: string;
    source_record_id: string;
    status: string;
    outcome_id: string | null;
    document_id: string | null;
    document_number: string | null;
    created_at: string;
    completed_at: string | null;
  }[];
  next_cursor: string | null;
  has_more: boolean;
};
export type CompanySetupChoices = {
  name: string;
  environment: "business" | "sandbox";
  content: "empty" | "international_demo";
  live_simulation?: boolean;
};
export type CompanySetupRequest = CompanySetupChoices & { request_key: string; confirmed: true };
export type CompanySetupOptions = {
  actor_id: string;
  suggested_name: string;
  environments: ("business" | "sandbox")[];
  practice_enabled: boolean;
  pending: boolean;
};
export type CompanySetupResult = {
  tenant_id: string;
  run_id: string | null;
  name: string;
  status: string;
  environment: string;
  destination: string | null;
  error_code: string | null;
  profile: { key: string; version: number } | null;
};

export type TableQuery = { size?: number; sort?: string; sort_direction?: "asc" | "desc" };
function tableSearch(query: TableQuery) {
  return new URLSearchParams({
    size: String(query.size || 50),
    sort: query.sort || "",
    sort_direction: query.sort_direction || "asc",
  }).toString();
}
export type Tenant = {
  id: string;
  name: string;
  role?: "owner" | "member";
  purpose?: "playground";
  sandbox_run_id?: string;
  company_kind?: "company" | "sandbox" | "demo";
  demo_data_state?: "running" | "paused" | "stopped" | "disconnected";
};
export type CompanyAccess = {
  members: Array<{ id: string; email: string; display_name: string; role: "owner" | "member" }>;
  invitations: Array<{
    id: string;
    email: string;
    status: string;
    delivery_status: string;
    expires_at: string;
  }>;
};
export type Bootstrap = { tenants: Tenant[]; default_tenant_id: string | null };
export type AuthUser = {
  id: string;
  email: string;
  display_name: string;
  status: "email_unverified" | "pending_approval" | "active" | "rejected" | "suspended";
  language: "en" | "de" | "nl" | "es";
  locale: "en-GB" | "de-DE" | "nl-NL" | "es-ES";
  timezone: string;
  is_platform_admin: boolean;
  application: null | {
    id: string;
    company_name: string;
    company_website: string;
    orders_per_day: string;
    role_title: string;
    status: string;
    requested_at: string;
    reviewed_at: string | null;
  };
};
export type AccessCapacity = { used: number; limit: number | null };
export type PlatformOverview = {
  generated_at: string;
  deployment: {
    auth_mode: string;
    cookie_secure: string;
    auth_expose_codes: string;
    artifact_storage: string;
    email_provider: string;
    email_sender_configured: boolean;
    email_credential_configured: boolean;
    master_key_configured: boolean;
    database_revision: string | null;
    expected_revision: string | null;
    migrations_current: boolean;
    automatic_access_used: number;
    automatic_access_limit: number | null;
  };
  people: {
    total: number;
    by_status: Record<string, number>;
    pending_applications: number;
    oldest_pending_at: string | null;
    users: Array<{
      id: string;
      email: string;
      display_name: string;
      status: string;
      is_platform_admin: boolean;
      email_verified_at: string | null;
      last_login_at: string | null;
      created_at: string | null;
      active_sessions: number;
      companies: Array<{ id: string; name: string; role: string }>;
    }>;
  };
  companies: {
    total: number;
    archived: number;
    rows: Array<{
      id: string;
      name: string;
      created_at: string | null;
      archived_at: string | null;
      owners: number;
      members: number;
      open_invitations: number;
      business_events: number;
      last_event_at: string | null;
    }>;
  };
  operations: {
    import_jobs: Record<string, number>;
    projections_failed: number;
    invitation_deliveries: Record<string, number>;
    active_agent_tokens: number;
  };
  security: Array<{
    id: string;
    event_type: string;
    outcome: string | null;
    occurred_at: string | null;
    tenant_id: string | null;
    subject: string | null;
    actor: string | null;
  }>;
};
export type CompanyRow = Tenant & {
  created_at: string;
  archived_at: string | null;
  state: "empty" | "configured" | "in_use";
  source_count: number;
  evidence_count: number;
  reality_count: number;
  configured_count: number;
  last_activity_at: string | null;
};
export type SandboxRun = {
  id: string;
  sandbox_kind: "temporary" | "practice";
  company_name: string;
  tenant_id: string | null;
  status: "initializing" | "active" | "initialization_failed" | "archived";
  created_at: string;
  archived_at: string | null;
};
export type SandboxRuns = { runs: SandboxRun[]; total: number };
export type AIConfiguration = {
  copilot: {
    managed: true;
    available: boolean;
    provider_name: string;
    credential_mode: "managed" | "company";
    provider_preset: string;
    model: string;
    base_url: string;
    presets: { id: string; name: string; base_url: string; models: [string, string][] }[];
    has_company_api_key: boolean;
    api_key_fingerprint: string;
  };
  provider_preset: string;
  model: string;
  base_url: string;
  has_api_key: boolean;
  presets: { id: string; name: string; base_url: string; models: [string, string][] }[];
  mcp_url: string;
  tools: { name: string; label: string; description: string; access: string; group: string }[];
  tokens: {
    id: string;
    name: string;
    token_prefix: string;
    allowed_tools: string[];
    created_at: string;
    last_used_at: string | null;
  }[];
};
export type ExceptionRow = { severity: string; title: string; id: string; impact: string };
export type FactRow = {
  source_version?: number | null;
  id: string;
  subject_type: string;
  subject_id: string;
  predicate: string;
  value: string;
  observed_at: string;
  source_record_id?: string | null;
  source?: { system: string; type: string; external_id: string } | null;
  interpretation_rule_id?: string | null;
  interpretation_rule?: { id: string; logical_name: string; version: number } | null;
};
export type InventoryRow = {
  id: string;
  sku: string;
  name: string;
  unit: string;
  physical: string;
  reserved: string;
  available: string;
  incoming: string;
  projected: string;
};
export type CommitmentRow = {
  id: string;
  risk: "at_risk" | "ok";
  type: string;
  due_at: string | null;
  counterparty: string;
  item_id: string | null;
  location_id?: string | null;
  item: string;
  quantity: string;
  open_quantity: string;
  reserved: string;
  status: string;
  document_id: string | null;
};
export type DocumentRow = {
  id: string;
  date: string | null;
  type: string;
  number: string;
  party_id: string | null;
  party: string;
  currency: string;
  gross_amount: string;
  line_count: number;
  reality_link_count: number;
  source: { system: string; type: string; external_id: string } | null;
  status: string;
};
export type DocumentLineCorrection = {
  document_id: string;
  revision: string;
  correctable: boolean;
  has_linked_reality: boolean;
  economic_changes_blocked: boolean;
  correction_guidance: string;
  lines: Array<{
    id: string;
    item_id: string | null;
    source_line_id: string;
    sku: string;
    description: string;
    quantity: string;
    unit: string;
    unit_price: string;
    gross_amount: string;
    promised_at: string;
    line_type: string;
    billed_document_line_id?: string | null;
  }>;
};
export type DocumentLineCorrectionResult = DocumentLineCorrection & {
  changed: boolean;
  added: number;
  updated: number;
  removed: number;
};
export type OpenItemRow = {
  coverage_kind?: string | null;
  original_due_date?: string | null;
  account_code?: string;
  document_id: string;
  number: string;
  document_type: string;
  document_date: string | null;
  party_id: string | null;
  party: string;
  gross: string;
  settled: string;
  open: string;
  currency: string;
  status: string;
};
export type PaymentRow = {
  id: string;
  effective_at: string;
  direction: string;
  document_id: string;
  reference: string;
  document_type: string;
  party: string;
  currency: string;
  amount: string;
  allocated: string;
  unallocated: string;
  posting_group_id: string;
  reversal_role?: string;
};
export type JournalRow = {
  id: string;
  effective_at: string;
  account: string;
  account_id: string;
  account_code: string;
  account_name: string;
  debit_credit: "debit" | "credit";
  amount: string;
  currency: string;
  posting_group_id: string;
  party_id: string | null;
  document_id: string | null;
  source_record_id: string | null;
  inspect_kind: "ledger_entry";
  inspect_id: string;
};
export type JournalTotal = {
  currency: string;
  debit: string;
  credit: string;
  balance: string;
};
export type LedgerReversalPreview = {
  posting_group_id: string;
  revision: string;
  role: string;
  status: string;
  reason: string;
  request_fingerprint: string;
  original_entries: Array<Record<string, unknown>>;
  inverse_entries: Array<Record<string, unknown>>;
  affected_allocations: Array<Record<string, unknown>>;
  inactive_allocation_ids: string[];
};
export type LedgerReversalResult = {
  reversal_id: string;
  original_posting_group_id: string;
  reversing_posting_group_id: string;
  request_fingerprint: string;
  replayed: boolean;
};
export type PartyBalanceRow = {
  party_id: string;
  party: string;
  currency: string;
  open: string;
  overdue: string;
  credit: string;
  balance: string;
  open_count: number;
  credit_count: number;
  oldest_due_date: string | null;
};
export type BalanceTotals = {
  currency: string;
  open: string;
  overdue: string;
  credit: string;
  balance: string;
};
export type FinancialTotals = {
  currency: string;
  gross?: string;
  settled?: string;
  open?: string;
  amount?: string;
  allocated?: string;
  unallocated?: string;
};
export type ActivityCounts = Record<"orders" | "reservations" | "movements" | "documents", number>;
export type ActivityBucket = { start: string; end: string; counts: ActivityCounts };
export type ActivityVolume = {
  start: string;
  observed_at: string;
  coverage_start: string;
  bucket_seconds: number;
  total: number;
  buckets: ActivityBucket[];
};

export type SystemReadiness = {
  status: "ready" | "unknown" | "unavailable";
  observed_at: string;
  components: Record<"connection" | "scheduler" | "worker", "ready" | "unknown" | "unavailable">;
};

export type TimelineEvent = {
  business_context?: Record<string, unknown>;
  id: string;
  sequence: number;
  type: string;
  subject_type: string;
  subject_id: string;
  occurred_at: string;
  recorded_at: string;
  payload: Record<string, unknown>;
  source_record_id: string | null;
  action_id: string | null;
  correlation_id: string | null;
  causation_id: string | null;
  area: string;
  status: "attention" | "completed";
  business_title: string;
  business_detail: string;
};
export type TimelineActivity = {
  id: string;
  title: string;
  subtitle: string;
  business_title: string;
  business_detail: string;
  occurred_at: string;
  duration_ms: number;
  status: "attention" | "completed";
  events: TimelineEvent[];
};
export type TimelineData = {
  business_counts?: Record<string, number>;
  record_counts?: Record<string, number>;
  summary: {
    events: number;
    orders: number;
    exceptions: number;
    latency_ms: number;
    latest_source: string | null;
  };
  chart: { label: string; count: number; attention: number }[];
  activities: TimelineActivity[];
  events: TimelineEvent[];
  has_more: boolean;
};
export type ActivitySignal = {
  latest_sequence: number;
  new_events: number;
  attention_events: number;
};
export type SourceSystemRow = {
  id: string;
  code: string;
  name: string;
  description: string;
  is_active: boolean;
  record_count: number;
};
export type ConnectorShell = {
  code: string;
  name: string;
  category: string;
  capabilities: Record<string, string>;
  instances: SourceSystemRow[];
};
export type SourceCapabilityRow = {
  id: string;
  system_id: string;
  system: string;
  system_code: string;
  source_type: string;
  target_type: string;
  is_active: boolean;
  interpreter_available: boolean;
};
export type RecentSourceRow = {
  id: string;
  received_at: string;
  source_system: string;
  source_type: string;
  external_id: string;
  version: number;
  job_status: string | null;
};
export type IntegrationData = {
  systems: SourceSystemRow[];
  capabilities: SourceCapabilityRow[];
  recent_records: RecentSourceRow[];
};
export type ExplorerField = {
  name: string;
  label: string;
  value: unknown;
  format: "text" | "json";
  target: string | null;
};
export type InspectorRegisterData = {
  items: {
    id: string;
    kind: string;
    label: string;
    title: string;
    details: { label: string; value: unknown }[];
  }[];
  types: { kind: string; label: string }[];
  page: Page;
};
export type ExplorerRecord = { id: string; title: string; fields: ExplorerField[] };
export type ExplorerCollection = { name: string; label: string; records: ExplorerRecord[] };
export type ExplorerSection = {
  name: string;
  description: string;
  collections: ExplorerCollection[];
};
export type ExplorerData = {
  query: string;
  limit_per_collection: number;
  sections: ExplorerSection[];
};
export type CopilotSession = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
};
export type CopilotMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};
export type CopilotProposal = {
  id: string;
  tool: string;
  actor_type: string;
  status: string;
  input: Record<string, unknown>;
  created_at: string;
  // Both are absent for a decision settled before attribution existed, and the
  // person is absent for one taken without a signed-in principal.
  decided_at: string | null;
  decided_by: string | null;
};
export type CopilotSuggestion = {
  category: string;
  label: string;
  description: string;
  message: string;
  disabled?: boolean;
};
export type ManagedAllowance = {
  limit: number;
  used: number;
  remaining: number;
  resets_at: string;
};
export type CopilotData = {
  allowance?: ManagedAllowance | null;
  sessions: CopilotSession[];
  active_session_id: string | null;
  messages: CopilotMessage[];
  proposals: CopilotProposal[];
  suggestions: CopilotSuggestion[];
  has_archived: boolean;
};
export type RealityGapRow = {
  rule_statuses?: string[];
  id: string;
  question: string;
  intended_use: string;
  origin: "chat" | "mcp" | "web";
  status: string;
  destination: string | null;
  revision: number;
  created_at: string;
  updated_at: string;
};
export type RealityGapCondition =
  | {
      path: string;
      scope: "source" | "element";
      operator: string;
      value_type: string;
      operand?: unknown;
    }
  | {
      mode: "all" | "any";
      conditions: RealityGapCondition[];
    };
export type RealityGapDetail = {
  gap: RealityGapRow;
  entries: Array<{
    id: string;
    type: string;
    payload: Record<string, unknown>;
    actor_type: string;
    created_at: string;
  }>;
  rules: Array<{
    id: string;
    logical_name: string;
    version: number;
    status: string;
    predicate: string;
    source_system: string;
    source_type: string;
    value_path: string;
    conditions_mode: "all" | "any";
    conditions: RealityGapCondition[];
    iteration_path: string | null;
    source_line_id_path: string | null;
    output_mode: "source_path" | "constant";
    output_path: string | null;
    output_scope: "source" | "element";
    constant_value: unknown;
    subject_type: "commitment" | "document_line";
    subject_resolver: "source_document_commitments" | "source_document_lines";
    observed_at_mode: "source_received_at" | "source_path";
    observed_at_path: string | null;
    value_type: string;
    allowed_values: string[];
    summary: {
      last_evaluated_at: string | null;
      counts: Record<string, number>;
      examples: Array<Record<string, unknown>>;
      facts: Array<{
        fact_id: string;
        source_record_id: string;
        element_key: string;
        evaluated_at: string;
      }>;
    };
  }>;
};
export type RealityGapSourceExample = {
  source_record_id: string;
  source_system: string;
  source_type: string;
  external_id: string;
  received_at: string;
  candidates: Array<{ path: string; value: string; value_type: string }>;
};
export type RealityGapSimulation = {
  sources_considered: number;
  matches: number;
  expected_facts: number;
  invalid_values: number;
  ambiguous_subjects: number;
  not_applicable: number;
  conflicts: number;
  examples: Array<{
    status: string;
    source_record_id: string;
    external_id: string;
    detail?: string;
    value?: unknown;
  }>;
};
export type InspectorRow = {
  display_parts?: import("./unified/inspectorPresentation").InspectorPart[];
  label: string;
  value: unknown;
  tone: string;
  link: { kind: string; id: string } | null;
};
export type BillingAvailability = {
  order_line_id: string;
  order_id: string;
  label: string;
  unit: string;
  ordered: string;
  invoiced: string;
  remaining: string;
  can_invoice: boolean;
  evidence: {
    invoice_id: string;
    invoice_line_id: string;
    number: string;
    source_record_id: string | null;
    quantity: string;
    released: boolean;
    posting_group_ids: string[];
    reversal_ids: string[];
  }[];
};
export type InspectorData = {
  title_parts?: import("./unified/inspectorPresentation").InspectorPart[];
  subtitle_parts?: import("./unified/inspectorPresentation").InspectorPart[];
  meaning_parts?: import("./unified/inspectorPresentation").InspectorPart[];
  coverage?: { reservations_has_more: boolean; movements_has_more: boolean };
  evidence_lines?: Array<{
    billing?: BillingAvailability;
    id: string;
    label: string;
    quantity: string;
    gross_amount: string;
    unit: string;
  }>;
  kind: string;
  id: string;
  eyebrow: string;
  title: string;
  subtitle: string;
  status: string;
  meaning: string;
  business_reference: { label: string; value: string } | null;
  guidance: string | null;
  technical_rows: InspectorRow[];
  metrics: InspectorRow[];
  trail: { label: string; value: string; active: boolean }[];
  sections: { title: string; rows: InspectorRow[] }[];
  events: { type: string; occurred_at: string; subject_type: string; subject_id: string }[];
  source_payload: string | null;
};
export type Page = {
  number: number;
  size: number;
  total: number;
  pages: number;
  has_previous: boolean;
  has_next: boolean;
};
export type Dashboard = {
  tenant: Tenant;
  totals: {
    exceptions: number;
    open_commitments: number;
    open_deliveries: number;
    stocked_items: number;
    documents: number;
    payments: number;
    sources: number;
    facts: number;
    pending_decisions: number;
    decision_history: number;
  };
  exceptions: ExceptionRow[];
  inventory: InventoryRow[];
  facts: FactRow[];
  capabilities: {
    sources: boolean;
    facts: boolean;
    operations: boolean;
    warehouse: boolean;
    finance: boolean;
    activity: boolean;
  };
};
export type PartyRow = {
  id: string;
  tenant_id: string;
  name: string;
  type: string;
  roles: string[] | null;
  accounting_code: string;
  payment_term_code: string;
  default_currency: string;
  credit_limit: string;
  tax_identifier: string;
  is_active: boolean;
  source_system: string | null;
  external_id: string | null;
  source_record_id: string | null;
};
export type ItemRow = {
  id: string;
  tenant_id: string;
  sku: string;
  name: string;
  unit: string;
  item_type: string;
  tracking_type: string;
  default_location_id: string | null;
  purchase_unit: string | null;
  conversion_factor: string;
  lead_time_days: number;
  is_active: boolean;
  source_system: string | null;
  external_id: string | null;
  source_record_id: string | null;
};
export type LocationRow = {
  id: string;
  tenant_id: string;
  name: string;
  type: string;
  parent_location_id: string | null;
  allows_stock: boolean;
  is_active: boolean;
  source_system: string | null;
  external_id: string | null;
  source_record_id: string | null;
};
export type SuggestionRow = { value: string; label: string; description: string; status: string };
export type SuggestionData = { items: SuggestionRow[]; allow_custom: boolean };
export type PaymentTermRow = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  due_days: number;
  is_active: boolean;
  source_record_id: string | null;
};
export type PriceListRow = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  direction: string;
  currency: string;
  is_default: boolean;
  is_active: boolean;
  source_record_id: string | null;
  valid_from: string | null;
  valid_until: string | null;
};
export type PricingGroupRow = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  group_type: string;
  is_active: boolean;
  source_record_id: string | null;
};
export type ImportJobRow = {
  id: string;
  tenant_id: string;
  source_record_id: string;
  status: string;
  attempts: number;
  error: string;
};
export type CatalogCode = {
  kind: string;
  key: string;
  relationship: string;
  sources: Array<{ path: string; function: string; code: string; truncated: boolean }>;
};
export type CatalogContract = {
  service: string;
  inputs: Array<{
    name: string;
    description: string;
    type: string;
    required: boolean;
    default: string;
  }>;
  returns: string;
  source?: { path: string; function: string };
};
export type CatalogCommand = {
  service: string;
  name?: string;
  effect?: string;
  related_services?: string[];
  mode: string;
  adapters: string[];
  reads?: string[];
  writes?: string[];
  contracts?: CatalogContract[];
};
export type ProjectionDefinition = {
  service?: string;
  reads?: string[];
  contracts?: CatalogContract[];
  name: string;
  materialized_as: string;
  calculation: string;
  consumers: string[];
  outputs: string[];
  invalidated_by: string[];
};
export type WorkspaceViewDefinition = {
  key: string;
  label: string;
  route: string;
  kind: "authoritative_register" | "materialized_projection";
  projection?: string;
  description: string;
};
export type WorkspaceActionDefinition = {
  key: string;
  label: string;
  description: string;
  command: string;
  target_route: string;
  confirmation: "summary" | "server_preview";
  prerequisites: string[];
  result_kind?: string;
};
export type WorkspaceDefinition = {
  key: string;
  label: string;
  // A reference workspace lists its whole surface directly instead of keeping
  // part of it behind a launcher.
  complete_navigation: boolean;
  views: WorkspaceViewDefinition[];
  actions: WorkspaceActionDefinition[];
};
export type ProjectionMetadata = {
  projection: string;
  calculation_mode: "stored";
  state: "uninitialized" | "ready" | "pending" | "failed";
  processed_event_sequence: number | null;
  target_event_sequence: number;
  completed_at: string | null;
  projection_version: number | null;
  upstream_freshness: "unknown";
  consistency: "completed_snapshot";
};
export type ProjectionSnapshot = {
  items: Record<string, unknown>[];
  metadata?: ProjectionMetadata;
};
export type SpecializedProjectionRow = Record<string, unknown>;
export type SpecializedProjectionData = {
  metadata?: ProjectionMetadata;
  items: SpecializedProjectionRow[];
  page: Page;
};
export type ApplicationReference = {
  discovery?: import("./unified/actionDiscovery").ActionDiscovery;
  commands?: CatalogCommand[];
  command_count: number;
  event_count: number;
  projection_count: number;
  fact_predicate_count: number;
  projections: ProjectionDefinition[];
  workspaces: WorkspaceDefinition[];
};
export type ReservationRow = {
  id: string;
  commitment_id: string;
  item_id: string;
  location_id: string;
  quantity: string;
  status: string;
  reserved_at: string;
  handling_unit_id: string | null;
  lot_id: string | null;
  serial_unit_id: string | null;
};
export type MovementRow = {
  id: string;
  tenant_id: string;
  type: string;
  item_id: string;
  quantity: string;
  from_location_id: string | null;
  to_location_id: string | null;
  commitment_id: string | null;
  source_record_id: string | null;
  handling_unit_id: string | null;
  lot_id: string | null;
  serial_unit_id: string | null;
  occurred_at: string;
  correction_role: "normal" | "corrected" | "compensation" | "replacement";
  correction_status: "recorded" | "corrected";
};
export type MovementCorrectionSnapshot = {
  movement_id: string;
  revision: string;
  role: string;
  status: string;
  correctable: boolean;
  guidance: string;
  original: Record<string, unknown>;
  compensation: Record<string, unknown> | null;
  replacement: Record<string, unknown> | null;
  correction: {
    id: string;
    reason: string;
    corrected_at: string;
    actor_context: Record<string, unknown>;
    request_fingerprint: string;
  } | null;
};
export type MovementCorrectionPreview = {
  movement_id: string;
  revision: string;
  request_fingerprint: string;
  reason: string;
  original: Record<string, unknown>;
  compensation: Record<string, unknown>;
  replacement: Record<string, unknown> | null;
  net_quantity: string;
};
export type MovementCorrectionResult = {
  correction_id: string;
  original_movement_id: string;
  compensating_movement_id: string;
  replacement_movement_id: string | null;
  request_fingerprint: string;
  replayed: boolean;
};

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    credentials: "include",
    headers: { Accept: "application/json", "Content-Type": "application/json", ...init.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new APIError(
      typeof payload?.detail === "string"
        ? payload.detail
        : typeof payload?.detail?.message === "string"
          ? payload.detail.message
          : `Reality API returned ${response.status}`,
      response.status,
      payload?.code || payload?.detail?.code,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  demoDataStatus: (scope: string) => request<DemoDataStatus>(scope),
  demoDataPreview: (scope: string) => request<DemoDataPreview>(`${scope}/preview`),
  demoDataImports: (scope: string, cursor = "", recent = false) =>
    request<DemoImportPage>(
      `${scope}/imports?cursor=${encodeURIComponent(cursor)}&recent=${recent}`,
    ),
  demoDataConnect: (
    scope: string,
    body: { request_key: string; preview_fingerprint: string; confirmed: true },
  ) => request<DemoDataStatus>(`${scope}/connect`, { method: "POST", body: JSON.stringify(body) }),
  demoDataControl: (
    scope: string,
    body: {
      request_key: string;
      action: string;
      expected_revision: number;
      rate?: number;
      confirmed: true;
    },
  ) => request<DemoDataStatus>(`${scope}/control`, { method: "POST", body: JSON.stringify(body) }),
  demoDataImport: (scope: string, id: string) =>
    request<Record<string, unknown>>(`${scope}/imports/${encodeURIComponent(id)}`),
  demoDataRetry: (scope: string, id: string) =>
    request(`${scope}/imports/${encodeURIComponent(id)}/retry`, {
      method: "POST",
      body: JSON.stringify({ confirmed: true }),
    }),
  companySetupProfile: (key: string) =>
    request<CompanyProfileManifest>(
      `/api/company-setup/requests/${encodeURIComponent(key)}/profile`,
    ),
  companySetupExecution: (
    key: string,
    body: { request_key: string; name: string; confirmed: true },
  ) =>
    request<CompanySetupResult>(
      `/api/company-setup/requests/${encodeURIComponent(key)}/execution`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  playgroundEntry: () =>
    request<{
      requested: boolean;
      archived: boolean;
      enabled: boolean;
      eligible: boolean;
      receipt: CompanySetupResult | null;
    }>("/api/company-setup/playground"),
  enterPlayground: () =>
    request<CompanySetupResult>("/api/company-setup/playground", {
      method: "POST",
      body: JSON.stringify({ confirmed: true }),
    }),
  companySetupOptions: () => request<CompanySetupOptions>("/api/company-setup/options"),
  companySetupRequest: (key: string) =>
    request<CompanySetupResult>(`/api/company-setup/requests/${encodeURIComponent(key)}`),
  companySetup: (body: CompanySetupRequest) =>
    request<CompanySetupResult>("/api/company-setup", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  me: () => request<AuthUser>("/api/auth/me"),
  exceptionCatalog: () =>
    request<{
      version: number;
      classes: Array<{
        id: string;
        label: string;
        description: string;
        severity: string;
        owner: string;
        clears_through: string;
        /** Translated labels by UI language; absent languages fall back to `label`. */
        labels: Record<string, string>;
      }>;
    }>("/api/playground/exception-catalog"),

  signup: (email: string, password: string) =>
    request<{ email: string; next: string; verification_code?: string }>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, accepted_terms: true, playground: true }),
    }),
  invitationSignup: (token: string, email: string, password: string) =>
    request<{ email: string; next: string; verification_code?: string }>(
      "/api/auth/invitations/signup",
      { method: "POST", body: JSON.stringify({ token, email, password, accepted_terms: true }) },
    ),
  inspectInvitation: (token: string) =>
    request<{ status: string; company_name?: string; email?: string; expires_at?: string }>(
      "/api/auth/invitations/inspect",
      { method: "POST", body: JSON.stringify({ token }) },
    ),
  acceptInvitation: (token: string) =>
    request<{ status: string; company: Tenant }>("/api/auth/invitations/accept", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),
  verifyEmail: (email: string, code: string, invitationToken?: string) =>
    request<AuthUser>("/api/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ email, code, invitation_token: invitationToken }),
    }),
  login: (email: string, password: string) =>
    request<AuthUser>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),
  updateApplication: (body: Record<string, unknown>) =>
    request<AuthUser>("/api/auth/application", { method: "PUT", body: JSON.stringify(body) }),
  updateProfile: (body: Record<string, unknown>) =>
    request<AuthUser>("/api/auth/profile", { method: "PUT", body: JSON.stringify(body) }),
  accessApplications: () => request<AuthUser[]>("/api/admin/access-applications"),
  accessCapacity: () => request<AccessCapacity>("/api/admin/access-capacity"),
  platformOverview: () => request<PlatformOverview>("/api/admin/overview"),
  reviewAccess: (id: string, decision: "approve" | "reject", note = "") =>
    request<AuthUser>(`/api/admin/access-applications/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ decision, note }),
    }),
  bootstrap: () => request<Bootstrap>("/api/v1/bootstrap"),
  companyAccess: (tenant: string) =>
    request<CompanyAccess>(`/api/tenants/${tenant}/settings/members`),
  inviteMember: (tenant: string, email: string) =>
    request<{ status: string }>(`/api/tenants/${tenant}/settings/invitations`, {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  resendInvitation: (tenant: string, id: string) =>
    request(`/api/tenants/${tenant}/settings/invitations/${id}/resend`, { method: "POST" }),
  revokeInvitation: (tenant: string, id: string) =>
    request<void>(`/api/tenants/${tenant}/settings/invitations/${id}/revoke`, { method: "POST" }),
  removeMember: (tenant: string, id: string) =>
    request<void>(`/api/tenants/${tenant}/settings/members/${id}/remove`, { method: "POST" }),
  companies: () => request<CompanyRow[]>("/api/v1/companies"),
  createCompany: (name: string, guidedDemo = false) =>
    request<Tenant>("/api/v1/companies", {
      method: "POST",
      body: JSON.stringify({ name, guided_demo: guidedDemo }),
    }),
  archiveCompany: (id: string) => request(`/api/v1/companies/${id}/archive`, { method: "POST" }),
  restoreCompany: (id: string) => request(`/api/v1/companies/${id}/restore`, { method: "POST" }),
  deleteCompany: (id: string, confirmationName: string, confirmationWord: string) =>
    request<void>(`/api/v1/companies/${id}/delete`, {
      method: "POST",
      body: JSON.stringify({
        confirmation_name: confirmationName,
        confirmation_word: confirmationWord,
      }),
    }),
  sandboxRuns: () => request<SandboxRuns>("/api/playground?limit=100"),
  archiveSandbox: (runId: string) =>
    request<SandboxRun>(`/api/playground/runs/${runId}/archive`, {
      method: "POST",
      body: JSON.stringify({ confirmed: true }),
    }),
  restoreSandbox: (runId: string) =>
    request<SandboxRun>(`/api/playground/runs/${runId}/restore`, {
      method: "POST",
      body: JSON.stringify({ confirmed: true }),
    }),
  aiSettings: (tenant: string) => request<AIConfiguration>(`/api/tenants/${tenant}/settings/ai`),
  saveAISettings: (tenant: string, body: Record<string, unknown>) =>
    request<Pick<AIConfiguration, "copilot">>(`/api/tenants/${tenant}/settings/ai`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  createMCPToken: (tenant: string, name: string, allowedTools: string[]) =>
    request<{
      id: string;
      name: string;
      token: string;
      token_prefix: string;
      allowed_tools: string[];
    }>(`/api/tenants/${tenant}/settings/mcp/tokens`, {
      method: "POST",
      body: JSON.stringify({ name, allowed_tools: allowedTools }),
    }),
  revokeMCPToken: (tenant: string, id: string) =>
    request<void>(`/api/tenants/${tenant}/settings/mcp/tokens/${id}/revoke`, { method: "POST" }),
  dashboard: (tenant: string) => request<Dashboard>(`/api/tenants/${tenant}/dashboard`),
  facts: (
    tenant: string,
    q = "",
    page = 1,
    subjectType = "",
    subjectId = "",
    sourceId = "",
    table: TableQuery = {},
  ) =>
    request<{
      items: FactRow[];
      page: Page;
      subject_types: string[];
      subject_types_has_more: boolean;
    }>(
      `/api/tenants/${tenant}/facts?${new URLSearchParams({ q, page: String(page), subject_type: subjectType, subject_id: subjectId, source_record_id: sourceId })}${"&" + tableSearch(table)}`,
    ),
  realityGaps: (
    tenant: string,
    filters: {
      lifecycle?: "open" | "completed" | "all";
      status?: string;
      ruleStatus?: string;
      query?: string;
      page?: number;
      size?: number;
    } = {},
  ) => {
    const params = new URLSearchParams();
    if (filters.lifecycle) params.set("lifecycle", filters.lifecycle);
    if (filters.status) params.set("status", filters.status);
    if (filters.ruleStatus) params.set("rule_status", filters.ruleStatus);
    if (filters.query) params.set("q", filters.query);
    if (filters.page) params.set("page", String(filters.page));
    if (filters.size) params.set("size", String(filters.size));
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<{
      items: RealityGapRow[];
      total: number;
      page: number;
      size: number;
      counts: { open: number; completed: number; all: number };
    }>(`/api/tenants/${tenant}/reality-gaps${suffix}`);
  },
  realityGap: (tenant: string, id: string) =>
    request<RealityGapDetail>(`/api/tenants/${tenant}/reality-gaps/${id}`),
  realityGapSourceExamples: (tenant: string, query: string) =>
    request<{ items: RealityGapSourceExample[] }>(
      `/api/tenants/${tenant}/reality-gaps/source-examples/search?q=${encodeURIComponent(query)}`,
    ),
  createRealityGap: (tenant: string, body: Record<string, unknown>) =>
    request<RealityGapDetail>(`/api/tenants/${tenant}/reality-gaps`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  addRealityGapEntry: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<RealityGapDetail>(`/api/tenants/${tenant}/reality-gaps/${id}/entries`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  recommendRealityGap: (tenant: string, id: string, revision: number) =>
    request<RealityGapDetail>(`/api/tenants/${tenant}/reality-gaps/${id}/recommend`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision }),
    }),
  decideRealityGap: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<RealityGapDetail>(`/api/tenants/${tenant}/reality-gaps/${id}/decide`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  prepareRealityGap: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<RealityGapDetail>(`/api/tenants/${tenant}/reality-gaps/${id}/implementation`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  simulateRealityGapRule: (tenant: string, gapId: string, ruleId: string) =>
    request<RealityGapSimulation>(
      `/api/tenants/${tenant}/reality-gaps/${gapId}/rules/${ruleId}/simulate`,
      { method: "POST" },
    ),
  activateRealityGapRule: (tenant: string, gapId: string, ruleId: string) =>
    request<RealityGapDetail>(
      `/api/tenants/${tenant}/reality-gaps/${gapId}/rules/${ruleId}/activate`,
      { method: "POST" },
    ),
  disableRealityGapRule: (tenant: string, gapId: string, ruleId: string) =>
    request<RealityGapDetail>(
      `/api/tenants/${tenant}/reality-gaps/${gapId}/rules/${ruleId}/disable`,
      { method: "POST" },
    ),
  replayRealityGapRule: (tenant: string, gapId: string, ruleId: string, cursor?: string | null) =>
    request<{
      facts_created: number;
      facts_existing: number;
      not_applicable: number;
      conflicts: number;
      failed: number;
      cumulative: Record<string, number>;
      next_cursor: string | null;
      complete: boolean;
    }>(`/api/tenants/${tenant}/reality-gaps/${gapId}/rules/${ruleId}/replay`, {
      method: "POST",
      body: JSON.stringify({ limit: 500, cursor }),
    }),
  exceptions: (tenant: string) =>
    request<{ items: ExceptionRow[]; page: Page }>(`/api/tenants/${tenant}/exceptions`),
  inventory: (tenant: string, query = "", state = "") => {
    const params = new URLSearchParams({ q: query, state });
    return request<{ items: InventoryRow[]; page: Page }>(
      `/api/tenants/${tenant}/inventory-control?${params}`,
    );
  },
  specializedProjection: (
    tenant: string,
    projection: "fulfillment_queue" | "fulfillment_blockers" | "item_supply_demand",
    query = "",
    page = 1,
  ) => {
    const params = new URLSearchParams({ q: query, page: String(page), size: "50" });
    return request<SpecializedProjectionData>(
      `/api/tenants/${tenant}/projection-views/${projection}?${params}`,
    );
  },
  commitments: (tenant: string, query = "", status = "open", type = "", page = 1) => {
    const params = new URLSearchParams({
      q: query,
      commitment_status: status,
      commitment_type: type,
      page: String(page),
      size: "50",
    });
    return request<{ items: CommitmentRow[]; page: Page }>(
      `/api/tenants/${tenant}/commitment-control?${params}`,
    );
  },
  documents: (
    tenant: string,
    query = "",
    type = "",
    status = "",
    page = 1,
    sourceSystem = "",
    sourceRecord = "",
    table: TableQuery = {},
  ) => {
    const params = new URLSearchParams({
      q: query,
      document_type: type,
      document_status: status,
      source_system: sourceSystem,
      source_record_id: sourceRecord,
    });
    params.set("page", String(page));
    return request<{ items: DocumentRow[]; page: Page }>(
      `/api/tenants/${tenant}/evidence-documents?${params}${"&" + tableSearch(table)}`,
    );
  },
  createDocument: (tenant: string, body: Record<string, unknown>) =>
    request<{ id: string; status: string; line_count: number }>(
      `/api/tenants/${tenant}/documents`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  createManualOrder: (tenant: string, body: Record<string, unknown>) =>
    request<{
      source_record_id: string;
      document_id: string;
      document_line_ids: string[];
      commitment_ids: string[];
    }>(`/api/tenants/${tenant}/manual-orders`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  observeFact: (tenant: string, body: Record<string, unknown>) =>
    request<{ id: string }>(`/api/tenants/${tenant}/facts`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  postCustomerPayment: (tenant: string, body: Record<string, unknown>) =>
    request<{ ledger_entry_ids: string[] }>(`/api/tenants/${tenant}/finance/customer-payments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  postSupplierPayment: (tenant: string, body: Record<string, unknown>) =>
    request<{ ledger_entry_ids: string[] }>(`/api/tenants/${tenant}/finance/supplier-payments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  documentLineCorrection: (tenant: string, id: string) =>
    request<DocumentLineCorrection>(`/api/tenants/${tenant}/documents/${id}/line-correction`),
  correctDocumentLines: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<DocumentLineCorrectionResult>(
      `/api/tenants/${tenant}/documents/${id}/line-correction`,
      { method: "PUT", body: JSON.stringify(body) },
    ),
  suggestions: (tenant: string, kind: string, query = "") =>
    request<SuggestionData>(
      `/api/tenants/${tenant}/suggestions/${encodeURIComponent(kind)}?q=${encodeURIComponent(query)}`,
    ),
  openItems: (
    tenant: string,
    query = "",
    flow = "",
    status = "",
    page = 1,
    table: TableQuery = {},
    partyId = "",
  ) => {
    const params = new URLSearchParams({
      q: query,
      flow,
      item_status: status,
      page: String(page),
    });
    if (partyId) params.set("party_id", partyId);
    return request<{
      items: OpenItemRow[];
      totals: FinancialTotals[];
      page: Page;
      metadata?: ProjectionMetadata;
    }>(`/api/tenants/${tenant}/finance/open-items?${params}${"&" + tableSearch(table)}`);
  },
  partyBalances: (
    tenant: string,
    side: "customer" | "supplier",
    query = "",
    creditOnly = false,
    page = 1,
    table: TableQuery = {},
  ) => {
    const params = new URLSearchParams({
      q: query,
      flow: `${side}-balances`,
      page: String(page),
    });
    if (creditOnly) params.set("credit_only", "true");
    return request<{ items: PartyBalanceRow[]; totals: BalanceTotals[]; page: Page }>(
      `/api/tenants/${tenant}/finance/open-items?${params}${"&" + tableSearch(table)}`,
    );
  },
  payments: (tenant: string, query = "", direction = "", page = 1, table: TableQuery = {}) => {
    const params = new URLSearchParams({ q: query, direction, page: String(page) });
    return request<{ items: PaymentRow[]; totals: FinancialTotals[]; page: Page }>(
      `/api/tenants/${tenant}/finance/payments?${params}${"&" + tableSearch(table)}`,
    );
  },
  journal: (
    tenant: string,
    query = "",
    account = "",
    dateFrom = "",
    dateTo = "",
    page = 1,
    table: TableQuery = {},
  ) => {
    const params = new URLSearchParams({
      q: query,
      account,
      date_from: dateFrom,
      date_to: dateTo,
      page: String(page),
    });
    return request<{ items: JournalRow[]; totals: JournalTotal[]; page: Page }>(
      `/api/tenants/${tenant}/finance/journal?${params}${"&" + tableSearch(table)}`,
    );
  },
  activityVolume: (tenant: string, days: number, signal?: AbortSignal) =>
    request<ActivityVolume>(`/api/tenants/${tenant}/activity-volume?days=${days}`, { signal }),
  activityVolumeEvents: (tenant: string, start: string, end: string, signal?: AbortSignal) =>
    request<{ events: TimelineEvent[]; total: number; has_more: boolean }>(
      `/api/tenants/${tenant}/activity-volume/events?${new URLSearchParams({ start, end })}`,
      { signal },
    ),
  readiness: (tenant: string, signal?: AbortSignal) =>
    request<SystemReadiness>(`/api/tenants/${tenant}/readiness`, { signal }),
  timeline: (
    tenant: string,
    query = "",
    area = "",
    status = "",
    hours = 24,
    recordType = "",
    beforeSequence?: number,
    limit = 100,
    signal?: AbortSignal,
  ) => {
    const params = new URLSearchParams({
      q: query,
      area,
      event_status: status,
      hours: String(hours),
      record_type: recordType,
      limit: String(limit),
    });
    if (beforeSequence) params.set("before_sequence", String(beforeSequence));
    return request<TimelineData>(`/api/tenants/${tenant}/timeline?${params}`, { signal });
  },
  activitySignal: (tenant: string, afterSequence: number) =>
    request<ActivitySignal>(
      `/api/tenants/${tenant}/activity-signal?after_sequence=${afterSequence}`,
    ),
  integrations: (tenant: string) => request<IntegrationData>(`/api/tenants/${tenant}/integrations`),
  connectorShells: (tenant: string) =>
    request<ConnectorShell[]>(`/api/tenants/${tenant}/connector-shells`),
  installConnectorShell: (
    tenant: string,
    connectorCode: string,
    body: { source_types: string[]; system_code: string; system_name: string },
  ) =>
    request<SourceSystemRow>(
      `/api/tenants/${tenant}/connector-shells/${encodeURIComponent(connectorCode)}/install`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  importJobs: (tenant: string) => request<ImportJobRow[]>(`/api/tenants/${tenant}/import-jobs`),
  inspectorProjection: (tenant: string, name: string) =>
    request<ProjectionSnapshot>(
      `/api/tenants/${encodeURIComponent(tenant)}/projection-snapshots/${encodeURIComponent(name)}`,
    ),
  catalogCode: (tenant: string, kind: string, key: string) =>
    request<CatalogCode>(
      `/api/tenants/${encodeURIComponent(tenant)}/catalog-code?${new URLSearchParams({ kind, key })}`,
    ),
  applicationReference: (tenant: string) =>
    request<ApplicationReference>(`/api/tenants/${tenant}/application-reference`),
  inspectorRecords: (tenant: string, kind: string, query: string, page: number, size: number) => {
    const params = new URLSearchParams({ kind, q: query, page: String(page), size: String(size) });
    return request<InspectorRegisterData>(`/api/tenants/${tenant}/inspector-records?${params}`);
  },
  explorer: (tenant: string, query = "", kind = "") => {
    const params = new URLSearchParams({ q: query });
    if (kind) params.set("kind", kind);
    return request<ExplorerData>(`/api/tenants/${tenant}/explorer?${params}`);
  },
  copilot: (tenant: string, sessionId = "", archived = false) =>
    request<CopilotData>(
      `/api/tenants/${tenant}/copilot?${new URLSearchParams({
        ...(sessionId ? { session_id: sessionId } : {}),
        ...(archived ? { archived: "true" } : {}),
      })}`,
    ),
  createCopilotSession: (tenant: string) =>
    request<{ id: string; title: string }>(`/api/tenants/${tenant}/copilot/sessions`, {
      method: "POST",
    }),
  deleteCopilotSession: (tenant: string, sessionId: string) =>
    request<void>(`/api/tenants/${tenant}/copilot/sessions/${sessionId}`, { method: "DELETE" }),
  restoreCopilotSession: (tenant: string, sessionId: string) =>
    request<void>(`/api/tenants/${tenant}/copilot/sessions/${sessionId}/restore`, {
      method: "POST",
    }),
  changeProposals: (
    tenant: string,
    status: "pending" | "history",
    page = 1,
    query = "",
    size = 50,
    tool = "",
  ) =>
    request<{ items: CopilotProposal[]; page: Page }>(
      `/api/tenants/${tenant}/change-proposals?status=${status}&page=${page}&size=${size}` +
        `&q=${encodeURIComponent(query)}&tool=${encodeURIComponent(tool)}`,
    ),
  sendCopilotMessage: (
    tenant: string,
    sessionId: string,
    message: string,
    commitment?: string,
    analytics?: AnalyticsDefinition,
  ) =>
    request(`/api/tenants/${tenant}/copilot/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({
        message,
        ...(analytics
          ? { context: { kind: "analytics", definition: analytics } }
          : commitment
            ? { context: { kind: "commitment", id: commitment } }
            : {}),
      }),
    }),
  approveProposal: (tenant: string, proposalId: string, sessionId: string | null) =>
    request(`/api/tenants/${tenant}/change-proposals/${proposalId}/approve`, {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, confirmed: true }),
    }),
  rejectProposal: (tenant: string, proposalId: string, sessionId: string | null) =>
    request(`/api/tenants/${tenant}/change-proposals/${proposalId}/reject`, {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId }),
    }),
  inspector: (tenant: string, kind: string, id: string) =>
    request<InspectorData>(
      `/api/tenants/${tenant}/inspector/${encodeURIComponent(kind)}/${encodeURIComponent(id)}`,
    ),
  parties: (tenant: string) => request<PartyRow[]>(`/api/tenants/${tenant}/parties`),
  createParty: (tenant: string, body: Record<string, unknown>) =>
    request<PartyRow>(`/api/tenants/${tenant}/parties`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateParty: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<PartyRow>(`/api/tenants/${tenant}/parties/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  setPartyActive: (tenant: string, id: string, isActive: boolean) =>
    request<PartyRow>(`/api/tenants/${tenant}/parties/${id}/active`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    }),
  items: (tenant: string) => request<ItemRow[]>(`/api/tenants/${tenant}/items`),
  createItem: (tenant: string, body: Record<string, unknown>) =>
    request<ItemRow>(`/api/tenants/${tenant}/items`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateItem: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<ItemRow>(`/api/tenants/${tenant}/items/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  setItemActive: (tenant: string, id: string, isActive: boolean) =>
    request<ItemRow>(`/api/tenants/${tenant}/items/${id}/active`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    }),
  locations: (tenant: string) => request<LocationRow[]>(`/api/tenants/${tenant}/locations`),
  createLocation: (tenant: string, body: Record<string, unknown>) =>
    request<LocationRow>(`/api/tenants/${tenant}/locations`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateLocation: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<LocationRow>(`/api/tenants/${tenant}/locations/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  setLocationActive: (tenant: string, id: string, isActive: boolean) =>
    request<LocationRow>(`/api/tenants/${tenant}/locations/${id}/active`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    }),
  paymentTerms: (tenant: string) =>
    request<PaymentTermRow[]>(`/api/tenants/${tenant}/payment-terms`),
  createPaymentTerm: (tenant: string, body: Record<string, unknown>) =>
    request<PaymentTermRow>(`/api/tenants/${tenant}/payment-terms`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updatePaymentTerm: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<PaymentTermRow>(`/api/tenants/${tenant}/payment-terms/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  priceLists: (tenant: string) => request<PriceListRow[]>(`/api/tenants/${tenant}/price-lists`),
  createPriceList: (tenant: string, body: Record<string, unknown>) =>
    request<PriceListRow>(`/api/tenants/${tenant}/price-lists`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updatePriceList: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<PriceListRow>(`/api/tenants/${tenant}/price-lists/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  pricingGroups: (tenant: string) =>
    request<PricingGroupRow[]>(`/api/tenants/${tenant}/pricing-groups`),
  createPricingGroup: (tenant: string, body: Record<string, unknown>) =>
    request<PricingGroupRow>(`/api/tenants/${tenant}/pricing-groups`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updatePricingGroup: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<PricingGroupRow>(`/api/tenants/${tenant}/pricing-groups/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  reservations: (tenant: string, status = "") =>
    request<ReservationRow[]>(
      `/api/tenants/${tenant}/reservations?${new URLSearchParams({ status })}`,
    ),
  createReservation: (tenant: string, body: Record<string, unknown>) =>
    request(`/api/tenants/${tenant}/reservations`, { method: "POST", body: JSON.stringify(body) }),
  createHandlingUnit: (tenant: string, body: Record<string, unknown>) =>
    request<{ id: string }>(`/api/tenants/${tenant}/handling-units`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  createLot: (tenant: string, body: Record<string, unknown>) =>
    request<{ id: string }>(`/api/tenants/${tenant}/lots`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  createSerialUnit: (tenant: string, body: Record<string, unknown>) =>
    request<{ id: string }>(`/api/tenants/${tenant}/serial-units`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  holdCommitment: (tenant: string, id: string, body: Record<string, unknown>) =>
    request(`/api/tenants/${tenant}/commitments/${id}/holds`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  releaseCommitmentHold: (tenant: string, id: string) =>
    request(`/api/tenants/${tenant}/commitments/${id}/holds/release`, { method: "POST" }),
  holdDocumentCommitments: (tenant: string, id: string, body: Record<string, unknown>) =>
    request(`/api/tenants/${tenant}/documents/${id}/holds`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  releaseDocumentCommitmentHolds: (tenant: string, id: string) =>
    request(`/api/tenants/${tenant}/documents/${id}/holds/release`, { method: "POST" }),
  holdPartyDelivery: (tenant: string, id: string, body: Record<string, unknown>) =>
    request(`/api/tenants/${tenant}/parties/${id}/delivery-holds`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  releasePartyDeliveryHold: (tenant: string, id: string) =>
    request(`/api/tenants/${tenant}/parties/${id}/delivery-holds/release`, { method: "POST" }),
  movements: (tenant: string) => request<MovementRow[]>(`/api/tenants/${tenant}/movements`),
  createMovement: (tenant: string, body: Record<string, unknown>) =>
    request<MovementRow>(`/api/tenants/${tenant}/movements`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  movementCorrection: (tenant: string, id: string) =>
    request<MovementCorrectionSnapshot>(`/api/tenants/${tenant}/movements/${id}/correction`),
  previewMovementCorrection: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<MovementCorrectionPreview>(
      `/api/tenants/${tenant}/movements/${id}/correction/preview`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  correctMovement: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<MovementCorrectionResult>(`/api/tenants/${tenant}/movements/${id}/correction`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  previewLedgerReversal: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<LedgerReversalPreview>(
      `/api/tenants/${tenant}/ledger/posting-groups/${id}/reversal/preview`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  reverseLedgerPostingGroup: (tenant: string, id: string, body: Record<string, unknown>) =>
    request<LedgerReversalResult>(`/api/tenants/${tenant}/ledger/posting-groups/${id}/reversal`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  createSourceSystem: (tenant: string, body: { code: string; name: string; description: string }) =>
    request<SourceSystemRow>(`/api/tenants/${tenant}/source-systems`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  enqueueSource: (tenant: string, body: Record<string, unknown>) =>
    request(`/api/tenants/${tenant}/sources`, { method: "POST", body: JSON.stringify(body) }),
  setSourceSystemActive: (tenant: string, id: string, isActive: boolean) =>
    request<SourceSystemRow>(`/api/tenants/${tenant}/source-systems/${id}/active`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    }),
  setSourceCapabilityActive: (tenant: string, id: string, isActive: boolean) =>
    request<SourceCapabilityRow>(`/api/tenants/${tenant}/source-capabilities/${id}/active`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    }),
};

export type DeliveryRow = {
  type: "customer_delivery" | "supplier_delivery";
  id: string;
  tenant_id: string;
  document_id: string | null;
  document_line_id: string | null;
  party_id: string;
  counterparty: string | null;
  item_id: string;
  item: string | null;
  location_id: string;
  location: string | null;
  unit: string;
  promised: string;
  due_at: string | null;
  reserved: string;
  fulfilled: string;
  open: string;
  status: string;
};
export type DeliveryDetail = {
  case: DeliveryRow & {
    blockers: Array<{
      id: string;
      reason: string;
      scope?: "commitment" | "party";
      note?: string;
      created_at?: string;
    }>;
  };
  hold_reasons?: string[];
  inventory: {
    item_id: string;
    location_id: string;
    unit: string;
    physical: string;
    reserved: string;
    available: string;
  };
  links: Array<{ kind: string; id: string; label: string }>;
  history: {
    items: Array<{
      id: string;
      sequence: number;
      type: string;
      occurred_at: string;
      subject_type: string;
      subject_id: string;
    }>;
    has_more: boolean;
    next_cursor: string | null;
  };
  observation: { observed_at: string; evidence_available: boolean };
};
export const deliveryApi = {
  register: (
    tenant: string,
    query: string,
    page: number,
    status: "open" | "all",
    type: "customer_delivery" | "supplier_delivery",
    document: string,
    table: TableQuery = {},
  ) =>
    request<{ items: DeliveryRow[]; page: Page }>(
      `/api/tenants/${encodeURIComponent(tenant)}/delivery-work?${new URLSearchParams({ q: query, page: String(page), status, commitment_type: type, document_id: document })}${"&" + tableSearch(table)}`,
    ),
  list: (tenant: string, query = "", page = 1) =>
    request<{ items: DeliveryRow[]; page: Page }>(
      `/api/tenants/${encodeURIComponent(tenant)}/delivery-work?${new URLSearchParams({ q: query, page: String(page) })}`,
    ),
  detail: (tenant: string, id: string, before = "") =>
    request<DeliveryDetail>(
      `/api/tenants/${encodeURIComponent(tenant)}/delivery-work/${encodeURIComponent(id)}${before ? `?before=${encodeURIComponent(before)}` : ""}`,
    ),
};

export type ShipmentRow = {
  id: string;
  direction: "inbound" | "outbound";
  purpose: "customer_delivery" | "supplier_delivery" | "customer_return" | "supplier_return";
  counterparty_id: string;
  created_at: string;
  source_record_id: string | null;
  packages: Array<{
    id: string;
    carrier: string | null;
    tracking_number: string | null;
    source_record_id: string | null;
  }>;
  movements: Array<{
    id: string;
    package_id: string;
    type: string;
    item_id: string;
    quantity: string;
    occurred_at: string;
  }>;
  events: Array<{
    id: string;
    package_id: string | null;
    event_type: string;
    reporter_type: string;
    occurred_at: string | null;
    location_text: string | null;
    source_record_id: string | null;
  }>;
  event_history: Array<{
    id: string;
    package_id: string | null;
    event_type: string;
    reporter_type: string;
    occurred_at: string | null;
    recorded_at: string;
    location_text: string | null;
    source_record_id: string | null;
    superseded: boolean;
    supersession_id: string | null;
    supersession_reason: string | null;
    replacement_event_id: string | null;
  }>;
  observations: {
    announced: boolean;
    announced_at: string | null;
    dispatched: boolean;
    dispatched_at: string | null;
    received: boolean;
    received_at: string | null;
    externally_delivered: boolean;
    externally_delivered_at: string | null;
    has_exception: boolean;
  };
  quantities: {
    promised: string | null;
    announced: string | null;
    dispatched: string | null;
    externally_delivered: string | null;
    received: string | null;
  };
  discrepancies: {
    external_delivery_without_warehouse_receipt: boolean;
    warehouse_receipt_without_external_delivery: boolean;
  };
};
export const shipmentApi = {
  list: (
    tenant: string,
    query: string,
    page: number,
    direction: "inbound" | "outbound",
    purpose = "",
    carrier = "",
    size = 50,
  ) =>
    request<{ items: ShipmentRow[]; page: Page }>(
      `/api/tenants/${encodeURIComponent(tenant)}/shipments?${new URLSearchParams({ q: query, page: String(page), size: String(size), direction, purpose, carrier })}`,
    ),
  detail: (tenant: string, id: string) =>
    request<ShipmentRow>(
      `/api/tenants/${encodeURIComponent(tenant)}/shipments/${encodeURIComponent(id)}`,
    ),
};

export type DeliveryProposal = {
  movement_type?: string;
  id: string;
  tool: string;
  status: string;
  review: null | {
    token: string;
    intent: Record<string, unknown>;
    effect: Record<string, string>;
    state: {
      case: DeliveryRow;
      inventory: DeliveryDetail["inventory"];
      holds?: Array<{ id: string; reason_code: string; note: string }>;
    };
  };
  receipt: Record<string, unknown> | null;
  verification: string;
  links: Array<{ kind: string; id: string }>;
  observation: DeliveryDetail | null;
  observation_error: string | null;
};
export const deliveryActions = {
  references: (tenant: string, commitment: string, family: string, query = "") =>
    request<{ items: Array<{ id: string; label: string }>; has_more: boolean }>(
      `/api/tenants/${encodeURIComponent(tenant)}/delivery-references?${new URLSearchParams({ commitment_id: commitment, family, q: query })}`,
    ),
  prepare: (tenant: string, requestId: string, tool: string, args: Record<string, unknown>) =>
    request<DeliveryProposal>(
      `/api/tenants/${encodeURIComponent(tenant)}/delivery-actions/prepare`,
      { method: "POST", body: JSON.stringify({ request_id: requestId, tool, arguments: args }) },
    ),
  detail: (tenant: string, id: string) =>
    request<DeliveryProposal>(
      `/api/tenants/${encodeURIComponent(tenant)}/delivery-actions/${encodeURIComponent(id)}`,
    ),
  review: (tenant: string, id: string) =>
    request<DeliveryProposal>(
      `/api/tenants/${encodeURIComponent(tenant)}/delivery-actions/${encodeURIComponent(id)}/review`,
      { method: "POST" },
    ),
  reconcile: (tenant: string, id: string) =>
    request<DeliveryProposal>(
      `/api/tenants/${encodeURIComponent(tenant)}/delivery-actions/${encodeURIComponent(id)}/reconcile`,
      { method: "POST" },
    ),
  confirm: (tenant: string, id: string, token: string) =>
    request<{ id: string; status: string; output: Record<string, unknown> }>(
      `/api/tenants/${encodeURIComponent(tenant)}/change-proposals/${encodeURIComponent(id)}/approve`,
      { method: "POST", body: JSON.stringify({ review_token: token, confirmed: true }) },
    ),
};

export type ReferenceFamily = "customer" | "supplier" | "item" | "location";
export type InsightMetric =
  | "open"
  | "fully_reserved"
  | "needs_reservation"
  | "overdue"
  | "unknown_due"
  | "created"
  | "shipped";
export type Insights = {
  position: Record<
    "open" | "fully_reserved" | "needs_reservation" | "overdue" | "unknown_due",
    number
  > & { coverage_percent: string | null };
  series: { date: string; created: number; shipped: number }[];
  window: { days: number; start: string; end: string; timezone: string };
  observed_at: string;
  coverage: string;
};
export type ReferenceRow = {
  id: string;
  family: ReferenceFamily;
  name: string;
  sku?: string;
  unit?: string;
  is_active: boolean;
};
export type ReferenceDetail = ReferenceRow & {
  expected_revision: string;
  source_record_id?: string;
  roles?: string[];
  type?: string;
  [key: string]: unknown;
};
export type ReferenceProposal = {
  id: string;
  tool: string;
  status: string;
  input: { records: Record<string, unknown>[] };
  output: {
    records?: { id: string; changes?: { field: string; before: unknown; after: unknown }[] }[];
  };
  links: { family: string; id: string }[];
};
export const referenceTools = [
  "party_create",
  "party_update",
  "item_create",
  "item_update",
  "location_create",
  "location_update",
];
export const workspaceApi = {
  insights: (tenant: string, days = 30) =>
    request<Insights>(`/api/tenants/${tenant}/analytics?days=${days}`),
  contributors: (tenant: string, metric: InsightMetric, days: number, day: string, page: number) =>
    request<{ items: { id: string; kind: string; at: string; label?: string }[]; page: Page }>(
      `/api/tenants/${tenant}/analytics/contributors?${new URLSearchParams({ metric, days: String(days), page: String(page), ...(day ? { day } : {}) })}`,
    ),
  references: (
    tenant: string,
    family: ReferenceFamily,
    q: string,
    page: number,
    active: boolean,
    table: TableQuery = {},
  ) =>
    request<{ items: ReferenceRow[]; page: Page }>(
      `/api/tenants/${tenant}/master-data?${new URLSearchParams({ family, q, page: String(page), include_inactive: String(active) })}${"&" + tableSearch(table)}`,
    ),
  reference: (tenant: string, family: ReferenceFamily, id: string) =>
    request<ReferenceDetail>(
      `/api/tenants/${tenant}/master-data/${family}/${encodeURIComponent(id)}`,
    ),
  prepare: (
    tenant: string,
    family: ReferenceFamily,
    operation: "create" | "update",
    record: Record<string, unknown>,
    request_id: string,
  ) =>
    request<ReferenceProposal>(`/api/tenants/${tenant}/master-data/prepare`, {
      method: "POST",
      body: JSON.stringify({ family, operation, record, request_id }),
    }),
  proposal: (tenant: string, id: string) =>
    request<ReferenceProposal>(
      `/api/tenants/${tenant}/master-data/proposals/${encodeURIComponent(id)}`,
    ),
  confirm: (tenant: string, id: string) =>
    request<ReferenceProposal>(
      `/api/tenants/${tenant}/master-data/proposals/${encodeURIComponent(id)}/confirm`,
      { method: "POST", body: JSON.stringify({ confirmed: true }) },
    ),
};

export type WarehouseView = "stock" | "reservations" | "movements";
export type WarehouseRow = {
  id: string;
  name?: string;
  sku: string;
  unit: string;
  physical?: string;
  reserved?: string;
  available?: string;
  item_id?: string;
  item?: string;
  quantity?: string;
  status?: string;
  type?: string;
  at?: string;
  location?: string;
  from_location?: string;
  to_location?: string;
  commitment_id?: string;
  delivery_id?: string;
  correction_role?: string;
};
export type AttentionRow = {
  context?: string | null;
  id: string;
  class_id: string;
  severity: string;
  title: string;
  impact: string;
  record_type: string;
  record_id: string;
  cause_ids: string[];
  causal_values: Record<string, unknown>;
  trace: Record<string, string | null>;
  target: { kind: string; id: string; delivery_id?: string };
  guidance?: string;
  observed_at?: string;
};
export const operationsApi = {
  warehouse: (
    tenant: string,
    view: WarehouseView,
    q: string,
    state: string,
    item: string,
    page: number,
    table: TableQuery = {},
  ) =>
    request<{
      items: WarehouseRow[];
      page: Page;
      scope: { view: WarehouseView; item_id: string | null; item: string | null };
      observed_at: string;
    }>(
      `/api/tenants/${tenant}/warehouse/${view}?${new URLSearchParams({ q, state, page: String(page), ...(item ? { item_id: item } : {}) })}${"&" + tableSearch(table)}`,
    ),
  attention: (
    tenant: string,
    q: string,
    severity: string,
    page: number,
    classId = "",
    size?: number,
  ) =>
    request<{
      items: AttentionRow[];
      page: Page;
      observed_at: string | null;
      metadata?: ProjectionMetadata;
    }>(
      `/api/tenants/${tenant}/attention?${new URLSearchParams({
        q,
        severity,
        page: String(page),
        ...(classId ? { class_id: classId } : {}),
        ...(size ? { size: String(size) } : {}),
      })}`,
    ),
  /** Open findings per exception class from the stored generation; every catalog class is listed. */
  attentionSummary: (tenant: string) =>
    request<{
      classes: { class_id: string; open: number }[];
      total: number;
      observed_at: string | null;
      metadata?: ProjectionMetadata;
    }>(`/api/tenants/${tenant}/attention/summary`),
  finding: (tenant: string, id: string) =>
    request<AttentionRow>(`/api/tenants/${tenant}/attention/${encodeURIComponent(id)}`),
};

export type SourceMetadataRow = RecentSourceRow & { supersedes_source_record_id: string | null };
export const sourceWorkspaceApi = {
  systems: (tenant: string, q: string, page: number) =>
    request<{ items: SourceSystemRow[]; page: Page }>(
      `/api/tenants/${tenant}/data-sources/systems?${new URLSearchParams({ q, page: String(page) })}`,
    ),
  records: (tenant: string, q: string, system: string, page: number, table: TableQuery = {}) =>
    request<{ items: SourceMetadataRow[]; page: Page }>(
      `/api/tenants/${tenant}/data-sources/records?${new URLSearchParams({ q, source_system: system, page: String(page) })}${"&" + tableSearch(table)}`,
    ),
};

export type CorrectionPool = {
  item_id: string;
  item: string;
  location_id: string;
  location: string;
  unit: string;
  physical: string;
  reserved: string;
  delta: string;
  after: string;
  available_after: string;
};
export type CorrectionProposal = Omit<DeliveryProposal, "review" | "observation"> & {
  review: null | {
    token: string;
    intent: Record<string, unknown>;
    state: {
      correction: MovementCorrectionPreview;
      pools: CorrectionPool[];
      commitments: DeliveryRow[];
    };
  };
  observation: null | { pools: CorrectionPool[] };
};
export const correctionActions = {
  prepare: (tenant: string, requestId: string, args: Record<string, unknown>) =>
    deliveryActions.prepare(
      tenant,
      requestId,
      "movement_correct",
      args,
    ) as unknown as Promise<CorrectionProposal>,
  detail: (tenant: string, id: string) =>
    deliveryActions.detail(tenant, id) as unknown as Promise<CorrectionProposal>,
  review: (tenant: string, id: string) =>
    deliveryActions.review(tenant, id) as unknown as Promise<CorrectionProposal>,
  reconcile: (tenant: string, id: string) =>
    deliveryActions.reconcile(tenant, id) as unknown as Promise<CorrectionProposal>,
};

export type OrderLineInput = {
  item_id: string;
  quantity: string;
  unit_price: string;
  gross_amount: string;
  [key: string]: unknown;
};
export type OrderInput = {
  direction: string;
  number: string;
  company_party_id: string;
  counterparty_id: string;
  location_id: string;
  currency: string;
  gross_amount: string;
  lines: OrderLineInput[];
  [key: string]: unknown;
};
export type OrderProposal = Omit<DeliveryProposal, "review" | "observation"> & {
  review: null | {
    token: string;
    intent: OrderInput;
    state: {
      creation: { direction: string; document: Record<string, unknown>; lines: OrderLineInput[] };
      references: Record<string, { id: string; name: string }>;
      items: Record<string, { id: string; name: string; sku: string; unit: string }>;
    };
  };
  observation: null | { deliveries: DeliveryRow[] };
};
export const orderActions = {
  prepare: (tenant: string, requestId: string, args: OrderInput) =>
    deliveryActions.prepare(
      tenant,
      requestId,
      "order_create",
      args,
    ) as unknown as Promise<OrderProposal>,
  detail: (tenant: string, id: string) =>
    deliveryActions.detail(tenant, id) as unknown as Promise<OrderProposal>,
  review: (tenant: string, id: string) =>
    deliveryActions.review(tenant, id) as unknown as Promise<OrderProposal>,
  reconcile: (tenant: string, id: string) =>
    deliveryActions.reconcile(tenant, id) as unknown as Promise<OrderProposal>,
};

export type InvoiceInput = {
  order_line_id?: string;
  lines?: { order_line_id: string; quantity: string; gross_amount: string }[];
  quantity?: string;
  gross_amount: string;
  number: string;
  effective_at?: string;
  [key: string]: unknown;
};
export type InvoiceProposal = Omit<DeliveryProposal, "review" | "observation"> & {
  review: null | {
    token: string;
    intent: InvoiceInput;
    effect: { debit: string; credit: string };
    state: {
      creation: {
        direction: string;
        number: string;
        quantity: string;
        gross_amount: string;
        currency: string;
        unit: string;
        effective_at?: string;
      };
      billing?: (BillingAvailability & { requested: string; remaining_after: string })[];
      positions?: {
        order_line_id: string;
        quantity: string;
        gross_amount: string;
        item: { name: string };
        line: { unit: string };
      }[];
      order: { id: string; number: string };
      party: { name: string };
      item: { name: string };
    };
  };
  observation: null;
};
export const invoiceActions = {
  prepare: (tenant: string, request: string, tool: string, args: InvoiceInput) =>
    deliveryActions.prepare(tenant, request, tool, args) as unknown as Promise<InvoiceProposal>,
  detail: (tenant: string, id: string) =>
    deliveryActions.detail(tenant, id) as unknown as Promise<InvoiceProposal>,
  review: (tenant: string, id: string) =>
    deliveryActions.review(tenant, id) as unknown as Promise<InvoiceProposal>,
  reconcile: (tenant: string, id: string) =>
    deliveryActions.reconcile(tenant, id) as unknown as Promise<InvoiceProposal>,
};

export type PaymentInput = {
  invoice_id: string;
  amount: string;
  payment_number?: string | null;
  effective_at?: string | null;
  source_record_id?: string | null;
  [key: string]: unknown;
};
export type PaymentProposal = Omit<DeliveryProposal, "review" | "observation"> & {
  review: null | {
    token: string;
    intent: PaymentInput;
    state: {
      creation: {
        direction: string;
        invoice_id: string;
        amount: string;
        currency: string;
        payment_number?: string | null;
        effective_at?: string | null;
      };
      invoice: { id: string; number: string };
      party: { name: string };
      source: null | { id: string; source_system: string; external_id: string };
      open_before: string;
      open_after: string;
    };
  };
  payment_entry_id?: string;
  observation: null | { open: string; allocation_active: boolean };
};
export const paymentActions = {
  prepare: (tenant: string, request: string, tool: string, args: PaymentInput) =>
    deliveryActions.prepare(tenant, request, tool, args) as unknown as Promise<PaymentProposal>,
  detail: (tenant: string, id: string) =>
    deliveryActions.detail(tenant, id) as unknown as Promise<PaymentProposal>,
  review: (tenant: string, id: string) =>
    deliveryActions.review(tenant, id) as unknown as Promise<PaymentProposal>,
  reconcile: (tenant: string, id: string) =>
    deliveryActions.reconcile(tenant, id) as unknown as Promise<PaymentProposal>,
};

export type FinancialReversalInput = {
  posting_group_id: string;
  reason: string;
  expected_revision?: string;
  preview_fingerprint?: string;
};
type ReversalBalance = {
  id: string;
  number: string;
  currency: string;
  before: string;
  after: string;
};
type ReversalEffects = {
  billing?: (BillingAvailability & {
    invoiced_before: string;
    invoiced_after: string;
    remaining_before: string;
    remaining_after: string;
  })[];
  invoices: ReversalBalance[];
  payments: ReversalBalance[];
  newly_inactive: { id: string; amount: string; currency: string }[];
  already_inactive: { id: string; amount: string; currency: string }[];
};
export type FinancialReversalProposal = Omit<DeliveryProposal, "review" | "observation"> & {
  review: null | {
    token: string;
    intent: FinancialReversalInput;
    state: {
      party: null | { name: string };
      documents: { id: string; number: string; type: string }[];
      effects: ReversalEffects;
      preview: {
        posting_group_id: string;
        reason: string;
        original_entries: { id: string }[];
        inverse_entries: {
          account: string;
          amount: string;
          currency: string;
          debit_credit: string;
        }[];
      };
    };
  };
  observation: null | ReversalEffects;
};
export const financialReversalActions = {
  choices: (tenant: string, q: string, page: number) =>
    request<{
      items: { id: string; number: string; party: string; currency: string; amount: string }[];
      page: Page;
    }>(
      `/api/tenants/${tenant}/finance/reversal-choices?${new URLSearchParams({ q, page: String(page) })}`,
    ),
  prepare: (tenant: string, id: string, args: FinancialReversalInput) =>
    deliveryActions.prepare(
      tenant,
      id,
      "ledger_reverse",
      args,
    ) as unknown as Promise<FinancialReversalProposal>,
  detail: (tenant: string, id: string) =>
    deliveryActions.detail(tenant, id) as unknown as Promise<FinancialReversalProposal>,
  review: (tenant: string, id: string) =>
    deliveryActions.review(tenant, id) as unknown as Promise<FinancialReversalProposal>,
  reconcile: (tenant: string, id: string) =>
    deliveryActions.reconcile(tenant, id) as unknown as Promise<FinancialReversalProposal>,
};

export type CreditInput = {
  invoice_id: string;
  lines: { invoice_line_id: string; quantity: string; gross_amount: string }[];
  gross_amount: string;
  number: string;
  reason: string;
  allocation_amount: string;
  effective_at?: string;
  [key: string]: unknown;
};
export type CreditContext = {
  invoice: { id: string; number: string; currency: string; gross_amount: string };
  party: { name: string };
  open_amount: string;
  remaining_amount: string;
  credited_amount: string;
  positions: {
    id: string;
    label: string;
    quantity: string;
    credited: string;
    remaining: string;
    unit: string;
    legacy_credit_ids: string[];
    evidence: { id: string; number: string; quantity: string; released: boolean }[];
  }[];
};
export type CreditProposal = Omit<DeliveryProposal, "review" | "observation"> & {
  review: null | {
    token: string;
    intent: CreditInput;
    state: {
      creation: CreditInput & { selections: CreditInput["lines"] };
      context: CreditContext;
      invoice_after: string;
      credit_open: string;
    };
  };
  observation: null;
};
export const creditActions = {
  context: (tenant: string, invoice: string) =>
    request<CreditContext>(`/api/tenants/${tenant}/finance/invoice-credit/${invoice}`),
  prepare: (tenant: string, requestId: string, tool: string, args: CreditInput) =>
    deliveryActions.prepare(tenant, requestId, tool, args) as unknown as Promise<CreditProposal>,
  detail: (tenant: string, id: string) =>
    deliveryActions.detail(tenant, id) as unknown as Promise<CreditProposal>,
  review: (tenant: string, id: string) =>
    deliveryActions.review(tenant, id) as unknown as Promise<CreditProposal>,
  reconcile: (tenant: string, id: string) =>
    deliveryActions.reconcile(tenant, id) as unknown as Promise<CreditProposal>,
};

export type RefundInput = {
  credit_note_id: string;
  amount: string;
  refund_number?: string | null;
  effective_at?: string | null;
  source_record_id?: string | null;
  [key: string]: unknown;
};
export type RefundProposal = Omit<PaymentProposal, "review"> & {
  review: (Omit<NonNullable<PaymentProposal["review"]>, "intent"> & { intent: RefundInput }) | null;
  payment_document_id?: string;
};
export const refundActions = {
  prepare: (tenant: string, request: string, args: RefundInput) =>
    deliveryActions.prepare(
      tenant,
      request,
      "customer_refund_post",
      args,
    ) as unknown as Promise<RefundProposal>,
  detail: (tenant: string, id: string) =>
    deliveryActions.detail(tenant, id) as unknown as Promise<RefundProposal>,
  review: (tenant: string, id: string) =>
    deliveryActions.review(tenant, id) as unknown as Promise<RefundProposal>,
  reconcile: (tenant: string, id: string) =>
    deliveryActions.reconcile(tenant, id) as unknown as Promise<RefundProposal>,
};

export type ItemImportConfig = {
  artifact_id: string;
  source_system: string;
  mapping: Record<string, string>;
  default_unit: string;
};
export type ItemImportArtifact = {
  id: string;
  filename: string;
  sha256: string;
  columns: string[];
  row_count: number;
  mapping: Record<string, string>;
};
export type ItemImportProposal = {
  id: string;
  status: string;
  verification: string;
  review: {
    token: string;
    intent: { import_file: ItemImportConfig };
    state: {
      creation: {
        artifact: { id: string; filename: string };
        source_system: string;
        default_unit: string;
        rows: Array<{ sku: string; name: string; unit: string }>;
      };
    };
  };
  receipt: { artifact_id: string; source_record_id: string; item_ids: string[] } | null;
};
export const itemImports = {
  stage: (tenant: string, file: File) =>
    request<ItemImportArtifact>(
      `/api/tenants/${encodeURIComponent(tenant)}/item-imports/artifacts?${new URLSearchParams({ filename: file.name })}`,
      { method: "POST", headers: { "Content-Type": "text/csv" }, body: file },
    ),
  prepare: (tenant: string, requestId: string, config: ItemImportConfig) =>
    request<ItemImportProposal>(`/api/tenants/${encodeURIComponent(tenant)}/item-imports/prepare`, {
      method: "POST",
      body: JSON.stringify({ request_id: requestId, config }),
    }),
  detail: (tenant: string, id: string) =>
    request<ItemImportProposal>(
      `/api/tenants/${encodeURIComponent(tenant)}/delivery-actions/${encodeURIComponent(id)}`,
    ),
  original: (tenant: string, artifact: string) =>
    `/api/tenants/${encodeURIComponent(tenant)}/item-imports/artifacts/${encodeURIComponent(artifact)}/download`,
};

export type OpeningProposal = Omit<DeliveryProposal, "review" | "observation"> & {
  intent: Record<string, unknown>;
  review: null | {
    token: string;
    intent: Record<string, unknown>;
    state: {
      item: { id: string; sku: string; name: string; unit: string };
      location: { id: string; name: string };
      physical: string;
      reserved: string;
    };
    effect: { added: string; physical_after: string; reserved_after: string };
  };
  observation: null | { physical: string; reserved: string };
};
export const openingActions = {
  prepare: (tenant: string, requestId: string, args: Record<string, unknown>) =>
    deliveryActions.prepare(
      tenant,
      requestId,
      "movement_create",
      args,
    ) as unknown as Promise<OpeningProposal>,
  detail: (tenant: string, id: string) =>
    deliveryActions.detail(tenant, id) as unknown as Promise<OpeningProposal>,
  review: (tenant: string, id: string) =>
    deliveryActions.review(tenant, id) as unknown as Promise<OpeningProposal>,
  reconcile: (tenant: string, id: string) =>
    deliveryActions.reconcile(tenant, id) as unknown as Promise<OpeningProposal>,
};

export type CustomerHoldTool = "party_delivery_hold" | "party_delivery_hold_release";
export type CustomerHold = {
  id: string;
  party_id: string;
  hold_type: string;
  reason_code: string;
  note: string;
  created_by: string;
  created_at: string;
};
export type CustomerHoldContext = {
  party: { id: string; name: string; type: string; roles: string[]; is_active: boolean };
  holds: CustomerHold[];
  reasons: string[];
};
export type CustomerHoldProposal = Omit<DeliveryProposal, "review" | "observation"> & {
  intent: Record<string, unknown>;
  review: null | {
    token: string;
    intent: Record<string, unknown>;
    state: Omit<CustomerHoldContext, "reasons">;
    effect: Record<string, string>;
  };
  observation: CustomerHoldContext | null;
};
export const customerHoldActions = {
  context: (tenant: string, party: string) =>
    request<CustomerHoldContext>(
      `/api/tenants/${encodeURIComponent(tenant)}/customer-holds/${encodeURIComponent(party)}`,
    ),
  prepare: (
    tenant: string,
    requestId: string,
    tool: CustomerHoldTool,
    args: Record<string, unknown>,
  ) =>
    deliveryActions.prepare(
      tenant,
      requestId,
      tool,
      args,
    ) as unknown as Promise<CustomerHoldProposal>,
  detail: (tenant: string, id: string) =>
    deliveryActions.detail(tenant, id) as unknown as Promise<CustomerHoldProposal>,
  review: (tenant: string, id: string) =>
    deliveryActions.review(tenant, id) as unknown as Promise<CustomerHoldProposal>,
  reconcile: (tenant: string, id: string) =>
    deliveryActions.reconcile(tenant, id) as unknown as Promise<CustomerHoldProposal>,
};

// ---------------------------------------------------------------- Storyline (spec 182)

export type StorylineText = { en?: string; de?: string; nl?: string; es?: string };
export type StorylineBranch = {
  key: string;
  label: StorylineText;
  next: string;
  default: boolean;
};
export type StorylineChapterEntry = {
  key: string;
  status: "done" | "current" | "upcoming";
  kind: "command" | "read" | "unsupported";
  step_id: string | null;
  step_status: string | null;
  refused: { code: string; detail: string; phase?: string } | null;
  marker: { sequence: number; at: string } | null;
  title: StorylineText;
  view: string | null;
  command: string | null;
  branches: StorylineBranch[];
};
export type StorylineState = {
  run_id: string;
  tenant_id: string;
  status: string;
  key: string;
  version: number;
  title: StorylineText;
  chapters: StorylineChapterEntry[];
  current_chapter: string | null;
  branches: Record<string, string>;
  start: string | null;
};
export type StorylineChapter = {
  key: string;
  kind: "command" | "read" | "unsupported";
  title: StorylineText;
  situation: StorylineText;
  explain: StorylineText;
  view: string | null;
  command: string | null;
  input: Record<string, unknown>;
  context: Record<string, { tool: string; input: Record<string, unknown>; field: string | null }>;
  reads: Array<{ tool: string; input: Record<string, unknown> }>;
  primary: { record_type: string; from: string } | null;
  expect: { raised: string[]; cleared: string[]; facts: string[] };
  next: string | null;
  branches: StorylineBranch[];
};
export type StorylineStep = {
  step_id: string;
  chapter: string;
  sequence: number;
  status: "done" | "refused" | "pending" | "rejected";
  proposal_id: string | null;
  proposal_status: string | null;
  preview_revision: string | null;
  review: Record<string, unknown> | null;
  arguments: Record<string, unknown> | null;
  output: Record<string, unknown> | null;
  refused: { code: string; detail: string; phase?: string } | null;
  context: Record<string, unknown> | null;
  marker: { sequence: number; at: string } | null;
  receipt: {
    kind: string;
    records?: Array<{ family: string; id: string }>;
    event_ids?: string[];
    event_sequence?: number;
    results?: Array<{ tool: string; input: Record<string, unknown>; result: unknown }>;
  } | null;
  error?: { code: string; detail: string; unresolved?: boolean };
};
export type StorylineChapterDetail = {
  chapter: StorylineChapter;
  status: string;
  preconditions: Array<{ kind: string; name: string; holds: boolean }>;
  can_run: boolean;
  step: StorylineStep | null;
};
export type StorylineTraceItem = {
  id: string;
  ordinal: number;
  step_id: string | null;
  chapter: string | null;
  kind: "view" | "read" | "propose" | "confirm" | "reject" | "error";
  name: string;
  access: "read" | "propose" | "confirm";
  actor: string;
  proposal_id: string | null;
  marker: { sequence: number; at: string } | null;
  before_exceptions: string[] | null;
  input: unknown;
  result: unknown;
  duration_ms: number | null;
  recorded_at: string;
};
export type StorylineDelta = {
  range: {
    after_sequence: number;
    after_at: string | null;
    latest_sequence: number;
    available: boolean;
    has_more: boolean;
  };
  events: Array<{
    id: string;
    sequence: number;
    type: string;
    subject_type: string;
    subject_id: string;
    title: string;
    occurred_at: string;
    recorded_at: string;
    action_id: string | null;
  }>;
  facts: Array<{
    id: string;
    subject_type: string;
    subject_id: string;
    predicate: string;
    value: unknown;
    observed_at: string;
    recorded_at: string;
  }>;
  records: Array<{ record_type: string; record_id: string }>;
  exceptions: {
    raised: StorylineFinding[];
    cleared: StorylineFinding[];
  };
  graph: {
    record: { record_type: string; record_id: string } | null;
    nodes: Array<{ record_type: string; record_id: string; new: boolean; primary: boolean }>;
    edges: Array<{ from: string; to: string; relation: string; new: boolean }>;
  };
};
export type StorylineFinding = {
  id: string;
  class_id: string;
  record_type: string | null;
  record_id: string | null;
  label: StorylineText;
  title: string;
  impact: string | null;
  severity: string | null;
  clears_through: string;
};
export type StorylineToolReference = {
  key: string;
  kind: "command" | "read" | "view" | "exception";
  label: StorylineText;
  description: string;
  access?: string;
  parameters?: Array<{ name: string; type: string; required: boolean; description: string }>;
  projections?: string[];
  clears_through?: string;
  docs_path: string;
};
export type StorylineLibraryItem = {
  key: string;
  version: number;
  title: StorylineText;
  summary: StorylineText;
  author: string | null;
  chapters: number;
  origin: "builtin" | "import";
  imported_at: string | null;
  run: {
    run_id: string;
    tenant_id: string;
    status: string;
    current_chapter: string | null;
    position: number | null;
    total: number;
    done: number;
    company_name: string | null;
  } | null;
};
export type StorylineRun = {
  run_id: string;
  tenant_id: string | null;
  status: string;
  key: string;
  version: number;
  error: { entry: number | null; command: string | null; detail: string } | null;
  current_chapter: string | null;
};

export const storylineApi = {
  library: () =>
    request<{ items: StorylineLibraryItem[]; enabled: boolean }>("/api/storyline/library"),
  start: (key: string, version: number, requestKey: string) =>
    request<StorylineRun>("/api/storyline/runs", {
      method: "POST",
      body: JSON.stringify({ key, version, request_key: requestKey, confirmed: true }),
    }),
  state: (tenant: string, signal?: AbortSignal) =>
    request<StorylineState>(`/api/tenants/${tenant}/storyline`, { signal }),
  chapter: (tenant: string, key: string) =>
    request<StorylineChapterDetail>(`/api/tenants/${tenant}/storyline/chapters/${key}`),
  prepare: (tenant: string, key: string, requestKey: string) =>
    request<StorylineStep>(`/api/tenants/${tenant}/storyline/chapters/${key}/prepare`, {
      method: "POST",
      body: JSON.stringify({ request_key: requestKey }),
    }),
  confirm: (tenant: string, key: string, stepId: string, previewRevision: string) =>
    request<StorylineStep>(`/api/tenants/${tenant}/storyline/chapters/${key}/confirm`, {
      method: "POST",
      body: JSON.stringify({ step_id: stepId, preview_revision: previewRevision, confirmed: true }),
    }),
  reject: (tenant: string, key: string, stepId: string) =>
    request<StorylineStep>(`/api/tenants/${tenant}/storyline/chapters/${key}/reject`, {
      method: "POST",
      body: JSON.stringify({ step_id: stepId, confirmed: true }),
    }),
  branch: (tenant: string, chapter: string, branch: string) =>
    request<{ current_chapter: string | null; branches: Record<string, string> }>(
      `/api/tenants/${tenant}/storyline/branches`,
      { method: "POST", body: JSON.stringify({ chapter, branch }) },
    ),
  restart: (tenant: string, requestKey: string) =>
    request<StorylineRun>(`/api/tenants/${tenant}/storyline/restart`, {
      method: "POST",
      body: JSON.stringify({ request_key: requestKey, confirmed: true }),
    }),
  trace: (tenant: string, stepId?: string, signal?: AbortSignal) => {
    const params = new URLSearchParams(stepId ? { step_id: stepId } : { limit: "50" });
    return request<{ items: StorylineTraceItem[]; has_more: boolean }>(
      `/api/tenants/${tenant}/storyline/trace?${params}`,
      { signal },
    );
  },
  delta: (tenant: string, stepId: string, signal?: AbortSignal) =>
    request<StorylineDelta>(
      `/api/tenants/${tenant}/storyline/delta?step_id=${encodeURIComponent(stepId)}`,
      { signal },
    ),
  /** Calls made outside any chapter (spec 182, FR-011). */
  freeTrace: (tenant: string, signal?: AbortSignal) =>
    request<{ items: StorylineTraceItem[]; has_more: boolean }>(
      `/api/tenants/${tenant}/storyline/trace?free=true&limit=100`,
      { signal },
    ),
  /** What one confirmation outside the story added, by its trace ordinal. */
  deltaAt: (tenant: string, ordinal: number, signal?: AbortSignal) =>
    request<StorylineDelta>(`/api/tenants/${tenant}/storyline/delta?ordinal=${ordinal}`, {
      signal,
    }),
  toolReference: (tenant: string, name: string) =>
    request<StorylineToolReference>(`/api/tenants/${tenant}/storyline/tool-reference/${name}`),
  exportUrl: (key: string, version: number, format: "yaml" | "json") =>
    `/api/storyline/library/${encodeURIComponent(key)}/${version}?download=${format}`,
  /** The run's confirmed commands as a storyline draft to edit and import (FR-021). */
  draftUrl: (runId: string, format: "yaml" | "json" = "yaml") =>
    `/api/storyline/runs/${encodeURIComponent(runId)}/draft?format=${format}`,
  importPackage: async (file: File, replace: boolean) => {
    const params = new URLSearchParams({
      filename: file.name,
      replace: replace ? "true" : "false",
    });
    const response = await fetch(`/api/storyline/library?${params}`, {
      method: "POST",
      credentials: "include",
      headers: { Accept: "application/json", "Content-Type": file.type || "application/yaml" },
      body: file,
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const error = new APIError(
        typeof payload?.detail === "string"
          ? payload.detail
          : `Reality API returned ${response.status}`,
        response.status,
        payload?.code,
      );
      (error as APIError & { errors?: StorylineImportError[] }).errors = payload?.errors;
      throw error;
    }
    return payload as StorylineImportResult;
  },
  deletePackage: (key: string, version: number) =>
    request<void>(`/api/storyline/library/${encodeURIComponent(key)}/${version}`, {
      method: "DELETE",
    }),
};
export type StorylineImportError = { path: string; code: string; detail: string };
export type StorylineImportResult = {
  key: string;
  version: number;
  title: StorylineText;
  chapters: number;
  warnings: StorylineImportError[];
  replaced: boolean;
};
export type AnalyticsFilter = {
  field?: string;
  op?: string;
  value?: string | number | boolean;
  values?: (string | number | boolean)[];
  relationship?: "purchases" | "order_lines" | "outbound";
  where?: AnalyticsFilter;
  time?: AnalyticsDefinition["time"];
  all?: AnalyticsFilter[];
  any?: AnalyticsFilter[];
};
export type AnalyticsDefinition = {
  version?: 1;
  dataset: string;
  dimensions: string[];
  measures: string[];
  where?: AnalyticsFilter | null;
  time?: {
    field: string;
    timezone: string;
    window: {
      kind: string;
      start?: string;
      end?: string;
      year?: number;
      week?: number;
      count?: number;
    };
  } | null;
  cancellation?: string;
  sort?: { field: string; direction: "asc" | "desc" }[];
  compare?: "previous_period" | AnalyticsDefinition["time"] | null;
  presentation?: {
    kind: "table" | "bar" | "line" | "pivot";
    rows?: string[];
    column?: string | null;
    measures?: string[];
  };
};
export type AnalyticsDataset = {
  key: string;
  label: string;
  grain: string;
  relationships?: ("purchases" | "order_lines" | "outbound")[];
  dimensions: {
    key: string;
    label: string;
    type: string;
    operators: string[];
    groupable?: boolean;
  }[];
  measures: { key: string; label: string; aggregation: string; partition: string | null }[];
};
export type AnalyticsCatalog = {
  version: number;
  datasets: AnalyticsDataset[];
  starters: { name: string; definition: AnalyticsDefinition }[];
  limits: Record<string, number>;
};
export type AnalyticsResult = {
  executed_definition: AnalyticsDefinition;
  definition_fingerprint: string;
  columns: { key: string; label: string; type: string }[];
  rows: Record<string, string | number | null>[];
  population_totals: Record<string, string | number | null>[];
  page: { has_more: boolean; next_cursor: string | null; total: number };
  pivot?: {
    row_dimensions: string[];
    column_dimension: string;
    measures: string[];
    cells: Record<string, string | number | null>[];
    row_totals: Record<string, string | number | null>[];
    column_totals: Record<string, string | number | null>[];
    totals: Record<string, string | number | null>[];
  } | null;
  comparison: AnalyticsResult | null;
  metadata: {
    observed_at: string;
    resolved_window: { start: string; end: string; timezone: string; field: string } | null;
    missing_values: Record<string, number>;
    undated_excluded: number;
    history_scope: string;
    consistency?: string;
  };
};
export type AnalyticsReport = {
  id: string;
  name: string;
  definition: AnalyticsDefinition;
  revision: number;
  updated_at: string;
  deleted: boolean;
};
export const analyticsApi = {
  proposal: (tenant: string, id: string) =>
    request<{
      proposal_id: string;
      status: string;
      operation: string;
      name: string;
      definition: AnalyticsDefinition;
      expected_revision: number | null;
    }>(`/api/tenants/${tenant}/analytics/reports/proposals/${encodeURIComponent(id)}`),
  catalog: (tenant: string) =>
    request<AnalyticsCatalog>(`/api/tenants/${tenant}/analytics/catalog`),
  query: (tenant: string, definition: AnalyticsDefinition, signal?: AbortSignal, cursor?: string) =>
    request<AnalyticsResult>(`/api/tenants/${tenant}/analytics/query`, {
      method: "POST",
      body: JSON.stringify({ definition, cursor }),
      signal,
    }),
  contributors: (
    tenant: string,
    definition: AnalyticsDefinition,
    group: Record<string, unknown>,
    measure: string,
    cursor?: string,
  ) =>
    request<{
      records: Record<string, string | null>[];
      total: number;
      has_more: boolean;
      next_cursor: string | null;
    }>(`/api/tenants/${tenant}/analytics/query/contributors`, {
      method: "POST",
      body: JSON.stringify({ definition, group, measure, ...(cursor ? { cursor } : {}) }),
    }),
  export: (tenant: string, definition: AnalyticsDefinition) =>
    request<{ csv: string; filename: string; row_count: number }>(
      `/api/tenants/${tenant}/analytics/export`,
      { method: "POST", body: JSON.stringify({ definition }) },
    ),
  reports: (tenant: string, query = "", cursor?: string) =>
    request<{ records: AnalyticsReport[]; has_more: boolean; next_cursor: string | null }>(
      `/api/tenants/${tenant}/analytics/reports?${new URLSearchParams({ query, ...(cursor ? { cursor } : {}) })}`,
    ),
  report: (tenant: string, id: string) =>
    request<AnalyticsReport>(`/api/tenants/${tenant}/analytics/reports/${encodeURIComponent(id)}`),
  change: (
    tenant: string,
    body: {
      operation: string;
      request_id: string;
      report_id?: string;
      expected_revision?: number;
      name?: string;
      definition?: AnalyticsDefinition;
    },
  ) =>
    request<AnalyticsReport>(`/api/tenants/${tenant}/analytics/reports/changes`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
