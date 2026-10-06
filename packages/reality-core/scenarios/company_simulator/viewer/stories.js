let DATA,
  mode = "watch",
  runKey = "",
  generation = 0;
let day = 8,
  view = "customers",
  party = null,
  selected = null,
  tab = "story",
  timer = null;
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
const eur = (n) => `${esc(n)} €`,
  item = (s) => (s === "A" ? "mugs" : "bowls"),
  icon = (s) => (s === "A" ? "☕" : "🥣");
const names = {
  customer_order: ["🛒", "Order received"],
  partial_customer_dispatch: ["📦", "Part of the order shipped"],
  customer_dispatch: ["📦", "Dispatch recorded"],
  package_delivery: ["🏠", "Customer arrival recorded"],
  customer_cancellation: ["✋", "Customer asked to cancel"],
  cancel_commitment: ["✋", "Remaining order cancelled"],
  return_announcement: ["↩", "Return announced"],
  return_receipt: ["📥", "Returned item received"],
  customer_return: ["↩", "Customer reported a return"],
  sales_invoice: ["🧾", "Invoice recorded"],
  customer_payment: ["💶", "Customer payment recorded"],
  sales_credit: ["🧾", "Credit recorded"],
  customer_refund: ["💸", "Refund recorded"],
  delivery_failure: ["⚠", "Delivery failed; goods returned"],
  carrier_exception: ["⚠", "Carrier reported a delay"],
  purchase_order: ["🛒", "Purchase placed"],
  partial_supplier_receipt: ["📥", "Supplier goods received"],
  supplier_delay: ["⏳", "Supplier delay recorded"],
  supplier_invoice: ["🧾", "Supplier invoice recorded"],
  supplier_payment: ["💶", "Supplier payment recorded"],
  warehouse_transfer: ["🏭", "Stock moved between warehouses"],
  stock_adjustment: ["🔎", "Stock count adjustment"],
};
const cp = () => DATA.checkpoints.find((c) => c.day === day),
  events = () =>
    (DATA.snapshot.world_events || DATA.report.world_events || []).filter(
      (e) => e.day <= day,
    ),
  requests = () => DATA.snapshot.released.requests.filter((r) => r.day <= day);
const person = (label) => DATA.snapshot.parties.find((p) => p.label === label),
  line = (r) => cp().actual.lines[`${r.id}:${r.sku}`],
  belongs = (e, id) =>
    e.id === id ||
    e.id === `INV-${id}` ||
    e.id === `CR-${id}` ||
    e.id === `PINV-${id}` ||
    e.id === `PPAY-${id}` ||
    e.id?.startsWith(`PAY-${id}-`) ||
    e.id?.startsWith(`REF-${id}-`);
const messages = (id) =>
  DATA.messages.filter(
    (m) =>
      m.day <= day &&
      m.payload.thread_id === `${DATA.manifest.run_id}:thread:${id}`,
  );
