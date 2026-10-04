import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = (name) => readFile(new URL(`../src/${name}`, import.meta.url), "utf8");

test("signup links retain the selected language", async () => {
  const auth = await source("Auth.tsx");
  assert.doesNotMatch(auth, /href="\/signup"/);
  assert.match(auth, /languageHref\("\/signup",/);
});

test("reservation review describes a proposed effect", async () => {
  const card = await source("unified/ActionCard.tsx");
  assert.match(card, /key === "applied"\s*\? "Reserved after confirming"/);
});
