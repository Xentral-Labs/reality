const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
import assert from "node:assert/strict";
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_PATH,
});
try {
  for (const locale of ["", "de/"])
    for (const route of ["", "tool-usage/"])
      for (const width of [375, 768, 1024, 1194, 1280, 1600]) {
        const page = await browser.newPage({ viewport: { width, height: 1000 } });
        await page.goto(
          (process.env.DOCS_TEST_URL || "http://127.0.0.1:4187") + "/" + locale + route,
        );
        await page.locator(".DocSearch-Button").waitFor();
        await page.waitForLoadState("networkidle");
        // Wait for rendered header state without relying on retired preference storage.
        await page.locator(".VPNavBarMenu").waitFor({ state: "attached" });
        const boxes = await page.locator(".VPNavBar .content-body > *").evaluateAll((els) =>
          els
            .filter(
              (e) => e.getBoundingClientRect().width && getComputedStyle(e).display !== "none",
            )
            .map((e) => ({
              cls: e.className,
              x: e.getBoundingClientRect().x,
              right: e.getBoundingClientRect().right,
            })),
        );
        assert(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          `overflow ${locale} ${route} ${width}`,
        );
        for (let i = 1; i < boxes.length; i++)
          assert(
            boxes[i].x >= boxes[i - 1].right - 1,
            JSON.stringify({ locale, route, width, boxes }),
          );
        const links = page.locator(".VPNavBarMenu > a:visible");
        assert.equal(await links.count(), width < 768 ? 0 : width < 1280 ? 3 : 6);
        if (width < 1280) {
          await page.locator(".VPNavBarHamburger").click();
          await page.locator(".VPNavScreen .VPNavScreenMenuLink").first().waitFor();
          assert.equal(await page.locator(".VPNavScreen .VPNavScreenMenuLink:visible").count(), 6);
          await page.locator(".VPNavBarHamburger").click();
          await page.locator(".VPNavScreen").waitFor({ state: "hidden" });
        }
        if (width === 1024 || width === 1280)
          await page.screenshot({
            path: `/tmp/docs-header-${locale ? "de" : "en"}-${route ? "article" : "home"}-${width}.png`,
          });
        if (route === "" && (width === 375 || width === 1024))
          for (const dark of [false, true]) {
            await page.evaluate(
              (dark) => document.documentElement.classList.toggle("dark", dark),
              dark,
            );
            await page.locator(".DocSearch-Button").click();
            const input = page.locator(".VPLocalSearchBox .search-input");
            await input.fill("Commitment");
            assert.equal(await input.evaluate((el) => getComputedStyle(el).outlineStyle), "none");
            assert(await input.evaluate((el) => el.parentElement.matches(":focus-within")));
            await page.screenshot({
              path: `/tmp/docs-search-${locale ? "de" : "en"}-${width}-${dark ? "dark" : "light"}.png`,
            });
            await page.keyboard.press("Tab");
            assert(
              await page.evaluate(
                () => getComputedStyle(document.activeElement).outlineStyle !== "none",
              ),
            );
            await page.keyboard.press("Escape");
            await page.locator(".VPLocalSearchBox").waitFor({ state: "hidden" });
          }
        await page.close();
      }
  console.log("24 header layouts and 8 search focus checks passed");
} finally {
  await browser.close();
}
