import { analyticsError } from "./errors";
import { useEffect, useRef, useState } from "react";
import { analyticsApi, type AnalyticsDefinition, type AnalyticsResult } from "../../api";

/** Keep edits separate from the definition that actually produced displayed values. */
export function useAnalyticsExecution(tenant: string) {
  const [result, setResult] = useState<AnalyticsResult | null>(null);
  const [submitted, setSubmitted] = useState<AnalyticsDefinition | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      generation.current += 1;
      controller.current?.abort();
    },
    [tenant],
  );
  const cancel = () => {
    generation.current += 1;
    controller.current?.abort();
    setRunning(false);
  };
  const run = async (definition: AnalyticsDefinition, cursor?: string) => {
    controller.current?.abort();
    controller.current = new AbortController();
    const current = ++generation.current;
    setRunning(true);
    setError("");
    try {
      const next = await analyticsApi.query(
        tenant,
        structuredClone(definition),
        controller.current.signal,
        cursor,
      );
      if (current === generation.current) {
        setResult(next);
        setSubmitted(structuredClone(definition));
      }
    } catch (failure) {
      if (current === generation.current && (failure as Error).name !== "AbortError")
        setError(analyticsError(failure));
    } finally {
      if (current === generation.current) setRunning(false);
    }
  };
  return { result, submitted, running, error, run, cancel };
}
