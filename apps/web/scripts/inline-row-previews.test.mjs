import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = async (name) => readFile(new URL(`../src/unified/${name}`, import.meta.url), "utf8");

test("shared inline previews expose disclosure and trace semantics", async () => {
  const preview = await source("InlinePreview.tsx");
  assert.match(preview, /aria-expanded/);
  assert.match(preview, /aria-controls/);
  assert.match(preview, /data-action-meaning="preview"/);
  assert.match(preview, /className="erp-preview-trigger"/);
  assert.match(preview, /<span className="sr-only">/);
  assert.doesNotMatch(preview, /className="br-btn"[\s\S]*data-action-meaning="preview"/);
  assert.match(preview, /ChevronDown/);
  assert.match(preview, /ChevronRight/);
  assert.match(preview, /InlineInspector/);
  assert.match(preview, /Open full explanation/);
});

test("preview placement and compact layout remain stable", async () => {
  const table = await source("RegisterTable.tsx");
  const inspector = await source("Inspector.tsx");
  const css = await readFile(new URL("../src/tailwind.css", import.meta.url), "utf8");
  assert.match(table, /erp-preview-action/);
  assert.match(table, /erp-actions-cell/);
  assert.match(table, /visible\.length/);
  assert.match(inspector, /md:grid-cols-2/);
  assert.match(inspector, /md:col-span-2/);
  assert.match(inspector, /compactMeaningIsRedundant/);
  assert.match(inspector, /items-baseline/);
  assert.match(table, /data-inline-preview/);
  assert.doesNotMatch(css, /\.erp-table td:last-child \.br-btn/);
  assert.match(css, /\.erp-actions-cell \.erp-preview-action:hover/);
  assert.match(css, /background: transparent !important/);
});

test("sticky identity cells share the row highlight", async () => {
  const css = await readFile(new URL("../src/tailwind.css", import.meta.url), "utf8");
  assert.match(
    css,
    /\[data-selectable="true"\] \.erp-table tr:not\(\[data-inline-preview\]\):hover td:nth-child\(2\)\s*\{\s*background: var\(--color-surface-muted\);/,
  );
});

test("expanded preview rows keep their background while the pointer moves over them", async () => {
  const preview = await source("InlinePreview.tsx");
  const css = await readFile(new URL("../src/tailwind.css", import.meta.url), "utf8");
  assert.match(preview, /<tr data-inline-preview>/);
  assert.match(css, /\.erp-table tr:not\(\[data-inline-preview\]\):hover td/);
  assert.doesNotMatch(css, /\.erp-table tr:hover td/);
});

test("daily work lists render previews inline instead of WorkDrawer", async () => {
  for (const name of ["CommitmentsPage.tsx", "AttentionPage.tsx", "DecisionsPage.tsx"]) {
    const page = await source(name);
    assert.match(page, /WorkPreview/);
    assert.doesNotMatch(page, /<WorkDrawer/);
  }
});

test("workspace registers use explicit table preview rows", async () => {
  for (const name of [
    "OrdersPage.tsx",
    "WarehousePage.tsx",
    "FinancePage.tsx",
    "MasterDataPage.tsx",
  ]) {
    const page = await source(name);
    assert.match(page, /TablePreview/);
    assert.match(page, /PreviewButton/);
  }
});

test("workspace row cells keep secondary actions inside the expanded preview", async () => {
  const preview = await source("InlinePreview.tsx");
  assert.match(preview, /mt-5 flex flex-wrap justify-end gap-2/);
  for (const name of ["OrdersPage.tsx", "WarehousePage.tsx", "FinancePage.tsx"]) {
    const page = await source(name);
    assert.match(page, /<PreviewButton[\s\S]*?<\/td>[\s\S]*?<TablePreview/);
    assert.match(page, /<TablePreview[\s\S]*?<InlineInspector[\s\S]*?<button/);
    assert.doesNotMatch(page, /<ActionIcon/);
  }
});

test("navigation filtering editing and work do not reuse disclosure chevrons", async () => {
  const preview = await source("InlinePreview.tsx");
  const table = await source("RegisterTable.tsx");
  assert.match(preview, /ArrowRight/);
  assert.match(preview, /ListFilter/);
  assert.match(preview, /Pencil/);
  assert.match(preview, /Play/);
  assert.doesNotMatch(table, /\bEye\b/);
  assert.doesNotMatch(table, /position === 0/);
  assert.match(table, /meaning === "filter"/);
  assert.match(table, /meaning === "edit"/);
  assert.match(table, /meaning === "work"/);
  assert.match(table, /ExternalLink/);
});
