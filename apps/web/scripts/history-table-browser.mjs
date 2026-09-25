// Spec 269: the History register reads by business names, against a real API.
// Needs an API with an owner owner@example.test and a company (TENANT) that has
// recorded at least one item; see specs/269-history-table/spec.md.
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const BASE = process.env.HISTORY_BASE_URL || "http://127.0.0.1:5269";
const TENANT = process.env.TENANT;
const results = [];
const check = (name, ok, detail = "") => {
  results.push({ name, ok });
  console.log(`${ok ? "PASS" : "FAIL"} ${name}${detail ? ` — ${detail}` : ""}`);
};
const browser = await chromium.launch();
for (const [scheme, width] of [
  ["dark", 1320],
  ["light", 390],
]) {
  const context = await browser.newContext({
    colorScheme: scheme,
    viewport: { width, height: 900 },
  });
  await context.request.post(`${BASE}/api/auth/login`, {
    data: { email: "owner@example.test", password: "a-long-account-password" },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  await page.goto(`${BASE}/app/inspector?tenant=${TENANT}&inspector_view=history&hours=0`);
  await page.waitForSelector("[data-activity-event]", { timeout: 15000 });
  if (scheme === "dark") {
    const records = await page.locator("[data-history-record]").allInnerTexts();
    check(
      "rows name records, never raw ids",
      records.every((text) => !/^[a-z]+_[0-9a-f]{8,}$/.test(text.trim())),
      records.slice(0, 4).join(" | "),
    );
    check(
      "an item reads by its SKU",
      records.some((text) => text.includes("LAMP-")),
      "",
    );
    const row = page.locator("[data-activity-event]").first();
    check(
      "event type as the title tooltip",
      (await row.locator("td span[title*='.']").count()) >= 1,
    );
    check("area chip", (await page.locator("[data-history-area]").count()) > 0);
    check(
      "completed rows carry no status badge",
      (await page.locator('[data-history-status="completed"]').count()) === 0,
    );
    check(
      "no decision line in rows",
      (await page.locator("[data-activity-event] [data-activity-decision]").count()) === 0,
    );
    const layout = () =>
      page.evaluate(() => {
        const table = document.querySelector("[data-table-id='inspector:history'] table");
        const cells = [...table.querySelectorAll("thead th")];
        return {
          filler: table.querySelectorAll(".erp-fill").length,
          event: cells[1].getBoundingClientRect().width,
          record: cells[2].getBoundingClientRect().width,
          overflow: table.scrollWidth - table.parentElement.clientWidth,
        };
      });
    // Beside the open chat dock at 1200px the register has about 600px.
    await page.setViewportSize({ width: 1200, height: 900 });
    await page.waitForTimeout(300);
    const narrow = await layout();
    check(
      "no filler column, minimum widths hold",
      narrow.filler === 0 && narrow.event >= 107 && narrow.record >= 111 && narrow.overflow <= 0,
      `event ${Math.round(narrow.event)}px, record ${Math.round(narrow.record)}px, overflow ${narrow.overflow}px`,
    );
    await page.setViewportSize({ width: 1800, height: 900 });
    await page.waitForTimeout(300);
    const wide = await layout();
    check(
      "spare width goes to event, record and area",
      wide.event > narrow.event + 40 && wide.record > narrow.record + 40 && wide.overflow <= 0,
      `event ${Math.round(wide.event)}px, record ${Math.round(wide.record)}px`,
    );
    await page.setViewportSize({ width, height: 900 });
    await row.locator("button[aria-controls^='history-preview-']").click();
    const details = await page.locator("[data-history-details]").first().innerText();
    check(
      "preview shows ids and actions",
      /evt_/.test(details) && details.includes("Inspect event"),
      "",
    );
    await page.screenshot({ path: `${process.env.SHOTS || "/tmp"}/history-${scheme}.png` });
  } else {
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    check("no horizontal page overflow at 390px", overflow <= 0, `${overflow}px`);
    await page.screenshot({
      path: `${process.env.SHOTS || "/tmp"}/history-${scheme}.png`,
      fullPage: true,
    });
  }
  check(`no console errors (${scheme})`, errors.length === 0, errors.slice(0, 2).join(" | "));
  await context.close();
}
await browser.close();
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exitCode = failed.length ? 1 : 0;
