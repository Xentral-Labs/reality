let state,
  party = null,
  order = null,
  selected = null,
  previewed = null,
  requestId = null,
  busy = false,
  direction = "all",
  workspaceTab = "overview",
  metricFilter = "";
const $ = (id) => document.getElementById(id),
  esc = (v) =>
    String(v ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
const name = (id) => state.parties.find((p) => p.id === id)?.name || id;
const refs = (o) =>
  `<details class="evidence"><summary>ⓘ Reality records</summary><p>Company: ${esc(state.company_id)}</p>${["source_record_id", "document_line_id", "commitment_id"].map((k) => (o[k] ? `<div class="ref"><b>${esc(k.replaceAll("_", " "))}</b><code>${esc(o[k])}</code></div>` : "")).join("")}<div class="ref"><b>Document</b><code>${esc(o.id || o.document_id)}</code></div><p>Use these exact IDs in your connected Reality instance. The live console does not verify external URLs.</p></details>`;
const matching = (rows) => rows.filter((r) => !party || r.party_id === party);
const time = (date) =>
  new Date(date).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
const directionLabel = (category) =>
  ({
    incoming: "↙ Received",
    outgoing: "↗ Sent locally",
    activity: "✓ Recorded action",
  })[category];
const orderCard = (o) =>
  `<button class="order compact" data-order="${esc(o.id)}"><small>${esc(o.number)} · ${esc(name(o.party_id))}</small><strong>${esc(o.quantity)} pieces · ${esc(o.amount)} €</strong><span>${esc(o.fulfilled)} fulfilled · ${esc(o.open)} open · ${esc(o.status)}</span></button>`;
const documentCard = (d) =>
  `<button class="document-row" data-document="${esc(d.id)}"><span>▤ ${esc(d.type.replaceAll("_", " "))}</span><strong>${esc(d.number || d.id)}</strong><small>${esc(d.amount)} ${esc(d.currency)} · ${esc(time(d.recorded_at))}</small></button>`;
const mailCard = (m) =>
  `<button class="mail-row" data-message="${esc(m.source_record_id)}"><small>${esc(directionLabel(m.direction))} · ${esc(time(m.recorded_at))}</small><strong>${esc(m.subject)}</strong><span>${esc(m.body.slice(0, 120))}</span></button>`;
const messageText = (m) =>
  `<article class="message conversation ${m.direction === "outgoing" ? "out" : ""}"><small>${esc(directionLabel(m.direction))} · ${esc(m.recorded_at)}</small><h3>${esc(m.subject)}</h3><p>${esc(m.body)}</p>${m.requested_quantity ? `<p class="request">Requested quantity: ${esc(m.requested_quantity)} — request only</p>` : ""}<details class="evidence"><summary>Original email & Reality context</summary><p>${esc(m.from)} → ${esc(m.to)}</p><code>${esc(m.source_record_id)}</code><p>Thread: ${esc(m.thread_id)}</p><p>Reply to: ${esc(m.in_reply_to || "—")}</p><p>Case: ${esc(m.case_family || m.kind)}</p></details></article>`;
function render() {
  const checkpoint = state.checkpoint;
  const latest = state.last_world_tick;
  const age = latest
    ? Math.round((Date.now() - Date.parse(latest)) / 1000)
    : null;
  const enabled = state.schedules.find(
    (s) => s.type === "simulator.world",
  )?.enabled;
  $("status").textContent =
    `${enabled ? "Intake enabled" : "Intake paused"} · target ${state.target_orders_per_hour}/hour · last intake ${age === null ? "not observed" : age + "s ago"} · checked ${checkpoint.observed_at || "not yet"} · worker/operator liveness unverified`;
  $("checks").textContent =
    `${checkpoint.core_status} · ${checkpoint.automatic_orders_last_hour ?? "—"} automatic orders in the last hour · ${checkpoint.open_orders ?? "—"} open · ${checkpoint.overdue_orders ?? "—"} overdue · ${checkpoint.manual ?? "—"} manual events · Delivery: ${
      Object.entries(checkpoint.delivery_goals || {})
        .map(([k, v]) => `${k}: ${v}`)
        .join(", ") || "unchecked"
    } · Cases: ${
      Object.entries(checkpoint.case_families || {})
        .map(([k, v]) => `${k}: ${v}`)
        .join(", ") || "unchecked"
    }`;
  $("tiles").innerHTML = [
    ["🛒", state.order_count, "Orders received"],
    ["↙", state.message_count, "Incoming emails"],
    ["↗", state.reply_count, "Actual local replies"],
    [
      "📦",
      state.stock.map((i) => `${i.sku}: ${i.quantity}`).join(" / "),
      "Stock",
    ],
    ["🔎", checkpoint.unread ?? "—", "Unread at last check"],
  ]
    .map(
      (t) =>
        `<div class="tile"><span>${t[0]}</span><strong>${esc(t[1])}</strong><small>${t[2]}</small></div>`,
    )
    .join("");
  const p = state.performance;
  if (p && $("performance")) {
    $("performance-summary").textContent =
      `Full run: ${p.eligible_orders} eligible orders · first dispatch average ${p.average_first_dispatch_minutes ?? "—"} min (${p.first_dispatch_sample_orders} samples) · complete dispatch average ${p.average_complete_dispatch_minutes ?? "—"} min (${p.complete_dispatch_sample_orders} samples). Dispatch is not customer arrival.`;
    $("performance").innerHTML = [
      ["ready", p.ready_orders, "Ready to dispatch"],
      [
        "reservation_blocked",
        p.reservation_blocked_orders,
        "Missing reservations",
      ],
      [
        "complete",
        `${p.complete_dispatch_orders} / ${p.eligible_orders}`,
        `Completely dispatched · ${p.dispatch_rate_percent ?? "—"}%`,
      ],
      ["partial", p.partial_orders, "Partial dispatch"],
      ["overdue", p.overdue_orders, "Overdue orders"],
      ["at_risk", p.at_risk_orders, "Blocked & due within 2h"],
    ]
      .map(
        ([flag, value, label]) =>
          `<button class="tile ${metricFilter === flag ? "active" : ""}" data-metric="${flag}"><strong>${esc(value)}</strong><small>${esc(label)}</small></button>`,
      )
      .join("");
    $("performance-orders").hidden = !metricFilter;
    $("performance-orders").innerHTML =
      `<h3>Matching orders · ${esc(metricFilter.replaceAll("_", " "))}</h3><p>Counts cover the full run. Oldest 200 matching orders are shown. Average complete dispatch: ${esc(p.average_complete_dispatch_minutes ?? "—")} minutes · ${esc(p.complete_dispatch_sample_orders)} samples.</p>${p.orders.map((o) => `<button class="document-row" data-performance-order="${esc(o.document_id)}"><strong>${esc(o.number)} · ${esc(o.party_name)}</strong><small>${esc(o.flags.filter((f) => !["eligible", "received_last_hour", "completed_last_hour", "first_dispatch_sample", "complete_dispatch_sample"].includes(f)).join(" · "))} · open ${esc(o.open_units)} · age ${esc(o.age_minutes)} minutes</small></button>`).join("") || "<p>No matching orders recorded.</p>"}`;
    document.querySelectorAll("[data-metric]").forEach(
      (b) =>
        (b.onclick = async () => {
          metricFilter =
            metricFilter === b.dataset.metric ? "" : b.dataset.metric;
          await refresh();
        }),
    );
    document
      .querySelectorAll("[data-performance-order]")
      .forEach(
        (b) =>
          (b.onclick = () =>
            openDetail("performance", b.dataset.performanceOrder)),
      );
  }
  $("people").innerHTML = state.parties
    .filter((p) => p.role !== "company")
    .map((p) => {
      const counts = state.party_summaries[p.id];
      return `<button class="person ${party === p.id ? "active" : ""}" data-party="${esc(p.id)}"><span class="avatar">${p.role === "supplier" ? "🏭" : "👤"}</span><div><strong>${esc(p.name)}</strong><small>${esc(p.role)}</small><span class="party-stats">↙ ${counts.incoming} · ↗ ${counts.outgoing}<br>${counts.orders} orders · ${counts.documents} documents</span></div></button>`;
    })
    .join("");
  const entries = matching(state.flow)
    .filter((r) => direction === "all" || r.category === direction)
    .slice(0, 60);
  $("flowcount").textContent =
    `${entries.length} recent entries · newest first · incoming requests are separate from accepted business actions`;
  $("flow").innerHTML =
    entries
      .map(
        (r) =>
          `<button class="flow-row ${esc(r.category)}" data-flow="${esc(r.id)}"><span class="flow-icon">${{ incoming: "↙", outgoing: "↗", activity: "✓" }[r.category]}</span><div><small>${esc(directionLabel(r.category))} · ${esc(name(r.party_id || "Company"))} · ${esc(time(r.recorded_at))}</small><h4>${esc(r.title)}</h4><p>${esc(r.body?.slice(0, 100) || r.document_number || r.event_type || "")}</p></div><span class="flow-arrow">›</span></button>`,
      )
      .join("") || '<div class="empty">No entries for this filter yet.</div>';
  $("heading").textContent = party
    ? name(party) + " — at a glance"
    : "Company workspace";
  const counts = party ? state.party_summaries[party] : null;
  $("partycounts").textContent = counts
    ? `${counts.incoming} incoming emails · ${counts.outgoing} outgoing replies · ${counts.orders} orders · ${counts.documents} documents in this run. Lists below show the recent window.`
    : "Select a customer or supplier to see their emails, orders and documents together.";
  const mails = matching(state.messages).slice().reverse(),
    orders = matching(state.orders),
    documents = matching(state.documents);
  const content = {
    mail: `<div class="mail-list">${mails.slice(0, 40).map(mailCard).join("") || '<p class="empty">No emails here yet.</p>'}</div>`,
    orders: `<div class="orders">${orders.map(orderCard).join("") || '<p class="empty">No orders here yet.</p>'}</div>`,
    documents: `<div class="document-list">${documents.map(documentCard).join("") || '<p class="empty">No documents here yet.</p>'}</div>`,
  };
  const catalogue = (state.purchasing || [])
    .filter((s) => s.supplier_id === party)
    .map(
      (s) =>
        `<section class="evidence"><h3>Supplier purchasing catalogue</h3><p>Current EUR price resolution at the shown quantity. Missing values need clarification.</p>${s.items.map((i) => `<article><strong>${esc(i.name)} · ${esc(i.supplier_item_number || "Supplier number missing")}</strong><p>${esc(i.unit_price || "Price missing")} ${esc(i.currency)} / ${esc(i.unit)} · minimum ${esc(i.minimum_quantity || "unknown")} · multiple ${esc(i.order_multiple || "unknown")}</p><small>Evaluated quantity ${esc(i.evaluated_quantity)} · item ${esc(i.item_id)}<br>Price entry ${esc(i.price_list_entry_id || "not recorded")}</small></article>`).join("")}</section>`,
    )
    .join("");
  $("workspace-content").innerHTML =
    catalogue +
    (workspaceTab === "overview"
      ? `<div class="overview-grid"><section><h3>Latest emails</h3>${mails.slice(0, 4).map(mailCard).join("") || '<p class="muted">No emails yet.</p>'}</section><section><h3>Orders</h3>${orders.slice(0, 4).map(orderCard).join("") || '<p class="muted">No orders yet.</p>'}<h3>Documents</h3>${documents.slice(0, 4).map(documentCard).join("") || '<p class="muted">No documents yet.</p>'}</section></div>`
      : content[workspaceTab]);
  $("limits").textContent = state.view_limit;
  document.querySelectorAll("[data-party]").forEach(
    (b) =>
      (b.onclick = () => {
        party = b.dataset.party;
        order = null;
        workspaceTab = "overview";
        close();
        render();
        $("workspace").scrollIntoView({ behavior: "smooth", block: "start" });
      }),
  );
  document.querySelectorAll("[data-direction]").forEach((b) => {
    b.classList.toggle("active", direction === b.dataset.direction);
    b.onclick = () => {
      direction = b.dataset.direction;
      render();
    };
  });
  document.querySelectorAll("[data-tab]").forEach((b) => {
    b.classList.toggle("active", workspaceTab === b.dataset.tab);
    b.onclick = () => {
      workspaceTab = b.dataset.tab;
      render();
    };
  });
  bindDetails();
  if (selected) showDetail();
}
function bindDetails() {
  document
    .querySelectorAll("[data-flow]")
    .forEach((b) => (b.onclick = () => openDetail("flow", b.dataset.flow)));
  document
    .querySelectorAll("[data-message]")
    .forEach(
      (b) => (b.onclick = () => openDetail("message", b.dataset.message)),
    );
  document
    .querySelectorAll("[data-order]")
    .forEach((b) => (b.onclick = () => openDetail("order", b.dataset.order)));
  document
    .querySelectorAll("[data-document]")
    .forEach(
      (b) => (b.onclick = () => openDetail("document", b.dataset.document)),
    );
}
function openDetail(type, id) {
  selected = { type, id };
  showDetail();
}
function showDetail() {
  const { type, id } = selected;
  const record =
    type === "performance"
      ? state.performance.orders.find((r) => r.document_id === id)
      : type === "flow"
        ? state.flow.find((r) => r.id === id)
        : type === "message"
          ? state.messages.find((r) => r.source_record_id === id)
          : type === "order"
            ? state.orders.find((r) => r.id === id)
            : state.documents.find((r) => r.id === id);
  const r = record || selected.record;
  if (!r) return;
  selected.record = r;
  let documentId =
    r.document_id || (type === "order" || type === "document" ? r.id : null);
  const doc = state.documents.find((d) => d.id === documentId);
  const o = state.orders.find((d) => d.id === documentId);
  let body =
    r.body !== undefined
      ? messageText(r)
      : `<span class="pill">${esc(r.category === "activity" ? "Accepted business event" : r.type?.replaceAll("_", " "))}</span><h2>${esc(r.title || r.number)}</h2><p>${esc(name(r.party_id || "Company"))}</p>`;
  if (o)
    body += `<section class="detail-order"><h3>Order ${esc(o.number)}</h3><p>${esc(o.quantity)} stated · ${esc(o.fulfilled)} fulfilled · ${esc(o.open)} open · ${esc(o.status)}</p><p>${esc(o.amount)} € · deadline ${esc(o.due_at || "not stated")}</p>${refs(o)}</section>`;
  else if (doc)
    body += `<h3>Document ${esc(doc.number || doc.id)}</h3><p>${esc(doc.type)} · ${esc(doc.amount)} ${esc(doc.currency)}</p>${refs(doc)}`;
  else if (documentId)
    body += `<p>Linked document (outside recent list): <code>${esc(documentId)}</code></p>`;
  if (type === "performance")
    body += `<p>State: ${esc(r.flags.filter((f) => !["eligible", "received_last_hour", "completed_last_hour", "first_dispatch_sample", "complete_dispatch_sample"].includes(f)).join(" · "))} · open ${esc(r.open_units)} · age ${esc(r.age_minutes)} minutes</p><p>Source: <code>${esc(r.source_record_id)}</code></p><p>Commitments: ${r.commitment_ids.map(esc).join(" · ")}</p>`;
  if (r.category === "activity")
    body += `<details class="evidence"><summary>Recorded event & source</summary><p>${esc(r.event_type)} · ${esc(r.id)}</p><p>${esc(r.subject_type)}: ${esc(r.subject_id)}</p><code>${esc(r.source_record_id || "No source on event")}</code><pre>${esc(JSON.stringify(r.payload, null, 2))}</pre></details>`;
  const conversation = state.messages.filter((m) =>
    documentId
      ? m.document_id === documentId
      : r.thread_id && m.thread_id === r.thread_id,
  );
  body += `<h3>Conversation${conversation.length ? ` (${conversation.length} in recent window)` : ""}</h3>${conversation.length ? conversation.map(messageText).join("") : '<p class="muted">No recorded messages for this object in the recent window.</p>'}`;
  if (!record)
    body =
      `<p class="notice">This object is outside the current recent list; its previously displayed snapshot is retained.</p>` +
      body;
  $("detail").innerHTML = body;
  $("drawer").hidden = false;
  $("shade").hidden = false;
}
function close() {
  $("drawer").hidden = true;
  $("shade").hidden = true;
  selected = null;
}
$("close").onclick = close;
$("shade").onclick = close;
$("all").onclick = () => {
  party = null;
  order = null;
  workspaceTab = "overview";
  close();
  render();
};
async function refresh() {
  if (busy) return;
  busy = true;
  try {
    const r = await fetch(
      "/api/state?" + new URLSearchParams({ order_filter: metricFilter }),
      { cache: "no-store" },
    );
    const data = await r.json();
    if (!r.ok) throw Error(data.error);
    state = data;
    render();
  } catch (e) {
    $("status").textContent = e.message + " · previous view retained";
  } finally {
    busy = false;
  }
}
async function post(path, args) {
  const r = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Simulator-Token": state.csrf,
    },
    body: JSON.stringify(args),
  });
  const data = await r.json();
  if (!r.ok) throw Error(data.error);
  return data;
}
$("compose").onclick = () => {
  if (!state) return;
  $("sender").innerHTML = state.parties
    .filter((p) => p.role !== "company")
    .map(
      (p) =>
        `<option value="${esc(p.id)}">${esc(p.name)} (${esc(p.role)})</option>`,
    )
    .join("");
  $("related").innerHTML =
    '<option value="">Email only / new order</option>' +
    state.orders
      .map(
        (o) =>
          `<option value="${esc(o.id)}">${esc(o.number)} — ${esc(name(o.party_id))}</option>`,
      )
      .join("");
  $("item").innerHTML = state.items
    .map((i) => `<option value="${esc(i.id)}">${esc(i.name)}</option>`)
    .join("");
  previewed = null;
  $("inject").disabled = true;
  $("preview").textContent = "";
  $("composer").showModal();
};
$("eventform").oninput = () => {
  previewed = null;
  $("inject").disabled = true;
};
$("eventform").onsubmit = async (e) => {
  e.preventDefault();
  const event = Object.fromEntries(new FormData(e.target));
  event.quantity = Number(event.quantity);
  event.document_id = event.document_id || null;
  try {
    const data = await post("/api/preview", { event });
    previewed = event;
    requestId = crypto.randomUUID();
    $("preview").textContent = JSON.stringify(data, null, 2);
    $("previewnote").textContent =
      data.kind === "order"
        ? "Releasing creates the stated order and its message."
        : "Releasing creates a simulated message; it does not change stock or finance.";
    $("inject").disabled = false;
  } catch (err) {
    $("previewnote").textContent = err.message;
  }
};
$("inject").onclick = async () => {
  if (!previewed) return;
  $("inject").disabled = true;
  try {
    await post("/api/inject", {
      event: previewed,
      request_id: requestId,
      confirmed: true,
    });
    $("composer").close();
    await refresh();
  } catch (e) {
    $("previewnote").textContent =
      e.message + " Use the same request identity when reconciling.";
  }
};
$("cancel").onclick = () => $("composer").close();
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") close();
});
refresh();
setInterval(refresh, 5000);
