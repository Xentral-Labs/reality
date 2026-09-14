import { useEffect, useRef, useState } from "react";
import { api, type RealityGapDetail, type RealityGapSourceExample } from "../api";
import { t } from "../localization";
import { RuleField } from "./RuleDraftEditor";
export type PrepareRuleChange = (label: string, body: unknown, run: () => Promise<unknown>) => void;
export function RuleEvidence({
  tenant,
  detail,
  disabled,
  prepare,
  seed,
  guided = false,
}: {
  guided?: boolean;
  tenant: string;
  detail: RealityGapDetail;
  disabled: boolean;
  prepare: PrepareRuleChange;
  seed: (
    example: RealityGapSourceExample,
    candidate: RealityGapSourceExample["candidates"][number],
  ) => void;
}) {
  const [query, setQuery] = useState(""),
    [note, setNote] = useState(""),
    [error, setError] = useState("");
  const [results, setResults] = useState<RealityGapSourceExample[] | null>(null),
    [loading, setLoading] = useState(false);
  const [destination, setDestination] = useState("fact"),
    [rationale, setRationale] = useState("");
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const evidence = detail.entries.filter((e) => e.type === "evidence");
  const recommendation = [...detail.entries].reverse().find((e) => e.type === "recommendation");
  const add = (payload: Record<string, unknown>, after?: () => void) => {
    const body = { entry_type: "evidence", payload, expected_revision: detail.gap.revision };
    prepare("Add evidence", body, async () => {
      const result = await api.addRealityGapEntry(tenant, detail.gap.id, body);
      after?.();
      return result;
    });
  };
  const decide = (value: string, reason: string) => {
    const body = { destination: value, rationale: reason, expected_revision: detail.gap.revision };
    prepare("Choose interpretation", body, () => api.decideRealityGap(tenant, detail.gap.id, body));
  };
  return (
    <section className="space-y-4 rounded-xl border border-border-default p-4" data-rule-evidence>
      <h3 className="font-semibold">{t("Supporting examples")}</h3>
      {guided && (
        <p className="text-sm text-fg-muted">
          {t(
            !evidence.length
              ? "Search by an order reference, then choose the relevant value. Saving an example only documents your evidence."
              : !recommendation && !detail.gap.destination
                ? "Example saved. Request a recommendation to check whether this information belongs in a Fact rule."
                : !detail.gap.destination
                  ? "Review the recommendation and its limitations, then confirm the interpretation you want."
                  : "Your examples remain linked to their original sources.",
          )}
        </p>
      )}
      {evidence.map((e) => (
        <div className="rounded-lg bg-surface-muted p-3 text-sm" key={e.id}>
          {typeof e.payload.external_id === "string" && (
            <p className="mb-1 font-medium" data-localization="original">
              {e.payload.external_id}
            </p>
          )}
          <p className="break-words" data-localization="original">
            {String(
              e.payload.note ||
                `${e.payload.field_path || ""} = ${e.payload.displayed_value ?? ""}`,
            )}
          </p>
          {typeof e.payload.source_record_id === "string" && (
            <a
              className="mt-1 inline-block text-accent underline"
              href={`/app/inspector?tenant=${encodeURIComponent(tenant)}&inspector_view=records&family=source_record&entry=${encodeURIComponent(e.payload.source_record_id)}`}
            >
              {t("Open source")}
            </a>
          )}
        </div>
      ))}
      <fieldset disabled={disabled} className="space-y-3">
        <form
          className="space-y-2"
          onSubmit={async (e) => {
            e.preventDefault();
            if (loading) return;
            setLoading(true);
            setError("");
            try {
              const response = await api.realityGapSourceExamples(tenant, query);
              if (mounted.current) setResults(response.items);
            } catch (reason) {
              if (mounted.current) setError(String(reason));
            } finally {
              if (mounted.current) setLoading(false);
            }
          }}
        >
          <RuleField label="Find an order or source record">
            <input
              className="br-control w-full"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </RuleField>
          <button className="br-btn" disabled={loading || !query.trim()}>
            {t(loading ? "Loading" : "Search")}
          </button>
        </form>
        {error && <p role="alert">{error}</p>}
        {results?.length === 0 && (
          <p className="text-sm text-fg-muted">
            {t(
              "No matching source record found. Try another reference or add a manual observation.",
            )}
          </p>
        )}
        {results?.map((example) => (
          <article
            key={example.source_record_id}
            className="space-y-2 rounded-lg border border-border-default p-3"
          >
            <p className="font-medium" data-localization="original">
              {example.external_id} · {example.source_system} · {example.source_type}
            </p>
            {example.candidates.map((candidate) => (
              <button
                type="button"
                key={candidate.path}
                className="flex w-full flex-wrap items-center justify-between gap-2 rounded-lg bg-surface-muted p-3 text-left text-sm"
                onClick={() =>
                  add(
                    {
                      source_record_id: example.source_record_id,
                      source_system: example.source_system,
                      source_type: example.source_type,
                      external_id: example.external_id,
                      field_path: candidate.path,
                      displayed_value: candidate.value,
                      value_type: candidate.value_type,
                    },
                    () => seed(example, candidate),
                  )
                }
              >
                <span className="min-w-0 break-all" data-localization="original">
                  {candidate.path} = <strong>{candidate.value}</strong>
                </span>
                <span className="text-accent">{t("Use this value")}</span>
              </button>
            ))}
          </article>
        ))}
        <details>
          <summary className="cursor-pointer text-sm">{t("Manual observation")}</summary>
          <div className="mt-3 space-y-2">
            <RuleField label="Manual observation">
              <textarea
                className="br-control min-h-24 w-full"
                rows={3}
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </RuleField>
            <button
              type="button"
              className="br-btn"
              disabled={!note.trim()}
              onClick={() => add({ note, evidence_kind: "manual_observation" })}
            >
              {t("Save manual observation")}
            </button>
          </div>
        </details>
        {!detail.gap.destination && (
          <>
            {evidence.length > 0 && (
              <button
                type="button"
                className="br-btn"
                onClick={() =>
                  prepare("Create recommendation", { expected_revision: detail.gap.revision }, () =>
                    api.recommendRealityGap(tenant, detail.gap.id, detail.gap.revision),
                  )
                }
              >
                {t("Create recommendation")}
              </button>
            )}
            {recommendation && (
              <div className="space-y-3 rounded-lg bg-accent-soft p-4">
                <h4 className="font-semibold">{t("Reality recommendation")}</h4>
                <p data-localization="original">{String(recommendation.payload.destination)}</p>
                {["reasons", "limitations"].map((key) =>
                  Array.isArray(recommendation.payload[key]) ? (
                    <ul className="list-disc pl-5 text-sm" key={key}>
                      {(recommendation.payload[key] as unknown[]).map((v, i) => (
                        <li key={i} data-localization="original">
                          {String(v)}
                        </li>
                      ))}
                    </ul>
                  ) : null,
                )}
                <button
                  className="br-btn br-btn-primary"
                  onClick={() =>
                    decide(
                      String(recommendation.payload.destination),
                      "Accepted the reviewed Reality recommendation",
                    )
                  }
                >
                  {t("Accept recommendation")}
                </button>
              </div>
            )}
            <details>
              <summary className="cursor-pointer text-sm">
                {t("Choose a different outcome")}
              </summary>
              <div className="mt-3 space-y-3">
                <RuleField label="Technical model destination">
                  <select
                    className="br-control"
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                  >
                    {[
                      ["fact", "Fact"],
                      ["source_only", "Source only"],
                      ["typed_evidence", "Typed Evidence"],
                      ["typed_reality", "Typed Reality"],
                      ["derived_view", "Projection or Exception"],
                      ["rejected", "Reject"],
                    ].map(([v, label]) => (
                      <option key={v} value={v}>
                        {t(label)}
                      </option>
                    ))}
                  </select>
                </RuleField>
                <RuleField label="Reason">
                  <textarea
                    className="br-control min-h-24"
                    value={rationale}
                    onChange={(e) => setRationale(e.target.value)}
                  />
                </RuleField>
                <button
                  className="br-btn"
                  disabled={!rationale.trim()}
                  onClick={() => decide(destination, rationale)}
                >
                  {t("Use different outcome")}
                </button>
              </div>
            </details>
          </>
        )}
      </fieldset>
    </section>
  );
}
