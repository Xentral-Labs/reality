export type Destination =
  | "inspector"
  | "facts"
  | "orders-deliveries"
  | "settings"
  | "data-sources"
  | "demo-data"
  | "finance"
  | "home"
  | "cockpit"
  | "copilot"
  | "work"
  | "decisions"
  | "analytics"
  | "master-data"
  | "warehouse"
  | "attention"
  | "storyline"
  | "chat";
export type Selection = {
  route: Destination;
  cockpitDay?: string;
  cockpitLocation?: string;
  cockpitMeasure?: CockpitMeasure;
  cockpitCase?: string;
  cockpitBasis?: string;
  cockpitMinutes?: 5 | 15 | 60;
  cockpitOrigin?: CockpitOrigin;
  storylineChapter?: string;
  inspectorView?: string;
  /** The engine room's filter, as its `live_*` URL parameters (spec 266). */
  liveFilter?: string;
  attentionView?: "findings" | "rules";
  inspectorRecordKind?: string;
  inspectorTargetKind?: string;
  inspectorTargetId?: string;
  tableSize: 25 | 50 | 100;
  tableSort: string;
  tableDirection: "asc" | "desc";
  tableScope: string;
  factSubjectType: string;
  factSubject: string;
  factSource: string;
  factTarget: "fact" | "source_record";
  ordersView:
    | "commitments"
    | "deliveries"
    | "shipments"
    | "customer-orders"
    | "supplier-orders"
    | "readiness";
  deliveryType: "customer_delivery" | "supplier_delivery";
  deliveryStatus: "open" | "all";
  order: string;
  settingsView: "personal" | "company" | "current" | "new" | "access" | "ai" | "agents" | "usage";
  decisionsView?: "pending" | "history";
  tenant: string;
  commitment: string;
  proposal: string;
  importProposal: string;
  session: string;
  q: string;
  page: number;
  analyticsProposal?: string;
  analyticsReport?: string;
  analyticsTemplate?: string;
  calculatedReport?: string;
  toolCapability?: string;
  analyticsView?: "templates" | "graph" | "reports" | "explore";
  family: "customer" | "supplier" | "item" | "location";
  record: string;
  active: boolean;
  dataView: "systems" | "records" | "documents";
  sourceSystem: string;
  sourceRecord: string;
  evidenceType: string;
  financeSettings: "accounts" | "cost-centers" | "classifications" | "source-mappings";
  financeView: "open-items" | "payments" | "journal" | "balances" | "month-end" | "settings";
  balanceSide: "customer" | "supplier";
  creditOnly: boolean;
  partyId: string;
  flow: "receivable" | "payable" | "customer-credit" | "customer-balance" | "supplier-balance";
  financeStatus: string;
  financeOverdue?: boolean;
  direction: string;
  account: string;
  warehouseView: "stock" | "reservations" | "movements";
  item: string;
  location: string;
  entry: string;
  state: string;
  severity: string;
  exception: string;
};
const routes = [
  "/app",
  "/app/",
  "/app/cockpit",
  "/app/facts",
  "/app/inspector",
  "/app/settings",
  "/app/orders-deliveries",
  "/app/copilot",
  "/app/work",
  "/app/decisions",
  "/app/analytics",
  "/app/master-data",
  "/app/data-sources",
  "/app/demo-data",
  "/app/finance",
  "/app/warehouse",
  "/app/attention",
  "/app/storyline",
  "/app/free-play",
  "/app/chat",
];
export function unifiedPath(path: string) {
  return routes.includes(path);
}
export function readSelection(url: URL): Selection {
  const path = url.pathname.split("/")[2] || "home";
  const legacyExceptionRules =
    path === "inspector" && url.searchParams.get("inspector_view") === "exceptions";
  const candidate = legacyExceptionRules ? "attention" : path === "free-play" ? "chat" : path;
  const page = Number(url.searchParams.get("page") || 1);
  return {
    cockpitDay: cockpitDay(url.searchParams.get("cockpit_day")),
    cockpitLocation: url.searchParams.get("cockpit_location") || "",
    cockpitMeasure: cockpitMeasure(url.searchParams.get("cockpit_measure")),
    cockpitCase: url.searchParams.get("cockpit_case") || "",
    cockpitBasis: url.searchParams.get("cockpit_basis") || "",
    cockpitMinutes: cockpitMinutes(url.searchParams.get("cockpit_minutes")),
    cockpitOrigin: readCockpitOrigin(
      url.searchParams.get("cockpit_origin"),
      url.searchParams.get("tenant") || "",
    ),
    attentionView:
      legacyExceptionRules || url.searchParams.get("attention_view") === "rules"
        ? "rules"
        : "findings",
    inspectorView: [
      "overview",
      "facts",
      "records",
      "graph",
      "rules",
      "exceptions",
      "commands",
      "views",
      "history",
      "live",
      "business",
    ].includes(url.searchParams.get("inspector_view") || "")
      ? url.searchParams.get("inspector_view")!
      : "overview",
    liveFilter: new URLSearchParams(
      [...url.searchParams].filter(([key]) => key.startsWith("live_")),
    ).toString(),
    inspectorRecordKind: url.searchParams.get("inspector_record_kind") || undefined,
    inspectorTargetKind: url.searchParams.get("inspector_target_kind") || "",
    inspectorTargetId: url.searchParams.get("inspector_target_id") || "",
    factSubjectType: url.searchParams.get("fact_subject_type") || "",
    factSubject: url.searchParams.get("fact_subject") || "",
    factSource: url.searchParams.get("fact_source") || "",
    factTarget: url.searchParams.get("fact_target") === "source_record" ? "source_record" : "fact",
    tableSize: [25, 50, 100].includes(Number(url.searchParams.get("size")))
      ? (Number(url.searchParams.get("size")) as 25 | 50 | 100)
      : 50,
    tableSort: url.searchParams.get("sort") || "",
    tableDirection: url.searchParams.get("sort_direction") === "desc" ? "desc" : "asc",
    tableScope: url.searchParams.get("table") || "",
    ordersView: [
      "commitments",
      "deliveries",
      "shipments",
      "customer-orders",
      "supplier-orders",
      "readiness",
    ].includes(url.searchParams.get("orders_view") || "")
      ? (url.searchParams.get("orders_view") as Selection["ordersView"])
      : "deliveries",
    deliveryType:
      url.searchParams.get("delivery_type") === "supplier_delivery"
        ? "supplier_delivery"
        : "customer_delivery",
    deliveryStatus: url.searchParams.get("delivery_status") === "all" ? "all" : "open",
    order: url.searchParams.get("order") || "",
    decisionsView: url.searchParams.get("decisions_view") === "history" ? "history" : "pending",
    settingsView: [
      "personal",
      "company",
      "current",
      "new",
      "access",
      "ai",
      "agents",
      "usage",
    ].includes(url.searchParams.get("settings_view") || "")
      ? (url.searchParams.get("settings_view") as Selection["settingsView"])
      : "company",
    route: [
      "cockpit",
      "facts",
      "inspector",
      "settings",
      "orders-deliveries",
      "copilot",
      "work",
      "decisions",
      "analytics",
      "master-data",
      "data-sources",
      "demo-data",
      "finance",
      "warehouse",
      "attention",
      "storyline",
      "chat",
    ].includes(candidate)
      ? (candidate as Destination)
      : "home",
    storylineChapter: /^[a-z0-9][a-z0-9-]{1,78}$/.test(url.searchParams.get("chapter") || "")
      ? url.searchParams.get("chapter")!
      : "",
    dataView: ["systems", "records", "documents"].includes(url.searchParams.get("data_view") || "")
      ? (url.searchParams.get("data_view") as Selection["dataView"])
      : "systems",
    sourceSystem: url.searchParams.get("source_system") || "",
    sourceRecord: url.searchParams.get("source_record") || "",
    evidenceType: url.searchParams.get("evidence_type") || "",
    financeSettings: ["accounts", "cost-centers", "classifications", "source-mappings"].includes(
      url.searchParams.get("finance_settings") || "",
    )
      ? (url.searchParams.get("finance_settings") as Selection["financeSettings"])
      : "accounts",
    financeView: [
      "open-items",
      "payments",
      "journal",
      "balances",
      "month-end",
      "settings",
    ].includes(url.searchParams.get("finance_view") || "")
      ? (url.searchParams.get("finance_view") as Selection["financeView"])
      : "open-items",
    flow: ["customer-credit", "customer-balance", "supplier-balance"].includes(
      url.searchParams.get("flow") || "",
    )
      ? (url.searchParams.get("flow") as Selection["flow"])
      : url.searchParams.get("flow") === "payable"
        ? "payable"
        : "receivable",
    balanceSide: url.searchParams.get("balance_side") === "supplier" ? "supplier" : "customer",
    creditOnly: url.searchParams.get("credit_only") === "1",
    partyId: url.searchParams.get("party_id") || "",
    financeOverdue: url.searchParams.get("finance_overdue") === "1",
    financeStatus: ["", "outstanding", "open", "partial", "paid"].includes(
      url.searchParams.get("finance_status") ?? "outstanding",
    )
      ? (url.searchParams.get("finance_status") ?? "outstanding")
      : "outstanding",
    direction: ["incoming", "outgoing"].includes(url.searchParams.get("direction") || "")
      ? url.searchParams.get("direction")!
      : "",
    account: url.searchParams.get("account") || "",
    warehouseView: ["stock", "reservations", "movements"].includes(
      url.searchParams.get("warehouse_view") || "",
    )
      ? (url.searchParams.get("warehouse_view") as Selection["warehouseView"])
      : "stock",
    item: url.searchParams.get("item") || "",
    location: url.searchParams.get("location") || "",
    entry: url.searchParams.get("entry") || "",
    state: [
      "available",
      "fully_allocated",
      "shortage",
      "active",
      "released",
      "consumed",
      "receipt",
      "shipment",
      "transfer",
      "correction",
      "return",
      "supplier_return",
      "adjustment",
      "assembly_input",
      "assembly_output",
    ].includes(url.searchParams.get("state") || "")
      ? url.searchParams.get("state")!
      : "",
    severity: ["critical", "high", "normal", "low"].includes(url.searchParams.get("severity") || "")
      ? url.searchParams.get("severity")!
      : "",
    exception: url.searchParams.get("exception") || "",
    // Preserve explicit graph/template links; the workspace entry opens saved reports.
    analyticsProposal:
      !url.searchParams.get("analytics_report") && !url.searchParams.get("analytics_template")
        ? url.searchParams.get("analysis_proposal") || ""
        : "",
    analyticsReport: url.searchParams.get("analytics_report") || "",
    analyticsTemplate: !url.searchParams.get("analytics_report")
      ? url.searchParams.get("analytics_template") || ""
      : "",
    calculatedReport: url.searchParams.get("calculated_report") || "",
    toolCapability: url.searchParams.get("tool_capability") || "",
    analyticsView: ["templates", "graph", "reports", "explore"].includes(
      url.searchParams.get("analytics_view") || "",
    )
      ? (url.searchParams.get("analytics_view") as Selection["analyticsView"])
      : url.searchParams.get("analytics_view")
        ? "graph"
        : "reports",
    family: ["customer", "supplier", "item", "location"].includes(
      url.searchParams.get("family") || "",
    )
      ? (url.searchParams.get("family") as Selection["family"])
      : "customer",
    record: url.searchParams.get("record") || "",
    active: url.searchParams.get("active") === "all",
    tenant: url.searchParams.get("tenant") || "",
    commitment: url.searchParams.get("commitment") || "",
    proposal: url.searchParams.get("proposal") || "",
    importProposal: url.searchParams.get("import_proposal") || "",
    session: url.searchParams.get("session") || "",
    q: url.searchParams.get("q") || "",
    page: Number.isSafeInteger(page) && page > 0 ? page : 1,
  };
}
export function selectionUrl(selection: Selection): string {
  selection = normalizeInspectorSelection(selection);
  const query = new URLSearchParams();
  if (selection.route === "cockpit") {
    query.set("cockpit_day", cockpitDay(selection.cockpitDay));
    query.set("cockpit_measure", cockpitMeasure(selection.cockpitMeasure));
    query.set("cockpit_minutes", String(cockpitMinutes(selection.cockpitMinutes)));
    if (selection.cockpitLocation) query.set("cockpit_location", selection.cockpitLocation);
    if (selection.cockpitCase) query.set("cockpit_case", selection.cockpitCase);
    if (selection.cockpitBasis) query.set("cockpit_basis", selection.cockpitBasis);
  }
  const origin = readCockpitOrigin(
    JSON.stringify(selection.cockpitOrigin) ?? null,
    selection.tenant,
  );
  if (origin) query.set("cockpit_origin", JSON.stringify(origin));
  if (selection.route === "inspector")
    query.set("inspector_view", selection.inspectorView || "overview");
  for (const key of ["tenant", "commitment", "proposal", "session", "q"] as const)
    if (selection[key]) query.set(key, selection[key]);
  if (selection.route === "analytics") {
    if (selection.analyticsReport) query.set("analytics_report", selection.analyticsReport);
    if (!selection.analyticsReport && selection.analyticsTemplate)
      query.set("analytics_template", selection.analyticsTemplate);
  }
  if (selection.route === "inspector" && selection.inspectorView === "live" && selection.liveFilter)
    for (const [key, value] of new URLSearchParams(selection.liveFilter))
      if (key.startsWith("live_")) query.set(key, value);
  if (selection.route === "inspector") {
    if (selection.calculatedReport) query.set("calculated_report", selection.calculatedReport);
    if (selection.toolCapability) query.set("tool_capability", selection.toolCapability);
  }
  if (selection.tableSize !== 50) query.set("size", String(selection.tableSize));
  if (selection.tableScope) {
    query.set("table", selection.tableScope);
    query.set("size", String(selection.tableSize));
    if (selection.tableSort) {
      query.set("sort", selection.tableSort);
      query.set("sort_direction", selection.tableDirection);
    }
  }
  if (selection.route === "orders-deliveries") {
    query.set("orders_view", selection.ordersView);
    if (
      selection.ordersView === "deliveries" ||
      selection.ordersView === "commitments" ||
      selection.ordersView === "shipments"
    ) {
      query.set("delivery_type", selection.deliveryType);
      query.set("delivery_status", selection.deliveryStatus);
      if (selection.order) query.set("order", selection.order);
    }
    if (selection.entry) query.set("entry", selection.entry);
  }
  if (selection.route === "inspector" && selection.inspectorRecordKind)
    query.set("inspector_record_kind", selection.inspectorRecordKind);
  if (selection.route === "facts" || selection.route === "inspector") {
    if (selection.inspectorTargetKind && selection.inspectorTargetId) {
      query.set("inspector_target_kind", selection.inspectorTargetKind);
      query.set("inspector_target_id", selection.inspectorTargetId);
    }
    if (selection.factSubjectType) query.set("fact_subject_type", selection.factSubjectType);
    if (selection.factSubject) query.set("fact_subject", selection.factSubject);
    if (selection.factSource) query.set("fact_source", selection.factSource);
    if (selection.entry) {
      query.set("entry", selection.entry);
      query.set("fact_target", selection.factTarget);
    }
  }
  if (selection.route === "data-sources" && selection.importProposal)
    query.set("import_proposal", selection.importProposal);
  if (selection.route === "settings") query.set("settings_view", selection.settingsView);
  if (selection.route === "decisions" && selection.decisionsView === "history")
    query.set("decisions_view", "history");
  if (selection.route === "analytics") {
    if (!selection.analyticsReport && !selection.analyticsTemplate && selection.analyticsProposal)
      query.set("analysis_proposal", selection.analyticsProposal);
    if (selection.analyticsView === "graph") query.set("analytics_view", "graph");
    if (selection.analyticsView === "explore") query.set("analytics_view", "explore");
    if (selection.analyticsView === "reports") query.set("analytics_view", "reports");
    if (selection.analyticsView === "templates") query.set("analytics_view", "templates");
  }
  if (selection.route === "master-data") {
    query.set("family", selection.family);
    if (selection.record) query.set("record", selection.record);
    if (selection.active) query.set("active", "all");
  }
  if (selection.route === "data-sources") {
    query.set("data_view", selection.dataView);
    if (selection.sourceSystem) query.set("source_system", selection.sourceSystem);
    if (selection.sourceRecord) query.set("source_record", selection.sourceRecord);
    if (selection.evidenceType) query.set("evidence_type", selection.evidenceType);
    if (selection.entry) query.set("entry", selection.entry);
  }
  if (selection.route === "finance") {
    query.set("finance_view", selection.financeView);
    if (selection.financeView === "settings")
      query.set("finance_settings", selection.financeSettings);
    query.set("flow", selection.flow);
    query.set("finance_status", selection.financeStatus);
    if (selection.financeOverdue) query.set("finance_overdue", "1");
    if (selection.financeView === "balances") {
      query.set("balance_side", selection.balanceSide);
      if (selection.creditOnly) query.set("credit_only", "1");
    }
    if (selection.partyId) query.set("party_id", selection.partyId);
    for (const key of ["direction", "account", "entry"] as const)
      if (selection[key]) query.set(key, selection[key]);
  }
  if (selection.route === "warehouse") {
    query.set("warehouse_view", selection.warehouseView);
    for (const key of ["item", "location", "entry", "state"] as const)
      if (selection[key]) query.set(key, selection[key]);
  }
  if (selection.route === "attention") {
    if (selection.attentionView === "rules") query.set("attention_view", "rules");
    if (selection.exception) query.set("exception", selection.exception);
    if (selection.severity) query.set("severity", selection.severity);
  }
  if (selection.route === "storyline" && selection.storylineChapter)
    query.set("chapter", selection.storylineChapter);
  if (selection.page > 1) query.set("page", String(selection.page));
  return `/app${selection.route === "home" ? "" : `/${selection.route}`}${query.size ? `?${query}` : ""}`;
}
export function companySelection(selection: Selection, tenant: string): Selection {
  return {
    ...selection,
    tenant,
    cockpitDay: "today",
    cockpitLocation: "",
    cockpitMeasure: "due",
    cockpitCase: "",
    cockpitBasis: "",
    cockpitOrigin: undefined,
    tableSort: "",
    tableScope: "",
    tableDirection: "asc",
    inspectorTargetKind: "",
    inspectorTargetId: "",
    liveFilter: "",
    factSubjectType: "",
    factSubject: "",
    factSource: "",
    factTarget: "fact",
    commitment: "",
    order: "",
    proposal: "",
    importProposal: "",
    session: "",
    q: "",
    page: 1,
    record: "",
    analyticsView: "reports",
    analyticsProposal: "",
    analyticsReport: "",
    analyticsTemplate: "",
    calculatedReport: "",
    toolCapability: "",
    active: false,
    sourceSystem: "",
    sourceRecord: "",
    evidenceType: "",
    flow: "receivable",
    balanceSide: "customer",
    creditOnly: false,
    partyId: "",
    financeStatus: "outstanding",
    financeOverdue: false,
    direction: "",
    account: "",
    item: "",
    location: "",
    entry: "",
    state: "",
    severity: "",
    exception: "",
    storylineChapter: "",
  };
}

