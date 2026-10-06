// Local browser contract proof. No database or npm install required.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { appendFile, cp, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "/opt/codex/runtimes/cua/lib/node_modules/playwright-core");
const repository = fileURLToPath(new URL("../../../../../", import.meta.url));
const core = path.join(repository, "packages/reality-core");
const temporary = await mkdtemp(path.join(tmpdir(), "simulator-viewer-"));
const output = path.join(repository, "artifacts/company_simulator/viewer");
await mkdir(output, { recursive: true });
const write = (name, value) => writeFile(path.join(temporary, name), JSON.stringify(value) + "\n");
await mkdir(path.join(temporary, "live"));
await mkdir(path.join(temporary, "other"));
await write("live/manifest.json", { run_id: "browser-live-fixture", profile_id: "Browser fixture", days: 30, operator: "fixture" });
await write("other/manifest.json", { run_id: "browser-other-fixture", profile_id: "Other fixture", days: 30, operator: "fixture" });
await write("live/spectator.json", { run_id: "browser-live-fixture", day: 2, run_state: "unfinished", core_status: "passed_at_checkpoint", parties: [{ id: "customer", name: "North customer", role: "customer" }, { id: "supplier", name: "Cup supplier", role: "supplier" }], world_events: [{ day: 2, kind: "purchase_order", party_id: "supplier", id: "P001" }], coverage: { planned: ["purchase_order", "return_receipt"], exercised: ["purchase_order"], not_exercised: ["return_receipt"] } });
await write("live/checkpoints.jsonl", { day: 2, recorded_at: "2026-10-05T10:00:00Z", actual: { physical: { A: "6" } }, differences: [] });
const hostile = '<img src=x onerror="window.viewerInjection=true">';
await write("live/messages.jsonl", { day: 2, party_id: "customer", direction: "incoming", status: "received", payload: { from: "customer@example.invalid", to: "company@example.invalid", subject: "First order", body: hostile } });
let retained = false, correspondenceMonth = false;
try {
  await cp(process.env.SIMULATOR_RETAINED_RUN || path.join(repository, "artifacts/company_simulator/complete_acceptance/prompt"), path.join(temporary, "retained/prompt"), { recursive: true });
  const manifest = JSON.parse(await readFile(path.join(temporary, "retained/prompt/manifest.json"), "utf8"));
  correspondenceMonth = manifest.profile_id === "general_company_complete_v2";
  retained = true;
} catch { /* Optional saved acceptance artifact; synthetic browser proof is standalone. */ }
const server = spawn(path.join(repository, ".venv/bin/python"), ["-m", "scenarios.company_simulator.viewer", "--root", temporary, "--port", "0"], { cwd: core, stdio: ["ignore", "pipe", "pipe"] });
let log = "";
server.stderr.on("data", (chunk) => { log += chunk; });
const url = await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error("Viewer startup timed out")), 10000);
  server.once("exit", (code) => { clearTimeout(timer); reject(new Error(`Viewer exited ${code}: ${log}`)); });
  server.stdout.on("data", (chunk) => { const match = String(chunk).match(/http:\/\/127\.0\.0\.1:\d+/); if (match) { clearTimeout(timer); resolve(match[0]); } });
});
let browser;
try {
  browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_EXECUTABLE || "/usr/bin/chromium", headless: true, args: ["--no-sandbox"] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(url);
  await page.locator("#activity-heading").waitFor();
  await page.waitForFunction(() => document.querySelector("#status").textContent.includes("Day 2"));
  await page.getByRole("button", { name: "Customers", exact: true }).click();
  await page.locator("#party").selectOption("customer");
  assert.equal(await page.locator(".entry.message").count(), 1);
  assert.match(await page.locator(".message-body").innerText(), /<img/);
  assert.equal(await page.locator(".message-body img").count(), 0);
  assert.equal(await page.evaluate(() => window.viewerInjection), undefined);
  await page.getByRole("button", { name: "Suppliers", exact: true }).click();
  assert.equal(await page.locator(".entry.message").count(), 0);
  assert.match(await page.locator("#activity").innerText(), /Purchase order placed/);
  assert.match(await page.locator("#view-note").innerText(), /No messages recorded/);
  await appendFile(path.join(temporary, "live/messages.jsonl"), JSON.stringify({ day: 3, party_id: "supplier", direction: "incoming", status: "received", payload: { message_id: "supplier-confirmation", subject: "Purchase confirmation", body: { text: "We confirm the purchase." } } }) + "\n");
  await appendFile(path.join(temporary, "live/messages.jsonl"), JSON.stringify({ day: 3, party_id: "supplier", direction: "outgoing", status: "simulated", payload: { in_reply_to: "supplier-confirmation", subject: "Re: Purchase confirmation", body: { text: "Thank you for the confirmation." }, transport: "local_simulation" } }) + "\n");
  await page.waitForFunction(() => document.querySelectorAll(".entry.message").length === 2, null, { timeout: 10000 });
  assert.match(await page.locator("#activity").innerText(), /Simulated locally · no real email sent/);
  assert.match(await page.locator("#activity").innerText(), /Reply to: Purchase confirmation/);
  assert.match(await page.locator("#activity").innerText(), /We confirm the purchase/);
  await page.screenshot({ path: path.join(output, "supplier-correspondence.png"), fullPage: false });
  await page.getByRole("button", { name: "Customers", exact: true }).click();
  await page.locator("#party").selectOption("customer");
  await appendFile(path.join(temporary, "live/messages.jsonl"), JSON.stringify({ day: 3, party_id: "customer", direction: "outgoing", status: "proposed", payload: { subject: "Proposed reply", body: "Exact draft, not sent." } }) + "\n");
  await page.waitForFunction(() => document.querySelectorAll(".entry.message").length === 2, null, { timeout: 10000 });
  assert.equal(await page.locator("#party").inputValue(), "customer");
  assert.match(await page.locator("#activity").innerText(), /outgoing · Reply draft · not sent/);
  await appendFile(path.join(temporary, "live/messages.jsonl"), '{"day":4');
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await page.waitForFunction(() => document.querySelector("#notice").textContent.includes("incomplete"));
  assert.equal(await page.locator(".entry.message").count(), 2);
  await page.locator("#run").selectOption("other");
  await page.waitForFunction(() => document.querySelector("#status").textContent.includes("Not checked"));
  assert.equal(await page.locator(".entry.message").count(), 0);
  if (retained) {
    await page.locator("#run").selectOption("retained/prompt");
    await page.getByRole("button", { name: "Company timeline", exact: true }).click();
    await page.waitForFunction(() => document.querySelector("#status").textContent.includes("Day 30"));
    assert.equal(await page.locator(".entry.message").count(), correspondenceMonth ? 106 : 10);
    assert.match(await page.locator("#insights").innerText(), /190 EUR/);
    assert.match(await page.locator("#status").innerText(), correspondenceMonth ? /28 \/ 28/ : /22 \/ 22/);
    await page.screenshot({ path: path.join(output, "company-desktop.png"), fullPage: false });
    await page.getByRole("button", { name: "Customers", exact: true }).click();
    assert.equal(await page.locator(".entry.message").count(), correspondenceMonth ? 74 : 10);
    const options = await page.locator("#party option").allTextContents();
    assert(options.includes("Reference Retail North"));
    await page.locator("#party").selectOption({ label: "Reference Retail North" });
    assert.equal(await page.locator(".entry.message").count(), correspondenceMonth ? 37 : 5);
    await page.screenshot({ path: path.join(output, "customer-desktop.png"), fullPage: false });
    await page.getByRole("button", { name: "Suppliers", exact: true }).click();
    assert.equal(await page.locator(".entry.message").count(), correspondenceMonth ? 32 : 0);
    assert.match(await page.locator("#activity").innerText(), /Supplier paid/);
    if (correspondenceMonth) {
      assert.match(await page.locator("#activity").innerText(), /Revised delivery schedule/);
      assert.match(await page.locator("#activity").innerText(), /Simulated locally · no real email sent/);
      await page.screenshot({ path: path.join(output, "supplier-month.png"), fullPage: false });
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(output, "spectator-mobile.png"), fullPage: false });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  assert.deepEqual(errors, []);
  const result = { status: "passed", retained_month_checked: retained, correspondence_month_checked: correspondenceMonth, checks: ["run selection", "explicit partner filtering", "supplier actions are not messages", "recorded outgoing draft state", "supplier conversation and simulated send boundary", "reply context", "inert hostile text", "poll within ten seconds", "partial journal recovery", "mobile overflow", "no browser errors"] };
  await writeFile(path.join(output, "browser-result.json"), JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify(result));
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
  await rm(temporary, { recursive: true, force: true });
}
