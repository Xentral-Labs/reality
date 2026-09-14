import assert from "node:assert/strict";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_PATH,
});
const base = process.env.DOCS_TEST_URL || "http://127.0.0.1:4187";
try {
  for (const locale of ["de", "en"]) {
    for (const width of [375, 1280]) {
      for (const theme of ["light", "dark"]) {
        const page = await browser.newPage({ viewport: { width, height: 1000 } });
        const errors = [];
        page.on("pageerror", (error) => errors.push(error.message));
        await page.goto(`${base}/${locale === "de" ? "de/" : ""}tool-usage/`);
        await page.locator(".explorer-intro").waitFor();
        await page.evaluate(
          (dark) => document.documentElement.classList.toggle("dark", dark),
          theme === "dark",
        );
        let cardStyle;
        let filterStyle;
        for (const [index, name] of ["resources", "processes", "model", "technical"].entries()) {
          await page.locator(".tool-usage-tabs button").nth(index).click();
          await page.locator(".explorer-intro").scrollIntoViewIfNeeded();
          assert.ok(await page.locator(".explorer-intro h2").innerText());
          assert.ok(
            await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            `${locale}/${width}/${theme}/${name} overflow`,
          );
          const style = async (selector) =>
            page
              .locator(selector)
              .first()
              .evaluate((el) => {
                const css = getComputedStyle(el);
                return [css.padding, css.borderRadius, css.backgroundColor, css.fontSize];
              });
          if (index < 3) {
            const current = await style(".explorer-card");
            if (cardStyle) assert.deepEqual(current, cardStyle, `card treatment: ${name}`);
            cardStyle = current;
          }
          if (index >= 2) {
            const current = await style('.explorer-filter:not(.active):not([aria-pressed="true"])');
            if (filterStyle) assert.deepEqual(current, filterStyle, "filter treatment");
            filterStyle = current;
          }
          if (name === "model") {
            const guidance = page.locator(".model-guidance");
            await guidance.locator("summary").focus();
            await page.keyboard.press("Enter");
            assert.equal(await guidance.getAttribute("open"), "");
            await page.keyboard.press("Enter");
          }
          await page.screenshot({ path: `/tmp/explorer-${locale}-${width}-${theme}-${name}.png` });
        }
        for (const entry of ["tool:inventory_read", "projection:price_resolution"]) {
          await page.goto(`${base}/${locale === "de" ? "de/" : ""}tool-usage/#${entry}`);
          const modes = page.locator("[data-read-execution]").filter({
            hasText: entry.startsWith("tool:") ? "response_format=legacy" : "/prices/resolve",
          });
          await modes.waitFor();
          await modes.scrollIntoViewIfNeeded();
          const content = await modes.innerText();
          assert.ok(content.includes("Live —"));
          assert.ok(
            content.includes(
              entry.startsWith("tool:") ? "response_format=legacy" : "/prices/resolve",
            ),
          );
          if (entry.startsWith("tool:"))
            assert.ok(content.includes(locale === "de" ? "Vorberechnet —" : "Stored —"));
          assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
          await page.screenshot({
            path: `/tmp/read-execution-${locale}-${width}-${theme}-${entry.split(":")[0]}.png`,
          });
        }
        assert.deepEqual(errors, []);
        await page.close();
      }
    }
  }
  console.log(
    "Explorer visual contracts passed: four tabs, two locales, two widths, light and dark.",
  );
} finally {
  await browser.close();
}
