import { useEffect, useRef, useState } from "react";
import { api, recordsChanged } from "../api";

/** While a tab stays visible a work count is re-read at most this often. */
export const WORK_COUNT_REFRESH_MS = 60_000;

/**
 * A count of open work, read with the same query its register pages.
 *
 * `key` names the read (company included); a new key starts over. A disabled
 * count keeps its last value and does not read, so a tab whose own register is
 * open does not ask twice. A hidden tab does not read; it catches up as soon
 * as it is shown again, and after any write in this browser.
 */
export function useWorkCount(
  key: string,
  read: () => Promise<number>,
  enabled = true,
): number | null {
  const [count, setCount] = useState<{ key: string; value: number } | null>(null);
  const current = useRef(read);
  current.current = read;
  useEffect(() => {
    if (!enabled) return;
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
      current
        .current()
        .then((value) => {
          if (!disposed) setCount({ key, value });
        })
        .catch(() => {
          // The count keeps its last value; the register reports errors.
        })
        .finally(() => {
          busy = false;
          if (again) {
            again = false;
            refresh();
          }
        });
    };
    // A write can open or settle work; several writes in a row read once.
    const changed = () => {
      window.clearTimeout(settle);
      settle = window.setTimeout(refresh, 300);
    };
    const visible = () => {
      if (!document.hidden) refresh();
    };
    refresh();
    const timer = window.setInterval(refresh, WORK_COUNT_REFRESH_MS);
    window.addEventListener(recordsChanged, changed);
    document.addEventListener("visibilitychange", visible);
    return () => {
      disposed = true;
      window.clearInterval(timer);
      window.clearTimeout(settle);
      window.removeEventListener(recordsChanged, changed);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [key, enabled]);
  return count?.key === key ? count.value : null;
}

/** The number of decisions awaiting approval in one company (spec 253). */
export function usePendingDecisions(tenant: string): number | null {
  return useWorkCount(`decisions:${tenant}`, () =>
    api.changeProposals(tenant, "pending", 1, "", 1).then((result) => result.page.total),
  );
}
