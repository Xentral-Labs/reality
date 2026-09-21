// Read-only HTTP fixtures; canonical financial semantics remain covered by PostgreSQL tests.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const requests = [],
  errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en",
  fail = false;
let projectionState = "ready";
const tenant = "finance_fixture";
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    url = new URL(req.url()),
    path = url.pathname;
  requests.push({ path, method: req.method(), query: url.search });
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: tenant, name: "Northstar Commerce" },
        { id: "other", name: "Other company" },
      ],
      default_tenant_id: tenant,
    });
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  if (path.includes("/finance/")) {
    if (fail) return reply({ detail: "Finance unavailable" }, 503);
    const view = path.split("/finance/")[1],
      n = Number(url.searchParams.get("page") || 1),
      empty = url.searchParams.get("q") === "missing";
    const pager = {
      number: n,
      size: 50,
      total: empty ? 0 : 51,
      pages: empty ? 1 : 2,
      has_previous: n > 1,
      has_next: !empty && n === 1,
    };
    const item = {
      document_id: `invoice_${n}`,
      number: `INV-${n}`,
      document_type:
        url.searchParams.get("flow") === "payable" ? "supplier_invoice" : "sales_invoice",
      document_date: "2026-09-07",
      party: "Schneider",
      party_id: "party_1",
      gross: "600",
      settled: "200",
      open: "400",
      currency: "EUR",
      status: "partial",
    };
    const payment = {
      id: `payment_${n}`,
      effective_at: "2026-09-07T10:00:00Z",
      direction: "incoming",
      document_id: "payment_doc",
      reference: "PAY-1",
      party: "Schneider",
      currency: "EUR",
      amount: "200",
      allocated: "0",
      unallocated: "0",
      posting_group_id: "posting_1",
      reversal_role: "reversed_original",
    };
    const journal = {
      id: `ledger_${n}`,
      effective_at: "2026-09-07T10:00:00Z",
      account: "cash",
      debit_credit: "debit",
      amount: "200",
      currency: "EUR",
      posting_group_id: "posting_1",
      document_id: "payment_doc",
      inspect_kind: "ledger_entry",
      inspect_id: `ledger_${n}`,
    };
    if (url.searchParams.get("flow")?.endsWith("-balances"))
      return reply({
        side: url.searchParams.get("flow").split("-")[0],
        as_of: "2026-09-07T10:00:00Z",
        items: [
          {
            party_id: "party_1",
            party: "Schneider",
            currency: "EUR",
            open: "400",
            overdue: "150",
            credit: "20",
            balance: "380",
            open_count: 2,
            credit_count: 1,
            oldest_due_date: "2026-08-15",
          },
        ],
        totals: [{ currency: "EUR", open: "400", overdue: "150", credit: "20", balance: "380" }],
        page: { ...pager, total: 1, pages: 1, has_next: false },
      });
    return reply({
      ...(view === "open-items"
        ? {
            metadata: {
              projection: "open_financial_items",
              calculation_mode: "stored",
              state: projectionState,
              completed_at: projectionState === "uninitialized" ? null : "2026-09-12T10:00:00Z",
              processed_event_sequence: projectionState === "uninitialized" ? null : 10,
              target_event_sequence: projectionState === "ready" ? 10 : 11,
              projection_version: 4,
              upstream_freshness: "unknown",
              consistency: "completed_snapshot",
            },
          }
        : {}),
      items:
        empty || projectionState === "uninitialized"
          ? []
          : [view === "open-items" ? item : view === "payments" ? payment : journal],
      page: pager,
      totals:
        empty || projectionState === "uninitialized"
          ? []
          : view === "open-items"
            ? [
                { currency: "EUR", gross: "30600", settled: "10200", open: "20400" },
                { currency: "USD", gross: "100", settled: "0", open: "100" },
              ]
            : view === "journal"
              ? [
                  { currency: "EUR", debit: "10200", credit: "0", balance: "10200" },
                  { currency: "USD", debit: "100", credit: "100", balance: "0" },
                ]
              : [{ currency: "EUR", amount: "999999", allocated: "0", unallocated: "999999" }],
    });
  }
  if (path.includes("/inspector/"))
    return reply({
      title: "Financial evidence",
      subtitle: "Schneider",
      meaning: "Recorded values",
      sections: [],
      technical_rows: [],
      source_payload: '{"untrusted":"<script>alert(1)</script>"}',
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177",
  out = "/private/tmp/reality-110-browser";
await mkdir(out, { recursive: true });
try {
  await page.goto(`${base}/app/finance?tenant=${tenant}`);
  await page.locator("[data-page-introduction] h1").waitFor();
  await page.locator("tbody tr").waitFor();
  assert.ok(
    requests.some(
      (r) => r.query.includes("flow=receivable") && r.query.includes("item_status=outstanding"),
    ),
  );
  for (projectionState of ["pending", "failed", "uninitialized", "ready"]) {
    await page.locator("[data-projection-freshness] button").click();
    await page.locator(`[data-projection-freshness="${projectionState}"]`).waitFor();
    if (projectionState === "uninitialized") {
      assert.equal(await page.locator("tbody tr").count(), 0);
      assert.equal(
        await page.getByRole("heading", { name: "No matching records", exact: true }).count(),
        0,
      );
      assert.equal(await page.locator("[data-finance-controls]").count(), 0);
    } else {
      await page.getByText("INV-1", { exact: true }).waitFor();
    }
  }
  const hideChat = page.getByRole("button", { name: "Hide chat", exact: true }).first();
  if (await hideChat.isVisible()) await hideChat.click();
  // Shared notices align with register content, including wrapped mobile states.
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (projectionState of ["ready", "pending", "failed", "uninitialized"]) {
      await page.locator("[data-projection-freshness] button").click();
      const notice = page.locator(`[data-projection-freshness="${projectionState}"]`);
      await notice.waitFor();
      const dimensions = await notice.evaluate((node) => {
        const card = node.closest(".register-surface");
        const a = node.getBoundingClientRect(),
          b = card.getBoundingClientRect();
        const style = getComputedStyle(card);
        return {
          left: a.left - b.left - parseFloat(style.borderLeftWidth),
          right: b.right - a.right - parseFloat(style.borderRightWidth),
          overflow: node.scrollWidth > node.clientWidth,
          paddingLeft: parseFloat(getComputedStyle(node).paddingLeft),
          borderRadius: parseFloat(getComputedStyle(node).borderTopLeftRadius),
        };
      });
      assert.ok(Math.abs(dimensions.left - 16) < 1, JSON.stringify(dimensions));
      assert.ok(Math.abs(dimensions.right - 16) < 1, JSON.stringify(dimensions));
      assert.equal(dimensions.overflow, false);
      if (projectionState !== "ready") {
        assert.ok(dimensions.paddingLeft >= 12, JSON.stringify(dimensions));
        assert.ok(dimensions.borderRadius >= 8, JSON.stringify(dimensions));
      }
    }
  }
  // Already-padded and standalone contexts must not gain a second outer inset.
  const margins = await page.locator("[data-projection-freshness]").evaluate((node) => {
    const parent = node.parentNode,
      next = node.nextSibling;
    const wrapper = document.createElement("div");
    wrapper.style.padding = "16px";
    parent.insertBefore(wrapper, node);
    wrapper.append(node);
    const nested = getComputedStyle(node).marginLeft;
    document.body.append(wrapper);
    const standalone = getComputedStyle(node).marginLeft;
    parent.insertBefore(node, next);
    wrapper.remove();
    return { nested, standalone };
  });
  assert.deepEqual(margins, { nested: "0px", standalone: "0px" });
  await page.setViewportSize({ width: 1440, height: 1000 });
  projectionState = "ready";
  await page.locator("[data-projection-freshness] button").click();
  await page.locator('[data-projection-freshness="ready"]').waitFor();
  if (process.env.NOTICE_SPACING_ONLY) {
    assert.deepEqual(errors, []);
    assert.equal(requests.filter((r) => r.method !== "GET").length, 0);
    console.log(
      "Notice spacing: desktop/mobile, four states, nested/standalone and refresh passed.",
    );
    await browser.close();
    process.exit(0);
  }
  const totals = await page.locator("[data-finance-controls]").innerText();
  assert.ok(totals.includes("EUR") && totals.includes("USD"));
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByText("INV-2", { exact: true }).waitFor();
  assert.equal(await page.locator("[data-finance-controls]").innerText(), totals);
  await page.getByRole("combobox", { name: "Flow", exact: true }).selectOption("payable");
  await page.getByText("INV-1", { exact: true }).waitFor();
  await page.getByRole("combobox", { name: "Status", exact: true }).selectOption("paid");
  await page.reload();
  assert.equal(
    await page.getByRole("combobox", { name: "Status", exact: true }).inputValue(),
    "paid",
  );
  const inspect = page
    .locator("tbody")
    .getByRole("button", { name: /[Pp]review/ })
    .first();
  await inspect.focus();
  await page.keyboard.press("Enter");
  await page.locator("[data-inline-preview]").waitFor();
  assert.equal(await page.getByRole("dialog").count(), 0);
  await inspect.click();
  await page.locator("[data-inline-preview]").waitFor({ state: "hidden" });
  await inspect.click();
  await page.reload();
  await page.locator("[data-inline-preview]").waitFor();
  for (const [view, label] of [
    ["payments", "Payments"],
    ["journal", "Journal"],
  ]) {
    await page.getByRole("button", { name: label, exact: true }).click();
    await page.locator("tbody tr").waitFor();
    await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes(`/finance/${view}?`) && r.url().includes("page=2"),
      ),
      page.getByRole("button", { name: "Next", exact: true }).click(),
    ]);
    await page
      .locator("tbody")
      .getByRole("button", { name: /[Pp]review/ })
      .first()
      .click();
    await page.locator("[data-inline-preview]").waitFor();
    assert.ok(page.url().includes(view === "payments" ? "entry=payment_2" : "entry=ledger_2"));
    await page
      .locator("tbody")
      .getByRole("button", { name: /Close preview/ })
      .first()
      .click();
    if (view === "payments") {
      assert.equal(await page.locator("[data-finance-controls]").count(), 0);
      await page.getByText("Reversed original", { exact: true }).waitFor();
    }
  }
  await page.locator("tbody").getByRole("button", { name: "cash", exact: true }).click();
  assert.ok(page.url().includes("account=cash"));
  await page.getByRole("textbox", { name: "Search finance", exact: true }).fill("missing");
  await page.getByRole("heading", { name: "No matching records", exact: true }).waitFor();
  fail = true;
  await page.reload();
  await page.getByRole("alert").waitFor();
  fail = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.getByRole("heading", { name: "No matching records", exact: true }).waitFor();
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator('[data-company-option="other"]:visible').first().click();
  assert.equal(new URL(page.url()).searchParams.has("account"), false);
  assert.equal(new URL(page.url()).searchParams.has("entry"), false);
  for (language of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
        await page.evaluate((theme) => localStorage.setItem("reality.theme", theme), theme);
        for (const view of ["open-items", "payments", "journal"]) {
          await page.goto(
            `${base}/app/finance?tenant=${tenant}&finance_view=${view}&lang=${language}`,
          );
          await page.locator("tbody tr").waitFor();
          const numeric =
            view === "open-items" ? [2, 3, 4] : view === "payments" ? [2, 3, 4] : [2, 3];
          const alignment = await page
            .locator("tbody tr")
            .first()
            .locator("td:not(.erp-select-cell)")
            .evaluateAll((cells) => cells.map((cell) => getComputedStyle(cell).textAlign));
          assert.ok(
            numeric.every((index) => alignment[index] === "right"),
            `${view}: numeric alignment`,
          );
          if (view === "payments")
            assert.equal(
              await page
                .locator("thead th")
                .filter({
                  hasText: language === "de" ? "Status" : language === "es" ? "Estado" : "Status",
                })
                .count(),
              1,
            );

          assert.ok(
            await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            `${language}/${theme}/${width}/${view}`,
          );
          await page.screenshot({
            path: `${out}/${language}-${theme}-${width}-${view}.png`,
            fullPage: true,
          });
        }
      }
  // Feature 170: party balances with drill-down into the party's open items and credits.
  language = "en";
  await page.goto(`${base}/app/finance?tenant=${tenant}&finance_view=balances&lang=en`);
  await page.locator("[data-party-balance]").waitFor();
  assert.ok(requests.some((r) => r.query.includes("flow=customer-balances")));
  const balances = await page.locator("[data-finance-controls]").innerText();
  assert.ok(balances.includes("380") && balances.includes("150"));
  await page.getByLabel("Side").selectOption("supplier");
  await page.waitForFunction(() => location.search.includes("balance_side=supplier"));
  assert.ok(requests.some((r) => r.query.includes("flow=supplier-balances")));
  await page.getByLabel("Credit only").check();
  await page.waitForFunction(() => location.search.includes("credit_only=1"));
  assert.ok(requests.some((r) => r.query.includes("credit_only=true")));
  await page.getByRole("button", { name: "Open items", exact: true }).last().click();
  await page.waitForFunction(() => location.search.includes("party_id=party_1"));
  assert.ok(page.url().includes("finance_view=open-items") && page.url().includes("flow=payable"));
  assert.ok(requests.some((r) => r.query.includes("party_id=party_1")));
  await page.getByRole("button", { name: "All parties", exact: true }).click();
  await page.waitForFunction(() => !location.search.includes("party_id"));
  assert.equal(requests.filter((r) => r.method !== "GET").length, 0);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: three finance tabs, complete currency controls, paging, filters, inline preview reload, company reset, retry, no writes and 48 localized screenshots.",
  );
} finally {
  await browser.close();
}
