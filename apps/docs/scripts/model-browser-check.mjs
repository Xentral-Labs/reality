const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
import assert from "node:assert/strict";
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_PATH,
});
try {
  for (const locale of ["de", "en"])
    for (const width of [375, 1280]) {
      const page = await browser.newPage({ viewport: { width, height: 950 } });
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      const url = `${process.env.DOCS_TEST_URL || "http://127.0.0.1:4187"}/${locale === "de" ? "de/" : ""}tool-usage/#model:commitment`;
      await page.goto(url);
      await page.locator(".model-detail").waitFor();
      assert.equal(await page.locator(".model-fields .model-field").count(), 17);
      assert.equal(await page.locator(".model-picker a").count(), 9);
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
        true,
        `overflow ${locale}/${width}`,
      );
      await page.locator(".model-detail").evaluate((el) => el.scrollIntoView({ block: "start" }));
      await page.screenshot({ path: `/tmp/model-${locale}-${width}.png` });
      const search = page.locator(".tool-usage-search input");
      await search.fill("due_at");
      assert.equal(await page.locator(".model-fields .model-field").count(), 1);
      assert.equal(await page.locator(".model-fields-table thead th").count(), 6);
      await page.locator(".model-fields").focus();
      if (width === 375) {
        await page.keyboard.press("End");
        await page.locator(".model-fields").evaluate((el) => {
          el.scrollLeft = el.scrollWidth;
        });
        assert.ok(await page.locator(".model-fields").evaluate((el) => el.scrollLeft > 0));
      }
      await page.locator(".model-fields").evaluate((el) => {
        el.scrollLeft = 0;
        el.scrollIntoView({ block: "center" });
      });
      await page.screenshot({ path: `/tmp/model-table-${locale}-${width}.png` });
      assert.ok(await page.locator(".model-field").innerText());
      await search.fill("");
      await page.locator('.related-models a[href="#model:commitment_revision"]').click();
      await page.waitForURL("**/#model:commitment_revision");
      assert.equal(await page.locator(".model-fields .model-field").count(), 9);
      await page.locator('.model-actions a[href="#command:revise_commitment"]').click();
      await page.waitForURL("**/#command:revise_commitment");
      await page.locator(".tool-usage-detail").waitFor();
      await page.goBack();
      await page.locator(".model-detail").waitFor();
      assert.equal(new URL(page.url()).hash, "#model:commitment_revision");
      await page.reload();
      await page.locator(".model-detail").waitFor();
      assert.equal(await page.locator(".model-fields .model-field").count(), 9);
      await page.goto(url.replace("model:commitment", "model:unknown"));
      await page.locator(".model-picker").waitFor();
      assert.equal(await page.locator(".model-picker a").count(), 9);
      await page.goto(url.split("#")[0]);
      await page
        .getByRole("tab", { name: locale === "de" ? "Datenmodell" : "Data model", exact: true })
        .click();
      await page.locator(".model-picker").waitFor();
      await page.goBack();
      await page
        .getByRole("tab", { name: locale === "de" ? "Ressourcen" : "Resources", exact: true })
        .waitFor();
      assert.equal(
        await page
          .getByRole("tab", { name: locale === "de" ? "Ressourcen" : "Resources", exact: true })
          .getAttribute("aria-selected"),
        "true",
      );
      for (const [key, count, groupText] of [
        ["party", 12, locale === "de" ? "Stammdaten" : "Master data"],
        ["item", 13, locale === "de" ? "Stammdaten" : "Master data"],
        ["shipment", 7, locale === "de" ? "Lager & Versand" : "Warehouse & shipping"],
      ]) {
        await page.goto(url.replace("model:commitment", `model:${key}`));
        await page.locator(".model-detail").waitFor();
        assert.equal(await page.locator(".model-fields .model-field").count(), count);
        assert.ok(
          (await page.locator('.model-groups button[aria-pressed="true"]').innerText()).includes(
            groupText,
          ),
        );
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          true,
        );
      }
      await page.locator(".model-groups button").first().click();
      assert.equal(await page.locator(".model-picker a").count(), 35);
      await page.locator('.model-picker a[href="#model:party"]').click();
      await search.fill("tracking_number");
      assert.equal(await page.locator(".model-picker a").count(), 1);
      await page.locator('.model-picker a[href="#model:shipment_package"]').click();
      await page.locator('.related-models a[href="#model:shipment"]').click();
      await page.goBack();
      await page.locator('.model-detail[aria-label="ShipmentPackage"]').waitFor();
      await page.locator(".model-groups").evaluate((el) => el.scrollIntoView({ block: "start" }));
      await page.screenshot({ path: `/tmp/model-erp-${locale}-${width}.png` });
      assert.deepEqual(errors, []);
      console.log(
        `PASS ${locale}/${width}: fields, search, links, action, Back, reload, unknown hash, ERP groups, cross-group search, no overflow/errors`,
      );
      await page.close();
    }
} finally {
  await browser.close();
}
