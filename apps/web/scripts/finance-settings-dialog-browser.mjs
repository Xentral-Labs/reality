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
let emptyTargets = true;
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
        {
          id: "blocked-bank",
          code: "BLOCKED",
          name: "Blocked bank",
          role: "cash",
          state: "blocked",
          revision: 1,
        },
        {
          id: "receivable",
          code: "AR",
          name: "Receivables",
          role: "accounts_receivable",
          state: "active",
          revision: 1,
        },
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
  else if (path.endsWith("/finance/matrix"))
    body = {
      revision: 1,
      operations: [
        {
          transaction: "customer_payment",
          label: "Customer payment",
          basis: "Received gross amount",
          control_policy: "original_when_linked",
          legs: [
            {
              side: "debit",
              role: "cash",
              role_label: "Cash and bank",
              account: { id: "bank", code: "BANK", name: "Bank", revision: 1 },
              status: "configured",
            },
          ],
        },
      ],
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
  else if (path.endsWith("/finance/targets"))
    body = {
      revision: 1,
      total: 1,
      items: [
        {
          id: "target",
          namespace: "accounting",
          name: "Accounting software",
          state: "active",
          revision: 1,
        },
      ],
    };
  else if (path.endsWith("/finance/target-references") || path.endsWith("/finance/target-mappings"))
    body = { revision: 1, total: 0, items: [] };
  else {
    status = 503;
    body = { detail: "Unrelated read unavailable" };
  }
  if (
    path.endsWith("/finance/targets") &&
    (emptyTargets || new URL(request.url()).searchParams.get("query"))
  )
    body = { revision: 1, total: 0, items: [] };
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
async function inspectToolbar(region) {
  const toolbar = region.locator("[data-settings-toolbar]");
  assert.equal(await toolbar.count(), 1, "Each settings list has one shared toolbar");
  const action = toolbar.locator(".br-btn-primary");
  if (await action.count()) {
    const bounds = await toolbar.boundingBox();
    const button = await action.boundingBox();
    assert.ok(
      Math.abs(bounds.x + bounds.width - button.x - button.width) < 2,
      "Create action aligns with the right edge",
    );
  }
}
async function inspectModal(modal, name) {
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const theme of ["light", "dark"]) {
      await page.evaluate((theme) => {
        document.documentElement.dataset.theme = theme;
        document.documentElement.classList.toggle("dark", theme === "dark");
      }, theme);
      await page.evaluate(() =>
        Promise.all(document.getAnimations().map((a) => a.finished.catch(() => undefined))),
      );
      assert.ok(await modal.isVisible());
      assert.ok(
        await modal.evaluate((n) => n.scrollWidth <= n.clientWidth),
        `${name} overflows at ${width}`,
      );
      await page.screenshot({ path: `${out}/${name.replaceAll(" ", "-")}-${width}-${theme}.png` });
    }
  }
  await page.evaluate(() => {
    document.documentElement.dataset.theme = "light";
    document.documentElement.classList.remove("dark");
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
}
try {
  await page.goto(`${base}/app/finance?tenant=owner&finance_view=settings`);
  const accounts = panel("Accounts & account mapping");
  await accounts.getByRole("cell", { name: "SAVINGS", exact: true }).waitFor();
  assert.equal(
    await accounts.locator("form").count(),
    0,
    "Settings must start as a list, without a permanent create form",
  );
  assert.equal(
    await accounts.locator("summary").filter({ hasText: "Transaction matrix" }).count(),
    0,
  );
  await page.screenshot({ path: `${out}/account-list.png` });
  await accounts.getByRole("button", { name: "View account usage", exact: true }).click();
  const usage = page.getByRole("dialog", {
    name: "Accounts for business transactions",
    exact: true,
  });
  await usage.getByRole("article", { name: "Customer payment", exact: true }).waitFor();
  await inspectModal(usage, "Account usage");
  await usage.getByRole("button", { name: "Change default", exact: true }).click();
  const defaults = page.getByRole("dialog", { name: "Change default account", exact: true });
  assert.deepEqual(
    await defaults
      .getByLabel("Account", { exact: true })
      .locator("option")
      .evaluateAll((rows) => rows.map((r) => r.value)),
    ["", "bank", "savings"],
  );
  await inspectModal(defaults, "Default account");
  await defaults.getByLabel("Account", { exact: true }).selectOption("savings");
  assert.ok(
    await defaults
      .getByText(
        "This default applies to every transaction using this account role. Existing postings keep their original accounts.",
        { exact: true },
      )
      .isVisible(),
  );
  await page.keyboard.press("Escape");
  await inspectToolbar(accounts);
  await accounts.getByRole("button", { name: "Add account", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Create account", exact: true });
  await dialog.waitFor();
  await dialog.getByLabel("Code", { exact: true }).fill("DRAFT");
  await page.keyboard.press("Escape");
  assert.equal(await page.getByRole("dialog").count(), 0);
  assert.equal(
    await accounts
      .getByRole("button", { name: "Add account", exact: true })
      .evaluate((n) => n === document.activeElement),
    true,
  );
  await accounts
    .getByRole("row")
    .filter({ hasText: "SAVINGS" })
    .getByRole("button", { name: "Edit", exact: true })
    .click();
  const edit = page.getByRole("dialog", { name: "Edit account", exact: true });
  assert.equal(await edit.getByLabel("Code", { exact: true }).inputValue(), "SAVINGS");
  await edit.getByRole("button", { name: "Close", exact: true }).click();
  for (const [section, create] of [
    ["Cost centers", "Create cost center"],
    ["Case codes & coding groups", "Create case code"],
    ["Source code mappings", "New source mapping"],
  ]) {
    await area(section);
    await panel(section).getByRole("button", { name: create, exact: true }).waitFor();
    assert.equal(await panel(section).locator("form").count(), 0);
    await panel(section).getByText("No entries yet.", { exact: true }).waitFor();
    assert.equal(await panel(section).locator("input, table").count(), 0);
    assert.equal(
      await panel(section).getByRole("button", { name: "Previous", exact: true }).count(),
      0,
    );
    await inspectToolbar(panel(section));
    if (await page.getByRole("button", { name: "Hide chat", exact: true }).isVisible())
      await page.getByRole("button", { name: "Hide chat", exact: true }).click();
    await page.setViewportSize({ width: 390, height: 900 });
    await inspectToolbar(panel(section));
    await page.screenshot({ path: `${out}/${section.replaceAll(" ", "-")}-list-mobile.png` });
    await page.setViewportSize({ width: 1440, height: 1000 });
    await panel(section).getByRole("button", { name: create, exact: true }).click();
    await page.getByRole("dialog", { name: create, exact: true }).waitFor();
    await inspectModal(page.getByRole("dialog", { name: create, exact: true }), create);
    await page.keyboard.press("Escape");
  }
  assert.equal(
    requests.filter((r) => r.method !== "GET").length,
    0,
    "Cancelled editors cannot write",
  );
  await area("Case codes & coding groups");
  await inspectToolbar(panel("Case codes & coding groups"));
  await panel("Case codes & coding groups")
    .getByLabel("Reference type", { exact: true })
    .selectOption("coding_group");
  await panel("Case codes & coding groups")
    .getByRole("button", { name: "Create coding group", exact: true })
    .click();
  await page.getByRole("dialog", { name: "Create coding group", exact: true }).waitFor();
  await page.keyboard.press("Escape");
  const referenceRoute = "**/api/tenants/owner/finance/references?*";
  await page.route(referenceRoute, (route) => {
    const params = new URL(route.request().url()).searchParams;
    const rows =
      params.get("kind") === "case_code" && !params.get("query") && !params.get("state")
        ? [{ id: "case", code: "DOMESTIC", name: "Domestic sales", state: "active", revision: 1 }]
        : [];
    return route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ revision: 1, total: rows.length, items: rows }),
    });
  });
  await page.reload();
  const cases = panel("Case codes & coding groups");
  await cases.getByLabel("Search references", { exact: true }).fill("missing");
  await cases.getByRole("button", { name: "Reset filters", exact: true }).click();
  await cases.getByText("DOMESTIC", { exact: true }).waitFor();
  await cases.getByLabel("Reference status filter", { exact: true }).selectOption("blocked");
  await cases.getByRole("button", { name: "Reset filters", exact: true }).waitFor();
  await cases.getByLabel("Reference type", { exact: true }).selectOption("coding_group");
  await cases.getByText("No entries yet.", { exact: true }).waitFor();
  assert.equal(await cases.locator("input").count(), 0);
  assert.equal(await cases.getByLabel("Reference status filter", { exact: true }).count(), 0);
  await page.unroute(referenceRoute);
  await area("Accounts & account mapping");
  await page.getByRole("button", { name: "External accounting", exact: true }).click();
  const external = panel("External accounting");
  assert.equal(await external.getByLabel("Accounting target", { exact: true }).count(), 0);
  await external.getByText("No accounting targets yet.", { exact: true }).waitFor();
  assert.equal(await external.locator("input, select").count(), 0);
  assert.equal(await external.getByRole("button", { name: "Previous", exact: true }).count(), 0);
  await page.screenshot({ path: `${out}/external-empty.png` });
  await external.getByRole("button", { name: "Create accounting target", exact: true }).click();
  await inspectModal(
    page.getByRole("dialog", { name: "Create accounting target", exact: true }),
    "Empty-target-create",
  );
  await page.keyboard.press("Escape");
  emptyTargets = false;
  await page.reload();

  await external.getByLabel("Search", { exact: true }).fill("missing target");
  await external.getByText("No matching references", { exact: true }).waitFor();
  await external.getByRole("button", { name: "Reset filters", exact: true }).click();
  assert.equal(await external.getByLabel("Search", { exact: true }).inputValue(), "");
  await external.getByRole("button", { name: "Open account setup", exact: true }).click();
  for (const [tab, create] of [
    ["Accounting targets", "Create accounting target"],
    ["External accounts", "Create external account"],
    ["Tax codes", "Create tax code"],
    ["Rules", "Create mapping rule"],
  ]) {
    if (tab === "Accounting targets") {
      await external
        .getByRole("button", { name: "Back to accounting targets", exact: true })
        .click();
    } else {
      if (tab === "External accounts")
        await external.getByRole("button", { name: "Open account setup", exact: true }).click();
      await external.getByRole("button", { name: tab, exact: true }).click();
    }
    await external.getByRole("button", { name: create, exact: true }).click();
    await inspectToolbar(external);
    const modal = page.getByRole("dialog", { name: create, exact: true });
    await modal.waitFor();
    await inspectModal(modal, create);
    await modal.getByRole("button", { name: "Close", exact: true }).click();
    assert.equal(await external.locator("form").count(), 0);
  }
  await page.getByRole("button", { name: "Operational accounts", exact: true }).click();
  await accounts.getByRole("button", { name: "Add account", exact: true }).click();
  const createDialog = page.getByRole("dialog", { name: "Create account", exact: true });
  await createDialog.getByLabel("Code", { exact: true }).fill("BANK2");
  await createDialog.getByLabel("Name", { exact: true }).fill("Second bank account");
  for (const width of [390, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const theme of ["light", "dark"]) {
      await page.evaluate((theme) => {
        document.documentElement.dataset.theme = theme;
        document.documentElement.classList.toggle("dark", theme === "dark");
      }, theme);
      await page.evaluate(() =>
        Promise.all(document.getAnimations().map((a) => a.finished.catch(() => undefined))),
      );
      assert.ok(await createDialog.isVisible());
      assert.ok(await createDialog.evaluate((n) => n.scrollWidth <= n.clientWidth));
      await page.screenshot({ path: `${out}/account-dialog-${width}-${theme}.png` });
    }
  }
  await createDialog.getByRole("button", { name: "Review account change", exact: true }).click();
  await createDialog.getByRole("alert").waitFor();
  assert.equal(await createDialog.getByLabel("Code", { exact: true }).inputValue(), "BANK2");
  await page.keyboard.press("Escape");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.evaluate(() => {
    document.documentElement.dataset.theme = "light";
    document.documentElement.classList.remove("dark");
  });
  await switchCompany("member");
  await accounts.getByRole("cell", { name: "SAVINGS", exact: true }).waitFor();
  assert.equal(await accounts.getByRole("button", { name: "Add account", exact: true }).count(), 0);
  assert.ok(
    await accounts
      .getByRole("row")
      .filter({ hasText: "SAVINGS" })
      .getByRole("button", { name: "Edit", exact: true })
      .isDisabled(),
  );
  await switchCompany("owner");
  await page.evaluate(() =>
    sessionStorage.setItem(
      "finance-account-review:owner",
      JSON.stringify({ id: "prepared", description: "BANK · Reviewed account" }),
    ),
  );
  await page.reload();
  const review = page.getByRole("dialog", { name: "Confirm account change", exact: true });
  await review.waitFor();
  await review.getByRole("button", { name: "Close", exact: true }).click();
  await accounts.getByRole("button", { name: "Continue review", exact: true }).click();
  await review.waitFor();
  assert.equal(await review.getByText("BANK · Reviewed account", { exact: true }).count(), 1);
  await review.getByRole("button", { name: "Close", exact: true }).click();
  await page.evaluate(() => sessionStorage.removeItem("finance-account-review:owner"));
  await page.route("**/api/tenants/owner/finance/accounts", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ revision: 1, accounts: [], roles: {}, defaults: {} }),
    }),
  );
  await page.reload();
  await accounts.getByText("No entries yet.", { exact: true }).waitFor();
  assert.equal(await accounts.locator("table, input, select").count(), 0);
  assert.ok(await accounts.getByRole("button", { name: "Add account", exact: true }).isEnabled());
  assert.deepEqual(errors, []);
  console.log("PASS Finance list/create/edit dialogs and no-write cancellation");
} catch (error) {
  await page.screenshot({ path: `${out}/error.png` });
  console.error(await page.locator("body").innerText());
  throw error;
} finally {
  await browser.close();
}
