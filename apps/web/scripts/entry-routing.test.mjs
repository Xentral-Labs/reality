import assert from "node:assert/strict";
import test from "node:test";
import { resolveEntry, safeAccountReturn } from "../src/entryRouting.ts";

const entry = (path) => resolveEntry(new URL(path, "https://app.example"));
test("current routes stay current and unknown routes are explicit", () => {
  for (const path of [
    "/app",
    "/app/warehouse?tenant=t1",
    "/app/inspector?inspector_view=graph",
    "/app/free-play?tenant=t1",
  ])
    assert.equal(entry(path).kind, "app");
  assert.equal(entry("/app/not-real").kind, "missing");
  assert.equal(entry("/app/work/foreign").kind, "missing");
});
test("legacy register links preserve the tenant and select the matching tab", () => {
  for (const [path, target, key, value] of [
    ["/app/movements", "/app/warehouse", "warehouse_view", "movements"],
    ["/app/reservations", "/app/warehouse", "warehouse_view", "reservations"],
    ["/app/commitments", "/app/orders-deliveries", "orders_view", "deliveries"],
    ["/app/orders", "/app/orders-deliveries", "orders_view", "customer-orders"],
    ["/app/payments", "/app/finance", "finance_view", "payments"],
    ["/app/journal", "/app/finance", "finance_view", "journal"],
    ["/app/items", "/app/master-data", "family", "item"],
    ["/app/profile", "/app/settings", "settings_view", "personal"],
    ["/app/documents", "/app/data-sources", "data_view", "documents"],
    ["/app/explorer", "/app/inspector", "inspector_view", "records"],
  ]) {
    const result = entry(path + "?tenant=ten_1&q=bike&confirm=1&proposal=old");
    assert.equal(result.kind, "redirect");
    const url = new URL(result.href, "https://app.example");
    assert.equal(url.pathname, target);
    assert.equal(url.searchParams.get(key), value);
    assert.equal(url.searchParams.get("tenant"), "ten_1");
    assert.equal(url.searchParams.get("q"), "bike");
    assert.equal(url.searchParams.has("confirm"), false);
    assert.equal(url.searchParams.has("proposal"), false);
  }
});
test("retired entries and trailing slash bookmarks never execute work", () => {
  for (const path of ["/playground", "/playground/runs/pgr_1", "/playground/unknown"])
    assert.equal(entry(path).kind, "retired");
  assert.deepEqual(entry("/app/warehouse/?tenant=t"), {
    kind: "redirect",
    href: "/app/warehouse?tenant=t",
  });
  assert.equal(entry("/app/playground").kind, "retired");
});
test("account returns reject external and malformed destinations", () => {
  assert.equal(safeAccountReturn("/app/warehouse?tenant=t"), "/app/warehouse?tenant=t");
  assert.equal(
    safeAccountReturn("/app/movements?tenant=t"),
    "/app/warehouse?tenant=t&warehouse_view=movements",
  );
  assert.equal(safeAccountReturn("/playground/runs/pgr_1"), "/playground/runs/pgr_1");
  for (const path of [
    "https://evil.example/app",
    "//evil.example/app",
    "/\\evil.example/app",
    "/app/../login",
    "/app/missing",
    "/app#token=secret",
  ])
    assert.equal(safeAccountReturn(path), null, path);
});

test("object prototype names are never routes", () => {
  for (const path of ["/app/__proto__", "/app/constructor", "/app/toString"])
    assert.equal(entry(path).kind, "missing");
});

test("Demo Data has a direct tenant-preserving app entry", () => {
  assert.deepEqual(entry("/app/demo-data?tenant=demo"), { kind: "app" });
  assert.equal(safeAccountReturn("/app/demo-data?tenant=demo"), "/app/demo-data?tenant=demo");
});
test("legacy aliases preserve validated language", () => {
  for (const lang of ["en", "de", "nl", "es"])
    assert.equal(
      new URL(entry(`/profile?lang=${lang}`).href, "https://app.example").searchParams.get("lang"),
      lang,
    );
  assert.equal(
    new URL(entry("/profile?lang=invalid").href, "https://app.example").searchParams.has("lang"),
    false,
  );
});
