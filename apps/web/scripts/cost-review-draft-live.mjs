// Spec 282 T905 / SC-001: live proof against a running stack. In a business company an
// owner goes from "not evidenced" to a proven acquisition value without typing an
// identifier, a field name or a tool name:
//   draft names the missing company party and stock history → the company is recorded as
//   a business partner → opening stock is recorded through the form with the value its
//   evidence states → "Prüfung vorbereiten" drafts the review → proposed → confirmed in
//   Decisions → the panel shows the acquisition value.
//
// Environment: UNIFIED_APP_URL, TENANT (a business company whose ITEM has no effective
// stock movements), ITEM, LOCATION, REALITY_PLATFORM_ADMIN_EMAIL / _PASSWORD (an owner),
// PLAYWRIGHT_MODULE / PLAYWRIGHT_EXECUTABLE.
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = process.env.UNIFIED_APP_URL || "http://localhost:8180";
const { TENANT: tenant, ITEM: item } = process.env;
const out = "/private/tmp/reality-282-live";
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_EXECUTABLE });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(45_000);
const errors = [],
  log = [];
page.on("pageerror", (error) => errors.push(error.message));
const note = (line) => {
  log.push(line);
  console.log(line);
};
const stockPanel = async () => {
  await page.goto(
    `${base}/app/warehouse?tenant=${tenant}&warehouse_view=stock&item=${item}&entry=${item}&lang=de`,
  );
  const panel = page.locator("[data-resolution-guidance]").first();
  await panel.waitFor();
  return panel;
};
const draftDialog = () => page.locator("dialog[data-cost-review-draft=inventory]");

try {
  await page.goto(`${base}/login?lang=de`);
  await page.locator('input[name="email"]').fill(process.env.REALITY_PLATFORM_ADMIN_EMAIL);
  await page.locator('input[name="password"]').fill(process.env.REALITY_PLATFORM_ADMIN_PASSWORD);
  await page.locator("form button").first().click();
  await page.waitForURL(/\/app/);

  let panel;
  // RENEW=1 skips the setup (steps 1–3) and renews an existing review after new movements.
  if (!process.env.RENEW) {
    // 1. The draft names what is missing, in words.
    panel = await stockPanel();
    await panel.getByRole("button", { name: "Prüfung vorbereiten" }).click();
    const dialog = draftDialog();
    await dialog.locator("[data-draft-open-inputs]").waitFor();
    const missing = await dialog
      .locator("[data-open-input]")
      .evaluateAll((nodes) => nodes.map((node) => node.dataset.openInput));
    note(`1. open inputs: ${missing.join(", ")}`);
    await page.screenshot({ path: `${out}/01-draft-missing.png`, fullPage: true });
    await dialog.getByRole("button", { name: "Schließen" }).click();

    // 2. The company records itself as a business partner (the master data form's service).
    if (missing.includes("company_party_missing")) {
      const status = await page.evaluate(async (tenant) => {
        const response = await fetch(`/api/tenants/${tenant}/parties`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            name: "Walkthrough 282 GmbH",
            type: "company",
            roles: ["company"],
          }),
        });
        return response.status;
      }, tenant);
      note(`2. company business partner recorded: ${status}`);
    }

    // 3. Opening stock through the form, with the value its evidence states.
    await page.goto(`${base}/app/warehouse?tenant=${tenant}&warehouse_view=stock&lang=de`);
    // Actions open through the global launcher, as a clerk would with ⌘K.
    await page
      .getByRole("button", { name: /Suchen/ })
      .first()
      .click();
    await page.keyboard.type("Anfangsbestand");
    await page
      .getByRole("option", { name: /Anfangsbestand erfassen/ })
      .first()
      .click();
    const form = page.locator("dialog[open]").filter({ hasText: "Anfangsbestand erfassen" });
    await form.waitFor();
    const search = form.getByLabel("Suchen Artikel", { exact: false });
    await search.fill("279");
    await form.getByLabel("Artikel", { exact: true }).selectOption({ value: item });
    await form.getByLabel("Suchen Lagerort", { exact: false }).fill("Main");
    const locations = form.getByLabel("Lagerort", { exact: true });
    await page.waitForFunction(
      () => document.querySelectorAll("dialog[open] select")[1]?.options.length > 1,
    );
    await locations.selectOption({ index: 1 });
    await form.getByLabel("Menge hinzufügen", { exact: true }).fill("40");
    await form.getByLabel("Gesamtwert laut Nachweis").fill("480.00");
    await form.getByLabel("Grundlage des Werts", { exact: true }).fill("Inventurliste 31.12.2025");
    await form.getByRole("button", { name: "Änderung prüfen" }).click();
    await form.locator("[data-opening-cost-review]").waitFor();
    note(
      `3. reviewed opening value: ${await form.locator("[data-opening-cost-review]").innerText()}`,
    );
    await page.screenshot({ path: `${out}/02-opening-review.png`, fullPage: true });
    await form.locator(".br-btn-primary").last().click();
    await page.waitForTimeout(3000);
  }

  // 4. The draft is complete except for the method, preselected; propose it.
  panel = await stockPanel();
  await panel.getByRole("button", { name: "Prüfung vorbereiten" }).click();
  const review = draftDialog();
  await review.locator("[data-draft-summary]").waitFor();
  await page.waitForFunction(
    () => document.querySelector("[data-draft-submit]")?.hasAttribute("disabled") === false,
  );
  note(
    `4. draft summary: ${(await review.locator("[data-draft-summary]").innerText()).replace(/\n/g, " / ")}`,
  );
  await page.screenshot({ path: `${out}/03-draft-complete.png`, fullPage: true });
  await review.locator("[data-draft-submit]").click();
  await review.waitFor({ state: "detached" });

  // 5. The owner confirms in Decisions.
  panel = await stockPanel();
  await panel.getByRole("button", { name: "In Entscheidungen prüfen" }).click();
  await page.waitForURL(/\/app\/decisions/);
  const decision = page.locator("dialog[open]").last();
  await decision.locator(".br-btn-primary").last().waitFor();
  await page.screenshot({ path: `${out}/04-decision.png`, fullPage: true });
  await decision.locator(".br-btn-primary").last().click();
  await page.waitForTimeout(4000);

  // 6. The value is proven.
  await page.goto(
    `${base}/app/warehouse?tenant=${tenant}&warehouse_view=stock&item=${item}&entry=${item}&lang=de`,
  );
  const cost = page.getByRole("region", { name: "Kostenerklärung" }).first();
  await cost.waitFor();
  // The account's locale decides the number format (480,00 € or €480.00).
  await cost
    .getByText(new RegExp(process.env.EXPECTED_VALUE || "^(480,00 €|€480\\.00)$"))
    .first()
    .waitFor();
  note(`6. panel: ${(await cost.innerText()).replace(/\n/g, " / ").slice(0, 300)}`);
  await page.screenshot({ path: `${out}/05-proven.png`, fullPage: true });
  assert.deepEqual(errors, []);
  console.log("PASS: live drafted review from not evidenced to a proven acquisition value.");
} catch (error) {
  await page.screenshot({ path: `${out}/error.png`, fullPage: true });
  console.log(errors);
  throw error;
} finally {
  await writeFile(`${out}/walkthrough.log`, log.join("\n"));
  await browser.close();
}
