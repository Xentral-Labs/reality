import { test } from "node:test";
import assert from "node:assert/strict";
import { pageIntroduction } from "../src/unified/pageIntroduction.ts";
import { readSelection } from "../src/unified/routing.ts";
const selection = (path) => readSelection(new URL(`https://example.test/app${path}`));
test("every application destination has a concise introduction", () => {
  for (const route of [
    "",
    "/facts",
    "/inspector",
    "/settings",
    "/orders-deliveries",
    "/copilot",
    "/work",
    "/decisions",
    "/analytics",
    "/master-data",
    "/data-sources",
    "/demo-data",
    "/finance",
    "/warehouse",
    "/attention",
  ]) {
    const intro = pageIntroduction(selection(route));
    assert.ok(intro.title, route);
    assert.ok(intro.description.length > 20 && intro.description.length < 180, route);
  }
});
test("subviews have distinct useful descriptions and aliases remain compatible", () => {
  for (const [route, key, values] of [
    [
      "inspector",
      "inspectorView",
      ["overview", "graph", "facts", "views", "rules", "exceptions", "history", "commands"],
    ],
    ["warehouse", "warehouseView", ["stock", "reservations", "movements"]],
    ["finance", "financeView", ["open-items", "payments", "journal", "settings"]],
    ["master-data", "family", ["customer", "supplier", "item", "location"]],
    ["data-sources", "dataView", ["systems", "records", "documents"]],
    ["orders-deliveries", "ordersView", ["deliveries", "customer-orders", "supplier-orders"]],
    ["settings", "settingsView", ["personal", "company"]],
  ]) {
    const descriptions = values.map(
      (value) => pageIntroduction({ ...selection("/" + route), [key]: value }).description,
    );
    assert.equal(new Set(descriptions).size, values.length, route);
  }
  const base = selection("/inspector");
  assert.deepEqual(
    pageIntroduction({ ...base, inspectorView: "records" }),
    pageIntroduction({ ...base, inspectorView: "facts" }),
  );
  assert.notEqual(
    pageIntroduction({
      ...selection("/orders-deliveries"),
      ordersView: "commitments",
      deliveryType: "customer_delivery",
    }).description,
    pageIntroduction({
      ...selection("/orders-deliveries"),
      ordersView: "commitments",
      deliveryType: "supplier_delivery",
    }).description,
  );
});

test("Sales and Purchasing titles follow existing order and delivery links", () => {
  for (const [query, title] of [
    ["orders_view=customer-orders", "Sales"],
    ["orders_view=supplier-orders", "Purchasing"],
    ["orders_view=deliveries&delivery_type=customer_delivery", "Sales"],
    ["orders_view=deliveries&delivery_type=supplier_delivery", "Purchasing"],
  ])
    assert.equal(pageIntroduction(selection(`/orders-deliveries?${query}`)).title, title);
});