export function navigationSelection(selection: Selection, changes: Partial<Selection>): Selection {
  const base =
    changes.tenant && changes.tenant !== selection.tenant
      ? companySelection(selection, changes.tenant)
      : selection;
  const next = { ...base, ...changes };
  if (next.tenant !== selection.tenant) {
    next.cockpitDay = "today";
    next.cockpitLocation = "";
    next.cockpitMeasure = "due";
    next.cockpitCase = "";
    next.cockpitBasis = "";
    next.cockpitOrigin = undefined;
  }
  next.cockpitOrigin = readCockpitOrigin(JSON.stringify(next.cockpitOrigin) ?? null, next.tenant);
  // Links to findings must leave the rule catalog, including links from rule previews.
  if (changes.route === "attention" && changes.attentionView === undefined)
    next.attentionView = "findings";
  return normalizeInspectorSelection(next);
}

function normalizeInspectorSelection(selection: Selection): Selection {
  return selection.route === "inspector" && selection.inspectorView === "exceptions"
    ? { ...selection, route: "attention", attentionView: "rules" }
    : selection;
}

export type CockpitMeasure = "due" | "plan" | "handover" | "risk" | "forecast" | "unplanned";
export type CockpitOrigin = {
  tenant: string;
  day: string;
  location: string;
  measure: CockpitMeasure;
  case: string;
  basis: string;
  minutes: 5 | 15 | 60;
};
const cockpitMeasures = ["due", "plan", "handover", "risk", "forecast", "unplanned"];

