import { useState } from "react";
import { graphApi, type GraphQuestion, type GraphReport, type GraphTemplate } from "../../api";
import { currentLanguage, t } from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { analyticsError } from "./errors";
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
}: {
  tenant: string;
  onAdopted: (report: GraphReport) => void;
}) {
  const language = currentLanguage();
  const read = useRead(() => graphApi.templates(tenant, language), [tenant, language]);
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState("");

  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;

  const adopt = async (template: GraphTemplate) => {
    setBusy(template.key);
    setFailed("");
    try {
      onAdopted(
        await graphApi.change(tenant, {
          operation: "create",
          request_id: crypto.randomUUID(),
          name: template.label,
          question: dated(template),
        }),
      );
    } catch (failure) {
      setFailed(failure instanceof Error ? failure.message : analyticsError(failure));
    } finally {
      setBusy("");
    }
  };

  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold">{t("Start from a template")}</h2>
        <p className="mt-1 max-w-2xl text-sm text-fg-muted">
          {t(
            "Each one is a question, not an answer: taking it over runs it against your records and gives you your own copy to change.",
          )}
        </p>
      </div>
      {failed && (
        <div className="rounded-xl border border-warning-200 bg-warning-50 p-4 text-sm">
          {failed}
        </div>
      )}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {read.data.templates.map((template) => (
          <article
            key={template.key}
            className="flex flex-col gap-3 rounded-xl border border-border-default bg-surface p-5"
          >
            <div>
              <h3 className="font-medium">{template.label}</h3>
              <p className="mt-2 text-sm text-fg-muted">{template.about}</p>
            </div>
            {template.period && (
              <p className="text-xs text-fg-muted">
                {t("Comes with a period")}:{" "}
                {t(WINDOWS[template.period.window] ?? template.period.window)}
              </p>
            )}
            <button
              className="br-btn mt-auto self-start"
              disabled={Boolean(busy)}
              onClick={() => void adopt(template)}
            >
              {busy === template.key ? t("Saving…") : t("Take this over")}
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

/** The words a window is named by, so the card says what it will set. */
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
function dated(template: GraphTemplate): GraphQuestion {
  if (!template.period) return template.question;
  const period = periodOf(template.period.window);
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
