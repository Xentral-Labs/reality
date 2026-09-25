// Spec 266: the engine room against a real API, not fixtures. See
// specs/266-engine-room/quickstart.md for the seed and the environment.
import { execSync } from "node:child_process";

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE);
const BASE = process.env.ENGINE_ROOM_BASE_URL || "http://127.0.0.1:5266";
const TENANT = process.env.TENANT;
const TOKEN = process.env.TOKEN;
const SHOTS = process.env.SHOTS || "/tmp";
const PASSWORD = "a-long-account-password";
const results = [];
const check = (name, ok, detail = "") => {
  results.push({ name, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"} ${name}${detail ? ` — ${detail}` : ""}`);
};

const browser = await chromium.launch();
async function signedIn(email, options = {}) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 950 }, ...options });
  const login = await context.request.post(`${BASE}/api/auth/login`, {
    data: { email, password: PASSWORD },
  });
  if (!login.ok()) throw new Error(`login ${email}: ${login.status()}`);
  return context;
}
const errors = [];
const owner = await signedIn("owner@example.test");
const page = await owner.newPage();
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(`${BASE}/app/inspector?tenant=${TENANT}&inspector_view=live`);
await page.waitForSelector("[data-engine-room]", { timeout: 15000 });
check("Live tab renders for the owner", true);
await page.screenshot({ path: `${SHOTS}/01-live-empty.png` });

// A member reads and writes through the web.
const member = await signedIn("member@example.test");
const memberRequests = member.request;
await memberRequests.get(`${BASE}/api/tenants/${TENANT}/items`, {
  headers: { "X-Reality-Correlation": "click_member_1" },
});
const created = await memberRequests.post(`${BASE}/api/tenants/${TENANT}/items`, {
  data: { sku: "LAMP-2", name: "Floor lamp" },
  headers: { "X-Reality-Correlation": "click_member_2" },
});
check("member write succeeded", created.status() === 201, String(created.status()));

const t0 = Date.now();
await page
  .locator("[data-interaction]", { hasText: "Max Member" })
  .first()
  .waitFor({ timeout: 5000 });
check("the member's interaction appears live", true, `${Date.now() - t0} ms after the write`);
await page
  .locator("[data-interaction]", { hasText: "POST /items" })
  .first()
  .waitFor({ timeout: 5000 });
// Read the list only once the write has arrived; the read may come a poll earlier.
const text = await page.locator("[data-engine-room-list]").innerText();
check("the row names the member", text.includes("Max Member"), "");
check(
  "the row names the route template",
  text.includes("POST /items") && text.includes("GET /items"),
);
const mapMark = await page.locator('[data-stage="master_data"]').getAttribute("data-stage-mark");
check("the model map marks master data as written", mapMark === "written", mapMark || "none");
await page.screenshot({ path: `${SHOTS}/02-live-rows.png` });

// An MCP client calls a read tool through the real MCP handler.
if (!process.env.ENGINE_ROOM_MCP_CALL)
  throw new Error("Set ENGINE_ROOM_MCP_CALL (see quickstart).");
execSync(process.env.ENGINE_ROOM_MCP_CALL, { stdio: "inherit" });
await page.waitForSelector('[data-interaction-channel="mcp"]', { timeout: 5000 });
const mcpText = await page.locator('[data-interaction-channel="mcp"]').first().innerText();
check(
  "MCP row names the token and its issuer",
  mcpText.includes("Claude Desktop") && mcpText.includes("Olga Owner"),
  mcpText.replace(/\s+/g, " ").slice(0, 160),
);

const mcpRow = page.locator('[data-interaction-channel="mcp"]').first();
await mcpRow.locator("button").click();
const mcpDetails = await page.locator("[data-cockpit-details]").innerText();
check(
  "MCP details show the choice, not only argument names",
  mcpDetails.includes("family: item"),
  "",
);
await mcpRow.locator("button").click();
check(
  "MCP row carries a reader's label",
  /Discover business records|Geschäftsdaten/.test(mcpText),
  "",
);
const mcpRows = await owner.request
  .get(`${BASE}/api/tenants/${TENANT}/interactions?channel=mcp`)
  .then((response) => response.json());
