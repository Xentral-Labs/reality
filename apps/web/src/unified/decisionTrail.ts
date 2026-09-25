/**
 * Who settled a decision, as the server states it (spec 263).
 *
 * The browser derives nothing here: it chooses the sentence for the attribution the
 * server returned. A decision confirmed through MCP names the token and the owner
 * who issued it, never that owner as the one who confirmed, because Reality sees the
 * token and not the person at the agent client.
 */
export type Decider =
  | { kind: "person"; name: string }
  | { kind: "chat_agent" }
  | {
      kind: "mcp_token";
      token_name: string;
      token_prefix: string;
      revoked: boolean;
      issuer: string | null;
    }
  | { kind: "unknown" };

export type DecisionAttribution = {
  id: string;
  tool: string;
  outcome: string;
  decided_at: string | null;
  decider: Decider;
};

export type DeciderSentence = { template: string; values: Record<string, string> };

export function deciderSentence(outcome: string, decider: Decider): DeciderSentence {
  const rejected = outcome === "rejected";
  if (outcome === "proposed") return { template: "Not decided yet", values: {} };
  if (decider.kind === "person")
    return {
      template: rejected ? "Rejected by {name}" : "Confirmed by {name}",
      values: { name: decider.name },
    };
  if (decider.kind === "chat_agent")
    return {
      template: rejected ? "Rejected by Chat agent" : "Confirmed by Chat agent",
      values: {},
    };
  if (decider.kind === "mcp_token")
    return decider.issuer
      ? {
          template: rejected
            ? "Rejected through token {token}, issued by {issuer}"
            : "Confirmed through token {token}, issued by {issuer}",
          values: { token: decider.token_name, issuer: decider.issuer },
        }
      : {
          template: rejected
            ? "Rejected through token {token}, issuer unknown"
            : "Confirmed through token {token}, issuer unknown",
          values: { token: decider.token_name },
        };
  return {
    template: rejected
      ? "Rejected, decided by an unrecorded person"
      : "Confirmed, decided by an unrecorded person",
    values: {},
  };
}

export function fillSentence(template: string, values: Record<string, string>): string {
  return Object.entries(values).reduce(
    (text, [key, value]) => text.replaceAll(`{${key}}`, value),
    template,
  );
}

export function decisionHref(tenant: string, proposal: string): string {
  return `/app/decisions?${new URLSearchParams({
    tenant,
    decisions_view: "history",
    proposal,
  })}`;
}
