// Shared response presentation only. Business decisions are server-derived.
export type LogicNode = {
  id: string;
  function: string;
  kind: string;
  text: string;
  expression: string;
  evidence_id: string;
  line: number;
  end_line?: number;
  durable?: boolean;
  context: string[];
};
export type LogicSource = {
  id: string;
  path: string;
  function: string;
  role?: "reader" | "builder" | "shared" | "dependency";
  called_by?: string[];
  start_line: number;
  code: string;
  digest: string;
};
export type LogicScenario = {
  id: string;
  name: string;
  facts: {
    name: string;
    value: unknown;
    currency?: string | null;
    unit?: string | null;
  }[];
  setup: string[];
  action: string[];
  expectations: string[];
  assumptions: string[];
  parameters: Record<string, unknown>;
  relationship: string;
  rules: string[];
  code: string;
  helpers: LogicSource[];
  run: {
    outcome: string;
    revision_match: boolean;
    executed_at?: string;
    commit?: string;
    evidence?: string;
  };
};
export type BusinessBlueprint = {
  business?: {
    language: string;
    heading: string;
    notice: string;
    mode: "llm" | "unavailable" | "outdated";
    model: string | null;
    overview?: { text: string; evidence_ids: string[] } | null;
    diagram_notice?: string;
    unexplained_rules: number;
    steps: {
      id: string;
      function: string;
      kind: string;
      text: string;
      rule_ids: string[];
      evidence_ids: string[];
      line: number;
    }[];
    edges: { source: string; target: string; outcome: string }[];
    scenarios: {
      id: string;
      title: string;
      given: string[];
      when: string[];
      then: string[];
      notice: string;
      unexplained_assertions: number;
    }[];
  } | null;
  kind: string;
  key: string;
  label: string;
  purpose: string;
  status: string;
  presentation_language: string;
  release: { version: string; commit: string | null; source_digest: string };
  limitations: string[];
  nodes: LogicNode[];
  edges: { source: string; target: string; outcome: string }[];
  sources: LogicSource[];
  scenarios: LogicScenario[];
  test_gaps: string[];
  requirements: string[];
  consumers: string[];
  inputs: string[];
  outputs: string[];
  prerequisites: string[];
  runtime_values?: Record<string, unknown>;
  evidence_digest: string;
};
export type LogicComparison = {
  context: string;
  comparisons: {
    scenario_id: string;
    conditions: {
      name: string;
      test_values: string[];
      case_value: unknown;
      status: string;
    }[];
    unknown_assumptions: string[];
    untested_aspects: string[];
  }[];
  case_facts: {
    name: string;
    value: unknown;
    currency: string | null;
    unit: string | null;
  }[];
  recorded_decisions: {
    event_id: string;
    recorded_at: string;
    facts: Record<string, unknown> | null;
    rule_version: string;
  }[];
  links: { kind: string; id: string }[];
  limitations: string[];
  historical_rule_version: string;
};

export function diagram(nodes: LogicNode[], edges: BusinessBlueprint["edges"]) {
  const indices = new Map(nodes.map((n, i) => [n.id, i]));
  return {
    height: Math.max(80, nodes.length * 90),
    nodes: nodes.map((n, i) => ({ ...n, y: i * 90 + 10 })),
    edges: edges
      .filter((e) => indices.has(e.source) && indices.has(e.target))
      .map((e) => ({
        ...e,
        from: indices.get(e.source)! * 90 + 65,
        to: indices.get(e.target)! * 90 + 10,
      })),
  };
}

// Presentation numbering only: never infer an edge from adjacent cards.
export function flowCards(
  steps: NonNullable<BusinessBlueprint["business"]>["steps"],
  edges: BusinessBlueprint["edges"],
) {
  const indices = new Map(steps.map((step, index) => [step.id, index + 1]));
  return steps.map((step, index) => {
    const targets = new Map<number, Set<string>>();
    for (const edge of edges) {
      const target = indices.get(edge.target);
      if (edge.source !== step.id || target === undefined) continue;
      const paths = targets.get(target) || new Set<string>();
      paths.add(edge.outcome);
      targets.set(target, paths);
    }
    return {
      ...step,
      number: index + 1,
      next: Array.from(targets, ([target, paths]) => {
        const outcomes = Array.from(paths);
        const outcome =
          outcomes.length === 1 &&
          outcomes[0].length <= 30 &&
          !outcomes[0].includes(" / ")
            ? outcomes[0]
            : "";
        return { target, outcome, outcomes };
      }),
    };
  });
}

export type SourceRange = { start: number; end: number };
export function sourceRanges(
  source: LogicSource,
  nodes: LogicNode[],
  ruleIds: string[],
  fallbackLine?: number,
): SourceRange[] {
  const matching = nodes.filter(
    (node) =>
      ruleIds.includes(node.id) &&
      node.evidence_id === source.id &&
      node.function === source.function,
  );
  const ranges = matching.map((node) => {
    const end = node.end_line ?? node.line;
    const nested =
      ["decision", "loop", "refusal"].includes(node.kind) &&
      end - node.line > 4;
    return { start: node.line, end: nested ? node.line : end };
  });
  if (!ruleIds.length && fallbackLine !== undefined)
    ranges.push({ start: fallbackLine, end: fallbackLine });
  return ranges;
}
export function sourceExcerpt(
  source: LogicSource,
  ranges: SourceRange[],
  full = false,
) {
  const text = source.code.split("\n");
  const end = source.start_line + text.length - 1;
  const valid = ranges
    .filter(
      (range) =>
        Number.isInteger(range.start) &&
        Number.isInteger(range.end) &&
        range.start <= range.end &&
        range.end >= source.start_line &&
        range.start <= end,
    )
    .map((range) => ({
      start: Math.max(source.start_line, range.start),
      end: Math.min(end, range.end),
    }))
    .sort((a, b) => a.start - b.start);
  const first =
    full || !valid.length
      ? source.start_line
      : Math.max(source.start_line, valid[0].start - 3);
  const last =
    full || !valid.length
      ? end
      : Math.min(
          end,
          Math.max(...valid.map((range) => range.end)) + 3,
          first + 119,
        );
  return {
    lines: text
      .slice(first - source.start_line, last - source.start_line + 1)
      .map((line, index) => ({
        number: first + index,
        text: line,
        highlighted: valid.some(
          (range) => first + index >= range.start && first + index <= range.end,
        ),
      })),
    focusAvailable: valid.length > 0,
    total: text.length,
  };
}