function progress(r) {
  const l = line(r),
    f = cp().actual_finance.open_balances,
    ships = r.shipments.filter((s) => cp().actual_logistics.shipments[s.id]);
  return [
    true,
    Number(l?.fulfilled) > 0,
    ships.some((s) => cp().actual_logistics.shipments[s.id].delivered),
    Object.hasOwn(f, `INV-${r.id}`),
    Object.hasOwn(f, `INV-${r.id}`) && f[`INV-${r.id}`] === "0",
  ];
}
function status(r) {
  const l = line(r),
    p = progress(r);
  if (l?.status === "cancelled") return ["Cancelled", "gray"];
  if (p[2] && l?.open === "0") return ["Arrival recorded", ""];
  if (Number(l?.fulfilled) > 0) return ["On its way", ""];
  return ["Waiting for stock", "warn"];
}
function orderCard(r) {
  const s = status(r),
    p = progress(r);
  return `<button class="order" data-order="${esc(r.id)}"><div class="orderhead"><small>${esc(r.id)} · ${esc(person(r.customer).name.replace("Reference Retail ", ""))}</small><span class="tag ${s[1]}">${s[0]}</span></div><span class="item">${icon(r.sku)}</span><h3>${r.quantity} ${item(r.sku)}</h3><small>Stated order ${eur(r.amount)} · wanted by day ${r.deadline}</small><div class="dots">${p.map((x) => `<i class="${x ? "on" : ""}"></i>`).join("")}</div><small>${esc(line(r)?.fulfilled ?? 0)} shipped · ${messages(r.id).length} messages</small></button>`;
}
function storyEvents(id) {
  return events().filter((e) => belongs(e, id) && names[e.kind]);
}
function render() {
  const c = cp();
  $("day").textContent = `Day ${day} / ${DATA.manifest.days}`;
  $("scrub").max = DATA.manifest.days;
  $("scrub").value = day;
  const tiles = [
    [
      "customers",
      "👥",
      DATA.snapshot.parties.filter((p) => p.role === "customer").length,
      "Customers",
    ],
    ["sales", "🛒", c.actual.counts.sales_orders, "Sales"],
    ["suppliers", "🚚", c.actual.counts.purchase_orders, "Purchases"],
    [
      "stock",
      "📦",
      `${c.actual.physical.A} / ${c.actual.physical.B}`,
      "Mugs / bowls in stock",
    ],
    ["money", "💶", `${c.actual_finance.accounts.cash} €`, "Recorded cash"],
  ];
  $("tiles").innerHTML = tiles
    .map(
      (t) =>
        `<button class="tile ${view === t[0] ? "active" : ""}" data-view="${t[0]}"><span class="icon">${t[1]}</span><strong>${t[2]}</strong><small>${t[3]}</small></button>`,
    )
    .join("");
  let html = "";
  if (view === "customers") {
    html =
      '<div class="sectionhead"><h2>Your customers</h2><span class="muted">Pick a person to see their story</span></div><div class="people">' +
      DATA.snapshot.parties
        .filter((p) => p.role === "customer")
        .map((p, i) => {
          const rs = requests().filter((r) => r.customer === p.label);
          return `<button class="person" data-person="${esc(p.label)}"><span class="avatar">${i ? "👨🏻" : "👩🏻"}</span><div><strong>${esc(p.name.replace("Reference Retail ", "Retail "))}</strong><small>${rs.length} orders so far · ${rs.reduce((n, r) => n + messages(r.id).length, 0)} recorded messages</small></div><span class="person-arrow">↗</span></button>`;
        })
        .join("") +
      "</div>";
    const rs = requests().filter((r) => !party || r.customer === party);
    html += `<div class="sectionhead"><h2>${party ? esc(person(party).name.replace("Reference Retail ", "")) + "'s orders" : "Their orders"}</h2>${party ? '<button class="quiet" id="clear">All customers</button>' : ""}</div><div class="orders">${rs.map(orderCard).join("") || '<div class="empty">No orders released yet. Move to the next day.</div>'}</div>`;
  } else if (view === "sales") {
    html =
      '<div class="sectionhead"><h2>Every sale has a story</h2><span class="muted">Click a card to follow it</span></div><div class="orders">' +
      requests().map(orderCard).join("") +
      "</div>";
  } else if (view === "suppliers") {
    const purchases = DATA.snapshot.released.purchases.filter((p) =>
      Object.hasOwn(c.actual.lines, `${p.id}:${p.sku}`),
    );
    html =
      '<div class="sectionhead"><h2>Your supplier</h2></div><div class="card"><h2>🏭 Reference supplier</h2><p class="muted">Confirmations, delayed goods, partial deliveries and payments.</p></div><div class="sectionhead"><h2>What you bought</h2></div><div class="orders">' +
      purchases
        .map(
          (p) =>
            `<button class="order" data-order="${esc(p.id)}"><small>Purchase ${esc(p.id)}</small><div class="item">${icon(p.sku)}</div><h3>${p.quantity} ${item(p.sku)}</h3><small>${esc(c.actual.lines[`${p.id}:${p.sku}`].fulfilled)} received · ${messages(p.id).length} messages</small><p>Open the supplier story →</p></button>`,
        )
        .join("") +
      "</div>";
    if (!purchases.length)
      html += '<div class="empty">No purchase has been placed yet.</div>';
  } else if (view === "stock") {
    html =
      '<div class="sectionhead"><h2>Inside the warehouse</h2></div><div class="two">' +
      Object.entries(c.actual.locations)
        .map(
          ([loc, stock]) =>
            `<div class="card"><h2>🏭 ${esc(loc)}</h2><div class="row"><span>☕ Mugs</span><strong>${stock.A}</strong></div><div class="row"><span>🥣 Bowls</span><strong>${stock.B}</strong></div><p class="muted">Recorded stock at the end of day ${day}</p></div>`,
        )
        .join("") +
      "</div>";
  } else {
    html =
      '<div class="sectionhead"><h2>The money story</h2></div><div class="two"><div class="card"><h2>💶 Recorded balances</h2>' +
      [
        ["cash", "Cash"],
        ["accounts_receivable", "Customer receivables"],
        ["accounts_payable", "Supplier payable — signed ledger balance"],
      ]
        .map(
          ([k, label]) =>
            `<div class="row"><span>${label}</span><strong>${eur(c.actual_finance.accounts[k])}</strong></div>`,
        )
        .join("") +
      '</div><div class="card"><h2>🧾 Invoice & credit balances</h2>' +
      Object.entries(c.actual_finance.open_balances)
        .map(
          ([label, n]) =>
            `<div class="row"><span>${esc(label)}</span><strong>${eur(n)}</strong></div>`,
        )
        .join("") +
      "</div></div>";
  }
  const latest = events()
    .filter((e) => names[e.kind])
    .slice(-6)
    .reverse();
  html +=
    '<div class="sectionhead"><h2>Recently in your company</h2><span class="pill">' +
    (c.differences.length
      ? "Checkpoint differences recorded"
      : "✓ This day’s checkpoint passed") +
    '</span></div><div class="card feed">' +
    latest
      .map((e) => {
        const r = requests().find((r) => belongs(e, r.id));
        return `<div class="feedrow"><span class="daybadge">Day ${e.day}</span><span>${names[e.kind][0]}</span><div><strong>${names[e.kind][1]}</strong><br>${r ? `<button data-order="${esc(r.id)}">${r.quantity} ${item(r.sku)} for ${esc(person(r.customer).name.replace("Reference Retail ", ""))} →</button>` : `<span class="muted">${esc(e.id || e.source_event?.sku || "Warehouse")}</span>`}</div></div>`;
      })
      .join("") +
    "</div>";
  $("content").innerHTML = html;
  document.querySelectorAll("[data-view]").forEach(
    (b) =>
      (b.onclick = () => {
        view = b.dataset.view;
        party = null;
        render();
      }),
  );
  document.querySelectorAll("[data-person]").forEach(
    (b) =>
      (b.onclick = () => {
        party = b.dataset.person;
        render();
      }),
  );
  document
    .querySelectorAll("[data-order]")
    .forEach((b) => (b.onclick = () => open(b.dataset.order)));
  if ($("clear"))
    $("clear").onclick = () => {
      party = null;
      render();
    };
  if (selected) drawer();
}

