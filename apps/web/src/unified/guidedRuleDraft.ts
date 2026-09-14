import type { RealityGapCondition, RealityGapDetail } from "../api";
export type Rule = RealityGapDetail["rules"][number];
export type RuleDraft = Omit<Rule, "id" | "version" | "status" | "summary"> & {
  normalization?: string[];
  value_mapping?: Record<string, unknown>;
};
export const valueTypes = ["string", "enum", "boolean", "integer", "decimal", "date", "datetime"];
export const operators = {
  equals: "Equals",
  not_equals: "Does not equal",
  in: "Is one of",
  not_in: "Is not one of",
  exists: "Exists",
  not_exists: "Does not exist",
  greater_than: "Greater than",
  greater_or_equal: "At least",
  less_than: "Less than",
  less_or_equal: "At most",
};
export const emptyDraft = (): RuleDraft => ({
  logical_name: "",
  source_system: "",
  source_type: "",
  predicate: "",
  value_type: "string",
  value_path: "",
  output_mode: "source_path",
  output_path: "",
  output_scope: "source",
  constant_value: "",
  subject_type: "commitment",
  subject_resolver: "source_document_commitments",
  iteration_path: null,
  source_line_id_path: null,
  conditions_mode: "all",
  conditions: [],
  normalization: [],
  allowed_values: [],
  observed_at_mode: "source_received_at",
  observed_at_path: null,
});
export function draftForRule(rule: Rule, entries: RealityGapDetail["entries"]): RuleDraft {
  const saved = entries.find(
    (e) => e.type === "implementation_proposal" && e.payload.rule_id === rule.id,
  )?.payload.draft;
  const { id: _id, version: _version, status: _status, summary: _summary, ...fields } = rule;
  return { ...emptyDraft(), ...fields, ...(saved && typeof saved === "object" ? saved : {}) };
}
export function typedValue(value: unknown, type: string): unknown {
  if (type === "string" || type === "enum") return String(value ?? "");
  const text = String(value ?? "").trim();
  if (type === "boolean") {
    if (/^true$/i.test(text)) return true;
    if (/^false$/i.test(text)) return false;
    throw new Error("Enter true or false.");
  }
  if (type === "integer") {
    if (!/^-?\d+$/.test(text) || !Number.isSafeInteger(Number(text)))
      throw new Error("Enter a whole number within the supported range.");
    return Number(text);
  }
  if (type === "decimal") {
    if (!/^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(text)) throw new Error("Enter a decimal number.");
    return text;
  }
  if (!text || !Number.isFinite(Date.parse(text)))
    throw new Error("Enter a valid date or date and time.");
  return text;
}
export function conditionOperand(value: unknown, operator: string, type: string): unknown {
  if (operator === "exists" || operator === "not_exists") return undefined;
  if (operator === "in" || operator === "not_in") {
    const values = Array.isArray(value)
      ? value
      : String(value)
          .split(",")
          .map((v) => v.trim());
    if (!values.length || values.some((v) => v === ""))
      throw new Error("Enter at least one comparison value.");
    return values.map((v) => typedValue(v, type));
  }
  return typedValue(value, type);
}
export function validateDraft(input: RuleDraft): RuleDraft {
  const draft = structuredClone(input);
  for (const key of ["logical_name", "source_system", "source_type", "predicate"] as const)
    if (!draft[key]?.trim()) throw new Error("Complete the rule name, source and Fact fields.");
  const path = (value: string | null) => {
    if (!value || !/^[A-Za-z_][A-Za-z0-9_]*(?:\.(?:[A-Za-z_][A-Za-z0-9_]*|\d+))*$/.test(value))
      throw new Error("Enter a valid source field path.");
  };
  if (draft.output_mode === "source_path") {
    path(draft.output_path);
    draft.value_path = draft.output_path!;
  } else draft.constant_value = typedValue(draft.constant_value, draft.value_type);
  if (draft.subject_resolver === "source_document_lines") {
    path(draft.iteration_path);
    path(draft.source_line_id_path);
    draft.subject_type = "document_line";
  } else {
    draft.subject_type = "commitment";
    draft.iteration_path = null;
    draft.source_line_id_path = null;
  }
  if (draft.observed_at_mode === "source_path") path(draft.observed_at_path);
  if (draft.conditions_mode === "any" && !draft.conditions.length)
    throw new Error("A condition group cannot be empty.");
  let leaves = 0;
  const visit = (node: RealityGapCondition, depth: number): RealityGapCondition => {
    if ("mode" in node) {
      if (depth > 3 || !node.conditions.length)
        throw new Error("Use nonempty condition groups within three levels.");
      return { ...node, conditions: node.conditions.map((n) => visit(n, depth + 1)) };
    }
    if (++leaves > 20) throw new Error("A rule supports at most 20 conditions.");
    path(node.path);
    if (!(node.operator in operators)) throw new Error("Choose a supported comparison.");
    return { ...node, operand: conditionOperand(node.operand, node.operator, node.value_type) };
  };
  draft.conditions = draft.conditions.map((n) => visit(n, 2));
  return draft;
}
export const operandText = (value: unknown): string =>
  Array.isArray(value) ? value.map(String).join(", ") : String(value ?? "");

