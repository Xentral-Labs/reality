import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { auditLocalization, discoverSourceFiles, formatResults } from "./i18n-audit-lib.mjs";

function fixture({
  source = '<button aria-label="Save">Save</button>',
  de = 'Save: "Speichern"',
  nl = 'Save: "Opslaan"',
  es = 'Save: "Guardar"',
} = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "reality-i18n-"));
  fs.mkdirSync(path.join(root, "src", "nested"), { recursive: true });
  fs.writeFileSync(
    path.join(root, "src", "nested", "View.tsx"),
    `export const View = () => (${source});`,
  );
  fs.writeFileSync(
    path.join(root, "src", "localization.tsx"),
    `const dictionaries = { de: { ${de} }, nl: { ${nl} }, es: { ${es} } };`,
  );
  return root;
}

test("discovers nested TypeScript and TSX source deterministically", () => {
  const root = fixture();
  fs.writeFileSync(path.join(root, "src", "A.ts"), 'export const label = t("Review order");');
  assert.deepEqual(
    discoverSourceFiles(path.join(root, "src")).map((file) => path.relative(root, file)),
    ["src/A.ts", "src/nested/View.tsx"],
  );
});

test("reports one passing result per advertised language for complete catalogs", () => {
  const root = fixture();
  const results = auditLocalization({
    sourceRoot: path.join(root, "src"),
    localizationFile: path.join(root, "src", "localization.tsx"),
  });
  assert.deepEqual(
    results.map(({ language, status }) => [language, status]),
    [
      ["en", "pass"],
      ["de", "pass"],
      ["nl", "pass"],
      ["es", "pass"],
    ],
  );
});

test("reports missing and blank translations by language in one run", () => {
  const root = fixture({ nl: "", es: 'Save: ""' });
  const results = auditLocalization({
    sourceRoot: path.join(root, "src"),
    localizationFile: path.join(root, "src", "localization.tsx"),
  });
  assert.deepEqual(
    results.map(({ language, status }) => [language, status]),
    [
      ["en", "pass"],
      ["de", "pass"],
      ["nl", "fail"],
      ["es", "fail"],
    ],
  );
  assert.equal(results[2].missing[0].source, "Save");
  assert.equal(results[3].invalid[0].source, "Save");
  assert.match(
    formatResults(results, root),
    /nl: FAIL[\s\S]*missing: Save[\s\S]*es: FAIL[\s\S]*invalid: Save/u,
  );
});

test("accepts reviewed invariants but rejects unapproved English-equal entries", () => {
  const root = fixture({
    source: "<><span>Reality</span><span>Save</span></>",
    de: 'Save: "Save"',
    nl: 'Save: "Save"',
    es: 'Save: "Save"',
  });
  const results = auditLocalization({
    sourceRoot: path.join(root, "src"),
    localizationFile: path.join(root, "src", "localization.tsx"),
  });
  assert.equal(results[1].invariant, 1);
  assert.equal(results[1].invalid[0].source, "Save");
});

test("ignores machine values while auditing accessibility text", () => {
  const root = fixture({
    source: '<div aria-label="Save"><span>api/v1/orders</span><span>UTC</span></div>',
  });
  const results = auditLocalization({
    sourceRoot: path.join(root, "src"),
    localizationFile: path.join(root, "src", "localization.tsx"),
  });
  assert.equal(results[0].discovered, 1);
  assert.ok(results.every(({ status }) => status === "pass"));
});
