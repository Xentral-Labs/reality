import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { test } from "node:test";
import ts from "typescript";

const source = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const routeSource = source("../src/unified/routing.ts");
const compiled = ts.transpile(routeSource, { module: ts.ModuleKind.ES2022 });
const { unifiedPath, readSelection, selectionUrl } = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
);

test("current routes are bounded; compatibility is resolved at the entry", () => {
  for (const path of ["/app", "/app/", "/app/copilot", "/app/work", "/app/decisions"])
    assert.equal(unifiedPath(path), true);
  for (const path of ["/playground", "/app/companies", "/app/orders", "/app/work/foreign"])
    assert.equal(unifiedPath(path), false);
});

test("selection round-trips opaque IDs and does not propagate arbitrary query data", () => {
  const selection = readSelection(
    new URL(
      "https://example.test/app/work?tenant=t%26x&commitment=c%2Fx&token=secret&page=2&q=Lamp",
    ),
  );
  const url = new URL(selectionUrl(selection), "https://example.test");
  assert.equal(url.searchParams.get("tenant"), "t&x");
  assert.equal(url.searchParams.get("commitment"), "c/x");
  assert.equal(url.searchParams.has("token"), false);
  assert.equal(url.searchParams.get("page"), "2");
  assert.equal(url.searchParams.get("q"), "Lamp");
});

