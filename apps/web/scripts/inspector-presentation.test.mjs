import { test } from "node:test";
import assert from "node:assert/strict";
import { renderInspectorValue } from "../src/unified/inspectorPresentation.ts";
for (const locale of ["en-GB", "de-DE", "nl-NL", "es-ES"]) {
  test(`Inspector composites use ${locale}, leaving original text untouched`, () => {
    const number = (value) =>
      new Intl.NumberFormat(locale, { maximumFractionDigits: 4 }).format(Number(value));
    const money = (value, currency, precision) =>
      new Intl.NumberFormat(locale, {
        style: "currency",
        currency,
        maximumFractionDigits: precision,
      }).format(value);
    const date = (value) => `DATE(${value})`;
    const dateTime = (value) => `DATETIME(${value})`;
    const parts = [
      { type: "number", value: "1234.5000" },
      { type: "text", value: " pcs · " },
      { type: "money", value: "120.0000", currency: "EUR", precision: 2 },
    ];
    assert.equal(
      renderInspectorValue("raw", parts, { number, money }),
      `${number("1234.5")} pcs · ${money("120", "EUR", 2)}`,
    );
    assert.equal(renderInspectorValue("001234.5000", undefined, { number, money }), "001234.5000");
    assert.equal(
      renderInspectorValue("INV-120.0000", undefined, { number, money }),
      "INV-120.0000",
    );
    assert.equal(
      renderInspectorValue("Maple 120.0000", undefined, { number, money }),
      "Maple 120.0000",
    );
    assert.equal(
      renderInspectorValue(
        "raw",
        [{ type: "money", value: "12.3456", currency: "EUR", precision: 4 }],
        { number, money },
      ),
      money("12.3456", "EUR", 4),
    );
    assert.equal(
      renderInspectorValue(
        "raw",
        [
          { type: "number", value: "2" },
          { type: "text", value: " · " },
          { type: "datetime", value: "2026-09-09T19:09:54+00:00" },
        ],
        { number, money, date, dateTime },
      ),
      `${number("2")} · DATETIME(2026-09-09T19:09:54+00:00)`,
    );
    assert.equal(
      renderInspectorValue(
        "raw",
        [
          { type: "number", value: "2" },
          { type: "text", value: " · 2026-09-09T19:09:54.743897+00:00" },
        ],
        { number, money, date, dateTime },
      ),
      `${number("2")} · DATETIME(2026-09-09T19:09:54.743897+00:00)`,
    );
  });
}