function cockpitDay(value: unknown): string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return "today";
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value
    ? value
    : "today";
}
function cockpitMeasure(value: unknown): CockpitMeasure {
  return typeof value === "string" && cockpitMeasures.includes(value)
    ? (value as CockpitMeasure)
    : "due";
}
function cockpitMinutes(value: unknown): 5 | 15 | 60 {
  return value === 5 || value === "5" ? 5 : value === 60 || value === "60" ? 60 : 15;
}
function readCockpitOrigin(raw: string | null, tenant: string): CockpitOrigin | undefined {
  if (!raw || raw.length > 4096 || !tenant) return undefined;
  try {
    const origin = JSON.parse(raw);
    const keys = ["tenant", "day", "location", "measure", "case", "basis", "minutes"];
    if (
      !origin ||
      typeof origin !== "object" ||
      Array.isArray(origin) ||
      Object.keys(origin).length !== keys.length ||
      Object.keys(origin).some((key) => !keys.includes(key)) ||
      keys.filter((key) => key !== "minutes").some((key) => typeof origin[key] !== "string") ||
      origin.tenant !== tenant ||
      (origin.day !== "today" && cockpitDay(origin.day) !== origin.day) ||
      !cockpitMeasures.includes(origin.measure) ||
      ![5, 15, 60].includes(origin.minutes)
    )
      return undefined;
    return origin as CockpitOrigin;
  } catch {
    return undefined;
  }
}
export function cockpitOriginSelection(selection: Selection): CockpitOrigin | undefined {
  if (selection.route !== "cockpit" || !selection.tenant) return undefined;
  return {
    tenant: selection.tenant,
    day: cockpitDay(selection.cockpitDay),
    location: selection.cockpitLocation || "",
    measure: cockpitMeasure(selection.cockpitMeasure),
    case: selection.cockpitCase || "",
    basis: selection.cockpitBasis || "",
    minutes: cockpitMinutes(selection.cockpitMinutes),
  };
}
export function cockpitReturnSelection(selection: Selection): Selection | null {
  const origin = readCockpitOrigin(
    JSON.stringify(selection.cockpitOrigin) ?? null,
    selection.tenant,
  );
  return origin
    ? {
        ...companySelection(selection, selection.tenant),
        route: "cockpit",
        cockpitDay: origin.day,
        cockpitLocation: origin.location,
        cockpitMeasure: origin.measure,
        cockpitCase: origin.case,
        cockpitBasis: origin.basis,
        cockpitMinutes: origin.minutes,
      }
    : null;
}
