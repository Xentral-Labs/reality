import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const browser = readFileSync(new URL("./mcp-oauth-browser.mjs", import.meta.url), "utf8");

test("personal settings browser supplies the account-scoped journey suggestion list", () => {
  assert.match(
    browser,
    /path === "\/api\/auth\/journey-proposals"[\s\S]+request\.method\(\) === "GET"[\s\S]+reply\(\[\]\)/u,
  );
});