let prepared, accepted;
function indexActions() {
  prepared = new Map(
    DATA.actions
      .filter((x) => x.phase === "prepared")
      .map((x) => [x.proposal_id, x]),
  );
  accepted = DATA.actions
    .filter((x) => x.phase === "committed")
    .map((x) => ({ ...x, input: prepared.get(x.proposal_id) }))
    .filter((x) => x.input);
}
function hasValue(obj, ids) {
  if (typeof obj === "string") return ids.has(obj);
  if (Array.isArray(obj)) return obj.some((x) => hasValue(x, ids));
  return obj && typeof obj === "object"
    ? Object.values(obj).some((x) => hasValue(x, ids))
    : false;
}
function recordRef(kind, id, label) {
  if (!id) return "";
  const q = new URLSearchParams({
    tenant: DATA.manifest.company_id,
    inspector_view: "records",
    inspector_record_kind: kind,
    entry: id,
  });
  const route = "/app/inspector?" + q;
  return `<div class="ref"><b>${esc(label)}</b><code>${esc(id)}</code><button data-copy="${esc(id)}">Copy ID</button> <button data-copy="${esc(route)}">Copy Reality path</button><div class="archived">Reality target unverified · copy path to inspect in your instance</div></div>`;
}
function orderInfo(obj) {
  const l = line(obj);
  return `<details class="evidence"><summary>ⓘ How this order exists in Reality</summary><p>Order source → document → document line → commitment. The commitment tracks the quantity promised and fulfilled.</p>${recordRef("source_record", l?.source_record_id, "Order source — created by order_create")}${recordRef("document", l?.document_id, "Document — the order")}${recordRef("document_line", l?.document_line_id, "Document line — this item and quantity")}${recordRef("commitment", l?.commitment_id, "Commitment — the delivery obligation")}<p>End of day ${day}: ${esc(l?.quantity)} ordered · ${esc(l?.fulfilled)} fulfilled · ${esc(l?.open)} open · ${esc(l?.reserved)} reserved.</p><p class="archived">Reality paths require the same retained company in your instance. Test runs may have been rolled back; this viewer does not verify record availability.</p></details>`;
}
const toolEffects = {
  order_create: "Creates the order document, its item lines and commitments.",
  reserve: "Reserves stock against the delivery commitment.",
  outbound_delivery_plan:
    "Records the intended recipient and delivery address.",
  shipment_dispatch: "Records dispatch and the linked inventory movements.",
  shipment_event_record: "Records carrier or arrival evidence.",
  movement_create: "Records a stock movement.",
  sales_invoice_record: "Records the customer invoice and its ledger postings.",
  customer_payment_post:
    "Records the customer payment and its ledger postings.",
};
function receiptRefs(r) {
  let html = "";
  for (const x of r.records || [])
    html += recordRef(x.family, x.id, x.family.replaceAll("_", " "));
  const one = {
    document_id: "document",
    source_record_id: "source_record",
    commitment_id: "commitment",
    reservation_id: "reservation",
    shipment_id: "shipment",
    package_id: "package",
    event_id: "event",
    notice_event_id: "shipment_event",
  };
  for (const [key, kind] of Object.entries(one))
    html += recordRef(kind, r[key], kind.replaceAll("_", " "));
  for (const [key, kind] of Object.entries({
    document_line_ids: "document_line",
    commitment_ids: "commitment",
    movement_ids: "movement",
    ledger_entry_ids: "ledger_entry",
  }))
    for (const id of r[key] || [])
      html += recordRef(kind, id, kind.replaceAll("_", " "));
  return html;
}
function eventInfo(e, obj) {
  const l = line(obj),
    ids = new Set(
      [
        l?.commitment_id,
        l?.document_id,
        l?.document_line_id,
        l?.source_record_id,
        ...(obj.shipments || []).map((x) => x.id),
        ...(e.ledger_entry_ids || []),
      ].filter(Boolean),
    );
  const rows = accepted.filter(
    (a) =>
      a.input.scenario_day === e.day &&
      (hasValue(a.input.arguments, ids) || hasValue(a.receipt, ids)),
  );
  const kinds = {
    customer_order: ["order_create"],
    purchase_order: ["order_create"],
    partial_customer_dispatch: [
      "reserve",
      "outbound_delivery_plan",
      "shipment_dispatch",
    ],
    customer_dispatch: [
      "reserve",
      "outbound_delivery_plan",
      "shipment_dispatch",
    ],
    package_delivery: ["shipment_event_record"],
  };
  const relevant = rows.filter(
    (a) => !kinds[e.kind] || kinds[e.kind].includes(a.tool),
  );
  return `<details class="evidence"><summary>ⓘ Reality evidence & effects</summary><p>Accepted actions linked by exact record IDs for this order on day ${e.day}. This groups the recorded actions; it does not assume one action per timeline entry.</p>${relevant.length ? relevant.map((a) => `<div class="operation"><strong>${esc(a.tool)}</strong><p>${esc(toolEffects[a.tool] || "Accepted Reality operation; exact input and receipt below.")}</p>${receiptRefs(a.receipt)}<details><summary>Exact accepted input & receipt</summary><pre>${esc(JSON.stringify({ proposal_id: a.proposal_id, input: a.input.arguments, receipt: a.receipt }, null, 2))}</pre></details></div>`).join("") : "<p>No accepted receipt with a direct record-ID match is available for this timeline entry.</p>"}</details>`;
}
function mailInfo(row) {
  return `<details class="evidence"><summary>ⓘ Source email in Reality</summary>${recordRef("source_record", row.source_record_id, "Source record — this simulated message")}<p>${row.direction === "outgoing" ? "Recorded local reply or unsent draft. No real email delivery is implied." : "Related scenario email. The order was created separately; this is not its canonical order source."}</p><div class="ref"><b>Message / conversation</b><code>${esc(row.payload.message_id)}</code><code>${esc(row.payload.thread_id)}</code></div></details>`;
}
function bindCopies() {
  document.querySelectorAll("[data-copy]").forEach(
    (b) =>
      (b.onclick = async () => {
        try {
          await navigator.clipboard.writeText(b.dataset.copy);
          b.textContent = "Copied";
        } catch {
          b.textContent = "Select ID above to copy";
        }
      }),
  );
}

