import { useEffect, useRef, useState } from "react";
import { operationalCases, type OperationalCase } from "../api";
import { t } from "../localization";

/** Keep the exact reviewed request stable while sibling observations advance. */
export function useOperationalCaseControls(tenant: string, context = "") {
  const key = `${tenant}:${context}`;
  const current = useRef(key);
  current.current = key;
  const [review, setReview] = useState<(OperationalCase & { digest: string }) | null>(null);
  const [confirm, setConfirm] = useState<OperationalCase | "adopt" | null>(null);
  const [requestKey, setRequestKey] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const attempted = useRef<{ key: string; reason: string } | null>(null);
  useEffect(() => {
    setReview(null);
    setConfirm(null);
    setRequestKey("");
    setReason("");
    setError("");
    setBusy(false);
    attempted.current = null;
  }, [key]);
  async function act(operation: () => Promise<unknown>) {
    const started = current.current;
    setBusy(true);
    setError("");
    try {
      await operation();
      if (current.current === started) {
        setReview(null);
        setConfirm(null);
        attempted.current = null;
        setRefresh((value) => value + 1);
      }
    } catch (failure: unknown) {
      if (current.current === started)
        setError(failure instanceof Error ? failure.message : t("Could not load this view"));
    } finally {
      if (current.current === started) setBusy(false);
    }
  }
  function beginTakeover(value: OperationalCase) {
    setReview(null);
    setConfirm(value);
    setRequestKey(crypto.randomUUID());
    setReason("");
    setError("");
    attempted.current = null;
  }
  async function prepare(value: OperationalCase) {
    const started = current.current;
    setBusy(true);
    setError("");
    setReview(null);
    setConfirm(null);
    setRequestKey(crypto.randomUUID());
    attempted.current = null;
    try {
      const result = await operationalCases.review(tenant, value.case_id);
      if (current.current === started) setReview(result);
    } catch (failure: unknown) {
      if (current.current === started)
        setError(failure instanceof Error ? failure.message : t("Could not load this view"));
    } finally {
      if (current.current === started) setBusy(false);
    }
  }
  function takeover() {
    if (!confirm || confirm === "adopt") return;
    // A retry after a lost response must retain the original key and exact payload.
    attempted.current ??= { key: requestKey, reason };
    const payload = attempted.current;
    return act(() => operationalCases.takeover(tenant, confirm, payload.key, payload.reason));
  }
  function handback() {
    if (review)
      return act(() =>
        operationalCases.handback(tenant, review.case_id, review.digest, requestKey),
      );
  }
  return {
    handback,
    review,
    setReview,
    confirm,
    setConfirm,
    requestKey,
    setRequestKey,
    busy,
    setBusy,
    error,
    setError,
    refresh,
    setRefresh,
    act,
    prepare,
    beginTakeover,
    takeover,
    reason,
    setReason,
    reasonLocked: attempted.current !== null,
  };
}