test("authenticated dispatcher loads only the unified app", () => {
  const app = source("../src/App.tsx");
  assert.match(app, /AuthGate/);
  assert.doesNotMatch(app, /VITE_UNIFIED_APP|LegacyProductApp|PracticeEntry/);
  assert.match(app, /lazy\(/);
  assert.doesNotMatch(source("../src/main.tsx"), /import "\.\/(styles|chat)\.css"/);
});

test("unified shell uses the canonical Reality wordmark", () => {
  const shell = source("../src/unified/Shell.tsx");
  assert.match(shell, /shell-brand-home[^>]*aria-label="Reality"/s);
  const switcher = source("../src/unified/CompanySwitcher.tsx");
  assert.match(switcher, />\s*Reality\s*<\/span>/);
  assert.doesNotMatch(shell + switcher, />\s*reality\s*<\/span>/);
});

test("workspace routes and bounded filters survive reload without leaking company selection", async () => {
  const { companySelection } = await import(
    `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
  );
  for (const path of ["/app/analytics", "/app/master-data"]) assert.equal(unifiedPath(path), true);
  const selection = readSelection(
    new URL(
      "https://example.test/app/master-data?tenant=one&family=item&record=it1&days=90&metric=shipped&day=2026-09-07&active=all",
    ),
  );
  assert.equal(selection.family, "item");
  assert.equal(
    readSelection(new URL(selectionUrl(selection), "https://example.test")).record,
    "it1",
  );
  assert.equal(companySelection(selection, "two").record, "");
  const bad = readSelection(
    new URL("https://example.test/app/analytics?days=999&family=secret&metric=revenue&day=bad"),
  );
  assert.equal(bad.family, "customer");
});

test("warehouse and attention selections preserve exact references and clear on company switch", async () => {
  const { companySelection } = await import(
    `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
  );
  assert.equal(unifiedPath("/app/warehouse"), true);
  assert.equal(unifiedPath("/app/attention"), true);
  assert.equal(unifiedPath("/app/exceptions"), false);
  const value = readSelection(
    new URL(
      "https://example.test/app/warehouse?tenant=one&warehouse_view=movements&item=it1&entry=mv1&state=shipment",
    ),
  );
  const round = readSelection(new URL(selectionUrl(value), "https://example.test"));
  assert.equal(round.item, "it1");
  assert.equal(round.entry, "mv1");
  assert.equal(round.warehouseView, "movements");
  assert.equal(companySelection(value, "two").item, "");
  assert.equal(companySelection(value, "two").entry, "");
  const attention = readSelection(
    new URL("https://example.test/app/attention?exception=exc1&severity=high"),
  );
  assert.equal(
    readSelection(new URL(selectionUrl(attention), "https://example.test")).exception,
    "exc1",
  );
  assert.equal(companySelection(attention, "two").exception, "");
});

test("finance deep links preserve filters and inspection while company changes clear context", async () => {
  const { companySelection } = await import(
    `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
  );
  assert.equal(unifiedPath("/app/finance"), true);
  assert.equal(unifiedPath("/app/open-items"), false);
  const value = readSelection(
    new URL(
      "https://example.test/app/finance?tenant=one&finance_view=journal&account=cash&entry=le%2F1&q=source&page=3&flow=payable&finance_status=partial&direction=outgoing",
    ),
  );
  const round = readSelection(new URL(selectionUrl(value), "https://example.test"));
  for (const key of [
    "financeView",
    "account",
    "entry",
    "q",
    "page",
    "flow",
    "financeStatus",
    "direction",
  ])
    assert.equal(round[key], value[key]);
  assert.equal(round.financeView, "journal");
  assert.equal(companySelection(value, "two").account, "");
  assert.equal(companySelection(value, "two").entry, "");
  assert.equal(companySelection(value, "two").flow, "receivable");
  const bad = readSelection(
    new URL(
      "https://example.test/app/finance?finance_view=secret&flow=all&finance_status=bad&direction=sideways",
    ),
  );
  assert.equal(bad.financeView, "open-items");
  assert.equal(bad.flow, "receivable");
  assert.equal(bad.financeStatus, "outstanding");
  assert.equal(bad.direction, "");
});

test("source exploration retains exact versions and clears company context", async () => {
  const { companySelection } = await import(
    `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
  );
  assert.equal(unifiedPath("/app/data-sources"), true);
  assert.equal(unifiedPath("/app/integrations"), false);
  const value = readSelection(
    new URL(
      "https://example.test/app/data-sources?tenant=one&data_view=documents&source_system=shop&source_record=src%2F2&evidence_type=sales_order&entry=doc1&page=2&q=REF",
    ),
  );
  const round = readSelection(new URL(selectionUrl(value), "https://example.test"));
  assert.equal(round.dataView, "documents");
  for (const key of ["sourceSystem", "sourceRecord", "evidenceType", "entry", "q", "page"])
    assert.equal(round[key], value[key]);
  for (const key of ["sourceSystem", "sourceRecord", "evidenceType", "entry"])
    assert.equal(companySelection(value, "two")[key], "");
  assert.equal(
    readSelection(new URL("https://example.test/app/data-sources?data_view=payload_dump")).dataView,
    "systems",
  );
});

test("settings section round-trips and unknown sections fall back safely", () => {
  assert.equal(unifiedPath("/app/settings"), true);
  const company = readSelection(
    new URL("https://example.test/app/settings?tenant=one&settings_view=company"),
  );
  assert.equal(
    readSelection(new URL(selectionUrl(company), "https://example.test")).settingsView,
    "company",
  );
  const agents = readSelection(
    new URL("https://example.test/app/settings?tenant=one&settings_view=agents"),
  );
  assert.equal(agents.settingsView, "agents");
  assert.equal(
    readSelection(new URL(selectionUrl(agents), "https://example.test")).settingsView,
    "agents",
  );
  const selected = readSelection(
    new URL("https://example.test/app/settings?tenant=one&settings_view=ai"),
  );
  assert.equal(selected.settingsView, "ai");
  assert.equal(
    readSelection(new URL(selectionUrl(selected), "https://example.test")).settingsView,
    "ai",
  );
  assert.equal(
    readSelection(new URL("https://example.test/app/settings?settings_view=secret")).settingsView,
    "company",
  );
});

test("orders workspace keeps typed filters and exact order scope without changing legacy routes", async () => {
  const { companySelection } = await import(
    `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
  );
  assert.equal(unifiedPath("/app/orders-deliveries"), true);
  assert.equal(unifiedPath("/app/orders"), false);
  const selection = readSelection(
    new URL(
      "https://example.test/app/orders-deliveries?tenant=one&orders_view=deliveries&delivery_type=supplier_delivery&delivery_status=all&order=d%2Fx&entry=c1",
    ),
  );
  const round = readSelection(new URL(selectionUrl(selection), "https://example.test"));
  assert.equal(round.order, "d/x");
  assert.equal(round.deliveryType, "supplier_delivery");
  assert.equal(round.deliveryStatus, "all");
  assert.equal(companySelection(selection, "two").order, "");
  assert.equal(companySelection(selection, "two").entry, "");
  const invalid = readSelection(
    new URL(
      "https://example.test/app/orders-deliveries?orders_view=secret&delivery_type=invoice&delivery_status=fake",
    ),
  );
  assert.equal(invalid.ordersView, "deliveries");
  assert.equal(invalid.deliveryType, "customer_delivery");
  assert.equal(invalid.deliveryStatus, "open");
});

test("Facts normalizes inspection and clears exact subject/source scope between companies", async () => {
  const { companySelection } = await import(
    `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
  );
  assert.equal(unifiedPath("/app/facts"), true);
  const selected = readSelection(
    new URL(
      "https://example.test/app/facts?tenant=one&fact_subject_type=commitment&fact_subject=c%2F1&fact_source=s%2F1&entry=f1&fact_target=source_record",
    ),
  );
  const round = readSelection(new URL(selectionUrl(selected), "https://example.test"));
  assert.equal(round.factSubject, "c/1");
  assert.equal(round.factSource, "s/1");
  assert.equal(round.factTarget, "source_record");
  const reset = companySelection(selected, "two");
  assert.equal(reset.factSubject, "");
  assert.equal(reset.factSource, "");
  assert.equal(reset.factSubjectType, "");
  assert.equal(reset.entry, "");
  assert.equal(
    readSelection(new URL("https://example.test/app/facts?fact_target=secret")).factTarget,
    "fact",
  );
});

test("Inspector tabs and embedded fact filters survive reload without arbitrary view names", () => {
  assert.equal(unifiedPath("/app/inspector"), true);
  const selection = readSelection(
    new URL(
      "https://example.test/app/inspector?tenant=t1&inspector_view=facts&fact_subject=c1&fact_subject_type=commitment",
    ),
  );
  const next = readSelection(new URL(selectionUrl(selection), "https://example.test"));
  assert.equal(next.route, "inspector");
  assert.equal(next.inspectorView, "facts");
  assert.equal(next.factSubject, "c1");
  assert.equal(
    readSelection(new URL("https://example.test/app/inspector?inspector_view=unknown"))
      .inspectorView,
    "overview",
  );
});

test("unified UI has no audited legacy exits", () => {
  for (const file of [
    "Shell",
    "UnifiedApp",
    "OrdersPage",
    "WarehousePage",
    "FinancePage",
    "MasterDataPage",
    "DataSourcesPage",
    "DeliveryCase",
    "DecisionsPage",
    "ChatPage",
    "MasterDataCard",
  ]) {
    const content = source(`../src/unified/${file}.tsx`);
    assert.doesNotMatch(
      content,
      /(?:href=|location\.assign|location\.replace)[^\n]*(?:\/playground|\/app\/(?:orders[?`]|exceptions|explorer|commitments|parties))/,
    );
    assert.doesNotMatch(
      content,
      /t\("(?:Advanced order operations|Advanced warehouse operations|Advanced finance operations|Advanced settings|Technical Explorer|More workspaces|Open existing workspace|Open practice company)"\)/,
    );
  }
  assert.match(
    source("../src/unified/DecisionsPage.tsx"),
    /This proposal cannot be reviewed in this interface yet/,
  );
  assert.doesNotMatch(source("../src/unified/UnifiedApp.tsx"), /Sandbox — practice environment/);
  assert.match(source("../src/unified/CompanySwitcher.tsx"), /Sandbox/);
  assert.match(source("../src/unified/MasterDataCard.tsx"), /inspector_view: "records"/);
});

test("a reload keeps the answer already on screen and never collapses to a placeholder", () => {
  const hook = source("../src/unified/useCompanyContext.ts");
  assert.match(hook, /setState\(\(previous\) => \(\{ data: previous\.data, loading: true \}\)\)/);
  assert.doesNotMatch(hook, /setState\(\{ loading: true \}\);/);
  // A failed reload drops the previous answer, so a stale table never stands in for it.
  assert.match(
    hook,
    /catch\(\(error\) => \{\s*if \(current\)\s*setState\(\{\s*error: [^}]*loading: false,?\s*\}\);/,
  );

  // Register results dim in place while the next read is in flight.
  assert.match(source("../src/unified/RegisterTable.tsx"), /busy\?: boolean;/);
  assert.match(
    source("../src/unified/RegisterTable.tsx"),
    /className=\{reading\(busy, "erp-table-scroll"\)\}\s*\n\s*aria-busy=\{busy \|\| undefined\}/,
  );
  for (const file of [
    "OrdersPage",
    "WarehousePage",
    "FinancePage",
    "MasterDataPage",
    "DataSourcesPage",
    "FactsPage",
    "InspectorRecordsPage",
    "RulesWorkbench",
  ])
    assert.match(source(`../src/unified/${file}.tsx`), /busy=\{(?:read|list)\.loading\}/);

  // Facts and Inspector records showed the placeholder on every reload, not only the first.
  for (const file of ["FactsPage", "InspectorRecordsPage"])
    assert.doesNotMatch(
      source(`../src/unified/${file}.tsx`),
      /\{read\.loading \|\| read\.error \?/,
    );
});

test("the Workspaces sidebar does not duplicate the Inspector Facts register", () => {
  // Spec 114 FR-001 (revised 2026-09-10): /app/facts stays reachable through Data & sources and
  // the Reality Inspector Facts group, but the Workspaces group lists no separate Facts link.
  const shell = source("../src/unified/Shell.tsx");
  assert.doesNotMatch(shell, /selection\.route === "facts"/);
  assert.match(shell, /\{t\("Finance"\)\}/);
  assert.match(source("../src/unified/UnifiedApp.tsx"), /selection\.route === "facts"/);
  assert.match(source("../src/unified/DataSourcesPage.tsx"), /route: "facts"/);
});

test("one shared read placeholder draws the shape of the answer, not a framed sentence", () => {
  const state = source("../src/unified/ReadState.tsx");
  assert.match(state, /className="read-skeleton" role="status" aria-label=\{t\("Loading…"\)\}/);
  assert.match(state, /rows = 3/);
  // The failure keeps its own card and retry; the placeholder carries no border of its own.
  assert.match(state, /role="alert"/);
  assert.match(state, /t\("Could not load this view"\)/);
  assert.match(state, /t\("Retry"\)/);
  assert.doesNotMatch(state.split("if (loading)")[1].split("return (")[1], /border-border-default/);

  const css = source("../src/tailwind.css");
  // A read fast enough to go unnoticed must never flash a placeholder.
  assert.match(css, /\.read-skeleton \{[^}]*animation: read-reveal 120ms ease 200ms both;/);
  assert.match(css, /\.read-busy \{\s*opacity: 0\.55;/);
  assert.match(css, /prefers-reduced-motion: reduce/);

  // No page states loading in prose any more; only shared placeholders and busy controls do.
  const unified = new URL("../src/unified/", import.meta.url);
  for (const name of readdirSync(unified).filter((file) => file.endsWith(".tsx"))) {
    if (name === "ReadState.tsx") continue;
    assert.doesNotMatch(
      source(`../src/unified/${name}`),
      /role="status"[^>]*>\s*\{?t\("Loading…"\)/,
      name,
    );
  }
});

test("a register with no rows explains itself once, inside the shared table frame", () => {
  const table = source("../src/unified/RegisterTable.tsx");
  // The empty explanation is a body row of the register, so header, selection and
  // pagination stay where they were and no second card is drawn beside the table.
  assert.match(table, /<tbody>\s*\{!rows\.length && \(/);
  assert.match(table, /className="erp-empty" role="status"/);
  assert.match(table, /empty\?\.title \|\| t\("No matching records"\)/);
  assert.match(
    table,
    /empty\?\.hint \|\| t\("Try another filter or inspect the original records\."\)/,
  );

  const css = source("../src/tailwind.css");
  // Wide registers scroll horizontally; the explanation stays at the visible edge.
  assert.match(css, /\.erp-empty \{[^}]*position: sticky;[^}]*left: 0;/);

  // No register page keeps an empty state of its own next to or instead of the table.
  for (const name of [
    "OrdersPage",
    "WarehousePage",
    "FinancePage",
    "FactsPage",
    "MasterDataPage",
    "DataSourcesPage",
    "InspectorRecordsPage",
    "RulesWorkbench",
  ]) {
    const page = source(`../src/unified/${name}.tsx`);
    assert.doesNotMatch(page, /!\w+(?:\.\w+)*\.items\.length/, name);
    assert.doesNotMatch(page, /<(?:p|h2)[^>]*>\{t\("No matching records"\)\}/, name);
  }
});

test("every page action reaches the header through the one shared bar", () => {
  const bar = source("../src/unified/PageActionBar.tsx");
  // Every available page action is in one More actions disclosure; none: nothing.
  assert.match(bar, /const available = actions\.filter/);
  assert.match(bar, /if \(!available\.length\) return null;/);
  assert.match(bar, /<RegisterActions>\{available\.map\(button\)\}<\/RegisterActions>/);
  assert.match(bar, /data-page-action="menu"/);
  assert.doesNotMatch(bar, /br-btn-primary/);
  const unified = new URL("../src/unified/", import.meta.url);
  for (const name of readdirSync(unified).filter((file) => file.endsWith(".tsx"))) {
    if (name === "PageActionBar.tsx" || name === "PageHeading.tsx") continue;
    const page = source(`../src/unified/${name}`);
    assert.doesNotMatch(page, /<PageActions>/, `${name} writes into the header slot directly`);
    if (name !== "RegisterWorkbench.tsx")
      assert.doesNotMatch(page, /<RegisterActions>/, `${name} builds its own More actions`);
    assert.doesNotMatch(page, /pageActions=/, `${name} still switches the toolbar slot`);
  }
  // The register toolbar keeps search, submit, filters and count; actions left it.
  const toolbar = source("../src/unified/RegisterWorkbench.tsx");
  assert.doesNotMatch(
    toolbar.split("export function RegisterToolbar")[1].split("export function RegisterActions")[0],
    /\bactions\??:/,
  );
  // Non-actions stay with their content.
  assert.doesNotMatch(source("../src/unified/DecisionsPage.tsx"), /<WorkHeader[^/]*>\s*<span/);
  assert.match(source("../src/unified/SettingsPage.tsx"), /form="personal-preferences-form"/);
  // Master data names the primary action after its family.
  const master = source("../src/unified/MasterDataPage.tsx");
  for (const label of ["New customer", "New supplier", "New item", "New location"])
    assert.match(master, new RegExp(`"${label}"`), label);
  assert.doesNotMatch(master, /Create a record/);
});

test("workspace header is separate from company and chat chrome", () => {
  const shell = source("../src/unified/Shell.tsx");
  const header = shell.match(/<header[\s\S]*?<\/header>/)?.[0] || "";
  assert.doesNotMatch(
    header,
    /CompanySwitcher|ActionLauncher|LiveSimulationIndicator|page-introduction-actions/,
  );
  assert.match(header, /data-page-description-trigger/);
  assert.match(shell, /data-dock-open=\{dockOpen\}/);
  assert.match(
    shell,
    /data-page-tabs[\s\S]*ref=\{setRegisterHeader\}[\s\S]*page-introduction-actions[\s\S]*ref=\{setPageActions\}/,
  );
  assert.match(shell, /shell-navigation-utilities[\s\S]*<ActionLauncher/);
});

test("Exceptions keeps its catalog control beside filters instead of page actions", () => {
  const attention = source("../src/unified/AttentionPage.tsx");
  assert.doesNotMatch(attention, /<WorkHeader[\s\S]*?actions=/);
  assert.match(
    attention,
    /className="exceptions-filter-row[^"]*"[\s\S]*View all possible findings/,
  );
  assert.match(
    attention,
    /className="work-list-filters[^"]*"[\s\S]*<select[\s\S]*View all possible findings/,
  );
});

test("Decisions explains how proposals enter the queue beside its action filter", () => {
  const decisions = source("../src/unified/DecisionsPage.tsx");
  assert.match(decisions, /<select[\s\S]*All actions[\s\S]*How does a decision arise\?/);
  assert.match(decisions, /function DecisionHelp/);
  assert.match(decisions, /aria-labelledby="decision-help-title"/);
  assert.match(decisions, /className="br-exception-catalog"/);
  assert.doesNotMatch(decisions, /Oldest first/);
  assert.match(decisions, /A connected agent proposes a change but cannot carry it out/);
  assert.match(decisions, /A pending decision has changed nothing yet/);
  assert.match(decisions, /commitments_list or fulfillment_blockers/);
  assert.match(decisions, /business_records_discover/);
  assert.match(decisions, /reservation_propose/);
  assert.match(decisions, /Possible future direction/);
  assert.match(decisions, /not a committed part of the project/);
});

test("company context sits beside the logo as one workspace switcher", () => {
  const shell = source("../src/unified/Shell.tsx");
  assert.match(
    shell,
    /className="shell-brand[^"]*">[\s\S]*shell-brand-home[\s\S]*<LogoMark \/>[\s\S]*<div className="shell-company min-w-0 flex-1">\s*<CompanySwitcher/,
  );
  assert.equal(shell.match(/<CompanySwitcher/g).length, 1);
  assert.doesNotMatch(shell, /shell-company-(mobile|desktop)/);
  const switcher = source("../src/unified/CompanySwitcher.tsx");
  assert.match(
    switcher,
    /company\.sandbox_run_id \? \([\s\S]*company-switcher-context[\s\S]*data-company-context="sandbox"[\s\S]*t\("Sandbox"\)[\s\S]*\) : \([\s\S]*company-switcher-context[\s\S]*Reality/,
  );
  assert.match(switcher, /className="company-switcher-name" data-localization="original"/);
  const css = source("../src/tailwind.css");
  assert.match(css, /\.company-switcher-copy\s*\{[^}]*flex-direction:\s*column;/s);
  assert.match(
    css,
    /\.company-switcher-context\[data-company-context="sandbox"\]\s*\{[^}]*color:\s*var\(--color-accent\);/s,
  );
  assert.doesNotMatch(css, /shell-company-(mobile|desktop)/);
});

test("company switcher labels sandbox companies in its option list", () => {
  const switcher = source("../src/unified/CompanySwitcher.tsx");
  assert.match(
    switcher,
    /row\.sandbox_run_id && \([\s\S]*company-sandbox-badge[\s\S]*t\("Sandbox"\)/,
  );
});

test("Inspector records uses the same single toolbar inset as operational registers", () => {
  const records = source("../src/unified/InspectorRecordsPage.tsx");
  assert.match(records, /className="register-surface" data-inspector-records/);
  assert.match(records, /<form\s+className="register-toolbar-form"/);
  const css = source("../src/tailwind.css");
  assert.match(
    css,
    /\.register-surface > form\.register-toolbar-form\s*\{[^}]*padding-inline:\s*0;/s,
  );
  assert.match(records, /<div className="register-table-inset">\s*<RegisterTable/);
  assert.match(css, /\.register-table-inset\s*\{[^}]*padding-inline:\s*16px;/s);
  assert.doesNotMatch(css, /\[data-inspector-records\][^{]*margin-inline/);
});

test("Actions uses the shared register inset instead of custom spacing", () => {
  const actions = source("../src/unified/ActionDirectory.tsx");
  assert.match(actions, /<RegisterToolbar/);
  assert.match(actions, /search=\{/);
  assert.match(actions, /filters=\{/);
  assert.match(actions, /<div className="py-4">/);
  assert.doesNotMatch(actions, /<div className="p-4">/);
  assert.doesNotMatch(actions, /register-toolbar-block flex/);
});

test("Actions event history uses the shared toolbar and table structure", () => {
  const activity = source("../src/unified/ActivityDrawer.tsx");
  assert.match(activity, /embedded \? \(\s*<RegisterToolbar/);
  assert.match(activity, /const embeddedActivityBody = "register-table-inset py-4"/);
  assert.match(activity, /className=\{embedded \? embeddedActivityBody : drawerActivityBody\}/);
  assert.match(activity, /if \(embedded\)[\s\S]*<RegisterWorkbench>[\s\S]*data-inline-activity/);
  assert.match(activity, /className="register-surface min-w-0 overflow-hidden"/);
  const css = source("../src/tailwind.css");
  assert.match(css, /:not\(\.register-toolbar-form\)/);
  assert.match(css, /:not\(\s*\.register-table-inset\s*\)/s);
});

test("Rules table uses the same inset as its toolbar", () => {
  const rules = source("../src/unified/RulesWorkbench.tsx");
  assert.match(rules, /className="register-surface" data-rules-register/);
  assert.match(rules, /<div className="register-table-inset">\s*<RegisterTable/);
  const css = source("../src/tailwind.css");
  assert.match(css, /\.register-table-inset\s*\{[^}]*padding-inline:\s*16px;/s);
  assert.doesNotMatch(css, /\[data-rules-register\][^{]*margin-inline/);
});

test("every Inspector table footer uses the shared browser-bottom footer", () => {
  const table = source("../src/unified/RegisterTable.tsx");
  assert.doesNotMatch(table, /\{cursorView && footer\}/);
  assert.match(table, /\(selectable \|\| !cursorView \|\| footer\)/);
  assert.match(table, /<div className="erp-register-footer">/);
  const activity = source("../src/unified/ActivityDrawer.tsx");
  assert.match(activity, /footer=\{olderControls\}/);
  assert.match(activity, /\{!embedded && olderControls\}/);
  const records = source("../src/unified/InspectorRecordsPage.tsx");
  const rules = source("../src/unified/RulesWorkbench.tsx");
  assert.doesNotMatch(records, /footer=\{[\s\S]{0,120}<div[^>]*(border-t|p-3)/);
  assert.doesNotMatch(rules, /footer=\{[\s\S]{0,120}<div[^>]*p-3/);
});

test("master data forms expose every field the shared services accept", () => {
  const card = source("../src/unified/MasterDataCard.tsx");
  const fields = {
    party: [
      "name",
      "type",
      "roles",
      "accounting_code",
      "payment_term_code",
      "default_currency",
      "credit_limit",
      "tax_identifier",
    ],
    item: [
      "sku",
      "name",
      "unit",
      "item_type",
      "tracking_type",
      "default_location_id",
      "purchase_unit",
      "conversion_factor",
      "lead_time_days",
    ],
    location: ["name", "type", "parent_location_id", "allows_stock"],
    provenance: ["source_system", "external_id"],
  };
  for (const key of Object.values(fields).flat())
    assert.match(card, new RegExp(`key: "${key}"`), key);
  // Lossless external evidence is never edited through the form.
  assert.doesNotMatch(card, /source_payload/);
  // Choices come from the tenant-scoped suggestion endpoint, not from a second list.
  assert.match(card, /api\.suggestions\(tenant, kind\)/);
  for (const kind of ["payment-terms", "currencies", "units", "locations", "source-system-codes"])
    assert.match(card, new RegExp(`choices: "${kind}"`), kind);
  // The register's own role stays fixed while other roles are editable.
  assert.match(card, /disabled=\{option\.value === family\}/);
  const page = source("../src/unified/MasterDataPage.tsx");
  assert.match(page, /t\("Edit details"\)/);
  assert.match(page, /<RecordSummary/);
  for (const file of [card, page]) assert.doesNotMatch(file, /Edit basic details/);
});
