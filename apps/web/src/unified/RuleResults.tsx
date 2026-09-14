import { formatNumber, t } from "../localization";
import type { RealityGapSimulation } from "../api";
import type { Rule } from "./guidedRuleDraft";
export type ReplayResult = {
  facts_created: number;
  facts_existing: number;
  not_applicable: number;
  conflicts: number;
  failed: number;
  cumulative: Record<string, number>;
  next_cursor: string | null;
  complete: boolean;
};
export function RuleMetrics({ counts }: { counts: Record<string, number> }) {
  const labels: Record<string, string> = {
    sources_considered: "Sources checked",
    expected_facts: "Matching observations in this preview",
    invalid_values: "Invalid values",
    ambiguous_subjects: "Ambiguous subjects",
    not_applicable: "Sources not applicable",
    conflicts: "Conflicts",
    failed: "Failed",
    facts_created: "Facts created",
    facts_existing: "Existing facts",
    created: "Facts created",
    existing: "Existing facts",
    matched: "Matching observations in this preview",
    conflict: "Conflicts",
    invalid_value: "Invalid values",
    ambiguous_subject: "Ambiguous subjects",
  };
  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {Object.entries(counts).map(([key, value]) => (
        <div key={key} className="rounded-lg border border-border-default bg-surface p-3">
          <dt className="text-xs text-fg-muted">{t(labels[key] || key)}</dt>
          <dd className="mt-2 text-xl font-semibold">{formatNumber(value)}</dd>
        </div>
      ))}
    </dl>
  );
}
export function SimulationResults({
  result,
  tenant,
}: {
  result: RealityGapSimulation;
  tenant: string;
}) {
  const { examples, matches: _matches, ...counts } = result;
  return (
    <section
      className="space-y-3 rounded-xl border border-accent bg-accent-soft/30 p-4"
      aria-label={t("Simulation result")}
    >
      <h3 className="font-semibold">{t("Simulation result")}</h3>
      <p className="text-sm text-fg-muted">
        {t("Preview of up to 100 sources. No business data is changed.")}
      </p>
      <RuleMetrics counts={counts} />
      {examples.length > 0 && (
        <details open>
          <summary>{t("Show checked sources")}</summary>
          <div className="mt-3 space-y-2">
            {examples.map((e, i) => (
              <div className="rounded-lg bg-surface p-3 text-sm" key={`${e.source_record_id}:${i}`}>
                <a
                  className="text-accent underline"
                  href={`/app/inspector?tenant=${encodeURIComponent(tenant)}&inspector_view=records&family=source_record&entry=${encodeURIComponent(e.source_record_id)}`}
                >
                  {e.external_id}
                </a>
                <p>
                  {t(
                    (
                      {
                        matched: "Conditions match",
                        not_applicable: "Conditions do not apply",
                        conflict: "Conflicts with an existing Fact",
                        invalid_value: "Field is missing or has the wrong value",
                      } as Record<string, string>
                    )[e.status] || "Source needs review",
                  )}
                </p>
                {e.detail && (
                  <p className="break-words text-fg-muted" data-localization="original">
                    {e.detail}
                  </p>
                )}
              </div>
            ))}
          </div>
        </details>
      )}
    </section>
  );
}
export function ExecutionResults({ rule, tenant }: { rule: Rule; tenant: string }) {
  if (!Object.keys(rule.summary.counts).length) return null;
  return (
    <details className="my-3">
      <summary className="cursor-pointer text-sm">{t("Rule execution summary")}</summary>
      <div className="mt-3 space-y-3">
        <RuleMetrics counts={rule.summary.counts} />
        <div className="flex flex-wrap gap-2">
          {rule.summary.facts.map((f, i) => (
            <a
              key={`${f.fact_id}:${i}`}
              className="text-sm text-accent underline"
              href={`/app/inspector?tenant=${encodeURIComponent(tenant)}&inspector_view=records&family=fact&entry=${encodeURIComponent(f.fact_id)}`}
            >
              {t("Fact")} {i + 1}
            </a>
          ))}
        </div>
      </div>
    </details>
  );
}

export function RuleChangeSummary({ body }: { body: unknown }) {
  if (!body || typeof body !== "object") return null;
  const data = body as Record<string, unknown>;
  const payload =
    data.payload && typeof data.payload === "object"
      ? (data.payload as Record<string, unknown>)
      : {};
  const values = { ...data, ...payload };
  const labels: Record<string, string> = {
    question: "Business question",
    intended_use: "Intended use",
    source_system: "Source system",
    source_type: "Source type",
    external_id: "Source",
    field_path: "Source value path",
    displayed_value: "Fact value",
    note: "Manual observation",
    destination: "Technical model destination",
    rationale: "Reason",
    rule: "Rule",
    version: "Version",
  };
  return (
    <dl className="grid gap-2 text-sm sm:grid-cols-2">
      {Object.entries(labels).flatMap(([key, label]) =>
        values[key] === undefined
          ? []
          : [
              <div key={key}>
                <dt className="text-fg-muted">{t(label)}</dt>
                <dd className="break-words whitespace-pre-wrap" data-localization="original">
                  {String(values[key])}
                </dd>
              </div>,
            ],
      )}
    </dl>
  );
}
