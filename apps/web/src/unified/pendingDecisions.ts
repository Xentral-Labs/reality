import { useEffect, useState } from "react";
import { api, recordsChanged } from "../api";

/** While a tab stays visible the count is re-read at most this often. */
export const PENDING_DECISIONS_REFRESH_MS = 60_000;

/**
 * The number of decisions awaiting approval in one company.
 *
 * It reads the same queue count the Decisions register pages, one row wide, so
 * the badge cannot disagree with the list it points to. A hidden tab does not
 * read; it catches up as soon as it is shown again.
 */
export function usePendingDecisions(tenant: string): number | null {
  const [count, setCount] = useState<number | null>(null);
  useEffect(() => {
    setCount(null);
    let disposed = false;
    let busy = false;
    let again = false;
    let settle: number | undefined;
    const refresh = () => {
      if (disposed || document.hidden) return;
      if (busy) {
        again = true;
        return;
      }
      busy = true;
      api
        .changeProposals(tenant, "pending", 1, "", 1)
        .then((result) => {
          if (!disposed) setCount(result.page.total);
        })
        .catch(() => {
          // The badge keeps its last known count; the register reports errors.
        })
        .finally(() => {
          busy = false;
          if (again) {
            again = false;
            refresh();
          }
        });
    };
    // A write can create or settle a decision; several writes in a row read once.
    const changed = () => {
      window.clearTimeout(settle);
      settle = window.setTimeout(refresh, 300);
    };
    const visible = () => {
      if (!document.hidden) refresh();
    };
    refresh();
    const timer = window.setInterval(refresh, PENDING_DECISIONS_REFRESH_MS);
    window.addEventListener(recordsChanged, changed);
    document.addEventListener("visibilitychange", visible);
    return () => {
      disposed = true;
      window.clearInterval(timer);
      window.clearTimeout(settle);
      window.removeEventListener(recordsChanged, changed);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [tenant]);
  return count;
}
