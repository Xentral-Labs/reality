// Real shared CSS; no business calls or preference writes.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const out = "/private/tmp/reality-shared-select";
let lightIndicator;
try {
  await mkdir(out, { recursive: true });
  for (const theme of ["light", "dark"]) {
    for (const width of [320, 390, 1440]) {
      await page.setViewportSize({ width, height: 1100 });
      await page.goto(`${base}/scripts/fixtures/shared-select-harness.html?theme=${theme}`);
      await page.getByLabel("Standard form", { exact: true }).waitFor();
      const fields = await page.locator("[data-shared-select]").evaluateAll((elements) =>
        elements.map((element) => {
          const css = getComputedStyle(element),
            rect = element.getBoundingClientRect();
          return {
            label: element.labels[0].innerText,
            appearance: css.appearance,
            image: css.backgroundImage,
            position: css.backgroundPosition,
            padding: parseFloat(css.paddingInlineEnd),
            repeat: css.backgroundRepeat,
            width: rect.width,
            right: rect.right,
            height: rect.height,
          };
        }),
      );
      for (const field of fields) {
        assert.equal(
          field.appearance,
          "none",
          `${theme}/${width}/${field.label}: one shared indicator`,
        );
        assert.notEqual(field.image, "none", `${field.label}: visible indicator`);
        assert.equal(field.repeat, "no-repeat");
        assert(
          field.position.includes("12px") && field.position.includes("50%"),
          `${field.label}: centered, inset indicator`,
        );
        assert(field.padding >= 40, `${field.label}: text reserves indicator space`);
        assert(
          field.right <= width && field.width > field.padding + 20,
          `${field.label}: readable within viewport`,
        );
      }
      if (theme === "light") lightIndicator = fields[0].image;
      else assert.notEqual(fields[0].image, lightIndicator, "indicator follows the theme");
      const compact = fields.find((field) => field.label.startsWith("Rows per page"));
      assert.equal(compact.height, 32, "pagination remains compact");
      const disabled = page.getByLabel("Unavailable selection");
      assert.equal(await disabled.isEnabled(), false);
      const field = page.getByLabel("Standard form", { exact: true });
      await field.focus();
      await page.keyboard.press("a");
      assert.equal(await field.inputValue(), "second", "native keyboard selection survives");
      const focus = await field.evaluate((element) => ({
        focused: element === document.activeElement,
        outline: getComputedStyle(element).outlineStyle,
        shadow: getComputedStyle(element).boxShadow,
      }));
      assert(
        focus.focused && (focus.outline !== "none" || focus.shadow !== "none"),
        "keyboard focus stays visible",
      );
      await page.keyboard.press("Tab");
      assert.equal(
        await page
          .getByLabel("Settings", { exact: true })
          .evaluate((element) => element === document.activeElement),
        true,
        "keyboard focus advances to the next field",
      );
      for (const label of ["Native multiple", "Native listbox", "Row density"]) {
        const css = await page.getByLabel(label, { exact: true }).evaluate((element) => ({
          appearance: getComputedStyle(element).appearance,
          image: getComputedStyle(element).backgroundImage,
        }));
        assert.notEqual(css.appearance, "none", `${label}: native rendering preserved`);
        assert.equal(css.image, "none", `${label}: no duplicate indicator`);
      }
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
        false,
        "no page overflow",
      );
      await page.screenshot({ path: `${out}/${theme}-${width}.png`, fullPage: true });
    }
  }
  await page.emulateMedia({ forcedColors: "active" });
  const forced = await page.getByLabel("Standard form", { exact: true }).evaluate((element) => ({
    appearance: getComputedStyle(element).appearance,
    image: getComputedStyle(element).backgroundImage,
  }));
  assert.equal(forced.appearance, "auto", "forced colors restores native arrow");
  assert.equal(forced.image, "none");
  assert.deepEqual(errors, []);
  console.log(
    "PASS shared selects: themes, narrow layouts, inset indicators, keyboard, disabled, pagination, chip/listbox exclusions and forced colors",
  );
} finally {
  await browser.close();
}
