// Real API only. Failures remain samples; cold browser caches do not imply cold database caches.
import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
if (!process.env.PLAYWRIGHT_MODULE || !process.env.SEARCH_BENCHMARK_MANIFEST)
  throw Error("Set PLAYWRIGHT_MODULE and SEARCH_BENCHMARK_MANIFEST.");
const manifest = JSON.parse(await readFile(process.env.SEARCH_BENCHMARK_MANIFEST, "utf8"));
assert.equal(manifest.tenant, "search_benchmark");
assert(manifest.users.length >= 10);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5235";
assert(
  ["127.0.0.1", "localhost"].includes(new URL(base).hostname),
  "Use only the disposable local benchmark host.",
);
const observations = Number(process.env.SEARCH_BENCHMARK_OBSERVATIONS || 100);
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const counts = manifest.counts;
const number = (value) => String(value).padStart(6, "0");
const cases = [
  {
    name: "partner_exact",
    query: `PARTNER-${number(counts.party - 1)}`,
    key: `party:bench_party_${number(counts.party - 1)}`,
  },
  {
    name: "item_exact",
    query: `SKU-${number(counts.item - 1)}`,
    key: `item:bench_item_${number(counts.item - 1)}`,
  },
  { name: "item_prefix", query: "Warehouse", prefix: "item:" },
  { name: "item_typo", query: "warehose", prefix: "item:" },
  { name: "partner_diacritic", query: "Muller", prefix: "party:" },
  {
    name: "order_exact",
    query: `CUSTOMER_ORDER-${number(counts.customer_order - 1)}`,
    key: `document:bench_customer_order_${number(counts.customer_order - 1)}`,
  },
  {
    name: "invoice_exact",
    query: `CUSTOMER_INVOICE-${number(counts.customer_invoice - 1)}`,
    key: `document:bench_customer_invoice_${number(counts.customer_invoice - 1)}`,
  },
  {
    name: "payment_exact",
    query: `bench_payment_${number(counts.payment - 1)}`,
    key: `ledger_entry:bench_payment_${number(counts.payment - 1)}`,
  },
  {
    name: "tracking_exact",
    query: `TRACK-${number(counts.shipment - 1)}`,
    key: `shipment:bench_shipment_${number(counts.shipment - 1)}`,
  },
  { name: "source_versions", query: "EXTERNAL-000000", prefix: "source_record:" },
  {
    name: "reality_exact",
    query: `bench_fact_${number(counts.fact - 1)}`,
    key: `fact:bench_fact_${number(counts.fact - 1)}`,
  },
  { name: "private_reports", query: "Warehouse", prefix: "analytics_report:", filter: "Reports" },
  { name: "static_page", query: "Warehouse", key: "page:warehouse", filter: "Pages" },
];
const samples = [];
async function session(user) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await context.addCookies([
    { name: "reality_session", value: user.token, url: base, httpOnly: true, sameSite: "Lax" },
  ]);
  const page = await context.newPage();
  const cdp = await context.newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 100,
    downloadThroughput: -1,
    uploadThroughput: -1,
  });
  await page.goto(`${base}/app/inspector?tenant=${manifest.tenant}&inspector_view=commands`);
  await page.locator("[data-tool-catalog]").waitFor({ timeout: 30000 });
  return { context, page };
}
async function measure(page, test, regime, user) {
  const row = { case: test.name, regime, user, opening_ms: null, result_ms: null, error: null };
  const palette = page.locator("[data-action-menu]:popover-open");
  try {
    const opening = performance.now();
    await page.keyboard.press("Control+k");
    await palette.getByRole("combobox").waitFor({ timeout: 5000 });
    row.opening_ms = performance.now() - opening;
    await palette.getByRole("button", { name: test.filter || "All", exact: true }).click();
    const started = performance.now();
    await palette
      .getByRole("combobox")
      .fill(test.name === "private_reports" ? `bench_private_report_${number(user)}` : test.query);
    const selector = test.key
      ? `[data-palette-key="${test.key}"]`
      : `[data-palette-key^="${test.prefix}"]`;
    await palette.locator(selector).first().waitFor({ timeout: 7000 });
    row.result_ms = performance.now() - started;
    if (test.name !== "static_page") {
      await page.waitForFunction(
        () => !document.querySelector("[data-action-menu]:popover-open [data-search-loading]"),
        {},
        { timeout: 7000 },
      );
      const errors = await palette
        .getByText("Search is temporarily unavailable. Please retry.", { exact: false })
        .count();
      if (errors) row.error = "Provider failure";
    }
  } catch (error) {
    row.error = String(error.message).slice(0, 240);
  } finally {
    await page.keyboard.press("Escape");
    samples.push(row);
  }
}
try {
  for (const regime of ["cold_browser", "warm"]) {
    let next = 0;
    const work = Array.from({ length: 10 }, async (_, worker) => {
      let current = null;
      try {
        while (next < observations * cases.length) {
          const index = next++,
            test = cases[index % cases.length];
          try {
            if (!current) current = await session(manifest.users[worker]);
            await measure(current.page, test, regime, worker);
          } catch (error) {
            samples.push({
              case: test.name,
              regime,
              user: worker,
              opening_ms: null,
              result_ms: null,
              error: `Session setup: ${String(error.message).slice(0, 200)}`,
            });
          }
          if (regime === "cold_browser" && current) {
            await current.context.close();
            current = null;
          }
        }
      } finally {
        await current?.context.close();
      }
    });
    await Promise.all(work);
  }
} finally {
  await browser.close();
}
const percentile = (values, fraction) =>
  values.length ? values.sort((a, b) => a - b)[Math.ceil(values.length * fraction) - 1] : null;
const summaries = [];
for (const regime of ["cold_browser", "warm"])
  for (const test of cases) {
    const rows = samples.filter((row) => row.case === test.name && row.regime === regime);
    const durations = rows.map((row) => row.result_ms ?? 7000);
    const opening = rows.map((row) => row.opening_ms ?? 5000);
    summaries.push({
      regime,
      case: test.name,
      observations: rows.length,
      failures: rows.filter((row) => row.error).length,
      p50_ms: percentile(durations, 0.5),
      p95_ms: percentile(durations, 0.95),
      max_ms: Math.max(...durations),
      opening_p95_ms: percentile(opening, 0.95),
      budget_ms: test.name === "static_page" ? 300 : 1500,
    });
  }
const output =
  process.env.SEARCH_BENCHMARK_OUTPUT || "/private/tmp/reality-235-browser-performance.json";
const pass = summaries.every(
  (row) => !row.failures && row.p95_ms <= row.budget_ms && row.opening_p95_ms <= 200,
);
await writeFile(
  output,
  JSON.stringify(
    {
      records: manifest.records,
      users: 10,
      rtt_ms: 100,
      observations,
      cache_method:
        "cold_browser recreates browser contexts. Database and OS caches are not cleared; this is not controlled cold-database acceptance.",
      budgets_pass: pass,
      full_acceptance: false,
      summaries,
      samples,
    },
    null,
    2,
  ),
);
console.log(
  JSON.stringify({ output, budgets_pass: pass, samples: samples.length, full_acceptance: false }),
);
if (!pass) process.exitCode = 1;
