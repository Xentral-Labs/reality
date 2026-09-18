import { analysisMessageText } from "./analytics/chatHandoff";
/** Annotation is historical presentation, never tool authority.
 *
 * Messages written while the configured generation was live can still carry an
 * `analytics` annotation. It is ignored rather than rejected: the text stays
 * readable, which is the only thing an annotation was ever allowed to affect.
 */
export function messageContext(content: string): {
  text: string;
  context?: { id: string; label: string };
} {
  const prefix = "reality.context.v1:";
  if (content.startsWith(prefix)) {
    try {
      const value = JSON.parse(content.slice(prefix.length));
      if (typeof value.message === "string" && typeof value.commitment_id === "string")
        return {
          text: analysisMessageText(value.message),
          context: {
            id: value.commitment_id,
            label: typeof value.label === "string" ? value.label : value.commitment_id,
          },
        };
      if (typeof value.message === "string") return { text: analysisMessageText(value.message) };
    } catch {
      /* Historical text that is not a valid annotation remains readable. */
    }
  }
  return { text: analysisMessageText(content) };
}
