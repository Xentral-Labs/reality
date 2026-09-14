import { test } from "node:test";
import assert from "node:assert/strict";
import {
  emptyDraft,
  readDraft,
  validateDraft,
  draftForRule,
  typedValue,
  conditionOperand,
} from "../src/unified/guidedRuleDraft.ts";
test("typed fields preserve false, zero and decimal precision", () => {
  assert.equal(typedValue("False", "boolean"), false);
  assert.equal(typedValue("0", "integer"), 0);
  assert.equal(typedValue("12345678901234567890.012345", "decimal"), "12345678901234567890.012345");
  assert.throws(() => typedValue("maybe", "boolean"));
  assert.throws(() => typedValue("1.2", "integer"));
  assert.throws(() => typedValue("", "decimal"));
  assert.deepEqual(conditionOperand("true, false", "in", "boolean"), [true, false]);
});
test("new version preserves advanced fields and scopes from matching proposal", () => {
  const rule = {
    ...emptyDraft(),
    id: "r",
    version: 2,
    status: "active",
    logical_name: "stable",
    conditions: [
      {
        path: "status",
        scope: "source",
        operator: "equals",
        value_type: "string",
        operand: "paid",
      },
    ],
  };
  const draft = draftForRule(rule, [
    {
      type: "implementation_proposal",
      payload: { rule_id: "other", draft: { normalization: ["lower"] } },
    },
    {
      type: "implementation_proposal",
      payload: {
        rule_id: "r",
        draft: {
          normalization: ["trim"],
          value_mapping: { YES: true },
          source_line_id_path: "sku",
        },
      },
    },
  ]);
  assert.deepEqual(draft.normalization, ["trim"]);
  assert.deepEqual(draft.value_mapping, { YES: true });
  assert.equal(draft.conditions[0].scope, "source");
  assert.equal(draft.logical_name, "stable");
  assert.ok(!("id" in draft));
});
test("nested rule validates paths and prevents incomplete typed inputs", () => {
  const draft = {
    ...emptyDraft(),
    logical_name: "priority",
    source_system: "shop",
    source_type: "order",
    predicate: "priority",
    output_path: "priority",
    conditions: [
      {
        mode: "any",
        conditions: [
          {
            path: "total",
            scope: "source",
            operator: "greater_than",
            value_type: "decimal",
            operand: "1.25",
          },
        ],
      },
    ],
  };
  assert.equal(validateDraft(draft).conditions[0].conditions[0].operand, "1.25");
  assert.throws(() => validateDraft({ ...draft, conditions: [{ mode: "any", conditions: [] }] }));
  assert.throws(() => validateDraft({ ...draft, subject_resolver: "source_document_lines" }));
  assert.throws(() =>
    validateDraft({ ...draft, conditions: Array(21).fill(draft.conditions[0].conditions[0]) }),
  );
});

test("typed constants and mixed source/line mappings survive validation", () => {
  const draft = {
    ...emptyDraft(),
    logical_name: "line.flag",
    source_system: "shop",
    source_type: "order",
    predicate: "line.flag",
    subject_resolver: "source_document_lines",
    iteration_path: "items",
    source_line_id_path: "external_id",
    output_mode: "constant",
    constant_value: "False",
    value_type: "boolean",
    output_scope: "element",
    conditions: [
      { path: "paid", scope: "source", operator: "equals", value_type: "boolean", operand: "true" },
      {
        path: "quantity",
        scope: "element",
        operator: "greater_than",
        value_type: "integer",
        operand: "0",
      },
    ],
  };
  const result = validateDraft(draft);
  assert.equal(result.constant_value, false);
  assert.equal(result.subject_type, "document_line");
  assert.equal(result.source_line_id_path, "external_id");
  assert.equal(result.conditions[0].scope, "source");
  assert.equal(result.conditions[0].operand, true);
  assert.equal(result.conditions[1].operand, 0);
  assert.equal(draft.constant_value, "False");
});

test("malformed technical conditions fail before rendering or preparing", () => {
  assert.throws(() =>
    readDraft(JSON.stringify({ conditions: [{ mode: "any", conditions: null }] })),
  );
  assert.deepEqual(readDraft("{}").conditions, []);
});

test("editing starts with the latest draft, then active version, and setup stays honest", async () => {
  const { initialRuleDraft, ruleSentence } = await import("../src/unified/guidedRuleDraft.ts");
  const active = {
    ...emptyDraft(),
    id: "active",
    status: "active",
    version: 1,
    predicate: "gift",
    logical_name: "Gift",
    source_system: "shop",
    source_type: "order",
    output_mode: "constant",
    constant_value: false,
    value_type: "boolean",
  };
  const pending = { ...active, id: "pending", status: "draft", version: 2, constant_value: true };
  assert.equal(
    initialRuleDraft({ gap: { question: "Gift" }, rules: [active, pending], entries: [] })
      .constant_value,
    true,
  );
  assert.equal(
    initialRuleDraft({ gap: { question: "Gift" }, rules: [active], entries: [] }).constant_value,
    false,
  );
  const fresh = initialRuleDraft({ gap: { question: "Gift" }, rules: [], entries: [] });
  assert.equal(fresh.logical_name, "Gift");
  assert.equal(fresh.predicate, "");
  assert.match(
    ruleSentence(fresh, (s) => s),
    /Choose/,
  );
  assert.match(
    ruleSentence(active, (s) => s),
    /No/,
  );
});
