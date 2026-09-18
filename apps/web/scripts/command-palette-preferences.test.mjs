import { test } from "node:test";
import assert from "node:assert/strict";
import {
  readPalettePreferences,
  writePalettePreferences,
  clearPalettePreferences,
} from "../src/unified/commandPalettePreferences.ts";
function storage() {
  const values = new Map();
  return {
    get length() {
      return values.size;
    },
    key: (i) => [...values.keys()][i],
    getItem: (k) => values.get(k) || null,
    setItem: (k, v) => values.set(k, v),
    removeItem: (k) => values.delete(k),
  };
}
test("preferences retain only bounded references in a user/company namespace", () => {
  const store = storage();
  writePalettePreferences(store, "a", "one", {
    favorites: [
      { key: "page:home", target: { kind: "page", id: "home" }, label: "SECRET", query: "SECRET" },
    ],
    recents: [],
  });
  assert(!store.getItem(store.key(0)).includes("SECRET"));
  assert.equal(readPalettePreferences(store, "a", "one").favorites.length, 1);
  assert.equal(readPalettePreferences(store, "a", "two").favorites.length, 0);
  assert.equal(readPalettePreferences(store, "b", "one").favorites.length, 0);
  clearPalettePreferences(store);
  assert.equal(store.length, 0);
});
test("malformed versions and untrusted targets cannot turn into launch instructions", () => {
  const store = storage();
  writePalettePreferences(store, "a", "one", {
    favorites: [{ key: "x", target: { kind: "url", id: "javascript:evil" } }],
    recents: [],
  });
  assert.deepEqual(readPalettePreferences(store, "a", "one"), { favorites: [], recents: [] });
});

test("storage failures preserve a bounded in-memory fallback across palette mounts", () => {
  const unavailable = {
    getItem() {
      throw Error("disabled");
    },
    setItem() {
      throw Error("disabled");
    },
    removeItem() {
      throw Error("disabled");
    },
    key() {
      return null;
    },
    length: 0,
  };
  assert.equal(
    writePalettePreferences(unavailable, "memory-user", "one", {
      favorites: [{ key: "page:home", target: { kind: "page", id: "home" } }],
      recents: [],
    }),
    false,
  );
  assert.equal(readPalettePreferences(unavailable, "memory-user", "one").favorites.length, 1);
  clearPalettePreferences(unavailable);
  assert.equal(readPalettePreferences(unavailable, "memory-user", "one").favorites.length, 0);
});
