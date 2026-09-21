import type { CompanySetupResult } from "../api";

/** Feature 199: a company is committed before its profile is seeded.
 *
 * The creation request answers with `initializing`; the shared worker seeds the
 * profile and completes the live setup. The preparing screens therefore follow the
 * receipt instead of waiting inside one long request.
 */
export const SETUP_POLL_MS = 1000;
/** Three minutes of following, after which the person is offered the explicit retry. */
export const SETUP_POLL_ATTEMPTS = 180;
export const SETUP_READY_CURRENT_MS = 1500;
export const SETUP_READY_DONE_MS = 2000;

export type SetupProgress = "ready" | "failed" | "waiting";

export function setupProgress(receipt: CompanySetupResult | null): SetupProgress {
  if (!receipt) return "waiting";
  if (receipt.status === "ready") return "ready";
  return receipt.status === "initializing" ? "waiting" : "failed";
}

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Where the company stands, as far as the receipt can honestly say (feature 201). */
export type SetupStage = "created" | "queued" | "preparing" | "retrying" | "ready";

export function setupStage(receipt: CompanySetupResult | null): SetupStage | null {
  if (!receipt || setupProgress(receipt) === "failed") return null;
  if (receipt.status === "ready") return "ready";
  if (receipt.preparation === "preparing") return "preparing";
  if (receipt.preparation === "retrying") return "retrying";
  return receipt.preparation === "queued" ? "queued" : "created";
}

export type SetupStepState = "done" | "current" | "waiting";
export type SetupStep = { key: string; label: string; state: SetupStepState };

/** The four setup outcomes a person can see, each one taken from real state.
 *
 * Nothing here is estimated: queued work is visibly current but says it is waiting;
 * the label changes only once a worker has actually claimed it.
 */
export function setupSteps(receipt: CompanySetupResult | null): SetupStep[] | null {
  const stage = setupStage(receipt);
  if (!stage) return null;
  const ready = stage === "ready";
  return [
    { key: "created", label: "Company created", state: "done" },
    {
      key: "data",
      label:
        stage === "preparing"
          ? "Preparing orders, deliveries and invoices"
          : stage === "retrying"
            ? "Trying preparation again automatically"
            : "Waiting to start",
      state: ready ? "done" : "current",
    },
    {
      key: "calculation",
      label: ready ? "Finance and margins calculated" : "Calculating finance and margins",
      state: ready ? "done" : "waiting",
    },
    { key: "ready", label: "Ready to explore", state: ready ? "done" : "waiting" },
  ];
}

/** Keep confirmed completion visible before navigation without inventing backend state. */
export async function presentReadySetup(
  observe: (steps: SetupStep[]) => void,
  active: () => boolean,
  options: { currentDelay?: number; doneDelay?: number } = {},
): Promise<void> {
  if (!active()) return;
  const done = setupSteps({ status: "ready" } as CompanySetupResult)!;
  observe(done.map((step) => (step.key === "ready" ? { ...step, state: "current" } : step)));
  await wait(options.currentDelay ?? SETUP_READY_CURRENT_MS);
  if (!active()) return;
  observe(done);
  await wait(options.doneDelay ?? SETUP_READY_DONE_MS);
}

/** Read the receipt until the company is ready, fails, or the bound is reached.
 *
 * The first read happens immediately: a company that is already ready must not wait
 * out an interval first. `active` stops the loop when the screen is gone, and a read
 * that fails is retried, because a transient network answer must not end a setup that
 * is still running.
 */
export async function followSetup(
  read: () => Promise<CompanySetupResult | null>,
  active: () => boolean,
  options: {
    attempts?: number;
    delay?: number;
    observe?: (receipt: CompanySetupResult | null) => void;
  } = {},
): Promise<CompanySetupResult | null> {
  const attempts = options.attempts ?? SETUP_POLL_ATTEMPTS;
  const delay = options.delay ?? SETUP_POLL_MS;
  let last: CompanySetupResult | null = null;
  for (let attempt = 0; attempt < attempts && active(); attempt++) {
    if (attempt > 0) {
      await wait(delay);
      if (!active()) return null;
    }
    try {
      last = await read();
    } catch {
      continue;
    }
    options.observe?.(last);
    if (setupProgress(last) !== "waiting") return last;
  }
  return active() ? last : null;
}
