import type { GraphNode, GraphQuestion } from "../../api";
import type { Plan } from "./GraphSteps";

/** The longest name the store accepts. */
const LIMIT = 120;

/** What to call this analysis, before anybody is asked to name it.
 *
 * The field used to open empty, and an empty name is refused, so the moment a
 * question became a report asked the reader to invent a title with nothing to
 * hand. Everything a title needs was already on the screen: the records being
 * read, the measures being reported, and the axes they are cut by — and all of
 * it in the reader's own language, because the catalog is served translated.
 *
 * It is a suggestion and nothing more. It is offered selected so one keystroke
 * replaces it, and it is never written unless somebody confirms it.
 */
export function suggestedName(
  plan: Plan,
  nodes: Record<string, GraphNode>,
  captions: string[] = [],
): string {
  const root = nodes[plan.blocks[0]?.node ?? ""];
  const declared = plan.blocks.flatMap((block) => nodes[block.node]?.measures ?? []);
  const measures = plan.measures
    // A stored question outlives a declaration. A retired key in the name would
    // be the one place a reader meets the model's own vocabulary.
    .map((key) => declared.find((measure) => measure.key === key)?.label)
    .filter((label): label is string => Boolean(label));
  const parts = [root?.label, ...measures, ...captions].filter((part): part is string =>
    Boolean(part),
  );
  return fitted(parts);
}

/** Join what fits and leave out what does not.
 *
 * Slicing the text would cut a label mid-word and put an ellipsis into a name
 * somebody is about to accept unchanged. Dropping a whole part keeps every word
 * in the name a word the analysis actually uses.
 */
function fitted(parts: string[]): string {
  const kept: string[] = [];
  for (const part of parts) {
    if (kept.includes(part)) continue;
    const candidate = [...kept, part].join(" · ");
    if (candidate.length > LIMIT) continue;
    kept.push(part);
  }
  return kept.join(" · ").slice(0, LIMIT);
}

/** Whether the question on screen is still the one that was saved.
 *
 * The server answers with the question canonicalized, so comparing the stored
 * text against the executed text reports a change nobody made. What is compared
 * is two canonical questions: key order does not matter, an absent list and an
 * empty one are the same question, and the order within a list does — two axes
 * swapped are two different tables.
 */
export function sameQuestion(saved: GraphQuestion | null, current: GraphQuestion | null): boolean {
  if (!saved || !current) return false;
  return stable(saved) === stable(current);
}

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.entries(value as Record<string, unknown>)
      .filter(([, entry]) => entry !== undefined && !(Array.isArray(entry) && !entry.length))
      .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0))
      .map(([key, entry]) => `${JSON.stringify(key)}:${stable(entry)}`)
      .join(",")}}`;
  return JSON.stringify(value ?? null);
}
