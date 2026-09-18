import { useState } from "react";
import { graphApi, type GraphQuestion, type GraphTemplate } from "../../api";
import { currentLanguage, t } from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { periodOf } from "./GraphSteps";

/** Questions worth starting from, and one click to make one your own.
 *
 * An empty builder asks the reader to know the model before it shows them
 * anything. A template shows them what the model can answer, in the words of
 * their own business, and every one of them is resolved against the declaration
 * when the model loads — so nothing here can be offered and then refused.
 */
export function GraphTemplates({
  tenant,
  onAdopted,
  selectedKey,
}: {
  tenant: string;
  selectedKey?: string;
  onAdopted: (question: GraphQuestion) => void;
}) {
  const [snapshots, setSnapshots] = useState<Record<string, string>>({});
  const language = currentLanguage();
  const read = useRead(() => graphApi.templates(tenant, language), [tenant, language]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;

  return (
    <section className="register-surface">
      <div>
        <p className="mb-3 text-xs text-fg-muted">
          {t("Choose a starting point. You can adjust it before saving.")}
        </p>
      </div>
      <div className="divide-y divide-border-default">
        {read.data.templates
          .filter((template) => !selectedKey || template.key === selectedKey)
          .map((template) => (
            <article key={template.key} className="flex flex-wrap items-center gap-3 py-3 text-sm">
              <div className="min-w-0 flex-1">
                <h3 className="font-medium">{template.label}</h3>
                <p className="mt-1 text-xs text-fg-muted">{template.about}</p>
              </div>
              {template.period && (
                <p className="text-xs text-fg-muted">
                  {t("Comes with a period")}:{" "}
                  {t(WINDOWS[template.period.window] ?? template.period.window)}
                </p>
              )}
              {template.snapshot && (
                <label className="text-xs text-fg-muted">
                  {t("Snapshot date (UTC)")}
                  <input
                    type="date"
                    className="br-control ml-2"
                    value={snapshots[template.key] ?? ""}
                    max={new Date().toISOString().slice(0, 10)}
                    onChange={(event) =>
                      setSnapshots({ ...snapshots, [template.key]: event.target.value })
                    }
                  />
                </label>
              )}
              <button
                className="br-btn"
                disabled={Boolean(template.snapshot && !snapshots[template.key])}
                onClick={() => onAdopted(dated(template, snapshots[template.key]))}
              >
                {t("Use template")}
              </button>
            </article>
          ))}
      </div>
    </section>
  );
}

/** The words a window is named by, so the template says what it will set. */
const WINDOWS: Record<string, string> = {
  this_month: "this month",
  last_month: "last month",
  this_year: "this year",
  last_year: "last year",
  last_30_days: "the last 30 days",
};

/** Resolve the template's window here, where the reader's calendar is.
 *
 * A stored question holds instants. "This month" is a different pair of
 * instants in Auckland and in Lisbon, and only the browser asking knows which.
 */
function dated(template: GraphTemplate, snapshot?: string): GraphQuestion {
  if (template.snapshot && snapshot)
    return {
      ...template.question,
      filter: [
        ...(template.question.filter ?? []),
        { field: template.snapshot, op: "eq", value: snapshot },
      ],
    };
  if (!template.period) return template.question;
  const period = periodOf(template.period.window, template.period.temporal);
  if (!period) return template.question;
  return {
    ...template.question,
    filter: [
      ...(template.question.filter ?? []),
      ...period.conditions.map((condition) => ({
        field: template.period!.field,
        op: condition.op,
        value: condition.value,
      })),
    ],
  };
}
