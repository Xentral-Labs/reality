"use strict";

const el = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = String(text);
  if (className) node.className = className;
  return node;
};
const byId = (id) => document.getElementById(id);
const original = (value) => JSON.stringify(value, null, 2);
const state = { key: "", view: "company", party: "", data: null, revision: "", generation: 0, busy: false, opened: new Set() };
const labels = {
  customer_order: "Customer order received", customer_message: "Customer message received",
  purchase_order: "Purchase order placed", partial_supplier_receipt: "Supplier goods received",
  supplier_delay: "Supplier delay recorded", partial_customer_dispatch: "Part of the order dispatched",
  customer_dispatch: "Order dispatched", package_delivery: "Delivery confirmed",
  carrier_exception: "Carrier exception recorded", delivery_failure: "Delivery failed — goods returned",
  customer_cancellation: "Customer requested cancellation", cancel_commitment: "Remaining order cancelled",
  return_announcement: "Customer return announced", return_receipt: "Returned goods received",
  stock_adjustment: "Stock count adjustment", warehouse_transfer: "Stock moved between warehouses",
  sales_invoice: "Customer invoice recorded", customer_payment: "Customer payment recorded",
  supplier_invoice: "Supplier invoice recorded", supplier_payment: "Supplier paid",
  sales_credit: "Customer credit recorded", customer_refund: "Customer refund recorded",
  shopify_payout: "Provider payout recorded", payout_replay: "Repeated payout checked"
};
const readable = (key) => labels[key] || String(key || "Recorded activity").replaceAll("_", " ");
const date = (value) => value ? new Date(value).toLocaleString(undefined, { timeZoneName: "short" }) : "Not recorded";
function detail(parent, value, key, title = "Original evidence & references") {
  const node = el("details");
  node.open = state.opened.has(key);
  node.append(el("summary", title), el("pre", original(value)));
  node.addEventListener("toggle", () => node.open ? state.opened.add(key) : state.opened.delete(key));
  parent.append(node);
}
function notice(messages) {
  const root = byId("notice");
  root.replaceChildren();
  if (!messages.length) return;
  const box = el("div", undefined, "notice");
  for (const message of messages) box.append(el("div", message));
  root.append(box);
}
function stat(label, value, note, badgeClass) {
  const node = el("div", undefined, "stat");
  node.append(el("span", label, "stat-label"));
  if (badgeClass) { const strong = el("strong"); strong.append(el("span", value, `badge ${badgeClass}`)); node.append(strong); }
  else node.append(el("strong", value));
  node.append(el("small", note));
  return node;
}
function row(parent, label, value) {
  const line = el("div", undefined, "metric-row");
  line.append(el("span", label), el("strong", value));
  parent.append(line);
}
function panel(title) {
  const node = el("section", undefined, "insight");
  node.append(el("h2", title));
  return node;
}
function drawStatus() {
  const { summary: s, manifest: m } = state.data;
  const core = { passed: "Checks passed", passed_at_checkpoint: "Last check passed", failed: "Mismatch found", failed_at_checkpoint: "Mismatch found", unchecked: "Not checked", unknown: "Outcome uncertain", awaiting_review: "Awaiting exact review" }[s.core_status] || s.core_status;
  const badge = s.core_status.startsWith("passed") ? "" : s.core_status.startsWith("failed") ? "fail" : "warn";
  const exercised = s.coverage.exercised?.length;
  byId("status").replaceChildren(
    stat("SIMULATED TIME", s.day === null || s.day === undefined ? "—" : `Day ${s.day}`, `of ${m.days ?? "?"} authored days · ${m.operator ?? "unknown operator"}`),
    stat("REALITY CORE", core, state.data.notices.length ? "Evidence notices — see above" : "Recorded independent checkpoint", badge || "good"),
    stat("BUSINESS CASE FAMILIES", exercised === undefined ? "Not reported" : `${exercised} / ${s.coverage.planned?.length ?? "?"}`, s.event_count === null ? `${s.operation_count} accepted tool operations · not case coverage` : `${s.event_count} recorded business events`),
    stat("RUN RECORD", s.run_state === "finished" ? "Final report" : "Unfinished", s.run_state === "finished" ? "Saved outcome available" : "Process liveness is not verified")
  );
}
function drawInsights() {
  const { summary: s, checkpoint, report, snapshot } = state.data;
  const root = byId("insights");
  root.replaceChildren();
  const check = panel("Last independent checkpoint");
  row(check, "Simulated day", s.day ?? "—");
  check.append(el("p", `Recorded ${date(s.last_observed_at)}`, "subtle"));
  for (const [sku, quantity] of Object.entries(s.physical)) row(check, `Stock · ${sku}`, `${quantity} pieces`);
  if (!Object.keys(s.physical).length) check.append(el("p", "No stock observation recorded.", "subtle"));
  if (checkpoint) detail(check, checkpoint, "checkpoint", "Inspect full checkpoint");
  root.append(check);
  const goals = panel("Customer delivery goals");
  for (const status of ["met", "pending", "missed", "cancelled"]) row(goals, { met: "Delivered as expected", pending: "Still pending", missed: "Missed goal", cancelled: "Fully cancelled" }[status], s.goals[status] ?? 0);
  goals.append(el("p", "A missed delivery goal is separate from a booking mismatch.", "subtle"));
  if (!Object.keys(s.goals).length) goals.append(el("p", "Goals have not been reported yet.", "subtle"));
  if ((report.goals || snapshot.goals)?.length) detail(goals, report.goals || snapshot.goals, "goals", "Inspect original goal results");
  root.append(goals);
  const coverage = panel("Business case coverage");
  if (s.coverage.planned) {
    const heading = el("div", `${s.coverage.exercised?.length ?? 0} `, "coverage-head");
    heading.append(el("small", `/ ${s.coverage.planned.length} planned families`));
    coverage.append(heading);
    const track = el("div", undefined, "coverage-track"), fill = el("div", undefined, "coverage-fill");
    // Presentation-only ratio; no amount or business quantity is recomputed.
    fill.style.width = `${100 * (s.coverage.exercised?.length ?? 0) / (s.coverage.planned.length || 1)}%`;
    track.append(fill); coverage.append(track);
    for (const [kind, count] of Object.entries(s.case_counts)) row(coverage, readable(kind), count);
    if (s.coverage.not_exercised?.length) detail(coverage, s.coverage.not_exercised.map(readable), "missing", "Families not exercised");
  } else coverage.append(el("p", "No business case coverage report yet. Tool calls are not counted as cases.", "subtle"));
  root.append(coverage);
  const finance = panel("Recorded account balances");
  for (const [name, amount] of Object.entries(s.accounts)) row(finance, readable(name), `${amount} EUR`);
  if (!Object.keys(s.accounts).length) finance.append(el("p", "No financial checkpoint recorded.", "subtle"));
  finance.append(el("p", "Signed ledger balances, preserved as recorded.", "subtle")); root.append(finance);
  if (s.differences.length) { const mismatch = panel("Checkpoint differences"); mismatch.append(el("span", `${s.differences.length} differences`, "badge fail")); detail(mismatch, s.differences, "mismatch", "Expected / actual / delta"); root.prepend(mismatch); }
  const pending = report.pending_proposal || snapshot.pending_proposal;
  if (pending) { const review = panel("Awaiting exact review"); review.append(el("p", readable(pending.tool), "subtle")); detail(review, pending, "pending"); root.prepend(review); }
}
function partyName(id) { return state.data.parties.find((p) => p.id === id)?.name || (id ? "Unresolved business partner" : "Company activity"); }
function messageEntry(message, index) {
  const node = el("article", undefined, "entry message");
  node.append(el("span", "✉", "entry-icon"));
  const content = el("div"), meta = el("div", undefined, "entry-meta");
  meta.append(el("span", message.party_id ? partyName(message.party_id) : "Unassigned correspondence"));
  const status = message.status === "simulated" ? "Simulated locally · no real email sent" : message.status === "proposed" ? "Reply draft · not sent" : message.status === "not_recorded" ? "Message state not recorded" : String(message.status).replaceAll("_", " ");
  meta.append(el("span", `${message.direction === "not_recorded" ? "Direction not recorded" : message.direction} · ${status}`, "badge"));
  if (message.day !== undefined) meta.append(el("span", `Simulation day ${message.day}`));
  content.append(meta, el("h3", message.payload.subject || "Recorded message"));
  if (message.payload.in_reply_to) {
    const parent = state.data.messages.find((m) => m.payload.message_id === message.payload.in_reply_to);
    content.append(el("p", `Reply to: ${parent?.payload.subject || message.payload.in_reply_to}`, "subtle"));
  }
  content.append(el("div", `From: ${message.payload.from ?? "not recorded"} → To: ${message.payload.to ?? "not recorded"}`, "mail-fields"));
  const body = el("div", undefined, "message-body"), value = message.payload.body;
  if (value && typeof value === "object") {
    if (value.text !== undefined) body.append(el("p", value.text));
    const known = new Set(["text", "item", "quantity", "stated_amount", "deadline_day", "destination"]);
    if (value.item !== undefined || value.quantity !== undefined) body.append(el("p", `Quantity: ${value.quantity ?? "quantity not stated"} pieces${value.item !== undefined ? ` · ${value.item}` : ""}`));
    if (value.stated_amount !== undefined) body.append(el("p", `Stated order total: ${value.stated_amount} EUR`));
    if (value.deadline_day !== undefined) body.append(el("p", `Requested delivery by simulation day ${value.deadline_day}`));
    if (value.destination !== undefined) {
      const address = value.destination;
      body.append(el("p", `Deliver to: ${address && typeof address === "object" ? [address.name, address.street, address.postal_code, address.city, address.country].filter(Boolean).join(", ") : address}`));
    }
    for (const [key, received] of Object.entries(value)) if (!known.has(key)) body.append(el("p", `${readable(key)}: ${typeof received === "object" ? original(received) : received}`));
  } else body.append(el("p", value ?? "No body recorded."));
  content.append(body);
  if (message.recorded_at) content.append(el("p", `Recorded ${date(message.recorded_at)}`));
  detail(content, message, `message-${index}`); node.append(content); return node;
}
function actionEntry(event, index, operation = false) {
  const node = el("article", undefined, "entry"); node.append(el("span", "↗", "entry-icon"));
  const content = el("div"), meta = el("div", undefined, "entry-meta");
  meta.append(el("span", partyName(event.party_id)), el("span", operation ? "Accepted tool operation" : "Business event"));
  content.append(meta, el("h3", readable(operation ? event.tool : event.kind)));
  if (event.id) content.append(el("p", `Reference: ${event.id}`));
  const args = event.order?.arguments;
  if (args?.lines) for (const line of args.lines) content.append(el("p", `Quantity: ${line.quantity} · stated amount: ${line.gross_amount} EUR`));
  detail(content, event, `action-${operation}-${index}`); node.append(content); return node;
}
function drawActivity() {
  const data = state.data, filtered = state.view !== "company";
  byId("party-filter").hidden = !filtered;
  const selector = byId("party"), candidates = data.parties.filter((p) => p.role === state.view);
  selector.replaceChildren(el("option", `All ${state.view === "supplier" ? "suppliers" : "customers"}`)); selector.options[0].value = "";
  for (const party of candidates) { const option = el("option", party.name); option.value = party.id; selector.append(option); }
  if (state.party && !candidates.some((p) => p.id === state.party)) state.party = "";
  selector.value = state.party;
  for (const button of document.querySelectorAll("[data-view]")) button.setAttribute("aria-pressed", String(button.dataset.view === state.view));
  byId("activity-heading").textContent = { company: "Company timeline", customer: "Customer correspondence & activity", supplier: "Supplier correspondence & activity" }[state.view];
  const allowed = (partyId) => !filtered || (state.party ? partyId === state.party : candidates.some((p) => p.id === partyId));
  const messages = data.messages.map((item, index) => ({ type: "message", item, index })).filter((entry) => allowed(entry.item.party_id));
  const usingOperations = data.summary.event_count === null;
  const actions = (usingOperations ? data.operations : data.timeline.filter((e) => e.kind !== "customer_message")).map((item, index) => ({ type: "action", item, index })).filter((entry) => allowed(entry.item.party_id));
  const entries = [...messages, ...actions].sort((a, b) => (a.item.day ?? 0) - (b.item.day ?? 0));
  byId("activity-count").textContent = `${messages.length} messages · ${actions.length} ${usingOperations ? "operations" : "events"}`;
  const outgoing = messages.filter((e) => e.item.direction === "outgoing").length;
  byId("view-note").textContent = `${messages.length ? "Original recorded messages and separate business activity." : "No messages recorded in this view. Business activity is shown separately."} ${outgoing ? `${outgoing} outgoing messages with their recorded states.` : "No outgoing agent replies recorded."} ${usingOperations ? "Business timeline is not published yet; showing accepted tool operations." : ""}`;
  const root = byId("activity"); root.replaceChildren();
  if (!entries.length) { const empty = el("div", undefined, "empty"); empty.append(el("strong", "Nothing recorded here yet."), el("span", "The spectator will show messages and actions when the selected run records them.")); root.append(empty); return; }
  let day = null;
  for (const entry of entries) {
    if (entry.item.day !== day) { day = entry.item.day; root.append(el("div", day === null || day === undefined ? "Day not recorded" : `Simulation day ${day}`, "day-heading")); }
    root.append(entry.type === "message" ? messageEntry(entry.item, entry.index) : actionEntry(entry.item, entry.index, usingOperations));
  }
}
function render() { drawStatus(); drawInsights(); drawActivity(); }
async function fetchJson(path) { const response = await fetch(path, { cache: "no-store" }); if (!response.ok) throw new Error(`Viewer request failed (${response.status}). Retry with Refresh.`); return response.json(); }
async function refresh(force = false) {
  if (state.busy) return;
  state.busy = true;
  const generation = state.generation, selected = state.key;
  byId("refresh").disabled = true;
  try {
    const listing = await fetchJson("/api/runs");
    if (generation !== state.generation) return;
    const select = byId("run"); select.replaceChildren();
    for (const run of listing.runs) { const option = el("option", `${run.operator || "run"} · ${run.profile_id || "profile"} · ${run.key}`); option.value = run.key; select.append(option); }
    if (!listing.runs.length) { select.append(el("option", "No runs yet")); state.key = ""; state.data = null; byId("status").replaceChildren(); byId("insights").replaceChildren(); byId("activity").replaceChildren(el("div", "No run journals found. Start a simulator or select another artifact root.", "empty")); notice(listing.notices); return; }
    if (!listing.runs.some((r) => r.key === selected)) { state.key = listing.runs[0].key; state.party = ""; state.opened.clear(); }
    select.value = state.key;
    const key = state.key, data = await fetchJson(`/api/runs/${key.split("/").map(encodeURIComponent).join("/")}`);
    if (generation !== state.generation || key !== state.key) return;
    const revision = original(data);
    state.data = data;
    if (force || revision !== state.revision) { state.revision = revision; render(); }
    notice([...listing.notices, ...data.notices]);
    byId("updated").textContent = `Last viewer refresh: ${new Date().toLocaleTimeString()}`;
  } catch (error) { if (generation === state.generation) notice([error.message, "Previously displayed data may be stale."]); }
  finally { state.busy = false; byId("refresh").disabled = false; if (generation !== state.generation) refresh(true); }
}
byId("run").addEventListener("change", () => {
  state.key = byId("run").value; state.party = ""; state.data = null; state.generation++; state.opened.clear();
  byId("status").replaceChildren(); byId("insights").replaceChildren(); byId("party").replaceChildren();
  byId("view-note").textContent = ""; byId("activity-count").textContent = ""; notice([]);
  byId("activity").replaceChildren(el("div", "Loading selected run…", "empty")); refresh(true);
});
byId("party").addEventListener("change", () => { state.party = byId("party").value; drawActivity(); });
for (const button of document.querySelectorAll("[data-view]")) button.addEventListener("click", () => { state.view = button.dataset.view; state.party = ""; if (state.data) drawActivity(); });
byId("refresh").addEventListener("click", () => refresh(true));
refresh();
setInterval(() => refresh(), 5000);