function drawer() {
  const expanded = [...$("drawer").querySelectorAll("details")]
    .map((d, i) => (d.open ? i : -1))
    .filter((i) => i >= 0);
  const scroll = $("drawer").scrollTop;
  const r = requests().find((r) => r.id === selected),
    p = DATA.snapshot.released.purchases.find((p) => p.id === selected);
  if (!r && !Object.hasOwn(cp().actual.lines, `${p?.id}:${p?.sku}`)) {
    close();
    return;
  }
  const who = r ? person(r.customer) : person("SUPPLIER"),
    m = messages(selected),
    es = storyEvents(selected);
  let html = `<button class="close" id="close" aria-label="Close story">×</button><span class="pill">${r ? "Customer order" : "Supplier purchase"} ${esc(selected)}</span><h2>${r ? r.quantity : p.quantity} ${item((r || p).sku)} ${r ? "for" : "from"}<br>${esc(who.name.replace("Reference Retail ", "Retail "))}</h2>`;
  if (r) {
    html += `<p class="muted">Ordered day ${r.day} · wanted by day ${r.deadline}<br>Stated original order: ${eur(r.amount)}</p><div class="journey">${progress(
      r,
    )
      .map(
        (v, i) =>
          `<div class="step ${v ? "on" : ""}"><span>${["🛒", "📦", "🏠", "🧾", "💶"][i]}</span>${["Ordered", "Dispatch", "Arrival evidence", "Invoice", "Invoice settled"][i]}</div>`,
      )
      .join("")}</div>`;
    const g = (DATA.report.goals || []).find((g) => g.id === selected);
    if (day === DATA.manifest.days && g)
      html += `<div class="notice">Recorded delivery goal: <strong>${esc(g.status)}</strong> · ${g.delivered_on_time_correct_destination}/${g.required_after_cancellation} at the correct destination on time</div>`;
  }
  html += orderInfo(r || p);
  html += `<div class="tabs"><button id="storytab" class="${tab === "story" ? "active" : ""}">What happened</button><button id="mailtab" class="${tab === "messages" ? "active" : ""}">Messages (${m.length})</button></div>`;
  if (tab === "story") {
    html +=
      '<div class="story">' +
      es
        .map(
          (e) =>
            `<div class="event"><small>DAY ${e.day}</small><strong>${names[e.kind][0]} ${names[e.kind][1]}</strong>${e.kind === "customer_order" ? '<span class="muted">The customer’s stated quantity and delivery deadline arrive.</span>' : ""}${eventInfo(e, r || p)}</div>`,
        )
        .join("") +
      "</div>";
  } else {
    html += m
      .map((row) => {
        const v = row.payload,
          body = v.body;
        const text = typeof body === "string" ? body : body.text || "";
        const parent = DATA.messages.find(
          (x) => x.payload.message_id === v.in_reply_to,
        );
        return `<div class="message ${row.direction === "outgoing" ? "out" : ""}"><small>Day ${row.day} · ${row.direction === "outgoing" ? "🤖 Agent · " + (row.status === "proposed" ? "unsent draft" : "local simulated reply") : r ? "👤 Customer" : "🏭 Supplier"}</small><h4>${esc(v.subject)}</h4>${parent ? `<div class="reply">↩ ${esc(parent.payload.subject)}</div>` : ""}<p>${esc(text)}</p>${
          typeof body === "object" && body.observed
            ? `<small>Recorded status: ${Object.entries(body.observed)
                .map(
                  ([k, x]) =>
                    esc(k.replaceAll("_", " ")) +
                    ": " +
                    esc(x ?? "not recorded"),
                )
                .join(" · ")}</small>`
            : ""
        }${typeof body === "object" && body.revised_arrival_days ? `<p>Revised arrival days: ${body.revised_arrival_days.map(esc).join(", ")}</p>` : ""}${typeof body === "object" && body.quantity ? `<p>Stated quantity: ${esc(body.quantity)}</p>` : ""}${typeof body === "object" && body.accepted_event ? `<p>${esc(names[body.accepted_event.kind]?.[1] || body.accepted_event.kind)}</p>` : ""}${mailInfo(row)}</div>`;
      })
      .join("");
  }
  html += `<details><summary>Original recorded evidence</summary><pre>${esc(JSON.stringify({ checkpoint_day: day, order: cp().actual.lines[`${selected}:${(r || p).sku}`], events: es, messages: m }, null, 2))}</pre></details>`;
  $("drawer").innerHTML = html;
  expanded.forEach((i) => {
    const d = $("drawer").querySelectorAll("details")[i];
    if (d) d.open = true;
  });
  $("drawer").scrollTop = scroll;
  bindCopies();
  $("close").onclick = close;
  $("storytab").onclick = () => {
    tab = "story";
    drawer();
  };
  $("mailtab").onclick = () => {
    tab = "messages";
    drawer();
  };
}
function open(id) {
  selected = id;
  tab = "story";
  $("shade").hidden = false;
  $("drawer").hidden = false;
  drawer();
  $("close").focus();
}
function close() {
  selected = null;
  $("shade").hidden = true;
  $("drawer").hidden = true;
}
$("shade").onclick = close;
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") close();
});
function stop() {
  clearInterval(timer);
  timer = null;
  $("play").textContent = "▶ Play recording";
}
function days() {
  return DATA.checkpoints.map((x) => x.day).sort((a, b) => a - b);
}
function replayDay(n) {
  const available = days().filter((x) => x <= n);
  return available.length ? available.at(-1) : days()[0];
}
function setMode(next) {
  stop();
  mode = next;
  $("play").hidden = mode === "watch";
  $("next").hidden = mode === "watch";
  $("scrub").disabled = mode === "watch";
  $("watch").textContent = mode === "watch" ? "● Live watch" : "Live watch";
  if (DATA && days().length) {
    if (mode === "watch") day = days().at(-1);
    render();
  }
}
$("watch").onclick = () => setMode("watch");
$("replay").onclick = () => setMode("replay");
$("play").onclick = () => {
  if (!DATA) return;
  if (timer) {
    stop();
    return;
  }
  if (day === days().at(-1)) day = days()[0];
  $("play").textContent = "Ⅱ Pause replay";
  render();
  timer = setInterval(() => {
    const next = days().find((n) => n > day);
    if (next === undefined) {
      stop();
      return;
    }
    day = next;
    render();
  }, 1500);
};
$("next").onclick = () => {
  if (!DATA) return;
  stop();
  day = days().find((n) => n > day) ?? day;
  render();
};
$("scrub").oninput = (e) => {
  if (!DATA) return;
  stop();
  day = replayDay(Number(e.target.value));
  render();
};
async function refresh() {
  if (!runKey) return;
  const key = runKey,
    version = generation;
  try {
    const response = await fetch("/api/stories/" + key, { cache: "no-store" });
    if (!response.ok) throw Error("Artifacts unavailable; retrying");
    const incoming = await response.json();
    if (version !== generation || key !== runKey) return;
    if (!incoming.snapshot.released?.requests || !incoming.checkpoints.length) {
      $("observation").textContent =
        "Waiting for a complete company checkpoint. Other profiles: use original spectator at /.";
      return;
    }
    DATA = incoming;
    indexActions();
    const available = days();
    day = mode === "watch" ? available.at(-1) : replayDay(day);
    DATA.report.run_id = DATA.manifest.run_id;
    const stamp = DATA.snapshot.observed_at;
    $("observation").textContent =
      (DATA.report.run_id && DATA.report.world_events
        ? "Finished recording"
        : "No final report · process liveness unverified") +
      " · last observation " +
      (stamp || "unknown") +
      (DATA.notices.length ? " · " + DATA.notices.join(" · ") : "");
    render();
  } catch (error) {
    if (version === generation)
      $("observation").textContent =
        error.message + " · previous view retained";
  }
}
async function listRuns() {
  try {
    const response = await fetch("/api/runs", { cache: "no-store" });
    if (!response.ok) throw Error("Run list unavailable");
    const listing = await response.json();
    $("runs").innerHTML = listing.runs
      .map((r) => `<option value="${esc(r.key)}">${esc(r.key)}</option>`)
      .join("");
    if (listing.runs.some((r) => r.key === runKey)) $("runs").value = runKey;
    else if (listing.runs.length) {
      runKey = listing.runs[0].key;
      generation++;
    } else
      $("observation").textContent =
        "No runs yet. Start the simulator with its CLI script.";
  } catch (error) {
    $("observation").textContent = error.message;
  }
}
$("runs").onchange = () => {
  generation++;
  runKey = $("runs").value;
  stop();
  close();
  party = null;
  DATA = null;
  $("content").innerHTML = "";
  $("tiles").innerHTML = "";
  refresh();
};
setMode("watch");
(async () => {
  await listRuns();
  await refresh();
})();
let polling = false;
setInterval(async () => {
  if (polling) return;
  polling = true;
  try {
    await listRuns();
    await refresh();
  } finally {
    polling = false;
  }
}, 5000);
