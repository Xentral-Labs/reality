import assert from "node:assert/strict";
import test from "node:test";
import {
  readSelection,
  selectionUrl,
  companySelection,
  navigationSelection,
  unifiedPath,
  cockpitOriginSelection,
  cockpitReturnSelection,
} from "../src/unified/routing.ts";
import { resolveEntry } from "../src/entryRouting.ts";
import { pageIntroduction } from "../src/unified/pageIntroduction.ts";

const parse = (path) => readSelection(new URL(path, "https://example.test"));

test("cockpit is additive; the ordinary entry remains Home", () => {
  assert.equal(parse("/app").route, "home");
  assert.equal(unifiedPath("/app/cockpit"), true);
  assert.deepEqual(resolveEntry(new URL("https://example.test/app/cockpit")), { kind: "app" });
  assert.equal(parse("/app/cockpit").route, "cockpit");
  assert.equal(parse("/app/cockpit").cockpitDay, "today");
  assert.equal(pageIntroduction(parse("/app/cockpit")).title, "Control Tower");
});

test("day, site, measure, case, basis and independent live window survive bookmarks", () => {
  const selected = parse(
    "/app/cockpit?tenant=a&cockpit_day=2026-10-06&cockpit_location=loc_1&cockpit_measure=risk&cockpit_case=case_1&cockpit_basis=basis_1&cockpit_minutes=60",
  );
  const reopened = parse(selectionUrl(selected));
  for (const key of [
    "route",
    "tenant",
    "cockpitDay",
    "cockpitLocation",
    "cockpitMeasure",
    "cockpitCase",
    "cockpitBasis",
    "cockpitMinutes",
  ])
    assert.equal(reopened[key], selected[key], key);
  assert.equal(reopened.cockpitDay, "2026-10-06");
  assert.equal(reopened.cockpitMinutes, 60);
});

test("invalid dates and unsupported measures/windows fall back without accepting a return URL", () => {
  for (const day of ["2026-02-30", "2026-13-01", "yesterday", "2026-1-2"])
    assert.equal(parse(`/app/cockpit?cockpit_day=${day}`).cockpitDay, "today");
  const selected = parse(
    "/app/cockpit?cockpit_measure=whatever&cockpit_minutes=999&return=https://evil.test",
  );
  assert.equal(selected.cockpitMeasure, "due");
  assert.equal(selected.cockpitMinutes, 15);
  assert.equal(selectionUrl(selected).includes("evil"), false);
});

test("specialist detail and return carry only structured same-company cockpit context", () => {
  const cockpit = parse(
    "/app/cockpit?tenant=a&cockpit_day=2026-10-06&cockpit_location=loc_a&cockpit_measure=risk&cockpit_case=case_a&cockpit_minutes=5",
  );
  const detail = navigationSelection(cockpit, {
    route: "orders-deliveries",
    ordersView: "customer-orders",
    entry: "doc_a",
    cockpitOrigin: cockpitOriginSelection(cockpit),
  });
  const reopened = parse(selectionUrl(detail));
  assert.equal(reopened.entry, "doc_a");
  assert.equal(reopened.cockpitOrigin.tenant, "a");
  const returned = cockpitReturnSelection(reopened);
  assert.equal(returned.route, "cockpit");
  assert.equal(returned.cockpitDay, "2026-10-06");
  assert.equal(returned.cockpitLocation, "loc_a");
  assert.equal(returned.cockpitMeasure, "risk");
  assert.equal(returned.cockpitMinutes, 5);
  assert.equal(returned.entry, "");
});

test("untrusted origins cannot contain external paths or another company's context", () => {
  const valid = cockpitOriginSelection(parse("/app/cockpit?tenant=a"));
  for (const value of [
    { ...valid, tenant: "b" },
    { ...valid, returnUrl: "https://evil.test" },
    "https://evil.test",
    null,
  ]) {
    const selected = parse(
      `/app/inspector?tenant=a&cockpit_origin=${encodeURIComponent(JSON.stringify(value))}`,
    );
    assert.equal(selected.cockpitOrigin, undefined);
    assert.equal(cockpitReturnSelection(selected), null);
  }
});

test("company change drops pinned dates, identities and origin even when stale changes are supplied", () => {
  const selected = parse(
    "/app/cockpit?tenant=a&cockpit_day=2026-10-06&cockpit_location=loc_a&cockpit_case=case_a&cockpit_basis=old&cockpit_minutes=60",
  );
  selected.cockpitOrigin = cockpitOriginSelection(selected);
  const reset = companySelection(selected, "b");
  assert.equal(reset.cockpitDay, "today");
  assert.equal(reset.cockpitLocation, "");
  assert.equal(reset.cockpitCase, "");
  assert.equal(reset.cockpitBasis, "");
  assert.equal(reset.cockpitOrigin, undefined);
  assert.equal(reset.cockpitMinutes, 60);
  assert.equal(
    navigationSelection(selected, { tenant: "b", cockpitOrigin: selected.cockpitOrigin })
      .cockpitOrigin,
    undefined,
  );
});
