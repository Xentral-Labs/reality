// Synthetic HTTP responses: this acceptance test never writes tenant data.
import { writeFile, unlink, mkdir } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const base = process.env.REALITY_BROWSER_URL || "http://127.0.0.1:5194";
const output = process.env.FINANCE_SCREENSHOTS || "/private/tmp/reality-148-browser";
await mkdir(output, { recursive: true });
const harnessFiles = [
  [
    new URL("../finance-acceptance.html", import.meta.url),
    '<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><div id="root"></div><script type="module" src="/src/finance/acceptance-harness.tsx"></script></body></html>\n',
  ],
  [
    new URL("../src/finance/acceptance-harness.tsx", import.meta.url),
    'import React from "react";\nimport { createRoot } from "react-dom/client";\nimport { AccountSettings } from "./AccountSettings";\nimport { LocalizationProvider, type Language } from "../localization";\nimport "../tailwind.css";\nconst language = new URLSearchParams(location.search).get("language") as Language || "en";\ncreateRoot(document.getElementById("root")!).render(<LocalizationProvider preferences={{language, locale:"en-GB", timezone:"UTC"}}><main style={{padding:20, width:"100%", boxSizing:"border-box"}}><AccountSettings tenantId="fixture" /></main></LocalizationProvider>);\n',
  ],
];
const created = [];

import assert from "node:assert/strict";
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE || undefined,
});
const labels = {
  en: "Operational accounts",
  de: "Operative Konten",
  nl: "Operationele rekeningen",
  es: "Cuentas operativas",
};
let captures = 0;
try {
  for (const [path, contents] of harnessFiles) {
    await writeFile(path, contents, { flag: "wx" });
    created.push(path);
  }
  for (const language of ["en", "de", "nl", "es"])
    for (const theme of ["light", "dark"])
      for (const width of [390, 1024, 1440]) {
        const page = await browser.newPage({ viewport: { width, height: 950 } });
        const errors = [];
        page.on("pageerror", (e) => errors.push(e.message));
        const data = {
          revision: 1,
          roles: { accounts_receivable: "Customer receivables", cash: "Cash and bank" },
          defaults: { accounts_receivable: "a" },
          accounts: [
            {
              id: "a",
              code: "AR",
              name: "Customer receivables",
              role: "accounts_receivable",
              state: "active",
              revision: 1,
            },
          ],
        };
        let proposed;
        let confirmed = 0;
        await page.route("**/api/tenants/fixture/**", async (route) => {
          const url = route.request().url();
          if (url.endsWith("/proposals")) {
            proposed = route.request().postDataJSON();
            return route.fulfill({ json: { id: "proposal", status: "proposed" } });
          }
          if (url.endsWith("/approve")) {
            confirmed++;
            data.revision++;
            data.accounts.push({
              id: "new",
              code: proposed.arguments.code,
              name: proposed.arguments.name,
              role: "cash",
              state: "active",
              revision: 1,
            });
            return route.fulfill({ json: { status: "executed" } });
          }
          return route.fulfill({ json: data });
        });
        await page.goto(`${base}/finance-acceptance.html?language=${language}`);
        await page.evaluate((theme) => {
          document.documentElement.dataset.theme = theme;
          document.documentElement.classList.toggle("dark", theme === "dark");
        }, theme);
        await page.getByText(labels[language], { exact: true }).click();
        await page.locator('input[name="code"]').waitFor();
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          true,
          `overflow ${language}/${theme}/${width}`,
        );
        if (language === "en" && theme === "light" && width === 390) {
          await page.locator('input[name="code"]').fill("BANK");
          await page.locator('input[name="name"]').fill("Main bank");
          await page.locator('select[name="role"]').selectOption("cash");
          await page.getByRole("button", { name: "Create account", exact: true }).click();
          await page.getByRole("heading", { name: "Confirm account change" }).waitFor();
          assert.equal(confirmed, 0);
          await page.getByRole("button", { name: "Confirm", exact: true }).click();
          await page.getByRole("cell", { name: "Main bank", exact: true }).waitFor();
          assert.equal(confirmed, 1);
        }
        await page.screenshot({
          path: `${output}/finance-${language}-${theme}-${width}.png`,
          fullPage: true,
        });
        assert.deepEqual(errors, []);
        captures++;
        await page.close();
      }
  console.log(
    `${captures} viewport/locale/theme cases passed; create-preview-confirm verified with synthetic HTTP responses.`,
  );
} finally {
  await browser.close();
  for (const path of created) await unlink(path);
}
