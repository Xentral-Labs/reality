// Spec 279 T909: live walk-through against a running stack. A company owner follows the
// cost guidance from "not evidenced" through the chat handoff into Decisions and back to
// a proven value. Every change goes through chat and Decisions; nothing writes directly.
// Demo and practice companies admit no invited members, so the member's view ("a company
// owner must confirm this") is proven by the fixture run in cost-explanation-browser.mjs.
//
// Environment: UNIFIED_APP_URL, PANEL_PATH (page that shows the scope's cost panel),
// REALITY_PLATFORM_ADMIN_EMAIL / _PASSWORD (the owner), PLAYWRIGHT_MODULE /
// PLAYWRIGHT_EXECUTABLE. STAGE: chat | decide | all.
import { mkdir, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = process.env.UNIFIED_APP_URL || "http://localhost:8180";
const stage = process.env.STAGE || "all";
const out = "/private/tmp/reality-279-walkthrough";
await mkdir(out, { recursive: true });
const browser = await chromium.launch({
  headless: process.env.HEADLESS !== "false",
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const log = [];
const note = (line) => {
  log.push(line);
  console.log(line);
};
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(30_000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));

async function openPanel() {
  // The account language decides otherwise; `lang` holds for this document.
  await page.goto(`${base}${process.env.PANEL_PATH}&lang=de`);
  const panel = page.locator("[data-resolution-guidance]").first();
  await panel.waitFor({ timeout: 60_000 });
  return panel;
}
const steps = (panel) =>
  panel
    .locator("[data-guidance-step]")
    .evaluateAll((nodes) =>
      nodes.map((node) => `${node.dataset.guidanceStep}:${node.dataset.guidanceState}`),
    );

try {
  await page.goto(`${base}/login?lang=de`);
  await page.locator('input[name="email"]').fill(process.env.REALITY_PLATFORM_ADMIN_EMAIL);
  await page.locator('input[name="password"]').fill(process.env.REALITY_PLATFORM_ADMIN_PASSWORD);
  await page.locator("form button").first().click();
  await page.waitForURL(/\/app/);

  if (stage === "all" || stage === "chat") {
    const panel = await openPanel();
    note(`before: ${(await steps(panel)).join(", ")}`);
    note(`reason: ${(await panel.locator("div").first().innerText()).replace(/\n/g, " / ")}`);
    await page.screenshot({ path: `${out}/01-panel.png`, fullPage: true });
    await panel.getByRole("button", { name: "Mit Reality vorbereiten" }).first().click();
    const composer = page.locator("[data-global-chat] textarea").first();
    await composer.waitFor();
    note(`prepared request: ${await composer.inputValue()}`);
    await page.screenshot({ path: `${out}/02-draft.png`, fullPage: true });
    // The person sends it; the handoff itself never does.
    await composer.press("Enter");
    const chat = page.locator("[data-global-chat]");
    // Wait until the answer stops streaming: the transcript stops growing.
    let previous = "";
    for (let second = 0; second < 300; second += 5) {
      await page.waitForTimeout(5000);
      const text = await chat.innerText();
      if (second >= 20 && text === previous) break;
      previous = text;
    }
    await writeFile(`${out}/chat-transcript.txt`, await chat.innerText());
    await page.screenshot({ path: `${out}/03-chat.png`, fullPage: true });
    note("chat transcript saved");
  }

  if (stage === "all" || stage === "decide") {
    const panel = await openPanel();
    note(`after chat: ${(await steps(panel)).join(", ")}`);
    await page.screenshot({ path: `${out}/04-waiting.png`, fullPage: true });
    const review = panel.getByRole("button", { name: "In Entscheidungen prüfen" });
    if (await review.count()) {
      await review.click();
      await page.waitForURL(/\/app\/decisions/);
      note(`decision url: ${page.url()}`);
      await page.waitForTimeout(3000);
      await page.screenshot({ path: `${out}/05-decision.png`, fullPage: true });
    } else note("no decision review step is open");
  }
  note(`page errors: ${JSON.stringify(errors)}`);
} finally {
  await writeFile(`${out}/walkthrough-${stage}.log`, log.join("\n"));
  await browser.close();
}
