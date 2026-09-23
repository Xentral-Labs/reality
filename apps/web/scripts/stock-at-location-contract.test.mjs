import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = (name) => readFile(new URL(`../src/${name}`, import.meta.url), "utf8");

test("the place scope lives in the URL beside the item scope", async () => {
  const routing = await source("unified/routing.ts");
  assert.match(routing, /location: string;/);
  assert.match(routing, /location: url\.searchParams\.get\("location"\) \|\| "",/);
  assert.match(routing, /for \(const key of \["item", "location", "entry", "state"\] as const\)/);
});

test("the warehouse read passes the place scope to the shared register", async () => {
  const api = await source("api.ts");
  const warehouse = api.match(/warehouse:\s*\([\s\S]*?\n {4}\),/)?.[0] || "";
  assert.match(warehouse, /location = ""/);
  assert.match(warehouse, /location \? \{ location_id: location \} : \{\}/);
  assert.match(warehouse, /location_id: string \| null;/);
});

test("a scoped register names its scope and can clear it", async () => {
  const page = await source("unified/WarehousePage.tsx");
  assert.match(
    page,
    /operationsApi\.warehouse\(tenant, view, q, state, item, page, table, location\)/,
  );
  assert.match(page, /Clear location filter/);
  assert.match(page, /Quantities are what lies at this location, not the whole company\./);
  assert.match(page, /Reservations held at this location\./);
  assert.match(page, /Movements into and out of this location\./);
});

test("a scoped movement row says which side of the place it is on", async () => {
  const page = await source("unified/WarehousePage.tsx");
  assert.match(page, /function scopeSide\(/);
  for (const side of ["Within this location", "Into this location", "Out of this location"])
    assert.match(page, new RegExp(side));
  assert.match(page, /location \? `\$\{t\(scopeSide\(row, location\)\)\} · ` : ""/);
});

test("a location quantity opens the pair, and the pair reaches both registers", async () => {
  const page = await source("unified/WarehousePage.tsx");
  assert.match(page, /shown\.kind === "stock"/);
  assert.match(page, /const \[itemId, locationId\] = shown\.id\.split\(":"\)/);
  assert.match(page, /location: locationId/);
  const inline = await source("unified/InlinePreview.tsx");
  assert.match(inline, /followActions\?: \(/);
  const inspector = await source("unified/Inspector.tsx");
  assert.match(inspector, /actions\?: \(target: \{ kind: string; id: string \}\) => ReactNode;/);
});

test("a location in master data opens the warehouse scoped to it", async () => {
  const master = await source("unified/MasterDataPage.tsx");
  assert.match(master, /family === "item" \|\| family === "location"/);
  assert.match(master, /location: family === "location" \? detail\.id : ""/);
});

test("the new wording is translated in every edition", async () => {
  const dictionary = await source("localization.tsx");
  for (const key of [
    "Clear location filter",
    "Into this location",
    "Out of this location",
    "Within this location",
    "Movements here",
    "Reservations here",
    "Held here",
    "Physical stock by item",
  ]) {
    const entries = dictionary.split(`"${key}":`).length - 1;
    assert.ok(entries >= 3, `${key} is translated ${entries} times`);
  }
});
