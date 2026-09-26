import type { GuidanceStep, ResolutionGuidance, ResolutionGuidanceCatalog } from "../api";
import { t } from "../localization";

/** Spec 279: the event the shell and chat already listen to, now carrying a draft. */
export const openChatEvent = "reality:open-chat";

/** Open the chat with a prepared, unsent request for this scope. */
export function prepareChat(prompt: string, scopeLabel: string) {
  window.dispatchEvent(
    new CustomEvent(openChatEvent, { detail: { draft: t(prompt).replace("{scope}", scopeLabel) } }),
  );
}

export function reasonText(catalog: ResolutionGuidanceCatalog | undefined, code: string) {
  const entry = catalog?.reasons[code.split(":", 1)[0]];
  return entry
    ? { label: t(entry.label), explanation: t(entry.explanation) }
    : {
        label: t("Something this value needs is still missing"),
        explanation: t("Open the explanation to see which evidence is involved."),
      };
}

/** What stands in for a control when the viewer cannot act on the step. */
export function stepBarrier(
  step: GuidanceStep,
  guidance: ResolutionGuidance,
  viewer: { owner: boolean },
): string | null {
  if (step.state !== "open") return null;
  if (step.role === "operator") return t("An administrator takes care of this.");
  if (guidance.writable === false && step.path !== "none")
    return t("Cost decisions cannot be confirmed in this company.");
  if (step.role === "owner" && !viewer.owner) return t("A company owner must confirm this.");
  return null;
}