export function readDraft(text: string): RuleDraft {
  const parsed: unknown = JSON.parse(text);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed))
    throw new Error("Invalid rule definition.");
  const draft = { ...emptyDraft(), ...parsed } as RuleDraft;
  if (
    !Array.isArray(draft.allowed_values) ||
    draft.allowed_values.some((v) => typeof v !== "string")
  )
    throw new Error("Invalid rule definition.");
  const check = (nodes: unknown): void => {
    if (!Array.isArray(nodes)) throw new Error("Invalid rule definition.");
    for (const node of nodes) {
      if (!node || typeof node !== "object") throw new Error("Invalid rule definition.");
      if ("mode" in node) {
        if (!["all", "any"].includes(node.mode)) throw new Error("Invalid rule definition.");
        check(node.conditions);
      } else if ([node.path, node.operator, node.value_type].some((v) => typeof v !== "string"))
        throw new Error("Invalid rule definition.");
    }
  };
  check(draft.conditions);
  return draft;
}

export function initialRuleDraft(detail: RealityGapDetail): RuleDraft {
  const sorted = [...detail.rules].sort((a, b) => b.version - a.version);
  const rule =
    sorted.find((r) => r.status === "draft") ||
    sorted.find((r) => r.status === "active") ||
    sorted[0];
  if (rule) return draftForRule(rule, detail.entries);
  const evidence = [...detail.entries]
    .reverse()
    .find((e) => e.type === "evidence" && typeof e.payload.field_path === "string")?.payload;
  return {
    ...emptyDraft(),
    logical_name: detail.gap.question,
    ...(evidence
      ? {
          source_system: String(evidence.source_system || ""),
          source_type: String(evidence.source_type || ""),
          output_path: String(evidence.field_path),
          value_path: String(evidence.field_path),
          value_type: String(evidence.value_type || "string"),
        }
      : {}),
  };
}
export function ruleSentence(draft: RuleDraft, translate: (label: string) => string): string {
  if (
    !draft.source_system ||
    !draft.source_type ||
    !draft.predicate ||
    (draft.output_mode === "source_path" && !draft.output_path)
  )
    return translate("Choose a source, a characteristic and a value to complete this rule.");
  const value = (v: unknown, type: string) =>
    type !== "boolean"
      ? operandText(v)
      : v === true || String(v).toLowerCase() === "true"
        ? translate("Yes")
        : v === false || String(v).toLowerCase() === "false"
          ? translate("No")
          : operandText(v);
  const condition = (n: RealityGapCondition): string =>
    "mode" in n
      ? `(${n.conditions.map(condition).join(translate(n.mode === "all" ? " and " : " or "))})`
      : `${n.path || translate("Choose a field")} ${translate(operators[n.operator as keyof typeof operators] || n.operator)} ${["exists", "not_exists"].includes(n.operator) ? "" : value(n.operand, n.value_type)}`;
  const parts: Record<string, string> = {
    source: `${draft.source_system} · ${draft.source_type}`,
    conditions: draft.conditions.length
      ? draft.conditions
          .map(condition)
          .join(translate(draft.conditions_mode === "all" ? " and " : " or "))
      : translate("the source matches"),
    fact: `${draft.predicate} = ${draft.output_mode === "constant" ? value(draft.constant_value, draft.value_type) : draft.output_path}`,
    subject: translate(
      draft.subject_resolver === "source_document_lines"
        ? "each matching order line"
        : "the delivery commitment",
    ),
  };
  return translate("For {source}, when {conditions}, remember {fact} for {subject}.").replace(
    /\{(source|conditions|fact|subject)\}/g,
    (_, key: string) => parts[key],
  );
}
