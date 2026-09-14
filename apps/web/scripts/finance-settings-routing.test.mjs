import assert from "node:assert/strict";
import test from "node:test";
import { readSelection, selectionUrl, companySelection } from "../src/unified/routing.ts";
import { pageIntroduction } from "../src/unified/pageIntroduction.ts";
import { reference } from "./action-discovery-fixture.mjs";

test("Finance settings is a bookmarkable company-scoped destination", () => {
  const held = readSelection(
    new URL("https://example.test/app/finance?tenant=company-a&finance_view=settings"),
  );
  assert.equal(held.financeView, "settings");
  const reopened = readSelection(new URL(selectionUrl(held), "https://example.test"));
  assert.equal(reopened.financeView, "settings");
  assert.equal(reopened.tenant, "company-a");
  const switched = companySelection(held, "company-b");
  assert.equal(switched.financeView, "settings");
  assert.equal(switched.tenant, "company-b");
  assert.equal(pageIntroduction(held).title, "Finance");
  assert.match(pageIntroduction(held).description, /accounts.*classifications.*source/i);
});

test("all financial management entries lead to Finance settings", () => {
  for (const key of ["navigate_accounts", "navigate_finance_references"]) {
    const entry = reference.discovery.entries.find((row) => row.key === key);
    assert.deepEqual(entry.destination, {
      route: "finance",
      financeView: "settings",
      ...(key === "navigate_finance_references" ? { financeSettings: "cost-centers" } : {}),
    });
    assert.equal(entry.access, "owner");
  }
});

test("Finance settings areas survive links and invalid areas fall back to accounts", () => {
  for (const area of ["accounts", "cost-centers", "classifications", "source-mappings"]) {
    const selected = readSelection(
      new URL(`https://example.test/app/finance?finance_view=settings&finance_settings=${area}`),
    );
    assert.equal(selected.financeSettings, area);
    assert.equal(
      readSelection(new URL(selectionUrl(selected), "https://example.test")).financeSettings,
      area,
    );
  }
  assert.equal(
    readSelection(new URL("https://example.test/app/finance?finance_settings=unknown"))
      .financeSettings,
    "accounts",
  );
});
