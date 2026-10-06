const { chromium } = require(
  process.env.PLAYWRIGHT_MODULE || "playwright-core",
);
(async () => {
  const b = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_EXECUTABLE || "/usr/bin/chromium",
    args: ["--no-sandbox"],
  });
  const p = await b.newPage();
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  await p.goto(process.env.SIMULATOR_LIVE_URL);
  await p.locator(".tile").first().waitFor();
  if (!(await p.title()).includes("Reality Company Simulator"))
    throw Error("Title");
  if (process.env.SIMULATOR_SCREENSHOT_DIR)
    await p.screenshot({
      path: process.env.SIMULATOR_SCREENSHOT_DIR + "/simulator-overview.png",
      fullPage: true,
    });
  if (process.env.SIMULATOR_SCREENSHOT_DIR) {
    await p
      .locator("#flow [data-flow]")
      .filter({ hasText: "Where is my order" })
      .first()
      .click();
    await p.locator("#drawer").waitFor({ state: "visible" });
    await p.screenshot({
      path: process.env.SIMULATOR_SCREENSHOT_DIR + "/email-detail.png",
    });
    await p.locator("#close").click();
  }
  await p.locator("[data-metric=reservation_blocked]").click();
  await p
    .locator("#performance-orders [data-performance-order]")
    .first()
    .waitFor();
  await p
    .locator("#performance-orders [data-performance-order]")
    .first()
    .click();
  await p.locator("#drawer").waitFor({ state: "visible" });
  await p.locator("#close").click();
  await p.locator("[data-metric=reservation_blocked]").click();
  await p.locator("#performance-orders").waitFor({ state: "hidden" });
  await p
    .locator("[data-party]")
    .filter({ hasText: "supplier" })
    .first()
    .click();
  await p
    .getByRole("heading", { name: "Supplier purchasing catalogue" })
    .waitFor();
  const catalogue = await p.locator("#workspace-content").innerText();
  if (
    !catalogue.includes("SIM-") ||
    !catalogue.includes("EUR") ||
    !catalogue.includes("Price entry")
  )
    throw Error("Supplier purchasing catalogue missing evidence");
  if (process.env.SIMULATOR_SCREENSHOT_DIR)
    await p.screenshot({
      path: process.env.SIMULATOR_SCREENSHOT_DIR + "/supplier-workspace.png",
      fullPage: true,
    });
  await p
    .locator("[data-party]")
    .filter({ hasText: "customer" })
    .first()
    .click();
  await p.locator("#compose").click();
  if (process.env.SIMULATOR_SCREENSHOT_DIR)
    await p.screenshot({
      path: process.env.SIMULATOR_SCREENSHOT_DIR + "/manual-event.png",
    });
  await p.locator("[name=subject]").fill("Manual browser enquiry");
  await p
    .locator("[name=body]")
    .fill("<img src=x onerror=alert(1)> Please update me.");
  await p.locator("button[type=submit]").click();
  await p.locator("#inject").waitFor({ state: "visible" });
  await p.waitForFunction(() => !document.getElementById("inject").disabled);
  await p.locator("#inject").click();
  await p.locator("#composer").waitFor({ state: "hidden" });
  await p
    .locator("#flow")
    .getByRole("heading", { name: "Manual browser enquiry" })
    .waitFor();
  await p
    .locator("#flow [data-flow]")
    .filter({ hasText: "Manual browser enquiry" })
    .click();
  await p
    .locator("#detail")
    .getByText("<img src=x onerror=alert(1)> Please update me.", {
      exact: true,
    })
    .first()
    .waitFor();
  await p.locator("#close").click();
  await p.locator("[data-direction=incoming]").click();
  if (await p.locator("#flow .outgoing").count())
    throw Error("Direction filter");
  await p.locator("[data-party]").first().click();
  if (process.env.SIMULATOR_SCREENSHOT_DIR)
    await p.screenshot({
      path: process.env.SIMULATOR_SCREENSHOT_DIR + "/customer-workspace.png",
      fullPage: true,
    });
  if (process.env.SIMULATOR_SCREENSHOT_DIR) {
    await p.locator("#workspace").screenshot({
      path: process.env.SIMULATOR_SCREENSHOT_DIR + "/customer-workspace.png",
    });
  }
  await p.locator("[data-tab=documents]").click();
  await p.locator("[data-document]").first().click();
  await p.locator("#detail .detail-order").waitFor();
  await p.locator("#close").click();
  await p.locator("[data-tab=orders]").click();
  if (await p.locator(".message img").count()) throw Error("Unsafe HTML");
  await p.locator("[data-order]").first().click();
  await p.locator("#drawer").waitFor({ state: "visible" });
  await p.locator("#close").click();
  if (process.env.SIMULATOR_SCREENSHOT)
    await p.screenshot({
      path: process.env.SIMULATOR_SCREENSHOT,
      fullPage: true,
    });
  await p.setViewportSize({ width: 390, height: 844 });
  if (await p.evaluate(() => document.documentElement.scrollWidth > innerWidth))
    throw Error("Overflow");
  if (errors.length) throw Error(errors.join("\n"));
  console.log(
    "PASS live data, manual preview/injection, inert mail, order evidence and mobile",
  );
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
