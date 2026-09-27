import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

import { localizeRefusal } from "../src/refusals.ts";

// A German stand-in for the web's t() and formatters: the contract is the interpolation.
const german = {
  "Line {index} requires a stated amount; it is never calculated.":
    "Position {index} braucht einen angegebenen Betrag; er wird nie berechnet.",
  "{field} cannot be negative.": "{field} darf nicht negativ sein.",
  "Lead time days": "Lieferzeit in Tagen",
  "The amount {amount} is due on {day}.": "Der Betrag {amount} ist am {day} fällig.",
  "Broken {index}.": "Kaputt.",
};
const helpers = {
  t: (source) => german[source] ?? source,
  exact: (value, keepZeros) =>
    keepZeros ? String(value).replace(".", ",") : String(value).replace(".", ","),
  date: (value) => value.split("-").reverse().join("."),
};
const refusal = (template, values, detail = "English sentence.") => ({
  detail,
  template,
  values,
});

// FR-005: values keep their place, formatted for the language, terms translated.
test("a coded refusal is shown with its values in place", () => {
  assert.equal(
    localizeRefusal(
      refusal("Line {index} requires a stated amount; it is never calculated.", {
        index: { value: "3", kind: "number" },
      }),
      helpers,
    ),
    "Position 3 braucht einen angegebenen Betrag; er wird nie berechnet.",
  );
  assert.equal(
    localizeRefusal(
      refusal("{field} cannot be negative.", {
        field: { value: "Lead time days", kind: "term" },
      }),
      helpers,
    ),
    "Lieferzeit in Tagen darf nicht negativ sein.",
  );
  assert.equal(
    localizeRefusal(
      refusal("The amount {amount} is due on {day}.", {
        amount: { value: "59.50", kind: "amount" },
        day: { value: "2026-09-27", kind: "date" },
      }),
      helpers,
    ),
    "Der Betrag 59,50 ist am 27.09.2026 fällig.",
  );
});

test("text values are shown exactly as the service sent them", () => {
  const english = { ...helpers, t: (source) => source };
  assert.equal(
    localizeRefusal(
      refusal("Code {code} exists.", { code: { value: "NET30.5", kind: "text" } }),
      english,
    ),
    "Code NET30.5 exists.",
  );
});

// FR-005 fallback: never show a broken sentence.
test("a translation that drops a placeholder falls back to the English sentence", () => {
  assert.equal(
    localizeRefusal(
      refusal("Broken {index}.", { index: { value: "1", kind: "number" } }, "Broken 1."),
      helpers,
    ),
    "Broken 1.",
  );
});

test("an uncoded or unknown refusal shows the English sentence", () => {
  assert.equal(localizeRefusal({ detail: "Plain." }, helpers), "Plain.");
  assert.equal(localizeRefusal(refusal("Unknown {x}.", {}, "Unknown."), helpers), "Unknown.");
});

// FR-005: one translation point for every form, the chat stream included.
test("request and the chat stream localize the refusal once for every form", () => {
  const api = readFileSync(new URL("../src/api.ts", import.meta.url), "utf8");
  const stream = readFileSync(new URL("../src/chatStream.ts", import.meta.url), "utf8");
  // request, sendChatRequest and the chat stream's error event.
  assert.equal(api.match(/refusalError\(/g)?.length, 3);
  assert.match(stream, /refusal: event/);
});

// FR-009: behaviour never depends on refusal text.
test("no web code compares a refusal's text", () => {
  const root = new URL("../src/", import.meta.url).pathname;
  const files = [];
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      const path = join(dir, name);
      if (statSync(path).isDirectory()) walk(path);
      else if (/\.(ts|tsx)$/.test(name) && !name.startsWith("localization")) files.push(path);
    }
  };
  walk(root);
  const comparesText = (line) => /\.message\s*===\s*["'`]/.test(line) && !/typeof\s/.test(line);
  const offenders = files.filter((file) =>
    readFileSync(file, "utf8").split("\n").some(comparesText),
  );
  // Positive control: the comparison the chat page used before spec 286 is caught.
  assert.ok(comparesText('        error.message === "ChatSession not found."'));
  assert.deepEqual(offenders, []);
});