const mcpStages = mcpRows.interactions.at(-1)?.stages?.read || [];
check("a choice names the stage it read", mcpStages.includes("master_data"), mcpStages.join(","));
check(
  "the owner's own page loads are hidden by default",
  (await page.locator('[data-interaction-channel="web"]', { hasText: "Olga Owner" }).count()) === 0,
);

// The bridge: an access that changed something opens that change in the Inspector.
await page
  .locator("[data-interaction]", { hasText: "POST /items" })
  .first()
  .locator("[data-cockpit-change]")
  .click();
await page.waitForSelector("dialog[open]", { timeout: 5000 });
check("a change opens in the Inspector", (await page.locator("dialog[open]").count()) === 1);
await page.getByRole("button", { name: "Close" }).click();
// The details of a write list its events.
await page
  .locator("[data-interaction]", { hasText: "POST /items" })
  .first()
  .locator("button")
  .first()
  .click();
await page.waitForSelector("[data-engine-room-events] li", { timeout: 5000 });
check("linked events list", (await page.locator("[data-engine-room-events] li").count()) >= 1);

// The cockpit shows the last minute only: the status names what is happening now.
const status = await page.locator("[data-cockpit-status]").getAttribute("data-cockpit-status");
check("the cockpit reports activity while it happens", status === "active", status || "none");

// Filter by channel through a row badge; the URL carries it.
await page.locator('[data-cockpit-channel="mcp"]').click();
await page.waitForTimeout(1500);
check("channel filter in the URL", page.url().includes("live_channel=mcp"), page.url());
check(
  "only MCP rows remain",
  (await page.locator('[data-interaction]:not([data-interaction-channel="mcp"])').count()) === 0,
);
await page.screenshot({ path: `${SHOTS}/03-filtered.png` });
await page.reload();
await page.waitForSelector('[data-interaction-channel="mcp"]', { timeout: 8000 });
check("filter survives reload", page.url().includes("live_channel=mcp"));
await page.getByText("Clear filters").click();

// The live monitor shows no history: there is no period or step control.
check(
  "no history controls",
  (await page.locator("[data-engine-room-period], [data-engine-room-step]").count()) === 0,
);

// Header pulse exists for owners and opens the Live tab.
check(
  "header pulse for owners",
  (await page.locator('button[aria-label="Live monitor"]').count()) === 1,
);

// Member: no Live tab, direct URL refuses.
const memberPage = await member.newPage();
await memberPage.goto(`${BASE}/app/inspector?tenant=${TENANT}&inspector_view=history`);
await memberPage.waitForTimeout(2500);
check(
  "member sees no Live tab",
  (await memberPage.getByRole("button", { name: "Live", exact: true }).count()) === 0,
);
check(
  "member has no header pulse",
  (await memberPage.locator('button[aria-label="Live monitor"]').count()) === 0,
);
await memberPage.goto(`${BASE}/app/inspector?tenant=${TENANT}&inspector_view=live`);
await memberPage.waitForTimeout(2500);
check(
  "member direct URL says owners only",
  (await memberPage.getByText("Only company owners can open the live monitor.").count()) === 1,
);

// Entry point: MCP token link.
await page.goto(`${BASE}/app/settings?tenant=${TENANT}&settings_view=agents`);
await page.waitForTimeout(2500);
const tokenLink = page.locator("[data-token-engine-room]");
check("MCP token links to its calls", (await tokenLink.count()) >= 1);
if (await tokenLink.count()) {
  await tokenLink.first().click();
  await page.waitForSelector("[data-engine-room]");
  check("token link filters by token", page.url().includes(`live_token=${TOKEN}`), page.url());
}

// Mobile width and dark mode.
const phone = await signedIn("owner@example.test", {
  viewport: { width: 390, height: 844 },
  colorScheme: "dark",
});
const phonePage = await phone.newPage();
await phonePage.goto(`${BASE}/app/inspector?tenant=${TENANT}&inspector_view=live`);
await phonePage.waitForSelector("[data-interaction]", { timeout: 10000 });
const overflow = await phonePage.evaluate(() => document.documentElement.scrollWidth - innerWidth);
check("no horizontal overflow at 390px", overflow <= 0, `overflow ${overflow}px`);
await phonePage.screenshot({ path: `${SHOTS}/05-phone-dark.png`, fullPage: true });

check("no console errors", errors.length === 0, errors.slice(0, 3).join(" | "));
await browser.close();
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exitCode = failed.length ? 1 : 0;
