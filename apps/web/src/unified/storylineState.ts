import type { Selection } from "./routing";
import type { StorylineChapterDetail, StorylineStep, StorylineText } from "../api";
import { currentLanguage } from "../localization";

/** The text of a package in the UI language, English when the package has none. */
export function pickText(text: StorylineText | null | undefined): string {
  if (!text) return "";
  return (text[currentLanguage()] || text.en || "").trim();
}

export type Phase = "idle" | "preview" | "done" | "refused" | "unresolved";

/** The chapter slot of the URL that means "free play" (browser-only mode, FR-011). */
export const FREE_PLAY = "free";
/** The chapter slot that opens the library from a company that already has a run. */
export const LIBRARY = "library";

/** What the narrator shows for a chapter, derived from its latest step only. */
export function phaseOf(step: StorylineStep | null | undefined): Phase {
  if (!step) return "idle";
  if (step.status === "done") return "done";
  if (step.status === "refused") return "refused";
  if (step.status === "rejected") return "idle";
  if (step.error?.unresolved) return "unresolved";
  return step.review ? "preview" : "idle";
}

/** One request key per click; a retry of the same click resumes the same step. */
export function requestKey(chapter: string): string {
  return `${chapter}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

const viewRoutes: Record<string, Partial<Selection>> = {
  orders: { route: "orders-deliveries", ordersView: "customer-orders" },
  commitments: { route: "orders-deliveries", ordersView: "deliveries" },
  inventory: { route: "warehouse", warehouseView: "stock" },
  reservations: { route: "warehouse", warehouseView: "reservations" },
  movements: { route: "warehouse", warehouseView: "movements" },
  open_items: { route: "finance", financeView: "open-items" },
  payments: { route: "finance", financeView: "payments" },
  journal: { route: "finance", financeView: "journal" },
  documents: { route: "data-sources", dataView: "documents" },
  fulfillment_blockers: { route: "attention" },
  activity: { route: "inspector", inspectorView: "history" },
  parties: { route: "master-data", family: "customer" },
  items: { route: "master-data", family: "item" },
  locations: { route: "master-data", family: "location" },
};

/** Where the ordinary app shows the view a chapter names. */
export function viewRoute(view: string | null): Partial<Selection> | null {
  if (!view) return null;
  return viewRoutes[view.replace(/^view:/, "")] || null;
}

/** Where a delta item opens on its ordinary surface. */
export function recordRoute(recordType: string, recordId: string): Partial<Selection> {
  if (recordType === "fact") return { route: "facts", entry: recordId, factTarget: "fact" };
  return {
    route: "inspector",
    inspectorView: "records",
    inspectorRecordKind: recordType,
    entry: recordId,
    q: "",
    page: 1,
  };
}

/** Row values that name one of the records a chapter added. */
export function rowIsNew(row: Record<string, unknown>, newIds: Set<string>): boolean {
  if (!newIds.size) return false;
  return Object.values(row).some((value) => typeof value === "string" && newIds.has(value));
}

/** What presentation mode does next; `null` means wait for the page to settle. */
export type PresentationAction =
  | { kind: "prepare" }
  | { kind: "confirm" }
  | { kind: "branch"; branch: string }
  | { kind: "next"; chapter: string }
  | { kind: "end"; reason: "finished" | "blocked" | "unresolved" | "later" };

/** Beats a presenter gets to read before each move (FR-013 "a readable pause"). */
export const PRESENTATION_BEATS: Record<PresentationAction["kind"], number> = {
  prepare: 1,
  confirm: 1,
  branch: 1,
  next: 2,
  end: 0,
};

const DEFAULT_PACE_MS = 4000;

/** Milliseconds per beat; a presenter can slow or speed the run for this browser tab. */
export function presentationPace(): number {
  try {
    const stored = Number(window.sessionStorage.getItem("storyline.pace"));
    if (Number.isFinite(stored) && stored >= 50) return stored;
  } catch {
    /* no storage: default pace */
  }
  return DEFAULT_PACE_MS;
}

/**
 * The next move of a timed run, derived from what the page already shows. The
 * presentation goes through exactly the calls a person would click (FR-013):
 * prepare, confirm, the default branch when none is chosen, then the next chapter.
 */
export function nextPresentationAction(input: {
  detail: StorylineChapterDetail | null;
  step: StorylineStep | null;
  currentChapter: string | null;
  chosenBranch: string | null;
  busy: boolean;
}): PresentationAction | null {
  const { detail, step, currentChapter, chosenBranch, busy } = input;
  if (busy || !detail) return null;
  const chapter = detail.chapter;
  const isCurrent = currentChapter === chapter.key;
  const phase = phaseOf(step);
  if (phase === "preview") return { kind: "confirm" };
  if (phase === "unresolved") return { kind: "end", reason: "unresolved" };
  if (phase === "idle") {
    if (isCurrent) {
      if (detail.can_run) return { kind: "prepare" };
      return { kind: "end", reason: "blocked" };
    }
    if (currentChapter) return { kind: "next", chapter: currentChapter };
    return { kind: "end", reason: "finished" };
  }
  // done or refused
  if (chapter.branches.length > 0 && !chosenBranch) {
    const fallback = chapter.branches.find((branch) => branch.default) || chapter.branches[0];
    return { kind: "branch", branch: fallback.key };
  }
  if (currentChapter && currentChapter !== chapter.key)
    return { kind: "next", chapter: currentChapter };
  if (!currentChapter) return { kind: "end", reason: "finished" };
  return { kind: "end", reason: "later" };
}

/** Expected against observed findings, never blocking (spec 182, FR-014). */
export function compareFindings(
  expected: { raised: string[]; cleared: string[] },
  observed: { raised: Array<{ class_id: string }>; cleared: Array<{ class_id: string }> } | null,
) {
  const raised = new Set(observed?.raised.map((x) => x.class_id) || []);
  const cleared = new Set(observed?.cleared.map((x) => x.class_id) || []);
  return {
    raised: expected.raised.map((id) => ({ id, met: raised.has(id) })),
    cleared: expected.cleared.map((id) => ({ id, met: cleared.has(id) })),
  };
}
