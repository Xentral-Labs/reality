import assert from "node:assert/strict";
import test from "node:test";
import { signupPreferences } from "../src/signupPreferences.ts";

test("an explicit language choice on the signup page wins", () => {
  assert.deepEqual(signupPreferences("de", ["en-US", "en"], "Europe/Berlin"), {
    language: "de",
    timezone: "Europe/Berlin",
  });
});

test("without a choice the browser's first supported request is taken", () => {
  assert.equal(signupPreferences(undefined, ["nl-BE", "fr-FR"], "Europe/Brussels").language, "nl");
  assert.equal(signupPreferences(undefined, ["es-419", "en-GB"], "America/Bogota").language, "es");
  assert.equal(signupPreferences(undefined, ["DE"], "Europe/Vienna").language, "de");
});

test("an unsupported request states no language, so the server keeps its default", () => {
  assert.deepEqual(signupPreferences(undefined, ["fr-FR", "it-IT"], "Europe/Paris"), {
    timezone: "Europe/Paris",
  });
  assert.deepEqual(signupPreferences(undefined, [], undefined), {});
});

test("the time zone is stated as the browser resolved it", () => {
  for (const zone of ["Europe/Berlin", "America/New_York", "Asia/Tokyo", "UTC"]) {
    assert.equal(signupPreferences("en", [], zone).timezone, zone, zone);
  }
});

test("an unusable or oversized zone is omitted rather than rejected at the boundary", () => {
  assert.equal(signupPreferences("en", [], "").timezone, undefined);
  assert.equal(signupPreferences("en", [], "   ").timezone, undefined);
  assert.equal(signupPreferences("en", [], undefined).timezone, undefined);
  // The signup request caps this field; a request that would be refused is never sent.
  assert.equal(signupPreferences("en", [], `Europe/${"B".repeat(80)}`).timezone, undefined);
});

test("the hint carries presentation only, never a locale or another account value", () => {
  assert.deepEqual(Object.keys(signupPreferences("de", ["de"], "Europe/Berlin")).sort(), [
    "language",
    "timezone",
  ]);
});
