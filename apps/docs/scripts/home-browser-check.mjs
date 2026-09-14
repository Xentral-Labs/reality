import assert from "node:assert/strict";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH });
const base = process.env.DOCS_TEST_URL || "http://127.0.0.1:4198";
const productOrigin = process.env.APP_URL || "https://app.runreality.ai";
try {
  for (const locale of ["", "de/"]) {
    for (const width of [375, 1280]) {
      const page = await browser.newPage({ viewport: { width, height: 1000 } });
      const errors = [];
      page.on("pageerror", (error) => errors.push(error.message));
      await page.goto(`${base}/${locale}`);
      const buttons = page.locator(".VPHero .actions a");
      assert.equal(await buttons.count(), 4);
      assert.match(await buttons.first().getAttribute("class"), /brand/u);
      const product = new URL(await buttons.last().getAttribute("href"));
      assert.equal(product.origin, new URL(productOrigin).origin);
      assert.equal(product.pathname, "/app");
      assert.equal(await buttons.last().getAttribute("target"), "_blank");
      assert.match(await buttons.last().getAttribute("rel"), /noopener/u);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({ path: `/tmp/docs-home-${locale ? "de" : "en"}-${width}.png` });
      for (const [index, target] of [
        "concepts/business-reality-guide",
        "concepts/business-reality-guide/07-model-at-a-glance",
        "integrations/parallel-test",
      ].entries()) {
        await page.goto(`${base}/${locale}`);
        await buttons.nth(index).click();
        await page.waitForURL(`${base}/${locale}${target}`);
        await page.locator(".vp-doc h1").waitFor();
        assert.ok((await page.locator(".vp-doc h1").innerText()).trim());
        // Production nginx resolves clean routes to these HTML files first.
        assert.equal((await page.request.get(`${base}/${locale}${target}.html`)).status(), 200);
      }
      assert.deepEqual(errors, []);
      await page.close();
    }
  }
  console.log(
    "Home navigation passed: both languages, mobile/desktop, every documentation action and configured product link.",
  );
} finally {
  await browser.close();
}
