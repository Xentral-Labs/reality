export type Destination =
  | "inspector"
  | "facts"
  | "orders-deliveries"
  | "settings"
  | "data-sources"
  | "demo-data"
  | "finance"
  | "home"
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
  storylineChapter?: string;
  inspectorView?: string;
  inspectorRecordKind?: string;
  tableSize: 25 | 50 | 100;
  tableSort: string;
  tableDirection: "asc" | "desc";
  tableScope: string;
  factSubjectType: string;
  factSubject: string;
  factSource: string;
  factTarget: "fact" | "source_record";
  ordersView: "commitments" | "deliveries" | "shipments" | "customer-orders" | "supplier-orders";
  deliveryType: "customer_delivery" | "supplier_delivery";
  deliveryStatus: "open" | "all";
  order: string;
  settingsView: "personal" | "company" | "access" | "ai" | "agents" | "usage";
  tenant: string;
  commitment: string;
  proposal: string;
  importProposal: string;
  session: string;
  q: string;
  page: number;
  analyticsView?: "overview" | "explore" | "reports";
  days: 7 | 30 | 90;
  metric:
    | "open"
    | "fully_reserved"
    | "needs_reservation"
    | "overdue"
    | "unknown_due"
    | "created"
    | "shipped";
  day: string;
  family: "customer" | "supplier" | "item" | "location";
  record: string;
  active: boolean;
  dataView: "systems" | "records" | "documents";
  sourceSystem: string;
  sourceRecord: string;
  evidenceType: string;
  financeSettings: "accounts" | "cost-centers" | "classifications" | "source-mappings";
  financeView: "open-items" | "payments" | "journal" | "balances" | "settings";
  balanceSide: "customer" | "supplier";
  creditOnly: boolean;
  partyId: string;
  flow: "receivable" | "payable" | "customer-credit" | "customer-balance" | "supplier-balance";
  financeStatus: string;
  direction: string;
  account: string;
  warehouseView: "stock" | "reservations" | "movements";
  item: string;
  entry: string;
  state: string;
  severity: string;
  exception: string;
};
const routes = [
  "/app",
  "/app/",
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
  const candidate = path === "free-play" ? "chat" : path;
  const page = Number(url.searchParams.get("page") || 1);
  return {
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
    ].includes(url.searchParams.get("inspector_view") || "")
      ? url.searchParams.get("inspector_view")!
      : "overview",
    inspectorRecordKind: url.searchParams.get("inspector_record_kind") || undefined,
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
    ].includes(url.searchParams.get("orders_view") || "")
      ? (url.searchParams.get("orders_view") as Selection["ordersView"])
      : "deliveries",
    deliveryType:
      url.searchParams.get("delivery_type") === "supplier_delivery"
        ? "supplier_delivery"
        : "customer_delivery",
    deliveryStatus: url.searchParams.get("delivery_status") === "all" ? "all" : "open",
    order: url.searchParams.get("order") || "",
    settingsView: ["personal", "company", "access", "ai", "agents", "usage"].includes(
      url.searchParams.get("settings_view") || "",
    )
      ? (url.searchParams.get("settings_view") as Selection["settingsView"])
      : "company",
    route: [
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
    financeView: ["open-items", "payments", "journal", "balances", "settings"].includes(
      url.searchParams.get("finance_view") || "",
    )
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
    ].includes(url.searchParams.get("state") || "")
      ? url.searchParams.get("state")!
      : "",
    severity: ["critical", "high", "normal", "low"].includes(url.searchParams.get("severity") || "")
      ? url.searchParams.get("severity")!
      : "",
    exception: url.searchParams.get("exception") || "",
    days: [7, 30, 90].includes(Number(url.searchParams.get("days")))
      ? (Number(url.searchParams.get("days")) as Selection["days"])
      : 30,
    analyticsView: ["explore", "reports"].includes(url.searchParams.get("analytics_view") || "")
      ? (url.searchParams.get("analytics_view") as Selection["analyticsView"])
      : "overview",
    metric: [
      "open",
      "fully_reserved",
      "needs_reservation",
      "overdue",
      "unknown_due",
      "created",
      "shipped",
    ].includes(url.searchParams.get("metric") || "")
      ? (url.searchParams.get("metric") as Selection["metric"])
      : "open",
    day: /^\d{4}-\d{2}-\d{2}$/.test(url.searchParams.get("day") || "")
      ? url.searchParams.get("day")!
      : "",
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
  const query = new URLSearchParams();
  if (selection.route === "inspector")
    query.set("inspector_view", selection.inspectorView || "overview");
  for (const key of ["tenant", "commitment", "proposal", "session", "q"] as const)
    if (selection[key]) query.set(key, selection[key]);
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
    if (selection.ordersView === "deliveries" || selection.ordersView === "commitments") {
      query.set("delivery_type", selection.deliveryType);
      query.set("delivery_status", selection.deliveryStatus);
      if (selection.order) query.set("order", selection.order);
    }
    if (selection.entry) query.set("entry", selection.entry);
  }
  if (selection.route === "inspector" && selection.inspectorRecordKind)
    query.set("inspector_record_kind", selection.inspectorRecordKind);
  if (selection.route === "facts" || selection.route === "inspector") {
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
  if (selection.route === "analytics") {
    if (selection.analyticsView && selection.analyticsView !== "overview")
      query.set("analytics_view", selection.analyticsView);
    query.set("days", String(selection.days));
    query.set("metric", selection.metric);
    if (selection.day) query.set("day", selection.day);
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
    for (const key of ["item", "entry", "state"] as const)
      if (selection[key]) query.set(key, selection[key]);
  }
  if (selection.route === "attention") {
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
    tableSort: "",
    tableScope: "",
    tableDirection: "asc",
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
    day: "",
    metric: "open",
    analyticsView: "overview",
    active: false,
    sourceSystem: "",
    sourceRecord: "",
    evidenceType: "",
    flow: "receivable",
    balanceSide: "customer",
    creditOnly: false,
    partyId: "",
    financeStatus: "outstanding",
    direction: "",
    account: "",
    item: "",
    entry: "",
    state: "",
    severity: "",
    exception: "",
    storylineChapter: "",
  };
}
