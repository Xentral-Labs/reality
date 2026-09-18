import { APIError } from "../../api";
import { t } from "../../localization";

export function analyticsError(failure: unknown): string {
  const messages: Record<string, string> = {
    provider_unavailable:
      "No AI provider is connected. Choose an example or use the sentence controls.",
    interpretation_failed:
      "The question could not be interpreted. Rephrase it or choose an example.",
    query_too_broad: "This analysis is too broad. Narrow the period or filters.",
    query_timeout: "The analysis took too long. Narrow the period or filters and run again.",
    query_cancelled: "The analysis was cancelled.",
    invalid_definition: "Check the selected fields, filters and time window.",
    invalid_cursor: "This page no longer matches the analysis. Refresh the first page.",
    revision_conflict: "The report changed. Reload it before saving again.",
    idempotency_conflict: "This retry belongs to a different change. Reload the report.",
    user_context_required: "Sign in with your own account to use private reports.",
  };
  return t(
    failure instanceof APIError && failure.code && messages[failure.code]
      ? messages[failure.code]
      : failure instanceof Error
        ? failure.message
        : "The analysis could not be completed.",
  );
}
