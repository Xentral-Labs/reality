// Synthetic reads verify workspace placement and permissions without tenant writes.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const base = process.env.BASE_URL || "http://127.0.0.1:18163";
const out = process.env.FINANCE_SCREENSHOTS || "/private/tmp/finance-settings-workspace";
await mkdir(out, { recursive: true });
const requests = [];
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
await page.route("**/api/**", (route) => {
  const request = route.request();
  const path = new URL(request.url()).pathname;
  requests.push({ path, method: request.method() });
  let body = {},
    status = 200;
  if (path === "/api/auth/me")
    body = {
      id: "user",
      email: "owner@example.test",
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
    };
  else if (path === "/api/v1/bootstrap")
    body = {
      tenants: [
        { id: "owner", name: "Owner company", role: "owner" },
        { id: "member", name: "Member company", role: "member" },
      ],
      default_tenant_id: "owner",
    };
  else if (path.endsWith("/copilot"))
    body = {
      sessions: [],
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
      active_session_id: null,
    };
  else if (path.endsWith("/finance/accounts"))
    body = {
      revision: 1,
      accounts: [
        { id: "bank", code: "BANK", name: "Bank", role: "cash", state: "active", revision: 1 },
        {
          id: "savings",
          code: "SAVINGS",
          name: "Savings",
          role: "cash",
          state: "active",
          revision: 1,
        },
      ],
      roles: { cash: "Cash and bank", accounts_receivable: "Customer receivables" },
      defaults: { cash: "bank" },
    };
  else if (path.endsWith("/finance/references"))
    body = { revision: 1, items: [], total: 0, limit: 50, offset: 0 };
  else if (path.endsWith("/finance/source-mappings"))
    body = {
      revision: 1,
      items: [],
      total: 0,
      sources: [],
      sources_total: 0,
      references: { case_code: { items: [], total: 0 }, coding_group: { items: [], total: 0 } },
    };
  else {
    status = 503;
    body = { detail: "Unrelated read unavailable" };
  }
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
});
const panel = (label) => page.getByRole("region", { name: label, exact: true });
async function area(name) {
  await page
    .getByRole("navigation", { name: "Finance settings areas", exact: true })
    .getByRole("button", { name, exact: true })
    .click();
  await panel(name).waitFor();
}
async function switchCompany(id) {
  await page.getByRole("button", { name: "Switch company", exact: true }).click();
  await page.locator(`[data-company-option="${id}"]`).click();
  await panel("Finance settings").waitFor();
}
try {
  await page.goto(`${base}/app/finance?tenant=owner&finance_view=settings`);
  const accounts = panel("Accounts & account mapping");
  await accounts.getByRole("button", { name: "Add account", exact: true }).waitFor();
  async function compactForm(region) {
    await region
      .getByRole("button", {
        name: /^(Add account|Create cost center|Create case code|Create coding group|New source mapping)$/,
      })
      .click();
    const form = region.locator("form");
    const submit = form.locator('button:not([type="button"])').first();
    const box = await submit.boundingBox();
    assert.ok(box.height <= 40, `Form action too tall: ${box.height}`);
    const bottoms = await form
      .locator("input, select, textarea")
      .evaluateAll((fields) => fields.map((f) => f.getBoundingClientRect().bottom));
    assert.ok(box.y >= Math.max(...bottoms), "Submit must be below every form field");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Close", exact: true })
      .first()
      .click();
  }
  await compactForm(accounts);
  const bank = accounts
    .locator("tr")
    .filter({ has: page.getByRole("cell", { name: "BANK", exact: true }) });
  assert.equal(await bank.getByRole("button", { name: "Default", exact: true }).count(), 0);
  assert.equal(await bank.getByText("Default", { exact: true }).count(), 1);
  const more = bank.getByRole("button", { name: "More actions", exact: true });
  assert.ok(
    (await bank.getByRole("button", { name: "Edit", exact: true }).boundingBox()).height <= 36,
  );
  await more.click();
  await bank.getByRole("button", { name: "Block account", exact: true }).waitFor();
  assert.equal(await bank.getByRole("button", { name: "Use as default", exact: true }).count(), 0);
  const popup = await bank.locator(":popover-open").boundingBox();
  assert.ok(
    popup.x >= 0 && popup.y >= 0 && popup.x + popup.width <= 1440 && popup.y + popup.height <= 1000,
  );
  await page.screenshot({ path: `${out}/account-actions.png` });
  await page.keyboard.press("Escape");
  await bank
    .getByRole("button", { name: "Block account", exact: true })
    .waitFor({ state: "hidden" });
  await more.click();
  await accounts.getByRole("heading").click();
  await bank
    .getByRole("button", { name: "Block account", exact: true })
    .waitFor({ state: "hidden" });
  const savings = accounts.locator("tr").filter({ hasText: "SAVINGS" });
  await savings.getByRole("button", { name: "More actions", exact: true }).click();
  assert.equal(
    await savings.getByRole("button", { name: "Use as default", exact: true }).isEnabled(),
    true,
  );
  await page.keyboard.press("Escape");
  await accounts.getByRole("button", { name: "Add account", exact: true }).click();
  await accounts.locator('input[name="code"]').fill("UNSAVED");
  await page.keyboard.press("Escape");
  await switchCompany("member");
  await accounts.getByRole("button", { name: "Set up standard accounts", exact: true }).waitFor();
  assert.equal(await accounts.getByRole("button", { name: "Add account", exact: true }).count(), 0);
  assert.ok(
    await accounts
      .getByRole("button", { name: "Set up standard accounts", exact: true })
      .isDisabled(),
  );
  await area("Cost centers");
  assert.equal(await page.getByLabel("Reference type", { exact: true }).count(), 0);
  assert.equal(
    await page
      .getByRole("button", { name: /^Review (reference change|cost center)$/, exact: true })
      .count(),
    0,
  );
  await area("Source code mappings");
  await page.getByText("Source code mappings: 0", { exact: true }).waitFor();
  assert.equal(
    await page.getByRole("heading", { name: "New source mapping", exact: true }).count(),
    0,
  );
  await switchCompany("owner");
  await area("Accounts & account mapping");
  await accounts.getByRole("button", { name: "Add account", exact: true }).click();
  await accounts.locator('input[name="code"]').waitFor();
  assert.equal(await accounts.locator('input[name="code"]').inputValue(), "");
  await page.keyboard.press("Escape");
  await compactForm(accounts);
  await area("Case codes & coding groups");
  assert.deepEqual(
    await page
      .getByLabel("Reference type", { exact: true })
      .locator("option")
      .evaluateAll((rows) => rows.map((r) => r.value)),
    ["case_code", "coding_group"],
  );
  await compactForm(panel("Case codes & coding groups"));
  assert.equal(await accounts.count(), 0);
  await area("Source code mappings");
  await page.getByRole("button", { name: "New source mapping", exact: true }).waitFor();
  await compactForm(panel("Source code mappings"));
  await area("Cost centers");
  await page.getByRole("button", { name: "Create cost center", exact: true }).waitFor();
  await compactForm(panel("Cost centers"));
  await page.reload();
  await panel("Cost centers").waitFor();
  assert.equal(new URL(page.url()).searchParams.get("finance_settings"), "cost-centers");
  await page.evaluate(() =>
    sessionStorage.setItem(
      "finance-reference-proposal:owner",
      JSON.stringify({
        id: "legacy-review",
        preview: {
          reference: {
            before: null,
            after: {
              kind: "cost_center",
              code: "WAREHOUSE",
              name: "Warehouse",
              state: "active",
              revision: 1,
            },
            reason: "Recover previous review",
          },
        },
      }),
    ),
  );
  await page.reload();
  await page.getByRole("region", { name: "Confirm reference change", exact: true }).waitFor();
  await page.keyboard.press("Escape");
  await area("Case codes & coding groups");
  assert.equal(
    await page.getByRole("region", { name: "Confirm reference change", exact: true }).count(),
    0,
  );
  await area("Cost centers");
  await page.getByRole("region", { name: "Confirm reference change", exact: true }).waitFor();
  assert.equal(
    await page.evaluate(() => sessionStorage.getItem("finance-reference-proposal:owner")),
    null,
  );
  await page.evaluate(() =>
    sessionStorage.removeItem("finance-reference-proposal:owner:cost-centers"),
  );
  await page.reload();
  await panel("Cost centers").waitFor();
  if (await page.getByRole("button", { name: "Hide chat", exact: true }).isVisible())
    await page.getByRole("button", { name: "Hide chat", exact: true }).click();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    if (width === 390) {
      await page.getByLabel("Settings area", { exact: true }).selectOption("source-mappings");
      await panel("Source code mappings").waitFor();
      await page.getByLabel("Settings area", { exact: true }).selectOption("cost-centers");
    }
    for (const theme of ["light", "dark"]) {
      await page.evaluate((value) => {
        document.documentElement.dataset.theme = value;
        document.documentElement.style.colorScheme = value;
        document.documentElement.classList.toggle("dark", value === "dark");
      }, theme);
      await page.evaluate(() =>
        Promise.all(
          document.getAnimations().map((animation) => animation.finished.catch(() => undefined)),
        ),
      );
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({ path: `${out}/${width}-${theme}.png` });
    }
  }
  assert.equal(await page.getByLabel("Search finance", { exact: true }).count(), 0);
  assert.deepEqual(
    requests.filter((row) => /\/finance\/(open-items|payments|journal)$/.test(row.path)),
    [],
  );
  assert.deepEqual(
    requests.filter((row) => row.method !== "GET"),
    [],
  );
  assert.deepEqual(errors, []);
  console.log(
    "PASS Finance settings: compact footer/row dimensions, default badge, unclipped secondary actions, Escape/outside dismissal, area/recovery/permissions and responsive themes",
  );
} finally {
  await browser.close();
}
