import { useEffect, useRef, useState } from "react";
import { CockpitLiveRead, type LiveReadState } from "./cockpitLiveRead";

const empty = { data: null, status: "loading", receivedAt: null, error: null } as const;

/** A context key isolates company/filter reads without resetting sibling inspection state. */
export function useCockpitLiveRead<T>(key: string, read: (signal: AbortSignal) => Promise<T>) {
  const readRef = useRef({ key, read });
  readRef.current = { key, read };
  const [held, setHeld] = useState<{ key: string; state: LiveReadState<T> }>({ key, state: empty });
  useEffect(() => {
    const controller = new CockpitLiveRead({
      read: (signal) => {
        if (readRef.current.key !== key)
          return Promise.reject(new DOMException("Context changed", "AbortError"));
        return readRef.current.read(signal);
      },
      onChange: (state) => setHeld({ key, state }),
    });
    const visible = () => controller.setVisible(document.visibilityState === "visible");
    document.addEventListener("visibilitychange", visible);
    controller.start(document.visibilityState === "visible");
    return () => {
      document.removeEventListener("visibilitychange", visible);
      controller.dispose();
    };
  }, [key]);
  // Do not expose another company's held data for the render before effect cleanup.
  return held.key === key ? held.state : empty;
}
