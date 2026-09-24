import { formatDateTime, t } from "../localization";
import {
  decisionHref,
  deciderSentence,
  fillSentence,
  type DecisionAttribution,
} from "./decisionTrail";

/** Who settled a decision and when, linked to the decision itself (spec 263). */
export function DecisionLine({
  decision,
  tenant,
  label,
  link = true,
}: {
  decision: Pick<DecisionAttribution, "id" | "outcome" | "decided_at" | "decider">;
  tenant?: string;
  /** What the decision did, already translated; omitted where the context says it. */
  label?: string;
  link?: boolean;
}) {
  const sentence = deciderSentence(decision.outcome, decision.decider);
  const text = fillSentence(t(sentence.template), sentence.values);
  const revoked = decision.decider.kind === "mcp_token" && decision.decider.revoked;
  const parts = [
    label,
    text,
    revoked ? t("Token revoked") : "",
    decision.decided_at ? formatDateTime(decision.decided_at) : "",
  ].filter(Boolean);
  const content = parts.join(" · ");
  return (
    <span
      className="text-fg-muted"
      data-decision={decision.id}
      data-decider-kind={decision.decider.kind}
    >
      {link && tenant ? (
        <a
          className="underline decoration-dotted underline-offset-2 hover:text-fg-strong"
          href={decisionHref(tenant, decision.id)}
          data-action-meaning="navigate"
          title={t("Open the decision")}
        >
          {content}
        </a>
      ) : (
        content
      )}
    </span>
  );
}
