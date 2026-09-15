import type { CompanySetupResult } from "../api";

/** Feature 199: a company is committed before its profile is seeded.
 *
 * The creation request answers with `initializing`; the shared worker seeds the
 * profile and completes the live setup. The preparing screens therefore follow the
 * receipt instead of waiting inside one long request.
 */
export const SETUP_POLL_MS = 2000;
/** Three minutes of following, after which the person is offered the explicit retry. */
export const SETUP_POLL_ATTEMPTS = 90;

export type SetupProgress = "ready" | "failed" | "waiting";

export function setupProgress(receipt: CompanySetupResult | null): SetupProgress {
  if (!receipt) return "waiting";
  if (receipt.status === "ready") return "ready";
  return receipt.status === "initializing" ? "waiting" : "failed";
}

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Read the receipt until the company is ready, fails, or the bound is reached.
 *
 * `active` stops the loop when the screen is gone. A read that fails is retried:
 * a transient network answer must not end a setup that is still running.
 */
export async function followSetup(
  read: () => Promise<CompanySetupResult | null>,
  active: () => boolean,
  options: { attempts?: number; delay?: number } = {},
): Promise<CompanySetupResult | null> {
  const attempts = options.attempts ?? SETUP_POLL_ATTEMPTS;
  const delay = options.delay ?? SETUP_POLL_MS;
  let last: CompanySetupResult | null = null;
  for (let attempt = 0; attempt < attempts && active(); attempt++) {
    await wait(delay);
    if (!active()) return null;
    try {
      last = await read();
    } catch {
      continue;
    }
    if (setupProgress(last) !== "waiting") return last;
  }
  return active() ? last : null;
}
